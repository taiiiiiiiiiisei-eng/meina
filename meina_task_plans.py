"""めいなの安全な固定タスク計画。自由なシェル実行は行わない。"""

from __future__ import annotations


TASK_PLANS = {
    "stream_prepare_valorant": (
        {"kind": "app_open", "target": "OBS", "label": "OBSを起動"},
        {"kind": "app_open", "target": "Discord", "label": "Discordを起動"},
        {"kind": "app_open", "target": "VALORANT", "label": "VALORANTを起動"},
    ),
    "stream_prepare_apex": (
        {"kind": "app_open", "target": "OBS", "label": "OBSを起動"},
        {"kind": "app_open", "target": "Discord", "label": "Discordを起動"},
        {"kind": "app_open", "target": "Apex", "label": "Apex Legendsを起動"},
    ),
}


def detect_task_plan(text: str) -> str | None:
    command = str(text or "").lower().replace(" ", "").replace("　", "")
    if any(alias in command for alias in ("valorant", "valo", "バロ", "バロラント", "ヴァロ", "ヴァロラント")):
        if "配信" in command or "twitch" in command:
            return "stream_prepare_valorant"
    if any(alias in command for alias in ("apex", "エーペックス", "エペ", "apexlegends")):
        if "配信" in command or "twitch" in command:
            return "stream_prepare_apex"
    if "配信準備" in command:
        return "stream_prepare_valorant"
    return None


def get_task_plan(name: str):
    return TASK_PLANS.get(name)


def validate_task_plan(name: str) -> bool:
    plan = get_task_plan(name)
    if not plan:
        return False
    allowed_targets = {
        "app_open": {"OBS", "Discord", "VALORANT", "Apex", "notepad", "calculator", "explorer"},
        "web_open": {"google", "youtube", "browser"},
    }
    for step in plan:
        if not isinstance(step, dict):
            return False
        kind = step.get("kind")
        target = step.get("target")
        label = step.get("label")
        if kind not in allowed_targets:
            return False
        if target not in allowed_targets[kind]:
            return False
        if not isinstance(target, str) or not target.strip():
            return False
        if not isinstance(label, str) or not label.strip():
            return False
    return True
