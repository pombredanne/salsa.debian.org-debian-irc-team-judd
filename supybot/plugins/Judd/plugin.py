###
# Copyright (c) 2007,2008, Mike O'Connor
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

release_map = { 'unstable':'sid', 'testing':'lenny', 'stable':'etch' }

def parse_standard_options( optlist ):
    release='etch'
    arch='i386'
    for( option,arg ) in optlist:
        if option=='release':
            release=arg;
        elif option=='arch':
            arch=arg;

    if release_map.has_key( release ):
        release = release_map[ release ]

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



    def versions(self, irc, msg, args, package, optlist):
        """
        Output available versions of a package.
        Usage: "versions pattern [--arch i386] [--release etch]"
        pattern will treat * and ? as wildcards
        """
        release = None
        arch='i386'
        atleastone=False

        for( option,arg ) in optlist:
            if option=='release':
                release=arg;
            elif option=='arch':
                arch=arg;

        c = self.psql.cursor()
        if package.find( '*' ) == -1 and package.find( '?' ) == -1:
            sql = "SELECT distinct release,version,component FROM packages WHERE package=%(package)s AND (architecture=%(arch)s or architecture='all')"
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
		atleaseone=True
                if( row[2] == 'main' ):
                    reply += " %s: %s" % (row[0], row[1])
                else:
                    reply += " %s/%s: %s" % (row[0], row[2], row[1])

        else:
            package = package.replace( "*", "%" )
            package = package.replace( "?", "_" )
            sql = "SELECT distinct release,version,package,component FROM packages WHERE package like %(package)s AND (architecture=%(arch)s or architecture='all')"
            if release:
                sql += " AND release=%(release)s"

            c.execute( sql,
                       dict( package=package, 
                             arch=arch,
                             release=release ) );
    
            pkgs=[]
            for row in c.fetchall():
                atleaseone=True
                pkgs.append( [row[0], row[1], row[2]] )

            if release:
                reply = "%s in %s:" % (package,release)
            else:
                reply = "%s" % package

            pkgs.sort( lambda a,b: debian_support.version_compare( a[1], b[1] ) )
            for row in pkgs:
                if release:
                    if( row[2] == 'main' ):
                        reply += " %s %s" % (row[2], row[1] )
                    else:
                        reply += " %s: %s %s" % (row[0], row[2], row[1] )
                else:
                    if( row[2] == 'main' ):
                        reply += " %s: %s %s" % (row[0], row[2], row[1])
#                    else:
#                        reply += " %s %s (%s/%s)" % (row[2], row[1], row[0], row[3])

#fixme should be checking atleastone
        if True:
            irc.reply( reply )
        else:
            irc.reply( "No package named %s found" % package )
        
    versions = wrap(versions, ['something', getopts( { 'arch':'something', 'release':'something' } ) ] )
    
    def info(self, irc, msg, args, package, optlist ):
        """
        Output brief info about a package.
        Usage: "info packagename [--arch i386] [--release etch]"
        """
        release,arch = parse_standard_options( optlist )

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
                                              'release':'something' } ) ] )

    def depends( self, irc, msg, args, package, optlist ):
        """
        Show Depends: of a given package.
        Usage: "depends packagename [--arch i386] [--release etch]"
        """
        release,arch = parse_standard_options( optlist )

        c = self.psql.cursor()
        c.execute( "SELECT depends FROM packages WHERE package=%(package)s AND (architecture='all' or architecture=%(arch)s) AND release=%(release)s", 
                   dict( package=package, 
                         arch=arch,
                         release=release) );

        row = c.fetchone()
        if row:
            irc.reply( "%s -- Depends: %s" % ( package, row[0]) )

        
    depends = wrap(depends, ['something', getopts( { 'arch':'something',
                                                         'release':'something' } ) ] );
    def source( self, irc, msg, args, package, optlist ):
        """
        Show Source: of a given package.
        Usage: "source packagename [--release etch]"
        """
        release,arch = parse_standard_options( optlist )

        c = self.psql.cursor()
        c.execute( "SELECT source FROM packages WHERE package=%(package)s AND release=%(release)s limit 1", 
                   dict( package=package, 
                         arch=arch,
                         release=release) );

        row = c.fetchone()
        if row:
            irc.reply( "%s -- Source: %s" % ( package, row[0]) )

        
    source = wrap(source, ['something', getopts( { 'release':'something' } ) ] );

    def find( self, irc, msg, args, filename, optlist ):
        """
        Show package containing a given file.
        Usage: "find filename [--release etch] [--arch i386]"
        """
        release,arch = parse_standard_options( optlist )

        c = self.psql.cursor()
        c.execute( "SELECT package FROM package_contents WHERE Filename=%(filename)s AND release=%(release)s and arch=%(arch)s", 
                   dict( filename=filename, 
                         arch=arch,
                         release=release) );

        row = c.fetchone()
        if row:
            irc.reply( "%s -- Source: %s" % ( package, row[0]) )

        
    source = wrap(source, ['something', getopts( { 'release':'something' } ) ] );
        
    def obsolete_testing( self, irc, msg, args ):
        """
        Find packages which are in testing-security but don't exist in testing or unstable
        """
        pass

    def builddep( self, irc, msg, args, package, optlist ):
        """
        Show BuildDepends: of a given package.
        Usage: "buliddep packagename [--arch i386] [--release etch]"
        """
        release,arch = parse_standard_options( optlist )

        c = self.psql.cursor()
        c.execute( "SELECT build_depends FROM sources WHERE source=%(package)s AND release=%(release)s limit 1", 
                   dict( package=package, 
                         arch=arch,
                         release=release) );

        row = c.fetchone()
        if row:
            irc.reply( "%s -- BuildDepends: %s" % ( package, row[0]) )
        else:
            c.execute( """SELECT sources.source,build_depends FROM sources 
                        INNER JOIN packages on packages.source = sources.source
                        WHERE packages.package=%(package)s AND packages.release=%(release)s limit 1""", 
                       dict( package=package, 
                             arch=arch,
                             release=release) );
            row = c.fetchone()
            if row:
                irc.reply( "%s -- BuildDepends: %s" % ( row[0], row[1]) )

        
        
    builddep = wrap(builddep, ['something', getopts( { 'release':'something' } ) ] );
        
    def conflicts( self, irc, msg, args, package, optlist ):
        """
        Show Conflicts: of a given package.
        Usage: "conflicts packagename [--arch i386] [--release etch]"
        """
        release,arch = parse_standard_options( optlist )

        c = self.psql.cursor()
        c.execute( "SELECT conflicts FROM packages WHERE package=%(package)s AND (architecture='all' or architecture=%(arch)s) AND release=%(release)s limit 1", 
                   dict( package=package, 
                         arch=arch,
                         release=release) );

        row = c.fetchone()
        if row:
            irc.reply( "%s -- Conflicts: %s" % ( package, row[0]) )

        
    conflicts = wrap(conflicts, ['something', getopts( { 'arch':'something',
                                                         'release':'something' } ) ] );
    def recommends( self, irc, msg, args, package, optlist ):
        """
        Show Recommends: of a given package.
        Usage: "recommends packagename [--arch i386] [--release etch]"
        """
        release,arch = parse_standard_options( optlist )

        c = self.psql.cursor()
        c.execute( "SELECT recommends FROM packages WHERE package=%(package)s AND (architecture='all' or architecture=%(arch)s) AND release=%(release)s limit 1", 
                   dict( package=package, 
                         arch=arch,
                         release=release) );

        row = c.fetchone()
        if row:
            irc.reply( "%s -- Recommends: %s" % ( package, row[0]) )

        
    recommends = wrap(recommends, ['something', getopts( { 'arch':'something',
                                                         'release':'something' } ) ] );

    def suggests( self, irc, msg, args, package, optlist ):
        """
        Show Suggests: of a given package.
        Usage: "suggests packagename [--arch i386] [--release etch]"
        """
        release,arch = parse_standard_options( optlist )

        c = self.psql.cursor()
        c.execute( "SELECT suggests FROM packages WHERE package=%(package)s AND (architecture='all' or architecture=%(arch)s) AND release=%(release)s limit 1", 
                   dict( package=package, 
                         arch=arch,
                         release=release) );

        row = c.fetchone()
        if row:
            irc.reply( "%s -- Suggests: %s" % ( package, row[0]) )

        
    suggests = wrap(suggests, ['something', getopts( { 'arch':'something',
                                                         'release':'something' } ) ] );
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
        """
        Return the popcon data  of the given package. 
        Usage: "popcon packagename"
        """
        c = self.psql.cursor()

        c.execute( "SELECT insts,vote,olde,recent,nofiles FROM popcon where package=%(package)s", dict( package=package ) )

        row = c.fetchone()
        if row:
            irc.reply( "Popcon data for %s: inst: %d, vote: %d, old: %d, recent: %d, nofiles: %d" % (package, row[0],row[1],row[2],row[3],row[4]) )
        else:
            irc.reply( "no popcon data for %s" % (package) )

    popcon = wrap(popcon, ['something'] )
        
    def uploader( self, irc, msg, args, package, version ):
        """
        Return the gpg keyid of the uploader of the given package version. 
        Usage: "uploader package [version]"
        If version is omitted, the most recent upload is used.
        """
        c = self.psql.cursor()

        c.execute( "SELECT key_id FROM upload_history where package=%(package)s and version=%(version)s", dict( package=package, version=version ) )

        row = c.fetchone()
        if row:
            irc.reply( "Uploader of %s %s: %s" % (package, version, row[0]) )
        else:
            irc.reply( "no record of %s %s" % (package,version) )

    uploader = wrap(uploader, ['something', optional( 'something' )] )
        
    def changer( self, irc, msg, args, package, version ):
        """
        Return the person listed as the changer in the uploaded .changes file.
        Usage: "changer package [version]" -- 
        If version is omitted, the most recently changed version is used.
        """
        c = self.psql.cursor()

        if( version ):
            c.execute( "SELECT changed_by, version FROM upload_history where package=%(package)s and version=%(version)s", dict( package=package, version=version ) )
        else:
            c.execute( "SELECT changed_by, version FROM upload_history where package=%(package)s order by date desc", dict( package=package, version=version ) )

        row = c.fetchone()
        if row:
            irc.reply( "%s %s was changed by: %s" % (package, row[1], row[0]) )
        else:
            if( version ):
                irc.reply( "no record of %s %s" % (package,version) )
            else:
                irc.reply( "no record of %s" % (package) )

    changer = wrap(changer, ['something', optional( 'something' )] )
        

# TODO: this should use package.gz data (instead of?  as well as?)
    def maintainer( self,irc,msg,args,package,version ):
        """
        Return the listed maintainer of a package.
        Usage: "{maintainer,maint} package [version]"
        If version is omitted, the most recent upload is used.
        """
        c = self.psql.cursor()

        if version:
            c.execute( "SELECT maintainer FROM upload_history where package=%(package)s and version=%(version)s", dict( package=package, version=version ) )
            row = c.fetchone()
            if row:
                irc.reply( "%s is listed as maintainer of %s %s" % (row[0], package, version ) )
            else:
                irc.reply( "no record of %s %s" % (package,version) )
        else:
            c.execute( "SELECT maintainer,version FROM upload_history where package=%(package)s order by date desc limit 1", dict( package=package, version=version ) )
            row = c.fetchone()
            if row:
                irc.reply( "%s is listed as maintainer of %s %s" % (row[0], package, row[1] ) )
            else:
                irc.reply( "no record of %s" % (package) )


    maint = wrap(maintainer, ['something', optional( 'something' )] )
    maintainer = wrap(maintainer, ['something', optional( 'something' )] )
        
        
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
