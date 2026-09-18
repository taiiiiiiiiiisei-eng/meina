"""めいなGUIの依存関係なし静的セルフテスト。

Tkinterやmeina_agentを起動せず、GUIの重要な構造だけを確認する。
"""
from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "meina_app.py"


def main() -> int:
    source = SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(SOURCE))

    methods = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
    }

    required = {
        "__init__",
        "_focus_entry",
        "add_message",
        "set_busy",
        "_initialize",
        "send_text",
        "_process_text",
        "start_voice",
        "_process_voice",
        "main",
    }
    missing = required - methods
    assert not missing, f"missing GUI methods: {sorted(missing)}"

    assert "self.entry.bind("<Return>"" in source
    assert "threading.Thread(target=self._process_text" in source
    assert "threading.Thread(target=self._process_voice" in source
    assert "log_runtime_error("text", e)" in source
    assert "log_runtime_error("voice", e)" in source
    assert "finally:" in source
    assert "self.root.after(0, lambda: self.set_busy(False, "オンライン"))" in source
    assert 'root.protocol("WM_DELETE_WINDOW", root.destroy)' in source
    assert "meina_agent.process_command(text)" in source
    assert "meina_agent.listen(duration=5.0)" in source
    assert "はい、どうしました？" in source

    print("GUI static self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
