# EnterpriseWAF

Enterprise architecture analysis for resilient F5-based application delivery and WAF design.

The current analysis focuses on a two-site, four-tenant extranet environment using F5 BIG-IP DNS/GTM, LTM and Advanced WAF/ASM, with external partner/customer access over private-network paths plus internal users and application dependencies.

# Start here

Use these documents in this order:

1. [Current state and stable invariants](./enterprise-scenarios/enterprise_scenario_invariants.md)
2. [High-level current-state architecture](./enterprise-scenarios/high_level_architecture.md)
3. [Future architecture improvements / target health model](./enterprise-scenarios/future_architecture_improvements.md)
4. [Executive architecture and 99.95% recommendation](./enterprise-scenarios/executive_recommendation.md)
5. [Deployment options, resilience and four-tenant cost summary](./enterprise-scenarios/deployment_options_resilience_summary.md)

The complete document map is in [enterprise-scenarios/README.md](./enterprise-scenarios/README.md).

# Current state versus future state

The repository deliberately separates what exists today from what is proposed.

```text
CURRENT / STABLE
enterprise_scenario_invariants.md
        |
high_level_architecture.md

FUTURE / TO-BE
future_architecture_improvements.md
```

Do not draw target-state features as current-state facts unless they have been validated as deployed.

# Current architecture grounding

The current baseline includes:

- two sites;
- one BIG-IP DNS/GTM cluster per site with cross-site GTM synchronization;
- two HA edge-firewall pairs per tenant/site, two devices per pair (2 x 2);
- GTM/DNS located inside the edge-firewall boundary;
- external/customer DNS reaching edge GTM over private leased-line/VPN connectivity;
- internal enterprise DNS delegating/forwarding selected names to the same edge GTM service;
- existing tenant LTM HA boundaries, normally two LTMs per tenant/site;
- internal users/DNS/internal service VIPs outside private cloud;
- a separate internal firewall between the enterprise internal network and private cloud;
- private-cloud CFW -> ELB/service -> application delivery;
- App A/B/C/D dependency chains;
- a 99.95% availability target.

The exact **current** GTM health-check implementation is not yet assumed to be known. The analysis must validate whether current checks are TCP/port or Layer-7, which external/internal VIPs are monitored, whether iQuery is used, and whether GTM probing is local-only or cross-site.

# Target health-monitoring direction

The target-state design is documented in [future_architecture_improvements.md](./enterprise-scenarios/future_architecture_improvements.md).

The key recommendation is a **layered health model**:

- local LTM/ELB health drives fast member-level recovery;
- GTM owns site/DNS decisions using Layer-7 health of the published **external VIP**;
- internal delegated names use Layer-7 health of the corresponding **internal VIP**, either directly from GTM or through authoritative LTM/iQuery health;
- application teams own the readiness-check contract;
- App B/shared-dependency health is handled at the dependency/service layer;
- independent synthetic monitoring measures the real user/SLO outcome.

The design must avoid both:

- **false green** - WAF/LTM port is up but CFW/ELB/application is unusable; and
- **false red** - an over-deep health check withdraws healthy applications because a non-critical downstream dependency failed.

# Management artifacts

Version-controlled management outputs are under [management-artifacts/](./management-artifacts/):

- [PowerPoint management summary](./management-artifacts/EnterpriseWAF_Management_Summary.pptx)
- [PDF management summary](./management-artifacts/EnterpriseWAF_Management_Summary.pdf)
- [End-to-end topology diagram](./management-artifacts/diagrams/EnterpriseWAF_End_to_End_Topology.svg)

Use stable filenames from `main`; Git history provides versioning.

The management deck is structured to distinguish:

1. current-state architecture;
2. architecture-layer breakdown;
3. target health-monitoring model;
4. application dependency/cascade risk;
5. WAF topology options and recommendation;
6. cross-site contingency;
7. 99.95% and change-safety evidence.

# WAF topology shorthand

| ID | Meaning |
|---|---|
| **W1** | tenant LTM -> independent active WAF pool |
| **W2** | WAF HA/DSC cluster |
| **W3** | tenant-preferred WAFs + shared reserve |
| **W4** | asymmetric Site 1 cluster + extra WAF; Site 2 cluster only |
| **S1** | tenant-specific LTM pairs -> shared active WAF pool |
| **S2** | shared LTM -> shared active WAF pool; future consolidation comparison |

The leading shared-capacity candidate remains **S1**, with dedicated W1 as the high-isolation fallback, subject to the detailed resilience and acceptance testing in the executive documents.

# Supporting analyses

- [End-to-end service impact](./enterprise-scenarios/end_to_end_service_impact_analysis.md)
- [Technical failure matrix](./enterprise-scenarios/common_failure_matrix.md)
- [Maintainability/change safety](./enterprise-scenarios/maintainability_change_management_analysis.md)
- [Cross-site routing and dependency recovery](./enterprise-scenarios/cross_site_routing_and_dependency_recovery.md)
- [F5/topology variables and assumptions](./enterprise-scenarios/analysis_variables_and_f5_assumptions.md)
- [2 vs 3 LTM/WAF node appendix](./enterprise-scenarios/appendix_ltm_waf_2_vs_3_nodes.md)
- [WebSocket resilience patterns](./waf_websocket_resilience_cloud_patterns.md)

# Branch strategy

`main` is the authoritative branch. Use short-lived branches/PRs for coherent updates and merge back to `main`.
