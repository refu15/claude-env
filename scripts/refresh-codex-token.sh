#!/bin/bash
# Codex CLI OAuth アクセストークン自動更新スクリプト
# cron や起動時に呼び出す: ./refresh-codex-token.sh

AUTH_FILE="$HOME/.codex/auth.json"

if [ ! -f "$AUTH_FILE" ]; then
  echo "[refresh-codex-token] auth.json not found at $AUTH_FILE" >&2
  exit 1
fi

REFRESH_TOKEN=$(python3 -c "
import json, sys
d = json.load(open('$AUTH_FILE'))
rt = d.get('tokens', {}).get('refresh_token', '')
if not rt:
    sys.exit(1)
print(rt)
" 2>/dev/null)

if [ -z "$REFRESH_TOKEN" ]; then
  echo "[refresh-codex-token] No refresh_token found" >&2
  exit 1
fi

# Refresh via OpenAI auth endpoint
RESPONSE=$(curl -s -X POST https://auth.openai.com/oauth/token \
  -H "Content-Type: application/json" \
  -d "{
    \"grant_type\": \"refresh_token\",
    \"refresh_token\": \"$REFRESH_TOKEN\",
    \"client_id\": \"app_EMoamEEZ73f0CkXaXp7hrann\"
  }")

NEW_ACCESS_TOKEN=$(echo "$RESPONSE" | python3 -c "
import json, sys
d = json.load(sys.stdin)
if 'access_token' in d:
    print(d['access_token'])
else:
    print('ERROR: ' + str(d.get('error', d)), file=sys.stderr)
    sys.exit(1)
" 2>/dev/null)

if [ -z "$NEW_ACCESS_TOKEN" ]; then
  echo "[refresh-codex-token] Failed to refresh token: $RESPONSE" >&2
  exit 1
fi

# Save back to auth.json
python3 -c "
import json, os
auth_path = '$AUTH_FILE'
d = json.load(open(auth_path))
d['tokens']['access_token'] = '$NEW_ACCESS_TOKEN'
# Check if new refresh token provided
import sys
new_rt = $(echo "$RESPONSE" | python3 -c "import json,sys; d=json.load(sys.stdin); print(repr(d.get('refresh_token', '')))")
if new_rt:
    d['tokens']['refresh_token'] = new_rt
json.dump(d, open(auth_path, 'w'), indent=2)
print('[refresh-codex-token] Token refreshed successfully')
" 2>/dev/null

echo "[refresh-codex-token] Done"
