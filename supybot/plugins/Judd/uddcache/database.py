###
# -*- coding: utf-8 -*-
#
# Copyright (c) 2011  Stuart Prescott
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
# SUBSTITUTE GOODS OR SERVICES LOSS OF USE, DATA, OR PROFITS OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

""" Wrapper functions for logging of psycopg2 database connections """

from __future__ import unicode_literals

import types
import os
import time
import psycopg2
import psycopg2.extras
import psycopg2.extensions

import logging


def Connect(logfile, **kwargs):
    """Create a psycopg2 database connection that logs all SQL

    logfile: filename to log into
    kwargs: as per psycopg2.connect()

    The statement log also includes statement execution time.
    """
    psql = None
    if logfile:
        psql = psycopg2.connect(
                        connection_factory=WrappingLoggingConnection,
                        **kwargs
                     )
        db_logger = logging.getLogger('psql')
        db_logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(logfile)
        formatter = logging.Formatter('[%(asctime)-15s] %(name)s:%(levelname)s %(message)s')
        fh.setFormatter(formatter)
        db_logger.addHandler(fh)
        psql.initialize(db_logger)
    else:
        psql = psycopg2.connect(**kwargs)
    psql.set_isolation_level(0)
    psql.set_client_encoding('UTF8')
    psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
    psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)
    return psql


def _wrap(cursor, func):
    """ Construct a proxy function for methods that logs the call """
    def wrapper(*args, **kwargs):
        """ Wrapper function: call the original method and then log """
        cursor.timestamp = time.time()
        try:
            return func(*args, **kwargs)
        finally:
            if not isinstance(cursor, psycopg2.extras.LoggingCursor):
                cursor.connection.log(cursor.query.replace("%", "%%"), cursor)

    newfunc = types.FunctionType(wrapper.func_code, wrapper.func_globals,
                                func.func_name,
                                wrapper.func_defaults, wrapper.func_closure)
    newfunc.__doc__ = wrapper.__doc__
    return newfunc


class WrappingLoggingConnection(psycopg2.extras.LoggingConnection):
    """A connection that logs all queries to a file or logger__ object.

        As distinct to the original LoggingConnection class, the
        cursor_factory argument to the cursor() method can still be used.
        All cursor types can then be used with a connection that will
        always log.

    .. __: http://docs.python.org/library/logging.html
    """

    def filter(self, msg, curs):
        """Add the total execution time to the log output """
        t = (time.time() - curs.timestamp) * 1000
        return "[%d ms] %s" % (t, " ".join([line.strip()
                                            for line in msg.split("\n")]))
        #return msg + os.linesep + "  (execution time: %d ms)" % t

    def cursor(self, name=None, cursor_factory=None):
        """ Create a new cursor for the connection

        By default this will be a psycopg2.extras.LoggingCursor,
        however any other cursor type can be created by specifying
        cursor_factory.
        """
        self._check()
        # default to creating a LoggingCursor
        if cursor_factory is None:
            cursor_factory = psycopg2.extras.LoggingCursor
        if name is None:
            c = psycopg2.extensions.connection.cursor(self,
                                    cursor_factory=cursor_factory)
        else:
            c = psycopg2.extensions.connection.cursor(self, name,
                                    cursor_factory=cursor_factory)

        # wrap the execute and callproc methods of the cursor with
        # the logging wrapper -- this has two effects:
        #  * the wrapper will record the cursor creation so the total
        #     execution time can be logged
        #  * if a cursor other than the LoggingCursor is used, the log
        #    will still be written by the wrapper
        c.execute = _wrap(c, c.execute)
        c.callproc = _wrap(c, c.callproc)
        return c

#
#    return __changeFunctionName(wrapper, func.func_name, func.__doc__)
#
#def __changeFunctionName(func, name, doc=None):
#    if doc is None:
#        doc = func.__doc__
#    newfunc = types.FunctionType(func.func_code, func.func_globals, name,
#                              func.func_defaults, func.func_closure)
#    newfunc.__doc__ = doc
#    return newfunc
#
#def __wrap(cursor, func):
#    def newfunc(*args, **kwargs):
#        cursor.timestamp = time.time()
#        try:
#            return func(*args, **kwargs)
#        finally:
#            if not isinstance(cursor, psycopg2.extras.LoggingCursor):
#                cursor.connection.log(cursor.query, cursor)
#    return __changeFunctionName(newfunc, func.func_name, func.__doc__)
#
#def __changeFunctionName(func, name, doc=None):
#    if doc is None:
#        doc = func.__doc__
#    newfunc = types.FunctionType(func.func_code, func.func_globals, name,
#                              func.func_defaults, func.func_closure)
#    newfunc.__doc__ = doc
#    return newfunc
