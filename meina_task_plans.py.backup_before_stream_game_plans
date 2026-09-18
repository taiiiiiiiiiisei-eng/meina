"""めいなの安全な固定タスク計画。自由なシェル実行は行わない。"""

from __future__ import annotations


TASK_PLANS = {
    "stream_prepare": (
        {"kind": "app_open", "target": "OBS", "label": "OBSを起動"},
        {"kind": "app_open", "target": "Discord", "label": "Discordを起動"},
        {"kind": "web_open", "target": "youtube", "label": "YouTubeを開く"},
    ),
}


def detect_task_plan(text: str) -> str | None:
    command = str(text or "").lower().replace(" ", "").replace("　", "")
    if "配信準備" in command:
        return "stream_prepare"
    return None


def get_task_plan(name: str):
    return TASK_PLANS.get(name)


def validate_task_plan(name: str) -> bool:
    plan = get_task_plan(name)
    if not plan:
        return False
    allowed_kinds = {"app_open", "web_open"}
    return all(
        isinstance(step, dict)
        and step.get("kind") in allowed_kinds
        and isinstance(step.get("target"), str)
        and isinstance(step.get("label"), str)
        for step in plan
    )
