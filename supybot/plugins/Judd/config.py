###
# Copyright (c) 2007, Mike O'Connor
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

import supybot.conf as conf
import supybot.registry as registry
import Judd

def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified himself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import output, expect, anything, something, yn
    conf.registerPlugin('Judd', True)
    if not utils.findBinaryInPath('zgrep'):
        if not advanced:
            output("""I can't find zgrep in your path.  This is necessary
                      to run the file command.  I'll disable this command
                      now.  When you get zgrep in your path, use the command
                      'enable Judd.file' to re-enable the command.""")
            capabilities = conf.supybot.capabilities()
            capabilities.add('-Judd.file')
            conf.supybot.capabilities.set(capabilities)
        else:
            output("""I can't find zgrep in your path.  If you want to run
                      the file command with any sort of expediency, you'll
                      need it.  You can use a python equivalent, but it's
                      about two orders of magnitude slower.  THIS MEANS IT
                      WILL TAKE AGES TO RUN THIS COMMAND.  Don't do this.""")
            if yn('Do you want to use a Python equivalent of zgrep?'):
                conf.supybot.plugins.Judd.pythonZgrep.setValue(True)
            else:
                output('I\'ll disable file now.')
                capabilities = conf.supybot.capabilities()
                capabilities.add('-Judd.file')
                conf.supybot.capabilities.set(capabilities)


Judd = conf.registerPlugin('Judd')
# This is where your configuration variables (if any) should go.  For example:
# conf.registerGlobalValue(Judd, 'someConfigVariableName',
#     registry.Boolean(False, """Help for someConfigVariableName."""))
conf.registerGlobalValue( Judd, 'db_hostname', registry.String( "localhost", "hostname of udd postgres database" ) )
conf.registerGlobalValue( Judd, 'db_username', registry.String( 'stew', "username of udd postgres database" ) )
conf.registerGlobalValue( Judd, 'db_password', registry.String( 'stew', "password to udd postgres database" ) )
conf.registerGlobalValue( Judd, 'db_port', registry.Integer( 5432, "port of udd postgres database" ) )
conf.registerGlobalValue( Judd, 'db_database', registry.String( "udd", "postgres to use" ) )
conf.registerGlobalValue( Judd, 'base_path', registry.String("judd", "base path to the data files; if a relative path is used, it is relative to supybot.directories.data") )
conf.registerChannelValue( Judd, 'bold', registry.Boolean(True, """Determines whether the plugin will use bold in the responses to some of its commands."""))

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
