"""Download execution helpers backed by yt-dlp."""

import os
from pathlib import Path

from constants import (
    ERROR_INVALID_URL,
    MSG_DOWNLOAD_COMPLETE,
    MSG_PAUSED_BY_USER,
    STATUS_FINISHED,
    STATUS_POSTPROCESSING,
)
from core.download.finalization_pipeline import finalize_and_commit_download
from core.download.finalization_policy import target_output_format
from core.download.metadata_mapper import build_metadata_result
from core.download.options import _build_all_options
from core.download.output_paths import (
    verified_download_output_path,
    verified_workspace_output_path,
)
from core.download.result import DownloadResult
from core.download.workspace_cleanup import remove_task_workspace
from core.download.workspace_state import (
    destination_changed_since_ready,
    read_ready_source,
    remove_ready_marker,
    write_ready_source,
)
from core.youtube_url import _sanitize_url
from core.ytdlp.wrapper import YtDlpWrapper
from locales.strings import STR
from utils.bin.manager import get_ytdlp_path
from utils.logger import log
from utils.settings_store import get_download_folder
from utils.utils import get_ffmpeg_path, is_youtube_url


OUTPUT_PATH_VERIFICATION_ERROR = "Downloaded output path could not be verified"


def download_video_with_result(
    url,
    settings,
    progress_hook,
    is_resume=False,
    stop_check=None,
    metadata_hook=None,
    temp_identity=None,
) -> DownloadResult:
    """Download a single URL and return its exact final output path."""
    if not url:
        return DownloadResult(False, ERROR_INVALID_URL)

    if is_youtube_url(url):
        clean_url, is_playlist = _sanitize_url(url)
    else:
        clean_url = url
        is_playlist = False

    ytdlp_path = get_ytdlp_path()
    if not ytdlp_path:
        return DownloadResult(False, STR.ERR_YTDLP_RESTART)

    save_path = get_download_folder(settings)
    ffmpeg_path = get_ffmpeg_path()
    ydl_opts = _build_all_options(
        settings,
        save_path,
        ffmpeg_path,
        is_playlist,
        is_resume=is_resume,
        url=clean_url,
        temp_identity=temp_identity or settings.get("_temp_identity"),
    )
    workspace = str(ydl_opts.get("temp_path") or "")

    try:
        wrapper = YtDlpWrapper(ytdlp_path, ffmpeg_path)

        def handle_raw_metadata(info):
            mapped = build_metadata_result(info, clean_url, is_playlist)
            selected_audio_bitrate = mapped.get("audio_bitrate")
            if selected_audio_bitrate:
                settings["_selected_audio_bitrate"] = selected_audio_bitrate
            if metadata_hook is not None:
                metadata_hook(mapped)

        def handle_progress(progress):
            progress_hook(progress)

        resume_output = verified_download_output_path(
            str(settings.get("_resume_output_path") or ""),
            save_path,
        )
        if resume_output:
            remove_task_workspace(workspace)
            progress_hook({"status": STATUS_FINISHED, "filename": resume_output})
            return DownloadResult(True, MSG_DOWNLOAD_COMPLETE, resume_output)

        ready_source = read_ready_source(workspace)
        if ready_source:
            ready_destination = verified_download_output_path(
                str(os.path.join(save_path, ready_source.final_name)),
                save_path,
            )
            if ready_destination and destination_changed_since_ready(
                ready_source,
                ready_destination,
            ):
                remove_task_workspace(workspace)
                progress_hook(
                    {"status": STATUS_FINISHED, "filename": ready_destination}
                )
                return DownloadResult(
                    True,
                    MSG_DOWNLOAD_COMPLETE,
                    ready_destination,
                )
            workspace_output = verified_workspace_output_path(
                ready_source.source_path,
                workspace,
            )
            if not workspace_output:
                remove_ready_marker(workspace)
                ready_source = None

        if ready_source:
            if ready_source.audio_bitrate:
                settings["_selected_audio_bitrate"] = ready_source.audio_bitrate
            success, message = True, "Ready source found"
        else:
            success, message = wrapper.download(
                clean_url,
                ydl_opts,
                handle_progress,
                is_resume=is_resume,
                stop_check=stop_check,
                metadata_hook=handle_raw_metadata,
            )
            workspace_output = ""

        if success:
            if not workspace_output:
                workspace_output = verified_workspace_output_path(
                    str(wrapper.final_output_path or ""),
                    workspace,
                )
            if not workspace_output:
                return DownloadResult(False, OUTPUT_PATH_VERIFICATION_ERROR)
            if not ready_source:
                final_name = (
                    f"{Path(workspace_output).stem}."
                    f"{target_output_format(settings)}"
                )
                write_ready_source(
                    workspace,
                    workspace_output,
                    final_name,
                    settings.get("_selected_audio_bitrate"),
                    os.path.join(save_path, final_name),
                )

            progress_hook(
                {
                    "status": STATUS_POSTPROCESSING,
                    "filename": workspace_output,
                }
            )
            finalization = finalize_and_commit_download(
                workspace_output,
                workspace,
                save_path,
                settings,
                ffmpeg_path,
                stop_check,
            )
            if finalization.paused:
                return DownloadResult(
                    False,
                    MSG_PAUSED_BY_USER,
                    workspace_output,
                )
            if not finalization.success:
                return DownloadResult(
                    False,
                    f"Media finalization failed: {finalization.error}",
                    workspace_output,
                )
            final_path = verified_download_output_path(
                finalization.output_path,
                save_path,
            )
            if not final_path:
                return DownloadResult(False, OUTPUT_PATH_VERIFICATION_ERROR)
            remove_task_workspace(workspace)
            progress_hook({"status": STATUS_FINISHED, "filename": final_path})
            return DownloadResult(True, MSG_DOWNLOAD_COMPLETE, final_path)

        if MSG_PAUSED_BY_USER in message:
            return DownloadResult(False, MSG_PAUSED_BY_USER)
        return DownloadResult(False, message)
    except Exception as exc:
        error_msg = str(exc)
        if MSG_PAUSED_BY_USER in error_msg:
            return DownloadResult(False, MSG_PAUSED_BY_USER)

        log.error(f"Download Error: {error_msg}", exc_info=True)
        return DownloadResult(False, error_msg)


def download_video(
    url,
    settings,
    progress_hook,
    is_resume=False,
    stop_check=None,
    metadata_hook=None,
    temp_identity=None,
):
    """Download a single URL using the historical two-value return API."""
    result = download_video_with_result(
        url,
        settings,
        progress_hook,
        is_resume=is_resume,
        stop_check=stop_check,
        metadata_hook=metadata_hook,
        temp_identity=temp_identity,
    )
    return result.as_legacy_tuple()
