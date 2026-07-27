"""
DECOMPOSE operation - breaks questions into sub-questions.

This operation uses the provider's explore() method to identify
research angles, then parses the Q: lines into child nodes.
"""

from typing import Any

from ..graph import KnowledgeGraph
from ..node import EpistemicStatus, Node, NodeRelation, NodeType
from ..operation import (
    BaseOperation,
    OperationResult,
    OperationSpec,
    OperationType,
)
from .base import get_model_from_context, get_provider_from_context


class DecomposeOperation(BaseOperation):
    """Breaks a question into sub-questions through exploration."""

    @property
    def spec(self) -> OperationSpec:
        return OperationSpec(
            operation_type=OperationType.DECOMPOSE,
            input_types=[NodeType.QUESTION, NodeType.SUB_QUESTION],
            output_types=[NodeType.SUB_QUESTION],
            required_status=[
                EpistemicStatus.UNKNOWN,
                EpistemicStatus.PROPOSED,
                EpistemicStatus.EXPLORED,
            ],
            resulting_status=EpistemicStatus.EXPLORED,
            requires_model=True,
            can_spawn=True,
        )

    async def _execute_impl(
        self,
        graph: KnowledgeGraph,
        nodes: list[Node],
        context: dict[str, Any],
    ) -> OperationResult:
        """Execute decomposition on target nodes."""
        model = get_model_from_context(context)
        provider = get_provider_from_context(context)

        created_nodes: list[Node] = []
        raw_outputs: list[str] = []

        for node in nodes:
            # Call provider to explore the question
            raw_output = await provider.explore(node.content, model.model)
            raw_outputs.append(raw_output)

            # Parse Q: lines from output
            questions = self._parse_questions(raw_output)

            # Create child nodes for each question
            for q_text in questions:
                child = Node(
                    node_type=NodeType.SUB_QUESTION,
                    status=EpistemicStatus.UNKNOWN,
                    content=q_text,
                    depth=node.depth + 1,
                    created_by=f"decompose:{model}",
                    model=str(model),
                )

                # Link to parent
                child.add_edge(node.id, NodeRelation.PARENT)
                node.add_edge(child.id, NodeRelation.CHILD)

                created_nodes.append(child)

            # Store exploration output in node metadata
            node.metadata["exploration_output"] = raw_output
            node.metadata["child_count"] = len(questions)

        return OperationResult(
            success=True,
            created_nodes=created_nodes,
            modified_nodes=[n.id for n in nodes],
            raw_output="\n---\n".join(raw_outputs),
            metadata={"questions_found": len(created_nodes)},
        )

    @staticmethod
    def _parse_questions(raw_output: str) -> list[str]:
        """Parse Q: lines from exploration output."""
        questions = []
        for line in raw_output.strip().split("\n"):
            line = line.strip()
            if line.startswith("Q: "):
                q_text = line[3:].strip()
                if q_text:
                    questions.append(q_text)
        return questions
