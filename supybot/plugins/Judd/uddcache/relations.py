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

import re
try:
    from debian import debian_support
except:
    from debian_bundle import debian_support


class Relationship(object):
    """Representation of a single package relationship

    Accepts either a textual representation of relationship or
    kwargs to describe the relationship. A set of these objects
    may form part of a RelationshipOptions object that represents
    a set of options in a declared relationship e.g. "Depends: foo | bar"

    relation: textual representation such as "foo", "foo (>> 1.2)",
                "foo (>> 1.2) [amd64]"
    package:  package name part of the relationship
    operator: operator part of the relationship (<<, <=, = >=, >>)
    version:  version part of the relationship
    arch:     architecture part of the relationship (either a list
                of valid architecture keywords e.g.
                ['amd64', 'i386'], or a space separated string of
                keywords e.g. 'amd64 i386')

    Typical usage:
        rel = Relationship(relation="libc6")
        rel = Relationship(relation="libc6 (>= 1.2.3)")
        rel = Relationship(package="libc6", operator=">=", version="1.2.3")
    """
    def __init__(self, **kwargs):
        self.relation = kwargs.get('relation', None)
        """ textual representation of the entire relationship"""
        self.package = kwargs.get('package', None)
        """ package name from relationship as a string """
        self.operator = kwargs.get('operator', None)
        """ version operator from the relationship as a string """
        self.version = kwargs.get('version', None)
        """ version string from the relationship as a string """
        self.arch = self._archsplit(kwargs.get('arch', None))
        """ architecture specification for the relationship as a list """
        self.archIgnore = False
        """ boolean: this relationship is to be ignored in this architecture"""
        self.virtual = False
        """ boolean: this relationship is satisfied only by virtual packages"""
        self.packagedata = None
        """ For relations satisfied by real packages: the Package object; for
            "virtual"  relationships, a list of Providers"""

        if self.relation and self.package:
            raise ValueError("Cannot specify both the textual relation "
                        "and the components as keyword arguments")
        if (self.operator and not self.version) or \
                (not self.operator and self.version):
            raise ValueError("If one of 'operator' or 'version' keyword "
                            "arguments is specified, both must be given")
        if self.relation:
            self._ParseRelation(self.relation)
        self._checkOperatorSyntax()

    def _ParseRelation(self, relationship):
        #print "checking item %s" % item
        m = re.match(r"""(?x)
                  ^\s*
                  (?P<package>[\w\d.+-]+)
                  (?:
                    \s*
                    \(\s*
                      (?P<operator>\>\>|\>=|=|\<\<|\<=)\s*(?P<version>[^\s]+)
                    \s*\)
                  )?
                  (?:
                    \s*
                    \[\s*
                      (?P<arch>[^]]+)
                    \s*\]
                  )?
                  \s*$
                  """, relationship)
        if not m:
            raise ValueError("Couldn't parse the relationship expression")
        self.package = m.group('package')
        self.operator = m.group('operator')
        self.version = m.group('version')
        self.arch = self._archsplit(m.group('arch'))

    def isVersioned(self):
        return self.operator != None

    def _checkOperatorSyntax(self):
        ops = ['>>', '>=', '=', '<=', '<<']
        if self.operator and (not self.operator in ops):
            raise ValueError("Illegal operator found in relationship: %s" % \
                             self.operator)

    def _archsplit(self, value):
        """ split up whitespace separated into list of archs accept lists"""
        if value and type(value) is str:
            return re.split(r"\s+", value.strip())
        elif type(value) is list:
            return value
        else:
            return []

    def __str__(self):
        if self.relation:
            return self.relation
        else:
            return "%s (%s %s) [%s]" % \
              (self.package, self.operator, self.version, " ".join(self.arch))


class RelationshipOptions(list):
    """
    List of alternatives that form a single package relationship.

    Note: this will commonly contain only one entry in the list
    from a "Depends: foo" line generating a single entry for "foo".
    A line like "Depends: foo | bar" will create two entries in
    this list, one for each of "foo" and "bar".

    Typical usage:
    rel = RelationshipOptions("libc6")
    rel = RelationshipOptions("default-mta | mail-transport-agent")
    rel = RelationshipOptions("dpkg (>> 1.15.4)")
    """
    def __init__(self, options):
        """Create a list of Relationship objects that represent a
        single package relationship, parsing the standard
        'foo | bar' format for the option syntax.

        options: text representation of the relationship, for
            example any one of the following:
            'foo'
            'foo | bar'
            'foo (>> 1.2-3)'
        """
        self.relation = options   # text representation
        self.satisfiedBy = None   # Relationship alternative that satisfies
        self.satisfied = False  # relationship is satisfied (boolean)
        self.virtual = False  # used virtual package to satisfy
        self.package = None   # Package object that satisfied
        self.status = None   # Extended status (SolverHierarchy)
        list.__init__(self)
        for rel in self._SplitOptions(options):
            #print "found rel=%s" % rel
            self.append(Relationship(relation=rel))

    def _SplitOptions(self, item):
        return re.split(r"\s*\|\s*", item)

    def __str__(self):
        return self.relation


class RelationshipOptionsList(list):
    """
    List of RelationshipOptions objects

    Each RelationshipOptions object in the list is an individual relationship
    declared by the package (i.e. "libc6 (>= 2.3)" or "apache2 | httpd". This
    list of objects represents all of these relationships (e.g. the entire
    Depends entry for the package).
    """

    def ReleaseMap(self):
        """
        Convert the list of relationship objects into a dictionary
        of releases with a list of package objects in each release

        Packages that have not been resolved by the resolver are
        added to a special "unresolved" release. Relationships
        that are resolved by virtual packages are placed into
        the "virtual" release. Dependencies that are irrelevant
        to the current architecture are mapped to the "archignore" release
        """
        releases = {}
        for i in self.__iter__():
            #print "%s : %s" % (type(i), i)
            # map unresolved packages to a dummy release
            r = "unresolved"
            if i.satisfied:
                if i.archIgnore:
                    # put deps for the wrong arch somewhere else
                    # print "ARCHIGNORE DEP %s" % i
                    r = "archignore"
                elif i.virtual:
                    # stick virtual relationships into a separate release too
                    r = "virtual"
                else:
                    #print "%s : %s" % (type(i), i)
                    #print "%s : %s" % (type(i.satisfiedBy), i.satisfiedBy)
                    r = i.satisfiedBy.packagedata.data['release']
            if not r in releases:
                releases[r] = []
            releases[r].append(i)
        return releases

    def PackageSet(self):
        """Create a set representing the list but not containing duplicates

        The list of RelationshipOptions objects is scanned and the package that
        actually satisfied the relationship is added to the set. If the same
        package is requested multiple times then this process will de-duplicate
        the list.

        If the RelationshipOptions object has not been run through the resolver
        hence it is not know which option will actually satisfy the
        relationship, the raw relation is added to the set instead.
        FIXME: is this the desired behaviour?
        """
        d = set()
        for o in self:
            #print o
            if o.satisfiedBy:
                d.add(o.satisfiedBy.package)
            else:
                d.add(o.relation)
        return d

    def __str__(self):
        #print "making output %d" % len(self)
        return ", ".join([str(x) for x in self.__iter__()])


class PackageLists(object):
    """
    Lists of packages as categorised into lists given pre-determined names.

    Example:
        l = PackageLists(['good', 'bad'])
        l.good.append('foo')
    """

    def __init__(self, fields, generator=list):
        """ construct the lists and the accessors to them

            fields: a list of field names (must be valid python variable names)
            generator: function to use to generate the lists
        """
        self._fields = fields
        [self.__setattr__(name, generator()) for name in fields]

    def get(self, name):
        return getattr(self, name)

    def set(self, name, value):
        # print "setting %s = %s" %(name, value)
        return setattr(self, name, value)

#    def __getattr__(self, name):
#        print "Using __getattr__ %s:%d" %(__FILE__, __LINE__)
#        try:
#            return self.__dict__[name]
#        except KeyError:
#            raise AttributeError(name)

    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)

    def __str__(self):
        def strline(label, rlist):
            s = ", ".join(sorted(rlist))
            if s:
                return "%s: %s" % (label, s)

        s = [strline(name.title(), self.get(name)) for name in self._fields]
        return "\n".join(filter(None, s))

    def __len__(self):
        total = 0
        for field in self._fields:
            total += len(self.get(field))
        return total

    def __nonzero__(self):
        return len(self) > 0


class RelationshipStatus(PackageLists):
    """Package lists reflecting whether dependencies are satisfied

    Typical usage:

    status = RelationshipStatus()
    status.good.extend(['perl', 'bash'])
    status.bad.extend(['python', 'ruby'])
    print status.PackageSets
    """
    def __init__(self):
        PackageLists.__init__(self, ['good', 'bad', 'unchecked'],
                                RelationshipOptionsList)

    def PackageSets(self):
        """ Return de-duplicated packages sets for the package lists

        Collapse the lists of package options in this object that may contain
        numerous requests for the same package perhaps due to various different
        packages in a dependency chain each requesting the package.

        The de-duplication of the lists is performed by converting them into
        python sets of Package objects.
        """
        s = PackageLists(self._fields, set)
        [s.set(r, self.get(r).PackageSet()) for r in self._fields]
        return s

#    def CheckVersionedDeps(self):
#        d = {}
#        gops = [">>", ">="]?
#            if d.has_key(o.satisfiedBy):
#                v1 = d[o.satisfiedBy].version
#                op1 = d[o.satisfiedBy].operator
#                v2 = o.version
#                op2 = o.operator
#                if op1 in lops and op2 in lops:
#
#                elif op1 in gops and op2 in gops:
#
#                elif op1 == "=" and op2 == "=":
#
#                else:
#
#            else:
#                d[o.satisfiedBy] = copy.deepcopy(o)
#

    def extend(self, otherRelStatus):
        """Merge a second RelationshipStatus object into this one

        The contents of the given RelationshipStatus object are merged into
        this one, with each of the "good", "bad", and "unchecked" fields
        being extended by the given statuses.
        """
        [self.get(r).extend(otherRelStatus.get(r)) for r in self._fields]

    def swap(self):
        """Swap the good and bad entries around"""
        temp = self.bad
        self.bad = self.good
        self.good = temp

    def satisfied(self):
        """Check if there are any 'bad' or 'unchecked' relationships"""
        # print "Satisfied?: %d %s" % (len(self.bad), len(self.bad)==0)
        return len(self.unchecked) + len(self.bad) == 0

    def __str__(self):
        """Convert to string form"""
        return unicode(self).encode("UTF-8")

    def __unicode__(self):
        """Convert to unicode form"""
        def strline(label, rlist):
            #print "making string from %s" %label
            s = str(rlist)
            if s:
                return "%s: %s" % (label, s)

        s = [strline(u"Good", self.good),
             strline(u"Bad", self.bad),
             strline(u"Unchecked", self.unchecked)]
        ps = []
        for p in self.good:
            if p.status:
                ps.append(unicode(p.status))
        s.extend(ps)
        return "\n".join(filter(None, s))

    def __nonzero__(self):
        """True (non-zero) if there are any packages in the list at all"""
        return len(self.good) + len(self.unchecked) + len(self.bad) > 0


class BuildDepStatus(object):
    """Contains the status of the build-dependencies of a package

    Both the Build-Depends and Build-Depends-Indep data can be found in this
    object.
    """
    def __init__(self, bd=None, bdi=None):
        if bd != None:
            self.bd = bd
        else:
            self.bd = RelationshipStatus()
        if bdi != None:
            self.bdi = bdi
        else:
            self.bdi = RelationshipStatus()

    def AllFound(self):
        """Check that all build-dependencies are satisified"""
        return self.bd.satisfied() and self.bdi.satisfied()

    def ReleaseMap(self):
        """Prepare a mapping of which releases the packages come from

        When considering a collection of build-dependencies for a package,
        particularly in the case of backporting a package, map the packages
        back to the releases that would provide them to provide the requisite
        versioned build-deps.
        """
        bdm = self.bd.good.ReleaseMap()
        bdim = self.bdi.good.ReleaseMap()
        releases = dict([(k, []) for k in bdm.keys() + bdim.keys()])

        [releases[r].extend(bdm[r]) for r in bdm.keys()]
        [releases[r].extend(bdim[r]) for r in bdim.keys()]
#        for r in m.keys():
#            releases[r] = m[r]
#        m = self.bdi.good.ReleaseMap()
#        for r in m.keys():
#            if not r in releases:
#                releases[r] = []
#            releases[r].extend(m[r])
        return releases

    def __str__(self):
        """Compile a string listing of the build-dependencies"""
        return "Build-Depends: %s\nBuild-Depends-Indep: %s\n" % \
                (self.bd, self.bdi)
