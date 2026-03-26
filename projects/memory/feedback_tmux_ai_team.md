---
name: tmux AI-Team 自動起動
description: 複数のAI社員・チームを使うとき、必ずtmux ai-teamセッションを起動するよう案内する
type: feedback
---

複数のエージェントを使う前に、tmuxのai-teamセッションが起動しているかチェックし、起動していなければユーザーに案内する。

**Why:** 複数AI社員を1画面で同時視認できるようにするため。リアルタイムで各エージェントの出力を確認できる。

**How to apply:**
- 2つ以上のエージェントを起動するタスク（dev-manager, ai-director, chief-operating-agent含む）の前に必ず確認
- 起動コマンド: `~/.claude/scripts/ai-team-tmux.sh`（新しいターミナルで実行）
- セッション確認: `tmux has-session -t ai-team 2>/dev/null`
