# search-agent - Learning History

**Role**: Information retrieval from internal and external sources

## Accumulated Learnings

- WebSearch で複数観点を並列検索することで調査時間を大幅短縮できる（1クエリずつではなく3-4クエリを同時発行）
- 技術調査では「公式ドキュメントURL（code.claude.com/docs）」「eesel.ai」「claudelog.com」「claudefa.st」が信頼性の高いソース
- 現在年（2026）を検索クエリに含めることで最新情報にヒットしやすくなる

## Active Patterns

- 調査前に既存の設定ファイル（settings.json等）を確認し、現状把握してから調査結果を文脈に合わせて提示する
- 並列WebSearch（3-4件同時）→ 深掘りWebSearch（2件同時）の2段階で効率よく情報収集
- 報告は「まとめ：優先度別アクションリスト」テーブルで締めると実用性が高い

## Known Pitfalls

- `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` は自動更新も無効化するため、個別変数（TELEMETRY・ERROR_REPORTING・FEEDBACK_SURVEY）の設定を推奨する
- MCP設定の `enableAllProjectMcpServers` を `true` のままにするとセキュリティリスクがある

<!-- Reflection entries will be appended below this line -->
## Reflections

### 2026-03-22: Claude Code 最適化調査
- タスク: Claude Code の最適化・パフォーマンス向上に関する最新情報調査（7観点）
- 手法: 8クエリを2バッチで並列WebSearch実行 + 既存設定ファイル確認
- 成果: settings.json・CLAUDE.md・MCP・パーミッション・メモリ・サブエージェント・コスト最適化の各観点で具体的な設定例付きレポートを作成
- 学び: claudefa.st, eesel.ai, claudelog.com が Claude Code 専門の高品質情報源。code.claude.com が公式。
