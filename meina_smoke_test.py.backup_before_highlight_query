"""めいなの主要ロジックを一括確認する軽量スモークテスト。

Whisper、Ollama、Tkinter、マイク、Twitch APIなどの重い実行環境は起動しない。
"""

from __future__ import annotations

from command_router import route_command
from meina_reminder_parser import parse_reminder_command
from meina_twitch_intent import is_twitch_clip_request, requested_day
from meina_voice_intent import (
    contains_wake_word,
    correct_recognition,
    is_invalid_command,
    remove_wake_word,
)


def assert_route(text: str, kind: str, target: str | None = None) -> None:
    route = route_command(text, {"confidence": 1.0})
    assert route is not None, f"no route: {text}"
    assert route["kind"] == kind, f"{text}: {route}"
    if target is not None:
        assert route["target"] == target, f"{text}: {route}"


def main() -> int:
    cases = (
        ("メモ帳を開いて", "app_open", "notepad"),
        ("Discordつけて", "app_open", "Discord"),
        ("VALOやる", "app_open", "VALORANT"),
        ("GoogleでVALORANTを検索して", "web_search", "google"),
        ("YouTubeでUVERworldの曲を探して", "web_search", "youtube"),
        ("最新のVALORANT情報を調べて", "web_search", "google"),
        ("今日の天気を教えて", "weather", "current"),
        ("明日の雨降る？", "weather", "current"),
        ("東京の明日雨降る？", "weather", "東京"),
        ("今何時？", "time", "local"),
        ("今日は何曜日？", "weekday", "local"),
        ("PCの状態を教えて", "pc_status", "pc"),
        ("18時に起こして", "reminder", "local"),
        ("明日18時に配信を予定に追加して", "reminder", "local"),
        ("30分後に知らせて", "reminder", "local"),
        ("あと30分で知らせて", "reminder", "local"),
        ("30分で知らせて", "reminder", "local"),
        ("明日の予定を教えて", "reminder_tomorrow", "local"),
        ("今後の予定を教えて", "reminder_upcoming", "local"),
        ("今日の配信の切り抜きを作って", "twitch_clip", "latest"),
        ("切り抜きの投稿準備して", "twitch_publish_prep", "latest"),
        ("配信中の見どころを監視して", "twitch_live_highlight", "live"),
        ("配信中の見どころ監視を停止して", "twitch_live_highlight_stop", "live"),
        ("何ができる？", "help", "meina"),
        ("めいなの状態を教えて", "self_status", "meina"),
    )

    for text, kind, target in cases:
        assert_route(text, kind, target)

    assert_route("音量を大きくして", "voice_volume", "up")
    assert_route("話す速度を速くして", "voice_rate", "fast")

    assert contains_wake_word("メイナー、メモ帳を開いて")
    assert contains_wake_word("メイ ナ、メモ帳を開いて")
    assert contains_wake_word("めーな、メモ帳を開いて")
    corrected = correct_recognition("メインなぁ、メモ帳を開いて")
    assert corrected == "メイナ、メモ帳を開いて", corrected
    assert correct_recognition("メイナ、エーペクスを開いて") == "メイナ、Apexを開いて"
    assert correct_recognition("メイナ、ディスコルドを開いて") == "メイナ、Discordを開いて"
    assert correct_recognition("メイナ、ユーチュブを開いて") == "メイナ、YouTubeを開いて"
    assert remove_wake_word(corrected) == "メモ帳を開いて"
    assert remove_wake_word("メイ ナ、メモ帳を開いて") == "メモ帳を開いて"
    assert remove_wake_word("めーな、メモ帳を開いて") == "メモ帳を開いて"
    assert is_invalid_command("ー")
    assert not is_invalid_command("メモ帳")

    parsed = parse_reminder_command("明日午後6時に配信予定を追加して")
    assert parsed is not None
    assert parsed["text"] == "配信"

    assert parse_reminder_command("あと30分で知らせて") is not None
    assert parse_reminder_command("30分で知らせて") is not None

    assert is_twitch_clip_request("昨日の配信切り抜いて")
    assert requested_day("昨日の配信切り抜いて") == "yesterday"
    assert requested_day("今日の配信をハイライトにして") == "today"

    print(f"Core smoke test: PASS ({len(cases) + 2} routes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
