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
    if text:
        from meina_reminder_parser import parse_reminder_detail_command

        detail_request = parse_reminder_detail_command(text)
        if detail_request is not None:
            return {
                "kind": "reminder_detail",
                "target": "local",
                "query": detail_request,
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
            for p in (
                "空き時間",
                "空いてる時間",
                "空いている時間",
                "予定のメモ",
                "予定メモ",
                "リマインダーのメモ",
                "リマインドのメモ",
                "予定の場所",
                "予定場所",
                "リマインダーの場所",
                "リマインドの場所",
            )
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
            r"(?:\s*(?:で|の中で))?"
            r"(?:\s*の)?"
            r"(?:空き時間|空いてる時間|空いている時間|空き|"
            r"どれくらい空いてる|何分空いてる)",
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
                query_data = {
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
                }
                aggregate_free = any(
                    p in compact
                    for p in (
                        "空き時間合計",
                        "空きの合計",
                        "何分空いて",
                        "どれくらい空いて",
                    )
                )
                if aggregate_free:
                    return {
                        "kind": "reminder_free_total",
                        "target": "local",
                        "query": query_data,
                        "confidence": 1.0,
                    }
                return {
                    "kind": "reminder_free_time",
                    "target": "local",
                    "query": query_data,
                    "confidence": 1.0,
                }

    if text and any(p in compact for p in (
        "今日あとどれくらい空いてる",
        "今日あと何分空いてる",
        "今日あと何時間空いてる",
        "今日の残りどれくらい空いてる",
        "今日の残り何分空いてる",
    )):
        return {
            "kind": "reminder_remaining_today",
            "target": "local",
            "query": None,
            "confidence": 1.0,
        }

    if text and any(p in compact for p in (
        "今日どれくらい忙しい",
        "今日どれくらい予定詰まってる",
        "今日の予定どれくらい詰まってる",
        "今日の予定の詰まり具合",
    )):
        return {
            "kind": "reminder_day_load",
            "target": "local",
            "query": "today",
            "confidence": 1.0,
        }

    if text and any(p in compact for p in (
        "明日どれくらい忙しい",
        "明日どれくらい予定詰まってる",
        "明日の予定どれくらい詰まってる",
        "明日の予定の詰まり具合",
    )):
        return {
            "kind": "reminder_day_load",
            "target": "local",
            "query": "tomorrow",
            "confidence": 1.0,
        }

    if text and any(p in compact for p in (
        "今週いちばん予定が多い日",
        "今週一番予定が多い日",
        "今週予定が一番多い日",
        "今週予定がいちばん多い日",
    )):
        return {
            "kind": "reminder_week_peak",
            "target": "local",
            "query": "count",
            "confidence": 1.0,
        }

    if text and any(p in compact for p in (
        "今週いちばん忙しい日",
        "今週一番忙しい日",
        "今週いちばん詰まってる日",
        "今週一番詰まってる日",
        "今週予定時間が一番長い日",
    )):
        return {
            "kind": "reminder_week_peak",
            "target": "local",
            "query": "duration",
            "confidence": 1.0,
        }

    if text:
        grouped_duration_scope_map = {
            "今日": "today",
            "明日": "tomorrow",
            "今週": "week",
            "今月": "month",
        }
        category_duration_summary_match = re.fullmatch(
            r"(?P<scope>今日|明日|今週|今月)(?:の)?"
            r"カテゴリ(?:別|ごとの)"
            r"(?:予定時間|時間)(?:合計|内訳)?"
            r"(?:を)?(?:教えて|見せて|確認して|確認してください)?[?？]?",
            str(text).strip(),
        )
        if category_duration_summary_match:
            return {
                "kind": "reminder_category_duration_summary",
                "target": "local",
                "query": grouped_duration_scope_map[
                    category_duration_summary_match.group("scope")
                ],
                "confidence": 1.0,
            }

        location_duration_summary_match = re.fullmatch(
            r"(?P<scope>今日|明日|今週|今月)(?:の)?"
            r"場所(?:別|ごとの)"
            r"(?:予定時間|時間)(?:合計|内訳)?"
            r"(?:を)?(?:教えて|見せて|確認して|確認してください)?[?？]?",
            str(text).strip(),
        )
        if location_duration_summary_match:
            return {
                "kind": "reminder_location_duration_summary",
                "target": "local",
                "query": grouped_duration_scope_map[
                    location_duration_summary_match.group("scope")
                ],
                "confidence": 1.0,
            }

    if text:
        category_duration_match = re.fullmatch(
            r"(?P<category>.+?)カテゴリ(?:の|で)?"
            r"(?P<scope>今日|明日|今週|今月)(?:の)?"
            r"(?:予定時間合計|予定の時間合計|何時間予定(?:入ってる)?)"
            r"[?？]?",
            str(text).strip(),
        )
        if category_duration_match:
            scope_text = category_duration_match.group("scope")
            scope_map = {
                "今日": "today",
                "明日": "tomorrow",
                "今週": "week",
                "今月": "month",
            }
            category = category_duration_match.group("category").strip()
            if category and len(category) <= 32:
                return {
                    "kind": "reminder_duration_total",
                    "target": "local",
                    "query": {
                        "scope": scope_map[scope_text],
                        "category": category,
                    },
                    "confidence": 1.0,
                }

        location_duration_match = re.fullmatch(
            r"(?:場所(?:が|は))?(?P<location>.+?)で"
            r"(?P<scope>今日|明日|今週|今月)(?:の)?"
            r"(?:予定時間合計|予定の時間合計|何時間予定(?:入ってる)?)"
            r"[?？]?",
            str(text).strip(),
        )
        if location_duration_match:
            scope_text = location_duration_match.group("scope")
            scope_map = {
                "今日": "today",
                "明日": "tomorrow",
                "今週": "week",
                "今月": "month",
            }
            location = location_duration_match.group("location").strip()
            if location and len(location) <= 100:
                return {
                    "kind": "reminder_duration_total",
                    "target": "local",
                    "query": {
                        "scope": scope_map[scope_text],
                        "location": location,
                    },
                    "confidence": 1.0,
                }

    scoped_missing_duration_phrases = {
        "今日の所要時間未設定の予定": "today",
        "今日の所要時間がない予定": "today",
        "明日の所要時間未設定の予定": "tomorrow",
        "明日の所要時間がない予定": "tomorrow",
        "今週の所要時間未設定の予定": "week",
        "今週の所要時間がない予定": "week",
        "今月の所要時間未設定の予定": "month",
        "今月の所要時間がない予定": "month",
    }
    for phrase, scope in scoped_missing_duration_phrases.items():
        if phrase in compact:
            return {
                "kind": "reminder_missing_duration",
                "target": "local",
                "query": scope,
                "confidence": 1.0,
            }

    if text and any(p in compact for p in (
        "所要時間未設定の予定",
        "所要時間がない予定",
        "時間未設定の予定",
        "長さ未設定の予定",
    )):
        return {
            "kind": "reminder_missing_duration",
            "target": "local",
            "query": None,
            "confidence": 1.0,
        }

    if text and any(p in compact for p in (
        "今月の予定時間合計",
        "今月の予定の時間合計",
        "今月何時間予定",
        "今月どれくらい予定入ってる",
        "今月の予定時間",
    )):
        return {
            "kind": "reminder_duration_total",
            "target": "local",
            "query": "month",
            "confidence": 1.0,
        }

    if text and any(p in compact for p in (
        "今週の予定時間合計",
        "今週の予定の時間合計",
        "今週何時間予定",
        "今週どれくらい予定入ってる",
        "今週の予定時間",
    )):
        return {
            "kind": "reminder_duration_total",
            "target": "local",
            "query": "week",
            "confidence": 1.0,
        }

    if text and any(p in compact for p in (
        "今日の予定時間合計",
        "今日の予定の時間合計",
        "今日何時間予定",
        "今日どれくらい予定入ってる",
        "今日の予定時間",
    )):
        return {
            "kind": "reminder_duration_total",
            "target": "local",
            "query": "today",
            "confidence": 1.0,
        }

    if text and any(p in compact for p in (
        "明日の予定時間合計",
        "明日の予定の時間合計",
        "明日何時間予定",
        "明日どれくらい予定入ってる",
        "明日の予定時間",
    )):
        return {
            "kind": "reminder_duration_total",
            "target": "local",
            "query": "tomorrow",
            "confidence": 1.0,
        }

    if text and any(p in compact for p in (
        "次に何やればいい",
        "次何すればいい",
        "今何やればいい",
        "次にやること",
        "次にやる予定",
        "次に何する",
    )):
        return {
            "kind": "reminder_next_action",
            "target": "local",
            "query": None,
            "confidence": 1.0,
        }

    if text and any(p in compact for p in (
        "今日の優先予定",
        "今日優先する予定",
        "今日の予定の優先順位",
        "今日やること優先順",
        "今日のやること優先順",
    )):
        return {
            "kind": "reminder_priority_today",
            "target": "local",
            "query": None,
            "confidence": 1.0,
        }

    if text:
        focus_match = re.search(
            r"(?:(?P<day>今日|明日)\s*)?"
            r"(?P<num>\d{1,4})\s*(?P<unit>分|時間)"
            r"(?:くらい|以上)?\s*"
            r"(?:集中できる(?:時間|空き時間)?|"
            r"まとまって空いてる(?:時間)?|"
            r"まとまった空き時間)",
            str(text),
        )
        if focus_match:
            amount = int(focus_match.group("num"))
            minutes = amount * (60 if focus_match.group("unit") == "時間" else 1)
            if 1 <= minutes <= 1440:
                return {
                    "kind": "reminder_focus_slot",
                    "target": "local",
                    "query": {
                        "day": focus_match.group("day") or "今日",
                        "duration_minutes": minutes,
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
    if text:
        note_presence_scope_map = {
            None: "all",
            "今日": "today",
            "明日": "tomorrow",
            "今週": "week",
            "今月": "month",
        }
        note_presence_summary_match = re.fullmatch(
            r"(?:(?P<scope>今日|明日|今週|今月)(?:の)?)?"
            r"(?P<state>メモ付き|メモあり|メモ未設定|メモなし)"
            r"(?:の)?(?:予定|リマインダー|リマインド)?"
            r"(?:は)?(?:何件|件数)"
            r"(?:を)?(?:教えて|見せて|確認して|確認してください)?[?？]?",
            str(text).strip(),
        )
        if note_presence_summary_match:
            state = note_presence_summary_match.group("state")
            return {
                "kind": "reminder_note_presence",
                "target": "local",
                "query": {
                    "scope": note_presence_scope_map[
                        note_presence_summary_match.group("scope")
                    ],
                    "has_note": state in ("メモ付き", "メモあり"),
                    "summary": True,
                },
                "confidence": 1.0,
            }

        note_presence_list_match = re.fullmatch(
            r"(?:(?P<scope>今日|明日|今週|今月)(?:の)?)?"
            r"(?P<state>メモ付き|メモあり|メモ未設定|メモなし)"
            r"(?:の)?(?:予定|リマインダー|リマインド)"
            r"(?:を)?(?:教えて|見せて|一覧|確認して|確認してください)?[?？]?",
            str(text).strip(),
        )
        if note_presence_list_match:
            state = note_presence_list_match.group("state")
            return {
                "kind": "reminder_note_presence",
                "target": "local",
                "query": {
                    "scope": note_presence_scope_map[
                        note_presence_list_match.group("scope")
                    ],
                    "has_note": state in ("メモ付き", "メモあり"),
                    "summary": False,
                },
                "confidence": 1.0,
            }

    if text:
        scoped_list_scope_map = {
            "今日": "today",
            "明日": "tomorrow",
            "今週": "week",
            "今月": "month",
        }
        scoped_category_list_patterns = (
            r"(?P<scope>今日|明日|今週|今月)(?:の)?"
            r"(?P<category>.+?)カテゴリ(?:の)?"
            r"(?:予定|リマインダー|リマインド)"
            r"(?:を)?(?:教えて|見せて|一覧|確認して|確認してください)?[?？]?",
            r"(?P<category>.+?)カテゴリ(?:の)?"
            r"(?P<scope>今日|明日|今週|今月)(?:の)?"
            r"(?:予定|リマインダー|リマインド)"
            r"(?:を)?(?:教えて|見せて|一覧|確認して|確認してください)?[?？]?",
        )
        for pattern in scoped_category_list_patterns:
            scoped_category_list_match = re.fullmatch(pattern, str(text).strip())
            if not scoped_category_list_match:
                continue
            category = scoped_category_list_match.group("category").strip()
            if category and len(category) <= 32:
                return {
                    "kind": "reminder_category_list",
                    "target": "local",
                    "query": {
                        "scope": scoped_list_scope_map[
                            scoped_category_list_match.group("scope")
                        ],
                        "category": category,
                    },
                    "confidence": 1.0,
                }

        scoped_location_list_patterns = (
            r"(?P<scope>今日|明日|今週|今月)(?:の)?"
            r"(?P<location>.+?)(?:での|にある)"
            r"(?:予定|リマインダー|リマインド)"
            r"(?:を)?(?:教えて|見せて|一覧|確認して|確認してください)?[?？]?",
            r"(?P<location>.+?)(?:での|にある)"
            r"(?P<scope>今日|明日|今週|今月)(?:の)?"
            r"(?:予定|リマインダー|リマインド)"
            r"(?:を)?(?:教えて|見せて|一覧|確認して|確認してください)?[?？]?",
            r"(?P<scope>今日|明日|今週|今月)(?:の)?"
            r"場所(?:が|は)(?P<location>.+?)の"
            r"(?:予定|リマインダー|リマインド)"
            r"(?:を)?(?:教えて|見せて|一覧|確認して|確認してください)?[?？]?",
            r"場所(?:が|は)(?P<location>.+?)の"
            r"(?P<scope>今日|明日|今週|今月)(?:の)?"
            r"(?:予定|リマインダー|リマインド)"
            r"(?:を)?(?:教えて|見せて|一覧|確認して|確認してください)?[?？]?",
        )
        for pattern in scoped_location_list_patterns:
            scoped_location_list_match = re.fullmatch(pattern, str(text).strip())
            if not scoped_location_list_match:
                continue
            location = scoped_location_list_match.group("location").strip()
            if location and len(location) <= 100:
                return {
                    "kind": "reminder_location_list",
                    "target": "local",
                    "query": {
                        "scope": scoped_list_scope_map[
                            scoped_location_list_match.group("scope")
                        ],
                        "location": location,
                    },
                    "confidence": 1.0,
                }

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
    if text:
        category_completed_match = re.fullmatch(
            r"(?P<category>.+?)カテゴリ(?:で|の)?"
            r"(?P<scope>今日|今週|今月)"
            r"(?:終わった|完了した|済ませた)"
            r"(?:予定|リマインダー|リマインド)"
            r"(?:を)?(?:教えて|見せて|一覧|確認して|確認してください)?[?？]?",
            str(text).strip(),
        )
        if category_completed_match:
            category = category_completed_match.group("category").strip()
            if category and len(category) <= 32:
                return {
                    "kind": "reminder_completed_period",
                    "target": "local",
                    "query": {
                        "scope": (
                            "month"
                            if category_completed_match.group("scope") == "今月"
                            else (
                                "week"
                                if category_completed_match.group("scope") == "今週"
                                else "today"
                            )
                        ),
                        "category": category,
                    },
                    "confidence": 1.0,
                }

        location_completed_match = re.fullmatch(
            r"(?:場所(?:が|は))?(?P<location>.+?)で"
            r"(?P<scope>今日|今週|今月)"
            r"(?:終わった|完了した|済ませた)"
            r"(?:予定|リマインダー|リマインド)"
            r"(?:を)?(?:教えて|見せて|一覧|確認して|確認してください)?[?？]?",
            str(text).strip(),
        )
        if location_completed_match:
            location = location_completed_match.group("location").strip()
            if location and len(location) <= 100:
                return {
                    "kind": "reminder_completed_period",
                    "target": "local",
                    "query": {
                        "scope": (
                            "month"
                            if location_completed_match.group("scope") == "今月"
                            else (
                                "week"
                                if location_completed_match.group("scope") == "今週"
                                else "today"
                            )
                        ),
                        "location": location,
                    },
                    "confidence": 1.0,
                }

    if text and any(p in compact for p in (
        "今月終わった予定",
        "今月完了した予定",
        "今月済ませた予定",
        "今月終わったリマインダー",
        "今月完了したリマインダー",
    )):
        return {
            "kind": "reminder_completed_period",
            "target": "local",
            "query": {"scope": "month", "category": None},
            "confidence": 1.0,
        }

    if text and any(p in compact for p in (
        "今週終わった予定",
        "今週完了した予定",
        "今週済ませた予定",
        "今週終わったリマインダー",
        "今週完了したリマインダー",
    )):
        return {
            "kind": "reminder_completed_period",
            "target": "local",
            "query": {"scope": "week", "category": None},
            "confidence": 1.0,
        }

    if text and any(p in compact for p in (
        "今日終わった予定",
        "今日完了した予定",
        "今日済ませた予定",
        "今日終わったリマインダー",
        "今日完了したリマインダー",
    )):
        return {
            "kind": "reminder_completed_today",
            "target": "local",
            "query": None,
            "confidence": 1.0,
        }

    if text and any(p in compact for p in (
        "今日何個終わった",
        "今日何件終わった",
        "今日何個完了した",
        "今日何件完了した",
        "今日の予定の進捗",
        "今日の予定どれくらい終わった",
    )):
        return {
            "kind": "reminder_completion_summary",
            "target": "local",
            "query": "today",
            "confidence": 1.0,
        }

    if text and any(p in compact for p in (
        "今月何個終わった",
        "今月何件終わった",
        "今月何個完了した",
        "今月何件完了した",
        "今月の予定の進捗",
    )):
        return {
            "kind": "reminder_completion_summary",
            "target": "local",
            "query": "month",
            "confidence": 1.0,
        }

    if text and any(p in compact for p in (
        "今週何個終わった",
        "今週何件終わった",
        "今週何個完了した",
        "今週何件完了した",
        "今週の予定の進捗",
    )):
        return {
            "kind": "reminder_completion_summary",
            "target": "local",
            "query": "week",
            "confidence": 1.0,
        }

    if text and any(p in compact for p in (
        "今月の場所別進捗",
        "今月の場所ごとの進捗",
        "今月場所別にどれくらい終わった",
        "今月場所ごとにどれくらい終わった",
    )):
        return {
            "kind": "reminder_location_progress",
            "target": "local",
            "query": "month",
            "confidence": 1.0,
        }

    if text and any(p in compact for p in (
        "今週の場所別進捗",
        "今週の場所ごとの進捗",
        "今週場所別にどれくらい終わった",
        "今週場所ごとにどれくらい終わった",
    )):
        return {
            "kind": "reminder_location_progress",
            "target": "local",
            "query": "week",
            "confidence": 1.0,
        }

    if text and any(p in compact for p in (
        "明日の場所別進捗",
        "明日の場所ごとの進捗",
        "明日場所別にどれくらい予定がある",
        "明日場所ごとにどれくらい予定がある",
    )):
        return {
            "kind": "reminder_location_progress",
            "target": "local",
            "query": "tomorrow",
            "confidence": 1.0,
        }

    if text and any(p in compact for p in (
        "今日の場所別進捗",
        "今日の場所ごとの進捗",
        "今日場所別にどれくらい終わった",
        "今日場所ごとにどれくらい終わった",
    )):
        return {
            "kind": "reminder_location_progress",
            "target": "local",
            "query": "today",
            "confidence": 1.0,
        }

    if text and any(p in compact for p in (
        "今月のカテゴリ別進捗",
        "今月のカテゴリごとの進捗",
        "今月カテゴリ別にどれくらい終わった",
        "今月カテゴリごとにどれくらい終わった",
    )):
        return {
            "kind": "reminder_category_progress",
            "target": "local",
            "query": "month",
            "confidence": 1.0,
        }

    if text and any(p in compact for p in (
        "今週のカテゴリ別進捗",
        "今週のカテゴリごとの進捗",
        "今週カテゴリ別にどれくらい終わった",
        "今週カテゴリごとにどれくらい終わった",
    )):
        return {
            "kind": "reminder_category_progress",
            "target": "local",
            "query": "week",
            "confidence": 1.0,
        }

    if text and any(p in compact for p in (
        "明日のカテゴリ別進捗",
        "明日のカテゴリごとの進捗",
        "明日カテゴリ別にどれくらい予定がある",
        "明日カテゴリごとにどれくらい予定がある",
    )):
        return {
            "kind": "reminder_category_progress",
            "target": "local",
            "query": "tomorrow",
            "confidence": 1.0,
        }

    if text and any(p in compact for p in (
        "今日のカテゴリ別進捗",
        "今日のカテゴリごとの進捗",
        "今日カテゴリ別にどれくらい終わった",
        "今日カテゴリごとにどれくらい終わった",
    )):
        return {
            "kind": "reminder_category_progress",
            "target": "local",
            "query": "today",
            "confidence": 1.0,
        }

    if text and any(p in compact for p in (
        "今月のカテゴリ別件数",
        "今月のカテゴリ別予定数",
        "今月のカテゴリ内訳",
    )):
        return {"kind":"reminder_category_summary","target":"local","query":"month","confidence":1.0}

    if text and any(p in compact for p in (
        "今週のカテゴリ別件数",
        "今週のカテゴリ別予定数",
        "今週のカテゴリ内訳",
    )):
        return {"kind":"reminder_category_summary","target":"local","query":"week","confidence":1.0}

    if text and any(p in compact for p in (
        "今月の場所別件数",
        "今月の場所別予定数",
        "今月の場所内訳",
    )):
        return {"kind":"reminder_location_summary","target":"local","query":"month","confidence":1.0}

    if text and any(p in compact for p in (
        "今週の場所別件数",
        "今週の場所別予定数",
        "今週の場所内訳",
    )):
        return {"kind":"reminder_location_summary","target":"local","query":"week","confidence":1.0}

    if text and any(p in compact for p in (
        "明日のカテゴリ別件数",
        "明日のカテゴリ別予定数",
        "明日のカテゴリ内訳",
        "明日の予定カテゴリ内訳",
    )):
        return {
            "kind": "reminder_category_summary",
            "target": "local",
            "query": "tomorrow",
            "confidence": 1.0,
        }

    if text and any(p in compact for p in (
        "今日のカテゴリ別件数",
        "今日のカテゴリ別予定数",
        "今日のカテゴリ内訳",
        "今日の予定カテゴリ内訳",
    )):
        return {
            "kind": "reminder_category_summary",
            "target": "local",
            "query": "today",
            "confidence": 1.0,
        }

    if text:
        category_list_match = re.fullmatch(
            r"(?P<category>.+?)カテゴリ(?:の)?"
            r"(?:予定|リマインダー|リマインド)"
            r"(?:を)?(?:教えて|見せて|一覧|確認して|確認してください)?[?？]?",
            str(text).strip(),
        )
        if category_list_match:
            category = category_list_match.group("category").strip()
            if category and len(category) <= 32:
                return {
                    "kind": "reminder_category_list",
                    "target": "local",
                    "query": category,
                    "confidence": 1.0,
                }

    if text and any(p in compact for p in (
        "場所未設定の予定",
        "場所が未設定の予定",
        "場所のない予定",
        "場所がない予定",
        "場所未設定のリマインダー",
    )):
        return {
            "kind": "reminder_missing_location",
            "target": "local",
            "query": None,
            "confidence": 1.0,
        }

    if text and any(p in compact for p in (
        "明日の場所別件数",
        "明日の場所別予定数",
        "明日の場所内訳",
        "明日の予定場所内訳",
    )):
        return {
            "kind": "reminder_location_summary",
            "target": "local",
            "query": "tomorrow",
            "confidence": 1.0,
        }

    if text and any(p in compact for p in (
        "今日の場所別件数",
        "今日の場所別予定数",
        "今日の場所内訳",
        "今日の予定場所内訳",
    )):
        return {
            "kind": "reminder_location_summary",
            "target": "local",
            "query": "today",
            "confidence": 1.0,
        }

    if text:
        location_list_patterns = (
            r"場所(?:が|は)(?P<location>.+?)の"
            r"(?:予定|リマインダー|リマインド)"
            r"(?:を)?(?:教えて|見せて|一覧|確認して|確認してください)?[?？]?",
            r"(?P<location>.+?)での"
            r"(?:予定|リマインダー|リマインド)"
            r"(?:を)?(?:教えて|見せて|一覧|確認して|確認してください)?[?？]?",
            r"(?P<location>.+?)にある"
            r"(?:予定|リマインダー|リマインド)"
            r"(?:を)?(?:教えて|見せて|一覧|確認して|確認してください)?[?？]?",
        )
        for pattern in location_list_patterns:
            location_list_match = re.fullmatch(pattern, str(text).strip())
            if not location_list_match:
                continue
            location = location_list_match.group("location").strip()
            if location and len(location) <= 100:
                return {
                    "kind": "reminder_location_list",
                    "target": "local",
                    "query": location,
                    "confidence": 1.0,
                }

    if text and any(p in compact for p in (
        "最近削除した予定",
        "削除した予定を教えて",
        "削除した予定一覧",
        "ゴミ箱の予定",
        "ゴミ箱の予定を教えて",
    )):
        return {
            "kind": "reminder_deleted_list",
            "target": "local",
            "query": None,
            "confidence": 1.0,
        }

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
            parse_reminder_category_command,
            parse_reminder_duration_command,
            parse_reminder_importance_command,
            parse_reminder_location_command,
            parse_reminder_move_free_command,
            parse_reminder_note_command,
            parse_reminder_pause_command,
            parse_reminder_pre_notify_clear_command,
            parse_reminder_pre_notify_set_command,
            parse_reminder_rename_command,
            parse_reminder_repeat_change_command,
            parse_reminder_repeat_clear_command,
            parse_reminder_restore_completed_command,
            parse_reminder_restore_deleted_command,
            parse_reminder_resume_command,
            parse_reminder_reschedule_command,
            parse_reminder_snooze_command,
        )

        restore_deleted = parse_reminder_restore_deleted_command(text)
        if restore_deleted is not None:
            return {
                "kind": "reminder_restore_deleted",
                "target": "local",
                "query": restore_deleted,
                "confidence": 1.0,
            }

        restore_completed = parse_reminder_restore_completed_command(text)
        if restore_completed is not None:
            return {
                "kind": "reminder_restore_completed",
                "target": "local",
                "query": restore_completed,
                "confidence": 1.0,
            }

        note_command = parse_reminder_note_command(text)
        if note_command is not None:
            return {
                "kind": "reminder_note",
                "target": "local",
                "query": note_command,
                "confidence": 1.0,
            }

        location_command = parse_reminder_location_command(text)
        if location_command is not None:
            return {
                "kind": "reminder_location",
                "target": "local",
                "query": location_command,
                "confidence": 1.0,
            }

        category_change = parse_reminder_category_command(text)
        if category_change is not None:
            return {
                "kind": "reminder_category",
                "target": "local",
                "query": category_change,
                "confidence": 1.0,
            }

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
