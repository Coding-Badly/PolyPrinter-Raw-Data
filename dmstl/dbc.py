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

# rmv https://github.com/niklasf/indexed.py
# rmv import indexed

class DeadbandCheckerBase:
    def __init__(self):
        super().__init__()
    def alive(self):
        return False
    def commit(self):
        pass
    def set_field_map(self, new_field_map):
        pass

class DeadbandCheckerAlwaysDead(DeadbandCheckerBase):
    def __str__(self):
        return "Always Dead"

class DeadbandCheckerDoOnce(DeadbandCheckerBase):
    def __init__(self):
        super().__init__()
        self._count = 1
    def __str__(self):
        return "Do Once"
    def alive(self):
        return self._count > 0
    def commit(self):
        if self._count > 0:
            self._count -= 1

class DeadbandChecker(DeadbandCheckerBase):
    def __init__(self):
        super().__init__()
        self._previous_value = None
        self._current_value = None
    def __str__(self):
        return "Any Change"
    def values_significantly_different(self, lft, rgt):
        return lft != rgt
    def alive(self):
        self._current_value = self._field_map.get_value()
        return self.values_significantly_different(self._current_value, self._previous_value)
    def commit(self):
        # rmv self._previous_value = self._current_value
        self._previous_value = self._field_map.get_value()
    def set_field_map(self, new_field_map):
        self._field_map = new_field_map

def is_float(v):
    try:
        return ( True, float(v) )
    except (ValueError, TypeError):
        return ( False, 0.0 )

class DeadbandCheckerForPercent(DeadbandChecker):
    def __str__(self):
        return "For Percent"
    def values_significantly_different(self, lft, rgt):
        lb, lv = is_float(lft)
        rb, rv = is_float(rgt)
        # If neither are float then they cannot be significantly difference from each other.
        if (not lb) and (not rb):
            return False
        # If one is a float and the other is not then they are definitely significantly different.
        if lb != rb:
            return True
        # At this point they both have to be float.  We'll make that an assertion to prove the point.
        assert lb and rb
        # If they are more than 1 (percent) different then they are significantly different.
        if abs(lv-rv) >= 1.0:
            return True
        # If just one value is exactly 100 (percent) then they are significantly different.
        if ((lv == 100.0) and (rv != 100.0)) or ((lv != 100.0) and (rv == 100.0)):
            return True
        return False

class DeadbandCheckers:
    def __init__(self, maps):
        super().__init__()
        self._active = list()
        self._bindable = dict()
        self._fixed = list()
        self._maps = maps
        self._need_to_activate_checkers = True
    def __iter__(self):
        if self._need_to_activate_checkers:
            self._activate_checkers()
        return iter(self._active)
    def _activate_checkers(self):
        for dbc in self._fixed:
            self._active.append(dbc)
        self._fixed = list()
        for fm in self._maps:
            fn = fm.field_name()
            dbc = self._bindable.get(fn, None)
            if dbc is None:
                dbc = DeadbandChecker()
            else:
                del self._bindable[fn]
            dbc.set_field_map(fm)
            self._active.append(dbc)
        self._need_to_activate_checkers = False
    def add_checker(self, name, checker):
        if name != '':
            self._bindable[name] = checker
        else:
            self._fixed.append(checker)
    def alive(self):
        for i1 in self:
            if i1.alive():
                return True
        return False
    def commit(self):
        for i1 in self:
            i1.commit()


