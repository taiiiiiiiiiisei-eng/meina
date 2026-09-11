from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
EDITED_DIR = ROOT / "clips" / "edited"
BGM_PATH = ROOT / "assets" / "bgm.mp3"

HIGHLIGHT_WORDS = (
    "やば", "うま", "神", "えぐ", "勝った", "負け", "キル", "クラッチ",
    "なんで", "無理", "最高", "すご", "マジ", "プラチナ", "びっくり", "わっしょい",
)


def _find_executable(name: str) -> str:
    found = shutil.which(name)
    if found:
        return found
    if os.name == "nt":
        local = Path(os.environ.get("LOCALAPPDATA", ""))
        if local.exists():
            pattern = "Microsoft\\WinGet\\Packages\\Gyan.FFmpeg_*\\ffmpeg-*\\bin\\" + name + ".exe"
            matches = list(local.glob(pattern))
            if matches:
                return str(matches[0])
    raise FileNotFoundError(f"{name} が見つかりません。FFmpegをインストールしてください。")


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def _ass_time(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int(round((seconds - int(seconds)) * 100))
    if cs >= 100:
        s += 1
        cs = 0
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _ass_escape(text: str) -> str:
    return (
        str(text)
        .replace("\\", "\\\\")
        .replace("{", "\\{")
        .replace("}", "\\}")
        .replace("\n", " ")
        .strip()
    )


def _make_ass(
    segments: list[dict[str, Any]],
    clip_start: float,
    clip_end: float,
    path: Path,
) -> list[float]:
    highlight_times: list[float] = []
    lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: 1920",
        "PlayResY: 1080",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: Default,Yu Gothic,64,&H00FFFFFF,&H00FFFFFF,&H00101010,&H80000000,-1,0,0,0,100,100,0,0,1,4,2,2,80,80,90,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]

    for seg in segments:
        start = max(float(seg.get("start", 0.0)), clip_start)
        end = min(float(seg.get("end", 0.0)), clip_end)
        text = str(seg.get("text", "")).strip()
        if not text or end <= start:
            continue
        rel_start = start - clip_start
        rel_end = end - clip_start
        safe = _ass_escape(text)
        if any(word in text for word in HIGHLIGHT_WORDS):
            safe = "{\\c&H00FFFF&}" + safe
            highlight_times.append(rel_start)
        lines.append(
            f"Dialogue: 0,{_ass_time(rel_start)},{_ass_time(rel_end)},Default,,0,0,0,,{safe}"
        )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")
    return highlight_times


def _make_filter(highlight_times: list[float], vertical: bool) -> str:
    if vertical:
        video = (
            "scale=608:1080:force_original_aspect_ratio=increase,"
            "crop=608:1080,"
            "eq=contrast=1.04:saturation=1.08,"
            "unsharp=5:5:0.35:5:5:0"
        )
    else:
        video = (
            "scale=2035:1145:force_original_aspect_ratio=increase,"
            "crop=1920:1080,"
            "eq=contrast=1.04:saturation=1.08,"
            "unsharp=5:5:0.35:5:5:0"
        )

    for t in highlight_times[:12]:
        a = max(0.0, t)
        b = a + 0.10
        video += f",drawbox=x=0:y=0:w=iw:h=ih:color=white@0.18:t=fill:enable='between(t,{a:.3f},{b:.3f})'"
    return video


def _escape_filter_path(path: Path) -> str:
    # FFmpegのfilter引数用。Windowsのドライブ文字とバックスラッシュを処理する。
    value = str(path).replace("\\", "/")
    value = value.replace(":", r"\:")
    return value


def edit_clip(
    input_path: Path,
    output_path: Path,
    segments: list[dict[str, Any]],
    clip_start: float,
    clip_end: float,
    title: str = "",
    vertical: bool = False,
    bgm_path: Path | None = None,
) -> Path:
    """切り抜きに字幕・軽い演出・任意BGMを追加する。"""
    ffmpeg = _find_executable("ffmpeg")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="meina_edit_") as tmp:
        ass_path = Path(tmp) / "captions.ass"
        highlight_times = _make_ass(segments, clip_start, clip_end, ass_path)
        vf = _make_filter(highlight_times, vertical)
        vf += ",ass=" + _escape_filter_path(ass_path)

        cmd = [
            ffmpeg, "-y",
            "-ss", f"{clip_start:.3f}",
            "-to", f"{clip_end:.3f}",
            "-i", str(input_path),
        ]

        use_bgm = bgm_path is not None and bgm_path.exists()
        if use_bgm:
            cmd += ["-stream_loop", "-1", "-i", str(bgm_path)]

        if use_bgm:
            cmd += [
                "-filter_complex",
                f"[0:v]{vf}[vout];[0:a]loudnorm=I=-16:TP=-1.5:LRA=11[voice];[1:a]volume=0.08[bgm];[voice][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]",
                "-map", "[vout]",
                "-map", "[aout]",
            ]
        else:
            cmd += [
                "-vf", vf,
                "-map", "0:v:0",
                "-map", "0:a?",
            ]

        cmd += [
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "19",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            str(output_path),
        ]
        _run(cmd)

    return output_path


def edit_generated_clip(
    clip_path: Path,
    segments: list[dict[str, Any]],
    clip_start: float,
    clip_end: float,
    vertical: bool = False,
) -> Path:
    EDITED_DIR.mkdir(parents=True, exist_ok=True)
    output = EDITED_DIR / f"{clip_path.stem}_edited.mp4"
    return edit_clip(
        clip_path,
        output,
        segments,
        clip_start,
        clip_end,
        vertical=vertical,
        bgm_path=BGM_PATH if BGM_PATH.exists() else None,
    )
