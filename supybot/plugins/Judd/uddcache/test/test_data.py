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

""" Unit tests for data """

# Fairly sparse tests at this stage

from __future__ import unicode_literals

from uddcache.data import DebianData

try:
    import unittest2 as unittest
except:
    import unittest


class data(unittest.TestCase):
    def setUp(self):
        pass

    def testDebian(self):
        """Test switching to Debian data sets"""
        dat = DebianData()
        self.assertEqual(dat.release_map['unstable'], 'sid')
        self.assertTrue('i386' in dat.arches)
        self.assertTrue('sid' in dat.releases)

    def testReleaseName(self):
        """Test manipulations of the release names"""
        self.assertEqual(DebianData.clean_release_name('sid'), 'sid')
        self.assertEqual(DebianData.clean_release_name('unstable'), 'sid')
        self.assertEqual(DebianData.clean_release_name('nosuchrelease', default="quux"), 'quux')
        self.assertEqual(DebianData.clean_release_name(args=['a', 'sid', 'argument']), 'sid')
        self.assertEqual(DebianData.clean_release_name(args=['a', 'nonsid', 'argument'], default='quux'), 'quux')
        self.assertEqual(DebianData.clean_release_name(optlist=[('option', 'value'), ('release', 'sid')]), 'sid')
        self.assertEqual(DebianData.clean_release_name(optlist=[('option', 'value')], default='quux'), 'quux')
        self.assertEqual(DebianData.clean_release_name(optlist=[('want', 'sid'), ('release', 'stable')], optname='want'), 'sid')

    def testDependRelease(self):
        """Test finding dependent releases"""
        self.assertEqual(DebianData.list_dependent_releases('nosuchrelease'), [])
        self.assertEqual(DebianData.list_dependent_releases('sid'), ['sid'])
        self.assertNotEqual(DebianData.list_dependent_releases('squeeze'), ['sid'])
        self.assertEqual(DebianData.list_dependent_releases('squeeze-backports'), ['squeeze-backports', 'squeeze'])
        self.assertEqual(DebianData.list_dependent_releases('squeeze-backports', include_self=False), ['squeeze'])
        self.assertEqual(DebianData.list_dependent_releases('squeeze', suffixes=['security', 'backports']), ['squeeze', 'squeeze-security', 'squeeze-backports'])
        self.assertEqual(DebianData.list_dependent_releases('sid', suffixes=['security', 'backports']), ['sid'])
        # experimental is an overlay to sid
        self.assertEqual(DebianData.list_dependent_releases('experimental'), ['experimental', 'sid'])
        # also support release names
        self.assertEqual(DebianData.list_dependent_releases('stable-backports'), ['wheezy-backports', 'wheezy'])

    def testArchName(self):
        """Test manipulations of the arch names"""
        self.assertEqual(DebianData.clean_arch_name('amd64'), 'amd64')
        self.assertEqual(DebianData.clean_arch_name('nosucharch', default="hppa"), 'hppa')
        self.assertEqual(DebianData.clean_arch_name(args=['a', 'powerpc', 'argument']), 'powerpc')
        self.assertEqual(DebianData.clean_arch_name(args=['a', 'non-i386', 'argument'], default='quux'), 'quux')
        self.assertEqual(DebianData.clean_arch_name(optlist=[('option', 'value'), ('arch', 'powerpc')]), 'powerpc')
        self.assertEqual(DebianData.clean_arch_name(optlist=[('option', 'value')], default='quux'), 'quux')
        self.assertEqual(DebianData.clean_arch_name(optlist=[('want', 'amd64'), ('arch', 'hppa')], optname='want'), 'amd64')

if __name__ == "__main__":
    unittest.main()
