#!/usr/bin/env python
#
# Ultimate Debian Database query tool
#
# Test suite
#
###
#
# Copyright (c) 2010-2012  Stuart Prescott
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
from uddcache.bug_queries import Commands
from uddcache.bts import BugNotFoundError


class commands(unittest.TestCase):
    def setUp(self):
        self.udd = Udd()
        self.dispatcher = Commands(self.udd)

    def tearDown(self):
        self.udd = None
        self.dispatcher = None

    def testBug(self):
        self.assertTrue(self.dispatcher.bug(123456, False))
        self.assertTrue(self.dispatcher.bug(123456, True))
        self.assertRaises(BugNotFoundError, self.dispatcher.bug, 9999999, True)
        self.assertTrue(self.dispatcher.bug("123456", True))
        self.assertTrue(self.dispatcher.bug("#123456", True))

    def testBug_package(self):
        self.assertFalse(self.dispatcher.bug_package("when")) #no bugs
        self.assertTrue(self.dispatcher.bug_package("qtikz"))
        self.assertTrue(self.dispatcher.bug_package("src:ktikz"))
        self.assertTrue(self.dispatcher.bug_package("htdig"))
        self.assertFalse(self.dispatcher.bug_package("nosuchpacakge"))
        self.assertFalse(self.dispatcher.bug_package("src:nosuchpacakge"))

    def testBug_package_search(self):
        self.assertFalse(self.dispatcher.bug_package_search('ktikz', 'quux')) # no bugs
        self.assertTrue(self.dispatcher.bug_package_search('libc6', 'locales'))
        self.assertFalse(self.dispatcher.bug_package_search("nosuchpacakge", 'quux'))
        self.assertFalse(self.dispatcher.bug_package_search("src:nosuchpacakge", 'quux'))

    def testWnpp(self):
        bl = self.dispatcher.wnpp('levmar')
        self.assertEqual(len(bl), 1)
        self.assertEqual(bl[0].id, 546202)
        bl = self.dispatcher.wnpp('levmar', 'RFP')
        self.assertEqual(len(bl), 1)
        self.assertEqual(bl[0].id, 546202)
        bl = self.dispatcher.wnpp('levmar', 'ITP')
        self.assertEqual(len(bl), 0)
        bl = self.dispatcher.wnpp('python') # don't match partial package names
        self.assertEqual(len(bl), 0)

    def testRcbugs(self):
        bl = self.dispatcher.rcbugs('ktikz')
        self.assertEqual(len(bl), 0)    # has bugs but not rc bugs
        bl = self.dispatcher.rcbugs('eglibc')
        self.assertGreaterEqual(len(bl), 1)
        bl = self.dispatcher.rcbugs('libc6')   # test mapping to source package
        self.assertGreaterEqual(len(bl), 1)
        bl = self.dispatcher.rcbugs('nosuchpackage')
        self.assertEqual(len(bl), 0)

    def testRm(self):
        bl = self.dispatcher.rm('sun-java6')
        self.assertEqual(len(bl), 1)    # there are other RM requests of experimental packages too
        self.assertEqual(bl[0].id, 646524)
        bl = self.dispatcher.rm('nosuchpackage')
        self.assertEqual(len(bl), 0)

###########################################################
if __name__ == "__main__":
    unittest.main()
