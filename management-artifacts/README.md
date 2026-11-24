# Management Artifacts

This directory contains the current, version-controlled management outputs derived from the authoritative EnterpriseWAF Markdown analysis.

# Stable filenames

- [EnterpriseWAF_Management_Summary.pptx](./EnterpriseWAF_Management_Summary.pptx) — editable management deck
- [EnterpriseWAF_Management_Summary.pdf](./EnterpriseWAF_Management_Summary.pdf) — PDF export
- [diagrams/EnterpriseWAF_Architecture_Planes.svg](./diagrams/EnterpriseWAF_Architecture_Planes.svg) — architecture planes / parallel-path model
- [diagrams/EnterpriseWAF_End_to_End_Topology.svg](./diagrams/EnterpriseWAF_End_to_End_Topology.svg) — **current-state** editable topology
- [diagrams/EnterpriseWAF_Target_Health_Monitoring.svg](./diagrams/EnterpriseWAF_Target_Health_Monitoring.svg) — **target-state** editable health-monitoring topology
- [diagrams/EnterpriseWAF_Health_Check_Placement.svg](./diagrams/EnterpriseWAF_Health_Check_Placement.svg) — health decision-owner / probe-placement model
- `diagrams/EnterpriseWAF_Architecture_Planes.png` — generated architecture planes diagram
- `diagrams/EnterpriseWAF_End_to_End_Topology.png` — generated current-state topology
- `diagrams/EnterpriseWAF_Target_Health_Monitoring.png` — generated target-state health diagram
- `diagrams/EnterpriseWAF_Health_Check_Placement.png` — generated health placement table
- `diagrams/GTM_Health_and_Convergence.png` — generated GTM probing/convergence diagram

Git history provides versioning. Do not create `_v2/_v3/_v4/...` copies on `main`.

# Source-of-truth split

## Current / stable

- [current_architecture_and_invariants.md](../enterprise-scenarios/current_architecture_and_invariants.md) — **single authoritative current-state architecture + invariant baseline**

## Future / target-state

- [future_architecture_improvements.md](../enterprise-scenarios/future_architecture_improvements.md)

The deck must keep current-state and target-state diagrams on different slides.

# Reproducible generation

- `source/build_management_deck.py` generates the base PowerPoint.
- `source/replace_management_slides.py` inserts Slides 3, 4, 5, and 6 from the four authoritative SVG diagrams (`EnterpriseWAF_Architecture_Planes.svg`, `EnterpriseWAF_End_to_End_Topology.svg`, `EnterpriseWAF_Target_Health_Monitoring.svg`, and `EnterpriseWAF_Health_Check_Placement.svg`).
- `.github/workflows/build-management-artifacts.yml` regenerates the PowerPoint, PDF and PNG diagrams when the architecture source changes on `main`.

The automated generated-artifact commit uses the same stable filenames.

# Management-deck architecture breakdown

Do **not** present the architecture as one linear L0-L7 stack. External and internal access are parallel paths that converge at the private-cloud service tier, while DNS/GTM and health/observability are control planes.

Use this management structure:

1. executive recommendation;
2. **current state versus target state**;
3. **architecture planes and parallel paths**:
   - client/resolver plane;
   - DNS/GTM site-selection control plane;
   - external ingress path;
   - internal ingress path;
   - private-cloud delivery tier;
   - application/dependency tier;
   - cross-cutting health/observability/recovery plane;
4. current-state end-to-end topology;
5. target layered health-monitoring topology;
6. health-check placement decision table;
7. GTM probe-source, synchronization and convergence model;
8. App A/B/C/D dependency cascade;
9. WAF topology options;
10. 99.95% / failure-recovery domains;
11. cross-site contingency;
12. application types;
13. four-tenant cost/blast radius;
14. implementation sequence and decision gates;
15. T1-T9 timing appendix.

# Health-check management rule

The deck should distinguish **decision ownership** from **probe origin**:

- GTM owns external/internal DNS site selection;
- local LTM/ELB owns local member selection;
- an external VIP health probe should originate from a vantage that meaningfully exercises the external/extranet path where possible;
- an internal VIP health probe should originate from the internal-network side, or use authoritative internal LTM Layer-7 health exported to GTM through iQuery;
- independent synthetics measure the user/business outcome.

A GTM monitor originating inside the edge boundary can still provide useful application health, but it must not be described as proving external leased-line/firewall reachability unless its actual routing path does so.

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
