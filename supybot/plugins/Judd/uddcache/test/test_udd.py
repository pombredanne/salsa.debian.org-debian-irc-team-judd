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

""" Unit tests for base UDD bindings """

from __future__ import unicode_literals

try:
    import unittest2 as unittest
except:
    import unittest

from uddcache.udd import Udd
from uddcache.config import Config


class database(unittest.TestCase):
    def setUp(self):
        self.udd = Udd()

    def tearDown(self):
        self.udd = None

    def testDBTypes(self):
        """Test creating a Debian and derivative UDD instance"""
        self.assertTrue(Udd(distro='debian'))
        self.assertRaises(NotImplementedError, Udd,  distro='ubuntu')   # TODO: update when implemented
        self.assertRaises(ValueError, Udd,  distro='nosuchdistro')

    def testPassConfig(self):
        """Test loading a config file manually"""
        config = Config()
        self.assertTrue(Udd(config=config))

    def testRelease(self):
        """Test binding to a release and doing a lookup"""
        r = self.udd.BindRelease('sid', 'i386')
        self.assertTrue(r)
        r = self.udd.BindRelease(['stable', 'stable-backports'], 'i386')
        self.assertTrue(r)

    def testPackage(self):
        """Test binding to a binary package and doing a lookup"""
        r = self.udd.BindPackage('libc6', 'sid', 'i386')
        self.assertTrue(r)
        self.assertTrue(r.Found())

    def testSource(self):
        """Test binding to a source package and doing a lookup"""
        r = self.udd.BindSourcePackage('glibc', 'sid')
        self.assertTrue(r)
        self.assertTrue(r.Found())
        r = self.udd.BindSourcePackage('libc6', 'sid')
        self.assertTrue(r)
        self.assertTrue(r.Found())
        self.assertTrue(r.data['version'])

    def testBts(self):
        """Test binding to a source package and doing a lookup"""
        tracker = self.udd.Bts(False)
        self.assertFalse(tracker.include_archived)


###########################################################
if __name__ == "__main__":
    unittest.main()
