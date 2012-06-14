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

"""Unit test for cli.py"""

import os
import sys
import unittest2 as unittest
from cStringIO import StringIO
from uddcache.clibase import CliBase

import codecs
sys.stdout = codecs.getwriter('utf8')(sys.stdout)

includeSlowTests = 1
if os.environ.has_key('UDD_SKIP_SLOW_TESTS') and int(os.environ['UDD_SKIP_SLOW_TESTS']):
    #print "Skipping slow tests in %s" % __file__
    includeSlowTests = 0


class cliTests(unittest.TestCase):

    # TODO: these tests are overly minimal

    def setUp(self):
        class dummyOptions:
            def __init__(self):
                self.distro = 'debian'
                self.verbose = False
        class dummyDispatcher:
            def __init__(self, initialiser):
                pass
        # gobble all stdout so that the tests can just be run without output
        # this is crude: it would be better to test that the output was correct
        # rather than just testing that the program doesn't crash on running
        # the code.
        # FIXME: replace these tests with doctest?
        # http://docs.python.org/library/doctest.html#doctest-unittest-api
        self.held, sys.stdout = sys.stdout, StringIO()
        self.cli = CliBase(options=dummyOptions(), dispatcherClass=dummyDispatcher)

    def tearDown(self):
        sys.stdout = self.held
        self.cli = None

    def test_init(self):
        self.assertRaises(ValueError, CliBase)

    def _dummy_func(self, package, args, options):
        return True

    def testis_valid_command(self):
        self.cli.command_map = {'versions': self._dummy_func}
        self.cli.command_aliases = {'show': 'versions'}
        self.assert_(self.cli.is_valid_command("versions"))
        self.assert_(self.cli.is_valid_command("show"))    # test an alias
        self.assertFalse(self.cli.is_valid_command("nosuchcommand"))

    def testrun(self):
        self.cli.command_map = {'versions': self._dummy_func}
        self.cli.command_aliases = {'show': 'versions'}
        self.assert_(self.cli.run("versions", "dpkg", []) is None)
        self.assert_(self.cli.run("show", "dpkg", []) is None)
        self.assertRaises(ValueError, self.cli.run, "nosuchcommand", "", [])

###########################################################
if __name__ == "__main__":
    unittest.main()
