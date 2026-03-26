#!/bin/bash
# Stop hook: .claude設定変更を自動でgitにコミット

CLAUDE_DIR="/home/nnkre/.claude"
cd "$CLAUDE_DIR" || exit 0

# 変更があるか確認
if git diff --quiet && git diff --staged --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
  exit 0
fi

# 変更ファイルをステージング（機密ファイルは.gitignoreで除外済み）
git add -A 2>/dev/null

# ステージングされたファイルがあればコミット
if ! git diff --staged --quiet; then
  TIMESTAMP=$(date '+%Y-%m-%d %H:%M')
  git commit -m "auto: 設定・ナレッジ更新 ${TIMESTAMP}" 2>/dev/null
  env -u GITHUB_TOKEN git push origin main 2>/dev/null &
fi

exit 0
