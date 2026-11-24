# AGENTS.md

## Purpose

This repository contains enterprise architecture analysis for resilient F5-based application delivery and WAF design. AI coding and documentation agents must preserve the distinction between **validated current state** and **proposed target state**.

Before making any change, read:

1. `CONTEXT.md`
2. `README.md`
3. `enterprise-scenarios/enterprise_scenario_invariants.md`
4. `enterprise-scenarios/high_level_architecture.md`
5. `enterprise-scenarios/future_architecture_improvements.md`
6. Any topic-specific document affected by the task

## Source-of-truth order

When sources conflict, use this precedence:

1. Explicit task/user instruction
2. `enterprise-scenarios/enterprise_scenario_invariants.md` for current/stable facts
3. `enterprise-scenarios/high_level_architecture.md` for current-state topology
4. `enterprise-scenarios/future_architecture_improvements.md` for target/to-be design
5. Detailed scenario analyses
6. Management slides, PDFs and diagrams

Do **not** turn a recommendation, assumption or future capability into a current-state fact unless it has been explicitly validated.

## Architecture rules

- Maintain the separation between **CURRENT / STABLE** and **FUTURE / TO-BE**.
- Treat the exact current GTM health-check implementation as unverified unless evidence is added to the repository.
- Do not assume TCP/port health checks, Layer-7 health checks, iQuery behaviour, cross-site probing, or application readiness endpoints are deployed unless confirmed.
- Preserve the distinction between external VIPs, internal VIPs, application endpoints, WAF/LTM health, downstream application health and shared-dependency health.
- Internal enterprise DNS may delegate or forward selected endpoint namespaces to the edge GTM service; do not collapse internal and external DNS flows into a single generic path.
- Avoid diagrams that imply a component is healthy merely because a device or port is reachable.
- Avoid target-state diagrams that visually look like deployed current state.

## Health-monitoring target

The target direction is a layered health model:

- LTM/ELB performs fast local member/service recovery.
- GTM makes DNS/site decisions based on Layer-7 health of published service VIPs.
- External names should reflect the health of the published external VIP/service.
- Internal delegated names should reflect the corresponding internal VIP/service.
- Application teams define stable readiness checks for application-specific endpoints.
- Shared or downstream dependency health should be evaluated at the correct service/dependency layer rather than blindly embedded in every top-level probe.
- Independent synthetic monitoring should validate the real user/SLO outcome.

The design should minimise both **false green** and **false red** health states.

## Documentation and diagram changes

When changing architecture:

- Update the authoritative Markdown first.
- Update related Mermaid/SVG/source diagrams where applicable.
- Check that management slides/PDFs remain consistent with the Markdown source.
- Keep current-state and target-state diagrams visually distinct.
- Use the same terminology across Markdown, diagrams and slides.
- Do not edit generated binary artifacts without also updating their maintainable source where one exists.

For management outputs, review:

- `management-artifacts/`
- `management-artifacts/diagrams/`
- `management-artifacts/source/`

## Change discipline

- Prefer a small, coherent branch and pull request.
- Do not rewrite unrelated architecture material.
- Preserve useful uncertainty explicitly using labels such as **validated**, **assumption**, **to confirm**, **target**, or **future**.
- If a task requires an architecture decision that is not supported by repository evidence, document it as an assumption or recommendation rather than silently treating it as fact.
- Check links and cross-references after renames or document moves.

## Before completing a task

Confirm that:

- current state is not mixed with target state;
- health-check ownership is clear by layer;
- internal and external DNS/VIP paths are represented correctly;
- diagrams match the authoritative Markdown;
- slide-layer breakdowns remain consistent with the architecture;
- assumptions and unknowns remain visible;
- all touched files tell the same architectural story.
