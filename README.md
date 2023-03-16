A [yt-dlp](https://github.com/yt-dlp/yt-dlp) extractor [plugin](https://github.com/yt-dlp/yt-dlp#plugins) for downloading all videos posted by a TikTok user

---

Based on [redraskal's TikTokUserIE fork](https://github.com/redraskal/yt-dlp/tree/fix/tiktok-user)

 * Pass `--extractor-args "tiktok:sec_uid=ID"` to specify a secondary user id with the value of `ID`

 * Pass `--extractor-args "tiktok:firefox_path=PATH"` to specify the `PATH` of the Playwright Firefox binary if needed

## Installation

Requires yt-dlp `2023.02.17` or above.

You can install this package with pip:
```
python3 -m pip install -U https://github.com/bashonly/yt-dlp-TTUser/archive/master.zip
```

See [yt-dlp installing plugins](https://github.com/yt-dlp/yt-dlp#installing-plugins) for the many other ways this plugin package can be installed.

## Requirements

The plugin requires Playwright for Python to be installed with its Firefox binary:
```
python3 -m pip install playwright
playwright install --with-deps firefox
```
See the [Playwright for Python documentation](https://playwright.dev/python/docs/intro) for more information.
