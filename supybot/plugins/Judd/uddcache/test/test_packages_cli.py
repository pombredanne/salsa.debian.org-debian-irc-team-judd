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

"""Unit test for cli.py"""

from __future__ import unicode_literals

import os
import sys
try:
    import unittest2 as unittest
except:
    import unittest
try:
    from StringIO import StringIO
except:
    from io import StringIO

from uddcache.packages_cli import Cli

#import codecs
#sys.stdout = codecs.getwriter('utf8')(sys.stdout)

exclude_slow_tests = 0
if 'UDD_SKIP_SLOW_TESTS' in os.environ and int(os.environ['UDD_SKIP_SLOW_TESTS']):
    #print "Skipping slow tests in %s" % __file__
    exclude_slow_tests = 1


class cliTests(unittest.TestCase):

    # TODO: these tests are overly minimal

    def setUp(self):
        class dummyOptions:
            def __init__(self):
                self.arch = None
                self.distro = 'debian'
                self.deptype = None
                self.release = None
                self.fromrelease = 'unstable'
                self.torelease = 'stable'
                self.withrecommends = True
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

    def testnotfound(self):
        self.assertTrue(self.cli.notfound("nosuchpackage") is None)
        self.assertTrue(self.cli.notfound("nosuchpackage", release="stable") is None)
        self.assertTrue(self.cli.notfound("nosuchpackage", arch="i386") is None)
        self.assertTrue(self.cli.notfound("nosuchpackage", arch="i386", release="stable") is None)
        self.assertTrue(self.cli.notfound("nosuchpackage", arch="i386", release="stable", message="foo %s bar %s") is None)
        self.assertRaises(TypeError, self.cli.notfound, "nosuchpackage", arch="i386", release="stable", message="bad format %s")
        self.assertRaises(TypeError, self.cli.notfound, "nosuchpackage", message="bad format %s")

    def testversions(self):
        self.assertTrue(self.cli.versions("versions", "dpkg", []) is None)
        self.assertTrue(self.cli.versions("versions", "dpkg", ["amd64"]) is None)
        self.assertTrue(self.cli.versions("versions", "sun-java6-jre", []) is None)
        self.assertTrue(self.cli.versions("versions", "nosuchpackage", []) is None)

    def testinfo(self):
        self.assertTrue(self.cli.info("info", "dpkg", []) is None)
        self.assertTrue(self.cli.info("info", "latexdraw", []) is None)
        self.assertTrue(self.cli.info("info", "nosuchpackage", []) is None)

    def testnames(self):
        self.assertTrue(self.cli.names("names", "dpkg*", []) is None)
        self.assertTrue(self.cli.names("names", "sun-java*", []) is None)
        self.assertTrue(self.cli.names("names", "nosuchpackage", []) is None)

    def testarchs(self):
        self.assertTrue(self.cli.archs("archs", "dpkg", []) is None)
        self.assertTrue(self.cli.archs("archs", "sun-java6-jre", []) is None)
        self.assertTrue(self.cli.archs("archs", "nosuchpackage", []) is None)

    def testrprovides(self):
        self.assertTrue(self.cli.rprovides("rprovides", "dpkg", []) is None)
        self.assertTrue(self.cli.rprovides("rprovides", "mail-transport-agent", []) is None)
        self.assertTrue(self.cli.rprovides("rprovides", "imagemagick", []) is None)
        self.assertTrue(self.cli.rprovides("rprovides", "nosuchpackage", []) is None)

    def testprovides(self):
        self.assertTrue(self.cli.provides("provides", "dpkg", []) is None)
        self.assertTrue(self.cli.provides("provides", "postfix", []) is None)
        self.assertTrue(self.cli.provides("provides", "nosuchpackage", []) is None)

    def testsource(self):
        self.assertTrue(self.cli.source("source", "dpkg", []) is None)
        self.assertTrue(self.cli.source("source", "libc6", []) is None)
        self.assertTrue(self.cli.source("source", "nosuchpackage", []) is None)

    def testbinaries(self):
        self.assertTrue(self.cli.binaries("binaries", "dpkg", []) is None)
        self.assertTrue(self.cli.binaries("binaries", "glibc", []) is None)
        self.assertTrue(self.cli.binaries("binaries", "nosuchpackage", []) is None)

    def testbuilddeps(self):
        self.assertTrue(self.cli.builddeps("builddeps", "perl", []) is None)
        self.assertTrue(self.cli.builddeps("builddeps", "texlive", []) is None)
        self.assertTrue(self.cli.builddeps("builddeps", "libc6", []) is None)
        self.assertTrue(self.cli.builddeps("builddeps", "nosuchpackage", []) is None)

    def testrelations(self):
        self.assertTrue(self.cli.relations("relations", "perl", []) is None)
        self.assertTrue(self.cli.relations("relations", "texlive", []) is None)
        self.assertTrue(self.cli.relations("relations", "libc6", []) is None)
        self.assertTrue(self.cli.relations("relations", "nosuchpackage", []) is None)

    def testdepends(self):
        self.assertTrue(self.cli.depends("depends", "perl", []) is None)
        self.assertTrue(self.cli.depends("recommends", "dpkg", []) is None)
        self.assertTrue(self.cli.depends("suggests", "dpkg", []) is None)
        self.assertTrue(self.cli.depends("enhances", "kipi-plugins", []) is None)
        self.assertTrue(self.cli.depends("conflicts", "libc6", []) is None)
        self.assertTrue(self.cli.depends("depends", "nosuchpackage", []) is None)

    def testrecent(self):
        self.assertTrue(self.cli.recent("recent", "pyx", []) is None)
        self.assertTrue(self.cli.recent("recent", "libc6", []) is None)
        self.assertTrue(self.cli.recent("recent", "nosuchpackage", []) is None)

    def testmaint(self):
        self.assertTrue(self.cli.maint("maint", "pyx", []) is None)
        self.assertTrue(self.cli.maint("maint", "pyx", ["0.10-0+nmu3"]) is None)
        self.assertTrue(self.cli.maint("maint", "libc6", []) is None)
        self.assertTrue(self.cli.maint("maint", "nosuchpackage", []) is None)

    def testpopcon(self):
        self.assertTrue(self.cli.popcon("popcon", "libc6", []) is None)
        self.assertTrue(self.cli.popcon("popcon", "nosuchpackage", []) is None)

    def testcheckdeps(self):
        self.assertTrue(self.cli.checkdeps("checkdeps", "libc6", []) is None)
        self.assertTrue(self.cli.checkdeps("checkdeps", "libdvdcss2", ["sid-multimedia"]) is None)
        self.assertTrue(self.cli.checkdeps("checkdeps", "drizzle", ["armhf", "sid"]) is None)
        self.assertTrue(self.cli.checkdeps("checkdeps", "nosuchpackage", []) is None)
        self.cli.options.deptype = ['suggests', 'depends']
        self.assertTrue(self.cli.checkdeps("checkdeps", "dpkg", []) is None)

    def testcheckbuilddeps(self):
        self.assertTrue(self.cli.checkbuilddeps("checkbuilddeps", "glibc", []) is None)
        self.assertTrue(self.cli.checkbuilddeps("checkbuilddeps", "libdvdcss", ["squeeze-multimedia"]) is None)
        self.assertTrue(self.cli.checkbuilddeps("checkbuilddeps", "stage", ["amd64", "sid"]) is None)
        self.assertTrue(self.cli.checkbuilddeps("checkbuilddeps", "nosuchpackage", []) is None)

    @unittest.skipIf(exclude_slow_tests, 'slow test')
    def testcheckinstall(self):
        self.assertTrue(self.cli.checkinstall("checkinstall", "libc6", []) is None)
        self.assertTrue(self.cli.checkinstall("checkinstall", "ffmpeg", ["sid-multimedia"]) is None)
        self.assertTrue(self.cli.checkinstall("checkinstall", "nosuchpackage", []) is None)
        self.cli.options.verbose = True
        self.assertTrue(self.cli.checkinstall("checkinstall", "libc6", []) is None)

    def testwhy(self):
        self.assertTrue(self.cli.why("why", "dpkg", ["libc6"]) is None)
        self.assertTrue(self.cli.why("why", "dpkg", ["dolphin"]) is None)
        self.assertTrue(self.cli.why("why", "nosuchpackage", ["nosuchpackage"]) is None)
        self.assertRaises(ValueError, self.cli.why, "why", "nosuchpackage", [])

    @unittest.skipIf(exclude_slow_tests, 'slow test')
    def testcheckbackport(self):
        """Test the checkbackport command"""
        self.assertTrue(self.cli.checkbackport("checkbackport", "java-imaging-utilities", []) is None)
        self.assertTrue(self.cli.checkbackport("checkbackport", "xserver-xorg-video-intel", []) is None)
        self.assertTrue(self.cli.checkbackport("checkbackport", "pyxplot", []) is None)
        self.assertTrue(self.cli.checkbackport("checkbackport", "libv4l-0", []) is None)
        self.assertTrue(self.cli.checkbackport("checkbackport", "libxfont1", []) is None)
        self.assertTrue(self.cli.checkbackport("checkbackport", "nosuchpackage", []) is None)

###########################################################
if __name__ == "__main__":
    unittest.main()
