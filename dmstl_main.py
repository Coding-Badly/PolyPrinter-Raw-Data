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


