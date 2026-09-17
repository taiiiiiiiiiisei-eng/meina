"""許可済みの音声コマンドだけをPC操作へ変換する安全なルーター。"""

import re


MIN_CONFIDENCE = 0.70

APP_ALIASES = {
    "notepad": ("メモ帳",),
    "calculator": ("電卓", "計算機"),
    "explorer": ("エクスプローラー", "ファイルエクスプローラー", "explorer"),
    "Discord": ("discord", "ディスコード"),
    "Steam": ("steam", "スチーム"),
    "Chrome": ("chrome", "クローム"),
    "Edge": ("edge", "エッジ"),
    "OBS": ("obs", "オービーエス"),
    "VALORANT": ("valorant", "バロラント"),
}

WEB_ALIASES = {
    "google": ("google", "グーグル"),
    "youtube": ("youtube", "ユーチューブ"),
}

PC_STATUS_PHRASES = (
    "pcの状態", "pc状態", "パソコンの状態", "パソコン状態",
    "pcのスペック", "パソコンのスペック", "pc情報", "パソコン情報",
    "メモリ使用量", "メモリの状態", "ディスク容量", "gpuの状態", "gpu情報",
)


def _compact(text):
    return re.sub(r"[\s　]+", "", str(text).lower())


def _find_alias(text, aliases):
    for canonical, values in aliases.items():
        if any(alias in text for alias in values):
            return canonical
    return None


def _confidence(frame):
    try:
        return float(frame.get("confidence", 0))
    except (AttributeError, TypeError, ValueError):
        return 0.0


def _extract_search_query(text, aliases):
    """サービス名と命令表現を取り除き、検索語だけを返す。"""
    query = text
    for alias in aliases:
        query = query.replace(alias, "", 1)
    query = re.sub(r"^(?:で|に|を|から)", "", query)
    query = re.sub(
        r"(?:について|に関して)?(?:を)?(?:検索|調べ|探)(?:する|して|して下さい|してください|て|て下さい|てください|す)?$",
        "",
        query,
    )
    query = query.strip("、。！？? ")
    return query or None


def route_command(text, frame):
    """安全に実行できる命令だけを固定形式で返し、それ以外は None を返す。"""
    # MEINA_TASK_PLAN_ROUTER_LOCAL_V1
    if text and "配信準備" in _compact(text):
        return {
            "kind": "task_plan",
            "target": "stream_prepare",
            "query": None,
            "confidence": 1.0,
        }

    # MEINA_REMINDER_ROUTER_V1
    if text and any(word in _compact(text) for word in ("リマインド", "リマインダー")):
        return {
            "kind": "reminder",
            "target": "local",
            "query": str(text).strip(),
            "confidence": 1.0,
        }

    if not text or _confidence(frame) < MIN_CONFIDENCE:
        return None

    command = _compact(text)
    is_search = any(word in command for word in ("検索", "調べ", "探して", "探す"))
    is_open = any(word in command for word in ("開く", "開いて", "起動", "立ち上げ"))

    if any(phrase in command for phrase in PC_STATUS_PHRASES):
        return {
            "kind": "pc_status",
            "target": "pc",
            "query": None,
            "confidence": _confidence(frame),
        }

    web_target = _find_alias(command, WEB_ALIASES)
    if web_target:
        aliases = WEB_ALIASES[web_target]
        if is_search:
            query = _extract_search_query(command, aliases)
            if query:
                return {
                    "kind": "web_search",
                    "target": web_target,
                    "query": query,
                    "confidence": _confidence(frame),
                }
            return None
        if is_open:
            return {
                "kind": "web_open",
                "target": web_target,
                "query": None,
                "confidence": _confidence(frame),
            }
        return None

    app_target = _find_alias(command, APP_ALIASES)
    if app_target and is_open:
        return {
            "kind": "app_open",
            "target": app_target,
            "query": None,
            "confidence": _confidence(frame),
        }

    return None
