import base64
import itertools
import random
import string
import urllib.parse

from yt_dlp.aes import aes_cbc_encrypt_bytes
from yt_dlp.utils import (
    ExtractorError,
    traverse_obj,
    try_call,
    update_url_query,
)
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

    _API_BASE_URL = 'https://us.tiktok.com/api/post/item_list/'
    _PARAMS = {
        'aid': '1988',
        'app_language': 'en',  # url only?
        'app_name': 'tiktok_web',
        'browser_language': 'en-US',
        'browser_name': 'Mozilla',
        'browser_online': 'true',
        'browser_platform': 'Win32',
        'browser_version': '5.0 (Windows)',
        'channel': 'tiktok_web',
        'cookie_enabled': 'true',
        'device_id': ''.join(random.choices(string.digits, k=19)),
        'device_platform': 'web_pc',
        'focus_state': 'false',
        'from_page': 'user',
        'history_len': '2',
        'is_encryption': '1',
        'is_fullscreen': 'false',
        'is_page_visible': 'true',
        'os': 'windows',
        'region': 'US',
        'screen_height': '1080',
        'screen_width': '1920',
        'tz_name': 'UTC',  # x-tt-params only?
        'webcast_language': 'en',  # x-tt-params only?
    }
    _PARAMS_AES_KEY = b'webapp1.0+202106'

    def _x_tt_params(self, sec_uid, cursor):
        query = self._PARAMS.copy()
        # query.pop('app_language', None)
        query.update({
            'cursor': cursor,
            'language': 'en',
            'priority_region': '',
            'referer': '',
            'root_referer': 'undefined',
            'secUid': sec_uid,
            'userId': 'undefined',
            'verifyFp': 'undefined',
        })
        return base64.b64encode(aes_cbc_encrypt_bytes(
            urllib.parse.urlencode(dict(sorted(query.items()))),
            self._PARAMS_AES_KEY, self._PARAMS_AES_KEY)).decode()

    def _entries(self, sec_uid, user_name):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise ExtractorError('Playwright is not installed', expected=True)

        api_url = update_url_query(self._API_BASE_URL, self._PARAMS)
        cursor = '0'

        with sync_playwright() as p:
            browser = p.firefox.launch(args=['--mute-audio'])
            webpage = browser.new_page()
            webpage.goto('https://www.tiktok.com/', wait_until='load')
            webpage.wait_for_timeout(2000)

            for page in itertools.count(1):
                self.to_screen(f'Downloading page {page}')
                res = webpage.evaluate(
                    '([api_url, params]) => fetch(api_url, { headers: { "x-tt-params": params } }).then(res => res.json())',
                    [api_url, self._x_tt_params(sec_uid, cursor)])

                for video in traverse_obj(res, ('itemList', ..., {dict})):
                    video_id = video.get('id')
                    if video_id:
                        yield self.url_result(self._create_url(user_name, video_id), TikTokIE, video_id)
                        # entry = {}
                        # try:
                        #     entry = self._extract_aweme_app(video_id)
                        # except ExtractorError:
                        #     self.report_warning('Failed to extract from feed; falling back to web API response')
                        #     aweme_detail = traverse_obj(
                        #         res, ('itemList', lambda _, v: v['id'] == video_id, {dict}), get_all=False)
                        #     if traverse_obj(aweme_detail, ('video', 'playAddr')):
                        #         entry = self._parse_aweme_video_web(
                        #             aweme_detail, self._create_url(user_name, video_id))
                        #
                        # if entry:
                        #     yield {
                        #         **entry,
                        #         'extractor_key': TikTokIE.ie_key(),
                        #         'extractor': 'TikTok',
                        #         'webpage_url': self._create_url(user_name, video_id),
                        #     }
                        # else:
                        #     self.report_warning(f'Unable to extract video {video_id}')

                if not res.get('hasMore') or not res.get('cursor'):
                    break
                cursor = res['cursor']

            browser.close()

    def _parse_aweme_video_app(self, aweme_detail):
        ret = super()._parse_aweme_video_app(aweme_detail)
        ret['channel_id'] = traverse_obj(aweme_detail, ('author', 'sec_uid'))
        return ret

    def _get_sec_uid(self, user_url, user_name, msg):
        webpage = self._download_webpage(
            user_url, user_name, fatal=False, headers={'User-Agent': 'Mozilla/5.0'},
            note=f'Downloading {msg} webpage', errnote=f'Unable to download {msg} webpage')
        data = try_call(lambda: self._get_sigi_state(webpage, user_name))
        return traverse_obj(
            data, ('LiveRoom', 'liveRoomUserInfo', 'user', 'secUid'),
            ('UserModule', 'users', ..., 'secUid'), get_all=False, expected_type=str)

    def _real_extract(self, url):
        user_name = self._match_id(url)
        sec_uid = self._configuration_arg('sec_uid', [None], ie_key=TikTokIE)[0]

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
                f'https://www.tiktok.com/embed/@{user_name}', user_name, note='Downloading user embed page')
            data = traverse_obj(self._search_json(
                r'(?s)<script[^>]+\bid=[\'"]__FRONTITY_CONNECT_STATE__[\'"][^>]*>', webpage, 'data', user_name),
                ('source', 'data', f'/embed/@{user_name}', {dict}))

            info = {}
            for aweme_id in traverse_obj(data, ('videoList', ..., 'id')):
                try:
                    info = self._extract_aweme_app(aweme_id)
                except ExtractorError:
                    continue

                sec_uid = info.get('channel_id')
                if sec_uid:
                    break

            if not sec_uid:
                raise ExtractorError('Could not extract secondary user ID')

        return self.playlist_result(self._entries(sec_uid, user_name), user_name)


__all__ = []
