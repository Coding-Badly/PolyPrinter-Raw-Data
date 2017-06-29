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

from .insulation import PrintersLoadFromMemory
from .logging import get_logger
from .raw import *
from pubsub import pub
import requests
import sys

class OctoPrintRawDataCollected(RawDataCollected):
    def __init__(self):
        super().__init__()
        self._logger = get_logger(__name__)
        self.reset()
    def reset(self):
        super().reset()
        self._requests = dict()
        self._jsons = dict()
        self._http_status = None
        self._http_message = None
        self._first_exception = None
        self._exceptions = dict()
    def set_exception(self, prefix, exception):
        if self._first_exception is None:
            self._first_exception = exception
        self._exceptions[prefix] = exception
        self._logger.warning(
                'An exception occurred trying to collected raw data: {0}'.
                format(exception.__class__.__name__))
    def set_request(self, prefix, request):
        self._requests[prefix] = request
        if request.status_code == 200:
            self._jsons[prefix] = request.json()
            if self._http_status is None:
                self._http_status = request.status_code
        else:
            if (self._http_status is None) or (self._http_status == 200):
                self._http_status = request.status_code
                if request.status_code == 409:
                    self._http_message = request.text

class OctoPrintRawDataCollectorConfiguration(RawDataCollectorConfiguration):
    def __init__(self, row):
        super().__init__()
        self._id = row[0]
        self._name = row[1]
        self._ip_address = row[2]
        self._api_key = row[3]
        self._active = row[4]
    def __repr__(self):
        row = (self._id, self._name, self._ip_address, self._api_key, self._active)
        return "%s(%s)" \
            % ( self.__class__.__name__, repr(row) )
    @property
    def api_key(self):
        return self._api_key
    @property
    def id(self):
        return self._id
    @property
    def ip_address(self):
        return self._ip_address
    @property
    def active(self):
        return (self._active) and (self._api_key is not None) and (self._ip_address is not None)
    @property
    def name(self):
        return self._name

class OctoPrintRequestDetails:
    def __init__(self, verb, prefix):
        super().__init__()
        self.verb = verb
        self.prefix = prefix

class OctoPrintRawDataCollector(RawDataCollector):
    REQUEST_DETAILS = [
            OctoPrintRequestDetails('printer', 'PRINTER'),
            OctoPrintRequestDetails('job', 'JOB') ]
    def __init__(self, configuration):
        super().__init__()
        self._configuration = configuration
        self._logger = get_logger(__name__)
    def get_fresh_data(self, collected=None):
        if collected is None:
            collected = OctoPrintRawDataCollected()
        collected.reset()
        c1 = self._configuration
        if self.active and c1.active:
            headers = {
                    'User-Agent': 'Raw Data Logger/1',
                    'X-Api-Key': c1.api_key,
                    'Content-Type': 'application/json' }
            for detail in OctoPrintRawDataCollector.REQUEST_DETAILS:
                url = "http://%s/api/%s" % ( c1.ip_address, detail.verb )
                try:
                    collected.set_request(detail.prefix, requests.get(url, headers=headers, timeout=0.5) )
                except: #  requests.exceptions.ConnectTimeout as exception:
                    exception = sys.exc_info()[1]
                    collected.set_exception(detail.prefix, exception)
        else:
            collected.active = False
        pub.sendMessage('raw_data.octoprint', sender=self, collected=collected)
        return collected
    @property
    def id(self):
        return self._configuration.id
    @property
    def name(self):
        return self._configuration.name
    def shutdown(self):
        super().shutdown()

class OctoPrintRawDataCollectors(RawDataCollectors):
    SqlSelectPrinters = """
select
  P.PRINTERID,
  P.PRINTERNAME,
  P.IPADDRESS,
  P.APIKEY,
  P.ISACTIVE
from
  PRINTERS P
order by
  P.PRINTERID
"""
    def _create_collector_from_row(self, row):
        configuration = OctoPrintRawDataCollectorConfiguration(row)
        collector = OctoPrintRawDataCollector(configuration)
        return collector
    def _get_sql(self):
        return OctoPrintRawDataCollectors.SqlSelectPrinters
    def _load_collectors_from_memory(self, method):
        loader = PrintersLoadFromMemory()
        loader._load_collectors_from_memory(method)
    def get_fresh_data(self):
        for c1 in self:
            if c1.active:
                c1.get_fresh_data()
    def shutdown(self):
        super().shutdown()

