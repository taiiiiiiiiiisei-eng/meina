"""めいな起動用ランチャー。
実際に起動しているPython環境からCUDA DLLを自動検出してから本体を起動する。
"""

import os
import runpy
import site
import sys


def add_cuda_dll_dirs():
    candidates = []

    try:
        candidates.extend(site.getsitepackages())
    except Exception:
        pass

    try:
        candidates.append(site.getusersitepackages())
    except Exception:
        pass

    # 実行中のPython環境を最優先
    prefix = sys.prefix
    candidates.extend([
        os.path.join(prefix, "Lib", "site-packages"),
        os.path.join(os.path.dirname(sys.executable), "Lib", "site-packages"),
    ])

    seen = set()
    for site_packages in candidates:
        if not site_packages or site_packages in seen:
            continue
        seen.add(site_packages)

        for package in ("cublas", "cudnn"):
            dll_dir = os.path.join(
                site_packages, "nvidia", package, "bin"
            )
            if not os.path.isdir(dll_dir):
                continue

            try:
                os.add_dll_directory(dll_dir)
            except Exception:
                pass

            os.environ["PATH"] = (
                dll_dir + os.pathsep + os.environ.get("PATH", "")
            )


if __name__ == "__main__":
    add_cuda_dll_dirs()
    runpy.run_path(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "meina_agent.py"),
        run_name="__main__",
    )
