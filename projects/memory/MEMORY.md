# Agent Team Self-Learning System

## Overview
All agents in this environment operate with a **self-learning loop**. Every task execution includes reflection, logging, and knowledge accumulation that feeds into future sessions.

## Learning Loop
```
[Pre-Task] Consult learnings -> [Execute] Perform task -> [Post-Task] Reflect & log -> [Consolidate] Update patterns
```

## Agent Learning Files
Each agent maintains its own learning file:
- [coding-agent](./agents/coding-agent.md)
- [code-review-agent](./agents/code-review-agent.md)
- [test-agent](./agents/test-agent.md)
- [dev-manager](./agents/dev-manager.md)
- [debug-specialist](./agents/debug-specialist.md)
- [system-design-agent](./agents/system-design-agent.md)
- [security-check-agent](./agents/security-check-agent.md)
- [business-manager](./agents/business-manager.md)
- [content-manager](./agents/content-manager.md)
- [writing-agent](./agents/writing-agent.md)
- [research-manager](./agents/research-manager.md)
- [search-agent](./agents/search-agent.md)
- [data-analyst](./agents/data-analyst.md)
- [marketing-agent](./agents/marketing-agent.md)
- [design-manager](./agents/design-manager.md)
- [knowledge-manager](./agents/knowledge-manager.md)
- [secretary-manager](./agents/secretary-manager.md)
- [schedule-agent](./agents/schedule-agent.md)
- [reminder-agent](./agents/reminder-agent.md)
- [task-agent](./agents/task-agent.md)
- [posting-agent](./agents/posting-agent.md)
- [trend-watcher](./agents/trend-watcher.md)
- [tech-scout](./agents/tech-scout.md)
- [proposal-writer](./agents/proposal-writer.md)
- [accounting-agent](./agents/accounting-agent.md)
- [competitor-analyst](./agents/competitor-analyst.md)
- [doc-organizer](./agents/doc-organizer.md)
- [research-content-agent](./agents/research-content-agent.md)
- [meeting-prep-agent](./agents/meeting-prep-agent.md)
- [ai-director](./agents/ai-director.md)
- [chief-operating-agent](./agents/chief-operating-agent.md)
- [learning-agent](./agents/learning-agent.md)

## Shared Knowledge
- [Cross-Agent Patterns](./shared/cross-agent-patterns.md) - Patterns observed across multiple agents
- [Error Catalog](./shared/error-catalog.md) - Known errors and proven solutions
- [Performance Log](./shared/performance-log.md) - Task success/failure tracking

## Protocol
See [Learning Protocol](./learning-protocol.md) for the mandatory post-task reflection process.

## Key Rules
1. **Every agent MUST read its learning file before starting a task**
2. **Every agent MUST write a reflection after completing a task**
3. **learning-agent consolidates weekly into cross-agent patterns**
4. **Patterns confirmed 3+ times are promoted to MEMORY.md**

---

## AI 委譲ルール（必ず適用すること）

Claude はオーケストレーター。タスクに応じて Codex / Gemini を自動的に呼び出す。

| タスク種別 | 委譲先 | スクリプト |
|-----------|--------|-----------|
| シンプルなコード生成・リファクタリング・バグ修正・テスト生成 | **Codex** | `/home/nnkre/.claude/scripts/ask-codex.sh "..."` |
| 長文要約・調査・ドキュメント生成・比較まとめ | **Gemini** | `/home/nnkre/.claude/scripts/ask-gemini.sh "..."` |
| 設計・オーケストレーション・複合判断・統合 | **Claude 自身** | — |

詳細ルール → [ai-delegation.md](./ai-delegation.md)

---

## ツール実行時の許可ルール

- ツール実行（Bash、ファイル操作など）の許可を求めるときは、必ず日本語で説明・確認を行うこと
- 許可を求める際、以下のセキュリティリスクをパーセンテージ(%)で提示すること
  - パスワードや秘密鍵が外に漏れる可能性
  - 外部サーバーにデータが送られる可能性
  - 悪意あるコードが勝手に動く可能性
  - PCの設定が書き換わる可能性

## Feedback
- [tmux AI-Team 自動起動](./feedback_tmux_ai_team.md) - 複数エージェント起動前にtmux ai-teamセッションを案内する
- [コミュニケーションスタイル](./feedback_communication_style.md) - 率直・論理的・具体的な回答を好む。コード正確性重視
- [組織優先順位](./feedback_org_priority.md) - メインはデジゴリ（TWISTではない）、カレンダー優先はr.sakurai@digital-gorilla.co.jp、タスクは組織別+短期/長期

## User
- [櫻井理也のビジョン](./user_sakurai_vision.md) - 根底にある思い・未来創造室の目標・AI投資ROIの考え方
- [櫻井理也 包括プロフィール](./user_sakurai_profile.md) - 基本情報・全所属・学業・事業・思考スタイル・強み弱み・価値観（Gemini/ChatGPT記憶統合）

## Projects
- [kintai-bot](./project_kintai_bot.md) - Slack勤怠管理ボット（構成・環境・実装・既知の問題）
- [補助金事業](./project_subsidy_business.md) - TWIST社の補助金申請サポート事業（案件管理・ナレッジ蓄積・AI支援体制）
- [案件チャンネルコマンド](./project_subsidy_channel_commands.md) - Discord案件チャンネルの4機能（リサーチ・ドラフト・シート・ナレッジ）
- [radio-ai-os](./project_radio_ai_os.md) - ラジオ制作AI業務OS（取材自動化・AI社員18名・VPS移行予定）
