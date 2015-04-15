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
from uddcache.bugs_cli import Cli

import codecs
sys.stdout = codecs.getwriter('utf8')(sys.stdout)


class cliTests(unittest.TestCase):

    # TODO: these tests are overly minimal

    def setUp(self):
        class dummyOptions:
            def __init__(self):
                self.distro = 'debian'
                self.verbose = False
        # gobble all stdout so that the tests can just be run without output
        # this is crude: it would be better to test that the output was correct
        # rather than just testing that the program doesn't crash on running
        # the code.
        # FIXME: replace these tests with doctest?
        # http://docs.python.org/library/doctest.html#doctest-unittest-api
        self.held, sys.stdout = sys.stdout, StringIO()
        self.cli = Cli(options=dummyOptions())

    def tearDown(self):
        sys.stdout = self.held
        self.cli = None

    def testbug(self):
        self.assertTrue(self.cli.bug("bug", "500000", []) is None)
        self.assertTrue(self.cli.bug("bug", "#500000", []) is None)
        self.assertTrue(self.cli.bug("bug", "999999999999", []) is None)
        self.assertTrue(self.cli.bug("bug", "9999999", []) is None)
        self.assertTrue(self.cli.bug("bug", "src:ktikz", []) is None)
        self.assertTrue(self.cli.bug("bug", "qtikz", []) is None)
        self.assertTrue(self.cli.bug("bug", "htdig", []) is None)
        self.assertTrue(self.cli.bug("bug", "nosuchpackage", []) is None)
        self.assertTrue(self.cli.bug("bug", "src:nosuchpackage", []) is None)
        self.assertTrue(self.cli.bug("bug", "src:pyxplot", ['ia64']) is None)
        self.assertTrue(self.cli.bug("bug", "pyxplot", ['ia64']) is None)
        self.cli.options.verbose = True
        self.assertTrue(self.cli.bug("bug", "qtikz", []) is None)
        self.assertTrue(self.cli.bug("bug", "src:ktikz", []) is None)
        self.assertTrue(self.cli.bug("bug", "postgresql-9.0", []) is None)

    def testrcbugs(self):
        self.assertTrue(self.cli.rcbugs("rcbugs", "ktikz", []) is None)
        self.assertTrue(self.cli.rcbugs("rcbugs", "eglibc", []) is None)
        self.assertTrue(self.cli.rcbugs("rcbugs", "libc6", []) is None)
        self.assertTrue(self.cli.rcbugs("rcbugs", "nosuchpackage", []) is None)

    def testwnpp(self):
        self.assertTrue(self.cli.wnpp("rfp", "levmar", []) is None)
        self.assertTrue(self.cli.wnpp("wnpp", "levmar", []) is None)
        self.assertTrue(self.cli.wnpp("orphan", "htdig", []) is None)
        self.assertTrue(self.cli.wnpp("rfp", "nosuchpackage", []) is None)

    def testrm(self):
        self.assertTrue(self.cli.rm("rm", "sun-java6", []) is None)
        self.assertTrue(self.cli.rm("rm", "nosuchpackage", []) is None)

    def testrfs(self):
        self.assertTrue(self.cli.rfs('rfs', '-', []) is None)
        self.assertTrue(self.cli.rfs('rfs', 'sks', []) is None) # FIXME: fragile test
        self.assertTrue(self.cli.rfs('rfs', 'nosuchpackage', []) is None)

###########################################################
if __name__ == "__main__":
    unittest.main()
