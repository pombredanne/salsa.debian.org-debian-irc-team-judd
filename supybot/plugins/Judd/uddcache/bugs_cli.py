# coding: utf-8

#
# Ultimate Debian Database query tool
#
# CLI bindings
#
###
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

""" Command line interface to udd - output to stdout """

import clibase
import udd
import bug_queries
import bts

from packages import PackageNotFoundError
from bts import BugNotFoundError

class Cli(clibase.CliBase):
    """ Run a specified command sending output to stdout """

    def __init__(self, config=None, options=None, initialise=True):
        super(Cli,self).__init__(config, options, initialise, bug_queries.Commands)
        self.command_map = {
                'bug':          self.bug,
                'rcbugs':       self.rcbugs,
                'rm':           self.rm,
                'rfs':          self.rfs,
                'wnpp':         self.wnpp,
                'rfp':          self.wnpp,
                'itp':          self.wnpp,
                'rfa':          self.wnpp,
                'ita':          self.wnpp,
                'orphan':       self.wnpp,
                'stats':        self.stats,
                }
        self.command_aliases = {
                }

    def bug(self, command, search, args):
        search = search.replace('#', '')
        if search.isdigit() and int(search) < 1e7:
            bugnumber = int(search)
            try:
                bug = self.dispatcher.bug(bugnumber, self.options.verbose)
            except BugNotFoundError:
                print "Sorry, bug %d was not found." % bugnumber
                return
            print bug
        else:
            if not args:
                bugs = self.dispatcher.bug_package(search, verbose=self.options.verbose, archived=False, filter={'status': ('forwarded', 'pending', 'pending-fixed')})
                if self.options.verbose:
                    print "\n".join([str(b) for b in bugs])
                else:
                    for s in bts.severities:
                        bs = [str(b.id) for b in bugs if b.severity == s]
                        if bs:
                            print "%s: %d: %s" % (s, len(bs), ", ".join(bs))
                bugs = self.dispatcher.wnpp(search)
                for s in bts.wnpp_types:
                    bl = [b for b in bugs if b.wnpp_type == s]
                    if bl:
                        print "%s: #%d" % (s, bl[0].id)
                bugs = self.dispatcher.rm(search)
                if bugs:
                    print "RM: %s" % (",".join(["#%d" % b.id for b in bugs]))
            else:
                bugs = self.dispatcher.bug_package_search(search, args[0], verbose=self.options.verbose, archived=False)
                if self.options.verbose:
                    print "\n".join([str(b) for b in bugs])
                else:
                    print "\n".join(["#%d: %s" % (b.id, b.title) for b in bugs])


    def rm(self, command, package, args):
        bugs = self.dispatcher.rm(package)
        if not bugs:
            print "Sorry, no removal bug for %s was found." % package
            return
        print bugs[0]

    def wnpp(self, command, package, args):
        bugtype = command.upper()
        if bugtype == 'ORPHAN':
            bugtype = 'O'
        if bugtype == 'WNPP':
            bugtype = None
        bugs = self.dispatcher.wnpp(package, bugtype)
        if not bugs:
            print "Sorry, no WNPP bug for %s was found." % package
            return
        print "\n".join([str(b) for b in bugs])

    def rfs(self, command, package, args):
        bugfilter={'title': package}
        if not self.options.verbose: # also get fixed bugs for verbose
            bugfilter['status'] = ('forwarded', 'pending', 'pending-fixed')
        bugs = self.dispatcher.bug_package("sponsorship-requests",
                                       verbose=True, # always get tags
                                       archived=self.options.verbose,
                                       filter=bugfilter)
        if not bugs:
            print "No open RFS bugs found for that package"
            return
        for b in bugs:
            s = [
                "Bug: %d" % b.id,
                "Title: %s" % b.title.splitlines()[0],
                "Severity: %s" % b.severity,
                "Status: %s" % b.readable_status,
                "Opened: %s" % b.arrival.date(),
                "Last-Modified: %s" % b.last_modified.date(),
                "Tags: %s" % ", ".join(b.tags),
                "Submitter: %s" % b.submitter,
                "Owner: %s" % b.owner,
                ""
            ]
            print "\n".join(s)

    def rcbugs(self, command, package, args):
        bugs = self.dispatcher.rcbugs(package)
        if not bugs:
            print "No release critical bugs were found for '%s'." % package
            return
        print "\n".join([str(b) for b in bugs])

    def stats(self, command, _, __):
        statistics = self.dispatcher.stats()
        print \
        """UDD currently knows about the following release critical bugs:

In Total: %(total)d

    Affecting testing: %(testing)d That's the number we need to get down
    to zero before the release. They can be split in two big categories:

        Affecting testing and unstable: %(testing_unstable)d
            Those need someone to find a fix, or to finish the work to upload
            a fix to unstable:
            %(testing_patch)d bugs are tagged 'patch'.
            %(unstable_done)d bugs are marked as done, but still affect unstable.
            %(nostatus)d bugs are neither tagged patch, nor marked done.

        Affecting testing only: %(testing_only)d Those are already fixed in
        unstable, but the fix still needs to migrate to wheezy.
        """ % statistics

