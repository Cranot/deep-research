"""
Knowledge graph for the MasterChef architecture.

The KnowledgeGraph holds all nodes and provides:
- Node storage and retrieval
- Relationship traversal
- Lazy persistence (checkpoint at phase boundaries)
- Query operations for common patterns
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from .node import EpistemicStatus, Node, NodeRelation, NodeType


@dataclass
class GraphMetadata:
    """Metadata about the knowledge graph."""

    question: str  # Root research question
    created_at: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)
    strategy: str | None = None  # Strategy being executed
    current_phase: str | None = None  # Current phase in strategy
    checkpoint_count: int = 0  # Number of checkpoints saved
    total_nodes: int = 0
    completed_nodes: int = 0


class KnowledgeGraph:
    """A graph of research nodes with persistence support.

    The graph provides:
    - O(1) node access by ID
    - Efficient relationship traversal
    - Lazy checkpointing for resume capability
    - Query operations for research patterns
    """

    def __init__(self, question: str, output_dir: Path | None = None, strategy: str | None = None):
        """Initialize a new knowledge graph.

        Args:
            question: The root research question
            output_dir: Directory for persistence (None = no persistence)
            strategy: Name of the strategy being executed
        """
        self._nodes: dict[str, Node] = {}
        self._root_id: str | None = None
        self.output_dir = output_dir
        self.metadata = GraphMetadata(question=question, strategy=strategy)

    @property
    def root(self) -> Node | None:
        """Get the root question node."""
        if self._root_id:
            return self._nodes.get(self._root_id)
        return None

    def add(self, node: Node) -> str:
        """Add a node to the graph.

        Returns the node ID. If this is the first node, it becomes the root.
        """
        self._nodes[node.id] = node
        if self._root_id is None:
            self._root_id = node.id
        self.metadata.total_nodes = len(self._nodes)
        self.metadata.last_modified = datetime.now()
        return node.id

    def get(self, node_id: str) -> Node | None:
        """Get a node by ID."""
        return self._nodes.get(node_id)

    def __getitem__(self, node_id: str) -> Node:
        """Get a node by ID, raising KeyError if not found."""
        return self._nodes[node_id]

    def __contains__(self, node_id: str) -> bool:
        """Check if a node exists."""
        return node_id in self._nodes

    def __len__(self) -> int:
        """Get the number of nodes."""
        return len(self._nodes)

    def __iter__(self) -> Iterator[Node]:
        """Iterate over all nodes."""
        return iter(self._nodes.values())

    def remove(self, node_id: str) -> Node | None:
        """Remove a node by ID. Returns the removed node or None."""
        return self._nodes.pop(node_id, None)

    # =========================================================================
    # Query Operations
    # =========================================================================

    def by_type(self, node_type: NodeType) -> list[Node]:
        """Get all nodes of a specific type."""
        return [n for n in self._nodes.values() if n.node_type == node_type]

    def by_status(self, status: EpistemicStatus) -> list[Node]:
        """Get all nodes with a specific epistemic status."""
        return [n for n in self._nodes.values() if n.status == status]

    def by_depth(self, depth: int) -> list[Node]:
        """Get all nodes at a specific depth."""
        return [n for n in self._nodes.values() if n.depth == depth]

    def pending(self) -> list[Node]:
        """Get nodes ready for processing (UNKNOWN or PROPOSED)."""
        return [
            n
            for n in self._nodes.values()
            if n.status in (EpistemicStatus.UNKNOWN, EpistemicStatus.PROPOSED)
        ]

    def exploring(self) -> list[Node]:
        """Get nodes currently being explored."""
        return self.by_status(EpistemicStatus.EXPLORING)

    def terminal(self) -> list[Node]:
        """Get nodes in terminal states (EXHAUSTED, DORMANT, REFUTED)."""
        return [
            n
            for n in self._nodes.values()
            if n.status
            in (EpistemicStatus.EXHAUSTED, EpistemicStatus.DORMANT, EpistemicStatus.REFUTED)
        ]

    def leaves(self) -> list[Node]:
        """Get leaf nodes (no children)."""
        return [n for n in self._nodes.values() if not n.get_edges(NodeRelation.CHILD)]

    def roots(self) -> list[Node]:
        """Get root nodes (no parents)."""
        return [n for n in self._nodes.values() if not n.get_edges(NodeRelation.PARENT)]

    def children_of(self, node_id: str) -> list[Node]:
        """Get all children of a node."""
        node = self.get(node_id)
        if not node:
            return []
        child_ids = node.get_related_ids(NodeRelation.CHILD)
        return [self._nodes[cid] for cid in child_ids if cid in self._nodes]

    def parents_of(self, node_id: str) -> list[Node]:
        """Get all parents of a node."""
        node = self.get(node_id)
        if not node:
            return []
        parent_ids = node.get_related_ids(NodeRelation.PARENT)
        return [self._nodes[pid] for pid in parent_ids if pid in self._nodes]

    def descendants(self, node_id: str) -> list[Node]:
        """Get all descendants (children, grandchildren, etc.)."""
        result = []
        queue = self.children_of(node_id)
        visited = set()

        while queue:
            node = queue.pop(0)
            if node.id in visited:
                continue
            visited.add(node.id)
            result.append(node)
            queue.extend(self.children_of(node.id))

        return result

    def ancestors(self, node_id: str) -> list[Node]:
        """Get all ancestors (parents, grandparents, etc.)."""
        result = []
        queue = self.parents_of(node_id)
        visited = set()

        while queue:
            node = queue.pop(0)
            if node.id in visited:
                continue
            visited.add(node.id)
            result.append(node)
            queue.extend(self.parents_of(node.id))

        return result

    def related(self, node_id: str, relation: NodeRelation) -> list[Node]:
        """Get nodes related to a node by a specific relation."""
        node = self.get(node_id)
        if not node:
            return []
        related_ids = node.get_related_ids(relation)
        return [self._nodes[rid] for rid in related_ids if rid in self._nodes]

    # =========================================================================
    # Graph Mutations
    # =========================================================================

    def link(
        self,
        source_id: str,
        target_id: str,
        relation: NodeRelation,
        bidirectional: bool = False,
        **metadata: Any,
    ) -> None:
        """Create a relationship between nodes.

        Args:
            source_id: Source node ID
            target_id: Target node ID
            relation: Type of relationship
            bidirectional: If True, also create reverse edge
            **metadata: Additional edge metadata
        """
        source = self.get(source_id)
        if source:
            source.add_edge(target_id, relation, **metadata)

        if bidirectional:
            target = self.get(target_id)
            inverse = self._inverse_relation(relation)
            if target and inverse:
                target.add_edge(source_id, inverse, **metadata)

    @staticmethod
    def _inverse_relation(relation: NodeRelation) -> NodeRelation | None:
        """Get the inverse of a relation."""
        inverses = {
            NodeRelation.PARENT: NodeRelation.CHILD,
            NodeRelation.CHILD: NodeRelation.PARENT,
            NodeRelation.SUPPORTS: NodeRelation.SUPPORTS,  # Symmetric-ish
            NodeRelation.CONTRADICTS: NodeRelation.CONTRADICTS,
            NodeRelation.CHALLENGES: NodeRelation.CHALLENGES,
            NodeRelation.VALIDATES: NodeRelation.VALIDATES,
        }
        return inverses.get(relation)

    def spawn_child(
        self, parent_id: str, child_type: NodeType, content: str, **metadata: Any
    ) -> Node:
        """Create a child node linked to a parent.

        Automatically sets up parent-child relationships.
        """
        parent = self.get(parent_id)
        if not parent:
            raise ValueError(f"Parent node {parent_id} not found")

        child = Node(
            node_type=child_type, content=content, depth=parent.depth + 1, metadata=metadata
        )

        self.add(child)
        self.link(parent_id, child.id, NodeRelation.CHILD, bidirectional=True)

        return child

    def update_status(self, node_id: str, status: EpistemicStatus) -> None:
        """Update a node's epistemic status."""
        node = self.get(node_id)
        if node:
            node.status = status
            if status in (
                EpistemicStatus.SYNTHESIZED,
                EpistemicStatus.VALIDATED,
                EpistemicStatus.GROUNDED,
            ):
                self.metadata.completed_nodes += 1
            self.metadata.last_modified = datetime.now()

    # =========================================================================
    # Persistence
    # =========================================================================

    def checkpoint(self, phase: str | None = None) -> Path | None:
        """Save the current graph state to disk.

        Args:
            phase: Optional phase name to include in checkpoint filename

        Returns:
            Path to the saved checkpoint, or None if no output_dir
        """
        if not self.output_dir:
            return None

        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Update metadata
        if phase:
            self.metadata.current_phase = phase
        self.metadata.checkpoint_count += 1

        # Build checkpoint data
        data = {
            "metadata": {
                "question": self.metadata.question,
                "created_at": self.metadata.created_at.isoformat(),
                "last_modified": self.metadata.last_modified.isoformat(),
                "strategy": self.metadata.strategy,
                "current_phase": self.metadata.current_phase,
                "checkpoint_count": self.metadata.checkpoint_count,
                "total_nodes": len(self._nodes),
                "completed_nodes": self.metadata.completed_nodes,
            },
            "root_id": self._root_id,
            "nodes": {node_id: node.to_dict() for node_id, node in self._nodes.items()},
        }

        # Save as human-readable JSON
        checkpoint_path = self.output_dir / "graph.json"
        with open(checkpoint_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return checkpoint_path

    @classmethod
    def load(cls, checkpoint_path: Path) -> "KnowledgeGraph":
        """Load a graph from a checkpoint file."""
        with open(checkpoint_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        meta = data["metadata"]
        graph = cls(
            question=meta["question"],
            output_dir=checkpoint_path.parent,
            strategy=meta.get("strategy"),
        )

        # Restore metadata
        graph.metadata.created_at = datetime.fromisoformat(meta["created_at"])
        graph.metadata.last_modified = datetime.fromisoformat(meta["last_modified"])
        graph.metadata.current_phase = meta.get("current_phase")
        graph.metadata.checkpoint_count = meta.get("checkpoint_count", 0)
        graph.metadata.completed_nodes = meta.get("completed_nodes", 0)

        # Restore nodes
        for node_id, node_data in data.get("nodes", {}).items():
            node = Node.from_dict(node_data)
            graph._nodes[node_id] = node

        graph._root_id = data.get("root_id")

        return graph

    # =========================================================================
    # Stats & Visualization
    # =========================================================================

    def stats(self) -> dict[str, Any]:
        """Get statistics about the graph."""
        type_counts = {}
        status_counts = {}
        depth_counts = {}

        for node in self._nodes.values():
            type_counts[node.node_type.value] = type_counts.get(node.node_type.value, 0) + 1
            status_counts[node.status.value] = status_counts.get(node.status.value, 0) + 1
            depth_counts[node.depth] = depth_counts.get(node.depth, 0) + 1

        return {
            "total_nodes": len(self._nodes),
            "completed_nodes": self.metadata.completed_nodes,
            "by_type": type_counts,
            "by_status": status_counts,
            "by_depth": depth_counts,
            "max_depth": max(depth_counts.keys()) if depth_counts else 0,
        }

    def to_tree_string(self, node_id: str | None = None, indent: int = 0) -> str:
        """Generate a tree visualization string."""
        if node_id is None:
            node_id = self._root_id
        if not node_id:
            return "(empty graph)"

        node = self.get(node_id)
        if not node:
            return "(node not found)"

        prefix = "  " * indent
        content_preview = node.content[:50] + "..." if len(node.content) > 50 else node.content
        lines = [f"{prefix}[{node.node_type.value}:{node.status.value}] {content_preview}"]

        for child in self.children_of(node_id):
            lines.append(self.to_tree_string(child.id, indent + 1))

        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"KnowledgeGraph(nodes={len(self._nodes)}, root='{self.metadata.question[:30]}...')"
