#!/bin/bash
# Discord チャンネル自動同期スクリプト
# サーバー内の全テキストチャンネルを access.json に自動登録する
# 新しいチャンネルが追加されたら自動で検出・追加される
#
# 使い方:
#   手動実行: ~/.claude/scripts/discord-sync-channels.sh
#   cron登録: */5 * * * * ~/.claude/scripts/discord-sync-channels.sh

set -euo pipefail

GUILD_IDS="1485275291050971357 1427848708677963928"
ACCESS_JSON="$HOME/.claude/channels/discord/access.json"
ENV_FILE="$HOME/.claude/channels/discord/.env"
LOG_FILE="$HOME/.claude/logs/discord-sync.log"

mkdir -p "$(dirname "$LOG_FILE")"

# トークン読み込み
TOKEN=$(grep DISCORD_BOT_TOKEN "$ENV_FILE" | cut -d= -f2)
if [ -z "$TOKEN" ]; then
  echo "$(date -Iseconds) ERROR: Bot token not found" >> "$LOG_FILE"
  exit 1
fi

# 全サーバーのチャンネルを同期
for GUILD_ID in $GUILD_IDS; do
  CHANNELS=$(curl -s -H "Authorization: Bot $TOKEN" \
    "https://discord.com/api/v10/guilds/$GUILD_ID/channels" 2>/dev/null)

  if [ -z "$CHANNELS" ] || echo "$CHANNELS" | grep -q '"code"'; then
    echo "$(date -Iseconds) ERROR: Failed to fetch channels for guild $GUILD_ID" >> "$LOG_FILE"
    continue
  fi

  TEXT_CHANNEL_IDS=$(echo "$CHANNELS" | python3 -c "
import json, sys
channels = json.load(sys.stdin)
for ch in channels:
    if ch['type'] == 0:
        print(ch['id'])
" 2>/dev/null)

  if [ -z "$TEXT_CHANNEL_IDS" ]; then
    continue
  fi

  python3 -c "
import json

access_path = '$ACCESS_JSON'
channel_ids = '''$TEXT_CHANNEL_IDS'''.strip().split('\n')

try:
    with open(access_path) as f:
        access = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    access = {'dmPolicy': 'pairing', 'allowFrom': [], 'groups': {}, 'pending': {}}

access.setdefault('groups', {})
added = 0
for ch_id in channel_ids:
    ch_id = ch_id.strip()
    if ch_id and ch_id not in access['groups']:
        access['groups'][ch_id] = {'requireMention': False, 'allowFrom': []}
        added += 1

if added:
    with open(access_path, 'w') as f:
        json.dump(access, f, indent=2, ensure_ascii=False)
        f.write('\n')
    print(f'ADDED {added} channels from guild $GUILD_ID')
else:
    print(f'NO_CHANGE for guild $GUILD_ID')
"
done

echo "$(date -Iseconds) Sync completed" >> "$LOG_FILE"
