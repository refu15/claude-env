---
name: radio-ai-os プロジェクト概要
description: ラジオ制作会社向けAI業務OS。取材アポイント自動化・AI社員管理・Podcast配信の全構成
type: project
---

## プロジェクト概要
ラジオ制作会社のAI業務OS。Slack経由でAI社員に指示、取材アポイント〜収録〜配信まで全自動化。

## リポジトリ
`/home/nnkre/radio-ai-os/`

## デプロイ
- Fly.io: https://radio-ai-os.fly.dev/
- API: Fastify (ポート8080 on Fly.io, 4000 local)
- フロント: Next.js ダッシュボード

## 主要構成
- `apps/api` — Fastify API
- `apps/web` — Next.js ダッシュボード
- `discord-bot` — Discord Bot (Radio#3647)
- `packages/db` — Drizzle ORM + PostgreSQL

## セキュリティ対応状況（2026-03-25完了）
- JWT署名検証（jose jwtVerify）
- レート制限（@fastify/rate-limit: 100/min, AI: 20/min）
- セキュリティヘッダー（@fastify/helmet + Next.js CSP/HSTS）
- Slack署名検証必須化
- パストラバーサル/SSRF防止
- 起動時環境変数バリデーション
- NEXTAUTH_SECRET/INTERNAL_API_KEY を強固なランダム値に更新済み
- ALLOWED_EMAILS設定済み（3アドレス）

## Slack Bot（2026-03-25拡張）
- コマンド: /shortage, /followup, /interview-status, /generate-questions, /broadcast, /daily-report
- イベント: app_mention（テキスト応答 + 音声ファイル自動処理）
- インタラクティブ: 承認/却下ボタン（slack-interactivity.ts）
- 共通ユーティリティ: utils/slack.ts

## フロントエンド（2026-03-25追加）
- /office/interview — キーワード質問生成 + ソースURL表示
- /office/ai-ops — AI運用管理ダッシュボード
- /office/analytics — 分析ダッシュボード

## 取材質問生成
- Perplexity Sonar API で実ニュース検索（3段階: news → company → external）
- キーワードによるベース質問の加筆修正
- 参照ソースのURL付き表示

## スプレッドシート列構成
No | リストアップ日 | 転載日 | 作成 | TEL済 | M送付 | 再度確認 | 出演可否 | 収録日 | 曜日 | ゲスト氏名 | 肩書き | 所属 | ご担当者名 | メールアドレス | 電話番号 | 訪問先 | 備考1 | 備考2

## マスタシートデータ（2026-03-25同期）
- マスタシートID: 1dhXyOTEB0Vw_iNOk66BdUIwRLdv-uZLFD1wgKpWRXxM
- パートナー企業: 12社
- バックナンバー: 640エピソード（2019年〜2025年9月）
- チームメンバー・スケジュール設定・請求書テンプレートも同期済み
- config-sheet.ts で1時間ごとに自動同期 + Slack変更通知

## エージェントへのビジネスデータ注入（2026-03-25実装）
- `buildCommanderPrompt()` にパートナー・チーム・バックナンバー統計・スケジュール設定を動的注入
- `runner.ts` で各エージェント実行時にエージェント種別に応じたビジネスコンテキストを注入
  - 取材系: パートナー情報 + バックナンバー統計（重複避け）
  - 分析系: チーム + バックナンバー統計
  - 全エージェント: パートナー一覧

## 本番移行計画
- VPS推奨: Xserver VPS 2GB (¥1,170/月) or Hetzner CPX11
- Docker Compose + Caddy (自動HTTPS) + Cloudflare (WAF)

**Why:** ラジオ制作会社の取材業務を全自動化し、人間の作業を-60%以上削減する
**How to apply:** 取材関連の指示には必ず4エージェント連携フローを使用。スプレッドシートは実運用列構成を遵守。内部API呼び出しはINTERNAL_API_KEYを使用。
