"""自然な日本語の予定追加をリマインダー形式へ正規化する。"""
from __future__ import annotations

import re
from datetime import datetime, timedelta


def parse_schedule_command(text: str, now: datetime | None = None) -> dict | None:
    raw = str(text or "").strip()
    if not raw:
        return None
    current = now or datetime.now().astimezone()

    day_match = re.search(r"(今日|明日|明後日)", raw)
    time_match = re.search(r"(午前|午後)?\s*(\d{1,2})\s*時(?:\s*(\d{1,2})\s*分?)?", raw)
    if not time_match:
        return None

    ampm, hour_s, minute_s = time_match.groups()
    hour = int(hour_s)
    minute = int(minute_s or 0)
    if ampm == "午前" and hour == 12:
        hour = 0
    elif ampm == "午後" and hour < 12:
        hour += 12
    if hour > 23 or minute > 59:
        return None

    day = day_match.group(1) if day_match else "今日"
    offset = {"今日": 0, "明日": 1, "明後日": 2}[day]
    due = current.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=offset)
    if offset == 0 and due <= current:
        due += timedelta(days=1)

    content = raw
    content = re.sub(r"メイナ[、,\s]*", "", content, flags=re.IGNORECASE)
    content = re.sub(r"(今日|明日|明後日)", "", content)
    content = re.sub(r"(午前|午後)?\s*\d{1,2}\s*時(?:\s*\d{1,2}\s*分?)?", "", content)
    content = re.sub(r"(?:に)?(?:予定|スケジュール)?(?:を)?(?:追加|登録|入れて|設定)", "", content)
    content = re.sub(r"(?:して|してね|してください|お願いします)$", "", content)
    content = content.strip(" 、。！？?\t")
    if not content:
        return None

    return {"text": content, "due_at": due.isoformat(timespec="seconds")}
