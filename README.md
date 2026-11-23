# EnterpriseWAF

Enterprise architecture analysis for resilient F5-based application delivery and WAF design.

The current analysis focuses on a two-site enterprise environment using F5 BIG-IP DNS/GTM, LTM and Advanced WAF/ASM, with multiple tenant/hosting environments and a mix of stateless web, stateful web, WebSocket/long-lived and non-web applications.

## Start here

The current authoritative analysis is under:

- [enterprise-scenarios/](./enterprise-scenarios/)

For the document map and reading order, see:

- [Enterprise scenario analysis index](./enterprise-scenarios/README.md)

## Current analysis structure

The analysis is deliberately separated into **stable inputs**, **changeable inputs**, and **derived outputs** so that new design options can be evaluated without constantly shifting the baseline.

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
    Lens 1: failure       Lens 2: maintainability
    common_failure_       maintainability_change_
    matrix.md             management_analysis.md

Supporting derived study:
`cross_site_routing_and_dependency_recovery.md`

## Scope

The current baseline assumes:

- two enterprise sites;
- approximately 3–4 tenant/hosting environments in the wider estate;
- one representative tenant used for most worked examples;
- similar GTM/LTM roles in both sites;
- W1–W3 normally use equivalent WAF topology in both sites;
- W4 is deliberately asymmetric: Site 1 has a WAF HA cluster plus an extra active/spare WAF, while Site 2 has only the WAF HA cluster;
- external users access services through private leased-line paths and edge firewalls;
- externally reachable application VIPs live on the firewall tier;
- internal users may bypass the WAF and use internal service/ELB paths;
- applications may run on-premises, on VMs, Kubernetes or PaaS;
- Application A -> Application B dependencies are treated as first-class resilience scenarios.

Supported application types include:

1. stateless web applications;
2. stateful web applications;
3. socket/WebSocket/long-lived connection applications;
4. non-web/L4 applications that may bypass the WAF.

## Analysis lenses

### Lens 1 — Failure and recovery

Primary output:

- [Common failure matrix](./enterprise-scenarios/common_failure_matrix.md)

Covers GTM/DNS, leased-line, firewall, LTM, WAF, backend, cross-site, dependency and full-site failures, including application-specific recovery requirements and F5 recovery-time drivers.

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

1. If the **real enterprise environment changed**, update [enterprise_scenario_invariants.md](./enterprise-scenarios/enterprise_scenario_invariants.md).
2. If a **topology, F5, routing, health, capacity or maintenance assumption changed**, update [analysis_variables_and_f5_assumptions.md](./enterprise-scenarios/analysis_variables_and_f5_assumptions.md).
3. If neither changed, do not change the baseline just to reach a different conclusion.
4. Regenerate/review the derived analyses using [enterprise_scenario_analysis_prompt.md](./enterprise-scenarios/enterprise_scenario_analysis_prompt.md).

## WAF topology shorthand

| ID | WAF topology |
|---|---|
| **W1** | LTM-fronted scalable independent WAF pool, normally 2..N WAFs per site |
| **W2** | WAF HA cluster, with or without an ingress LTM |
| **W3** | Tenant-preferred WAFs plus shared enterprise reserve WAFs |
| **W4** | Asymmetric: Site 1 WAF HA cluster + extra active/spare WAF; Site 2 WAF HA cluster only |

Site-level GTM recovery is common to all topologies and is **not** a separate WAF topology.

## Authoritative vs working/legacy documents

The files under `enterprise-scenarios/` listed in its README are the current authoritative set for this analysis.

The following root-level documents are older/reference material and may contain assumptions that pre-date the current invariant/variable model:

- `waf_architecture_options_cross_site_resilience.md`
- `f5_failover_failure_V4_matrix_footnotes.md`
- `f5_failover_failure_matrix-v3.md`
- `waf_websocket_resilience_cloud_patterns.md`

Use them as background unless/until they are explicitly reconciled with the authoritative scenario set.

## Current development status

The current scenario-analysis rework is being developed on:

- branch: `analysis/enterprise-scenarios-round-2`
- draft PR: [Round 2: enterprise WAF scenario and failure analysis](https://github.com/jfang88/EnterpriseWAF/pull/1)

Once merged, the relative links in this README will continue to point to the authoritative files on the default branch.