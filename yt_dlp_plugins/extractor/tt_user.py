from yt_dlp.update import version_tuple
from yt_dlp.version import __version__

if version_tuple(__version__) < (2023, 9, 24):
    raise ImportError('yt-dlp version 2023.09.24 or later is required to use the TTUser plugin')

import itertools
import random
import string
import time

from yt_dlp.utils import ExtractorError, int_or_none, traverse_obj
from yt_dlp.extractor.tiktok import TikTokIE, TikTokUserIE


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

                if not self._configuration_arg('web_fallback', ie_key=TikTokIE):
                    yield self.url_result(self._create_url(user_name, video_id), TikTokIE, video_id)
                    continue

                entry = {}
                try:
                    entry = self._extract_aweme_app(video_id)
                except ExtractorError as e:
                    self.report_warning(
                        f'{e.orig_msg}. Failed to extract from feed; falling back to web API response')
                    if traverse_obj(video, ('video', 'playAddr')):
                        entry = self._parse_aweme_video_web(video, self._create_url(user_name, video_id), video_id)
                if entry:
                    yield {
                        **entry,
                        'extractor_key': TikTokIE.ie_key(),
                        'extractor': 'TikTok',
                        'webpage_url': self._create_url(user_name, video_id),
                    }
                else:
                    self.report_warning(f'Unable to extract video {video_id}')

            cursor = traverse_obj(
                response, ('itemList', -1, 'createTime', {lambda x: x * 1E3}, {int_or_none}))
            if not cursor or not response.get('hasMorePrevious'):
                break

    def _get_sec_uid(self, user_url, user_name, msg):
        webpage = self._download_webpage(
            user_url, user_name, fatal=False, headers={'User-Agent': 'Mozilla/5.0'},
            note=f'Downloading {msg} webpage', errnote=f'Unable to download {msg} webpage') or ''
        sec_uid = traverse_obj(self._search_json(
            r'<script[^>]+\bid="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>', webpage,
            'rehydration data', user_name, end_pattern=r'</script>', default={}),
            ('__DEFAULT_SCOPE__', 'webapp.user-detail', 'userInfo', 'user', 'secUid', {str}))
        if sec_uid:
            return sec_uid
        try:
            return traverse_obj(
                self._get_sigi_state(webpage, user_name),
                ('LiveRoom', 'liveRoomUserInfo', 'user', 'secUid'),
                ('UserModule', 'users', ..., 'secUid'),
                get_all=False, expected_type=str)
        except ExtractorError:
            return None

    def _real_extract(self, url):
        user_name = self._match_id(url)
        sec_uid = self._configuration_arg('sec_uid', [None], ie_key=TikTokIE, casesense=True)[0]

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
                    'Try using  --extractor-arg "tiktok:sec_uid=ID"  with your command, '
                    'replacing "ID" with the channel_id of the requested user')

        return self.playlist_result(self._entries(sec_uid, user_name), user_name)


__all__ = []
