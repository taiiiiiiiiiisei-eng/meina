"""Lightweight Twitch voice-intent helpers.

This module intentionally has no network/ML dependencies so command routing
tests can run in minimal CI environments.
"""

from __future__ import annotations

import re


def is_twitch_clip_request(text: str) -> bool:
    compact = re.sub(r"\s+", "", text).lower()
    return (
        ("切り抜" in compact or "ハイライト" in compact)
        and (
            "配信" in compact
            or "twitch" in compact
            or "昨日" in compact
            or "今日" in compact
            or "最近" in compact
        )
    )


def requested_day(text: str) -> str | None:
    compact = re.sub(r"\s+", "", text)
    if "昨日" in compact:
        return "yesterday"
    if "今日" in compact:
        return "today"
    return None
