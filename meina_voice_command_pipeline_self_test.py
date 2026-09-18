"""音声入力から安全なコマンドルーティングまでの軽量統合テスト。"""

from __future__ import annotations

from command_router import route_command
from meina_voice_intent import (
    contains_wake_word,
    correct_recognition,
    is_invalid_command,
    remove_wake_word,
)


def run_voice_case(raw_text: str):
    corrected = correct_recognition(raw_text)
    assert contains_wake_word(corrected), f"wake not detected: {raw_text!r} -> {corrected!r}"

    command = remove_wake_word(corrected)
    assert not is_invalid_command(command), f"invalid command: {raw_text!r} -> {command!r}"

    route = route_command(command, {"confidence": 1.0})
    assert route is not None, f"no route: {raw_text!r} -> {command!r}"
    return corrected, command, route


def main() -> int:
    cases = (
        ("メイナ、メモ帳を開いて", "app_open", "notepad"),
        ("メインなぁ、ディスコルドを開いて", "app_open", "Discord"),
        ("メーな、ユーチュブでUver Worldの曲を探して", "web_search", "youtube"),
        ("メイ ナ、ヴァロランをやる", "app_open", "VALORANT"),
        ("めーな、エーペクスを始める", "app_open", "Apex"),
        ("メイナー、最新のVALORANT情報を調べて", "web_search", "google"),
        ("メイナ、18時に起こして", "reminder", "local"),
        ("メイナ、配信中の見どころを監視して", "twitch_live_highlight", "live"),
        ("メイナ、配信中の見どころ監視を停止して", "twitch_live_highlight_stop", "live"),
        ("メイナ、最新の見どころを教えて", "twitch_live_highlight_list", "live"),
        ("メイナ、おすすめの見どころを教えて", "twitch_live_highlight_shortlist", "live"),
    )

    for raw_text, expected_kind, expected_target in cases:
        corrected, command, route = run_voice_case(raw_text)
        assert route["kind"] == expected_kind, (raw_text, corrected, command, route)
        assert route["target"] == expected_target, (raw_text, corrected, command, route)

    assert not contains_wake_word("メモ帳を開いて")
    assert route_command("メモ帳を開いて", {"confidence": 0.1}) is None

    print(f"Voice command pipeline self-test: PASS ({len(cases)} cases)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
