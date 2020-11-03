import datetime
from sys import platform
from typing import NamedTuple
from urllib.parse import quote
from urllib.parse import urlencode

mobile = "https://mobile.twitter.com"
base = "https://api.twitter.com/2/search/adaptive.json"


class SearchParams(NamedTuple):
    url: str
    params: list
    serial_query: str


def sanitize_query(_url, params):
    _serialQuery = ""
    _serialQuery = urlencode(params, quote_via=quote)
    _serialQuery = _url + "?" + _serialQuery
    return _serialQuery


def format_date(date):
    if "win" in platform:
        return f'\"{date.split()[0]}\"'
    try:
        return int(datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S").timestamp())
    except ValueError:
        return int(datetime.datetime.strptime(date, "%Y-%m-%d").timestamp())


def common_search(username: str, config, init) -> SearchParams:
    """
    Creates query parameters and URL for search
    """

    url = base
    tweet_count = config.TweetsPortionSize
    q = ""
    params = [
        # ('include_blocking', '1'),
        # ('include_blocked_by', '1'),
        # ('include_followed_by', '1'),
        # ('include_want_retweets', '1'),
        # ('include_mute_edge', '1'),
        # ('include_can_dm', '1'),
        ('include_can_media_tag', '1'),
        # ('skip_status', '1'),
        # ('include_cards', '1'),
        ('include_ext_alt_text', 'true'),
        ('include_quote_count', 'true'),
        ('include_reply_count', '1'),
        ('tweet_mode', 'extended'),
        ('include_entities', 'true'),
        ('include_user_entities', 'true'),
        ('include_ext_media_availability', 'true'),
        ('send_error_codes', 'true'),
        ('simple_quoted_tweet', 'true'),
        ('count', tweet_count),
        # ('query_source', 'typed_query'),
        # ('pc', '1'),
        ('cursor', str(init)),
        ('spelling_corrections', '1'),
        ('ext', 'mediaStats%2ChighlightedLabel'),
        ('tweet_search_mode', 'live'),  # this can be handled better, maybe take an argument and set it then
    ]
    if not config.PopularTweets:
        params.append(('f', 'tweets'))
    if config.Lang:
        params.append(("l", config.Lang))
        params.append(("lang", "en"))
    if username:
        q += f" from:{username}"

    if config.Query:
        q += f" from:{config.Query}"
    if config.Geo:
        config.Geo = config.Geo.replace(" ", "")
        q += f" geocode:{config.Geo}"
    if config.Search:
        q += f" {config.Search}"
    if config.Year:
        q += f" until:{config.Year}-1-1"
    if config.Since:
        q += f" since:{format_date(config.Since)}"
    if config.Until:
        q += f" until:{format_date(config.Until)}"
    if config.Email:
        q += ' "mail" OR "email" OR'
        q += ' "gmail" OR "e-mail"'
    if config.Phone:
        q += ' "phone" OR "call me" OR "text me"'
    if config.Verified:
        q += " filter:verified"
    if config.To:
        q += f" to:{config.To}"
    if config.All:
        q += f" to:{config.All} OR from:{config.All} OR @{config.All}"
    if config.Near:
        q += f' near:"{config.Near}"'
    if config.Images:
        q += " filter:images"
    if config.Videos:
        q += " filter:videos"
    if config.Media:
        q += " filter:media"
    if config.Replies:
        q += " filter:replies"
    # although this filter can still be used, but I found it broken in my preliminary testing, needs more testing
    if config.NativeRetweets:
        q += " filter:nativeretweets"
    if config.MinLikes:
        q += f" min_faves:{config.MinLikes}"
    if config.MinRetweets:
        q += f" min_retweets:{config.MinRetweets}"
    if config.MinReplies:
        q += f" min_replies:{config.MinReplies}"
    if config.Links == "include":
        q += " filter:links"
    elif config.Links == "exclude":
        q += " exclude:links"
    if config.Source:
        q += f" source:\"{config.Source}\""
    if config.MembersList:
        q += f" list:{config.MembersList}"
    if config.FilterRetweets:
        q += f" exclude:nativeretweets exclude:retweets"
    if config.CustomQuery:
        q = config.CustomQuery

    q = q.strip()
    params.append(("q", q))
    serial_query = sanitize_query(url, params)
    return SearchParams(url, params, serial_query)


def profile_search(user_id: str, config, init=None) -> SearchParams:
    """
    Creates query parameters and URL for profile feed
    """

    url = f'https://api.twitter.com/2/timeline/profile/{user_id}.json'
    tweet_count = config.TweetsPortionSize
    params = [
        # some of the fields are not required, need to test which ones aren't required
        ('include_profile_interstitial_type', '1'),
        ('include_blocking', '1'),
        ('include_blocked_by', '1'),
        ('include_followed_by', '1'),
        ('include_want_retweets', '1'),
        ('include_mute_edge', '1'),
        ('include_can_dm', '1'),
        ('include_can_media_tag', '1'),
        ('skip_status', '1'),
        ('cards_platform', 'Web - 12'),
        ('include_cards', '1'),
        ('include_ext_alt_text', 'true'),
        ('include_quote_count', 'true'),
        ('include_reply_count', '1'),
        ('tweet_mode', 'extended'),
        ('include_entities', 'true'),
        ('include_user_entities', 'true'),
        ('include_ext_media_color', 'true'),
        ('include_ext_media_availability', 'true'),
        ('send_error_codes', 'true'),
        ('simple_quoted_tweet', 'true'),
        ('include_tweet_replies', 'true'),
        ('count', tweet_count),
        ('ext', 'mediaStats%2ChighlightedLabel'),
    ]

    if type(init) == str:
        params.append(('cursor', str(init)))
    serial_query = sanitize_query(url, params)
    return SearchParams(url, params, serial_query)
