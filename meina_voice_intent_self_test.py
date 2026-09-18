"""めいなの音声前処理の軽量セルフテスト。"""
from meina_voice_intent import (
    contains_wake_word,
    correct_recognition,
    is_invalid_command,
    normalize_text,
    remove_wake_word,
)


def main() -> int:
    assert contains_wake_word("めいな、メモ帳を開いて")
    assert contains_wake_word("メイナー、ブラウザを開いて")
    assert contains_wake_word(correct_recognition("メインなぁ、メモ帳を開いて"))
    assert contains_wake_word(" メ イ ナ ")
    assert contains_wake_word("メーな、メモ帳を開いて")
    assert contains_wake_word("めーな、メモ帳を開いて")
    assert contains_wake_word("メイな、メモ帳を開いて")
    assert not contains_wake_word("メモ帳を開いて")

    assert correct_recognition("メイナー、バロランを開いて") == "メイナ、バロラントを開いて"
    assert correct_recognition("メインなぁ、メモ帳を開いて") == "メイナ、メモ帳を開いて"
    assert correct_recognition("グーグルでUver Worldを検索") == "GoogleでUVERworldを検索"
    assert correct_recognition("グーグルでUber Worldを検索") == "GoogleでUVERworldを検索"

    assert normalize_text(" めいな　メモ帳 ") == "めいなメモ帳"
    assert remove_wake_word("メイナー、メモ帳を開いて") == "メモ帳を開いて"
    assert remove_wake_word("メイ ナ、メモ帳を開いて") == "メモ帳を開いて"
    assert remove_wake_word("メーな、メモ帳を開いて") == "メモ帳を開いて"
    assert remove_wake_word("めーな、メモ帳を開いて") == "メモ帳を開いて"
    assert remove_wake_word("めいなー") == ""
    assert is_invalid_command("ー")
    assert is_invalid_command("？")
    assert is_invalid_command("")
    assert not is_invalid_command("メモ帳")
    assert not is_invalid_command("開いて")

    print("Voice intent self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
