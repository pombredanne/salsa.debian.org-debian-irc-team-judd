#!/usr/bin/python
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

from uddcache.udd import Udd
from uddcache.packages import *
import unittest2 as unittest


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.udd = Udd()

    def testRelease(self):
        """Test binding the release"""
        rd = Release(self.udd.psql)
        self.assert_(rd)
        rs = Release(self.udd.psql, release='sid')
        self.assert_(rs)
        ra = Release(self.udd.psql, arch='ia64')
        self.assert_(ra)
        rb = Release(self.udd.psql, release=['lenny', 'lenny-backports'])
        self.assert_(rb)
        rb = Release(self.udd.psql, release=('lenny', 'lenny-backports'))
        self.assert_(rb)


    def testPackage(self):
        """Test looking up an individual binary package"""
        rd = Release(self.udd.psql)
        self.assert_(rd.Package('libc6'))
        self.assert_(rd.Package('libc6').Found())
        self.assertFalse(rd.Package('ktikz').Found(), 'Check a package that is not in stable')

        rs = Release(self.udd.psql, release='sid')
        self.assert_(rs.Package('ktikz').Found())

        ra = Release(self.udd.psql, arch='ia64')
        self.assertFalse(ra.Package('libc6').Found(), 'Check a package that is not in this arch')

        rb = Release(self.udd.psql, release=['lenny', 'lenny-backports'])
        self.assert_(rb.Package('debhelper').Found())
        self.assert_(rb.Package('flashplugin-nonfree').Found())

        rb = Release(self.udd.psql, release=['squeeze', 'squeeze-backports'], pins='illegal value')
        self.assertRaises(ValueError, rb.Package, 'debhelper')

        rb = Release(self.udd.psql, release=['squeeze', 'squeeze-backports'])
        self.assert_(rb.Package('debhelper').data['version'] > '8.0.0')
        rb = Release(self.udd.psql, release=['squeeze', 'squeeze-backports'], pins={'squeeze':2, 'squeeze-backports':1})
        self.assert_(rb.Package('debhelper').data['version'] == '8.0.0', 'Check pinning of package from stable')
        rb = Release(self.udd.psql, release=['squeeze', 'squeeze-backports'], pins={'no-such-release':2})
        self.assert_(rb.Package('debhelper').data['version'] > '8.0.0', 'Nonsense pinning ignored')

        rb = Release(self.udd.psql, release='squeeze')
        self.assert_(rb.Package('debhelper', version='7.0.0', operator='>>').Found())
        self.assertFalse(rb.Package('debhelper', version='8.0.0', operator='<<').Found())


    def testSource(self):
        """Test looking up an individual source package"""
        rd = Release(self.udd.psql, release='sid')
        self.assert_(rd.Source('eglibc'))
        self.assert_(rd.Source('eglibc').Found())
        self.assertFalse(rd.Source('nosuchpackage').Found())
        self.assert_(rd.Source('libc6').Found())
        self.assertFalse(rd.Source('libc6', autoBin2Src=False).Found())

    def testArchApplies(self):
        """Test matching arch names and wildcard archs"""
        rd = Release(self.udd.psql, release='sid', arch='i386')
        self.assert_(rd.arch_applies('i386'))
        self.assert_(not rd.arch_applies('amd64'))
        self.assert_(rd.arch_applies('linux-any'))
        self.assert_(rd.arch_applies('any-i386'))
        self.assert_(not rd.arch_applies('any-amd64'))
        self.assert_(not rd.arch_applies('kfreebsd-any'))

        rd = Release(self.udd.psql, release='sid', arch='kfreebsd-i386')
        self.assert_(rd.arch_applies('kfreebsd-i386'))
        self.assert_(not rd.arch_applies('i386'))
        self.assert_(not rd.arch_applies('linux-any'))
        self.assert_(rd.arch_applies('any-i386'))
        self.assert_(not rd.arch_applies('any-amd64'))
        self.assert_(rd.arch_applies('kfreebsd-any'))

    def testStr(self):
        rd = Release(self.udd.psql, release='sid', arch='i386')
        self.assert_(str(rd))
        rd.Package('libc6')
        self.assert_(str(rd))
        rd.Source('eglibc')
        self.assert_(str(rd))


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.udd = Udd()

    def testPackage(self):
        """Test binding a package"""
        self.assertRaises(ValueError, Package, self.udd.psql)
        rs = Package(self.udd.psql, package="libc6")
        self.assert_(rs)
        self.assert_(rs.Found())
        rne = Package(self.udd.psql, package="libc6", arch='ia64')
        self.assert_(rne, "Test package that doesn't exist on specified arch")
        self.assertFalse(rne.Found(), "Test package that doesn't exist on specified arch")
        rne = Package(self.udd.psql, package="latexdraw", release='lenny')
        self.assert_(rne)
        self.assertFalse(rne.Found())
        rb = Package(self.udd.psql, package="flashplugin-nonfree", release=['lenny', 'lenny-backports'])
        self.assert_(rb)
        self.assert_(rb.Found())
        rnb = Package(self.udd.psql, package="flashplugin-nonfree", release=['lenny'])
        self.assert_(rnb)
        self.assertFalse(rnb.Found())
        rne = Package(self.udd.psql, package="nosuchpackage")
        self.assertFalse(rne.Found())
        self.assertRaises(ValueError,  Package, self.udd.psql, package=rne)

    def testProviders(self):
        """Test searching for provided packages"""
        rm = Package(self.udd.psql, package="mail-transport-agent")
        self.assert_(len(rm.ProvidersList()), "Test rprovides for mail-transport-agent")
        rne = Package(self.udd.psql, package="nosuchpackage")
        self.assertFalse(len(rne.ProvidersList()), "Test rprovides for non-existent package")
        rne = Package(self.udd.psql, package="imagemagick")
        self.assert_(len(rne.ProvidersList()), "Test rprovides for real+virtual package")

    def testIsVirtual(self):
        """Test virtual package identification"""
        # pure virtual, many providers
        p = Package(self.udd.psql, package="mail-transport-agent")
        self.assert_(p.IsVirtual())
        # neither concrete nor virtual
        p = Package(self.udd.psql, package="no-such-package")
        self.assertFalse(p.IsVirtual())
        # concrete only
        p = Package(self.udd.psql, package="libc6")
        self.assertFalse(p.IsVirtual())
        # both concrete and virtual
        p = Package(self.udd.psql, package="imagemagick")
        self.assert_(p.IsVirtual())

    def testIsVirtualOnly(self):
        """Test purely virtual package identification"""
        # pure virtual, many providers
        p = Package(self.udd.psql, package="mail-transport-agent")
        self.assert_(p.IsVirtualOnly())
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
        self.assert_(p.IsAvailable())
        # neither concrete nor virtual
        p = Package(self.udd.psql, package="no-such-package")
        self.assertFalse(p.IsVirtual())
        # concrete only
        p = Package(self.udd.psql, package="libc6")
        self.assert_(p.IsAvailable())
        # both concrete and virtual
        p = Package(self.udd.psql, package="imagemagick")
        self.assert_(p.IsAvailable())

    def testRelationEntry(self):
        """Test getting the relationships between packages"""
        p = Package(self.udd.psql, package="libc6", release='sid')
        self.assertFalse(p.RelationEntry('pre_depends'), "Test package with no dependencies")
        self.assertFalse(p.PreDepends(), "Test package with no dependencies")
        self.assert_(p.RelationEntry('depends'), "Test package with dependencies")
        self.assert_(p.Depends(), "Test package with dependencies")
        self.assert_(p.RelationEntry('recommends'), "Test package with dependencies")
        self.assert_(p.Recommends(), "Test package with dependencies")
        self.assert_(p.RelationEntry('suggests'), "Test package with dependencies")
        self.assert_(p.Suggests(), "Test package with dependencies")
        self.assert_(p.RelationEntry('conflicts'), "Test package with dependencies")
        self.assert_(p.Conflicts(), "Test package with dependencies")
        self.assert_(p.RelationEntry('breaks'), "Test package with dependencies")
        self.assert_(p.Breaks(), "Test package with dependencies")
        self.assertFalse(p.RelationEntry('enhances'), "Test package with no dependencies")
        self.assertFalse(p.Enhances(), "Test package with no dependencies")
        p = Package(self.udd.psql, package="dpkg", release='sid')
        self.assert_(p.RelationEntry('pre_depends'), "Test package with dependencies")
        self.assert_(p.PreDepends(), "Test package with dependencies")
        p = Package(self.udd.psql, package="libc6", release='sid')
        self.assert_(p.RelationEntry('replaces'), "Test package with dependencies")
        self.assert_(p.Replaces(), "Test package with dependencies")
        p = Package(self.udd.psql, package="nosuchpackage")
        self.assertRaises(LookupError, p.RelationEntry, 'depends')
        p = Package(self.udd.psql, package="libc6")
        self.assertRaises(KeyError, p.RelationEntry, 'nosuchrelation')

    def testRelationEntryList(self):
        """Test getting the relationships between packages as a structure"""
        p = Package(self.udd.psql, package="libc6", release='sid')
        self.assertFalse(len(p.RelationshipOptionsList('pre_depends')), "Test package with dependencies")
        self.assertFalse(len(p.PreDependsList()), "Test package with dependencies")
        self.assert_(len(p.RelationshipOptionsList('depends')), "Test package with dependencies")
        self.assert_(len(p.DependsList()), "Test package with dependencies")
        self.assert_(len(p.RelationshipOptionsList('recommends')), "Test package with dependencies")
        self.assert_(len(p.RecommendsList()), "Test package with dependencies")
        self.assert_(len(p.RelationshipOptionsList('suggests')), "Test package with dependencies")
        self.assert_(len(p.SuggestsList()), "Test package with dependencies")
        self.assert_(len(p.RelationshipOptionsList('conflicts')), "Test package with dependencies")
        self.assert_(len(p.ConflictsList()), "Test package with dependencies")
        self.assertFalse(len(p.RelationshipOptionsList('enhances')), "Test package with no dependencies")
        self.assertFalse(len(p.EnhancesList()), "Test package with no dependencies")
        self.assert_(len(p.RelationshipOptionsList('breaks')), "Test package with no dependencies")
        self.assert_(len(p.BreaksList()), "Test package with no dependencies")
        self.assert_(len(p.RelationshipOptionsList('replaces')), "Test package with no dependencies")
        self.assert_(len(p.ReplacesList()), "Test package with no dependencies")
        p = Package(self.udd.psql, package="nosuchpackage")
        self.assertRaises(LookupError, p.RelationshipOptionsList, 'depends')
        p = Package(self.udd.psql, package="libc6")
        self.assertRaises(KeyError, p.RelationshipOptionsList, 'nosuchrelation')

    def testStr(self):
        p = Package(self.udd.psql, package="libc6", release='sid')
        self.assert_(str(p))
        p = Package(self.udd.psql, package="no-such-package", release='sid')
        self.assert_(str(p))


class SourcePackageTests(unittest.TestCase):
    def setUp(self):
        self.udd = Udd()

    def testPackage(self):
        """Test binding a package"""
        self.assertRaises(ValueError, Package, self.udd.psql)
        rs = SourcePackage(self.udd.psql, package="eglibc", release='sid')
        self.assert_(rs)
        self.assert_(rs.Found())
        rne = SourcePackage(self.udd.psql, package="nosuchpackage")
        self.assertFalse(rne.Found())

    def testBinaries(self):
        """Test listing the binary packages compiled by a source package"""
        ps = SourcePackage(self.udd.psql, package="eglibc", arch="i386", release="sid")
        self.assert_(ps.Binaries())
        pne = SourcePackage(self.udd.psql, package="nosuchpackage")
        self.assertFalse(pne.Binaries())

    def testBuildDeps(self):
        """Test listing the build-dep and build-dep-indep packages"""
        ps = SourcePackage(self.udd.psql, package="eglibc", arch="i386", release="sid")
        self.assert_(ps.BuildDepends())
        self.assert_(ps.BuildDependsIndep())
        self.assert_(ps.BuildDependsList())
        self.assert_(ps.BuildDependsIndepList())
        # package has no build-deps-indep
        ps = SourcePackage(self.udd.psql, package="perl", arch="i386", release="sid")
        self.assertFalse(ps.BuildDependsIndep())
        self.assertFalse(ps.BuildDependsIndepList())

###########################################################
if __name__ == "__main__":
    unittest.main()
