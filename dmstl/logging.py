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

# cd "C:\ProjectsSplit\Make\PolyPrinter Raw Data"
# grep -d "\.info[ ]*\(" *
# grep -d "\.warn[ ]*\(" *
# grep -d "\.warning[ ]*\(" *
# grep -d "\.error[ ]*\(" *
# grep -d "\.critical[ ]*\(" *
# grep -d "\.exception[ ]*\(" *
# grep -d "\.log[ ]*\(" *

# try:
#     open('/path/to/does/not/exist', 'rb')
# except (SystemExit, KeyboardInterrupt):
#     raise
# except Exception, e:
#     logger.error('Failed to open file', exc_info=True)
#
# You can also call logger.exception(msg, *args), it equals to logger.error(msg, exc_info=True, *args).


import logging

def prepare_root_logger():
    l1 = logging.getLogger()
    # Set logging for all of this application to the least restrictive filter.
    # Each subsystem can decide for itself what to do.
    l1.setLevel(logging.NOTSET)  # rmv l1.setLevel(logging.WARNING)
    # Set some of the packages to warning
    for name in ('oauthlib', 'requests', 'requests_oauthlib', 'tweepy'):
        logging.getLogger(name).setLevel(logging.WARNING)
    # Use the default Formatter from logging.basicConfig.
    fmt = logging.Formatter(
            fmt = '%(asctime)s %(levelname)-5.5s %(name)s %(message)s',  # fix fmt = '%(asctime)s %(levelname)-5.5s %(name)-12.12s %(message)s',
            datefmt = '%Y-%m-%d %H:%M:%S')
    # Output to stderr
    h = logging.StreamHandler()
    h.setFormatter(fmt)
    l1.addHandler(h)
    # Output to a file
    h = logging.FileHandler('RawDataLogger.log')
    h.setFormatter(fmt)
    l1.addHandler(h)

prepare_root_logger()

def get_logger(name):
    return logging.getLogger(name)


