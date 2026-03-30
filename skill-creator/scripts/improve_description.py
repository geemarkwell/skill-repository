#!/usr/bin/env python3
"""Improve a skill description based on eval results.

Takes eval results (from run_eval.py) and generates an improved description
using a direct LLM API call.
"""

import argparse
import json
import re
import sys
from pathlib import Path

from scripts.utils import call_llm, parse_skill_md


def improve_description(
    skill_name: str,
    skill_content: str,
    current_description: str,
    eval_results: dict,
    history: list[dict],
    model: str,
    log_dir: Path | None = None,
    iteration: int | None = None,
) -> str:
    """Call an LLM to improve the description based on eval results."""
    failed_triggers = [
        r for r in eval_results["results"] if r["should_trigger"] and not r["pass"]
    ]
    false_triggers = [
        r for r in eval_results["results"] if not r["should_trigger"] and not r["pass"]
    ]

    train_score = (
        f"{eval_results['summary']['passed']}/{eval_results['summary']['total']}"
    )

    prompt = f"""You are optimizing a skill description. A "skill" is an on-demand instruction set that an AI agent can load when it decides a user's request matches the skill's description.

The description appears in the agent's available_skills list. When a user sends a query, the agent decides whether to invoke the skill based solely on the name and description. Your goal: trigger for relevant queries, don't trigger for irrelevant ones.

Current description:
<current_description>
"{current_description}"
</current_description>

Current score (Train: {train_score}):
<scores>
"""
    if failed_triggers:
        prompt += "FAILED TO TRIGGER (should have triggered but didn't):\n"
        for r in failed_triggers:
            prompt += (
                f'  - "{r["query"]}" (triggered {r["triggers"]}/{r["runs"]} times)\n'
            )
        prompt += "\n"

    if false_triggers:
        prompt += "FALSE TRIGGERS (triggered but shouldn't have):\n"
        for r in false_triggers:
            prompt += (
                f'  - "{r["query"]}" (triggered {r["triggers"]}/{r["runs"]} times)\n'
            )
        prompt += "\n"

    if history:
        prompt += "PREVIOUS ATTEMPTS (do NOT repeat these — try something structurally different):\n\n"
        for h in history:
            train_s = f"{h.get('train_passed', h.get('passed', 0))}/{h.get('train_total', h.get('total', 0))}"
            score_str = f"train={train_s}"
            prompt += f"<attempt {score_str}>\n"
            prompt += f'Description: "{h["description"]}"\n'
            if "results" in h:
                prompt += "Train results:\n"
                for r in h["results"]:
                    status = "PASS" if r["pass"] else "FAIL"
                    prompt += f'  [{status}] "{r["query"][:80]}" (triggered {r["triggers"]}/{r["runs"]})\n'
            prompt += "</attempt>\n\n"

    prompt += f"""</scores>

Skill content (for context):
<skill_content>
{skill_content[:3000]}
</skill_content>

Write an improved description. Generalize from failures to broad categories of user intent — don't overfit to specific queries. Keep it 100-200 words, hard limit 1024 characters.

Tips:
- Use imperative phrasing: "Use this skill for..." not "this skill does..."
- Focus on user intent, not implementation details
- Make it distinctive — it competes with other skills for attention
- If repeated attempts aren't working, change structure and wording significantly

Respond with ONLY the new description in <new_description> tags."""

    response = call_llm(
        system="You optimize skill descriptions for AI agent triggering accuracy.",
        message=prompt,
        model=model,
        temperature=0.8,
    )

    match = re.search(r"<new_description>(.*?)</new_description>", response, re.DOTALL)
    description = (
        match.group(1).strip().strip('"') if match else response.strip().strip('"')
    )

    # Auto-retry if over the 1024-char hard limit
    if len(description) > 1024:
        shorten_prompt = (
            f"This description is {len(description)} characters, over the 1024-character limit:\n\n"
            f'"{description}"\n\n'
            f"Rewrite under 1024 characters, keeping the most important trigger words. "
            f"Respond with ONLY the new description in <new_description> tags."
        )
        shorten_response = call_llm(
            system="You write concise skill descriptions.",
            message=shorten_prompt,
            model=model,
            temperature=0.3,
        )
        match = re.search(
            r"<new_description>(.*?)</new_description>", shorten_response, re.DOTALL
        )
        description = (
            match.group(1).strip().strip('"')
            if match
            else shorten_response.strip().strip('"')
        )

    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"improve_iter_{iteration or 'unknown'}.json"
        log_file.write_text(
            json.dumps(
                {
                    "iteration": iteration,
                    "prompt_length": len(prompt),
                    "parsed_description": description,
                    "char_count": len(description),
                },
                indent=2,
            )
        )

    return description


def main():
    parser = argparse.ArgumentParser(
        description="Improve a skill description based on eval results"
    )
    parser.add_argument(
        "--eval-results", required=True, help="Path to eval results JSON"
    )
    parser.add_argument("--skill-path", required=True, help="Path to skill directory")
    parser.add_argument("--history", default=None, help="Path to history JSON")
    parser.add_argument("--model", required=True, help="Model ID")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    skill_path = Path(args.skill_path)
    if not (skill_path / "SKILL.md").exists():
        print(f"Error: No SKILL.md found at {skill_path}", file=sys.stderr)
        sys.exit(1)

    eval_results = json.loads(Path(args.eval_results).read_text())
    history = json.loads(Path(args.history).read_text()) if args.history else []
    name, _, content = parse_skill_md(skill_path)
    current_description = eval_results["description"]

    if args.verbose:
        print(f"Current: {current_description}", file=sys.stderr)

    new_description = improve_description(
        skill_name=name,
        skill_content=content,
        current_description=current_description,
        eval_results=eval_results,
        history=history,
        model=args.model,
    )

    if args.verbose:
        print(f"Improved: {new_description}", file=sys.stderr)

    print(json.dumps({"description": new_description}, indent=2))


if __name__ == "__main__":
    main()
