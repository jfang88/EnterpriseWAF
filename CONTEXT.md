# CONTEXT.md

## Purpose

This file is a short orientation and bootstrap guide for ChatGPT, Codex and other agents working on EnterpriseWAF.

It is **not** an architecture source of truth and intentionally avoids duplicating the detailed current- or target-state specifications.

If this file conflicts with a canonical architecture document, the canonical document wins.

## Canonical sources

### Current / stable

`enterprise-scenarios/current_architecture_and_invariants.md`

Authoritative for:

- current topology and failure domains;
- stable infrastructure and DNS/GTM facts;
- external and internal application paths;
- architecture planes and parallel-path model;
- current BIG-IP 17.5.x software baseline and health-check unknowns;
- application dependency grounding;
- availability and RTO rules;
- canonical current-state diagram.

### Future / to-be

`enterprise-scenarios/future_architecture_improvements.md`

Authoritative for:

- target Layer-7 health-monitoring design;
- GTM external/internal VIP health decisions;
- readiness-check ownership;
- prober diversity and cross-site visibility;
- dependency-local recovery;
- cross-site contingency improvements;
- platform rebuild impact (BIG-IP 17.5.x -> BIG-IP 21.1.x+ on confirmed rSeries `r2800` pizza boxes running `F5OS-A 1.8.0+`, no blade chassis);
- synthetic/SLO validation;
- implementation and acceptance gates.

## Essential project orientation

The project analyses a two-site, multi-tenant **end-to-end application-delivery environment** (currently **BIG-IP 17.5.x**, with a confirmed target rebuild standard of **F5 rSeries `r2800` pizza boxes** running `F5OS-A 1.8.0+` + BIG-IP 21.1.x+, no blade chassis), with an **initial delivery focus on the WAF tier** (and its F5 LTM/GTM interfaces) because firewalls, private-cloud CFW/ELB, and applications are owned by partner teams. The end-to-end path includes:

- BIG-IP DNS/GTM for DNS/site selection;
- edge firewalls (*Network/Security owned*);
- tenant LTM services;
- WAF capacity (*initial Phase 1 execution focus*);
- internal enterprise DNS and internal service paths;
- a separate internal firewall (*Network/Security owned*) and private-cloud firewall (CFW) (*Cloud Platform owned*);
- ELB/service layers (*Cloud Platform owned*);
- VM, Kubernetes, PaaS and on-premises application hosting (*Application teams*);
- App A/B/C/D dependency chains;
- a **99.95% total availability objective (`4h 22m 48s / year`) covering BOTH managed (planned maintenance/changes) and unmanaged (unplanned failure) outages combined**.

External and internal users may use different DNS paths and different VIPs.

GTM is a **DNS control-plane / endpoint-selection service**, not an inline application-data proxy.

Site 1 and Site 2 are separate failure domains.

## Important current-state uncertainty

The exact deployed GTM health-monitoring model is not assumed to be known.

Until validated, do not assume:

- TCP/port versus HTTP/Layer-7 monitor type;
- direct GTM checks of each external VIP;
- direct GTM checks of each internal VIP;
- iQuery-derived application health;
- cross-site GTM probing;
- readiness endpoints for every application;
- end-to-end CFW -> ELB -> application validation;
- automatic cross-site dependency fallback.

These are **unknown / validate** unless evidence is added to the canonical current-state document.

## Current versus target rule

Use this decision:

```text
True and validated in the real environment today?
    -> current_architecture_and_invariants.md

Desired, recommended or not yet deployed?
    -> future_architecture_improvements.md

Selectable topology, product behaviour or implementation assumption?
    -> analysis_variables_and_f5_assumptions.md

Conclusion derived from those inputs?
    -> scenario / failure / resilience / executive analysis
```

Do not draw a target capability as a current-state feature.

## Supporting analyses

Use topic-specific documents as needed, including:

- `enterprise-scenarios/analysis_variables_and_f5_assumptions.md`
- `enterprise-scenarios/common_failure_matrix.md`
- `enterprise-scenarios/end_to_end_service_impact_analysis.md`
- `enterprise-scenarios/cross_site_routing_and_dependency_recovery.md`
- `enterprise-scenarios/maintainability_change_management_analysis.md`
- `enterprise-scenarios/executive_recommendation.md`
- `enterprise-scenarios/deployment_options_resilience_summary.md`
- `waf_websocket_resilience_cloud_patterns.md`

The repository `README.md` and `enterprise-scenarios/README.md` provide the full document map.

## Working convention

Use `AGENTS.md` for agent operating rules.

Use this file for fast orientation.

Use the canonical current- and target-state Markdown for architecture facts and decisions.

When a current-state fact changes, update `enterprise-scenarios/current_architecture_and_invariants.md` first, then update derived analyses, diagrams and management artifacts as required.
