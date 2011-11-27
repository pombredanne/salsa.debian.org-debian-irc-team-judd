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

import os
import udd
import commands
from packages import PackageNotFoundError
from bts import BugNotFoundError

class Cli():
    """ Run a specified command sending output to stdout """

    def __init__(self, config=None, options=None, initialise=True):
        if not options:
            raise ValueError("No options specified.")
        self.command_map = {
                'versions':     self.versions,
                'info':         self.info,
                'names':        self.names,
                'archs':        self.archs,
                'rprovides':    self.rprovides,
                'provides':     self.provides,
                'source':       self.source,
                'binaries':     self.binaries,
                'builddeps':    self.builddeps,
                'recent':       self.recent,
                'maint':        self.maint,
                'popcon':       self.popcon,
                'relations':    self.relations,
                'depends':      self.depends,
                'recommends':   self.depends,
                'suggests':     self.depends,
                'enhances':     self.depends,
                'conflicts':    self.depends,
                'checkdeps':    self.checkdeps,
                'checkbuilddeps': self.checkbuilddeps,
                'checkinstall': self.checkinstall,
                'checkbackport': self.checkbackport,
                'why':          self.why,
                'bug':          self.bug,
                'rcbugs':       self.rcbugs,
                'rm':           self.rm,
                'wnpp':         self.wnpp,
                'rfp':          self.wnpp,
                'itp':          self.wnpp,
                'rfa':          self.wnpp,
                'ita':          self.wnpp,
                'orphan':       self.wnpp,
                }
        self.command_aliases = {
                'show':         'info',
                'arches':       'archs',
                'whatprovides': 'rprovides',
                'maintainer':   'maint',
                'uploader':     'maint',
                'changer':      'maint',
                'builddep':     'builddeps',
                'build-dep':    'builddeps',
                'build-deps':   'builddeps',
                }
        if initialise:
            self.udd = udd.Udd(config=config,
                                                  distro=options.distro)
            self.dispatcher = commands.Commands(self.udd)
            self.options = options

    def is_valid_command(self, command):
        """ test if the supplied command string is a valid command """
        return command.lower() in self.command_map or \
                command.lower() in self.command_aliases

    def run(self, command, package, args):
        """ run the specified command """
        if command.lower() in self.command_aliases:
            command = self.command_aliases[command.lower()]
        if not self.is_valid_command(command):
            raise ValueError("command was not valid: %s" % command)
        callback = self.command_map[command.lower()]
        callback(command, package, args)

    @staticmethod
    def notfound(package, release=None, arch=None,
                 message="No package named '%s' was found%s."):
        """ print a message indicating that the package was not found """
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
        print message % (package, tag)

    def versions(self, command, package, args):
        """ look up the version of a package in a release or releases """
        release = self.udd.data.clean_release_name(self.options.release,
                                   args=args, default=None)
        arch = self.udd.data.clean_arch_name(self.options.arch, args=args)

        try:
            pkgs = self.dispatcher.versions(package, release, arch)
        except PackageNotFoundError:
            return self.notfound(package, release, arch)

        replies = []
        for row in pkgs:
            if (row['component'] == 'main'):
                replies.append("%-30s %s" % \
                                ("%s:" % row['release'], row['version']))
            else:
                replies.append("%-30s %s" % \
                                ("%s/%s:" % (row['release'], row['component']),
                                  row['version']))

        print "Package: %s %s/%s\n%s" % (package, release, arch,
                                        "\n".join(replies))

    def info(self, command, package, args):
        """ show info (version, size, homepage, screenshot) about a package """
        release = self.udd.data.clean_release_name(self.options.release,
                                                   args=args)
        arch = self.udd.data.clean_arch_name(self.options.arch, args=args)

        try:
            p = self.dispatcher.info(package, release, arch)
        except PackageNotFoundError:
            return self.notfound(package, release, arch)

        print "Package: %s (%s, %s)" % \
                        (package, p['section'], p['priority'])
        print "Release: %s/%s" % (release, arch)
        print "Version: %s" % p['version']
        print "Size: %0.1fk" % (p['size'] / 1024.0)
        print "Installed-Size: %dk" % p['installed_size']
        if p['homepage']:
            print "Homepage: %s" % p['homepage']
        if p['screenshot_url']:
            print "Screenshot: %s" % p['screenshot_url']
        print "Description: %s" % p['description']

    def names(self, command, package, args):
        """ search for package names with wildcard (? and *) expressions """
        release = self.udd.data.clean_release_name(self.options.release,
                                                   args=args)
        arch = self.udd.data.clean_arch_name(self.options.arch, args=args)

        pkgs = self.dispatcher.names(package, release, arch)
        if not pkgs:
            return self.notfound(package, release, arch,
                             message="No packages matching %s were found%s.")

        replies = []
        for row in pkgs:
            if (row['component'] == 'main'):
                replies.append("%s %s" % \
                                (row['package'], row['version']))
            else:
                replies.append("%s %s (%s)" % \
                                (row['package'], row['version'],
                                  row['component']))

        print "%s in %s/%s:\n%s" % (package, release, arch, "\n".join(replies))

    def archs(self, command, package, args):
        """
        Show for what architectures a package is available. By default,
        the current stable release is used.
        """
        release = self.udd.data.clean_release_name(self.options.release,
                                                   args=args)

        try:
            pkgs = self.dispatcher.archs(package, release)
        except PackageNotFoundError:
            return self.notfound(package, release)

        replies = []
        for row in pkgs:
            replies.append("%s (%s)" % (row[0], row[1]))
        print "%s: %s" % (package, ", ".join(replies))

    def rprovides(self, command, package, args):
        """
        Show the packages that 'Provide' the specified virtual package
        ('reverse provides').
        By default, the current stable release and i386 are used.
        """
        release = self.udd.data.clean_release_name(self.options.release,
                                                   args=args)
        arch = self.udd.data.clean_arch_name(self.options.arch, args=args)

        p = self.udd.BindPackage(package, release, arch)
        if p.IsVirtual():
            reply = "%s in %s/%s is provided by:\n%s" % \
                    (package, release, arch, "\n".join(p.ProvidersList()))
            if p.Found():
                reply += "\n%s is also a real package." % package
        else:
            if p.Found():
                reply = "In %s/%s, %s is a real package." % \
                            (release, arch, package)
            else:
                reply = "No packages provide '%s' in %s/%s." % \
                                                (package, release, arch)

        print reply

    def provides(self, command, package, args):
        """
        Show the list of "provided" packages for the specified binary package
        in the given release and architecture. By default, the current
        stable release and i386 are used.
        """
        release = self.udd.data.clean_release_name(self.options.release,
                                                   args=args)
        arch = self.udd.data.clean_arch_name(self.options.arch, args=args)

        p = self.udd.BindPackage(package, release, arch)

        if p.Found():
            if p.data['provides']:
                print "%s in %s/%s provides: %s." % \
                            (package, release, arch, p.data['provides'])
            else:
                print "%s in %s/%s provides no additional packages." % \
                            (package, release, arch)
        else:
            return self.notfound(package, release, arch)

    def source(self, command, package, args):
        """
        Show the name of the source package from which a given binary package
        is derived.
        By default, the current stable release and i386 are used.
        """
        release = self.udd.data.clean_release_name(self.options.release,
                                                   args=args)
        arch = self.udd.data.clean_arch_name(self.options.arch, args=args)

        r = self.udd.BindRelease(release, arch)

        try:
            p = r.bin2src(package)
        except PackageNotFoundError:
            return self.notfound(package, release, arch)

        print "Source: %s" % p

    def binaries(self, command, package, args):
        """
        Show the name of the binary package(s) that are derived from a given
        source package.
        By default, the current stable release and i386 are used.
        """
        release = self.udd.data.clean_release_name(self.options.release,
                                                   args=args)
        arch = self.udd.data.clean_arch_name(self.options.arch, args=args)

        try:
            p = self.udd.BindSourcePackage(package, release)
        except PackageNotFoundError:
            return self.notfound(package, release, arch)

        print "Binaries: %s" % ", ".join(p.Binaries())

    def builddeps(self, command, package, args):
        """
        Show the name of the binary packages on which a given source package
        or binary package build-depends.
        By default, the current stable release is used.
        """
        release = self.udd.data.clean_release_name(self.options.release,
                                                   args=args)

        try:
            p = self.udd.BindSourcePackage(package, release)
        except PackageNotFoundError:
            return self.notfound(package, release)

        self._package_relation_lookup(p, release, 'build_depends')
        self._package_relation_lookup(p, release, 'build_depends_indep',
                                     skipErrors=True, skipHeaders=True)

    def relations(self, command, package, args):
        """
        Show all package relationships for this binary package.
        By default, the current stable release is used.
        """
        release = self.udd.data.clean_release_name(self.options.release,
                                                   args=args)
        arch = self.udd.data.clean_arch_name(self.options.arch, args=args)
        p = self.udd.BindPackage(package, release, arch)
        self._package_relation_lookup(p, release, 'depends')
        self._package_relation_lookup(p, release, 'recommends',
                                     skipErrors=True, skipHeaders=True)
        self._package_relation_lookup(p, release, 'suggests',
                                     skipErrors=True, skipHeaders=True)
        self._package_relation_lookup(p, release, 'enhances',
                                     skipErrors=True, skipHeaders=True)
        self._package_relation_lookup(p, release, 'conflicts',
                                     skipErrors=True, skipHeaders=True)

    def depends(self, command, package, args):
        """
        Show one particular package relationship for this binary package.
        By default, the current stable release is used.
        """
        release = self.udd.data.clean_release_name(self.options.release,
                                                   args=args)
        arch = self.udd.data.clean_arch_name(self.options.arch, args=args)
        p = self.udd.BindPackage(package, release, arch)
        self._package_relation_lookup(p, release, command)

    def recent(self, command, package, args):
        release = self.udd.data.clean_release_name(self.options.release,
                                                   args=args)
        try:
            p = self.udd.BindSourcePackage(package, release)
        except PackageNotFoundError:
            return self.notfound(package)

        uploads = self.dispatcher.uploads(p, max=10)
        format = "%-20s %-10s %-20s %-20s %s"
        print format % ('version', 'date', 'changer', 'signer', 'nmu')
        for u in uploads:
            nmu = ['', 'nmu'][u['nmu']]
            print format % \
                (u['version'], u['date'].date(),
                    u['changed_by_name'], u['signed_by_name'], nmu)

    def maint(self, command, package, args):
        release = self.udd.data.clean_release_name(self.options.release,
                                                   args=args)
        try:
            p = self.udd.BindSourcePackage(package, release)
        except PackageNotFoundError:
            return self.notfound(package)

        version = ""
        if args:
            version = args.pop(0)

        uploads = self.dispatcher.uploads(p, max=1, version=version)
        u = uploads[0]
        print "Version: %s" % u['version']
        print "Date: %s" % u['date'].date()
        print "Uploader: %s <%s>" % (u['signed_by_name'], u['signed_by_email'])
        print "Changer: %s <%s>" % \
                (u['changed_by_name'], u['changed_by_email'])
        print "Maintainer: %s <%s>" % \
                (u['maintainer_name'], u['maintainer_email'])
        if u['nmu']:
            print "NMU: yes"

    def popcon(self, command, package, args):
        release = self.udd.data.clean_release_name(self.options.release,
                                                   args=args)
        try:
            d = self.dispatcher.popcon(package)
        except PackageNotFoundError:
            return self.notfound(package)

        print "Popcon data for %s:" % package
        print "  installed: %d" % d['insts']
        print "  vote:      %d" % d['vote']
        print "  old:       %d" % d['olde']
        print "  recent:    %d" % d['recent']
        print "  nofiles:   %d" % d['nofiles']

    def checkdeps(self, command, package, args):
        """
        Check a package's dependencies are satisfiable

        Checks that each dependency (by default, Depends, Recommends and
        Suggests) as listed by a package is satisfiable for the
        specified release and architecture. In contrast to the "checkinstall"
        function, this check is not done recursively.

        By default, the current stable release and i386 are used.
        """
        release = self.udd.data.clean_release_name(self.options.release,
                                                   args=args)
        arch = self.udd.data.clean_arch_name(self.options.arch, args=args)

        relation = []
        if self.options.deptype:
            for dep in self.options.deptype:
                if dep in self.udd.data.relations:
                    relation.append(dep)
        if not relation:
            relation = self.udd.data.relations

        try:
            status = self.dispatcher.checkdeps(package, release, arch, relation)
        except PackageNotFoundError:
            return self.notfound(package, release, arch)

        for rel in self.udd.data.relations:
            if rel in relation:
                label = rel.title().replace('_', '-')
                if status[rel].bad:
                    print "%s: unsatisfied: %s" % \
                            (label, str(status[rel].bad))
                else:
                    print "%s: satisfied" % label


    def checkbuilddeps(self, command, package, args):
        """
        Check a package's build-dependencies are satisfiable

        Checks that each Build-Depends and Build-Depends-Indep package
        as listed by a source package is satisfiable for the
        specified release and architecture.

        By default, the current stable release and i386 are used.
        """
        release = self.udd.data.clean_release_name(self.options.release,
                                                   args=args)
        arch = self.udd.data.clean_arch_name(self.options.arch, args=args)

        r = self.udd.BindRelease(arch=arch, release=release)

        try:
            status = self.dispatcher.checkBackport(package, r, r)
        except PackageNotFoundError:
            return self.notfound(package)

        print "Build-dependency check for %s in %s/%s:" % \
                (package, release, arch)
        print "Checked: %s" % ", ".join(r.release)

        self._builddeps_status_formatter(status)


    def checkinstall(self, command, package, args):
        release = self.udd.data.clean_release_name(self.options.release,
                                                   args=args)
        arch = self.udd.data.clean_arch_name(self.options.arch, args=args)

        try:
            solverh = self.dispatcher.checkInstall(package, release,
                                    arch, self.options.withrecommends)
        except PackageNotFoundError:
            return self.notfound(package, release, arch)

        flatlist = solverh.flatten()
        print flatlist
        if self.options.verbose:
            print solverh

    def checkbackport(self, command, package, args):
        """
        Check that the build-dependencies listed by a package in the release
        specified as "from-release" are satisfiable for in "to-release" for the
        given host architecture.
        By default, a backport from unstable to the current stable release
        and i386 are used.
        """
        fromrelease = self.udd.data.clean_release_name(
                                        self.options.fromrelease,
                                        default='unstable')
        torelease = self.udd.data.clean_release_name(
                                        self.options.torelease,
                                        default='stable')
        arch = self.udd.data.clean_arch_name(self.options.arch, args=args)

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
            return self.notfound(package)

        print "Backport check for %s in %s->%s/%s:" % \
                (package, fromrelease, torelease, arch,)
        print "Checked: %s" % ", ".join(tr.release)

        self._builddeps_status_formatter(status)

    def why(self, command, package, args):
        """
        Find all the dependency chains that link two packages

        Generates a list of dependency chains that go from package1 to
        package2 in the specified release and architecture. Recommends
        are optionally included in the dependency analysis too. Note that
        this function will look for *all* dependency chains not just the
        shortest/strongest one that is available.
        """
        release = self.udd.data.clean_release_name(self.options.release,
                                                   args=args)
        arch = self.udd.data.clean_arch_name(self.options.arch, args=args)

        if not args:
            raise ValueError("No second package specified for command 'why'")
        package2 = args.pop(0)

        try:
            chains = self.dispatcher.why(package, package2, release, arch,
                              self.options.withrecommends)
        except PackageNotFoundError:
            return self.notfound(package, release, arch)

        if chains:
            print "Packages %s and %s are linked by %d chains." \
                    % (package, package2, len(chains))
            for c in chains:
                print unicode(c).encode('UTF-8')
        else:
            print "No dependency chain could be found between %s and %s" \
                    % (package, package2)

    @classmethod
    def _builddeps_status_formatter(self, status):

        if not status.AllFound():  # packages missing
            badrels = self._builddeps_formatter(status, data='bad')
            print "Unsatisfiable build dependencies:"
            print "\n".join(badrels)
        else:
            extras = []
            rm = status.ReleaseMap()
            for releasename in rm.keys():
                #print "XR=%s" % releasename
                l = []
                for relation in rm[releasename]:
                    if relation.archIgnore:
                        continue
                    if not relation.virtual:
                        #print relation.package.data['package']
                        l.append(unicode(relation.satisfiedBy.packagedata.data['package']))
                    else:
                        l.append(ur"%s→%s" % (relation.satisfiedBy.package,
                            " ".join(relation.satisfiedBy.packagedata.ProvidersList())))
#                extras.append("%s: %s" % (xr,
#                    ", ".join([i.package.data['package'] for i in rm[xr]])))
                if l:
                    extras.append(ur"%s: %s" % (releasename, ', '.join(l)))
            print "All build-dependencies satisfied."
            print u"\n".join(extras).encode("UTF-8")

    @classmethod
    def _package_relation_lookup(cls, package, release, relation,
                                skipErrors=False, skipHeaders=False):
        """ Print a summary of the relationships of a package """
        label = relation.title().replace('_', '-')
        if not package.Found():
            if not skipErrors:
                cls.notfound(package.package, release, package.arch)
            return
        if not skipHeaders:
            print "Package: %s %s/%s" % \
                    (package.package, release, package.arch)
        print "%s: %s" % \
                    (label, package.RelationEntry(relation))

    @staticmethod
    def _builddeps_formatter(bdstatus, data='bad'):
        """ Print a summary of the build-deps of a package """
        def format_rel(rel, longname):
            if rel:
                return "%s: %s" % (longname, str(rel))
            return None

        l = [
               format_rel(bdstatus.bd.get(data),  'Build-Depends'),
               format_rel(bdstatus.bdi.get(data), 'Build-Depends-Indep')
            ]
        return filter(None, l)

    def bug(self, command, bugnumber, args):
        bugnumber = int(bugnumber)
        try:
            bug = self.dispatcher.bug(bugnumber, self.options.verbose)
        except BugNotFoundError:
            print "Sorry, bug %d was not found." % bugnumber
            return
        print bug

    def rm(self, command, package, args):
        try:
            bug = self.dispatcher.rm(package)
        except BugNotFoundError:
            print "Sorry, no removal bug for %s was found." % package
            return
        print bug[0]

    def wnpp(self, command, package, args):
        bugtype = command.upper()
        if bugtype == 'ORPHAN':
            bugtype = 'O'
        if bugtype == 'WNPP':
            bugtype = None
        try:
            bugs = self.dispatcher.wnpp(package, bugtype)
        except BugNotFoundError:
            print "Sorry, no WNPP bug for %s was found." % package
            return
        print "\n".join([str(b) for b in bugs])

    def rcbugs(self, command, package, args):
        bugs = self.dispatcher.rcbugs(package)
        if not bugs:
            print "No release critical bugs were found for '%s'." % package
            return
        print "\n".join([str(b) for b in bugs])
