A [yt-dlp](https://github.com/yt-dlp/yt-dlp) extractor [plugin](https://github.com/yt-dlp/yt-dlp#plugins) for downloading all videos posted by a TikTok user

---

## NOTICE

This plugin has been made obsolete by [yt-dlp version 2024.05.27](https://github.com/yt-dlp/yt-dlp/releases/tag/2024.05.27), [commit c53c2e4](https://github.com/yt-dlp/yt-dlp/commit/c53c2e40fde8f2e15c7c62f8ca1a5d9e90ddc079)

**The TikTok user extractor has now been fixed in yt-dlp. As such, this plugin will no longer be updated, and it has been disabled for yt-dlp versions where it is obsolete and/or incompatible**

Update your yt-dlp to the latest version (`yt-dlp -U`) if you have not already.

---

 * Pass `--extractor-args "tiktok:sec_uid=USERNAME1:SECUID1,USERNAME2:SECUID2"` to specify a secondary user ID (`SECUID`) for a given username (`USERNAME`).
	- **NOTE:** This extractor-arg does not apply to the fixed/actual yt-dlp extractor; it instead accepts `tiktokuser:`-prefixed URLs, e.g. `tiktokuser:SEC_UID`

## Installation

Requires yt-dlp version [2023.09.24](https://github.com/yt-dlp/yt-dlp/releases/tag/2023.09.24) to [2024.05.26.232421](https://github.com/yt-dlp/yt-dlp-master-builds/releases/tag/2024.05.26.232421).

You can download the wheel of the [latest release](https://github.com/bashonly/yt-dlp-TTUser/releases/latest) and place the `.whl` file in one of [yt-dlp's plugin paths](https://github.com/yt-dlp/yt-dlp#installing-plugins).

Or you can install this package with pip:
```
python3 -m pip install -U https://github.com/bashonly/yt-dlp-TTUser/archive/master.zip
```

See [the plugins section of the yt-dlp README](https://github.com/yt-dlp/yt-dlp#installing-plugins) for more information.
