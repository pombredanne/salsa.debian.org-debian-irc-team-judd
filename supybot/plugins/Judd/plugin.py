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

#TODO: add build-dep - (should work with binary package name too)

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from debian_bundle import debian_support

import psycopg2

release_map = { 'unstable':'sid', 'testing':'squeeze', 'stable':'lenny' }
releases = [ 'etch', 'etch-backports', 'etch-multimedia', 'etch-security', 'etch-volatile', 'experimental', 'lenny', 'lenny-multimedia', 'lenny-security', 'lenny-backports', 'lenny-volatile', 'squeeze', 'squeeze-security', 'squeeze-multimedia', 'sid', 'sid-multimedia', 'unstable', 'testing', 'stable' ]

arches = [ 'alpha', 'amd64', 'arm', 'armel', 'hppa', 'hurd-i386', 'i386', 'ia64', 'm68k', 'mips', 'mipsel', 'powerpc', 's390', 'sparc', 'all' ]

def parse_standard_options( optlist, args=None ):
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

class Judd(callbacks.Plugin):
    """A plugin for querying a debian udd instance:  http://wiki.debian.org/UltimateDebianDatabase."""

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

        Show the available versions of a package in the specified release and 
        for the given architecture.
        The current stable release and i386 are searched by default.
        The characters * and ? can be used as wildcards in the pattern.
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

        c = self.psql.cursor()
        if package.find( '*' ) == -1 and package.find( '?' ) == -1:
            sql = "SELECT DISTINCT release,version,component FROM packages WHERE package=%(package)s AND (architecture=%(arch)s OR architecture='all')"
            if release:
                sql += " AND release=%(release)s"

            c.execute( sql,
                       dict( package=package,
                             arch=arch,
                             release=release ) );

            pkgs=[]
            for row in c.fetchall():
                pkgs.append( [row[0], row[1], row[2]] )


            pkgs.sort( lambda a,b: debian_support.version_compare( a[1], b[1] ) )

            reply = "%s --" % package
            for row in pkgs:
		atleastone=True
                if( row[2] == 'main' ):
                    reply += " %s: %s" % (row[0], row[1])
                else:
                    reply += " %s/%s: %s" % (row[0], row[2], row[1])

        else:
            package = package.replace( "*", "%" )
            package = package.replace( "?", "_" )
            sql = "SELECT DISTINCT release,version,package,component FROM packages WHERE package LIKE %(package)s AND (architecture=%(arch)s OR architecture='all')"
            if release:
                sql += " AND release=%(release)s"

            c.execute( sql,
                       dict( package=package, 
                             arch=arch,
                             release=release ) );
            pkgs=[]
            for row in c.fetchall():
                atleastone=True
                pkgs.append( [row[0], row[1], row[2], row[3]] )

            
            if release:
                reply = "%s in %s:" % (package,release)
            else:
                reply = "%s" % package

            pkgs.sort( lambda a,b: debian_support.version_compare( a[1], b[1] ) )
            print pkgs
            for row in pkgs:
                if release:
                    if( row[3] == 'main' ):
                        reply += " %s %s" % (row[2], row[1] )
                    else:
                        reply += " %s: %s %s" % (row[0], row[2], row[1] )
                else:
                    if( row[3] == 'main' ):
                        reply += " %s: %s %s" % (row[0], row[2], row[1])
                    else:
                        reply += " %s %s (%s/%s)" % (row[2], row[1], row[0], row[3])

        if atleastone:
            irc.reply( reply )
        else:
            irc.reply( "Sorry, no package named '%s' found." % package )
        
    versions = wrap(versions, ['something', getopts( { 'arch':'something', 'release':'something' } ), optional( 'something' ) ] )
    
    def info(self, irc, msg, args, package, optlist, something ):
        """<packagename> [--arch <i386>] [--release <lenny>]

        Show the short description and some other brief details about a package
        in the specified release and architecture. By default, the current 
        stable release and i386 are used.
        """
        release,arch = parse_standard_options( optlist, something )

        c = self.psql.cursor()
        c.execute( "SELECT section, priority, version, size, installed_size, description FROM packages WHERE package=%(package)s AND (architecture=%(arch)s OR architecture='all') AND release=%(release)s", 
                   dict( package=package, 
                         arch=arch,
                         release=release) );

        row = c.fetchone()
        if row:
            ds = row[5].splitlines()
            if ds:
                d = ds[0]
            else:
                d=""
            irc.reply( "%s (%s): is %s; Version: %s; Size: %0.1fk; Installed: %dk -- %s" % (
                package, row[0], row[1], row[2], row[3]/1024.0, row[4], d ) )

        
    info = wrap(info, ['something', getopts( { 'arch':'something',
                                              'release':'something' } ), optional( 'something' ) ] )

    def depends( self, irc, msg, args, package, optlist, something ):
        """<packagename> [--arch <i386>] [--release <lenny>]

        Show the packages that are listed as 'Depends' for a given package.
        By default, the current stable release and i386 are used.
        """
        release,arch = parse_standard_options( optlist, something )

        print( "release: %s arch: %s" % (release, arch) )
        c = self.psql.cursor()
        c.execute( "SELECT depends FROM packages WHERE package=%(package)s AND (architecture='all' or architecture=%(arch)s) AND release=%(release)s", 
                   dict( package=package, 
                         arch=arch,
                         release=release) );

        row = c.fetchone()
        if row:
            irc.reply( "%s -- Depends: %s" % ( package, row[0]) )

        
    depends = wrap(depends, ['something', getopts( { 'arch':'something',
                                                     'release':'something' } ), 
                             optional( 'something' ) ] );

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

        c = self.psql.cursor()
        c.execute( "SELECT source FROM packages WHERE package=%(package)s AND release=%(release)s limit 1", 
                   dict( package=package, 
                         arch=arch,
                         release=release) );

        row = c.fetchone()
        if row:
            irc.reply( "%s -- Source: %s" % ( package, row[0]) )

        
    src = wrap(source, ['something', getopts( { 'release':'something' } ),
                           optional( 'something' ) ] );

    def binaries( self, irc, msg, args, package, optlist, something ):
        """<packagename> [--release <lenny>]

        Show the name of the binary package(s) that are derived from a given 
        source package.
        By default, the current stable release and i386 are used.
        """
        release,arch = parse_standard_options( optlist, something )

        c = self.psql.cursor()
        c.execute( "SELECT distinct package FROM packages WHERE source=%(package)s AND release=%(release)s", 
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
        
    binaries = wrap(binaries, ['something', getopts( { 'release':'something' } ),
                           optional( 'something' ) ] );

    def builddep( self, irc, msg, args, package, optlist, something ):
        """<packagename> [--release <lenny>]

        Show the name of the binary packages on which a given source package
        build-depends.
        By default, the current stable release is used.
        """
        release,arch = parse_standard_options( optlist, something )

        c = self.psql.cursor()
        c.execute( "SELECT build_depends,build_depends_indep FROM sources WHERE source=%(package)s AND release=%(release)s limit 1", 
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
            c.execute( """SELECT sources.source,build_depends,build_depends_indep FROM sources 
                        INNER JOIN packages on packages.source = sources.source
                        WHERE packages.package=%(package)s AND packages.release=%(release)s limit 1""", 
                       dict( package=package, 
                             release=release) );
            row = c.fetchone()
            if row:
                irc.reply(bdformat(row[0], row[1], row[2]))
            else:
                irc.reply( "Sorry, there is no record of the %s package in %s." %(package, release) )
        
        
    builddep = wrap(builddep, ['something', getopts( { 'release':'something' } ), optional( 'something' )] );
        
    def conflicts( self, irc, msg, args, package, optlist, something ):
        """<packagename> [--arch <i386>] [--release <lenny>]

        Show the binary packages listed as conflicting with a given binary
        package.
        By default, the current stable release and i386 are used.
        """
        release,arch = parse_standard_options( optlist, something )

        c = self.psql.cursor()
        c.execute( "SELECT conflicts FROM packages WHERE package=%(package)s AND (architecture='all' or architecture=%(arch)s) AND release=%(release)s limit 1", 
                   dict( package=package, 
                         arch=arch,
                         release=release) );

        row = c.fetchone()
        if row:
            irc.reply( "%s -- Conflicts: %s" % ( package, row[0]) )

        
    conflicts = wrap(conflicts, ['something', getopts( { 'arch':'something',
                                                         'release':'something' } ),
                                 optional( 'something' )] );

    def recommends( self, irc, msg, args, package, optlist, something ):
        """<packagename> [--arch <i386>] [--release <lenny>]

        Show the packages that are listed as 'Recommends' for a given package.
        By default, the current stable release and i386 are used.
        """
        release,arch = parse_standard_options( optlist, something )

        c = self.psql.cursor()
        c.execute( "SELECT recommends FROM packages WHERE package=%(package)s AND (architecture='all' or architecture=%(arch)s) AND release=%(release)s limit 1", 
                   dict( package=package, 
                         arch=arch,
                         release=release) );

        row = c.fetchone()
        if row:
            irc.reply( "%s -- Recommends: %s" % ( package, row[0]) )

        
    recommends = wrap(recommends, ['something', getopts( { 'arch':'something',
                                                         'release':'something' } ),
                                   optional( 'something' )] );

    def suggests( self, irc, msg, args, package, optlist, something ):
        """<packagename> [--arch <i386>] [--release <lenny>]

        Show the packages that are listed as 'Suggests' for a given package.
        By default, the current stable release and i386 are used.
        """
        release,arch = parse_standard_options( optlist, something )

        c = self.psql.cursor()
        c.execute( "SELECT suggests FROM packages WHERE package=%(package)s AND (architecture='all' or architecture=%(arch)s) AND release=%(release)s limit 1", 
                   dict( package=package, 
                         arch=arch,
                         release=release) );

        row = c.fetchone()
        if row:
            irc.reply( "%s -- Suggests: %s" % ( package, row[0]) )

        
    suggests = wrap(suggests, ['something', getopts( { 'arch':'something',
                                                         'release':'something' } ),
                               optional( 'something' ) ] );
    def bug( self, irc, msg, args, bugno ):
        """ 
        Show information about a bug in a given pacage.  
        Usage: "conflicts packagename"
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
            c.execute( "SELECT signed_by_name, changed_by_name, maintainer_name, nmu, version FROM upload_history WHERE source=%(package)s and version=%(version)s", dict( package=package, version=version ) )
        else:
            c.execute( "SELECT signed_by_name, changed_by_name, maintainer_name, nmu, version FROM upload_history WHERE source=%(package)s  ORDER BY date DESC LIMIT 1", dict( package=package) )

        row = c.fetchone()
        if row:
            reply = "Package %s version %s was uploaded by %s, last changed by %s and maintained by %s." % (package, row[4], row[0], row[1], row[2])
            if row[3]:
                reply += " (non-maintainer upload)"

            irc.reply( reply )
        else:
            if version:
                irc.reply( "Sorry, there is no record of '%s', version '%s'." % (package,version) )
            else:
                irc.reply( "Sorry, there is no record of '%s'." % package )

    uploader   = wrap(uploaderHelper, ['something', optional( 'something' )] )
    changer    = wrap(uploaderHelper, ['something', optional( 'something' )] )
    maint      = wrap(uploaderHelper, ['something', optional( 'something' )] )
    maintainer = wrap(uploaderHelper, ['something', optional( 'something' )] )

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

Class = Judd


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
