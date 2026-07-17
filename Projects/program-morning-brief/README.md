# Program Morning Brief

The Program Morning Brief is the first minimum viable product for TPM Copilot.

It will transform a small collection of program information into a concise, source-supported summary of what needs a Technical Program Manager’s attention.

## Initial Workflow

```text
Sample program data
        ↓
Validate and organize the inputs
        ↓
Analyze priorities, risks, decisions, and dependencies
        ↓
Generate a concise morning brief
        ↓
Cite the supporting source for each important conclusion
```

## Initial Scope

The first version will:

- Use synthetic program data.
- Read structured inputs from local files.
- Identify high-priority items.
- Produce a concise morning brief.
- Include citations to the supplied source material.
- Clearly communicate uncertainty and missing information.

The first version will not:

- Connect to live enterprise systems.
- Use confidential or proprietary information.
- Send messages or modify external systems.
- Make consequential decisions without human review.

## Required Output Format: BLUF 3×3

Every morning brief will begin with a short **Bottom Line Up Front (BLUF)** that summarizes the overall program condition and the most important attention required from the Technical Program Manager.

The BLUF will be followed by three sets of three bullets:

### 1. Accomplished Since the Previous Brief

Three concise bullets describing the most important work completed, progress made, or decisions reached since the previous brief.

### 2. Before the Next Brief

Three concise bullets describing the most important work planned and the outcomes expected before the next brief.

### 3. Roadblocks, Risks, and Bottlenecks

Three concise bullets describing the most important obstacles, emerging risks, unresolved dependencies, or constraints requiring attention.

### Format Rules

- Prioritize significance rather than attempting to summarize everything.
- Keep each bullet concise and action-oriented.
- Identify owners and due dates when supported by the source material.
- Cite the source supporting every substantive bullet.
- Clearly distinguish confirmed facts from inference.
- Clearly communicate uncertainty and missing information.
- Do not invent information to fill the format.
- If fewer than three supported items exist in a section, state that no additional supported item was identified.

## Run and Evaluate the Prototype

Run these commands from the repository root.

Generate a dated local Markdown brief:

```bash
python3 Projects/program-morning-brief/src/generate_brief.py
```

Run objective quality checks:

```bash
python3 Projects/program-morning-brief/src/evaluate_brief.py
```

Run the complete automated test suite:

```bash
python3 -m unittest discover -s Projects/program-morning-brief/tests -v
```

Objective checks do not replace human judgment. Apply the [Morning Brief Evaluation Rubric](../../Documentation/Morning-Brief-Evaluation-Rubric.md) to assess faithfulness, prioritization, actionability, clarity, uncertainty, and overall usefulness.

## AI-Assisted Analysis Status

The provider-neutral [Program Item Analysis Prompt](prompts/analyze-program-items.md) defines the planned AI-analysis behavior, governance gate, classification rules, scoring requirements, and structured JSON output.

The project now includes:

- A validator for structured AI-analysis responses.
- Complete identifier and source-item coverage checks.
- Classification, scoring, provenance, and governance validation.
- Safe application of validated analysis to a separate copy of source data.
- Trusted system timestamps for applied analysis.
- Automated tests for valid, invalid, excluded, and unauthorized responses.
- A configurable interface for deterministic and AI-assisted analysis methods.
- Explicit AI authorization metadata for approved synthetic items.
- Brief generation that preserves validated precomputed analysis.

The prompt is not yet connected to a model. Before live execution, the project must still add:

- Evaluation against the human-approved golden brief.
- A model adapter that preserves the provider-neutral contract.

## Learning Goals

This project will introduce:

- Markdown documentation
- Structured data and JSON
- Python fundamentals
- Input validation
- AI-assisted analysis
- Prompt design
- Source citations
- Testing and evaluation
- Secure enterprise integration concepts
