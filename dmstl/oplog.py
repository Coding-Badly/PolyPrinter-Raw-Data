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
from pubsub import pub
from .dbc import *

class OctoPrintRawDataMaps(dmstl.JsonValueToDatabaseFieldMaps):
    def __init__(self, redundant_strings):
        super().__init__('RAW_DATA')
        self._printer_id_map = self.add(dmstl.PrinterIdFieldMap())
        self._observed_map = self.add(dmstl.ObservedFieldMap())
        self._http_status_map = self.add(dmstl.HttpStatusFieldMap())
        self._http_message_map = self.add(dmstl.HttpMessageFieldMap(redundant_strings))
        self._exception_map = self.add(dmstl.ExceptionFieldMap(redundant_strings))
        self.add(dmstl.JsonValueToBooleanFieldMap('PRINTER_SD_READY'))
        self.add(dmstl.JsonValueToBooleanFieldMap('PRINTER_STATE_FLAGS_CLOSEDORERROR'))
        self.add(dmstl.JsonValueToBooleanFieldMap('PRINTER_STATE_FLAGS_ERROR'))
        self.add(dmstl.JsonValueToBooleanFieldMap('PRINTER_STATE_FLAGS_OPERATIONAL'))
        self.add(dmstl.JsonValueToBooleanFieldMap('PRINTER_STATE_FLAGS_PAUSED'))
        self.add(dmstl.JsonValueToBooleanFieldMap('PRINTER_STATE_FLAGS_PRINTING'))
        self.add(dmstl.JsonValueToBooleanFieldMap('PRINTER_STATE_FLAGS_READY'))
        self.add(dmstl.JsonValueToBooleanFieldMap('PRINTER_STATE_FLAGS_SDREADY'))
        self.add(dmstl.JsonValueToStringIdFieldMap('PRINTER_STATE_TEXT', redundant_strings))
        self.add(dmstl.JsonValueToFloatFieldMap('PRINTER_TEMPERATURE_BED_ACTUAL'))
        self.add(dmstl.JsonValueToFloatFieldMap('PRINTER_TEMPERATURE_BED_OFFSET'))
        self.add(dmstl.JsonValueToFloatFieldMap('PRINTER_TEMPERATURE_BED_TARGET'))
        self.add(dmstl.JsonValueToFloatFieldMap('PRINTER_TEMPERATURE_TOOL0_ACTUAL'))
        self.add(dmstl.JsonValueToFloatFieldMap('PRINTER_TEMPERATURE_TOOL0_OFFSET'))
        self.add(dmstl.JsonValueToFloatFieldMap('PRINTER_TEMPERATURE_TOOL0_TARGET'))
        self.add(dmstl.JsonValueToFloatFieldMap('JOB_JOB_AVERAGEPRINTTIME'))
        self.add(dmstl.JsonValueToFloatFieldMap('JOB_JOB_ESTIMATEDPRINTTIME'))
        self.add(dmstl.JsonValueToFloatFieldMap('JOB_JOB_FILAMENT_TOOL0_LENGTH'))
        self.add(dmstl.JsonValueToFloatFieldMap('JOB_JOB_FILAMENT_TOOL0_VOLUME'))
        self.add(dmstl.JsonValueToIntFieldMap('JOB_JOB_FILE_DATE'))
        self.add(dmstl.JsonValueToStringIdFieldMap('JOB_JOB_FILE_NAME', redundant_strings))
        self.add(dmstl.JsonValueToStringIdFieldMap('JOB_JOB_FILE_ORIGIN', redundant_strings))
        self.add(dmstl.JsonValueToStringIdFieldMap('JOB_JOB_FILE_PATH', redundant_strings))
        self.add(dmstl.JsonValueToIntFieldMap('JOB_JOB_FILE_SIZE'))
        self.add(dmstl.JsonValueToFloatFieldMap('JOB_JOB_LASTPRINTTIME'))
        self.add(dmstl.JsonValueToFloatFieldMap('JOB_PROGRESS_COMPLETION'))
        self.add(dmstl.JsonValueToIntFieldMap('JOB_PROGRESS_FILEPOS'))
        self.add(dmstl.JsonValueToIntFieldMap('JOB_PROGRESS_PRINTTIME'))
        self.add(dmstl.JsonValueToIntFieldMap('JOB_PROGRESS_PRINTTIMELEFT'))
        self.add(dmstl.JsonValueToStringIdFieldMap('JOB_PROGRESS_PRINTTIMELEFTORIGIN', redundant_strings))
        self.add(dmstl.JsonValueToStringIdFieldMap('JOB_STATE', redundant_strings))
    def set_printer_id(self, printer_id):
        self._printer_id_map.id = printer_id
    def set_exception(self, exception):
        if exception is not None:
            self._exception_map.class_name = exception.__class__.__name__
            return True
        else:
            return False
    def set_http_status(self, http_status, http_message):
        if http_status is not None:
            self._http_status_map.status = http_status
            self._http_message_map.message = http_message
            if http_status == 200:
                return False
            return True
        else:
            return False

class OctoPrintDeadbandCheckers(DeadbandCheckers):
    def __init__(self, maps):
        super().__init__(maps)
        self.add_checker('', DeadbandCheckerDoOnce() )
        self.add_checker('PRINTERID', DeadbandChecker() )
        self.add_checker('OBSERVED', DeadbandCheckerAlwaysDead() )
        self.add_checker('HTTP_STATUS', DeadbandChecker() )
        self.add_checker('JOB_PROGRESS_COMPLETION', DeadbandCheckerForPercent() )
        self.add_checker('JOB_PROGRESS_FILEPOS', DeadbandCheckerAlwaysDead() )
        self.add_checker('JOB_PROGRESS_PRINTTIME', DeadbandCheckerAlwaysDead() )
        self.add_checker('JOB_PROGRESS_PRINTTIMELEFT', DeadbandCheckerAlwaysDead() )
        self.add_checker('PRINTER_TEMPERATURE_BED_ACTUAL', DeadbandCheckerAlwaysDead() )
        self.add_checker('PRINTER_TEMPERATURE_TOOL0_ACTUAL', DeadbandCheckerAlwaysDead() )

class OctoPrintRawDataLogger:
    def __init__(self, database_interface, redundant_strings):
        super().__init__()
        self._dbi = database_interface
        self._rs = redundant_strings
        self._maps = OctoPrintRawDataMaps(self._rs)
        self._dbcs = dict()
        self._sql = None
        pub.subscribe(self.map_then_log, 'raw_data.octoprint')
    def map_then_log(self, sender, collected):
        # Map the raw data to database fields
        maps = self._maps
        dbcs = self._dbcs.get(sender.id, None)
        if dbcs is None:
            dbcs = OctoPrintDeadbandCheckers(maps)
            self._dbcs[sender.id] = dbcs
        maps.reset()
        maps.set_printer_id(sender.id)
        got_json = True
        if maps.set_exception(collected._first_exception):
            got_json = False
        if maps.set_http_status(collected._http_status, collected._http_message):
            # rmv got_json = False
            pass
        if got_json:
            for prefix, json in collected._jsons.items():
                maps.update(prefix, json)
        if dbcs.alive():
            values = maps.generate_value_tuple()
            if self._sql is None:
                self._sql = maps.generate_insert()
            self._dbi.execute(self._sql, values, True)
            self._dbi.commit()
            dbcs.commit()

