###
# Copyright (c) 2009, Stuart Prescott
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
import Piccy

def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified himself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import expect, anything, something, yn
    conf.registerPlugin('Piccy', True)


Piccy = conf.registerPlugin('Piccy')
# This is where your configuration variables (if any) should go.  For example:
# conf.registerGlobalValue(Piccy, 'someConfigVariableName',
#     registry.Boolean(False, """Help for someConfigVariableName."""))
conf.registerGlobalValue( Piccy, 'base_path', registry.String("piccy", "base path to the data files; if a relative path is used, it is relative to supybot.directories.data") )
conf.registerGlobalValue( Piccy, 'pci_map', registry.String( "pci.ids", "pci-id file (full path or path relative to base_path)" ) )
conf.registerGlobalValue( Piccy, 'module_map', registry.String("modules.pcimap-%s", "kernel pci-id to module mapping file; use %s for the release name; (full path or path relative to base_path)") )
conf.registerGlobalValue( Piccy, 'hcl_url', registry.String( "http://kmuto.jp/debian/hcl/index.rhtmlx?check=1&lspci=%s", "link for extra information about the pci-id; use %s for the pci-id; will not be included in output if set to empty string") )
conf.registerGlobalValue( Piccy, 'extra_module_maps', registry.SpaceSeparatedListOfStrings(["squeeze-extras", "sid-extras"], "space separated list of extra kernel pci-id to module mapping files from out-of-tree modules; used in the %s 'release name' field of the module_map parameter; (full path or path relative to base_path)") )
conf.registerGlobalValue( Piccy, 'xorg_maps', registry.String("xorg-%s", "directory for xorg pci-id to xorg driver mappings; use %s for the release name; (full path or path relative to base_path)") )
conf.registerGlobalValue( Piccy, 'wiki_map', registry.String( "modules.wikilinks", "moin-moin wiki file that maps module names to wiki pages for further information (full path or path relative to base_path)") )
conf.registerGlobalValue( Piccy, 'wiki_url', registry.String( "http://wiki.debian.org/%s", "link for extra user contributed information about the module; use %s for the module; will not be included in output if set to empty string") )
conf.registerGlobalValue( Piccy, 'kernel_config', registry.String("config-%s", "kernel config file; use %s for the release name; (full path or path relative to base_path)") )
conf.registerGlobalValue( Piccy, 'kernel_versions', registry.String( "versions", "file containing a list of known kernel versions (full path or path relative to base_path)" ) )
conf.registerGlobalValue( Piccy, 'default_release', registry.String("stretch", "default release kernel to look at for modules") )
conf.registerGlobalValue( Piccy, 'fallback_release', registry.String("sid", "fallback release kernel to look at for modules if not found in requested release") )
conf.registerGlobalValue( Piccy, 'use_bold', registry.Boolean(True, "use bold face in selected places in the output") )

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
