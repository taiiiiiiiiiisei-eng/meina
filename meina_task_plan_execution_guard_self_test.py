"""固定タスク計画の実行関数を静的に検証するテスト。"""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def _find_function(source: str, name: str) -> ast.FunctionDef:
    tree = ast.parse(source, filename="meina_agent.py")
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"missing function: {name}")


def _call_names(node: ast.AST) -> list[str]:
    names: list[str] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            if isinstance(child.func, ast.Name):
                names.append(child.func.id)
            elif isinstance(child.func, ast.Attribute):
                names.append(child.func.attr)
    return names


def main() -> int:
    source = (ROOT / "meina_agent.py").read_text(encoding="utf-8")
    node = _find_function(source, "execute_task_plan")
    calls = _call_names(node)

    # 実行前に必ず計画名を検証し、許可済みの計画だけ取得する。
    validation_lines = [
        child.lineno
        for child in ast.walk(node)
        if isinstance(child, ast.Call)
        and isinstance(child.func, ast.Name)
        and child.func.id == "validate_task_plan"
    ]
    plan_lines = [
        child.lineno
        for child in ast.walk(node)
        if isinstance(child, ast.Call)
        and isinstance(child.func, ast.Name)
        and child.func.id == "get_task_plan"
    ]
    assert validation_lines and plan_lines
    assert min(validation_lines) < min(plan_lines)

    # 各ステップは安全な共通実行関数を通る。
    assert "_execute_routed_command_base" in calls

    # 実行関数から自由なシェル実行やサブプロセス起動を直接呼ばない。
    assert "system" not in calls
    assert "Popen" not in calls
    assert "run" not in calls
    assert "check_output" not in calls
    assert "subprocess" not in calls

    # 計画失敗時の中断メッセージと、両対応ゲームの完了メッセージを保持する。
    assert "配信準備を中断しました" in source
    assert "stream_prepare_valorant" in source
    assert "stream_prepare_apex" in source
    assert "VALORANTの配信準備が完了しました" in source
    assert "Apex Legendsの配信準備が完了しました" in source

    print("Task plan execution guard self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
