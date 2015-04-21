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

""" Unit tests for bts UDD bindings """

from __future__ import unicode_literals

import sys
try:
    import unittest2 as unittest
except:
    import unittest

from uddcache.udd import Udd
from uddcache.bts import Bts, BugNotFoundError, Bugreport

# permit use of unicode() in py2 and str() in py3 to always get unicode results
if sys.version_info > (3, 0):
    unicode = str


class BtsTests(unittest.TestCase):

    def setUp(self):
        self.udd = Udd()
        self.bts = self.udd.Bts(True)
        self.btsc = self.udd.Bts(False)

    def tearDown(self):
        self.bts = None
        self.btsc = None
        self.udd = None

    def testBugs(self):
        bugs = [500000, 500001, 500002, 666666]
        self.assertTrue(self.bts.bugs(bugs))
        self.assertEqual(len(self.bts.bugs(bugs)), 4)
        self.assertEqual(len(self.btsc.bugs(bugs)), 0)

    def testBug(self):
        b = self.bts.bug(500000)
        self.assertTrue(b)
        self.assertEqual(b.title, "cdbs: Please add dh_installdefoma in debhelper.mk")
        self.assertEqual(b.id, 500000)
        self.assertEqual(b.severity, "wishlist")
        self.assertEqual(b.status, "done")
        self.assertEqual(b.archived, True)
        self.assertTrue(self.bts.bug("500000"))
        self.assertTrue(self.bts.bug("544925"))
        self.assertTrue(self.bts.bug("#500000"))
        self.assertRaises(BugNotFoundError, self.bts.bug, -1)
        self.assertRaises(BugNotFoundError, self.bts.bug, 99999999)
        self.assertRaises(BugNotFoundError, self.btsc.bug, 500000) # bug is archived

    def test_get_bugs(self):
        self.assertTrue(self.bts.get_bugs({'package': 'latexdraw'}))
        self.assertTrue(self.bts.get_bugs({'package': 'pyx'}))  # package -> source mapping
        self.assertTrue(self.btsc.get_bugs({'title': 'RM: '}))
        self.assertTrue(self.bts.get_bugs({'source': 'latexdraw'}))
        self.assertFalse(self.btsc.get_bugs({'source': 'spline'}))
        self.assertTrue(self.bts.get_bugs({'source': 'latexdraw', 'sort': 'id DESC'}))
        self.assertEqual(len(self.bts.get_bugs({'source': 'latexdraw', 'limit':1})), 1)

    def test_get_bugs_tags(self):
        b = self.bts.bug(2297)
        self.bts.get_bugs_tags(b)
        self.assertEqual(len(b.tags), 1)
        bl = self.bts.bugs([500000, 500001, 500002, 620381])
        self.bts.get_bugs_tags(bl)


class BugReportTests(unittest.TestCase):
    def test_load(self):
        b = Bugreport()
        self.assertEqual(b.id, None)
        self.assertEqual(b.title, None)
        self.assertEqual(b.package, None)
        data = {
                'id': 12345,
                'package': 'foo',
                'title' : 'a really nasty bug'
                }
        b = Bugreport(data)
        self.assertEqual(b.id, 12345)
        self.assertEqual(b.package, 'foo')

    def test_readable_status(self):
        self.assertEqual(Bugreport({'status': 'pending'}).readable_status, 'open')
        self.assertEqual(Bugreport({'status': 'pending-fixed'}).readable_status, 'pending')
        self.assertEqual(Bugreport({'status': 'fixed'}).readable_status, 'fixed')

    def test_wnpp_type(self):
        self.assertEqual(Bugreport({'package': 'wnpp', 'title': 'ITA: somepackage -- the description'}).wnpp_type, 'ITA')
        self.assertEqual(Bugreport({'package': 'wnpp', 'title': 'RFP -- somepackage -- the description'}).wnpp_type, 'RFP')
        self.assertEqual(Bugreport({'package': 'wnpp', 'title': 'some other badly titled bug'}).wnpp_type, None)
        self.assertRaises(ValueError, getattr, Bugreport(), 'wnpp_type')

    def test_str(self):
        data = {
                'id': 12345,
                'package': 'foo',
                'title' : 'a really nasty bug'
                }
        b = Bugreport(data)
        self.assertTrue(str(b))
        b.tags = ['help']
        self.assertTrue(str(b))
        b.tags = ['help', 'moreinfo']
        self.assertTrue(str(b))


class BugNotFoundErrorTests(unittest.TestCase):
    def test_str(self):
        e = BugNotFoundError(12345)
        self.assertIn('12345', str(e))
        e = BugNotFoundError("12345")
        self.assertIn('12345', str(e))


###########################################################
if __name__ == "__main__":
    unittest.main()
