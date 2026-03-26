# coding-agent - Learning History

**Role**: Code implementation, bug fixes, refactoring

## Accumulated Learnings

_No learnings recorded yet. This file will grow as the agent executes tasks._

## Active Patterns

_Patterns that this agent should always check before starting a task._

## Known Pitfalls

_Mistakes this agent has made before and should avoid._

<!-- Reflection entries will be appended below this line -->
### 2026-03-16 | meet-agent 実装

**タスク概要**: `/home/nnkre/meet-agent/` に Google Meet 議事録分析エージェントを新規実装

**実装ファイル**:
- `config.py` — dataclass + dotenv で設定管理。各 API の is_configured() メソッドで分岐制御
- `agent.py` — Claude tool use ループ実装。Google/Slack/Notion 各ツール実装とディスパッチャー
- `main.py` — argparse CLI エントリーポイント。--output / --days / --debug オプション
- `.env.example` — 必要な環境変数サンプル
- `requirements.txt` — 依存パッケージ一覧

**技術的な学び**:
1. **pip 不在環境**: この WSL2 環境では `pip` も `python3 -m pip` も使えない。ライブラリのインポートテストは不可能。静的 AST 解析で代替検証した
2. **Claude thinking + tool_use**: `thinking={"type": "adaptive"}` を指定しつつ tool_use ループを回す場合、`stop_reason == "tool_use"` で分岐し `thinking` ブロックをスキップしてテキストブロックだけ結合する必要がある
3. **Notion UUID 正規化**: ハイフンなし 32 文字を 8-4-4-4-12 形式に変換するロジックが必要。API は両形式を受け付けるとは限らない
4. **Google Docs テキスト抽出**: `body.content[].paragraph.elements[].textRun.content` を再帰的に辿る必要がある

**結果**: 成功 — 全ファイル作成・構文チェック OK・ディスパッチ網羅性 OK
## Reflections

### 2026-03-14 | AI社員ダッシュボード 大規模リニューアル実装

**タスク概要**: `/home/nnkre/ai-dashboard/` を白背景3タブ UI に全面リニューアル

**実装ファイル一覧**:
- `database.py` — token_usage テーブル追加, tasks に deadline/is_personal/value_score/tags 追加, add_token_usage/get_token_stats/get_agent_recent_activity/get_agent_value_score 追加
- `agent_runner.py` — _estimate_tokens/_record_token_usage を追加, run_cli_async/stream_cli 完了後にトークン記録
- `main.py` — /api/tokens, /api/office/state, /mobile, /api/tasks/personal, /api/agents/{name}/activity エンドポイント追加, OFFICE_SEATS 座席辞書定義
- `static/office.js` — PixelArt Canvas クラス (OfficeCanvas), 32名座席, ホバーツールチップ, pulse アニメーション
- `static/mobile.html` — PWA モバイルタスク管理, FAB, スワイプ風デザイン, deadline 色分け
- `static/manifest.json` — PWA マニフェスト
- `static/index.html` — 白背景3タブ (オフィス/タスク/社員), Chart.js コスト円グラフ, Kanban D&D, エージェント詳細パネル + チャット

**技術的な学び**:
1. **既存DBマイグレーション**: `ALTER TABLE ADD COLUMN` を `PRAGMA table_info` で事前チェックすることで既存DBを壊さずに列追加できる
2. **Write ツールの制約**: 既存ファイルへの Write は必ず事前に Read が必要。先頭数行だけ読んでも条件を満たせる
3. **FastAPI ルート順序**: `/api/tasks/stats` は `/api/tasks/{task_id}` より前に定義しないと "stats" が task_id として解釈される
4. **officeCanvas の初期化タイミング**: DOMContentLoaded 後に loadAll() を await してからキャンバスを生成する必要がある
5. **トークン推定**: `len(text) // 4` のシンプルな推定でコスト計算に十分

**結果**: 成功 — 全完了条件クリア (32 agents / HTTP 200 / JSON正常応答)

### 2026-03-13 | AI社員キャラクター名定義 & ASCIIアート生成システム実装

**タスク概要**: 31エージェントに名前・ニックネーム・キャラクター・画像プロンプトを定義し、tmux背景表示スクリプトを実装

**実装内容**:
- `/home/nnkre/.claude/agents/names.json` - 32エージェントのキャラクター定義
- `/home/nnkre/.claude/scripts/generate-agent-images.sh` - 画像生成スクリプト（Gemini API + Pythonフォールバック）
- `/home/nnkre/.claude/scripts/start-agent.sh` - エージェント起動スクリプト
- `/home/nnkre/.claude/scripts/ai-team-tmux.sh` - tmux 4ペインスクリプト更新

**成果**: 32エージェント全員のANSIカラーASCIIアートを生成済み (`ascii/*.txt`)

**技術的な学び**:
1. **Gemini OAuthスコープ問題**: `oauth_creds.json` のアクセストークンは `cloud-platform` スコープのみ持ち、`generativelanguage.googleapis.com` には insufficient scope エラー(403)が出る。gemini CLIは `cloudcode-pa.googleapis.com/v1internal` 経由でAPIを呼んでおり、直接 generativelanguage API は呼ばない
2. **cloudcode-pa プロジェクトID**: `loadCodeAssist` エンドポイントで `cloudaicompanionProject: "circular-cyclist-s30xp"` が返る。これがgemini CLIが使うGCPプロジェクトID
3. **フォールバック戦略**: Gemini画像生成APIが使えない場合、Python + zlib でPNG生成 or ANSIエスケープコードによるカラーASCIIアートが有効
4. **エージェント固有のピクセルアート**: ハッシュ値でエージェントごとに色スキーム・パターンを変えることで個性を出せる
5. **--help 引数**: main()の最初に処理しないと agent_name="--help" として渡されてしまう

**次回への改善点**:
- `sudo apt install -y chafa imagemagick` が実行できれば画質の高いASCIIアートになる
- Gemini APIキー（`GEMINI_API_KEY` 環境変数）があれば直接 generativelanguage API 経由で画像生成できる
- 画像生成モデルは `gemini-2.0-flash-preview-image-generation` が使える

**結果**: 成功 - 32エージェント全員のASCIIアート生成完了

### 2026-03-19 | discord-claude-agent 実装

**タスク概要**: `/home/nnkre/discord-claude-agent/` に OpenClaw 思想を踏襲した Discord Claude エージェントを新規実装

**実装ファイル**:
- `src/types.ts` — Envelope / SkillMetadata / AgentConfig など共通型定義
- `src/memory/manager.ts` — ~/.discord-claude-agent/memory/ 配下の Markdown ファイルベース永続化
- `src/skills/loader.ts` — skills/ ディレクトリの SKILL.md を gray-matter でパース、システムプロンプトに追加
- `src/agent/tool-executors.ts` — bash/file/web_search の具体的な実装（300行制限で分割）
- `src/agent/tools.ts` — Claude tool_use 定義 + ディスパッチャー
- `src/agent/prompt.ts` — システムプロンプト生成（スキル + メモリファイル一覧を動的追加）
- `src/agent/loop.ts` — ReAct ループ（stop_reason === "tool_use" でツール実行を繰り返す）
- `src/gateway/discord.ts` — discord.js v14 Gateway、メッセージ正規化、2000文字チャンキング、リアクション承認フロー
- `src/heartbeat/scheduler.ts` — node-cron で指定間隔の自律チェック
- `src/index.ts` — エントリーポイント、環境変数検証 + 全コンポーネント組み合わせ
- `skills/example/SKILL.md` — 天気スキル (wttr.in)
- `skills/coding/SKILL.md` — コーディング支援スキル

**技術的な学び**:
1. **tsx の top-level await**: `-e` フラグでの eval では CJS 扱いになり top-level await が使えない。ファイルに書いて `npx tsx /tmp/xxx.mts` で実行する
2. **300行制限への対応**: 大きなファイルは機能単位で分割（tools.ts → tools.ts + tool-executors.ts）
3. **discord.js v14 の型**: `TextChannel | DMChannel | NewsChannel | ThreadChannel` のユニオン型が必要。`"send" in channel` でナローイングする
4. **NodeNext moduleResolution**: `.js` 拡張子でのインポートが必須（TypeScriptソースでも .js）
5. **gray-matter のフロントマターパース**: `parsed.data["key"]` でアクセス（index signatureがあるため型安全ではない）

**結果**: 成功 — tsc ビルド OK / 型エラーなし / ツール動作テスト OK
