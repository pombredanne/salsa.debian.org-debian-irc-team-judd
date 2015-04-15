# -*- coding: utf-8 -*-
###
#
# Copyright (c) 2007,2008, Mike O'Connor
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

###

#TODO:

import supybot.conf as conf
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks

import re
import psycopg2
import psycopg2.extras
import time

import os
import fnmatch
import debcontents.contents_file

import uddcache.udd
import uddcache.package_queries
import uddcache.bug_queries
import uddcache.config
from uddcache.packages import PackageNotFoundError
import uddcache.bts
from uddcache.bts import BugNotFoundError

#
#def parse_standard_options(optlist, args=None):
#    release = clean_release_name(optlist=optlist, args=args)
#    arch = clean_arch_name(optlist=optlist, args=args)
#    return release, arch


class Judd(callbacks.Plugin):
    """A plugin for querying a debian udd instance:  http://wiki.debian.org/UltimateDebianDatabase."""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(Judd, self)
        self.__parent.__init__(irc)

        # If there is an udd-cache.conf in the plugin directory then it
        # probably contains useful configuration data
        conffile = os.path.join(os.path.dirname(__file__), 'udd-cache.conf')
        if os.path.isfile(conffile) and self.registryValue('use_conf_file'):
            self.log.debug("Using file udd-db configuration: %s", conffile)
            uddconf = uddcache.config.Config(file=conffile)
        else:
            self.log.debug("Using registry udd-db configuration")
            sqllog = os.path.join(conf.supybot.directories.log(),
                     self.registryValue('db_querylog'))
            self.log.debug("UDD SQL Query logfile: %s",  sqllog)
            # some amount of remapping of config option names is required
            confdict = {
                        'database': self.registryValue('db_database'),
                        'hostname': self.registryValue('db_hostname'),
                        'port': self.registryValue('db_port'),
                        'username': self.registryValue('db_username'),
                        'password': self.registryValue('db_password'),
                        'logfile': sqllog
                    }
            uddconf = uddcache.config.Config(confdict=confdict)
        # Initialise a UDD instance with the appropriate configuration
        self.udd = uddcache.udd.Udd(uddconf)
        self.dispatcher = uddcache.package_queries.Commands(self.udd)
        self.bugs_dispatcher = uddcache.bug_queries.Commands(self.udd)

    def notfound(self, irc, package, release=None, arch=None,
                 message="No package named '%s' was found%s."):
        """ return a message indicating that the package was not found """
        if release:
            if arch:
                tag = " in %s/%s" % (release, arch)
            else:
                tag = " in %s" % release
        else:
            if arch:
                tag = " in %s" % arch
            else:
                tag = ""
        irc.reply(message % (package, tag))

    def versions(self, irc, msg, args, package, optlist, something):
        """<pattern> [--arch <amd64>] [--release <stable>]

        Show the available versions of a package in the optionally specified
        release and for the given architecture.
        All current releases and amd64 are searched by default. By default,
        binary packages are searched; prefix the packagename with "src:" to
        search source packages.
        """
        channel = msg.args[0]
        release = self.udd.data.clean_release_name(optlist=optlist,
                            args=something, default=None)
        arch = self.udd.data.clean_arch_name(optlist=optlist,
                            args=something, default=self.default_arch(channel))

        try:
            pkgs = self.dispatcher.versions(package, release, arch)
        except PackageNotFoundError:
            return self.notfound(irc, package, release, arch)

        replies = []
        for row in pkgs:
            if (row['component'] == 'main'):
                replies.append("%s %s" % \
                    ("%s:" % self.bold(row['release']),
                    row['version']))
            else:
                replies.append("%s %s" % \
                    ("%s/%s:" % (self.bold(row['release']), row['component']),
                    row['version']))

        irc.reply("Package: %s on %s -- %s" % (package, arch,
                            "; ".join(replies)))

    versions = wrap(versions, ['something',
                                getopts({'arch':'something',
                                        'release':'something'}),
                                any('something')])

    def names(self, irc, msg, args, package, optlist, something):
        """<pattern> [--arch <amd64>] [--release <stable>]

        Search package names with * and ? as wildcards.
        The current stable release and amd64 are searched by default.
        """
        channel = msg.args[0]
        release = self.udd.data.clean_release_name(optlist=optlist,
                        args=something, default=self.default_release(channel))
        arch = self.udd.data.clean_arch_name(optlist=optlist,
                        args=something, default=self.default_arch(channel))

        try:
            pkgs = self.dispatcher.names(package, release, arch)
        except PackageNotFoundError:
            return self.notfound(irc, package, release, arch,
                             message="No packages matching %s were found%s.")

        replies = []
        for row in pkgs:
            if (row['component'] == 'main'):
                replies.append("%s %s" % \
                                (self.bold(row['package']), row['version']))
            else:
                replies.append("%s %s (%s)" % \
                                (self.bold(row['package']), row['version'],
                                  row['component']))

        irc.reply("Search for %s in %s/%s: %s" % \
                            (package, release, arch, "; ".join(replies)))

    names = wrap(names, ['something',
                          getopts({'arch':'something',
                                   'release':'something'}),
                          any('something')])

    def info(self, irc, msg, args, package, optlist, something):
        """<packagename> [--arch <amd64>] [--release <stable>]

        Show the short description and some other brief details about a package
        in the specified release and architecture. By default, the current
        stable release and amd64 are used.
        """
        channel = msg.args[0]
        release = self.udd.data.clean_release_name(optlist=optlist,
                        args=something, default=self.default_release(channel))
        arch = self.udd.data.clean_arch_name(optlist=optlist,
                        args=something, default=self.default_arch(channel))

        try:
            pinfo = self.dispatcher.info(package, release, arch)
        except PackageNotFoundError:
            return self.notfound(irc, package, release, arch)

        description = pinfo['description'].splitlines()
        if description:
            description = description[0]
        else:
            description = ""
        reply = "Package %s (%s, %s) in %s/%s: %s. Version: %s; " \
                "Size: %0.1fk; Installed: %dk" % \
                  (package, pinfo['section'], pinfo['priority'],
                    release, arch, description,
                    pinfo['version'],
                    pinfo['size'] / 1024.0, pinfo['installed_size'])
        if pinfo['homepage']:    # homepage field
            reply += "; Homepage: %s" % pinfo['homepage']
        # screenshot url from screenshots.debian.net
        if pinfo['screenshot_url']:
            reply += "; Screenshot: %s" % pinfo['screenshot_url']

        bug_count = []
        bugs = self.bugs_dispatcher.wnpp(package)
        for t in uddcache.bts.wnpp_types:
            bt = [b for b in bugs if b.wnpp_type == t]
            if bt:
                bug_count.append("%s: #%d" % (bt[0].wnpp_type, bt[0].id))
        if bug_count:
            reply += "; %s" % ", ".join(bug_count)
        irc.reply(reply)

    info = wrap(info, ['something',
                        getopts({'arch':'something',
                                 'release':'something'}),
                        any('something')])

    def archs(self, irc, msg, args, package, optlist, something):
        """<packagename> [--release <stable>]

        Show for what architectures a package is available. By default, the
        current stable release is used.
        """
        channel = msg.args[0]
        release = self.udd.data.clean_release_name(optlist=optlist,
                        args=something, default=self.default_release(channel))

        try:
            pkgs = self.dispatcher.archs(package, release)
        except PackageNotFoundError:
            return self.notfound(irc, package, release, None)

        replies = []
        for row in pkgs:
            replies.append("%s (%s)" % (row[0], row[1]))
        irc.reply("Package %s in %s: %s" % (package, release,
                                            ", ".join(replies)))

    archs  = wrap(archs, ['something',
                                getopts({'release':'something'}),
                                any('something')])

    def rprovides(self, irc, msg, args, package, optlist, something):
        """<packagename> [--arch <amd64>] [--release <stable>]

        Show the packages that 'Provide' the specified virtual package
        ('reverse provides').
        By default, the current stable release and amd64 are used.
        """
        channel = msg.args[0]
        release = self.udd.data.clean_release_name(optlist=optlist,
                        args=something, default=self.default_release(channel))
        arch = self.udd.data.clean_arch_name(optlist=optlist,
                        args=something, default=self.default_arch(channel))

        pack = self.udd.BindPackage(package, release, arch)
        if pack.IsVirtual():
            reply = "Package %s in %s/%s is provided by: %s." % \
                    (package, release, arch, ", ".join(pack.ProvidersList()))
            if pack.Found():
                reply += " %s is also a real package." % package
        else:
            if pack.Found():
                reply = "In %s/%s, %s is a real package." % \
                            (release, arch, package)
            else:
                reply = "No packages provide '%s' in %s/%s." % \
                                                (package, release, arch)

        irc.reply(reply)

    rprovides = wrap(rprovides, ['something',
                                      getopts({'arch':'something',
                                               'release':'something'}),
                                      any('something')])

    def provides(self, irc, msg, args, package, optlist, something):
        """<packagename> [--arch <amd64>] [--release <stable>]

        Show the list of "provided" packages for the specified binary package
        in the given release and architecture. By default, the current
        stable release and amd64 are used.
        """
        channel = msg.args[0]
        release = self.udd.data.clean_release_name(optlist=optlist,
                        args=something, default=self.default_release(channel))
        arch = self.udd.data.clean_arch_name(optlist=optlist,
                        args=something, default=self.default_arch(channel))

        pack = self.udd.BindPackage(package, release, arch)

        if pack.Found():
            if pack.data['provides']:
                irc.reply("Package %s in %s/%s provides: %s." % \
                            (package, release, arch, pack.data['provides']))
            else:
                irc.reply("Package %s in %s/%s provides no additional packages." % \
                            (package, release, arch))
        else:
            return self.notfound(irc, package, release, arch)

    provides = wrap(provides, ['something',
                              getopts({'arch':'something',
                                       'release':'something'}),
                              any('something')])

    def danke(self, irc, msg, args):
        """
        Someone is trying to speak esperanto to me
        """
        irc.reply("ne dankinde")

    danke = wrap(danke, [])

    def src(self, irc, msg, args, package, optlist, something):
        """<packagename> [--release <stable>]

        Show the name of the source package from which a given binary package
        is derived.
        By default, the current stable release and amd64 are used.
        """
        channel = msg.args[0]
        release = self.udd.data.clean_release_name(optlist=optlist,
                        args=something, default=self.default_release(channel))
        arch = self.udd.data.clean_arch_name(optlist=optlist,
                        args=something, default=self.default_arch(channel))

        rel = self.udd.BindRelease(release, arch)
        try:
            pack = rel.bin2src(package)
        except PackageNotFoundError:
            return self.notfound(irc, package, release, arch,
                            message="Sorry, there is no record of a "
                            "source package for the binary package '%s'%s.")

        irc.reply("Package %s in %s -- source: %s" % (package, release, pack))

    src = wrap(src, ['something',
                        getopts({'release':'something'}),
                        any('something')])

    def binaries(self, irc, msg, args, package, optlist, something):
        """<packagename> [--release <stable>]

        Show the name of the binary package(s) that are derived from a given
        source package.
        By default, the current stable release and amd64 are used.
        """
        channel = msg.args[0]
        release = self.udd.data.clean_release_name(optlist=optlist,
                        args=something, default=self.default_release(channel))
#        arch = self.udd.data.clean_arch_name(optlist=optlist,
#                        args=something, default=self.default_arch())

        try:
            pack = self.udd.BindSourcePackage(package, release)
        except PackageNotFoundError:
            return self.notfound(irc, package, release, None)

        irc.reply("Source %s in %s: Binaries: %s" % \
                      (package, release, ", ".join(pack.Binaries())))

    binaries = wrap(binaries, ['something',
                              getopts({'release':'something'}),
                              any('something')])

    def builddep(self, irc, msg, args, package, optlist, something):
        """<packagename> [--release <stable>]

        Show the name of the binary packages on which a given source package
        or binary package build-depends.
        By default, the current stable release is used.
        """
        channel = msg.args[0]
        release = self.udd.data.clean_release_name(optlist=optlist,
                        args=something, default=self.default_release(channel))
        arch = self.udd.data.clean_arch_name(optlist=optlist,
                        args=something, default=None)

        # FIXME: make b-d list arch-specific
        try:
            pack = self.udd.BindSourcePackage(package, release)
        except PackageNotFoundError:
            return self.notfound(irc, package, release, arch)

        bd = pack.BuildDepends()
        bdi = pack.BuildDependsIndep()
        irc.reply("Package %s in %s -- %s." %
                  (package, release,
                    "; ".join(
                    self._builddeps_formatter(bd, bdi))))

    builddep = wrap(builddep, ['something',
                                getopts({'release':'something'}),
                                any('something')])

    def relationship_helper(self, irc, msg, args, package, optlist, something, relation):
        """Does the dirty work for each of the functions that show
        "conflicts", "depends", "recommends", "suggests", "enhances".

        The standard usage for each of these functions is accepted:
            relationship <packagename> [--arch <amd64>] [--release <stable>]

        Show the packages that are listed as 'Depends' for a given package.
        By default, the current stable release and amd64 are used.
        """
        known_relations = [ 'conflicts',
                           'depends',
                           'recommends',
                           'suggests',
                           'enhances' ]

        if not relation in known_relations:
            irc.error("Sorry, unknown error determining package relationship.")

        channel = msg.args[0]
        release = self.udd.data.clean_release_name(optlist=optlist,
                        args=something, default=self.default_release(channel))
        arch = self.udd.data.clean_arch_name(optlist=optlist,
                        args=something, default=self.default_arch(channel))

        pack = self.udd.BindPackage(package, release, arch)

        if pack.Found():
            irc.reply("Package %s in %s/%s -- %s: %s." % \
                      (package, release, arch,
                        relation, pack.RelationEntry(relation)))
        else:
            return self.notfound(irc, package, release, arch)

    def conflicts(self, irc, msg, args, package, optlist, something):
        """<packagename> [--arch <amd64>] [--release <stable>]

        Show the binary packages listed as conflicting with a given binary
        package.
        By default, the current stable release and amd64 are used.
        """
        self.relationship_helper(irc, msg, args, package, optlist, something, 'conflicts')

    conflicts = wrap(conflicts, ['something', getopts({'arch':'something',
                                                       'release':'something'}),
                                 any('something')])

    def depends(self, irc, msg, args, package, optlist, something):
        """<packagename> [--arch <amd64>] [--release <stable>]

        Show the packages that are listed as 'Depends' for a given package.
        By default, the current stable release and amd64 are used.
        """
        self.relationship_helper(irc, msg, args, package, optlist, something, 'depends')

    depends = wrap(depends, ['something', getopts({'arch':'something',
                                                   'release':'something'}),
                                 any('something')])

    def recommends(self, irc, msg, args, package, optlist, something):
        """<packagename> [--arch <amd64>] [--release <stable>]

        Show the packages that are listed as 'Recommends' for a given package.
        By default, the current stable release and amd64 are used.
        """
        self.relationship_helper(irc, msg, args, package, optlist, something, 'recommends')

    recommends = wrap(recommends, ['something', getopts({'arch':'something',
                                                    'release':'something'}),
                                   any('something')])

    def suggests(self, irc, msg, args, package, optlist, something):
        """<packagename> [--arch <amd64>] [--release <stable>]

        Show the packages that are listed as 'Suggests' for a given package.
        By default, the current stable release and amd64 are used.
        """
        self.relationship_helper(irc, msg, args, package, optlist, something, 'suggests')

    suggests = wrap(suggests, ['something', getopts({'arch':'something',
                                                    'release':'something'}),
                               any('something')])

    def enhances(self, irc, msg, args, package, optlist, something):
        """<packagename> [--arch <amd64>] [--release <stable>]

        Show the packages that are listed as 'Enhances' for a given package.
        By default, the current stable release and amd64 are used.
        """
        self.relationship_helper(irc, msg, args, package, optlist, something, 'enhances')

    enhances = wrap(enhances, ['something', getopts({'arch':'something',
                                                    'release':'something'}),
                               any('something')])

    def checkdeps(self, irc, msg, args, package, optlist, something):
        """<packagename> [--arch <amd64>] [--release <stable>] [--type depends|recommends|suggests]

        Check that the dependencies listed by a package are satisfiable for the
        specified release and architecture.
        By default, all dependency types with the current stable release and
        amd64 are used.
        """
        channel = msg.args[0]
        release = self.udd.data.clean_release_name(optlist=optlist,
                        args=something, default=self.default_release(channel))
        arch = self.udd.data.clean_arch_name(optlist=optlist,
                        args=something, default=self.default_arch(channel))

        relation = []
        for (option, arg) in optlist:
            if option == 'type':
                if arg in self.udd.data.relations:
                    relation.append(arg)
                else:
                    irc.error("Unknown relationship type.")
                    return

        if not relation:
            relation = self.udd.data.relations

        try:
            status = self.dispatcher.checkdeps(package, release, arch, relation)
        except PackageNotFoundError:
            return self.notfound(irc, package, release, arch)

        badlist = []
        for rel in relation:
            if status[rel].bad:
                badlist.append("%s: %s" % (self.bold(rel.title()), str(status[rel].bad)))

        if badlist:
            irc.reply("Package %s in %s/%s unsatisfiable dependencies: %s." %
                        (package, release, arch, "; ".join(badlist)))
        else:
            irc.reply("Package %s in %s/%s: all dependencies satisfied." %
                        (package, release, arch))

    checkdeps = wrap(checkdeps, ['something',
                                  getopts({'arch':'something',
                                           'release':'something',
                                           'type':'something'}),
                                  any('something')])

    def checkinstall(self, irc, msg, args, package, optlist, something):
        """<packagename> [--arch <amd64>] [--release <stable>] [--norecommends]

        Check that the package is installable (i.e. dependencies checked
        recursively) within the specified release and architecture.
        By default, recommended packages are checked too and the current
        stable release and amd64 are used.
        """
        channel = msg.args[0]
        release = self.udd.data.clean_release_name(optlist=optlist,
                        args=something, default=self.default_release(channel))
        arch = self.udd.data.clean_arch_name(optlist=optlist,
                        args=something, default=self.default_arch(channel))

        withrecommends = True
        for (option, arg) in optlist:
            if option == 'norecommends':
                withrecommends = False

        try:
            solverh = self.dispatcher.checkInstall(package, release, arch,
                                              withrecommends)
        except PackageNotFoundError:
            return self.notfound(irc, package, release, arch)

        solverh = solverh.flatten()
        details = []
        if solverh.depends.satisfied:
            details.append("all Depends are satisfied")
        else:
            details.append("%d packages in the Depends chain are uninstallable"
                            % len(solverh.depends.bad))
        if withrecommends:
            if solverh.recommends.satisfied:
                details.append("all Recommends are satisfied")
            else:
                details.append("%d packages in the Recommends chain are "
                                "uninstallable" % len(solverh.recommends.bad))

        irc.reply("Package %s on %s/%s: %s" % \
                    (package, release, arch, "; ".join(details)))

    checkinstall = wrap(checkinstall, ['something',
                                        getopts({'arch':'something',
                                                 'release':'something',
                                                 'norecommends':'' }),
                                        any('something')])

    def why(self, irc, msg, args, package1, package2, optlist, something):
        """<package1> <package2> [--arch <amd64>] [--release <stable>] [--norecommends]

        Find dependency chains  between the two packages within the specified
        release and architecture.
        By default, recommended packages are checked too and the current
        stable release and amd64 are used.
        """
        channel = msg.args[0]
        release = self.udd.data.clean_release_name(optlist=optlist,
                        args=something, default=self.default_release(channel))
        arch = self.udd.data.clean_arch_name(optlist=optlist,
                        args=something, default=self.default_arch(channel))

        withrecommends = True
        for (option, arg) in optlist:
            if option == 'norecommends':
                withrecommends = False

        try:
            chains = self.dispatcher.why(package1, package2, release, arch,
                                              withrecommends)
        except PackageNotFoundError:
            return self.notfound(irc, package1, release, arch)

        details = ""
        if chains:
            chaintext = []
            for c in chains:
                chaintext.append(unicode(c))
            details = "Packages %s and %s in %s/%s " \
                        "are linked by %d chains: %s" % \
                            (package1, package2, release, arch,
                                len(chains),  "; ".join(chaintext))
        else:
            details= "No dependency chain found between "\
                        "packages %s and %s in %s/%s." % \
                            (package1, package2, release, arch)

        irc.reply(details.encode('UTF-8'))

    why= wrap(why, ['something', 'something',
                                        getopts({'arch':'something',
                                                 'release':'something',
                                                 'norecommends':'' }),
                                        any('something')])

    def _builddeps_formatter(self, bd, bdi):
        """Format a pair of build-depends lists (build-dep, build-dep-indep)"""
        def formatRel(rel, longname):
            """Format the individual relation"""
            if rel:
                return u"%s: %s" % (self.bold(longname), unicode(rel))
            return None

        sbuild = [
               formatRel(bd,  'Build-Depends'),
               formatRel(bdi, 'Build-Depends-Indep')
            ]
        return [item for item in sbuild if item]

    def _builddeps_status_formatter(self, status):
        """Format a build-deps status object"""
        if not status.AllFound():
            return u"unsatisfiable build dependencies: %s." % \
                    ";".join(self._builddeps_formatter(status.bd.bad,
                                                      status.bdi.bad))
        return u"all build-dependencies satisfied using %s." % \
                    ', '.join(status.ReleaseMap().keys())

    def checkbuilddeps(self, irc, msg, args, package, optlist, something):
        """<packagename> [--release <stable>] [--arch <amd64>]

        Check that the build-dependencies listed by a package are satisfiable
        for the specified release and host architecture.
        By default, the current stable release and amd64 are used.
        """
        channel = msg.args[0]
        release = self.udd.data.clean_release_name(optlist=optlist,
                        args=something, default=self.default_release(channel))
        arch = self.udd.data.clean_arch_name(optlist=optlist,
                        args=something, default=self.default_arch(channel))

        rel = self.udd.BindRelease(arch=arch, release=release)

        try:
            status = self.dispatcher.checkBackport(package, rel, rel)
        except PackageNotFoundError:
            return self.notfound(irc, package, None, None)

        irc.reply("Package %s in %s/%s: %s" % \
                        (package, release, arch,
                        self._builddeps_status_formatter(status)))

    checkbuilddeps = wrap(checkbuilddeps, ['something',
                                            getopts({'arch':'something',
                                                     'release':'something'}),
                                            any('something')])

    def checkbackport(self, irc, msg, args, package, optlist, something):
        """<packagename> [--fromrelease <sid>] [--torelease <stable>] [--arch <amd64>] [--verbose]

        Check that the build-dependencies listed by a package in the release
        specified as "fromrelease" are satisfiable for in "torelease" for the
        given host architecture.
        By default, a backport from unstable to the current stable release
        and amd64 are used.
        """
        channel = msg.args[0]
        fromrelease = self.udd.data.clean_release_name(optlist=optlist,
                            optname='fromrelease',
                            args=None, default=self.udd.data.devel_release)
        torelease = self.udd.data.clean_release_name(optlist=optlist,
                            optname='torelease',
                            args=None, default=self.default_release(channel))
        arch = self.udd.data.clean_arch_name(optlist=optlist,
                            args=something, default=self.default_arch(channel))

        fr = self.udd.BindRelease(arch=arch, release=fromrelease)
        # FIXME: should torelease do fallback to allow --to-release lenny-multimedia etc?
        releases = self.udd.data.list_dependent_releases(torelease,
                                                     suffixes=['backports'])

        pins = dict(zip(releases, reversed(range(len(releases)))))
        tr = self.udd.BindRelease(arch=arch,
                        release=releases, pins=pins)

        try:
            status = self.dispatcher.checkBackport(package, fr, tr)
        except PackageNotFoundError:
            return self.notfound(irc, package, fromrelease, arch)

        irc.reply((u"Backporting package %s in %s→%s/%s: %s" % \
                    (package, fromrelease, torelease, arch,
                    self._builddeps_status_formatter(status))).encode('UTF-8'))

        verbose = [option for (option, arg) in optlist if option == 'verbose']
        if verbose:
            rm = status.ReleaseMap()
            reply = []
            for release in rm.keys():
                packages = rm[release]
                reply.append("%s: %s" % (self.bold(release), ",".join([str(p) for p in packages])))

            irc.reply("; ".join(reply), to=msg.nick, private=True)


    checkbackport = wrap(checkbackport, ['something',
                                          getopts({'arch':'something',
                                                   'fromrelease':'something',
                                                   'torelease':'something',
                                                   'verbose':''}),
                                         any('something')])

    def popcon(self, irc, msg, args, package):
        """<packagename>

        Show the popcon (popularity contents) data for a given binary package.
        http://popcon.debian.org/FAQ
        """
        try:
            popdata = self.dispatcher.popcon(package)
        except PackageNotFoundError:
            return self.notfound(irc, package, None, None)

        irc.reply("Popcon data for %s: inst: %d, vote: %d, "
                    "old: %d, recent: %d, nofiles: %d" %
                    (package, popdata['insts'], popdata['vote'],
                    popdata['olde'], popdata['recent'], popdata['nofiles']))

    popcon = wrap(popcon, ['something'])

    def maint(self, irc, msg, args, package, version):
        """<packagename> [<version>]

        Return the names of the person who uploaded the source package, the
        person who changed the package prior to upload and the maintainer of
        the specified source package. If version is omitted, the most recent
        upload is used. Imperfect binary-to-source package mapping will be
        attempted.
        """
        self._uploads_helper(irc, msg, args, package, version, 1)

    maint      = wrap(maint, ['something', optional('something')])

    def whouploads(self, irc, msg, args, package, number):
        """<packagename> [<number>]

        Return the names of the person who uploaded the source package, the
        person who changed the package prior to upload and the maintainer of
        the specified source package. Up to <number> (default 3) uploads are
        listed. Imperfect binary-to-source package mapping will be attempted.
        """
        if number and int(number) == number and number > 0:
            number = int(number)
        else:
            number = 3
        self._uploads_helper(irc, msg, args, package, None, number)

    whouploads = wrap(whouploads, ['private', 'something',
                                  optional('positiveInt')])

    def _uploads_helper(self, irc, msg, args, package, version, number):
        """ helper function to obtain data about uploads """
        try:
            release = self.udd.data.clean_release_name(#optlist=optlist, args=something,
                            default=self.udd.data.devel_release)

            pack = self.udd.BindSourcePackage(package, release)
            uploads = self.dispatcher.uploads(pack, max=number, version=version)
        except PackageNotFoundError:
            if version:
                irc.reply("Sorry, there is no record of '%s', version '%s'." %
                                    (package, version))
            else:
                irc.reply("Sorry, there is no record of '%s'." % package)
            return

        for u in uploads:
            reply = u"Package %s version %s was uploaded by %s on %s, " \
                        "last changed by %s and maintained by %s." % \
                    (u['source'], u['version'], u['signed_by_name'],
                        u['date'].date(),
                        u['changed_by_name'], u['maintainer_name'])
            if u['nmu']:
                reply += u" (non-maintainer upload)"
            irc.reply(reply.encode("UTF-8"))

    def recent(self, irc, msg, args, package, version):
        """<packagename>

        Return the dates and versions of recent uploads of the specified source
        package.
        Imperfect binary-to-source package mapping will be tried too.
        """
        release = self.udd.data.clean_release_name(#optlist=optlist, args=something,
                            default=self.udd.data.devel_release)

        try:
            p = self.udd.BindSourcePackage(package, release)
            uploads = self.dispatcher.uploads(p, max=10, version=version)
        except PackageNotFoundError:
            irc.reply("Sorry, there is no record of source package '%s'." %
                            package)
            return

        uploads = ["%s %s" % (self.bold(u['version']), u['date'].date()) for u in uploads]
        reply = "Package %s recent uploads: %s." % \
                    (package, ", ".join(uploads))
        irc.reply(reply)

    recent   = wrap(recent, ['something', optional('something')])

    class bug(callbacks.Commands):
        def __init__(self, irc):
            self.__parent = super(callbacks.Commands, self)
            self.__parent.__init__(irc)
            self._found_conf = False
            self.throttle = RequestThrottle()

        def _find_conf(self, irc):
            if self._found_conf:
                return
            outer = irc.getCallback('Judd')
            self.registryValue = outer.registryValue
            self.udd = outer.udd
            self.dispatcher = outer.bugs_dispatcher
            self.bold = outer.bold
            self.log = outer.log
            self.throttle.log = outer.log
            self._found_conf = True

        def bug(self, irc, msg, args, search, titlesearch):
            """<number>|<package> [title]

            Show bug information about from the Debian Bug Tracking System,
            searching by bug number, package name or package name and title.
            """
            self._find_conf(irc)
            search = search.replace('#', '')
            if search.isdigit():
                self._bug_number(irc, int(search), False)
            elif not titlesearch:
                self._bug_summary(irc, search)
            else:
                self._bug_title_search(irc, msg, search, titlesearch)

        bug = wrap(bug, ['something', optional('something')])

        def autobug(self, irc, msg, args, search):
            """<number>

            Show information about a bug from the Debian Bug Tracking System,
            limiting how often the information will be repeated.
            """
            self._find_conf(irc)
            search = search.replace('#', '')
            if search.isdigit():
                channel = msg.args[0]
                if (self.throttle.permit(msg, search)) \
                    and not re.search(self.registryValue('auto_bug_ignore_re', channel), msg.nick):
                    self._bug_number(irc, int(search), True)
                self.throttle.record(msg,
                        self.registryValue('auto_bug_throttle', channel),
                        search)
            else:
                # should never get here; just log it
                self.log("Unacceptable input to autobug: '%s'", search)

        autobug = wrap(autobug, ['something'])

        def rm(self, irc, msg, args, search):
            """<package>

            Looks for removal reasons for a package
            """
            self._find_conf(irc)
            bugs = self.dispatcher.rm(search)
            if bugs:
                self._show_bug(irc, bugs[0])
            else:
                irc.reply("Sorry, no removal reasons were found.")

        rm = wrap(rm, ['something'])

        def wnpp(self, irc, msg, args, search, optlist):
            """<package>

            Looks for WNPP (work-needed and prospective package) bugs
            for a package
            """
            self._find_conf(irc)
            bug_type = None
            for (option, arg) in optlist:
                if option == 'type' and arg.upper() in uddcache.bts.wnpp_types:
                    bug_type = arg.upper()
            bugs = self.dispatcher.wnpp(search, bug_type)
            if bugs:
                self._show_bug(irc, bugs[0])
            else:
                irc.reply("Sorry, no wnpp bugs were found.")

        wnpp = wrap(wnpp, ['something',
                            getopts({'type':'something'})])

        def _bug_number(self, irc, bugno, silent_failures):
            try:
                bug = self.dispatcher.bug(bugno, True)
            except BugNotFoundError:
                if not silent_failures:
                  irc.reply("Sorry, the requested bug was not found.")
                return
            return self._show_bug(irc, bug)

        def _bug_title_search(self, irc, msg, package, title):
            bugs = self.dispatcher.bug_package_search(package, title, verbose=True, archived=False)
            if len(bugs) > 10:
                irc.reply("Matching bugs: %s" % ", ".join(["#%d" % b.id for b in bugs]))
            else:
                if not bugs:
                    irc.reply("Sorry, no bugs match that search criterion.", to=msg.nick, private=True)
                for b in bugs:
                    irc.reply(self._format_bug(b).encode('UTF-8'), to=msg.nick, private=True)

        def _format_bug(self, bug):
            title = bug.title.splitlines()
            if title:
                title = title[0]
            else:
                title = ""

            status = [bug.readable_status]
            [status.append(t) for t in bug.tags if t not in status]

            return u"Bug http://bugs.debian.org/%d in %s (%s): «%s»; " \
                        "severity: %s; opened: %s; last modified: %s." % \
                        (bug.id, bug.package, ", ".join(status), title,
                        bug.severity, bug.arrival.date(), bug.last_modified.date())

        def _show_bug(self, irc, bug):
            irc.reply(self._format_bug(bug).encode('UTF-8'))

        def _bug_summary(self, irc, package):
            bug_count = []
            bugs = self.dispatcher.bug_package(package, verbose=False, archived=False, filter={'status': ('forwarded', 'pending', 'pending-fixed')})
            for s in uddcache.bts.severities:
                bs = [b for b in bugs if b.severity == s]
                if bs:
                    bug_count.append("%s: %d" % (s, len(bs)))

            bugs = self.dispatcher.wnpp(package)
            for t in uddcache.bts.wnpp_types:
                bt = [b for b in bugs if b.wnpp_type == t]
                if bt:
                    bug_count.append("%s: #%d" % (bt[0].wnpp_type, bt[0].id))

            bugs = self.dispatcher.rm(package, False)
            if bugs:
                bug_count.append("RM: #%d" % bugs[0].id)

            if not bug_count:
                irc.reply("No bugs were found in package %s." % package)
                return

            irc.reply("Bug summary for package %s: %s" % \
                        (package, ", ".join(bug_count))
                      )

        def rc(self, irc, msg, args, package):
            """<package>

            List the release critical bugs for a given source package. Binary
            package names will be mapped to source package names.
            """
            self._find_conf(irc)
            bugs = self.dispatcher.rcbugs(package, True)
            if not bugs:
                irc.reply("No release critical bugs were found in "
                            "package '%s'." % package)
                return

            buglist = []
            for bug in bugs:
                status = [bug.readable_status]
                [status.append(t) for t in bug.tags if t not in status]
                buglist.append("#%d (%s)" % (bug.id, ", ".join(status)))

            irc.reply("Release critical bugs in package %s (%d): %s" % \
                        (package, len(bugs), ", ".join(buglist))
                      )

        rc = wrap(rc, ['something'] )

        def rfs(self, irc, msg, args, package):
            """<package>

            List RFS (request for sponsorship) bugs for a package. Imperfect
            substring matching against the bug title is performed."""
            self._find_conf(irc)
            bugfilter={'title': package,
                        'status': ('forwarded', 'pending', 'pending-fixed')}
            bugs = self.dispatcher.bug_package("sponsorship-requests",
                                           verbose=True, # always get tags
                                           archived=False,
                                           filter=bugfilter)
            if not bugs:
                return irc.reply("Sorry, no open RFS bugs found for '%s'."
                                 % package)
            if len(bugs) > 3:
                return irc.reply("Lots of RFS bugs match that query: %s" %
                                 ", ".join(["#%d" % b.id for b in bugs]))
            s = []
            for bug in bugs:
                status = [bug.readable_status]
                [status.append(t) for t in bug.tags if t not in status]
                if bug.owner:
                    contacts = u"%s/%s" % (bug.submitter, bug.owner)
                else:
                    contacts = bug.submitter
                s.append("#%s (%s): %s (%s)" % \
                     (self.bold(bug.id), ", ".join(status),
                        bug.title.splitlines()[0], contacts))
            irc.reply("; ".join(s))

        rfs = wrap(rfs, ['something'])

    def file(self, irc, msg, args, glob, optlist, something):
        """<pattern> [--arch <amd64>] [--release <stable>] [--regex | --exact]

        Returns packages that include files matching <pattern> which, by
        default, is interpreted as a glob (see glob(7)).
        If --regex is given, the pattern is treated as a extended regex
        (see regex(7); note not PCRE!).
        If --exact is given, the exact filename is required.
        The current stable release and amd64 are searched by default.
        """
        # Based on the file command in the Debian plugin by James Vega

        channel = msg.args[0]
        release = self.udd.data.clean_release_name(optlist=optlist,
                        args=something, default=self.default_release(channel))
        arch = self.udd.data.clean_arch_name(optlist=optlist,
                        args=something, default=self.default_arch(channel))

        mode = 'glob'
        for (option, arg) in optlist:
            if option == 'exact':
                mode = 'exact'
            elif option == 'regex' or option == 'regexp':
                mode = 'regex'

        # Convert the glob/re/fixed string to a regexp.
        # Strip leading / since they're not in the index anyway.
        # Contents file is whitespace delimited.
        regexp = glob
        if mode == 'glob':
            regexp = fnmatch.translate(regexp)
            #print regexp
            if regexp.startswith(r'\/'):
                regexp = '^' + regexp[2:]
            elif not regexp.startswith(r'.*'):
                regexp = '.*' + regexp
            if regexp.endswith(r'$'):
                regexp = regexp[:-1] + r'[[:space:]]'
            elif regexp.endswith(r'\Z(?ms)'):
                regexp = regexp[:-7] + r'[[:space:]]'
        elif mode == 'regex':
            if regexp.startswith(r'/'):
                regexp = '^' + regexp[1:]
            if regexp.endswith(r'$'):
                regexp = regexp[:-1] + r'[[:space:]]'
        else:
            regexp = regexp = r'^%s[[:space:]]' % re.escape(regexp.lstrip(r'/'))

        self.log.debug("RE=%s" % regexp)

        path = os.path.join(conf.supybot.directories.data(),
                            self.registryValue('base_path'))

        contents = debcontents.contents_file.contents_file(path, release, arch,
                                            ['main', 'contrib', 'non-free'])

        try:
            packages = contents.search(regexp)
        except debcontents.contents_file.ContentsError, e:
            self.log.error("File search for '%s' produced re '%s' "
                            "and errors: %s",  glob, regexp, e)
            irc.error("Sorry, an error occurred trying to search for that "
                        "file. Further details have been logged.")
            return

        if len(packages) == 0:
            irc.reply('No packages in %s/%s were found with that file.' % \
                  (release, arch))
        else:
            s = packages.to_string(self.bold)
            truncated =  ""
            if packages.results_truncated:
                truncated = "[truncated] "
            irc.reply("Search for %s in %s/%s: %s%s" % \
                      (glob, release, arch, truncated, s))

    file = wrap(file, ['something',
                        getopts({'arch':'something',
                                'release':'something',
                                'regex':'',
                                'regexp':'',
                                'exact':''
                                }),
                       optional('something')
                       ])

    def alternative(self, irc, msg, args, filename):
        """<pattern>

        Returns packages that provide alternatives for either the absolute path
        <pattern> or the alternative name <pattern>.
        Only the unstable release can be searched at present.
        """

        channel = msg.args[0]
        release = "sid"
        arch = "alt"
        if filename.startswith("/"):
            filename = filename[1:]
            regexp = "^%s\s+" % filename
        elif "/" not in filename:
            regexp = "^[^[:space:]]+/%s\s+" % filename
        else:
            irc.error("Either a full path or the filename only "
                "must be specified.")
            return

        path = os.path.join(conf.supybot.directories.data(),
                            self.registryValue('base_path'))

        contents = debcontents.contents_file.contents_file(path, release, arch,
                                            ['main', 'contrib', 'non-free'])

        try:
            packages = contents.search(regexp)
        except debcontents.contents_file.ContentsError, e:
            self.log.error("File search for '%s' produced re '%s' "
                            "and errors: %s",  filename, regexp, e)
            irc.error("Sorry, an error occurred trying to search for that "
                        "alternative. Further details have been logged.")
            return

        if len(packages) == 0:
            irc.reply('No packages in %s were found with that alternative.' % \
                  release)
        else:
            packs = sorted([k[4:] for k in packages.keys()])
            s = ", ".join(packs)
            irc.reply("Alternative %s in %s: %s." % \
                      (filename, release, s))

    alternative = wrap(alternative, ['something'])

    def bold(self, s):
        """return the string in bold markup if required"""
        if self.registryValue('bold', dynamic.channel):
            return ircutils.bold(s)
        return s

    def default_release(self, channel):
        """the release that is the default for the current channel"""
        return self.registryValue('default_release', channel)

    def default_arch(self, channel):
        """the architecture that is the default for the current channel"""
        return self.registryValue('default_arch', channel)


class RequestThrottle(object):
    """ A throttle to control the rate of automated responses """
    def __init__(self):
        self.cache = {}
        self.limit_private = False

    def permit(self, msg, *args):
        """ permit the request according to the throttle conditions
        (False disallows the call) """
        channel = msg.args[0]
        if self.limit_private and not channel.startswith("#"):
            # don't throttle privmsg queries
           return False

        reqid = self._id(channel, *args)
        ts = time.time()
        permit = not (reqid in self.cache and self.cache[reqid] > ts)
        if self.log:
            if permit:
                self.log.info("Permitting request id %s", reqid)
            else:
                self.log.info("Not permitting request %s", reqid)
        return permit

    def _id(self, channel, *args):
        return "/".join((channel,) + args)

    def record(self, msg, timeout, *args):
        """track a timestamp for this throttle """
        channel = msg.args[0]
        reqid = self._id(channel, *args)
        ts = time.time()
        self.cache[reqid] = ts + timeout
        # clean out old timestamps; there will never be enough entries in
        # the cache for performance to be slow enough to be an issue
        [self.cache.pop(k) for k in self.cache.keys() if self.cache[k] < ts]


Class = Judd

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
