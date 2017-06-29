#
# Copyright (c) 2017 by Rowdy Dog Software
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import MySQLdb
import MySQLdb.constants.ER as MySQLErrorCodes
import _mysql_exceptions as MySQLExceptions
import time
# from .singleton import Singleton

def get_DatabaseInterfaceServerInformation():
    try:
        import dbisi
    except ModuleNotFoundError:
        with open('dbisi.py', 'wt') as ouf:
            ouf.write("""
class DatabaseInterfaceServerInformation:
    def __init__(self):
        self.host = "localhost"
        self.port = 3306
        self.database = "databasenamegoeshere"
        self.username = "usernamegoeshere"
        self.password = "passwordgoeshere"
""")
        import dbisi
    return dbisi.DatabaseInterfaceServerInformation()

def automatic_retry(call_me):
    def _automatic_retry(*args, **kwargs):
        self = args[0]
        tries = 2
        while tries > 0:
            try:
                rv = call_me(*args, **kwargs)
                tries = 0
            except MySQLExceptions.OperationalError as exc:
                self.reset()
                tries -= 1
                if tries > 0:
                    time.sleep(0.5)
                else:
                    raise
        return rv
    return _automatic_retry

# class DatabaseInterface(metaclass=Singleton):
class DatabaseInterface:
    def __init__(self):
        # The following 'if' is only required if this class is a Singleton.  If
        # this class is not a Singleton the 'if' does no harm.
        if not hasattr(self, '_connection'):
            self._connection = None
            self._server_information = get_DatabaseInterfaceServerInformation()
            self.reset()
    @property
    def connection(self):
        if self._connection is None:
            si = self._server_information
            self._connection = MySQLdb.connect(host=si.host, user=si.username, passwd=si.password, port=si.port, db=si.database)
        return self._connection
    @automatic_retry
    def execute(self, query, args=None, raise_dup_entry=False):
        c1 = self.connection
        c2 = self._execute_cursor
        if c2 is None:
            c2 = c1.cursor()
            self._execute_cursor = c2
        success = False
        try:
            c2.execute(query, args)
            self.lastrowid = c2.lastrowid
            success = True
        except MySQLExceptions.IntegrityError as exc:
            if raise_dup_entry or (exc.args[0] != MySQLErrorCodes.DUP_ENTRY):
                raise
        return success
    @automatic_retry
    def singleton(self, query, args=None):
        c1 = self.connection
        c2 = self._singleton_cursor
        if c2 is None:
            c2 = c1.cursor()
            self._singleton_cursor = c2
        c2.execute(query, args)
        row = c2.fetchone()
        while c2.nextset():
            pass
        return row
    def foreach(self, method, query, args=None):
        c1 = self.connection
        c2 = self._query_cursor
        if c2 is None:
            c2 = c1.cursor()
            self._query_cursor = c2
        c2.execute(query, args)
        for row in c2:
            method( row )
    def commit(self):
        self.connection.commit()
    def rollback(self):
        self.connection.rollback()
    def reset(self):
        if self._connection is not None:
            self._connection.close()
            self._connection = None
        self._execute_cursor = None
        self._query_cursor = None
        self._singleton_cursor = None
        self.lastrowid = None

