"""めいなのローカル・リマインダー管理。外部サービスを使わずJSONへ保存する。"""
from __future__ import annotations

import calendar
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

REMINDER_PATH = Path(__file__).with_name("meina_reminders.json")


def _load() -> list[dict[str, Any]]:
    if not REMINDER_PATH.exists():
        return []
    try:
        data = json.loads(REMINDER_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def _save(items: list[dict[str, Any]]) -> None:
    REMINDER_PATH.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def _trash_path() -> Path:
    """現在のリマインダー保存先に対応する削除履歴JSONを返す。"""
    return REMINDER_PATH.with_name(f"{REMINDER_PATH.stem}_trash.json")


def _load_trash() -> list[dict[str, Any]]:
    path = _trash_path()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def _save_trash(items: list[dict[str, Any]]) -> None:
    _trash_path().write_text(
        json.dumps(items, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def format_reminder_due(due_at: str, now: datetime | None = None) -> str:
    """予定日時を音声で読みやすい日本語へ整形する。"""
    raw = str(due_at or "").strip()
    try:
        due = datetime.fromisoformat(raw)
    except (TypeError, ValueError):
        return raw or "日時不明"

    current = now or datetime.now().astimezone()
    if due.tzinfo is None and current.tzinfo is not None:
        due = due.replace(tzinfo=current.tzinfo)
    elif due.tzinfo is not None and current.tzinfo is not None:
        due = due.astimezone(current.tzinfo)

    if due.date() == current.date():
        date_text = "今日"
    elif due.date() == (current + timedelta(days=1)).date():
        date_text = "明日"
    elif due.year == current.year:
        date_text = f"{due.month}月{due.day}日"
    else:
        date_text = f"{due.year}年{due.month}月{due.day}日"

    if due.minute:
        time_text = f"{due.hour}時{due.minute}分"
    else:
        time_text = f"{due.hour}時"
    return f"{date_text}{time_text}"


_WEEKDAYS_JA = ("月", "火", "水", "木", "金", "土", "日")
_VALID_REPEAT_RULES = {None, "daily", "weekdays", "weekly", "monthly"}


def format_reminder_duration(item: dict[str, Any]) -> str:
    """所要時間を読み上げやすい日本語へ整形する。"""
    try:
        minutes = int(item.get("duration_minutes") or 0)
    except (TypeError, ValueError):
        return ""
    if minutes <= 0:
        return ""
    hours, remain = divmod(minutes, 60)
    if hours and remain:
        return f"{hours}時間{remain}分"
    if hours:
        return f"{hours}時間"
    return f"{remain}分"


def format_reminder_importance(item: dict[str, Any]) -> str:
    """重要予定なら表示用ラベルを返す。"""
    return "重要" if item.get("important") else ""


def format_reminder_category(item: dict[str, Any]) -> str:
    """予定カテゴリの表示名を返す。"""
    return str(item.get("category") or "").strip()


def format_reminder_note(item: dict[str, Any]) -> str:
    """予定メモの表示文字列を返す。"""
    return str(item.get("note") or "").strip()


def format_reminder_location(item: dict[str, Any]) -> str:
    """予定場所の表示文字列を返す。"""
    return str(item.get("location") or "").strip()


def format_reminder_repeat(item: dict[str, Any]) -> str:
    """繰り返し設定を読み上げやすい日本語へ整形する。"""
    rule = item.get("repeat_rule")
    if rule == "daily":
        return "毎日"
    if rule == "weekdays":
        return "平日"
    if rule == "weekly":
        try:
            due = datetime.fromisoformat(str(item.get("due_at", "")))
            return f"毎週{_WEEKDAYS_JA[due.weekday()]}曜"
        except (TypeError, ValueError):
            return "毎週"
    if rule == "monthly":
        try:
            day = int(item.get("repeat_day") or 0)
        except (TypeError, ValueError):
            day = 0
        if not 1 <= day <= 31:
            try:
                day = datetime.fromisoformat(str(item.get("due_at", ""))).day
            except (TypeError, ValueError):
                return "毎月"
        return f"毎月{day}日"
    return ""


def _normalize_repeat_rule(value: Any) -> str | None:
    rule = str(value or "").strip().lower() or None
    if rule not in _VALID_REPEAT_RULES:
        raise ValueError(f"unsupported repeat_rule: {value}")
    return rule


def add_reminder(
    text: str,
    due_at: str,
    repeat_rule: str | None = None,
    repeat_day: int | None = None,
    duration_minutes: int | None = None,
) -> dict[str, Any]:
    due = datetime.fromisoformat(due_at)
    duration = None
    if duration_minutes is not None:
        duration = int(duration_minutes)
        if not 1 <= duration <= 1440:
            raise ValueError("duration_minutes must be between 1 and 1440")
    repeat = _normalize_repeat_rule(repeat_rule)
    monthly_day = None
    if repeat == "monthly":
        monthly_day = int(repeat_day or due.day)
        if not 1 <= monthly_day <= 31:
            raise ValueError("repeat_day must be between 1 and 31")
    item = {
        "id": f"r-{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
        "text": str(text).strip(),
        "due_at": due.isoformat(timespec="seconds"),
        "done": False,
    }
    if repeat:
        item["repeat_rule"] = repeat
    if monthly_day is not None:
        item["repeat_day"] = monthly_day
    if duration is not None:
        item["duration_minutes"] = duration
    items = _load()
    items.append(item)
    _save(items)
    return item


def list_reminders(include_done: bool = False) -> list[dict[str, Any]]:
    items = _load()
    if include_done:
        return items
    return [item for item in items if not item.get("done")]


def _normalize_reminder_text(value: Any) -> str:
    """音声認識で混ざりやすい空白を無視して比較用文字列へ正規化する。"""
    return re.sub(r"[\s　]+", "", str(value or "")).casefold()


def find_reminders(query: str) -> list[dict[str, Any]]:
    """完全一致を優先し、なければ部分一致する未完了リマインダーを返す。"""
    needle = _normalize_reminder_text(query)
    if not needle:
        return []

    items = list_reminders()
    exact = [
        item
        for item in items
        if _normalize_reminder_text(item.get("text", "")) == needle
    ]
    if exact:
        return exact

    return [
        item
        for item in items
        if needle in _normalize_reminder_text(item.get("text", ""))
    ]



def find_completed_reminders(query: str) -> list[dict[str, Any]]:
    """完了済みの単発予定を、完全一致優先で検索する。"""
    needle = _normalize_reminder_text(query)
    if not needle:
        return []

    items = [
        item
        for item in list_reminders(include_done=True)
        if item.get("done") and item.get("completed_at")
    ]
    exact = [
        item
        for item in items
        if _normalize_reminder_text(item.get("text", "")) == needle
    ]
    if exact:
        return exact
    return [
        item
        for item in items
        if needle in _normalize_reminder_text(item.get("text", ""))
    ]


def restore_completed_reminder(reminder_id: str) -> dict[str, Any] | None:
    """完了済みの単発予定だけを未完了へ戻す。定期予定の履歴は巻き戻さない。"""
    items = _load()
    for item in items:
        if item.get("id") != reminder_id:
            continue
        if not item.get("done") or not item.get("completed_at"):
            return None
        if item.get("repeat_rule") in ("daily", "weekdays", "weekly", "monthly"):
            return None

        item["done"] = False
        item.pop("completed_at", None)
        item.pop("pre_notified_due_at", None)
        _save(items)
        return item
    return None


def find_duplicate_reminder(
    text: str,
    due_at: str,
    *,
    repeat_rule: str | None = None,
    repeat_day: int | None = None,
    duration_minutes: int | None = None,
) -> dict[str, Any] | None:
    """同名・同日時・同じ繰り返し設定の未完了予定を探す。"""
    needle = _normalize_reminder_text(text)
    if not needle:
        return None

    try:
        requested_due = datetime.fromisoformat(str(due_at))
    except (TypeError, ValueError):
        return None

    try:
        requested_rule = _normalize_repeat_rule(repeat_rule)
    except ValueError:
        return None

    requested_day = None
    if requested_rule == "monthly":
        try:
            requested_day = int(repeat_day or requested_due.day)
        except (TypeError, ValueError):
            return None

    for item in list_reminders():
        if _normalize_reminder_text(item.get("text", "")) != needle:
            continue
        try:
            item_due = datetime.fromisoformat(str(item.get("due_at", "")))
        except (TypeError, ValueError):
            continue
        if item_due != requested_due:
            continue
        if (item.get("repeat_rule") or None) != requested_rule:
            continue
        if requested_rule == "monthly":
            try:
                item_day = int(item.get("repeat_day") or item_due.day)
            except (TypeError, ValueError):
                continue
            if item_day != requested_day:
                continue
        try:
            item_duration = int(item.get("duration_minutes") or 0)
            requested_duration = int(duration_minutes or 0)
        except (TypeError, ValueError):
            continue
        if item_duration != requested_duration:
            continue
        return item
    return None


def next_reminder(
    now: datetime | None = None,
    *,
    include_paused: bool = False,
) -> dict[str, Any] | None:
    """現在以降で最も近い未完了予定を返す。通常は一時停止中を除外する。"""
    current = now or datetime.now().astimezone()
    candidates: list[tuple[datetime, dict[str, Any]]] = []
    for item in list_reminders():
        if item.get("paused") and not include_paused:
            continue
        try:
            due = datetime.fromisoformat(str(item.get("due_at", "")))
            if due.tzinfo is None and current.tzinfo is not None:
                due = due.replace(tzinfo=current.tzinfo)
            elif due.tzinfo is not None and current.tzinfo is not None:
                due = due.astimezone(current.tzinfo)
        except (TypeError, ValueError):
            continue
        if due >= current:
            candidates.append((due, item))

    if not candidates:
        return None
    candidates.sort(key=lambda pair: pair[0])
    return candidates[0][1]


def prioritized_reminders(
    now: datetime | None = None,
    *,
    target_date=None,
) -> list[dict[str, Any]]:
    """未完了予定を期限切れ→重要→時刻順の固定ルールで並べる。"""
    current = now or datetime.now().astimezone()
    ranked: list[tuple[int, int, datetime, dict[str, Any]]] = []

    for item in list_reminders():
        if item.get("paused"):
            continue
        try:
            due = datetime.fromisoformat(str(item.get("due_at", "")))
            if due.tzinfo is None and current.tzinfo is not None:
                due = due.replace(tzinfo=current.tzinfo)
            elif due.tzinfo is not None and current.tzinfo is not None:
                due = due.astimezone(current.tzinfo)
        except (TypeError, ValueError):
            continue

        if target_date is not None and due.date() != target_date:
            continue

        overdue_rank = 0 if due < current else 1
        important_rank = 0 if item.get("important") else 1
        ranked.append((overdue_rank, important_rank, due, item))

    ranked.sort(key=lambda row: (row[0], row[1], row[2]))
    return [item for _, _, _, item in ranked]


def next_priority_reminder(
    now: datetime | None = None,
) -> dict[str, Any] | None:
    """固定優先ルールで最上位の未完了予定を1件返す。"""
    items = prioritized_reminders(now)
    return items[0] if items else None


def _reminder_interval(
    item: dict[str, Any],
    current: datetime,
) -> tuple[datetime, datetime] | None:
    """予定の開始・終了を返す。所要時間なしは1分の点予定として扱う。"""
    try:
        start = datetime.fromisoformat(str(item.get("due_at", "")))
        if start.tzinfo is None and current.tzinfo is not None:
            start = start.replace(tzinfo=current.tzinfo)
        elif start.tzinfo is not None and current.tzinfo is not None:
            start = start.astimezone(current.tzinfo)
        duration = int(item.get("duration_minutes") or 1)
    except (TypeError, ValueError):
        return None
    duration = max(1, min(duration, 1440))
    return start, start + timedelta(minutes=duration)


def find_schedule_conflicts(
    now: datetime | None = None,
    *,
    days: int = 7,
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """指定期間内で時間帯が重なる通知中の予定ペアを返す。"""
    current = now or datetime.now().astimezone()
    end = current + timedelta(days=max(1, min(int(days), 31)))
    candidates: list[tuple[datetime, datetime, dict[str, Any]]] = []

    for item in list_reminders():
        if item.get("paused"):
            continue
        interval = _reminder_interval(item, current)
        if interval is None:
            continue
        start, finish = interval
        if finish < current or start > end:
            continue
        candidates.append((start, finish, item))

    candidates.sort(key=lambda row: row[0])
    conflicts: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for index, (start, finish, item) in enumerate(candidates):
        for other_start, other_finish, other in candidates[index + 1:]:
            if other_start >= finish:
                break
            if start < other_finish and other_start < finish:
                conflicts.append((item, other))
    return conflicts


def find_free_time_slots(
    start_at: datetime,
    end_at: datetime,
    *,
    minimum_minutes: int = 15,
    exclude_reminder_id: str | None = None,
) -> list[tuple[datetime, datetime]]:
    """指定時間帯の空き枠を返す。一時停止中の予定は占有しない。"""
    if end_at <= start_at:
        return []

    minimum = max(1, min(int(minimum_minutes), 1440))
    busy: list[tuple[datetime, datetime]] = []
    current = start_at

    for item in list_reminders():
        if item.get("paused"):
            continue
        if exclude_reminder_id and item.get("id") == exclude_reminder_id:
            continue
        interval = _reminder_interval(item, start_at)
        if interval is None:
            continue
        busy_start, busy_end = interval
        if busy_end <= start_at or busy_start >= end_at:
            continue
        busy.append((max(busy_start, start_at), min(busy_end, end_at)))

    busy.sort(key=lambda row: row[0])
    merged: list[list[datetime]] = []
    for busy_start, busy_end in busy:
        if not merged or busy_start > merged[-1][1]:
            merged.append([busy_start, busy_end])
        elif busy_end > merged[-1][1]:
            merged[-1][1] = busy_end

    free: list[tuple[datetime, datetime]] = []
    for busy_start, busy_end in merged:
        if (busy_start - current).total_seconds() >= minimum * 60:
            free.append((current, busy_start))
        if busy_end > current:
            current = busy_end

    if (end_at - current).total_seconds() >= minimum * 60:
        free.append((current, end_at))
    return free


def schedule_window_stats(
    start_at: datetime,
    end_at: datetime,
) -> dict[str, int]:
    """指定時間帯の空き・占有時間を分単位で集計する。"""
    if end_at <= start_at:
        return {
            "window_minutes": 0,
            "free_minutes": 0,
            "busy_minutes": 0,
            "longest_free_minutes": 0,
        }

    window_minutes = int((end_at - start_at).total_seconds() // 60)
    slots = find_free_time_slots(
        start_at,
        end_at,
        minimum_minutes=1,
    )
    free_minutes = sum(
        int((slot_end - slot_start).total_seconds() // 60)
        for slot_start, slot_end in slots
    )
    longest_free = max(
        (
            int((slot_end - slot_start).total_seconds() // 60)
            for slot_start, slot_end in slots
        ),
        default=0,
    )
    return {
        "window_minutes": window_minutes,
        "free_minutes": free_minutes,
        "busy_minutes": max(0, window_minutes - free_minutes),
        "longest_free_minutes": longest_free,
    }


def reminder_duration_summary(
    items: list[dict[str, Any]],
    *,
    include_paused: bool = False,
) -> dict[str, int]:
    """予定群の明示された所要時間合計と未設定件数を返す。"""
    total = 0
    timed_count = 0
    missing_count = 0

    for item in items:
        if item.get("paused") and not include_paused:
            continue
        try:
            duration = int(item.get("duration_minutes") or 0)
        except (TypeError, ValueError):
            duration = 0

        if duration > 0:
            total += min(duration, 1440)
            timed_count += 1
        else:
            missing_count += 1

    return {
        "total_minutes": total,
        "timed_count": timed_count,
        "missing_count": missing_count,
    }


def reminders_missing_duration() -> list[dict[str, Any]]:
    """所要時間が未設定の未完了予定を時刻順で返す。"""
    result: list[dict[str, Any]] = []
    for item in list_reminders():
        try:
            duration = int(item.get("duration_minutes") or 0)
        except (TypeError, ValueError):
            duration = 0
        if duration <= 0:
            result.append(item)
    result.sort(key=lambda item: str(item.get("due_at", "")))
    return result


def _next_projected_repeat_due(
    due: datetime,
    item: dict[str, Any],
) -> datetime | None:
    """保存状態を変更せず、繰り返し予定の次回日時を1回分だけ計算する。"""
    rule = item.get("repeat_rule")
    if rule == "daily":
        return due + timedelta(days=1)
    if rule == "weekdays":
        candidate = due + timedelta(days=1)
        while candidate.weekday() >= 5:
            candidate += timedelta(days=1)
        return candidate
    if rule == "weekly":
        return due + timedelta(days=7)
    if rule == "monthly":
        try:
            repeat_day = int(item.get("repeat_day") or due.day)
        except (TypeError, ValueError):
            return None
        if not 1 <= repeat_day <= 31:
            return None
        year = due.year + (1 if due.month == 12 else 0)
        month = 1 if due.month == 12 else due.month + 1
        last_day = calendar.monthrange(year, month)[1]
        return due.replace(
            year=year,
            month=month,
            day=min(repeat_day, last_day),
        )
    return None


def project_reminder_occurrences(
    start_date,
    end_date,
    now: datetime | None = None,
    *,
    include_paused: bool = False,
) -> list[dict[str, Any]]:
    """現在の未完了予定を、指定日付範囲へ安全に投影して返す。"""
    current = now or datetime.now().astimezone()
    if end_date < start_date:
        return []

    projected: list[dict[str, Any]] = []
    for item in list_reminders():
        if item.get("paused") and not include_paused:
            continue

        try:
            actual_due = datetime.fromisoformat(str(item.get("due_at", "")))
            if actual_due.tzinfo is None and current.tzinfo is not None:
                actual_due = actual_due.replace(tzinfo=current.tzinfo)
            elif actual_due.tzinfo is not None and current.tzinfo is not None:
                actual_due = actual_due.astimezone(current.tzinfo)
        except (TypeError, ValueError):
            continue

        if start_date <= actual_due.date() <= end_date:
            occurrence = dict(item)
            occurrence["due_at"] = actual_due.isoformat(timespec="seconds")
            projected.append(occurrence)

        if item.get("repeat_rule") not in (
            "daily",
            "weekdays",
            "weekly",
            "monthly",
        ):
            continue

        anchor_raw = item.get("snooze_original_due_at") or item.get("due_at")
        try:
            anchor = datetime.fromisoformat(str(anchor_raw))
            if anchor.tzinfo is None and current.tzinfo is not None:
                anchor = anchor.replace(tzinfo=current.tzinfo)
            elif anchor.tzinfo is not None and current.tzinfo is not None:
                anchor = anchor.astimezone(current.tzinfo)
        except (TypeError, ValueError):
            continue

        candidate = anchor
        while candidate <= actual_due:
            candidate = _next_projected_repeat_due(candidate, item)
            if candidate is None:
                break

        while candidate is not None and candidate.date() <= end_date:
            if candidate.date() >= start_date:
                occurrence = dict(item)
                occurrence["due_at"] = candidate.isoformat(timespec="seconds")
                occurrence.pop("snooze_original_due_at", None)
                projected.append(occurrence)
            candidate = _next_projected_repeat_due(candidate, item)

    projected.sort(key=lambda item: str(item.get("due_at", "")))
    return projected


def schedule_items_window_stats(
    items: list[dict[str, Any]],
    start_at: datetime,
    end_at: datetime,
) -> dict[str, int]:
    """与えられた予定群だけを使って指定時間帯の占有状況を集計する。"""
    if end_at <= start_at:
        return {
            "window_minutes": 0,
            "free_minutes": 0,
            "busy_minutes": 0,
            "longest_free_minutes": 0,
        }

    busy: list[tuple[datetime, datetime]] = []
    for item in items:
        if item.get("paused"):
            continue
        interval = _reminder_interval(item, start_at)
        if interval is None:
            continue
        busy_start, busy_end = interval
        if busy_end <= start_at or busy_start >= end_at:
            continue
        busy.append((max(busy_start, start_at), min(busy_end, end_at)))

    busy.sort(key=lambda row: row[0])
    merged: list[list[datetime]] = []
    for busy_start, busy_end in busy:
        if not merged or busy_start > merged[-1][1]:
            merged.append([busy_start, busy_end])
        elif busy_end > merged[-1][1]:
            merged[-1][1] = busy_end

    window_minutes = int((end_at - start_at).total_seconds() // 60)
    busy_minutes = sum(
        int((busy_end - busy_start).total_seconds() // 60)
        for busy_start, busy_end in merged
    )

    free_ranges: list[tuple[datetime, datetime]] = []
    cursor = start_at
    for busy_start, busy_end in merged:
        if busy_start > cursor:
            free_ranges.append((cursor, busy_start))
        if busy_end > cursor:
            cursor = busy_end
    if cursor < end_at:
        free_ranges.append((cursor, end_at))

    longest_free = max(
        (
            int((free_end - free_start).total_seconds() // 60)
            for free_start, free_end in free_ranges
        ),
        default=0,
    )
    return {
        "window_minutes": window_minutes,
        "free_minutes": max(0, window_minutes - busy_minutes),
        "busy_minutes": max(0, busy_minutes),
        "longest_free_minutes": longest_free,
    }


def day_schedule_summary(
    target_date,
    now: datetime | None = None,
) -> dict[str, Any]:
    """指定日の投影予定について件数・所要時間・重なりを要約する。"""
    current = now or datetime.now().astimezone()
    items = project_reminder_occurrences(
        target_date,
        target_date,
        current,
    )
    duration_summary = reminder_duration_summary(items)
    important_count = sum(1 for item in items if item.get("important"))

    intervals: list[tuple[datetime, datetime]] = []
    for item in items:
        interval = _reminder_interval(item, current)
        if interval is not None:
            intervals.append(interval)
    intervals.sort(key=lambda pair: pair[0])
    conflicts = 0
    for index, (start, finish) in enumerate(intervals):
        for other_start, other_finish in intervals[index + 1:]:
            if other_start >= finish:
                break
            if start < other_finish and other_start < finish:
                conflicts += 1

    return {
        "date": target_date.isoformat(),
        "count": len(items),
        "total_minutes": duration_summary["total_minutes"],
        "timed_count": duration_summary["timed_count"],
        "missing_count": duration_summary["missing_count"],
        "important_count": important_count,
        "conflict_pairs": conflicts,
    }


def remaining_week_schedule_summary(
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """今日から今週日曜までの日別予定要約を返す。"""
    current = now or datetime.now().astimezone()
    sunday = current.date() + timedelta(days=6 - current.weekday())
    result: list[dict[str, Any]] = []
    target = current.date()
    while target <= sunday:
        result.append(day_schedule_summary(target, current))
        target += timedelta(days=1)
    return result


def find_first_free_slot(
    start_at: datetime,
    end_at: datetime,
    *,
    required_minutes: int,
    exclude_reminder_id: str | None = None,
) -> tuple[datetime, datetime] | None:
    """必要時間を満たす最初の空き枠を返す。"""
    try:
        required = int(required_minutes)
    except (TypeError, ValueError):
        return None
    if not 1 <= required <= 1440:
        return None

    slots = find_free_time_slots(
        start_at,
        end_at,
        minimum_minutes=required,
        exclude_reminder_id=exclude_reminder_id,
    )
    if not slots:
        return None

    start, available_end = slots[0]
    end = start + timedelta(minutes=required)
    if end > available_end:
        return None
    return start, end


def find_conflicting_reminders(
    reminder_id: str,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """対象予定と時間帯が重なる他の通知中予定を返す。"""
    current = now or datetime.now().astimezone()
    items = list_reminders()
    target = next((item for item in items if item.get("id") == reminder_id), None)
    if target is None or target.get("paused"):
        return []

    target_interval = _reminder_interval(target, current)
    if target_interval is None:
        return []
    target_start, target_end = target_interval

    conflicts: list[dict[str, Any]] = []
    for item in items:
        if item.get("id") == reminder_id or item.get("paused"):
            continue
        interval = _reminder_interval(item, current)
        if interval is None:
            continue
        start, end = interval
        if target_start < end and start < target_end:
            conflicts.append(item)

    conflicts.sort(key=lambda item: str(item.get("due_at", "")))
    return conflicts


def important_reminders() -> list[dict[str, Any]]:
    """重要フラグが付いた未完了予定を時刻順で返す。"""
    items = [item for item in list_reminders() if item.get("important")]
    items.sort(key=lambda item: str(item.get("due_at", "")))
    return items


def set_reminder_note(
    reminder_id: str,
    note: str | None,
) -> dict[str, Any] | None:
    """予定のメモだけを設定・解除する。"""
    clean = None
    if note is not None:
        clean = str(note).strip()
        if (
            not clean
            or len(clean) > 500
            or any(ord(ch) < 32 for ch in clean)
        ):
            return None

    items = _load()
    for item in items:
        if item.get("id") != reminder_id or item.get("done"):
            continue
        if clean is None:
            item.pop("note", None)
        else:
            item["note"] = clean
        _save(items)
        return item
    return None


def set_reminder_location(
    reminder_id: str,
    location: str | None,
) -> dict[str, Any] | None:
    """予定の場所だけを設定・解除する。"""
    clean = None
    if location is not None:
        clean = str(location).strip()
        if (
            not clean
            or len(clean) > 100
            or any(ord(ch) < 32 for ch in clean)
        ):
            return None

    items = _load()
    for item in items:
        if item.get("id") != reminder_id or item.get("done"):
            continue
        if clean is None:
            item.pop("location", None)
        else:
            item["location"] = clean
        _save(items)
        return item
    return None


def set_reminder_category(
    reminder_id: str,
    category: str | None,
) -> dict[str, Any] | None:
    """予定のカテゴリだけを設定・解除する。"""
    clean = None
    if category is not None:
        clean = str(category).strip()
        if (
            not clean
            or len(clean) > 32
            or any(ord(ch) < 32 for ch in clean)
        ):
            return None

    items = _load()
    for item in items:
        if item.get("id") != reminder_id or item.get("done"):
            continue
        if clean is None:
            item.pop("category", None)
        else:
            item["category"] = clean
        _save(items)
        return item
    return None


def reminders_by_category(category: str) -> list[dict[str, Any]]:
    """カテゴリ完全一致の未完了予定を時刻順で返す。"""
    needle = _normalize_reminder_text(category)
    if not needle:
        return []

    result = [
        item
        for item in list_reminders()
        if _normalize_reminder_text(item.get("category", "")) == needle
    ]
    result.sort(key=lambda item: str(item.get("due_at", "")))
    return result


def reminder_category_counts(
    items: list[dict[str, Any]],
) -> dict[str, int]:
    """予定群をカテゴリ別に集計する。未分類は「未分類」として数える。"""
    counts: dict[str, int] = {}
    for item in items:
        category = str(item.get("category") or "").strip() or "未分類"
        counts[category] = counts.get(category, 0) + 1
    return dict(
        sorted(
            counts.items(),
            key=lambda pair: (-pair[1], pair[0]),
        )
    )


def set_reminder_duration(
    reminder_id: str,
    minutes: int | None,
) -> dict[str, Any] | None:
    """予定の所要時間を変更する。Noneなら所要時間だけ解除する。"""
    duration = None
    if minutes is not None:
        try:
            duration = int(minutes)
        except (TypeError, ValueError):
            return None
        if not 1 <= duration <= 1440:
            return None

    items = _load()
    for item in items:
        if item.get("id") != reminder_id or item.get("done"):
            continue
        if duration is None:
            item.pop("duration_minutes", None)
        else:
            item["duration_minutes"] = duration
        _save(items)
        return item
    return None


def set_reminder_importance(
    reminder_id: str,
    important: bool,
) -> dict[str, Any] | None:
    """予定の重要フラグだけを変更する。"""
    items = _load()
    for item in items:
        if item.get("id") != reminder_id or item.get("done"):
            continue
        if important:
            item["important"] = True
        else:
            item.pop("important", None)
        _save(items)
        return item
    return None


def filter_reminders_by_due(
    items: list[dict[str, Any]],
    *,
    date: str | None = None,
    hour: int | None = None,
    minute: int | None = None,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """候補を日付・時刻で安全に絞り込む。日時指定なしならそのまま返す。"""
    if date is None and hour is None and minute is None:
        return list(items)

    current = now or datetime.now().astimezone()
    result: list[dict[str, Any]] = []
    for item in items:
        try:
            due = datetime.fromisoformat(str(item["due_at"]))
            if due.tzinfo is None and current.tzinfo is not None:
                due = due.replace(tzinfo=current.tzinfo)
            elif due.tzinfo is not None and current.tzinfo is not None:
                due = due.astimezone(current.tzinfo)
        except (KeyError, TypeError, ValueError):
            continue

        if date is not None and due.date().isoformat() != str(date):
            continue
        if hour is not None and due.hour != int(hour):
            continue
        if minute is not None and due.minute != int(minute):
            continue
        result.append(item)

    return result


def _date_reminders(target_date, current: datetime) -> list[dict[str, Any]]:
    result = []
    for item in list_reminders():
        try:
            due = datetime.fromisoformat(str(item["due_at"])).astimezone(current.tzinfo)
            if due.date() == target_date:
                result.append(item)
        except (KeyError, TypeError, ValueError):
            continue
    result.sort(key=lambda item: str(item.get("due_at", "")))
    return result


def today_reminders(now: datetime | None = None) -> list[dict[str, Any]]:
    current = now or datetime.now().astimezone()
    return _date_reminders(current.date(), current)


def tomorrow_reminders(now: datetime | None = None) -> list[dict[str, Any]]:
    current = now or datetime.now().astimezone()
    return _date_reminders((current + timedelta(days=1)).date(), current)


def _range_reminders(start_date, end_date, current: datetime) -> list[dict[str, Any]]:
    """開始日〜終了日の未完了予定を時刻順で返す。"""
    result: list[dict[str, Any]] = []
    for item in list_reminders():
        try:
            due = datetime.fromisoformat(str(item["due_at"]))
            if due.tzinfo is None and current.tzinfo is not None:
                due = due.replace(tzinfo=current.tzinfo)
            elif due.tzinfo is not None and current.tzinfo is not None:
                due = due.astimezone(current.tzinfo)
        except (KeyError, TypeError, ValueError):
            continue
        if start_date <= due.date() <= end_date:
            result.append(item)
    result.sort(key=lambda item: str(item.get("due_at", "")))
    return result


def week_reminders(now: datetime | None = None) -> list[dict[str, Any]]:
    """現在の暦週（月曜〜日曜）の未完了予定を返す。"""
    current = now or datetime.now().astimezone()
    monday = current.date() - timedelta(days=current.weekday())
    sunday = monday + timedelta(days=6)
    return _range_reminders(monday, sunday, current)


def month_reminders(now: datetime | None = None) -> list[dict[str, Any]]:
    """現在の暦月の未完了予定を返す。"""
    current = now or datetime.now().astimezone()
    last_day = calendar.monthrange(current.year, current.month)[1]
    start = current.date().replace(day=1)
    end = current.date().replace(day=last_day)
    return _range_reminders(start, end, current)


def overdue_reminders(
    now: datetime | None = None,
    *,
    include_paused: bool = False,
) -> list[dict[str, Any]]:
    """期限を過ぎた未完了予定を古い順に返す。"""
    current = now or datetime.now().astimezone()
    result: list[dict[str, Any]] = []
    for item in list_reminders():
        if item.get("paused") and not include_paused:
            continue
        try:
            due = datetime.fromisoformat(str(item.get("due_at", "")))
            if due.tzinfo is None and current.tzinfo is not None:
                due = due.replace(tzinfo=current.tzinfo)
            elif due.tzinfo is not None and current.tzinfo is not None:
                due = due.astimezone(current.tzinfo)
        except (TypeError, ValueError):
            continue
        if due < current:
            result.append(item)
    result.sort(key=lambda item: str(item.get("due_at", "")))
    return result


def upcoming_reminders(days: int = 7, now: datetime | None = None) -> list[dict[str, Any]]:
    """現在から指定日数以内の未完了予定を時刻順で返す。"""
    current = now or datetime.now().astimezone()
    end = current + timedelta(days=max(1, int(days)))
    result = []
    for item in list_reminders():
        try:
            due = datetime.fromisoformat(str(item["due_at"])).astimezone(current.tzinfo)
            if current <= due <= end:
                result.append(item)
        except (KeyError, TypeError, ValueError):
            continue
    result.sort(key=lambda item: str(item.get("due_at", "")))
    return result




def set_reminder_pre_notify(
    reminder_id: str,
    minutes: int,
) -> dict[str, Any] | None:
    """予定の事前通知を設定する。1分〜24時間前まで。"""
    try:
        value = int(minutes)
    except (TypeError, ValueError):
        return None
    if not 1 <= value <= 1440:
        return None

    items = _load()
    for item in items:
        if item.get("id") != reminder_id or item.get("done"):
            continue
        item["notify_before_minutes"] = value
        item.pop("pre_notified_due_at", None)
        _save(items)
        return item
    return None


def clear_reminder_pre_notify(reminder_id: str) -> dict[str, Any] | None:
    """事前通知だけを解除する。通常の本番通知は残す。"""
    items = _load()
    for item in items:
        if item.get("id") != reminder_id or item.get("done"):
            continue
        item.pop("notify_before_minutes", None)
        item.pop("pre_notified_due_at", None)
        _save(items)
        return item
    return None


def pre_due_reminders(
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """事前通知の時間帯に入った未通知予定を返す。"""
    current = now or datetime.now().astimezone()
    result: list[dict[str, Any]] = []

    for item in list_reminders():
        if item.get("paused"):
            continue

        try:
            lead = int(item.get("notify_before_minutes") or 0)
        except (TypeError, ValueError):
            continue
        if not 1 <= lead <= 1440:
            continue

        try:
            due = datetime.fromisoformat(str(item.get("due_at", "")))
            if due.tzinfo is None and current.tzinfo is not None:
                due = due.replace(tzinfo=current.tzinfo)
            elif due.tzinfo is not None and current.tzinfo is not None:
                due = due.astimezone(current.tzinfo)
        except (TypeError, ValueError):
            continue

        due_key = str(item.get("due_at", ""))
        if item.get("pre_notified_due_at") == due_key:
            continue

        start = due - timedelta(minutes=lead)
        if start <= current < due:
            result.append(item)

    result.sort(key=lambda item: str(item.get("due_at", "")))
    return result


def mark_reminder_pre_notified(
    reminder_id: str,
    due_at: str,
) -> bool:
    """現在の予定時刻に対する事前通知済みマーカーを保存する。"""
    due_key = str(due_at or "").strip()
    if not due_key:
        return False

    items = _load()
    for item in items:
        if item.get("id") != reminder_id or item.get("done"):
            continue
        if str(item.get("due_at", "")) != due_key:
            return False
        item["pre_notified_due_at"] = due_key
        _save(items)
        return True
    return False


def reminders_within(
    minutes: int = 30,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """現在から指定分以内に始まる通知中の予定を時刻順で返す。"""
    current = now or datetime.now().astimezone()
    window = max(1, min(int(minutes), 1440))
    end = current + timedelta(minutes=window)
    result: list[dict[str, Any]] = []

    for item in list_reminders():
        if item.get("paused"):
            continue
        try:
            due = datetime.fromisoformat(str(item.get("due_at", "")))
            if due.tzinfo is None and current.tzinfo is not None:
                due = due.replace(tzinfo=current.tzinfo)
            elif due.tzinfo is not None and current.tzinfo is not None:
                due = due.astimezone(current.tzinfo)
        except (TypeError, ValueError):
            continue

        if current <= due <= end:
            result.append(item)

    result.sort(key=lambda item: str(item.get("due_at", "")))
    return result


def due_reminders(now: datetime | None = None) -> list[dict[str, Any]]:
    current = now or datetime.now().astimezone()
    result = []
    for item in list_reminders():
        if item.get("paused"):
            continue
        try:
            due = datetime.fromisoformat(str(item["due_at"]))
            if due <= current:
                result.append(item)
        except (KeyError, TypeError, ValueError):
            continue
    return result


def move_reminder_occurrence(
    reminder_id: str,
    due_at: str,
) -> dict[str, Any] | None:
    """予定を指定時刻へ移す。定期予定は今回分だけ移し、次回周期は元の時刻を維持する。"""
    try:
        due = datetime.fromisoformat(str(due_at))
    except (TypeError, ValueError):
        return None

    items = _load()
    for item in items:
        if item.get("id") != reminder_id or item.get("done"):
            continue

        try:
            old_due = datetime.fromisoformat(str(item.get("due_at", "")))
        except (TypeError, ValueError):
            return None

        if item.get("repeat_rule") in ("daily", "weekdays", "weekly", "monthly"):
            item.setdefault(
                "snooze_original_due_at",
                old_due.isoformat(timespec="seconds"),
            )
        else:
            item.pop("snooze_original_due_at", None)

        item["due_at"] = due.isoformat(timespec="seconds")
        item.pop("pre_notified_due_at", None)
        _save(items)
        return item
    return None


def snooze_reminder(
    reminder_id: str,
    minutes: int,
    now: datetime | None = None,
) -> dict[str, Any] | None:
    """今回の予定だけを指定分後へ回す。定期予定の次回周期は元時刻を維持する。"""
    try:
        delay = int(minutes)
    except (TypeError, ValueError):
        return None
    if not 1 <= delay <= 1440:
        return None

    current = now or datetime.now().astimezone()
    items = _load()
    for item in items:
        if item.get("id") != reminder_id or item.get("done"):
            continue

        try:
            old_due = datetime.fromisoformat(str(item.get("due_at", "")))
            if old_due.tzinfo is None and current.tzinfo is not None:
                old_due = old_due.replace(tzinfo=current.tzinfo)
            elif old_due.tzinfo is not None and current.tzinfo is not None:
                old_due = old_due.astimezone(current.tzinfo)
        except (TypeError, ValueError):
            return None

        if item.get("repeat_rule") in ("daily", "weekdays", "weekly", "monthly"):
            item.setdefault(
                "snooze_original_due_at",
                old_due.isoformat(timespec="seconds"),
            )
        else:
            item.pop("snooze_original_due_at", None)

        new_due = current + timedelta(minutes=delay)
        item["due_at"] = new_due.isoformat(timespec="seconds")
        item.pop("pre_notified_due_at", None)
        _save(items)
        return item
    return None


def reschedule_reminder(reminder_id: str, due_at: str) -> dict[str, Any] | None:
    """IDが一致する未完了リマインダーの日時だけを更新する。"""
    try:
        due = datetime.fromisoformat(str(due_at))
    except (TypeError, ValueError):
        return None

    items = _load()
    for item in items:
        if item.get("id") != reminder_id or item.get("done"):
            continue
        item["due_at"] = due.isoformat(timespec="seconds")
        item.pop("snooze_original_due_at", None)
        item.pop("pre_notified_due_at", None)
        if item.get("repeat_rule") == "monthly":
            item["repeat_day"] = due.day
        _save(items)
        return item
    return None




def set_reminder_repeat(
    reminder_id: str,
    repeat_rule: str,
    *,
    repeat_day: int | None = None,
    repeat_weekday: int | None = None,
    now: datetime | None = None,
) -> dict[str, Any] | None:
    """未完了予定の繰り返し設定を変更し、次回日時を未来へ正規化する。"""
    try:
        rule = _normalize_repeat_rule(repeat_rule)
    except ValueError:
        return None
    if rule is None:
        return clear_reminder_repeat(reminder_id)

    current = now or datetime.now().astimezone()
    items = _load()
    for item in items:
        if item.get("id") != reminder_id or item.get("done"):
            continue

        try:
            due = datetime.fromisoformat(str(item.get("due_at", "")))
        except (TypeError, ValueError):
            return None

        if due.tzinfo is None and current.tzinfo is not None:
            due = due.replace(tzinfo=current.tzinfo)
        elif due.tzinfo is not None and current.tzinfo is not None:
            due = due.astimezone(current.tzinfo)

        hour, minute, second = due.hour, due.minute, due.second
        base = current.replace(
            hour=hour,
            minute=minute,
            second=second,
            microsecond=0,
        )

        if rule == "daily":
            next_due = base
            if next_due <= current:
                next_due += timedelta(days=1)
            item.pop("repeat_day", None)
        elif rule == "weekdays":
            next_due = base
            if next_due <= current:
                next_due += timedelta(days=1)
            while next_due.weekday() >= 5:
                next_due += timedelta(days=1)
            item.pop("repeat_day", None)
        elif rule == "weekly":
            try:
                weekday = int(
                    due.weekday() if repeat_weekday is None else repeat_weekday
                )
            except (TypeError, ValueError):
                return None
            if not 0 <= weekday <= 6:
                return None
            days_ahead = (weekday - current.weekday()) % 7
            next_due = base + timedelta(days=days_ahead)
            if next_due <= current:
                next_due += timedelta(days=7)
            item.pop("repeat_day", None)
        else:
            try:
                day = int(repeat_day or due.day)
            except (TypeError, ValueError):
                return None
            if not 1 <= day <= 31:
                return None

            year, month = current.year, current.month
            last_day = calendar.monthrange(year, month)[1]
            next_due = current.replace(
                day=min(day, last_day),
                hour=hour,
                minute=minute,
                second=second,
                microsecond=0,
            )
            if next_due <= current:
                year = year + (1 if month == 12 else 0)
                month = 1 if month == 12 else month + 1
                last_day = calendar.monthrange(year, month)[1]
                next_due = next_due.replace(
                    year=year,
                    month=month,
                    day=min(day, last_day),
                )
            item["repeat_day"] = day

        item["repeat_rule"] = rule
        item["due_at"] = next_due.isoformat(timespec="seconds")
        item.pop("snooze_original_due_at", None)
        item.pop("pre_notified_due_at", None)
        _save(items)
        return item
    return None



def pause_reminder(reminder_id: str) -> dict[str, Any] | None:
    """予定の通知だけを一時停止する。予定内容と繰り返し設定は保持する。"""
    items = _load()
    for item in items:
        if item.get("id") != reminder_id or item.get("done"):
            continue
        item["paused"] = True
        _save(items)
        return item
    return None


def resume_reminder(
    reminder_id: str,
    now: datetime | None = None,
) -> dict[str, Any] | None:
    """一時停止を解除し、期限切れの定期予定は次回の未来日時へ進める。"""
    current = now or datetime.now().astimezone()
    items = _load()
    target = None
    for item in items:
        if item.get("id") != reminder_id or item.get("done"):
            continue
        item.pop("paused", None)
        target = item
        _save(items)
        break

    if target is None:
        return None

    try:
        due = datetime.fromisoformat(str(target.get("due_at", "")))
        if due.tzinfo is None and current.tzinfo is not None:
            due = due.replace(tzinfo=current.tzinfo)
        elif due.tzinfo is not None and current.tzinfo is not None:
            due = due.astimezone(current.tzinfo)
    except (TypeError, ValueError):
        return target

    if (
        due <= current
        and target.get("repeat_rule") in ("daily", "weekdays", "weekly", "monthly")
    ):
        advanced = advance_recurring_reminder(reminder_id, now=current)
        return advanced or target
    return target


def clear_reminder_repeat(reminder_id: str) -> dict[str, Any] | None:
    """繰り返し設定だけを解除し、現在の次回予定は1回分として残す。"""
    items = _load()
    for item in items:
        if item.get("id") != reminder_id or item.get("done"):
            continue
        item.pop("repeat_rule", None)
        item.pop("repeat_day", None)
        item.pop("snooze_original_due_at", None)
        _save(items)
        return item
    return None


def rename_reminder(reminder_id: str, new_text: str) -> dict[str, Any] | None:
    """IDが一致する未完了リマインダーの名前だけを更新する。"""
    name = str(new_text or "").strip()
    if not name or any(ord(char) < 32 for char in name):
        return None

    items = _load()
    for item in items:
        if item.get("id") != reminder_id or item.get("done"):
            continue
        item["text"] = name
        _save(items)
        return item
    return None



def advance_recurring_reminder(
    reminder_id: str,
    now: datetime | None = None,
    *,
    record_completion: bool = False,
) -> dict[str, Any] | None:
    """繰り返し予定を次回へ進める。遅延時は現在時刻より後まで繰り越す。"""
    current = now or datetime.now().astimezone()
    items = _load()
    for item in items:
        if item.get("id") != reminder_id or item.get("done"):
            continue

        rule = item.get("repeat_rule")
        if rule not in ("daily", "weekdays", "weekly", "monthly"):
            return None

        if record_completion:
            history = item.get("completion_history")
            if not isinstance(history, list):
                history = []
            entry = {
                "reminder_id": item.get("id"),
                "text": str(item.get("text") or ""),
                "due_at": str(item.get("due_at") or ""),
                "completed_at": current.isoformat(timespec="seconds"),
            }
            for key in (
                "category",
                "duration_minutes",
                "important",
                "note",
                "location",
                "repeat_rule",
                "repeat_day",
            ):
                if key in item:
                    entry[key] = item[key]
            history.append(entry)
            item["completion_history"] = history[-200:]

        anchor_due_at = item.pop("snooze_original_due_at", None)
        try:
            due = datetime.fromisoformat(
                str(anchor_due_at or item.get("due_at", ""))
            )
        except (TypeError, ValueError):
            return None

        if due.tzinfo is None and current.tzinfo is not None:
            due = due.replace(tzinfo=current.tzinfo)
        elif due.tzinfo is not None and current.tzinfo is not None:
            due = due.astimezone(current.tzinfo)

        if rule == "daily":
            due += timedelta(days=1)
            while due <= current:
                due += timedelta(days=1)
        elif rule == "weekdays":
            due += timedelta(days=1)
            while due.weekday() >= 5:
                due += timedelta(days=1)
            while due <= current:
                due += timedelta(days=1)
                while due.weekday() >= 5:
                    due += timedelta(days=1)
        elif rule == "weekly":
            due += timedelta(days=7)
            while due <= current:
                due += timedelta(days=7)
        else:
            try:
                repeat_day = int(item.get("repeat_day") or due.day)
            except (TypeError, ValueError):
                return None
            if not 1 <= repeat_day <= 31:
                return None

            while True:
                year = due.year + (1 if due.month == 12 else 0)
                month = 1 if due.month == 12 else due.month + 1
                last_day = calendar.monthrange(year, month)[1]
                due = due.replace(
                    year=year,
                    month=month,
                    day=min(repeat_day, last_day),
                )
                if due > current:
                    break

        item["due_at"] = due.isoformat(timespec="seconds")
        item["done"] = False
        _save(items)
        return item
    return None


def complete_reminder(
    reminder_id: str,
    now: datetime | None = None,
) -> bool:
    """通常予定は完了日時を保存し、繰り返し予定は今回分を記録して次回へ進める。"""
    current = now or datetime.now().astimezone()
    items = _load()
    for item in items:
        if item.get("id") != reminder_id:
            continue
        if item.get("done"):
            return False
        if item.get("repeat_rule") in ("daily", "weekdays", "weekly", "monthly"):
            return (
                advance_recurring_reminder(
                    reminder_id,
                    now=current,
                    record_completion=True,
                )
                is not None
            )
        item["done"] = True
        item["completed_at"] = current.isoformat(timespec="seconds")
        _save(items)
        return True
    return False


def completion_events(
    start_date=None,
    end_date=None,
    now: datetime | None = None,
    *,
    category: str | None = None,
) -> list[dict[str, Any]]:
    """保存済みの完了履歴を指定日付範囲で返す。"""
    current = now or datetime.now().astimezone()
    events: list[dict[str, Any]] = []
    category_needle = (
        _normalize_reminder_text(category)
        if category is not None
        else ""
    )

    def _category_matches(event: dict[str, Any]) -> bool:
        if category is None:
            return True
        return (
            _normalize_reminder_text(event.get("category", ""))
            == category_needle
        )

    def _in_range(completed_at: str) -> bool:
        try:
            completed = datetime.fromisoformat(str(completed_at))
            if completed.tzinfo is None and current.tzinfo is not None:
                completed = completed.replace(tzinfo=current.tzinfo)
            elif completed.tzinfo is not None and current.tzinfo is not None:
                completed = completed.astimezone(current.tzinfo)
        except (TypeError, ValueError):
            return False
        if start_date is not None and completed.date() < start_date:
            return False
        if end_date is not None and completed.date() > end_date:
            return False
        return True

    for item in _load():
        completed_at = item.get("completed_at")
        if item.get("done") and completed_at and _in_range(str(completed_at)):
            event = {
                "reminder_id": item.get("id"),
                "text": str(item.get("text") or ""),
                "due_at": str(item.get("due_at") or ""),
                "completed_at": str(completed_at),
            }
            for key in ("category", "duration_minutes", "important", "note", "location"):
                if key in item:
                    event[key] = item[key]
            if _category_matches(event):
                events.append(event)

        history = item.get("completion_history")
        if not isinstance(history, list):
            continue
        for raw_event in history:
            if not isinstance(raw_event, dict):
                continue
            completed_at = raw_event.get("completed_at")
            if not completed_at or not _in_range(str(completed_at)):
                continue
            event = dict(raw_event)
            event.setdefault("reminder_id", item.get("id"))
            event.setdefault("text", str(item.get("text") or ""))
            if _category_matches(event):
                events.append(event)

    events.sort(key=lambda event: str(event.get("completed_at", "")))
    return events


def completion_events_for_date(
    target_date,
    now: datetime | None = None,
    *,
    category: str | None = None,
) -> list[dict[str, Any]]:
    """指定日に完了した予定履歴を返す。"""
    return completion_events(
        target_date,
        target_date,
        now,
        category=category,
    )


def completion_progress_summary(
    now: datetime | None = None,
    *,
    scope: str = "today",
) -> dict[str, int]:
    """今日または今週の完了件数と残り件数を返す。"""
    current = now or datetime.now().astimezone()
    normalized = str(scope or "today").strip().lower()

    if normalized == "today":
        target = current.date()
        completed = completion_events_for_date(target, current)
        remaining = _date_reminders(target, current)
        return {
            "completed_count": len(completed),
            "remaining_count": len(remaining),
        }

    if normalized != "week":
        return {
            "completed_count": 0,
            "remaining_count": 0,
        }

    monday = current.date() - timedelta(days=current.weekday())
    sunday = monday + timedelta(days=6)
    completed = completion_events(
        monday,
        current.date(),
        current,
    )

    remaining_future = project_reminder_occurrences(
        current.date(),
        sunday,
        current,
    )

    overdue_ids: set[str] = set()
    for item in list_reminders():
        try:
            due = datetime.fromisoformat(str(item.get("due_at", "")))
            if due.tzinfo is None and current.tzinfo is not None:
                due = due.replace(tzinfo=current.tzinfo)
            elif due.tzinfo is not None and current.tzinfo is not None:
                due = due.astimezone(current.tzinfo)
        except (TypeError, ValueError):
            continue
        if monday <= due.date() < current.date():
            reminder_id = str(item.get("id") or "")
            if reminder_id:
                overdue_ids.add(reminder_id)

    return {
        "completed_count": len(completed),
        "remaining_count": len(remaining_future) + len(overdue_ids),
    }


def completion_category_progress(
    target_date,
    now: datetime | None = None,
) -> dict[str, dict[str, int]]:
    """指定日のカテゴリ別に完了件数と未完了件数を返す。"""
    current = now or datetime.now().astimezone()
    completed = completion_events_for_date(target_date, current)
    remaining = _date_reminders(target_date, current)

    progress: dict[str, dict[str, int]] = {}
    for event in completed:
        category = str(event.get("category") or "").strip() or "未分類"
        bucket = progress.setdefault(category, {"completed": 0, "remaining": 0})
        bucket["completed"] += 1
    for item in remaining:
        category = str(item.get("category") or "").strip() or "未分類"
        bucket = progress.setdefault(category, {"completed": 0, "remaining": 0})
        bucket["remaining"] += 1

    return dict(
        sorted(
            progress.items(),
            key=lambda pair: (
                -(pair[1]["completed"] + pair[1]["remaining"]),
                pair[0],
            ),
        )
    )


def list_deleted_reminders(limit: int = 20) -> list[dict[str, Any]]:
    """最近削除した予定を新しい順で返す。"""
    try:
        safe_limit = max(1, min(int(limit), 200))
    except (TypeError, ValueError):
        safe_limit = 20
    items = _load_trash()
    items.sort(key=lambda item: str(item.get("deleted_at", "")), reverse=True)
    return items[:safe_limit]


def find_deleted_reminders(query: str) -> list[dict[str, Any]]:
    """削除履歴を予定名で完全一致優先検索する。"""
    needle = _normalize_reminder_text(query)
    if not needle:
        return []

    items = _load_trash()
    exact = [
        item
        for item in items
        if _normalize_reminder_text(item.get("text", "")) == needle
    ]
    if exact:
        return exact
    return [
        item
        for item in items
        if needle in _normalize_reminder_text(item.get("text", ""))
    ]


def restore_deleted_reminder(reminder_id: str) -> dict[str, Any] | None:
    """削除履歴から予定を元の内容のまま復元する。"""
    items = _load()
    if any(item.get("id") == reminder_id for item in items):
        return None

    trash = _load_trash()
    for index, deleted in enumerate(trash):
        if deleted.get("id") != reminder_id:
            continue
        restored = dict(deleted)
        restored.pop("deleted_at", None)
        items.append(restored)
        del trash[index]
        _save(items)
        _save_trash(trash)
        return restored
    return None


def delete_reminder(
    reminder_id: str,
    now: datetime | None = None,
) -> bool:
    """予定を削除し、復元できるよう削除履歴へ最大200件保存する。"""
    current = now or datetime.now().astimezone()
    items = _load()
    deleted = None
    remaining: list[dict[str, Any]] = []
    for item in items:
        if item.get("id") == reminder_id and deleted is None:
            deleted = dict(item)
            continue
        remaining.append(item)

    if deleted is None:
        return False

    deleted["deleted_at"] = current.isoformat(timespec="seconds")
    trash = _load_trash()
    trash.append(deleted)
    trash.sort(key=lambda item: str(item.get("deleted_at", "")))
    trash = trash[-200:]

    _save(remaining)
    _save_trash(trash)
    return True
