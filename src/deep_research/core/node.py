"""
Core node types for the MasterChef architecture.

Nodes are typed content units that represent different epistemic objects
in a research graph. Each node has:
- A type (what kind of content)
- An epistemic status (how well we know it)
- Content (the actual text/data)
- Relationships to other nodes
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class NodeType(str, Enum):
    """Types of content nodes in a research graph.

    Each type represents a different epistemic object that can be
    created, transformed, or consumed by research operations.
    """

    # Primary question types
    QUESTION = "question"  # A research question to explore
    SUB_QUESTION = "sub_question"  # A decomposed sub-question

    # Epistemic content types
    ASSUMPTION = "assumption"  # An unstated premise to challenge
    PERSPECTIVE = "perspective"  # A lens or viewpoint to apply
    CLAIM = "claim"  # An assertion to validate
    EVIDENCE = "evidence"  # Support for a claim
    COUNTERPOINT = "counterpoint"  # Opposition to a claim

    # Discovery types
    TENSION = "tension"  # A productive conflict between ideas
    INSIGHT = "insight"  # A novel understanding
    BLIND_SPOT = "blind_spot"  # A discovered gap in thinking
    FAILURE_MODE = "failure_mode"  # A way something can fail

    # Synthesis types
    SYNTHESIS = "synthesis"  # An integrated understanding
    ANSWER = "answer"  # A direct response to a question

    # Meta types
    DOMAIN = "domain"  # Detected problem domain
    STRATEGY = "strategy"  # A research approach to apply


class EpistemicStatus(str, Enum):
    """Epistemic state of a node - how well do we know this?

    Nodes progress through epistemic states as research operations
    transform them. The status determines what operations can be
    applied next.
    """

    # Initial states
    UNKNOWN = "unknown"  # Not yet explored
    PROPOSED = "proposed"  # Suggested but not examined

    # Active research states
    EXPLORING = "exploring"  # Currently being investigated
    EXPLORED = "explored"  # Initial investigation complete

    # Validation states
    CHALLENGED = "challenged"  # Subjected to critical examination
    VALIDATED = "validated"  # Passed validation checks
    REFUTED = "refuted"  # Failed validation

    # Integration states
    SYNTHESIZED = "synthesized"  # Integrated with other findings
    GROUNDED = "grounded"  # Connected to concrete evidence

    # Terminal states
    EXHAUSTED = "exhausted"  # No more productive exploration possible
    DORMANT = "dormant"  # Paused, may revive with new tools/context


class NodeRelation(str, Enum):
    """Types of relationships between nodes."""

    # Structural relations
    PARENT = "parent"  # This node was derived from parent
    CHILD = "child"  # This node spawned child
    SIBLING = "sibling"  # Same-level related nodes

    # Epistemic relations
    SUPPORTS = "supports"  # Evidence/argument supporting
    CONTRADICTS = "contradicts"  # Evidence/argument opposing
    CHALLENGES = "challenges"  # Questions the validity of
    VALIDATES = "validates"  # Confirms the validity of

    # Transformation relations
    TRANSFORMS_TO = "transforms_to"  # Became (e.g., question -> answer)
    SYNTHESIZES = "synthesizes"  # Combined from multiple sources
    DECOMPOSES = "decomposes"  # Broke down from single source

    # Perspective relations
    VIEWS_AS = "views_as"  # Perspective applied to content
    REVEALS = "reveals"  # Discovery relationship


@dataclass
class NodeEdge:
    """An edge connecting two nodes with a typed relationship."""

    target_id: str
    relation: NodeRelation
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Node:
    """A typed content unit in the research graph.

    Nodes are the atomic units of research. They hold content, track
    epistemic state, and maintain relationships to other nodes.
    """

    # Identity
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    # Type and status
    node_type: NodeType = NodeType.QUESTION
    status: EpistemicStatus = EpistemicStatus.UNKNOWN

    # Content
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    # Relationships
    edges: list[NodeEdge] = field(default_factory=list)

    # Provenance
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str | None = None  # Operation or model that created this
    depth: int = 0  # Distance from root question

    # Model assignment
    model: str | None = None  # Model assigned to process this node

    def add_edge(self, target_id: str, relation: NodeRelation, **metadata: Any) -> None:
        """Add an edge to another node."""
        self.edges.append(NodeEdge(target_id=target_id, relation=relation, metadata=metadata))

    def get_edges(self, relation: NodeRelation | None = None) -> list[NodeEdge]:
        """Get edges, optionally filtered by relation type."""
        if relation is None:
            return self.edges
        return [e for e in self.edges if e.relation == relation]

    def get_related_ids(self, relation: NodeRelation) -> list[str]:
        """Get IDs of nodes with a specific relation."""
        return [e.target_id for e in self.edges if e.relation == relation]

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for JSON persistence."""
        return {
            "id": self.id,
            "node_type": self.node_type.value,
            "status": self.status.value,
            "content": self.content,
            "metadata": self.metadata,
            "edges": [
                {"target_id": e.target_id, "relation": e.relation.value, "metadata": e.metadata}
                for e in self.edges
            ],
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "depth": self.depth,
            "model": self.model,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Node":
        """Deserialize from dictionary."""
        edges = [
            NodeEdge(
                target_id=e["target_id"],
                relation=NodeRelation(e["relation"]),
                metadata=e.get("metadata", {}),
            )
            for e in data.get("edges", [])
        ]

        return cls(
            id=data["id"],
            node_type=NodeType(data["node_type"]),
            status=EpistemicStatus(data["status"]),
            content=data["content"],
            metadata=data.get("metadata", {}),
            edges=edges,
            created_at=datetime.fromisoformat(data["created_at"]),
            created_by=data.get("created_by"),
            depth=data.get("depth", 0),
            model=data.get("model"),
        )

    def __repr__(self) -> str:
        content_preview = self.content[:40] + "..." if len(self.content) > 40 else self.content
        return f"Node({self.id}, {self.node_type.value}, {self.status.value}, '{content_preview}')"


# Factory functions for common node types
def question(content: str, depth: int = 0, **metadata: Any) -> Node:
    """Create a question node."""
    return Node(
        node_type=NodeType.QUESTION,
        status=EpistemicStatus.UNKNOWN,
        content=content,
        depth=depth,
        metadata=metadata,
    )


def perspective(name: str, description: str, **metadata: Any) -> Node:
    """Create a perspective node."""
    return Node(
        node_type=NodeType.PERSPECTIVE,
        status=EpistemicStatus.PROPOSED,
        content=description,
        metadata={"name": name, **metadata},
    )


def assumption(content: str, **metadata: Any) -> Node:
    """Create an assumption node."""
    return Node(
        node_type=NodeType.ASSUMPTION,
        status=EpistemicStatus.UNKNOWN,
        content=content,
        metadata=metadata,
    )


def insight(content: str, sources: list[str] | None = None, **metadata: Any) -> Node:
    """Create an insight node."""
    return Node(
        node_type=NodeType.INSIGHT,
        status=EpistemicStatus.PROPOSED,
        content=content,
        metadata={"sources": sources or [], **metadata},
    )


def synthesis(content: str, source_ids: list[str], **metadata: Any) -> Node:
    """Create a synthesis node with links to its sources."""
    node = Node(
        node_type=NodeType.SYNTHESIS,
        status=EpistemicStatus.SYNTHESIZED,
        content=content,
        metadata=metadata,
    )
    for source_id in source_ids:
        node.add_edge(source_id, NodeRelation.SYNTHESIZES)
    return node
