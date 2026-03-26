---
name: cc-security
description: "Claude Code セキュリティ多層防御のセットアップと監査。.claudeignore / settings.json deny / PreToolUseフック / Git管理を組み合わせてリスクをゼロに近づける。"
compatibility: "Claude Code, bash, git"
---

# CC-Security: Claude Code セキュリティ多層防御

## When to use

以下の場面で使う：

- 新しいプロジェクトに Claude Code を導入するとき
- セキュリティ設定を見直したいとき
- `--dangerously-skip-permissions` を使っていないか確認したいとき
- 機密ファイルが Claude に読まれていないか不安なとき

## 防御の4層構造

```
Layer 1: .claudeignore    → コンテキストに入れない
Layer 2: settings.json    → コマンド実行を deny
Layer 3: PreToolUse フック → 確定的なブロック（Layer2のバグを補完）
Layer 4: Git 管理         → 最後の砦（即座に巻き戻せる）
```

## Procedure

### 1) .claudeignore のセットアップ

プロジェクトルートに `.claudeignore` を作成する。
`.gitignore` と同じ書式。これにより `cat` や `grep` での間接読み取りリスクも消える。

```
.env*
*.pem
*.key
*.p12
*.pfx
credentials/
secrets/
.aws/
.ssh/
```

確認コマンド：
```bash
cat .claudeignore
```

### 2) settings.json の deny リスト

`~/.claude/settings.json` に deny ルールを追加：

```json
{
  "permissions": {
    "deny": [
      "Bash(curl *)",
      "Bash(wget *)",
      "Bash(ssh *)",
      "Bash(nc *)",
      "Bash(ncat *)",
      "Read(**/.env*)",
      "Read(**/*.pem)",
      "Read(**/*.key)",
      "Read(**/credentials*)"
    ]
  }
}
```

⚠️ **注意**: deny ルールには複数のバグが報告されている（GitHub Issues #6699, #8961, #24846, #27040）。
これ単体では不十分。Layer 3 のフックで必ず補完すること。

### 3) PreToolUse フックのセットアップ

`~/.claude/settings.json` にフックを追加（deny の上位互換）：

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "/home/nnkre/.claude/scripts/security-check.sh"
          }
        ]
      }
    ]
  }
}
```

`security-check.sh` の内容：

```bash
#!/bin/bash
# Claude Code のツール実行前にセキュリティチェックを行うフック
# 標準入力から tool_input (JSON) を受け取る

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // ""')

# 危険なコマンドパターンをブロック
BLOCKED_PATTERNS=(
  "curl"
  "wget"
  "ssh "
  "scp "
  "nc "
  "ncat"
  "/etc/passwd"
  "/etc/shadow"
  "\.env"
  "\.pem"
  "\.key"
  "id_rsa"
  "id_ed25519"
)

for pattern in "${BLOCKED_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qiE "$pattern"; then
    echo "{\"action\": \"block\", \"reason\": \"セキュリティポリシー違反: '$pattern' を含むコマンドはブロックされました\"}"
    exit 0
  fi
done

echo "{\"action\": \"allow\"}"
```

```bash
chmod +x /home/nnkre/.claude/scripts/security-check.sh
```

### 4) Git 管理の徹底

Claude Code を使う作業ディレクトリは必ず Git リポジトリにする：

```bash
git init
git add -A
git commit -m "initial commit before claude code session"
```

何か壊された場合の復旧：
```bash
git diff          # 差分確認
git checkout .    # 全変更を元に戻す
git stash         # 一時退避
```

### 5) 絶対にやってはいけないこと

```bash
# ❌ 絶対禁止
claude --dangerously-skip-permissions

# ✅ 正しい使い方
claude
```

`--dangerously-skip-permissions` は全確認をスキップする。CI/CD 専用と考えること。

## 監査チェックリスト

```
[ ] .claudeignore が存在し、.env* / *.pem / *.key を含む
[ ] settings.json に deny リストが設定されている
[ ] PreToolUse フックが機能している
[ ] 作業ディレクトリが git 管理されている
[ ] --dangerously-skip-permissions を使っていない
[ ] CLAUDE.md に機密情報を書いていない
```

## セキュリティリスク評価（実行前に必ず提示）

ツール実行許可を求める際は以下の形式でリスクを提示：

| リスク項目 | 可能性 |
|-----------|--------|
| パスワードや秘密鍵が外に漏れる可能性 | X% |
| 外部サーバーにデータが送られる可能性 | X% |
| 悪意あるコードが勝手に動く可能性 | X% |
| PCの設定が書き換わる可能性 | X% |

## 参考

- [Claude Code Security Best Practices](https://docs.anthropic.com/claude/docs/claude-code-security)
- GitHub Issues: #6699, #8961, #24846, #27040 (deny ルールのバグ報告)
- [cloudnative-co/claude-code-starter-kit](https://github.com/cloudnative-co/claude-code-starter-kit)
