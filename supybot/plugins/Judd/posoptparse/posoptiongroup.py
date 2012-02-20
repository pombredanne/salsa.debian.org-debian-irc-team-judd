###
# Copyright (c) 2010-2011    Stuart Prescott
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

"""
OptionGroup class that allows for pre-defined positional arguments such
as sub-commands

    e.g.   udd-cache search [...]
"""

# Based loosely on:
# http://stackoverflow.com/questions/642648/how-do-i-format-positional-argument-help-using-pythons-optparse
#
# See also:
# http://corebio.googlecode.com/svn/tags/0.5.0/apidocs/optparse.IndentedHelpFormatter-class.html
# http://docs.huihoo.com/pydoc/python/2.5/stdlib/optparse.OptionGroup-class.html

import types
from optparse import Option, IndentedHelpFormatter, OptionGroup


class PosOptionGroup(OptionGroup):
    """ Defines a set of positional parameters that can be used
        in the same way as --long-options can be used with OptionGroup """

    def __init__(self, parser, heading, description):
        self.positional = []
        OptionGroup.__init__(self, parser, heading, description)

    def format_help(self, formatter=None):
        """ Create a help text based on the options defined.
        The -- that is added to the options is automatically removed """

        class Positional(object):
            def __init__(self, args):
                self.option_groups = []
                self.option_list = args

        positional = Positional(self.positional)
        formatter = IndentedHelpFormatter()
        formatter.store_option_strings(positional)
        output = ['\n', formatter.format_heading("Commands")]
        formatter.indent()
        pos_help = [formatter.format_option(opt) for opt in self.positional]
        pos_help = [line.replace('--', '') for line in pos_help]
        output += pos_help
        return OptionGroup.format_help(self, formatter) + ''.join(output)

    def add_option(self, *args, **kwargs):
        """ Add a new option to the option group """
        if type(args[0]) is types.StringType:
            kwargs['action'] = 'store_true'
            option = Option(*args, **kwargs)
        elif len(args) == 1 and not kwargs:
            option = args[0]
            if not isinstance(option, Option):
                raise TypeError("not an Option instance: %r" % option)
        else:
            raise TypeError("invalid arguments")

        self.positional .append(option)
