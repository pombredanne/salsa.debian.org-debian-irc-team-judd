###
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

""" Contents file results parsing """

class PackageFileList:
    """
    Manage a mapping of filenames to packages that contain them
    """

    def __init__(self):
        """ Create internal storage """
        self.packages = {}

    def add(self, filename, packagelist):
        """ Add a file and set of packages containing that file"""
        for pack in packagelist:
            if not pack in self.packages.keys():
                self.packages[pack] = []
            self.packages[pack].append(filename)

    def to_string(self, boldfn):
        """ Turn the list into a condensed one-line string output """
        s = []
        # sort the packages so that packages that contain the shortest paths
        # (by number of path elements, /) come first.
        pprio = sorted(self.packages.keys(),
          key=lambda p: min(map(lambda f: f.count('/'), self.packages[p])))
        for pack in pprio:
            #section,name = p.split('/')
            info = pack.split('/')
            if len(info) == 2:
                name = info[1]
            elif len(info) == 3:
                name = info[2]
            s.append("%s: %s" % (boldfn(name), ", ".join(self.packages[pack])))
        return "; ".join(s)

    def __len__(self):
        """ Return the number of packages in the list """
        return len(self.packages.keys())

    def __str__(self):
        """ Turn the list into a condensed one-line string (simple) """
        s = []
        for pack in self.packages.keys():
           # either section/package (shells/bash) or
            # component/section/package (non-free/editors/axe)
            info = pack.split('/')
            if len(info) == 2:
                name = info[1]
            elif len(info) == 3:
                name = info[2]
            s.append("%s: %s" % (name, ", ".join(self.packages[pack])))
        return "; ".join(s)
