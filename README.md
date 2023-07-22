A [yt-dlp](https://github.com/yt-dlp/yt-dlp) extractor [plugin](https://github.com/yt-dlp/yt-dlp#plugins) for downloading all videos posted by a TikTok user

---

 * Pass `--extractor-args "tiktok:sec_uid=ID"` to specify a secondary user id with the value of `ID`

 * Pass `--extractor-args "tiktok:web_fallback"` to extract videos from web API when unavailable from mobile feed (user extraction will take longer)

## Installation

Requires yt-dlp `2023.02.17` or above.

You can install this package with pip:
```
python3 -m pip install -U https://github.com/bashonly/yt-dlp-TTUser/archive/master.zip
```

See [yt-dlp installing plugins](https://github.com/yt-dlp/yt-dlp#installing-plugins) for the many other ways this plugin package can be installed.
