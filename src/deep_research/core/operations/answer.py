"""
ANSWER operation - directly answers a question.

This operation uses the provider's answer() method to generate
a direct response to a question (leaf node behavior).
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


class AnswerOperation(BaseOperation):
    """Directly answers a question."""

    @property
    def spec(self) -> OperationSpec:
        return OperationSpec(
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
        )

    async def _execute_impl(
        self,
        graph: KnowledgeGraph,
        nodes: list[Node],
        context: dict[str, Any],
    ) -> OperationResult:
        """Execute answering on target nodes."""
        model = get_model_from_context(context)
        provider = get_provider_from_context(context)

        created_nodes: list[Node] = []
        raw_outputs: list[str] = []

        for node in nodes:
            # Call provider to answer the question
            raw_output = await provider.answer(node.content, model.model)
            raw_outputs.append(raw_output)

            # Create answer node
            answer = Node(
                node_type=NodeType.ANSWER,
                status=EpistemicStatus.SYNTHESIZED,
                content=raw_output,
                depth=node.depth,
                created_by=f"answer:{model}",
                model=str(model),
            )

            # Link answer to question
            answer.add_edge(node.id, NodeRelation.PARENT)
            node.add_edge(answer.id, NodeRelation.TRANSFORMS_TO)

            created_nodes.append(answer)

            # Store in node metadata
            node.metadata["answer"] = raw_output

        return OperationResult(
            success=True,
            created_nodes=created_nodes,
            modified_nodes=[n.id for n in nodes],
            raw_output="\n---\n".join(raw_outputs),
            metadata={"answers_generated": len(created_nodes)},
        )
