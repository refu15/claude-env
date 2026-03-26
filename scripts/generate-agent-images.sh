#!/bin/bash
# =============================================================================
# generate-agent-images.sh
# Gemini API でエージェントのイラストを生成し、chafa でASCIIアートに変換する
#
# 前提条件:
#   - 課金有効なGoogle AI Studio アカウント（画像生成は有料プランのみ）
#   - chafa: sudo apt install -y chafa imagemagick
#
# 使い方:
#   ./generate-agent-images.sh              # 未生成のみ
#   ./generate-agent-images.sh --force      # 全員強制再生成
#   ./generate-agent-images.sh coding-agent # 1人だけ生成
# =============================================================================

set -euo pipefail

AGENTS_DIR="/home/nnkre/.claude/agents"
NAMES_JSON="${AGENTS_DIR}/names.json"
IMAGES_DIR="${AGENTS_DIR}/images"
ASCII_DIR="${AGENTS_DIR}/ascii"
ENV_FILE="/home/nnkre/.claude/.env"

# APIキー読み込み
if [ -z "${GEMINI_API_KEY:-}" ] && [ -f "${ENV_FILE}" ]; then
  export GEMINI_API_KEY=$(grep GEMINI_API_KEY "${ENV_FILE}" | cut -d= -f2-)
fi

if [ -z "${GEMINI_API_KEY:-}" ]; then
  echo "ERROR: GEMINI_API_KEY が設定されていません" >&2
  exit 1
fi

mkdir -p "${IMAGES_DIR}" "${ASCII_DIR}"

FORCE=false
TARGET_AGENT=""

for arg in "$@"; do
  case "$arg" in
    --force) FORCE=true ;;
    --*) ;;
    *) TARGET_AGENT="$arg" ;;
  esac
done

# =============================================================================
# Gemini API で画像生成
# =============================================================================
generate_image() {
  local agent_name="$1"
  local prompt="$2"
  local out_file="${IMAGES_DIR}/${agent_name}.png"

  if [ -f "${out_file}" ] && [ "${FORCE}" = "false" ]; then
    echo "  SKIP: ${agent_name} (既存)"
    return 0
  fi

  echo -n "  GENERATING: ${agent_name} ... "

  python3 - <<PYEOF
import os, json, urllib.request, base64, sys

API_KEY = os.environ.get('GEMINI_API_KEY', '')
MODEL = "gemini-2.5-flash-image"
url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"

full_prompt = """${prompt}

Style: pixel art 8-bit retro sprite, anime chibi character, cute and expressive,
clean white background, front-facing portrait, vibrant colors, clear outlines"""

data = json.dumps({
    "contents": [{"parts": [{"text": full_prompt}]}],
    "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]}
}).encode()

req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
try:
    res = urllib.request.urlopen(req, timeout=90)
    d = json.loads(res.read())
    for part in d["candidates"][0]["content"]["parts"]:
        if "inlineData" in part:
            img = base64.b64decode(part["inlineData"]["data"])
            with open("${out_file}", "wb") as f:
                f.write(img)
            print(f"OK ({len(img)} bytes)")
            sys.exit(0)
    print("WARN: 画像なし")
    sys.exit(1)
except urllib.error.HTTPError as e:
    err = json.loads(e.read())
    msg = err.get("error", {}).get("message", "")[:120]
    print(f"HTTP {e.code}: {msg}")
    sys.exit(2)
except Exception as ex:
    print(f"ERROR: {ex}")
    sys.exit(3)
PYEOF
  return $?
}

# =============================================================================
# PNG → chafa ASCIIアート変換
# =============================================================================
convert_to_ascii() {
  local agent_name="$1"
  local png_file="${IMAGES_DIR}/${agent_name}.png"
  local txt_file="${ASCII_DIR}/${agent_name}.txt"

  [ -f "${png_file}" ] || return 1

  if command -v chafa &>/dev/null; then
    echo -n "  CHAFA: ${agent_name} ... "
    chafa --format=symbols --colors=256 --size=32x20 "${png_file}" > "${txt_file}"
    echo "OK"
  else
    echo "  WARN: chafa未インストール → sudo apt install -y chafa imagemagick"
  fi
}

# =============================================================================
# メイン処理
# =============================================================================
echo "=== AI社員 イラスト生成 ==="
echo "  モデル: gemini-2.5-flash-image"
echo "  対象: ${TARGET_AGENT:-全員}"
echo ""

SUCCESS=0
FAIL=0

agents=$(python3 -c "
import json
d = json.load(open('${NAMES_JSON}'))
for k, v in d.items():
    prompt = v.get('image_prompt', 'cute anime chibi AI character, white background')
    # パイプ文字をエスケープ
    prompt = prompt.replace('|', ',')
    print(k + '|' + prompt)
")

while IFS='|' read -r agent_name image_prompt; do
  if [ -n "${TARGET_AGENT}" ] && [ "${agent_name}" != "${TARGET_AGENT}" ]; then
    continue
  fi

  sleep 4  # レート制限対策（有料: 150 RPM）

  if generate_image "${agent_name}" "${image_prompt}"; then
    convert_to_ascii "${agent_name}"
    SUCCESS=$((SUCCESS+1))
  else
    FAIL=$((FAIL+1))
  fi

done <<< "${agents}"

echo ""
echo "=== 完了: 成功=${SUCCESS}, 失敗=${FAIL} ==="
if ! command -v chafa &>/dev/null; then
  echo ""
  echo "chafaをインストールするとPNGをASCIIアートに変換できます:"
  echo "  sudo apt install -y chafa imagemagick"
  echo "  $0 --force"
fi
