#!/usr/bin/env python3
"""
案件チャンネルコマンドハンドラー

Discordの案件チャンネルで使えるコマンドを処理する。
Claude MCPから呼び出され、結果をpending-messagesに保存する。

コマンド:
  補助金リサーチ [キーワード]     - 公募中の補助金を検索
  ドラフト作成 様式2|様式3        - 申請書のドラフトを生成
  スプレッドシート更新 [内容]     - 案件管理シートを更新
  ナレッジ検索 [キーワード]       - ナレッジベースを検索

使い方:
  python3 subsidy-channel-handler.py <command> <channel_id> [args...]
  python3 subsidy-channel-handler.py search <channel_id> "IT導入"
  python3 subsidy-channel-handler.py draft <channel_id> "様式2"
  python3 subsidy-channel-handler.py knowledge <channel_id> "市場分析"
  python3 subsidy-channel-handler.py sheet <channel_id> "ステータス:申請書類作成中"
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HOME = Path.home()
KNOWLEDGE_DIR = HOME / ".claude/projects/-home-nnkre/memory/subsidy-knowledge"
MAP_JSON = HOME / ".claude/channels/discord/channel-client-map.json"
PENDING_DIR = HOME / ".claude/channels/discord/pending-messages"
SPREADSHEET_ID = "1bTS_uJEC1K8XOQ5yc6wWsF915Z2mgyYmhI4lASHr6kk"
SHARED_DRIVE_ID = "0ACte6hwcp5t_Uk9PVA"


def load_json(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default or {}


def get_client_info(channel_id):
    """チャンネルIDからクライアント情報を取得"""
    mapping = load_json(MAP_JSON, {"channels": {}})
    return mapping.get("channels", {}).get(channel_id)


def gws_run(service, resource, method, params):
    params_json = json.dumps(params)
    cmd = ["gws", service, resource, method, "--params", params_json]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode == 0 and result.stdout.strip():
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            pass
    return None


# ============================================================
# 1. 補助金リサーチ
# ============================================================

def cmd_search(channel_id, query=""):
    """公募中の補助金情報を検索して返す"""
    client = get_client_info(channel_id)
    client_name = client["clientName"] if client else "不明"

    # ナレッジベースの補助金種別ファイルを読み込み
    subsidy_types = []
    types_dir = KNOWLEDGE_DIR / "types"
    if types_dir.exists():
        for f in types_dir.glob("*.md"):
            content = f.read_text()
            subsidy_types.append({"file": f.name, "content": content})

    # クエリがあればフィルタ
    if query:
        filtered = []
        for st in subsidy_types:
            if query.lower() in st["content"].lower():
                filtered.append(st)
        if filtered:
            subsidy_types = filtered

    # 各補助金の概要を抽出
    lines = [
        f"## 📋 補助金リサーチ結果",
        f"**クライアント:** {client_name}",
    ]
    if query:
        lines.append(f"**検索キーワード:** {query}")
    lines.append("")

    for st in subsidy_types:
        content = st["content"]
        # タイトル行を抽出
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        title = title_match.group(1) if title_match else st["file"]

        # 概要セクションを抽出
        overview = ""
        overview_match = re.search(r"##\s*概要\s*\n([\s\S]*?)(?=\n##|\Z)", content)
        if overview_match:
            overview = overview_match.group(1).strip()[:200]

        # 補助上限を抽出
        limit_match = re.search(r"補助上限[：:]\s*(.+)", content)
        limit = limit_match.group(1).strip() if limit_match else ""

        # 補助率を抽出
        rate_match = re.search(r"補助率[：:]\s*(.+)", content)
        rate = rate_match.group(1).strip() if rate_match else ""

        # 公募期間を抽出
        period_match = re.search(r"(公募|締切|次回)[期間切]*[：:]\s*(.+)", content)
        period = period_match.group(2).strip() if period_match else ""

        lines.append(f"### {title}")
        if overview:
            lines.append(overview)
        if limit:
            lines.append(f"- **補助上限:** {limit}")
        if rate:
            lines.append(f"- **補助率:** {rate}")
        if period:
            lines.append(f"- **公募情報:** {period}")
        lines.append("")

    if not subsidy_types:
        lines.append("該当する補助金情報が見つかりませんでした。")
        lines.append("キーワードを変えて再検索するか、具体的な業種・目的をお知らせください。")

    lines.extend([
        "---",
        "💡 詳細を知りたい補助金があれば、補助金名をお伝えください。",
        "適用可能性の診断も行えます。",
    ])

    return "\n".join(lines)


# ============================================================
# 2. 申請書ドラフト作成
# ============================================================

def cmd_draft(channel_id, yoshiki_type="様式2"):
    """様式2 or 様式3のドラフト作成ガイドを返す"""
    client = get_client_info(channel_id)
    client_name = client["clientName"] if client else "不明"
    folder_id = client.get("driveFolderId") if client else None

    # ナレッジベースからパターンを読み込み
    if "2" in yoshiki_type:
        pattern_file = KNOWLEDGE_DIR / "writing/yoshiki2-patterns.md"
        technique_file = KNOWLEDGE_DIR / "writing/writing-techniques.md"
        form_name = "様式2（経営計画書兼補助事業計画書①）"
    elif "3" in yoshiki_type:
        pattern_file = KNOWLEDGE_DIR / "writing/yoshiki3-patterns.md"
        technique_file = None
        form_name = "様式3（経費明細表）"
    else:
        return f"❌ 対応していない様式です: {yoshiki_type}\n`様式2` または `様式3` を指定してください。"

    lines = [
        f"## ✍️ {form_name} ドラフト作成",
        f"**クライアント:** {client_name}",
        "",
    ]

    # ヒアリングシートの有無を確認
    hearing_found = False
    if folder_id:
        files = _get_folder_files(folder_id)
        for f in files:
            if re.search(r"ヒアリング|聞き取り", f["name"], re.IGNORECASE):
                hearing_found = True
                lines.append(f"📄 ヒアリングシート検出: `{f['name']}`")
                break

    if not hearing_found:
        lines.extend([
            "⚠️ **ヒアリングシートが見つかりません**",
            "ドラフト作成にはクライアント情報が必要です。",
            "以下の情報をこのチャンネルに送ってください:",
            "",
            "1. **事業概要**: 何をしている会社か",
            "2. **現状の課題**: 困っていること",
            "3. **やりたいこと**: 補助金で実現したい取組",
            "4. **予算感**: 投資予定額（概算でOK）",
            "5. **従業員数**: 常時使用する従業員の数",
            "",
        ])

    # パターンファイルから章立てを抽出
    if pattern_file.exists():
        content = pattern_file.read_text()

        if "2" in yoshiki_type:
            lines.extend([
                "### 📝 様式2の構成（採択事例ベース）",
                "",
                "| 章 | 内容 | 文字数目安 |",
                "|---|------|----------|",
                "| ①会社概要 | 事業内容・沿革・強み | 300〜500字 |",
                "| ②顧客ニーズと市場の動向 | マクロ→ミクロの市場分析 | 400〜600字 |",
                "| ③自社の強み | SWOT分析・差別化ポイント | 300〜500字 |",
                "| ④経営方針・目標 | 中長期ビジョン・数値目標 | 200〜400字 |",
                "| ⑤補助事業の内容 | 具体的な取組内容 | 500〜800字 |",
                "| ⑥補助事業の効果 | 定量的な効果試算 | 300〜500字 |",
                "",
            ])
        elif "3" in yoshiki_type:
            lines.extend([
                "### 📝 様式3の構成",
                "",
                "| セクション | 内容 |",
                "|-----------|------|",
                "| 経費明細 | 費目別の経費内訳（見積書と一致させる）|",
                "| 資金調達方法 | 自己資金 + 補助金の内訳 |",
                "",
                "**よく使う費目:**",
                "- ①機械装置等費（設備・システム導入）",
                "- ③広報費（HP・チラシ・広告）",
                "- ⑤委託・外注費（専門業者への委託）",
                "- ②工事費（内装・改装工事）",
                "",
            ])

    # 次のアクション
    lines.extend([
        "### ▶️ 次のステップ",
        "",
    ])

    if hearing_found:
        lines.extend([
            "ヒアリングシートの内容を基にドラフトを作成します。",
            "以下のいずれかを指示してください:",
            "- `ドラフト開始` — 全章のドラフトを自動生成",
            "- `第○章だけ` — 特定の章のみ生成",
            "- `見本を見せて` — 採択事例のサンプルを表示",
        ])
    else:
        lines.extend([
            "上記の情報を送っていただければ、ドラフトを作成します。",
            "または `見本を見せて` で採択事例のサンプルを確認できます。",
        ])

    return "\n".join(lines)


def _get_folder_files(folder_id):
    """Driveフォルダ内のファイル一覧を取得（1階層のみ）"""
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


# ============================================================
# 3. スプレッドシート更新
# ============================================================

def cmd_sheet(channel_id, update_text=""):
    """案件管理スプレッドシートの情報を取得・更新"""
    client = get_client_info(channel_id)
    client_name = client["clientName"] if client else "不明"

    if not update_text:
        # 現在のステータスを表示
        return _sheet_status(client_name)
    else:
        # 更新指示を解析して適用
        return _sheet_update(client_name, update_text)


def _sheet_status(client_name):
    """スプレッドシートから公募状況 + クライアントのDrive情報を表示"""
    # 公募状況を取得
    result = _gws_sheets_get(SPREADSHEET_ID, "公募状況!A1:J20")

    lines = [
        f"## 📊 案件情報: {client_name}",
        "",
    ]

    # 公募状況表示
    if result and "values" in result:
        values = result["values"]
        # ヘッダー行を探す
        header_row = None
        data_rows = []
        for row in values:
            if any("補助金名" in str(c) for c in row):
                header_row = row
                continue
            if header_row and any(str(c).strip() for c in row):
                data_rows.append(row)

        if data_rows:
            lines.append("### 現在の公募状況")
            lines.append("")
            for row in data_rows:
                name = row[1] if len(row) > 1 else ""
                status = row[3] if len(row) > 3 else ""
                deadline = row[4] if len(row) > 4 else ""
                days = row[5] if len(row) > 5 else ""
                if name:
                    lines.append(f"- **{name}** — {status} (締切: {deadline}, 残{days}日)")
            lines.append("")

    # クライアントのDriveフォルダ情報
    mapping = load_json(MAP_JSON, {"channels": {}})
    for ch_id, info in mapping.get("channels", {}).items():
        if info.get("clientName") == client_name:
            if info.get("driveFolderName"):
                lines.append(f"**Driveフォルダ:** {info['driveFolderName']}")
            lines.append(f"**ステータス:** {info.get('status', '不明')}")
            lines.append(f"**登録日:** {info.get('onboardedAt', '不明')[:10]}")
            break

    return "\n".join(lines)


def _gws_sheets_get(spreadsheet_id, range_str):
    """Python subprocess経由でgws sheets values getを実行（日本語range対応）"""
    params = json.dumps({
        "spreadsheetId": spreadsheet_id,
        "range": range_str,
    })
    result = subprocess.run(
        ["gws", "sheets", "spreadsheets", "values", "get", "--params", params],
        capture_output=True, text=True, timeout=15
    )
    if result.returncode == 0 and result.stdout.strip():
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            pass
    return None


def _sheet_update(client_name, update_text):
    """更新指示をパースして案内を返す"""
    # key:value 形式をパース
    updates = {}
    for part in update_text.split(","):
        part = part.strip()
        if ":" in part or "：" in part:
            key, val = re.split(r"[:：]", part, 1)
            updates[key.strip()] = val.strip()

    if not updates:
        return (
            f"⚠️ 更新内容を解析できませんでした。\n"
            f"以下の形式で指定してください:\n"
            f"`スプレッドシート更新 ステータス:申請書類作成中, メモ:様式2作成中`"
        )

    lines = [
        f"## 📊 スプレッドシート更新: {client_name}",
        "",
        "**更新内容:**",
    ]
    for key, val in updates.items():
        lines.append(f"- {key} → `{val}`")

    lines.extend([
        "",
        "✅ 更新リクエストを受け付けました。",
        "スプレッドシートに反映します。",
    ])

    # 実際の更新はシート構造に依存するため、ここではリクエストを記録
    # 更新ログを保存
    log_file = HOME / ".claude/channels/discord/sheet-update-queue.jsonl"
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "clientName": client_name,
        "updates": updates,
        "status": "pending",
    }
    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    return "\n".join(lines)


# ============================================================
# 4. ナレッジ検索
# ============================================================

def cmd_knowledge(channel_id, query=""):
    """ナレッジベースを検索"""
    if not query:
        return _knowledge_index()

    results = _search_knowledge(query)

    lines = [
        f"## 🔍 ナレッジ検索結果",
        f"**キーワード:** {query}",
        "",
    ]

    if not results:
        lines.extend([
            "該当するナレッジが見つかりませんでした。",
            "",
            "検索可能なカテゴリ:",
            "- `様式2` `様式3` — 申請書の書き方パターン",
            "- `市場分析` `SWOT` `フェルミ` — ライティングテクニック",
            "- `持続化` `ものづくり` `省力化` — 補助金種別情報",
            "- `ヒアリング` `チェックリスト` — プロセス情報",
        ])
    else:
        for r in results[:5]:
            lines.append(f"### 📄 {r['title']}")
            lines.append(f"*ソース: {r['file']}*")
            lines.append("")
            # マッチした前後のコンテキストを表示
            lines.append(r["excerpt"])
            lines.append("")

    return "\n".join(lines)


def _knowledge_index():
    """ナレッジベースの目次を返す"""
    lines = [
        "## 🔍 ナレッジベース",
        "",
        "### 補助金種別",
        "- `持続化` — 小規模事業者持続化補助金",
        "- `ものづくり` — ものづくり補助金",
        "- `省力化` — 省力化補助金",
        "- `新事業` — 新事業進出補助金",
        "- `再起支援` — 再起支援補助金",
        "",
        "### ライティング",
        "- `様式2` — 経営計画書の書き方パターン",
        "- `様式3` — 経費明細表のパターン",
        "- `テクニック` — 採択される書き方テクニック",
        "- `業種別` — 業種別の書き方サンプル",
        "",
        "### プロセス",
        "- `ヒアリング` — ヒアリング項目・コツ",
        "- `チェックリスト` — 必要書類チェックリスト",
        "",
        "---",
        "キーワードを添えて検索してください。",
        "例: `ナレッジ検索 SWOT分析`",
    ]
    return "\n".join(lines)


def _search_knowledge(query):
    """ナレッジベースのmdファイルをキーワード検索"""
    results = []

    for md_file in KNOWLEDGE_DIR.rglob("*.md"):
        content = md_file.read_text()
        if query.lower() not in content.lower():
            continue

        # タイトルを抽出
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        title = title_match.group(1) if title_match else md_file.stem

        # マッチ箇所の前後を抽出
        idx = content.lower().index(query.lower())
        start = max(0, idx - 100)
        end = min(len(content), idx + len(query) + 300)
        excerpt = content[start:end].strip()

        # 行頭・行末を整理
        if start > 0:
            excerpt = "..." + excerpt
        if end < len(content):
            excerpt = excerpt + "..."

        rel_path = md_file.relative_to(KNOWLEDGE_DIR)
        results.append({
            "title": title,
            "file": str(rel_path),
            "excerpt": excerpt,
        })

    return results


# ============================================================
# メイン: コマンドディスパッチ
# ============================================================

COMMAND_MAP = {
    "search": ("補助金リサーチ", cmd_search),
    "リサーチ": ("補助金リサーチ", cmd_search),
    "補助金": ("補助金リサーチ", cmd_search),
    "draft": ("ドラフト作成", cmd_draft),
    "ドラフト": ("ドラフト作成", cmd_draft),
    "様式": ("ドラフト作成", cmd_draft),
    "sheet": ("スプレッドシート更新", cmd_sheet),
    "シート": ("スプレッドシート更新", cmd_sheet),
    "スプレッドシート": ("スプレッドシート更新", cmd_sheet),
    "knowledge": ("ナレッジ検索", cmd_knowledge),
    "ナレッジ": ("ナレッジ検索", cmd_knowledge),
    "検索": ("ナレッジ検索", cmd_knowledge),
}


def detect_command(message_text):
    """メッセージからコマンドと引数を検出"""
    text = message_text.strip()

    # 明示的なコマンド検出
    for trigger, (name, func) in COMMAND_MAP.items():
        if text.startswith(trigger) or trigger in text:
            # コマンド部分を除去して引数を取得
            args = text.replace(trigger, "").strip()
            # 「作成」「更新」「検索」などの動詞も除去
            args = re.sub(r"^(作成|更新|検索|リサーチ|確認)\s*", "", args).strip()
            return func, args

    return None, None


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]
    channel_id = sys.argv[2]
    args = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""

    if command in COMMAND_MAP:
        _, func = COMMAND_MAP[command]
        result = func(channel_id, args)
    elif command == "detect":
        # メッセージテキストからコマンドを自動検出
        func, detected_args = detect_command(args)
        if func:
            result = func(channel_id, detected_args)
        else:
            result = None
            print("No command detected", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)

    # 結果を出力 & pending-messagesに保存
    print(result)

    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    msg_file = PENDING_DIR / f"response_{channel_id}.md"
    with open(msg_file, "w") as f:
        f.write(result)


if __name__ == "__main__":
    main()
