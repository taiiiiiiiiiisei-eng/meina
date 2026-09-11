# めいな - Local AI Assistant

Windows向けのローカル音声AIアシスタント「めいな」の開発リポジトリです。

## 現在の構成

- `meina_agent.py` - 音声入力・Whisper・TTS・AI判断・PC操作を統合
- `requirements.txt` - Python依存パッケージ
- `command_router.py` - 安全なPC/Web操作ルーティング（ローカル環境側）
- `meina2/tools.py` - PC/Web操作ツール（ローカル環境側）
- `meina_brain/brain_core.py` - 自作AIの判断コア（ローカル環境側）

## 音声認識

- faster-whisper `large-v3`
- NVIDIA CUDA / float16
- `sounddevice`

## 音声出力

- `pyttsx3`
- Windows日本語音声

## AI

- Ollamaのローカルモデル `meina`
- 自作AI `brain_core` によるアクションフレーム解析

## セットアップ

1. Python 3.14系を用意
2. Ollamaをインストールし、`meina` モデルを作成
3. NVIDIA GPU/CUDA環境を用意
4. 仮想環境を作成
5. `pip install -r requirements.txt`
6. 必要なローカルソース（`command_router.py`、`meina2/`、`meina_brain/`）を配置
7. `python meina_agent.py` を実行

> 現在は開発中です。GitHubには統合エージェント本体と依存関係を先に登録し、補助モジュールを順次整理していきます。
