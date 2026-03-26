# Claude Code 環境エクスポート
- **エクスポート日時:** 2026/03/25 18:41:35
- **ソースマシン:** rink1516
- **ユーザー:** nnkre

## 含まれるファイル
| ディレクトリ | 内容 | 復元先 |
|-------------|------|--------|
| config/ | settings.json等 | ~/.claude/ |
| scripts/ | 自動化スクリプト | ~/.claude/scripts/ |
| channels/ | Discord設定・マッピング | ~/.claude/channels/ |
| skills/ | カスタムスキル | ~/.claude/skills/ |
| hooks/ | フック設定 | ~/.claude/hooks/ |
| projects/CLAUDE.md | プロジェクト指示 | ~/.claude/projects/{project}/CLAUDE.md |
| projects/memory/ | ナレッジ・メモリ | ~/.claude/projects/{project}/memory/ |
| agents/ | エージェント学習ファイル | ~/.claude/agents/ |
| plugins/ | プラグイン設定 | ~/.claude/plugins/ |

## 復元方法
```bash
# VPS上で実行
tar xzf claude-env-20260325-184135.tar.gz
cd claude-env
bash restore.sh
```

## 注意事項
- channels/discord/.env にBotトークンが含まれます（機密情報）
- VPS側でClaude Codeのインストールが必要です
- プラグインはインストール済み設定のみ。キャッシュは初回起動時に再取得されます
