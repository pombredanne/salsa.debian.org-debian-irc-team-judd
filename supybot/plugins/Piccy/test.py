###
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

# Note that the comments for each test are structured as:
#
#    self.assertNotError('test command')  # short test description ; test result
#
# this is designed to allow the tests to be run semi-interactively through 
# some RPC interaction with an IRC client.

from supybot.test import *

class PiccyPluginTestCase(PluginTestCase):
    plugins = ('Piccy',)
    
    # prevent supybot-test from deleting all the data
    cleanDataDir = False

    def testPCIname(self):
        self.assertNotError('pciname 82574L')     # single hit; matches [8086:10d3] 82574L Gigabit Network Connection
        self.assertNotError('pciname 8257')       # multiple hits; matches [8086:105e] '82571EB Gigabit Ethernet Controller' and a lot of other devices
        self.assertNotError('pciname centaur')    # match not at start of devname; [13d1:ab02] 'ADMtek Centaur-C rev 17 [D-Link DFE-680TX] CardBus Fast Ethernet Adapter' and three others
        self.assertError('pciname 825')           # minimum search string length; at least 4 chars in required in search
        self.assertError('pciname 8..7')          # minimum search string length; at least 4 chars in required in search (will sanitised down to 87 which is then an error)
        self.assertNotError('pciname 82574.*')    # escape bad characters ; No matches
        self.assertNotError('pciname 82574L Gigabit')    # single space in arguments; matches [8086:10d3] '82574L Gigabit Network Connection' amongst others.
        self.assertNotError('pciname "82574L  Gigabit"') # multiple spaces in arguments; matches [8086:10d3] '82574L Gigabit Network Connection' amongst others.
        self.assertNotError('pciname 82574L gigabit')    # case sensitivity; [8086:10d3] '82574L Gigabit Network Connection' amongst others

    def testPCImap(self):
        self.assertNotError('pciid 14e4:170c')        # simple test ; 'BCM4401-B0 100Base-TX' to b44 module with no wiki link
        self.assertNotError('pciid 14e4:170c --release unstable') # different release ; 'BCM4401-B0 100Base-TX' to b44 module with no wiki link
        self.assertNotError('pciid 168C:001B')        # case sensitivity ; 'AR5413 802.11abg NIC' ath5k
        self.assertNotError('pciid 8086:27b9')        # multiple module matches ; intel-rng and iTCO_wdt
        self.assertNotError('pciid 8086:4229')        # multiple wikifaq matches ; wikifaq: iwlwifi iwlagn
        self.assertNotError('pciid 10de:1234')        # PCI_ID_ANY module ; nvidia device with PCI_ID_ANY in map for out-of-tree nvidia driver
        #self.assertNotError('pciid 1904:8139 --release etch')      # fallthru to sid ; RTL8139D has no match in etch, matches sc92031 in sid
        self.assertNotError('pciid "[8086:4222]"')    # pciid wrapped in brackets ; 'PRO/Wireless 3945ABG [Golan] Network Connection'. Should include wikilink for iwlwifi.
        self.assertNotError('pciid "[8086:4222]" --release unstable') # check driver in sid ; 'PRO/Wireless 3945ABG [Golan] Network Connection'. Should include wikilink for iwlwifi.
        self.assertNotError('pciid "[1002:7145]"')    # non-free driver ; 'Radeon Mobility X1400' with in kernel ati-agp module and out-of-tree fglrx and wikilink for fglrx
        self.assertNotError('pciid "001c:0001"')      # no matches ; no matches in any distro
        self.assertNotError('pciid ffff:0001')        # illegal vendor ID ; unknown device from illegal vendor id
        self.assertNotError('pciid 0069:0001')  # unknown vendor ID ; 'Unknown device' from 'Unknown vendor'
        self.assertNotError('pciid 0070:0002')  # unknown device ID (start) ; 'Unknown device'
        self.assertNotError('pciid 0070:7445')  # unknown device ID (middle) ; 'Unknown device'
        self.assertNotError('pciid 0070:f000')  # unknown device ID (end) ; 'Unknown device'
        self.assertError('pciid 1:0011')        # malformed pciid ; vendor id too short
        self.assertError('pciid 123:0011')      # malformed pciid ; vendor id too short
        self.assertError('pciid qwe1:0011')     # malformed pciid ; vendor id bad characters
        self.assertError('pciid 001c:123q')     # malformed pciid ; device id bad characters

    def testXorgMap(self):
        self.assertNotError('xorg 1002:7145')    # single match ; radeon and radeonhd
        self.assertNotError('xorg 1002:9442')    # no matches ; no matches in either lenny or sid
        self.assertNotError('xorg 1106:1122')    # fallthru ; no match in lenny, matches openchrome in sid 

    def testConfigMap(self):
        self.assertNotError('kconfig CONFIG_GENERIC_CMOS_UPDATE')    # single hit ; returns single hit, full module name
        self.assertNotError('kconfig PROC')      # multiple hits ; several partial matches
        self.assertNotError('kconfig proc')      # case sensitive ; case-insensitive matching, several partial matches
        self.assertNotError('kconfig FIRMWARE')  # avoid comments ; shoudn't return comments with firmware
        self.assertNotError('kconfig foobar')    # no match ; fails to match
        #self.assertNotError('kconfig CONFIG_SMB_FS --release etch')  # match in release ; only set in etch
        self.assertNotError('kconfig CONFIG_SMB_FS --release lenny') # match in release ; not set in lenny

    def testVersionList(self):
        self.assertNotError('kernels')    # kernel versions ; returns all versions from oldstable to trunk
        self.assertNotError('kernels --release lenny')  # single release ; returns a single release
        self.assertNotError('kernel')     # kernels alias ; returns all versions

    def testUpdater(self):
        # disable this test for the sake of bandwidth usage
        #self.assertNotError('update')    # update the data
        True

    def testLastUpdate(self):
        self.assertNotError('lastupdate')  # last update ; print date and time of last update

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
