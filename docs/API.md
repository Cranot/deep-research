# Deep Research API Reference

This document describes the Python API for using deep-research programmatically.

## Installation

```bash
pip install -e .
```

## Quick Start

```python
import asyncio
from deep_research import Orchestrator, ResearchConfig, ModelSpec

# Create configuration
config = ResearchConfig(
    question="What makes startups successful?",
    orchestrator=ModelSpec.parse("opus"),
    researcher=ModelSpec.parse("haiku"),
    max_depth=2,
    max_parallel=10,
)

# Run research
async def main():
    orchestrator = Orchestrator(config)
    result = await orchestrator.run()
    print(result)

asyncio.run(main())
```

---

## Core Classes

### ResearchConfig

Configuration for a research run.

```python
from deep_research import ResearchConfig, ModelSpec
from pathlib import Path

config = ResearchConfig(
    question="Your research question",
    orchestrator=ModelSpec.parse("opus"),       # Required: orchestrator model
    researcher=ModelSpec.parse("haiku"),        # Required: researcher model
    leaf_models=[],                             # Optional: ensemble models
    merger=None,                                # Optional: merger model
    max_depth=2,                                # see note below on 0
    max_parallel=10,                            # Concurrent agents
    web_search=False,                           # Enable web search
    output_dir=Path("reports/custom"),          # Custom output directory
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `question` | `str` | Required | The research question |
| `orchestrator` | `ModelSpec` | Required | Model for exploration/synthesis |
| `researcher` | `ModelSpec` | Required | Model for child agents |
| `leaf_models` | `list[ModelSpec]` | `[]` | Ensemble models for leaves |
| `merger` | `ModelSpec \| None` | `None` | Model for merging ensemble |
| `max_depth` | `int` | `0` | Max recursion. See note below |
| `max_parallel` | `int` | `10` | Concurrent agents (not a total cap) |
| `web_search` | `bool` | `False` | Not read by `Orchestrator`; only the `grounded_research` strategy grounds |
| `output_dir` | `Path \| None` | auto | Output directory |

> **`max_depth=0` is not the same on both paths.** Constructing `ResearchConfig`
> directly with `max_depth=0` disables the depth guard entirely — recursion
> continues until the model stops producing sub-questions. The CLI never passes
> `0` through: it treats `-d 0` as "use `DEEP_RESEARCH_MAX_DEPTH`" (normally 5).
> Fan-out is uncapped in either case — one child agent per sub-question, at
> every level.

---

### ModelSpec

Specification for a model (provider:model).

```python
from deep_research import ModelSpec, ProviderType

# Parse from string
spec = ModelSpec.parse("gemini:flash")
print(spec.provider)  # ProviderType.GEMINI
print(spec.model)     # "flash"

# Create directly
spec = ModelSpec(provider=ProviderType.CLAUDE, model="opus")

# Convert to string
print(str(spec))  # "claude:opus"
```

**Valid Providers:**
- `ProviderType.CLAUDE` - Anthropic Claude
- `ProviderType.GEMINI` - Google Gemini
- `ProviderType.OPENAI` - Azure OpenAI
- `ProviderType.OPENROUTER` - OpenRouter
- `ProviderType.KIMI` - Kimi

---

### Orchestrator

Main research orchestrator.

```python
from deep_research import Orchestrator, ResearchConfig

# Create orchestrator
orchestrator = Orchestrator(
    config=config,
    max_retries=3,                    # Retry on transient failures
    retry_delay=1.0,                  # Initial retry delay (seconds)
    continue_on_child_failure=True,   # Don't crash on child failure
)

# Run research
result = await orchestrator.run()
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `config` | `ResearchConfig` | Required | Research configuration |
| `max_retries` | `int` | `3` | Retry count for transient errors |
| `retry_delay` | `float` | `1.0` | Initial retry delay |
| `continue_on_child_failure` | `bool` | `True` | Continue if children fail |

---

## Validation Functions

### validate_question

```python
from deep_research import validate_question
from deep_research.exceptions import QuestionValidationError

try:
    cleaned = validate_question("  My question?  ")
    print(cleaned)  # "My question?"
except QuestionValidationError as e:
    print(f"Invalid: {e.reason}")
```

### validate_model_spec

```python
from deep_research import validate_model_spec

spec, warnings = validate_model_spec("gemini:flash")
for warning in warnings:
    print(f"Warning: {warning}")
```

### validate_api_key

```python
from deep_research import validate_api_key, ProviderType
from deep_research.exceptions import APIKeyError

try:
    key = validate_api_key(ProviderType.CLAUDE)
except APIKeyError as e:
    print(f"Missing: {e.env_var}")
```

---

## Exception Classes

All exceptions inherit from `DeepResearchError`.

### Validation Errors

```python
from deep_research.exceptions import (
    ValidationError,           # Base validation error
    QuestionValidationError,   # Invalid question
    ConfigValidationError,     # Invalid configuration
    ModelValidationError,      # Invalid model spec
)
```

### Provider Errors

```python
from deep_research.exceptions import (
    ProviderError,        # Base provider error
    APIKeyError,          # Missing API key
    APIConnectionError,   # Connection failed
    APITimeoutError,      # Request timed out
    APIRateLimitError,    # Rate limit exceeded
    APIResponseError,     # Error response
    EmptyResponseError,   # Empty response
)
```

### Orchestration Errors

```python
from deep_research.exceptions import (
    OrchestrationError,      # Base orchestration error
    AgentError,              # Agent failed
    ChildFailureError,       # Children failed
    MaxDepthExceededError,   # Depth limit reached
)
```

### Error Handling Example

```python
from deep_research import Orchestrator, ResearchConfig
from deep_research.exceptions import (
    DeepResearchError,
    APIKeyError,
    ValidationError,
)

try:
    orchestrator = Orchestrator(config)
    result = await orchestrator.run()
except APIKeyError as e:
    print(f"Set environment variable: {e.env_var}")
except ValidationError as e:
    print(f"Invalid input: {e.message}")
except DeepResearchError as e:
    print(f"Research failed: {e.message}")
    for key, value in e.details.items():
        print(f"  {key}: {value}")
```

---

## Logging

### ResearchLogger

```python
from deep_research import init_logger, get_logger
from pathlib import Path

# Initialize for a research run
logger = init_logger(
    output_dir=Path("reports/my-run"),
    verbose=True,
)

# Get the current logger
logger = get_logger()

# Log messages
logger.info("Starting research")
logger.warning("Low confidence result")
logger.error("Something went wrong", exc_info=True)

# Get metrics
metrics = logger.get_metrics()
print(f"Agents: {metrics.completed_agents}/{metrics.total_agents}")
print(f"API calls: {metrics.total_api_calls}")
print(f"Tokens: {metrics.total_input_tokens} in, {metrics.total_output_tokens} out")
```

### ResearchMetrics

```python
from deep_research import ResearchMetrics

# Metrics are collected during research
# Access via logger.get_metrics()

metrics = logger.get_metrics()
print(metrics.to_dict())
# {
#   "start_time": "2024-01-01T12:00:00",
#   "end_time": "2024-01-01T12:05:00",
#   "total_agents": 25,
#   "completed_agents": 24,
#   "failed_agents": 1,
#   "total_api_calls": 50,
#   "cached_calls": 5,
#   "total_input_tokens": 50000,
#   "total_output_tokens": 25000,
#   "total_duration_ms": 300000,
#   "max_depth_reached": 2,
#   "errors": ["Agent d1-005 failed: timeout"]
# }
```

---

## Settings

### Global Settings

```python
from deep_research import settings, configure

# View current settings
print(settings.default_orchestrator)  # "opus"
print(settings.max_depth)             # 5
print(settings.cache_enabled)         # True

# Override at runtime
configure(
    default_orchestrator="sonnet",
    max_depth=3,
    cache_enabled=False,
)
```

### Environment Variables

| Variable | Setting | Default |
|----------|---------|---------|
| `DEEP_RESEARCH_ORCHESTRATOR` | `default_orchestrator` | `opus` |
| `DEEP_RESEARCH_RESEARCHER` | `default_researcher` | `haiku` |
| `DEEP_RESEARCH_MAX_DEPTH` | `max_depth` | `5` |
| `DEEP_RESEARCH_MAX_PARALLEL` | `max_parallel` | `10` |
| `DEEP_RESEARCH_CACHE_ENABLED` | `cache_enabled` | `true` |
| `DEEP_RESEARCH_CACHE_DIR` | `cache_dir` | `~/.cache/deep-research` |
| `DEEP_RESEARCH_VERBOSE` | `verbose` | `false` |

---

## Output Structure

After a research run, the output directory contains:

```
reports/YYYY-MM-DD-slug/
├── research.log        # JSON lines log
├── metrics.json        # Summary metrics
└── agents/
    ├── d0-001-opus.md      # Orchestrator — this file IS the final report
    ├── d1-002-haiku.md     # Child 1
    ├── d1-003-haiku.md     # Child 2
    └── ...
```

There is no separate `SYNTHESIS.md` on this path; the orchestrator's own file
under `agents/` holds the synthesis. (`SYNTHESIS.md` is written by the legacy
`deep-research.sh` only.) `graph.json` is written by `MasterChef`, not by
`Orchestrator`.

---

## Complete Example

```python
import asyncio
from pathlib import Path
from deep_research import (
    Orchestrator,
    ResearchConfig,
    ModelSpec,
    init_logger,
    validate_question,
    validate_api_key,
    ProviderType,
)
from deep_research.exceptions import (
    DeepResearchError,
    APIKeyError,
    ValidationError,
)


async def run_research(question: str) -> str:
    """Run a complete research workflow."""

    # 1. Validate inputs
    try:
        question = validate_question(question)
        validate_api_key(ProviderType.CLAUDE)
    except ValidationError as e:
        raise ValueError(f"Invalid input: {e.message}")
    except APIKeyError as e:
        raise RuntimeError(f"Set {e.env_var} environment variable")

    # 2. Configure research
    config = ResearchConfig(
        question=question,
        orchestrator=ModelSpec.parse("opus"),
        researcher=ModelSpec.parse("haiku"),
        max_depth=2,
        max_parallel=10,
        output_dir=Path("reports/my-research"),
    )

    # 3. Initialize logging
    logger = init_logger(
        output_dir=config.output_dir,
        verbose=True,
    )

    # 4. Run research
    try:
        orchestrator = Orchestrator(config)
        result = await orchestrator.run()

        # 5. Report metrics
        metrics = logger.get_metrics()
        print(f"\nCompleted {metrics.completed_agents} agents")
        print(f"Total tokens: {metrics.total_input_tokens + metrics.total_output_tokens:,}")

        return result

    except DeepResearchError as e:
        logger.error(f"Research failed: {e.message}")
        raise


if __name__ == "__main__":
    result = asyncio.run(run_research("What makes great software architecture?"))
    print("\n=== RESULT ===\n")
    print(result)
```
