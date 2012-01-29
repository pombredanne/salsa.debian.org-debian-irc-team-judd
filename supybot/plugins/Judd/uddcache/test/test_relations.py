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

""" Unit tests for package relationships """

import os
import unittest2 as unittest
from uddcache.udd import Udd
from uddcache.relations import *
from uddcache.resolver import *


includeSlowTests = 1
if os.environ.has_key('UDD_SKIP_SLOW_TESTS') and int(os.environ['UDD_SKIP_SLOW_TESTS']):
    #print "Skipping slow tests in %s" % __file__
    includeSlowTests = 0

class RelationshipTests(unittest.TestCase):
    def testRelationship(self):
        """Test construction/parsing of package relationships"""
        r = Relationship(relation="pkg")
        self.assert_(r.package == "pkg" and not(r.operator) and not(r.version) and not(r.arch))
        r = Relationship(relation="pkg (>> 1.0.1)")
        self.assert_(r.package == "pkg" and r.operator == ">>" and r.version == "1.0.1" and not(r.arch))
        r = Relationship(relation="pkg (<< 1.0.1~)")
        self.assert_(r.package == "pkg" and r.operator == "<<" and r.version == "1.0.1~" and not(r.arch))
        r = Relationship(relation="pkg (>= 0)")
        self.assert_(r.package == "pkg" and r.operator == ">=" and r.version == "0" and not(r.arch))
        r = Relationship(relation="pkg (= 1.2-3release4.1)")
        self.assert_(r.package == "pkg" and r.operator == "=" and r.version == "1.2-3release4.1" and not(r.arch))
        r = Relationship(relation="pkg [amd64]")
        self.assert_(r.package == "pkg" and not(r.operator) and not(r.version) and r.arch == ["amd64"])
        r = Relationship(relation="pkg [!amd64]")
        self.assert_(r.package == "pkg" and not(r.operator) and not(r.version) and r.arch == ["!amd64"])
        r = Relationship(relation="pkg (>> 1.0) [amd64]")
        self.assert_(r.package == "pkg" and r.operator == ">>" and r.version == "1.0" and r.arch == ["amd64"])

        r = Relationship(package="pkg", operator=">>", version="1.0", arch="amd64")
        self.assert_(r.package == "pkg" and r.operator == ">>" and r.version == "1.0" and r.arch == ["amd64"])
        r = Relationship(package="pkg", operator=">>", version="1.0", arch=["amd64", "i386"])
        self.assert_(r.package == "pkg" and r.operator == ">>" and r.version == "1.0" and r.arch == ["amd64", "i386"])
        r = Relationship(package="pkg", operator=">>", version="1.0", arch="amd64 i386")
        self.assert_(r.package == "pkg" and r.operator == ">>" and r.version == "1.0" and r.arch == ["amd64", "i386"])

        # catch over-specification
        self.assertRaises(ValueError, Relationship, relation="pkg", package="pkg")
        # catch invalid syntax
        self.assertRaises(ValueError, Relationship, package="pkg", operator='>>')
        self.assertRaises(ValueError, Relationship, package="pkg", version='2.0')
        self.assertRaises(ValueError, Relationship, relation="pkg >> 1.0")
        self.assertRaises(ValueError, Relationship, package="pkg", operator="!=", version="1.0")
        self.assertRaises(ValueError, Relationship, relation="pkg != 1.0")

    def testStr(self):
        r = Relationship(package="pkg", operator=">>", version="1.0")
        self.assert_(str(r) == "pkg (>> 1.0) []")
        r = Relationship(package="pkg", operator=">>", version="1.0", arch="amd64")
        self.assert_(str(r) == "pkg (>> 1.0) [amd64]")
        r = Relationship(package="pkg", operator=">>", version="1.0", arch=["amd64", "i386"])
        self.assert_(str(r) == "pkg (>> 1.0) [amd64 i386]")
        r = Relationship(relation="pkg (>> 1.1) [386]")
        self.assert_(str(r) == "pkg (>> 1.1) [386]")

    def testIsVersioned(self):
        r = Relationship(package="pkg", operator=">>", version="1.0")
        self.assert_(r.isVersioned())
        r = Relationship(package="pkg")
        self.assertFalse(r.isVersioned())


class RelationshipOptionsTests(unittest.TestCase):
    def testRelationshipOptions(self):
        """Test parsing of options in package relationship clauses"""
        o = RelationshipOptions("a")
        self.assert_(o[0].package == "a" and len(o) == 1)
        o = RelationshipOptions("a | b")
        self.assert_(o[0].package == "a" and o[1].package == "b" and len(o) == 2)
        o = RelationshipOptions("a | b | c")
        self.assert_(o[0].package == "a" and o[1].package == "b" and o[2].package == "c" and len(o) == 3)
        o = RelationshipOptions("a (>> 1.0)")
        self.assert_(o[0].package == "a" and o[0].version == "1.0" and len(o) == 1)
        o = RelationshipOptions("a (>> 1.0 ) | b (= 2.0)")
        self.assert_(o[0].package == "a" and o[0].version == "1.0" and o[1].package == "b" and o[1].version == "2.0")


class RelationshipOptionsListTests(unittest.TestCase):
    def setUp(self):
        self.udd = Udd()
#        self.checker = RelationChecker(self.udd.BindRelease(arch="i386",release="lenny"))

    def tearDown(self):
        self.udd = None

    def testReleaseMap(self):
        """Test mapping a list of RelationshipOptions into a releases/packages dict"""
        # non-existent package should be unresolvable
        rl = RelationshipOptionsList()
        rl.append(RelationshipOptions("no-such-package"))
        self.assert_(rl)
        self.assert_(rl.ReleaseMap()['unresolved'])

        # resolver not run so all relationships are "unresolved"
        p = self.udd.BindPackage("libc6", "sid", "i386")
        rl = p.RelationshipOptionsList("depends")
        self.assert_(rl)
        self.assert_(rl.ReleaseMap()['unresolved'])

        release = self.udd.BindRelease(arch="i386", release="squeeze")
        checker = Checker(release)

        # all resolvable, options, versioned deps
        p = release.Package("build-essential")
        rl = checker.CheckRelationshipOptionsList(p.RelationshipOptionsList("depends"))
        self.assert_(rl.good.ReleaseMap())
        self.assert_(rl.good.ReleaseMap()['squeeze'])
        self.assertFalse('unresolved' in rl.good.ReleaseMap())

        # all resolvable, virtual packages
        p = release.Package("debbugs")
        rl = checker.CheckRelationshipOptionsList(p.RelationshipOptionsList("depends"))
        self.assert_(rl.good.ReleaseMap())
        self.assert_(rl.good.ReleaseMap()['squeeze'])
        self.assertFalse('unresolved' in rl.good.ReleaseMap())
        self.assert_('virtual' in rl.good.ReleaseMap())
        self.assert_(rl.good.ReleaseMap()['virtual'])
        #print rl.good.ReleaseMap()
        #print rl

        # some arch-specific dependencies
        p = release.Source("eglibc")
        rl = checker.CheckRelationshipOptionsList(p.RelationshipOptionsList("build_depends"))
        self.assert_(rl.good.ReleaseMap())
        self.assert_(rl.good.ReleaseMap()['squeeze'])
        self.assert_('archignore' in rl.good.ReleaseMap())
        self.assert_(rl.good.ReleaseMap()['archignore'])

    def testPackageSet(self):
        """Test reducing a list of RelationshipOptions into list of packages"""
        # resolver not run so all relationships are unsatisified
        p = self.udd.BindPackage("libc6", "sid", "i386")
        rl = p.RelationshipOptionsList("depends")
        #print rl.PackageSet()
        self.assert_(rl.PackageSet())

        release = self.udd.BindRelease(arch="i386", release="squeeze")
        checker = Checker(release)

        # all resolvable, options, versioned deps
        p = release.Package("build-essential")
        rl = checker.CheckRelationshipOptionsList(p.RelationshipOptionsList("depends"))
        #print rl.good.PackageSet()
        self.assert_(rl.good.PackageSet())
        self.assertFalse(rl.bad.PackageSet())

        # all resolvable, virtual packages
        p = release.Package("debbugs")
        rl = checker.CheckRelationshipOptionsList(p.RelationshipOptionsList("depends"))
        #print rl.good.PackageSet()
        self.assert_(rl.good.PackageSet())
        self.assertFalse(rl.bad.PackageSet())

    def testStr(self):
        # non-existent package
        rl = RelationshipOptionsList()
        rl.append(RelationshipOptions("no-such-package"))
        self.assert_(str(rl))

        # list of packages
        release = self.udd.BindRelease(arch="i386", release="squeeze")
        p = release.Package("build-essential")
        rl = p.RelationshipOptionsList("depends")
        self.assert_(str(rl))


class PackageListsTests(unittest.TestCase):
    def setUp(self):
        self.l = PackageLists(['foo', 'bar'])
        self.l.foo.append('1')
        self.l.foo.append('2')
        self.l.bar.append('quux')

    def testInit(self):
        """ Test creation of PackageList lists """
        self.assertFalse(PackageLists([]))
        self.assertFalse(PackageLists(['foo', 'bar']))
        self.assertFalse(PackageLists(['foo', 'bar'], RelationshipOptionsList))

    def testGetSet(self):
        """ Test getting and setting the values directly """
        self.assert_(len(self.l.foo) == 2)
        self.assert_(len(self.l.bar) == 1)
        self.assert_(self.l.bar[0] == 'quux')

    def testIndirectNames(self):
        """ Test getting and setting the values indirectly """
        self.assert_(len(self.l.get('foo')) == 2)
        self.assert_(len(self.l.get('bar')) == 1)
        self.assert_(self.l.get('bar')[0] == 'quux')
        self.l.get('bar').append('goo')
        self.assert_(len(self.l.get('bar')) == 2)
        self.l.set('bar', ['quux'])
        self.assert_(len(self.l.get('bar')) == 1)

    def testStr(self):
        """ Test string representation """
        self.assert_(str(self.l))
        self.assert_(len(str(self.l)))

    def testNonzero(self):
        """ Test counting """
        self.assert_(self.l)
        self.assertFalse(PackageLists([]))


class BuildDepStatusTests(unittest.TestCase):
    def setUp(self):
        self.udd = Udd()

    def tearDown(self):
        self.udd = None

    def testInit(self):
        self.assert_(BuildDepStatus())
        self.assert_(BuildDepStatus(bd=RelationshipStatus(), bdi=RelationshipStatus()))

    def testAllFound(self):
        release = self.udd.BindRelease(arch="i386", release="squeeze")
        checker = Checker(release)
        p = release.Source("eglibc")
        bdstatus = BuildDepStatus(bd=checker.CheckRelationshipOptionsList(p.BuildDependsList()),
                                  bdi=checker.CheckRelationshipOptionsList(p.BuildDependsIndepList()))
        self.assert_(bdstatus.AllFound())

        release = self.udd.BindRelease(arch="i386", release="sid")
        checker = Checker(release)
        p = release.Source("stage")   # has been BD-uninstallable since 2009
        bdstatus = BuildDepStatus(bd=checker.CheckRelationshipOptionsList(p.BuildDependsList()),
                                  bdi=checker.CheckRelationshipOptionsList(p.BuildDependsIndepList()))
        self.assertFalse(bdstatus.AllFound())

    def testReleaseMap(self):
        release = self.udd.BindRelease(arch="i386", release="squeeze")
        checker = Checker(release)
        p = release.Source("eglibc")
        bdstatus = BuildDepStatus(bd=checker.CheckRelationshipOptionsList(p.BuildDependsList()),
                                  bdi=checker.CheckRelationshipOptionsList(p.BuildDependsIndepList()))
        m = bdstatus.ReleaseMap()
        self.assertEquals(sorted(m.keys()), ['archignore', 'squeeze'])
        self.assert_(len(m['squeeze']) > 1)

        release = self.udd.BindRelease(arch="i386", release=["squeeze", "squeeze-backports"])
        checker = Checker(release)
        p = release.Source("libxfont1", version='1:1.4.3', operator='>>')
        bdstatus = BuildDepStatus(bd=checker.CheckRelationshipOptionsList(p.BuildDependsList()),
                                  bdi=checker.CheckRelationshipOptionsList(p.BuildDependsIndepList()))
        m = bdstatus.ReleaseMap()
        self.assertEquals(sorted(m.keys()), ['squeeze', 'squeeze-backports'])

    def testStr(self):
        bdstatus = BuildDepStatus()
        self.assert_(str(bdstatus))

        release = self.udd.BindRelease(arch="i386", release="squeeze")
        checker = Checker(release)
        p = release.Source("eglibc")
        bdstatus = BuildDepStatus(bd=checker.CheckRelationshipOptionsList(p.BuildDependsList()),
                                  bdi=checker.CheckRelationshipOptionsList(p.BuildDependsIndepList()))
        self.assert_(str(bdstatus))


class RelationshipStatusTests(unittest.TestCase):
    def setUp(self):
        self.udd = Udd()

    def tearDown(self):
        self.udd = None

    def testPackageSets(self):
        release = self.udd.BindRelease(arch="i386", release="squeeze")
        s = RelationshipStatus()
        s.good.append(release.Package('dpkg').DependsList()[0])
        s.good.append(release.Package('dpkg').DependsList()[0])
        self.assert_(s.PackageSets())
        self.assert_(len(s.PackageSets().good)==1)
        self.assert_(len(s.PackageSets().bad)==0)
        s.good.append(release.Package('perl').DependsList()[0])
        s.bad.append(release.Package('python').DependsList()[0])
        self.assert_(s.PackageSets())
        self.assert_(len(s.PackageSets().good)==2)
        self.assert_(len(s.PackageSets().bad)==1)

    def testExtend(self):
        s = RelationshipStatus()
        s.good.append('pkg')
        s2 = RelationshipStatus()
        s2.good.append('pkg2')
        s2.bad.append('pkg3')
        s.extend(s2)
        self.assert_(len(s.good)==2)
        self.assert_(len(s.bad)==1)

    def testSwap(self):
        s = RelationshipStatus()
        s.good.extend(['pkg1', 'pkg2'])
        self.assert_(s.satisfied())
        s.bad.extend(['pkg3'])
        self.assertFalse(s.satisfied())
        s = RelationshipStatus()
        s.unchecked.extend(['pkg1', 'pkg2'])
        self.assertFalse(s.satisfied())
        s = RelationshipStatus()
        s.bad.extend(['pkg1', 'pkg2'])
        self.assertFalse(s.satisfied())

    def testSatisfied(self):
        s = RelationshipStatus()
        s.good.extend(['pkg1', 'pkg2'])
        s.bad.extend(['pkg3'])
        self.assert_(len(s.good)==2)
        self.assert_(len(s.bad)==1)
        s.swap()
        self.assert_(len(s.good)==1)
        self.assert_(len(s.bad)==2)

    def testStr(self):
        release = self.udd.BindRelease(arch="i386", release="squeeze")
        s = RelationshipStatus()
        s.good.extend(release.Package('dpkg').DependsList())
        self.assert_(unicode(s))
        self.assert_(str(s))

        release = self.udd.BindRelease(arch="i386", release="squeeze")
        s = RelationshipStatus()
        s.good.extend(release.Package('dpkg').DependsList())
        s.bad.extend(release.Package('python').DependsList())
        s.unchecked.extend(release.Package('ruby').DependsList())
        self.assert_(unicode(s))
        self.assert_(str(s))

        release = self.udd.BindRelease(arch="i386", release="squeeze")
        s = RelationshipStatus()
        s.good.extend(release.Package('dpkg').DependsList())
        s2 = RelationshipStatus()
        s2.good.extend(release.Package('perl').DependsList())
        s.good[0].status = s2
        s3 = RelationshipStatus()
        s3.good.extend(release.Package('python').DependsList())
        s2.good[0].status = s3
        self.assert_(unicode(s))
        self.assert_(str(s))

    def testNonzero(self):
        s = RelationshipStatus()
        self.assertFalse(s)
        s.good.append('pkg')
        self.assert_(s)
        s = RelationshipStatus()
        s.bad.append('pkg')
        self.assert_(s)
        s = RelationshipStatus()
        s.unchecked.append('pkg')
        self.assert_(s)
        s = RelationshipStatus()
        s.good.append('pkg')
        s.bad.append('pkg')
        s.unchecked.append('pkg')
        self.assert_(s)

class MockPackage(object):
    def __init__(self, name):
        self.package = name

class DependsTest(unittest.TestCase):
    def testInit(self):
        d = Depends(MockPackage('foo'))
        self.assert_(d)
        self.assertEqual(d.packagedata.package, 'foo')

    def testStr(self):
        d = Depends(MockPackage('foo'))
        self.assertEqual(str(d), '=>foo')

    def testUnicode(self):
        d = Depends(MockPackage('foo'))
        self.assertIn('foo', unicode(d))


class RecommendsTest(unittest.TestCase):
    def testInit(self):
        d = Recommends(MockPackage('foo'))
        self.assert_(d)
        self.assertEqual(d.packagedata.package, 'foo')

    def testStr(self):
        d = Recommends(MockPackage('foo'))
        self.assertEqual(str(d), '->foo')

    def testUnicode(self):
        d = Recommends(MockPackage('foo'))
        self.assertIn('foo', unicode(d))


class DependencyChainTest(unittest.TestCase):
    def testInit(self):
        self.assertFalse(DependencyChain())
        self.assert_(DependencyChain(relation=Depends('a'), base="z"))
        self.assert_(DependencyChain(chain=[Depends('a'), Depends('b')]))
        self.assertEqual(len(DependencyChain(chain=[Depends('a'), Depends('b')])), 2)

    def testTruncated(self):
        c = DependencyChain(chain=[Depends(MockPackage(x)) for x in ['a', 'b', 'c', 'd', 'e']])
        self.assertEqual(len(c.truncated('a')), 1)
        self.assertEqual(len(c.truncated('d')), 4)
        self.assertEqual(len(c.truncated('f')), 0)

    def testContains(self):
        c = DependencyChain(chain=[Depends(MockPackage(x)) for x in ['a', 'b', 'c', 'd', 'e']])
        self.assert_(c.contains('a'))
        self.assertFalse(c.contains('f'))

    def testDistance(self):
        c = DependencyChain(chain=[Depends(MockPackage(x)) for x in ['a', 'b', 'c', 'd', 'e']])
        self.assertEquals(c.distance(), 5)
        c = DependencyChain(chain=[Recommends(MockPackage(x)) for x in ['a', 'b', 'c', 'd', 'e']])
        self.assertEquals(c.distance(), 5000)
        c = DependencyChain(chain=[Depends(MockPackage('a')), Recommends(MockPackage('b')), Depends(MockPackage('c'))])
        self.assertEquals(c.distance(), 1002)

    def testStr(self):
        names = ['aaa', 'bbbb', 'ccccc', 'ddddddd', 'eee']
        c = DependencyChain(chain=[Depends(MockPackage(x)) for x in names])
        for n in names:
            self.assertIn(n, str(c))
        c.base = "test"
        self.assertIn("test", str(c))

    def testUnicode(self):
        names = ['aaa', 'bbbb', 'ccccc', 'ddddddd', 'eee']
        c = DependencyChain(chain=[Depends(MockPackage(x)) for x in names])
        for n in names:
            self.assertIn(n, unicode(c))
        c.base = "test"
        self.assertIn("test", unicode(c))


class DependencyChainListTest(unittest.TestCase):
    def testUnique(self):
        names = ['aaa', 'bbbb', 'ccccc', 'ddddddd', 'eee', 'ff', 'ggggg']
        cl = DependencyChainList([
              DependencyChain(chain=[Depends(MockPackage(x)) for x in names]),
              DependencyChain(chain=[Depends(MockPackage(x)) for x in names[3:5]]),
              DependencyChain(chain=[Depends(MockPackage(x)) for x in names[:4]]),
              DependencyChain(chain=[Depends(MockPackage(x)) for x in names[3:5]])
            ])
        self.assertEqual(len(cl), 4)
        self.assertEqual(len(cl.unique()), 3)

    def testTruncated(self):
        names = ['aaa', 'bbbb', 'ccccc', 'ddddddd', 'eee', 'ff', 'ggggg']
        cl = DependencyChainList([
              DependencyChain(chain=[Depends(MockPackage(x)) for x in names]),
              DependencyChain(chain=[Depends(MockPackage(x)) for x in names[3:5]]),
              DependencyChain(chain=[Depends(MockPackage(x)) for x in names[:4]]),
              DependencyChain(chain=[Depends(MockPackage(x)) for x in names[3:5]])
            ])
        self.assertEqual(len(cl.truncated('ccccc')), 2)

    def testSorted(self):
        names = ['aaa', 'bbbb', 'ccccc', 'ddddddd', 'eee', 'ff', 'ggggg']
        cl = DependencyChainList([
              DependencyChain(chain=[Depends(MockPackage(x)) for x in names]),
              DependencyChain(chain=[Depends(MockPackage(x)) for x in names[3:5]]),
              DependencyChain(chain=[Depends(MockPackage(x)) for x in names[:4]]),
              DependencyChain(chain=[Depends(MockPackage(x)) for x in names[3:5]])
            ])
        cls = cl.sorted()
        self.assertEqual(len(cls[0]), 2)
        self.assertEqual(len(cls[3]), 7)

        cl.append(DependencyChain(chain=[Depends(MockPackage('a')), Recommends(MockPackage('b')), Depends(MockPackage('c'))]))
        cls = cl.sorted()
        self.assertEqual(len(cls[0]), 2)
        self.assertEqual(len(cls[4]), 3)

    def testSetBase(self):
        names = ['aaa', 'bbbb', 'ccccc', 'ddddddd', 'eee', 'ff', 'ggggg']
        cl = DependencyChainList([
              DependencyChain(chain=[Depends(MockPackage(x)) for x in names]),
              DependencyChain(chain=[Depends(MockPackage(x)) for x in names[3:5]]),
              DependencyChain(chain=[Depends(MockPackage(x)) for x in names[:4]]),
              DependencyChain(chain=[Depends(MockPackage(x)) for x in names[3:5]])
            ])
        cl.set_base("foo")
        for c in cl:
            self.assertEqual(c.base, "foo")

###########################################################
if __name__ == "__main__":
    unittest.main()
