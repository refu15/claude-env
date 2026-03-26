#!/usr/bin/env python3
"""
補助金申請 書類ウォッチドッグ

機能:
1. Google Drive 共有ドライブの案件フォルダをスキャン
2. 必要書類の有無を判定（ファイル名パターンマッチング）
3. 締切までの残日数に応じてアラートレベルを変更
4. Discord のアラートチャンネルに通知

アラート頻度:
- 締切30日以上前: 週1回（月曜日）
- 締切14〜30日前: 週2回（月・木）
- 締切7〜14日前: 毎日
- 締切7日以内: 1日2回（朝・夕）
- 締切当日: 3時間おき

使い方:
  python3 ~/.claude/scripts/doc-watchdog.py              # チェック実行
  python3 ~/.claude/scripts/doc-watchdog.py --force       # 頻度制限を無視して実行
  python3 ~/.claude/scripts/doc-watchdog.py --dry-run     # 通知せずに確認
  python3 ~/.claude/scripts/doc-watchdog.py --report      # 全案件のレポート出力
"""

import json
import os
import subprocess
import sys
import re
from datetime import datetime, timedelta
from pathlib import Path

# --- 設定 ---
SHARED_DRIVE_ID = "0ACte6hwcp5t_Uk9PVA"
ALERT_CHANNEL_ID = "1486250376926593076"  # アラートチャンネル
SPREADSHEET_ID = "1bTS_uJEC1K8XOQ5yc6wWsF915Z2mgyYmhI4lASHr6kk"

HOME = Path.home()
MAP_JSON = HOME / ".claude/channels/discord/channel-client-map.json"
STATE_FILE = HOME / ".claude/channels/discord/doc-watchdog-state.json"
LOG_DIR = HOME / ".claude/logs"

FORCE = "--force" in sys.argv
DRY_RUN = "--dry-run" in sys.argv
REPORT = "--report" in sys.argv

# --- 補助金別の必要書類定義 ---

JIZOKUKA_DOCS = {
    "様式2": {
        "patterns": [r"様式\s*2", r"経営計画書", r"事業計画書①"],
        "label": "様式2（経営計画書）",
        "priority": "必須",
        "description": "経営計画書兼補助事業計画書①"
    },
    "様式3": {
        "patterns": [r"様式\s*3", r"経費明細", r"事業計画書②"],
        "label": "様式3（経費明細表）",
        "priority": "必須",
        "description": "補助事業計画書②【経費明細表・資金調達方法】"
    },
    "様式5": {
        "patterns": [r"様式\s*5", r"交付申請"],
        "label": "様式5（交付申請書）",
        "priority": "必須",
        "description": "補助金交付申請書"
    },
    "決算書": {
        "patterns": [r"決算書", r"損益計算書", r"貸借対照表", r"BS", r"PL"],
        "label": "決算書",
        "priority": "必須",
        "description": "法人: 直近1期の決算書一式"
    },
    "確定申告書": {
        "patterns": [r"確定申告", r"申告書"],
        "label": "確定申告書",
        "priority": "必須（個人）",
        "description": "個人事業主: 直近1年の確定申告書"
    },
    "見積書": {
        "patterns": [r"見積", r"見積書", r"estimate", r"quotation"],
        "label": "見積書",
        "priority": "必須",
        "description": "補助対象経費の見積書"
    },
    "株主名簿": {
        "patterns": [r"株主名簿", r"株主"],
        "label": "株主名簿",
        "priority": "法人必須",
        "description": "株主名簿の写し"
    },
    "登記簿": {
        "patterns": [r"登記", r"履歴事項", r"謄本"],
        "label": "登記簿謄本",
        "priority": "法人必須",
        "description": "履歴事項全部証明書"
    },
    "インボイス": {
        "patterns": [r"インボイス", r"登録通知", r"様式\s*9"],
        "label": "インボイス登録通知書",
        "priority": "特例時必須",
        "description": "適格請求書発行事業者の登録通知書"
    },
}

# 汎用（全補助金共通で確認したいもの）
COMMON_DOCS = {
    "ヒアリングシート": {
        "patterns": [r"ヒアリング", r"聞き取り", r"hearing"],
        "label": "ヒアリングシート",
        "priority": "推奨",
        "description": "事業者情報ヒアリングシート"
    },
}

# 全書類定義を統合
ALL_DOCS = {**JIZOKUKA_DOCS, **COMMON_DOCS}


def log(msg):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{ts} {msg}"
    print(line)
    with open(LOG_DIR / "doc-watchdog.log", "a") as f:
        f.write(line + "\n")


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


def get_folder_files(folder_id):
    """フォルダ内の全ファイルを再帰的に取得"""
    all_files = []

    def _fetch(fid):
        result = gws_run("drive", "files", "list", {
            "q": f'"{fid}" in parents and trashed = false',
            "corpora": "drive",
            "driveId": SHARED_DRIVE_ID,
            "includeItemsFromAllDrives": True,
            "supportsAllDrives": True,
            "fields": "files(id,name,mimeType,modifiedTime,parents)",
            "pageSize": 100
        })
        if not result or "files" not in result:
            return

        for f in result["files"]:
            if f["mimeType"] == "application/vnd.google-apps.folder":
                _fetch(f["id"])  # サブフォルダも探索
            else:
                all_files.append(f)

    _fetch(folder_id)
    return all_files


def check_documents(files, doc_definitions):
    """ファイル一覧と書類定義を突合して、ある/なしを判定"""
    results = {}

    for doc_key, doc_def in doc_definitions.items():
        found = False
        matched_file = None

        for f in files:
            fname = f["name"]
            for pattern in doc_def["patterns"]:
                if re.search(pattern, fname, re.IGNORECASE):
                    found = True
                    matched_file = f
                    break
            if found:
                break

        results[doc_key] = {
            "label": doc_def["label"],
            "priority": doc_def["priority"],
            "found": found,
            "fileName": matched_file["name"] if matched_file else None,
            "modifiedTime": matched_file.get("modifiedTime") if matched_file else None,
        }

    return results


def get_deadline_info():
    """現在アクティブな補助金の締切情報を取得"""
    # 持続化補助金 第19回の締切
    deadlines = {
        "持続化補助金_第19回": {
            "name": "小規模事業者持続化補助金（第19回）",
            "deadline": datetime(2026, 4, 30, 17, 0),
            "yoshiki4_deadline": datetime(2026, 4, 16),
            "docs": JIZOKUKA_DOCS,
        }
    }
    return deadlines


def calc_alert_level(days_remaining):
    """残日数からアラートレベルと絵文字を決定"""
    if days_remaining <= 0:
        return "EXPIRED", "⛔"
    elif days_remaining <= 3:
        return "CRITICAL", "🚨"
    elif days_remaining <= 7:
        return "URGENT", "🔴"
    elif days_remaining <= 14:
        return "WARNING", "🟠"
    elif days_remaining <= 30:
        return "NOTICE", "🟡"
    else:
        return "INFO", "🟢"


def should_run(state, days_remaining):
    """アラート頻度制御: 締切までの日数に応じて実行するか判定"""
    if FORCE or REPORT:
        return True

    last_run = state.get("lastRun")
    if not last_run:
        return True

    last_dt = datetime.fromisoformat(last_run)
    elapsed_hours = (datetime.now() - last_dt).total_seconds() / 3600

    if days_remaining <= 0:
        return elapsed_hours >= 3     # 3時間おき
    elif days_remaining <= 7:
        return elapsed_hours >= 12    # 1日2回
    elif days_remaining <= 14:
        return elapsed_hours >= 24    # 毎日
    elif days_remaining <= 30:
        return elapsed_hours >= 84    # 週2回（3.5日）
    else:
        return elapsed_hours >= 168   # 週1回


def build_alert_message(client_name, channel_id, doc_results, deadline_info):
    """アラートメッセージを生成"""
    now = datetime.now()
    days_left = (deadline_info["deadline"] - now).days
    level, emoji = calc_alert_level(days_left)

    # 様式4の締切チェック
    y4_days = (deadline_info["yoshiki4_deadline"] - now).days if "yoshiki4_deadline" in deadline_info else None

    lines = [
        f"## {emoji} 書類チェック: {client_name}",
        f"**補助金:** {deadline_info['name']}",
        f"**申請締切:** {deadline_info['deadline'].strftime('%Y/%m/%d %H:%M')}（残り **{days_left}日**）",
    ]

    if y4_days is not None and y4_days > 0:
        y4_level, y4_emoji = calc_alert_level(y4_days)
        lines.append(f"**様式4締切:** {deadline_info['yoshiki4_deadline'].strftime('%Y/%m/%d')}（残り **{y4_days}日**）{y4_emoji}")

    # 書類状況
    missing = []
    found = []
    for key, result in doc_results.items():
        if result["found"]:
            found.append(result)
        elif result["priority"] in ("必須", "法人必須"):
            missing.append(result)

    if missing:
        lines.append(f"\n### ❌ 未提出書類（{len(missing)}件）")
        for doc in missing:
            lines.append(f"- **{doc['label']}** [{doc['priority']}]")

    if found:
        lines.append(f"\n### ✅ 確認済み書類（{len(found)}件）")
        for doc in found:
            mod = ""
            if doc.get("modifiedTime"):
                mod_dt = doc["modifiedTime"][:10]
                mod = f" (更新: {mod_dt})"
            lines.append(f"- {doc['label']}: `{doc['fileName']}`{mod}")

    # 残り日数に応じたアクションガイド
    if days_left <= 3:
        lines.append("\n### ⚡ 今すぐやるべきこと")
        lines.append("- 全書類の最終確認・整合性チェック")
        lines.append("- jGrantsでの電子申請テスト")
        lines.append("- 不足書類があれば**至急**対応")
    elif days_left <= 7:
        lines.append("\n### 📌 今週中にやるべきこと")
        lines.append("- 未提出書類の催促・取得")
        lines.append("- 申請書と添付書類の数値突合")
        lines.append("- 商工会議所への最終確認")
    elif days_left <= 14:
        lines.append("\n### 📋 次のアクション")
        lines.append("- 見積書の取得催促")
        lines.append("- 決算書・納税証明書の準備")

    if channel_id:
        lines.append(f"\n<#{channel_id}>")

    return "\n".join(lines)


def build_summary_report(all_results):
    """全案件の一覧レポートを生成"""
    now = datetime.now()

    lines = [
        f"## 📊 書類準備状況サマリー",
        f"**チェック日時:** {now.strftime('%Y/%m/%d %H:%M')}",
        ""
    ]

    deadlines = get_deadline_info()

    for dl_key, dl_info in deadlines.items():
        days_left = (dl_info["deadline"] - now).days
        level, emoji = calc_alert_level(days_left)
        lines.append(f"### {emoji} {dl_info['name']}（残り{days_left}日）")
        lines.append("")
        lines.append("| クライアント | 必須書類 | 不足 | ステータス |")
        lines.append("|------------|---------|------|----------|")

        for client_name, data in all_results.items():
            doc_results = data.get("docs", {})
            total_required = sum(1 for d in doc_results.values() if d["priority"] in ("必須", "法人必須"))
            found_required = sum(1 for d in doc_results.values() if d["priority"] in ("必須", "法人必須") and d["found"])
            missing = total_required - found_required

            if missing == 0:
                status = "✅ 完了"
            elif missing <= 2:
                status = f"🟠 あと{missing}件"
            else:
                status = f"🔴 {missing}件不足"

            lines.append(f"| {client_name} | {found_required}/{total_required} | {missing} | {status} |")

    return "\n".join(lines)


def main():
    log("=== Doc Watchdog start ===")

    # 状態読み込み
    state = load_json(STATE_FILE, {"lastRun": None, "clients": {}})

    # 締切情報
    deadlines = get_deadline_info()
    now = datetime.now()

    # 最も近い締切の残日数
    nearest_days = min(
        (dl["deadline"] - now).days for dl in deadlines.values()
    )

    # 頻度チェック
    if not should_run(state, nearest_days):
        log(f"Skipping (next deadline in {nearest_days} days, frequency control)")
        return

    # クライアントマッピング読み込み
    mapping = load_json(MAP_JSON, {"channels": {}})

    if not mapping.get("channels"):
        log("No client channels mapped. Run discord-channel-onboard.py first.")
        return

    all_results = {}
    alerts_to_send = []

    for ch_id, client_info in mapping["channels"].items():
        folder_id = client_info.get("driveFolderId")
        client_name = client_info.get("clientName", "不明")

        if not folder_id:
            log(f"  {client_name}: No Drive folder linked, skipping file check")
            # Driveフォルダなしでもアラートは出す
            all_results[client_name] = {"docs": {}, "channelId": ch_id}
            continue

        log(f"  Scanning: {client_name} (folder: {folder_id})")

        # ファイル一覧取得
        files = get_folder_files(folder_id)
        log(f"    Found {len(files)} files")

        # 各締切に対して書類チェック
        for dl_key, dl_info in deadlines.items():
            days_left = (dl_info["deadline"] - now).days
            doc_results = check_documents(files, dl_info["docs"])

            # 結果を保存
            all_results[client_name] = {
                "docs": doc_results,
                "channelId": ch_id,
                "folderId": folder_id,
                "deadline": dl_key,
            }

            # 不足書類がある場合のみアラート
            missing_count = sum(
                1 for d in doc_results.values()
                if not d["found"] and d["priority"] in ("必須", "法人必須")
            )

            if missing_count > 0 or days_left <= 7:
                message = build_alert_message(client_name, ch_id, doc_results, dl_info)
                alerts_to_send.append({
                    "channelId": ch_id,
                    "message": message,
                    "daysLeft": days_left,
                    "missingCount": missing_count,
                })

    # レポートモード
    if REPORT:
        report = build_summary_report(all_results)
        print("\n" + report)
        # ファイルにも保存
        report_file = HOME / ".claude/channels/discord/pending-messages/doc-report.md"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        with open(report_file, "w") as f:
            f.write(report)
        log(f"Report saved to {report_file}")

        if not DRY_RUN:
            state["lastRun"] = now.isoformat()
            state["lastReport"] = now.isoformat()
            save_json(STATE_FILE, state)
        return

    # アラート送信
    if alerts_to_send:
        log(f"Sending {len(alerts_to_send)} alerts")

        for alert in alerts_to_send:
            if DRY_RUN:
                print(f"\n--- Alert for channel {alert['channelId']} ---")
                print(alert["message"])
                continue

            # 個別チャンネルにアラート
            msg_file = HOME / f".claude/channels/discord/pending-messages/alert_{alert['channelId']}.md"
            msg_file.parent.mkdir(parents=True, exist_ok=True)
            with open(msg_file, "w") as f:
                f.write(alert["message"])

            # アラートチャンネルにもサマリーを送信
            summary_file = HOME / f".claude/channels/discord/pending-messages/alert_summary.md"
            with open(summary_file, "w") as f:
                f.write(build_summary_report(all_results))

        log("Alert messages saved to pending-messages/")
    else:
        log("No alerts needed")

    # 状態保存
    if not DRY_RUN:
        state["lastRun"] = now.isoformat()
        state["clients"] = {
            name: {
                "lastCheck": now.isoformat(),
                "missingDocs": sum(1 for d in data["docs"].values() if not d["found"] and d["priority"] in ("必須", "法人必須")),
                "totalDocs": len(data["docs"]),
            }
            for name, data in all_results.items()
        }
        save_json(STATE_FILE, state)

    log("=== Doc Watchdog complete ===")


if __name__ == "__main__":
    main()
