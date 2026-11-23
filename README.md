# EnterpriseWAF

Enterprise architecture analysis for resilient F5-based application delivery and WAF design.

The current analysis focuses on a two-site enterprise environment using F5 BIG-IP DNS/GTM, LTM and Advanced WAF/ASM, with multiple tenant/hosting environments and a mix of stateless web, stateful web, WebSocket/long-lived and non-web applications.

## Start here

The current authoritative analysis is under:

- [enterprise-scenarios/](./enterprise-scenarios/)

For the document map and reading order, see:

- [Enterprise scenario analysis index](./enterprise-scenarios/README.md)

For the high-level architecture and entity/relationship view, start with:

- [High-level EnterpriseWAF architecture](./enterprise-scenarios/high_level_architecture.md)

This is the canonical diagram for external/internal consumers, DNS namespaces, network paths, LTM/WAF/CFW/ELB layers, application hosting and App A -> B -> C/D dependencies.

For the authoritative W/S/X/T/AT shorthand and the reference end-to-end path, use:

- [Canonical architecture shorthand and end-to-end topology](./enterprise-scenarios/architecture_shorthand_topology_reference.md)

For the executive decision and final recommendation, then read:

- [Executive architecture and 99.95% recommendation](./enterprise-scenarios/executive_recommendation.md)

Then use:

- [Deployment options, resilience and four-tenant cost summary](./enterprise-scenarios/deployment_options_resilience_summary.md) for the detailed option comparison

## Current analysis structure

The analysis is deliberately separated into **canonical terminology/topology**, **stable inputs**, **changeable inputs**, and **derived outputs** so that new design options can be evaluated without constantly shifting the baseline.

    canonical W/S/X/T/AT shorthand + path
            |
            v
    architecture_shorthand_topology_reference.md
            |
            v
    Stable enterprise facts
            |
            v
    enterprise_scenario_invariants.md
            |
            +-------------------+
            |                   |
            v                   v
    changeable topology /       regeneration prompt
    F5 / change assumptions          |
            |                        |
            v                        |
    analysis_variables_...md         |
            |                        |
            +-----------+------------+
                        |
              +---------+---------+
              |                   |
              v                   v
    Lens 1: service       Lens 2: maintainability
    impact/recovery       /change safety
              |
              +--> end_to_end_service_impact_analysis.md
              +--> common_failure_matrix.md (technical appendix)

High-level entity/relationship view:
`high_level_architecture.md`

Supporting derived study:
`cross_site_routing_and_dependency_recovery.md`

## Scope

The current baseline assumes:

- two enterprise sites;
- approximately 3–4 tenant/hosting environments in the wider estate;
- one representative tenant used for most worked examples;
- similar GTM/LTM roles in both sites;
- **two LTMs per site is the default LTM baseline**; three-device LTM DSC is optional analysis only;
- W1–W3 normally use equivalent WAF topology in both sites;
- W4 is deliberately asymmetric: Site 1 has a WAF HA cluster plus an extra active/spare WAF, while Site 2 has only the WAF HA cluster;
- external users access services through private leased-line paths and edge firewalls;
- externally reachable application VIPs live on the firewall tier;
- external and internal DNS namespaces are separate;
- internal users/applications use internal enterprise DNS, with selected internal service names optionally delegated/forwarded to GTM;
- internal users may bypass the WAF and use internal service paths;
- private-cloud application paths include a distinct platform/cloud firewall (CFW) immediately in front of the ELB/service tier;
- applications may run on-premises, on VMs, Kubernetes or PaaS;
- Application A -> Application B -> Application C and shared-dependency chains are treated as first-class resilience scenarios.

Supported application types include:

1. **AT1** — stateless web applications;
2. **AT2** — stateful web applications;
3. **AT3** — socket/WebSocket/long-lived connection applications;
4. **AT4** — non-web/L4 applications that may bypass the WAF.

## Analysis lenses

### High-level architecture

Primary entity/relationship and traffic-path view:

- [High-level EnterpriseWAF architecture](./enterprise-scenarios/high_level_architecture.md)

This distinguishes generic network/application-delivery infrastructure from the WAF enforcement platform and the **application-coupled WAF policy**.

### Canonical shorthand and topology

Single terminology/timing source of truth:

- [Canonical architecture shorthand and end-to-end topology](./enterprise-scenarios/architecture_shorthand_topology_reference.md)

Use this for W1-W4, D1/S1-S3, X1/X2/XD1, T1-T9 and AT1-AT4 meanings. Do not reuse W1/W2/W3 as WAF-node names or S1/S2 as site labels.

### Executive recommendation

Primary decision summary:

- [Executive architecture and 99.95% recommendation](./enterprise-scenarios/executive_recommendation.md)

This states the preferred four-tenant architecture, the highest-isolation alternative, the 99.95% availability potential of each option, and the change/recovery conditions required before the target can be claimed.

### Architecture option summary

Detailed comparison:

- [Deployment options, resilience and four-tenant cost summary](./enterprise-scenarios/deployment_options_resilience_summary.md)

This compares W1-W4, dedicated versus shared capacity, one/two-node and cluster/tier failure tolerance, cross-site versus local-only recovery, application-type behavior, and an illustrative four-tenant LTM/WAF device-count model.

### Lens 1 — End-to-end service impact and recovery

**Primary output:**

- [End-to-end service impact and recoverability analysis](./enterprise-scenarios/end_to_end_service_impact_analysis.md)

This is the main service/user story. It explains what external human users, external API/system clients, internal users and App A/B/C dependencies experience, how long the interruption lasts, and whether recovery is automatic, manual or not possible with the current design.

**Technical supporting matrix:**

- [Common technical failure matrix](./enterprise-scenarios/common_failure_matrix.md)

The technical matrix contains the component-by-component F5/infrastructure detail and timing drivers used to support the end-to-end service conclusions.

### Lens 2 — Maintainability and change safety

Primary output:

- [Maintainability, change management and availability analysis](./enterprise-scenarios/maintainability_change_management_analysis.md)

Covers monitoring difficulty, firmware/software upgrades, WAF policy/signature deployment, LTM/GTM changes, config sync, BIG-IQ/change tooling, rolling upgrades, canary/blue-green patterns, draining, rollback, staggered changes and 99.95% availability considerations.

## Cross-site routing and dependency recovery

Supporting analysis:

- [Cross-site WAF/LTM routing and application dependency recovery](./enterprise-scenarios/cross_site_routing_and_dependency_recovery.md)

This evaluates remote-WAF borrowing, remote front-end route-back, conventional site failover, and App A remaining local while using App B in the alternate site.

## Change-control model

Before modifying the analysis:

1. If the **canonical shorthand or canonical path changed**, update [architecture_shorthand_topology_reference.md](./enterprise-scenarios/architecture_shorthand_topology_reference.md) first.
2. If the **real enterprise environment changed**, update [enterprise_scenario_invariants.md](./enterprise-scenarios/enterprise_scenario_invariants.md).
3. If a **topology, F5, routing, health, capacity or maintenance assumption changed**, update [analysis_variables_and_f5_assumptions.md](./enterprise-scenarios/analysis_variables_and_f5_assumptions.md).
4. If none changed, do not change the baseline just to reach a different conclusion.
5. Regenerate/review the derived analyses using [enterprise_scenario_analysis_prompt.md](./enterprise-scenarios/enterprise_scenario_analysis_prompt.md).

## LTM/WAF node-count appendix

For the difference between 2- and 3-device DSC groups versus true active WAF pools, see:

- [2 vs 3 BIG-IP LTM and WAF nodes](./enterprise-scenarios/appendix_ltm_waf_2_vs_3_nodes.md)

The baseline remains **two LTMs per site**.

## WAF topology and sharing shorthand

| ID | Meaning |
|---|---|
| **W1** | LTM-fronted scalable independent **active** WAF pool, normally 2..N WAFs per site |
| **W2** | WAF HA/DSC cluster, with or without an ingress LTM |
| **W3** | Tenant-preferred active WAFs plus shared enterprise reserve WAFs |
| **W4** | Asymmetric: Site 1 WAF HA cluster + extra active/spare WAF; Site 2 WAF HA cluster only |
| **S1** | Tenant-specific LTM HA pairs feeding a shared independent active WAF pool |
| **S2** | Shared LTM HA pair feeding a shared independent active WAF pool |

**W1-W4 describe WAF topology patterns. S1/S2 describe tenancy/sharing patterns.** They are compared together in the executive summary because the final architecture decision needs both dimensions.

Use [the canonical reference](./enterprise-scenarios/architecture_shorthand_topology_reference.md) for the full W/S/X/T/AT definitions.

Site-level GTM recovery is common to all topologies and is **not** a separate WAF topology.

## Authoritative, supporting and archived documents

The files under [`enterprise-scenarios/`](./enterprise-scenarios/README.md) are the current authoritative analysis set.

Current specialist guidance retained at the repository root:

- [WebSocket resilience and cloud patterns](./waf_websocket_resilience_cloud_patterns.md) — application-level reconnect, replay, idempotency, draining, reconnect storms and SSE guidance. Current terminology/timing in the canonical reference takes precedence.

Older architecture/failure-analysis versions have been moved to:

- [`archive/`](./archive/README.md)

The archive contains the superseded Design A/Design B architecture paper, V4/V3 failure matrices and the Round 2 working-history file. Archived W/S labels may have historical meanings; do not use them as the current baseline.

## Branch strategy

`main` is the **single authoritative branch** for the EnterpriseWAF documentation.

For future changes:

1. create one short-lived working branch for a coherent change;
2. review it in a pull request;
3. merge it back to `main`;
4. retire the working branch after merge;
5. avoid long-lived branches for individual analysis lenses or Markdown files.

## Current status

The consolidated enterprise scenario analysis is now published on `main`.

Use these as the primary entry points:

- [Repository README](./README.md)
- [High-level EnterpriseWAF architecture](./enterprise-scenarios/high_level_architecture.md) — **canonical entity/relationship and traffic-path view**
- [Canonical architecture shorthand and end-to-end topology](./enterprise-scenarios/architecture_shorthand_topology_reference.md) — **canonical W/S/X/T/AT definitions**
- [Executive architecture and 99.95% recommendation](./enterprise-scenarios/executive_recommendation.md)
- [Enterprise scenario analysis index](./enterprise-scenarios/README.md)
- [End-to-end service impact and recoverability analysis](./enterprise-scenarios/end_to_end_service_impact_analysis.md) — **primary resilience/recovery document**
