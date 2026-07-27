#!/bin/bash
# Monitor running deep-research agents

echo "=== Deep Research Monitor ==="
echo ""

# Count total agents
TOTAL=$(ps aux | grep "claude -p" | grep -v grep | wc -l)
echo "Active agents: $TOTAL"
echo ""

if [ "$TOTAL" -eq 0 ]; then
    echo "No agents running."
    exit 0
fi

# Show agent tree
echo "Agent Tree:"
echo "─────────────────────────────────────────────────────────────"

ps aux | grep "claude -p" | grep -v grep | while read -r line; do
    # Extract the question from the command (handle escaped quotes)
    QUESTION=$(echo "$line" | sed 's/.*QUESTION: ["\x27]*\([^"\x27]*\).*/\1/' | head -c 80)
    MODEL=$(echo "$line" | grep -oE -- '--model (haiku|sonnet|opus)' | awk '{print $2}')

    if [ -n "$QUESTION" ] && [ "$QUESTION" != "$line" ]; then
        # Check model to determine level
        if [ "$MODEL" = "haiku" ]; then
            echo "  └─ [haiku] $QUESTION..."
        elif [ "$MODEL" = "sonnet" ]; then
            echo "  └─ [sonnet] $QUESTION..."
        else
            echo "  └─ [opus] $QUESTION..."
        fi
    fi
done

echo ""
echo "─────────────────────────────────────────────────────────────"
echo ""

# Show reports in progress
echo "Reports directory:"
ls -la reports/ 2>/dev/null | grep -E "^d.*2025" | while read -r line; do
    DIR=$(echo "$line" | awk '{print $NF}')
    if [ -f "reports/$DIR/SYNTHESIS.md" ]; then
        LINES=$(wc -l < "reports/$DIR/SYNTHESIS.md")
        echo "  📄 $DIR ($LINES lines)"
    else
        echo "  📝 $DIR (in progress)"
    fi
done
