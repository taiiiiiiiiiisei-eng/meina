"""めいなの自然な日本語リマインダー・予定命令を安全に解析する。"""
from __future__ import annotations

import re
from datetime import datetime, timedelta


_RELATIVE = re.compile(r"(?:あと\s*)?(?P<num>\d+)\s*(?P<unit>秒|分|時間|時|日)\s*(?:後|で)")
_CLOCK = re.compile(r"(?:(?P<ampm>午前|午後)\s*)?(?P<hour>\d{1,2})\s*時(?:\s*(?P<minute>\d{1,2})\s*分?)?")
_DAY_WORDS = re.compile(r"(?P<day>今日|明日|明後日)")
_CALENDAR_DATE = re.compile(r"(?:(?P<year>\d{4})\s*年\s*)?(?P<month>\d{1,2})\s*月\s*(?P<day>\d{1,2})\s*日")
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

        due = _parse_due_at_text(match.group("when"), now)
        if due is None:
            return None
        return {
            "target": target,
            "due_at": due.isoformat(timespec="seconds"),
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
    """予定名変更命令から現在名と新しい名前を安全に取り出す。"""
    del now  # 日時変更パーサーと同じ呼び出し形を保つ。
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
        new_name = match.group("new_name").strip("をのは")
        return {"target": target, "new_name": new_name}

    # 名前か新名称のどちらかがない場合も、実行側で安全に聞き返せる形にする。
    missing_target = re.fullmatch(
        rf"^{_ACTION_NOUN}(?:を|は)?(?P<new_name>.+?)に{_RENAME_FINISH}$",
        compact,
    )
    if missing_target:
        return {
            "target": "",
            "new_name": missing_target.group("new_name").strip("をのは"),
        }

    missing_name = re.fullmatch(
        rf"^(?P<target>.+?)(?:の)?{_ACTION_NOUN}(?:を|は)?{_RENAME_FINISH}$",
        compact,
    )
    if missing_name:
        return {
            "target": missing_name.group("target").strip("をのは"),
            "new_name": "",
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

    explicit_date = _CALENDAR_DATE.search(raw)
    day_match = _DAY_WORDS.search(raw)

    if explicit_date:
        due = _make_explicit_date(current, explicit_date, hour, minute)
        if due is None:
            return None
        spans = [explicit_date.span(), clock.span()]
    else:
        day_name = day_match.group("day") if day_match else "今日"
        day_offset = {"今日": 0, "明日": 1, "明後日": 2}[day_name]
        due = current.replace(hour=hour, minute=minute, second=0, microsecond=0)
        due += timedelta(days=day_offset)
        if day_offset == 0 and due <= current:
            due += timedelta(days=1)
        spans = [clock.span()]
        if day_match:
            spans.append(day_match.span())

    text_part = _extract_text(raw, spans)
    return _build_result(raw, text_part, due)


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


def _build_result(raw: str, text_part: str, due: datetime) -> dict | None:
    if text_part:
        return {"text": text_part, "due_at": due.isoformat(timespec="seconds")}
    fallback = _default_direct_notice_text(raw)
    if fallback:
        return {"text": fallback, "due_at": due.isoformat(timespec="seconds")}
    return None


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
    text = _COMMAND_WORDS.sub("", text)
    text = _TRAILING.sub("", text)

    # 時刻・日付部分を空白置換した後に、助詞除去より先に空白を整える。
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"^(?:に|へ|を|の|って)\s*", "", text)
    text = re.sub(r"(?:に|へ|を|の|って)\s*$", "", text)
    text = text.replace("予定", "")
    return text.strip(" 、。！？?")
