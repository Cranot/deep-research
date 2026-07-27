#!/bin/bash
# Deep Research - Hierarchical Agent Exploration
# https://github.com/Cranot/deep-research
#
# Turn any question into multi-agent exploration.
# Agents autonomously decide to break down complex questions
# or answer directly when atomic.

set -e

# Defaults
ORCHESTRATOR="opus"
RESEARCHER="sonnet"
WEB_SEARCH=false
MAX_CONCURRENT=10

show_help() {
    cat << 'EOF'
Deep Research - Hierarchical Agent Exploration

USAGE:
    ./deep-research.sh [options] "Your question"

OPTIONS:
    -m, --model MODEL       Orchestrator model: opus (default), sonnet, haiku
    -r, --researcher MODEL  Sub-agent model: opus, sonnet (default), haiku
    -c, --concurrent N      Max concurrent agents (default: 10)
    -w, --web               Enable web search for agents
    -h, --help              Show this help

EXAMPLES:
    # Best quality: Opus orchestrator + Sonnet researchers (default)
    ./deep-research.sh "What makes people buy vs just admire?"

    # With web search for current information
    ./deep-research.sh --web "What are the latest AI agent frameworks?"

    # Fast & cheap: Sonnet + Haiku
    ./deep-research.sh -m sonnet -r haiku "Why do startups fail?"

    # All Opus (expensive but thorough)
    ./deep-research.sh -m opus -r opus --web "Deep analysis of X"

HOW IT WORKS:
    1. Your question goes to a coordinator agent
    2. Agent decides: complex → spawn sub-agents, atomic → answer
    3. Sub-agents follow the same rule (recursive, unlimited depth)
    4. Results synthesize back up the chain
    5. Final report saved to reports/ folder

REQUIREMENTS:
    - Claude CLI installed (claude command available)
    - API access configured

EOF
    exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            ;;
        -m|--model)
            ORCHESTRATOR="$2"
            shift 2
            ;;
        -r|--researcher)
            RESEARCHER="$2"
            shift 2
            ;;
        -w|--web)
            WEB_SEARCH=true
            shift
            ;;
        -c|--concurrent)
            MAX_CONCURRENT="$2"
            shift 2
            ;;
        *)
            QUESTION="$1"
            shift
            ;;
    esac
done

if [ -z "$QUESTION" ]; then
    show_help
fi

# Build allowed tools based on flags
if [ "$WEB_SEARCH" = true ]; then
    TOOLS="Bash(./research.sh:*),WebSearch,WebFetch"
    RESEARCH_METHOD="Use WebSearch for current information."
else
    TOOLS="Bash(./research.sh:*)"
    RESEARCH_METHOD="Answer from your knowledge."
fi

# Export for research.sh to inherit
export WEB_SEARCH
export MAX_CONCURRENT

# Generate folder name from question
SLUG=$(echo "$QUESTION" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//' | sed 's/-$//' | cut -c1-50)
DATE=$(date '+%Y-%m-%d')

# Create research folder
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPORT_DIR="${SCRIPT_DIR}/reports/${DATE}-${SLUG}"
mkdir -p "$REPORT_DIR"

OUTPUT_FILE="${REPORT_DIR}/SYNTHESIS.md"

echo "=== Deep Research ===" >&2
echo "Question: $QUESTION" >&2
echo "Orchestrator: $ORCHESTRATOR" >&2
echo "Researchers: $RESEARCHER" >&2
echo "Max concurrent: $MAX_CONCURRENT" >&2
echo "Web search: $WEB_SEARCH" >&2
echo "Output: $OUTPUT_FILE" >&2
echo "====================" >&2
echo "" >&2

# The prompt with recursive DNA (Recipe v5)
PROMPT="QUESTION: \"$QUESTION\"

You are the orchestrator. Break down this question, delegate to researchers, then synthesize.

TO SPAWN A RESEARCHER:
./research.sh \"sub-question\" $RESEARCHER

IMPORTANT: Each ./research.sh call will BLOCK and return the researcher's findings.
Spawn multiple researchers in ONE response to run them in parallel.
After ALL researchers return their findings, write your synthesis.

$RESEARCH_METHOD

Steps:
1. List the angles this question needs explored
2. Spawn a researcher for each angle (in one response)
3. Read ALL their findings when they return
4. Write a comprehensive synthesis combining all findings

Begin by identifying the angles, then spawn your researchers."

# Write header
echo "# $QUESTION" > "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "> Generated $(date '+%Y-%m-%d %H:%M') | Orchestrator: $ORCHESTRATOR | Researchers: $RESEARCHER | Web: $WEB_SEARCH" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "---" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Run and save
claude -p "$PROMPT" --model "$ORCHESTRATOR" --output-format text --allowedTools "$TOOLS" | tee -a "$OUTPUT_FILE"

echo "" >&2
echo "=== Research saved to $OUTPUT_FILE ===" >&2
