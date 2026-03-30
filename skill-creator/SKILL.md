---
name: skill-creator
description: Create, modify, and improve project-specific skills. Use when the user wants to create a new skill from scratch, edit or improve an existing skill, test skill quality with subagent runs, run blind comparisons between skill versions, or optimize a skill's description for better triggering accuracy. Invoke via the /create-skill command.
---

# Skill Creator

Create project-specific skills that persist domain knowledge and workflows across sessions.

## Purpose

Skills capture patterns, conventions, and domain knowledge that would otherwise be lost between sessions. A project-specific skill is to code conventions what AGENTS.md is to agent behavior — persistent, scoped context that makes every future session more effective.

**Output location:** `.claude/skills/<name>/SKILL.md` in the project root.

This makes skills project-scoped — they load only when working in that project. For global skills, write to `~/.claude/skills/<name>/` instead.

## The Loop

1. Understand what the skill should do
2. Draft it
3. Test it (spawn subagent runs with and without the skill)
4. Review results with the user
5. Iterate based on feedback
6. Optimize the description for triggering accuracy
7. Write to the project

Your job is to figure out where the user is in this process and help them progress. Maybe they want to create something from scratch. Maybe they already have a draft. Maybe they want to improve an existing skill. Jump in at the right point.

Be flexible. If the user says "just vibe with me, skip the evals," do that.

## Communicating with the User

Pay attention to context cues about the user's technical familiarity. Terms like "evaluation" and "benchmark" are fine for most users. For terms like "JSON" and "assertion," look for cues that the user knows what those are before using them without explanation. Briefly explain terms when in doubt.

---

## Creating a Skill

### Capture Intent

Start by understanding the user's intent. The current conversation might already contain a workflow worth capturing (e.g., they say "turn this into a skill"). If so, extract answers from the conversation history — the tools used, the sequence of steps, corrections the user made. The user may need to fill gaps; confirm before proceeding.

1. What should this skill enable the agent to do?
2. When should this skill trigger? (what user phrases/contexts)
3. What's the expected output format?
4. Should we set up test cases? Skills with objectively verifiable outputs (file transforms, data extraction, code generation) benefit from testing. Skills with subjective outputs (writing style, design taste) often don't. Suggest the default based on skill type, but let the user decide.

### Interview and Research

Ask about edge cases, input/output formats, example files, success criteria, and dependencies. Wait to write test prompts until this is ironed out.

If research tools are available (web search, documentation lookup), research in parallel to reduce burden on the user.

### Write the SKILL.md

Based on the interview, produce:

- **name**: Lowercase, hyphenated identifier (must match directory name). Regex: `^[a-z0-9]+(-[a-z0-9]+)*$`
- **description**: 1-1024 chars. This is the primary triggering mechanism — include both what the skill does AND specific contexts/phrases that should trigger it. Descriptions should be "pushy" to combat undertriggering. Example: instead of "How to handle API errors", write "How to handle API errors in this project. Use this skill whenever the user encounters API errors, writes error handling code, implements retry logic, or asks about error responses from any of our services."
- **The skill body**: The instructions, patterns, and domain knowledge.

### Skill Writing Guide

#### Anatomy

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter (name, description required)
│   └── Markdown instructions
└── Bundled Resources (optional)
    ├── scripts/    - Executable code for deterministic/repetitive tasks
    ├── references/ - Docs loaded into context as needed
    └── assets/     - Files used in output (templates, icons, fonts)
```

#### Progressive Disclosure

Skills use a three-level loading system:
1. **Metadata** (name + description) — Always in context (~100 words)
2. **SKILL.md body** — Loaded when skill triggers (<500 lines ideal)
3. **Bundled resources** — Loaded as needed (unlimited size)

**Key patterns:**
- Keep SKILL.md under 500 lines; if approaching this limit, split detail into reference files with clear pointers about when to read them
- For large reference files (>300 lines), include a table of contents
- When a skill supports multiple domains/frameworks, organize references by variant so only the relevant one gets loaded

**Domain organization example:**
```
cloud-deploy/
├── SKILL.md (workflow + selection)
└── references/
    ├── aws.md
    ├── gcp.md
    └── azure.md
```

#### Writing Style

Explain *why* things are important rather than piling on rigid MUSTs. LLMs have good theory of mind — when they understand the reasoning, they apply it flexibly across situations. If you find yourself writing ALWAYS or NEVER in all caps, that's a signal to reframe as an explanation of consequences.

Use the imperative form for instructions. Include examples when they clarify intent.

Start by writing a draft, then review it with fresh eyes and improve it. Really try to understand the user's intent and transmit that understanding into the instructions.

#### Principle of Lack of Surprise

Skills must not contain malware, exploit code, or content that could compromise security. A skill's contents should not surprise the user if described. Don't create misleading skills or skills designed for unauthorized access or data exfiltration.

### Test Cases

After writing the skill draft, come up with 2-3 realistic test prompts — the kind of thing a real user would actually say. Share them with the user for approval before running.

Save test cases to `evals/evals.json` in the workspace:

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "User's task prompt",
      "expected_output": "Description of expected result",
      "files": []
    }
  ]
}
```

See `references/schemas.md` for the full schema (including the `assertions` field, added after initial runs).

---

## Testing

Put results in `<skill-name>-workspace/` as a sibling to the skill directory. Organize by iteration (`iteration-1/`, `iteration-2/`, etc.).

### Step 1: Spawn Subagent Runs

For each test case, spawn two subagents in parallel — one with the skill, one without. Launch everything at once so results arrive around the same time.

**With-skill run:**

Spawn a subagent with instructions:
```
Execute this task:
- Read and follow the skill at: <path-to-skill/SKILL.md>
- Task: <eval prompt>
- Input files: <eval files if any, or "none">
- Save outputs to: <workspace>/iteration-<N>/eval-<ID>/with_skill/outputs/
```

**Baseline run** (same prompt, no skill):

Spawn a subagent with the same prompt but without loading any skill. Save to `without_skill/outputs/`.

- **Creating a new skill**: baseline = no skill at all.
- **Improving an existing skill**: baseline = the old version. Snapshot it first (`cp -r <skill-path> <workspace>/skill-snapshot/`), then point the baseline subagent at the snapshot.

### Step 2: Draft Assertions While Runs Are In Progress

Don't wait idle — use this time to draft quantitative assertions for each test case. Good assertions are objectively verifiable and have descriptive names. Subjective skills are better evaluated qualitatively — don't force assertions onto things that need human judgment.

Update `evals/evals.json` with the assertions. Explain to the user what each assertion checks.

### Step 3: Grade Results

When runs complete, evaluate each assertion against the outputs. For assertions that can be checked programmatically, write and run a script. For subjective quality, grade inline or spawn a grader subagent — read `agents/grader.md` for the grading protocol.

Save results to `grading.json` in each run directory. The grading expectations array uses the fields `text`, `passed`, and `evidence`.

### Step 4: Present Results to the User

Present both outputs directly in the conversation:

- **Prompt**: what was asked
- **With-skill output**: what the skill produced
- **Baseline output**: what was produced without the skill
- **Grades**: which assertions passed/failed for each
- **Ask for feedback**: "How does this compare? Anything the skill should handle differently?"

Empty feedback means it looked fine. Focus improvements on test cases where the user had specific complaints.

---

## Improving the Skill

### How to Think About Improvements

1. **Generalize from feedback.** You're iterating on a few examples, but the skill will be used across many prompts. Don't overfit with fiddly rules. If there's a stubborn issue, try different metaphors or patterns rather than adding more constraints.

2. **Keep it lean.** Remove instructions that aren't pulling their weight. Read the subagent transcripts, not just the final outputs — if the skill is making the agent waste time on unproductive steps, cut those parts.

3. **Explain the why.** Even when user feedback is terse, understand the underlying intent and transmit that understanding into the instructions. Reasoning beats rigid rules.

4. **Look for repeated work.** If every test run independently wrote similar helper code, that's a signal to bundle it as a script in the skill. Write it once, save every future invocation from reinventing it.

### The Iteration Loop

1. Apply improvements to the skill
2. Rerun all test cases (new subagent runs into `iteration-<N+1>/`)
3. Present new results alongside previous results
4. Get feedback
5. Repeat

Keep going until:
- The user says they're happy
- Feedback is all empty (everything looks good)
- You're not making meaningful progress

---

## Blind Comparison

For rigorous comparison between two skill versions — when you can't tell from outputs alone whether a change helped, or when the user asks "is the new version actually better?":

1. Read `agents/comparator.md` for the comparison protocol
2. Spawn a subagent with the comparator instructions
3. Give it both outputs without revealing which came from which version
4. The subagent judges quality on defined criteria and picks a winner
5. Read `agents/analyzer.md` and spawn an analysis subagent to explain *why* the winner won

This eliminates confirmation bias. Optional — the inline review loop is usually sufficient.

---

## Description Optimization

The description field in SKILL.md frontmatter determines whether the agent invokes the skill. After creating or improving a skill, offer to optimize the description for triggering accuracy.

### Step 1: Generate Trigger Eval Queries

Create 20 queries — a mix of should-trigger (8-10) and should-not-trigger (8-10):

```json
[
  {"query": "realistic user prompt", "should_trigger": true},
  {"query": "another realistic prompt", "should_trigger": false}
]
```

Queries must be realistic — concrete, specific, with details like file paths, column names, context about the user's situation. Not abstract requests. Include casual speech, abbreviations, typos.

**Should-trigger queries:** Different phrasings of the same intent. Include cases where the user doesn't name the skill but clearly needs it. Include edge cases and cases where this skill competes with another but should win.

**Should-not-trigger queries:** Near-misses that share keywords but need something different. Adjacent domains, ambiguous phrasing. Don't make them obviously irrelevant — the negative cases should be genuinely tricky.

### Step 2: Review with User

Present the eval set to the user. Let them add, remove, or modify queries. Bad queries lead to bad descriptions.

### Step 3: Evaluate and Iterate

For each query, spawn a subagent with these instructions:

```
You are evaluating whether a skill should trigger for a given user request.

Available skills:
- Name: <skill-name>
  Description: <current-description>

User request: "<query>"

Would you load this skill to handle this request? Answer:
- "yes" or "no"
- Brief reasoning (1-2 sentences)
```

Run each query 3 times (LLM responses vary) and take the majority answer. Score: did the majority answer match the expected `should_trigger` value?

Based on failures, revise the description:
- If should-trigger queries aren't triggering: add more specific trigger phrases, broaden the scope language
- If should-not-trigger queries are triggering: sharpen the boundary language, add exclusion phrases

Re-evaluate after each revision. Iterate up to 5 times, tracking scores per iteration. Select the description with the best overall score.

### Step 4: Apply

Update the skill's SKILL.md frontmatter with the improved description. Show the user before/after and report the scores.

---

## Writing to the Project

When the skill is ready, write it to the project:

```
<project-root>/.claude/skills/<name>/SKILL.md
```

If the skill needs reference files or scripts, create subdirectories:

```
<project-root>/.claude/skills/<name>/
├── SKILL.md
├── references/    (if needed)
└── scripts/       (if needed)
```

This location is automatically discovered by the agent when working in the project. The skill is project-scoped — it won't load in other projects.

If the user wants a global skill instead, write to `~/.claude/skills/<name>/`.

---

## Reference Files

The agents/ directory contains instructions for specialized subagents. Read them when you need to spawn the relevant subagent.

- `agents/grader.md` — How to evaluate assertions against outputs
- `agents/comparator.md` — How to do blind A/B comparison between two outputs
- `agents/analyzer.md` — How to analyze why one version beat another

The references/ directory has additional documentation:
- `references/schemas.md` — JSON structures for evals.json, grading.json, etc.
