from yt_dlp.update import version_tuple
from yt_dlp.version import __version__

if version_tuple(__version__) < (2023, 9, 24):
    raise ImportError('yt-dlp version 2023.09.24 or later is required to use the TTUser plugin')

import itertools
import random
import string
import time

from yt_dlp.extractor.tiktok import TikTokIE, TikTokUserIE
from yt_dlp.utils import ExtractorError, int_or_none, traverse_obj, try_call


class TikTokUser_TTUserIE(TikTokUserIE, plugin_name='TTUser'):
    IE_NAME = 'tiktok:user'
    _VALID_URL = r'https?://(?:www\.)?tiktok\.com/@(?P<id>[\w\.-]+)/?(?:$|[#?])'
    _WORKING = True
    _TESTS = [{
        'url': 'https://tiktok.com/@therock?lang=en',
        'playlist_mincount': 25,
        'info_dict': {
            'id': 'therock',
        },
    }]

    _USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0'
    _API_BASE_URL = 'https://www.tiktok.com/api/creator/item_list/'

    def _build_web_query(self, sec_uid, cursor):
        return {
            'aid': '1988',
            'app_language': 'en',
            'app_name': 'tiktok_web',
            'browser_language': 'en-US',
            'browser_name': 'Mozilla',
            'browser_online': 'true',
            'browser_platform': 'Win32',
            'browser_version': '5.0 (Windows)',
            'channel': 'tiktok_web',
            'cookie_enabled': 'true',
            'count': '15',
            'cursor': cursor,
            'device_id': ''.join(random.choices(string.digits, k=19)),
            'device_platform': 'web_pc',
            'focus_state': 'true',
            'from_page': 'user',
            'history_len': '2',
            'is_fullscreen': 'false',
            'is_page_visible': 'true',
            'language': 'en',
            'os': 'windows',
            'priority_region': '',
            'referer': '',
            'region': 'US',
            'screen_height': '1080',
            'screen_width': '1920',
            'secUid': sec_uid,
            'type': '1',  # pagination type: 0 == oldest-to-newest, 1 == newest-to-oldest
            'tz_name': 'UTC',
            'verifyFp': 'verify_%s' % ''.join(random.choices(string.hexdigits, k=7)),
            'webcast_language': 'en',
        }

    def _entries(self, sec_uid, user_name):
        cursor = int(time.time() * 1E3)
        for page in itertools.count(1):
            response = self._download_json(
                self._API_BASE_URL, user_name, f'Downloading page {page}',
                query=self._build_web_query(sec_uid, cursor), headers={'User-Agent': self._USER_AGENT})

            for video in traverse_obj(response, ('itemList', lambda _, v: v['id'])):
                video_id = video['id']
                webpage_url = self._create_url(user_name, video_id)
                info = try_call(
                    lambda: self._parse_aweme_video_web(video, webpage_url, video_id)) or {'id': video_id}
                info.pop('formats', None)
                yield self.url_result(webpage_url, TikTokIE, **info)

            old_cursor = cursor
            cursor = traverse_obj(
                response, ('itemList', -1, 'createTime', {lambda x: x * 1E3}, {int_or_none}))
            if not cursor:
                cursor = old_cursor - 604800000  # jump 1 week back in time
            if cursor < 1472706000000 or not traverse_obj(response, 'hasMorePrevious'):
                break

    # For compat until required yt-dlp version is bumped
    def _get_universal_data(self, webpage, display_id):
        return traverse_obj(self._search_json(
            r'<script[^>]+\bid="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>', webpage,
            'universal data', display_id, end_pattern=r'</script>', default={}),
            ('__DEFAULT_SCOPE__', {dict})) or {}

    def _get_sec_uid(self, user_url, user_name, msg):
        webpage = self._download_webpage(
            user_url, user_name, fatal=False, headers={'User-Agent': 'Mozilla/5.0'},
            note=f'Downloading {msg} webpage', errnote=f'Unable to download {msg} webpage') or ''
        return traverse_obj(
            self._get_universal_data(webpage, user_name),
            ('webapp.user-detail', 'userInfo', 'user', 'secUid', {str})) or traverse_obj(
            try_call(lambda: self._get_sigi_state(webpage, user_name)),  # try_call is compat
            ('LiveRoom', 'liveRoomUserInfo', 'user', 'secUid'),
            ('UserModule', 'users', ..., 'secUid'),
            get_all=False, expected_type=str)

    def _real_extract(self, url):
        user_name = self._match_id(url)

        input_map = {
            k: v for (k, _, v) in map(
                lambda x: x.rpartition(':'),
                self._configuration_arg('sec_uid', ie_key=TikTokIE, casesense=True))
        }
        sec_uid = input_map.get(user_name)
        if not sec_uid and input_map.get(''):
            self.report_warning(
                '--extractor-args "tiktok:sec_uid=SECUID" has been deprecated. Use the new syntax: '
                '--extractor-args "tiktok:sec_uid=USERNAME1:SECUID1,USERNAME2:SECUID2"')
            sec_uid = input_map['']

        if not sec_uid:
            for user_url, msg in (
                (self._UPLOADER_URL_FORMAT % user_name, 'user'),
                (self._UPLOADER_URL_FORMAT % f'{user_name}/live', 'live'),
            ):
                sec_uid = self._get_sec_uid(user_url, user_name, msg)
                if sec_uid:
                    break

        if not sec_uid:
            webpage = self._download_webpage(
                f'https://www.tiktok.com/embed/@{user_name}', user_name,
                note='Downloading user embed page', fatal=False) or ''
            data = traverse_obj(self._search_json(
                r'<script[^>]+\bid=[\'"]__FRONTITY_CONNECT_STATE__[\'"][^>]*>',
                webpage, 'data', user_name, default={}),
                ('source', 'data', f'/embed/@{user_name}', {dict}))

            for aweme_id in traverse_obj(data, ('videoList', ..., 'id')):
                try:
                    sec_uid = self._extract_aweme_app(aweme_id).get('channel_id')
                except ExtractorError:
                    continue
                if sec_uid:
                    break

            if not sec_uid:
                raise ExtractorError(
                    'Could not extract secondary user ID. '
                    'Try using  --extractor-args "tiktok:sec_uid=USERNAME:ID"  with your command, '
                    'replacing "USERNAME" with the requested username and '
                    'replacing "ID" with the channel_id of the requested user')

        return self.playlist_result(self._entries(sec_uid, user_name), user_name)


__all__ = []
