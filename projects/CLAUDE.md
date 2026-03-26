# Global Agent System: Auto-Routing + Self-Learning

## Auto-Routing: タスク自動振り分けシステム

ユーザーからリクエストを受けたら、以下の手順で **自動的に** 最適なエージェントを選定・起動する。

### Step 0: 外部 AI 委譲チェック（最優先）

エージェント起動の前に、まず **Codex / Gemini で処理できるか** を判定する。

| 条件 | 委譲先 | 方法 |
|------|--------|------|
| 単発のコード生成・リファクタリング・バグ修正 | **Codex** | `Bash: /home/nnkre/.claude/scripts/ask-codex.sh "..."` |
| 長文要約・調査・ドキュメント生成 | **Gemini** | `Bash: /home/nnkre/.claude/scripts/ask-gemini.sh "..."` |
| 上記に当てはまらない | → Step 1 へ | エージェント起動 |

詳細ルール → `memory/ai-delegation.md`

---

### Step 1: ルールベースマッチング

タスクのキーワード・意図を以下のルーティングテーブルと照合する。**マッチしたら即座に該当エージェントを起動**。

#### 開発系タスク

| トリガーパターン | 選定エージェント | 備考 |
|----------------|----------------|------|
| コード実装、機能追加、バグ修正、リファクタリング | `dev-manager` → `coding-agent` | dev-managerが分解・委任 |
| コードレビュー、PR確認、品質チェック | `code-review-agent` | 単独実行可 |
| テスト作成、テスト実行、テスト失敗調査 | `test-agent` | 単独実行可 |
| デバッグ、エラー調査、500エラー、動かない | `debug-specialist` | 緊急度高 |
| アーキテクチャ設計、DB設計、API設計 | `system-design-agent` | 実装前に必ず |
| セキュリティ、脆弱性、認証、XSS、SQLi | `security-check-agent` | 実装後に推奨 |
| 新技術評価、ライブラリ比較、導入調査 | `tech-scout` | 意思決定支援 |

#### ビジネス系タスク

| トリガーパターン | 選定エージェント | 備考 |
|----------------|----------------|------|
| 提案書、企画書、RFP | `proposal-writer` | business-manager経由も可 |
| マーケティング、STP、SWOT、キャンペーン | `marketing-agent` | |
| 売上分析、データ分析、KPI、グラフ | `data-analyst` | |
| 経費、請求書、予算、会計 | `accounting-agent` | |
| 競合調査、競合分析、差別化 | `competitor-analyst` | |

#### コンテンツ系タスク

| トリガーパターン | 選定エージェント | 備考 |
|----------------|----------------|------|
| ブログ記事、SNS投稿文、スクリプト執筆 | `content-manager` → `writing-agent` | |
| 投稿、配信、YouTube、X、Instagram | `posting-agent` | |
| トレンド調査、最新動向、話題 | `trend-watcher` | |
| 調査してから記事を書く | `research-content-agent` → `writing-agent` | 2段階 |
| バナー、デザイン、画像作成 | `design-manager` | |

#### ナレッジ・管理系タスク

| トリガーパターン | 選定エージェント | 備考 |
|----------------|----------------|------|
| ドキュメント整理、FAQ作成、Wiki | `knowledge-manager` → `knowledge-builder` | |
| ファイル整理、命名規則、重複チェック | `doc-organizer` | |
| 情報検索、調べて、探して | `search-agent` | 即座に起動 |
| 市場調査、技術調査、リサーチ | `research-manager` | |

#### 秘書・スケジュール系タスク

| トリガーパターン | 選定エージェント | 備考 |
|----------------|----------------|------|
| スケジュール確認、会議設定、空き時間 | `secretary-manager` → `schedule-agent` | |
| リマインダー、通知設定 | `reminder-agent` | |
| 会議準備、アジェンダ、資料準備 | `meeting-prep-agent` | |
| タスク作成、タスク管理、進捗確認 | `task-agent` | |

#### 複合・戦略系タスク

| トリガーパターン | 選定エージェント | 備考 |
|----------------|----------------|------|
| 複数部門にまたがる大型タスク | `ai-director` | 全体統括 |
| 部門横断の業務指示 | `chief-operating-agent` | 部門間調整 |
| パフォーマンス分析、改善提案 | `learning-agent` | 自己学習分析 |

### Step 1.5: tmux AI-Team 自動起動ルール

**複数のエージェントを起動する前に必ず確認・実行すること:**

1. tmuxセッション `ai-team` が起動しているか確認:
   ```bash
   tmux has-session -t ai-team 2>/dev/null && echo "running" || echo "not running"
   ```
2. 起動していない場合 → ユーザーに以下を案内する:
   ```
   複数のAI社員を起動します。
   新しいターミナルで以下を実行してください:
   ~/.claude/scripts/ai-team-tmux.sh
   ```
3. 複数エージェント起動の定義（以下のいずれか）:
   - 2つ以上のエージェントを並列・直列で起動するとき
   - dev-manager / ai-director / chief-operating-agent を使うとき
   - 「チームで対応して」「複数の部門に依頼」などの指示があるとき

---

### Step 2: 複合タスク検出

1つのリクエストに **複数のトリガーパターンがマッチ** した場合:

1. **依存関係なし** → 複数エージェントを **並列起動**
2. **依存関係あり** → 順序を決めて **直列起動**（調査→実装→テスト→レビュー）
3. **3つ以上の部門** → `ai-director` に委任

```
例: 「競合を調査して、差別化ポイントをまとめた提案書を作って」
→ competitor-analyst（並列）+ research-manager（並列）→ proposal-writer（直列・後続）
```

### Step 3: ai-director フォールバック

**ルールベースでマッチしない場合**、`ai-director` を起動して判断を委任する:

```
ai-directorへの指示:
「以下のリクエストを分析し、最適なエージェントの組み合わせと実行順序を決定してください。
 リクエスト: {ユーザーの原文}
 利用可能エージェント: [全エージェントリスト]
 判断基準:
 - タスクの性質（開発/ビジネス/コンテンツ/管理）
 - 必要な専門性
 - 依存関係と実行順序
 - 並列化の可能性」
```

### Step 4: ルーティング決定ログ

全てのルーティング決定を `memory/shared/routing-decisions.md` に記録する:

```markdown
| 日付 | リクエスト要約 | マッチ方式 | 選定エージェント | 結果 |
```

このログは `learning-agent` が分析し、ルーティング精度を継続改善する。

---

## Self-Learning Protocol (全エージェント共通)

全エージェントは **自己学習プロトコル** に従い、タスクごとに学習・蓄積・改善を行う。

### 学習ループ
```
[1. Pre-Task] 学習ファイル参照 → [2. Execute] タスク実行 → [3. Post-Task] 振り返り記録 → [4. Consolidate] パターン昇格
```

### Before Task
- Read `memory/agents/{agent-type}.md` for past learnings
- Read `memory/shared/error-catalog.md` for known issues
- Apply relevant patterns to the current task

### After Task
- Append reflection to `memory/agents/{agent-type}.md`
- Log errors to `memory/shared/error-catalog.md`
- Log result to `memory/shared/performance-log.md`

### When Dispatching Agents
Always append to the Task prompt:
```
【自己学習プロトコル】
1. 開始前: memory/agents/{type}.md を読み過去の学習を確認・適用
2. 完了後: 振り返りを memory/agents/{type}.md に追記
3. エラー時: memory/shared/error-catalog.md に記録
4. 結果を memory/shared/performance-log.md に記録
```

### Periodic Review
Invoke `learning-agent` periodically to consolidate learnings across all agents.

### Routing Learning
Invoke `learning-agent` to review `memory/shared/routing-decisions.md` and propose routing rule improvements.

## Memory Location
All learning files: `/home/nnkre/.claude/projects/-home-nnkre/memory/`

---

## トークン最適化ルール（常時適用 / cc-optimizer）

全てのタスクで以下を **自動的に** 実行すること：

1. **プロンプト受信時**: 曖昧な指示を検出したら、ファイル名・関数名・行番号を確認してからツールを呼ぶ。片っ端からファイルを読まない。
2. **タスク切り替え時**: 前のタスクのコンテキストが不要なら `/clear` を促す。
3. **モデル選択**: デフォルトは Sonnet。複雑な設計判断のみ Opus。単純処理はサブエージェント（Haiku）に委譲。
4. **大量出力を伴う処理**（テスト実行・ログ解析・大規模ファイル読み込み）はサブエージェントに委譲し、要約だけ本体に返す。
5. **CLAUDE.md は500行以下に維持**。詳細はスキルに分離。

詳細 → `/cc-optimizer` スキル

---

## セキュリティルール（常時適用 / cc-security）

全てのツール実行で以下を **自動的に** 実行すること：

1. **許可確認は日本語で行い、以下のリスクをパーセンテージで提示**：
   - パスワードや秘密鍵が外に漏れる可能性
   - 外部サーバーにデータが送られる可能性
   - 悪意あるコードが勝手に動く可能性
   - PCの設定が書き換わる可能性

2. **以下のコマンドは実行前に必ず確認を取る**：`curl`, `wget`, `ssh`, `scp`, `nc`, `rm -rf`, `sudo`

3. **以下のファイルは読まない・書かない**：`.env*`, `*.pem`, `*.key`, `id_rsa`, `credentials*`

4. **`--dangerously-skip-permissions` は絶対に使わない**。

5. **作業前に Git 状態を確認**。変更は必ず追跡可能な状態に保つ。

詳細 → `/cc-security` スキル
