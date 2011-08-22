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
import psycopg2
import psycopg2.extras
from psycopg2.extensions import adapt
from relations import *


class Release(object):
    """ Class that represents the contents of a release
    i.e lists of binary and source packages """
    def __init__(self, dbconn, arch="i386", release="lenny", pins=None):
        self.dbconn = dbconn
        self.arch = arch
        if type(release) is tuple:
            self.release = release
        elif type(release) is list:
            self.release = tuple(release)
        else:
            self.release = (release,)
        self.pins = pins
        self.cache = {}
        self.scache = {}

    def Package(self, package, version=None, operator=None):
        """Look up a binary package by name in the current release.
            package: name of the package (string)
            returns Package object
        """
        phash = self._mkpackagehash(package, operator, version)
        if not phash in self.cache:
            self.cache[phash] = Package(self.dbconn, arch=self.arch, \
                                  release=self.release, package=package, \
                                  pins=self.pins,
                                  version=version, operator=operator)
        return self.cache[phash]

    def Source(self, package, autoBin2Src=True, version=None, operator=None):
        """Look up a source package by name in the current release.
            package: name of the package (string)
            autoBin2Src: (default true) convert names of binary packages to
                            source packages automatically if needed
            returns Package object
        """
        phash = self._mkpackagehash(package, operator, version)
        if not phash in self.scache:
            self.scache[phash] = SourcePackage(self.dbconn, arch=self.arch, \
                                  release=self.release, package=package,
                                  pins=self.pins,
                                  version=version, operator=operator)
            if autoBin2Src and not self.scache[phash].Found():
                p = self.bin2src(package)
                if p:
                    return self.Source(p, False)
        return self.scache[phash]

    def bin2src(self, package):
        """Returns the source package for a given binary package"""
        c = self.dbconn.cursor()
        c.execute(r"""SELECT source
                      FROM packages
                      WHERE package=%(package)s
                        AND release IN %(release)s LIMIT 1""",
                   dict(package=package,
                         release=self.release))
        row = c.fetchone()
        if row:
            return row[0]
        else:
            return

    def arch_applies(self, proposed):
        def kern_arch_split(archspec):
            if '-' in archspec:
                return archspec.split("-")
            else:
                return ("linux", archspec)

        if proposed == self.arch or proposed == "all":
            return True

        (pkern, parch) = kern_arch_split(proposed)
        (skern, sarch) = kern_arch_split(self.arch)

        if pkern == "any":
            return sarch == parch
        if parch == "any":
            return skern == pkern
        return parch == sarch and pkern == skern

    def _mkpackagehash(self, package, operator, version):
        return "%s|%s|%s" % (package, operator, version)

    def __str__(self):
        return "Release: %s.\n" \
                "\t%d binary packages and %d source packages in cache." % \
                        (self.release, len(self.cache), len(self.scache))


class AbstractPackage(object):
    fields = ['*']
    table = ''
    column = ''
    pins = []
    data = []

    def __init__(self, dbconn, arch="i386", release="lenny", package=None,
                 pins=None, version=None, operator=None):
        """
        Bind a specified binary or source package.

        A single release or a list or tuple of releases can be used. If more
        than one release is given, a set of pins giving the priority of the
        different releases in searching for packages can be specified. The pins
        should be a dict of releasename => pin value where higher values are
        preferred. In the absence of any specified pins, all releases are
        treated equally, meaning that the most recent package version will be
        chosen.

        Note that the "pinning" used here is a very simple rank order not the
        sophisticated system used by apt as described in apt_preferences(5).
        """
        if not package:
            raise ValueError("Package name not specified")
#        if type(package) is Package:
#            return package
        if not type(package) is str:
            raise ValueError("What did you do to 'package'? It was a %s" % \
                                type(package))
        self.dbconn = dbconn
        self.arch = arch
        if type(release) is tuple:
            self.release = release
        elif type(release) is list:
            self.release = tuple(release)
        else:
            self.release = (release,)
        self.package = package
        if pins and not type(pins) is dict:
            raise ValueError("List of pins must be a dict mapping the "
                                "release name to its relative importance.")
        self.pins = pins
        self.version = version
        self.operator = operator
        self._Fetch()

    def _Fetch(self):
        c = self.dbconn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        f = ','.join(self.fields)
        pin = ''
        if self.pins and self.release:
            pin = "pin DESC, "
            cases = ["WHEN release = %s THEN %s" % \
                        (adapt(r), adapt(self.pins[r])) \
                            for r in self.pins.keys()]
            f += ", CASE %s ELSE 0 END AS pin" % ' '.join(cases)
        verwhere = ""
        if self.version and self.operator:
            verwhere = "AND version %s debversion(%s)" % \
                        (self.operator.replace('>>', '>').replace('<<', '<'),
                            adapt(self.version))
        c.execute(r"""SELECT """ + f + """
                      FROM """ + self.table + """
                      WHERE """ + self.column + """=%(package)s
                        AND (architecture='all' OR architecture=%(arch)s)
                        AND release IN %(release)s """ + verwhere + """
                      ORDER BY """ + pin + """version DESC
                      LIMIT 1""",
                   dict(package=self.package,
                         arch=self.arch,
                         release=self.release))
        self.data = c.fetchone()

    def Found(self):
        '''Does the package exist in the database for the release specified?

        For binary packages this is equivalent to:
            "Is the package a real package?"
        (returns false for packages that are only virtual packages)'''
        return self.data != None

    def RelationEntry(self, relation, combinePreDepends=True):
        if not self.Found():
            raise LookupError("Requested package does not exist")
        if relation == 'depends' and combinePreDepends:
            rs = [self.data['depends'], self.data['pre_depends']]
            return ",".join(filter(None, rs))
        return self.data[relation]

    def RelationshipOptionsList(self, relation, combinePreDepends=True):
        rels = RelationshipOptionsList()
        l = self.RelationEntry(relation, combinePreDepends)
        if l:
            for r in re.split(r"\s*,\s*", l):
                roptions = RelationshipOptions(r)
                rels.append(roptions)
        return rels


class Package(AbstractPackage):
    def __init__(self, dbconn, arch="i386", release="lenny", package=None,
                 pins=None, version=None, operator=None):
        """
        Bind a specified binary package from a releases, list of releases
        or tuple of releases

        """
        self.table = 'packages'
        self.column = 'package'
        self._ProvidersList = None
        self.installable = None
        AbstractPackage.__init__(self, dbconn, arch, release, package,
                                 pins=pins, version=version, operator=operator)

    def IsVirtual(self):
        """Test if the package is a virtual package.

        Tests to see if any package Provides the current package
        """
        return len(self.ProvidersList()) > 0

    def IsVirtualOnly(self):
        """Test if the package is a (purely) virtual package."""
        return not self.Found() and self.IsVirtual()

    def IsAvailable(self):
        return self.Found() or self.IsVirtual()

    def ProvidersList(self):
        if self._ProvidersList == None:
            # remove all characters from the package name that aren't legal in
            # a package name i.e. not in:
            #    a-z0-9-.+
            # see §5.6.1 of Debian Policy "Source" for details.
            # http://www.debian.org/doc/debian-policy/ch-controlfields.html#s-f-Source
            #
            # \m is start word boundary, \M is finish word boundary
            # (but - in package name is a word boundary)
            # \A is start string,        \Z is finish string
            # http://www.postgresql.org/docs/8.3/static/functions-matching.html
            packagere = r"(?:\A|[, ])%s(?:\Z|[, ])" % \
                        re.escape(re.sub(r"[^a-z\d\-+.]", "", self.package))
            # print packagere
            c = self.dbconn.cursor()
            c.execute(r"""SELECT DISTINCT package
                          FROM packages
                          WHERE provides ~ %(package)s
                            AND (architecture='all' OR architecture=%(arch)s)
                            AND release IN %(release)s""",
                      dict(package=packagere,
                            arch=self.arch,
                            release=self.release))
            pkgs = []
            for row in c.fetchall():
                pkgs.append(row[0])
            self._ProvidersList = pkgs
        return self._ProvidersList

    def PreDepends(self):
        return self.RelationEntry('pre_depends')

    def PreDependsList(self):
        return self.RelationshipOptionsList('pre_depends')

    def Depends(self, combinePreDepends=True):
        return self.RelationEntry('depends', combinePreDepends)

    def DependsList(self, combinePreDepends=True):
        return self.RelationshipOptionsList('depends', combinePreDepends)

    def Recommends(self):
        return self.RelationEntry('recommends')

    def RecommendsList(self):
        return self.RelationshipOptionsList('recommends')

    def Suggests(self):
        return self.RelationEntry('suggests')

    def SuggestsList(self):
        return self.RelationshipOptionsList('suggests')

    def Enhances(self):
        return self.RelationEntry('enhances')

    def EnhancesList(self):
        return self.RelationshipOptionsList('enhances')

    def Conflicts(self):
        return self.RelationEntry('conflicts')

    def ConflictsList(self):
        return self.RelationshipOptionsList('conflicts')

    def Breaks(self):
        return self.RelationEntry('breaks')

    def BreaksList(self):
        return self.RelationshipOptionsList('breaks')

    def Replaces(self):
        return self.RelationEntry('replaces')

    def ReplacesList(self):
        return self.RelationshipOptionsList('replaces')

    def __str__(self):
        return "Package %s on %s in release %s" % \
            (self.package, self.arch, self.release)


class SourcePackage(AbstractPackage):
    def __init__(self, dbconn, arch="i386", release="lenny", package=None,
                 pins=None, version=None, operator=None):
        #self.fields = ['build_depends', 'build_depends_indep', 'version']
        self.table = 'sources'
        self.column = 'source'
        #self.autobin2src = kwargs.get('bin2src', True)
        AbstractPackage.__init__(self, dbconn, arch, release, package,
                                 pins=pins, version=version, operator=operator)

    def _Fetch(self):
        c = self.dbconn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        f = ','.join(self.fields)
        c.execute(r"""SELECT """ + f + """
                      FROM """ + self.table + """
                      WHERE """ + self.column + """=%(package)s
                        AND release IN %(release)s
                      ORDER BY version DESC
                      LIMIT 1""",
                   dict(package=self.package,
                         release=self.release))
        self.data = c.fetchone()

    def Binaries(self):
        c = self.dbconn.cursor()
        c.execute(r"""SELECT DISTINCT package
                      FROM packages
                      WHERE source=%(package)s
                        AND release IN %(release)s""",
                   dict(package=self.package,
                         arch=self.arch,
                         release=self.release))
        pkgs = []
        for row in c.fetchall():
            pkgs.append(row[0])
        return pkgs

    def BuildDepends(self):
        return self.RelationEntry('build_depends')

    def BuildDependsList(self):
        return self.RelationshipOptionsList('build_depends')

    def BuildDependsIndep(self):
        return self.RelationEntry('build_depends_indep')

    def BuildDependsIndepList(self):
        return self.RelationshipOptionsList('build_depends_indep')
