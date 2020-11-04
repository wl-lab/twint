from json import dumps
from urllib.parse import quote

import aiohttp

from .config import Config
from .errors import TokenExpiryException, AccessError
from .url import search_url, profile_feed_url


def dict_to_url(dct):
    """
    Function to convert python `dict` to json and then encode it to be passed in the url as a parameter.
    Some urls require this format
    """
    return quote(dumps(dct))


async def request_json(url, connector=None, params=None, headers=None, timeout=aiohttp.client.DEFAULT_TIMEOUT,
                       proxy=None) -> dict:
    """
    Shorthand for issuing async requests
    """
    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        async with session.get(url, ssl=True, params=params, proxy=proxy, timeout=timeout) as response:
            json = await response.json()
            if response.status == 429:  # 429 implies Too many requests i.e. Rate Limit Exceeded
                raise TokenExpiryException(json['errors'][0]['message'])
            if response.status == 403:
                raise AccessError(json['errors'][0]['message'])
            return json


async def get_user_id(username, bearer_token, guest_token) -> str:
    """
    Query user ID by username
    """
    dct = {'screen_name': username, 'withHighlightedLabel': False}
    url = 'https://api.twitter.com/graphql/jMaTS-_Ea8vh9rpKggJbCQ/UserByScreenName?variables={}' \
        .format(dict_to_url(dct))
    headers = {
        'authorization': bearer_token,
        'x-guest-token': guest_token,
    }

    response = await request_json(url, headers=headers)
    return response['data']['user']['rest_id']


async def search(username: str, config, init, connector: aiohttp.TCPConnector = None) -> dict:
    """
    Composes search (or feed) parameters and issues request.

    :param username:
    :param config: search configuration. config.TweetsPortionSize sets tweets count for query
    :param init: start index in tweet feed
    :param connector:

    :returns: JSON response as string
    """
    headers = [("authorization", config.BearerToken), ("x-guest-token", config.GuestToken)]
    search_params = search_url(username, config, init)

    return await request_json(search_params.url, params=search_params.params, connector=connector, headers=headers)


async def get_profile_feed(user_id: str, config: Config, init, connector: aiohttp.TCPConnector = None) -> dict:
    """
    Composes search (or feed) parameters and issues request.

    :param user_id:
    :param config: search configuration. config.TweetsPortionSize sets tweets count for query
    :param init: start index in tweet feed
    :param connector:

    :returns: JSON response as string
    """
    headers = [("authorization", config.BearerToken), ("x-guest-token", config.GuestToken)]
    search_params = profile_feed_url(user_id, config.TweetsPortionSize, init)

    return await request_json(search_params.url, params=search_params.params, connector=connector, headers=headers)
