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

import supybot.conf as conf
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks

import re
import os
import errno
import types


class Ernie(callbacks.Plugin):
    """Error and status codes lookup plugin"""

    def __init__(self, irc):
        self.__parent = super(Ernie, self)
        self.__parent.__init__(irc)

    def grubHelper(self, irc, msg, args, errcode):
        """<error code>

        Output the description for a grub error code.
        """
        
        # See http://www.gnu.org/software/grub/manual/grub.html#Stage2-errors
        # look through the grub error map
        grub    = self.registryValue('grub_map')
        path    = self.registryValue('base_path')
        data    = conf.supybot.directories.data()

        grub = os.path.join(data, path, grub)
        try:
            grubmap = open(grub, 'r')
        except IOError, e:
            self.log.error(str(e))
            irc.error("Error looking up grub error codes.")
            return None

        reply = "No information was found for grub error %s." % errcode

        errre = re.compile(r"^%s\t(.+)\t(.+)" % errcode)
        for line in grubmap:
            m = errre.match(line)
            if m:
                reply = "Grub error %s: %s: %s" % (self.bold(errcode), self.bold(m.groups(1)[0]), m.groups(1)[1])

        irc.reply(reply)

    grub = wrap(grubHelper, ['something'] )


    def errnoHelper(self, irc, msg, args, errcode):
        """<error code>

        Output a brief error description for a posix numeric or literal error code.
        """
        
        # see http://www.python.org/doc/2.5.2/lib/module-errno.html
        # Also: 
        # perl -MErrno -e 'my %e= map { Errno->$_()=>$_ } keys(%!); print grep ! /unknown error/i, map sprintf("%4d %-12s %s".$/,$_,$e{$_},$!=$_), 0..127'

        name = ''
        description = ''
        if re.search(r"[^\d]", errcode):
            invmap = dict([[v,k] for k,v in errno.errorcode.items()])
            if errcode in invmap:
                errcode = invmap[errcode]
        else:
            errcode = int(errcode)
        
        if errcode in errno.errorcode.keys():
            name = errno.errorcode[errcode]
            description = os.strerror(errcode)
          
        reply = "Error code %s could not be found" % errcode
        if not name == '':
            reply = "Error code %s is %s: %s." % (self.bold(errcode), self.bold(name), description)

        irc.reply(reply)

    errno = wrap(errnoHelper, ['something'] )


    def bold(self, s):
        if self.registryValue('use_bold'):
            return ircutils.bold(s)
        else:
            return s


Class = Ernie


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
