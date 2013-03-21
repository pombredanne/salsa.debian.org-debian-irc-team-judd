#
# Ultimate Debian Database query tool
#
# Database abstraction layer
#
###
#
# Copyright (c) 2010-2011   Stuart Prescott
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


import re
import psycopg2
import database
from data import DebianData
from config import Config
from packages import *
import bts

class Udd():
    """
    """

    def __init__(self, config=None, distro="debian", logfile=None):
        """Initialise the connection to the UDD instance

            config: config filename or Config instance
            distro: string naming the distribution that is being used
            logfile: filename into which database calls should be logged
                    or False to suppress loading this setting from the
                    config file
        """
        if type(config) is str or config is None:
            config = Config(config)
        self.config = config
        self.psql = None
        self._connect(logfile)
        if distro == 'debian':
            self.data = DebianData
        elif distro == 'ubuntu':
            raise NotImplementedError("Only distro='debian' implemented")
            # TODO: add this in
        else:
            raise ValueError("Unknown data types requested by 'distro'")

    def __del__(self):
        self._disconnect()

    def _connect(self, logfile):
        arg_mapping = {
                            'database': 'database',
                            'hostname': 'host',
                            'port':     'port',
                            'password': 'password',
                            'username': 'user',
                        }
        args = {}
        c = self.config.db()
        for i in c.keys():
            if c[i] != None:
                args[arg_mapping[i]] = c[i]

        # look up logfile settings from config file unless instructed not to
        if logfile == None:
            logfile = self.config.db_logging()

        # make the connection, logging to the file if requests
        self.psql = database.Connect(logfile, **args)

    def _disconnect(self):
        self.psql.close()

    def BindRelease(self, release=None, arch="i386", **kwargs):
        """
        Select a release from the database
        """
        if release is None:
            release = self.data.stable_release
        r = Release(self.psql, arch=arch, release=release, **kwargs)
        return r

    def BindPackage(self, package="", release=None, arch="i386"):
        """
        Select a package from the database
        """
        if release is None:
            release = self.data.stable_release
        r = Release(self.psql, arch=arch, release=release)
        p = r.Package(package)
        return p

    def BindSourcePackage(self, package="", release=None):
        """
        Select a source package from the database
        """
        if release is None:
            release = self.data.stable_release
        r = Release(self.psql, release=release)
        p = r.Source(package)
        return p

    def Bts(self, include_archived=True):
        """
        Create a new bug tracker
        """
        return bts.Bts(self.psql, include_archived)
