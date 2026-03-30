# Pipeline Audit Reference — Extended Checklists

This file contains detailed checklists and patterns for common pipeline types. The main SKILL.md covers the general workflow; consult this file when you need domain-specific guidance.

## Table of Contents
1. [Extraction Pipeline Checklist](#extraction)
2. [Transformation Pipeline Checklist](#transformation)
3. [Migration Pipeline Checklist](#migration)
4. [Common Bug Patterns](#bug-patterns)
5. [Regex/Pattern Library Audit](#regex-audit)
6. [LLM Integration Audit](#llm-audit)
7. [Cache System Audit](#cache-audit)
8. [Schema Evolution Checklist](#schema-evolution)
9. [Generalization & Coupling Analysis](#generalization)

---

## 1. Extraction Pipeline Checklist <a name="extraction"></a>

Extraction pipelines pull structured data from unstructured or semi-structured sources (documents, HTML, PDFs, etc.).

### Source Document Analysis
- [ ] Are all expected source documents accounted for? (file count matches manifest)
- [ ] Are there duplicate source files? (check by hash or filename pattern)
- [ ] Are source documents in the expected format? (check encoding, file type, structure)
- [ ] Are there zero-byte or corrupted source files?

### Conversion Stage
- [ ] Does the conversion preserve all relevant content? (compare source to converted output)
- [ ] Are formatting artifacts introduced? (extra whitespace, encoding mangling, lost structure)
- [ ] Are tables, lists, and nested structures preserved?
- [ ] Are special characters handled correctly?

### Extraction Stage
- [ ] Are all expected fields being extracted?
- [ ] Are extracted values accurate against the source? (spot-check N items)
- [ ] Are there systematic extraction failures? (same field missing across many items)
- [ ] Are numerical values extracted with correct precision?
- [ ] Are hierarchical relationships preserved? (parent-child, scope nesting)
- [ ] Are there boundary detection issues? (sections bleeding into each other)

### Validation Stage
- [ ] Do extracted values pass type checks? (numbers are numbers, dates are dates)
- [ ] Do cross-field validations pass? (totals match sum of parts, references resolve)
- [ ] Are there statistical outliers in extracted values?
- [ ] Does the output conform to the target schema?

---

## 2. Transformation Pipeline Checklist <a name="transformation"></a>

### Data Mapping
- [ ] Are all source fields mapped to target fields?
- [ ] Are mapping rules documented and version-controlled?
- [ ] Do type conversions produce expected results? (string→number, date formatting)
- [ ] Are null/missing values handled consistently?

### Aggregation
- [ ] Do aggregated totals match the sum of their parts?
- [ ] Are there rounding errors in aggregated numerical values?
- [ ] Is the grouping logic correct? (items grouped by the right key)
- [ ] Are edge cases handled? (empty groups, single-item groups)

### Enrichment
- [ ] Do lookups/joins produce correct matches?
- [ ] How are unmatched items handled? (null, default, error)
- [ ] Are there duplicate matches causing fan-out?

---

## 3. Migration Pipeline Checklist <a name="migration"></a>

### Pre-Migration
- [ ] Source record count documented
- [ ] Source schema/structure captured
- [ ] Target schema defined and validated
- [ ] Mapping document reviewed
- [ ] Rollback plan exists

### During Migration
- [ ] Record count in = record count out (or delta explained)
- [ ] No data truncation in target fields
- [ ] Foreign key/reference integrity maintained
- [ ] Character encoding preserved
- [ ] Timestamps handled correctly (timezone-aware)

### Post-Migration
- [ ] Spot-check N records for accuracy
- [ ] Run target system validation/integrity checks
- [ ] Compare aggregate metrics (counts, sums) source vs target
- [ ] Verify that downstream systems can read the migrated data

---

## 4. Common Bug Patterns <a name="bug-patterns"></a>

These are recurring patterns in pipeline bugs. When debugging, scan this list to see if your issue matches a known pattern.

### Misattribution
**Symptom**: Values are present but assigned to the wrong entity, field, or scope.
**Common causes**:
- Scope/context not properly tracked when parsing nested structures
- Greedy regex matching across section boundaries
- Shared mutable state between processing iterations
**Detection**: Compare extracted values against source — values are correct but in the wrong place.

### Boundary Bleed
**Symptom**: Content from one section appears in an adjacent section's output.
**Common causes**:
- Section delimiter detection is too permissive or too strict
- Off-by-one errors in line/position ranges
- Delimiter patterns that match within section content
**Detection**: Look for output fields containing content that belongs to a different section.

### Silent Drops
**Symptom**: Items or fields are missing from output with no error logged.
**Common causes**:
- Overly broad try/except blocks swallowing errors
- Conditional logic that silently skips items
- Filter criteria that are too aggressive
**Detection**: Compare input item count vs output item count. Check for items in source that have no corresponding output.

### Aggregation Drift
**Symptom**: Totals don't match the sum of their parts, or values shift slightly.
**Common causes**:
- Floating point arithmetic accumulation
- Double-counting due to many-to-many relationships
- Items counted in wrong categories
**Detection**: Recompute aggregations independently and compare against pipeline output.

### Schema Mismatch
**Symptom**: Output looks structurally wrong — missing fields, extra fields, wrong nesting.
**Common causes**:
- Schema was updated but processing code wasn't (or vice versa)
- Optional fields treated as required (or vice versa)
- Schema version mismatch between pipeline stages
**Detection**: Validate output against the declared schema. Check schema version in config vs code.

### Stale Cache
**Symptom**: Output doesn't reflect recent changes to source data or pipeline logic.
**Common causes**:
- Cache not invalidated after code/config changes
- Cache key doesn't include all relevant inputs (e.g., includes file hash but not schema version)
- Manual override left a cached result in place
**Detection**: Compare cache timestamps against source modification times. Clear cache and re-run a sample.

### Encoding Corruption
**Symptom**: Garbled text, missing characters, or unexpected byte sequences.
**Common causes**:
- Mixed encodings in source files (some UTF-8, some Latin-1)
- Encoding not specified when reading files
- Double-encoding (UTF-8 bytes interpreted as Latin-1 then re-encoded)
**Detection**: Look for replacement characters (�), mojibake, or byte sequences like \xc3\xa9 appearing as literal text.

---

## 5. Regex/Pattern Library Audit <a name="regex-audit"></a>

If the pipeline uses a regex pattern library for extraction:

### Coverage Analysis
- Count total patterns in the library
- For each pattern, count how many source items it matches
- Identify patterns with zero matches (dead patterns)
- Identify source items matched by no pattern (coverage gaps)

### Conflict Analysis
- Find items where multiple patterns match the same content
- Determine if pattern priority/ordering is well-defined
- Check for patterns that are strict subsets of other patterns

### Quality Checks
- [ ] Are patterns documented with their intended purpose?
- [ ] Are named capture groups used for readability?
- [ ] Are patterns tested against both positive and negative examples?
- [ ] Are there patterns that are overly broad? (match too much)
- [ ] Are there patterns that are overly narrow? (miss valid variations)
- [ ] Do patterns handle optional whitespace and formatting variations?

### Maintainability
- [ ] Can patterns be reused across different contexts?
- [ ] Is there metadata stored with patterns (author, date, purpose, test cases)?
- [ ] Is the pattern library version-controlled?

---

## 6. LLM Integration Audit <a name="llm-audit"></a>

If the pipeline uses LLM calls (for extraction, classification, validation, etc.):

### Prompt Quality
- [ ] Are prompts versioned and tracked?
- [ ] Do prompts include concrete examples of expected output?
- [ ] Is the output format clearly specified? (JSON schema, template)
- [ ] Are prompts tested against edge cases?

### Fallback Behavior
- [ ] When does the pipeline fall back to LLM? (what triggers it)
- [ ] What's the fallback rate? (what % of items need LLM)
- [ ] Is the fallback rate increasing or stable over time?
- [ ] What happens if the LLM call fails? (retry, skip, error)

### Output Parsing
- [ ] Is LLM output parsed robustly? (handles minor format deviations)
- [ ] Are there validation checks on parsed LLM output?
- [ ] Is there a mechanism to detect and handle hallucinated content?
- [ ] Are LLM outputs cached to avoid redundant calls?

### Cost & Performance
- [ ] What's the cost per LLM call? Total cost per run?
- [ ] What's the latency impact of LLM calls?
- [ ] Are there opportunities to batch LLM calls?
- [ ] Could any LLM-dependent paths be replaced with deterministic logic?

---

## 7. Cache System Audit <a name="cache-audit"></a>

### Cache Health
- [ ] How many cache entries exist?
- [ ] What's the cache hit rate?
- [ ] How old are the cache entries? (distribution)
- [ ] What's the total cache size on disk?

### Cache Correctness
- [ ] Does the cache key include all relevant inputs? (source content, code version, config version, schema version)
- [ ] Is the cache invalidation strategy documented?
- [ ] Can stale cache entries be identified programmatically?
- [ ] Is there a way to force a full re-run bypassing cache?

### Cache Strategy
- Content-addressed (hash of input) — good for dedup, bad if you need to reprocess after logic changes
- Version-stamped (input hash + code/config version) — more correct, requires version tracking
- TTL-based (time expiry) — simple but can serve stale data or waste recomputation

---

## 8. Schema Evolution Checklist <a name="schema-evolution"></a>

When the output schema changes between versions:

- [ ] Is the schema version tracked in output files?
- [ ] Are there migration scripts between schema versions?
- [ ] Are old outputs still valid against the new schema? (backward compatibility)
- [ ] Can new code read old-format outputs? (forward compatibility)
- [ ] Are there items that were processed under an old schema that need reprocessing?
- [ ] Are downstream consumers aware of the schema change?
- [ ] Is the schema changelog documented?

---

## 9. Generalization & Coupling Analysis <a name="generalization"></a>

When auditing a pipeline for multi-client readiness, use this checklist to systematically scan for client-specific coupling. Work through each category, checking every item. The categories are ordered from easiest to find (and fix) to hardest.

### Surface Scan: Naming & References

These are the most visible coupling points. Grep-able, usually low-risk to change.

- [ ] **Client name in string literals**: Search the entire codebase for the client name (and common abbreviations, misspellings, case variants). Check log messages, error messages, print statements, comments, docstrings.
- [ ] **Client name in identifiers**: Function names, class names, variable names, module names that embed the client name (e.g., `parse_axiom_header`, `ACME_FEE_TYPES`).
- [ ] **Client-specific file paths**: Hardcoded paths that assume a specific directory structure, drive letter, or naming convention. Watch for both absolute paths and relative paths that assume a specific project layout.
- [ ] **Client-specific URLs/endpoints**: API endpoints, webhook URLs, Salesforce instance URLs, or other integration targets that are hardcoded.
- [ ] **Client name in output files**: Does the pipeline stamp the client name into output filenames, JSON keys, or metadata fields?
- [ ] **README/documentation assumptions**: Does documentation describe the pipeline as if it only works for one client?

### Structural Scan: Data Assumptions

These are harder to find because they're embedded in logic, not just text. You have to understand what the code expects to see in the data.

#### Schema Assumptions
- [ ] **Sheet/tab names**: Does the pipeline expect specific worksheet names? (e.g., "Fee Summary", "Project Info")
- [ ] **Column headers**: Are expected column names hardcoded? Are they matched exactly or fuzzily?
- [ ] **Column positions**: Does the pipeline assume data is in specific columns (A, B, C) rather than finding columns by header?
- [ ] **Row positions**: Are there hardcoded row numbers for headers, data start, or summary rows?
- [ ] **Field names in JSON/XML**: Are expected field names hardcoded in extraction or mapping logic?
- [ ] **Required vs. optional fields**: Which fields does the pipeline treat as required? Would all clients have these fields?

#### Taxonomy Assumptions
- [ ] **Category names**: Are fee categories, service types, project phases, or other classifications hardcoded?
- [ ] **Status codes**: Are expected status values (e.g., "Active", "Completed") specific to one client's terminology?
- [ ] **Classification hierarchies**: Is there a hardcoded tree of categories/subcategories?
- [ ] **Mapping tables**: Are there lookup tables that translate client-specific terms to canonical terms? Are these in code or configuration?

#### Format Assumptions
- [ ] **Date formats**: Does the pipeline assume MM/DD/YYYY vs DD/MM/YYYY or other date conventions?
- [ ] **Number formats**: Are there assumptions about decimal separators, thousands separators, currency symbols?
- [ ] **Text patterns**: Do regex patterns assume client-specific phrasing, abbreviations, or formatting conventions?
- [ ] **Document structure**: Does the pipeline assume a specific ordering of sections, headers, or content blocks?

#### Detection & Routing Assumptions
- [ ] **Document type detection**: How does the pipeline identify what kind of document it's processing? Is this based on client-specific patterns?
- [ ] **Section boundary detection**: How are section boundaries identified? Are the delimiters client-specific?
- [ ] **Template matching**: If the pipeline matches against known templates, are these templates specific to one client?
- [ ] **Heuristic thresholds**: Are any magic numbers (distances, sizes, counts) tuned to one client's data characteristics?

### Architectural Scan: System Design

These are pipeline-level design decisions, not individual code points.

#### Configuration Architecture
- [ ] **Config file structure**: Is there a configuration system? Is it global or per-client?
- [ ] **Environment variables**: Are there environment variables that assume a single client?
- [ ] **Feature flags**: Can pipeline behavior be toggled per client?
- [ ] **Default values**: Do defaults assume one client's conventions?

#### Pipeline Flow
- [ ] **Stage ordering**: Is the sequence of processing stages fixed? Would other clients need a different order?
- [ ] **Conditional stages**: Are there stages that only apply to certain document types? Could other clients have different conditional logic?
- [ ] **Parallel vs. sequential**: Are there assumptions about processing order that depend on one client's data relationships?

#### Output Architecture
- [ ] **Output schema**: Is the output schema specific to one client's needs, or is it generic?
- [ ] **Output format**: Does the pipeline produce output in a format dictated by one client's downstream system?
- [ ] **Downstream integrations**: Are Salesforce field mappings, API payloads, or database schemas hardwired to one client?

#### State & Scale
- [ ] **Volume assumptions**: Are batch sizes, memory allocations, or timeout values tuned to one client's data volume?
- [ ] **Naming conventions in state tracking**: Do job IDs, cache keys, or log entries embed client-specific information?
- [ ] **Data isolation**: If running for multiple clients, is there a risk of cross-contamination between client datasets?

### Coupling Severity Classification

When cataloging findings, classify each by how deeply it's embedded:

| Severity | Description | Typical Fix | Risk |
|---|---|---|---|
| **Cosmetic** | Client name in strings, comments, variable names | Find-and-replace, rename | Low — no behavior change |
| **Configurable** | Hardcoded value that should come from config | Extract to config file, add client profile lookup | Low-Medium — behavior preserved, source changes |
| **Structural** | Logic that assumes client-specific data shape | Refactor to use schema-driven processing | Medium-High — core logic changes |
| **Architectural** | Pipeline design assumes single-client context | Redesign component boundaries, add client routing | High — significant refactoring |

### Anti-Patterns to Flag

Watch for these patterns that make generalization harder than it needs to be:

- **Scattered constants**: The same client-specific value (e.g., a category name) appears in multiple files rather than being defined once. Changing it requires finding every instance.
- **Implicit coupling**: Code that works for the current client not because it was designed to, but by coincidence. Example: a date parser that handles MM/DD/YYYY because that's what the client uses, but would silently produce wrong results for DD/MM/YYYY.
- **Leaky abstractions**: A function claims to be generic (e.g., `parse_fee_table()`) but internally hardcodes client-specific assumptions.
- **Mixed concerns**: A single function that handles both generic logic (parsing Excel cells) and client-specific logic (mapping to fee categories). These need to be separated before either can be independently configured.
- **Test data coupling**: Test fixtures or sample data that only represent one client's format. When you generalize the code, the tests won't catch regressions for other formats.