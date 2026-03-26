# competitor-analyst - Learning History

**Role**: Competitive intelligence, differentiation

## Accumulated Learnings

_No learnings recorded yet. This file will grow as the agent executes tasks._

## Active Patterns

_Patterns that this agent should always check before starting a task._

## Known Pitfalls

_Mistakes this agent has made before and should avoid._

<!-- Reflection entries will be appended below this line -->
## Reflections

### 2026-03-10: SurveyAI 競合調査（アンケートプラットフォーム比較）
**タスク**: 8競合の調査 + 差別化分析 + 追加機能提案
**実行**: WebSearch × 8回 + WebFetch × 2回（formrun公式料金は取得成功、SurveyMonkey公式はJSレンダリングで取得失敗）
**成果物**: `/home/nnkre/survey-platform/app/reports/competitor-report-2026-03-10-survey-platforms.md`
**学習**:
- SurveyMonkey/Typeformの公式料金ページはJSレンダリングのためWebFetchで取得不可。WebSearchのスニペットから価格情報を収集するのが効率的
- 日本向けツールの不満調査は「{ツール名} 評判 デメリット 不満 レビュー {year}」というクエリが有効
- LINE連携 + クーポン + AI生成の三位一体を提供する競合は2026-03時点でゼロ確認（重要な差別化ポイント）
- 競合比較表を先に構造化してから詳細分析を書くと整合性が保ちやすい
