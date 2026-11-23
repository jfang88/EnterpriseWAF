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

- W1-W5 candidate WAF topologies;
- local-only versus controlled cross-site routing;
- GTM health-check models;
- GTM response/preference models;
- F5 LTM/GTM/WAF health-monitor behavior;
- F5 HA/mirroring considerations;
- recovery-time modelling assumptions.

Change this file when testing a different topology, health-check strategy, capacity assumption or F5 recovery configuration.

### 3. Derived analysis

Regenerate/update:

- [common_failure_matrix.md](./common_failure_matrix.md)

The matrix is a **derived output**. It should be regenerated when the invariant file or analysis-variable file changes.

Do not copy new assumptions directly into the matrix without first deciding whether they belong in the invariant file or the variable file.

---

# Analysis instructions

You are reviewing a dual-site enterprise application-delivery architecture using F5 BIG-IP DNS/GTM, LTM and Advanced WAF/ASM.

Use the invariant and variable files above.

## Mandatory comparison dimensions

Analyse all selected WAF topology options:

- W1 — LTM-fronted scalable independent WAF pool;
- W2 — WAF HA cluster, with and without ingress LTM where relevant;
- W3 — tenant-preferred WAFs plus shared reserve WAFs;
- W4 — local WAF cluster + local spare + second-site WAF cluster;
- W5 — per-site scalable WAF pools + GTM site recovery.

Also distinguish:

- X1 — local-only dataplane routing;
- X2 — controlled cross-site contingency where technically applicable.

## Mandatory actor/path dimensions

Analyse:

- external users over private leased-line paths;
- external systems/API clients;
- internal users that may bypass WAF and connect directly to ELB/service endpoints;
- Application A -> Application B dependencies;
- non-web services that bypass WAF.

## Mandatory application types

Every failure scenario must state the applicable application type:

1. stateless web;
2. stateful web;
3. socket/WebSocket/long-lived connection;
4. non-web/L4 application bypassing WAF.

Do not call infrastructure failover successful until the application-specific recovery requirement is also satisfied.

## Mandatory failure layers

Cover at least:

1. DNS/GTM node and service;
2. GTM health-check false-positive/false-negative;
3. leased-line access;
4. edge firewall member and full pair;
5. LTM member and full HA pair;
6. one WAF member;
7. multiple WAF members;
8. entire local WAF service;
9. common-mode WAF policy/configuration error;
10. shared reserve exhaustion;
11. cloud firewall / ELB;
12. VM/Kubernetes member/cluster;
13. application readiness;
14. session/state store;
15. App A -> App B dependency;
16. cross-site route;
17. asymmetric cross-site path;
18. entire site;
19. passive site not ready;
20. long-lived connection recovery.

## GTM analysis

Compare at minimum:

- IP/port-only GTM health;
- full application-readiness health;
- F5 DNS/LTM integration using BIG-IP monitor/iQuery;
- local-only probing;
- distributed/cross-site probing.

For active/passive applications, analyse health-gated Global Availability behavior.

For active/active/locality designs, analyse Topology load balancing only when LDNS/resolver source can reliably map to desired site.

Never assume the site containing the GTM that answered the query is automatically the preferred application site.

## F5 timing rules

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

Regenerate the derived matrix with:

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
- W1-W5 outcome;
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

---

# Change-control rule

Before changing any analysis:

1. Ask: **Did the real enterprise environment change?**
   - Yes -> update invariants.
   - No -> leave invariants untouched.

2. Ask: **Did a topology/health/timing assumption change?**
   - Yes -> update variables.
   - No -> leave variables untouched.

3. Regenerate the failure matrix from those inputs.

This separation is intended to prevent the baseline from drifting every time a new WAF option or failure scenario is considered.
