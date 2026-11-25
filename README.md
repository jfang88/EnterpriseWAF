# EnterpriseWAF

Enterprise architecture analysis for **end-to-end resilient F5-based application delivery**, with an **initial delivery focus on the WAF tier** (and its F5 LTM/GTM interfaces) while coordinating partner-owned tiers (edge/internal firewalls, private-cloud CFW/ELB, and application teams) through explicit health and recovery contracts.

The current analysis covers a two-site, four-tenant extranet application-delivery environment using F5 BIG-IP DNS/GTM, LTM and Advanced WAF/ASM (currently **BIG-IP 17.5.x**, with a confirmed target hardware rebuild standard of **F5 rSeries `r2800` pizza boxes only** running `F5OS-A 1.8.0+` + BIG-IP 21.1.x+, no blade chassis), serving external partner/customer access over private-network paths plus internal users and application dependencies.

# Start here

Use these documents in this order:

1. [Current architecture and stable invariants](./enterprise-scenarios/current_architecture_and_invariants.md)
2. [Future architecture improvements / target health model](./enterprise-scenarios/future_architecture_improvements.md)
3. [Executive architecture and 99.95% recommendation](./enterprise-scenarios/executive_recommendation.md)
4. [Deployment options, resilience and four-tenant cost summary](./enterprise-scenarios/deployment_options_resilience_summary.md)

The complete document map is in [enterprise-scenarios/README.md](./enterprise-scenarios/README.md).

# Current state versus future state

The repository deliberately separates what exists today from what is proposed.

```text
CURRENT / STABLE
current_architecture_and_invariants.md

FUTURE / TO-BE
future_architecture_improvements.md
```

Do not draw target-state features as current-state facts unless they have been validated as deployed.

# Current architecture grounding

The current baseline includes:

- two sites;
- one BIG-IP DNS/GTM cluster per site with cross-site GTM synchronization;
- two HA edge-firewall pairs per tenant/site, two devices per pair (2 x 2) — *owned by Network/Security*;
- GTM/DNS located inside the edge-firewall boundary;
- external/customer DNS reaching edge GTM over private leased-line/VPN connectivity;
- internal enterprise DNS delegating/forwarding selected names to the same edge GTM service;
- existing tenant LTM HA boundaries, normally two LTMs per tenant/site — *F5/ADC tier*;
- internal users/DNS/internal service VIPs outside private cloud;
- a separate internal firewall between the enterprise internal network and private cloud — *owned by Network/Security*;
- private-cloud CFW -> ELB/service -> application delivery — *owned by Cloud Platform & Application teams*;
- App A/B/C/D dependency chains;
- a **99.95% total availability target (`4h 22m 48s / year`) covering BOTH managed (planned maintenance/changes) and unmanaged (unplanned failure) outages combined**.

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

- [Executive & Tech-Lead Discussion Deck (PPTX — 9 slides + Speaker Notes)](./management-artifacts/EnterpriseWAF_Discussion_Deck.pptx) — 3 executive theme slides + 6 tech-lead discussion slides (`r2800`, F5 KBs & timings in Speaker Notes)
- [Executive & Tech-Lead Discussion Deck (PDF)](./management-artifacts/EnterpriseWAF_Discussion_Deck.pdf)
- [Long-Form Management Summary (PPTX — 17 slides)](./management-artifacts/EnterpriseWAF_Management_Summary.pptx) — full reference deck
- [Long-Form Management Summary (PDF)](./management-artifacts/EnterpriseWAF_Management_Summary.pdf)
- [End-to-end topology diagram](./management-artifacts/diagrams/EnterpriseWAF_End_to_End_Topology.svg)
- [WAF topology options visual diagram](./management-artifacts/diagrams/EnterpriseWAF_Topology_Options.svg)

Use stable filenames from `main`; Git history provides versioning.

The management deck is structured to distinguish:

1. end-to-end application delivery scope (with initial focus on the WAF tier) and current vs. target separation;
2. architecture planes and current-state end-to-end topology;
3. target layered health-monitoring model and placement;
4. application dependency/cascade risk;
5. visual WAF topology options (`W1`–`W4`, `S1`–`S2`, and F5OS rebuild) and explicit LTM + WAF device counts;
6. cross-site contingency and application-type recovery;
7. 99.95% total availability (managed + unmanaged outages), recovery classes (`R0`–`R4`), timing (`T1`–`T9`), and executive glossary.

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
