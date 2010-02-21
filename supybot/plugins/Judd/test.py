###
# Copyright (c) 2007, Mike O'Connor
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

###

from supybot.test import *

class DebianTestCase(PluginTestCase):
    plugins = ('Judd',)

    def testVersion(self):
        self.assertNotError('versions libc6')                   # all versions; show oldstable->experimental
        self.assertNotError('versions libc6 --release sid')     # one version; only show sid
        self.assertNotError('versions libc6 --arch amd64')      # one arch; show amd64 instead
        self.assertNotError('versions libc6 --release qwerty')  # no such release; should default to lenny
        self.assertNotError('versions libc6 --arch qwerty')     # no such arch; should default to i386
        self.assertNotError('versions nosuchpackage')           # package not found; no such package in the archive

    def testInfo(self):
        self.assertNotError('info libc6')                       # package info stable; only show stable
        self.assertNotError('info libc6 --release sid')         # package info sid; only show sid
        self.assertNotError('info nosuchpackage')               # package not found; no such package in the archive

    def testArch(self):
        self.assertNotError('arches libc6')                     # arch-dep package; lots of arches for libc6
        self.assertNotError('arches python')                    # arch:all package; all
        self.assertNotError('arches nosuchpackage')             # package not found; no such package in the archive

    def testDepends(self):
        self.assertNotError('depends texlive')                  # depends; some packages
        self.assertNotError('depends dpkg')                     # depends; no packages
        self.assertNotError('depends nosuchpackage')            # package not found; no such package in the archive

    def testRecommends(self):
        self.assertNotError('recommends python-pyx')            # recommends; a package
        self.assertNotError('recommends texlive')               # recommends; no packages
        self.assertNotError('recommends nosuchpackage')         # package not found; no such package in the archive

    def testSuggests(self):
        self.assertNotError('suggests texlive')                 # suggests; a package
        self.assertNotError('suggests locales')                 # suggests; no packages
        self.assertNotError('suggests nosuchpackage')           # package not found; no such package in the archive

    def testConflicts(self):
        self.assertNotError('conflicts python')                  # some conflicts; several packages
        self.assertNotError('conflicts texlive')                 # no conflicts; no packages conflict
        self.assertNotError('conflicts nosuchpackage')           # package not found; no such package in the archive

    def testProvides(self):
        self.assertNotError('provides postfix')                 # provided packages; m-t-a
        self.assertNotError('provides nosuchpackage')           # package not found; no such package in the archive

    def testRprovides(self):
        self.assertNotError('rprovides mail-transport-agent')   # find rproviders; several packages provide m-t-a
        self.assertNotError('rprovides nosuchpackage')          # no rproviders; no packages provide this

    def testSource(self):
        self.assertNotError('src libc6 --release lenny')        # source package; glibc has libc6 in lenny
        self.assertNotError('src libc6 --release sid')          # source package; eglibc has libc6 in sid
        self.assertNotError('src nosuchpackage')                # package not found; no such package in the archive

    def testBinaries(self):
        self.assertNotError('binaries python-defaults')         # list binary packages; several binary packages
        self.assertNotError('binaries pyxplot')                 # list binary packages; only one binary package
        self.assertNotError('binaries nosuchpackage')           # package not found; no such package in the archive

    def testBuilddep(self):
        self.assertNotError('builddep perl')                    # simple build-deps; B-D only
        self.assertNotError('builddep texlive')                 # complex build-deps; B-D and B-D-I
        self.assertNotError('builddep libc6')                   # build-deps by binary; give build-deps of (e)glibc package
        self.assertNotError('builddep nosuchpackage')           # package not found; no such package in the archive

    def testPopcon(self):
        self.assertNotError('popcon perl')                      # list popcon; popular package
        self.assertNotError('popcon nosuchpackage')             # package not found; no such package in the archive

    def testMaintainer(self):
        self.assertNotError('maintainer perl')                  # show maintainer; maintianer, uploader and changer
        self.assertNotError('maintainer nosuchpackage')         # package not found; no such package in the archive

    def testBugs(self):
        # this is known to be broken at present
        pass

    def testFile(self):
        self.assertNotError('file /usr/bin/perl')               # absolute file exists ; /usr/bin/perl in perl
        self.assertNotError('file bin/perl')                    # fragment file exists ; /usr/bin/perl in perl
        self.assertNotError('file *bin/perl*')                  # fragment file exists ; /usr/bin/perl in perl, /usr/bin/perldoc in perldoc
        self.assertNotError('file nvidia-glx')                  # fragment file exists in non-free; various nvidia package should match this
        self.assertNotError('file /nosuchpackage')              # fragment doesn't exist ; no package contains

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
