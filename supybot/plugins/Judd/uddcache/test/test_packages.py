#!/usr/bin/env python
#
# Ultimate Debian Database query tool
#
# Test suite
#
###
#
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
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
###

""" Unit tests for packages """

from __future__ import unicode_literals

from uddcache.udd import Udd
from uddcache.packages import *

try:
    import unittest2 as unittest
except:
    import unittest


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.udd = Udd()

    def tearDown(self):
        self.udd = None

    def testRelease(self):
        """Test binding the release"""
        rd = Release(self.udd.psql)
        self.assertTrue(rd)
        rs = Release(self.udd.psql, release='sid')
        self.assertTrue(rs)
        ra = Release(self.udd.psql, arch='armhf')
        self.assertTrue(ra)
        rb = Release(self.udd.psql, release=['squeeze', 'squeeze-backports'])
        self.assertTrue(rb)


    def testPackage(self):
        """Test looking up an individual binary package"""
        rd = Release(self.udd.psql)
        self.assertTrue(rd.Package('libc6'))
        self.assertTrue(rd.Package('libc6').Found())
        self.assertFalse(rd.Package('ktikz').Found(), 'Check a package that is not in stable')

        rs = Release(self.udd.psql, release='sid')
        self.assertTrue(rs.Package('ktikz').Found())

        ra = Release(self.udd.psql, arch='armhf')
        self.assertFalse(ra.Package('libc0.1').Found(), 'Check a package that is not in this arch')

        rb = Release(self.udd.psql, release=['wheezy', 'wheezy-backports'])
        self.assertTrue(rb.Package('debhelper').Found())
        self.assertTrue(rb.Package('pepperflashplugin-nonfree').Found())

        rb = Release(self.udd.psql, release=['wheezy', 'wheezy-backports'], pins='illegal value')
        self.assertRaises(ValueError, rb.Package, 'debhelper')

        rb = Release(self.udd.psql, release=['wheezy', 'wheezy-backports'])
        self.assertTrue(rb.Package('debhelper').data['version'] > '8.0.0')
        rb = Release(self.udd.psql, release=['squeeze', 'squeeze-backports'], pins={'squeeze':2, 'squeeze-backports':1})
        self.assertTrue(rb.Package('debhelper').data['version'] == '8.0.0', 'Check pinning of package from stable')
        rb = Release(self.udd.psql, release=['squeeze', 'squeeze-backports'], pins={'no-such-release':2})
        self.assertTrue(rb.Package('debhelper').data['version'] > '8.0.0', 'Nonsense pinning ignored')

        rb = Release(self.udd.psql, release='squeeze')
        self.assertTrue(rb.Package('debhelper', version='7.0.0', operator='>>').Found())
        self.assertFalse(rb.Package('debhelper', version='8.0.0', operator='<<').Found())


    def testSource(self):
        """Test looking up an individual source package"""
        rd = Release(self.udd.psql, release='sid')
        self.assertTrue(rd.Source('glibc'))
        self.assertTrue(rd.Source('glibc').Found())
        self.assertRaises(PackageNotFoundError, rd.Source, 'nosuchpackage')
        self.assertTrue(rd.Source('libc6').Found())
        self.assertRaises(PackageNotFoundError, rd.Source, 'libc6', autoBin2Src=False)

    def testArchApplies(self):
        """Test matching arch names and wildcard archs"""
        rd = Release(self.udd.psql, release='sid', arch='i386')
        self.assertTrue(rd.arch_applies('i386'))
        self.assertTrue(not rd.arch_applies('amd64'))
        self.assertTrue(rd.arch_applies('linux-any'))
        self.assertTrue(rd.arch_applies('any-i386'))
        self.assertTrue(not rd.arch_applies('any-amd64'))
        self.assertTrue(not rd.arch_applies('kfreebsd-any'))

        rd = Release(self.udd.psql, release='sid', arch='kfreebsd-i386')
        self.assertTrue(rd.arch_applies('kfreebsd-i386'))
        self.assertTrue(not rd.arch_applies('i386'))
        self.assertTrue(not rd.arch_applies('linux-any'))
        self.assertTrue(rd.arch_applies('any-i386'))
        self.assertTrue(not rd.arch_applies('any-amd64'))
        self.assertTrue(rd.arch_applies('kfreebsd-any'))

    def testUnicode(self):
        rd = Release(self.udd.psql, release='sid', arch='i386')
        self.assertTrue(unicode(rd))
        rd.Package('libc6')
        self.assertTrue(unicode(rd))
        rd.Source('glibc')
        self.assertTrue(unicode(rd))


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.udd = Udd()

    def tearDown(self):
        self.udd = None

    def testPackage(self):
        """Test binding a package"""
        self.assertRaises(ValueError, Package, self.udd.psql)
        rs = Package(self.udd.psql, package="libc6")
        self.assertTrue(rs)
        self.assertTrue(rs.Found())
        rne = Package(self.udd.psql, package="libc0.1", arch='armhf')
        self.assertTrue(rne, "Test package that doesn't exist on specified arch")
        self.assertFalse(rne.Found(), "Test package that doesn't exist on specified arch")
        rne = Package(self.udd.psql, package="nodejs", release='wheezy')
        self.assertTrue(rne)
        self.assertFalse(rne.Found())
        rb = Package(self.udd.psql, package="nodejs", release=['wheezy', 'wheezy-backports'])
        self.assertTrue(rb)
        self.assertTrue(rb.Found())
        rnb = Package(self.udd.psql, package="youtube-dl", release=['wheezy'])
        self.assertTrue(rnb)
        self.assertFalse(rnb.Found())
        rne = Package(self.udd.psql, package="nosuchpackage")
        self.assertFalse(rne.Found())
        self.assertRaises(ValueError,  Package, self.udd.psql, package=rne)

    def testProviders(self):
        """Test searching for provided packages"""
        rm = Package(self.udd.psql, package="mail-transport-agent")
        self.assertTrue(len(rm.ProvidersList()), "Test rprovides for mail-transport-agent")
        rne = Package(self.udd.psql, package="nosuchpackage")
        self.assertFalse(len(rne.ProvidersList()), "Test rprovides for non-existent package")
        rne = Package(self.udd.psql, package="imagemagick")
        self.assertTrue(len(rne.ProvidersList()), "Test rprovides for real+virtual package")

    def testIsVirtual(self):
        """Test virtual package identification"""
        # pure virtual, many providers
        p = Package(self.udd.psql, package="mail-transport-agent")
        self.assertTrue(p.IsVirtual())
        # neither concrete nor virtual
        p = Package(self.udd.psql, package="no-such-package")
        self.assertFalse(p.IsVirtual())
        # concrete only
        p = Package(self.udd.psql, package="libc6")
        self.assertFalse(p.IsVirtual())
        # both concrete and virtual
        p = Package(self.udd.psql, package="imagemagick")
        self.assertTrue(p.IsVirtual())

    def testIsVirtualOnly(self):
        """Test purely virtual package identification"""
        # pure virtual, many providers
        p = Package(self.udd.psql, package="mail-transport-agent")
        self.assertTrue(p.IsVirtualOnly())
        # neither concrete nor virtual
        p = Package(self.udd.psql, package="no-such-package")
        self.assertFalse(p.IsVirtualOnly())
        # concrete only
        p = Package(self.udd.psql, package="libc6")
        self.assertFalse(p.IsVirtualOnly())
        # both concrete and virtual
        p = Package(self.udd.psql, package="imagemagick")
        self.assertFalse(p.IsVirtualOnly())

    def testIsAvailable(self):
        """Test package finding for concrete/virtual packges"""
        # pure virtual, many providers
        p = Package(self.udd.psql, package="mail-transport-agent")
        self.assertTrue(p.IsAvailable())
        # neither concrete nor virtual
        p = Package(self.udd.psql, package="no-such-package")
        self.assertFalse(p.IsVirtual())
        # concrete only
        p = Package(self.udd.psql, package="libc6")
        self.assertTrue(p.IsAvailable())
        # both concrete and virtual
        p = Package(self.udd.psql, package="imagemagick")
        self.assertTrue(p.IsAvailable())

    def testRelationEntry(self):
        """Test getting the relationships between packages"""
        p = Package(self.udd.psql, package="libc6", release='sid')
        self.assertFalse(p.RelationEntry('pre_depends'), "Test package with no dependencies")
        self.assertFalse(p.PreDepends(), "Test package with no dependencies")
        self.assertTrue(p.RelationEntry('depends'), "Test package with dependencies")
        self.assertTrue(p.Depends(), "Test package with dependencies")
        self.assertTrue(p.RelationEntry('suggests'), "Test package with dependencies")
        self.assertTrue(p.Suggests(), "Test package with dependencies")
        self.assertTrue(p.RelationEntry('conflicts'), "Test package with dependencies")
        self.assertTrue(p.Conflicts(), "Test package with dependencies")
        self.assertTrue(p.RelationEntry('breaks'), "Test package with dependencies")
        self.assertTrue(p.Breaks(), "Test package with dependencies")
        self.assertFalse(p.RelationEntry('enhances'), "Test package with no dependencies")
        self.assertFalse(p.Enhances(), "Test package with no dependencies")

        p = Package(self.udd.psql, package="ktikz", release='sid')
        self.assertTrue(p.RelationEntry('recommends'), "Test package with dependencies")
        self.assertTrue(p.Recommends(), "Test package with dependencies")

        p = Package(self.udd.psql, package="dpkg", release='sid')
        self.assertTrue(p.RelationEntry('pre_depends'), "Test package with dependencies")
        self.assertTrue(p.PreDepends(), "Test package with dependencies")
        self.assertTrue(p.RelationEntry('breaks'), "Test package with dependencies")
        self.assertTrue(p.Breaks(), "Test package with dependencies")
        self.assertTrue(p.RelationEntry('replaces'), "Test package with dependencies")
        self.assertTrue(p.Replaces(), "Test package with dependencies")

        p = Package(self.udd.psql, package="libc6", release='sid')
        self.assertTrue(p.RelationEntry('replaces'), "Test package with dependencies")
        self.assertTrue(p.Replaces(), "Test package with dependencies")

        p = Package(self.udd.psql, package="nosuchpackage")
        self.assertRaises(LookupError, p.RelationEntry, 'depends')

        p = Package(self.udd.psql, package="libc6")
        self.assertRaises(KeyError, p.RelationEntry, 'nosuchrelation')

    def testRelationEntryList(self):
        """Test getting the relationships between packages as a structure"""
        p = Package(self.udd.psql, package="libc6", release='sid')
        self.assertFalse(len(p.RelationshipOptionsList('pre_depends')), "Test package with dependencies")
        self.assertFalse(len(p.PreDependsList()), "Test package with dependencies")
        self.assertTrue(len(p.RelationshipOptionsList('depends')), "Test package with dependencies")
        self.assertTrue(len(p.DependsList()), "Test package with dependencies")
        self.assertTrue(len(p.RelationshipOptionsList('suggests')), "Test package with dependencies")
        self.assertTrue(len(p.SuggestsList()), "Test package with dependencies")
        self.assertTrue(len(p.RelationshipOptionsList('conflicts')), "Test package with dependencies")
        self.assertTrue(len(p.ConflictsList()), "Test package with dependencies")
        self.assertFalse(len(p.RelationshipOptionsList('enhances')), "Test package with no dependencies")
        self.assertFalse(len(p.EnhancesList()), "Test package with no dependencies")
        self.assertTrue(len(p.RelationshipOptionsList('breaks')), "Test package with no dependencies")
        self.assertTrue(len(p.BreaksList()), "Test package with no dependencies")
        self.assertTrue(len(p.RelationshipOptionsList('replaces')), "Test package with no dependencies")
        self.assertTrue(len(p.ReplacesList()), "Test package with no dependencies")

        p = Package(self.udd.psql, package="ktikz", release='sid')
        self.assertTrue(len(p.RelationshipOptionsList('recommends')), "Test package with dependencies")
        self.assertTrue(len(p.RecommendsList()), "Test package with dependencies")

        p = Package(self.udd.psql, package="nosuchpackage")
        self.assertRaises(LookupError, p.RelationshipOptionsList, 'depends')

        p = Package(self.udd.psql, package="libc6")
        self.assertRaises(KeyError, p.RelationshipOptionsList, 'nosuchrelation')

    def testUnicode(self):
        p = Package(self.udd.psql, package="libc6", release='sid')
        self.assertTrue(unicode(p))
        p = Package(self.udd.psql, package="no-such-package", release='sid')
        self.assertTrue(unicode(p))


class SourcePackageTests(unittest.TestCase):
    def setUp(self):
        self.udd = Udd()

    def tearDown(self):
        self.udd = None

    def testPackage(self):
        """Test binding a package"""
        self.assertRaises(ValueError, Package, self.udd.psql)
        rs = SourcePackage(self.udd.psql, package="glibc", release='sid')
        self.assertTrue(rs)
        self.assertTrue(rs.Found())
        rne = SourcePackage(self.udd.psql, package="nosuchpackage")
        self.assertFalse(rne.Found())

    def testBinaries(self):
        """Test listing the binary packages compiled by a source package"""
        ps = SourcePackage(self.udd.psql, package="glibc", arch="i386", release="sid")
        self.assertTrue(ps.Binaries())
        pne = SourcePackage(self.udd.psql, package="nosuchpackage")
        self.assertFalse(pne.Binaries())

    def testBuildDeps(self):
        """Test listing the build-dep and build-dep-indep packages"""
        ps = SourcePackage(self.udd.psql, package="glibc", arch="i386", release="sid")
        self.assertTrue(ps.BuildDepends())
        self.assertTrue(ps.BuildDependsIndep())
        self.assertTrue(ps.BuildDependsList())
        self.assertTrue(ps.BuildDependsIndepList())
        # package has no build-deps-indep
        ps = SourcePackage(self.udd.psql, package="perl", arch="i386", release="sid")
        self.assertFalse(ps.BuildDependsIndep())
        self.assertFalse(ps.BuildDependsIndepList())


class PackageNotFoundErrorTests(unittest.TestCase):
    def testInit(self):
        self.assertTrue(PackageNotFoundError("packagename"))

    def testUnicode(self):
        e = PackageNotFoundError("packagename")
        self.assertTrue("packagename" in unicode(e))

###########################################################
if __name__ == "__main__":
    unittest.main()
