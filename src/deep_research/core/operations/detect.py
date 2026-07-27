"""
DETECT operation - discovers blind spots, tensions, and hidden angles.

This operation analyzes existing perspectives or syntheses to find
what's missing or in tension.
"""

from typing import Any

from ...providers.base import ProviderOptions
from ..graph import KnowledgeGraph
from ..node import EpistemicStatus, Node, NodeRelation, NodeType
from ..operation import (
    BaseOperation,
    OperationResult,
    OperationSpec,
    OperationType,
)
from .base import get_model_from_context, get_provider_from_context

BLIND_SPOT_PROMPT = """You are analyzing research perspectives to identify blind spots and gaps.

Given the following perspectives that have been identified for the question:

{PERSPECTIVES}

Your task is to identify what perspectives are MISSING. Think about:
- What viewpoints are not represented?
- What assumptions are shared by all perspectives (and therefore not questioned)?
- What stakeholders or domains are overlooked?
- What methodologies or lenses are absent?

For each blind spot you identify, output a line starting with "BLIND_SPOT: " followed by:
- A name for the missing perspective
- A brief description of what it would examine

Be thorough. Find at least 3 blind spots if they exist."""


TENSION_PROMPT = """You are analyzing research findings to identify tensions and contradictions.

Given the following findings:

{FINDINGS}

Identify any tensions, contradictions, or tradeoffs between these findings.

For each tension, output a line starting with "TENSION: " followed by:
- A brief description of the conflict
- Which findings are in tension
- Why this tension matters

Look for:
- Direct contradictions
- Implicit assumptions that conflict
- Tradeoffs where optimizing one thing hurts another
- Perspectives that cannot both be fully correct

Be thorough. Surface the non-obvious tensions."""


class DetectOperation(BaseOperation):
    """Detects blind spots, tensions, and hidden angles."""

    @property
    def spec(self) -> OperationSpec:
        return OperationSpec(
            operation_type=OperationType.DETECT,
            input_types=[NodeType.QUESTION, NodeType.SYNTHESIS, NodeType.PERSPECTIVE],
            output_types=[NodeType.BLIND_SPOT, NodeType.TENSION],
            required_status=[
                EpistemicStatus.UNKNOWN,  # For domain detection on new questions
                EpistemicStatus.EXPLORED,
                EpistemicStatus.SYNTHESIZED,
                EpistemicStatus.PROPOSED,
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
        """Execute detection on target nodes."""
        model = get_model_from_context(context)
        provider = get_provider_from_context(context)

        created_nodes: list[Node] = []
        detection_type = context.get("detection_type", "blind_spot")

        for node in nodes:
            if detection_type == "tension":
                new_nodes = await self._detect_tensions(graph, node, provider, model)
            else:
                new_nodes = await self._detect_blind_spots(graph, node, provider, model)

            created_nodes.extend(new_nodes)

        return OperationResult(
            success=True,
            created_nodes=created_nodes,
            modified_nodes=[n.id for n in nodes],
            metadata={
                "detection_type": detection_type,
                "discoveries": len(created_nodes),
            },
        )

    async def _detect_blind_spots(
        self,
        graph: KnowledgeGraph,
        node: Node,
        provider: Any,
        model: Any,
    ) -> list[Node]:
        """Detect blind spots in perspectives."""
        # Gather existing perspectives
        perspectives = self._gather_perspectives(graph, node)

        if not perspectives:
            # No perspectives to analyze
            return []

        # Format perspectives for prompt
        perspectives_text = "\n\n".join(
            [f"**{p.metadata.get('name', 'Perspective')}**: {p.content}" for p in perspectives]
        )

        prompt = BLIND_SPOT_PROMPT.format(PERSPECTIVES=perspectives_text)

        # Call provider
        options = ProviderOptions(system_prompt=prompt)
        raw_output = await provider.generate(
            f"Question: {node.content}\n\nAnalyze for blind spots.",
            model.model,
            options,
        )

        # Parse BLIND_SPOT: lines
        blind_spots = []
        for line in raw_output.strip().split("\n"):
            line = line.strip()
            if line.startswith("BLIND_SPOT:"):
                content = line[len("BLIND_SPOT:") :].strip()
                if content:
                    bs_node = Node(
                        node_type=NodeType.BLIND_SPOT,
                        status=EpistemicStatus.PROPOSED,
                        content=content,
                        depth=node.depth + 1,
                        created_by=f"detect:{model}",
                        model=str(model),
                    )
                    bs_node.add_edge(node.id, NodeRelation.PARENT)
                    node.add_edge(bs_node.id, NodeRelation.REVEALS)
                    blind_spots.append(bs_node)

        return blind_spots

    async def _detect_tensions(
        self,
        graph: KnowledgeGraph,
        node: Node,
        provider: Any,
        model: Any,
    ) -> list[Node]:
        """Detect tensions between findings."""
        # Gather findings
        findings = self._gather_findings(graph, node)

        if len(findings) < 2:
            # Need at least 2 findings to find tensions
            return []

        # Format findings for prompt
        findings_text = "\n\n".join(
            [
                f"**Finding {i + 1}**: {f.content[:500]}..."
                if len(f.content) > 500
                else f"**Finding {i + 1}**: {f.content}"
                for i, f in enumerate(findings)
            ]
        )

        prompt = TENSION_PROMPT.format(FINDINGS=findings_text)

        # Call provider
        options = ProviderOptions(system_prompt=prompt)
        raw_output = await provider.generate(
            f"Question: {node.content}\n\nAnalyze for tensions.",
            model.model,
            options,
        )

        # Parse TENSION: lines
        tensions = []
        for line in raw_output.strip().split("\n"):
            line = line.strip()
            if line.startswith("TENSION:"):
                content = line[len("TENSION:") :].strip()
                if content:
                    t_node = Node(
                        node_type=NodeType.TENSION,
                        status=EpistemicStatus.PROPOSED,
                        content=content,
                        depth=node.depth,
                        created_by=f"detect:{model}",
                        model=str(model),
                    )
                    t_node.add_edge(node.id, NodeRelation.PARENT)
                    node.add_edge(t_node.id, NodeRelation.REVEALS)
                    tensions.append(t_node)

        return tensions

    def _gather_perspectives(self, graph: KnowledgeGraph, node: Node) -> list[Node]:
        """Gather perspective nodes related to this node."""
        perspectives = []

        # Check children for perspectives
        children = graph.children_of(node.id)
        for child in children:
            if child.node_type == NodeType.PERSPECTIVE:
                perspectives.append(child)

        # Also check siblings
        parents = graph.parents_of(node.id)
        for parent in parents:
            siblings = graph.children_of(parent.id)
            for sibling in siblings:
                if sibling.node_type == NodeType.PERSPECTIVE and sibling.id != node.id:
                    perspectives.append(sibling)

        return perspectives

    def _gather_findings(self, graph: KnowledgeGraph, node: Node) -> list[Node]:
        """Gather all findings (answers, insights, syntheses) from children."""
        findings = []

        children = graph.children_of(node.id)
        for child in children:
            if child.node_type in (NodeType.ANSWER, NodeType.INSIGHT, NodeType.SYNTHESIS):
                findings.append(child)
            else:
                # Check if child has answers
                related = graph.related(child.id, NodeRelation.TRANSFORMS_TO)
                findings.extend([r for r in related if r.node_type == NodeType.ANSWER])

        return findings
