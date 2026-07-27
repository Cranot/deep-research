#!/bin/bash
# Deep Research - Hierarchical Agent Exploration
# https://github.com/Cranot/deep-research
#
# Turn any question into multi-agent exploration.
# Two-phase agents: Explore (spawn) → Synthesize (combine results)
#
# WARNING: Run from a SEPARATE terminal, NOT from within Claude Code!

set -e

# Defaults
ORCHESTRATOR="opus"
RESEARCHER="haiku"
LEAF_MODELS=""  # Empty = use RESEARCHER, comma-separated for ensemble
MERGER=""       # Empty = use ORCHESTRATOR for merging ensemble results
MAX_DEPTH=0
MAX_PARALLEL=10
WEB_SEARCH=false

show_help() {
    cat << 'EOF'
Deep Research - Hierarchical Agent Exploration

USAGE:
    ./deep-research.sh [options] "Your question"

OPTIONS:
    -m, --model MODEL       Orchestrator model (default: opus)
    -r, --researcher MODEL  Researcher model (default: haiku)
    -l, --leaves MODELS     Leaf ensemble models, comma-separated (default: use -r)
    --merger MODEL          Model for merging ensemble results (default: use -m)
    -d, --depth N           Max recursion depth, 0 = unlimited (default)
    -p, --parallel N        Max concurrent agents (default: 10)
    -w, --web               Enable web search (Claude only)
    -h, --help              Show this help

MODEL FORMAT:
    provider:model   Use specific provider (claude:opus, gemini:flash)
    model            Defaults to Claude (opus = claude:opus)

    Claude:  opus, sonnet, haiku
    Gemini:  pro (gemini-2.5-pro), flash (gemini-2.5-flash)

EXAMPLES:
    ./deep-research.sh "What makes people buy vs just admire?"
    ./deep-research.sh -m sonnet -r haiku "Complex analysis"
    ./deep-research.sh -m gemini:pro -r gemini:flash "Use Gemini"
    ./deep-research.sh -m opus -r gemini:flash "Mixed providers"
    ./deep-research.sh -l "haiku,gemini:flash" "Multi-model leaf ensemble"

OUTPUT:
    reports/YYYY-MM-DD-slug/
    ├── SYNTHESIS.md     Final report
    └── agents/          Individual agent logs

EOF
    exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help) show_help ;;
        -m|--model) ORCHESTRATOR="$2"; shift 2 ;;
        -r|--researcher) RESEARCHER="$2"; shift 2 ;;
        -l|--leaves) LEAF_MODELS="$2"; shift 2 ;;
        --merger) MERGER="$2"; shift 2 ;;
        -d|--depth) MAX_DEPTH="$2"; shift 2 ;;
        -p|--parallel) MAX_PARALLEL="$2"; shift 2 ;;
        -w|--web) WEB_SEARCH=true; shift ;;
        -*) echo "Unknown option: $1" >&2; exit 1 ;;
        *) QUESTION="$1"; shift ;;
    esac
done

if [ -z "$QUESTION" ]; then
    show_help
fi

# Create output directory
DATE=$(date '+%Y-%m-%d')
SLUG=$(echo "$QUESTION" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//' | sed 's/-$//' | cut -c1-50)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT_DIR="${SCRIPT_DIR}/reports/${DATE}-${SLUG}"
AGENTS_DIR="${OUTPUT_DIR}/agents"
mkdir -p "$AGENTS_DIR"

# Initialize counter
echo "0" > "$OUTPUT_DIR/.counter"

# Create clean temp directory
CLEAN_DIR=$(mktemp -d)

# Display settings
echo "=== Deep Research ===" >&2
echo "Question: $QUESTION" >&2
echo "Orchestrator: $ORCHESTRATOR" >&2
echo "Researcher: $RESEARCHER" >&2
if [ -n "$LEAF_MODELS" ]; then
    echo "Leaf Ensemble: $LEAF_MODELS" >&2
    echo "Merger: ${MERGER:-$ORCHESTRATOR}" >&2
fi
echo "Max Depth: $MAX_DEPTH $([ "$MAX_DEPTH" = "0" ] && echo "(unlimited)" || echo "")" >&2
echo "Max Parallel: $MAX_PARALLEL" >&2
echo "Web: $([ "$WEB_SEARCH" = true ] && echo 'enabled' || echo 'disabled')" >&2
echo "Output: $OUTPUT_DIR" >&2
echo "====================" >&2
echo "" >&2

# Prompts
EXPLORE_PROMPT='You are a research agent. Given a question, identify all important angles worth exploring.

Think deeply:
- What would experts consider?
- What is non-obvious or often missed?
- What tensions or tradeoffs exist?

List each angle as a focused research question on its own line starting with "Q: "

Be thorough. Do not stop at obvious angles.'

SYNTHESIZE_PROMPT='Synthesize the following research into a coherent, insightful answer.

Original question: {QUESTION}

Research findings:

{RESULTS}

Draw connections between findings, highlight tensions, and provide a nuanced perspective.'

LEAF_PROMPT='You are a focused research agent. Answer the question directly and thoroughly.
Be comprehensive but concise. Provide concrete examples where helpful.'

MERGE_LEAF_PROMPT='You are combining multiple AI responses to the same question.
Extract the best insights from each, resolve any conflicts, and produce a single comprehensive answer.

Question: {QUESTION}

{RESPONSES}

Provide a unified, high-quality answer that captures the best of each response.'

# Get next agent number
get_next_num() {
    local num=$(cat "$OUTPUT_DIR/.counter")
    num=$((num + 1))
    echo "$num" > "$OUTPUT_DIR/.counter"
    printf "%03d" $num
}

# Parse Q: lines from output
parse_questions() {
    local output="$1"
    echo "$output" | grep -E '^Q: ' | sed 's/^Q: //' || true
}

# Call claude (handles large inputs via file)
call_claude() {
    local prompt="$1"
    local question="$2"
    local model="$3"

    local tools=""
    if [ "$WEB_SEARCH" = true ]; then
        tools="--allowedTools WebSearch,WebFetch"
    fi

    # Use file-based prompt if content is large (>20KB)
    local prompt_len=${#prompt}
    local question_len=${#question}

    if [ $((prompt_len + question_len)) -gt 20000 ]; then
        # Large content - use file for system prompt
        local prompt_file=$(mktemp)
        echo "$prompt" > "$prompt_file"

        local result
        result=$(cd "$CLEAN_DIR" && claude --system-prompt-file "$prompt_file" \
            -p "$question" \
            --model "$model" \
            --output-format text \
            $tools 2>&1)

        rm -f "$prompt_file"
        echo "$result"
    else
        # Small content - direct args
        cd "$CLEAN_DIR" && claude --system-prompt "$prompt" \
            -p "$question" \
            --model "$model" \
            --output-format text \
            $tools 2>&1
    fi
}

# Call gemini (embeds system prompt in question - no --system-prompt flag)
call_gemini() {
    local prompt="$1"
    local question="$2"
    local model="$3"

    # Map short names to full model names
    case "$model" in
        flash) model="gemini-2.5-flash" ;;
        pro) model="gemini-2.5-pro" ;;
        *) ;; # Use as-is if already full name
    esac

    # Gemini doesn't have system prompt flag - embed in question
    local full_prompt="INSTRUCTIONS:
${prompt}

QUESTION:
${question}"

    local total_len=${#full_prompt}

    if [ "$total_len" -gt 20000 ]; then
        # Large content - pipe via stdin (avoids arg limit)
        echo "$full_prompt" | (cd "$CLEAN_DIR" && gemini -m "$model" -o text 2>/dev/null)
    else
        # Small content - direct arg
        (cd "$CLEAN_DIR" && gemini -m "$model" -o text "$full_prompt" 2>/dev/null)
    fi
}

# Call provider (routes to claude or gemini)
# Model format: "provider:model" (e.g., "claude:haiku", "gemini:flash")
# If no provider prefix, defaults to claude
call_provider() {
    local prompt="$1"
    local question="$2"
    local model="$3"

    # Parse provider:model
    local provider="claude"
    local model_name="$model"

    if [[ "$model" == *:* ]]; then
        provider="${model%%:*}"
        model_name="${model#*:}"
    fi

    case "$provider" in
        claude)
            call_claude "$prompt" "$question" "$model_name"
            ;;
        gemini)
            call_gemini "$prompt" "$question" "$model_name"
            ;;
        *)
            echo "Unknown provider: $provider" >&2
            return 1
            ;;
    esac
}

# Process a question (recursive)
# Args: question, model, level, remaining_depth
process_question() {
    local question="$1"
    local model="$2"
    local level="$3"
    local remaining_depth="$4"

    local num=$(get_next_num)
    local agent_id="d${level}-${num}"
    local agent_file="$AGENTS_DIR/${agent_id}-${model}.md"

    # Determine if this is a leaf node
    local is_leaf=false
    if [ "$remaining_depth" = "1" ]; then
        is_leaf=true
    fi

    # Calculate child depth
    local child_depth=0
    if [ "$remaining_depth" != "0" ]; then
        child_depth=$((remaining_depth - 1))
    fi

    echo "[${agent_id}] Starting: ${question:0:60}..." >&2

    if [ "$is_leaf" = true ]; then
        # Determine which models to use for leaves
        local leaf_models_list="$model"
        if [ -n "$LEAF_MODELS" ]; then
            leaf_models_list="$LEAF_MODELS"
        fi

        # Split models into array
        IFS=',' read -ra models_array <<< "$leaf_models_list"
        local num_models=${#models_array[@]}

        if [ "$num_models" = "1" ]; then
            # Single model - standard leaf behavior
            local single_model="${models_array[0]}"
            cat > "$agent_file" << EOF
# Agent ${agent_id} (${single_model})
**Status: ANSWERING**

## Question
${question}

## Response
(working...)
EOF

            echo "[${agent_id}] Answering directly..." >&2
            local output=$(call_provider "$LEAF_PROMPT" "$question" "$single_model")

            cat > "$agent_file" << EOF
# Agent ${agent_id} (${single_model})
**Status: COMPLETE**

## Question
${question}

## Response
${output}
EOF
            echo "[${agent_id}] Complete" >&2
            echo "$output"
            return
        fi

        # Multiple models - ensemble mode
        local models_display=$(IFS='+'; echo "${models_array[*]}")
        cat > "$agent_file" << EOF
# Agent ${agent_id} (ensemble: ${models_display})
**Status: ENSEMBLE ANSWERING**

## Question
${question}

## Models
${leaf_models_list}

## Responses
(working...)
EOF

        echo "[${agent_id}] Ensemble answering with $num_models models..." >&2

        # Call all models in parallel (with concurrency limit)
        local parallel_dir=$(mktemp -d)
        local -a pids=()
        local running=0

        for i in "${!models_array[@]}"; do
            local m="${models_array[$i]}"
            m=$(echo "$m" | xargs)  # Trim whitespace
            local output_file="$parallel_dir/$i.txt"
            echo "[${agent_id}] Calling ${m}..." >&2
            (call_provider "$LEAF_PROMPT" "$question" "$m" > "$output_file") &
            pids+=($!)
            ((running++))
            # Throttle if at max parallel
            if ((running >= MAX_PARALLEL)); then
                wait -n 2>/dev/null || wait "${pids[0]}"
                ((running--))
            fi
        done

        # Wait for remaining
        for pid in "${pids[@]}"; do
            wait "$pid" 2>/dev/null || true
        done

        echo "[${agent_id}] All ensemble models complete. Merging..." >&2

        # Build responses string for merge
        local responses=""
        for i in "${!models_array[@]}"; do
            local m="${models_array[$i]}"
            m=$(echo "$m" | xargs)  # Trim whitespace
            local response=$(cat "$parallel_dir/$i.txt")
            responses="${responses}

### Response from ${m}:
${response}
"
        done

        # Merge using merger model (defaults to orchestrator)
        local merge_model="${MERGER:-$ORCHESTRATOR}"
        local merge_prompt="${MERGE_LEAF_PROMPT//\{QUESTION\}/$question}"
        merge_prompt="${merge_prompt//\{RESPONSES\}/$responses}"
        echo "[${agent_id}] Merging with ${merge_model}..." >&2
        local output=$(call_provider "$merge_prompt" "Merge the responses above into a unified answer." "$merge_model")

        rm -rf "$parallel_dir"

        # Final update
        cat > "$agent_file" << EOF
# Agent ${agent_id} (ensemble: ${models_display})
**Status: COMPLETE**

## Question
${question}

## Individual Responses
${responses}

## Merged Response
${output}
EOF
        echo "[${agent_id}] Complete" >&2
        echo "$output"
        return
    fi

    # Explorer mode - may spawn children
    cat > "$agent_file" << EOF
# Agent ${agent_id} (${model})
**Status: EXPLORING**

## Question
${question}

## Exploration
(working...)
EOF

    echo "[${agent_id}] Exploring..." >&2
    local explore_output=$(call_provider "$EXPLORE_PROMPT" "$question" "$model")

    # Parse research questions from exploration
    local questions=$(parse_questions "$explore_output")
    local q_count=$(echo "$questions" | grep -c . || echo "0")
    echo "[${agent_id}] Found $q_count research questions" >&2

    if [ -z "$questions" ]; then
        # No questions - treat as leaf
        cat > "$agent_file" << EOF
# Agent ${agent_id} (${model})
**Status: COMPLETE**

## Question
${question}

## Response
${explore_output}
EOF
        echo "[${agent_id}] Complete (no sub-questions)" >&2
        echo "$explore_output"
        return
    fi

    # Update file with exploration results
    cat > "$agent_file" << EOF
# Agent ${agent_id} (${model})
**Status: WAITING FOR CHILDREN**

## Question
${question}

## Exploration
${explore_output}

## Children
(spawning...)
EOF

    # Process each research question
    local results=""
    local child_num=0

    # Read all questions into array first (avoids stdin issues with claude)
    local -a questions_array=()
    while IFS= read -r line || [ -n "$line" ]; do
        [ -n "$line" ] && questions_array+=("$line")
    done <<< "$questions"

    local total_q=${#questions_array[@]}
    echo "[${agent_id}] Processing $total_q research questions (max $MAX_PARALLEL parallel)..." >&2

    # Create temp directory for parallel outputs
    local parallel_dir=$(mktemp -d)
    local -a pids=()
    local running=0

    # Launch children with concurrency limit
    for i in "${!questions_array[@]}"; do
        local research_q="${questions_array[$i]}"
        local child_idx=$((i + 1))
        local output_file="$parallel_dir/$child_idx.txt"
        local question_file="$parallel_dir/$child_idx.q"

        # Save question for later
        echo "$research_q" > "$question_file"

        echo "[${agent_id}] Spawning ${child_idx}/${total_q}: ${research_q:0:50}..." >&2

        # Launch in background, save output to file (stderr still goes to terminal)
        (process_question "$research_q" "$RESEARCHER" $((level + 1)) "$child_depth" > "$output_file") &
        pids+=($!)
        ((running++))

        # Throttle if at max parallel
        if ((running >= MAX_PARALLEL)); then
            wait -n 2>/dev/null || wait "${pids[0]}"
            ((running--))
        fi
    done

    echo "[${agent_id}] Waiting for remaining children to complete..." >&2

    # Wait for remaining children
    for pid in "${pids[@]}"; do
        wait "$pid" 2>/dev/null || true
    done

    echo "[${agent_id}] All children complete. Collecting results..." >&2

    # Collect results in order
    for i in "${!questions_array[@]}"; do
        local child_idx=$((i + 1))
        local output_file="$parallel_dir/$child_idx.txt"
        local question_file="$parallel_dir/$child_idx.q"
        local research_q=$(cat "$question_file")
        local child_output=$(cat "$output_file")

        results="${results}

### Research ${child_idx}: ${research_q}

${child_output}

---"
    done

    # Cleanup
    rm -rf "$parallel_dir"

    echo "[${agent_id}] Finished processing $total_q children." >&2

    # Update file before synthesis
    cat > "$agent_file" << EOF
# Agent ${agent_id} (${model})
**Status: SYNTHESIZING**

## Question
${question}

## Exploration
${explore_output}

## Children Results
${results}

## Synthesis
(working...)
EOF

    # Synthesize
    echo "[${agent_id}] Synthesizing..." >&2
    local synth_prompt="${SYNTHESIZE_PROMPT//\{QUESTION\}/$question}"
    synth_prompt="${synth_prompt//\{RESULTS\}/$results}"

    local synthesis=$(call_provider "$synth_prompt" "Synthesize the research above." "$model")

    # Final update
    cat > "$agent_file" << EOF
# Agent ${agent_id} (${model})
**Status: COMPLETE**

## Question
${question}

## Exploration
${explore_output}

## Children Results
${results}

## Synthesis
${synthesis}
EOF

    echo "[${agent_id}] Complete" >&2
    echo "$synthesis"
}

# Prepare synthesis file
SYNTHESIS_FILE="$OUTPUT_DIR/SYNTHESIS.md"
cat > "$SYNTHESIS_FILE" << HEADER
# ${QUESTION}

> Generated $(date '+%Y-%m-%d %H:%M') | Orchestrator: $ORCHESTRATOR | Researcher: $RESEARCHER | Depth: $MAX_DEPTH | Web: $WEB_SEARCH

---

HEADER

# Run the research
FINAL_OUTPUT=$(process_question "$QUESTION" "$ORCHESTRATOR" 0 "$MAX_DEPTH")

# Append to synthesis
echo "$FINAL_OUTPUT" >> "$SYNTHESIS_FILE"

# Cleanup
rm -rf "$CLEAN_DIR"

echo "" >&2
echo "=== Research Complete ===" >&2
echo "Report: $SYNTHESIS_FILE" >&2
echo "Agents: $AGENTS_DIR/" >&2
