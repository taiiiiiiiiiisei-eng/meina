"""めいな起動用ランチャー。
実際に起動しているPython環境からCUDA DLLを自動検出してから本体を起動する。
"""
import os
import runpy
import site
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))


def add_cuda_dll_dirs() -> list[str]:
    candidates = []
    try:
        candidates.extend(site.getsitepackages())
    except Exception:
        pass
    try:
        candidates.append(site.getusersitepackages())
    except Exception:
        pass
    candidates.extend([
        os.path.join(sys.prefix, "Lib", "site-packages"),
        os.path.join(os.path.dirname(sys.executable), "Lib", "site-packages"),
    ])

    loaded_dirs = []
    seen = set()
    for site_packages in candidates:
        if not site_packages or site_packages in seen:
            continue
        seen.add(site_packages)
        for package in ("cublas", "cudnn"):
            dll_dir = os.path.join(site_packages, "nvidia", package, "bin")
            if not os.path.isdir(dll_dir):
                continue
            try:
                os.add_dll_directory(dll_dir)
            except Exception:
                pass
            os.environ["PATH"] = dll_dir + os.pathsep + os.environ.get("PATH", "")
            loaded_dirs.append(dll_dir)
    return loaded_dirs


def run_upgrade(script_name: str) -> int:
    script = os.path.join(ROOT, script_name)
    if not os.path.isfile(script):
        print(f"⚠️ 起動チェック対象が見つかりません: {script_name}")
        return 0
    result = subprocess.run([sys.executable, script], check=False)
    return result.returncode


if __name__ == "__main__":
    add_cuda_dll_dirs()

    # リマインダー秘書の最終版は「検査のみ」。
    # 旧アップグレーダーで execute_routed_command を再置換しない。
    if run_upgrade("upgrade_meina_reminder_secretary_final.py") != 0:
        print("❌ リマインダー秘書の安全チェックに失敗したため起動を停止します。")
        raise SystemExit(1)

    runpy.run_path(os.path.join(ROOT, "meina_agent.py"), run_name="__main__")
