"""音声設定永続化の軽量セルフテスト。Whisper/TTS本体を起動しない。"""
from pathlib import Path


ROOT = Path(__file__).resolve().parent
AGENT = ROOT / "meina_agent.py"


def main() -> int:
    source = AGENT.read_text(encoding="utf-8")

    env_line = 'MEINA_NEURAL_RATE = os.environ.get("MEINA_NEURAL_RATE", "-8%")'
    assert source.count(env_line) == 1

    env_pos = source.index(env_line)
    load_def_pos = source.index("def load_meina_voice_settings")
    load_call_pos = source.index("load_meina_voice_settings()")
    assert env_pos < load_def_pos < load_call_pos

    assert '"rate": MEINA_NEURAL_RATE' in source
    assert "set_meina_rate" in source
    assert '_ENGINE_RATE_PRESETS = {"-18%": 140, "-8%": 158, "+8%": 176}' in source
    assert 'engine.setProperty("rate", _ENGINE_RATE_PRESETS.get(MEINA_NEURAL_RATE, MEINA_TTS_RATE))' in source
    print("Voice settings persistence self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
