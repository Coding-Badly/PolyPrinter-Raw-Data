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

# cls
# cd "C:\ProjectsSplit\Make\PolyPrinter Raw Data\"
# "C:\Python36\python" dmstl_main.py

import dmstl
import time

def do_it():
    rdc = None
    cru = None
    try:
        scheduler = dmstl.ToolLogsScheduler()
        dbi = None  # dbi = dmstl.DatabaseInterface()
        # rs = dmstl.RedundantStrings(dbi)
        # rdl = dmstl.OctoPrintRawDataLogger(dbi, rs)
        cru = dmstl.OctoPrintRawDataCruncher(dbi, scheduler)
        rdc = dmstl.OctoPrintRawDataCollectors(dbi)
        scheduler.every(5, 100, rdc.get_fresh_data)
        scheduler.run()
    except (SystemExit, KeyboardInterrupt):
        if rdc is not None:
            rdc.shutdown()
        if cru is not None:
            cru.shutdown()
        raise

def wrap_do_it():
    while True:
        logger = dmstl.get_logger(__name__)
        try:
            do_it()
        except (SystemExit, KeyboardInterrupt):
            break
        except Exception as exc:
            logger.error(
                    'Unexpected exception: {0}'.format(exc.__class__.__name__),
                    exc_info=True)
            time.sleep(5.0)

if __name__ == '__main__':
    wrap_do_it()


