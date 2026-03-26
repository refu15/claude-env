#!/usr/bin/env python3
"""
Discord チャンネル⇔クライアント自動紐付けスクリプト

新しいDiscordチャンネルを検出し、以下を自動実行:
1. access.json にチャンネルを登録
2. チャンネル名からクライアント名を推定
3. Google Drive の共有ドライブからフォルダを検索
4. マッピング情報を channel-client-map.json に保存
5. チャンネルに初期メッセージを投稿（Discordプラグイン経由）

使い方:
  python3 ~/.claude/scripts/discord-channel-onboard.py
  python3 ~/.claude/scripts/discord-channel-onboard.py --dry-run
"""

import json
import os
import subprocess
import sys
import re
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

# --- 設定 ---
GUILD_IDS = ["1485275291050971357", "1427848708677963928"]
SHARED_DRIVE_ID = "0ACte6hwcp5t_Uk9PVA"
SPREADSHEET_ID = "1bTS_uJEC1K8XOQ5yc6wWsF915Z2mgyYmhI4lASHr6kk"

HOME = Path.home()
ACCESS_JSON = HOME / ".claude/channels/discord/access.json"
MAP_JSON = HOME / ".claude/channels/discord/channel-client-map.json"
ENV_FILE = HOME / ".claude/channels/discord/.env"
LOG_DIR = HOME / ".claude/logs"

# 除外チャンネル名（案件チャンネルではない一般チャンネル）
SYSTEM_CHANNELS = {
    "一般", "案件管理", "ナレッジ", "アラート", "general", "random",
    "テスト", "★案件管理-関連事項", "定常業務ルーム",
    "橋本タスクメモ", "岩谷タスクメモ", "櫻井チェック用",
}

DRY_RUN = "--dry-run" in sys.argv


def log(msg):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().isoformat(timespec="seconds")
    line = f"{ts} {msg}"
    print(line)
    with open(LOG_DIR / "channel-onboard.log", "a") as f:
        f.write(line + "\n")


def get_bot_token():
    with open(ENV_FILE) as f:
        for line in f:
            if line.startswith("DISCORD_BOT_TOKEN="):
                return line.strip().split("=", 1)[1]
    raise RuntimeError("Bot token not found")


def load_json(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default or {}


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def discord_api(endpoint, token):
    """Discord REST API を叩く（curl経由で安定性確保）"""
    result = subprocess.run(
        ["curl", "-s", "-H", f"Authorization: Bot {token}",
         f"https://discord.com/api/v10{endpoint}"],
        capture_output=True, text=True, timeout=15
    )
    try:
        return json.loads(result.stdout)
    except (json.JSONDecodeError, Exception) as e:
        log(f"Discord API error: {e}")
        return None


def gws_run(service, resource, method, params):
    """gws CLI を実行"""
    params_json = json.dumps(params)
    cmd = ["gws", service, resource, method, "--params", params_json]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0 and result.stdout.strip():
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            pass
    return None


def get_text_channels(token):
    """全サーバーのテキストチャンネルを取得"""
    all_channels = []
    for guild_id in GUILD_IDS:
        channels = discord_api(f"/guilds/{guild_id}/channels", token)
        if channels:
            all_channels.extend([ch for ch in channels if ch.get("type") == 0])
    return all_channels


def get_drive_folders():
    """共有ドライブの案件フォルダ一覧を取得"""
    result = gws_run("drive", "files", "list", {
        "q": f'mimeType="application/vnd.google-apps.folder" and "{SHARED_DRIVE_ID}" in parents',
        "corpora": "drive",
        "driveId": SHARED_DRIVE_ID,
        "includeItemsFromAllDrives": True,
        "supportsAllDrives": True,
        "fields": "files(id,name,webViewLink)",
        "pageSize": 100
    })
    if result and "files" in result:
        return result["files"]
    return []


def normalize_name(name):
    """マッチング用に名前を正規化"""
    # プレフィックス除去: 99進行中_, 99_, ★, 数字_
    name = re.sub(r"^(99進行中_|99_|★|[0-9]+_)", "", name)
    # 株式会社、合同会社、有限会社を除去
    name = re.sub(r"(株式会社|合同会社|有限会社|一般社団法人)", "", name)
    # 括弧内を除去
    name = re.sub(r"[（(].+?[）)]", "", name)
    # スペース・記号を除去
    name = re.sub(r"[\s　_\-・]", "", name)
    return name.strip().lower()


def find_matching_folder(channel_name, folders):
    """チャンネル名に最もマッチするDriveフォルダを探す"""
    ch_norm = normalize_name(channel_name)
    if not ch_norm:
        return None

    best_match = None
    best_score = 0

    for folder in folders:
        folder_norm = normalize_name(folder["name"])
        if not folder_norm:
            continue

        # 完全一致
        if ch_norm == folder_norm:
            return folder

        # 部分一致（チャンネル名がフォルダ名に含まれる or 逆）
        if ch_norm in folder_norm or folder_norm in ch_norm:
            score = len(ch_norm) / max(len(folder_norm), 1)
            if score > best_score:
                best_score = score
                best_match = folder
                continue

        # あいまい一致
        score = SequenceMatcher(None, ch_norm, folder_norm).ratio()
        if score > 0.6 and score > best_score:
            best_score = score
            best_match = folder

    return best_match if best_score > 0.5 else None


def search_drive_files(folder_id, query_name):
    """フォルダ内の様式ファイルを検索"""
    result = gws_run("drive", "files", "list", {
        "q": f'"{folder_id}" in parents and trashed = false',
        "corpora": "drive",
        "driveId": SHARED_DRIVE_ID,
        "includeItemsFromAllDrives": True,
        "supportsAllDrives": True,
        "fields": "files(id,name,mimeType)",
        "pageSize": 50
    })
    if result and "files" in result:
        return result["files"]
    return []


def build_onboard_message(channel_name, folder, files):
    """チャンネルに投稿する初期メッセージを生成"""
    msg_parts = [
        f"## 案件チャンネル初期化完了",
        f"**クライアント:** {channel_name}",
    ]

    if folder:
        folder_url = f"https://drive.google.com/drive/folders/{folder['id']}"
        msg_parts.append(f"**Driveフォルダ:** [📁 {folder['name']}]({folder_url})")

        if files:
            msg_parts.append("\n**関連ファイル:**")
            # 重要ファイルをピックアップ
            important = []
            for f in files:
                name = f["name"].lower()
                if any(k in name for k in ["様式2", "様式3", "経営計画", "事業計画", "ヒアリング"]):
                    important.append(f)

            for f in important[:5]:
                msg_parts.append(f"- 📄 {f['name']}")

    msg_parts.extend([
        "",
        "**利用可能な機能:**",
        "- 📋 補助金リサーチ（公募中の補助金検索）",
        "- ✍️ 申請書ドラフト作成（様式2・様式3）",
        "- 📊 スプレッドシート更新",
        "- 🔍 ナレッジ検索（過去事例・書き方テンプレート）",
        "",
        "このチャンネルで質問・指示をしてください。"
    ])

    return "\n".join(msg_parts)


def main():
    log("=== Channel onboard start ===")

    token = get_bot_token()
    access = load_json(ACCESS_JSON, {"dmPolicy": "pairing", "allowFrom": [], "groups": {}, "pending": {}})
    mapping = load_json(MAP_JSON, {"channels": {}, "lastSync": None})

    # 1. 全テキストチャンネル取得
    channels = get_text_channels(token)
    if not channels:
        log("ERROR: No channels found")
        return

    log(f"Found {len(channels)} text channels")

    # 2. Driveフォルダ一覧取得
    folders = get_drive_folders()
    log(f"Found {len(folders)} Drive folders")

    # 3. 新規チャンネルを検出
    new_channels = []
    for ch in channels:
        ch_id = ch["id"]
        ch_name = ch["name"]

        # システムチャンネルはスキップ
        if ch_name in SYSTEM_CHANNELS:
            # access.json には登録（機能は使えるように）
            if ch_id not in access.get("groups", {}):
                access.setdefault("groups", {})[ch_id] = {"requireMention": False, "allowFrom": []}
                log(f"Registered system channel: {ch_name} ({ch_id})")
            continue

        # 既にマッピング済みならスキップ
        if ch_id in mapping.get("channels", {}):
            # ただし access.json には登録確認
            if ch_id not in access.get("groups", {}):
                access.setdefault("groups", {})[ch_id] = {"requireMention": False, "allowFrom": []}
            continue

        new_channels.append(ch)

    if not new_channels:
        log("No new channels to onboard")
        mapping["lastSync"] = datetime.now().isoformat()
        save_json(MAP_JSON, mapping)
        save_json(ACCESS_JSON, access)
        return

    log(f"New channels to onboard: {len(new_channels)}")

    # 4. 各新規チャンネルを処理
    for ch in new_channels:
        ch_id = ch["id"]
        ch_name = ch["name"]
        log(f"Onboarding: #{ch_name} ({ch_id})")

        # access.json に登録
        access.setdefault("groups", {})[ch_id] = {"requireMention": False, "allowFrom": []}

        # Driveフォルダとマッチング
        matched_folder = find_matching_folder(ch_name, folders)

        # フォルダ内のファイル検索
        files = []
        if matched_folder:
            log(f"  Matched folder: {matched_folder['name']}")
            files = search_drive_files(matched_folder["id"], ch_name)
            log(f"  Found {len(files)} files")
        else:
            log(f"  No matching folder found")

        # マッピング保存
        mapping.setdefault("channels", {})[ch_id] = {
            "channelName": ch_name,
            "clientName": ch_name,
            "driveFolderId": matched_folder["id"] if matched_folder else None,
            "driveFolderName": matched_folder["name"] if matched_folder else None,
            "fileCount": len(files),
            "onboardedAt": datetime.now().isoformat(),
            "status": "active"
        }

        # チャンネルに初期メッセージを生成（実際の投稿はClaude MCP経由）
        message = build_onboard_message(ch_name, matched_folder, files)

        # メッセージをファイルに保存（Claude MCPで投稿するため）
        msg_dir = HOME / ".claude/channels/discord/pending-messages"
        msg_dir.mkdir(parents=True, exist_ok=True)
        msg_file = msg_dir / f"{ch_id}.md"
        with open(msg_file, "w") as f:
            f.write(message)

        log(f"  Onboard message saved: {msg_file}")

        if DRY_RUN:
            log(f"  [DRY RUN] Would post to #{ch_name}:")
            print(message)
            print("---")

    # 5. 保存
    mapping["lastSync"] = datetime.now().isoformat()

    if not DRY_RUN:
        save_json(ACCESS_JSON, access)
        save_json(MAP_JSON, mapping)
        log(f"Saved: access.json ({len(access['groups'])} channels), map ({len(mapping['channels'])} clients)")
    else:
        log("[DRY RUN] No files modified")

    log("=== Channel onboard complete ===")


if __name__ == "__main__":
    main()
