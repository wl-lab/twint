from async_timeout import timeout
import sys
import aiohttp
from fake_useragent import UserAgent
import random
from json import loads, dumps
from aiohttp_socks import ProxyConnector, ProxyType
from urllib.parse import quote

# from . import url
from .token import TokenExpiryException

import logging as logme

from .url import search, search_profile

httpproxy = None
default_user_agent = "Mozilla/5.0 (Windows NT 6.4; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2225.0 Safari/537.36"

user_agent_list = [
    # 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
    # ' Chrome/60.0.3112.113 Safari/537.36',
    # 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
    # ' Chrome/60.0.3112.90 Safari/537.36',
    # 'Mozilla/5.0 (Windows NT 5.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
    # ' Chrome/60.0.3112.90 Safari/537.36',
    # 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
    # ' Chrome/60.0.3112.90 Safari/537.36',
    # 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)'
    # ' Chrome/44.0.2403.157 Safari/537.36',
    # 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
    # ' Chrome/60.0.3112.113 Safari/537.36',
    # 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
    # ' Chrome/57.0.2987.133 Safari/537.36',
    # 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
    # ' Chrome/57.0.2987.133 Safari/537.36',
    # 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
    # ' Chrome/55.0.2883.87 Safari/537.36',
    # 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
    # ' Chrome/55.0.2883.87 Safari/537.36',

    'Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)',
    'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (Windows NT 6.2; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0)',
    'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)',
    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET '
    'CLR 3.5.30729)',
]


# function to convert python `dict` to json and then encode it to be passed in the url as a parameter
# some urls require this format
def dict_to_url(dct):
    return quote(dumps(dct))


async def issue(session: aiohttp.ClientSession, _url, params=None, proxy=None):
    with timeout(120):  # todo: aiohttp has own timeout
        async with session.get(_url, ssl=True, params=params, proxy=proxy) as response:
            text = await response.text()
            if response.status == 429:  # 429 implies Too many requests i.e. Rate Limit Exceeded
                raise TokenExpiryException(loads(text)['errors'][0]['message'])
            return text


async def req(url, connector=None, params=None, headers=None):
    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        return await issue(session, url, params)


async def get_user_id(username, bearer_token, guest_token) -> str:
    _dct = {'screen_name': username, 'withHighlightedLabel': False}
    url = 'https://api.twitter.com/graphql/jMaTS-_Ea8vh9rpKggJbCQ/UserByScreenName?variables={}'\
        .format(dict_to_url(_dct))
    _headers = {
        'authorization': bearer_token,
        'x-guest-token': guest_token,
    }
    response = await req(url, headers=_headers)
    content = loads(response)
    return content['data']['user']['rest_id']


def get_random_user_agent(wa=None) -> str:
    try:
        if wa:
            return default_user_agent
        return UserAgent(verify_ssl=False, use_cache_server=False).random
    except:
        return random.choice(user_agent_list)


def get_connector(config):
    _connector = None
    if config.ProxyHost:
        if config.ProxyHost.lower() == "tor":
            _connector = ProxyConnector(
                host='127.0.0.1',
                port=9050,
                rdns=True)
        elif config.ProxyPort and config.ProxyType:
            if config.ProxyType.lower() == "socks5":
                _type = ProxyType.SOCKS5
            elif config.ProxyType.lower() == "socks4":
                _type = ProxyType.SOCKS4
            elif config.ProxyType.lower() == "http":
                global httpproxy
                httpproxy = "http://" + config.ProxyHost + ":" + str(config.ProxyPort)
                return _connector
            else:
                logme.critical("get_connector:proxy-type-error")
                print("Error: Proxy types allowed are: http, socks5 and socks4. No https.")
                sys.exit(1)
            _connector = ProxyConnector(
                proxy_type=_type,
                host=config.ProxyHost,
                port=config.ProxyPort,
                rdns=True)
        else:
            logme.critical(__name__ + ':get_connector:proxy-port-type-error')
            print("Error: Please specify --proxy-host, --proxy-port, and --proxy-type")
            sys.exit(1)
    else:
        if config.ProxyPort or config.ProxyType:
            logme.critical(__name__ + ':get_connector:proxy-host-arg-error')
            print("Error: Please specify --proxy-host, --proxy-port, and --proxy-type")
            sys.exit(1)

    return _connector


async def issue_search_request(config, init):
    _connector = get_connector(config)
    _headers = [("authorization", config.BearerToken), ("x-guest-token", config.GuestToken)]

    search_func = search
    if config.Profile:
        search_func = search_profile

    _url, params, _serialQuery = await search_func(config, init)

    return await req(_url, params=params, connector=_connector, headers=_headers)
