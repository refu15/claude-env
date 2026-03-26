# Self-Learning Protocol

All agents MUST follow this protocol for every task execution.

## Phase 1: Pre-Task Consultation (BEFORE starting work)

Before executing any task, the agent MUST:

1. **Read its own learning file**: `memory/agents/{agent-type}.md`
2. **Read shared error catalog**: `memory/shared/error-catalog.md`
3. **Check for relevant cross-agent patterns**: `memory/shared/cross-agent-patterns.md`
4. **Apply known patterns** to the current task plan

### Pre-Task Prompt Template
```
Before starting, I will consult my learning history...
- Relevant past learnings: [list or "none found"]
- Known pitfalls to avoid: [list or "none"]
- Applicable patterns: [list or "none"]
```

## Phase 2: Task Execution (DURING work)

During execution, the agent SHOULD:
- Note any unexpected behaviors or errors encountered
- Track which approaches worked vs. failed
- Record time-consuming steps or blockers

## Phase 3: Post-Task Reflection (AFTER completing work)

After every task, the agent MUST append a reflection entry to its learning file.

### Reflection Entry Format
```markdown
### [YYYY-MM-DD] Task: {brief description}
- **Result**: success | partial | failure
- **What worked**: {what went well}
- **What didn't work**: {mistakes, failed approaches}
- **Root cause** (if failure): {why it failed}
- **Lesson learned**: {actionable insight for future tasks}
- **Pattern** (if applicable): {reusable pattern name}
- **Confidence**: low | medium | high
```

### Rules for Reflections
- Be specific and actionable, not vague
- Include file paths, error messages, and concrete details
- If a lesson contradicts a previous one, update the previous entry
- Mark lessons with confidence levels:
  - **low**: first occurrence, might be coincidence
  - **medium**: seen 2 times, likely a real pattern
  - **high**: seen 3+ times, confirmed pattern

## Phase 4: Pattern Promotion

When a lesson reaches **high confidence** (confirmed 3+ times):

1. Add it to `memory/shared/cross-agent-patterns.md`
2. If it applies to multiple agents, add it to `MEMORY.md` (keep under 200 lines)
3. Remove redundant individual entries from agent files

## Phase 5: Periodic Consolidation (learning-agent)

The `learning-agent` should be invoked periodically to:

1. **Review** all agent learning files for patterns
2. **Consolidate** duplicate learnings across agents
3. **Promote** high-confidence patterns to shared knowledge
4. **Prune** outdated or contradicted learnings
5. **Generate** a performance summary report

### Consolidation Schedule
- After every 10 tasks: Quick review
- Weekly: Full consolidation
- Monthly: Deep analysis with improvement proposals

## Error Logging

When an error occurs, agents MUST log it to `memory/shared/error-catalog.md`:

```markdown
### {Error Type}: {Brief Description}
- **First seen**: {date}
- **Frequency**: {count}
- **Context**: {what was happening}
- **Error message**: `{exact error}`
- **Solution**: {what fixed it}
- **Prevention**: {how to avoid it}
```

## Performance Tracking

After each task, log to `memory/shared/performance-log.md`:

```markdown
| Date | Agent | Task | Result | Duration | Notes |
```

## Self-Learning Prompt Injection

When dispatching ANY agent via Task tool, the orchestrator MUST append:

```
SELF-LEARNING PROTOCOL:
1. Before starting, read your learning file at memory/agents/{your-type}.md
2. Apply any relevant past learnings to this task
3. After completion, append a reflection entry to your learning file
4. If you encounter a new error, log it to memory/shared/error-catalog.md
5. Log task result to memory/shared/performance-log.md
```
