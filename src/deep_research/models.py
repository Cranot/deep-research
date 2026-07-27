"""
Data models for deep-research.

- Pydantic models: LLM outputs, JSON schemas, validation (boundaries)
- dataclasses: Internal state, dependencies (performance)
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field

# =============================================================================
# Enums
# =============================================================================


class AgentStatus(str, Enum):
    """Agent lifecycle states."""

    PENDING = "pending"
    EXPLORING = "exploring"
    ANSWERING = "answering"
    WAITING_FOR_CHILDREN = "waiting_for_children"
    SYNTHESIZING = "synthesizing"
    COMPLETE = "complete"
    FAILED = "failed"


class ProviderType(str, Enum):
    """Supported LLM providers."""

    CLAUDE = "claude"
    GEMINI = "gemini"
    OPENAI = "openai"  # Azure OpenAI (GPT-5 Mini)
    OPENROUTER = "openrouter"  # Grok, etc.
    KIMI = "kimi"  # Kimi-K2-Thinking via Azure AI Services


# =============================================================================
# Pydantic Models (LLM outputs, validation, serialization)
# =============================================================================


class ResearchQuestion(BaseModel):
    """A research question extracted from exploration."""

    question: str
    rationale: str | None = None


class ExplorationResult(BaseModel):
    """Result of exploring a question for angles."""

    raw_output: str
    questions: list[ResearchQuestion] = Field(default_factory=list)

    @classmethod
    def from_output(cls, output: str) -> "ExplorationResult":
        """Parse Q: lines from raw output."""
        questions = []
        for line in output.strip().split("\n"):
            line = line.strip()
            if line.startswith("Q: "):
                questions.append(ResearchQuestion(question=line[3:].strip()))
        return cls(raw_output=output, questions=questions)


class SynthesisResult(BaseModel):
    """Final synthesized answer."""

    content: str
    sources: list[str] = Field(default_factory=list)
    tensions: list[str] = Field(default_factory=list)


class AgentOutput(BaseModel):
    """Complete agent output for reporting."""

    agent_id: str
    model: str
    status: AgentStatus
    question: str
    exploration: str | None = None
    children_results: list["AgentOutput"] = Field(default_factory=list)
    synthesis: str | None = None
    response: str | None = None  # For leaf agents
    error: str | None = None
    duration_ms: int | None = None


# =============================================================================
# Dataclasses (Internal state, fast operations)
# =============================================================================


@dataclass
class ModelSpec:
    """Parsed model specification (provider:model)."""

    provider: ProviderType
    model: str

    @classmethod
    def parse(cls, spec: str) -> "ModelSpec":
        """Parse 'provider:model' or 'model' (defaults to claude)."""
        if ":" in spec:
            provider_str, model = spec.split(":", 1)
            provider = ProviderType(provider_str.lower())
        else:
            provider = ProviderType.CLAUDE
            model = spec
        return cls(provider=provider, model=model)

    def __str__(self) -> str:
        return f"{self.provider.value}:{self.model}"


@dataclass
class AgentConfig:
    """Configuration for a single agent."""

    question: str
    model: ModelSpec
    depth: int
    max_depth: int  # 0 = unlimited
    agent_num: int
    parent_id: str | None = None

    @property
    def agent_id(self) -> str:
        return f"d{self.depth}-{self.agent_num:03d}"

    @property
    def is_leaf(self) -> bool:
        """True if this agent should answer directly (no children)."""
        return self.max_depth != 0 and self.depth >= self.max_depth - 1


@dataclass
class ResearchConfig:
    """Global research configuration."""

    question: str
    orchestrator: ModelSpec
    researcher: ModelSpec
    leaf_models: list[ModelSpec] = field(default_factory=list)
    merger: ModelSpec | None = None
    max_depth: int = 0  # 0 = unlimited
    max_parallel: int = 10
    web_search: bool = False
    output_dir: Path | None = None
    # Perspective expansion options
    perspective_models: list[ModelSpec] = field(default_factory=list)
    perspective_picker: ModelSpec | None = None
    use_all_perspective_models: bool = False
    perspective_depth: int = 1  # 1 = flat, 2+ = recursive sub-perspectives
    perspective_enable_blind_spot: bool = True  # Enable blind spot detection
    perspective_enable_cache: bool = True  # Enable perspective caching

    def __post_init__(self):
        if self.output_dir is None:
            date = datetime.now().strftime("%Y-%m-%d")
            slug = self._slugify(self.question)
            self.output_dir = Path(f"reports/{date}-{slug}")

    @staticmethod
    def _slugify(text: str, max_len: int = 50) -> str:
        """Convert text to URL-safe slug."""
        import re

        slug = text.lower()
        slug = re.sub(r"[^a-z0-9]+", "-", slug)
        slug = slug.strip("-")[:max_len]
        return slug


@dataclass
class AgentState:
    """Mutable state for a running agent."""

    config: AgentConfig
    status: AgentStatus = AgentStatus.PENDING
    exploration_output: str | None = None
    child_questions: list[str] = field(default_factory=list)
    child_results: list[str] = field(default_factory=list)
    synthesis: str | None = None
    response: str | None = None
    error: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None

    @property
    def duration_ms(self) -> int | None:
        if self.start_time and self.end_time:
            return int((self.end_time - self.start_time).total_seconds() * 1000)
        return None
