#!/bin/bash
# =============================================================================
# start-agent.sh
# 指定エージェントのASCIIアートとプロフィールを表示してから
# claude または bash を起動する
# =============================================================================

AGENTS_DIR="/home/nnkre/.claude/agents"
ASCII_DIR="${AGENTS_DIR}/ascii"
NAMES_JSON="${AGENTS_DIR}/names.json"

# =============================================================================
# 使用法の表示
# =============================================================================
usage() {
  echo "使用法: $0 <agent-name> [--bash|--claude]"
  echo ""
  echo "引数:"
  echo "  agent-name   エージェント名 (例: coding-agent)"
  echo "  --bash       bashを起動（デフォルト: claudeを起動）"
  echo "  --claude     claudeを起動"
  echo ""
  echo "利用可能なエージェント:"
  if [ -f "${NAMES_JSON}" ] && command -v jq &>/dev/null; then
    jq -r 'to_entries[] | "  \(.key)\t(\(.value.nickname))"' "${NAMES_JSON}" 2>/dev/null
  fi
  exit 1
}

# =============================================================================
# ANSIカラー定義
# =============================================================================
RED='\033[91m'
GREEN='\033[92m'
YELLOW='\033[93m'
BLUE='\033[94m'
MAGENTA='\033[95m'
CYAN='\033[96m'
WHITE='\033[97m'
BOLD='\033[1m'
DIM='\033[2m'
RESET='\033[0m'

# エージェント名からカラーを決定（ハッシュ）
get_agent_color() {
  local agent="$1"
  local colors=("${RED}" "${GREEN}" "${YELLOW}" "${BLUE}" "${MAGENTA}" "${CYAN}" "${WHITE}")
  local hash=0
  for ((i=0; i<${#agent}; i++)); do
    hash=$(( (hash * 31 + $(printf '%d' "'${agent:$i:1}")) % 7 ))
  done
  echo "${colors[$hash]}"
}

# =============================================================================
# エージェントのバナーを表示
# =============================================================================
show_agent_banner() {
  local agent_name="$1"
  local ascii_file="${ASCII_DIR}/${agent_name}.txt"

  # names.jsonからデータ取得
  local agent_data nickname name personality
  if [ -f "${NAMES_JSON}" ] && command -v jq &>/dev/null; then
    agent_data=$(jq -r --arg n "${agent_name}" '.[$n] // empty' "${NAMES_JSON}" 2>/dev/null)
    nickname=$(echo "${agent_data}" | jq -r '.nickname // "Unknown"' 2>/dev/null)
    name=$(echo "${agent_data}" | jq -r '.name // "不明"' 2>/dev/null)
    personality=$(echo "${agent_data}" | jq -r '.personality // ""' 2>/dev/null)
  else
    nickname="${agent_name}"
    name="${agent_name}"
    personality=""
  fi

  local color
  color=$(get_agent_color "${agent_name}")

  echo ""

  # ASCIIアートが存在する場合は表示
  if [ -f "${ascii_file}" ]; then
    cat "${ascii_file}"
    echo ""
  else
    # フォールバック: テキストボックスで表示
    printf "${color}${BOLD}"
    printf "╔══════════════════════════════════════════════════╗\n"
    printf "║                                                  ║\n"
    printf "║  %-48s║\n" "AI Agent: ${agent_name}"
    printf "║                                                  ║\n"
    printf "╚══════════════════════════════════════════════════╝\n"
    printf "${RESET}"
    echo ""
  fi

  # エージェント情報テーブル
  printf "${color}${BOLD}┌─────────────────────────────────────────────────────┐${RESET}\n"
  printf "${color}${BOLD}│${RESET}  ${BOLD}%-10s${RESET} ${CYAN}%-40s${RESET}${color}${BOLD}│${RESET}\n" "名前:" "${name}"
  printf "${color}${BOLD}│${RESET}  ${BOLD}%-10s${RESET} ${YELLOW}%-40s${RESET}${color}${BOLD}│${RESET}\n" "ID:" "${agent_name}"
  printf "${color}${BOLD}│${RESET}  ${BOLD}%-10s${RESET} ${WHITE}%-40s${RESET}${color}${BOLD}│${RESET}\n" "Nickname:" "${nickname}"
  printf "${color}${BOLD}│${RESET}  ${BOLD}%-10s${RESET} ${DIM}%-40s${RESET}${color}${BOLD}│${RESET}\n" "役割:" "${personality:0:40}"
  if [ ${#personality} -gt 40 ]; then
    printf "${color}${BOLD}│${RESET}  %-10s ${DIM}%-40s${RESET}${color}${BOLD}│${RESET}\n" "" "${personality:40:40}"
  fi
  printf "${color}${BOLD}└─────────────────────────────────────────────────────┘${RESET}\n"
  echo ""
}

# =============================================================================
# メイン処理
# =============================================================================
main() {
  # 引数チェック（--help を最初に処理）
  if [ $# -eq 0 ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    usage
  fi

  local agent_name="$1"
  local launch_cmd="claude"

  # オプション解析
  shift
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --bash)
        launch_cmd="bash"
        shift
        ;;
      --claude)
        launch_cmd="claude"
        shift
        ;;
      --help|-h)
        usage
        ;;
      *)
        echo "不明なオプション: $1" >&2
        usage
        ;;
    esac
  done

  # エージェント名の検証
  if [ -f "${NAMES_JSON}" ] && command -v jq &>/dev/null; then
    local exists
    exists=$(jq -r --arg n "${agent_name}" 'has($n)' "${NAMES_JSON}" 2>/dev/null)
    if [ "${exists}" != "true" ]; then
      echo "WARNING: '${agent_name}' はnames.jsonに定義されていません" >&2
    fi
  fi

  # バナー表示
  show_agent_banner "${agent_name}"

  # 指定コマンドを起動
  echo "  Starting: ${launch_cmd} ..."
  echo ""
  exec ${launch_cmd}
}

main "$@"
