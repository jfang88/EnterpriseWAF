# CONTEXT.md

## EnterpriseWAF project context

This file provides durable grounding for ChatGPT, Codex and other coding/documentation agents working on this repository. It is intentionally concise. Detailed architecture remains in `enterprise-scenarios/`.

## Authoritative documents

Start with:

- `enterprise-scenarios/enterprise_scenario_invariants.md` — current-state facts and stable invariants
- `enterprise-scenarios/high_level_architecture.md` — current-state topology
- `enterprise-scenarios/future_architecture_improvements.md` — future/to-be architecture and target health-monitoring model
- `enterprise-scenarios/executive_recommendation.md` — executive recommendation
- `enterprise-scenarios/common_failure_matrix.md` — failure analysis
- `enterprise-scenarios/cross_site_routing_and_dependency_recovery.md` — cross-site and dependency recovery
- `enterprise-scenarios/analysis_variables_and_f5_assumptions.md` — assumptions and variables
- `waf_websocket_resilience_cloud_patterns.md` — WebSocket resilience patterns

The repository `README.md` contains the overall document map.

## Current / stable architecture grounding

The baseline architecture includes:

- two sites;
- a BIG-IP DNS/GTM cluster per site, with GTM synchronization across sites;
- edge firewalls at both sites, with two HA firewall pairs per tenant/site (2 x 2 devices);
- GTM/DNS inside the edge-firewall boundary;
- external/customer connectivity over private leased-line/VPN paths;
- internal enterprise users and systems using internal DNS;
- internal DNS potentially delegating or forwarding selected application endpoint names/namespaces to the GTM service;
- tenant LTM HA boundaries, normally two LTMs per tenant/site;
- WAF capacity behind the tenant LTM layer;
- a separate internal firewall between the enterprise internal network and private cloud;
- private-cloud firewall -> ELB/service -> Kubernetes/VM/application delivery paths;
- application-to-application and shared dependency chains;
- an availability objective of approximately 99.95%.

Do not infer details beyond what the authoritative current-state documents validate.

## Health checks: current state versus target

### Current state

The exact deployed GTM health-check implementation is not assumed to be known.

Items that may require validation include:

- whether GTM checks are TCP/port-level or Layer 7;
- which external VIPs are monitored;
- which internal VIPs are monitored;
- whether individual application endpoints have dedicated checks;
- whether GTM receives authoritative LTM state through iQuery;
- whether probes are local-site only or cross-site;
- how internal delegated DNS names derive service health.

Until confirmed, these remain **to be validated**, not deployed facts.

### Target / to-be direction

The intended target is a layered model:

1. **Local service/member health**
   - LTM and ELB perform fast local member/service checks and recovery.

2. **External service health**
   - GTM makes DNS/site decisions using Layer-7 health of the published external VIP/service.

3. **Internal service health**
   - Internal delegated names use Layer-7 health of the corresponding internal VIP/service, either directly from GTM or via authoritative LTM/iQuery health where appropriate.

4. **Application endpoint health**
   - Important applications expose stable readiness endpoints.
   - Application teams define what constitutes healthy service behaviour.

5. **Dependency health**
   - Shared/downstream dependencies are monitored at the correct dependency or service layer.
   - Avoid making every top-level endpoint fail because of a non-critical downstream issue.

6. **Independent validation**
   - Synthetic/end-to-end monitoring validates actual user or SLO outcomes independently of infrastructure health.

The objective is to avoid:

- **false green** — infrastructure appears reachable while the service is unusable; and
- **false red** — over-deep probes withdraw a usable service because a non-critical dependency has failed.

## DNS and health ownership

External and internal users may use different DNS paths and different published VIPs.

Do not assume one health check can automatically represent both paths.

A useful target ownership model is:

- GTM: site/DNS availability decision
- LTM: local VIP/pool/member availability
- WAF: security enforcement and local processing health
- ELB/service platform: backend service/member health
- application: readiness semantics
- synthetic monitoring: user-visible end-to-end outcome

Where internal DNS delegates application namespaces to GTM, the GTM health decision must represent the **internal published service path**, not merely reuse an external-path signal without validating equivalence.

## Diagram and slide grounding

Management artifacts live under `management-artifacts/`.

When diagrams or slides are updated:

- distinguish current state from target state;
- show DNS, GTM, edge firewall, LTM, WAF, internal firewall, private-cloud firewall, ELB/service and application layers separately where useful;
- represent internal and external paths separately when their VIPs or DNS flows differ;
- avoid presenting simple device/port reachability as application availability;
- keep health-check ownership visible by layer;
- ensure slide layer breakdowns match the authoritative Markdown.

If a diagram or slide conflicts with the current-state Markdown, the Markdown wins until the discrepancy is deliberately resolved.

## Working convention

Use `AGENTS.md` as the operating instructions for automated agents.

Use this file as durable project grounding.

Use the detailed Markdown in `enterprise-scenarios/` as the evidence and source of truth for architecture decisions.
