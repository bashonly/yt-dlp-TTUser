A [yt-dlp](https://github.com/yt-dlp/yt-dlp) extractor [plugin](https://github.com/yt-dlp/yt-dlp#plugins) for downloading all videos posted by a TikTok user

---

 * Pass `--extractor-args "tiktok:sec_uid=USERNAME1:SECUID1,USERNAME2:SECUID2"` to specify a secondary user ID (`SECUID`) for a given username (`USERNAME`)

## Installation

Requires yt-dlp `2023.09.24` or above.

You can download the wheel of the [latest release](https://github.com/bashonly/yt-dlp-TTUser/releases/latest) and place the `.whl` file in one of [yt-dlp's plugin paths](https://github.com/yt-dlp/yt-dlp#installing-plugins).

Or you can install this package with pip:
```
python3 -m pip install -U https://github.com/bashonly/yt-dlp-TTUser/archive/master.zip
```

See [the plugins section of the yt-dlp README](https://github.com/yt-dlp/yt-dlp#installing-plugins) for more information.
