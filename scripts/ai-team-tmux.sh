#!/bin/bash
# =============================================================================
# ai-team-tmux.sh
# AI Team tmux setup - 複数AI社員を同時視認
# 各ペインにエージェントのASCIIアートを表示してから起動する
# =============================================================================

SESSION="ai-team"
AGENTS_DIR="/home/nnkre/.claude/agents"
ASCII_DIR="${AGENTS_DIR}/ascii"
NAMES_JSON="${AGENTS_DIR}/names.json"

# =============================================================================
# ペインで実行するコマンド文字列を生成
# 引数: $1=agent_name, $2=後続コマンド (例: "claude" や "bash")
# =============================================================================
make_pane_command() {
  local agent_name="$1"
  local next_cmd="${2:-bash}"
  local ascii_file="${ASCII_DIR}/${agent_name}.txt"
  local nickname="" personality=""

  # names.jsonからエージェント情報取得
  if command -v jq &>/dev/null && [ -f "${NAMES_JSON}" ]; then
    nickname=$(jq -r --arg n "${agent_name}" '.[$n].nickname // ""' "${NAMES_JSON}" 2>/dev/null)
    personality=$(jq -r --arg n "${agent_name}" '.[$n].personality // ""' "${NAMES_JSON}" 2>/dev/null)
  fi

  # ASCIIアートまたはテキストバナーを表示してから次のコマンドを起動
  cat <<CMDEOF
clear; echo ''; if [ -f '${ascii_file}' ]; then cat '${ascii_file}'; else printf '\033[1;36m┌─────────────────────────────────┐\n│  %-32s│\n│  %-32s│\n└─────────────────────────────────┘\033[0m\n' '${agent_name}' '${nickname}'; fi; echo ''; ${next_cmd}
CMDEOF
}

# =============================================================================
# 既存セッションがあれば削除して新規作成
# =============================================================================
tmux kill-session -t $SESSION 2>/dev/null || true

# 新しいセッション作成（メインペイン: ai-director）
tmux new-session -d -s $SESSION -x "$(tput cols 2>/dev/null || echo 220)" -y "$(tput lines 2>/dev/null || echo 50)"

# ウィンドウ名設定
tmux rename-window -t $SESSION:0 "AI-Team"

# =============================================================================
# 4ペインレイアウト作成
#   ペイン0 (左上):  ai-director      → claude起動
#   ペイン1 (右上):  coding-agent     → bash
#   ペイン2 (左下):  research-manager → bash
#   ペイン3 (右下):  learning-agent   → bash（ログ監視）
# =============================================================================

# 右上ペイン作成（水平分割）
tmux split-window -t $SESSION:0 -h

# 左下ペイン作成（ペイン0を垂直分割）
tmux select-pane -t $SESSION:0.0
tmux split-window -t $SESSION:0.0 -v

# 右下ペイン作成（ペイン1を垂直分割）
tmux select-pane -t $SESSION:0.1
tmux split-window -t $SESSION:0.1 -v

# =============================================================================
# 各ペインにエージェントバナー表示 & コマンド起動
# =============================================================================

# ペイン0（左上）: ai-director → claude起動
tmux select-pane -t $SESSION:0.0 -T "ai-director | Director Ken"
tmux send-keys -t $SESSION:0.0 "$(make_pane_command "ai-director" "claude")" Enter

# ペイン1（右上）: coding-agent → bash
tmux select-pane -t $SESSION:0.1 -T "coding-agent | Coder Shin"
tmux send-keys -t $SESSION:0.1 "$(make_pane_command "coding-agent" "bash")" Enter

# ペイン2（左下）: research-manager → bash
tmux select-pane -t $SESSION:0.2 -T "research-manager | Research Chief Rin"
tmux send-keys -t $SESSION:0.2 "$(make_pane_command "research-manager" "bash")" Enter

# ペイン3（右下）: learning-agent → bash（ログ監視）
tmux select-pane -t $SESSION:0.3 -T "learning-agent | Learner Sou"
tmux send-keys -t $SESSION:0.3 "$(make_pane_command "learning-agent" "bash")" Enter

# =============================================================================
# ペインボーダーにタイトルを表示
# =============================================================================
tmux set-option -t $SESSION pane-border-status top
tmux set-option -t $SESSION pane-border-format " #{pane_title} "

# フォーカスをai-directorペイン（claude）に
tmux select-pane -t $SESSION:0.0

# セッションにアタッチ
tmux attach-session -t $SESSION
