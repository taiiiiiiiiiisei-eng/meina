# めいな

ローカルで動作する JARVIS 型 AI アシスタント。

## AI開発ルール

このリポジトリはGPT/Codexによる継続的な開発を前提にしています。

- `AGENTS.md` — AI開発エージェント向けの設計・変更・テスト・Gitルール
- `ci_self_test.py` — 外部依存なしで実行できる静的セルフテスト
- `.github/workflows/static-self-test.yml` — push / pull request時の自動静的テスト

エージェントは、既存コードを確認 → 必要な変更だけ実装 → テスト → 結果を確認、の順で進めます。

## 構成

- `meina_agent.py` — 音声入力・Whisper・TTS・AI判断・PC操作の統合本体
- `run_meina.py` — 実行中のPython環境からCUDA DLLを自動検出して起動
- `meina_brain/brain_core.py` — 自作AIブレイン
- `meina2/tools.py` — PC操作・Web操作
- `command_router.py` — 安全なコマンド振り分け
- `self_test.py` — Whisper/Ollamaを起動せず構成を確認するセルフテスト
- `twitch_clip_pipeline.py` — Twitch VOD取得・音声抽出・Whisper文字起こし・FFmpeg切り抜き
- `twitch_ai_clipper.py` — Whisper候補をOllamaで評価して自動切り抜き
- `twitch_video_editor.py` — 字幕・映像効果・動画編集
- `twitch_publish_metadata.py` — 切り抜き投稿用のAIタイトル・説明・キャプション・ハッシュタグ生成
- `twitch_publish_queue.py` — 投稿前の動画・文章・ハッシュタグをローカルキューへまとめる
- `twitch_live_monitor.py` — 配信中/終了を監視し、終了後にV2自動切り抜きを起動
- `twitch_live_highlight.py` — 配信中の短い音声チャンクをWhisper + Ollamaで評価し、見どころ候補を保存
- `meina_twitch.py` / `meina_twitch_voice.py` — めいなからTwitch切り抜きを呼び出す処理
- `twitch_auto_clip.py` — 配信監視を標準にした自動切り抜き入口（従来VOD監視も互換維持）

## 必要環境

- Windows 10 / 11
- Python 3.12+
- NVIDIA GPU + CUDA対応環境
- Ollama
- 日本語Windows音声（TTS用）
- FFmpeg / ffprobe
- Twitch Developer Application

## セットアップ

```powershell
git clone https://github.com/taiiiiiiiiiisei-eng/meina.git
cd meina
python -m venv .venv_new
.\.venv_new\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python self_test.py
python ci_self_test.py
python meina_health.py
python meina_doctor.py
python meina_smoke_test.py
```

Ollamaでモデル `meina` を用意してから起動：

```powershell
python run_meina.py
```

または `start_meina.bat` を実行。起動前に `meina_health.py` でPython・必須ファイル・必須パッケージ・Ollama/`meina`モデル・NVIDIA/CUDA環境を確認してから本体を起動します。FFmpeg/ffprobeはTwitch機能用の任意項目です。

GUIアプリとして使う場合は `start_meina_app.bat` を実行してください。こちらも起動前に同じヘルスチェックを行います。より詳しい実機診断は `start_meina_doctor.bat` または `python meina_doctor.py`、主要ロジックの一括確認は `start_meina_smoke_test.bat`、軽量セルフテストをまとめて実行する場合は `start_meina_full_self_test.bat` を実行してください。

## 音声操作

「メイナ」と呼びかけると待機し、その後の音声をWhisperで認識して処理します。

現在対応している主な操作：

- メモ帳 / 電卓 / エクスプローラーを開く
- Discord / Steam / Chrome / Edge / OBS / VALORANTなどのアプリ起動
- Google検索
- YouTube検索
- Webサイトを開く
- 日本語音声で返答
- 今日/明日の天気・気温・降水確率
- 現在時刻・日付・曜日
- PC状態（GPU・メモリ・ディスク）の確認
- リマインダー・予定の追加・確認・完了・削除（「18時に起こして」「30分後に知らせて」など自然な言い方にも対応）
- 所要時間つき予定（「18時から1時間勉強の予定を追加して」）、所要時間の変更・解除（「宿題の予定の所要時間を2時間にして」）、予定の重なり確認（「予定かぶってる？」）
- 必要時間つき空き枠確認（「今日18時から22時で1時間空いてる時間」）、空き時間の合計分析（「今日18時から22時の空き時間合計」）、最初の空き枠への予定追加、既存予定の今回分だけを空き枠へ移動
- 予定時間の合計確認（「今日の予定時間合計」「今週の予定時間合計」「今月何時間予定入ってる？」）に加え、カテゴリ/場所で絞った時間集計（「学校カテゴリの今週の予定時間合計」「自習室で今月の予定時間合計」）にも対応。今週/今月は定期予定を未来投影し、所要時間未設定件数もあわせて表示。「今日/明日/今週/今月の所要時間未設定の予定」で期間指定一覧も確認可能。今日残りの空き時間（「今日あとどれくらい空いてる？」）にも対応
- 日ごとの予定負荷（「今日どれくらい予定詰まってる？」）と、定期予定も含めた今週これからのピーク日確認（「今週いちばん予定が多い日は？」）
- 固定ルールによる次アクション候補（「次に何やればいい？」）、今日の優先予定、まとまった集中時間の最初の空き枠確認（「今日1時間集中できる時間ある？」）
- 予定追加時の重なり警告、重要予定の設定・解除（「宿題の予定を重要にして」）と重要予定だけの確認（「重要な予定を教えて」）
- 予定カテゴリの設定・解除（「宿題の予定を学校カテゴリにして」）、カテゴリ別一覧（「学校カテゴリの予定を教えて」）、今日/明日/今週/今月のカテゴリ別件数
- 予定メモの追加・確認・削除（「宿題の予定にメモを追加して『英語のワーク30ページ』」「宿題の予定のメモを教えて」「宿題の予定のメモを消して」）。一覧では本文を出さず「メモあり」と表示し、完了履歴にはその時点のメモを保持
- 予定場所の設定・確認・解除（「歯医者の予定の場所を彦根駅前にして」「18時の塾の予定の場所を教えて」「塾の予定の場所を解除して」）。一覧・完了履歴・削除ゴミ箱からの復元でも場所情報を保持
- 場所ベースの予定確認（「図書館での予定を教えて」「場所が図書館の予定を教えて」）、場所未設定一覧（「場所未設定の予定を教えて」）、今日/明日/今週/今月の場所別件数
- 完了履歴と進捗確認（「今日終わった予定を教えて」「今週終わった予定を教えて」「今月終わった予定を教えて」「学校カテゴリで今月終わった予定を教えて」「自習室で今月終わった予定を教えて」「今日何個終わった？」「今週何個終わった？」「今月何個終わった？」「今日/明日/今週/今月のカテゴリ別進捗」「今日/明日/今週/今月の場所別進捗」）。明日・今週・今月の残り件数には定期予定を未来投影し、今週/今月は期間内の過去日の未完了も含める。各回の完了履歴にはカテゴリ・場所・メモなどを保持
- 誤って完了した単発予定だけを安全に復元（「宿題の予定を未完了に戻して」「宿題の予定の完了を取り消して」）。定期予定の完了履歴は自動では巻き戻さない
- 削除した予定をローカルのゴミ箱へ最大200件保存し、「最近削除した予定を教えて」「宿題の予定の削除を取り消して」「18時の宿題の予定をゴミ箱から戻して」で確認・復元可能
- Twitch配信のAI切り抜き処理
- Twitch切り抜きの投稿準備（タイトル・説明・キャプション・ハッシュタグ・動画ファイルをキュー化）
- 配信中の見どころ監視（短い音声チャンクをAI評価して候補時刻を保存）
- 検出した見どころ候補の一覧表示（「最新の見どころを教えて」など）
- AIによる見どころ再選定（「おすすめの見どころを教えて」など。Ollama失敗時は候補スコア順へフォールバック）
- AIおすすめ候補からVOD切り抜きを生成（「おすすめの切り抜きを作って」など）

## Twitch AI切り抜き

めいなに「配信の切り抜きを作って」などと話しかけると、Twitchの最新アーカイブVODを対象に、次の流れで処理します。

1. Twitch APIで対象チャンネルの最新VODを取得
2. `yt-dlp` でVODを取得
3. FFmpegで音声を抽出
4. `faster-whisper` で日本語字幕・タイムスタンプを作成
5. 候補場面を抽出
6. Ollamaの `meina` が面白さ・驚き・上手さなどを評価
7. FFmpegでMP4切り抜きを作成
8. ローカルAIで投稿用タイトル・説明・キャプション・ハッシュタグを生成
9. `clips/` に保存し、選定理由と投稿用メタデータをJSONへ保存

Twitchの設定は `twitch_config.example.json` を `twitch_config.json` にコピーして、自分のチャンネルログイン名・Developer ApplicationのClient ID・Client Secretを設定してください。

```powershell
copy twitch_config.example.json twitch_config.json
python twitch_clip_runner.py "昨日の配信切り抜いて"
python twitch_publish_queue.py
```

配信中の状態を監視し、配信終了後に新しいVODを自動処理する場合：

```powershell
python twitch_auto_clip.py
```

既存の「新しいVODがあるかを定期確認する方式」に戻したい場合は：

```powershell
$env:MEINA_TWITCH_MONITOR_MODE="vod"
python twitch_auto_clip.py
```

ライブ監視はTwitchのStreams APIで配信中かを確認し、配信終了を検知した後、VODの生成・反映時間を置いて既存のV2切り抜き処理を実行します。

### 注意

- `twitch_config.json` にはClient Secretが入るため、GitHubへコミットしないでください。
- VODの取得・利用はTwitchの利用規約や対象コンテンツの権利・アクセス条件に従ってください。
- 長時間VODのWhisper解析と動画エンコードには時間とストレージを使います。

### AIおすすめ候補から切り抜く

配信中に保存した候補をAIが再選定したあと、配信終了後に最新VODへその時刻を適用して切り抜きを作れます。

```text
メイナ、おすすめの見どころを教えて
メイナ、おすすめの切り抜きを作って
```

「おすすめの切り抜きを作って」はVODから動画を生成し、既存のローカル投稿準備キューも作成します。外部SNSへの自動投稿は行いません。

## 注意

`.venv`、`__pycache__`、学習済みキャッシュ、Twitchの認証情報、VOD、切り抜き動画などの実行データはGitHubに含めず、各PCで構築してください。

### 配信中の見どころ監視

「配信中の見どころを監視して」と話しかけると、別ウィンドウで短い音声チャンクを取得し、Whisperで文字起こししてOllamaの `meina` が候補を評価します。
候補は `twitch_live_highlights/candidates.jsonl` に保存され、外部SNSへ自動投稿はしません。
同じ監視処理を複数起動しないようロックを持ち、「配信中の見どころ監視を停止して」で実行中の監視を安全に停止できます。
配信終了後のVOD切り抜きでは、TwitchのVOD情報に含まれる `stream_id` を使ってライブ候補と対応づけるため、VODファイル名そのものに配信IDが入ることを前提にしません。TwitchのVOD APIは `stream_id` を返します。
CLIで直接起動する場合：

```powershell
python twitch_live_highlight.py
```

既存のVOD自動切り抜きと独立して動作するため、必要なときだけ監視を開始できます。
