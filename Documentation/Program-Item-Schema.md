# Program Item Schema

## Purpose

The program-item schema defines the common internal representation used by TPM Copilot for information retrieved from Outlook, Microsoft Teams, Jira, Confluence, and other approved sources.

Connectors may receive different source-specific formats, but each connector must transform relevant information into this common structure before validation and analysis.

## Design Principle: Facts and Analysis Remain Separate

```text
Source facts
    ├── What the source actually says
    ├── Who created it
    ├── When it was created or updated
    └── Where it came from

Derived analysis
    ├── How TPM Copilot classified it
    ├── Estimated urgency and impact
    ├── Confidence in the interpretation
    └── Why the conclusion was reached
```

Derived analysis must never overwrite or silently alter source facts.

## Required Source Fields

| Field | Type | Meaning |
|---|---|---|
| `id` | string | Unique normalized identifier for the item |
| `source_system` | string | System from which the item originated |
| `source_type` | string | Email, message, ticket, documentation, or another supported type |
| `timestamp` | ISO 8601 string | Source creation or most relevant event time |
| `author` | string | Person or system that created the source item |
| `title` | string | Concise source title or normalized subject |
| `content` | string | Relevant source content used for analysis |
| `source_reference` | string | Human-readable provenance reference |
| `source_url` | string or null | Direct link when an authorized stable link is available |

## Optional Normalized Metadata

| Field | Type | Meaning |
|---|---|---|
| `owner` | string or null | Person accountable for the described work |
| `due_date` | ISO 8601 date or null | Supported due date found in the source |
| `status` | string or null | Normalized source-supported status |
| `source_priority` | string or null | Priority explicitly provided by the source system |
| `thread_id` | string or null | Identifier connecting related messages or updates |
| `retrieved_at` | ISO 8601 string or null | Time TPM Copilot retrieved the item |

A null value means the field is part of the schema but no supported value is available. TPM Copilot must not infer a source fact merely to replace null.

## Derived Analysis Fields

Derived fields are produced by an analysis method and must remain distinguishable from source-supported facts.

| Field | Type | Meaning |
|---|---|---|
| `brief_section` | string or null | `accomplished`, `before_next_brief`, `roadblock_risk_or_bottleneck`, or `unclassified` |
| `urgency` | integer or null | Time sensitivity from 1 (low) to 5 (critical) |
| `impact` | integer or null | Estimated program impact from 1 (low) to 5 (critical) |
| `confidence` | number or null | Confidence from 0.0 to 1.0 |
| `rationale` | string or null | Concise explanation supporting the classification and scores |
| `analysis_method` | string or null | Rule set, model, or human process that produced the analysis |
| `analyzed_at` | ISO 8601 string or null | Time the analysis was produced |

Derived values must include enough provenance to explain how they were produced. Low-confidence conclusions should be marked clearly or withheld from the final brief.

## Governance Fields

| Field | Type | Meaning |
|---|---|---|
| `sensitivity` | string | `public`, `internal`, `confidential`, `restricted`, or an approved organizational classification |
| `authorized_for_ai` | boolean | Whether the item is authorized for the configured AI-processing path |
| `retention_policy` | string or null | Applicable retention classification or policy reference |
| `contains_personal_data` | boolean or null | Whether the item is known to contain personal data |

Governance fields control whether and how an item may proceed through the pipeline. They must not be treated merely as descriptive metadata.

## Validation Rules

- Required fields must be present and use the documented type.
- Identifiers must be unique within a briefing dataset.
- Timestamps must use ISO 8601 format and include timezone information when time-of-day is present.
- Controlled fields must use an allowed value.
- Urgency and impact must be integers from 1 through 5.
- Confidence must be between 0.0 and 1.0.
- A direct source URL must use an approved scheme and domain.
- Unauthorized items must not proceed to AI-assisted analysis.
- Derived analysis must not modify the original source content.
- Missing source facts must remain null rather than being invented.
- Credentials, access tokens, and secrets must never appear in a program item.

## Dataset Envelope

Program items are exchanged inside a versioned dataset envelope.

| Field | Type | Meaning |
|---|---|---|
| `schema_version` | string | Version of the program-item contract |
| `brief_date` | ISO 8601 date | Date of the brief being prepared |
| `lookback_start` | ISO 8601 date | Beginning of the collection window |
| `program` | object | Program name and description |
| `items` | array | Collection of normalized program items |

Schema versioning allows the contract to evolve while keeping older datasets understandable.

## Complete Synthetic Example

```json
{
  "id": "TEAMS-001",
  "source_system": "Microsoft Teams",
  "source_type": "channel_message",
  "timestamp": "2026-07-12T15:30:00-06:00",
  "author": "Maya Chen",
  "title": "API contract approved",
  "content": "The architecture group approved version 2 of the customer-profile API contract.",
  "source_reference": "Synthetic Teams message TEAMS-001",
  "source_url": null,
  "owner": null,
  "due_date": null,
  "status": "approved",
  "source_priority": null,
  "thread_id": null,
  "retrieved_at": "2026-07-13T06:30:00-06:00",
  "analysis": {
    "brief_section": "accomplished",
    "urgency": 2,
    "impact": 4,
    "confidence": 0.9,
    "rationale": "The source explicitly states that an architecture approval was completed.",
    "analysis_method": "keyword_rules_v1",
    "analyzed_at": "2026-07-13T06:31:00-06:00"
  },
  "governance": {
    "sensitivity": "public",
    "authorized_for_ai": true,
    "retention_policy": null,
    "contains_personal_data": false
  }
}
```

## Prototype Adoption Plan

The current prototype will adopt the schema incrementally:

1. Add `schema_version` to the dataset envelope.
2. Add nullable normalized metadata and governance fields.
3. Extend validation to enforce field types and allowed values.
4. Move rule-based classification results into a separate analysis structure.
5. Add prioritization using urgency, impact, confidence, and recency.
6. Preserve backward compatibility only when it adds clear value.
