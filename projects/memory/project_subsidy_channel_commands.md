---
name: 補助金案件チャンネルコマンド
description: Discord案件チャンネルからのメッセージに対して補助金関連コマンドを自動検出・実行する方法
type: project
---

Discord案件チャンネル（channel-client-map.jsonに登録済み）からメッセージが来た場合、以下のキーワードを検出してハンドラーを実行する。

**ハンドラースクリプト:** `/home/nnkre/.claude/scripts/subsidy-channel-handler.py`

## コマンド対応表

| ユーザーの発言例 | コマンド | 実行方法 |
|---------------|---------|---------|
| 「補助金を調べて」「リサーチして」 | 補助金リサーチ | `python3 subsidy-channel-handler.py search <ch_id> "キーワード"` |
| 「様式2のドラフト作って」「申請書作成」 | ドラフト作成 | `python3 subsidy-channel-handler.py draft <ch_id> "様式2"` |
| 「シートを確認」「案件情報見せて」 | スプレッドシート | `python3 subsidy-channel-handler.py sheet <ch_id> ""` |
| 「過去の事例を検索」「ナレッジ SWOT」 | ナレッジ検索 | `python3 subsidy-channel-handler.py knowledge <ch_id> "SWOT"` |

## 使い方

1. Discordメッセージからキーワードを検出
2. スクリプトを実行して結果を取得
3. Discord reply toolで結果をチャンネルに返信

**Why:** オンボードメッセージで4つの機能を案内しているが、それを実際に動作させる仕組み。
**How to apply:** 案件チャンネル（channel-client-map.jsonに登録済みチャンネル）からのDiscordメッセージに対して、上記キーワードがあれば自動的にハンドラーを呼び出す。キーワードがない通常の会話はそのまま対応する。
