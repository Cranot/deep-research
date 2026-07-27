"""
GROUND operation - verifies claims using web search.

This operation takes claims, insights, or answers and uses web search
to find supporting or contradicting evidence.
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

GROUND_PROMPT = """You are a fact-checking research agent with web search capabilities.

Your task is to verify the following claim by searching for evidence:

CLAIM: {CLAIM}

Instructions:
1. Search the web for relevant sources that support or refute this claim
2. Evaluate the credibility of sources you find
3. Provide a verification assessment

For each piece of evidence found, output a line starting with "EVIDENCE:" followed by:
- Whether it SUPPORTS or REFUTES the claim
- A brief summary of the evidence
- The source (if available)

End with a line starting with "VERDICT:" followed by:
- VERIFIED (strong supporting evidence found)
- PARTIALLY_VERIFIED (some support, some gaps)
- UNVERIFIED (insufficient evidence)
- REFUTED (contradicting evidence found)
- CONTESTED (conflicting evidence)

Be thorough and objective. Search for multiple perspectives."""


class GroundOperation(BaseOperation):
    """Grounds claims using web search verification."""

    @property
    def spec(self) -> OperationSpec:
        return OperationSpec(
            operation_type=OperationType.GROUND,
            input_types=[NodeType.CLAIM, NodeType.INSIGHT, NodeType.ANSWER],
            output_types=[NodeType.EVIDENCE],
            required_status=[
                EpistemicStatus.PROPOSED,
                EpistemicStatus.EXPLORED,
                EpistemicStatus.SYNTHESIZED,
            ],
            resulting_status=EpistemicStatus.GROUNDED,
            requires_model=True,
            can_spawn=True,
        )

    async def _execute_impl(
        self,
        graph: KnowledgeGraph,
        nodes: list[Node],
        context: dict[str, Any],
    ) -> OperationResult:
        """Execute grounding on target nodes."""
        model = get_model_from_context(context)
        provider = get_provider_from_context(context)

        # Ensure web search is enabled for this operation
        if not context.get("web_search", False):
            return OperationResult.failed(
                "GROUND operation requires web_search=True in context. "
                "Enable it in the phase configuration."
            )

        created_nodes: list[Node] = []

        for node in nodes:
            # Build the grounding prompt
            prompt = GROUND_PROMPT.format(CLAIM=node.content)

            # Call provider with web search enabled
            options = ProviderOptions(
                system_prompt=prompt,
                web_search=True,
            )

            raw_output = await provider.generate(
                "Verify this claim using web search.",
                model.model,
                options,
            )

            # Parse evidence and verdict
            evidence_items, verdict = self._parse_output(raw_output)

            # Create evidence nodes
            for evidence_text in evidence_items:
                evidence_node = Node(
                    node_type=NodeType.EVIDENCE,
                    status=EpistemicStatus.GROUNDED,
                    content=evidence_text,
                    depth=node.depth,
                    created_by=f"ground:{model}",
                    model=str(model),
                    metadata={"source": "web_search"},
                )

                # Determine relationship based on content
                if "SUPPORTS" in evidence_text.upper():
                    evidence_node.add_edge(node.id, NodeRelation.SUPPORTS)
                elif "REFUTES" in evidence_text.upper():
                    evidence_node.add_edge(node.id, NodeRelation.CONTRADICTS)
                else:
                    evidence_node.add_edge(node.id, NodeRelation.PARENT)

                created_nodes.append(evidence_node)

            # Update node status based on verdict
            node.metadata["grounding_verdict"] = verdict
            node.metadata["grounding_output"] = raw_output

            if verdict == "VERIFIED":
                node.status = EpistemicStatus.VALIDATED
            elif verdict == "REFUTED":
                node.status = EpistemicStatus.REFUTED
            else:
                node.status = EpistemicStatus.GROUNDED

        return OperationResult(
            success=True,
            created_nodes=created_nodes,
            modified_nodes=[n.id for n in nodes],
            metadata={"evidence_found": len(created_nodes)},
        )

    @staticmethod
    def _parse_output(raw_output: str) -> tuple[list[str], str]:
        """Parse evidence and verdict from output."""
        evidence_items = []
        verdict = "UNVERIFIED"

        for line in raw_output.strip().split("\n"):
            line = line.strip()
            if line.startswith("EVIDENCE:"):
                evidence_text = line[len("EVIDENCE:") :].strip()
                if evidence_text:
                    evidence_items.append(evidence_text)
            elif line.startswith("VERDICT:"):
                verdict_text = line[len("VERDICT:") :].strip().upper()
                valid_verdicts = [
                    "VERIFIED",
                    "PARTIALLY_VERIFIED",
                    "UNVERIFIED",
                    "REFUTED",
                    "CONTESTED",
                ]
                if verdict_text in valid_verdicts:
                    verdict = verdict_text

        return evidence_items, verdict
