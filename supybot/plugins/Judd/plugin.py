###
# Copyright (c) 2007,2008, Mike O'Connor
# Copyright (c) 2010,      Stuart Prescott
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
from debian_bundle import debian_support

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
from PackageFileList import PackageFileList

release_map = { 'unstable':'sid', 'testing':'squeeze', 'stable':'lenny' }
releases = [ 'etch', 'etch-backports', 'etch-multimedia', 'etch-security', 'etch-volatile', 'experimental', 'lenny', 'lenny-multimedia', 'lenny-security', 'lenny-backports', 'lenny-volatile', 'squeeze', 'squeeze-security', 'squeeze-multimedia', 'sid', 'sid-multimedia', 'unstable', 'testing', 'stable' ]

arches = [ 'alpha', 'amd64', 'arm', 'armel', 'hppa', 'hurd-i386', 'i386', 'ia64', 'm68k', 'mips', 'mipsel', 'powerpc', 's390', 'sparc', 'all' ]

def parse_standard_options( optlist, args=None ):
    # FIXME: should this default to lenny/i386 if the args are out of bounds?
    if not args:
        args=[]
    release='lenny'
    arch='i386'

    for( option,arg ) in optlist:
        if option=='release':
            release=arg;
        elif option=='arch':
            arch=arg;

    if args in releases:
        release=args
    elif args in arches:
        arch=args

    if release_map.has_key( release ):
        release = release_map[ release ]

    if not release in releases:
        release=None

    if not arch in arches:
        arch=None

    return release, arch

class Release:
    def __init__(self, dbconn, arch="i386", release="lenny", **kwargs):
        self.dbconn = dbconn
        self.arch = arch
        self.release = release

class Package:
    fields = ['package']
    data = ''
    arch = ''
    def __init__(self, dbconn, arch="i386", release="lenny", package=None, **kwargs):
        if not package:
            raise ValueError("Package name not specified")
        self.dbconn = dbconn
        self.arch = arch
        self.release = release
        self.package = package
        self._Fetch()

    def _Fetch(self):
        c = self.dbconn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        f = ','.join(self.fields)
        c.execute(r"""SELECT """ + f + """
                      FROM packages
                      WHERE package=%(package)s
                        AND (architecture='all' OR architecture=%(arch)s)
                        AND release=%(release)s""",
                   dict( package=self.package,
                         arch=self.arch,
                         release=self.release) );
        self.data = c.fetchone()

    def Found(self):
        return len(self.data)

class PackageRelations(Package):
    def __init__(self, dbconn, arch="i386", release="lenny", package=None, **kwargs):
        self.fields = ['conflicts', 'depends', 'recommends', 'suggests', 'enhances']
        Package.__init__(self, dbconn, arch, release, package)

    def RelationEntry(self, relation):
        return self.data[relation]

    def RelationsEntryList(self, relation):
        return re.split(r"\s*,\s*", self.data[relation])

class Judd(callbacks.Plugin):
    """A plugin for querying a debian udd instance:  http://wiki.debian.org/UltimateDebianDatabase."""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(Judd, self)
        self.__parent.__init__(irc)

        self.psql = psycopg2.connect( "dbname='%s' host='%s' port='%d' password='%s' user='%s'" %
                                      ( self.registryValue('db_database'),
                                        self.registryValue('db_hostname'),
                                        self.registryValue('db_port'),
                                        self.registryValue('db_password'),
                                        self.registryValue('db_username') ),
                                      )

        self.psql.set_isolation_level(0)


    def versions(self, irc, msg, args, package, optlist, something ):
        """<pattern> [--arch <i386>] [--release <lenny>]

        Show the available versions of a package in the optionally specified
        release and for the given architecture.
        All current releases and i386 are searched by default. By default, binary
        packages are searched; prefix the packagename with "src:" to search
        source packages.
        """
        release = None
        arch='i386'
        atleastone=False

        for( option,arg ) in optlist:
            if option=='release':
                release=arg;
            elif option=='arch':
                arch=arg;
        for option in args:
            if option in releases:
                release=option
            elif option in arches:
                arch=option
        if release_map.has_key( release ):
            release = release_map[ release ]

        c = self.psql.cursor(cursor_factory=psycopg2.extras.DictCursor)
        if package.startswith('src:'):
            packagename = package[4:]
            sql = r"""SELECT DISTINCT release,version,component
                      FROM sources
                      WHERE source=%(package)s"""
            if release:
                sql += " AND release=%(release)s"
        else:
            packagename = package
            sql = r"""SELECT DISTINCT release,version,component
                      FROM packages
                      WHERE package=%(package)s AND
                        (architecture=%(arch)s OR architecture='all')"""
            if release:
                sql += " AND release=%(release)s"

        c.execute( sql,
                    dict( package=packagename,
                          arch=arch,
                          release=release ) );

        pkgs=[]
        for row in c.fetchall():
            pkgs.append( row )

        if not pkgs:
            irc.reply( "Sorry, no package named '%s' was found." % package )
            return

        pkgs.sort( lambda a,b: debian_support.version_compare( a['version'], b['version'] ) )

        replies = []
        for row in pkgs:
            if( row['component'] == 'main' ):
                replies.append("%s: %s" % \
                                (self.bold(row['release']), row['version']))
            else:
                replies.append("%s/%s: %s" % \
                                (self.bold(row['release']), row['component'],
                                  row['version']))

        irc.reply( "%s -- %s" % (package, "; ".join(replies)) )

    versions = wrap(versions, ['something', getopts( { 'arch':'something', 'release':'something' } ), optional( 'something' ) ] )

    def names(self, irc, msg, args, package, optlist, something ):
        """<pattern> [--arch <i386>] [--release <lenny>]

        Search package names with * and ? as wildcards.
        The current stable release and i386 are searched by default.
        """
        release,arch = parse_standard_options( optlist, something )

        c = self.psql.cursor(cursor_factory=psycopg2.extras.DictCursor)

        packagesql = package.replace( "*", "%" )
        packagesql = packagesql.replace( "?", "_" )

        if package.startswith('src:'):
            searchsource = True
            packagesql = packagesql[4:]
            sql = r"""SELECT DISTINCT version, source AS package, component
                      FROM sources
                      WHERE source LIKE %(package)s AND
                        release=%(release)s
                      ORDER BY source"""
        else:
            searchsource = False
            sql = r"""SELECT DISTINCT version, package, component
                      FROM packages
                      WHERE package LIKE %(package)s AND
                        (architecture=%(arch)s OR architecture='all') AND
                        release=%(release)s
                      ORDER BY package"""

        c.execute( sql,
                  dict( package=packagesql,
                          arch=arch,
                          release=release ) );
        pkgs=[]
        for row in c.fetchall():
            pkgs.append( row )

        if not pkgs:
            irc.reply( "Sorry, no packages matching '%s' were found." % package )
            return

        replies=[]
        for row in pkgs:
            if( row['component'] == 'main' ):
                replies.append("%s %s" % \
                                (self.bold(row['package']), row['version']) )
            else:
                replies.append("%s %s (%s)" % z
                                (self.bold(row['package']), row['version'],
                                  row['component']) )

        irc.reply( "%s in %s/%s: %s" % (package, release, arch, "; ".join(replies)) )

    names = wrap(names, ['something', getopts( { 'arch':'something', 'release':'something' } ), optional( 'something' ) ] )

    def info(self, irc, msg, args, package, optlist, something ):
        """<packagename> [--arch <i386>] [--release <lenny>]

        Show the short description and some other brief details about a package
        in the specified release and architecture. By default, the current
        stable release and i386 are used.
        """
        release,arch = parse_standard_options( optlist, something )

        c = self.psql.cursor(cursor_factory=psycopg2.extras.DictCursor)
        c.execute(r"""SELECT p.section, p.priority, p.version,
                      p.size, p.installed_size, p.description,
                      p.homepage, s.screenshot_url
                    FROM packages as p
                      LEFT JOIN screenshots as s ON p.package=s.package
                    WHERE p.package=%(package)s AND
                      (p.architecture=%(arch)s OR p.architecture='all') AND
                      p.release=%(release)s""",
                   dict( package=package,
                         arch=arch,
                         release=release) );

        row = c.fetchone()

        if row:
            ds = row['description'].splitlines()
            if ds:
                d = ds[0]
            else:
                d=""
            reply = "%s (%s, %s): %s. Version: %s; Size: %0.1fk; Installed: %dk" % \
                      ( package, row['section'], row['priority'], d,
                        row['version'], row['size']/1024.0, row['installed_size'] )
            if row[6]:    # homepage field
                reply += "; Homepage: %s" % row['homepage']
            if row[7]:    # screenshot url from screenshots.debian.net
                reply += "; Screenshot: %s" % row['screenshot_url']

            irc.reply(reply)
        else:
            irc.reply( "No record of package '%s' in %s/%s." % \
                                    (package, release, arch) )

    info = wrap(info, ['something', getopts( { 'arch':'something',
                                              'release':'something' } ), optional( 'something' ) ] )

    def archHelper(self, irc, msg, args, package, optlist, something ):
        """<packagename> [--release <lenny>]

        Show for what architectures a package is available. By default, the current
        stable release is used.
        """
        release,arch = parse_standard_options( optlist, something )

        c = self.psql.cursor()
        c.execute(r"""SELECT architecture, version
                      FROM packages
                      WHERE package=%(package)s
                        AND release=%(release)s""",
                   dict( package=package,
                         release=release) );
        pkgs=[]
        for row in c.fetchall():
            pkgs.append( [row[0], row[1]] )

        if not pkgs:
            irc.reply( "Sorry, no package named '%s' was found." % package )
            return

        replies=[]
        for row in pkgs:
            replies.append("%s (%s)" % (row[0], row[1]) )

        irc.reply( "%s in %s: %s" % (package, release, "; ".join(replies)) )

    arches = wrap(archHelper, ['something', getopts({ 'release':'something' } ), optional( 'something' ) ] )
    archs  = wrap(archHelper, ['something', getopts({ 'release':'something' } ), optional( 'something' ) ] )

    def rprovidesHelper( self, irc, msg, args, package, optlist, something ):
        """<packagename> [--arch <i386>] [--release <lenny>]

        Show the packages that 'Provide' the specified virtual package
        ('reverse provides').
        By default, the current stable release and i386 are used.
        """
        release,arch = parse_standard_options( optlist, something )

        # remove all characters from the package name that aren't legal in a
        # package name i.e. not in:
        #    a-z0-9-.+
        # see s5.6.1 of Debian Policy "Source" for details.
        # http://www.debian.org/doc/debian-policy/ch-controlfields.html#s-f-Source
        #
        # \m is start word boundary, \M is finish word boundary
        # (but - in package name is a word boundary)
        # \A is start string,        \Z is finish string
        # http://www.postgresql.org/docs/8.3/static/functions-matching.html
        packagere = r"(?:\A|[, ])%s(?:\Z|[, ])" % re.sub(r"[^a-z\d\-+.]", "", package)
        #print packagere
        c = self.psql.cursor()
        c.execute(r"""SELECT package
                      FROM packages
                      WHERE provides ~ %(package)s
                        AND (architecture='all' OR architecture=%(arch)s)
                        AND release=%(release)s""",
                   dict( package=packagere,
                         arch=arch,
                         release=release) );

        pkgs=[]
        for row in c.fetchall():
            pkgs.append( row[0] )

        c.execute(r"""SELECT package
                      FROM packages
                      WHERE package=%(package)s
                        AND (architecture='all' OR architecture=%(arch)s)
                        AND release=%(release)s""",
                   dict( package=package,
                         arch=arch,
                         release=release) );
        realpackage = c.fetchone()

        if pkgs:
            reply = "%s in %s/%s is provided by: %s." % \
                    ( package, release, arch, ", ".join(pkgs) )
            if realpackage:
                reply += " %s is also a real package." % package
        else:
            if realpackage:
                reply = "In %s/%s, %s is a real package." % (release, arch, package)
            else:
                reply = "Sorry, no packages provide '%s' in %s/%s." %\
                                                (package, release, arch)

        irc.reply(reply)

    rprovides = wrap(rprovidesHelper, ['something', getopts( { 'arch':'something',
                                                    'release':'something' } ),
                             optional( 'something' ) ] );
    whatprovides = wrap(rprovidesHelper, ['something', getopts( { 'arch':'something',
                                                    'release':'something' } ),
                             optional( 'something' ) ] );

    def provides(self, irc, msg, args, package, optlist, something ):
        """<packagename> [--arch <i386>] [--release <lenny>]

        Show the list of "provided" packages for the specified binary package
        in the given release and architecture. By default, the current
        stable release and i386 are used.
        """
        release,arch = parse_standard_options( optlist, something )

        c = self.psql.cursor()
        c.execute(r"""SELECT provides
                      FROM packages
                      WHERE package=%(package)s
                        AND (architecture=%(arch)s OR architecture='all')
                        AND release=%(release)s""",
                   dict( package=package,
                         arch=arch,
                         release=release) );

        row = c.fetchone()
        if row:
            if row[0]:
                irc.reply("%s in %s/%s provides: %s." % \
                            (package, release, arch, row[0]) )
            else:
                irc.reply("%s in %s/%s provides no additional packages." % \
                            (package, release, arch) )
        else:
            irc.reply("Cannot find the package %s in %s/%s." % \
                            (package, release, arch) )

    provides = wrap(provides, ['something', getopts( { 'arch':'something',
                                              'release':'something' } ), optional( 'something' ) ] )

    def danke( self, irc, msg, args ):
        """
        Someone is trying to speak esperanto to me
        """
        irc.reply( "ne dankinde" )

    danke = wrap( danke, [] )

    def source( self, irc, msg, args, package, optlist, something ):
        """<packagename> [--release <lenny>]

        Show the name of the source package from which a given binary package
        is derived.
        By default, the current stable release and i386 are used.
        """
        release,arch = parse_standard_options( optlist, something )

        p = self.bin2src(package, release)
        if p:
            irc.reply( "%s -- Source: %s" % ( package, p ) )
        else:
            irc.reply( "Sorry, there is no record of a source package for the binary package '%s' in %s/%s." % \
                  ( package, release, arch ) )

    src = wrap(source, ['something', getopts( { 'release':'something' } ),
                           optional( 'something' ) ] );

    def bin2src(self, package, release):
        """Returns the source package for a given binary package"""
        c = self.psql.cursor()
        c.execute(r"""SELECT source
                      FROM packages
                      WHERE package=%(package)s
                        AND release=%(release)s LIMIT 1""",
                   dict( package=package,
                         release=release) );
        row = c.fetchone()
        if row:
            return row[0]
        else:
            return

    def binaries( self, irc, msg, args, package, optlist, something ):
        """<packagename> [--release <lenny>]

        Show the name of the binary package(s) that are derived from a given
        source package.
        By default, the current stable release and i386 are used.
        """
        release,arch = parse_standard_options( optlist, something )

        c = self.psql.cursor()
        c.execute(r"""SELECT DISTINCT package
                      FROM packages
                      WHERE source=%(package)s AND release=%(release)s""",
                   dict( package=package,
                         arch=arch,
                         release=release) );

        row = c.fetchone()
        if row:
            reply = "%s -- Binaries:" % package
            while row:
                reply += " %s" % ( row[0] )
                row = c.fetchone()

            irc.reply( reply )
        else:
            irc.reply("Cannot find the package %s in %s/%s." % \
                            (package, release, arch) )

    binaries = wrap(binaries, ['something', getopts( { 'release':'something' } ),
                           optional( 'something' ) ] );

    def builddep( self, irc, msg, args, package, optlist, something ):
        """<packagename> [--release <lenny>]

        Show the name of the binary packages on which a given source package
        or binary package build-depends.
        By default, the current stable release is used.
        """
        release,arch = parse_standard_options( optlist, something )

        c = self.psql.cursor()
        c.execute(r"""SELECT build_depends, build_depends_indep
                      FROM sources
                      WHERE source=%(package)s AND release=%(release)s LIMIT 1""",
                   dict( package=package,
                         release=release) );

        def bdformat(package, bd, bdi):
            reply = []
            if bd:
                reply.append("Build-Depends: %s" % bd)
            if bdi:
                reply.append("Build-Depends-Indep: %s" % bdi)
            return "%s -- %s." % ( package, "; ".join(reply))

        row = c.fetchone()
        if row:
            irc.reply(bdformat(package, row[0], row[1]))
        else:
            c.execute(r"""SELECT sources.source, build_depends, build_depends_indep
                          FROM sources
                            INNER JOIN packages
                            ON packages.source = sources.source
                          WHERE packages.package=%(package)s
                            AND packages.release=%(release)s LIMIT 1""",
                       dict( package=package,
                             release=release) );
            row = c.fetchone()
            if row:
                irc.reply(bdformat(row[0], row[1], row[2]))
            else:
                irc.reply( "Sorry, there is no record of the %s package in %s." %(package, release) )

    builddep = wrap(builddep, ['something', getopts( { 'release':'something' } ), optional( 'something' )] );

    def relationshipHelper( self, irc, msg, args, package, optlist, something, relation ):
        """Does the dirty work for each of the functions that show
        "conflicts", "depends", "recommends", "suggests", "enhances".

        The standard usage for each of these functions is accepted:
            relationship <packagename> [--arch <i386>] [--release <lenny>]

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

        release,arch = parse_standard_options( optlist, something )

        relations = PackageRelations(self.psql, arch=arch, release=release, package=package)

        if relations.Found():
            irc.reply( "%s -- %s: %s." % ( package, relation, relations.RelationEntry(relation)) )
        else:
            irc.reply( "Sorry, no package named '%s' was found in %s/%s." % \
                                (package, release, arch) )

    def conflicts( self, irc, msg, args, package, optlist, something ):
        """<packagename> [--arch <i386>] [--release <lenny>]

        Show the binary packages listed as conflicting with a given binary
        package.
        By default, the current stable release and i386 are used.
        """
        self.relationshipHelper(irc, msg, args, package, optlist, something, 'conflicts')

    conflicts = wrap(conflicts, ['something', getopts( { 'arch':'something',
                                                         'release':'something' } ),
                                 optional( 'something' )] );

    def depends( self, irc, msg, args, package, optlist, something ):
        """<packagename> [--arch <i386>] [--release <lenny>]

        Show the packages that are listed as 'Depends' for a given package.
        By default, the current stable release and i386 are used.
        """
        self.relationshipHelper(irc, msg, args, package, optlist, something, 'depends')

    depends = wrap(depends, ['something', getopts( { 'arch':'something',
                                                         'release':'something' } ),
                                 optional( 'something' )] );

    def recommends( self, irc, msg, args, package, optlist, something ):
        """<packagename> [--arch <i386>] [--release <lenny>]

        Show the packages that are listed as 'Recommends' for a given package.
        By default, the current stable release and i386 are used.
        """
        self.relationshipHelper(irc, msg, args, package, optlist, something, 'recommends')

    recommends = wrap(recommends, ['something', getopts( { 'arch':'something',
                                                         'release':'something' } ),
                                   optional( 'something' )] );

    def suggests( self, irc, msg, args, package, optlist, something ):
        """<packagename> [--arch <i386>] [--release <lenny>]

        Show the packages that are listed as 'Suggests' for a given package.
        By default, the current stable release and i386 are used.
        """
        self.relationshipHelper(irc, msg, args, package, optlist, something, 'suggests')

    suggests = wrap(suggests, ['something', getopts( { 'arch':'something',
                                                         'release':'something' } ),
                               optional( 'something' ) ] );

    def enhances( self, irc, msg, args, package, optlist, something ):
        """<packagename> [--arch <i386>] [--release <lenny>]

        Show the packages that are listed as 'Enhances' for a given package.
        By default, the current stable release and i386 are used.
        """
        self.relationshipHelper(irc, msg, args, package, optlist, something, 'enhances')

    enhances = wrap(enhances, ['something', getopts( { 'arch':'something',
                                                         'release':'something' } ),
                               optional( 'something' ) ] );

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
                d=""
            irc.reply( "Bug #%d (%s) %s -- %s; Severity: %s; Last Modified: %s" % ( bugno, row[1], row[0], d, row[2], row[4]) )

    bug = wrap(bug, ['int'] )

    def popcon( self, irc, msg, args, package ):
        """<packagename>

        Show the popcon (popularity contents) data for a given binary package.
        http://popcon.debian.org/FAQ
        """
        c = self.psql.cursor()

        c.execute( "SELECT insts,vote,olde,recent,nofiles FROM popcon where package=%(package)s", dict( package=package ) )

        row = c.fetchone()
        if row:
            irc.reply( "Popcon data for %s: inst: %d, vote: %d, old: %d, recent: %d, nofiles: %d" % (package, row[0],row[1],row[2],row[3],row[4]) )
        else:
            irc.reply( "no popcon data for %s" % (package) )

    popcon = wrap(popcon, ['something'] )

    def uploaderHelper( self, irc, msg, args, package, version ):
        """<packagename> [<version>]

        Return the names of the person who uploaded the package, the person who
        changed the package prior to upload and the maintainer of the specified
        source package. If version is omitted, the most recent upload is used.
        """
        c = self.psql.cursor()

        if version:
            c.execute(r"""SELECT signed_by_name, changed_by_name,
                            maintainer_name, nmu, version
                          FROM upload_history
                          WHERE source=%(package)s AND version=%(version)s""",
                      dict(package=package, version=version) )
        else:
            c.execute(r"""SELECT signed_by_name, changed_by_name,
                            maintainer_name, nmu, version
                          FROM upload_history
                          WHERE source=%(package)s
                          ORDER BY date DESC LIMIT 1""",
                      dict(package=package) )

        row = c.fetchone()
        if row:
            reply = "Package %s version %s was uploaded by %s, last changed by %s and maintained by %s." % (package, row[4], row[0], row[1], row[2])
            if row[3]:
                reply += " (non-maintainer upload)"

            irc.reply( reply )
        else:
            source = self.bin2src(package, 'sid')
            if source:
                return self.uploaderHelper(irc, msg, args, source, version)
            elif version:
                irc.reply( "Sorry, there is no record of '%s', version '%s'." % (package,version) )
            else:
                irc.reply( "Sorry, there is no record of '%s'." % package )

    uploader   = wrap(uploaderHelper, ['something', optional( 'something' )] )
    changer    = wrap(uploaderHelper, ['something', optional( 'something' )] )
    maint      = wrap(uploaderHelper, ['something', optional( 'something' )] )
    maintainer = wrap(uploaderHelper, ['something', optional( 'something' )] )

    def recentHelper( self, irc, msg, args, package, version ):
        """<packagename>

        Return the dates and versions of recent uploads of the specified source
        or binary package.
        """
        c = self.psql.cursor()

        c.execute(r"""SELECT version, date
                      FROM upload_history
                      WHERE source=%(package)s
                      ORDER BY date DESC LIMIT 10""",
                  dict(package=package) )

        uploads = map(lambda u: "%s %s" % (self.bold(u[0]), u[1].date()), c.fetchall())
        if uploads:
            reply = "Package %s recent uploads: %s." % \
                        (package, ", ".join(uploads))
            irc.reply( reply )
        else:
            source = self.bin2src(package, 'sid')
            if source:
                return self.recentHelper(irc, msg, args, source, version)
            irc.reply( "Sorry, there is no record of source package '%s'." % package )

    recent   = wrap(recentHelper, ['something', optional( 'something' )] )

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

        reply = "RC bugs in %s:" % package;
        for row in c.fetchall():
            reply += " %d" % row[0]

        irc.reply( reply )

    rcbugs = wrap(rcbugs, ['something'] )

    def file(self, irc, msg, args, glob, optlist, something):
        """<pattern> [--arch <i386>] [--release <lenny>] [--regex | --exact]

        Returns packages that include files matching <pattern> which, by
        default, is interpreted as a glob (see glob(7)).
        If --regex is given, the pattern is treated as a regex (see regex(7)).
        If --exact is given, the exact filename is required.
        The current stable release and i386 are searched by default.
        """
        # Based on the file command in the Debian plugin by James Vega

        release,arch = parse_standard_options( optlist )

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
        elif mode == 'regex':
            if regexp.startswith(r'/'):
                regexp = '^' + regexp[1:]
            if regexp.endswith(r'$'):
                regexp = regexp[:-1] + r'[[:space:]]'
        else:
            regexp = regexp =  r'^%s[[:space:]]' % re.escape(regexp.lstrip(r'/'))

        self.log.debug("RE=%s" % regexp)

        packages = self.getContents(irc, release, arch, regexp)

        if len(packages) == 0:
            irc.reply('No packages were found with that file.')
        else:
            s = packages.toString(self.bold)
            irc.reply("%s in %s/%s: %s" % (glob, release, arch, s))

    file = wrap(file, [optional('something'),
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
            #print "Trying: zgrep -ie '%s' '%s'" % (regexp, contents)
            output = subprocess.Popen(['zgrep', '-ie', regexp, contents],
                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True).communicate()[0]
        except TypeError:
            irc.error(r"Sorry, couldn't look up the file list.", Raise=True)

        packages = PackageFileList()
        try:
            for line in output.split("\n"):
                if len(data) > 100:
                    irc.error('There were more than 100 files matching your search, '
                              'please narrow your search.', Raise=True)
                try:
                    (filename, pkg_list) = line.split()
                    if filename == 'FILE':
                        # This is the last line before the actual files.
                        continue
                except ValueError: # Unpack list of wrong size.
                    continue       # We've not gotten to the files yet.
                packages.add(filename, pkg_list.split(','))
        finally:
            pass
        return packages

    def bold(self, s):
        if self.registryValue('bold', dynamic.channel):
            return ircutils.bold(s)
        return s

Class = Judd

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
