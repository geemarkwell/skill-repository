#!/usr/bin/env python3
"""Run trigger evaluation for a skill description.

Tests whether an LLM would decide to load a skill for a set of queries.
Simulates the agent runtime's skill-triggering behavior by presenting the
LLM with available_skills and a user query, then checking its decision.
"""

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from scripts.utils import call_llm, parse_skill_md

# A dummy skill provides competition so the LLM has to actually discriminate
# rather than always selecting the only available option.
TRIGGER_SYSTEM_PROMPT = """You are an AI assistant with access to specialized skills. Skills provide domain-specific instructions you can load when a task matches their description.

Available skills:
<available_skills>
  <skill>
    <name>{skill_name}</name>
    <description>{description}</description>
  </skill>
  <skill>
    <name>general-assistant</name>
    <description>General-purpose coding and task assistance for simple, straightforward requests.</description>
  </skill>
</available_skills>

Given the user's request, decide whether you would load a specialized skill.
- If the request matches a skill's description, respond with ONLY: <use_skill>skill-name-here</use_skill>
- If no specialized skill is needed (the request is simple or general), respond with ONLY: <no_skill/>

Respond with ONLY the XML tag. No explanation."""


def test_single_query(
    query: str,
    skill_name: str,
    description: str,
    model: str | None = None,
) -> bool:
    """Test if an LLM would trigger a skill for a given query."""
    system = TRIGGER_SYSTEM_PROMPT.format(
        skill_name=skill_name,
        description=description,
    )
    try:
        response = call_llm(system=system, message=query, model=model)
        return f"<use_skill>{skill_name}</use_skill>" in response
    except Exception as e:
        print(f"Warning: LLM call failed: {e}", file=sys.stderr)
        return False


def run_eval(
    eval_set: list[dict],
    skill_name: str,
    description: str,
    num_workers: int = 10,
    runs_per_query: int = 3,
    trigger_threshold: float = 0.5,
    model: str | None = None,
) -> dict:
    """Run the full eval set and return results."""
    results = []

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        future_to_info = {}
        for item in eval_set:
            for run_idx in range(runs_per_query):
                future = executor.submit(
                    test_single_query,
                    item["query"],
                    skill_name,
                    description,
                    model,
                )
                future_to_info[future] = (item, run_idx)

        query_triggers: dict[str, list[bool]] = {}
        query_items: dict[str, dict] = {}
        for future in as_completed(future_to_info):
            item, _ = future_to_info[future]
            query = item["query"]
            query_items[query] = item
            if query not in query_triggers:
                query_triggers[query] = []
            try:
                query_triggers[query].append(future.result())
            except Exception as e:
                print(f"Warning: query failed: {e}", file=sys.stderr)
                query_triggers[query].append(False)

    for query, triggers in query_triggers.items():
        item = query_items[query]
        trigger_rate = sum(triggers) / len(triggers)
        should_trigger = item["should_trigger"]
        if should_trigger:
            did_pass = trigger_rate >= trigger_threshold
        else:
            did_pass = trigger_rate < trigger_threshold
        results.append(
            {
                "query": query,
                "should_trigger": should_trigger,
                "trigger_rate": trigger_rate,
                "triggers": sum(triggers),
                "runs": len(triggers),
                "pass": did_pass,
            }
        )

    passed = sum(1 for r in results if r["pass"])
    total = len(results)

    return {
        "skill_name": skill_name,
        "description": description,
        "results": results,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": total - passed,
        },
    }


def main():
    parser = argparse.ArgumentParser(
        description="Run trigger evaluation for a skill description"
    )
    parser.add_argument("--eval-set", required=True, help="Path to eval set JSON file")
    parser.add_argument("--skill-path", required=True, help="Path to skill directory")
    parser.add_argument(
        "--description", default=None, help="Override description to test"
    )
    parser.add_argument(
        "--num-workers", type=int, default=10, help="Number of parallel workers"
    )
    parser.add_argument(
        "--runs-per-query", type=int, default=3, help="Number of runs per query"
    )
    parser.add_argument(
        "--trigger-threshold", type=float, default=0.5, help="Trigger rate threshold"
    )
    parser.add_argument(
        "--model", default=None, help="Model ID (e.g., claude-sonnet-4-20250514)"
    )
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    eval_set = json.loads(Path(args.eval_set).read_text())
    skill_path = Path(args.skill_path)

    if not (skill_path / "SKILL.md").exists():
        print(f"Error: No SKILL.md found at {skill_path}", file=sys.stderr)
        sys.exit(1)

    name, original_description, _ = parse_skill_md(skill_path)
    description = args.description or original_description

    if args.verbose:
        print(f"Evaluating: {description}", file=sys.stderr)

    output = run_eval(
        eval_set=eval_set,
        skill_name=name,
        description=description,
        num_workers=args.num_workers,
        runs_per_query=args.runs_per_query,
        trigger_threshold=args.trigger_threshold,
        model=args.model,
    )

    if args.verbose:
        summary = output["summary"]
        print(
            f"Results: {summary['passed']}/{summary['total']} passed", file=sys.stderr
        )
        for r in output["results"]:
            status = "PASS" if r["pass"] else "FAIL"
            rate_str = f"{r['triggers']}/{r['runs']}"
            print(
                f"  [{status}] rate={rate_str} expected={r['should_trigger']}: {r['query'][:70]}",
                file=sys.stderr,
            )

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
