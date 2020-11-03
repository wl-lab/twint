import time
from asyncio import get_event_loop, TimeoutError, new_event_loop, set_event_loop
from logging import Logger

from .feed import NoMoreTweetsException, parse_tweets
from .get import issue_search_request, get_random_user_agent, get_user_id
from .token import TokenExpiryException, TokenGetter

default_bearer_token = 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs' \
                       '%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA'


class TwintSearch:
    def __init__(self, logger: Logger, config, token_getter: TokenGetter):
        self.logger = logger
        self.config = config
        if not config.BearerToken:
            config.BearerToken = default_bearer_token
        assert config.GuestToken
        self.guest_token = config.GuestToken
        self.token_getter = token_getter
        self.init = -1
        self.feed = [-1]
        self.count = 0
        self.user_agent = ""

    async def get_feed(self, minimum: int) -> list:
        consecutive_errors_count = 0
        tweets = []
        while True:
            # this will receive a JSON string, parse it into a `dict` and do the required stuff
            try:
                response = await issue_search_request(self.config, self.init)
            except TokenExpiryException:
                self.logger.debug('guest token expired, refreshing')
                self.token_getter.refresh()
                response = await issue_search_request(self.config, self.init)
            try:
                try:
                    parsed, self.init = parse_tweets(response)
                    tweets.extend(parsed)
                    if len(tweets) >= minimum:
                        return tweets
                except NoMoreTweetsException:
                    return tweets
            except TimeoutError:
                # todo log
                return tweets
            except Exception:
                # todo log.critical(__name__ + ':Twint:Feed:noData' + str(e))
                consecutive_errors_count += 1
                if consecutive_errors_count < self.config.RetriesCount:
                    # skip to the next iteration if wait time does not satisfy limit constraints
                    delay = round(consecutive_errors_count ** self.config.BackoffExponent, 1)
                    # if the delay is less than users set min wait time then replace delay
                    if self.config.MinWaitTime > delay:
                        delay = self.config.MinWaitTime
                    time.sleep(delay)
                    self.user_agent = get_random_user_agent(wa=True)
                    continue
                return tweets
        return tweets

    async def get_tweets(self, minimum: int = 0):
        self.user_agent = get_random_user_agent(wa=True)
        self.config.UserId = await get_user_id(self.config.Username, self.config.BearerToken, self.config.GuestToken)
        if self.config.UserId is None:
            raise ValueError("Cannot find twitter account with name = " + self.config.Username)
        return await self.get_feed(minimum)


def run(config, token_getter: TokenGetter):
    try:
        get_event_loop()
    except RuntimeError as e:
        if "no current event loop" in str(e):
            set_event_loop(new_event_loop())
        else:
            raise

    get_event_loop().run_until_complete(TwintSearch(config, token_getter).get_tweets())
