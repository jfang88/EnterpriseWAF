# Management Artifacts

This directory contains the current, version-controlled management outputs derived from the authoritative EnterpriseWAF Markdown analysis.

# Stable filenames

- [EnterpriseWAF_Discussion_Deck.pptx](./EnterpriseWAF_Discussion_Deck.pptx) — **concise 9-slide Executive & Tech-Lead Discussion Deck** (3 executive theme slides + 6 tech-lead deep-dive slides; `r2800` upgrade specs, F5 KBs, and `T1`–`T9` details in PowerPoint Speaker Notes)
- [EnterpriseWAF_Discussion_Deck.pdf](./EnterpriseWAF_Discussion_Deck.pdf) — PDF export of the 9-slide discussion deck
- [EnterpriseWAF_Management_Summary.pptx](./EnterpriseWAF_Management_Summary.pptx) — **full 17-slide long-form reference deck** (all technical details on-slide)
- [EnterpriseWAF_Management_Summary.pdf](./EnterpriseWAF_Management_Summary.pdf) — PDF export of the 17-slide long-form deck
- [diagrams/EnterpriseWAF_Architecture_Planes.svg](./diagrams/EnterpriseWAF_Architecture_Planes.svg) — architecture planes / parallel-path model
- [diagrams/EnterpriseWAF_End_to_End_Topology.svg](./diagrams/EnterpriseWAF_End_to_End_Topology.svg) — **current-state** editable topology
- [diagrams/EnterpriseWAF_Target_Health_Monitoring.svg](./diagrams/EnterpriseWAF_Target_Health_Monitoring.svg) — **target-state** editable health-monitoring topology
- [diagrams/EnterpriseWAF_Health_Check_Placement.svg](./diagrams/EnterpriseWAF_Health_Check_Placement.svg) — health decision-owner / probe-placement model (H1–H6)
- [diagrams/EnterpriseWAF_Topology_Options.svg](./diagrams/EnterpriseWAF_Topology_Options.svg) — visual topology diagrams for `W1-3`/`W1-2`, `W2`–`W4`, `S1`/`S1+2`, `S2`, and `r2800` rebuild option
- `diagrams/EnterpriseWAF_Architecture_Planes.png` — generated architecture planes diagram
- `diagrams/EnterpriseWAF_End_to_End_Topology.png` — generated current-state topology
- `diagrams/EnterpriseWAF_Target_Health_Monitoring.png` — generated target-state health diagram
- `diagrams/EnterpriseWAF_Health_Check_Placement.png` — generated health placement table
- `diagrams/GTM_Health_and_Convergence.png` — generated GTM probing/convergence diagram
- `diagrams/EnterpriseWAF_Topology_Options.png` — generated visual WAF topology options diagram

Git history provides versioning. Do not create `_v2/_v3/_v4/...` copies on `main`.

# Source-of-truth split

## Current / stable

- [current_architecture_and_invariants.md](../enterprise-scenarios/current_architecture_and_invariants.md) — **single authoritative current-state architecture + invariant baseline**

## Future / target-state

- [future_architecture_improvements.md](../enterprise-scenarios/future_architecture_improvements.md)

The decks must keep current-state and target-state diagrams on different slides.

# Reproducible generation

- `source/build_discussion_deck.py` generates the alternative **9-slide Executive & Tech-Lead Discussion Deck** (`EnterpriseWAF_Discussion_Deck.pptx`) with full Speaker Notes and embeds the 3 core authoritative SVGs directly.
- `source/build_management_deck.py` generates the base **17-slide Long-Form Reference Deck** (`EnterpriseWAF_Management_Summary.pptx`).
- `source/replace_management_slides.py` inserts Slides 3, 4, 5, 6, and 9 of the long-form deck from the five authoritative SVG diagrams (`EnterpriseWAF_Architecture_Planes.svg`, `EnterpriseWAF_End_to_End_Topology.svg`, `EnterpriseWAF_Target_Health_Monitoring.svg`, `EnterpriseWAF_Health_Check_Placement.svg`, and `EnterpriseWAF_Topology_Options.svg`).
- `.github/workflows/build-management-artifacts.yml` regenerates both PowerPoint decks, both PDFs, and the PNG diagrams when the architecture source changes on `main`.

The automated generated-artifact commit uses the same stable filenames.

# Deck structures

Do **not** present the architecture as one linear L0-L7 stack. External and internal access are parallel paths that converge at the private-cloud service tier, while DNS/GTM and health/observability are control planes.

## Executive & Tech-Lead Discussion Deck (9 slides + Speaker Notes)

Designed for mixed **Technical Leadership + Tech Lead** discussions (all `r2800` upgrade/hardware details, F5 KBs, `OneConnect`/`CARP`/`SNAT` mechanics, and `T1`–`T9` numbers live in PowerPoint Speaker Notes):

1. **Theme 1 (Executive):** Joint responsibility for 99.95% availability (managed + unmanaged) & ≤ 25% impact cap;
2. **Theme 2 (Executive):** Layered health checks & proportional recovery (stop false-greens, separate ext/int paths, isolate App B);
3. **Theme 3 (Executive):** Shortlist decision (`S1+2` vs. `W1-3`, both 20 `r2800`s) & 90-day decisions;
4. **Discussion 1 (Tech Leads):** Current-state end-to-end topology (SVG);
5. **Discussion 2 (Tech Leads):** Target layered health monitoring (SVG);
6. **Discussion 3 (Tech Leads):** Visual WAF topology options (`W1-3`/`W1-2`, `W2`–`W4`, `S1`/`S1+2`, `S2`) (SVG);
7. **Discussion 4 (Tech Leads):** Topology variant scorecard (≤ 25% impact, 99.95%, longest outage, auto/manual, trade-offs);
8. **Discussion 5 (Tech Leads):** End-to-end sticky sessions, client-IP headers (`XFF`/ELB), SNAT & throughput (`AT1`–`AT4`);
9. **Discussion 6 (Tech Leads):** Joint responsibility matrix by fault domain (Infra vs. App obligations).

## Long-Form Management Reference Deck (17 slides)

1. executive summary — joint responsibility & end-to-end application delivery (Phase 1 focus: WAF tier);
2. **baseline invariants versus target layer controls** (with team ownership boundaries);
3. **architecture planes and parallel paths** (with H1–H6 health layers explained);
4. current-state end-to-end application delivery topology (BIG-IP 17.5.x);
5. target layered health-monitoring topology (H2, H3, H4, H6 explained);
6. health-check placement decision table & team ownership (H1–H6);
7. BIG-IP DNS (GTM) probe-source, synchronization and convergence model;
8. App A/B/C/D dependency cascade vs. dependency-local recovery (XD1);
9. **visual WAF topology options (`W1-3`/`W1-2`, `W2`–`W4`, `S1`/`S1+2`, `S2`, and `r2800` rebuild)**;
10. **99.95% total availability (managed + unmanaged outages) & recovery classes (`R0`–`R4`)**;
11. cross-site contingency (`X2A`, `X2B`, `XD1`);
12. **end-to-end sticky sessions, client-IP headers, SNAT & throughput (`AT1`–`AT4`)**;
13. **four-tenant topology variant scorecard (25% impact, 99.95%, longest outage, auto/manual)**;
14. **joint responsibility & fault-domain recovery matrix (Infra vs. App per layer)**;
15. end-to-end implementation sequence and cross-team acceptance gates;
16. Appendix A — recovery timing shorthand (`T1`–`T9`);
17. **Appendix B — executive glossary of acronyms and shorthand codes**.

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
