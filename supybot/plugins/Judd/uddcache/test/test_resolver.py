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

""" Unit tests for package resolver """

from __future__ import unicode_literals

import os
try:
    import unittest2 as unittest
except:
    import unittest

from uddcache.udd import Udd
from uddcache.resolver import *

exclude_slow_tests = 0
if 'UDD_SKIP_SLOW_TESTS' in os.environ and int(os.environ['UDD_SKIP_SLOW_TESTS']):
    #print "Skipping slow tests in %s" % __file__
    exclude_slow_tests = 1


class CheckerTests(unittest.TestCase):
    def setUp(self):
        self.udd = Udd()
        self.checker = Checker(self.udd.BindRelease()) # i386 stable
        self.sidchecker = Checker(self.udd.BindRelease(release='sid')) # i386

    def tearDown(self):
        self.udd = None
        self.checker = None

    def testInit(self):
        self.assertRaises(TypeError, Checker, None)

    def testCheckRelationsList(self):
        """Test checking the dependencies of a package"""
        # FIXME: really need to check that the results are correct
        # package with no dependencies
        p = self.udd.BindPackage(package="libjiu-java", release="sid")
        r = self.checker.CheckRelationshipOptionsList(p.RelationshipOptionsList('depends'))
        self.assertTrue(r != None)
        # package with one dependency
        p = self.udd.BindPackage(package="patch")
        r = self.checker.CheckRelationshipOptionsList(p.RelationshipOptionsList('depends'))
        self.assertTrue(r)
        # package with lots of dependencies
        p = self.udd.BindPackage(package="perl")
        r = self.checker.CheckRelationshipOptionsList(p.RelationshipOptionsList('depends'))
        self.assertTrue(r)
        # package with lots of dependencies including options
        p = self.udd.BindPackage(package="php5")
        r = self.checker.CheckRelationshipOptionsList(p.RelationshipOptionsList('depends'))
        self.assertTrue(r)
        # package with dependencies including virtual package with no alternatives listed
        p = self.udd.BindPackage(package="bcron-run")
        r = self.checker.CheckRelationshipOptionsList(p.RelationshipOptionsList('depends'))
        self.assertTrue(r)
        # bad input object
        r = self.checker.CheckRelationshipOptionsList(None)
        self.assertTrue(not r is None)

    def testCheckRelationArch(self):
        """Check architecture-specific dependency syntax"""
        # note: self.checker is configured to be i386
        # nothing specified implies everything satisfies
        self.assertTrue(self.checker.CheckRelationArch(""))
        self.assertTrue(self.checker.CheckRelationArch(None))
        self.assertTrue(self.checker.CheckRelationArch([]))
        # single options
        self.assertTrue(self.checker.CheckRelationArch(["i386"]))
        self.assertFalse(self.checker.CheckRelationArch(["amd64"]))
        self.assertTrue(self.checker.CheckRelationArch(["!amd64"]))
        # multiple options
        self.assertTrue(self.checker.CheckRelationArch(["!alpha", "!amd64", "!ia64"]))
        self.assertFalse(self.checker.CheckRelationArch(["!alpha", "!amd64", "!i386", "!ia64"]))
        # wildcard archs
        self.assertTrue(self.checker.CheckRelationArch(["linux-any"]))
        self.assertTrue(self.checker.CheckRelationArch(["any-i386"]))
        self.assertFalse(self.checker.CheckRelationArch(["kfreebsd-any"]))
        self.assertTrue(self.checker.CheckRelationArch(["!kfreebsd-i386"]))
        self.assertFalse(self.checker.CheckRelationArch(["!linux-any",  "!hurd-any"]))
        # bad input
        self.assertRaises(TypeError, self.checker.CheckRelationArch, 1)

    def testRelationSatisfied(self):
        """Check whether relationships can be satisfied correctly"""
        # NOTE: self.checker is an i386 instance
        # >>
        r = Relationship(relation="libc6 (>> 1.0.1)")
        self.assertTrue(self.checker.RelationSatisfied(r))
        r = Relationship(relation="libc6 (>> 10:1.0.1)")
        self.assertFalse(self.checker.RelationSatisfied(r))
        # <<
        r = Relationship(relation="libc6 (<< 10.0.1)")
        self.assertTrue(self.checker.RelationSatisfied(r))
        r = Relationship(relation="libc6 (<< 1.0.1)")
        self.assertFalse(self.checker.RelationSatisfied(r))
        # =
        r = Relationship(relation="spline (= 1.2-1)")
        self.assertTrue(self.checker.RelationSatisfied(r))
        r = Relationship(relation="dpkg (= 1.14.1)")
        self.assertFalse(self.checker.RelationSatisfied(r))
        # >=
        r = Relationship(relation="spline (>= 1.1-11)")
        self.assertTrue(self.checker.RelationSatisfied(r))
        r = Relationship(relation="dpkg (>= 1.12.0)")
        self.assertTrue(self.checker.RelationSatisfied(r))
        # <=
        r = Relationship(relation="dpkg (<= 1.14.1)")
        self.assertFalse(self.checker.RelationSatisfied(r))
        r = Relationship(relation="dpkg (<= 5:1.14.27)")
        self.assertTrue(self.checker.RelationSatisfied(r))
        # simple relations
        r = Relationship(relation="libc6")
        self.assertTrue(self.checker.RelationSatisfied(r))
        r = Relationship(relation="no-such-package")
        self.assertFalse(self.checker.RelationSatisfied(r))
        # arch specific
        r = Relationship(relation="libc6 [i386]")
        self.assertTrue(self.checker.RelationSatisfied(r))
        r = Relationship(relation="libc6.1 [amd64]")  # irrelevant for i386
        self.assertTrue(self.checker.RelationSatisfied(r))
        r = Relationship(relation="no-such-package [amd64]")  # irrelevant for i386
        self.assertTrue(self.checker.RelationSatisfied(r))
        r = Relationship(relation="no-such-package [i386]")
        self.assertFalse(self.checker.RelationSatisfied(r))

    def testCheck(self):
        # package with no dependencies
        c = self.checker.Check(package="when")
        self.assertTrue(not c is None)
        self.assertTrue(len(c.good) == 0)
        self.assertTrue(len(c.bad) == 0)
        # known good package
        c = self.checker.Check(package="libc6")
        self.assertTrue(c)
        self.assertTrue(len(c.good) > 0)
        self.assertTrue(len(c.bad) == 0)
        # known bad package [cbedic has unsatisfied suggests]
        c = self.sidchecker.Check(package="cbedic", relation='suggests')
        self.assertTrue(c)
        self.assertTrue(len(c.bad) > 0)
        # non-existent package
        self.assertRaises(PackageNotFoundError, self.checker.Check, package="no-such-package")
        # conflicts in a package
        c = self.checker.Check(package="libc6", relation="conflicts")
        self.assertTrue(c)
        self.assertTrue(len(c.good) > 0)
        self.assertTrue(len(c.bad) == 0)
        # non-existent conflicts in a package
        c = self.checker.Check(package="libapr1", relation="conflicts")
        self.assertTrue(c)
        self.assertTrue(len(c.good) > 0)
        self.assertTrue(len(c.bad) == 0)


class BuildDepCheckerTests(unittest.TestCase):
    def setUp(self):
        self.udd = Udd()
        self.checker = BuildDepsChecker(self.udd.BindRelease(arch="i386", release="sid"))

    def tearDown(self):
        self.udd = None
        self.checker = None

    def testCheck(self):
        """Test checking the build-dependencies of a package"""
        # simple package, check by source package name
        b = self.checker.Check(package="pyxplot")
        self.assertTrue(b)
        self.assertTrue(len(b.bd.good) > 0)
        self.assertTrue(len(b.bd.bad) == 0)
        # big complicated package with lots of arch-dependent entries, check by binary name
        b = self.checker.Check(package="libc6")
        self.assertTrue(b)
        self.assertTrue(len(b.bd.good) > 0)
        self.assertTrue(len(b.bdi.good) > 0)
        self.assertTrue(len(b.bd.bad) == 0)
        self.assertTrue(len(b.bdi.bad) == 0)
        # check by SourcePackage object
        p = self.udd.BindSourcePackage(package="latexdraw", release="squeeze")
        b = self.checker.Check(package=p)
        self.assertTrue(b)
        self.assertTrue(len(b.bd.good) > 0)
        self.assertTrue(len(b.bd.bad) == 0)
        # non-existent package
        self.assertRaises(PackageNotFoundError, self.checker.Check, package="no-such-package")
        # bd and bdi lists
        p = self.udd.BindSourcePackage(package="libc6")
        bd = p.RelationshipOptionsList("build_depends")
        b = self.checker.Check(bdList=bd)
        self.assertTrue(b)
        self.assertTrue(len(b.bd.good) > 0)
        b = self.checker.Check(bdList=p.RelationshipOptionsList("build_depends"),
                               bdiList=p.RelationshipOptionsList("build_depends"))
        self.assertTrue(b)
        self.assertTrue(len(b.bd.good) > 0)
        self.assertTrue(len(b.bdi.good) > 0)
        self.assertRaises(ValueError, self.checker.Check)
        self.assertRaises(ValueError, self.checker.Check, bdList=[])


class InstallCheckerTests(unittest.TestCase):
    def setUp(self):
        self.udd = Udd()
        self.checker = InstallChecker(self.udd.BindRelease())

    def tearDown(self):
        self.udd = None
        self.checker = None

    @unittest.skipIf(exclude_slow_tests, 'slow test')
    def testCheck(self):
        """Test installability of packages"""
        # FIXME: it would be good to check if these results are right
        self.assertTrue(self.checker.Check('libc6'))
        self.assertRaises(PackageNotFoundError, self.checker.Check, 'nosuchpackage')
        self.assertTrue(self.checker.Check('perl', True))
        self.assertTrue(self.checker.Check('openjdk-6-jre-headless', True))   # missing recommended package

#
#
#class PackageListsTests(unittest.TestCase):
#    def testRelationshipOptions(self):
#        self.assertTrue(----)

class SolverHierarchyTests(unittest.TestCase):
    def setUp(self):
        self.udd = Udd()

    def tearDown(self):
        self.udd = None

    def testInit(self):
        s = SolverHierarchy('dpkg')
        self.assertTrue(not s is None)

    def testGet(self):
        s = SolverHierarchy('')
        rs = RelationshipStatus()
        rs.good.append('dpkg')
        s.depends.extend(rs)
        self.assertTrue(s.get('depends'))
        self.assertFalse(s.get('recommends'))
        rs2 = RelationshipStatus()
        rs2.bad.append('dpkg2')
        s.depends.extend(rs2)
        self.assertFalse(s.get('recommends'))

    def testFlatten(self):
        self.checker = InstallChecker(self.udd.BindRelease(arch="i386", release="squeeze"))
        s = self.checker.Check('perl', True)
        f = s.flatten()
        self.assertTrue(f)
        self.assertTrue(len(f.depends))

    def testChains(self):
        self.checker = InstallChecker(self.udd.BindRelease(arch="i386", release="squeeze"))
        s = self.checker.Check('pyxplot', True)
        c = s.chains()
        self.assertTrue(c)
        self.assertTrue(len(c))

    def testStr(self):
        self.checker = InstallChecker(self.udd.BindRelease(arch="i386", release="squeeze"))
        s = self.checker.Check('perl', True)
        self.assertTrue(unicode(s))
        #self.assertTrue(str(s))
        f = s.flatten()
        self.assertTrue(unicode(f))

###########################################################
if __name__ == "__main__":
    unittest.main()
