# AGENTS.md

## Purpose

This repository contains enterprise architecture analysis for resilient F5-based application delivery and WAF design.

Agents must preserve the distinction between **validated current state** and **proposed target state**.

Before making changes, read:

1. `CONTEXT.md`
2. `README.md`
3. `enterprise-scenarios/current_architecture_and_invariants.md`
4. `enterprise-scenarios/future_architecture_improvements.md`
5. Any topic-specific document affected by the task

## Source-of-truth order

When sources conflict, use this precedence:

1. Explicit task/user instruction
2. `enterprise-scenarios/current_architecture_and_invariants.md` — authoritative current-state facts, topology and invariants
3. `enterprise-scenarios/future_architecture_improvements.md` — authoritative target/to-be architecture
4. Detailed scenario and option-analysis documents
5. Management diagrams, PowerPoint and PDF outputs

Do **not** turn a recommendation, assumption, design option or future capability into a current-state fact unless it has been explicitly validated.

## Architecture handling rules

- Keep **CURRENT / STABLE** and **FUTURE / TO-BE** separate.
- Treat the exact deployed GTM health-check implementation as unverified unless repository evidence confirms it.
- Do not infer that Layer-7 GTM checks, iQuery health propagation, cross-site probing, readiness endpoints, remote-WAF routing or dependency failover are deployed merely because they appear in target-state analysis.
- Preserve distinctions between external and internal DNS paths, VIPs, service paths and failure domains.
- Keep DNS/GTM control-plane flows separate from application data paths.
- Do not equate device/port reachability with application availability.
- Preserve explicit uncertainty using labels such as **validated**, **assumption**, **unknown / validate**, **target** or **future**.

For detailed architecture, health-monitoring ownership and diagrams, follow the canonical current- and target-state documents rather than reproducing those details here.

## Documentation and artifact changes

When changing architecture:

- update the authoritative Markdown first;
- update related Mermaid/SVG/source diagrams where applicable;
- check management slides/PDFs for consistency;
- keep current-state and target-state diagrams visually distinct;
- use consistent terminology across Markdown, diagrams and slides;
- do not edit generated binary artifacts without also updating their maintainable source where one exists.

Management outputs are under:

- `management-artifacts/`
- `management-artifacts/diagrams/`
- `management-artifacts/source/`

## Change discipline

- Prefer a small, coherent branch and pull request.
- Do not rewrite unrelated architecture material.
- If a requested architecture decision is unsupported by evidence, document it as an assumption or recommendation rather than silently treating it as fact.
- Check links and cross-references after renames or document moves.
- Keep generated/derived outputs downstream of the authoritative Markdown.

## Before completing a task

Confirm that:

- current state is not mixed with target state;
- assumptions and unknowns remain visible;
- internal and external DNS/VIP paths are represented correctly where relevant;
- diagrams and slides match the authoritative Markdown;
- cross-references are valid;
- all touched files tell the same architectural story.
