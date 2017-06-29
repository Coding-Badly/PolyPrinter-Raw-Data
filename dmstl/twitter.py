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
from dmstl.uniquifier import Uniquifier
# rmv  import logging
import queue
import threading
import tweepy

def tidy_tweet_text(text, *args):
    text = text.lstrip()
    suffix = ''
    for arg in args:
        if len(suffix) + len(arg) > 140:
            break
        suffix += arg
    suffix = suffix.rstrip()
    if len(text) + len(suffix) <= 140:
        rv = text + suffix
    else:
        rv = text[:140-len(suffix)] + suffix
    return rv.strip()

class TwitterCredentials():
    def __init__(self, row):
        super().__init__()
        self.consumer_key = row[0]
        self.consumer_key_secret = row[1]
        self.access_token = row[2]
        self.access_token_secret = row[3]

class TwitterThreadWork():
    def __init__(self):
        super().__init__()
    def do_work(self, thread):
        pass

class TwitterThreadDestroyAll(TwitterThreadWork):
    def __str__(self):
        return 'destroy all tweets'
    def do_work(self, thread):
        thread._destroy_all()

class TwitterThreadUpdateStatus(TwitterThreadWork):
    def __init__(self, text, make_unique):
        super().__init__()
        self._text = tidy_tweet_text(text)
        self._make_unique = make_unique
    def __str__(self):
        return 'update status to "%s"' % self._text
    def do_work(self, thread):
        thread._update_status(self._text, self._make_unique)

class TwitterThread(threading.Thread):
    def __init__(self, name, credentials):
        super().__init__(name=name)
        self._api = None
        self._credentials = credentials
        self._logger = dmstl.get_logger(name)
        # rmv  self._logger.setLevel(logging.DEBUG)
        self._queue = queue.Queue()
        self._terminated = False
        self._uniquifier = Uniquifier()
        self.start()
    def add_work(self, work):
        self._queue.put_nowait(work)
    def run(self):
        logger = self._logger
        try:
            queue = self._queue
            while True:
                item = queue.get()
                if item is None:
                    break
                attempts_remaining = 2
                while attempts_remaining > 0:
                    try:
                        attempts_remaining -= 1
                        item.do_work(self)
                        queue.task_done()
                        attempts_remaining = 0
                    except Exception as exc:
                        logger.error( 'Failure trying to %s.', str(item), exc_info=True)
        except Exception as exc:
            logger.critical( 'TwitterThread stopped.', exc_info=True)
        self._terminated = True
    def terminate(self):
        self._terminated = True
        self._queue.put(None)
    def destroy_all(self):
        assert not self._terminated
        self.add_work(TwitterThreadDestroyAll())
    def update_status(self, text, make_unique=False):
        assert not self._terminated
        self.add_work(TwitterThreadUpdateStatus(text, make_unique))
    def _prepare_api(self):
        if self._api is None:
            credentials = self._credentials
            handler = tweepy.OAuthHandler(credentials.consumer_key, credentials.consumer_key_secret)
            handler.set_access_token(credentials.access_token, credentials.access_token_secret)
            self._api = tweepy.API(handler)
        return self._api
    def _destroy_all(self):
        api = self._prepare_api()
        for status in tweepy.Cursor(api.user_timeline).items():
            api.destroy_status(status.id)
    def _update_status(self, text, make_unique):
        api = self._prepare_api()
        logger = self._logger
        attempts_remaining = 2
        first_destroy_all = False
        truncated = False
        tweet_this = text
        while attempts_remaining > 0:
            try:
                attempts_remaining -= 1
                if first_destroy_all:
                    # rmv  logger.debug('destroying: "%s"', tweet_this)
                    for status in tweepy.Cursor(api.user_timeline).items():
                        # rmv  logger.debug('test: "%s"', status.text)
                        if tweet_this == status.text:
                            # rmv  logger.debug('destroyed: "%s"', tweet_this)
                            api.destroy_status(status.id)
                            break
                status = api.update_status(tweet_this)
                attempts_remaining = 0
            except tweepy.error.TweepError as exc:
                if exc.api_code == 187:  # Duplicate
                    # rmv  logger.debug('exc.api_code == 187')
                    if make_unique:
                        tweet_this = tidy_tweet_text(text, ' ' + self._uniquifier.next())
                        # make_unique = False
                        attempts_remaining += 1
                    else:
                        first_destroy_all = True
                else:
                    raise

class TwitterNull():
    def __init__(self):
        pass
    def add_work(self, work):
        pass
    def terminate(self):
        pass
    def destroy_all(self):
        pass
    def update_status(self, text):
        pass


