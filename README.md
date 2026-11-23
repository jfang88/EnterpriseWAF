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
    Lens 1: service       Lens 2: maintainability
    impact/recovery       /change safety
              |
              +--> end_to_end_service_impact_analysis.md
              +--> common_failure_matrix.md (technical appendix)

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

1. stateless web applications;
2. stateful web applications;
3. socket/WebSocket/long-lived connection applications;
4. non-web/L4 applications that may bypass the WAF.

## Analysis lenses

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

1. If the **real enterprise environment changed**, update [enterprise_scenario_invariants.md](./enterprise-scenarios/enterprise_scenario_invariants.md).
2. If a **topology, F5, routing, health, capacity or maintenance assumption changed**, update [analysis_variables_and_f5_assumptions.md](./enterprise-scenarios/analysis_variables_and_f5_assumptions.md).
3. If neither changed, do not change the baseline just to reach a different conclusion.
4. Regenerate/review the derived analyses using [enterprise_scenario_analysis_prompt.md](./enterprise-scenarios/enterprise_scenario_analysis_prompt.md).

## LTM/WAF node-count appendix

For the difference between 2- and 3-device DSC groups versus true active WAF pools, see:

- [2 vs 3 BIG-IP LTM and WAF nodes](./enterprise-scenarios/appendix_ltm_waf_2_vs_3_nodes.md)

The baseline remains **two LTMs per site**.

## WAF topology shorthand

| ID | WAF topology |
|---|---|
| **W1** | LTM-fronted scalable independent WAF pool, normally 2..N WAFs per site |
| **W2** | WAF HA cluster, with or without an ingress LTM |
| **W3** | Tenant-preferred WAFs plus shared enterprise reserve WAFs |
| **W4** | Asymmetric: Site 1 WAF HA cluster + extra active/spare WAF; Site 2 WAF HA cluster only |

Site-level GTM recovery is common to all topologies and is **not** a separate WAF topology.

## Authoritative, supporting and archived documents

The files under [`enterprise-scenarios/`](./enterprise-scenarios/README.md) are the current authoritative analysis set.

Current specialist guidance retained at the repository root:

- [WebSocket resilience and cloud patterns](./waf_websocket_resilience_cloud_patterns.md) — application-level reconnect, replay, idempotency, draining, reconnect storms and SSE guidance. Current W1-W4 topology/timing files take precedence.

Older architecture/failure-analysis versions have been moved to:

- [`archive/`](./archive/README.md)

The archive contains the superseded Design A/Design B architecture paper, V4/V3 failure matrices and the Round 2 working-history file. Do not use archived topology or timing tables as the current baseline.

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
- [Enterprise scenario analysis index](./enterprise-scenarios/README.md)
- [End-to-end service impact and recoverability analysis](./enterprise-scenarios/end_to_end_service_impact_analysis.md) — **primary resilience/recovery document**
