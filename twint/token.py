import re
import time
from typing import Callable

import requests


class TokenExpiryException(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class RefreshTokenException(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class TokenGetter:
    def __init__(self, *, session: requests.Session = None, timeout=10, retries=5,
                 sleep_timer: Callable[[int], int] = None):
        self._session = session or requests.Session()
        self.timeout = timeout
        self.retries = retries
        self.url = 'https://twitter.com'
        self.sleep_timer = sleep_timer or self._default_sleep_timer

    def _default_sleep_timer(self, attempt: int):
        return 2.0 * 2 ** attempt

    def _issue_request(self):
        for attempt in range(self.retries + 1):
            # The request is newly prepared on each retry because of potential cookie updates.
            req = self._session.prepare_request(requests.Request('GET', self.url))
            try:
                response = self._session.send(req, allow_redirects=True, timeout=self.timeout)
            except requests.exceptions.RequestException:
                pass
                # todo log.log(level, f'Error retrieving {req.url}: {exc!r}{retrying}')
            else:
                return response
            if attempt < self.retries:
                sleep_time = self.sleep_timer(attempt)
                time.sleep(sleep_time)
        else:
            msg = f'{self.retries + 1} requests to {self.url} failed, giving up.'
            raise RefreshTokenException(msg)

    def refresh(self) -> str:
        response = self._issue_request()
        match = re.search(r'\("gt=(\d+);', response.text)
        if match:
            return str(match.group(1))
        else:
            raise RefreshTokenException('Could not find the Guest token in HTML')
