from __future__ import annotations

from meina_pc_status import format_pc_status, get_pc_status


def main() -> int:
    status = get_pc_status()
    required = {"disk_free_gb", "disk_total_gb", "ram_total_gb", "ram_free_gb", "gpu"}
    missing = required - set(status)
    if missing:
        print("FAIL missing keys:", sorted(missing))
        return 1
    rendered = format_pc_status(status)
    if not isinstance(rendered, str) or not rendered:
        print("FAIL formatting")
        return 1
    print("PC status self-test: PASS")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
