# Archive

Historical EnterpriseWAF analysis is retained here so the repository root and `enterprise-scenarios/` directory remain easy to navigate.

## Archived documents

| File | Reason archived | Current replacement |
|---|---|---|
| [waf_architecture_options_cross_site_resilience.md](./waf_architecture_options_cross_site_resilience.md) | Earlier Design A/Design B architecture paper; useful concepts were carried forward but topology labels are superseded | [Enterprise scenario index](../enterprise-scenarios/README.md) |
| [f5_failover_failure_V4_matrix_footnotes.md](./f5_failover_failure_V4_matrix_footnotes.md) | Older fixed clustered+standalone GTM/LTM/WAF failure matrix | [End-to-end service impact](../enterprise-scenarios/end_to_end_service_impact_analysis.md) and [technical failure matrix](../enterprise-scenarios/common_failure_matrix.md) |
| [f5_failover_failure_matrix-v3.md](./f5_failover_failure_matrix-v3.md) | Obsolete predecessor to V4 | Same current failure-analysis set |
| [enterprise-scenarios-round-2-analysis.md](./enterprise-scenarios-round-2-analysis.md) | Working history used to derive the current invariant/variable model | [Enterprise scenario index](../enterprise-scenarios/README.md) |

## Historical shorthand warning

Archived Mermaid diagrams and matrices may use labels such as `W1`, `W2`, `W3`, `S1` or `S2` as **node, step or site identifiers**. Those labels pre-date the current shorthand and do **not** mean the current W1-W4 WAF-topology or S1-S3 tenancy/sharing patterns.

For current terminology and end-to-end paths, use [Canonical Architecture Shorthand and End-to-End Topology Reference](../enterprise-scenarios/architecture_shorthand_topology_reference.md).

## Not archived

`../waf_websocket_resilience_cloud_patterns.md` remains visible at the repository root because its application-level WebSocket/SSE resilience guidance is still relevant. Its historical Design A/Design B infrastructure references should not override the current W1-W4 model.

## Rule

Archived files are evidence/history only. If an archived concept is still required, promote it explicitly into the current invariant or variable files rather than editing the archive as a source of truth.
