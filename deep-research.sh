#!/bin/bash
# Deep Research - Hierarchical Agent Exploration
# https://github.com/Cranot/deep-research
#
# Turn any question into multi-agent exploration.
# Agents autonomously decide to break down complex questions
# or answer directly when atomic.

set -e

QUESTION="$1"
MODEL="${2:-opus}"
OUTPUT_FILE="$3"

show_help() {
    cat << 'EOF'
Deep Research - Hierarchical Agent Exploration

USAGE:
    ./deep-research.sh "Your question" [model] [output_file]

ARGUMENTS:
    question      The question to explore (required)
    model         Coordinator model: opus (default), sonnet, haiku
    output_file   Optional: save output to markdown file

EXAMPLES:
    # Basic usage (Opus coordinator)
    ./deep-research.sh "What makes people buy vs just admire?"

    # Use Sonnet (cheaper)
    ./deep-research.sh "How should I architect auth?" sonnet

    # Save to file
    ./deep-research.sh "Why do startups fail?" opus output.md

HOW IT WORKS:
    1. Your question goes to a coordinator agent
    2. Agent decides: complex → spawn sub-agents in parallel, atomic → answer
    3. Sub-agents follow the same rule (recursive)
    4. Results synthesize back up the chain

REQUIREMENTS:
    - Claude CLI installed (claude command available)
    - API access configured

EOF
    exit 0
}

# Show help
if [ "$1" = "-h" ] || [ "$1" = "--help" ] || [ -z "$QUESTION" ]; then
    show_help
fi

# Create temp directory for agent reports
REPORT_DIR=$(mktemp -d)
export REPORT_DIR

echo "=== Deep Research ===" >&2
echo "Question: $QUESTION" >&2
echo "Coordinator: $MODEL" >&2
echo "====================" >&2
echo "" >&2

PROMPT="QUESTION: \"$QUESTION\"

You are a research agent. You can spawn parallel sub-agents.

## TO SPAWN A SUB-AGENT:
\`\`\`bash
claude -p 'QUESTION: \"[your sub-question here]\"

You are a research agent with a SUPERPOWER... [same instructions]' --model sonnet --output-format text --allowedTools 'Bash(claude:*)' > \"$REPORT_DIR/topic-name.md\" &
\`\`\`

Key points:
- Use & to run in background (parallel)
- Use \`wait\` to collect all results before synthesizing
- Write to $REPORT_DIR/descriptive-name.md for comprehensive reports
- Read reports with: cat $REPORT_DIR/*.md

## YOUR DECISION:
1. COMPLEX question (multiple angles needed) → spawn parallel agents, wait, read their reports, synthesize
2. ATOMIC question (you can fully answer) → answer directly

Your sub-agents can also spawn more if needed.

What does this question need?"

if [ -n "$OUTPUT_FILE" ]; then
    echo "# Deep Research: $QUESTION" > "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "> Generated $(date '+%Y-%m-%d %H:%M') using $MODEL coordinator" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "---" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"

    claude -p "$PROMPT" --model "$MODEL" --output-format text --allowedTools 'Bash(claude:*)' | tee -a "$OUTPUT_FILE"

    echo "" >&2
    echo "=== Saved to $OUTPUT_FILE ===" >&2
else
    claude -p "$PROMPT" --model "$MODEL" --output-format text --allowedTools 'Bash(claude:*)'
fi

# Cleanup
rm -rf "$REPORT_DIR"
