"""
Strategies for the MasterChef architecture.

Strategies define HOW to conduct research. They are declarative recipes that:
- Specify goals (what epistemic state we want to reach)
- Define phases (ordered steps toward goals)
- Include heuristics (when to continue vs stop)
- Provide fallbacks (what to do when phases fail)

Strategies are the "cookbooks" - they tell the MasterChef what to do.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable

import yaml

from .node import EpistemicStatus, NodeType
from .operation import OperationType


class GoalType(str, Enum):
    """Types of research goals."""

    # Completeness goals
    ALL_ANSWERED = "all_answered"  # All questions have answers
    ALL_VALIDATED = "all_validated"  # All claims validated
    ALL_SYNTHESIZED = "all_synthesized"  # Everything integrated

    # Depth goals
    DEPTH_REACHED = "depth_reached"  # Hit max depth
    SATURATION = "saturation"  # No new insights emerging

    # Discovery goals
    BLIND_SPOTS_FOUND = "blind_spots_found"  # Discovered hidden angles
    TENSIONS_RESOLVED = "tensions_resolved"  # Conflicts addressed

    # Quality goals
    CONFIDENCE_MET = "confidence_met"  # Reached confidence threshold
    COVERAGE_MET = "coverage_met"  # All perspectives covered


@dataclass
class Goal:
    """A research goal - the desired end state.

    Goals define WHAT we want to achieve. The MasterChef checks
    goals to determine when to stop or continue.
    """

    goal_type: GoalType
    parameters: dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0  # Importance for multi-goal strategies

    def check(self, stats: dict[str, Any]) -> bool:
        """Check if the goal is met based on graph stats.

        This is a simple check - more complex goal checking
        is done by the MasterChef with full graph access.
        """
        if self.goal_type == GoalType.ALL_ANSWERED:
            pending = stats.get("by_status", {}).get("unknown", 0)
            return pending == 0

        if self.goal_type == GoalType.DEPTH_REACHED:
            max_depth = stats.get("max_depth", 0)
            target_depth = self.parameters.get("depth", 2)
            return max_depth >= target_depth

        if self.goal_type == GoalType.ALL_SYNTHESIZED:
            # Check if a SYNTHESIS node type exists (not just synthesized status)
            synthesis_count = stats.get("by_type", {}).get("synthesis", 0)
            return synthesis_count > 0

        # Default: not met
        return False


class PhaseType(str, Enum):
    """Types of research phases."""

    # Core phases
    EXPLORE = "explore"  # Discover angles
    DECOMPOSE = "decompose"  # Break into sub-questions
    ANSWER = "answer"  # Generate answers
    SYNTHESIZE = "synthesize"  # Combine findings

    # Validation phases
    CHALLENGE = "challenge"  # Question assumptions
    VALIDATE = "validate"  # Check against evidence
    GROUND = "ground"  # Verify with web search
    CRITIQUE = "critique"  # Critical review

    # Discovery phases
    DETECT = "detect"  # Find blind spots, tensions
    EXPAND = "expand"  # Add perspectives

    # Special phases
    DELEGATE = "delegate"  # Invoke sub-strategy
    CUSTOM = "custom"  # Custom operation sequence


@dataclass
class PhaseCondition:
    """Condition for when a phase should execute or continue."""

    # Node-based conditions
    min_nodes: int | None = None  # Minimum nodes of target type
    max_nodes: int | None = None  # Maximum nodes to process
    node_types: list[NodeType] | None = None  # Which types to target
    node_status: list[EpistemicStatus] | None = None  # Which statuses to target

    # Depth conditions
    min_depth: int | None = None
    max_depth: int | None = None

    # Custom predicate (for complex conditions)
    predicate: Callable[[dict[str, Any]], bool] | None = None

    def matches(self, stats: dict[str, Any], depth: int = 0) -> bool:
        """Check if conditions are met."""
        if self.min_depth is not None and depth < self.min_depth:
            return False
        if self.max_depth is not None and depth > self.max_depth:
            return False
        if self.predicate is not None:
            return self.predicate(stats)
        return True


@dataclass
class Phase:
    """A phase in a research strategy.

    Phases are ordered steps that apply operations to nodes.
    Each phase can:
    - Select target nodes by type/status
    - Apply one or more operations
    - Spawn parallel sub-phases
    - Delegate to sub-strategies
    """

    name: str
    phase_type: PhaseType

    # What nodes to target
    target_types: list[NodeType] = field(default_factory=list)
    target_status: list[EpistemicStatus] = field(default_factory=list)

    # What operations to apply
    operations: list[OperationType] = field(default_factory=list)

    # Execution control
    parallel: bool = False  # Run on targets in parallel
    max_concurrent: int = 10  # Max parallel executions
    batch_size: int | None = None  # Process in batches

    # Flow control
    repeat_until: PhaseCondition | None = None  # Repeat phase until condition
    skip_if: PhaseCondition | None = None  # Skip phase if condition met
    continue_on_error: bool = False  # Continue if operations fail

    # Sub-strategy delegation
    delegate_to: str | None = None  # Name of sub-strategy to invoke
    delegate_depth: int = 1  # Max recursion for delegation

    # Model assignment
    model_hint: str | None = None  # Suggested model for this phase

    # Tool access
    web_search: bool = False  # Enable web search for this phase

    # Metadata
    description: str | None = None


@dataclass
class StrategyMetadata:
    """Metadata about a strategy."""

    name: str
    version: str = "1.0"
    description: str | None = None
    author: str | None = None
    tags: list[str] = field(default_factory=list)


@dataclass
class Strategy:
    """A complete research strategy.

    Strategies are declarative recipes that define how to conduct
    research. They specify goals, phases, heuristics, and fallbacks.
    """

    metadata: StrategyMetadata
    goals: list[Goal]
    phases: list[Phase]

    # Execution control
    max_iterations: int = 100  # Safety limit
    checkpoint_after_phases: bool = True  # Save after each phase

    # Heuristics
    early_termination: PhaseCondition | None = None  # Stop early if met
    stall_detection: int = 3  # Phases without progress = stall

    # Fallback strategies
    on_stall: str | None = None  # Strategy to run if stalled
    on_error: str | None = None  # Strategy to run on errors

    def get_phase(self, name: str) -> Phase | None:
        """Get a phase by name."""
        for phase in self.phases:
            if phase.name == name:
                return phase
        return None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "metadata": {
                "name": self.metadata.name,
                "version": self.metadata.version,
                "description": self.metadata.description,
                "author": self.metadata.author,
                "tags": self.metadata.tags,
            },
            "goals": [
                {
                    "type": g.goal_type.value,
                    "parameters": g.parameters,
                    "weight": g.weight,
                }
                for g in self.goals
            ],
            "phases": [
                {
                    "name": p.name,
                    "type": p.phase_type.value,
                    "target_types": [t.value for t in p.target_types],
                    "target_status": [s.value for s in p.target_status],
                    "operations": [o.value for o in p.operations],
                    "parallel": p.parallel,
                    "max_concurrent": p.max_concurrent,
                    "delegate_to": p.delegate_to,
                    "model_hint": p.model_hint,
                    "web_search": p.web_search,
                    "description": p.description,
                }
                for p in self.phases
            ],
            "max_iterations": self.max_iterations,
            "checkpoint_after_phases": self.checkpoint_after_phases,
            "stall_detection": self.stall_detection,
            "on_stall": self.on_stall,
            "on_error": self.on_error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Strategy":
        """Deserialize from dictionary."""
        meta = data.get("metadata", {})
        metadata = StrategyMetadata(
            name=meta.get("name", "unnamed"),
            version=meta.get("version", "1.0"),
            description=meta.get("description"),
            author=meta.get("author"),
            tags=meta.get("tags", []),
        )

        goals = [
            Goal(
                goal_type=GoalType(g["type"]),
                parameters=g.get("parameters", {}),
                weight=g.get("weight", 1.0),
            )
            for g in data.get("goals", [])
        ]

        phases = [
            Phase(
                name=p["name"],
                phase_type=PhaseType(p["type"]),
                target_types=[NodeType(t) for t in p.get("target_types", [])],
                target_status=[EpistemicStatus(s) for s in p.get("target_status", [])],
                operations=[OperationType(o) for o in p.get("operations", [])],
                parallel=p.get("parallel", False),
                max_concurrent=p.get("max_concurrent", 10),
                delegate_to=p.get("delegate_to"),
                model_hint=p.get("model_hint"),
                web_search=p.get("web_search", False),
                description=p.get("description"),
            )
            for p in data.get("phases", [])
        ]

        return cls(
            metadata=metadata,
            goals=goals,
            phases=phases,
            max_iterations=data.get("max_iterations", 100),
            checkpoint_after_phases=data.get("checkpoint_after_phases", True),
            stall_detection=data.get("stall_detection", 3),
            on_stall=data.get("on_stall"),
            on_error=data.get("on_error"),
        )

    def save_yaml(self, path: Path) -> None:
        """Save strategy to YAML file."""
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, sort_keys=False)

    @classmethod
    def load_yaml(cls, path: Path) -> "Strategy":
        """Load strategy from YAML file."""
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)


# =============================================================================
# Strategy Registry
# =============================================================================


class StrategyRegistry:
    """Registry for strategies.

    Strategies can be registered by name and retrieved for execution.
    Supports both programmatic and YAML-based strategies.
    """

    _instance: "StrategyRegistry | None" = None
    _strategies: dict[str, Strategy]
    _strategy_paths: dict[str, Path]

    def __new__(cls) -> "StrategyRegistry":
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._strategies = {}
            cls._instance._strategy_paths = {}
        return cls._instance

    def register(self, strategy: Strategy) -> None:
        """Register a strategy."""
        self._strategies[strategy.metadata.name] = strategy

    def register_path(self, name: str, path: Path) -> None:
        """Register a path to a YAML strategy (lazy loading)."""
        self._strategy_paths[name] = path

    def get(self, name: str) -> Strategy | None:
        """Get a strategy by name."""
        # Check registered strategies first
        if name in self._strategies:
            return self._strategies[name]

        # Try lazy loading from path
        if name in self._strategy_paths:
            strategy = Strategy.load_yaml(self._strategy_paths[name])
            self._strategies[name] = strategy
            return strategy

        return None

    def available(self) -> list[str]:
        """Get list of available strategy names."""
        return list(set(self._strategies.keys()) | set(self._strategy_paths.keys()))

    @classmethod
    def instance(cls) -> "StrategyRegistry":
        """Get singleton instance."""
        return cls()


# =============================================================================
# Built-in Strategy Builders
# =============================================================================


def recursive_research_strategy(
    max_depth: int = 2,
    parallel: bool = True,
    web_grounding: bool = False,
    perspectives: bool = False,
    blind_spots: bool = False,
    researcher_model: str | None = None,
    name: str = "recursive_research",
    description: str = "Fractal exploration through recursive decomposition",
) -> Strategy:
    """Build the Recursive Research strategy (v1).

    Flow: [Perspectives] → Decompose → Answer → [Ground] → [Blind Spots] → Synthesize

    Args:
        max_depth: Maximum recursion depth (default: 2)
        parallel: Run leaf answers in parallel (default: True)
        web_grounding: Verify answers with web search before synthesis (default: False)
        perspectives: Expand question into multiple perspectives first (default: False)
        blind_spots: Detect blind spots before final synthesis (default: False)
        researcher_model: Model for leaf answers (default: use orchestrator model)
        name: Registry key for the built strategy. Variants built on top of this
            builder MUST pass a distinct name -- the registry is keyed on
            metadata.name, so two variants sharing a name silently overwrite
            each other and become unreachable.
        description: Human-readable description stored in the metadata.
    """
    phases = []

    # Optional: Expand into perspectives first
    if perspectives:
        phases.extend(
            [
                Phase(
                    name="detect_domain",
                    phase_type=PhaseType.DETECT,
                    target_types=[NodeType.QUESTION],
                    target_status=[EpistemicStatus.UNKNOWN],
                    operations=[OperationType.DETECT],
                    description="Detect the problem domain",
                ),
                Phase(
                    name="expand_perspectives",
                    phase_type=PhaseType.EXPAND,
                    target_types=[NodeType.QUESTION],
                    target_status=[EpistemicStatus.EXPLORED],
                    operations=[OperationType.EXPAND],
                    description="Generate relevant perspectives",
                ),
            ]
        )

    # Core research phases
    phases.extend(
        [
            Phase(
                name="decompose",
                phase_type=PhaseType.DECOMPOSE,
                target_types=[NodeType.QUESTION, NodeType.PERSPECTIVE]
                if perspectives
                else [NodeType.QUESTION],
                target_status=[EpistemicStatus.UNKNOWN, EpistemicStatus.PROPOSED],
                operations=[OperationType.DECOMPOSE],
                description="Break questions into sub-questions",
            ),
            Phase(
                name="answer_leaves",
                phase_type=PhaseType.ANSWER,
                target_types=[NodeType.SUB_QUESTION],
                target_status=[EpistemicStatus.UNKNOWN, EpistemicStatus.EXPLORED],
                operations=[OperationType.ANSWER],
                parallel=parallel,
                model_hint=researcher_model,  # Use researcher model if specified
                description="Answer leaf questions directly",
            ),
        ]
    )

    # Optional: Web grounding
    if web_grounding:
        phases.append(
            Phase(
                name="ground_answers",
                phase_type=PhaseType.GROUND,
                target_types=[NodeType.ANSWER],
                target_status=[EpistemicStatus.SYNTHESIZED],
                operations=[OperationType.GROUND],
                parallel=parallel,
                web_search=True,
                description="Verify answers with web search",
            )
        )

    # Optional: Blind spot detection
    if blind_spots:
        phases.append(
            Phase(
                name="detect_blind_spots",
                phase_type=PhaseType.DETECT,
                target_types=[NodeType.ANSWER, NodeType.SYNTHESIS],
                target_status=[EpistemicStatus.SYNTHESIZED, EpistemicStatus.GROUNDED],
                operations=[OperationType.DETECT],
                description="Discover blind spots and gaps",
            )
        )

    # Synthesis phase - targets the root QUESTION (which has EXPLORED status after decomposition)
    # The synthesize operation gathers child answers and creates a synthesis
    phases.append(
        Phase(
            name="synthesize",
            phase_type=PhaseType.SYNTHESIZE,
            target_types=[NodeType.QUESTION],
            target_status=[EpistemicStatus.EXPLORED],
            operations=[OperationType.SYNTHESIZE],
            description="Combine answers into coherent synthesis",
        )
    )

    # Build tags
    tags = ["recursive", "decomposition", "synthesis"]
    if web_grounding:
        tags.extend(["grounded", "web-search"])
    if perspectives:
        tags.append("perspectives")
    if blind_spots:
        tags.append("blind-spots")

    # Build goals - ALL_SYNTHESIZED is the primary completion goal
    # DEPTH_REACHED is used to limit decomposition, not as termination
    goals = [
        Goal(GoalType.ALL_SYNTHESIZED),
    ]
    if blind_spots:
        goals.append(Goal(GoalType.BLIND_SPOTS_FOUND))

    return Strategy(
        metadata=StrategyMetadata(
            name=name,
            version="1.0",
            description=description,
            tags=tags,
        ),
        goals=goals,
        phases=phases,
    )


def socratic_strategy() -> Strategy:
    """Build the Socratic Engine strategy.

    Flow: Question → Extract assumptions → Challenge → Deeper question → Recurse
    """
    return Strategy(
        metadata=StrategyMetadata(
            name="socratic",
            version="1.0",
            description="Transform questions through assumption-challenging",
            tags=["socratic", "assumptions", "questioning"],
        ),
        goals=[
            Goal(GoalType.SATURATION),  # Stop when no new assumptions found
        ],
        phases=[
            Phase(
                name="extract_assumptions",
                phase_type=PhaseType.EXPLORE,
                target_types=[NodeType.QUESTION],
                target_status=[EpistemicStatus.UNKNOWN],
                operations=[OperationType.EXPAND],
                description="Surface unstated assumptions",
            ),
            Phase(
                name="challenge",
                phase_type=PhaseType.CHALLENGE,
                target_types=[NodeType.ASSUMPTION],
                target_status=[EpistemicStatus.PROPOSED],
                operations=[OperationType.CHALLENGE],
                description="Challenge each assumption",
            ),
            Phase(
                name="deepen",
                phase_type=PhaseType.DECOMPOSE,
                target_types=[NodeType.QUESTION],
                target_status=[EpistemicStatus.EXPLORED],
                operations=[OperationType.TRANSFORM],
                description="Generate deeper questions from challenges",
            ),
        ],
        stall_detection=2,  # Quick termination when assumptions exhausted
    )


def perspective_strategy(
    max_depth: int = 2,
    enable_blind_spots: bool = True,
) -> Strategy:
    """Build the Perspective Expander strategy.

    Variant of recursive_research_strategy with perspectives=True. Registers
    under its own key, "perspective_expander".
    Flow: Detect domain → Expand perspectives → Decompose → Answer → [Blind Spots] → Synthesize
    """
    return recursive_research_strategy(
        max_depth=max_depth,
        perspectives=True,
        blind_spots=enable_blind_spots,
        name="perspective_expander",
        description="Multi-angle analysis with blind spot detection",
    )


def grounded_research_strategy(max_depth: int = 2, parallel: bool = True) -> Strategy:
    """Build the Grounded Research strategy.

    Variant of recursive_research_strategy with web_grounding=True. Registers
    under its own key, "grounded_research".

    Note: this variant runs a live web-search phase.
    Flow: Question → Decompose → Answer → Ground (web search) → Synthesize
    """
    return recursive_research_strategy(
        max_depth=max_depth,
        parallel=parallel,
        web_grounding=True,
        name="grounded_research",
        description="Web-verified answers (runs a live web-search phase)",
    )


# Register built-in strategies
def register_builtin_strategies() -> None:
    """Register all built-in strategies.

    Every builder must yield a distinct metadata.name. The registry is keyed on
    that name, so a collision would silently make a strategy unreachable and
    make its key resolve to whichever variant was registered last. Guard it
    here rather than discovering it at runtime.
    """
    registry = StrategyRegistry.instance()
    builtins = [
        recursive_research_strategy(),
        socratic_strategy(),
        perspective_strategy(),
        grounded_research_strategy(),
    ]

    seen: set[str] = set()
    for strategy in builtins:
        name = strategy.metadata.name
        if name in seen:
            raise ValueError(
                f"Built-in strategy name collision: {name!r} is registered twice. "
                "Each builder must pass a distinct name= to recursive_research_strategy()."
            )
        seen.add(name)
        registry.register(strategy)
