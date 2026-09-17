"""許可済みの音声コマンドだけをPC操作へ変換する安全なルーター。"""

import re

MIN_CONFIDENCE = 0.70

APP_ALIASES = {
    "notepad": ("メモ帳",), "calculator": ("電卓", "計算機"),
    "explorer": ("エクスプローラー", "ファイルエクスプローラー", "explorer"),
    "Discord": ("discord", "ディスコード"), "Steam": ("steam", "スチーム"),
    "Chrome": ("chrome", "クローム"), "Edge": ("edge", "エッジ"),
    "OBS": ("obs", "オービーエス"), "VALORANT": ("valorant", "バロラント"),
}
WEB_ALIASES = {"google": ("google", "グーグル"), "youtube": ("youtube", "ユーチューブ")}
PC_STATUS_PHRASES = (
    "pcの状態", "pc状態", "パソコンの状態", "パソコン状態", "pcのスペック",
    "パソコンのスペック", "pc情報", "パソコン情報", "メモリ使用量", "メモリの状態",
    "ディスク容量", "gpuの状態", "gpu情報",
)


def _compact(text):
    return re.sub(r"[\s　]+", "", str(text).lower())


def _find_alias(text, aliases):
    for canonical, values in aliases.items():
        if any(alias in text for alias in values): return canonical
    return None


def _confidence(frame):
    try: return float(frame.get("confidence", 0))
    except (AttributeError, TypeError, ValueError): return 0.0


def _extract_search_query(text, aliases):
    query = text
    for alias in aliases: query = query.replace(alias, "", 1)
    query = re.sub(r"^(?:で|に|を|から)", "", query)
    query = re.sub(r"(?:について|に関して)?(?:を)?(?:検索|調べ|探)(?:する|して|して下さい|してください|て|て下さい|てください|す)?$", "", query)
    return query.strip("、。！？? ") or None


def route_command(text, frame):
    """安全に実行できる命令だけを固定形式で返し、それ以外はNone。"""
    compact = _compact(text)
    if text and "配信準備" in compact:
        return {"kind": "task_plan", "target": "stream_prepare", "query": None, "confidence": 1.0}

    # MEINA_SCHEDULE_ROUTER_V1
    if text and any(p in compact for p in ("明日の予定", "明日のリマインダー", "明日のリマインド")):
        return {"kind": "reminder_tomorrow", "target": "local", "query": None, "confidence": 1.0}
    if text and any(p in compact for p in ("今日の予定", "今日のリマインダー", "今日のリマインド")):
        return {"kind": "reminder_today", "target": "local", "query": None, "confidence": 1.0}
    if text and any(p in compact for p in ("リマインダー一覧", "リマインド一覧", "リマインダーを教えて", "リマインドを教えて")):
        return {"kind": "reminder_list", "target": "local", "query": None, "confidence": 1.0}
    if text and any(p in compact for p in ("リマインダーを完了", "リマインドを完了", "リマインダー完了")):
        return {"kind": "reminder_done", "target": "local", "query": str(text).strip(), "confidence": 1.0}
    if text and any(p in compact for p in ("リマインダーを削除", "リマインドを削除", "リマインダー削除")):
        return {"kind": "reminder_delete", "target": "local", "query": str(text).strip(), "confidence": 1.0}
    if text and any(p in compact for p in ("予定を追加", "予定を登録", "予定を入れて", "スケジュールを追加", "スケジュールを登録")):
        return {"kind": "reminder", "target": "local", "query": str(text).strip(), "confidence": 1.0}
    if text and any(p in compact for p in ("リマインド", "リマインダー")):
        return {"kind": "reminder", "target": "local", "query": str(text).strip(), "confidence": 1.0}

    if not text or _confidence(frame) < MIN_CONFIDENCE: return None
    command = compact
    is_search = any(w in command for w in ("検索", "調べ", "探して", "探す"))
    is_open = any(w in command for w in ("開く", "開いて", "起動", "立ち上げ"))
    if any(p in command for p in PC_STATUS_PHRASES):
        return {"kind": "pc_status", "target": "pc", "query": None, "confidence": _confidence(frame)}
    web_target = _find_alias(command, WEB_ALIASES)
    if web_target:
        aliases = WEB_ALIASES[web_target]
        if is_search:
            query = _extract_search_query(command, aliases)
            if query: return {"kind": "web_search", "target": web_target, "query": query, "confidence": _confidence(frame)}
            return None
        if is_open: return {"kind": "web_open", "target": web_target, "query": None, "confidence": _confidence(frame)}
    app_target = _find_alias(command, APP_ALIASES)
    if app_target and is_open:
        return {"kind": "app_open", "target": app_target, "query": None, "confidence": _confidence(frame)}
    return None
