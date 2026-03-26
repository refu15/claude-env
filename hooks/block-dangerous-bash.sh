#!/bin/bash
# PreToolUse hook: 危険なBashコマンドをブロック
# 終了コード2でブロック、0で通過

COMMAND=$(echo "$CLAUDE_TOOL_INPUT" | jq -r '.command // ""' 2>/dev/null)

# 破壊的パターンチェック
DANGEROUS_PATTERNS=(
  "rm -rf /"
  "rm -rf ~"
  "rm -rf \$HOME"
  "rm -rf /home"
  "rm -rf /etc"
  "rm -rf /usr"
  "rm -rf /var"
  "> /dev/sda"
  "dd if=/dev/zero of=/"
  "chmod -R 777 /"
  "mkfs"
  ":(){:|:&};:"
)

for pattern in "${DANGEROUS_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qF "$pattern"; then
    jq -n '{
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason: "危険なコマンドをブロックしました: '"$pattern"'"
      }
    }'
    exit 2
  fi
done

exit 0
