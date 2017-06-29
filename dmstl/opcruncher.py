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

import dmstl
import enum
from pubsub import pub

class NetworkState(enum.Enum):
    UNKNOWN = 1
    GOOD = 2
    UNREACHABLE = 3
    OFFLINE = 4
    BAD_PASSWORD = 5

class DeviceState(enum.Enum):
    UNKNOWN = 1
    IDLE = 2
    BUSY = 3
    PAUSED = 4
    INOPERABLE = 5

class OctoPrintModel():
    def __init__(self, id, name, twitter_credentials, scheduler):
        super().__init__()
        self._id = id
        self._name = name
        if twitter_credentials is None:
            self._tweeter = dmstl.TwitterNull()
        else:
            self._tweeter = dmstl.TwitterThread(name, twitter_credentials)
        self._scheduler = scheduler
        self._frozen = 0
        self._network_state_current = NetworkState.UNKNOWN
        self._network_state_previous = NetworkState.UNKNOWN
        self._network_state_offline = 0
        self._device_state_current = DeviceState.UNKNOWN
        self._device_state_previous = DeviceState.UNKNOWN
        self._get_busy_prattler = dmstl.OctoPrintGetBusyPrattler()
        self._idle_prattler = dmstl.OctoPrintIdlePrattler()
        self._idle_prattling_event = None
        self._success_prattler = dmstl.OctoPrintSuccessPrattler(self._tweeter, self._scheduler)
        self._inoperable_prattler = dmstl.OctoPrintInoperablePrattler(self._tweeter, self._scheduler)
        self._paused_prattler = dmstl.OctoPrintPausedPrattler(self._tweeter, self._scheduler)
    def __enter__(self):
        self._frozen += 1
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        self._frozen -= 1
        self.update_if_not_frozen()
        return False
    def initialize(self):
        # rmv with self._tweeter:
        # self._tweeter.destroy_all()
        self._tweeter.update_status("Howdy doodly do. How's it going? I'm Prattle. Prattle Printer. Your chirpy printing companion. Prattle's the name. Printing's the game.")
        # self._tweeter.update_status("Anyone like any boaties?")
    def update_if_not_frozen(self):
        if self._frozen == 0:
            nsc = self._network_state_current
            nsp = self._network_state_previous
            dsc = self._device_state_current
            dsp = self._device_state_previous
            if nsc == NetworkState.OFFLINE:
                self._network_state_offline += 1
            else:
                if self._network_state_offline > 0:
                    line = "NetworkState.OFFLINE ({})".format(self._network_state_offline)
                    self._tweeter.update_status(line)
                    self._network_state_offline = 0
            if (nsc != nsp) or (dsc != dsp):
                self.stop_idle_prattling()
                self._inoperable_prattler.stop()
                self._paused_prattler.stop()
                if nsc == NetworkState.GOOD:
                    if dsc == DeviceState.BUSY:
                        self._do_prattle(self._get_busy_prattler)
                        # rmv self._tweeter.update_status("Oh happy day! Squeezing hot plastic through my extruder is such a good feeling!")
                    elif dsc == DeviceState.IDLE:
                        if dsp == DeviceState.BUSY:
                            self._do_prattle(self._success_prattler)
                            # rmv self._tweeter.update_status("Done! Another fine thing brought to you by your favourite Prattle Printer!")
                            # rmv self._tweeter.update_status("Would you like another one?")
                        self.start_idle_prattling()
                    elif dsc == DeviceState.PAUSED:
                        self._paused_prattler.start()
                        # rmv self._tweeter.update_status("DeviceState.PAUSED")
                    elif dsc == DeviceState.INOPERABLE:
                        self._inoperable_prattler.start()
                        # rmv self._tweeter.update_status("DeviceState.INOPERABLE")
                elif nsc == NetworkState.UNREACHABLE:
                    self._tweeter.update_status("NetworkState.UNREACHABLE")
                elif nsc == NetworkState.OFFLINE:
                    # self._tweeter.update_status("NetworkState.OFFLINE")
                    pass
                elif nsc == NetworkState.BAD_PASSWORD:
                    self._tweeter.update_status("NetworkState.BAD_PASSWORD")
                else:
                    pass # here! Walkabout?
                self._network_state_previous = nsc
                self._device_state_previous = dsc
    def update_network_state(self, new_state):
        self._network_state_current = new_state
        self.update_if_not_frozen()
    def update_device_state(self, new_state):
        self._device_state_current = new_state
        self.update_if_not_frozen()
    def start_idle_prattling(self):
        # fix? rmv? self.stop_idle_prattling()
        if self._idle_prattling_event is None:
            self._schedule_next_idle_prattle()
    def stop_idle_prattling(self):
        if self._idle_prattling_event is not None:
            try:
                self._scheduler.cancel(self._idle_prattling_event)
                self._idle_prattling_event = None
            except ValueError:
                pass
    def _do_prattle(self, prattler):
        prattle = prattler.get_next_prattle()
        for line in prattle:
            self._tweeter.update_status(line)
    def _schedule_next_idle_prattle(self):
        next_delay = self._idle_prattler.get_next_delay()
        self._idle_prattling_event = self._scheduler.enter(next_delay, 999, self._time_for_idle_prattle)
    def _time_for_idle_prattle(self):
        self._do_prattle(self._idle_prattler)
        #rmv prattle = self._idle_prattler.get_next_prattle()
        #rmv for line in prattle:
        #rmv     self._tweeter.update_status(line)
        self._schedule_next_idle_prattle()
    def shutdown(self):
        self.stop_idle_prattling()
        self._inoperable_prattler.stop()
        self._paused_prattler.stop()
        self._tweeter.terminate()

def get_leaf(dictionary, *args):
    current = dictionary
    for key in args:
        next = current.get(key)
        if next is None:
            return None
        current = next
    return current

class OctoPrintRawDataCruncher():
    def __init__(self, dbi, scheduler):
        super().__init__()
        if dbi is None:
            self._tcl = dmstl.TwitterCredentialsLoadFromMemory()
        else:
            self._tcl = dmstl.TwitterCredentialsLoadFromDatabase(dbi)
        # rmv self._dbi = dbi
        self._models = dict()
        self._scheduler = scheduler
        pub.subscribe(self.crunch_the_data, 'raw_data.octoprint')
    def crunch_the_data(self, sender, collected):
        model = self._models.get(sender.id, None)
        if model is None:
            twitter_credentials = self._tcl.get_credentials(sender.id)
            # rmv print(twitter_credentials)
            model = OctoPrintModel(sender.id, sender.name, twitter_credentials, self._scheduler)
            self._models[sender.id] = model
            model.initialize()
        with model:
            exception = collected._first_exception
            if exception is None:
                if collected._http_status == 401:
                    model.update_network_state(NetworkState.BAD_PASSWORD)
                else:
                    model.update_network_state(NetworkState.GOOD)
                    if collected._http_status == 200:
                        printer_state = get_leaf(collected._jsons, 'PRINTER', 'state', 'text')
                        progress_completion = get_leaf(collected._jsons, 'JOB', 'progress', 'completion')
                        # rmv print(progress_completion)
                        if printer_state == 'Operational':
                            model.update_device_state(DeviceState.IDLE)
                        elif printer_state == 'Printing':
                            model.update_device_state(DeviceState.BUSY)
                        elif printer_state == 'Paused':
                            model.update_device_state(DeviceState.PAUSED)
                        else:
                            model.update_device_state(DeviceState.INOPERABLE)
                    elif collected._http_status == 409:  # Conflict - printer is offline / not responding
                        model.update_device_state(DeviceState.INOPERABLE)
                    elif collected._http_status == 502:  # Bad Gateway - just ignore it
                        pass
                    else:
                        pass
            else:
                if (exception.__class__.__name__ == 'ConnectTimeout') or \
                        (exception.__class__.__name__ == 'ReadTimeout'):
                    model.update_network_state(NetworkState.OFFLINE)
                else:
                    model.update_network_state(NetworkState.UNREACHABLE)
    def shutdown(self):
        for model in self._models.values():
            model.shutdown()

