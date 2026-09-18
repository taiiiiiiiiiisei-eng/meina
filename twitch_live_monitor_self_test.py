"""Twitchライブ監視の依存軽量セルフテスト。"""

from __future__ import annotations

from twitch_live_monitor import stream_transition


def main() -> int:
    assert stream_transition(False, None) == "offline"
    assert stream_transition(False, {"id": "stream-1"}) == "started"
    assert stream_transition(True, {"id": "stream-1"}) == "live"
    assert stream_transition(True, None) == "ended"

    print("Twitch live monitor self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
