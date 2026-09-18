"""軽量なめいなの音声前処理・ウェイクワード判定。

Whisper本体や音声デバイスを起動せずにテストできるよう、
文字列処理だけを独立させる。
"""

from __future__ import annotations

import re

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
        ("メイナぁ", "メイナ"),
        ("めいなぁ", "めいな"),
        ("めいなー", "めいな"),
        ("めーな", "めいな"),
        ("メーな", "メイナ"),
        ("メイな", "メイナ"),
        ("メイ ナ", "メイナ"),
        ("めい な", "めいな"),
        ("メイ　ナ", "メイナ"),
        ("めい　な", "めいな"),
        ("メインなぁ", "メイナ"),
        ("メインな", "メイナ"),
        ("バロラン", "バロラント"),
        ("ばろらん", "バロラント"),
        ("ヴァロラン", "バロラント"),
        ("ゔぁろらん", "バロラント"),
        ("エーペクス", "Apex"),
        ("エイペックス", "Apex"),
        ("Uberworld", "UVERworld"),
        ("Uber World", "UVERworld"),
        ("Uver World", "UVERworld"),
        ("ユーバーワールド", "UVERworld"),
        ("ウーバーワールド", "UVERworld"),
        ("ディスコート", "Discord"),
        ("ディスコード", "Discord"),
        ("ディスコルド", "Discord"),
        ("ユーチューブ", "YouTube"),
        ("ユーチュブ", "YouTube"),
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


def _remove_fuzzy_wake_words(text: str) -> str:
    """Whisperが入れる空白や長音の揺れを許容してウェイクワードを除去する。"""
    result = str(text)
    patterns = (
        r"め[\s　ー]*い[\s　ー]*な[\s　ー]*(?:ー|ぁ|あ)?",
        r"メ[\s　ー]*イ[\s　ー]*ナ[\s　ー]*(?:ー|ァ|ぁ|ア)?",
        r"メ[\s　ー]*ー[\s　]*ナ[\s　ー]*(?:ー|ァ|ぁ|ア)?",
    )
    for pattern in patterns:
        result = re.sub(pattern, "", result)
    return result


def contains_wake_word(text: str) -> bool:
    corrected = correct_recognition(text)
    normalized = normalize_text(corrected)
    if not normalized:
        return False
    return any(word in normalized for word in WAKE_WORDS)


def remove_wake_word(text: str) -> str:
    if not text:
        return ""

    result = correct_recognition(str(text))
    result = _remove_fuzzy_wake_words(result)

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


def listen_command_with_retry(listen_fn, attempts: int = 2, duration: float = 5.0) -> str:
    """音声命令を最大attempts回聞き、最初の有効な認識結果を返す。"""
    try:
        max_attempts = max(1, int(attempts))
    except (TypeError, ValueError):
        max_attempts = 2

    for _ in range(max_attempts):
        try:
            text = listen_fn(duration=duration)
        except Exception:
            text = ""
        if text and not is_invalid_command(text):
            return str(text).strip()
    return ""
