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

# https://github.com/niklasf/indexed.py
import indexed

class RawDataCollected():
    def __init__(self):
        super().__init__()
        self.reset()
    def reset(self):
        self.active = True

class RawDataCollectorConfiguration:
    pass

class RawDataCollector():
    def __init__(self):
        super().__init__()
        self.active = True
    def get_fresh_data(self, collected):
        # returns a RawDataCollected or collected
        pass
    @property
    def name(self):
        return ''
    def shutdown(self):
        pass

class RawDataCollectors():
    def __init__(self, dbi):
        super().__init__()
        self._dbi = dbi
        self._container = indexed.IndexedOrderedDict()
        self._need_load = True
    def add_collector(self, collector):
        self._container[collector.name] = collector
    def _create_collector_from_row(self, row):
        assert False
    def _get_sql(self):
        assert False
    def _load_collector(self, row):
        collector = self._create_collector_from_row(row)
        self.add_collector(collector)
    def _load_collectors(self):
        self._need_load = False
        dbi = self._dbi
        if dbi is not None:
            try:
                dbi.foreach(self._load_collector, self._get_sql())
                dbi.commit()
            except:
                dbi.rollback()
                raise
        else:
            self._load_collectors_from_memory(self._load_collector)
    def _load_collectors_from_memory(self, method):
        assert False
    def __iter__(self):
        if self._need_load:
            self._load_collectors()
        return iter(self._container.values())
    def __getitem__(self, key):
        if self._need_load:
            self._load_collectors()
        if isinstance( key, int ):
            return self._container.values()[key]
        elif isinstance( key, str ):
            return self._container[key]
        else:
            # IndexError: list index out of range
            raise IndexError('only int keys are supported')
    def shutdown(self):
        for c1 in self:
            c1.shutdown()

