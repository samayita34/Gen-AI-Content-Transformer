# TransformAI Ground-Truth Annotation Protocol (Milestone 7)

> **Document Version**: 1.0.0  
> **Milestone**: 7 — Quantitative Research Evaluation Framework  
> **Purpose**: Standardized guidelines for constructing atomic ground-truth facts and labeling verification benchmarks.

---

## 1. Ten-Point Annotation Protocol

### 1. Atomic Fact Identification
- An **atomic fact** is the smallest independent proposition asserting a single factual relationship, state, or metric.
- Every atomic fact must express a complete, self-contained thought that can be evaluated as true or false against the source document.

### 2. Compound Statement Splitting
- Complex sentences with coordinating conjunctions (*and*, *but*, *whereas*) or multiple clauses must be split into separate atomic facts.
- *Example*: *"System X achieved 99.9% uptime in Q2 and reduced latency to 45ms."*
  - **Fact 1**: *"System X achieved 99.9% uptime in Q2."*
  - **Fact 2**: *"System X reduced latency to 45ms in Q2."*

### 3. Numerical Values and Units
- Numbers must always retain their exact units, multipliers, and qualifiers (*approximately*, *up to*, *at least*).
- Never round or truncate numbers during ground-truth extraction (e.g., preserve `$14.2 million`, not `$14M`).

### 4. Temporal Dates and Durations
- Dates, quarters, fiscal years, and durations must be explicitly stated in the normalized proposition.
- Avoid relative deictic terms (*last month*, *recently*) in favor of document-anchored dates (*Q3 2025*, *October 14, 2025*).

### 5. Named Entities and Roles
- Entities (organizations, systems, protocols, individuals) must be identified with their full canonical names.
- Hierarchical relationships (subsidiary vs parent, contractor vs client) must be preserved without conflation.

### 6. Criteria for Contradiction (`CONTRADICTED`)
- A generated claim is **contradicted** if and only if:
  1. A numerical value, metric, or threshold directly conflicts with the source (e.g., source: `$4.2M`, claim: `$42M`).
  2. A date, timeline, or sequence is inverted or misassigned.
  3. A causal or attributional assertion states the opposite of the source text.
  4. An entity is assigned an action or attribute explicitly refuted by the source.

### 7. Criteria for Insufficient Evidence (`INSUFFICIENT_EVIDENCE`)
- A claim receives **insufficient evidence** if the source document contains no information to confirm or deny the assertion.
- *Rule*: Never label an unmentioned external fact as contradicted; it is strictly `INSUFFICIENT_EVIDENCE`.

### 8. Criteria for Partial Support (`PARTIALLY_SUPPORTED`)
- A claim is **partially supported** if:
  1. Part of a compound assertion is verified by the source, but another part lacks evidence.
  2. The general concept is accurate, but a specific numerical bound or condition is unverified.

### 9. Handling Ambiguous Statements
- If the source text contains ambiguous phrasing, annotators must document the ambiguity in `distractor_notes`.
- Do not artificially resolve ambiguity using external knowledge or assumptions.

### 10. Avoidance of Outside Knowledge (Closed-World Assumption)
- Annotators and evaluation judges must operate under a strict **closed-world assumption**.
- The source document is the sole source of truth. Common-sense facts not present in the document are treated as ungrounded (`INSUFFICIENT_EVIDENCE`).

---

## 2. Fact Taxonomy Categories

| Category | Description | Example |
| :--- | :--- | :--- |
| `FACTUAL` | General declarative state or property | *"The platform is deployed across three availability zones."* |
| `STATISTICAL` | Quantitative distribution, ratio, or percent | *"92% of queries completed in under 50ms."* |
| `ATTRIBUTIONAL` | Author, organization, or stakeholder attribution | *"The security audit was performed by CyberGuard Inc."* |
| `TEMPORAL` | Chronological milestone, date, or phase | *"Phase 2 rollout will initiate in March 2026."* |
| `NUMERICAL` | Exact monetary, count, capacity, or dimension | *"Total capital expenditure was $18.5 million."* |
| `ENTITY_RELATION` | Explicit relationship between two or more named entities | *"Acme Corp acquired DataPulse as a subsidiary."* |
| `IMPLICATION` | Direct logical consequence explicitly stated in source | *"Exceeding the threshold triggers automatic node failover."* |
