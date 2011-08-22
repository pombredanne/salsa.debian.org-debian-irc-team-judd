#
# Ultimate Debian Database query tool
#
# Configuration for database access
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

"""
Config file support for udd-cache

Expected format is as follows:
    [database]
    hostname: machine_name
    port:     database_port
    username: database_username
    password: database_password
    database: udd

If working with a Judd instance, this can be generated from
the supybot config file as follows:
    (echo "[database]"; sed -nr 's/.*Judd\.db_(.*)$/\1/p' supybot.conf) \
        > udd-cache.conf

"""

# See also:
# http://docs.python.org/library/configparser.html

import os
import os.path
import ConfigParser


class Config:
    def __init__(self, file=None, skipDefaultFiles=False):
        self.filename = file
        self.config = None
        self._ReadConfig(skipDefaultFiles)

    def _ReadConfig(self,  skipDefaultFiles=False):
        """
        Read in the database config for connecting to the UDD instance.

        Returns a dict with these keys:value pairs.
        """
        self.config = ConfigParser.RawConfigParser()
        files = []
        if not skipDefaultFiles:
            files.append('/etc/udd-cache.conf')
            files.append(os.path.expanduser('~/.udd-cache.conf'))
            files.append('udd-cache.conf')

        if 'UDD_CACHE_CONFIG' in os.environ and os.environ['UDD_CACHE_CONFIG']:
            if not os.path.isfile(os.environ['UDD_CACHE_CONFIG']):
                raise IOError("Configuration file not found: '%s'." %
                              os.environ['UDD_CACHE_CONFIG'])
            files.append(os.environ['UDD_CACHE_CONFIG'])
        if self.filename:
            if not os.path.isfile(self.filename):
                raise IOError("Configuration file not found '%s'." %
                              self.filename)
            files.append(self.filename)
        files = self.config.read(files)
        if not files:
            raise ValueError("No valid configuration was found to connect"
                            " to the database.")
        #print files

    def db(self):
        """
        Read in the database config for connecting to the UDD instance.

        Returns a dict with these keys:value pairs.
        """
        conf = {
                'hostname': self.get('database', 'hostname', 'localhost'),
                'port':     self.get('database', 'port', '5432'),
                'username': self.get('database', 'username', None),
                'password': self.get('database', 'password', None),
                'database': self.get('database', 'database', 'udd'),
                }
        return conf

    def db_logging(self):
        """
        Return the filename if any that should be used for database logging
        """
        return self.get('database', 'logfile', None)

    def get(self, section, value, default):
        try:
            return self.config.get(section, value)
        except:
            return default
