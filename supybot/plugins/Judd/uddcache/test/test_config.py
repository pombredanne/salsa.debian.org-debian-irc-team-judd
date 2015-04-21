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

"""Unit test for uddconfig.py"""

from __future__ import unicode_literals

import os
try:
    import unittest2 as unittest
except:
    import unittest

from uddcache.config import Config


class config(unittest.TestCase):
    def setUp(self):
        pass

    def testNoFileName(self):
        """Test no specified filename to load"""
        self.assertTrue(Config())
        self.assertRaises(ValueError, Config, skipDefaultFiles=True)

    def testGoodFileName(self):
        """Test loading of config file"""
        conf = Config("udd-cache.conf")
        self.assertTrue(conf)
        self.assertEqual(conf.db()['hostname'], 'localhost')

    def testBadFileName(self):
        """Test loading of non-existent config file"""
        self.assertRaises(IOError, Config, "/path/to/no/such/file")

    def testEnvironment(self):
        """Test loading config file from environment"""
        origEnv = False
        if 'UDD_CACHE_CONFIG' in os.environ:
            origEnv = os.environ['UDD_CACHE_CONFIG']
        os.environ['UDD_CACHE_CONFIG'] = "/path/to/no/such/file"
        self.assertRaises(IOError, Config)
        os.environ['UDD_CACHE_CONFIG'] = "udd-cache.conf"
        self.assertTrue(Config(skipDefaultFiles=True))
        os.environ['UDD_CACHE_CONFIG'] = ""
        self.assertRaises(ValueError, Config, skipDefaultFiles=True)
        if origEnv:
            os.environ['UDD_CACHE_CONFIG'] = origEnv
        else:
            os.unsetenv('UDD_CACHE_CONFIG')

    def testConfDict(self):
        """Test loading config via a dict"""
        origEnv = False
        cd = {'database': 'quux', 'username': 'foobar'}
        conf = Config(skipDefaultFiles=True, confdict=cd)
        self.assertTrue(conf)
        self.assertEqual(conf.get('database', 'database'), 'quux')
        self.assertEqual(conf.get('database', 'username'), 'foobar')

    def testConfigGet(self):
        conf = Config()
        self.assertEqual(conf.get('database', 'hostname', 'quux'), 'localhost')
        self.assertEqual(conf.get('nosuchsection', 'hostname', 'quux'), 'quux')
        self.assertEqual(conf.get('database', 'nosuchkey', 'quux'), 'quux')

    def testLogging(self):
        conf = Config()
        self.assertTrue(conf.db_logging())

###########################################################
if __name__ == "__main__":
    unittest.main()
