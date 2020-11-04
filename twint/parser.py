import re
from datetime import datetime, timezone
from logging import Logger
from typing import Optional, Tuple, List


class NoMoreTweetsError(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class TokenNotFoundError(Exception):
    def __init__(self, msg):
        super().__init__(msg)


tweet_formats = {
    'datetime': '%Y-%m-%d %H:%M:%S %Z',
    'datestamp': '%Y-%m-%d',
    'timestamp': '%H:%M:%S'
}


def find_guest_token(markdown: str) -> str:
    match = re.search(r'\("gt=(\d+);', markdown)
    if match:
        return str(match.group(1))
    else:
        raise TokenNotFoundError('Could not find the Guest token in HTML')


def parse_tweets(response: dict, logger: Optional[Logger] = None) -> Tuple[List[dict], str]:
    if len(response['globalObjects']['tweets']) == 0:
        raise NoMoreTweetsError('No more data!')
    feed = []
    for timeline_entry in response['timeline']['instructions'][0]['addEntries']['entries']:
        if timeline_entry['entryId'].startswith('sq-I-t-') or timeline_entry['entryId'].startswith('tweet-'):
            if 'tweet' in timeline_entry['content']['item']['content']:
                _id = timeline_entry['content']['item']['content']['tweet']['id']
                # skip the ads
                if 'promotedMetadata' in timeline_entry['content']['item']['content']['tweet']:
                    continue
            elif 'tombstone' in timeline_entry['content']['item']['content'] and 'tweet' in \
                    timeline_entry['content']['item']['content']['tombstone']:
                _id = timeline_entry['content']['item']['content']['tombstone']['tweet']['id']
            else:
                _id = None
            if _id is None:
                raise ValueError('Unable to find ID of tweet in timeline.')
            try:
                temp_obj = response['globalObjects']['tweets'][_id]
            except KeyError:
                if logger:
                    logger.info('encountered a deleted tweet with id %s', _id)
                continue
            temp_obj['user_data'] = response['globalObjects']['users'][temp_obj['user_id_str']]
            if 'retweeted_status_id_str' in temp_obj:
                rt_id = temp_obj['retweeted_status_id_str']
                _dt = response['globalObjects']['tweets'][rt_id]['created_at']
                _dt = datetime.strptime(_dt, '%a %b %d %H:%M:%S %z %Y')
                _dt = utc_to_local(_dt)
                _dt = str(_dt.strftime(tweet_formats['datetime']))
                temp_obj['retweet_data'] = {
                    'user_rt_id': response['globalObjects']['tweets'][rt_id]['user_id_str'],
                    'user_rt': response['globalObjects']['tweets'][rt_id]['full_text'],
                    'retweet_id': rt_id,
                    'retweet_date': _dt,
                }
            feed.append(temp_obj)
    next_cursor = _get_cursor(response)
    return feed, next_cursor


def utc_to_local(utc_dt):
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)


def _get_cursor(response: dict):
    try:
        next_cursor = \
            response['timeline']['instructions'][0]['addEntries']['entries'][-1]['content']['operation']['cursor'][
                'value']
    except KeyError:
        # this is needed because after the first request location of cursor is changed
        next_cursor = \
            response['timeline']['instructions'][-1]['replaceEntry']['entry']['content']['operation']['cursor']['value']
    return next_cursor
