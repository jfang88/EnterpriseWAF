# Enterprise WAF Scenario Analysis — Regeneration Prompt

## Purpose

Use this prompt to regenerate or refresh the EnterpriseWAF failure analysis **without changing the stable enterprise baseline**.

The analysis is deliberately split into three source layers.

### 1. Stable invariants

Read:

- [enterprise_scenario_invariants.md](./enterprise_scenario_invariants.md)

Treat this as the authoritative enterprise context.

Do not change these facts merely because an architecture option is difficult to support.

If a real-world assumption changes, update the invariant file explicitly and record why.

### 2. Changeable design variables and F5 assumptions

Read:

- [analysis_variables_and_f5_assumptions.md](./analysis_variables_and_f5_assumptions.md)

This contains:

- W1-W4 candidate WAF topologies, each normally replicated across both sites;
- local-only versus controlled cross-site routing;
- GTM health-check models;
- GTM response/preference models;
- F5 LTM/GTM/WAF health-monitor behavior;
- F5 HA/mirroring considerations;
- recovery-time modelling assumptions.

Change this file when testing a different topology, health-check strategy, capacity assumption or F5 recovery configuration.

### 3. Derived analyses

Regenerate/update:

- **Lens 1 — primary end-to-end service impact/recovery:** [end_to_end_service_impact_analysis.md](./end_to_end_service_impact_analysis.md)
- **Lens 1 technical appendix:** [common_failure_matrix.md](./common_failure_matrix.md)
- **Lens 2 — maintainability/change safety:** [maintainability_change_management_analysis.md](./maintainability_change_management_analysis.md)

Both are **derived outputs**. They should be regenerated when the invariant file or analysis-variable file changes.

Do not copy new assumptions directly into either derived analysis without first deciding whether they belong in the invariant file or the variable file.

A new analysis lens should be added as a separate derived document where possible rather than expanding the invariant baseline or mixing unrelated conclusions into the failure matrix.

---

# Analysis instructions

You are reviewing a dual-site enterprise application-delivery architecture using F5 BIG-IP DNS/GTM, LTM and Advanced WAF/ASM.

Use the invariant and variable files above.

## Mandatory comparison dimensions

Analyse all selected WAF topology options:

- W1 — LTM-fronted scalable independent WAF pool;
- W2 — WAF HA cluster, with and without ingress LTM where relevant;
- W3 — tenant-preferred WAFs plus shared reserve WAFs;
- W4 — asymmetric design: Site 1 WAF HA cluster + one extra active/spare WAF; Site 2 WAF HA cluster only. Analyse both W4a (LTM in front) and W4b (no ingress LTM in front of WAF).

W1-W3 normally use the same logical WAF topology in both sites. W4 is the deliberate asymmetry exception: Site 1 has the cluster plus an extra active/spare WAF, while Site 2 has the cluster only. GTM/LTM roles remain similar per site unless a scenario explicitly says otherwise. GTM site recovery is part of each topology and is not a separate WAF option.

Also distinguish:

- X1 — local-only dataplane routing;
- X2A/X2B — controlled cross-site WAF/front-end contingency where technically applicable;
- X2C — conventional site/application failover;
- XD1 — App A -> App B remote-dependency fallback.


## Mandatory maintainability / change-safety lens

After completing the failure/recovery analysis, regenerate:

- [maintainability_change_management_analysis.md](./maintainability_change_management_analysis.md)

Assess every W1-W4 topology for:

- monitoring difficulty and operational visibility;
- firmware/software upgrades;
- WAF policy/signature deployment;
- LTM/GTM rule/configuration deployment;
- config-sync blast radius;
- BIG-IQ or equivalent centralized change control;
- rolling, canary and blue-green feasibility;
- pool/member drain behavior;
- application drain/reconnect/state requirements;
- rollback;
- maintenance capacity;
- staggered node/site change waves;
- whether one unplanned failure can still be tolerated during one planned maintenance event;
- component, path and end-to-end 99.95% availability potential.

Treat 99.95% as a target to test, not as an assumed result.

For every change scenario identify:

- change unit;
- capacity removed during change;
- remaining failure tolerance;
- drain method;
- config-sync behavior;
- canary/blue-green option;
- monitoring/acceptance criteria;
- rollback trigger/path;
- application behavior required;
- whether Site 1 and Site 2 can be staggered;
- whether the change can meet the availability target.

Do not deliberately create configuration drift between HA peers merely to simulate blue-green when the product expects synchronized HA configuration. Prefer a separate pool member, virtual/pool, policy staging, reserve WAF, extra WAF, application version, or site as the canary/blue-green boundary.

### No-cross-site cascading-failure requirement

For every scenario where cross-site capability improves recovery, also show the **no-cross-site** outcome.

Explicitly trace whether the absence of cross-site routing causes:

- WAF failure -> whole application/site failover;
- front-end failure -> healthy application move;
- B1 dependency failure -> A/C/D readiness failure;
- multiple application GTM withdrawals;
- Site 2 capacity surge;
- reconnect/login storm;
- dependency/database/identity overload;
- manual DR.

Quantify the change in recovery class/timing where possible (for example ~16s-class local recovery versus ~46–150s+ site recovery).

## Mandatory cross-site recovery study

Also read and regenerate/update when relevant:

- [cross_site_routing_and_dependency_recovery.md](./cross_site_routing_and_dependency_recovery.md)

Distinguish these mechanisms:

- **X2A:** surviving local LTM borrows remote WAF and routes back to the primary application;
- **X2B:** remote site's firewall/LTM/WAF becomes the front end and routes back to the healthy primary-site application;
- **X2C:** conventional full application/site failover;
- **XD1:** App A remains local and uses remote App B through a health-aware service VIP/service-discovery layer.

Do not describe them all simply as "cross-site routing". Their detection, DNS dependency, latency, capacity and failure modes differ materially.

## Mandatory end-to-end service outcome

The primary failure/recovery output is **not** a WAF or F5 component matrix.

For every failure scenario, finish the analysis by stating:

- impact to external human users;
- impact to external systems/API clients;
- impact to internal users/systems;
- impact to App A -> App B -> App C or other dependency chains;
- user-visible outage/degradation duration;
- whether recovery is automatic, manual, partial or unavailable;
- local-only result versus cross-site-enabled result;
- application retry/reconnect/re-auth/state/replay requirements;
- whether the business service has actually recovered after infrastructure recovery.

Use the service RTO measure:

> time from fault to successful business transaction for each affected actor.

Do not use "device green" or "WAF recovered" as the final success criterion.

Classify recoverability where useful:

- **R0** — no user impact;
- **R1** — automatic local recovery;
- **R2** — automatic cross-site component/dependency recovery;
- **R3** — automatic site/application recovery;
- **R4** — manual recovery;
- **R5** — not recoverable with current design.

## Mandatory actor/path dimensions

Analyse:

- external users over private leased-line paths using the **external namespace**;
- external systems/API clients using the external namespace;
- internal users using **internal enterprise DNS**, with selected internal service names optionally delegated/forwarded to GTM;
- internal applications resolving App B/App C/internal service endpoints through internal DNS and, where configured, GTM;
- internal users that may bypass WAF and connect directly to internal LTM/ELB/service endpoints;
- Application A -> Application B -> Application C and shared-dependency chains;
- non-web services that bypass WAF.

Treat **external namespace resolution** and **internal namespace resolution** as separate failure domains. Do not assume a DNS/GTM failure affects both unless the architecture actually shares that failure domain.

## Mandatory application types

Every failure scenario must state the applicable application type:

1. stateless web;
2. stateful web;
3. socket/WebSocket/long-lived connection;
4. non-web/L4 application bypassing WAF.

Do not call infrastructure failover successful until the application-specific recovery requirement is also satisfied.

## Mandatory failure layers

Cover at least:

1. external DNS/GTM namespace resolution;
2. internal enterprise DNS resolution;
3. internal DNS delegation/conditional forwarding to GTM;
4. internal GTM/service-name resolution;
5. GTM health-check false-positive/false-negative;
6. leased-line access;
7. edge firewall member and full pair;
8. LTM member and full HA pair;
9. one WAF member;
10. multiple WAF members;
11. entire local WAF service;
12. common-mode WAF policy/configuration error;
13. shared reserve exhaustion;
14. cloud firewall / ELB;
15. VM/Kubernetes member/cluster;
16. application readiness;
17. session/state store;
18. App A -> App B -> App C dependency;
19. cross-site route;
20. asymmetric cross-site path;
21. entire site;
22. passive site not ready;
23. long-lived connection recovery.

## GTM analysis

Compare at minimum:

- external namespace GTM resolution;
- internal namespace resolution through internal enterprise DNS;
- selected internal-name delegation/conditional forwarding to GTM;
- internal service-name GTM health/selection;
- IP/port-only GTM health;
- full application-readiness health;
- F5 DNS/LTM integration using BIG-IP monitor/iQuery;
- local-only probing;
- distributed/cross-site probing.

For active/passive applications, analyse health-gated Global Availability behavior.

For active/active/locality designs, analyse Topology load balancing only when LDNS/resolver source can reliably map to desired site.

Never assume the site containing the GTM that answered the query is automatically the preferred application site.

## F5 timing rules

### Numeric recovery timing requirement

The primary output must contain an explicit timing table with numeric planning windows where defaults support them.

At minimum show:

- BIG-IP HA peer: ~3s+ detection plus convergence;
- LTM member/WAF member: up to ~16s with common 5s/16s defaults;
- GTM DNS A-record pool TTL: 30s default;
- direct GTM monitor: 30s interval / 120s timeout for common HTTP/HTTPS/TCP-style monitors;
- illustrative fast site move: ~16s local health + up to 30s residual TTL = ~46s + T6, plus measured iQuery/propagation;
- default-direct-monitor site move: up to ~120s + up to 30s TTL = ~150s + T6;
- manual DR: T5 + DNS/site timing + T6.

Explicitly distinguish:

- new uncached clients;
- clients with cached old DNS answers;
- already-established TCP/TLS/WebSocket connections;
- applications with their own DNS/connection-pool cache.

Do not state that DNS TTL moves an existing connection.

Do not state that LTM member failover is interruption-free for a connection already anchored to the failed member.

Do not invent a single vendor failover number.

Use the timing model in the variables file:

- BIG-IP HA peer failure: seconds-scale, approximately 3+ seconds peer-loss detection under common/default-style settings plus data-plane convergence;
- LTM pool-member failure: driven by configured monitor interval/timeout, often around the documented 5s/16s defaults for many LTM monitors;
- direct BIG-IP DNS health: often much slower with documented 30s/120s defaults unless tuned;
- DNS/site recovery: health detection + GTM decision + DNS cache/TTL + client re-resolution + application readiness;
- warm/cold/manual application startup: operator/process dependent.

For every timing value state whether it is:

- F5 documented default/behavior;
- configured design target;
- measured value;
- or unknown/TBD.

## Application compliance

Call out application code/configuration prerequisites.

### Stateless web

Require:

- safe retry;
- idempotency where duplicate requests matter;
- shared/external state;
- readiness monitoring.

### Stateful web

Require:

- documented state/session location;
- portable/replicated state;
- safe re-auth/session recovery;
- transaction reconciliation;
- compatible alternate-site data.

### Socket/WebSocket

Require:

- disconnect detection;
- reconnect;
- exponential backoff + jitter;
- re-resolution;
- re-authentication;
- resubscription;
- sequence/gap detection;
- snapshot/replay;
- idempotent commands;
- durable state.

### App A -> App B

Require:

- bounded timeouts;
- retries with budgets/backoff;
- circuit breaker/bulkhead behavior where appropriate;
- service discovery/stable VIP;
- idempotent retry semantics;
- dependency failover without unnecessary site failover.

### Non-web

Require:

- protocol-specific reconnect/retry;
- safe replay/transaction semantics;
- endpoint re-resolution;
- state/persistence documentation.

If these are absent, explicitly mark the application **not end-to-end resilient** and explain how that reduces the overall recoverability even when F5 infrastructure is HA.

---

# Required output structure

## Lens 1 — end-to-end service impact/recovery

First regenerate [end_to_end_service_impact_analysis.md](./end_to_end_service_impact_analysis.md) as the primary output. It must lead with actor impact, service outage time and recoverability.

Then regenerate [common_failure_matrix.md](./common_failure_matrix.md) as the technical component appendix with:

1. topology shorthand;
2. timing model;
3. control-plane/ingress failure table;
4. LTM failure table;
5. WAF failure table;
6. backend/application failure table;
7. cross-site failure table;
8. full-site failure table;
9. socket/long-lived behavior;
10. non-web bypass behavior;
11. application resilience/compliance requirements;
12. GTM health-check comparison;
13. topology resilience summary;
14. critical failure points;
15. architecture conclusions.

For each scenario identify:

- failed component;
- detection signal;
- recovery mechanism;
- timing driver;
- W1-W4 outcome;
- external-user impact;
- internal-user impact;
- application-type impact;
- App A -> B impact where relevant;
- state/session/connection impact;
- cascading-failure risk;
- capacity impact;
- manual action;
- compliance requirement;
- overall recoverability.

## Lens 2 — maintainability/change safety

Regenerate the maintainability analysis with:

1. availability/SLO budget;
2. F5 operational capabilities;
3. maintainability principles;
4. monitoring complexity;
5. firmware strategy by W1-W4;
6. LTM maintenance/rule changes;
7. GTM maintenance;
8. WAF policy/signature strategy;
9. blue-green/canary feasibility;
10. application draining;
11. 99.95 maintainability test;
12. topology scorecard;
13. critical maintainability risks;
14. recommended operating model;
15. maintainability conclusions.

---

# Change-control rule

Before changing any analysis:

1. Ask: **Did the real enterprise environment change?**
   - Yes -> update invariants.
   - No -> leave invariants untouched.

2. Ask: **Did a topology/health/timing assumption change?**
   - Yes -> update variables.
   - No -> leave variables untouched.

3. Regenerate the end-to-end service impact/recoverability analysis.
4. Regenerate the technical common failure matrix that supports it.
5. Regenerate the maintainability/change-safety analysis from the same inputs.
6. Keep findings in their derived lens; promote a fact into invariants or variables only when it is genuinely a reusable input.

This separation is intended to prevent the baseline from drifting every time a new WAF option or failure scenario is considered.
