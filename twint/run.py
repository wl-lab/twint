import logging as logme
import time
from asyncio import get_event_loop, TimeoutError, new_event_loop, set_event_loop

from . import feed, get
from . import token
from .feed import NoMoreTweetsException
from .token import TokenExpiryException

bearer = 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs' \
         '%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA'


class TwintSearch:
    def __init__(self, config):
        logme.debug(__name__ + ':Twint:__init__')
        self.config = config
        self.init = -1
        config.deleted = []
        self.feed: list = [-1]
        self.count = 0
        self.user_agent = ""
        self.config.BearerToken = bearer
        # TODO might have to make some adjustments for it to work with multi-treading
        # USAGE : to get a new guest token simply do `self.token.refresh()`
        self.token = token.Token(config)
        self.token.refresh()

    async def get_feed(self):
        consecutive_errors_count = 0
        while True:
            # this will receive a JSON string, parse it into a `dict` and do the required stuff
            try:
                response = await get.issue_search_request(self.config, self.init)
            except TokenExpiryException as e:
                # todo: log
                self.token.refresh()
                response = await get.issue_search_request(self.config, self.init)
            self.feed = []
            try:
                try:
                    self.feed, self.init = feed.parse_tweets(self.config, response)
                except NoMoreTweetsException as e:
                    break
            except TimeoutError as e:
                # todo log
                break
            except Exception as e:
                # todo logme.critical(__name__ + ':Twint:Feed:noData' + str(e))
                consecutive_errors_count += 1
                if consecutive_errors_count < self.config.RetriesCount:
                    # skip to the next iteration if wait time does not satisfy limit constraints
                    delay = round(consecutive_errors_count ** self.config.BackoffExponent, 1)
                    # if the delay is less than users set min wait time then replace delay
                    if self.config.MinWaitTime > delay:
                        delay = self.config.MinWaitTime
                    time.sleep(delay)
                    self.user_agent = get.get_random_user_agent(wa=True)
                    continue
                break

    async def run(self):
        self.user_agent = get.get_random_user_agent(wa=True)

        self.config.UserId = await get.get_user_id(self.config.Username, self.config.BearerToken,
                                                   self.config.GuestToken)
        if self.config.UserId is None:
            raise ValueError("Cannot find twitter account with name = " + self.config.Username)
        while True:
            if len(self.feed) > 0:
                logme.debug(__name__ + ':Twint:main:twitter-search')
                await self.get_feed()


def run(config):
    logme.debug(__name__ + ':run')
    try:
        get_event_loop()
    except RuntimeError as e:
        if "no current event loop" in str(e):
            set_event_loop(new_event_loop())
        else:
            logme.exception(__name__ + ':run:Unexpected exception while handling an expected RuntimeError.')
            raise
    except Exception as e:
        logme.exception(
            __name__ + ':run:Unexpected exception occurred while attempting to get or create a new event loop.')
        raise

    get_event_loop().run_until_complete(TwintSearch(config).run())
