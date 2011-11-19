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

import os
import re
import subprocess
import contents_dict

class contents_file(object):
    """ abstraction of a Contents file """
    def __init__(self, base, release, arch, sections=None):
        self.base = base
        self.release = release
        self.arch = arch
        if not sections:
            self.sections = ['main']
        else:
            self.sections = sections
        self.maxhits = 20

    def search(self, regexp):
        packages = contents_dict.contents_dict()
        for s in self.sections:
            filename = 'debian-%s/%s/Contents-%s.gz' % \
                        (self.release, s, self.arch)
            filepath = os.path.join(self.base, filename)
            packages.update(self._search_file(filepath, regexp))
        return packages

    def _search_file(self, filepath, regexp):
        """
        Find the packages that provide files matching a particular regexp.
        """

        try:
            re_obj = re.compile(regexp, re.I)
        except re.error, e:
            raise ContentsError('Error in regexp: %s' % e, e)

        if not os.path.isfile(filepath):
            raise ContentsError('Could not look up file list')

        try:
            #print "Trying: zgrep -iE -e '%s' '%s'" % (regexp, contents)
            output = subprocess.Popen(['zgrep', '-iE', '-e', regexp, filepath],
                      stdout=subprocess.PIPE,
                      stderr=subprocess.PIPE,
                      close_fds=True).communicate()[0]
        except TypeError:
            raise ContentsError('Could not look up file list')

        packages = contents_dict.contents_dict()
        try:
            lines = output.split("\n")
            if len(lines) > self.maxhits:
                raise ContentsError('There were more than %s files matching '
                                'your search; please narrow your search.' % \
                                self.maxhits)
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

class ContentsError(LookupError):
    pass
