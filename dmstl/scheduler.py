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

import math
import sched
import time

class RepeatingEvent(sched.Event):
    def thunk(self, scheduler):
        # NOTE: If action raises an exception it will not be rescheduled.
        self.action(*self.argument, **self.kwargs)
        next = scheduler.get_next(self.time)
        scheduler.enterabs(next, self.priority, self.thunk, argument=(scheduler,))

class ToolLogsScheduler(sched.scheduler):
    def __init__(self, timefunc=time.time, delayfunc=time.sleep):
        super().__init__(timefunc, delayfunc)
    def every(self, frequency, priority, action, argument=(), kwargs=sched._sentinel):
        if kwargs is sched._sentinel:
            kwargs = {}
        repeating_event = RepeatingEvent(frequency, priority, action, argument, kwargs)
        # Schedule the first run within the next seconds
        next = self.get_next(1)  # rmv self.get_next(frequency)
        return self.enterabs(next, priority, repeating_event.thunk, argument=(self,))
    def get_next(self, frequency):
        mark = self.timefunc()
        fraction, whole = math.modf(mark+0.5)
        next = whole + frequency
        return next

