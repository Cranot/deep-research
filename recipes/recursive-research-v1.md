# Recursive Research v1

*The foundation: simple, elegant, fast.*

**Status**: Current implementation in `deep-research.sh`

## Philosophy

One rule, recursively applied: **Explore, then synthesize.**

Simple, elegant, fast. Each node decides: expand into sub-questions or answer directly.

## Flow

```
QUESTION
    ↓
┌─────────────────────────────────────┐
│  EXPLORE                            │
│  - Identify all important angles    │
│  - Output as Q: lines               │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  SPAWN (parallel)                   │
│  - Each Q: becomes a child agent    │
│  - Children explore or answer       │
│  - Recursion based on depth limit   │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  SYNTHESIZE                         │
│  - Combine all child results        │
│  - Draw connections                 │
│  - Produce coherent answer          │
└─────────────────────────────────────┘
    ↓
FINAL OUTPUT
```

## Prompts

### EXPLORE_PROMPT

```
You are a research agent. Given a question, identify all important angles worth exploring.

Think deeply:
- What would experts consider?
- What is non-obvious or often missed?
- What tensions or tradeoffs exist?

List each angle as a focused research question on its own line starting with "Q: "

Be thorough. Do not stop at obvious angles.
```

### LEAF_PROMPT

```
You are a focused research agent. Answer the question directly and thoroughly.
Be comprehensive but concise. Provide concrete examples where helpful.
```

### SYNTHESIZE_PROMPT

```
Synthesize the following research into a coherent, insightful answer.

Original question: {QUESTION}

Research findings:
{RESULTS}

Draw connections between findings, highlight tensions, and provide a nuanced perspective.
```

## Depth Control

| Depth | Behavior |
|-------|----------|
| 0 | Unlimited recursion |
| 1 | Leaf mode - answer directly |
| 2 | Orchestrator spawns leaf children (recommended) |
| 3+ | Multi-level hierarchy |

## Strengths

- **Simple**: One rule applied recursively
- **Fast**: Parallel execution, minimal overhead
- **Elegant**: Easy to understand and modify
- **Scalable**: Works from simple to complex questions

## Limitations

- No quality gate on decomposition
- No critic pass before synthesis
- Fixed depth (not adaptive)
- Single-perspective synthesis
- No validation of output quality
- Branches treated independently
- ~19% weak/empty leaves observed

## When to Use

- Exploratory questions
- Brainstorming and ideation
- Speed matters more than completeness
- Initial research to scope a problem
- Questions where approximate answers suffice

## Example Run

```bash
./deep-research.sh -m opus -r haiku -d 2 "What makes a startup successful?"
```

**Result**: 54 questions explored, 34 agent files, comprehensive synthesis.
