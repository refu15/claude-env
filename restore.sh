#!/bin/bash
# Claude Code 環境リストア
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="$HOME/.claude"

echo "🔄 Claude Code 環境リストア開始"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "復元先: $CLAUDE_DIR"
echo ""

# バックアップ（既存があれば）
if [ -d "$CLAUDE_DIR" ]; then
  BACKUP="$HOME/.claude-backup-$(date +%Y%m%d-%H%M%S)"
  echo "⚠️  既存の ~/.claude を $BACKUP にバックアップ"
  cp -r "$CLAUDE_DIR" "$BACKUP"
fi

mkdir -p "$CLAUDE_DIR"

# 設定ファイル
echo "  [1/8] 設定ファイル..."
cp -n "$SCRIPT_DIR/config/"* "$CLAUDE_DIR/" 2>/dev/null || true

# スクリプト
echo "  [2/8] スクリプト..."
mkdir -p "$CLAUDE_DIR/scripts"
cp -r "$SCRIPT_DIR/scripts/"* "$CLAUDE_DIR/scripts/"
chmod +x "$CLAUDE_DIR/scripts/"*.sh 2>/dev/null || true

# チャンネル
echo "  [3/8] チャンネル設定..."
mkdir -p "$CLAUDE_DIR/channels"
cp -r "$SCRIPT_DIR/channels/"* "$CLAUDE_DIR/channels/"

# スキル
echo "  [4/8] スキル..."
mkdir -p "$CLAUDE_DIR/skills"
cp -r "$SCRIPT_DIR/skills/"* "$CLAUDE_DIR/skills/"

# フック
echo "  [5/8] フック..."
mkdir -p "$CLAUDE_DIR/hooks"
cp -r "$SCRIPT_DIR/hooks/"* "$CLAUDE_DIR/hooks/"

# プロジェクト（CLAUDE.md + memory）
echo "  [6/8] メモリ・ナレッジ..."
# 現在のプロジェクトディレクトリを特定
# ホームディレクトリのパスからプロジェクトキーを生成
PROJECT_KEY=$(echo "$HOME" | sed 's|/|-|g; s|^-||')
PROJECT_DIR="$CLAUDE_DIR/projects/-${PROJECT_KEY}"
mkdir -p "$PROJECT_DIR"
[ -f "$SCRIPT_DIR/projects/CLAUDE.md" ] && cp "$SCRIPT_DIR/projects/CLAUDE.md" "$PROJECT_DIR/"
if [ -d "$SCRIPT_DIR/projects/memory" ]; then
  cp -r "$SCRIPT_DIR/projects/memory" "$PROJECT_DIR/memory"
fi

# エージェント
echo "  [7/8] エージェント学習..."
mkdir -p "$CLAUDE_DIR/agents"
cp "$SCRIPT_DIR/agents/"*.md "$CLAUDE_DIR/agents/" 2>/dev/null || true

# プラグイン
echo "  [8/8] プラグイン設定..."
mkdir -p "$CLAUDE_DIR/plugins"
cp -n "$SCRIPT_DIR/plugins/"*.json "$CLAUDE_DIR/plugins/" 2>/dev/null || true
[ -d "$SCRIPT_DIR/plugins/data" ] && cp -r "$SCRIPT_DIR/plugins/data" "$CLAUDE_DIR/plugins/"

echo ""
echo "✅ リストア完了"
echo ""
echo "次のステップ:"
echo "  1. Claude Code をインストール: npm install -g @anthropic-ai/claude-code"
echo "  2. gws CLI をインストール: https://github.com/nicholaskarlson/gws"
echo "  3. Discord Bot トークンを確認: ~/.claude/channels/discord/.env"
echo "  4. Claude Code を起動: claude"
