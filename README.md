# PyQt-YT-Downloader

A Windows-only YouTube video and playlist downloader with a PyQt5 GUI and yt-dlp.

## Supported Platform

- Windows 10 or later
- This project does not currently support Linux or macOS builds/runtime.

## Features

- Download YouTube videos and playlists
- Multiple quality and format options: MP4, MKV, WebM, MP3, M4A, WAV
- Audio normalization
- Optional fragment download acceleration
- Korean, English, and Japanese UI strings
- Automatic setup for required downloader components

## Download

Download the latest Windows executable from the [Releases](https://github.com/heokm-repo/PyQt-YT-Downloader/releases) page.

## Usage

1. Run `YTDownloader.exe` on Windows.
2. On first run, allow the app to download required components when prompted.
3. Enter a YouTube video or playlist URL.
4. Configure download folder, quality, format, and other options in Settings.
5. Click Download.

## Runtime Components

The app manages these files under `%APPDATA%\YTDownloader\bin`:

- `yt-dlp.exe`
- `ffmpeg.exe`
- `qjs.exe` optional, used for some yt-dlp JavaScript handling paths

FFmpeg is required for merging video/audio streams and audio conversion. The app can download the Windows FFmpeg build during initial setup.

## Building From Source

These instructions are for Windows developers.

### Requirements

- Windows 10 or later
- Python 3.7 or higher
- Dependencies from `requirements.txt`
- PyInstaller

### Build Steps

```powershell
pip install -r requirements.txt
pip install pyinstaller
.\build.bat
```

The built executable is created in `dist/`.

## License

This project is licensed under the [GPL-3.0](LICENSE) License.

## Disclaimer

1. This project is for educational and portfolio purposes.
2. Users are responsible for copyright, account, and Terms of Service issues caused by downloaded content.
3. Downloaded content should be used for personal purposes only.

## Libraries Used

- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [requests](https://requests.readthedocs.io/)
- [FFmpeg](https://ffmpeg.org/)
- [QuickJS](https://github.com/quickjs-ng/quickjs)
