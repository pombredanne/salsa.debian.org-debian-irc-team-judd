#
# Ultimate Debian Database query tool
#
# Debian BTS abstraction layer
#
###
#
# Copyright (c) 2011   Stuart Prescott
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

import re
import psycopg2
import psycopg2.extras

severities = ('wishlist', 'minor', 'normal', 'important',
                    'serious', 'grave', 'critical')
all_severities = ('fixed', 'wishlist', 'minor', 'normal', 'important',
                    'serious', 'grave', 'critical')

status = ('pending', 'pending-fixed', 'done', 'forwarded', 'fixed')
open_status = ('pending', 'pending-fixed', 'forwarded')
closed_status = ('done', 'fixed')

wnpp_types = ('RFP', 'ITP', 'RFH', 'RFA', 'ITA', 'O')

class Bts(object):
    """ interface to the UDD for extracting bug information """

    def __init__(self, dbconn, include_archived=True):
        """ create a BTS searching instance

        include_archived: include "archived" bugs in searches
        """
        self.dbconn = dbconn
        self.include_archived = include_archived

    def bugs(self, bugnumbers):
        """ look up one """
        c = self.dbconn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cleanbugs = []
        for b in bugnumbers:
            if type(b) is int:
                cleanbugs.append(b)
            if type(b) is str or type(b) is unicode:
                b = b.replace('#', '')
                cleanbugs.append(int(b))
        cleanbugs = tuple(cleanbugs)
        q = self._query_builder("id IN %(bugs)s")
        c.execute(r"""SELECT *, FALSE AS archived
                        FROM bugs
                        WHERE id IN %(bugs)s""",
                    {'bugs': cleanbugs})
        found_bugs = [Bugreport(r) for r in c.fetchall()]
        if self.include_archived:
            found_bugnums= [b.id for b in found_bugs]
            missing_bugnums = tuple([n for n in cleanbugs if n not in found_bugnums])
            if missing_bugnums:
                c.execute(r"""SELECT *, TRUE AS archived
                                FROM archived_bugs
                                WHERE id IN %(bugs)s""",
                            {'bugs': missing_bugnums})
                found_bugs.extend([Bugreport(r) for r in c.fetchall()])
        return found_bugs

    def bug(self, bugnumber):
        b = self.bugs([bugnumber])
        if not b:
            raise BugNotFoundError(bugnumber)
        else:
            return b[0]

    def get_bugs(self, search):
        """
        "package": bugs for the given package
        "source": bugs belonging to a source package
        "severity": bugs with a certain severity
        "status": tuple of desired statuses ('pending', 'pending-fixed',
                                            'done', 'forwarded', or 'fixed')
        "title": regular expression match on title
        """
        c = self.dbconn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        wheres = {
                 'package': 'bugs_packages.package = %(package)s',
                 'source': 'bugs_packages.source = %(source)s',
                 'severity': 'severity IN %(severity)s',
                 'status': 'status IN %(status)s',
                 'title': 'title ~* %(title)s'
             }
        where = " AND ".join([wheres[s] for s in search if s in wheres])
        q = self._query_builder(where)
        if 'sort' in search:
            q += " ORDER BY %s" % search['sort']
        if 'limit' in search:
            q += " LIMIT %d" % search['limit']
        c.execute(q, search)
        return [Bugreport(r) for r in c.fetchall()]

    def get_bugs_tags(self, bugs):
        """Look up the tags for a list of bug objects"""
        c = self.dbconn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        archived_bugs = {}
        unarchived_bugs = {}
        try:
            for b in bugs:
               if b.archived:
                   archived_bugs[b.id] = b
               else:
                   unarchived_bugs[b.id] = b
        except TypeError:
            return self.get_bugs_tags([bugs])
        if unarchived_bugs:
            c.execute(r"""SELECT id, tag
                            FROM bugs_tags
                            WHERE id IN %(bugs)s""",
                        {'bugs': tuple(unarchived_bugs)})
            [unarchived_bugs[id].tags.append(t) for (id, t) in c.fetchall()]
        if archived_bugs:
            c.execute(r"""SELECT id, tag
                            FROM archived_bugs_tags
                            WHERE id IN %(bugs)s""",
                        {'bugs': tuple(archived_bugs)})
            [archived_bugs[id].tags.append(t) for (id, t) in c.fetchall()]

    def _query_builder(self, where):
        columns = r"""
                        %(archived)sbugs.id,
                        %(archived)sbugs.package AS package,
                        %(archived)sbugs.source AS source,
                        arrival, status, severity,
                        submitter, submitter_name, submitter_email,
                        owner, owner_name, owner_email,
                        done, done_name, done_email, done_date, title,
                        last_modified, forwarded,
                        affects_oldstable, affects_stable, affects_testing,
                        affects_unstable, affects_experimental
                """
        if self.include_archived:
            q = \
                r"""
                    SELECT %(columns)s,
                        FALSE AS archived
                    FROM bugs
                    JOIN bugs_packages
                        ON bugs.id = bugs_packages.id
                    WHERE %(where)s
                UNION
                    SELECT %(columns_archived)s,
                        TRUE AS archived
                    FROM archived_bugs AS bugs
                    JOIN archived_bugs_packages AS bugs_packages
                        ON bugs.id = bugs_packages.id
                    WHERE %(where)s
                """
        else:
             q = \
                r"""SELECT %(columns)s,
                        FALSE AS archived
                    FROM bugs
                    JOIN bugs_packages
                        ON bugs.id = bugs_packages.id
                    WHERE %(where)s
                """
        return q % ({
                        'where': where,
                        'columns': columns % {'archived':''},
                        'columns_archived': columns % {'archived':''}
                     })


class Bugreport(object):
    def __init__(self, data=None, archived=False):
        self.id = None
        self.package = None
        self.source = None
        self.arrival = None
        self.status = None
        self.severity = None
        self.submitter = None
        self.submitter_name = None
        self.submitter_email = None
        self.owner = None
        self.owner_name = None
        self.owner_email = None
        self.done = None
        self.done_name= None
        self.done_email = None
        self.done_date = None
        self.title = None
        self.last_modified = None
        self.forwarded = None
        self.affects_oldstable = None
        self.affects_stable = None
        self.affects_testing = None
        self.affects_unstable = None
        self.affects_experimental = None
        self.archived = archived
        self.tags = []
        if data:
            self.load(data)

    def load(self, data):
        [self.__setattr__(field, data[field]) for field in data.keys()]

    @property
    def readable_status(self):
        if not self.status:
            return
        if self.status in ('forwarded', 'fixed'):
            return self.status
        if self.status in ('done'):
            return 'closed'
        if self.status in ('pending'):
            return 'open'
        if self.status in ('pending-fixed'):
            return 'pending'

    @property
    def wnpp_type(self):
        if self.package != 'wnpp':
            raise ValueError()
        m = re.match('^(%s):? .*' % "|".join(wnpp_types), self.title, re.I)
        if m:
            return m.group(1).upper()
        return

    def __str__(self):
        s = [
                "Bug: %d" % self.id,
                "Package: %s" % self.package,
                "Source: %s" % self.source,
                "Severity: %s" % self.severity,
                "Bts-Status: %s" % self.status,
                "Status: %s" % self.readable_status,
                "Opened: %s" % self.arrival.date() if self.arrival else "",
                "Last-Modified: %s" % self.last_modified.date() if self.last_modified else "",
                "Archived: %s" % self.archived
             ]
        if self.tags:
            s.append("Tags: %s" % ", ".join(self.tags))
        if self.title:
            t = self.title.splitlines()
            if t:
                s.append("Title: %s" % t[0])
        s.append("")

        return "\n".join(s)


class BugNotFoundError(LookupError):
    """Exception raised when a bug is assumed to exist but doesn't"""

    def __init__(self, bugnumber):
        self.bugnumber = bugnumber

    def __str__(self):
        return "Bug number %s was not found." % self.bugnumber
