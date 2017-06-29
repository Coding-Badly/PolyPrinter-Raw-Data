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

from .rs import RedundantStrings
from .logging import get_logger

class DatabaseFieldMap:
    def __init__(self, field_name):
        super().__init__()
        self._field_name = field_name
        self._value = None
    def extract_value(self, value):
        self._value = value
    def field_name(self):
        return self._field_name
    def get_raw_value(self):
        assert(False)
    def get_sql_value(self):
        if self.is_null():
            return None
        else:
            return self.get_raw_value()
    def get_value(self):
        if self.is_null():
            return None
        else:
            return self.get_raw_value()
    def insert_format(self):
        return '%s'
    def always_include(self):
        return False
    def is_null(self):
        return self._value is None
    def reset(self):
        self._value = None
    def provides_sql_value(self):
        return True

class JsonValueToDatabaseFieldMap(DatabaseFieldMap):
    def __init__(self, path):
        super().__init__(path)
        self._json_path = path
    def json_path(self):
        return self._json_path
    def get_raw_value(self):
        return self._value

class JsonValueToBooleanFieldMap(JsonValueToDatabaseFieldMap):
    def extract_value(self, value):
        if value is None:
            self._value = None
        else:
            self._value = bool(value)

class JsonValueToIntFieldMap(JsonValueToDatabaseFieldMap):
    def extract_value(self, value):
        if value is None:
            self._value = None
        else:
            self._value = int(value)

class JsonValueToFloatFieldMap(JsonValueToDatabaseFieldMap):
    def extract_value(self, value):
        if value is None:
            self._value = None
        else:
            self._value = float(value)

class JsonValueToStringIdFieldMap(JsonValueToDatabaseFieldMap):
    def __init__(self, path, redundant_strings):
        super().__init__(path)
        self._field_name += '_ID'
        assert redundant_strings is not None
        self._redundant_strings = redundant_strings
    def extract_value(self, value):
        if value is None:
            self._value = None
        else:
            self._value = self._redundant_strings.get_id(str(value))

class PrinterIdFieldMap(DatabaseFieldMap):
    def __init__(self):
        super().__init__('PRINTERID')
    @property
    def id(self):
        return self._value
    @id.setter
    def id(self, value):
        self._value = int(value)
    def always_include(self):
        return True
    def get_raw_value(self):
        return self.id

# The assumption is that the database server has a more accurate clock than we
# do and, by using the database server's clock, there is a consistent
# reference.  Logging will occur over daylight savings time transitions.  To
# eliminate the two problems UTC is used.
class ObservedFieldMap(DatabaseFieldMap):
    def __init__(self):
        super().__init__('OBSERVED')
        self._value = 0
    def always_include(self):
        return True
    def get_raw_value(self):
        # assert False
        return None
    def insert_format(self):
        return 'UTC_TIMESTAMP()'
    def reset(self):
        self._value = 0
    def provides_sql_value(self):
        return False

class HttpStatusFieldMap(DatabaseFieldMap):
    def __init__(self):
        super().__init__('HTTP_STATUS')
        # smallint
    @property
    def status(self):
        return self._value
    @status.setter
    def status(self, value):
        self._value = int(value)
    def always_include(self):
        return True
    def get_raw_value(self):
        return self.status

class HttpMessageFieldMap(JsonValueToStringIdFieldMap):
    def __init__(self, redundant_strings):
        assert redundant_strings is not None
        super().__init__('HTTP_MESSAGE', redundant_strings)
        self._message = ''
    @property
    def message(self):
        return self._message
    @message.setter
    def message(self, value):
        self._message = str(value)
        self.extract_value(self._message)
    def always_include(self):
        return True
    def reset(self):
        super().reset()
        self._message = ''

class ExceptionFieldMap(JsonValueToStringIdFieldMap):
    def __init__(self, redundant_strings):
        assert redundant_strings is not None
        super().__init__('EXCEPTION', redundant_strings)
        self._class_name = ''
    @property
    def class_name(self):
        return self._class_name
    @class_name.setter
    def class_name(self, value):
        self._class_name = str(value)
        self.extract_value(self._class_name)
    def always_include(self):
        return True
    def reset(self):
        super().reset()
        self._class_name = ''

class JsonValueToDatabaseFieldMaps:
    def __init__(self, table_name):
        super().__init__()
        self._by_json_path = dict()
        self._by_list = list()
        self._sql_insert = None
        self._table_name = table_name
        self._provides_value = None
        self._logger = get_logger(__name__)
    def __iter__(self):
        return iter(self._by_list)
    def add(self, whatever):
        if whatever.always_include():
            self.add_fixed(whatever)
        else:
            self.add_map(whatever)
        return whatever
    def add_fixed(self, fixed):
        self._sql_insert = None
        self._by_list.append(fixed)
    def add_map(self, map):
        self._sql_insert = None
        self._by_json_path[map.json_path()] = map
        self._by_list.append(map)
    def generate_field_name_list(self):
        return ', '.join(map(lambda f: f.field_name(), self._by_list))
    def generate_value_format_list(self):
        return ', '.join(map(lambda f: f.insert_format(), self._by_list))
    def generate_insert(self):
        if self._sql_insert is None:
            fnl = self.generate_field_name_list()
            vfl = self.generate_value_format_list()
            self._sql_insert = 'insert into %s ( %s ) values ( %s )' % (self._table_name, fnl, vfl)
        return self._sql_insert
    def generate_value_tuple(self):
        if self._provides_value is None:
            self._provides_value = [map for map in self._by_list if map.provides_sql_value()]
        return tuple(map(lambda f: f.get_sql_value(), self._provides_value))
    def reset(self):
        for f in self._by_list:
            f.reset()
    def unrecognized_path(self, path, value):
        self._logger.warning('Unrecognized path %s with value %s', path, value)
    def _update_traverse(self, left, node):
        for key, value in node.items():
            k2 = key.upper()
            if left != '':
                path = left + '_' + k2
            else:
                path = k2
            if isinstance(value, dict):
                self._update_traverse(path, value)
            else:
                map = self._by_json_path.get(path, None)
                if map is None:
                    self.unrecognized_path(path, value)
                else:
                    map.extract_value(value)
    def update(self, prefix, json):
        self._update_traverse(prefix, json)


