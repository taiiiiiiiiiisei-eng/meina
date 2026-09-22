"""めいなの自然な日本語リマインダー・予定命令を安全に解析する。"""
from __future__ import annotations

import calendar
import re
from datetime import datetime, timedelta


_RELATIVE = re.compile(r"(?:あと\s*)?(?P<num>\d+)\s*(?P<unit>秒|分|時間|時|日)\s*(?:後|で)")
_CLOCK = re.compile(r"(?:(?P<ampm>午前|午後)\s*)?(?P<hour>\d{1,2})\s*時(?:\s*(?P<minute>\d{1,2})\s*分?)?")
_DURATION_AFTER_CLOCK = re.compile(
    r"から\s*(?P<num>\d{1,4})\s*(?P<unit>分|時間)"
)
_DAY_WORDS = re.compile(r"(?P<day>今日|明日|明後日)")
_CALENDAR_DATE = re.compile(r"(?:(?P<year>\d{4})\s*年\s*)?(?P<month>\d{1,2})\s*月\s*(?P<day>\d{1,2})\s*日")
_REPEAT_DAILY = re.compile(r"毎日")
_REPEAT_WEEKDAYS = re.compile(r"(?:平日|毎平日)")
_REPEAT_WEEKLY = re.compile(
    r"毎週\s*(?P<weekday>月|火|水|木|金|土|日)(?:曜(?:日)?)?"
)
_REPEAT_MONTHLY = re.compile(r"毎月\s*(?P<day>\d{1,2})\s*日")
_WEEKDAY_INDEX = {"月": 0, "火": 1, "水": 2, "木": 3, "金": 4, "土": 5, "日": 6}
_COMMAND_WORDS = re.compile(
    r"(?:リマインド|リマインダー|予定|スケジュール|起こして|知らせて|思い出させて|教えて|追加|登録|設定)"
)
_TRAILING = re.compile(
    r"(?:を)?(?:追加|登録|設定|リマインド|リマインダー)?"
    r"(?:して|してね|してください|して下さい|お願い|お願いします)?$"
)


_ACTION_NOUN = r"(?:リマインダー|リマインド|予定|スケジュール)"
_DONE_ACTION = (
    r"(?:完了(?:して|してください|にして|にしてください)?|"
    r"済み(?:にして|にしてください)?|"
    r"終わった(?:ことにして|扱いにして)?|"
    r"終わり(?:にして|にしてください)?)"
)
_DELETE_ACTION = (
    r"(?:削除(?:して|してください)?|"
    r"消して|消してください|"
    r"取り消して|取り消してください|"
    r"キャンセルして|キャンセルしてください)"
)


def parse_reminder_action_target(text: str, action: str) -> str | None:
    """完了/削除命令から対象名を安全に取り出す。

    None はそのactionの命令ではないことを表す。
    空文字は命令だが対象名が指定されていないことを表す。
    """
    raw = str(text or "").strip()
    if not raw or raw.rstrip().endswith(("?", "？")):
        return None

    action_pattern = {
        "done": _DONE_ACTION,
        "delete": _DELETE_ACTION,
    }.get(str(action or "").lower())
    if action_pattern is None:
        return None

    compact = re.sub(r"[\s　、,。！!]+", "", raw)
    if not compact or not re.search(_ACTION_NOUN, compact):
        return None

    patterns = (
        # 「宿題のリマインダーを完了して」「宿題の予定を消して」
        rf"^(?P<target>.+?)(?:の)?{_ACTION_NOUN}(?:を|は)?{action_pattern}$",
        # 「リマインダーの宿題を完了して」「リマインダーから宿題を消して」
        rf"^{_ACTION_NOUN}(?:の|から)?(?P<target>.+?)(?:を|は)?{action_pattern}$",
        # 既存形式: 「リマインダーを完了して宿題」
        rf"^{_ACTION_NOUN}(?:を|は)?{action_pattern}(?P<target>.+)$",
    )
    for pattern in patterns:
        match = re.fullmatch(pattern, compact)
        if not match:
            continue
        target = match.group("target")
        target = re.sub(r"^(?:を|の|から|は|って)+", "", target)
        target = re.sub(r"(?:を|の|は|って)+$", "", target)
        return target.strip()

    # 命令自体は明確だが名前がない場合は、実行側に追加指定を求めさせる。
    if re.fullmatch(rf"^{_ACTION_NOUN}(?:を|は)?{action_pattern}$", compact):
        return ""

    return None


def parse_reminder_action_request(
    text: str,
    action: str,
    now: datetime | None = None,
) -> dict | None:
    """完了/削除命令を対象名と任意の日時絞り込みへ変換する。"""
    target = parse_reminder_action_target(text, action)
    raw = str(text or "").strip()
    if not raw or raw.rstrip().endswith(("?", "？")):
        return None

    action_pattern = {
        "done": _DONE_ACTION,
        "delete": _DELETE_ACTION,
    }.get(str(action or "").lower())
    if action_pattern is None:
        return None

    compact = re.sub(r"[\s　、,。！!]+", "", raw)

    # 「18時の宿題を完了して」「明日の宿題を削除して」のように
    # 予定という語を省略した形は、日時指定がある場合だけ安全に受け付ける。
    if target is None:
        has_due_hint = bool(
            _DAY_WORDS.search(compact)
            or _CALENDAR_DATE.search(compact)
            or _CLOCK.search(compact)
        )
        if not has_due_hint:
            return None
        match = re.fullmatch(
            rf"(?P<target>.+?)(?:を|は)?{action_pattern}",
            compact,
        )
        if not match:
            return None
        target = match.group("target")

    current = now or datetime.now().astimezone()
    target_text = str(target or "")

    date_value = None
    calendar_match = _CALENDAR_DATE.search(target_text)
    day_match = _DAY_WORDS.search(target_text)
    if calendar_match:
        year_text = calendar_match.group("year")
        year = int(year_text) if year_text else current.year
        month = int(calendar_match.group("month"))
        day = int(calendar_match.group("day"))
        try:
            date_value = current.replace(
                year=year,
                month=month,
                day=day,
            ).date().isoformat()
        except ValueError:
            return None
    elif day_match:
        day_offset = {"今日": 0, "明日": 1, "明後日": 2}[day_match.group("day")]
        date_value = (current + timedelta(days=day_offset)).date().isoformat()

    hour = None
    minute = None
    clock_match = _CLOCK.search(target_text)
    if clock_match:
        parsed_clock = _parse_clock(clock_match)
        if parsed_clock is None:
            return None
        hour, minute = parsed_clock

    clean_target = _CALENDAR_DATE.sub("", target_text)
    clean_target = _DAY_WORDS.sub("", clean_target)
    clean_target = _CLOCK.sub("", clean_target)
    clean_target = re.sub(r"^(?:の|を|は|から|って)+", "", clean_target)
    clean_target = re.sub(r"(?:の|を|は|って)+$", "", clean_target)
    clean_target = clean_target.strip(" 、。！？?")

    return {
        "target": clean_target,
        "date": date_value,
        "hour": hour,
        "minute": minute,
    }


def parse_reminder_selector_text(
    text: str,
    now: datetime | None = None,
) -> dict:
    """予定名に含まれる任意の日付・時刻指定を分離する。"""
    current = now or datetime.now().astimezone()
    target_text = str(text or "").strip()

    date_value = None
    calendar_match = _CALENDAR_DATE.search(target_text)
    day_match = _DAY_WORDS.search(target_text)
    if calendar_match:
        year_text = calendar_match.group("year")
        year = int(year_text) if year_text else current.year
        month = int(calendar_match.group("month"))
        day = int(calendar_match.group("day"))
        try:
            date_value = current.replace(
                year=year,
                month=month,
                day=day,
            ).date().isoformat()
        except ValueError:
            return {
                "target": "",
                "date": None,
                "hour": None,
                "minute": None,
                "valid": False,
            }
    elif day_match:
        day_offset = {"今日": 0, "明日": 1, "明後日": 2}[day_match.group("day")]
        date_value = (current + timedelta(days=day_offset)).date().isoformat()

    hour = None
    minute = None
    clock_match = _CLOCK.search(target_text)
    if clock_match:
        parsed_clock = _parse_clock(clock_match)
        if parsed_clock is None:
            return {
                "target": "",
                "date": date_value,
                "hour": None,
                "minute": None,
                "valid": False,
            }
        hour, minute = parsed_clock

    clean_target = _CALENDAR_DATE.sub("", target_text)
    clean_target = _DAY_WORDS.sub("", clean_target)
    clean_target = _CLOCK.sub("", clean_target)
    clean_target = re.sub(r"^(?:の|を|は|から|って)+", "", clean_target)
    clean_target = re.sub(r"(?:の|を|は|って)+$", "", clean_target)
    clean_target = clean_target.strip(" 、。！？?")

    return {
        "target": clean_target,
        "date": date_value,
        "hour": hour,
        "minute": minute,
        "valid": True,
    }




_REPEAT_CHANGE_ACTION = (
    r"(?:変更(?:して|してください)?|"
    r"変えて|変えてください|"
    r"にして|にしてください)"
)


def _parse_repeat_spec_text(text: str) -> dict | None:
    """繰り返し表現を内部ルールへ変換する。"""
    raw = str(text or "").strip()

    if _REPEAT_DAILY.fullmatch(raw):
        return {
            "repeat_rule": "daily",
            "repeat_day": None,
            "repeat_weekday": None,
        }

    if _REPEAT_WEEKDAYS.fullmatch(raw):
        return {
            "repeat_rule": "weekdays",
            "repeat_day": None,
            "repeat_weekday": None,
        }

    weekly = _REPEAT_WEEKLY.fullmatch(raw)
    if weekly:
        return {
            "repeat_rule": "weekly",
            "repeat_day": None,
            "repeat_weekday": _WEEKDAY_INDEX[weekly.group("weekday")],
        }

    monthly = _REPEAT_MONTHLY.fullmatch(raw)
    if monthly:
        day = int(monthly.group("day"))
        if not 1 <= day <= 31:
            return None
        return {
            "repeat_rule": "monthly",
            "repeat_day": day,
            "repeat_weekday": None,
        }

    return None


def parse_reminder_repeat_change_command(
    text: str,
    now: datetime | None = None,
) -> dict | None:
    """「薬の繰り返しを平日に変更して」の対象と新ルールを解析する。"""
    raw = str(text or "").strip()
    if not raw or raw.rstrip().endswith(("?", "？")):
        return None

    compact = re.sub(r"[\s　、,。！!]+", "", raw)
    repeat_spec = (
        r"(?:毎日|平日|毎平日|"
        r"毎週(?:月|火|水|木|金|土|日)(?:曜(?:日)?)?|"
        r"毎月\d{1,2}日)"
    )

    patterns = (
        rf"^(?P<target>.+?)(?:の)?{_ACTION_NOUN}?(?:の)?"
        rf"(?:繰り返し|定期設定)(?:を|は)?"
        rf"(?P<spec>{repeat_spec})(?:に)?{_REPEAT_CHANGE_ACTION}$",
        rf"^(?P<target>.+?)(?:を|は)?"
        rf"(?P<spec>{repeat_spec})(?:の)?(?:繰り返し|定期設定)"
        rf"(?:に)?{_REPEAT_CHANGE_ACTION}$",
    )

    for pattern in patterns:
        match = re.fullmatch(pattern, compact)
        if not match:
            continue

        selector = parse_reminder_selector_text(match.group("target"), now)
        if not selector.get("valid", False):
            return None

        repeat = _parse_repeat_spec_text(match.group("spec"))
        if repeat is None:
            return None

        return {
            "target": selector["target"],
            "date": selector["date"],
            "hour": selector["hour"],
            "minute": selector["minute"],
            **repeat,
        }

    return None




_PRE_NOTIFY_CLEAR_ACTION = (
    r"(?:解除(?:して|してください)?|"
    r"なし(?:にして|にしてください)?|"
    r"オフ(?:にして|にしてください)?|"
    r"停止(?:して|してください)?)"
)


def parse_reminder_pre_notify_set_command(
    text: str,
    now: datetime | None = None,
) -> dict | None:
    """予定ごとの「10分前通知」設定命令を解析する。"""
    raw = str(text or "").strip()
    if not raw or raw.rstrip().endswith(("?", "？")):
        return None

    compact = re.sub(r"[\s　、,。！!]+", "", raw)
    patterns = (
        (
            rf"^(?P<target>.+?)(?:の)?(?:{_ACTION_NOUN}(?:の)?)?"
            rf"(?:事前通知|事前のお知らせ|前通知)(?:を|は)?"
            rf"(?P<minutes>\d{{1,4}})分前(?:に)?"
            rf"(?:設定して|設定してください|して|してください)$"
        ),
        (
            rf"^(?P<target>.+?)(?:の)?(?:{_ACTION_NOUN})?(?:を|は)?"
            rf"(?P<minutes>\d{{1,4}})分前(?:にも|に)?"
            rf"(?:通知して|通知してください|知らせて|知らせてください)$"
        ),
    )

    for pattern in patterns:
        match = re.fullmatch(pattern, compact)
        if not match:
            continue

        minutes = int(match.group("minutes"))
        if not 1 <= minutes <= 1440:
            return None

        selector = parse_reminder_selector_text(match.group("target"), now)
        if not selector.get("valid", False):
            return None

        return {
            "target": selector["target"],
            "date": selector["date"],
            "hour": selector["hour"],
            "minute": selector["minute"],
            "notify_before_minutes": minutes,
        }
    return None


def parse_reminder_pre_notify_clear_command(
    text: str,
    now: datetime | None = None,
) -> dict | None:
    """予定ごとの事前通知解除命令を解析する。"""
    raw = str(text or "").strip()
    if not raw or raw.rstrip().endswith(("?", "？")):
        return None

    compact = re.sub(r"[\s　、,。！!]+", "", raw)
    patterns = (
        (
            rf"^(?P<target>.+?)(?:の)?(?:{_ACTION_NOUN}(?:の)?)?"
            rf"(?:事前通知|事前のお知らせ|前通知)(?:を|は)?"
            rf"{_PRE_NOTIFY_CLEAR_ACTION}$"
        ),
    )

    for pattern in patterns:
        match = re.fullmatch(pattern, compact)
        if not match:
            continue
        selector = parse_reminder_selector_text(match.group("target"), now)
        if not selector.get("valid", False):
            return None
        return {
            "target": selector["target"],
            "date": selector["date"],
            "hour": selector["hour"],
            "minute": selector["minute"],
        }
    return None


_PAUSE_ACTION = r"(?:一時停止(?:して|してください)?|保留(?:して|してください)?)"
_RESUME_ACTION = r"(?:再開(?:して|してください)?|再開して|戻して|戻してください)"


def _parse_reminder_pause_resume_command(
    text: str,
    action_pattern: str,
    now: datetime | None = None,
) -> dict | None:
    raw = str(text or "").strip()
    if not raw or raw.rstrip().endswith(("?", "？")):
        return None

    compact = re.sub(r"[\s　、,。！!]+", "", raw)
    patterns = (
        rf"^(?P<target>.+?)(?:の)?{_ACTION_NOUN}(?:を|は)?{action_pattern}$",
        rf"^(?P<target>.+?)(?:の)?(?:繰り返し|定期設定)(?:を|は)?{action_pattern}$",
    )
    for pattern in patterns:
        match = re.fullmatch(pattern, compact)
        if not match:
            continue
        selector = parse_reminder_selector_text(match.group("target"), now)
        if not selector.get("valid", False):
            return None
        return {
            "target": selector["target"],
            "date": selector["date"],
            "hour": selector["hour"],
            "minute": selector["minute"],
        }
    return None


def parse_reminder_pause_command(
    text: str,
    now: datetime | None = None,
) -> dict | None:
    """予定通知の一時停止命令を解析する。"""
    return _parse_reminder_pause_resume_command(text, _PAUSE_ACTION, now)


def parse_reminder_resume_command(
    text: str,
    now: datetime | None = None,
) -> dict | None:
    """一時停止した予定通知の再開命令を解析する。"""
    return _parse_reminder_pause_resume_command(text, _RESUME_ACTION, now)


_REPEAT_CLEAR_ACTION = (
    r"(?:停止(?:して|してください)?|"
    r"止めて|止めてください|"
    r"解除(?:して|してください)?|"
    r"やめて|やめてください|"
    r"終了(?:して|してください)?)"
)


def parse_reminder_repeat_clear_command(
    text: str,
    now: datetime | None = None,
) -> dict | None:
    """「薬の繰り返しを停止して」の対象名と任意の日時指定を取り出す。"""
    raw = str(text or "").strip()
    if not raw or raw.rstrip().endswith(("?", "？")):
        return None

    compact = re.sub(r"[\s　、,。！!]+", "", raw)
    patterns = (
        rf"^(?P<target>.+?)(?:の)?{_ACTION_NOUN}?(?:の)?"
        rf"(?:繰り返し|定期設定)(?:を|は)?{_REPEAT_CLEAR_ACTION}$",
        rf"^(?P<target>.+?)(?:の)?(?:繰り返し|定期設定)"
        rf"(?:を|は)?{_REPEAT_CLEAR_ACTION}$",
    )
    for pattern in patterns:
        match = re.fullmatch(pattern, compact)
        if not match:
            continue
        selector = parse_reminder_selector_text(match.group("target"), now)
        if not selector.get("valid", False):
            return None
        return {
            "target": selector["target"],
            "date": selector["date"],
            "hour": selector["hour"],
            "minute": selector["minute"],
        }
    return None




_IMPORTANT_SET_ACTION = (
    r"(?:重要(?:にして|にしてください|設定して|設定してください)|"
    r"大事(?:にして|にしてください|設定して|設定してください)|"
    r"優先(?:にして|にしてください|設定して|設定してください))"
)
_IMPORTANT_CLEAR_ACTION = (
    r"(?:解除(?:して|してください)?|"
    r"外して|外してください|"
    r"取り消して|取り消してください)"
)


def parse_reminder_importance_command(
    text: str,
    now: datetime | None = None,
) -> dict | None:
    """予定の重要フラグ変更命令を解析する。"""
    raw = str(text or "").strip()
    if not raw or raw.rstrip().endswith(("?", "？")):
        return None

    compact = re.sub(r"[\s　、,。！!]+", "", raw)
    set_patterns = (
        rf"^(?P<target>.+?)(?:の)?{_ACTION_NOUN}(?:を|は)?{_IMPORTANT_SET_ACTION}$",
        rf"^(?P<target>.+?)(?:を|は)?(?:重要な予定|大事な予定)(?:にして|にしてください)$",
    )
    clear_patterns = (
        rf"^(?P<target>.+?)(?:の)?{_ACTION_NOUN}(?:の)?"
        rf"(?:重要設定|重要|優先設定)(?:を|は)?{_IMPORTANT_CLEAR_ACTION}$",
    )

    for important, patterns in ((True, set_patterns), (False, clear_patterns)):
        for pattern in patterns:
            match = re.fullmatch(pattern, compact)
            if not match:
                continue
            selector = parse_reminder_selector_text(match.group("target"), now)
            if not selector.get("valid", False):
                return None
            return {
                "target": selector["target"],
                "date": selector["date"],
                "hour": selector["hour"],
                "minute": selector["minute"],
                "important": important,
            }
    return None


_SNOOZE_ACTION = (
    r"(?:回して|回してください|"
    r"延長して|延長してください|"
    r"延期して|延期してください|"
    r"スヌーズして|スヌーズしてください)"
)


def parse_reminder_snooze_command(
    text: str,
    now: datetime | None = None,
) -> dict | None:
    """「宿題を10分後に回して」の対象名・任意の日時指定・遅延分を解析する。"""
    raw = str(text or "").strip()
    if not raw or raw.rstrip().endswith(("?", "？")):
        return None

    compact = re.sub(r"[\s　、,。！!]+", "", raw)
    patterns = (
        rf"^(?P<target>.+?)(?:の)?{_ACTION_NOUN}?(?:を|は)?"
        rf"(?P<minutes>\d{{1,4}})分(?:後)?(?:に)?{_SNOOZE_ACTION}$",
    )

    for pattern in patterns:
        match = re.fullmatch(pattern, compact)
        if not match:
            continue

        minutes = int(match.group("minutes"))
        if not 1 <= minutes <= 1440:
            return None

        selector = parse_reminder_selector_text(match.group("target"), now)
        if not selector.get("valid", False):
            return None

        return {
            "target": selector["target"],
            "date": selector["date"],
            "hour": selector["hour"],
            "minute": selector["minute"],
            "delay_minutes": minutes,
        }

    return None


_RESCHEDULE_ACTION = (
    r"(?:変更(?:して|してください)?|"
    r"変えて|変えてください|"
    r"ずらして|ずらしてください|"
    r"移動して|移動してください)"
)


def _parse_due_at_text(text: str, now: datetime | None = None) -> datetime | None:
    """日時だけを安全に解析する。予定追加と日時変更で同じ規則を使う。"""
    raw = str(text or "").strip()
    if not raw:
        return None

    current = now or datetime.now().astimezone()

    relative = _RELATIVE.search(raw)
    if relative:
        amount = int(relative.group("num"))
        unit = relative.group("unit")
        delta = {
            "秒": timedelta(seconds=amount),
            "分": timedelta(minutes=amount),
            "時間": timedelta(hours=amount),
            "時": timedelta(hours=amount),
            "日": timedelta(days=amount),
        }[unit]
        return current + delta

    clock = _CLOCK.search(raw)
    if not clock:
        return None

    parsed_clock = _parse_clock(clock)
    if parsed_clock is None:
        return None
    hour, minute = parsed_clock

    duration_match = _DURATION_AFTER_CLOCK.search(raw, clock.end())
    duration_minutes = None
    if duration_match:
        amount = int(duration_match.group("num"))
        unit = duration_match.group("unit")
        duration_minutes = amount * 60 if unit == "時間" else amount
        if not 1 <= duration_minutes <= 1440:
            return None

    explicit_date = _CALENDAR_DATE.search(raw)
    if explicit_date:
        return _make_explicit_date(current, explicit_date, hour, minute)

    day_match = _DAY_WORDS.search(raw)
    day_name = day_match.group("day") if day_match else "今日"
    day_offset = {"今日": 0, "明日": 1, "明後日": 2}[day_name]
    due = current.replace(hour=hour, minute=minute, second=0, microsecond=0)
    due += timedelta(days=day_offset)
    if day_offset == 0 and due <= current:
        due += timedelta(days=1)
    return due


def parse_reminder_reschedule_command(
    text: str,
    now: datetime | None = None,
) -> dict | None:
    """「宿題の予定を明日20時に変更して」の対象名と新日時を解析する。"""
    raw = str(text or "").strip()
    if not raw or raw.rstrip().endswith(("?", "？")):
        return None

    compact = re.sub(r"[\s　、,。！!]+", "", raw)
    if not re.search(_ACTION_NOUN, compact):
        return None

    patterns = (
        (
            # 「宿題の予定を明日20時に変更して」
            rf"^(?P<target>.+?)(?:の)?{_ACTION_NOUN}(?:を|は)?"
            rf"(?P<when>.+?)(?:に)?{_RESCHEDULE_ACTION}$",
            True,
        ),
        (
            # 「予定の宿題を明日20時に変更して」
            rf"^{_ACTION_NOUN}(?:の|から)(?P<target>.+?)(?:を|は)"
            rf"(?P<when>.+?)(?:に)?{_RESCHEDULE_ACTION}$",
            True,
        ),
        (
            # 「予定を明日20時に変更して」: 対象名が未指定
            rf"^{_ACTION_NOUN}(?:を|は)?(?P<when>.+?)(?:に)?{_RESCHEDULE_ACTION}$",
            False,
        ),
    )

    for pattern, has_target in patterns:
        match = re.fullmatch(pattern, compact)
        if not match:
            continue

        target = match.groupdict().get("target", "") if has_target else ""
        target = re.sub(r"^(?:を|の|から|は|って)+", "", target)
        target = re.sub(r"(?:を|の|は|って)+$", "", target).strip()

        selector = parse_reminder_selector_text(target, now)
        if not selector.get("valid", False):
            return None

        due = _parse_due_at_text(match.group("when"), now)
        if due is None:
            return None
        return {
            "target": selector["target"],
            "due_at": due.isoformat(timespec="seconds"),
            "date": selector["date"],
            "hour": selector["hour"],
            "minute": selector["minute"],
        }

    return None


_RENAME_FINISH = (
    r"(?:名前変更(?:して|してください)?|"
    r"改名(?:して|してください)?|"
    r"名前(?:を)?(?:変更(?:して|してください)?|変えて|変えてください))"
)
_PLAIN_RENAME_FINISH = (
    r"(?:変更(?:して|してください)?|変えて|変えてください)"
)


def parse_reminder_rename_command(
    text: str,
    now: datetime | None = None,
) -> dict | None:
    """予定名変更命令から現在名・任意の日時指定・新しい名前を取り出す。"""
    raw = str(text or "").strip()
    if not raw or raw.rstrip().endswith(("?", "？")):
        return None

    compact = re.sub(r"[\s　、,。！!]+", "", raw)
    if not re.search(_ACTION_NOUN, compact):
        return None
    if not re.search(r"(?:名前変更|改名|名前(?:を)?(?:変更|変えて)|(?:予定|リマインダー|リマインド|スケジュール)名)", compact):
        return None

    patterns = (
        # 「宿題の予定を数学の宿題に名前変更して」
        rf"^(?P<target>.+?)(?:の)?{_ACTION_NOUN}(?:を|は)?"
        rf"(?P<new_name>.+?)に{_RENAME_FINISH}$",
        # 「リマインダーの配信を夜配信に改名して」
        rf"^{_ACTION_NOUN}(?:の|から)(?P<target>.+?)(?:を|は)"
        rf"(?P<new_name>.+?)に{_RENAME_FINISH}$",
        # 「宿題の予定名を数学の宿題に変更して」
        rf"^(?P<target>.+?)(?:の)?"
        rf"(?:予定名|リマインダー名|リマインド名|スケジュール名|{_ACTION_NOUN}の名前)"
        rf"(?:を|は)(?P<new_name>.+?)に{_PLAIN_RENAME_FINISH}$",
    )
    for pattern in patterns:
        match = re.fullmatch(pattern, compact)
        if not match:
            continue
        target = re.sub(
            r"^(?:を|の|から|は|って)+|(?:を|の|は|って)+$",
            "",
            match.group("target"),
        ).strip()
        selector = parse_reminder_selector_text(target, now)
        if not selector.get("valid", False):
            return None
        new_name = match.group("new_name").strip("をのは")
        return {
            "target": selector["target"],
            "new_name": new_name,
            "date": selector["date"],
            "hour": selector["hour"],
            "minute": selector["minute"],
        }

    # 名前か新名称のどちらかがない場合も、実行側で安全に聞き返せる形にする。
    missing_target = re.fullmatch(
        rf"^{_ACTION_NOUN}(?:を|は)?(?P<new_name>.+?)に{_RENAME_FINISH}$",
        compact,
    )
    if missing_target:
        return {
            "target": "",
            "new_name": missing_target.group("new_name").strip("をのは"),
            "date": None,
            "hour": None,
            "minute": None,
        }

    missing_name = re.fullmatch(
        rf"^(?P<target>.+?)(?:の)?{_ACTION_NOUN}(?:を|は)?{_RENAME_FINISH}$",
        compact,
    )
    if missing_name:
        selector = parse_reminder_selector_text(
            missing_name.group("target").strip("をのは"),
            now,
        )
        if not selector.get("valid", False):
            return None
        return {
            "target": selector["target"],
            "new_name": "",
            "date": selector["date"],
            "hour": selector["hour"],
            "minute": selector["minute"],
        }

    return None


def parse_reminder_command(text: str, now: datetime | None = None) -> dict | None:
    """相対時間・曜日語・年月日指定から予定/リマインダーを解析する。"""
    raw = str(text or "").strip()
    if not raw:
        return None

    direct_notice = bool(re.search(r"(?:起こして|知らせて|思い出させて|教えて)", raw))
    has_schedule_intent = bool(
        re.search(r"(?:リマインド|リマインダー|予定|スケジュール|追加|登録|設定)", raw)
    )
    if not has_schedule_intent and not direct_notice:
        return None

    current = now or datetime.now().astimezone()

    daily_match = _REPEAT_DAILY.search(raw)
    weekdays_match = _REPEAT_WEEKDAYS.search(raw)
    weekly_match = _REPEAT_WEEKLY.search(raw)
    monthly_match = _REPEAT_MONTHLY.search(raw)
    if daily_match or weekdays_match or weekly_match or monthly_match:
        clock = _CLOCK.search(raw)
        if not clock:
            return None

        parsed_clock = _parse_clock(clock)
        if parsed_clock is None:
            return None
        hour, minute = parsed_clock

        duration_match = _DURATION_AFTER_CLOCK.search(raw, clock.end())
        duration_minutes = None
        if duration_match:
            amount = int(duration_match.group("num"))
            unit = duration_match.group("unit")
            duration_minutes = amount * 60 if unit == "時間" else amount
            if not 1 <= duration_minutes <= 1440:
                return None

        due = current.replace(hour=hour, minute=minute, second=0, microsecond=0)
        repeat_rule = "daily"
        repeat_day = None

        if monthly_match:
            repeat_rule = "monthly"
            repeat_span = monthly_match.span()
            repeat_day = int(monthly_match.group("day"))
            if not 1 <= repeat_day <= 31:
                return None

            last_day = calendar.monthrange(current.year, current.month)[1]
            due = current.replace(
                day=min(repeat_day, last_day),
                hour=hour,
                minute=minute,
                second=0,
                microsecond=0,
            )
            if due <= current:
                year = current.year + (1 if current.month == 12 else 0)
                month = 1 if current.month == 12 else current.month + 1
                last_day = calendar.monthrange(year, month)[1]
                due = due.replace(
                    year=year,
                    month=month,
                    day=min(repeat_day, last_day),
                )
        elif weekly_match:
            repeat_rule = "weekly"
            repeat_span = weekly_match.span()
            target_weekday = _WEEKDAY_INDEX[weekly_match.group("weekday")]
            days_ahead = (target_weekday - current.weekday()) % 7
            due += timedelta(days=days_ahead)
            if due <= current:
                due += timedelta(days=7)
        elif weekdays_match:
            repeat_rule = "weekdays"
            repeat_span = weekdays_match.span()
            if due <= current:
                due += timedelta(days=1)
            while due.weekday() >= 5:
                due += timedelta(days=1)
        else:
            repeat_span = daily_match.span()
            if due <= current:
                due += timedelta(days=1)

        spans = [clock.span(), repeat_span]
        if duration_match:
            spans.append(duration_match.span())
        text_part = _extract_text(raw, spans)
        result = _build_result(
            raw,
            text_part,
            due,
            repeat_rule=repeat_rule,
        )
        if result is not None and repeat_day is not None:
            result["repeat_day"] = repeat_day
        if result is not None and duration_minutes is not None:
            result["duration_minutes"] = duration_minutes
        return result

    relative = _RELATIVE.search(raw)
    if relative:
        amount = int(relative.group("num"))
        unit = relative.group("unit")
        delta = {
            "秒": timedelta(seconds=amount),
            "分": timedelta(minutes=amount),
            "時間": timedelta(hours=amount),
            "時": timedelta(hours=amount),
            "日": timedelta(days=amount),
        }[unit]
        due = current + delta
        text_part = _extract_text(raw, [relative.span()])
        return _build_result(raw, text_part, due)

    clock = _CLOCK.search(raw)
    if not clock:
        return None

    parsed_clock = _parse_clock(clock)
    if parsed_clock is None:
        return None
    hour, minute = parsed_clock

    duration_match = _DURATION_AFTER_CLOCK.search(raw, clock.end())
    duration_minutes = None
    if duration_match:
        amount = int(duration_match.group("num"))
        unit = duration_match.group("unit")
        duration_minutes = amount * 60 if unit == "時間" else amount
        if not 1 <= duration_minutes <= 1440:
            return None

    explicit_date = _CALENDAR_DATE.search(raw)
    day_match = _DAY_WORDS.search(raw)

    if explicit_date:
        due = _make_explicit_date(current, explicit_date, hour, minute)
        if due is None:
            return None
        spans = [explicit_date.span(), clock.span()]
        if duration_match:
            spans.append(duration_match.span())
    else:
        day_name = day_match.group("day") if day_match else "今日"
        day_offset = {"今日": 0, "明日": 1, "明後日": 2}[day_name]
        due = current.replace(hour=hour, minute=minute, second=0, microsecond=0)
        due += timedelta(days=day_offset)
        if day_offset == 0 and due <= current:
            due += timedelta(days=1)
        spans = [clock.span()]
        if duration_match:
            spans.append(duration_match.span())
        if day_match:
            spans.append(day_match.span())

    text_part = _extract_text(raw, spans)
    result = _build_result(raw, text_part, due)
    if result is not None and duration_minutes is not None:
        result["duration_minutes"] = duration_minutes
    return result


def _parse_clock(match: re.Match[str]) -> tuple[int, int] | None:
    hour = int(match.group("hour"))
    minute = int(match.group("minute") or 0)
    ampm = match.group("ampm")

    if ampm == "午前" and hour == 12:
        hour = 0
    elif ampm == "午後" and hour < 12:
        hour += 12

    if hour > 23 or minute > 59:
        return None
    return hour, minute


def _make_explicit_date(
    current: datetime,
    match: re.Match[str],
    hour: int,
    minute: int,
) -> datetime | None:
    year_text = match.group("year")
    month = int(match.group("month"))
    day = int(match.group("day"))

    year = int(year_text) if year_text else current.year
    try:
        due = current.replace(
            year=year,
            month=month,
            day=day,
            hour=hour,
            minute=minute,
            second=0,
            microsecond=0,
        )
    except ValueError:
        return None

    # 年省略時、今年の日付がすでに過ぎていたら翌年に回す。
    if not year_text and due <= current:
        try:
            due = due.replace(year=year + 1)
        except ValueError:
            return None
    return due


def _build_result(
    raw: str,
    text_part: str,
    due: datetime,
    repeat_rule: str | None = None,
) -> dict | None:
    if text_part:
        result = {"text": text_part, "due_at": due.isoformat(timespec="seconds")}
    else:
        fallback = _default_direct_notice_text(raw)
        if not fallback:
            return None
        result = {"text": fallback, "due_at": due.isoformat(timespec="seconds")}

    if repeat_rule:
        result["repeat_rule"] = repeat_rule
    return result


def _default_direct_notice_text(raw: str) -> str | None:
    compact = str(raw).replace(" ", "").replace("　", "")
    if "起こして" in compact:
        return "起床"
    if "知らせて" in compact:
        return "通知"
    if "思い出させて" in compact:
        return "リマインド"
    if "教えて" in compact:
        return "通知"
    return None


def _extract_text(raw: str, spans: list[tuple[int, int]]) -> str:
    chars = list(raw)
    for start, end in sorted(spans, reverse=True):
        chars[start:end] = [" "] * (end - start)
    text = "".join(chars)

    text = _DAY_WORDS.sub("", text)
    text = _CALENDAR_DATE.sub("", text)
    text = _REPEAT_DAILY.sub("", text)
    text = _REPEAT_WEEKDAYS.sub("", text)
    text = _REPEAT_WEEKLY.sub("", text)
    text = _REPEAT_MONTHLY.sub("", text)
    text = _COMMAND_WORDS.sub("", text)
    text = _TRAILING.sub("", text)

    # 時刻・日付部分を空白置換した後に、助詞除去より先に空白を整える。
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"^(?:に|へ|を|の|って)\s*", "", text)
    text = re.sub(r"(?:に|へ|を|の|って)\s*$", "", text)
    text = text.replace("予定", "")
    return text.strip(" 、。！？?")
