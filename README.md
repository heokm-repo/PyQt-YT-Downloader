# PyQt-YT-Downloader

A YouTube video and playlist downloader with modern GUI built using PyQt5 and yt-dlp.

## Features

- Download YouTube videos and playlists
- Multiple quality and format options (MP4, MKV, WebM, MP3)
- Loudness Normalization
- Multi-threaded download acceleration
- Multi-language support (Korean, English, Japanese)
- Clean and modern UI

## Download

Download the latest executable from the [Releases](https://github.com/heokm-repo/PyQt-YT-Downloader/releases) page.

## Usage

1. Run the executable (`YTDownloader.exe`).
2. Enter a YouTube video or playlist URL in the input field at the top.
3. Click the settings button (⚙) to configure download folder, quality, format, etc.
4. Click the download button to start downloading.

## FFmpeg Notice

This program uses FFmpeg to merge video and audio. You need `ffmpeg.exe` in the same folder as the executable for it to work properly.

- Windows: Download from [FFmpeg official website](https://ffmpeg.org/download.html)
- Or place `ffmpeg.exe` in the same folder as the executable.

## Building from Source

> **Note**: Regular users can download the executable from the "Download" section above.  
> The following instructions are for developers who want to build from source.

### Requirements

- Python 3.7 or higher
- PyInstaller
- FFmpeg

### Build Steps

1. Install project dependencies:
```bash
pip install -r requirements.txt
pip install pyinstaller
```

2. Windows:
```bash
build.bat
```

3. Linux/Mac:
```bash
chmod +x build.sh
./build.sh
```

The built executable will be created in the `dist/` folder.

## License

This project is licensed under the [GPL-3.0](LICENSE) License.

## Disclaimer

1. **Educational Purpose**: This project was developed for educational purposes in Python and PyQt5 programming, as well as for portfolio purposes.
2. **Legal Responsibility**: All responsibility for copyright infringement or violations of YouTube's Terms of Service (ToS) that occur from using this software lies entirely with the user. The developer is not responsible for account suspensions or legal disputes resulting from the use of this tool.
3. **Personal Use Only**: Downloaded content should be used for personal purposes only. Do not distribute or use commercially.

## Libraries Used

- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - GUI framework
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube download engine
- [requests](https://requests.readthedocs.io/) - HTTP library

---

# PyQt-YT-Downloader

PyQt5 기반의 YouTube 영상 다운로더입니다.

## 주요 기능

- YouTube 영상 및 플레이리스트 다운로드
- 다양한 화질 및 포맷 선택 (MP4, MKV, WebM, MP3)
- 음량 평준화 (Loudness Normalization)
- 멀티 스레드 다운로드 가속
- 다국어 지원 (한국어, 영어, 일본어)
- 깔끔한 모던 UI

## 다운로드

[Releases](https://github.com/heokm-repo/PyQt-YT-Downloader/releases) 페이지에서 최신 버전의 실행 파일을 다운로드하세요.

## 사용 방법

1. 실행 파일(`YTDownloader.exe`)을 실행합니다.
2. 상단 입력창에 YouTube 영상 또는 플레이리스트 URL을 입력합니다.
3. 설정 버튼(⚙)을 클릭하여 다운로드 폴더, 화질, 포맷 등을 설정합니다.
4. 다운로드 버튼을 클릭하여 다운로드를 시작합니다.

## FFmpeg 안내

이 프로그램은 FFmpeg를 사용하여 비디오와 오디오를 병합합니다. 실행 파일과 같은 폴더에 `ffmpeg.exe`가 있어야 정상적으로 작동합니다.

- Windows: [FFmpeg 공식 사이트](https://ffmpeg.org/download.html)에서 다운로드
- 또는 실행 파일과 같은 폴더에 `ffmpeg.exe`를 배치하세요.

## 소스 코드에서 빌드하기

> **참고**: 일반 사용자는 위의 "다운로드" 섹션에서 실행 파일을 다운로드하면 됩니다.  
> 아래 내용은 소스 코드에서 직접 빌드하려는 개발자를 위한 것입니다.

### 빌드 요구사항

- Python 3.7 이상
- PyInstaller
- FFmpeg

### 빌드 절차

1. 프로젝트 의존성 설치:
```bash
pip install -r requirements.txt
pip install pyinstaller
```

2. Windows:
```bash
build.bat
```

3. Linux/Mac:
```bash
chmod +x build.sh
./build.sh
```

빌드된 실행 파일은 `dist/` 폴더에 생성됩니다.

## 라이선스

이 프로젝트는 [GPL-3.0](LICENSE) 라이선스를 따릅니다.

## 면책 조항

1. **학습 목적**: 이 프로젝트는 Python 및 PyQt5 프로그래밍 학습과 포트폴리오 목적으로 개발되었습니다.
2. **법적 책임**: 이 소프트웨어를 사용하여 발생하는 저작권 침해 또는 YouTube 서비스 약관(ToS) 위반에 대한 모든 책임은 전적으로 사용자에게 있습니다. 개발자는 이 도구의 사용으로 인한 계정 정지나 법적 분쟁에 대해 책임을 지지 않습니다.
3. **개인적 사용**: 다운로드한 콘텐츠는 개인적인 용도로만 사용해야 하며, 배포하거나 상업적으로 이용하지 마십시오.

## 사용된 라이브러리

- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - GUI 프레임워크
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube 다운로드 엔진
- [requests](https://requests.readthedocs.io/) - HTTP 라이브러리
