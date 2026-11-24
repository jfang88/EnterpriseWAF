# Enterprise Scenario Analysis — Document Index

This folder contains the current authoritative EnterpriseWAF architecture and resilience analysis.

# Start here

1. **[Current architecture and stable invariants](./current_architecture_and_invariants.md)** — authoritative current-state facts, topology, layers, DNS control plane and traffic paths
2. **[Future architecture improvements](./future_architecture_improvements.md)** — target health-check model, cross-site/dependency improvements and implementation sequence
3. **[Executive architecture and 99.95% recommendation](./executive_recommendation.md)** — ranked WAF/topology decision
4. **[Deployment options, resilience and four-tenant cost summary](./deployment_options_resilience_summary.md)** — detailed W1-W4/S1-S2 comparison
5. **[End-to-end service impact and recoverability](./end_to_end_service_impact_analysis.md)** — user/application failure story
6. [Maintainability / change-management analysis](./maintainability_change_management_analysis.md)
7. [Cross-site routing and dependency recovery](./cross_site_routing_and_dependency_recovery.md)
8. [Common technical failure matrix](./common_failure_matrix.md)

# Current state versus future state

The documentation is deliberately split so diagrams do not accidentally present target improvements as if they already exist.

```text
CURRENT / STABLE
current_architecture_and_invariants.md

FUTURE / TO-BE
future_architecture_improvements.md
        |
        +--> target health monitoring
        +--> GTM L7 endpoint health
        +--> prober diversity / cross-site visibility
        +--> dependency-local recovery
        +--> cross-site contingency
```

# Document map

| File | Type | Purpose |
|---|---|---|
| [current_architecture_and_invariants.md](./current_architecture_and_invariants.md) | **Authoritative current state** | Stable facts, topology/boundaries, DNS control plane, external/internal data paths, layer breakdown, diagrams, known unknowns and 99.95 requirement |
| [future_architecture_improvements.md](./future_architecture_improvements.md) | **Target / to-be architecture** | Layered health-check target, GTM external/internal VIP L7 health, app health contracts, cross-site/dependency improvements |
| [analysis_variables_and_f5_assumptions.md](./analysis_variables_and_f5_assumptions.md) | **Changeable technical inputs** | W1-W4/S1-S2, F5 timing, routing and product assumptions |
| [executive_recommendation.md](./executive_recommendation.md) | **Executive decision** | Final WAF/topology recommendation and 99.95 potential |
| [deployment_options_resilience_summary.md](./deployment_options_resilience_summary.md) | **Topology comparison** | N-1/N-2, four-tenant cost, cross-site comparison, application-type resilience |
| [end_to_end_service_impact_analysis.md](./end_to_end_service_impact_analysis.md) | **Service-impact analysis** | External/internal/dependency outage and recovery outcome |
| [common_failure_matrix.md](./common_failure_matrix.md) | **Technical appendix** | Component failure scenarios and timing drivers |
| [maintainability_change_management_analysis.md](./maintainability_change_management_analysis.md) | **Change-safety lens** | Upgrades, WAF changes, rollback and 99.95 maintainability |
| [cross_site_routing_and_dependency_recovery.md](./cross_site_routing_and_dependency_recovery.md) | **Supporting target study** | X2A/X2B/X2C/XD1 recovery patterns |
| [enterprise_scenario_analysis_prompt.md](./enterprise_scenario_analysis_prompt.md) | **Regeneration prompt** | Rules for keeping current-state and future-state outputs consistent |

# Key documentation rule

Use this decision:

```text
Is it true of the real environment today?
  -> current-state / invariant file

Is it desired but not yet proven/deployed?
  -> future_architecture_improvements.md

Is it a selectable topology / product configuration?
  -> analysis_variables_and_f5_assumptions.md

Is it a conclusion from those inputs?
  -> derived analysis document
```

# Current architecture facts

The current baseline includes:

- two sites;
- one BIG-IP DNS/GTM cluster per site, with cross-site GTM synchronization;
- two HA edge-firewall pairs per tenant/site, two devices per pair (2 x 2);
- GTM/DNS inside the edge-firewall boundary;
- external/customer DNS reaching edge GTM over the private leased-line/VPN path;
- internal enterprise DNS delegating/forwarding selected names to the same edge GTM service;
- two-LTM HA pair as the default tenant/site LTM model;
- internal users/DNS/internal LTM outside private cloud;
- a distinct internal firewall before the private-cloud CFW;
- CFW and ELB/service inside the private-cloud delivery path;
- App A/B/C/D dependency chains;
- a 99.95% service-availability target.

The exact current GTM health-check implementation is **not yet treated as known**. Port-vs-L7, external/internal VIP checks, iQuery integration, prober distribution and app readiness contracts must be validated.

# Target health-check direction

The target described in [future_architecture_improvements.md](./future_architecture_improvements.md) is layered:

- local LTM/ELB member health for fast local recovery;
- GTM Layer-7 health of the **external VIP** for external DNS/site steering;
- GTM or authoritative LTM/iQuery Layer-7 health of the **internal VIP** for delegated internal names;
- app-team-owned readiness contracts;
- dependency-local health/recovery for App B and other shared services;
- independent user-like synthetic monitoring for the 99.95 SLO.

# WAF topology shorthand

| ID | Meaning |
|---|---|
| **W1** | tenant LTM -> independent active WAF pool |
| **W2** | WAF HA/DSC cluster, with/without ingress LTM |
| **W3** | tenant-preferred WAFs + shared reserve |
| **W4** | asymmetric Site 1 cluster + extra WAF; Site 2 cluster only |
| **S1** | tenant-specific LTM pairs -> shared independent active WAF pool |
| **S2** | shared LTM -> shared independent active WAF pool; future consolidation comparison |

# Analysis sequence

1. Read the combined current architecture and invariant baseline.
2. Read the future-improvement target where to-be behavior is being assessed.
3. Read the changeable F5/topology assumptions.
4. Regenerate/review the executive, deployment, service-impact and maintainability analyses.
5. Keep current-state diagrams visually distinct from target-state diagrams.

# Management artifacts

Current version-controlled management outputs are under [`../management-artifacts/`](../management-artifacts/).

The PowerPoint/PDF should explicitly separate:

- current-state architecture;
- target health-monitoring architecture;
- topology decision;
- failure/recovery and application dependency story;
- 99.95/change-safety evidence required.

# Archive

Historical documents are under [`../archive/`](../archive/README.md) and are retained for traceability only.
