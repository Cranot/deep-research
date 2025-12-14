# Deep Research - Self-Spawning Agents

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Claude Code agents that spawn their own sub-agents.**

```bash
./deep-research.sh "Why do startups fail?"
```

Agent decides it needs help → spawns sub-agents → they can spawn more → results flow back up.

## What happens

```
You: "Why do startups fail?"
    │
    └── Coordinator: "I need 4 angles explored"
            ├── Agent 1: researches founder issues
            ├── Agent 2: researches market problems
            ├── Agent 3: researches money stuff
            └── Agent 4: researches team dynamics
                    │
                    ▼
            Combined answer
```

Each agent decides: "Can I answer this, or do I need to break it down more?"

Same logic at every level. It stops when questions become simple enough to answer directly.

## Install

```bash
git clone https://github.com/Cranot/deep-research.git
cd deep-research
chmod +x *.sh
```

Needs [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) installed.

## Use

```bash
# Best quality (Opus) - ~$1-5
./deep-research.sh "Your question"

# Cheaper (Sonnet) - ~$0.20
./deep-research.sh "Your question" sonnet

# Cheapest (Haiku) - ~$0.05
./deep-research.sh "Your question" haiku

# Save to file
./deep-research.sh "Your question" opus output.md
```

## How it works

The trick is `--allowedTools "Bash(claude:*)"` which lets spawned Claude instances spawn more instances.

Each agent:
1. Gets a question
2. Decides: break down (spawn parallel sub-agents) or answer directly
3. Sub-agents write reports to temp files for more comprehensive output
4. Parent reads reports, synthesizes

Agents run in parallel with `&` and `wait`. File-based reports tend to be more thorough than stdout.

## The prompt

This is the actual prompt each agent receives:

```
QUESTION: "Your question here"

You are a research agent. You can spawn parallel sub-agents.

TO SPAWN A SUB-AGENT:
claude -p 'QUESTION: "[sub-question]" ...' --model sonnet --output-format text --allowedTools 'Bash(claude:*)' > report.md &

Key points:
- Use & to run in background (parallel)
- Use `wait` to collect all results before synthesizing
- Write reports to files for comprehensive output

YOUR DECISION:
1. COMPLEX question (multiple angles needed) → spawn parallel agents, wait, synthesize
2. ATOMIC question (you can fully answer) → answer directly

Your sub-agents can also spawn more if needed.
```

`--allowedTools 'Bash(claude:*)'` pre-authorizes spawning more Claude instances.

## Examples

Some questions I ran through it (different models/approaches):

- [What makes people buy vs admire?](examples/buy-vs-admire.md) - Opus coordinator
- [Why do people self-sabotage?](examples/self-sabotage.md) - Sonnet coordinator
- [What makes people feel alive?](examples/aliveness.md) - Sonnet coordinator
- [What keeps people poor?](examples/money-misconceptions.md) - Opus + Sonnet researchers

## Cost

This spawns multiple Claude instances. It's not cheap.

A typical deep research run uses ~5% of a max tier Claude Code subscription ($200/mo). Depends on question complexity and how deep the agents go. Use wisely.

## Built by

[AgentsKB](https://agentskb.com)

## License

MIT
