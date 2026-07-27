"""
SYNTHESIZE operation - combines findings into coherent understanding.

This operation gathers child answers/insights and synthesizes them
into a unified response using the provider's synthesize() method.
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


class SynthesizeOperation(BaseOperation):
    """Synthesizes multiple findings into coherent understanding."""

    @property
    def spec(self) -> OperationSpec:
        return OperationSpec(
            operation_type=OperationType.SYNTHESIZE,
            input_types=[NodeType.QUESTION, NodeType.SUB_QUESTION],
            output_types=[NodeType.SYNTHESIS],
            required_status=[
                EpistemicStatus.EXPLORED,
                EpistemicStatus.VALIDATED,
                EpistemicStatus.CHALLENGED,
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
        """Execute synthesis on target nodes."""
        model = get_model_from_context(context)
        provider = get_provider_from_context(context)

        created_nodes: list[Node] = []

        for node in nodes:
            # Gather all child answers/insights
            findings = self._gather_findings(graph, node)

            if not findings:
                # No findings to synthesize - mark as complete anyway
                node.status = EpistemicStatus.SYNTHESIZED
                continue

            # Format findings for synthesis
            results_text = self._format_findings(findings)

            # Call provider to synthesize
            raw_output = await provider.synthesize(
                node.content,
                results_text,
                model.model,
            )

            # Create synthesis node
            synthesis = Node(
                node_type=NodeType.SYNTHESIS,
                status=EpistemicStatus.SYNTHESIZED,
                content=raw_output,
                depth=node.depth,
                created_by=f"synthesize:{model}",
                model=str(model),
                metadata={
                    "source_count": len(findings),
                    "original_question": node.content,
                },
            )

            # Link synthesis to source nodes
            synthesis.add_edge(node.id, NodeRelation.PARENT)
            for finding in findings:
                synthesis.add_edge(finding.id, NodeRelation.SYNTHESIZES)

            node.add_edge(synthesis.id, NodeRelation.TRANSFORMS_TO)

            created_nodes.append(synthesis)

        return OperationResult(
            success=True,
            created_nodes=created_nodes,
            modified_nodes=[n.id for n in nodes],
            metadata={"syntheses_created": len(created_nodes)},
        )

    def _gather_findings(self, graph: KnowledgeGraph, node: Node) -> list[Node]:
        """Gather all synthesizable findings from children."""
        findings: list[Node] = []

        # Get direct children
        children = graph.children_of(node.id)

        for child in children:
            # If child has an answer, use that
            answers = graph.related(child.id, NodeRelation.TRANSFORMS_TO)
            for answer in answers:
                if answer.node_type == NodeType.ANSWER:
                    findings.append(answer)
                    break
            else:
                # If child is a synthesis or insight, use it directly
                if child.node_type in (NodeType.SYNTHESIS, NodeType.INSIGHT, NodeType.ANSWER):
                    findings.append(child)
                # If child has been explored, check for its synthesis
                elif child.status == EpistemicStatus.SYNTHESIZED:
                    child_synth = graph.related(child.id, NodeRelation.TRANSFORMS_TO)
                    findings.extend([s for s in child_synth if s.node_type == NodeType.SYNTHESIS])

        return findings

    def _format_findings(self, findings: list[Node]) -> str:
        """Format findings for the synthesis prompt."""
        parts = []
        for i, finding in enumerate(findings, 1):
            # Get source question if available
            source = ""
            parents = finding.get_related_ids(NodeRelation.PARENT)
            if parents:
                source = " (from: ...)"  # Could look up parent content

            parts.append(f"### Finding {i}{source}\n\n{finding.content}")

        return "\n\n---\n\n".join(parts)
