# Enterprise Scenario Analysis — Document Index

This folder contains the current authoritative EnterpriseWAF scenario-analysis set.

If you only want the current conclusions, start with:

1. **[End-to-end service impact and recoverability](./end_to_end_service_impact_analysis.md)** — primary failure/recovery story
2. [Maintainability / change-management analysis](./maintainability_change_management_analysis.md)
3. [Cross-site routing and dependency recovery](./cross_site_routing_and_dependency_recovery.md)
4. [Common technical failure matrix](./common_failure_matrix.md) — component-level supporting detail

## Document map

| File | Type | Purpose | Change frequency |
|---|---|---|---|
| [enterprise_scenario_invariants.md](./enterprise_scenario_invariants.md) | **Invariant input** | Stable enterprise context, application types, sites, tenant model, design objectives and 99.95 maintainability objective | Rare |
| [analysis_variables_and_f5_assumptions.md](./analysis_variables_and_f5_assumptions.md) | **Variable input** | W1–W4 topologies, GTM health models, cross-site patterns, F5 timing assumptions, maintenance/change strategies | As designs change |
| [end_to_end_service_impact_analysis.md](./end_to_end_service_impact_analysis.md) | **Primary derived output — Lens 1** | External/internal user impact, App A/B/C dependency impact, outage timing, recoverability and cross-site/local-only result | Regenerate when inputs change |
| [common_failure_matrix.md](./common_failure_matrix.md) | **Technical appendix — Lens 1** | Component-level failure scenarios, F5 recovery paths/timing drivers and topology details supporting the service-impact analysis | Regenerate when inputs change |
| [maintainability_change_management_analysis.md](./maintainability_change_management_analysis.md) | **Derived output — Lens 2** | Monitoring, firmware, WAF/LTM/GTM changes, blue-green/canary, draining, rollback and 99.95 maintainability assessment | Regenerate when inputs change |
| [cross_site_routing_and_dependency_recovery.md](./cross_site_routing_and_dependency_recovery.md) | **Derived supporting study** | Cross-site WAF/LTM route-back and App A -> App B dependency recovery | Update when cross-site model changes |
| [enterprise_scenario_analysis_prompt.md](./enterprise_scenario_analysis_prompt.md) | **Regeneration/orchestration prompt** | Instructions for consistently rebuilding both analysis lenses from the invariant + variable inputs | Update when analysis scope changes |

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

This prevents the baseline from drifting every time a new topology or scenario is considered.

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

- **A1 — stateless web**
- **A2 — stateful web**
- **A3 — WebSocket/socket/long-lived**
- **A4 — non-web/L4 bypassing WAF**

Infrastructure recovery is not considered complete until the application-type-specific recovery is also satisfied.

Examples:

- stateless web may only need request retry;
- stateful web may need session/state recovery;
- WebSocket may need reconnect, re-authentication, re-subscription and replay;
- non-web protocols need protocol-specific reconnect/recovery.

## Current topology set

### W1 — scalable independent WAF pool

Per site:

    Firewall VIP
        |
    LTM HA pair
        |
    WAF1 WAF2 ... WAFn
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
    application

### W3 — tenant WAFs + shared reserve

The tenant LTM service may be a normal 2-device Sync-Failover pair (**W3-L2**) or a 3-device Sync-Failover group (**W3-L3**) when additional maintenance/second-failure headroom is justified.

    Tenant LTM DSC service
        |
    preferred WAFs
        |
    shared reserve WAF capacity

### W4 — asymmetric cluster + extra Site 1 WAF

    Site 1                         Site 2
    [LTM HA pair]                  [LTM HA pair]
         |                              |
    WAF HA cluster                 WAF HA cluster
         |
    extra active/spare WAF

The brackets indicate variants with/without an ingress LTM where relevant.

## Analysis sequence

When re-running the work:

1. Read [enterprise_scenario_invariants.md](./enterprise_scenario_invariants.md).
2. Read [analysis_variables_and_f5_assumptions.md](./analysis_variables_and_f5_assumptions.md).
3. Use [enterprise_scenario_analysis_prompt.md](./enterprise_scenario_analysis_prompt.md).
4. Regenerate/review [end_to_end_service_impact_analysis.md](./end_to_end_service_impact_analysis.md).
5. Regenerate/review [common_failure_matrix.md](./common_failure_matrix.md) as the technical supporting matrix.
6. Regenerate/review [maintainability_change_management_analysis.md](./maintainability_change_management_analysis.md).
7. Update [cross_site_routing_and_dependency_recovery.md](./cross_site_routing_and_dependency_recovery.md) if cross-site assumptions changed.
8. Use the [archive](../archive/README.md) only for historical traceability; do not promote archived assumptions implicitly.

## Output locations

For quick access:

- **Primary failure/resilience result:** [end_to_end_service_impact_analysis.md](./end_to_end_service_impact_analysis.md)
  - **Timing summary:** see sections 4.2–4.3 for validated LTM/GTM/DNS recovery windows and cache/connection behavior
- **Technical failure matrix:** [common_failure_matrix.md](./common_failure_matrix.md)
- **Maintainability result:** [maintainability_change_management_analysis.md](./maintainability_change_management_analysis.md)
- **Cross-site result:** [cross_site_routing_and_dependency_recovery.md](./cross_site_routing_and_dependency_recovery.md)
- **Baseline:** [enterprise_scenario_invariants.md](./enterprise_scenario_invariants.md)
- **Changeable assumptions:** [analysis_variables_and_f5_assumptions.md](./analysis_variables_and_f5_assumptions.md)
- **Regeneration prompt:** [enterprise_scenario_analysis_prompt.md](./enterprise_scenario_analysis_prompt.md)

## Archive and specialist references

Historical versions and working notes are under [`../archive/`](../archive/README.md). They are retained for traceability, not as inputs to the current analysis.

The root-level [WebSocket resilience document](../waf_websocket_resilience_cloud_patterns.md) remains a current specialist reference for application reconnect/replay/SSE behavior. Current W1-W4 topology, DNS namespace and F5 timing assumptions in this folder take precedence.

### Branch rule

Do not create separate long-lived branches for these documents.

Use one coherent working branch/PR, merge it into `main`, then delete the working branch.
