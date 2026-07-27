#!/bin/bash
# Helper script for spawning research agents
# Usage: ./research.sh "question" [model]
#
# Examples:
#   ./research.sh "What causes market failures?" haiku
#   ./research.sh "Deep dive into X" sonnet

QUESTION="$1"
MODEL="${2:-haiku}"

# Concurrent limit (inherited from environment, default 10)
MAX_CONCURRENT="${MAX_CONCURRENT:-10}"

if [ -z "$QUESTION" ]; then
    echo "Usage: ./research.sh \"question\" [model]" >&2
    exit 1
fi

# Wait for slot - first come first serve
while [ "$(pgrep -c claude)" -ge "$MAX_CONCURRENT" ]; do
    sleep 2
done

# Inherit web search capability if set
if [ "$WEB_SEARCH" = "true" ]; then
    TOOLS="Bash(./research.sh:*),WebSearch,WebFetch"
    METHOD="Use WebSearch for current information."
else
    TOOLS="Bash(./research.sh:*)"
    METHOD="Answer from your knowledge."
fi

claude -p "QUESTION: \"$QUESTION\"

You are a research agent. $METHOD

If this question has multiple angles worth exploring:
- Spawn sub-agents: ./research.sh \"sub-question\" $MODEL
- Make ALL calls in ONE response (they run in parallel)
- Then synthesize their findings

If this question is atomic: answer directly.

Go deep, not shallow." \
    --model "$MODEL" \
    --output-format text \
    --allowedTools "$TOOLS"
