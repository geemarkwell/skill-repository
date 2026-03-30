"""Shared utilities for skill-creator scripts."""

import os
import sys
from pathlib import Path


def parse_skill_md(skill_path: Path) -> tuple[str, str, str]:
    """Parse a SKILL.md file, returning (name, description, full_content)."""
    content = (skill_path / "SKILL.md").read_text()
    lines = content.split("\n")

    if lines[0].strip() != "---":
        raise ValueError("SKILL.md missing frontmatter (no opening ---)")

    end_idx = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        raise ValueError("SKILL.md missing frontmatter (no closing ---)")

    name = ""
    description = ""
    frontmatter_lines = lines[1:end_idx]
    i = 0
    while i < len(frontmatter_lines):
        line = frontmatter_lines[i]
        if line.startswith("name:"):
            name = line[len("name:") :].strip().strip('"').strip("'")
        elif line.startswith("description:"):
            value = line[len("description:") :].strip()
            # Handle YAML multiline indicators (>, |, >-, |-)
            if value in (">", "|", ">-", "|-"):
                continuation_lines: list[str] = []
                i += 1
                while i < len(frontmatter_lines) and (
                    frontmatter_lines[i].startswith("  ")
                    or frontmatter_lines[i].startswith("\t")
                ):
                    continuation_lines.append(frontmatter_lines[i].strip())
                    i += 1
                description = " ".join(continuation_lines)
                continue
            else:
                description = value.strip('"').strip("'")
        i += 1

    return name, description, content


def call_llm(
    *,
    system: str,
    message: str,
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> str:
    """Call an LLM. Auto-detects available SDK and API key.

    Tries anthropic SDK first, then openai SDK. Raises RuntimeError if
    neither is available or configured.

    The model parameter accepts raw model IDs (e.g., 'claude-sonnet-4-20250514')
    or provider-prefixed IDs (e.g., 'anthropic/claude-sonnet-4-20250514').
    """
    # Strip provider prefix if present (e.g., 'anthropic/claude-sonnet-4-20250514')
    if model and "/" in model:
        model = model.split("/", 1)[1]

    model = model or os.environ.get("LLM_MODEL")

    # Try anthropic SDK
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if anthropic_key:
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=anthropic_key)
            response = client.messages.create(
                model=model or "claude-sonnet-4-20250514",
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
                messages=[{"role": "user", "content": message}],
            )
            return response.content[0].text
        except ImportError:
            pass

    # Try openai SDK
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        try:
            from openai import OpenAI

            base_url = os.environ.get("LLM_BASE_URL")
            client = OpenAI(api_key=openai_key, base_url=base_url)
            response = client.chat.completions.create(
                model=model or "gpt-4o",
                temperature=temperature,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": message},
                ],
            )
            return response.choices[0].message.content
        except ImportError:
            pass

    raise RuntimeError(
        "No LLM SDK available. Set ANTHROPIC_API_KEY (with 'anthropic' package) "
        "or OPENAI_API_KEY (with 'openai' package)."
    )
