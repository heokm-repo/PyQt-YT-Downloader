@echo off
python -m PyInstaller --noconsole --onefile --name="YTDownloader" --add-binary "ffmpeg.exe;." --icon="app_icon.ico" --paths=src --hidden-import=main_window --hidden-import=settings_dialog --hidden-import=workers --hidden-import=utils --hidden-import=youtube_handler --hidden-import=yt_dlp --hidden-import=yt_dlp.extractor --hidden-import=yt_dlp.postprocessor --hidden-import=yt_dlp.downloader --hidden-import=yt_dlp.utils --hidden-import=requests --hidden-import=urllib3 --hidden-import=certifi --hidden-import=charset_normalizer --hidden-import=idna src/main.py

