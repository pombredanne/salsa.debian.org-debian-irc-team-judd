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

class PiccyPluginTestCase(PluginTestCase):
    plugins = ('Piccy',)
    
    # prevent supybot-test from deleting all the data
    cleanDataDir = False

    def testPCIname(self):
        self.assertNotError('pciname 82574L')     # [8086:10d3] 82574L Gigabit Network Connection
        self.assertError('pciname 825')           # require at least 4 chars in search
        self.assertNotError('pciname 8257')
        self.assertError('pciname 8..7')          # will sanitised down to 87 which is then an error
        self.assertNotError('pciname 82574.*')    # will be trimmed down to 82574
        self.assertNotError('pciname 82574L Gigabit')    # test spaces
        self.assertNotError('pciname "82574L  Gigabit"')    # test spaces
        self.assertNotError('pciname 82574L gigabit')    # test case sensitivity

    def testPCImap(self):
        self.assertNotError('pciid "[8086:4222]"')
        self.assertNotError('pciid "[8086:4222]" --release unstable')
        self.assertNotError('pciid "[1002:7145]"')                     # ATI card (fglrx)
        self.assertNotError('pciid "[1002:7145]" --release unstable')
        self.assertNotError('pciid 14e4:170c')
        self.assertNotError('pciid 14e4:170c --release unstable')
        self.assertNotError('pciid 168C:001B')                      # upper case
        self.assertNotError('pciid 8086:27b9')                      # multiple module matches
        self.assertNotError('pciid 8086:4229')                      # multiple wikifaq matches
        self.assertNotError('pciid 10de:1234')                      # nvidia device with PCI_ID_ANY in map
        self.assertNotError('pciid "[001c:0001]"')
        self.assertNotError('pciid ffff:0001')  # illegal vendor ID
        self.assertNotError('pciid 0069:0001')  # unknown vendor ID
        self.assertNotError('pciid 0070:0002')  # unknown device ID (start)
        self.assertNotError('pciid 0070:7445')  # unknown device ID (middle)
        self.assertNotError('pciid 0070:f000')  # unknown device ID (end)
        self.assertError('pciid 1:0011')      # malformed
        self.assertError('pciid 123:0011')    # malformed
        self.assertError('pciid qwe1:0011')   # malformed
        self.assertError('pciid 001c:123q')   # malformed

    def testConfigMap(self):
        self.assertNotError('kconfig FIRMWARE')    # matches some comments too
        self.assertNotError('kconfig CONFIG_GENERIC_CMOS_UPDATE')    # returns single hit, full module name
        self.assertNotError('kconfig PROC')                  # returns multiple hits, partial module name
        self.assertNotError('kconfig foobar')                        # fails to match
        self.assertNotError('kconfig CONFIG_SMB_FS --release etch')       # is set in etch
        self.assertNotError('kconfig CONFIG_SMB_FS --release lenny')    # fails to match (is not set)
        self.assertNotError('kconfig SMB --release lenny')      # fails to match (is not set)
        self.assertNotError('kconfig proc')      # allow case-insensitive matching

    def testVersionList(self):
        self.assertNotError('kversion')    # returns all versions
        self.assertNotError('kversion --release etch')  # returns a single release
        # test alases to the functions:
        self.assertNotError('kernelversion')    # returns all versions
        self.assertNotError('kernels')    # returns all versions

    def testUpdater(self):
        # disable this test for the sake of bandwidth usage
        #self.assertNotError('update')    # update the data
        True

    def testLastUpdate(self):
        self.assertNotError('lastupdate')

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
