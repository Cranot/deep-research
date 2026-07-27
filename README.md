# Deep Research

**Fractal exploration of any question through recursive AI agents.**

A question spawns angles. Each angle spawns deeper angles. The tree grows until questions become atomic — then everything synthesizes back up into one comprehensive answer.

```
Question: "Why do smart people make bad decisions?"
    │
    ├── What cognitive biases affect intelligent people?
    │       ├── How does overconfidence manifest in experts?
    │       ├── What is the curse of knowledge?
    │       └── ... (each can branch further)
    │
    ├── How does expertise create blind spots?
    │       └── ...
    │
    └── What role does emotional reasoning play?
            └── ...

            ↓ ALL BRANCHES EXPLORED IN PARALLEL ↓
            ↓ SYNTHESIZE BACK UP THE TREE ↓

                  [Comprehensive Answer]
```

---

## ⚠️ Read this before your first run

**Fan-out is unbounded, and it spends your money.**

There is no cap on how many sub-questions a decomposition may produce, and no cap
on how many child agents get spawned. The orchestrator parses *every* `Q:` line
the model emits and launches one agent per line, then recurses. `-p/--parallel`
limits how many run *at the same time*; it does not limit how many run in total.

A single run of the first command in this README decomposed one question into
**69 sub-questions and began spawning 69 child agents.** At the default depth of
5, a modest 8-way branch is ~4,000 leaf calls.

It happens with **no API key set**, which is the part that surprises people: the
default provider shells out to your locally installed `claude` binary, so it
inherits whatever session that binary is already logged into. Nothing prompts
you, and nothing warns you at runtime.

**Start with `-d 1`, on a cheap model, and watch what it does:**

```bash
deep-research research -d 1 -m haiku -r haiku "A small question"
```

Interrupting a run is safe but *unrecoverable* — there is no resume. See
[Checkpoints and resume](#checkpoints-and-resume).

---

## Requirements

The default path does **not** use an API key. It drives CLI tools you have
already installed and logged into.

| You want to use | You need |
|---|---|
| `opus`, `sonnet`, `haiku` (**the default**) | The [`claude` CLI](https://github.com/anthropics/claude-code) on your `PATH`, already logged in: `npm install -g @anthropic-ai/claude-code` then `claude` |
| `gemini:pro`, `gemini:flash` | The `gemini` CLI on your `PATH`, already logged in |
| `gpt5-mini` | `GPT5_MINI_API_KEY` + `GPT5_MINI_ENDPOINT` (your own Azure OpenAI resource) |
| `grok`, `grok-3`, `grok-4` | `OPENROUTER_API_KEY` |
| `kimi` | `KIMI_API_KEY` + `KIMI_ENDPOINT` (your own Azure AI Services resource) |

Python 3.10+.

> `ANTHROPIC_API_KEY` is **not** used for authentication anywhere in this
> project. It appears only as a label in `deep-research validate` output. Claude
> access comes from the `claude` CLI's own session. The same is true of
> `GEMINI_API_KEY` and the `gemini` CLI.

---

## Installation

```bash
git clone https://github.com/Cranot/deep-research.git
cd deep-research

pip install -e .

# Or with development dependencies
pip install -e ".[dev]"
```

### Environment variables

Only needed for the three key-based providers. Create a `.env` in the project
root (it is gitignored):

```bash
# Azure OpenAI — bring your own resource
GPT5_MINI_API_KEY=your-key
GPT5_MINI_ENDPOINT=https://<your-resource>.openai.azure.com
GPT5_MINI_DEPLOYMENT=gpt-5-mini          # optional
GPT5_MINI_API_VERSION=2024-02-01         # optional

# OpenRouter (Grok)
OPENROUTER_API_KEY=your-key
OPENROUTER_MODEL=x-ai/grok-4.1-fast:free  # optional

# Kimi via Azure AI Services — bring your own resource
KIMI_API_KEY=your-key
KIMI_ENDPOINT=https://<your-resource>.services.ai.azure.com/openai/v1/
KIMI_MODEL=Kimi-K2-Thinking               # optional
```

No endpoint defaults ship with this project. If you do not set the endpoint, the
provider raises a clear error rather than pointing at someone else's resource.

Behaviour can also be tuned through `DEEP_RESEARCH_*` variables — see
`deep-research config` for the full list and current values.

---

## Quick Start

### Python CLI

`deep-research` requires a subcommand. There are six: `research`,
`perspectives`, `socratic`, `cache`, `config`, `validate`.

```bash
# Basic research (start shallow — see the cost warning above)
deep-research research -d 1 "What makes startups successful?"

# Socratic mode — improve the question before researching it
deep-research socratic "How do I become more productive?"

# Perspective expansion — multi-angle analysis
deep-research perspectives "What makes good leadership?"

# Check what is configured and reachable
deep-research config
deep-research validate "Your question"
```

### Python API

The four strategies are reachable **only** from the Python API. There is no
`--strategy` CLI flag.

```python
import asyncio
from pathlib import Path

from deep_research.core import MasterChef

async def main():
    chef = MasterChef(
        output_dir=Path("reports/my-research"),
        max_parallel=10,
    )

    result = await chef.cook(
        "What makes startups successful?",
        "recursive_research",   # or "socratic" / "perspective_expander" / "grounded_research"
        context={"model": "haiku"},
    )

    print(result.final_synthesis.content)

asyncio.run(main())
```

`chef.cook()` also accepts a strategy object, which is how you change its
parameters:

```python
from deep_research.core import grounded_research_strategy

result = await chef.cook(
    "Current state of AI",
    grounded_research_strategy(max_depth=1),
    context={"model": "haiku"},
)
```

> `MasterChef` and the CLI are two separate execution paths. The CLI runs
> `Orchestrator`; strategies, the knowledge graph and `graph.json` belong to
> `MasterChef`. Features are not shared between them — the table below says
> which is which.

### Legacy bash

```bash
./deep-research.sh "Your question"
./deep-research.sh -d 2 -m opus -r haiku "Your question"
```

The bash script is the original implementation and is **not** flag-compatible
with the Python CLI: it has no `-o`, no `-v` and no perspective options, its
`-w/--web` genuinely works, and its `-d 0` genuinely means unlimited. It is the
only thing in this repo that writes `SYNTHESIS.md`.

---

## Strategies

| Strategy | Description | Best For |
|----------|-------------|----------|
| `recursive_research` | Decompose → Answer → Synthesize | General research |
| `socratic` | Challenge assumptions, find better questions | Unclear problems |
| `perspective_expander` | Multi-angle analysis with blind spot detection | Complex topics |
| `grounded_research` | Web-verified answers (runs live web searches) | Fact-checking, current events |

All four are addressable by name through `MasterChef.cook()`:

```python
from deep_research.core.strategy import StrategyRegistry, register_builtin_strategies

register_builtin_strategies()
print(sorted(StrategyRegistry.instance().available()))
# ['grounded_research', 'perspective_expander', 'recursive_research', 'socratic']
```

---

## Model Configuration

### Format

```
provider:model   →  gemini:flash, claude:opus
model            →  defaults to Claude (haiku = claude:haiku)
```

### Supported providers

Five providers ship with the project:

| Provider | Models | Auth | Notes |
|----------|--------|------|-------|
| **Claude** | `opus`, `sonnet`, `haiku` | local `claude` CLI | Default. Best orchestrator (`opus`) |
| **Gemini** | `flash`, `pro` | local `gemini` CLI | Fast, cost-effective leaves |
| **OpenAI/Azure** | `gpt5-mini` | API key + your endpoint | Requires temperature=1.0 |
| **OpenRouter** | `grok`, `grok-3`, `grok-4` | API key | Via x-ai |
| **Kimi** | `kimi` | API key + your endpoint | Strong merger in our testing |

### Recommended configurations

```bash
# Quality-focused
deep-research research -m opus -r haiku -d 2 "Your question"

# Cost-optimized with ensemble
deep-research research -l "haiku,gemini:flash" --merger kimi:kimi -d 2 "Your question"

# All-Gemini
deep-research research -m gemini:pro -r gemini:flash -d 2 "Your question"
```

---

## CLI Options

```bash
deep-research research [OPTIONS] "Your question"
```

| Flag | Default | Description |
|------|---------|-------------|
| `-m, --model` | `opus` | Orchestrator model |
| `-r, --researcher` | `haiku` | Researcher model for child agents |
| `-l, --leaves` | (use `-r`) | Leaf ensemble, comma-separated |
| `--merger` | (use `-m`) | Model for merging ensemble results |
| `-d, --depth` | `0` | Max recursion depth. **`0` means "use the configured default", currently 5 — it does not mean unlimited.** Hard ceiling 20 |
| `-p, --parallel` | `10` | Max *concurrent* agents (not a total cap) |
| `-o, --output` | auto | Output directory |
| `-w, --web` | off | **Accepted but not yet wired on this command** — it has no effect. The CLI prints a note if you pass it. Web grounding lives in the `grounded_research` strategy (Python API) and in the bash script |
| `-v, --verbose` | off | **Accepted but not yet wired on this command** — it has no effect |
| `--perspectives` | — | Perspective models, comma-separated |
| `--perspective-picker` | `sonnet` | Model that selects the best perspectives |
| `--all-perspectives` | off | Use all available models for perspective expansion |
| `--perspective-depth` | `1` | 1 = flat, 2+ = recursive sub-perspectives |
| `--no-blind-spot` | off | Disable blind spot detection |
| `--no-perspective-cache` | off | Disable perspective caching |

There is **no `--strategy` flag.** Strategy selection is Python-API only.

---

## Architecture

```
src/deep_research/
├── core/                    # MasterChef framework (Python API path)
│   ├── node.py              # Typed nodes, epistemic states
│   ├── graph.py             # Knowledge graphs with checkpointing
│   ├── operation.py         # Operation protocol
│   ├── strategy.py          # Declarative strategies + registry
│   ├── chef.py              # MasterChef orchestrator
│   └── operations/          # Concrete operations
│       ├── decompose.py     # DECOMPOSE: Question → Sub-questions
│       ├── answer.py        # ANSWER: Question → Answer
│       ├── synthesize.py    # SYNTHESIZE: Findings → Synthesis
│       ├── detect.py        # DETECT: Blind spots, tensions
│       └── ground.py        # GROUND: Web-verified claims
├── providers/               # LLM integrations
│   ├── claude.py            # Local `claude` CLI (subprocess)
│   ├── gemini.py            # Local `gemini` CLI (subprocess)
│   ├── openai_azure.py      # Azure OpenAI
│   ├── openrouter.py        # OpenRouter
│   └── kimi.py              # Kimi (Azure AI Services)
├── recipes/                 # Research methodologies
│   ├── perspective.py       # Perspective expansion
│   └── socratic.py          # Socratic questioning
├── orchestrator.py          # Recursive agent tree (CLI path)
└── cli.py                   # Typer CLI
```

### Key concepts

**Nodes**: Typed content units (Question, Answer, Insight, BlindSpot, …) with epistemic status (Unknown → Explored → Validated → Synthesized)

**Operations**: Epistemic transitions (DECOMPOSE, ANSWER, SYNTHESIZE, GROUND, …)

**Strategies**: Declarative recipes that orchestrate operations

**MasterChef**: Executes strategies on knowledge graphs

---

## Output

`deep-research research` writes:

```
reports/YYYY-MM-DD-your-question-slug/
├── agents/                   # Individual agent outputs
│   ├── d0-001-opus.md        # ← the root agent's file IS the final report
│   ├── d1-002-haiku.md
│   └── ...
├── research.log              # JSONL event log
└── metrics.json              # Run metrics
```

`deep-research perspectives` adds `PERSPECTIVES.md`; `deep-research socratic`
writes `SOCRATIC.md`.

There is deliberately no separate `SYNTHESIS.md` on the Python path — the
root agent's file under `agents/` is the synthesized report. `SYNTHESIS.md` is
written by the legacy `deep-research.sh` only.

`graph.json` is written by the **Python API** path (`MasterChef`) when an
`output_dir` is given. The CLI does not produce it.

### Checkpoints and resume

`MasterChef` checkpoints the knowledge graph to `graph.json` after each phase,
and `KnowledgeGraph.load()` can read one back. **There is no resume path wired
up** — no `--resume` flag, and nothing in the CLI or `MasterChef` restarts from
a checkpoint. The CLI path does not checkpoint at all; it writes per-agent
markdown as it goes, so an interrupted run leaves partial files you can read but
cannot continue. Treat `graph.json` as an inspectable artifact, not a resume
point.

---

## Development

```bash
pip install -e ".[dev]"

pytest tests/ -v          # 114 tests, no network, no spend
ruff check src/ tests/
ruff format --check src/ tests/
```

`tests/test_masterchef.py` contains two live integration tests that really do
invoke a model. They are skipped unless a `claude` binary is on `PATH` **and**
`DEEP_RESEARCH_LIVE_TESTS=1` is set:

```bash
DEEP_RESEARCH_LIVE_TESTS=1 pytest tests/test_masterchef.py
```

---

## Key Insights

1. **Multi-model merges beat single models** — ensembling 4+ diverse outputs produces higher quality than any single model
2. **Kimi-K2-Thinking is a strong merger** — 9.5/10 quality in our own side-by-side testing
3. **Cheap models ensemble well** — haiku + flash as leaves, kimi as merger = best cost/quality
4. **Every question contains hidden angles** — recursive exploration surfaces what you'd never think to ask

These are observations from the authors' own runs, not a benchmark.

---

## Related

- **[RECIPES.md](RECIPES.md)** — 156 research patterns
- **[docs/API.md](docs/API.md)** — Python API reference
- **[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** — Common problems
- **[AgentsKB](https://agentskb.com)** — Pre-researched knowledge for AI agents

---

## License

MIT — see [LICENSE](LICENSE).

---

<p align="center">
  <b>Deep Research</b> - Fractal exploration through recursive AI agents<br>
  Made by <a href="https://github.com/Cranot">Dimitris Mitsos</a> & <a href="https://agentskb.com">AgentsKB.com</a>
</p>
