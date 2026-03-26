#!/bin/bash
# ============================================================
# Claude Code 環境エクスポート
# 全ナレッジ・設定・スクリプトを1つのtarballにパッケージング
#
# 使い方:
#   ~/.claude/scripts/migrate-export.sh                  # エクスポート
#   ~/.claude/scripts/migrate-export.sh /path/to/output  # 出力先指定
#
# 出力: claude-env-YYYYMMDD-HHMMSS.tar.gz
# ============================================================
set -euo pipefail

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
OUTPUT_DIR="${1:-$HOME}"
ARCHIVE_NAME="claude-env-${TIMESTAMP}.tar.gz"
ARCHIVE_PATH="${OUTPUT_DIR}/${ARCHIVE_NAME}"
STAGING_DIR=$(mktemp -d)
DEST="${STAGING_DIR}/claude-env"

echo "📦 Claude Code 環境エクスポート開始"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

mkdir -p "$DEST"

# ============================================================
# 1. コア設定ファイル
# ============================================================
echo "  [1/8] 設定ファイル..."
mkdir -p "$DEST/config"
for f in settings.json settings.local.json config.json; do
  [ -f "$HOME/.claude/$f" ] && [ -r "$HOME/.claude/$f" ] && cp "$HOME/.claude/$f" "$DEST/config/" 2>/dev/null || true
done

# ============================================================
# 2. スクリプト（自作）
# ============================================================
echo "  [2/8] スクリプト..."
cp -r "$HOME/.claude/scripts" "$DEST/scripts"

# ============================================================
# 3. チャンネル設定（Discord等）
# ============================================================
echo "  [3/8] チャンネル設定..."
cp -r "$HOME/.claude/channels" "$DEST/channels"

# ============================================================
# 4. スキル（カスタム）
# ============================================================
echo "  [4/8] スキル..."
cp -r "$HOME/.claude/skills" "$DEST/skills"

# ============================================================
# 5. フック
# ============================================================
echo "  [5/8] フック..."
cp -r "$HOME/.claude/hooks" "$DEST/hooks"

# ============================================================
# 6. メモリ・ナレッジベース（CLAUDE.md含む）
# ============================================================
echo "  [6/8] メモリ・ナレッジ..."
mkdir -p "$DEST/projects"
# CLAUDE.md
[ -f "$HOME/.claude/projects/-home-nnkre/CLAUDE.md" ] && \
  cp "$HOME/.claude/projects/-home-nnkre/CLAUDE.md" "$DEST/projects/"
# memory ディレクトリ全体
cp -r "$HOME/.claude/projects/-home-nnkre/memory" "$DEST/projects/memory"

# ============================================================
# 7. エージェント学習ファイル
# ============================================================
echo "  [7/8] エージェント学習..."
mkdir -p "$DEST/agents"
# mdファイルのみ（学習データ）
find "$HOME/.claude/agents" -name "*.md" -exec cp {} "$DEST/agents/" \;

# ============================================================
# 8. プラグイン設定（キャッシュ除外）
# ============================================================
echo "  [8/8] プラグイン設定..."
mkdir -p "$DEST/plugins"
for f in installed_plugins.json blocklist.json known_marketplaces.json; do
  [ -f "$HOME/.claude/plugins/$f" ] && cp "$HOME/.claude/plugins/$f" "$DEST/plugins/"
done
# プラグインデータ（軽量）
[ -d "$HOME/.claude/plugins/data" ] && cp -r "$HOME/.claude/plugins/data" "$DEST/plugins/data"

# ============================================================
# マニフェスト生成
# ============================================================
echo ""
echo "📋 マニフェスト生成..."

cat > "$DEST/MANIFEST.md" << EOF
# Claude Code 環境エクスポート
- **エクスポート日時:** $(date '+%Y/%m/%d %H:%M:%S')
- **ソースマシン:** $(hostname)
- **ユーザー:** $(whoami)

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
\`\`\`bash
# VPS上で実行
tar xzf ${ARCHIVE_NAME}
cd claude-env
bash restore.sh
\`\`\`

## 注意事項
- channels/discord/.env にBotトークンが含まれます（機密情報）
- VPS側でClaude Codeのインストールが必要です
- プラグインはインストール済み設定のみ。キャッシュは初回起動時に再取得されます
EOF

# ============================================================
# リストアスクリプト生成
# ============================================================
cat > "$DEST/restore.sh" << 'RESTORE_EOF'
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
RESTORE_EOF

chmod +x "$DEST/restore.sh"

# ============================================================
# tarball作成
# ============================================================
echo ""
echo "📦 アーカイブ作成中..."
tar czf "$ARCHIVE_PATH" -C "$STAGING_DIR" claude-env

# サイズ表示
SIZE=$(du -sh "$ARCHIVE_PATH" | cut -f1)
FILE_COUNT=$(tar tzf "$ARCHIVE_PATH" | wc -l)

echo ""
echo "✅ エクスポート完了"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ファイル: $ARCHIVE_PATH"
echo "  サイズ:   $SIZE"
echo "  ファイル数: $FILE_COUNT"
echo ""
echo "VPSへの転送:"
echo "  scp $ARCHIVE_PATH user@vps-host:~/"
echo ""
echo "VPS上での復元:"
echo "  tar xzf $ARCHIVE_NAME && cd claude-env && bash restore.sh"

# クリーンアップ
rm -rf "$STAGING_DIR"
