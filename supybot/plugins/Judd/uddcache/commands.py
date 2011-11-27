#
# Ultimate Debian Database query tool
#
# Set piece queries for the database
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

from udd import Udd
from packages import *
from relations import *
from resolver import *
try:
    from debian import debian_support
except:
    from debian_bundle import debian_support


class Commands(object):

    def __init__(self, udd):
        self.udd = udd

    def versions(self, package, release, arch):
        c = self.udd.psql.cursor(cursor_factory=psycopg2.extras.DictCursor)
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

        sql += ' ORDER BY version'
        c.execute(sql,
                  dict(package=packagename,
                       arch=arch,
                       release=release))

        pkgs = c.fetchall()
        if not pkgs:
            raise PackageNotFoundError(package)

        return pkgs

    def info(self, package, release, arch):
        c = self.udd.psql.cursor(cursor_factory=psycopg2.extras.DictCursor)
        c.execute(r"""SELECT p.section, p.priority, p.version,
                      p.size, p.installed_size, p.description,
                      p.homepage, s.screenshot_url
                    FROM packages as p
                      LEFT JOIN screenshots as s ON p.package=s.package
                    WHERE p.package=%(package)s AND
                      (p.architecture=%(arch)s OR p.architecture='all') AND
                      p.release=%(release)s""",
                   dict(package=package,
                         arch=arch,
                         release=release))

        pkg = c.fetchone()
        if not pkg:
            raise PackageNotFoundError(package)
        return pkg

    def names(self, package, release, arch):
        """
        Search package names with * and ? as wildcards.
        """
        c = self.udd.psql.cursor(cursor_factory=psycopg2.extras.DictCursor)

        packagesql = package.replace("*", "%")
        packagesql = packagesql.replace("?", "_")

        if package.startswith('src:'):
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

        c.execute(sql,
                  dict(package=packagesql,
                       arch=arch,
                       release=release))
        return c.fetchall()

    def archs(self, package, release):
        """
        Find in which architectures a package is available.
        """
        c = self.udd.psql.cursor(cursor_factory=psycopg2.extras.DictCursor)
        c.execute(r"""SELECT architecture, version
                      FROM packages
                      WHERE package=%(package)s
                        AND release=%(release)s""",
                   dict(package=package,
                        release=release))
        archs = c.fetchall()
        if not archs:
            raise PackageNotFoundError(package)
        return archs

    def uploads(self, package, version="", max=0):
        """
        Return the dates and versions of recent uploads of the specified source
        package.
        """
        c = self.udd.psql.cursor(cursor_factory=psycopg2.extras.DictCursor)
        if type(package) == str:
            p = package
        else:
            p = package.package

        sql = r"""SELECT *
                      FROM upload_history
                      WHERE source=%(package)s"""
        if version:
            sql += """ AND version=%(version)s"""
        if max:
            sql += """ ORDER BY date DESC LIMIT %(max)s"""

        c.execute(sql,
                  dict(package=p,
                       version=version,
                       max=max))
        ups = c.fetchall()
        if not ups:
            raise PackageNotFoundError(package)
        return ups

    def popcon(self, package):
        """
        Return the popcon (popularity contest) data for the specified
        binary package.
        See also: http://popcon.debian.org/FAQ
        """
        c = self.udd.psql.cursor(cursor_factory=psycopg2.extras.DictCursor)
        c.execute(r"""SELECT insts, vote, olde, recent, nofiles
                      FROM popcon
                      WHERE package=%(package)s""",
                  dict(package=package))
        data = c.fetchone()
        if not data:
            raise PackageNotFoundError(package)
        return data

    def checkdeps(self, package, release, arch, relations):
        """
        Check that the dependencies listed by a package are satisfiable for the
        specified release and architecture.
        """
        releases = self.udd.data.list_dependent_releases(release)
        r = self.udd.BindRelease(arch=arch, release=releases)
        relchecker = Checker(r)

        statusdict = {}
        for rel in relations:
            # raises PackageNotFoundError if package not found
            status = relchecker.Check(package, rel)
            statusdict[rel] = status
        return statusdict

    def checkInstall(self, package, release, arch, withrecommends):
        releases = self.udd.data.list_dependent_releases(release)
        r = Release(self.udd.psql, arch=arch, release=releases)
        relchecker = InstallChecker(r)
        # raises PackageNotFoundError if package not found
        solverh = relchecker.Check(package, withrecommends)
        return solverh

    def checkBackport(self, package, fromrelease, torelease):
        """
        Check that the build-dependencies listed by a package in the release
        specified as "fromrelease" are satisfiable for in "torelease" for the
        given host architecture.
        """
        relchecker = BuildDepsChecker(torelease)

        s = fromrelease.Source(package)
        # raises PackageNotFoundError if package not found
        return relchecker.Check(s)

    def why(self, package1, package2, release, arch, withrecommends):
        """
        Find all the dependency chains between two packages

        Generates a list of dependency chains that go from package1 to
        package2 in the specified release and architecture. Recommends
        are optionally included in the dependency analysis too. Note that
        this function will look for *all* dependency chains not just the
        shortest/strongest one that is available.

        BUGS: Provides and optional dependencies ("a | b") are not handled
        except for accepting the first available package to satisfy them.

        BUGS: check that package2 exists before doing expensive work?
        """
        releases = self.udd.data.list_dependent_releases(release)
        r = Release(self.udd.psql, arch=arch, release=releases)
        relchecker = InstallChecker(r)
        # raises PackageNotFoundError if package not found
        solverh = relchecker.Check(package1, withrecommends)

        chains = solverh.chains()
        chains = chains.truncated(package2).unique().sorted()
        return chains

    def bug(self, bugnumber, verbose):
        """
        Retrieve information about a particular bug
        """
        tracker = self.udd.Bts()
        b = tracker.bug(bugnumber)
        if verbose:
            tracker.get_bugs_tags([b])
        return b

    def rm(self, package):
        """
        Retrieve information about a package removal bug
        """
        tracker = self.udd.Bts()
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
                    'sort': 'id DESC'
                }
        if bugtype:
            filter['title'] = '%s: %s ' % (bugtype, package)
        else:
            filter['title'] = r'\y%s\y' % (package)
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
