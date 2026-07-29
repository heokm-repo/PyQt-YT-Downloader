"""Choose source audio streams according to the requested output container."""

from __future__ import annotations

from dataclasses import dataclass

from constants import DEFAULT_AUDIO_QUALITY


@dataclass(frozen=True)
class AudioSourcePolicy:
    """Primary compatible selector plus a generic fallback selector."""

    primary: str
    fallback: str
    audio_only_candidates: tuple[str, ...] = ()

    @property
    def audio_only_selector(self) -> str:
        selectors = list(self.audio_only_candidates) or [self.primary, self.fallback]
        combined_fallback = (
            "worst" if self.primary.startswith("worst") else "best"
        )
        selectors.append(combined_fallback)
        selectors = list(dict.fromkeys(selectors))
        return "/".join(selectors)


def build_audio_source_policy(
    target_format: object,
    audio_quality: object,
) -> AudioSourcePolicy:
    """Prefer a codec/container that can be copied into the final output."""
    target = str(target_format or "").strip().lower()
    quality = str(audio_quality or DEFAULT_AUDIO_QUALITY).strip().lower()
    prefix = "worstaudio" if quality == "worst" else "bestaudio"

    if target in {"m4a", "mp4"}:
        primary = f"{prefix}[ext=m4a]"
    elif target == "webm":
        primary = f"{prefix}[ext=webm]"
    else:
        primary = prefix

    audio_only_candidates: tuple[str, ...] = ()
    if target == "m4a":
        combined = "worst" if prefix == "worstaudio" else "best"
        audio_only_candidates = (
            primary,
            f"{prefix}[acodec^=mp4a]",
            f"{prefix}[acodec=aac]",
            f"{combined}[acodec^=mp4a]",
            f"{combined}[acodec=aac]",
            prefix,
        )

    return AudioSourcePolicy(
        primary=primary,
        fallback=prefix,
        audio_only_candidates=audio_only_candidates,
    )
