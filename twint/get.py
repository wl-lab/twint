import random
from json import loads, dumps
from urllib.parse import quote

import aiohttp
from async_timeout import timeout
from fake_useragent import UserAgent

from .token import TokenExpiryException
from .url import common_search, profile_search

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
    with timeout(120):  # TODO: aiohttp has own timeout
        async with session.get(_url, ssl=True, params=params, proxy=proxy) as response:
            text = await response.text()
            if response.status == 429:  # 429 implies Too many requests i.e. Rate Limit Exceeded
                raise TokenExpiryException(loads(text)['errors'][0]['message'])
            return text


async def request(url, connector=None, params=None, headers=None):
    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        return await issue(session, url, params)


async def get_user_id(username, bearer_token, guest_token) -> str:
    dct = {'screen_name': username, 'withHighlightedLabel': False}
    url = 'https://api.twitter.com/graphql/jMaTS-_Ea8vh9rpKggJbCQ/UserByScreenName?variables={}' \
        .format(dict_to_url(dct))
    headers = {
        'authorization': bearer_token,
        'x-guest-token': guest_token,
    }
    response = await request(url, headers=headers)
    content = loads(response)
    return content['data']['user']['rest_id']


def get_random_user_agent(wa=None) -> str:
    try:
        if wa:
            return default_user_agent
        return UserAgent(verify_ssl=False, use_cache_server=False).random
    except:
        return random.choice(user_agent_list)


async def issue_search_request(config, init, connector: aiohttp.TCPConnector = None):
    headers = [("authorization", config.BearerToken), ("x-guest-token", config.GuestToken)]

    search_composer = common_search
    if config.Profile:
        search_composer = profile_search

    search_params = search_composer(config, init)

    return await request(search_params.url, params=search_params.params, connector=connector, headers=headers)
