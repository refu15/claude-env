#!/bin/bash
# ask-codex.sh — Claude から Codex CLI を呼び出すラッパー
# 使い方: ask-codex.sh "タスクの説明"
# 終了コード: 0=成功, 1=失敗

set -euo pipefail

if [ $# -eq 0 ]; then
  echo "Usage: ask-codex.sh <prompt>" >&2
  exit 1
fi

PROMPT="$*"

# 作業ディレクトリが指定されていれば移動
if [ -n "${WORK_DIR:-}" ]; then
  cd "$WORK_DIR"
fi

# codex exec で非インタラクティブ実行
codex exec "$PROMPT" 2>&1
