"""Localized runtime diagnostics and fallback metadata, resolved on access."""
from . import get_string


class RuntimeStrings:
    @property
    def ERR_UNSUPPORTED_PLATFORM(self):
        return get_string('ERR_UNSUPPORTED_PLATFORM', 'YTDownloader is supported on Windows only. Please run this version on Windows 10 or later.')

    @property
    def ERR_MEDIA_DISCOVERY(self):
        return get_string("ERR_MEDIA_DISCOVERY", "Media discovery failed; check access and extractor support")

    @property
    def ERR_OUTPUT_PATH_VERIFY(self):
        return get_string("ERR_OUTPUT_PATH_VERIFY", "Downloaded output path could not be verified")

    @property
    def ERR_UNEXPECTED_OUTPUTS(self):
        return get_string("ERR_UNEXPECTED_OUTPUTS", "Unexpected multiple outputs; workspace retained for recovery")

    @property
    def ERR_AUDIO_SAMPLE_RATE(self):
        return get_string("ERR_AUDIO_SAMPLE_RATE", "Input audio sample rate could not be determined")

    @property
    def ERR_WORKSPACE_OUTPUT_MISSING(self):
        return get_string("ERR_WORKSPACE_OUTPUT_MISSING", "Workspace output was not found")

    @property
    def ERR_FFMPEG_MISSING(self):
        return get_string("ERR_FFMPEG_MISSING", "FFmpeg executable was not found")

    @property
    def ERR_FINALIZATION_TIMEOUT(self):
        return get_string("ERR_FINALIZATION_TIMEOUT", "Media finalization timed out")

    @property
    def ERR_FINAL_AUDIO_VERIFY(self):
        return get_string("ERR_FINAL_AUDIO_VERIFY", "Final audio stream could not be verified")

    @property
    def ERR_FINAL_VIDEO_VERIFY(self):
        return get_string("ERR_FINAL_VIDEO_VERIFY", "Final video stream could not be verified")

    @property
    def ERR_FINAL_FORMAT_VERIFY_FMT(self):
        return get_string("ERR_FINAL_FORMAT_VERIFY_FMT", "Final {format} streams or codecs could not be verified")

    @property
    def ERR_FINAL_COMPAT_VERIFY(self):
        return get_string("ERR_FINAL_COMPAT_VERIFY", "Final MP4 video compatibility could not be verified")

    @property
    def ERR_FINAL_AUDIO_LOST(self):
        return get_string("ERR_FINAL_AUDIO_LOST", "Final audio stream was lost")

    @property
    def ERR_FINAL_SAMPLE_RATE_VERIFY(self):
        return get_string("ERR_FINAL_SAMPLE_RATE_VERIFY", "Final audio sample rate could not be verified")

    @property
    def ERR_FINAL_SAMPLE_RATE_MISMATCH(self):
        return get_string("ERR_FINAL_SAMPLE_RATE_MISMATCH", "Final audio sample rate did not match the source")

    @property
    def ERR_PROCESS_STOP_FMT(self):
        return get_string("ERR_PROCESS_STOP_FMT", "{name} could not be stopped after cancellation")

    @property
    def ERR_PROCESS_EXIT_FMT(self):
        return get_string("ERR_PROCESS_EXIT_FMT", "{name} exited with code {code}")

    @property
    def ERR_DOWNLOAD_TIMEOUT(self):
        return get_string("ERR_DOWNLOAD_TIMEOUT", "Download timeout")

    @property
    def ERR_PROCESS_STDOUT_FMT(self):
        return get_string("ERR_PROCESS_STDOUT_FMT", "{name} stdout reader failed")

    @property
    def ERR_PROCESS_STDERR_FMT(self):
        return get_string("ERR_PROCESS_STDERR_FMT", "Failed to capture {name} stderr: {error}")

    @property
    def ERR_SUBPROCESS_FMT(self):
        return get_string("ERR_SUBPROCESS_FMT", "Subprocess error: {error}")

    @property
    def ERR_UNEXPECTED_FMT(self):
        return get_string("ERR_UNEXPECTED_FMT", "Unexpected error: {error}")

    @property
    def ERR_RELEASE_INVALID_FMT(self):
        return get_string("ERR_RELEASE_INVALID_FMT", "Invalid {name} release response")

    @property
    def ERR_RELEASE_VERSION_FMT(self):
        return get_string("ERR_RELEASE_VERSION_FMT", "{name} release did not contain a version")

    @property
    def ERR_RELEASE_ASSET_FMT(self):
        return get_string("ERR_RELEASE_ASSET_FMT", "{name} release did not contain the required file")

    @property
    def ERR_RELEASE_TRUST_FMT(self):
        return get_string("ERR_RELEASE_TRUST_FMT", "{name} release asset is missing its URL or trusted SHA-256 digest")

    @property
    def ERR_RELEASE_CHECK_FMT(self):
        return get_string("ERR_RELEASE_CHECK_FMT", "Failed to check {name} version: {error}")

    @property
    def ERR_WORKSPACE_SYMLINK_FMT(self):
        return get_string("ERR_WORKSPACE_SYMLINK_FMT", "Task workspace cannot be a symbolic link: {path}")

    @property
    def ERR_WORKSPACE_DIRECTORY_FMT(self):
        return get_string("ERR_WORKSPACE_DIRECTORY_FMT", "Task workspace is not a directory: {path}")

    @property
    def ERR_WORKSPACE_INSPECT_FMT(self):
        return get_string("ERR_WORKSPACE_INSPECT_FMT", "Could not inspect task workspace {path}: {error}")

    @property
    def ERR_WORKSPACE_REPLACE_FMT(self):
        return get_string("ERR_WORKSPACE_REPLACE_FMT", "Could not replace empty task workspace {path}: {error}")

    @property
    def ERR_WORKSPACE_MIGRATE_FMT(self):
        return get_string("ERR_WORKSPACE_MIGRATE_FMT", "Could not migrate legacy task workspace to {path}: {error}")

    @property
    def ERR_UNKNOWN(self):
        return get_string("ERR_UNKNOWN", "Unknown error")

    @property
    def ERR_DOWNLOAD_FOLDER_PROTECTED(self):
        return get_string("ERR_DOWNLOAD_FOLDER_PROTECTED", "Protected Windows system folder cannot be used as a download folder.")

    @property
    def ERR_DOWNLOAD_FOLDER_EMPTY(self):
        return get_string("ERR_DOWNLOAD_FOLDER_EMPTY", "Download folder path is empty.")

    @property
    def ERR_DOWNLOAD_FOLDER_NOT_DIRECTORY(self):
        return get_string("ERR_DOWNLOAD_FOLDER_NOT_DIRECTORY", "Path is not a directory.")

    @property
    def DEFAULT_VIDEO_TITLE(self):
        return get_string("DEFAULT_VIDEO_TITLE", "No Title")

    @property
    def DEFAULT_UPLOADER(self):
        return get_string("DEFAULT_UPLOADER", "Unknown")

    @property
    def DEFAULT_PLAYLIST_TITLE(self):
        return get_string("DEFAULT_PLAYLIST_TITLE", "Playlist")

    @property
    def ERR_WORKSPACE_ID(self):
        return get_string("ERR_WORKSPACE_ID", "Invalid task workspace ID")

    @property
    def ERR_READY_SOURCE_OUTSIDE(self):
        return get_string("ERR_READY_SOURCE_OUTSIDE", "Ready source is outside the task workspace")
