from json import dumps
from urllib.parse import quote

import aiohttp
from aiohttp import ClientTimeout

from .config import Config
from .errors import TokenExpiryException, AccessError
from .url import search_url, profile_feed_url
from .user_agents import default_user_agent


def error_message(json: dict) -> str:
    return json['errors'][0]['message']


def dict_to_url(dct):
    """
    Function to convert python `dict` to json and then encode it to be passed in the url as a parameter.
    Some urls require this format
    """
    return quote(dumps(dct))


def create_headers(bearer: str, guest: str, ua: str) -> list:
    return [('authorization', bearer), ('x-guest-token', guest), ('User-Agent', ua)]


async def _issue_query(session, url: str, ssl: bool, params, proxy, timeout):
    async with session.get(url, ssl=ssl, params=params, proxy=proxy, timeout=timeout) as response:
        json = await response.json()
        if response.status == 429:  # 429 implies Too many requests i.e. Rate Limit Exceeded
            raise TokenExpiryException(error_message(json))
        if response.status == 403:  # Happens on multiple profile queries with one guest token
            raise AccessError(error_message(json))
        return json


async def request_json(url, connector=None, session=None, params=None, headers=None,
                       timeout=aiohttp.client.DEFAULT_TIMEOUT, proxy=None, trust_env=True) -> dict:
    """
    Shorthand for issuing async requests
    """
    if session:
        session.headers.update(headers)
        return await _issue_query(session, url, ssl=True, params=params, proxy=proxy, timeout=timeout)
    async with aiohttp.ClientSession(connector=connector, headers=headers, connector_owner=False,
                                     trust_env=trust_env) as ctx_session:
        return await _issue_query(ctx_session, url, ssl=True, params=params, proxy=proxy, timeout=timeout)


async def get_user_id(username, bearer_token, guest_token, connector: aiohttp.TCPConnector = None, session=None,
                      ua=default_user_agent, proxy: str = None, timeout=aiohttp.client.DEFAULT_TIMEOUT) -> str:
    """
    Query user ID by username
    """
    dct = {'screen_name': username, 'withHighlightedLabel': False}
    url = 'https://api.twitter.com/graphql/jMaTS-_Ea8vh9rpKggJbCQ/UserByScreenName?variables={}' \
        .format(dict_to_url(dct))
    headers = create_headers(bearer_token, guest_token, ua)

    response = await request_json(url, connector=connector, session=session, headers=headers, proxy=proxy,
                                  timeout=timeout)
    return response['data']['user']['rest_id']


async def search(username: str, config, init, connector: aiohttp.TCPConnector = None, session=None,
                 ua=default_user_agent, proxy: str = None) -> dict:
    """
    Composes search parameters and issues request.

    :param username:
    :param config: search configuration. config.TweetsPortionSize sets tweets count for query
    :param init: start index in tweet feed
    :param connector:
    :param session:
    :param ua: User-Agent header value
    :param proxy: proxy string

    :returns: JSON response as string
    """
    headers = create_headers(config.BearerToken, config.GuestToken, ua)
    search_params = search_url(username, config, init)

    return await request_json(search_params.url, params=search_params.params, connector=connector, session=session,
                              headers=headers, proxy=proxy, timeout=ClientTimeout(config.AiohttpTimeout))


async def get_profile_feed(user_id: str, config: Config, init, connector: aiohttp.TCPConnector = None, session=None,
                           ua=default_user_agent, proxy: str = None) -> dict:
    """
    Composes search (or feed) parameters and issues request.

    :param user_id:
    :param config: search configuration. config.TweetsPortionSize sets tweets count for query
    :param init: start index in tweet feed
    :param connector:
    :param session:
    :param ua: User-Agent header value
    :param proxy: proxy string

    :returns: JSON response as string
    """
    headers = create_headers(config.BearerToken, config.GuestToken, ua)
    search_params = profile_feed_url(user_id, config.TweetsPortionSize, init)

    return await request_json(search_params.url, params=search_params.params, connector=connector, session=session,
                              headers=headers, proxy=proxy, timeout=ClientTimeout(config.AiohttpTimeout))
