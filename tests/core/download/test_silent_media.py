import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from core.download import media_probe, finalization_pipeline
from core.download.finalization_policy import build_finalization_plan
from core.download.media_probe import MediaProbeResult
from locales.strings import STR


@pytest.mark.parametrize('target,codec', [('mp4', 'h264'), ('mkv', 'h264'), ('webm', 'vp9')])
def test_silent_video_skips_audio_processing_without_forcing_video_encode(target, codec):
    plan = build_finalization_plan(
        {'format': target, 'normalize_audio': True, 'audio_quality': '96k'},
        MediaProbeResult(video_codec=codec, video_pixel_format='yuv420p', has_audio=False),
        'source.' + target,
    )
    assert plan.audio_filter is None
    assert plan.audio_args == ('-c:a', 'copy')
    assert plan.video_args == ('-c:v', 'copy')
    assert not plan.requires_ffmpeg


@pytest.mark.parametrize('target', ['mp3', 'wav', 'm4a'])
@pytest.mark.parametrize('normalize', [False, True])
def test_audio_only_request_for_silent_video_has_clear_error(target, normalize):
    with pytest.raises(ValueError, match=STR.ERR_NO_AUDIO_STREAM):
        build_finalization_plan({'format': target, 'normalize_audio': normalize},
                                MediaProbeResult(video_codec='h264', has_audio=False))


@pytest.mark.parametrize('has_audio', [None, True])
def test_unknown_or_invalid_audio_is_not_treated_as_confirmed_silence(has_audio):
    with pytest.raises(ValueError, match='sample rate'):
        build_finalization_plan({'format': 'mp4', 'normalize_audio': True},
                                MediaProbeResult(video_codec='h264', has_audio=has_audio))


def test_audio_present_still_gets_normalized():
    plan = build_finalization_plan({'format': 'mp4', 'normalize_audio': True},
                                  MediaProbeResult(video_codec='h264', audio_codec='aac',
                                                   audio_sample_rate=44100, has_audio=True))
    assert 'loudnorm' in plan.audio_filter and 'aresample=44100' in plan.audio_filter
    assert plan.requires_ffmpeg


@pytest.mark.parametrize('streams,expected', [
    ([{'codec_type': 'video', 'codec_name': 'h264'}], False),
    ([{'codec_type': 'audio'}], True),
    (None, None),
])
def test_probe_distinguishes_audio_absence_from_incomplete_inspection(monkeypatch, streams, expected):
    monkeypatch.setattr(media_probe.subprocess, 'run', Mock(return_value=SimpleNamespace(
        returncode=0, stdout=json.dumps({'streams': streams}))))
    probe = media_probe._probe_with_ffprobe('source', 'ffprobe')
    assert (probe.has_audio if probe else None) is expected


def test_silent_audio_only_failure_does_not_run_ffmpeg_or_publish(tmp_path, monkeypatch):
    source = tmp_path / 'source.mp4'
    source.write_bytes(b'video')
    engine = tmp_path / 'ffmpeg.exe'
    engine.touch()
    monkeypatch.setattr(finalization_pipeline, 'probe_media_file', lambda *args: MediaProbeResult(
        video_codec='h264', has_audio=False))
    execute = Mock()
    monkeypatch.setattr(finalization_pipeline, 'run_ffmpeg_command', execute)
    result = finalization_pipeline.finalize_and_commit_download(
        str(source), str(tmp_path), str(tmp_path / 'saved'), {'format': 'mp3'}, str(engine))
    assert not result.success and result.error == STR.ERR_NO_AUDIO_STREAM
    execute.assert_not_called()
    assert source.exists() and not (tmp_path / 'saved').exists()
