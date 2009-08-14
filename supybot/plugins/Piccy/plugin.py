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
#   * handle multiple modules for a device
#   * handle stable-security kernel versions
#   * allow loading table(s) of non-free module mappings
#
#   * usbids => device + module?

import supybot.conf as conf
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks

import re
import os
import string
import time
import subprocess

# All data files are stored using the release code names (right half of the
# mapping) but this mapping also allows users to search using the release
# status name. Note that to handle minor releases like "etchnhalf" use
# a second entry such as "stable1". This map is also used for the input
# sanitisation of the release argument -- if it's not in this map, it is
# ignored.
release_map = { 'trunk'             : 'trunk',
                'unstable'          : 'sid',
                'testing'           : 'squeeze',
                'stable-backports'  : 'lenny-backports',
                'stable'            : 'lenny',
                'oldstable1'        : 'etchnhalf',
                'oldstable'         : 'etch' }

class Piccy(callbacks.Plugin):
    """A plugin for matching PCI-Ids with kernel modules and for looking up kernel config options"""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(Piccy, self)
        self.__parent.__init__(irc)

    def pciidHelper(self, irc, msg, args, pciid, optlist):
        """<pciid> [--release <release name>]

        Output the name of the device and matching kernel module if known,
        optionally restricted to the specified release.
        The pciid should be of the form 0000:0000. [ and ] are permitted around
        the pciid, but Supybot will try to act on those as nested commands unless
        they are enclosed in double quotes, e.g "[0000:0000]".
        """

        release = ""

        for (option,arg) in optlist:
            if option == 'release':
                release = arg

        release = self.cleanreleasename(release)

        vendor, device = self.splitpciid(pciid)

        if vendor == 0 or device == 0:
            irc.error("I don't know what you mean by PCI Id '%s'. 0000:0000 is my preferred format where both vendor Id and device Id are are in hexadecimal. You can find the PCI Id in the output of 'lspci -nn'." % pciid)
            return

        vname,dname = self.findname(vendor, device)
        if vname is None and dname is None:
            irc.error("Error looking up PCI Id.")
            return

        module = self.findmodule(vendor, device, release)
        if module is None:
            moduletext = self.bold("[Error looking up module list]") + '.'
        elif not len(module):
            modulefalltext=""
            fallback = self.cleanreleasename(self.registryValue('fallback_release'))
            if release != fallback:
                # no matching module found.
                module = self.findmodule(vendor, device, fallback)
                if module is None:
                    modulefalltext = self.bold(" [Error looking up module list for %s]" % fallback)
                elif not len(module):
                    modulefalltext = " or in %s" % fallback
                else:
                    modulefalltext = " but has kernel module %s in %s" % (self.boldCommaList(module), self.bold(fallback))
            moduletext = "with no known kernel module in %s%s." % (release, modulefalltext)
        else:
            if len(module) > 1:
                modlist = map(lambda m: "'%s'" % self.bold(m), module)
                moduletext = "with kernel modules %s in %s." % \
                              (self.boldCommaList(module), self.bold(release))
            else:
                moduletext = "with kernel module %s in %s." % \
                              (self.boldCommaList(module), self.bold(release))

        extras = set([])
        extramodules = ""
        for label in self.registryValue('extra_module_maps'):
            extraslist = self.findmodule(vendor, device, label)
            if extraslist: extras = extras.union(extraslist)
        if len(extras):
            extramodules = " and the out-of-tree %s module." % \
                    self.boldCommaList(extras)

        hcllink = [ self.registryValue('hcl_url') % ( "%s:%s" % (vendor, device)) ]

        map(lambda page: hcllink.append(self.registryValue('wiki_url') % page), self.checkWikiLink(extras.union(module)))

        reply = "[%s:%s] is '%s' from '%s' %s See also %s%s" % \
                ( vendor, device, dname, vname, 
                  moduletext, 
                  " ".join(hcllink), extramodules )

        irc.reply(reply)

    pciid = wrap(pciidHelper, ['something', getopts( { 'release':'something' } ) ] )


    def pcinameHelper(self, irc, msg, args, name):
        """<device>

        Output possible full names and PCI-Ids of a device based on a partial
        name. (Minimum length 4 characters, special characters are not allowed)
        """
        min_length = 4       # minimum string length for the search

        origname = " ".join(name)

        # cleanse special characters from the search term to see how long it is
        name = re.sub(r'[^\s\w\d]', '', origname)

        if len(name) < min_length:
            irc.error("Please give me name to search for that is at least %d characters long containing no special characters." % min_length)
            return

        # Clean up the expression
        name = re.sub(r' +', ' ', origname)     # allow multiple spaces
        name = re.escape(name)
        name = re.sub(r'\\ ', r'\s+', name)     # allow multiple spaces

        devices = self.finddevices(name)
        if devices is None:
            irc.error("Error looking up module list.")
            return

        reply = ""
        if devices:
            devicelist = ", ".join(
                    map(lambda d: 
                      "%s '%s' from '%s'" % 
                            (  self.bold("[%s:%s]" % (d[0], d[2])), 
                               d[3], d[1]  ), 
                      devices ))
            reply = "'%s' matched: %s" % (origname, devicelist)
        else:
            reply = "No devices were found that matched '%s'." % origname

        irc.reply(reply)

    pciname = wrap(pcinameHelper, [many('something')] )



    def xorgHelper(self, irc, msg, args, pciid, optlist):
        """<pciid> [--release <release name>]

        Output the name of the xorg driver (if any) that would claim the
        device, optionally restricted to the specified release.
        The pciid should be of the form 0000:0000. [ and ] are permitted around
        the pciid, but Supybot will try to act on those as nested commands unless
        they are enclosed in double quotes, e.g "[0000:0000]".
        """

        release = ""

        for (option,arg) in optlist:
            if option == 'release':
                release = arg

        release = self.cleanreleasename(release)

        vendor, device = self.splitpciid(pciid)

        if vendor == 0 or device == 0:
            irc.error("I don't know what you mean by PCI Id '%s'. 0000:0000 is my preferred format where both vendor Id and device Id are are in hexadecimal. You can find the PCI Id in the output of 'lspci -nn'." % pciid)
            return

        reply = ""

        drivers = self.findxorgdriver(vendor, device, release)
        if drivers == None:
            irc.error("Error looking up driver list.")
            return

        if drivers:
            reply = "In %s, device %s:%s is matched by xorg %s: %s." % \
                    ( self.bold(release), vendor, device, ("driver", "drivers")[len(drivers)!=1],
                      self.boldCommaList(drivers)
                    )
        else:
            fallback = self.cleanreleasename(self.registryValue('fallback_release'))
            if release != fallback:
                drivers = self.findxorgdriver(vendor, device, fallback)
                if drivers:
                    reply = "Device %s:%s is not matched by any xorg drivers in %s. In %s, it is matched by xorg %s: %s." % ( vendor, device, self.bold(release),
                          self.bold(fallback), ("driver", "drivers")[len(drivers)!=1],
                          self.boldCommaList(drivers)
                        )
                else:
                    reply = "Device %s:%s is not matched by any xorg drivers in %s or %s." % \
                        (vendor, device, self.bold(release), self.bold(fallback))
            else:
                reply = "Device %s:%s is not matched by any xorg drivers in %s." % \
                    (vendor, device, self.bold(release))

        irc.reply(reply)

    xorg = wrap(xorgHelper, ['something', getopts( { 'release':'something' } ) ] )


    def kconfigHelper(self, irc, msg, args, pattern, optlist):
        """<config string> [--release <release name>]

        Outputs the kernel configs that match the given string, optionally
        restricted to an individual release.
        The pattern will have wildcards automatically added around it.
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
            configtext = ' '.join(configlist)

        reply = "Searching for '%s' in %s kernel config gives %s." % (self.bold(pattern), self.bold(release), configtext)

        irc.reply(reply)

    kconfig = wrap(kconfigHelper, ['something', getopts( { 'release':'something' } ) ] )

    # provide a command alias as well
    kernelconfig = wrap(kconfigHelper, ['something', getopts( { 'release':'something' } ) ] )


    def kernelVersionHelper(self, irc, msg, args, optlist):
        """[--release <lenny>]

        Outputs the kernel versions in the archive, optionally restricted to
        one release. Note that semi-major releases like etchnhalf are treated
        as separate releases.
        """

        release = None

        for (option,arg) in optlist:
            if option == 'release':
                release = arg

        versions = self.findkernels(release)

        versionstrings = []
        if versions:
            for v in versions:
                versionstrings.append("%s: %s (%s)"
                                    % (self.bold(v["release"]),
                                       v["uname"],
                                       v["version"]))
            reply = "Available kernel versions are: " + ("; ".join(versionstrings))
        else:
            reply = "No kernel versions found."

        irc.reply(reply)

    # provide convenience aliases for kernel version command
    kernel        = wrap(kernelVersionHelper, [ getopts( { 'release':'something' } ) ] )
    kernels       = wrap(kernelVersionHelper, [ getopts( { 'release':'something' } ) ] )


    def updateHelper(self, irc, msg, args):
        """takes no arguments

        Refreshes the data used by the plugin. (Requires elevated privileges.)
        """

        sourcedir = os.path.dirname(__file__)
        refresh   = os.path.join(sourcedir, "refreshdata")

        path      = self.registryValue('base_path')
        data      = conf.supybot.directories.data()
        data      = os.path.join(data, path)

        self.log.info("Attempting to refresh with %s %s", refresh, data)
        try:
            starttime = time.time()
            irc.reply("Starting to refresh the kernel and PCI-Id data (this takes a while)...")
            output = subprocess.Popen([refresh, data],
                      stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()[0]
            self.log.debug(output)

            if re.search(r"^E:", "".join(output), re.MULTILINE):
                self.log.warn("Error updating data: %s", output)
                irc.error("Error refreshing data. Please see logs or run the update manually.")
            else:
                self.log.debug("Updater output: %s", output)
                self.log.info("Data refresh appeared to be successful")
                irc.reply("Data update completed in %d seconds." % (time.time()-starttime))
        except OSError, e:
            self.log.error("Error refreshing data. %s", e)
            irc.error("Error refreshing data. %s" % e)

    update       = wrap(updateHelper, ['owner', 'private'] )


    def lastUpdateHelper(self, irc, msg, args):
        """takes no arguments

        Outputs when the data used by the plugin was last refreshed.
        """

        klist    = self.registryValue('kernel_versions')
        path     = self.registryValue('base_path')
        data     = conf.supybot.directories.data()

        klist = os.path.join(data, path, klist)

        try:
            mtime = os.path.getmtime(klist)
            irc.reply("Piccy plugin data last updated at %s" % time.strftime('%Y-%m-%d %H:%M', time.localtime(mtime)))
        except OSError, e:
            self.log.error("Error looking up kernel versions mtime. %s", e)
            irc.error("Couldn't determine when data was last refreshed.")

    lastupdate   = wrap(lastUpdateHelper)


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
            if string.lower(line[0:4]) == vendor:
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
                if string.lower(line[0:4]) == device:
                    dname=line[6:]

        idmap.close()
        self.log.debug("Found: [%s:%s] => (%s) (%s)", vendor, device, vname, dname)
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

        mname = []

        # format of the modules.pcimap is:
        # driver   vendor_id   device_id     [lots of other fields we don't care about]
        # vendor and device ids are in hexadecimal format to 8 characters.
        # Since the ids have never been converted to numbers, they can be
        # used here as strings again.
        r = r'^([^\s]+)\s+0x0000%s\s+0x(0000%s|ffffffff)\s+' % (vendor, device)
        #print r
        module = re.compile(r, re.I)
        for line in modmap:
            m = module.match(line)
            if not (m is None):
                mname.append(m.groups(1)[0])
                # break

        modmap.close()
        self.log.debug("Found: [%s:%s] => (%s)", vendor, device, ", ".join(mname))
        return set(mname)


    def finddevices(self, name):
        """
        look through /usr/share/misc/pci.ids for possible device names
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

        devices = []
        vid   = ""
        did   = ""
        vname = "Unknown vendor"
        dname = "Unknown device"

        vidre = re.compile(r"^([0-9a-f]{4})\s+(.+)", re.I)
        didre = re.compile(r"^\s+([0-9a-f]{4})\s+(.*%s.*)" % name, re.I)

        for line in idmap:
            #print line
            vendormatch = vidre.match(line)
            if vendormatch:
                vid   = vendormatch.groups(1)[0]
                vname = vendormatch.groups(1)[1]
                continue

            devicematch = didre.match(line)
            if devicematch:
                did   = devicematch.groups(1)[0]
                dname = devicematch.groups(1)[1]
                devices.append([vid, vname, did, dname])

        idmap.close()

        self.log.debug("Found: %s", devices)
        return devices


    def findxorgdriver(self, vendor, device, release):
        """
        Search through xorg's /usr/share/xserver-xorg/pci/* maps for a 
        PCI-Id match
        """
        mapdir  = self.registryValue('xorg_maps') % release
        path    = self.registryValue('base_path')
        data    = conf.supybot.directories.data()

        mapdir = os.path.join(data, path, mapdir)

        drivers = []
        id = "%s%s" % (vendor, device)

        try:
            filelist = os.listdir(mapdir)
        except IOError, e:
            self.log.error(str(e))
            return None

        for f in filelist:
            filename = os.path.join(mapdir, f)
            if os.path.isdir(filename): continue

            if self.inxorgmap(id, filename):
                drivers.append(f)


        return map(lambda f: f[:-4], drivers)


    def inxorgmap(self, id, mapfilename):
        """
        Search through a single xorg /usr/share/xserver-xorg/pci/*.ids 
        map for a PCI-Id match
        """

        try:
            mapfile = open(mapfilename, 'r')
        except IOError, e:
            self.log.error(str(e))
            return None

        # format of /usr/share/xserver-xorg/pci/*.ids files is:
        #    {vendor_id}{device_id}
        # one per line with no punctuation. Not even the : from the PCI-Id.
        r = r'%s' % (id)
        module = re.compile(r, re.I)
        for line in mapfile:
            if module.match(line):
                return True
        return False


    def checkWikiLink(self, modules):
        """
        Search through wiki page for links from module name to wiki page
        """
        if not len(modules):
            return set([])

        wikifile = self.registryValue('wiki_map')
        path     = self.registryValue('base_path')
        data     = conf.supybot.directories.data()

        wikifile = os.path.join(data, path, wikifile)
        try:
            wikimap = open(wikifile, 'r')
        except IOError, e:
            self.log.error(str(e))
            return []

        wikipages = []

        # format of the wiki page is:
        # * iwl3945 [[iwlwifi]]
        # * iwl4965 [[iwlwifi]], [[iwlagn]]
        r = r'^\s*\*\s*(%s)\s*(.*)' % "|".join(modules)
        modulere = re.compile(r, re.I)
        p = r'\[\[([a-z0-9\-_]+)\]\]'
        linere = re.compile(p, re.I)
        for line in wikimap:
            linematches = modulere.match(line)
            if not (linematches is None):
                for page in re.split(r'[\s,]', linematches.groups(1)[1]):
                    pagelist = linere.match(page)
                    if pagelist:
                        wikipages.append(pagelist.groups(1)[0])

        wikimap.close()
        self.log.debug("Found wiki match: [%s] => (%s)", ", ".join(modules), ", ".join(wikipages))
        return set(wikipages)


    def splitpciid(self, pciid):
        # Parse the pciid of the form [0000:0000] into vendor and device id parts.
        # Note that supybot doesn't like the [ ]  around the pciid unless you
        # change the commands.nested.brackets configuration option for the bot.
        #pciid = pciid.strip()
        vid = 0
        did = 0
        m = re.search(r'\[?([\da-f]{4}):([\da-f]{4})\]?', pciid, re.I)
        if not (m is None):
            vid = string.lower(m.groups(1)[0])
            did = string.lower(m.groups(1)[1])
        self.log.debug("PCI id parsing gives vendor = '%s', device = '%s'", vid, did)
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
        pattern = re.sub(r'[^\s\w\d]', '', pattern)

        # format of the config-$(uname -r) is:
        # CONFIG_FOO=y
        # CONFIG_GOO=m
        # # CONFIG_HOO is not set
        # where all keys start with CONFIG_, comments start with a # and there are blank lines.

        if pattern[0:7] == "CONFIG_":
            searchkey = pattern[7:]
        else:
            searchkey = ".*" + pattern
        # generic search term to find matching lines
        config = re.compile(r"^CONFIG_%s" % searchkey, re.IGNORECASE)
        # specific term for matching "is not set" comments
        notset = re.compile(r"^#\s+CONFIG_(%s.*)\s+is not set" % searchkey, re.IGNORECASE)

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
            release = r"[^#,]+"
        else:
            release = self.cleanreleasename(release)

        keys = []
        versionre = re.compile(r"^\s*(%s)\s*,\s*([^,]+)\s*,\s*(.+)\s*$" % release)
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


    def boldCommaList(self, listing, format="'%s'"):
        """
        Return the list comma separated, with each term in bold
        """
        return ", ".join(
                map(lambda m: format % self.bold(m), listing)
              )


Class = Piccy

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
