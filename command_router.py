"""許可済みの音声コマンドだけをPC操作へ変換する安全なルーター。"""

import re

MIN_CONFIDENCE = 0.70

APP_ALIASES = {
    "notepad": ("メモ帳",), "calculator": ("電卓", "計算機"),
    "explorer": ("エクスプローラー", "ファイルエクスプローラー", "explorer"),
    "Discord": ("discord", "ディスコード"), "Steam": ("steam", "スチーム"),
    "Chrome": ("chrome", "クローム"), "Edge": ("edge", "エッジ"),
    "OBS": ("obs", "オービーエス"),
    "VALORANT": ("valorant", "valo", "バロ", "バロラント", "ヴァロ", "ヴァロラント"),
    "Apex": ("apex", "エーペックス", "エペ", "apexlegends"),
}
WEB_ALIASES = {
    "google": ("google", "グーグル"),
    "youtube": ("youtube", "ユーチューブ"),
    "browser": ("ブラウザ", "ウェブブラウザ", "webブラウザ"),
}
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
    query = re.sub(r"(?:について|に関して)?(?:を)?(?:検索|調べ|探|ググ)(?:する|して|して下さい|してください|って|る|て|て下さい|てください|す)?$", "", query)
    return query.strip("、。！？? ") or None


def route_command(text, frame):
    """安全に実行できる命令だけを固定形式で返し、それ以外はNone。"""
    compact = _compact(text)
    if text:
        # 固定タスク計画の判定は meina_task_plans に集約
        from meina_task_plans import detect_task_plan
        plan_name = detect_task_plan(text)
        if plan_name:
            return {"kind": "task_plan", "target": plan_name, "query": None, "confidence": 1.0}
    # Neural TTSの話速・音量調整: 固定プリセットのみ許可
    if text:
        if any(p in compact for p in ("話す速度", "話速", "話し方")):
            if any(p in compact for p in ("速く", "早く", "速め", "早め")):
                return {"kind": "voice_rate", "target": "fast", "query": None, "confidence": 1.0}
            if any(p in compact for p in ("遅く", "ゆっくり", "遅め")):
                return {"kind": "voice_rate", "target": "slow", "query": None, "confidence": 1.0}
            if any(p in compact for p in ("普通", "標準")):
                return {"kind": "voice_rate", "target": "normal", "query": None, "confidence": 1.0}
        if any(p in compact for p in ("声の音量", "音量", "声を")) and any(p in compact for p in ("大きく", "上げて", "大きめ")):
            return {"kind": "voice_volume", "target": "up", "query": None, "confidence": 1.0}
        if any(p in compact for p in ("声の音量", "音量", "声を")) and any(p in compact for p in ("小さく", "下げて", "小さめ")):
            return {"kind": "voice_volume", "target": "down", "query": None, "confidence": 1.0}

    # Neural TTSの声変更: 「声をナナミにして」など
    if text:
        voice_aliases = {
            "nanami": ("ナナミ", "ななみ", "nanami"),
            "keita": ("ケイタ", "けいた", "keita"),
            "shiori": ("シオリ", "しおり", "shiori"),
        }
        if any(p in compact for p in ("声を", "ボイスを", "音声を")) and any(p in compact for p in ("変えて", "変更して", "切り替えて", "にして")):
            for preset, aliases in voice_aliases.items():
                if any(alias in compact for alias in aliases):
                    return {"kind": "voice_change", "target": preset, "query": None, "confidence": 1.0}

    # 天気・気温: 今日/明日、場所指定、「今何度？」など自然な聞き方に対応
    if text and any(p in compact for p in ("天気", "気温", "気候", "何度", "雨降る", "雨が降る", "雨降り", "降水確率", "傘いる", "傘必要", "傘は必要")):
        original = str(text).strip()
        mode = "today"
        if any(p in compact for p in ("今の気温", "現在の気温", "今何度", "現在何度", "何度ですか", "何℃", "何度？", "何度?")):
            mode = "current_temp"
        elif any(p in compact for p in ("雨", "雨降る", "雨が降る", "雨降り", "降水確率", "傘いる", "傘必要", "傘は必要")):
            mode = "tomorrow_rain" if "明日" in compact else "rain"
        elif "明日" in compact:
            mode = "tomorrow"

        location = original
        location = re.sub(r"(?:今日|明日|現在|今)の?", "", location)
        location = re.sub(r"(?:天気|気温|気候|何度|雨降る|雨が降る|雨降り|降水確率|傘いる|傘必要|傘は必要).*?$", "", location)
        location = re.sub(r"(?:について|を|が|は|教えて|教えてください|おしえて|おしえてください|知りたい|知ってる|知っています|ですか|です|？|\?)", "", location)
        location = location.strip("、。！？? 　")
        location = re.sub(r"(?:の|で|は|な)\s*$", "", location).strip()
        return {
            "kind": "weather",
            "target": location or "current",
            "query": mode,
            "confidence": 1.0,
        }
    if text and re.search(r"\d{1,2}\s*時(?:\s*\d{1,2}\s*分?)?|(?:あと\s*)?\d+\s*(?:秒|分|時間|時|日)\s*(?:後|で)", str(text)) and any(p in compact for p in ("起こして", "知らせて", "思い出させて", "教えて")):
        return {"kind": "reminder", "target": "local", "query": str(text).strip(), "confidence": 1.0}
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
    if text and any(p in compact for p in ("今後の予定", "予定表", "今週の予定", "これからの予定")):
        return {"kind": "reminder_upcoming", "target": "local", "query": None, "confidence": 1.0}

    # めいなのヘルプ・自己診断は固定応答にして、AIのconfidenceに依存させない。
    if text and any(p in compact for p in ("何ができる", "できること", "使えるコマンド", "コマンド一覧", "ヘルプ")):
        return {"kind": "help", "target": "meina", "query": None, "confidence": 1.0}
    if text and any(p in compact for p in ("めいなの状態", "めいな状態", "自己診断", "システムチェック", "動作確認")):
        return {"kind": "self_status", "target": "meina", "query": None, "confidence": 1.0}

    # ローカルサービス: PC状態・日時・Twitch
    if text and any(p in compact for p in PC_STATUS_PHRASES):
        return {"kind": "pc_status", "target": "pc", "query": None, "confidence": 1.0}
    if text and any(p in compact for p in ("何日", "何月何日", "今日はいつ", "今日の日付", "日付を教えて")):
        return {"kind": "date", "target": "local", "query": None, "confidence": 1.0}
    if text and any(p in compact for p in ("今何時", "現在時刻", "今の時間", "時間を教えて", "何時ですか", "何時？", "何時?")):
        return {"kind": "time", "target": "local", "query": None, "confidence": 1.0}
    if text and any(p in compact for p in ("何曜日", "曜日を教えて", "今日は何曜")):
        return {"kind": "weekday", "target": "local", "query": None, "confidence": 1.0}
    if text and any(p in compact for p in ("切り抜き", "ハイライト")) and any(p in compact for p in ("配信", "twitch", "昨日", "今日", "最近")):
        return {"kind": "twitch_clip", "target": "latest", "query": str(text).strip(), "confidence": 1.0}

    if not text or _confidence(frame) < MIN_CONFIDENCE: return None
    command = compact
    is_search = any(w in command for w in ("検索", "調べ", "探して", "探す", "ググって", "ググる"))
    is_open = any(w in command for w in ("開く", "開いて", "起動", "立ち上げ", "立ち上げて", "つけて", "つける", "付けて"))
    is_play = any(w in command for w in ("やる", "プレイ", "遊ぶ", "ゲームする", "始める"))
    # 自然なゲーム起動: 「VALOやる」「エペをプレイ」「Apexを始める」など
    game_target = _find_alias(command, APP_ALIASES)
    if game_target in ("VALORANT", "Apex") and (is_open or is_play):
        return {"kind": "app_open", "target": game_target, "query": None, "confidence": _confidence(frame)}
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
    if is_search:
        query = _extract_search_query(command, WEB_ALIASES["google"])
        if query:
            return {"kind": "web_search", "target": "google", "query": query, "confidence": _confidence(frame)}
        return None
    app_target = _find_alias(command, APP_ALIASES)
    if app_target and is_open:
        return {"kind": "app_open", "target": app_target, "query": None, "confidence": _confidence(frame)}
    return None
