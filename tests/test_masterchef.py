"""
End-to-end test for the MasterChef architecture.

This test verifies the full pipeline:
1. Question → Decompose → Sub-questions
2. Sub-questions → Answer → Answers
3. Answers → Synthesize → Final synthesis

Two of these cases really do invoke a model: they shell out to the local
`claude` CLI and consume your subscription quota. They carry
@requires_live_claude and are skipped unless BOTH a `claude` binary is on
PATH and DEEP_RESEARCH_LIVE_TESTS=1 is set, so that `pytest` on CI (or on a
fresh clone) neither hangs nor spends anything:

    DEEP_RESEARCH_LIVE_TESTS=1 pytest tests/test_masterchef.py

test_graph_persistence is pure serialization and always runs.
"""

import asyncio
import os
import shutil
import sys
from pathlib import Path

import pytest

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from deep_research.core import (
    KnowledgeGraph,
    MasterChef,
    NodeRelation,
    OperationRegistry,
    OperationType,
    recursive_research_strategy,
)

requires_live_claude = pytest.mark.skipif(
    shutil.which("claude") is None or not os.environ.get("DEEP_RESEARCH_LIVE_TESTS"),
    reason=(
        "live integration test: needs a logged-in `claude` CLI on PATH and "
        "DEEP_RESEARCH_LIVE_TESTS=1"
    ),
)


def progress_callback(event: str, data: dict):
    """Simple progress callback for debugging."""
    print(f"  [{event}] {data}")


@requires_live_claude
async def test_decompose_only():
    """Test just the decompose operation."""
    print("\n=== Test 1: Decompose Operation ===\n")

    # Constructing MasterChef registers the built-in operations and strategies.
    MasterChef(
        output_dir=Path("reports/test-masterchef"),
        on_progress=progress_callback,
    )

    # Get decompose operation directly
    registry = OperationRegistry.instance()
    decompose_op = registry.create(OperationType.DECOMPOSE)

    # Create a simple graph
    from deep_research.core import question

    graph = KnowledgeGraph(question="What is 2+2?", output_dir=None)
    q = question("What is 2+2?")
    graph.add(q)

    # Execute decompose (this will call the LLM)
    context = {"model": "haiku"}
    result = await decompose_op.execute(graph, [q.id], context)

    print(f"Success: {result.success}")
    print(f"Created nodes: {len(result.created_nodes)}")
    for node in result.created_nodes:
        print(f"  - {node.content[:80]}...")

    return result.success


@requires_live_claude
async def test_full_research():
    """Test the full recursive research strategy."""
    print("\n=== Test 2: Full Recursive Research ===\n")

    output_dir = Path("reports/test-masterchef-full")

    chef = MasterChef(
        output_dir=output_dir,
        max_parallel=5,
        on_progress=progress_callback,
    )

    # Use a simple question
    question = "What are the three primary colors?"

    # Create a depth-1 strategy (just decompose and answer, no recursion)
    strategy = recursive_research_strategy(max_depth=1, parallel=True)

    # Run the research
    result = await chef.cook(
        question,
        strategy,
        context={"model": "haiku"},
    )

    print("\nResult:")
    print(f"  Success: {result.success}")
    print(f"  Nodes created: {result.stats.nodes_created}")
    print(f"  Phases completed: {result.stats.phases_completed}")
    print(f"  Duration: {result.stats.duration_seconds:.2f}s")
    print(f"  Goals met: {result.goals_met}")

    if result.final_synthesis:
        print("\nFinal synthesis preview:")
        print(f"  {result.final_synthesis.content[:200]}...")

    # Show graph structure
    print("\nGraph structure:")
    print(result.graph.to_tree_string())

    # Save checkpoint
    checkpoint = result.graph.checkpoint("final")
    if checkpoint:
        print(f"\nCheckpoint saved to: {checkpoint}")

    return result.success


async def test_graph_persistence():
    """Test graph serialization and loading."""
    print("\n=== Test 3: Graph Persistence ===\n")

    from deep_research.core import insight, question, synthesis

    # Create a graph with some nodes
    graph = KnowledgeGraph(
        question="Test question",
        output_dir=Path("reports/test-persistence"),
    )

    q = question("What makes good coffee?")
    graph.add(q)

    i1 = insight("Bean quality matters", sources=[q.id])
    graph.add(i1)
    graph.link(q.id, i1.id, graph._inverse_relation(None) or NodeRelation.CHILD)

    i2 = insight("Water temperature is crucial", sources=[q.id])
    graph.add(i2)

    s = synthesis("Good coffee requires quality beans and proper water temperature", [i1.id, i2.id])
    graph.add(s)

    # Save
    checkpoint_path = graph.checkpoint("test")
    print(f"Saved to: {checkpoint_path}")

    # Load
    loaded = KnowledgeGraph.load(checkpoint_path)
    print(f"Loaded graph with {len(loaded)} nodes")
    print(f"Root: {loaded.root.content if loaded.root else 'None'}")

    # Verify
    assert len(loaded) == len(graph), "Node count mismatch"
    print("Persistence test passed!")

    return True


async def main():
    """Run all tests."""
    print("=" * 60)
    print("MasterChef End-to-End Tests")
    print("=" * 60)

    tests = [
        ("Graph Persistence", test_graph_persistence),
        ("Decompose Operation", test_decompose_only),
        # ("Full Research", test_full_research),  # Enable for full test
    ]

    results = []
    for name, test_fn in tests:
        try:
            success = await test_fn()
            results.append((name, success, None))
        except Exception as e:
            print(f"\nError in {name}: {e}")
            import traceback

            traceback.print_exc()
            results.append((name, False, str(e)))

    print("\n" + "=" * 60)
    print("Test Results")
    print("=" * 60)
    for name, success, error in results:
        status = "PASS" if success else "FAIL"
        print(f"  [{status}] {name}")
        if error:
            print(f"         Error: {error}")

    all_passed = all(r[1] for r in results)
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
