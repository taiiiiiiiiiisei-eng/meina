"""軽量なめいなの音声前処理・ウェイクワード判定。

Whisper本体や音声デバイスを起動せずにテストできるよう、
文字列処理だけを独立させる。
"""

from __future__ import annotations

WAKE_WORDS = (
    "めいな",
    "メイナ",
    "メイナー",
)


def correct_recognition(text: str) -> str:
    if not text:
        return ""

    corrections = (
        ("メイナー", "メイナ"),
        ("めいナー", "めいな"),
        ("メイナァ", "メイナ"),
        ("バロラン", "バロラント"),
        ("ばろらん", "バロラント"),
        ("Uberworld", "UVERworld"),
        ("Uber World", "UVERworld"),
        ("ユーバーワールド", "UVERworld"),
        ("ウーバーワールド", "UVERworld"),
        ("ディスコート", "Discord"),
        ("ディスコード", "Discord"),
        ("ユーチューブ", "YouTube"),
        ("ゆーちゅーぶ", "YouTube"),
        ("グーグル", "Google"),
        ("ぐーぐる", "Google"),
        ("エモ帳", "メモ帳"),
        ("えも帳", "メモ帳"),
    )
    result = str(text)
    for before, after in corrections:
        result = result.replace(before, after)
    return result


def normalize_text(text: str) -> str:
    if not text:
        return ""
    return str(text).replace(" ", "").replace("　", "")


def contains_wake_word(text: str) -> bool:
    normalized = normalize_text(text)
    if not normalized:
        return False
    return any(word in normalized for word in WAKE_WORDS)


def remove_wake_word(text: str) -> str:
    if not text:
        return ""

    result = str(text)
    for word in sorted(WAKE_WORDS, key=len, reverse=True):
        result = result.replace(word, "")

    result = result.strip(" 、,。.!！?？")
    result = result.strip("ー―—-")
    result = result.strip(" 、,。.!！?？")
    return result


def is_invalid_command(text: str) -> bool:
    if not text:
        return True

    value = str(text).strip()
    if not value:
        return True

    invalid_values = {
        "ー", "――", "―", "—", "-", "--",
        "?", "？", ".", "。", ",", "、",
        "!", "！", "あ", "え", "ん",
    }
    if value in invalid_values:
        return True

    for char in value:
        if char.isalnum():
            return False
        if "぀" <= char <= "ヿ":
            return False
        if "一" <= char <= "鿿":
            return False

    return True
