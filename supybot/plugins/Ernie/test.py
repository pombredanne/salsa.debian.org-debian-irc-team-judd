###
# Copyright (c) 2009, Stuart Prescott
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

class ErnieTestCase(PluginTestCase):
    plugins = ('Ernie',)

    # prevent supybot-test from deleting all the data
    cleanDataDir = False
       
    def testGrubMap(self):
        self.assertNotError('grub 12')
        self.assertNotError('grub 123')   # no such error code

    def testErrno(self):
        self.assertNotError('errno 2')      # EPERM
        self.assertNotError('errno 1234')   # no such error code
        self.assertNotError('errno EPIPE')  # error 33
        self.assertNotError('errno EPIPE123')   # no such error code

    def testHTTP(self):
        self.assertNotError('http 200')     # Continue
        self.assertNotError('http 404')     # Not found
        self.assertError('http 404a')       # illegal status code
        self.assertNotError('http 12345')   # no such status code

    def testSMTP(self):
        self.assertNotError('smtp 211')     # Continue
        self.assertError('smtp 123a')       # illegal status code
        self.assertNotError('smtp 12345')   # no such status code

    def testkey(self):
        self.assertNotError('gpg 16BA136C')     # backports.org key (8 chars)
        self.assertNotError('gpg 0x16BA136C')     # backports.org key (8 chars with 0x)
        self.assertNotError('gpg EA8E8B2116BA136C')     # backports.org key (full)
        self.assertNotError('gpg 16BA136D')     # unknown key
        self.assertError('gpg 16BA136Z')     # invalid key
        
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
