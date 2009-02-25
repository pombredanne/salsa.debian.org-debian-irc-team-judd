###
# Copyright (c) 2009 Stuart Prescott
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

# TODO:
# usbids => device + module?

import supybot.conf as conf
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks

import re
import os

# All data files are stored using the release code names (right half of the
# mapping) but this mapping also allows users to search using the release
# status name. Note that to handle minor releases like "etchnhalf" use
# a second entry such as "stable1". This map is also used for the input
# sanitisation of the release argument -- if it's not in this map, it is
# ignored.
release_map = { 'trunk'       : 'trunk',
                'unstable'    : 'sid',
                'testing'     : 'squeeze',
                'stable'      : 'lenny',
                'oldstable1'  : 'etchnhalf',
                'oldstable'   : 'etch' }

#verbose = True
verbose = False

class Piccy(callbacks.Plugin):
    """A plugin for matching PCI-Ids with kernel modules and for looking up kernel config options"""

    def __init__(self, irc):
        self.__parent = super(Piccy, self)
        self.__parent.__init__(irc)

    def pciid(self, irc, msg, args, pciid, optlist):
        """
        Output the name of the device and matching kernel module if known.
        Usage: "pciid pattern [--release etch]" where the pattern should be of the form 0000:0000
        """

        release = ""

        for (option,arg) in optlist:
            if option == 'release':
                release = arg

        release = self.cleanreleasename(release)

        vendor, device = self.splitpciid(pciid)
        #print "vendor = '%s', device = '%s'" % (vendor, device)

        if vendor == 0 or device == 0:
            irc.error("I don't know what you mean by PCI Id '%s'. 0000:0000 is my preferred format where both vendor Id and device Id are are in hexadecimal." % pciid)
            return

        vname,dname = self.findname(vendor, device)
        if vname is None and dname is None:
            irc.error("Error looking up PCI Id.")
            return

        module = self.findmodule(vendor, device, release)
        if module is None:
            moduletext = self.bold("[Error looking up module list]") + '.'
        elif module == "":
            modulefalltext=""
            fallback = self.cleanreleasename(self.registryValue('fallback_release'))
            if release != fallback:
                # no matching module found.
                module = self.findmodule(vendor, device, fallback)
                if module is None:
                    modulefalltext = self.bold(" [Error looking up module list for %s]" % fallback)
                elif module == "":
                    modulefalltext = " or in %s" % fallback
                else:
                    modulefalltext = " but has kernel module '%s' in %s" % (self.bold(module), self.bold(fallback))
            moduletext = "with no known kernel module in %s%s." % (release, modulefalltext)
        else:
            moduletext = "with kernel module '%s' in %s." % (self.bold(module), self.bold(release))

        hcllink = self.registryValue('hcl_url') % ( "%s:%s" % (vendor, device))

        reply = "[%s:%s] is '%s' from '%s' %s See also %s" % (vendor, device, dname, vname, moduletext, hcllink)

        if verbose:
            print
            print reply

        irc.reply(reply)

    pciid = wrap(pciid, ['something', getopts( { 'release':'something' } ) ] )


    def kconfig(self, irc, msg, args, pattern, optlist):
        """
        Outputs the kernel configs that match the given pattern.
        Usage: "kconfig pattern [--release etch]". The pattern will have wildcards automatically added around it.
        """

        release = ""

        for (option,arg) in optlist:
            if option == 'release':
                release = arg

        release = self.cleanreleasename(release)

        configlist = self.getkconfig(pattern, release)

        if configlist is None:
            irc.error("Error looking up config list for release %s." % release)
            return

        if len(configlist) == 0:
            configtext = self.bold('no results')
        else:
            #print configlist
            configtext = ' '.join(configlist)

        reply = "Searching for '%s' in %s kernel config gives %s." % (self.bold(pattern), self.bold(release), configtext)

        if verbose:
            print
            print reply

        irc.reply(reply)

    kconfig = wrap(kconfig, ['something', getopts( { 'release':'something' } ) ] )


    def kversion(self, irc, msg, args, optlist):
        """
        Outputs the kernel versions in the archive.
        Usage: "kversion [--release etch]".
        """

        release = None

        for (option,arg) in optlist:
            if option == 'release':
                release = arg

        versions = self.findkernels(release)

        versionstrings = []
        if len(versions) > 0:
            for v in versions:
                versionstrings.append("%s: %s (%s)"
                                    % (self.bold(v["release"]),
                                       v["uname"],
                                       v["version"]))
            reply = "Available kernel versions are: " + ("; ".join(versionstrings))
        else:
            reply = "No kernel versions found."

        if verbose:
            print
            print reply

        irc.reply(reply)

    kversion = wrap(kversion, [ getopts( { 'release':'something' } ) ] )


    def findname(self, vendor, device):
        """
        /usr/share/misc/pci.ids
        """
        mapfile = self.registryValue('pci_map')
        path    = self.registryValue('base_path')
        data    = conf.supybot.directories.data()

        mapfile = os.path.join(data, path, mapfile)
        try:
            idmap = open(mapfile, 'r')
        except IOError, e:
            self.log.error(str(e))
            return None, None

        found = False
        vname = "Unknown vendor"
        dname = "Unknown device"

        for line in idmap:
            #print line
            if len(line) < 4 or line[0] == '#': continue
            if line[0:4] == vendor:
                vname = line[5:].strip()
                #print "Match line: %s" % line
                found = True
                break
            elif line[0:3] > vendor:
                break

        # only look for a device name if the vendor id was matched
        if found:
            for line in idmap:
                #print line
                if len(line) < 4 or line[0] == '#': continue
                if line[0] != "\t": break
                line = line.strip()
                if line[0:4] == device:
                    dname=line[6:]

        idmap.close()
        #print "Found: [%s:%s] => (%s) (%s)" % (vendor, device, vname, dname)
        return vname,dname


    def findmodule(self, vendor, device, release):
        """
        Search through a /lib/modules/$(uname -r)/modules.pcimap
        """
        modfile = self.registryValue('module_map') % release
        path    = self.registryValue('base_path')
        data    = conf.supybot.directories.data()

        modfile = os.path.join(data, path, modfile)
        try:
            modmap = open(modfile, 'r')
        except IOError, e:
            self.log.error(str(e))
            return None

        mname = ""

        # format of the modules.pcimap is:
        # driver   vendor_id   device_id     [lots of other fields we don't care about]
        # vendor and device ids are in hexadecimal format to 8 characters.
        # Since the ids have never been converted to numbers, they can be
        # used here as strings again.
        r = '^([^\s]+)\s+0x0000%s\s+0x0000%s\s+' % (vendor, device)
        #print r
        module = re.compile(r)
        for line in modmap:
            m = module.match(line)
            if not (m is None):
                mname = m.groups(1)[0]
                break

        modmap.close()
        #print "Found: [%s:%s] => (%s)" % (vendor, device, mname)
        return mname

    def splitpciid(self, pciid):
        # Parse the pciid of the form [0000:0000] into vendor and device id parts.
        # Note that supybot doesn't like the [ ]  around the pciid unless you
        # change the commands.nested.brackets configuration option for the bot.
        #pciid = pciid.strip()
        vid = 0
        did = 0
        m = re.search('\[?([\da-f]{4}):([\da-f]{4})\]?', pciid, re.I)
        if not (m is None):
            vid = m.groups(1)[0]
            did = m.groups(1)[1]
        return vid, did

    def cleanreleasename(self, release):
        if release_map.has_key(release):
            #print "release name found %s is %s" % (release, release_map[release])
            return release_map[release]

        invmap = dict([[v,k] for k,v in release_map.items()])
        if invmap.has_key(release):
            #print "release name found %s is ok" % (release)
            return release

        release = self.registryValue('default_release')
        if release_map.has_key(release):
            #print "default release found, %s is %s" % (release, release_map[release])
            return release_map[release]
        #print "assuming configured release is ok, %s" % release
        return release


    def getkconfig(self, pattern, release):
        """
        Search through a /boot/config-$(uname -r) file
        """
        conffile = self.registryValue('kernel_config') % release
        path     = self.registryValue('base_path')
        data    = conf.supybot.directories.data()

        conffile = os.path.join(data, path, conffile)
        try:
            configs = open(conffile, 'r')
        except IOError, e:
            self.log.error(str(e))
            return None

        keys = []

        # Cleanse any characters that aren't allowed in the regexp
        pattern = re.sub('[^\s\w\d]', '', pattern)

        # format of the config-$uname -r) is:
        # CONFIG_FOO=y
        # CONFIG_GOO=m
        # # CONFIG_HOO is not set
        # where all keys start with CONFIG_, comments start with a # and there are blank lines.

        # generic search term to find matching lines
        config = re.compile(pattern)
        if pattern[0:7] == "CONFIG_":
          searchkey = pattern[7:]
        else:
          searchkey = ".*" + pattern
        # specific term for matching "is not set" comments
        notset = re.compile("^#\s+CONFIG_(%s.*)\s+is not set" % searchkey)

        for line in configs:
            m = config.search(line)
            if not (m is None):
                nm = notset.match(line)
                if not (nm is None):
                    # strip off the CONFIG_ and is not set parts of the response
                    line = "%s=n" % nm.groups(1)[0]
                else:
                    line = line.strip()
                    line = line[7:]    # strip off the CONFIG_ for brevity of output
                keys.append(line)

        configs.close()
        return keys

    def findkernels(self, release):
        """
        Search through the list of available kernels for "release".
        If release is None, return all kernels
        """

        versions = []

        klist    = self.registryValue('kernel_versions')
        path     = self.registryValue('base_path')
        data     = conf.supybot.directories.data()

        klist = os.path.join(data, path, klist)
        try:
            kernels = open(klist, 'r')
        except IOError, e:
            self.log.error(str(e))
            return None

        if release == None:
            release = "[^#,]+"
        else:
            release = self.cleanreleasename(release)

        keys = []
        versionre = re.compile("^\s*(%s)\s*,\s*([^,]+)\s*,\s*(.+)\s*$" % release)
        for line in kernels:
            line = line.strip()
            m = versionre.search(line)
            if not (m is None):
                keys.append({
                                "release" : m.groups(1)[0],
                                "version" : m.groups(1)[1],
                                "uname"   : m.groups(1)[2]
                             })
        return keys


    def bold(self, s):
          if self.registryValue('use_bold'):
              return ircutils.bold(s)
          else:
              return s


Class = Piccy

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
