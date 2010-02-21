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


class PackageFileList:
    """
    Manage a mapping of filenames to packages that contain them
    """

    def __init__(self):
        self.packages = {}

    def add(self, f, p):
        for pack in p:
            if not pack in self.packages.keys():
                self.packages[pack] = []
            self.packages[pack].append(f)

    def toString(self, boldfn):
        s = []
        for p in self.packages.keys():
            #section,name = p.split('/')
            info = p.split('/')
            if len(info) == 2:
                name = info[1]
            elif len(info) == 3:
                name = info[2]
            s.append("%s: %s" % (boldfn(name), ", ".join(self.packages[p])))
        return "; ".join(s)

    def __len__(self):
        return len(self.packages.keys())

    def __str__(self):
        s = []
        for p in self.packages.keys():
            section,name = p.split('/')
            s.append("%s: %s" % (name, ", ".join(self.packages[p])))
        return "; ".join(s)
