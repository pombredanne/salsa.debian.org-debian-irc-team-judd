###
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007,2008, Mike O'Connor
# Copyright (c) 2010-2011  Stuart Prescott
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES LOSS OF USE, DATA, OR PROFITS OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###

"""
Package dependency resolution via UDD

RelationChecker -- check sets of dependency relationships, installability
SolverHierarchy -- TODO: complete
"""

import copy
from relations import *
from packages import *


class Checker(object):
    """
    Check sets of dependencies to determine installability, build-ability etc

    Check -- check specified relationship for a package
    CheckRelationshipOptionsList -- determine if a list of relationships is
                                satisfied
    RelationSatisfied -- check an individual relationship
    CheckRelationArch -- check if the relationship applies to the
                            current architecture

    Typical usage:
        udd = Udd()
        release = udd.BindRelease(arch="i386",release="sid")
        checker = Checker(release)

        relationship = Relationship(relation="libc6 (>> 2.7)")
        if checker.RelationSatisfied(relationship):
            ...
        if checker.Check('libc6', 'depends'):
            ...
    """

    def __init__(self, release):
        """ Construct a Checker for the specified release """
        if not isinstance(release, Release):
            raise TypeError("The release object must be of type "
                            "uddcache.packages.Release")
        self.release = release
        self._checkInstallCache = {}

    def Check(self, package=None, relation='depends'):
        """Check that the specified relationships for a package

        Checks that the chosen relationships for a package can be satisfied
        in the given release.
            package: name of the package (string)
            relation: package relationship to be tested (string: depends,
                recommends, suggests, conflicts)
            Returns a RelationshipStatus object for the check or None if the
            package does not exist
        """
        p = self.release.Package(package)
        if not p.Found():
            raise PackageNotFoundError(package)
        status = self.CheckRelationshipOptionsList(
                                    p.RelationshipOptionsList(relation))
        if relation == 'conflicts':
            status.swap()
        return status

    def CheckRelationshipOptionsList(self, relationlist):
        """Check a set of package relationships to see if they are satisfied

        Checks a RelationshipOptionsList object to see if each relationship
        can be satisfied in the current release.
        Returns a RelationshipStatus object reflecting the satisfied and
        unsatisfied dependencies
        """
        status = RelationshipStatus()
        if relationlist == None:
            return status

        for opts in relationlist:
            #print "Considering fragment %s" % str(opts)
            satisfied = False
            for item in opts:    # item is a RelationshipOptions object
                #print "== part %s (%d)" % (type(item), len(opts))
                satisfied = self.RelationSatisfied(item)
                if satisfied:
                    opts.satisfiedBy = item
                    opts.virtual = item.virtual
                    opts.satisfied = True
                    opts.archIgnore = item.archIgnore
                    break
            if not satisfied:
                #print "%s not satisfied" % opts
                status.bad.append(opts)
            else:
                #print "%s satisfied" % opts
                status.good.append(opts)
        return status

    def CheckRelationArch(self, arch_restriction):
        """
        Compare architecture restriction (in list form) to arch of release
        being studied. Examples:
          ['i386']
          ['i386', 'amd64']
          ['!i386', '!amd64']

        arch_restriction: list of architecture specifications to test

        Returns current release-arch satisfies the restriction

        See http://www.debian.org/doc/debian-policy/ch-relationships.html

        Note: policy requires that either all restrictions are positive or all
        restrictions are negative. This code assumes that this is adhered to
        and does not check the architecture restriction list.
        """

        # if there are no restrictions then it is satisfied
        if not arch_restriction:
            return True

        if not type(arch_restriction) is list:
            raise TypeError("'arch' parameter must be a list")

        if arch_restriction[0].startswith('!'):
            # Policy requires all specifiers be positive or all be negative
            # strip all first characters to get the actual arch specified.
            for testarch in [a[1:] for a in arch_restriction]:
                if self.release.arch_applies(testarch):
                    return False
            return True
        else:
            for testarch in arch_restriction:
                if self.release.arch_applies(testarch):
                    return True
            return False

    def RelationSatisfied(self, rel):
        """Check if a relationship is satisfied in the current release
            rel: a Relationship object
            Return true if satisfied
        """
#        print "Checking relationship for '%s', '%s', '%s' on %s" % \
#                     (rel.package, rel.operator, rel.version, rel.arch)
        if not self.CheckRelationArch(rel.arch):
            #print "    doesn't apply"
            rel.archIgnore = True
            return True

        p = self.release.Package(rel.package,
                                 operator=rel.operator, version=rel.version)
        if not p.Found():
            # Virtual packages cannot satisfy versioned dependencies.
            # See §7.5 of Policy.
            # http://www.debian.org/doc/debian-policy/ch-relationships.html
            if not rel.isVersioned():
                rel.virtual = p.IsVirtual()
                rel.packagedata = p
                return rel.virtual
            else:
                return False
        #print p

        version = p.data['version']
        # see policy §7.1
        # http://www.debian.org/doc/debian-policy/ch-relationships.html
        relOK = True
        if rel.operator:
            # version from dep line
            depver = debian_support.Version(rel.version)
            # version in archive
            aver = debian_support.Version(version)
            #print "    versions comparison %s %s %s %s" % \
            #               (rel.package, aver, rel.operator, depver)
            if rel.operator == ">>":    # strictly greater than
                relOK = aver > depver
            elif rel.operator == ">=":  # greater than or equal to
                relOK = aver >= depver
            elif rel.operator == "=":   # equal to
                relOK = aver == depver
            elif rel.operator == "<=":  # less than or equal to
                relOK = aver <= depver
            elif rel.operator == "<<":  # strictly less than
                relOK = aver < depver
        if relOK:
            rel.packagedata = p
        return relOK


class InstallChecker(Checker):
    """
    Recursively check package dependencies to determine installability

    Typical usage:
        udd = Udd()
        release = udd.BindRelease(arch="i386",release="sid")
        checker = RelationChecker(release)
        if checker.CheckInstall('libc6'):
            ...
    """
    def Check(self, package=None, recommends=True, _level=0):
        """
        Check the installability of a package

        A check is run to see if all the package's Depends satisfiable and
        that each of these packages are themselves installable too. This
        recursive search is expensive to do against UDD and other tools like
        edos-debcheck are better for performing large-scale checks; this
        function is designed for occasional one-off checks of a package.
        Recommended packages can be included in the analysis if desired.

        package: name of the package (string)
        recommends: include Recommended packages in the analysis
        level: recursion level (private)

        returns: SolverHierarchy object for the installation or None
        if the package doesn't exist.
        """
        s = SolverHierarchy(package, _level)
        if _level == 0:
            self._checkInstallCache = {}

        if package in self._checkInstallCache:
            return
        self._checkInstallCache[package] = True
        s.depends = super(InstallChecker, self).Check(package, 'depends')
        assert(s.depends != None)

        if recommends:
            s.recommends = super(InstallChecker, self).Check(package, 'recommends')
        reltypes = ['depends']
        if recommends:
            reltypes.append('recommends')

        for reltype in reltypes:
            for relation in s.get(reltype).good:
                if not relation.virtual:
                    relation.status = self.Check(relation.satisfiedBy.package,
                                                recommends, _level + 1)
                else:
                    # virtual package requires separate handling; iterate
                    # over each of the providers until one is installable
                    for vpackage in relation.satisfiedBy.packagedata.ProvidersList():
                        status = self.Check(vpackage,
                                            recommends, _level + 1)
                        if status:
                            break
                    relation.status = status
        return s


class BuildDepsChecker(Checker):
    """
    Check the build-dependencies of a source package

    Typical usage:
        udd = Udd()
        release = udd.BindRelease(arch="i386",release="sid")
        checker = RelationChecker(release)
        if checker.CheckBuildDeps('eglibc'):
            ...
    """
    def Check(self, package=None, bdList=None, bdiList=None):
        """
        Check that the build-depends and build-depends-indep are satisfied
        for a package in the current release
            package: string source package name (or binary package name)
            bdList: RelationshipOptionsList of build-depends to check
            bdiList: RelationshipOptionsList of build-depends-indep to check
        Note that if package is specified, bdList and bdiList should not be
        specified.

            Returns a BuildDepStatus object for the relationships tested.
            Returns None if the package doesn't exist.
        """
        s = package
        if type(package) == str:
            s = self.release.Source(package)
        if not (s and s.Found()) and not (bdList or bdiList):
            raise ValueError("A valid package or bdList/bdiList missing")
        if not bdList and s:
            bdList = s.BuildDependsList()
        if not bdiList and s:
            bdiList = s.BuildDependsIndepList()
        bdstatus = self.CheckRelationshipOptionsList(bdList)
        bdistatus = self.CheckRelationshipOptionsList(bdiList)
        return BuildDepStatus(bdstatus, bdistatus)


class SolverHierarchy(object):
    """A hierarchy of package objects linked by package dependencies

    SolverHierarchy objects are designed to accumulate the package tree
    that is associated with the dependencies of a package.
    The hierarchy is able to store either just packages listed as hard
    dependencies ("depends" member) or additionally store recommended
    packages as well ("recommends" member).

    Typical usage:

    udd = Udd()
    release = udd.BindRelease(arch="i386",release="sid")
    status = RelationshipStatus()
    status.good.append(release.Package('perl'))
    status.bad.append(release.Package('python'))
    s = SolverHierarchy('dpkg')
    s.depends = status
    print s.depends

    Members:
        depends, recommends: RelationshipOptions
    """

    def __init__(self, package, level=0):
        """Create a level in a hierarchy

        package:    name of the package (string)
        level:      level number of this node in the hierarchy (integer)
        """
        self.depends = RelationshipStatus()
        self.recommends = RelationshipStatus()
        self.package = package
        self.level = level
        self._types = ['depends', 'recommends']
        self._last_level = True

    def get(self, name):
        """Programmatic access to a RelationshipStatus object

        e.g.: s.get('depends')
        """
        if name in self.__dict__ and name in self._types:
            return self.__dict__[name]

    def flatten(self):
        """Flatten a tree of checked package relationships

        The hierarchy is collapsed from the remote leaves back into the trunk
        leaving a list of packages that in the dependency tree.
        Packages that appear in both a "Depends" chain and a "Recommends" chain
        are de-duplicated in favour of the stronger dependency.

        A new SolverHierarchy is returned containing the lists of packages;
        the original object is unaltered.
        """
        # create a new SolverHierarchy object to contain the flattened tree
        s = SolverHierarchy(self.package, level=-1)
        s.depends.extend(self.depends)
        s.recommends.extend(self.recommends)

        for relation in self.depends.good:
            # squash all of depends tree into the recommends objects
            if relation.status:
                ps = relation.status.flatten()
                s.depends.extend(ps.depends)
                s.recommends.extend(ps.recommends)
        for relation in self.recommends.good:
            # squash all of recommends tree into the recommends objects
            # NB that includes the Depends of Recommends packages and they
            # are only dragged in through a weak dependency.
            if relation.status:
                ps = relation.status.flatten()
                s.recommends.extend(ps.depends)
                s.recommends.extend(ps.recommends)
        # 'bad' and 'unchecked' relations are handled by the recursive flatten

        # ensure that the tree-links are not present in the new hierarchy
#        for rel in "depends", "recommends":
#            for state in "good", "bad", "unchecked":
#                for r in s.get(rel).get(state):
#                    r.status = None

        if self.level == 0:
            # remove packages from the "Recommends" list that are already in
            # the "Depends" list; do the de-duping based on package name
            foundnames = []
            for relation in s.depends.good:
                assert(relation.satisfied)
                foundnames.append(relation.satisfiedBy.package)
            for relation in s.recommends.good:
                assert(relation.satisfied)
                if relation.satisfiedBy.package in foundnames:
                    s.recommends.good.remove(relation)
        return s

    def chains(self):
        """ Turn the hierarchy into a list of relationship chains

        The hierarchy:
                A
               / \
              B   C
        becomes [ [A, Depends(B)], [A, Recommends(C)] ]
        """
        newchains = DependencyChainList()
        def addchains(package, packchain):
            if not package.status:
                newchains.append(packchain)
                return

            nextchains = package.status.chains()
            if not nextchains:
                newchains.append(packchain)
                return

            for pchain in nextchains:
                pcclone = DependencyChain(chain=packchain)
                pcclone.extend(pchain)
                newchains.append(pcclone)

        for p in self.depends.good:
            packchain = DependencyChain(Depends(p.satisfiedBy.packagedata))
            addchains(p, packchain)
        for p in self.recommends.good:
            packchain = DependencyChain(Recommends(p.satisfiedBy.packagedata))
            addchains(p, packchain)
        if self.level == 0:
            newchains.set_base(self.package)
        return newchains

    def __str__(self):
        return unicode(self).encode("UTF-8")

    def __unicode__(self):
        """ Generate a unicode tree-like representation of the hierarchy """

        def indent(text, sep="  "):
            return u"".join(sep + line for line in text.splitlines(True))

        def strline(rlist, label, last=False):
            if self.level < 0:
                s = rlist.PackageSets()
                return u"%s:\n%s" % (label, indent(str(s), "  "))
            s = unicode(rlist)
            if s:
                tree_tee = u"├─"
                tree_trunk =  u"│"
                if last:
                    tree_tee = u"└─"
                    tree_trunk =  u" "
                return u"%s[%d] %s for %s:\n%s" % \
                            (tree_tee, self.level, label, self.package,
                                    indent(s, u"%s   " % tree_trunk))
        if self.level >= 0:
            for p in [ps for ps in self.depends.good if ps.status][:-1] + \
                     [ps for ps in self.recommends.good if ps.status][:-1]:
                    p.status._last_level = False
        s = []
        if self.depends:
            s.append(strline(self.depends, "Depends",
                             self._last_level and not self.recommends))
        if self.recommends:
            s.append(strline(self.recommends, "Recommends", self._last_level))
        return u"\n".join(s)
