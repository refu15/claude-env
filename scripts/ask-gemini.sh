#!/bin/bash
# ask-gemini.sh — Claude から Gemini CLI を呼び出すラッパー
# 使い方: ask-gemini.sh "タスクの説明"
# 終了コード: 0=成功, 1=失敗

set -euo pipefail

if [ $# -eq 0 ]; then
  echo "Usage: ask-gemini.sh <prompt>" >&2
  exit 1
fi

PROMPT="$*"

# 作業ディレクトリが指定されていれば移動
if [ -n "${WORK_DIR:-}" ]; then
  cd "$WORK_DIR"
fi

# gemini --prompt で非インタラクティブ実行
gemini --prompt "$PROMPT" 2>&1
