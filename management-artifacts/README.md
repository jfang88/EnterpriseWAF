# Management Artifacts

This directory contains the **current, version-controlled management outputs** derived from the authoritative EnterpriseWAF Markdown analysis.

## Stable filenames

Use these names from `main`:

- [EnterpriseWAF_Management_Summary.pptx](./EnterpriseWAF_Management_Summary.pptx) — editable management deck.
- [EnterpriseWAF_Management_Summary.pdf](./EnterpriseWAF_Management_Summary.pdf) — PDF export.
- [diagrams/EnterpriseWAF_End_to_End_Topology.svg](./diagrams/EnterpriseWAF_End_to_End_Topology.svg) — editable/versionable topology source.
- `diagrams/EnterpriseWAF_End_to_End_Topology.png` — rendered topology generated from the deck.
- `diagrams/GTM_Health_and_Convergence.png` — rendered GTM health/convergence view.

Git history provides versioning. Do **not** add `_v2/_v3/_v4/_v5` copies to `main`.

## Reproducible generation

- `source/build_management_deck.py` generates the PowerPoint.
- `.github/workflows/build-management-artifacts.yml` regenerates the PowerPoint, PDF and PNG diagrams when the architecture source changes on `main`.

The generated binary commit is automated; the Markdown baseline remains authoritative.

## Architecture grounding

The management artifacts must remain consistent with:

- [enterprise_scenario_invariants.md](../enterprise-scenarios/enterprise_scenario_invariants.md)
- [high_level_architecture.md](../enterprise-scenarios/high_level_architecture.md)
- [executive_recommendation.md](../enterprise-scenarios/executive_recommendation.md)
- [deployment_options_resilience_summary.md](../enterprise-scenarios/deployment_options_resilience_summary.md)

Stable visual facts include:

- two sites, each with a BIG-IP DNS/GTM cluster;
- the site GTM clusters synchronize the enterprise GTM/DNS configuration/global-availability view;
- each site has **two HA edge-firewall pairs, two devices per pair (2 x 2)**;
- GTM/DNS sits inside the edge-firewall boundary;
- external/customer DNS and internal enterprise DNS can use the same edge GTM service for selected names;
- internal users/DNS/internal LTM are outside the private cloud;
- a distinct internal firewall sits before the private-cloud CFW;
- WAF listener/port-up does not by itself prove application health;
- application-layer health checks require an application-team-owned health contract;
- GTM synchronization does not automatically mean cross-site probing;
- X2A/X2B/XD1 are contingency paths, not healthy-state dependencies.
