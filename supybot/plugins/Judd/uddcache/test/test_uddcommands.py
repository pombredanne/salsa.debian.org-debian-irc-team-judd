#!/usr/bin/python
#
# Ultimate Debian Database query tool
#
# Test suite
#
###
#
# Copyright (c) 2010,      Stuart Prescott
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

import os
import unittest2 as unittest
from uddcache.uddcommands import UddCommands
from uddcache.uddpackages import *


includeSlowTests = 1
if os.environ.has_key('UDD_SKIP_SLOW_TESTS') and int(os.environ['UDD_SKIP_SLOW_TESTS']):
    #print "Skipping slow tests in %s" % __file__
    includeSlowTests = 0

class commands(unittest.TestCase):
    def setUp(self):
        self.udd = UddCommands()

    def testVersions(self):
        """Test version lookups"""
        self.assert_(self.udd.versions('libc6', 'sid', 'i386'))
        self.assertFalse(self.udd.versions('nosuchpackage', 'sid', 'i386'))
        self.assertFalse(self.udd.versions('libc6', 'sid', 'ia64'))
        self.assert_(self.udd.versions('libc6', None, 'amd64'))
        self.assert_(self.udd.versions('src:eglibc', 'sid', 'i386'))
        self.assertFalse(self.udd.versions('src:nosuchpackage', 'sid', 'i386'))

    def testInfo(self):
        """Test package information lookups"""
        self.assert_(self.udd.info('libc6', 'sid', 'i386'))
        self.assertFalse(self.udd.info('nosuchpackage', 'sid', 'i386'))
        self.assertFalse(self.udd.info('libc6', 'sid', 'ia64'))

    @unittest.skipUnless(includeSlowTests, 'slow test')
    def testNames(self):
        """Test package name lookups"""
        self.assert_(self.udd.names('libc6', 'sid', 'i386'))
        self.assert_(self.udd.names('lib?6', 'sid', 'i386'))
        self.assert_(self.udd.names('libc6*', 'sid', 'i386'))
        self.assert_(self.udd.names('*bc6', 'sid', 'i386'))
        self.assert_(self.udd.names('l*6', 'sid', 'i386'))
        self.assertFalse(self.udd.names('libc6', 'sid', 'ia64'))
        self.assert_(self.udd.names('libc6*', 'sid', 'ia64'))
        self.assert_(self.udd.names('src:eglibc', 'sid', 'ia64'))
        self.assertFalse(self.udd.names('src:nosuchpackage', 'sid', 'i386'))

    def testArchs(self):
        """Test architecture availability lookups"""
        self.assert_(self.udd.archs('libc6', 'sid'))
        self.assertFalse(self.udd.archs('nosuchpackage', 'sid'))

    def testPopcon(self):
        """Test popcon data lookups"""
        self.assert_(self.udd.popcon('libc6'))
        self.assertFalse(self.udd.popcon('nosuchpackage'))

    def testUploads(self):
        """Test upload/maintainer data lookups"""
        self.assert_(self.udd.uploads('eglibc', max=10))
        self.assert_(self.udd.uploads('eglibc'))
        self.assert_(self.udd.uploads('eglibc', '2.9-11'))
        self.assertFalse(self.udd.uploads('nosuchpackage'))
        self.assertFalse(self.udd.uploads('eglibc', 'nosuchversion'))
        self.assertFalse(self.udd.uploads('libc6'))  # only does source packages
        p = self.udd.BindSourcePackage('eglibc', 'sid')
        self.assert_(self.udd.uploads(p), 'Check uploads with bind to source package failed')
        p = self.udd.BindSourcePackage('libc6', 'sid')
        self.assert_(self.udd.uploads(p), 'Check uploads with bind to source package via bin2src failed')
        p = self.udd.BindSourcePackage('nosuchpackage', 'sid')
        self.assertFalse(self.udd.uploads(p), 'Check uploads with bind to non-existent source package failed')

    @unittest.skipUnless(includeSlowTests, 'slow test')
    def testCheckDeps(self):
        """Test dependency testing for packages"""
        # TODO: it would be nice to actually test the accuracy of the tests
        self.assert_(self.udd.checkdeps('libc6', 'lenny', 'i386', ['depends']))
        self.assert_(self.udd.checkdeps('libc6', 'lenny', 'i386', ['depends', 'recommends', 'suggests']))
        self.assert_(self.udd.checkdeps('openjdk-6-jre-headless', 'lenny', 'i386', ['depends', 'recommends']), 'broken recommends not handled correctly')
        self.assertFalse(self.udd.checkdeps('nosuchpackage', 'lenny', 'i386', ['depends']))

    @unittest.skipUnless(includeSlowTests, 'slow test')
    def testCheckInstall(self):
        """Test installability for packages"""
        # TODO: it would be nice to actually test the accuracy of the tests
        self.assert_(self.udd.checkInstall('libc6', 'lenny', 'i386', False))
        self.assert_(self.udd.checkInstall('perl', 'lenny', 'i386', True))
        self.assert_(self.udd.checkInstall('openjdk-6-jre-headless', 'lenny', 'i386', False))
        self.assert_(self.udd.checkInstall('openjdk-6-jre-headless', 'lenny', 'i386', True))
        self.assertFalse(self.udd.checkInstall('nosuchpackage', 'lenny', 'i386', True))

    @unittest.skipUnless(includeSlowTests, 'slow test')
    def testCheckBackport(self):
        """Test 'simple sid backport' procedure on packages"""
        # TODO: it would be nice to actually test the accuracy of the tests
        fr = self.udd.BindRelease(arch='i386', release='sid')

        tr = self.udd.BindRelease(arch='i386', release='squeeze')
        self.assert_(self.udd.checkBackport('iceweasel', fr, tr), 'Check [im]possible backport that requires bpo')

        trbp = self.udd.BindRelease(arch='i386',
                        release=self.udd.data.list_dependent_releases('squeeze', suffixes=['backports']))
        self.assert_(self.udd.checkBackport('libxfont1', fr, trbp), 'Check possible backport that requires bpo')

        tro = self.udd.BindRelease(arch='i386', release='lenny')
        self.assert_(self.udd.checkBackport('iceweasel', fr, tro), 'Check impossible backport')

        self.assert_(self.udd.checkBackport('sun-java6', fr, tr), 'Check resolution of arch-dependent build-deps')

        self.assert_(self.udd.checkBackport('pyxplot', fr, tr), 'Check resolution of virtual build-deps')

        self.assert_(self.udd.checkBackport('libv4l-0', fr, tr), 'Check resolution of virtual build-deps')

        self.assertFalse(self.udd.checkBackport('nosuchpackage', fr, tr))


###########################################################
if __name__ == "__main__":
    unittest.main()
