# Management Artifacts

This directory contains the **current, version-controlled management outputs** derived from the authoritative EnterpriseWAF Markdown analysis.

## Authoritative current artifacts

Use only these stable filenames from `main`:

- [EnterpriseWAF_Management_Summary.pptx](./EnterpriseWAF_Management_Summary.pptx) — editable PowerPoint management deck.
- [EnterpriseWAF_Management_Summary.pdf](./EnterpriseWAF_Management_Summary.pdf) — PDF export of the same management deck.
- [diagrams/EnterpriseWAF_End_to_End_Topology.svg](./diagrams/EnterpriseWAF_End_to_End_Topology.svg) — version-controlled end-to-end topology diagram.

The source-of-truth architecture remains [high_level_architecture.md](../enterprise-scenarios/high_level_architecture.md). The binary deck/PDF are review artifacts generated from the current architecture.

## Versioning rule

Do **not** add `_v2`, `_v3`, `_v4`, `_v5` copies to `main`.

Git history provides versioning. Replace the stable files in a normal pull request when the management pack changes.

Old generated files, Base64 fragments, and experimental artifact branches are **non-authoritative** and should not be linked from management documentation.

## Current boundary model

The current management pack and topology must show:

- internal users/desktops/systems outside the private-cloud boundary;
- internal enterprise DNS outside the private-cloud boundary;
- optional internal GTM/service-name resolution and internal LTM/service VIP in the enterprise internal network;
- a separate **internal firewall** between the enterprise internal network and the private-cloud CFW;
- private-cloud **CFW**, ELB/service and hosted App A/B/C/D inside the private cloud;
- X2A/X2B/XD1 as contingency paths, not normal dependencies.
