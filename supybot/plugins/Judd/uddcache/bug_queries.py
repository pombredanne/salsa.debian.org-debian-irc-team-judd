#
# Ultimate Debian Database query tool
#
# Set piece queries of bug information from the database
#
###
#
# Copyright (c) 2010-2012  Stuart Prescott
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

from udd import Udd
import bts
from packages import PackageNotFoundError
from bts import BugNotFoundError
import re

try:
    from debian import debian_support
except:
    from debian_bundle import debian_support


class Commands(object):

    def __init__(self, udd):
        self.udd = udd

    def bug(self, bugnumber, verbose):
        """
        Retrieve information about a particular bug
        """
        tracker = self.udd.Bts()
        b = tracker.bug(bugnumber)
        if verbose:
            tracker.get_bugs_tags([b])
        return b

    def bug_package(self, package, verbose=True, archived=False, source=None, filter=None):
        """
        Retrieve information about bugs in a package
        """
        if filter:
            fil = filter.copy()
        else:
            fil = {}
        if 'sort' not in fil:
            fil['sort'] = 'id'
        if package[0:4] == 'src:':
            packagename = package[4:]
            source = True
        else:
            packagename = package
            if source not in (True, False):
                source = False
        if source:
            try:
                p = self.udd.BindSourcePackage(packagename,
                                               self.udd.data.devel_release)
                fil['source'] = p.package
            except PackageNotFoundError:
                fil['source'] = package
        else:
            fil['package'] = package
        tracker = self.udd.Bts(archived)
        bugs = tracker.get_bugs(fil)
        if verbose:
            tracker.get_bugs_tags(bugs)
        return bugs

    def bug_package_search(self, package, search, verbose=True, archived=False, source=None):
        """
        Retrieve information about bugs in a package
        """
        return self.bug_package(package, verbose, archived, source, {'title':search})

    def rm(self, package, archived=True):
        """
        Retrieve information about a package removal bug
        """
        tracker = self.udd.Bts(archived)
        return tracker.get_bugs({'package': 'ftp.debian.org',
                                'title': 'RM: %s ' % package,
                                'sort': 'id DESC',
                                'limit': 1})

    def wnpp(self, package, bugtype=None):
        """
        Retrieve information about a package removal bug
        """
        tracker = self.udd.Bts(False)
        filter = {
                    'package': 'wnpp',
                    'sort': 'id DESC',
                    'status': bts.open_status
                }
        if bugtype:
            filter['title'] = r'''^["']?%s\s*(:|--|)\s*%s ''' % (bugtype, re.escape(package))
        else:
            filter['title'] = r'''^["']?(%s)\s*(:|--|)\s*%s ''' % ('|'.join(bts.wnpp_types), re.escape(package))
        return tracker.get_bugs(filter)

    def rcbugs(self, package, verbose=True):
        """
        Retrieve all open release critical bugs for a package
        """
        try:
            p = self.udd.BindSourcePackage(package,
                                           self.udd.data.devel_release)
            source = p.package
        except PackageNotFoundError:
            source = package
        tracker = self.udd.Bts(False) # only consider unarchived bugs
        bugs = tracker.get_bugs({
                        'source': source,
                        'severity': ('critical', 'grave', 'serious'),
                        'status': ('forwarded', 'pending', 'pending-fixed')
                    })
        if verbose:
            tracker.get_bugs_tags(bugs)
        return bugs
