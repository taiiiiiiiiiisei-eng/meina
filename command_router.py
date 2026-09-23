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
    if (
        text
        and re.search(
            r"\d{1,2}\s*時(?:\s*\d{1,2}\s*分?)?|"
            r"(?:あと\s*)?\d+\s*(?:秒|分|時間|時|日)\s*(?:後|で)",
            str(text),
        )
        and any(p in compact for p in ("起こして", "知らせて", "思い出させて", "教えて"))
        and not any(
            p in compact
            for p in ("空き時間", "空いてる時間", "空いている時間")
        )
    ):
        return {"kind": "reminder", "target": "local", "query": str(text).strip(), "confidence": 1.0}
    if text:
        from meina_reminder_parser import parse_reminder_free_slot_add_command

        free_slot_add = parse_reminder_free_slot_add_command(text)
        if free_slot_add is not None:
            return {
                "kind": "reminder_schedule_free",
                "target": "local",
                "query": free_slot_add,
                "confidence": 1.0,
            }

    if text and any(p in compact for p in (
        "予定かぶってる",
        "予定被ってる",
        "予定重なってる",
        "予定の重なり",
        "スケジュールかぶってる",
        "スケジュール重複",
    )):
        return {
            "kind": "reminder_conflicts",
            "target": "local",
            "query": 7,
            "confidence": 1.0,
        }

    if text:
        free_match = re.search(
            r"(?:(?P<day>今日|明日)\s*)?"
            r"(?P<start_hour>\d{1,2})\s*時"
            r"(?:\s*(?P<start_minute>\d{1,2})\s*分)?"
            r"\s*から\s*"
            r"(?P<end_hour>\d{1,2})\s*時"
            r"(?:\s*(?P<end_minute>\d{1,2})\s*分)?"
            r"(?:\s*まで)?"
            r"(?:\s*(?:で|の中で|の)\s*(?P<need_num>\d{1,4})\s*(?P<need_unit>分|時間)(?:以上)?)?"
            r"(?:\s*の)?"
            r"(?:空き時間|空いてる時間|空いている時間|空き)",
            str(text),
        )
        if free_match and not any(
            p in compact
            for p in (
                "移して",
                "移してください",
                "移動して",
                "移動してください",
                "ずらして",
                "ずらしてください",
                "動かして",
                "動かしてください",
            )
        ):
            sh = int(free_match.group("start_hour"))
            sm = int(free_match.group("start_minute") or 0)
            eh = int(free_match.group("end_hour"))
            em = int(free_match.group("end_minute") or 0)
            if (
                0 <= sh <= 23
                and 0 <= eh <= 23
                and 0 <= sm <= 59
                and 0 <= em <= 59
                and (eh, em) > (sh, sm)
            ):
                return {
                    "kind": "reminder_free_time",
                    "target": "local",
                    "query": {
                        "day": free_match.group("day") or "今日",
                        "start_hour": sh,
                        "start_minute": sm,
                        "end_hour": eh,
                        "end_minute": em,
                        "minimum_minutes": (
                            int(free_match.group("need_num"))
                            * (60 if free_match.group("need_unit") == "時間" else 1)
                            if free_match.group("need_num")
                            else 15
                        ),
                    },
                    "confidence": 1.0,
                }

    if text and any(p in compact for p in (
        "今日の予定まとめ",
        "今日の予定をまとめて",
        "今日の予定をまとめて教えて",
        "今日の予定を簡単に教えて",
        "今日のスケジュールまとめ",
    )):
        return {"kind": "reminder_brief", "target": "local", "query": None, "confidence": 1.0}
    if text:
        soon_match = re.search(
            r"(?P<minutes>\d{1,4})\s*分以内(?:の)?(?:予定|リマインダー|リマインド)",
            str(text),
        )
        if soon_match:
            minutes = max(1, min(int(soon_match.group("minutes")), 1440))
            return {
                "kind": "reminder_soon",
                "target": "local",
                "query": minutes,
                "confidence": 1.0,
            }
        if any(p in compact for p in (
            "もうすぐの予定",
            "近い予定",
            "直近の予定",
            "もうすぐのリマインダー",
        )):
            return {
                "kind": "reminder_soon",
                "target": "local",
                "query": 30,
                "confidence": 1.0,
            }
    if text and any(p in compact for p in (
        "次の予定",
        "次のリマインダー",
        "次のリマインド",
        "一番近い予定",
        "次は何の予定",
    )):
        return {"kind": "reminder_next", "target": "local", "query": None, "confidence": 1.0}
    if text and any(p in compact for p in (
        "期限切れの予定",
        "期限切れ予定",
        "期限を過ぎた予定",
        "過ぎた予定",
        "遅れている予定",
    )):
        return {"kind": "reminder_overdue", "target": "local", "query": None, "confidence": 1.0}
    if text and any(p in compact for p in (
        "今月の予定",
        "今月のリマインダー",
        "今月のスケジュール",
    )):
        return {"kind": "reminder_month", "target": "local", "query": None, "confidence": 1.0}
    if text and any(p in compact for p in (
        "今週の予定",
        "今週のリマインダー",
        "今週のスケジュール",
    )):
        return {"kind": "reminder_week", "target": "local", "query": None, "confidence": 1.0}
    if text and any(p in compact for p in ("明日の予定", "明日のリマインダー", "明日のリマインド")):
        return {"kind": "reminder_tomorrow", "target": "local", "query": None, "confidence": 1.0}
    if text and any(p in compact for p in ("今日の予定", "今日のリマインダー", "今日のリマインド")):
        return {"kind": "reminder_today", "target": "local", "query": None, "confidence": 1.0}
    if text and any(p in compact for p in (
        "重要な予定",
        "大事な予定",
        "優先予定",
        "重要なリマインダー",
    )):
        return {"kind": "reminder_important", "target": "local", "query": None, "confidence": 1.0}
    if text and any(p in compact for p in ("リマインダー一覧", "リマインド一覧", "リマインダーを教えて", "リマインドを教えて")):
        return {"kind": "reminder_list", "target": "local", "query": None, "confidence": 1.0}
    if text:
        from meina_reminder_parser import (
            parse_reminder_action_request,
            parse_reminder_duration_command,
            parse_reminder_importance_command,
            parse_reminder_move_free_command,
            parse_reminder_pause_command,
            parse_reminder_pre_notify_clear_command,
            parse_reminder_pre_notify_set_command,
            parse_reminder_rename_command,
            parse_reminder_repeat_change_command,
            parse_reminder_repeat_clear_command,
            parse_reminder_resume_command,
            parse_reminder_reschedule_command,
            parse_reminder_snooze_command,
        )

        duration_change = parse_reminder_duration_command(text)
        if duration_change is not None:
            return {
                "kind": "reminder_duration",
                "target": "local",
                "query": duration_change,
                "confidence": 1.0,
            }

        move_free = parse_reminder_move_free_command(text)
        if move_free is not None:
            return {
                "kind": "reminder_move_free",
                "target": "local",
                "query": move_free,
                "confidence": 1.0,
            }

        importance = parse_reminder_importance_command(text)
        if importance is not None:
            return {
                "kind": "reminder_importance",
                "target": "local",
                "query": importance,
                "confidence": 1.0,
            }

        pre_notify_set = parse_reminder_pre_notify_set_command(text)
        if pre_notify_set is not None:
            return {
                "kind": "reminder_pre_notify_set",
                "target": "local",
                "query": pre_notify_set,
                "confidence": 1.0,
            }

        pre_notify_clear = parse_reminder_pre_notify_clear_command(text)
        if pre_notify_clear is not None:
            return {
                "kind": "reminder_pre_notify_clear",
                "target": "local",
                "query": pre_notify_clear,
                "confidence": 1.0,
            }

        pause_request = parse_reminder_pause_command(text)
        if pause_request is not None:
            return {
                "kind": "reminder_pause",
                "target": "local",
                "query": pause_request,
                "confidence": 1.0,
            }

        resume_request = parse_reminder_resume_command(text)
        if resume_request is not None:
            return {
                "kind": "reminder_resume",
                "target": "local",
                "query": resume_request,
                "confidence": 1.0,
            }

        repeat_change = parse_reminder_repeat_change_command(text)
        if repeat_change is not None:
            return {
                "kind": "reminder_repeat_set",
                "target": "local",
                "query": repeat_change,
                "confidence": 1.0,
            }

        repeat_clear = parse_reminder_repeat_clear_command(text)
        if repeat_clear is not None:
            return {
                "kind": "reminder_repeat_clear",
                "target": "local",
                "query": repeat_clear,
                "confidence": 1.0,
            }

        snooze = parse_reminder_snooze_command(text)
        if snooze is not None:
            return {
                "kind": "reminder_snooze",
                "target": "local",
                "query": snooze,
                "confidence": 1.0,
            }

        reschedule = parse_reminder_reschedule_command(text)
        if reschedule is not None:
            return {
                "kind": "reminder_reschedule",
                "target": "local",
                "query": reschedule,
                "confidence": 1.0,
            }

        rename = parse_reminder_rename_command(text)
        if rename is not None:
            return {
                "kind": "reminder_rename",
                "target": "local",
                "query": rename,
                "confidence": 1.0,
            }

        done_request = parse_reminder_action_request(text, "done")
        if done_request is not None:
            has_due_filter = any(
                done_request.get(key) is not None
                for key in ("date", "hour", "minute")
            )
            return {
                "kind": "reminder_done",
                "target": "local",
                "query": done_request if has_due_filter else done_request.get("target", ""),
                "confidence": 1.0,
            }

        delete_request = parse_reminder_action_request(text, "delete")
        if delete_request is not None:
            has_due_filter = any(
                delete_request.get(key) is not None
                for key in ("date", "hour", "minute")
            )
            return {
                "kind": "reminder_delete",
                "target": "local",
                "query": delete_request if has_due_filter else delete_request.get("target", ""),
                "confidence": 1.0,
            }
    if text and any(p in compact for p in (
        "予定を追加",
        "予定に追加",
        "予定として追加",
        "予定を登録",
        "予定に登録",
        "予定を入れて",
        "スケジュールを追加",
        "スケジュールに追加",
        "スケジュールを登録",
    )):
        return {"kind": "reminder", "target": "local", "query": str(text).strip(), "confidence": 1.0}
    if text and any(p in compact for p in ("リマインド", "リマインダー")):
        return {"kind": "reminder", "target": "local", "query": str(text).strip(), "confidence": 1.0}
    if text and any(p in compact for p in ("今後の予定", "予定表", "これからの予定")):
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
    if text and any(p in compact for p in ("配信中の見どころ監視を停止", "ライブ中の見どころ監視を停止", "見どころ監視を停止", "ハイライト監視を停止", "配信中のハイライト監視を停止")):
        return {"kind": "twitch_live_highlight_stop", "target": "live", "query": str(text).strip(), "confidence": 1.0}
    if text and any(p in compact for p in ("おすすめの見どころを切り抜", "おすすめハイライトを切り抜", "選んだ見どころを切り抜", "おすすめの切り抜きを作", "おすすめの切り抜き作")):
        return {"kind": "twitch_shortlist_clip", "target": "latest", "query": str(text).strip(), "confidence": 1.0}
    if text and any(p in compact for p in ("おすすめの見どころ", "おすすめハイライト", "一番面白い見どころ", "切り抜き候補を選んで", "見どころを選んで")):
        return {"kind": "twitch_live_highlight_shortlist", "target": "live", "query": str(text).strip(), "confidence": 1.0}
    if text and any(p in compact for p in ("見どころを教えて", "見どころ一覧", "見どころ候補", "最新の見どころ", "ハイライトを教えて")):
        return {"kind": "twitch_live_highlight_list", "target": "live", "query": str(text).strip(), "confidence": 1.0}
    if text and any(p in compact for p in ("配信中の見どころ", "ライブ中の見どころ", "見どころ監視", "ハイライト監視", "配信中のハイライト監視")):
        return {"kind": "twitch_live_highlight", "target": "live", "query": str(text).strip(), "confidence": 1.0}
    if text and any(p in compact for p in ("投稿準備", "投稿用に準備", "投稿文を作って", "投稿文を準備", "切り抜きを投稿用", "切り抜きの投稿準備")) and any(p in compact for p in ("切り抜き", "配信", "twitch", "動画")):
        return {"kind": "twitch_publish_prep", "target": "latest", "query": str(text).strip(), "confidence": 1.0}
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
