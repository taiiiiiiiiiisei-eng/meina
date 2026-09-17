"""めいなの軽量ローカル長期記憶。秘密情報を前提にせずJSONへ保存する。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MEMORY_PATH = Path(__file__).with_name("meina_memory.json")


def _default_memory() -> dict[str, Any]:
    return {
        "user_settings": {},
        "facts": {},
        "conversation": [],
        "tasks": [],
    }


def load_memory() -> dict[str, Any]:
    if not MEMORY_PATH.exists():
        return _default_memory()
    try:
        data = json.loads(MEMORY_PATH.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return _default_memory()
        base = _default_memory()
        base.update({k: v for k, v in data.items() if k in base})
        return base
    except (OSError, json.JSONDecodeError):
        return _default_memory()


def save_memory(memory: dict[str, Any]) -> None:
    """ローカルJSONへ保存。親ディレクトリはプロジェクト直下固定。"""
    MEMORY_PATH.write_text(
        json.dumps(memory, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def set_user_setting(key: str, value: Any) -> None:
    memory = load_memory()
    memory["user_settings"][str(key)] = value
    save_memory(memory)


def get_user_setting(key: str, default: Any = None) -> Any:
    return load_memory()["user_settings"].get(str(key), default)


def remember_fact(key: str, value: Any) -> None:
    memory = load_memory()
    memory["facts"][str(key)] = value
    save_memory(memory)


def recall_fact(key: str, default: Any = None) -> Any:
    return load_memory()["facts"].get(str(key), default)


def add_conversation(role: str, text: str, limit: int = 50) -> None:
    memory = load_memory()
    history = memory["conversation"]
    history.append({"role": str(role), "text": str(text)})
    memory["conversation"] = history[-max(1, int(limit)) :]
    save_memory(memory)


def add_task(text: str) -> None:
    memory = load_memory()
    memory["tasks"].append({"text": str(text), "done": False})
    save_memory(memory)


def list_tasks() -> list[dict[str, Any]]:
    return list(load_memory()["tasks"])
