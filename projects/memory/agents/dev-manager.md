# dev-manager - Learning History

**Role**: Task decomposition, delegation, quality control

## Accumulated Learnings

_No learnings recorded yet. This file will grow as the agent executes tasks._

## Active Patterns

_Patterns that this agent should always check before starting a task._

## Known Pitfalls

_Mistakes this agent has made before and should avoid._

## Active Patterns

- **Next.js + Supabase 構成**: `createClient()` はブラウザ環境では `'use client'` コンポーネントのイベントハンドラ内か `useEffect` 内で呼ぶ。モジュールスコープやコンポーネントのトップレベルに置くとビルド時にエラーになる
- **shadcn/ui のインストール**: `npx shadcn@latest init` は対話式になる。代わりに `components.json` を手動作成してから `npx shadcn@latest add` すると非対話で済む。また `class-variance-authority`, `@radix-ui/react-slot` 等の依存が別途 `npm install` 必要
- **Next.js 16 の `cookies()`**: `await cookies()` が必要（非同期）

## Known Pitfalls

- `createClient()` をコンポーネントトップレベルに置くと SSG/SSR ビルド時にエラー → イベントハンドラか useEffect 内に移動
- shadcn/ui の依存パッケージ（`class-variance-authority` 等）は自動インストールされないことがある

<!-- Reflection entries will be appended below this line -->
## Reflections

### 2026-03-14: AI社員ダッシュボード構築

**タスク**: フルスタックWebアプリ `/home/nnkre/ai-dashboard/` の構築

**実施内容**:
- FastAPI + uvicorn バックエンド (main.py, database.py, agent_runner.py, task_executor.py)
- Vanilla JS + Alpine.js + Tailwind CSS フロントエンド (static/index.html)
- SQLite DB、32エージェント自動シード、SSEストリーミング実装

**学習事項**:
- Ubuntu WSL2 では `pip3` コマンドがなく `python3 -m venv` でvenvを作る必要がある
- `python3 -m ensurepip` は Ubuntu/Debian では無効化されている
- venvは `/home/nnkre/ai-dashboard-venv/` に作成し start.sh で自動作成する設計にした
- FastAPIの `/api/tasks/stats` のような静的サブパスは `/api/tasks/{task_id}` より先に定義する必要がある（パスパラメータとの競合を避けるため）

**成果**: 全APIエンドポイント動作確認済み、32エージェント読み込み成功

**残課題**: コードレビュー・セキュリティチェック・テストは今回スキップ（単独実装タスクのため）

### 2026-03-16: AI社員チーム Web App Phase 1 MVP 実装

**タスク**: `/home/nnkre/src/ai-employee/web/` に Next.js 14 + Supabase + shadcn/ui の Webアプリを実装

**実施内容**:
- `create-next-app` でプロジェクト初期化（TypeScript + Tailwind + App Router）
- shadcn/ui は `components.json` を手動作成してから `shadcn add` を実行（対話回避）
- Supabaseマイグレーション `006_web_app_schema.sql` 作成（conversations/messages/agent_logs/memory_entries）
- 全ページ実装: `/`, `/auth`, `/chat`, `/chat/[agentId]`, `/tasks`, `/memory`, `/settings`
- APIルート: `/api/chat`（SSEストリーミング）, `/api/conversations`, `/api/tasks`
- 30種類以上のエージェント定義（6部門）

**学習事項**:
- `createClient()` はビルド時に実行されないようイベントハンドラ/useEffect内に置く
- shadcn/ui の `class-variance-authority` 等は `shadcn add` 後に別途インストールが必要な場合がある
- Next.js 16 の `cookies()` は `await` が必要

**結果**: `npm run build` が全12ルートでエラーなく通過

**残課題**: ANTHROPIC_API_KEY 等の環境変数設定、Supabase プロジェクト作成・マイグレーション実行
