"""めいなローカル記憶モジュールの依存関係なしセルフテスト。"""
from __future__ import annotations

import tempfile
from pathlib import Path

import meina_memory


def main() -> int:
    original = meina_memory.MEMORY_PATH
    with tempfile.TemporaryDirectory() as tmp:
        meina_memory.MEMORY_PATH = Path(tmp) / "memory.json"
        meina_memory.remember_fact("test_fact", "hello")
        assert meina_memory.recall_fact("test_fact") == "hello"
        meina_memory.set_user_setting("test_setting", "ok")
        assert meina_memory.get_user_setting("test_setting") == "ok"
        meina_memory.add_conversation("user", "test")
        assert meina_memory.load_memory()["conversation"][-1]["text"] == "test"
        meina_memory.add_task("テスト")
        assert meina_memory.list_tasks()[-1]["text"] == "テスト"
    meina_memory.MEMORY_PATH = original
    print("Memory self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
