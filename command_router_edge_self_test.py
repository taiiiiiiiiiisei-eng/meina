"""command_routerの不正入力・境界値を確認する軽量テスト。"""

from __future__ import annotations

from command_router import route_command
from meina_voice_intent import (
    contains_wake_word,
    correct_recognition,
    is_invalid_command,
    normalize_text,
    remove_wake_word,
)


def main() -> int:
    # 空値・None・壊れたconfidenceでは実行命令を返さない。
    assert route_command(None, None) is None
    assert route_command("", {}) is None
    assert route_command("メモ帳を開いて", None) is None
    assert route_command("メモ帳を開いて", {"confidence": "not-a-number"}) is None
    assert route_command("メモ帳を開いて", {"confidence": 0.69}) is None

    # 数値文字列のconfidenceは許容し、境界値0.70以上なら通常判定する。
    route = route_command("メモ帳を開いて", {"confidence": "0.70"})
    assert route is not None
    assert route["kind"] == "app_open"
    assert route["target"] == "notepad"

    # 想定外の入力型でもクラッシュせず、許可コマンドには変換しない。
    assert route_command(12345, {"confidence": 1.0}) is None
    assert route_command([], {"confidence": 1.0}) is None
    assert route_command({}, {"confidence": 1.0}) is None

    # 音声前処理も空値・数字で落ちない。
    assert correct_recognition(None) == ""
    assert normalize_text(None) == ""
    assert remove_wake_word(None) == ""
    assert not contains_wake_word(None)
    assert is_invalid_command(None)
    assert not is_invalid_command(12345)

    # 既知の無効入力は安全に破棄する。
    for value in ("", " ", "ー", "？", "――", "--"):
        assert is_invalid_command(value), value

    print("Router edge-case self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
