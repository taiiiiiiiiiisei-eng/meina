# めいな

ローカルで動作する JARVIS 型 AI アシスタント。

## 構成

- `meina_agent.py` — 音声入力・Whisper・TTS・AI判断・PC操作の統合本体
- `meina_brain/brain_core.py` — 自作AIブレイン
- `meina2/tools.py` — PC操作・Web操作
- `command_router.py` — 安全なコマンド振り分け

## 必要環境

- Windows 10 / 11
- Python 3.14+
- NVIDIA GPU + CUDA対応環境
- Ollama
- 日本語Windows音声（TTS用）

## セットアップ

```powershell
git clone https://github.com/taiiiiiiiiiisei-eng/meina.git
cd meina
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Ollamaでモデル `meina` を用意してから起動：

```powershell
python meina_agent.py
```

## 音声操作

「メイナ」と呼びかけると待機し、その後の音声をWhisperで認識して処理します。

現在対応している主な操作：

- メモ帳 / 電卓 / エクスプローラーを開く
- Discord / Steam / Chrome / Edge / OBS / VALORANTなどのアプリ起動
- Google検索
- YouTube検索
- Webサイトを開く
- 日本語音声で返答

## 注意

`.venv`、`__pycache__`、学習済みキャッシュなどの実行環境はGitHubに含めず、各PCで構築してください。
