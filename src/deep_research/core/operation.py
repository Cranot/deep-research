"""
Operations for the MasterChef architecture.

Operations are epistemic transitions that transform nodes. Each operation:
- Takes input nodes of specific types
- Produces output nodes of specific types
- Requires specific epistemic preconditions
- Results in specific epistemic postconditions

Operations are the "verbs" of research - they DO things to knowledge.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, runtime_checkable

from .graph import KnowledgeGraph
from .node import EpistemicStatus, Node, NodeType


class OperationType(str, Enum):
    """Types of research operations.

    Each operation type represents a different epistemic transition.
    """

    # Decomposition operations (Unknown → Explored)
    DECOMPOSE = "decompose"  # Break question into sub-questions
    EXPAND = "expand"  # Discover angles/perspectives

    # Exploration operations (Unknown → Explored)
    EXPLORE = "explore"  # Investigate a question
    ANSWER = "answer"  # Directly answer a question

    # Validation operations (Explored → Validated/Refuted)
    CHALLENGE = "challenge"  # Question assumptions
    VALIDATE = "validate"  # Check against evidence
    CRITIQUE = "critique"  # Apply critical analysis

    # Synthesis operations (Multiple → Synthesized)
    SYNTHESIZE = "synthesize"  # Combine findings
    MERGE = "merge"  # Merge multiple answers

    # Discovery operations (Any → Discovery nodes)
    DETECT = "detect"  # Find tensions, blind spots
    DISCOVER = "discover"  # Generate insights

    # Ground operations (Proposed → Grounded)
    GROUND = "ground"  # Connect to evidence/sources

    # Selection operations (Multiple → Selected)
    SELECT = "select"  # Choose best from options
    PRIORITIZE = "prioritize"  # Order by importance

    # Transformation operations (Type → Different Type)
    TRANSFORM = "transform"  # Convert node type
    INVERT = "invert"  # Flip perspective (success → failure)


@dataclass
class OperationSpec:
    """Specification for an operation's requirements and effects."""

    operation_type: OperationType
    input_types: list[NodeType]  # What node types it accepts
    output_types: list[NodeType]  # What node types it produces
    required_status: list[EpistemicStatus]  # What status inputs must have
    resulting_status: EpistemicStatus  # What status outputs will have
    requires_model: bool = True  # Whether LLM call is needed
    can_spawn: bool = False  # Whether it can create child nodes


@dataclass
class OperationResult:
    """Result of executing an operation."""

    success: bool
    created_nodes: list[Node] = field(default_factory=list)
    modified_nodes: list[str] = field(default_factory=list)  # Node IDs
    raw_output: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    @classmethod
    def failed(cls, error: str) -> "OperationResult":
        """Create a failed result."""
        return cls(success=False, error=error)


@runtime_checkable
class Operation(Protocol):
    """Protocol for research operations.

    Operations implement specific epistemic transitions. They:
    - Take a graph and target nodes
    - Perform some transformation (often involving LLM calls)
    - Return results with new/modified nodes
    """

    @property
    def spec(self) -> OperationSpec:
        """Get the operation specification."""
        ...

    async def execute(
        self, graph: KnowledgeGraph, target_ids: list[str], context: dict[str, Any]
    ) -> OperationResult:
        """Execute the operation on target nodes.

        Args:
            graph: The knowledge graph
            target_ids: IDs of nodes to operate on
            context: Additional context (model, config, etc.)

        Returns:
            OperationResult with created/modified nodes
        """
        ...


class BaseOperation(ABC):
    """Base class for operation implementations.

    Provides common functionality for validation and execution.
    """

    @property
    @abstractmethod
    def spec(self) -> OperationSpec:
        """Get the operation specification."""
        ...

    def validate_inputs(self, graph: KnowledgeGraph, target_ids: list[str]) -> list[str]:
        """Validate that inputs meet requirements.

        Returns list of validation errors (empty if valid).
        """
        errors = []

        for target_id in target_ids:
            node = graph.get(target_id)
            if not node:
                errors.append(f"Node {target_id} not found")
                continue

            if node.node_type not in self.spec.input_types:
                errors.append(
                    f"Node {target_id} has type {node.node_type.value}, "
                    f"expected one of {[t.value for t in self.spec.input_types]}"
                )

            if self.spec.required_status and node.status not in self.spec.required_status:
                errors.append(
                    f"Node {target_id} has status {node.status.value}, "
                    f"expected one of {[s.value for s in self.spec.required_status]}"
                )

        return errors

    @abstractmethod
    async def _execute_impl(
        self, graph: KnowledgeGraph, nodes: list[Node], context: dict[str, Any]
    ) -> OperationResult:
        """Implementation of the operation logic."""
        ...

    async def execute(
        self, graph: KnowledgeGraph, target_ids: list[str], context: dict[str, Any]
    ) -> OperationResult:
        """Execute the operation with validation."""
        # Validate inputs
        errors = self.validate_inputs(graph, target_ids)
        if errors:
            return OperationResult.failed("; ".join(errors))

        # Get target nodes
        nodes = [graph[tid] for tid in target_ids]

        # Update status to show we're working
        for node in nodes:
            node.status = EpistemicStatus.EXPLORING

        # Execute implementation
        try:
            result = await self._execute_impl(graph, nodes, context)

            # Update status on success
            if result.success:
                for node in nodes:
                    node.status = self.spec.resulting_status

            return result

        except Exception as e:
            return OperationResult.failed(str(e))


# =============================================================================
# Operation Registry
# =============================================================================


class OperationRegistry:
    """Registry for operation implementations.

    Operations can be registered by type and retrieved for execution.
    """

    _instance: "OperationRegistry | None" = None
    _operations: dict[OperationType, type[BaseOperation]]

    def __new__(cls) -> "OperationRegistry":
        """Singleton pattern for global registry."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._operations = {}
        return cls._instance

    def register(self, operation_type: OperationType, operation_class: type[BaseOperation]) -> None:
        """Register an operation implementation."""
        self._operations[operation_type] = operation_class

    def get(self, operation_type: OperationType) -> type[BaseOperation] | None:
        """Get the operation class for a type."""
        return self._operations.get(operation_type)

    def create(self, operation_type: OperationType, **kwargs: Any) -> BaseOperation | None:
        """Create an instance of an operation."""
        op_class = self.get(operation_type)
        if op_class:
            return op_class(**kwargs)
        return None

    def available(self) -> list[OperationType]:
        """Get list of available operation types."""
        return list(self._operations.keys())

    @classmethod
    def instance(cls) -> "OperationRegistry":
        """Get the singleton instance."""
        return cls()


def register_operation(operation_type: OperationType):
    """Decorator to register an operation class."""

    def decorator(cls: type[BaseOperation]) -> type[BaseOperation]:
        OperationRegistry.instance().register(operation_type, cls)
        return cls

    return decorator


# =============================================================================
# Standard Operation Specifications
# =============================================================================

# These define the contracts for each operation type

OPERATION_SPECS = {
    OperationType.DECOMPOSE: OperationSpec(
        operation_type=OperationType.DECOMPOSE,
        input_types=[NodeType.QUESTION],
        output_types=[NodeType.SUB_QUESTION],
        required_status=[EpistemicStatus.UNKNOWN, EpistemicStatus.PROPOSED],
        resulting_status=EpistemicStatus.EXPLORED,
        requires_model=True,
        can_spawn=True,
    ),
    OperationType.EXPAND: OperationSpec(
        operation_type=OperationType.EXPAND,
        input_types=[NodeType.QUESTION],
        output_types=[NodeType.PERSPECTIVE, NodeType.ASSUMPTION],
        required_status=[
            EpistemicStatus.UNKNOWN,
            EpistemicStatus.PROPOSED,
            EpistemicStatus.EXPLORED,
        ],
        resulting_status=EpistemicStatus.EXPLORED,
        requires_model=True,
        can_spawn=True,
    ),
    OperationType.ANSWER: OperationSpec(
        operation_type=OperationType.ANSWER,
        input_types=[NodeType.QUESTION, NodeType.SUB_QUESTION],
        output_types=[NodeType.ANSWER],
        required_status=[
            EpistemicStatus.UNKNOWN,
            EpistemicStatus.PROPOSED,
            EpistemicStatus.EXPLORED,
        ],
        resulting_status=EpistemicStatus.SYNTHESIZED,
        requires_model=True,
        can_spawn=False,
    ),
    OperationType.CHALLENGE: OperationSpec(
        operation_type=OperationType.CHALLENGE,
        input_types=[NodeType.ASSUMPTION, NodeType.CLAIM],
        output_types=[NodeType.COUNTERPOINT, NodeType.INSIGHT],
        required_status=[EpistemicStatus.UNKNOWN, EpistemicStatus.PROPOSED],
        resulting_status=EpistemicStatus.CHALLENGED,
        requires_model=True,
        can_spawn=True,
    ),
    OperationType.SYNTHESIZE: OperationSpec(
        operation_type=OperationType.SYNTHESIZE,
        input_types=[NodeType.ANSWER, NodeType.INSIGHT, NodeType.CLAIM],
        output_types=[NodeType.SYNTHESIS],
        required_status=[
            EpistemicStatus.EXPLORED,
            EpistemicStatus.VALIDATED,
            EpistemicStatus.CHALLENGED,
        ],
        resulting_status=EpistemicStatus.SYNTHESIZED,
        requires_model=True,
        can_spawn=False,
    ),
    OperationType.DETECT: OperationSpec(
        operation_type=OperationType.DETECT,
        input_types=[NodeType.QUESTION, NodeType.SYNTHESIS],
        output_types=[NodeType.BLIND_SPOT, NodeType.TENSION],
        required_status=[EpistemicStatus.EXPLORED, EpistemicStatus.SYNTHESIZED],
        resulting_status=EpistemicStatus.EXPLORED,
        requires_model=True,
        can_spawn=True,
    ),
    OperationType.INVERT: OperationSpec(
        operation_type=OperationType.INVERT,
        input_types=[NodeType.QUESTION],
        output_types=[NodeType.QUESTION, NodeType.FAILURE_MODE],
        required_status=[EpistemicStatus.UNKNOWN, EpistemicStatus.PROPOSED],
        resulting_status=EpistemicStatus.EXPLORED,
        requires_model=True,
        can_spawn=True,
    ),
}


def get_spec(operation_type: OperationType) -> OperationSpec | None:
    """Get the standard specification for an operation type."""
    return OPERATION_SPECS.get(operation_type)
