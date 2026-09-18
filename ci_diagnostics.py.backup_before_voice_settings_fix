"""Generate a compact CI diagnostic report without changing project state."""
from __future__ import annotations

import datetime as dt
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPORT = ROOT / "ci_diagnostic_report.md"

COMMANDS = [
    ("Python version", [sys.executable, "--version"]),
    ("Compile meina_agent.py", [sys.executable, "-m", "py_compile", "meina_agent.py"]),
    ("Compile command_router.py", [sys.executable, "-m", "py_compile", "command_router.py"]),
    ("Compile meina2/tools.py", [sys.executable, "-m", "py_compile", "meina2/tools.py"]),
    ("Compile meina_app.py", [sys.executable, "-m", "py_compile", "meina_app.py"]),
    ("Compile meina_health.py", [sys.executable, "-m", "py_compile", "meina_health.py"]),
    ("Compile meina_doctor.py", [sys.executable, "-m", "py_compile", "meina_doctor.py"]),
    ("Compile meina_voice_intent.py", [sys.executable, "-m", "py_compile", "meina_voice_intent.py"]),
    ("Compile meina_twitch_intent.py", [sys.executable, "-m", "py_compile", "meina_twitch_intent.py"]),
    ("Router regression tests", [sys.executable, "tests/test_command_router.py"]),
    ("Static self-test", [sys.executable, "ci_self_test.py"]),
    ("Task plan self-test", [sys.executable, "meina_task_plan_self_test.py"]),
    ("Task plan integration self-test", [sys.executable, "meina_task_plan_integration_self_test.py"]),
    ("PC status self-test", [sys.executable, "meina_pc_status_self_test.py"]),
    ("Memory self-test", [sys.executable, "meina_memory_self_test.py"]),
    ("Reminder self-test", [sys.executable, "meina_reminders_self_test.py"]),
    ("Reminder AM PM self-test", [sys.executable, "meina_reminder_ampm_self_test.py"]),
    ("Core lightweight self-test", [sys.executable, "self_test.py"]),
    ("Voice intent self-test", [sys.executable, "meina_voice_intent_self_test.py"]),
    ("Twitch static self-test", [sys.executable, "twitch_self_test.py"]),
    ("Twitch command test", [sys.executable, "twitch_command_test.py"]),
    ("Twitch voice self-test", [sys.executable, "twitch_voice_self_test.py"]),
]

def run_command(label: str, command: list[str]) -> tuple[int, str]:
    result = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    output = (result.stdout or "") + (result.stderr or "")
    return result.returncode, output.strip()


def main() -> int:
    rows: list[str] = []
    rows.append("# Meina CI Diagnostic Report")
    rows.append("")
    rows.append(f"- Time (UTC): {dt.datetime.now(dt.timezone.utc).isoformat()}")
    rows.append(f"- Commit: {os.environ.get('GITHUB_SHA', 'local')}")
    rows.append(f"- Workflow: {os.environ.get('GITHUB_WORKFLOW', 'local')}")
    rows.append(f"- Job status: {os.environ.get('JOB_STATUS', 'unknown')}")
    rows.append("")

    overall_ok = True
    for label, command in COMMANDS:
        code, output = run_command(label, command)
        status = "PASS" if code == 0 else "FAIL"
        if code != 0:
            overall_ok = False
        rows.append(f"## {status}: {label}")
        rows.append("")
        rows.append("~~~text")
        rows.append("$ " + " ".join(command))
        rows.append(output or "(no output)")
        rows.append("~~~")
        rows.append("")

    rows.append("## Summary")
    rows.append("")
    rows.append("Diagnostic result: " + ("ALL PASS" if overall_ok else "FAILURES FOUND"))
    REPORT.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"Diagnostic report written to {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())