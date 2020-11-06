import time
from logging import Logger
from typing import Callable

import requests

from twint.parser import find_guest_token, TokenNotFoundError


class TokenGetter:
    def __init__(self, logger: Logger, *, session: requests.Session = None, timeout=10, retries=5,
                 sleep_timer: Callable[[int], int] = None, url='https://twitter.com'):
        self.logger = logger
        self.session = session or requests.Session()
        self.timeout = timeout
        self.retries = retries
        self.sleep_timer = sleep_timer or _default_sleep_timer
        self.url = url

    def query_page(self) -> requests.Response:
        for attempt in range(self.retries + 1):
            # The request is newly prepared on each retry because of potential cookie updates.
            try:
                response = self.session.get(self.url, timeout=self.timeout)
            except requests.exceptions.RequestException:
                self.logger.warning('error retrieving %s, retrying', self.url)
                pass
            else:
                return response
            if attempt < self.retries:
                sleep_time = self.sleep_timer(attempt)
                time.sleep(sleep_time)
        else:
            msg = f'{self.retries + 1} requests to {self.url} failed, giving up.'
            self.logger.error('error quering twitter guest token: %s', msg)
            raise TokenNotFoundError(msg)

    def refresh(self) -> str:
        response = self.query_page()
        return find_guest_token(response.text)


def _default_sleep_timer(attempt: int):
    return 2.0 * 2 ** attempt
