###
# Copyright (c) 2007, Mike O'Connor
# Copyright (c) 2009,2011 Stuart Prescott
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

    def __init__(self, *args,  **kwargs):
        PluginTestCase.__init__(self, *args, **kwargs)
        self.timeout = 60.   # bump up the timeout to 60s
        # don't delete data prior to running the tests
        self.cleanConfDir = False
        self.cleanDataDir = False


    def testVersion(self):
        self.assertNotError('versions libc6')                   # all versions; show oldstable->experimental
        self.assertNotError('versions libc6 --release sid')     # one version; only show sid
        self.assertNotError('versions libc6 --arch amd64')      # one arch; show amd64 instead
        self.assertNotError('versions libc6 --release qwerty')  # no such release; defaults to lenny
        self.assertNotError('versions libc6 --arch qwerty')     # no such arch; defaults to i386
        self.assertNotError('versions libc6 amd64')             # implicit arch; show amd64 instead of i386
        self.assertNotError('versions libc6 sid')               # implicit release; show sid only
        self.assertNotError('versions libc6 amd64 sid')         # implicit release; show amd64,sid only
        self.assertNotError('versions nosuchpackage')           # package not found; no such package in the archive

    def testNames(self):
        self.assertNotError('names libc6')                      # exact match; one package only (libc6)
        self.assertNotError('names libc6*')                     # terminal wildcard; lots of packages (libc6, libc6-dev, ....)
        self.assertNotError('names latexdraw --release sid')    # release selection; only in sid
        self.assertNotError('names libc6.1 --arch ia64')        # arch selection; only in amd64
        self.assertNotError('names nosuchpackage')              # package not found; no such package in the archive

    def testInfo(self):
        self.assertNotError('info libc6')                       # package info stable; only show stable
        self.assertNotError('info libc6 --release sid')         # package info sid with homepage; only show sid, include homepage URL too
        self.assertNotError('info libc6 --arch amd64')          # package info amd64; only show sid
        self.assertNotError('info synaptic')                    # package info with screenshot; include screenshot URL too
        self.assertNotError('info htdig')                       # package info with WNPP bug; include bug number too
        self.assertNotError('info nosuchpackage')               # package not found; no such package in the archive

    def testArch(self):
        self.assertNotError('archs libc6')                      # arch-dep package; lots of arches for libc6
        self.assertNotError('archs python')                     # arch:all package; all
        self.assertNotError('archs nosuchpackage')              # package not found; no such package in the archive

    def testConflicts(self):
        self.assertNotError('conflicts python')                  # some conflicts; several packages
        self.assertNotError('conflicts texlive')                 # no conflicts; no packages conflict
        self.assertNotError('conflicts nosuchpackage')           # package not found; no such package in the archive

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

    def testProvides(self):
        self.assertNotError('provides postfix')                 # provided packages; m-t-a
        self.assertNotError('provides nosuchpackage')           # package not found; no such package in the archive

    def testRprovides(self):
        self.assertNotError('rprovides mail-transport-agent')   # find rproviders; several packages provide m-t-a
        self.assertNotError('rprovides imagemagick')            # find rproviders real package; a real package as well as being "provided"
        self.assertNotError('rprovides libc6')                  # real package only; a real package only, not provided by anything
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

    def testCheckDeps(self):
        self.assertNotError('checkdeps libc6')                  # all dependencies present; all depends, recommends and suggests are fulfilled
        self.assertNotError('checkdeps openjdk-6-jre-headless --release lenny')  # missing recommends; package ca-certificates-java is recommended but not in lenny
        self.assertNotError('checkdeps openjdk-6-jre-headless')  # check release selection; all relations fulfilled
        self.assertNotError('checkdeps ffmpeg --release lenny-multimedia')  # check release fallback; all relations fulfilled only if fallback to main archive
        self.assertNotError('checkdeps nosuchpackage')          # package not found; no such package in the archive
        self.assertNotError('checkdeps libc6 --type depends')   # check relation type; check that depends are selectable
        self.assertNotError('checkdeps libc6 --type recommends')  # check relation type; check that recommends are selectable
        self.assertError('checkdeps dpkg --type nosuchrelation')  # package not found; no such package in the archive

    def testCheckBuildDeps(self):
        self.assertNotError('checkbuilddeps eglibc --release sid')  # source package selection; build-deps are fulfilled
        self.assertNotError('checkbuilddeps stage --release sid')   # source package selection; build-deps are uninstallable
        self.assertNotError('checkbuilddeps libc6')             # binary package selection; build-deps are fulfilled
        self.assertNotError('checkbuilddeps ffmpeg --release lenny-multimedia')  # fallback to official repo; all build-deps are fulfilled but only if lenny itself is included
        self.assertNotError('checkbuilddeps nosuchpackage')     # package not found; no such package in the archive

    def testCheckInstall(self):
        self.assertNotError('checkinstall libc6')               # installable package; default release
        self.assertNotError('checkinstall libc6 --release sid') # installable package, select release
        self.assertNotError('checkinstall when')                # installable package, no dependencies
        self.assertNotError('checkinstall openjdk-6-jre-headless --norecommends --release lenny') # installable package; all installable without recommends
        self.assertNotError('checkinstall openjdk-6-jre-headless --release lenny') # missing recommends in lenny; ca-certificates missing from recommends chain
        self.assertNotError('checkinstall nosuchpackage')       # package not found; no such package in the archive

    def testCheckbackport(self):
        self.assertNotError('checkbackport debhelper')          # simple sid backport; all build-deps should be fulfilled
        self.assertNotError('checkbackport iceweasel')          # backport requires bpo as well; all build-deps should be fulfilled with some from backports.org
        self.assertNotError('checkbackport iceweasel --torelease lenny')  # backport not possible; impossible build-deps even with backports
        self.assertNotError('checkbackport xserver-xorg-video-intel') # from/to release selection; only possible backport with backports
        self.assertNotError('checkbackport python-pyx')         # bin2src autoselection; simple backport
        self.assertNotError('checkbackport debhelper --verbose') # verbose output; single release used
        self.assertNotError('checkbackport heartbeat --verbose') # verbose output; multiple releases used
        self.assertNotError('checkbackport nosuchpackage')      # package not found; no such package in the archive

    def testWhy(self):
        self.assertNotError('why dpkg libc6')                   # many links; several links found
        self.assertNotError('why dpkg libc6.1 --arch ia64')     # many links; requires right arch
        self.assertNotError('why dpkg libc6-i686')              # one link; recommends used in link
        self.assertNotError('why dpkg libc6-i686 --norecommends') # no link; no link without recommends
        self.assertNotError('why nosuchpackage nosuchpackage')  # package not found; no such package in the archive
        self.assertNotError('why dpkg nosuchpackage')           # package not found; no such package in the archive
        self.assertNotError('why nosuchpackage dpkg')           # package not found; no such package in the archive

    def testPopcon(self):
        self.assertNotError('popcon perl')                      # list popcon; popular package
        self.assertNotError('popcon nosuchpackage')             # package not found; no such package in the archive

    def testMaintainer(self):
        self.assertNotError('maint perl')                  # show maintainer; maintianer, uploader and changer
        self.assertNotError('maint python-pyx')            # auto bin2src test; maintianer, uploader and changer for source package pyx
        self.assertNotError('maint nosuchpackage')         # package not found; no such package in the archive

    def testRecent(self):
        self.assertNotError('recent perl')                      # show recent upload; last 10 uploads of perl
        self.assertNotError('recent python-pyx')                # auto bin2src test; show last 10 uploads of pyx
        self.assertNotError('recent nosuchpackage')             # package not found; no such package in the archive

    def testBugs(self):
        self.assertNotError('bug 599019')                       # open bug; open and important
        self.assertNotError('bug 584031')                       # archived bug; archived and grave
        self.assertNotError('bug 644230')                       # pending upload bug; see "open" and "pending"
        self.assertNotError('bug 9999999')                      # bug not found; no such bug in the bts
        self.assertNotError('bug ktikz')                        # no bugs; no bugs found
        self.assertNotError('bug qtikz')                        # buggy no wnpp; show bug list
        self.assertNotError('bug htdig')                        # buggy incl wnpp; show bug list and orphaned bug
        self.assertNotError('bug postgresql-9.0')               # buggy incl RM; show bug list and RM bug
        self.assertNotError('bug nosuchpackage')                # package not found; no such package in the bts
        self.assertNotError('bug levmar')                       # package not found but in wnpp; show only wnpp
        self.assertNotError('bug src:pyxplot ia64')             # title search; bug matches
        self.assertNotError('bug src:pyxplot nosuchtitle')      # title search; no matches

    def testRcBugs(self):
        self.assertNotError('bug rc pyxplot')                   # no rc bugs; none found
        self.assertNotError('bug rc eglibc')                    # rc bugs; match via source package name
        self.assertNotError('bug rc libc6')                    # rc bugs; match via binary package name
        self.assertNotError('bug rc nosuchpackage')             # package not found; no such package in the archive

    def testRm(self):
        self.assertNotError('bug rm sun-java6')                    # removed from archive; removal reason found
        self.assertNotError('bug rm nosuchpackage')                # package doesn't exist; no removal reason found
        self.assertNotError('bug rm pyxplot')                      # package not removed; no removal reason found

    def testWnpp(self):
        self.assertNotError('bug wnpp levmar')                     # RFP filed; RFP details displayed
        self.assertNotError('bug wnpp nosuchpackage')              # no WNPP bug exists; no bug displayed
        self.assertNotError('bug wnpp a')                          # no WNPP bug exists; no bug displayed
        self.assertNotError('bug wnpp levmar --type rfp')          # explicitly require RFP bug; display RFP bug
        self.assertNotError('bug wnpp levmar --type o')            # explicitly require O bug; no bug displayed
        self.assertNotError('bug wnpp levmar --type nosuchtype')   # bogus type given; type ignored

    def testRfs(self):
        self.assertNotError('bug rfs -')                           # Lots of RFS match; only summary displayed
        self.assertNotError('bug rfs sks')                         # One RFS match; show bug summary #FIXME: fragile
        self.assertNotError('bug rfs nosuchpackage')               # No RFS match; no bug displayed

    def testFile(self):
        # TODO: test other architectures and releases as well
        self.assertNotError('file /usr/bin/perl')               # absolute file exists ; /usr/bin/perl in perl
        self.assertNotError('file /usr/bin/perl --release sid') # absolute file exists in sid; /usr/bin/perl in perl
        self.assertNotError('file /lib/firmware/3com/typhoon.bin --release sid') # absolute file exists in sid/non-free; lib/firmware/3com/typhoon.bin in firmware-linux-nonfree
        self.assertNotError('file bin/perl')                    # fragment file exists ; /usr/bin/perl in perl
        self.assertNotError('file *bin/perl*')                  # fragment file exists ; /usr/bin/perl in perl, /usr/bin/perldoc in perldoc
        self.assertNotError('file *bin/*')                      # small file fragment ; should trip "truncated" message
        self.assertNotError('file /nosuchpackage')              # fragment doesn't exist ; no package contains

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
