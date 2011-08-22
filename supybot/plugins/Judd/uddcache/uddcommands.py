#
# Ultimate Debian Database query tool
#
# Set piece queries for the database
#
###
#
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
#
###

from udd import Udd
from uddpackages import *
from uddrelations import *
from uddresolver import *
from debian import debian_support


class UddCommands(Udd):

    def versions(self, package, release, arch):
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

        c.execute(sql,
                  dict(package=packagename,
                       arch=arch,
                       release=release))

        pkgs = []
        for row in c.fetchall():
            pkgs.append(row)

        pkgs.sort(lambda a, b:
                    debian_support.version_compare(a['version'], b['version']))
        return pkgs

    def info(self, package, release, arch):
        c = self.psql.cursor(cursor_factory=psycopg2.extras.DictCursor)
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

        return c.fetchone()

    def names(self, package, release, arch):
        """
        Search package names with * and ? as wildcards.
        """
        c = self.psql.cursor(cursor_factory=psycopg2.extras.DictCursor)

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
        c = self.psql.cursor(cursor_factory=psycopg2.extras.DictCursor)
        c.execute(r"""SELECT architecture, version
                      FROM packages
                      WHERE package=%(package)s
                        AND release=%(release)s""",
                   dict(package=package,
                        release=release))
        return c.fetchall()

    def uploads(self, package, version="", max=0):
        """
        Return the dates and versions of recent uploads of the specified source
        package.
        """
        c = self.psql.cursor(cursor_factory=psycopg2.extras.DictCursor)
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
        return c.fetchall()

    def popcon(self, package):
        """
        Return the popcon (popularity contest) data for the specified
        binary package.
        See also: http://popcon.debian.org/FAQ
        """
        c = self.psql.cursor(cursor_factory=psycopg2.extras.DictCursor)
        c.execute(r"""SELECT insts, vote, olde, recent, nofiles
                      FROM popcon
                      WHERE package=%(package)s""",
                  dict(package=package))
        return c.fetchone()

    def checkdeps(self, package, release, arch, relations):
        """
        Check that the dependencies listed by a package are satisfiable for the
        specified release and architecture.
        """
        releases = self.data.list_dependent_releases(release)
        r = self.BindRelease(arch=arch, release=releases)
        relchecker = RelationChecker(r)

        statusdict = {}
        for rel in relations:
            status = relchecker.Check(package, rel)
            if status == None:
                return None
            statusdict[rel] = status
        return statusdict

    def checkInstall(self, package, release, arch, withrecommends):
        releases = self.data.list_dependent_releases(release)
        r = Release(self.psql, arch=arch, release=releases)
        relchecker = RelationChecker(r)
        status = relchecker.CheckInstall(package, withrecommends)

        if not status:
            return None

#        print status
#        print "Summary"
        s = status.flatten()
#        print s
        return s

    def checkBackport(self, package, fromrelease, torelease):
        """
        Check that the build-dependencies listed by a package in the release
        specified as "fromrelease" are satisfiable for in "torelease" for the
        given host architecture.
        """
        relchecker = RelationChecker(torelease)

        s = fromrelease.Source(package)
        if not s.Found():
            return None

        return relchecker.CheckBuildDeps(s)
