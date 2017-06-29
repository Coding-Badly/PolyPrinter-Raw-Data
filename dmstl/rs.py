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

from .errors import InsertSelectError
from .rsb import RedundantStringsBase
# from .singleton import Singleton

# class RedundantStrings(RedundantStringsBase, metaclass=Singleton):
class RedundantStrings(RedundantStringsBase):
    def __init__(self, dbi):
        super().__init__()
        # Singleton._assign_once(self, '_dbi', dbi)
        self._dbi = dbi
    def _insert_select_string(self, key):
        dbi = self._dbi
        try:
            success = dbi.execute("insert into REDUNDANT_STRINGS ( STRING ) values ( %s )", (key,))
            if success:
                id1 = dbi.lastrowid
            else:
                r1 = dbi.singleton("select STRING_ID from REDUNDANT_STRINGS where STRING = %s", (key,))
                if r1 is None:
                    raise InsertSelectError(
                        'Selecting from REDUNDANT_STRINGS returned zero rows after an insert failed with DUP_ENTRY.',
                        key )
                id1 = r1[0]
            dbi.commit()
        except:
            dbi.rollback()
            raise
        return id1

