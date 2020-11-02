import re
import time
from typing import Callable

import requests
import logging as logme


class TokenExpiryException(Exception):
    def __init__(self, msg):
        super().__init__(msg)

        
class RefreshTokenException(Exception):
    def __init__(self, msg):
        super().__init__(msg)
        

class Token:
    def __init__(self, config):
        self._session = requests.Session()
        self.config = config
        self._retries = 5
        self._timeout = 10
        self.url = 'https://twitter.com'

    def _request(self):
        for attempt in range(self._retries + 1):
            # The request is newly prepared on each retry because of potential cookie updates.
            req = self._session.prepare_request(requests.Request('GET', self.url))
            logme.debug(f'Retrieving {req.url}')
            try:
                r = self._session.send(req, allow_redirects=True, timeout=self._timeout)
            except requests.exceptions.RequestException as exc:
                if attempt < self._retries:
                    retrying = ', retrying'
                    level = logme.WARNING
                else:
                    retrying = ''
                    level = logme.ERROR
                logme.log(level, f'Error retrieving {req.url}: {exc!r}{retrying}')
            else:
                success, msg = (True, None)
                msg = f': {msg}' if msg else ''

                if success:
                    logme.debug(f'{req.url} retrieved successfully{msg}')
                    return r
            if attempt < self._retries:
                # TODO : might wanna tweak this back-off timer
                sleep_time = 2.0 * 2 ** attempt
                logme.info(f'Waiting {sleep_time:.0f} seconds')
                time.sleep(sleep_time)
        else:
            msg = f'{self._retries + 1} requests to {self.url} failed, giving up.'
            logme.fatal(msg)
            self.config.GuestToken = None
            raise RefreshTokenException(msg)

    def refresh(self):
        logme.debug('Retrieving guest token')
        res = self._request()
        match = re.search(r'\("gt=(\d+);', res.text)
        if match:
            logme.debug('Found guest token in HTML')
            self.config.GuestToken = str(match.group(1))
        else:
            self.config.GuestToken = None
            raise RefreshTokenException('Could not find the Guest token in HTML')


class TokenGetter:
    def __init__(self, *, session: requests.Session = None, timeout=10, retries=5,
                 sleep_timer: Callable[[int], int] = None):
        self._session = session or requests.Session()
        self.sleep_timer = sleep_timer or self._default_sleep_timer
        self._retries = retries
        self._timeout = timeout
        self.url = 'https://twitter.com'

    def _default_sleep_timer(self, attempt: int):
        return 2.0 * 2 ** attempt

    def _issue_request(self):
        for attempt in range(self._retries + 1):
            # The request is newly prepared on each retry because of potential cookie updates.
            req = self._session.prepare_request(requests.Request('GET', self.url))
            try:
                r = self._session.send(req, allow_redirects=True, timeout=self._timeout)
            except requests.exceptions.RequestException:
                pass
                # todo logme.log(level, f'Error retrieving {req.url}: {exc!r}{retrying}')
            else:
                return r
            if attempt < self._retries:
                sleep_time = self.sleep_timer(attempt)
                time.sleep(sleep_time)
        else:
            msg = f'{self._retries + 1} requests to {self.url} failed, giving up.'
            raise RefreshTokenException(msg)

    def refresh(self) -> str:
        response = self._issue_request()
        match = re.search(r'\("gt=(\d+);', response.text)
        if match:
            return str(match.group(1))
        else:
            raise RefreshTokenException('Could not find the Guest token in HTML')
