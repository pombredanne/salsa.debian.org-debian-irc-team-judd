###
# -*- coding: utf-8 -*-
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


import os
#import gzip
#import time
#import popen2
import fnmatch
import subprocess
#from supybot.utils.iter import all, imap, ifilter
import PackageFileList

import uddcache.udd
import uddcache.commands
import uddcache.config
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

        confdict = {
                        'database': self.registryValue('db_database'),
                        'hostname': self.registryValue('db_hostname'),
                        'port': self.registryValue('db_port'),
                        'username': self.registryValue('db_username'),
                        'password': self.registryValue('db_password')
                    }
        conf = uddcache.config.Config(confdict=confdict)
        self.udd = uddcache.udd.Udd(conf)
        #self.udd = uddcache.udd.Udd()
        self.dispatcher = uddcache.commands.Commands(self.udd)

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
        """<pattern> [--arch <i386>] [--release <stable>]

        Show the available versions of a package in the optionally specified
        release and for the given architecture.
        All current releases and i386 are searched by default. By default, binary
        packages are searched; prefix the packagename with "src:" to search
        source packages.
        """
        release = self.udd.data.clean_release_name(optlist=optlist,
                                    args=something, default=None)
        arch = self.udd.data.clean_arch_name(optlist=optlist,
                                    args=something, default=self.default_arch())

        pkgs = self.dispatcher.versions(package, release, arch)
        if not pkgs:
            return self.notfound(irc, package, release, arch)

        replies = []
        for row in pkgs:
            if (row['component'] == 'main'):
                replies.append("%s %s" % \
                                ("%s:" % self.bold(row['release']), row['version']))
            else:
                replies.append("%s %s" % \
                                ("%s/%s:" % (self.bold(row['release']), row['component']),
                                  row['version']))

        irc.reply("Package: %s on %s -- %s" % (package, arch,
                            "; ".join(replies)))

    versions = wrap(versions, ['something',
                                getopts( { 'arch':'something',
                                           'release':'something' } ),
                                any( 'something' ) ] )

    def names(self, irc, msg, args, package, optlist, something):
        """<pattern> [--arch <i386>] [--release <stable>]

        Search package names with * and ? as wildcards.
        The current stable release and i386 are searched by default.
        """
        release = self.udd.data.clean_release_name(optlist=optlist,
                                    args=something, default=self.default_release())
        arch = self.udd.data.clean_arch_name(optlist=optlist,
                                    args=something, default=self.default_arch())

        pkgs = self.dispatcher.names(package, release, arch)
        if not pkgs:
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

        irc.reply("Search for %s in %s/%s: %s" % (package, release, arch, "; ".join(replies)))

    names = wrap(names, ['something',
                          getopts( { 'arch':'something',
                                     'release':'something' } ),
                          any( 'something' ) ] )

    def info(self, irc, msg, args, package, optlist, something ):
        """<packagename> [--arch <i386>] [--release <stable>]

        Show the short description and some other brief details about a package
        in the specified release and architecture. By default, the current
        stable release and i386 are used.
        """
        release = self.udd.data.clean_release_name(optlist=optlist,
                                    args=something, default=self.default_release())
        arch = self.udd.data.clean_arch_name(optlist=optlist,
                                    args=something, default=self.default_arch())

        p = self.dispatcher.info(package, release, arch)
        if p:
            ds = p['description'].splitlines()
            if ds:
                d = ds[0]
            else:
                d = ""
            reply = "Package %s (%s, %s) in %s/%s: %s. Version: %s; Size: %0.1fk; Installed: %dk" % \
                      ( package, p['section'], p['priority'],
                        release, arch, d,
                        p['version'], p['size'] / 1024.0, p['installed_size'] )
            if p['homepage']:    # homepage field
                reply += "; Homepage: %s" % p['homepage']
            if p['screenshot_url']:    # screenshot url from screenshots.debian.net
                reply += "; Screenshot: %s" % p['screenshot_url']
            irc.reply(reply)
        else:
            return self.notfound(irc, package, release, arch)

    info = wrap(info, ['something',
                        getopts( { 'arch':'something',
                                   'release':'something' } ),
                        any( 'something' ) ] )

    def archs(self, irc, msg, args, package, optlist, something ):
        """<packagename> [--release <stable>]

        Show for what architectures a package is available. By default, the current
        stable release is used.
        """
        release = self.udd.data.clean_release_name(optlist=optlist,
                                    args=something, default=self.default_release())
        arch = self.udd.data.clean_arch_name(optlist=optlist,
                                    args=something, default=self.default_arch())

        pkgs = self.dispatcher.archs(package, release)

        if not pkgs:
            return self.notfound(irc, package, release, None)

        replies = []
        for row in pkgs:
            replies.append("%s (%s)" % (row[0], row[1]))
        irc.reply("Package %s in %s: %s" % (package, release, ", ".join(replies)))

    archs  = wrap(archs, ['something',
                                getopts({ 'release':'something' } ),
                                any( 'something' ) ] )

    def rprovides( self, irc, msg, args, package, optlist, something ):
        """<packagename> [--arch <i386>] [--release <stable>]

        Show the packages that 'Provide' the specified virtual package
        ('reverse provides').
        By default, the current stable release and i386 are used.
        """
        release = self.udd.data.clean_release_name(optlist=optlist,
                                    args=something, default=self.default_release())
        arch = self.udd.data.clean_arch_name(optlist=optlist,
                                    args=something, default=self.default_arch())

        p = self.udd.BindPackage(package, release, arch)
        if p.IsVirtual():
            reply = "Package %s in %s/%s is provided by: %s." % \
                    (package, release, arch, ", ".join(p.ProvidersList()))
            if p.Found():
                reply += " %s is also a real package." % package
        else:
            if p.Found():
                reply = "In %s/%s, %s is a real package." % \
                            (release, arch, package)
            else:
                reply = "No packages provide '%s' in %s/%s." % \
                                                (package, release, arch)

        irc.reply(reply)

    rprovides = wrap(rprovides, ['something',
                                      getopts( { 'arch':'something',
                                                 'release':'something' } ),
                                      any( 'something' ) ] )

    def provides(self, irc, msg, args, package, optlist, something ):
        """<packagename> [--arch <i386>] [--release <stable>]

        Show the list of "provided" packages for the specified binary package
        in the given release and architecture. By default, the current
        stable release and i386 are used.
        """
        release = self.udd.data.clean_release_name(optlist=optlist,
                                    args=something, default=self.default_release())
        arch = self.udd.data.clean_arch_name(optlist=optlist,
                                    args=something, default=self.default_arch())

        p = self.udd.BindPackage(package, release, arch)

        if p.Found():
            if p.data['provides']:
                irc.reply("Package %s in %s/%s provides: %s." % \
                            (package, release, arch, p.data['provides']))
            else:
                irc.reply("Package %s in %s/%s provides no additional packages." % \
                            (package, release, arch))
        else:
            return self.notfound(irc, package, release, arch)

    provides = wrap(provides, ['something',
                              getopts( { 'arch':'something',
                                         'release':'something' } ),
                              any( 'something' ) ] )

    def danke( self, irc, msg, args ):
        """
        Someone is trying to speak esperanto to me
        """
        irc.reply( "ne dankinde" )

    danke = wrap( danke, [] )

    def src( self, irc, msg, args, package, optlist, something ):
        """<packagename> [--release <stable>]

        Show the name of the source package from which a given binary package
        is derived.
        By default, the current stable release and i386 are used.
        """
        release = self.udd.data.clean_release_name(optlist=optlist,
                                    args=something, default=self.default_release())
        arch = self.udd.data.clean_arch_name(optlist=optlist,
                                    args=something, default=self.default_arch())

        r = self.udd.BindRelease(release, arch)
        p = r.bin2src(package)
        if p:
            irc.reply("Package %s in %s -- source: %s" % (package, release, p))
        else:
            return self.notfound(irc, package, release, arch,
                            message="Sorry, there is no record of a source package for the binary package '%s'%s.")

    src = wrap(src, ['something',
                        getopts( { 'release':'something' } ),
                        any( 'something' ) ] )

    def binaries( self, irc, msg, args, package, optlist, something ):
        """<packagename> [--release <stable>]

        Show the name of the binary package(s) that are derived from a given
        source package.
        By default, the current stable release and i386 are used.
        """
        release = self.udd.data.clean_release_name(optlist=optlist,
                                    args=something, default=self.default_release())
#        arch = self.udd.data.clean_arch_name(optlist=optlist,
#                                    args=something, default=self.default_arch())

        p = self.udd.BindSourcePackage(package, release)

        if p.Found():
            irc.reply("Source %s in %s: Binaries: %s" % \
                      (package, release, ", ".join(p.Binaries())))
        else:
            return self.notfound(irc, package, release, None)

    binaries = wrap(binaries, ['something',
                              getopts( { 'release':'something' } ),
                              any( 'something' ) ] )

    def builddep( self, irc, msg, args, package, optlist, something ):
        """<packagename> [--release <stable>]

        Show the name of the binary packages on which a given source package
        or binary package build-depends.
        By default, the current stable release is used.
        """
        release = self.udd.data.clean_release_name(optlist=optlist,
                                    args=something, default=self.default_release())
        arch = self.udd.data.clean_arch_name(optlist=optlist,
                                    args=something, default=None)

        # FIXME: make b-d list arch-specific
        p = self.udd.BindSourcePackage(package, release)
        if p.Found():
            bd = p.BuildDepends()
            bdi = p.BuildDependsIndep()
            irc.reply("Package %s in %s-- %s." %
                      (package, release,
                        "; ".join(
                        self._buildDepsFormatter(bd, bdi))))
        else:
            return self.notfound(irc, package, release, arch)

    builddep = wrap(builddep, ['something',
                                getopts( { 'release':'something' } ),
                                any( 'something' )] )

    def relationshipHelper(self, irc, msg, args, package, optlist, something, relation):
        """Does the dirty work for each of the functions that show
        "conflicts", "depends", "recommends", "suggests", "enhances".

        The standard usage for each of these functions is accepted:
            relationship <packagename> [--arch <i386>] [--release <stable>]

        Show the packages that are listed as 'Depends' for a given package.
        By default, the current stable release and i386 are used.
        """
        knownRelations = [ 'conflicts',
                           'depends',
                           'recommends',
                           'suggests',
                           'enhances' ]

        if not relation in knownRelations:
            irc.error("Sorry, unknown error determining package relationships.")

        release = self.udd.data.clean_release_name(optlist=optlist,
                                    args=something, default=self.default_release())
        arch = self.udd.data.clean_arch_name(optlist=optlist,
                                    args=something, default=self.default_arch())

        p = self.udd.BindPackage(package, release, arch)

        if p.Found():
            irc.reply( "Package %s in %s/%s -- %s: %s." % \
                      (package, release, arch,
                        relation, p.RelationEntry(relation)) )
        else:
            return self.notfound(irc, package, release, arch)

    def conflicts( self, irc, msg, args, package, optlist, something ):
        """<packagename> [--arch <i386>] [--release <stable>]

        Show the binary packages listed as conflicting with a given binary
        package.
        By default, the current stable release and i386 are used.
        """
        self.relationshipHelper(irc, msg, args, package, optlist, something, 'conflicts')

    conflicts = wrap(conflicts, ['something', getopts( { 'arch':'something',
                                                         'release':'something' } ),
                                 any( 'something' )] )

    def depends( self, irc, msg, args, package, optlist, something ):
        """<packagename> [--arch <i386>] [--release <stable>]

        Show the packages that are listed as 'Depends' for a given package.
        By default, the current stable release and i386 are used.
        """
        self.relationshipHelper(irc, msg, args, package, optlist, something, 'depends')

    depends = wrap(depends, ['something', getopts( { 'arch':'something',
                                                         'release':'something' } ),
                                 any( 'something' )] )

    def recommends( self, irc, msg, args, package, optlist, something ):
        """<packagename> [--arch <i386>] [--release <stable>]

        Show the packages that are listed as 'Recommends' for a given package.
        By default, the current stable release and i386 are used.
        """
        self.relationshipHelper(irc, msg, args, package, optlist, something, 'recommends')

    recommends = wrap(recommends, ['something', getopts( { 'arch':'something',
                                                         'release':'something' } ),
                                   any( 'something' )] )

    def suggests( self, irc, msg, args, package, optlist, something ):
        """<packagename> [--arch <i386>] [--release <stable>]

        Show the packages that are listed as 'Suggests' for a given package.
        By default, the current stable release and i386 are used.
        """
        self.relationshipHelper(irc, msg, args, package, optlist, something, 'suggests')

    suggests = wrap(suggests, ['something', getopts( { 'arch':'something',
                                                         'release':'something' } ),
                               any( 'something' ) ] )

    def enhances( self, irc, msg, args, package, optlist, something ):
        """<packagename> [--arch <i386>] [--release <stable>]

        Show the packages that are listed as 'Enhances' for a given package.
        By default, the current stable release and i386 are used.
        """
        self.relationshipHelper(irc, msg, args, package, optlist, something, 'enhances')

    enhances = wrap(enhances, ['something', getopts( { 'arch':'something',
                                                         'release':'something' } ),
                               any( 'something' ) ] )

    def checkdeps( self, irc, msg, args, package, optlist, something ):
        """<packagename> [--arch <i386>] [--release <stable>] [--type depends|recommends|suggests|conflicts]

        Check that the dependencies listed by a package are satisfiable for the
        specified release and architecture.
        By default, all dependency types with the current stable release and
        i386 are used.
        """
        release = self.udd.data.clean_release_name(optlist=optlist,
                                    args=something, default=self.default_release())
        arch = self.udd.data.clean_arch_name(optlist=optlist,
                                    args=something, default=self.default_arch())

        relation = []
        for opt in optlist:
            if opt in self.udd.data.relations:
                relation.append(dep)
        if not relation:
            relation = self.udd.data.relations

        status = self.dispatcher.checkdeps(package, release, arch, relation)

        if status == None:
            return self.notfound(irc, package, release, arch)

        badlist = []
        for rel in relation:
            if status[rel].bad:
                badlist.append("%s: %s" % (self.bold(rel.title()), str(status[rel].bad)))

        if badlist:
            irc.reply( "Package %s in %s/%s unsatisfiable dependencies: %s." % \
                        ( package, release, arch, "; ".join(badlist) ) )
        else:
            irc.reply( "Package %s in %s/%s: all dependencies satisfied." % \
                        ( package, release, arch) )

    checkdeps = wrap(checkdeps, ['something',
                                  getopts( { 'arch':'something',
                                             'release':'something',
                                             'type':'something' } ),
                                  any( 'something' ) ] )

    def checkinstall( self, irc, msg, args, package, optlist, something ):
        """<packagename> [--arch <i386>] [--release <stable>] [--norecommends]

        Check that the package is installable (i.e. dependencies checked recursively)
        within the specified release and architecture.
        By default, recommended packages are checked too and the current
        stable release and i386 are used.
        """
        release = self.udd.data.clean_release_name(optlist=optlist,
                                    args=something, default=self.default_release())
        arch = self.udd.data.clean_arch_name(optlist=optlist,
                                    args=something, default=self.default_arch())

        withrecommends = True
        for (option,arg) in optlist:
            if option == 'norecommends':
                withrecommends = False

        solverh = self.dispatcher.checkInstall(package, release, arch,
                                              withrecommends)

        if not solverh:
            return self.notfound(irc, package, release, arch)

        details = []
        if solverh.depends.satisfied:
            details.append("all Depends are satisfied")
        else:
            details.append("%d packages in the Depends chain are uninstallable" % len(solverh.depends.bad))
        if withrecommends:
            if solverh.recommends.satisfied:
                details.append("all Recommends are satisfied")
            else:
                details.append("%d packages in the Recommends chain are uninstallable" % len(solverh.recommends.bad))

        irc.reply("Package %s on %s/%s: %s" % \
                    (package, release, arch, "; ".join(details)))

    checkinstall = wrap(checkinstall, ['something',
                                        getopts( { 'arch':'something',
                                                  'release':'something',
                                                  'norecommends':'' } ),
                                        any( 'something' ) ] )

    def _buildDepsFormatter(self, bd, bdi):
        def formatRel(rel, longname):
            if rel:
                return u"%s: %s" % (self.bold(longname), unicode(rel))
            return None

        l = [
               formatRel(bd,  'Build-Depends'),
               formatRel(bdi, 'Build-Depends-Indep')
            ]
        return filter(None, l)

    def _builddeps_status_formatter(self, status):
        if not status.AllFound():
            return u"unsatisfiable build dependencies: %s." % ";".join(self._buildDepsFormatter(status.bd.bad, status.bdi.bad))
        return u"all build-dependencies satisfied."


    def checkbuilddeps( self, irc, msg, args, package, optlist, something ):
        """<packagename> [--release <stable>] [--arch <i386>]

        Check that the build-dependencies listed by a package are satisfiable for the
        specified release and host architecture.
        By default, the current stable release and i386 are used.
        """
        release = self.udd.data.clean_release_name(optlist=optlist,
                                    args=something, default=self.default_release())
        arch = self.udd.data.clean_arch_name(optlist=optlist,
                                    args=something, default=self.default_arch())

        r = self.udd.BindRelease(arch=arch, release=release)
        status = self.dispatcher.checkBackport(package, r, r)

        if not status:
            return self.notfound(irc, package, None, None)

        irc.reply("Package %s in %s/%s: %s" % \
                        (package, release, arch,
                        self._builddeps_status_formatter(status)))

    checkbuilddeps = wrap(checkbuilddeps, ['something',
                                            getopts( {'arch':'something',
                                                      'release':'something'} ),
                                            any( 'something' ) ] )

    def checkbackport( self, irc, msg, args, package, optlist, something):
        """<packagename> [--fromrelease <sid>] [--torelease <stable>] [--arch <i386>]

        Check that the build-dependencies listed by a package in the release
        specified as "fromrelease" are satisfiable for in "torelease" for the
        given host architecture.
        By default, a backport from unstable to the current stable release
        and i386 are used.
        """
        fromrelease = self.udd.data.clean_release_name(optlist=optlist,
                                    optname='fromrelease',
                                    args=None, default=self.udd.data.devel_release)
        torelease = self.udd.data.clean_release_name(optlist=optlist,
                                    optname='torelease',
                                    args=None, default=self.default_release())
        arch = self.udd.data.clean_arch_name(optlist=optlist,
                                    args=something, default=self.default_arch())

        fr = self.udd.BindRelease(arch=arch, release=fromrelease)
        # FIXME: should torelease do fallback to allow --to-release lenny-multimedia etc?
        releases = self.udd.data.list_dependent_releases(torelease,
                                                     suffixes=['backports'])

        pins = dict(zip(releases, reversed(range(len(releases)))))
        tr = self.udd.BindRelease(arch=arch,
                        release=releases, pins=pins)

        status = self.dispatcher.checkBackport(package, fr, tr)

        if not status:
            return self.notfound(irc, package, fromrelease, arch)

        irc.reply((u"Backporting package %s in %s→%s/%s: %s" % \
                        (package, fromrelease, torelease, arch,
                        self._builddeps_status_formatter(status))).encode('UTF-8'))

    checkbackport = wrap(checkbackport, ['something',
                                          getopts( {'arch':'something',
                                                    'fromrelease':'something',
                                                    'torelease':'something' } ),
                                         any( 'something' ) ] )

    def bug( self, irc, msg, args, bugno ):
        """
        Show information about a bug in a given pacage.
        Usage: "bug bugnumber"
        """
        c = self.psql.cursor()
        c.execute( "SELECT package, status, severity, title, last_modified FROM bugs WHERE id=%(bugno)s limit 1", dict( bugno=bugno ) )

        row = c.fetchone()
        if row:
            ds = row[3].splitlines()
            if ds:
                d = ds[0]
            else:
                d = ""
            irc.reply( "Bug #%d (%s) %s -- %s; Severity: %s; Last Modified: %s" % ( bugno, row[1], row[0], d, row[2], row[4]) )

    bug = wrap(bug, ['int'] )

    def popcon( self, irc, msg, args, package ):
        """<packagename>

        Show the popcon (popularity contents) data for a given binary package.
        http://popcon.debian.org/FAQ
        """
        d = self.dispatcher.popcon(package)
        if not d:
            return self.notfound(irc, package, None, None)

        irc.reply("Popcon data for %s: inst: %d, vote: %d, "
                    "old: %d, recent: %d, nofiles: %d" %
                    (package, d['insts'], d['vote'], d['olde'],
                            d['recent'], d['nofiles']))

    popcon = wrap(popcon, ['something'])

    def maint( self, irc, msg, args, package, version ):
        """<packagename> [<version>]

        Return the names of the person who uploaded the source package, the person who
        changed the package prior to upload and the maintainer of the specified
        source package. If version is omitted, the most recent upload is used.
        Imperfect binary-to-source package mapping will be tried too.
        """

        release = self.udd.data.clean_release_name(#optlist=optlist, args=something,
                            default=self.udd.data.devel_release)

        p = self.udd.BindSourcePackage(package, release)
        uploads = self.dispatcher.uploads(p, max=1, version=version)
        if not uploads:
            if version:
                irc.reply("Sorry, there is no record of '%s', version '%s'." % (package,version))
            else:
                irc.reply("Sorry, there is no record of '%s'." % package )
            return

        u = uploads[0]
        reply = "Package %s version %s was uploaded by %s on %s, " \
                    "last changed by %s and maintained by %s." % \
                (package, u['version'], u['signed_by_name'],
                    u['date'].date(),
                    u['changed_by_name'], u['maintainer_name'])
        if u['nmu']:
            reply += " (non-maintainer upload)"
        irc.reply( reply )

    maint      = wrap(maint, ['something', optional( 'something' )] )

    def recent(self, irc, msg, args, package, version):
        """<packagename>

        Return the dates and versions of recent uploads of the specified source
        package.
        Imperfect binary-to-source package mapping will be tried too.
        """
        release = self.udd.data.clean_release_name(#optlist=optlist, args=something,
                            default=self.udd.data.devel_release)

        p = self.udd.BindSourcePackage(package, release)
        uploads = self.dispatcher.uploads(p, max=10, version=version)

        uploads = ["%s %s" % (self.bold(u['version']), u['date'].date()) for u in uploads]
        if uploads:
            reply = "Package %s recent uploads: %s." % \
                        (package, ", ".join(uploads))
            irc.reply( reply )
        else:
            irc.reply( "Sorry, there is no record of source package '%s'." % package )

    recent   = wrap(recent, ['something', optional( 'something' )] )

    def rcbugs( self, irc, msg, args, package ):
        """
        Return the release critical bugs for a given package.
        Usage: "rcbugs packagename"
        """

        c = self.psql.cursor()

        if package.startswith( 'src:' ):
            package = package[4:]
            c.execute( "SELECT id FROM bugs inner join packages on packages.package=bugs.package WHERE packages.source=%(package)s AND severity in ('critical', 'grave', 'serious' ) and status not in ('done,fixed') order by bugs.id", dict( package=package ) )
        else:
            c.execute( "SELECT id FROM bugs WHERE package=%(package)s AND severity in ('critical', 'grave', 'serious' ) and status not in ('done,fixed') order by bugs.id", dict( package=package ) )

        reply = "RC bugs in %s:" % package
        for row in c.fetchall():
            reply += " %d" % row[0]

        irc.reply( reply )

    rcbugs = wrap(rcbugs, ['something'] )

    def file(self, irc, msg, args, glob, optlist, something):
        """<pattern> [--arch <i386>] [--release <stable>] [--regex | --exact]

        Returns packages that include files matching <pattern> which, by
        default, is interpreted as a glob (see glob(7)).
        If --regex is given, the pattern is treated as a extended regex
        (see regex(7); note not PCRE!).
        If --exact is given, the exact filename is required.
        The current stable release and i386 are searched by default.
        """
        # Based on the file command in the Debian plugin by James Vega

        release = self.udd.data.clean_release_name(optlist=optlist,
                                    args=something, default=self.default_release())
        arch = self.udd.data.clean_arch_name(optlist=optlist,
                                    args=something, default=self.default_arch())

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

        packages = self.getContents(irc, release, arch, regexp)

        if len(packages) == 0:
            irc.reply('No packages were found with that file.')
        else:
            s = packages.to_string(self.bold)
            irc.reply("%s in %s/%s: %s" % (glob, release, arch, s))

    file = wrap(file, ['something',
                        getopts({'arch':'something',
                                'release':'something',
                                'regex':'',
                                'regexp':'',
                                'exact':''
                                }),
                       optional('something')
                       ])

    def getContents(self, irc, release, arch, regexp):
        """
        Find the packages that provide files matching a particular regexp.
        """
        # Abstracted out to permit substitution with a db etc

        path     = self.registryValue('base_path')
        data     = conf.supybot.directories.data()
        filename = 'debian-%s/Contents-%s.gz' % (release, arch)
        contents = os.path.join(data, path, filename)

        try:
            re_obj = re.compile(regexp, re.I)
        except re.error, e:
            irc.error(format('Error in regexp: %s', e), Raise=True)

        if not os.path.isfile(contents):
            irc.error("Sorry, couldn't look up file list.", Raise=True)

        try:
            #print "Trying: zgrep -iE -e '%s' '%s'" % (regexp, contents)
            output = subprocess.Popen(['zgrep', '-iE', '-e', regexp, contents],
                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True).communicate()[0]
        except TypeError:
            irc.error(r"Sorry, couldn't look up the file list.", Raise=True)

        packages = PackageFileList.PackageFileList()
        try:
            lines = output.split("\n")
            maxhits = 20
            if len(lines) > maxhits:
                irc.error('There were more than %s files matching your '
                          'search; please narrow your search.' % maxhits,
                          Raise=True)
            for line in lines:
                try:
                    (filename, pkg_list) = line.split()
                    if filename == 'FILE':
                        # This is the last line before the actual files.
                        continue
                except ValueError:  # Unpack list of wrong size.
                    continue        # We've not gotten to the files yet.
                packages.add(filename, pkg_list.split(','))
        finally:
            pass
        return packages

    def bold(self, s):
        if self.registryValue('bold', dynamic.channel):
            return ircutils.bold(s)
        return s

    def default_release(self):
        return self.registryValue('default_release', dynamic.channel)

    def default_arch(self):
        return self.registryValue('default_arch', dynamic.channel)

Class = Judd

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
