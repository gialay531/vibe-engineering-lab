# Program Morning Brief Architecture

## Purpose

This document describes the logical architecture of the Program Morning Brief MVP and its planned evolution into a secure TPM Copilot capability.

The architecture separates source-system integration, data normalization, validation, analysis, brief generation, and human review. This separation allows individual components to evolve without tightly coupling the entire product to Outlook, Microsoft Teams, Jira, Confluence, or any single AI model.

## Logical Data Flow

```mermaid
flowchart LR
    A["Enterprise source systems<br/>Outlook, Teams, Jira, Confluence"] --> B["Connector layer"]
    B --> C["Normalized program-item schema"]
    C --> D["Input validation"]
    D --> E["Analysis and prioritization"]
    E --> F["BLUF 3×3 generator"]
    F --> G["Human review"]
    G -. "Approved future action" .-> H["Distribution or source-system update"]
```

## Current Prototype

The current prototype implements a safe local subset of the target architecture:

```text
Synthetic JSON data
        ↓
Schema validation
        ↓
Rule-based classification
        ↓
BLUF 3×3 generation
        ↓
Local Markdown file
        ↓
Human review
```

The prototype does not connect to enterprise systems, transmit data, or perform external actions.

## Current-to-Future Mapping

| Architectural capability | Current implementation | Planned evolution |
|---|---|---|
| Source ingestion | Local synthetic JSON | Approved Outlook, Teams, Jira, and Confluence connectors |
| Normalization | Manually structured program items | Connector-specific data transformed into a common schema |
| Validation | Required-field checks | Schema, type, freshness, provenance, and policy validation |
| Analysis | Transparent keyword rules | Context-aware analysis with deterministic safeguards |
| Prioritization | Input order within each category | Urgency, impact, confidence, and recency scoring |
| Brief generation | Deterministic Markdown formatter | Higher-quality synthesis constrained to BLUF 3×3 |
| Citations | Synthetic source identifiers | Direct links and immutable source references |
| Output | Local generated Markdown | Approved delivery channels with human authorization |

## Component Responsibilities

### Connector Layer

- Read only from explicitly approved source systems and scopes.
- Retrieve only information needed for the briefing window.
- Preserve source identifiers, timestamps, authorship, and direct links.
- Avoid embedding source-specific behavior in downstream components.

### Normalized Program-Item Schema

- Represent different source types through one consistent structure.
- Preserve the original source system and source reference.
- Separate raw source content from derived analysis.
- Support future fields such as owner, due date, confidence, and sensitivity.

### Validation Layer

- Reject malformed or incomplete inputs with clear errors.
- Verify required fields, data types, and supported source types.
- Detect stale, duplicate, or unverifiable information.
- Prevent invalid data from silently reaching the analysis layer.

### Analysis and Prioritization

- Identify accomplishments, planned outcomes, risks, bottlenecks, decisions, and dependencies.
- Rank items using urgency, impact, recency, confidence, and actionability.
- Distinguish confirmed facts from inference.
- Preserve evidence supporting every substantive conclusion.

### BLUF 3×3 Generator

- Produce a concise Bottom Line Up Front.
- Return three accomplishments, three next-period outcomes, and three roadblocks, risks, or bottlenecks.
- Avoid unsupported claims and invented filler.
- Include an actionable citation for every substantive bullet.

### Human Review

- Allow a Technical Program Manager to validate conclusions and wording.
- Require approval before consequential distribution or source-system updates.
- Make uncertainty, missing information, and conflicts visible.
- Preserve accountability with the human decision-maker.

## Trust and Security Boundaries

- Use least-privilege and read-only access wherever possible.
- Never store credentials, tokens, or secrets in the repository.
- Minimize collection and processing of enterprise data.
- Follow organizational requirements for data classification, retention, and approved AI use.
- Keep source content and derived conclusions traceable.
- Require explicit authorization before sending messages or modifying external systems.
- Record enough audit information to explain what sources informed a brief.
- Fail safely when authorization, provenance, or data quality cannot be verified.

## Foundational Architecture Decisions

### Use a Common Internal Schema

Each source system will have different data structures and terminology. Connector-specific data will be transformed into a shared program-item schema before validation and analysis.

This prevents the briefing engine from requiring separate logic for every source system.

### Separate Analysis from Presentation

The analysis layer determines what an item means and how important it is. The presentation layer formats approved analysis into the BLUF 3×3 structure.

This separation allows the analysis approach to evolve from simple rules to AI-assisted reasoning without rewriting the output format.

### Require Evidence for Important Claims

Every substantive conclusion must retain a reference to its supporting source. A claim without verifiable evidence must be marked as uncertain or excluded.

### Keep Consequential Actions Human-Governed

Reading, analyzing, recommending, and acting are different levels of authority. TPM Copilot may eventually recommend or prepare actions, but external communication and source-system changes will require explicit approval unless a separately authorized workflow permits them.

### Design for Safe Failure

When data is missing, stale, malformed, unauthorized, or contradictory, the system should stop or reduce confidence rather than silently produce an authoritative-sounding answer.

## Planned Evolution

1. Strengthen the normalized program-item schema.
2. Improve prioritization and confidence handling.
3. Introduce an interchangeable analysis interface.
4. Evaluate AI-assisted analysis using synthetic data.
5. Compare generated briefs against human-approved golden examples.
6. Add one approved, read-only enterprise connector.
7. Expand integrations incrementally after security and policy review.
8. Introduce authorized delivery or update workflows only when justified.

## Architecture Principle

> The usefulness of TPM Copilot depends not only on the intelligence of its conclusions, but on the trustworthiness, traceability, and governance of the complete system that produces them.
