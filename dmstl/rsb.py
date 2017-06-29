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

from .singleton import Singleton

class RedundantStringsBase:
    def __init__(self):
        if not hasattr(self, '_string_to_id'):
            self._string_to_id = dict()
    def _insert_select_string(self, key):
        assert(False)
        return 0
    def get_id(self, key):
        rv = self._string_to_id.get(key)
        if rv is None:
            rv = self._insert_select_string(key)
            self._string_to_id[key] = rv
        return rv
    def reset(self):
        del self._string_to_id
        self._string_to_id = dict()
    def __getitem__(self, key):
        return self.get_id(key)

class RedundantStringsInMemory(RedundantStringsBase, metaclass=Singleton):
    def __init__(self):
        super().__init__()
        if not hasattr(self, '_current_id'):
            self._current_id = 0
    def _insert_select_string(self, key):
        self._current_id += 1
        return self._current_id

