# Management Artifacts

This directory contains the current, version-controlled management outputs derived from the authoritative EnterpriseWAF Markdown analysis.

# Stable filenames

- [EnterpriseWAF_Management_Summary.pptx](./EnterpriseWAF_Management_Summary.pptx) — editable management deck
- [EnterpriseWAF_Management_Summary.pdf](./EnterpriseWAF_Management_Summary.pdf) — PDF export
- [diagrams/EnterpriseWAF_End_to_End_Topology.svg](./diagrams/EnterpriseWAF_End_to_End_Topology.svg) — **current-state** editable topology
- [diagrams/EnterpriseWAF_Target_Health_Monitoring.svg](./diagrams/EnterpriseWAF_Target_Health_Monitoring.svg) — **target-state** editable health-monitoring topology
- `diagrams/EnterpriseWAF_End_to_End_Topology.png` — generated current-state topology
- `diagrams/EnterpriseWAF_Target_Health_Monitoring.png` — generated target-state health diagram
- `diagrams/GTM_Health_and_Convergence.png` — generated GTM probing/convergence diagram

Git history provides versioning. Do not create `_v2/_v3/_v4/...` copies on `main`.

# Source-of-truth split

## Current / stable

- [current_architecture_and_invariants.md](../enterprise-scenarios/current_architecture_and_invariants.md)

## Future / target-state

- [future_architecture_improvements.md](../enterprise-scenarios/future_architecture_improvements.md)

The deck must keep current-state and target-state diagrams on different slides.

# Reproducible generation

- `source/build_management_deck.py` generates the PowerPoint.
- `.github/workflows/build-management-artifacts.yml` regenerates the PowerPoint, PDF and PNG diagrams when the architecture source changes on `main`.

The automated generated-artifact commit uses the same stable filenames.

# Management-deck layer breakdown

The deck is intentionally organized in this order:

1. executive recommendation;
2. **current state versus target state**;
3. architecture **layer breakdown L0-L7**;
4. current-state end-to-end topology;
5. target layered health-monitoring topology;
6. health-check placement decision table;
7. GTM probing/synchronization/convergence;
8. App A/B/C/D dependency cascade;
9. WAF topology options;
10. 99.95% / failure-recovery domains;
11. cross-site contingency;
12. application types;
13. four-tenant cost/blast radius;
14. implementation sequence and decision gates;
15. T1-T9 timing appendix.

# Stable visual facts

Current-state diagrams must show:

- one BIG-IP DNS/GTM cluster per site;
- GTM synchronization across sites;
- two HA edge-firewall pairs per tenant/site, two devices per pair (2 x 2);
- GTM/DNS inside the edge-firewall boundary;
- external/customer DNS reaching edge GTM over private leased-line/VPN connectivity;
- internal enterprise DNS using the same edge GTM service for selected delegated/forwarded names;
- internal users/DNS/internal LTM outside private cloud;
- a separate internal firewall before private-cloud CFW;
- CFW and ELB/service as separate private-cloud layers;
- App A/B/C/D dependencies.

Current-state diagrams must **not** imply the following are already implemented unless validated:

- GTM L7 checks of every external/internal VIP;
- cross-site GTM probing;
- X2A/X2B/XD1;
- S1 as the deployed WAF topology.

Target-state diagrams can show those improvements when clearly labelled target/to-be.
