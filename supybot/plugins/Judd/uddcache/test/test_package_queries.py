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

""" Unit tests for generic UDD commands """

from __future__ import unicode_literals

import os
try:
    import unittest2 as unittest
except:
    import unittest

from uddcache.udd import Udd
from uddcache.package_queries import Commands
from uddcache.packages import *


exclude_slow_tests = 0
if 'UDD_SKIP_SLOW_TESTS' in os.environ and int(os.environ['UDD_SKIP_SLOW_TESTS']):
    #print "Skipping slow tests in %s" % __file__
    exclude_slow_tests = 1


class commands(unittest.TestCase):
    def setUp(self):
        self.udd = Udd()
        self.dispatcher = Commands(self.udd)

    def tearDown(self):
        self.udd = None
        self.dispatcher = None

    def testVersions(self):
        """Test version lookups"""
        self.assertTrue(self.dispatcher.versions('libc6', 'sid', 'i386'))
        self.assertRaises(PackageNotFoundError, self.dispatcher.versions, 'nosuchpackage', 'sid', 'i386')
        self.assertRaises(PackageNotFoundError, self.dispatcher.versions, 'libc0.1', 'sid', 'armhf')
        self.assertTrue(self.dispatcher.versions('libc6', None, 'amd64'))
        self.assertTrue(self.dispatcher.versions('src:glibc', 'sid', 'i386'))
        self.assertRaises(PackageNotFoundError, self.dispatcher.versions, 'src:nosuchpackage', 'sid', 'i386')

    def testInfo(self):
        """Test package information lookups"""
        self.assertTrue(self.dispatcher.info('libc6', 'sid', 'i386'))
        self.assertRaises(PackageNotFoundError, self.dispatcher.info, 'nosuchpackage', 'sid', 'i386')
        self.assertRaises(PackageNotFoundError, self.dispatcher.info, 'libc6', 'sid', 'ia64')

    @unittest.skipIf(exclude_slow_tests, 'slow test')
    def testNames(self):
        """Test package name lookups"""
        self.assertTrue(self.dispatcher.names('libc6', 'sid', 'i386'))
        self.assertTrue(self.dispatcher.names('lib?6', 'sid', 'i386'))
        self.assertTrue(self.dispatcher.names('libc6*', 'sid', 'i386'))
        self.assertTrue(self.dispatcher.names('*bc6', 'sid', 'i386'))
        self.assertTrue(self.dispatcher.names('l*6', 'sid', 'i386'))
        self.assertFalse(self.dispatcher.names('libc0.1', 'sid', 'armhf'))
        self.assertTrue(self.dispatcher.names('libc6*', 'sid', 'armhf'))
        self.assertTrue(self.dispatcher.names('src:glibc', 'sid', 'armhf'))
        self.assertFalse(self.dispatcher.names('src:nosuchpackage', 'sid', 'i386'))

    def testArchs(self):
        """Test architecture availability lookups"""
        self.assertTrue(self.dispatcher.archs('libc6', 'sid'))
        self.assertRaises(PackageNotFoundError, self.dispatcher.archs, 'nosuchpackage', 'sid')

    def testPopcon(self):
        """Test popcon data lookups"""
        self.assertTrue(self.dispatcher.popcon('libc6'))
        self.assertRaises(PackageNotFoundError, self.dispatcher.popcon, 'nosuchpackage')

    def testUploads(self):
        """Test upload/maintainer data lookups"""
        self.assertTrue(self.dispatcher.uploads('glibc', max=10))
        self.assertTrue(self.dispatcher.uploads('glibc'))
        self.assertTrue(self.dispatcher.uploads('eglibc', '2.9-11'))
        self.assertRaises(PackageNotFoundError, self.dispatcher.uploads, 'nosuchpackage')
        self.assertRaises(PackageNotFoundError, self.dispatcher.uploads, 'glibc', 'nosuchversion')
        self.assertRaises(PackageNotFoundError, self.dispatcher.uploads, 'libc6')  # only does source packages
        p = self.udd.BindSourcePackage('glibc', 'sid')
        self.assertTrue(self.dispatcher.uploads(p), 'Check uploads with bind to source package failed')
        p = self.udd.BindSourcePackage('libc6', 'sid')
        self.assertTrue(self.dispatcher.uploads(p), 'Check uploads with bind to source package via bin2src failed')

    @unittest.skipIf(exclude_slow_tests, 'slow test')
    def testCheckDeps(self):
        """Test dependency testing for packages"""
        # TODO: it would be nice to actually test the accuracy of the tests
        self.assertTrue(self.dispatcher.checkdeps('libc6', 'sid', 'i386', ['depends']))
        self.assertTrue(self.dispatcher.checkdeps('libc6', 'sid', 'i386', ['depends', 'recommends', 'suggests']))
        self.assertTrue(self.dispatcher.checkdeps('cbedic', 'sid', 'i386', ['suggests']), 'broken relations not handled correctly')
        self.assertRaises(PackageNotFoundError, self.dispatcher.checkdeps, 'nosuchpackage', 'squeeze', 'i386', ['depends'])

    @unittest.skipIf(exclude_slow_tests, 'slow test')
    def testCheckInstall(self):
        """Test installability for packages"""
        # TODO: it would be nice to actually test the accuracy of the tests
        self.assertTrue(self.dispatcher.checkInstall('libc6', 'sid', 'i386', False))
        self.assertTrue(self.dispatcher.checkInstall('perl', 'sid', 'i386', True))
        #self.assertTrue(self.dispatcher.checkInstall('openjdk-6-jre-headless', 'lenny', 'i386', False))
        #self.assertTrue(self.dispatcher.checkInstall('openjdk-6-jre-headless', 'lenny', 'i386', True))
        self.assertRaises(PackageNotFoundError, self.dispatcher.checkInstall, 'nosuchpackage', 'sid', 'i386', True)

    @unittest.skipIf(exclude_slow_tests, 'slow test')
    def testWhy(self):
        """Test existence of package dependency chains"""
        # TODO: it would be nice to actually test the accuracy of the tests
        self.assertTrue(self.dispatcher.why('dpkg', 'libc6', 'squeeze', 'i386', False))
        self.assertEqual(self.dispatcher.why('dpkg', 'dolphin', 'squeeze','i386', False), [])
        self.assertEqual(self.dispatcher.why('dpkg', 'libc6-i686', 'squeeze', 'i386', False), [])
        self.assertTrue(self.dispatcher.why('dpkg', 'libc6-i686', 'squeeze', 'i386', True))
        self.assertEqual(self.dispatcher.why('dpkg', 'nosuchpackage', 'squeeze', 'i386', False), [])
        self.assertRaises(PackageNotFoundError, self.dispatcher.why, 'nosuchpackage', 'dpkg', 'squeeze', 'i386', False)

    @unittest.skipIf(exclude_slow_tests, 'slow test')
    def testCheckBackport(self):
        """Test 'simple sid backport' procedure on packages"""
        # TODO: it would be nice to actually test the accuracy of the tests
        fr = self.udd.BindRelease(arch='i386', release='sid')

        tr = self.udd.BindRelease(arch='i386', release='squeeze')
        self.assertTrue(self.dispatcher.checkBackport('iceweasel', fr, tr), 'Check [im]possible backport that requires bpo')

        trbp = self.udd.BindRelease(arch='i386',
                        release=self.udd.data.list_dependent_releases('squeeze', suffixes=['backports']))
        self.assertTrue(self.dispatcher.checkBackport('libxfont1', fr, trbp), 'Check possible backport that requires bpo')

        tro = self.udd.BindRelease(arch='i386', release="squeeze")
        self.assertTrue(self.dispatcher.checkBackport('gcc', fr, tro), 'Check impossible backport')

        self.assertTrue(self.dispatcher.checkBackport('openjdk-6', fr, tr), 'Check resolution of arch-dependent build-deps')

        self.assertTrue(self.dispatcher.checkBackport('pyxplot', fr, tr), 'Check resolution of virtual build-deps')

        self.assertTrue(self.dispatcher.checkBackport('libv4l-0', fr, tr), 'Check resolution of virtual build-deps')

        self.assertRaises(PackageNotFoundError, self.dispatcher.checkBackport, 'nosuchpackage', fr, tr)

###########################################################
if __name__ == "__main__":
    unittest.main()
