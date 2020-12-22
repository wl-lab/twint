import time
from asyncio import TimeoutError
from logging import Logger

import aiohttp

from .config import Config
from .errors import TokenExpiryException, AccessError
from .get import get_user_id, search, get_profile_feed
from .parser import NoMoreTweetsError, parse_tweets
from .token import TokenGetter
from .user_agents import get_random_user_agent

default_bearer_token = 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs' \
                       '%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA'


class TwintSearch:
    def __init__(self, logger: Logger, config: Config, token_getter: TokenGetter,
                 connector: aiohttp.TCPConnector = None, session=None, raise_access_error=True, proxy: str = None):
        self.logger = logger
        self.config = config
        if not config.BearerToken:
            config.BearerToken = default_bearer_token
        assert config.GuestToken
        self.token_getter = token_getter
        self.connector = connector
        self.session = session
        self.init = -1
        self.count = 0
        self.user_agent = ""
        self.raise_access_error = raise_access_error
        self.proxy = proxy

    async def get_feed(self, user_id_or_name: str, minimum: int, from_profile: bool) -> list:
        consecutive_errors_count = 0
        tweets = []
        if from_profile:
            query = get_profile_feed
        else:
            query = search
        while True:
            # noinspection PyBroadException
            try:
                response = await query(user_id_or_name, self.config, self.init, connector=self.connector,
                                       session=self.session, ua=self.user_agent, proxy=self.proxy)
            except TokenExpiryException:
                self.logger.debug('guest token expired, refreshing')
                self.config.GuestToken = self.token_getter.refresh()
                continue
            except TimeoutError:
                self.logger.exception('twitter request timed out')
                return tweets
            except Exception as e:
                if self.raise_access_error and isinstance(e, AccessError):
                    raise
                consecutive_errors_count += 1
                self.logger.exception('twitter request error. Username or id: %s, errors in row: %d, retries: %d',
                                      user_id_or_name, consecutive_errors_count, self.config.RetriesCount)
                if consecutive_errors_count < self.config.RetriesCount:
                    # skip to the next iteration if wait time does not satisfy limit constraints
                    delay = round(consecutive_errors_count ** self.config.BackoffExponent, 1)
                    # if the delay is less than users set min wait time then replace delay
                    if self.config.MinWaitTime > delay:
                        delay = self.config.MinWaitTime
                    self.logger.info('going to wait for %d', delay)
                    time.sleep(delay)
                    self.user_agent = get_random_user_agent(wa=True)
                    continue
                self.logger.info('twitter errors limit exceeded. Returning gathered tweets')
                return tweets
            try:
                parsed, self.init = parse_tweets(response)
                tweets.extend(parsed)
                if len(tweets) >= minimum:
                    return tweets
            except NoMoreTweetsError:
                return tweets
        return tweets

    async def get_tweets(self, username: str, minimum: int = 0):
        self.user_agent = get_random_user_agent(wa=True)
        if self.config.Profile:
            user_id = await get_user_id(username, self.config.BearerToken, self.config.GuestToken,
                                        connector=self.connector, session=self.session, proxy=self.proxy,
                                        timeout=self.config.AiohttpTimeout)
            if user_id is None:
                raise ValueError(f'Cannot find twitter account with name = {username}')
            return await self.get_feed(user_id, minimum, self.config.Profile)
        return await self.get_feed(username, minimum, self.config.Profile)
