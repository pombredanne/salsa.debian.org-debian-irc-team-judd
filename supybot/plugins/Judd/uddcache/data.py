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
#
###


""" Static classes describing the data that is available """


class AvailableData:
    """ Base class for available data across all distros """
    release_map = {}
    releases = []
    devel_release = ''
    stable_release = ''
    arches = []

    relations = [
                    'depends',
                    'recommends',
                    'suggests'
                ]

    extendedrelations = relations[:]
    extendedrelations.append('enhances')
    extendedrelations.append('conflicts')

    @classmethod
    def clean_release_name(cls, name=None, optlist=None, optname="release",
                         args=None, default="stable"):
        """
        Sanitised canonical release name
        """
        # Look for the name in an optlist, free-text args and simply specified
        rel = default
        optlist = optlist or []
        args = args or []
        for (option, arg) in optlist:
            if option == optname:
                rel = arg
        for arg in args:
            if arg in cls.releases:
                rel = arg
        if name:
            rel = name
        # Sanitise the name
        if not rel in cls.releases and not rel in cls.release_map:
            rel = default
        if rel in cls.release_map:
            rel = cls.release_map[rel]
        return rel

    @classmethod
    def clean_arch_name(cls, name=None, optlist=None, optname="arch",
                      args=None, default="i386"):
        """
        Sanitised architecture name
        """
        # Look for the name in an optlist, free-text args and simply specified
        arch = default
        optlist = optlist or []
        args = args or []
        for (option, arg) in optlist:
            if option == optname:
                arch = arg
        for arg in args:
            if arg in cls.arches:
                arch = arg
        if name:
            arch = name
        # Sanitise the name
        if not arch in cls.arches:
            arch = default
        return arch

    @classmethod
    def list_dependent_releases(cls, release, suffixes=None,
                                include_self=True):
        """
        List the releases that should also be included in the dependency
        analysis
        """
        rels = []
        suffixes = suffixes or []
        clean_rel = cls.clean_release_name(name=release, default=None)
        if not clean_rel:
            return rels

        if include_self:
            rels.append(clean_rel)
        parts = release.split('-')
        if len(parts) > 1:
            rel = cls.clean_release_name(name=parts[0], default=None)
            if rel:
                rels.append(rel)
        for suf in suffixes:
            rel = cls.clean_release_name(name="%s-%s" % (parts[0], suf),
                                        default=None)
            if rel:
                rels.append(rel)
        if release == "experimental":         # FIXME: move to distro-specific
            rels.append("sid")
        return rels


class DebianData(AvailableData):
    """ Debian-specific data """
    release_map = {
                    'rc-buggy':            'experimental',
                    'unstable':            'sid',
                    'testing':             'jessie',
                    'stable':              'wheezy',
                    'stable-backports':    'wheezy-backports',
                    'oldstable':           'squeeze',
                    'oldstable-backports': 'squeeze-backports',
                    'oldstable-backports-sloppy': 'squeeze-backports-sloppy',
                }

    releases = [
                    'squeeze',
                    'squeeze-security',
                    'squeeze-security-lts',
                    'squeeze-updates',
                    'squeeze-proposed-updates',
                    'squeeze-backports',
                    'squeeze-backports-sloppy',
                    'squeeze-multimedia',
                    'wheezy',
                    'wheezy-security',
                    'wheezy-updates',
                    'wheezy-proposed-updates',
                    'wheezy-backports',
                    'wheezy-multimedia',
                    'jessie',
                    'jessie-security',
                    'jessie-multimedia',
                    'sid',
                    'sid-multimedia',
                    'experimental',
                ]

    devel_release = 'sid'

    arches = ['alpha', 'amd64', 'armel', 'armhf',
               'hppa', 'hurd-i386', 'i386', 'ia64',
               'kfreebsd-amd64', 'kfreebsd-i386',
               'mips', 'mipsel', 'powerpc', 's390', 's390x',
               'sparc', 'all']

    stable_release = 'squeeze'
