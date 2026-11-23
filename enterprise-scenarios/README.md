# Enterprise Scenario Analysis — Document Index

This folder contains the current authoritative EnterpriseWAF scenario-analysis set.

If you only want the current conclusions, start with:

1. **[Executive architecture and 99.95% recommendation](./executive_recommendation.md)** — final recommendation and ranked options
2. **[Canonical architecture shorthand and end-to-end topology](./architecture_shorthand_topology_reference.md)** — authoritative W/S/X/T definitions and full logical path
3. **[Deployment options, resilience and four-tenant cost summary](./deployment_options_resilience_summary.md)** — detailed architecture/topology comparison
4. **[End-to-end service impact and recoverability](./end_to_end_service_impact_analysis.md)** — primary user/service failure story
5. [Maintainability / change-management analysis](./maintainability_change_management_analysis.md)
6. [Cross-site routing and dependency recovery](./cross_site_routing_and_dependency_recovery.md)
7. [Common technical failure matrix](./common_failure_matrix.md) — component-level supporting detail

## Document map

| File | Type | Purpose | Change frequency |
|---|---|---|---|
| [executive_recommendation.md](./executive_recommendation.md) | **Executive decision summary** | Final recommendation, 99.95 potential, ranked options and approval gates | Update when conclusions materially change |
| [architecture_shorthand_topology_reference.md](./architecture_shorthand_topology_reference.md) | **Canonical terminology/topology reference** | Single source of truth for W1-W4, S1-S3/D1, X1/X2/XD1, T1-T9 and the end-to-end logical layout | Update whenever shorthand or canonical path changes |
| [deployment_options_resilience_summary.md](./deployment_options_resilience_summary.md) | **Primary architecture summary** | W1-W4, dedicated/shared four-tenant cost, N-1/N-2/tier failure tolerance, cross-site comparison and application-type resilience | Regenerate when topology/capacity/tenancy assumptions change |
| [enterprise_scenario_invariants.md](./enterprise_scenario_invariants.md) | **Invariant input** | Stable enterprise context, application types, sites, tenant model, design objectives and 99.95 maintainability objective | Rare |
| [analysis_variables_and_f5_assumptions.md](./analysis_variables_and_f5_assumptions.md) | **Variable input** | W1–W4 topologies, GTM health models, cross-site patterns, F5 timing assumptions, maintenance/change strategies | As designs change |
| [end_to_end_service_impact_analysis.md](./end_to_end_service_impact_analysis.md) | **Primary derived output — Lens 1** | External/internal user impact, App A/B/C dependency impact, outage timing, recoverability and cross-site/local-only result | Regenerate when inputs change |
| [common_failure_matrix.md](./common_failure_matrix.md) | **Technical appendix — Lens 1** | Component-level failure scenarios, F5 recovery paths/timing drivers and topology details supporting the service-impact analysis | Regenerate when inputs change |
| [maintainability_change_management_analysis.md](./maintainability_change_management_analysis.md) | **Derived output — Lens 2** | Monitoring, firmware, WAF/LTM/GTM changes, blue-green/canary, draining, rollback and 99.95 maintainability assessment | Regenerate when inputs change |
| [cross_site_routing_and_dependency_recovery.md](./cross_site_routing_and_dependency_recovery.md) | **Derived supporting study** | Cross-site WAF/LTM route-back and App A -> App B dependency recovery | Update when cross-site model changes |
| [enterprise_scenario_analysis_prompt.md](./enterprise_scenario_analysis_prompt.md) | **Regeneration/orchestration prompt** | Instructions for consistently rebuilding both analysis lenses from the invariant + variable inputs | Update when analysis scope changes |
| [appendix_ltm_waf_2_vs_3_nodes.md](./appendix_ltm_waf_2_vs_3_nodes.md) | **Supporting appendix** | Explains 2 vs 3 LTM/WAF nodes, DSC active/standby vs active-active traffic groups, and independent load-balanced WAF pools | Update when node-count/HA design changes |

## The key rule

Do not put every new fact into every document.

Use this decision:

    Is it a real, stable property of the enterprise?
            |
           yes
            v
    enterprise_scenario_invariants.md

            no
            |
            v
    Is it a topology / F5 / routing / health / maintenance choice?
            |
           yes
            v
    analysis_variables_and_f5_assumptions.md

            |
            v
    Is it a conclusion produced from those inputs?
            |
           yes
            v
    derived analysis document

Use [architecture_shorthand_topology_reference.md](./architecture_shorthand_topology_reference.md) whenever a shorthand label or canonical path is needed. This prevents W/S/T definitions from drifting between documents.

## Current enterprise context

The baseline currently models:

- two sites;
- approximately 3–4 tenants/hosting environments in the wider estate;
- one representative tenant for most worked examples;
- equivalent GTM/LTM roles per site;
- W1–W3 with equivalent WAF topology in both sites;
- W4 as the deliberate asymmetric exception;
- edge-firewall-owned external application VIPs;
- private leased-line external-user ingress;
- separate external and internal DNS namespaces;
- internal users/applications using internal enterprise DNS, with selected internal service names optionally delegated/forwarded to GTM;
- internal users potentially bypassing WAF;
- a distinct platform/cloud firewall (CFW) layer in front of private-cloud ELB/service endpoints;
- on-prem, VM, Kubernetes and PaaS application hosting;
- App A -> App B -> App C and shared-dependency chains.

## Application types

Every relevant scenario must distinguish:

- **AT1 — stateless web**
- **AT2 — stateful web**
- **AT3 — WebSocket/socket/long-lived**
- **AT4 — non-web/L4 bypassing WAF**

The `AT` prefix is deliberate: it avoids confusing application-type shorthand with application/site-instance notation such as App A @ Site 1.

Infrastructure recovery is not considered complete until the application-type-specific recovery is also satisfied.

Examples:

- stateless web may only need request retry;
- stateful web may need session/state recovery;
- WebSocket may need reconnect, re-authentication, re-subscription and replay;
- non-web protocols need protocol-specific reconnect/recovery.

## Current topology set

For the authoritative definitions, see [Canonical Architecture Shorthand and End-to-End Topology Reference](./architecture_shorthand_topology_reference.md).

### W1 — scalable independent WAF pool

Per site:

    Firewall VIP
        |
    LTM HA pair
        |
    WAF-1  WAF-2 ... WAF-n
        |
       CFW
        |
    ELB / service
        |
    application

### W2 — WAF HA cluster

With or without ingress LTM:

    Firewall VIP
        |
    [LTM HA pair]
        |
    WAF HA cluster
        |
       CFW
        |
    ELB / service
        |
    application

### W3 — tenant WAFs + shared reserve

The **baseline is two LTMs per site** in a 2-device Sync-Failover pair (**W3-L2**). A 3-device Sync-Failover group (**W3-L3**) is an optional comparison only when additional maintenance/second-failure headroom is being evaluated.

    Tenant LTM DSC service
        |
    preferred WAFs
        |
    shared reserve WAF capacity
        |
       CFW
        |
    ELB / application

### W4 — asymmetric cluster + extra Site 1 WAF

    Site 1                         Site 2
    [LTM HA pair]                  [LTM HA pair]
         |                              |
    WAF HA cluster                 WAF HA cluster
         |                              |
    extra active/spare WAF              |
         |                              |
        CFW                            CFW
         |                              |
     ELB / app                      ELB / app

The brackets indicate variants with/without an ingress LTM where relevant.

### S1 — tenant LTMs + shared active WAF pool

    Tenant 1 LTM pair --\
    Tenant 2 LTM pair ---\
    Tenant 3 LTM pair ----> shared independent active WAF pool
    Tenant 4 LTM pair ---/                  |
                                             v
                                         CFW / ELB / app

S1 is a **tenancy/sharing pattern**, not a replacement definition for W1. It applies the independent-active-pool idea across several tenant LTM boundaries.

### S2 — shared LTM + shared active WAF pool

    Tenants 1..4
         |
    shared LTM pair
         |
    shared independent active WAF pool
         |
      CFW / ELB / app

S2 has the largest shared ingress failure/change domain among the active-pool options.

## Analysis sequence

When re-running the work:

1. Read [enterprise_scenario_invariants.md](./enterprise_scenario_invariants.md).
2. Read [architecture_shorthand_topology_reference.md](./architecture_shorthand_topology_reference.md).
3. Read [analysis_variables_and_f5_assumptions.md](./analysis_variables_and_f5_assumptions.md).
4. Use [enterprise_scenario_analysis_prompt.md](./enterprise_scenario_analysis_prompt.md).
5. Regenerate/review [deployment_options_resilience_summary.md](./deployment_options_resilience_summary.md).
6. Regenerate/review [end_to_end_service_impact_analysis.md](./end_to_end_service_impact_analysis.md).
7. Regenerate/review [common_failure_matrix.md](./common_failure_matrix.md) as the technical supporting matrix.
8. Regenerate/review [maintainability_change_management_analysis.md](./maintainability_change_management_analysis.md).
9. Update [cross_site_routing_and_dependency_recovery.md](./cross_site_routing_and_dependency_recovery.md) if cross-site assumptions changed.
10. Use the [archive](../archive/README.md) only for historical traceability; do not promote archived assumptions implicitly.

## Output locations

For quick access:

- **Executive recommendation:** [executive_recommendation.md](./executive_recommendation.md)
- **Canonical shorthand/topology:** [architecture_shorthand_topology_reference.md](./architecture_shorthand_topology_reference.md)
- **Architecture/topology summary:** [deployment_options_resilience_summary.md](./deployment_options_resilience_summary.md)
- **Primary failure/resilience result:** [end_to_end_service_impact_analysis.md](./end_to_end_service_impact_analysis.md)
  - **Timing summary:** see sections 4.2–4.4 for validated LTM/GTM/DNS recovery windows, CFW recovery effects, and cache/connection behavior
- **Technical failure matrix:** [common_failure_matrix.md](./common_failure_matrix.md)
- **Maintainability result:** [maintainability_change_management_analysis.md](./maintainability_change_management_analysis.md)
- **Cross-site result:** [cross_site_routing_and_dependency_recovery.md](./cross_site_routing_and_dependency_recovery.md)
- **Baseline:** [enterprise_scenario_invariants.md](./enterprise_scenario_invariants.md)
- **Changeable assumptions:** [analysis_variables_and_f5_assumptions.md](./analysis_variables_and_f5_assumptions.md)
- **Regeneration prompt:** [enterprise_scenario_analysis_prompt.md](./enterprise_scenario_analysis_prompt.md)
- **2 vs 3 LTM/WAF appendix:** [appendix_ltm_waf_2_vs_3_nodes.md](./appendix_ltm_waf_2_vs_3_nodes.md)

## Archive and specialist references

Historical versions and working notes are under [`../archive/`](../archive/README.md). They are retained for traceability, not as inputs to the current analysis. Historical `W1/W2/S1/S2` labels inside archived diagrams may be node/site identifiers and are not current shorthand.

The root-level [WebSocket resilience document](../waf_websocket_resilience_cloud_patterns.md) remains a current specialist reference for application reconnect/replay/SSE behavior. Current topology, DNS namespace and timing definitions in this folder take precedence.

### Branch rule

Do not create separate long-lived branches for these documents.

Use one coherent working branch/PR, merge it into `main`, then delete the working branch after merge.
