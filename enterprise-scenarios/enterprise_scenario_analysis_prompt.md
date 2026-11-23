# Enterprise WAF Scenario Analysis — Regeneration Prompt

## Purpose

Use this prompt to regenerate or refresh the EnterpriseWAF failure analysis **without changing the stable enterprise baseline**.

The analysis is deliberately split into canonical terminology/topology, stable inputs, changeable inputs and derived outputs.

### 0. Canonical shorthand and topology

Read first:

- [architecture_shorthand_topology_reference.md](./architecture_shorthand_topology_reference.md)

Treat this as the authoritative source for:

- W1-W4 topology meanings;
- D1/S1/S2/S3 tenancy/sharing meanings;
- X1/X2A/X2B/X2C/XD1 recovery meanings;
- T1-T9 timing meanings;
- AT1-AT4 application-type shorthand;
- the canonical external/internal/CFW/ELB/App A/B/C logical path.

Do not reuse `W1/W2/W3` as WAF-node names. Use `WAF-1/WAF-2/WAF-3`.

Do not reuse `S1/S2` as generic site labels. Use `Site 1 / Site 2`.

Prefer `App A @ Site 1` and `App B @ Site 2` rather than ambiguous application-instance labels such as `A1/B2`.

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

- W1-W4 candidate WAF topologies, each normally replicated across both sites except the deliberate W4 asymmetry;
- D1/S1/S2/S3 tenancy/sharing choices;
- local-only versus controlled cross-site routing;
- GTM health-check models;
- GTM response/preference models;
- F5 LTM/GTM/WAF health-monitor behavior;
- F5 HA/mirroring considerations;
- recovery-time modelling assumptions.

Change this file when testing a different topology, health-check strategy, capacity assumption or F5 recovery configuration.

### 3. Derived analyses

Regenerate/update:

- **Executive recommendation:** [executive_recommendation.md](./executive_recommendation.md)
- **Architecture summary:** [deployment_options_resilience_summary.md](./deployment_options_resilience_summary.md)
- **Lens 1 — primary end-to-end service impact/recovery:** [end_to_end_service_impact_analysis.md](./end_to_end_service_impact_analysis.md)
- **Lens 1 technical appendix:** [common_failure_matrix.md](./common_failure_matrix.md)
- **Lens 2 — maintainability/change safety:** [maintainability_change_management_analysis.md](./maintainability_change_management_analysis.md)
- **Cross-site/dependency study:** [cross_site_routing_and_dependency_recovery.md](./cross_site_routing_and_dependency_recovery.md)

These are **derived outputs**. They should be regenerated when the invariant file, variable file, or canonical shorthand/topology changes.

Do not copy new assumptions directly into a derived analysis without first deciding whether they belong in the invariant file or the variable file.

A new analysis lens should be added as a separate derived document where possible rather than expanding the invariant baseline or mixing unrelated conclusions into the failure matrix.

---

# Analysis instructions

You are reviewing a dual-site enterprise application-delivery architecture using F5 BIG-IP DNS/GTM, LTM and Advanced WAF/ASM.

Use the canonical, invariant and variable files above.

## Mandatory comparison dimensions

Analyse all selected WAF topology options using the canonical definitions:

- **W1** — LTM-fronted scalable independent **active** WAF pool;
- **W2** — WAF HA/DSC cluster, with and without ingress LTM where relevant;
- **W3** — tenant-preferred **active** WAFs plus shared reserve WAFs;
- **W4** — asymmetric design: Site 1 WAF HA cluster + one extra active/spare WAF; Site 2 WAF HA cluster only. Analyse both W4a (LTM in front) and W4b (no ingress LTM in front of WAF).

W1-W3 normally use the same logical WAF topology in both sites. W4 is the deliberate asymmetry exception: Site 1 has the cluster plus an extra active/spare WAF, while Site 2 has the cluster only. GTM/LTM roles remain similar per site unless a scenario explicitly says otherwise. GTM site recovery is part of each topology and is not a separate WAF option.

Also distinguish:

- **X1** — local-only dataplane routing;
- **X2A** — surviving local LTM uses a remote WAF and routes back through the healthy local CFW/ELB/application path;
- **X2B** — remote front end routes back through the healthy primary-site CFW/ELB/application path;
- **X2C** — conventional site/application failover;
- **XD1** — App A remains local and uses remote App B through a health-aware service abstraction.

## Mandatory tenancy, sharing and four-tenant cost comparison

Treat tenancy/sharing as a design axis separate from W1-W4.

Use an illustrative **four-tenant** planning case and compare canonical patterns:

- **D1** — fully dedicated tenant LTM + WAF capacity;
- **S1** — dedicated tenant LTMs + shared independent active WAF pool;
- **W3 hybrid** — dedicated preferred WAFs + shared reserve;
- **S2** — shared LTM + shared independent active WAF pool;
- **S3** — shared WAF HA cluster where relevant.

For each pattern show:

- LTM/WAF device-unit count across two sites;
- N-1 and N-2 WAF failure tolerance, with capacity caveat;
- complete cluster/pool failure impact;
- cross-tenant blast radius;
- maintenance/change blast radius;
- cross-site aggregate capacity requirement;
- whether one shared bad policy/configuration can affect all tenants.

Use device-unit count only as a planning proxy; do not present it as vendor pricing.

Do not silently change the invariant tenant count. Four tenants is an explicit comparison case derived from the wider 3–4 tenant estate.

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
- local App B dependency failure -> App A/C/D readiness failure;
- multiple application GTM withdrawals;
- Site 2 capacity surge;
- reconnect/login storm;
- dependency/database/identity overload;
- manual DR.

Quantify the change in recovery class/timing where possible, for example ~16s-class local/dependency recovery versus ~46–150s+ site recovery.

## Mandatory cross-site recovery study

Also read and regenerate/update when relevant:

- [cross_site_routing_and_dependency_recovery.md](./cross_site_routing_and_dependency_recovery.md)

Do not describe X2A/X2B/X2C/XD1 simply as "cross-site routing." Their detection, DNS dependency, latency, capacity and failure modes differ materially.

## Mandatory end-to-end topology/path

Use the canonical reference path for private-cloud hosted applications:

```text
External user/API
  -> external/customer DNS
  -> enterprise external DNS/GTM
  -> leased line / VPN
  -> edge firewall / application VIP
  -> tenant LTM HA pair where present
  -> WAF topology
  -> CFW
  -> ELB/service
  -> App A
  -> internal dependency DNS/service abstraction
  -> App B
  -> App C / shared dependencies
```

Internal path:

```text
Internal user/system
  -> internal enterprise DNS
  -> optional internal GTM/service name
  -> internal LTM/service VIP
  -> CFW
  -> ELB/service
  -> application
```

If a hosting pattern bypasses CFW, ELB, WAF or LTM, say so explicitly rather than silently omitting the layer.

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

## Default LTM count

The enterprise baseline is **two LTMs per site** in an HA/Sync-Failover pair wherever an ingress/tenant LTM tier is used.

A three-device LTM DSC group is an optional comparison only. Do not silently promote it into W1-W4 baseline calculations.

When node-count discussion is needed, use [appendix_ltm_waf_2_vs_3_nodes.md](./appendix_ltm_waf_2_vs_3_nodes.md) and distinguish:

- DSC failover groups, where one traffic group/VIP has one active owner;
- multiple traffic groups active on different DSC devices;
- independent WAF pool members behind an LTM, where all healthy WAF members can process the same service concurrently.

## Mandatory actor/path dimensions

Analyse:

- external users over private leased-line paths using the **external namespace**;
- external systems/API clients using the external namespace;
- internal users using **internal enterprise DNS**, with selected internal service names optionally delegated/forwarded to GTM;
- internal applications resolving App B/App C/internal service endpoints through internal DNS and, where configured, GTM;
- internal users that may bypass WAF and connect through internal LTM/service VIP -> CFW -> ELB/service endpoints for private-cloud applications;
- Application A -> Application B -> Application C and shared-dependency chains;
- non-web services that bypass WAF.

Treat **external namespace resolution** and **internal namespace resolution** as separate failure domains. Do not assume a DNS/GTM failure affects both unless the architecture actually shares that failure domain.

## Mandatory platform-firewall layer

For private-cloud hosted applications, model the inline path as:

```text
WAF/LTM
  -> platform/cloud firewall (CFW)
  -> application ELB/service
  -> VM / Kubernetes / PaaS workload
```

Treat CFW and ELB as separate health, routing, NAT/state, change and failure domains.

For CFW failures state:

- whether external and internal flows share the same CFW;
- CFW HA/member behavior;
- full CFW context/service failure impact;
- whether a healthy ELB/app becomes unreachable;
- whether multiple applications behind the same CFW fail together;
- whether cross-site routing can reach the alternate CFW/ELB;
- whether GTM/app health correctly detects the failure;
- whether CFW failure triggers unnecessary multi-application/site failover.

## Mandatory application types

Every failure scenario must state the applicable application type using the canonical IDs:

1. **AT1** — stateless web;
2. **AT2** — stateful web;
3. **AT3** — socket/WebSocket/long-lived connection;
4. **AT4** — non-web/L4 application bypassing WAF.

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
14. platform/cloud firewall (CFW) member/HA service and full CFW context;
15. application ELB/service tier;
16. VM/Kubernetes member/cluster;
17. application readiness;
18. session/state store;
19. App A -> App B -> App C dependency;
20. cross-site route;
21. asymmetric cross-site path;
22. entire site;
23. passive site not ready;
24. long-lived connection recovery.

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

## CFW timing/recovery requirement

For private-cloud paths, explicitly analyse:

- one CFW HA member failure with the same local service path retained;
- complete local CFW context/service failure;
- CFW false-green where WAF/front-end is healthy but CFW -> ELB/application is unreachable.

Do not assign an invented numeric CFW HA default. Record CFW HA timing as **measured/TBD** until the firewall product/configuration is known.

However, show the service-level consequence:

- successful CFW HA should remain local with **no DNS TTL**;
- whole CFW failure that triggers site recovery uses the existing GTM/DNS recovery timing (~46–150s + T6 depending health model);
- false-green CFW can be unbounded until through-path readiness detects it.

## F5 timing rules

The canonical timing meanings are T1-T9 in [architecture_shorthand_topology_reference.md](./architecture_shorthand_topology_reference.md) and [analysis_variables_and_f5_assumptions.md](./analysis_variables_and_f5_assumptions.md).

### Numeric recovery timing requirement

The primary output must contain an explicit timing table with numeric planning windows where defaults support them.

At minimum show:

- BIG-IP HA peer: ~3s+ detection plus convergence;
- LTM member/WAF member: up to ~16s with common 5s/16s defaults;
- GTM DNS A-record pool TTL: 30s default;
- direct GTM monitor: 30s interval / 120s timeout for common HTTP/HTTPS/TCP-style monitors;
- illustrative fast site move: ~16s local health + up to 30s residual TTL = ~46s + T6, plus measured iQuery/propagation;
- default-direct-monitor site move: T3 (~120s timeout) + T4 (up to ~30s residual TTL/cache) = up to ~150s + T6;
- manual DR: T5 + T4 + T6, with the applicable health-detection term stated separately.

Explicitly distinguish:

- new uncached clients;
- clients with cached old DNS answers;
- already-established TCP/TLS/WebSocket connections;
- applications with their own DNS/connection-pool cache.

Do not state that DNS TTL moves an existing connection.

Do not state that LTM member failover is interruption-free for a connection already anchored to the failed member.

Do not invent a single vendor failover number.

### T4 canonical rule

**T4 starts after the relevant health decision.** It means:

```text
GTM answer/site-selection update
 + residual DNS TTL/cache
 + client re-resolution/retry to the selected endpoint
```

Do **not** include T3 health detection, T5 alternate-site startup/readiness, or T6 application/session/socket restoration inside T4 and then add them again.

For every timing value state whether it is:

- F5 documented default/behavior;
- configured design target;
- measured value;
- or unknown/TBD.

## Application compliance

Call out application code/configuration prerequisites.

### AT1 — Stateless web

Require:

- safe retry;
- idempotency where duplicate requests matter;
- shared/external state;
- readiness monitoring.

### AT2 — Stateful web

Require:

- documented state/session location;
- portable/replicated state;
- safe re-auth/session recovery;
- transaction reconciliation;
- compatible alternate-site data.

### AT3 — Socket/WebSocket

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

### AT4 — Non-web

Require:

- protocol-specific reconnect/retry;
- safe replay/transaction semantics;
- endpoint re-resolution;
- state/persistence documentation.

If these are absent, explicitly mark the application **not end-to-end resilient** and explain how that reduces the overall recoverability even when F5 infrastructure is HA.

---

# Required output structure

## Executive recommendation output

Regenerate [executive_recommendation.md](./executive_recommendation.md) with:

1. a self-contained topology legend for **W1/W2/W3/W4/S1/S2** before any ranked table, with plain-English descriptions and small diagrams;
2. a link to the canonical shorthand/topology reference;
3. a short legend for X2A/X2B/X2C/XD1;
4. a ranked final recommendation rather than only neutral comparison;
5. the preferred four-tenant cost/resilience option;
6. the preferred highest-isolation option;
7. a 99.95% architectural-potential rating for each major option;
8. common/credible failure and maintenance events that should remain R0/R1;
9. failures where R2 cross-site component/dependency recovery materially improves the outcome;
10. options not recommended as the default and why;
11. required change controls and application compliance;
12. explicit decision/acceptance gates before claiming the 99.95 target.

Do not claim that any topology **meets** 99.95 until fault-injection and maintenance testing provide measured end-to-end evidence. Use terms such as **high potential**, **credible**, or **conditional** until proven.

## Architecture summary

Regenerate [deployment_options_resilience_summary.md](./deployment_options_resilience_summary.md) with:

- canonical W/S/X topology shorthand near the top;
- a self-contained **T1-T9 reference table**;
- a link back to the canonical reference and detailed timing assumptions;
- examples showing how T3/T4/T5/T6/T9 combine without double-counting.

Then include:

1. W1-W4 topology summary;
2. one-node / two-node / whole-cluster-or-pool resilience;
3. cross-site versus no-cross-site comparison;
4. AT1/AT2/AT3/AT4 application-type comparison;
5. failure scenarios from DNS/circuit/firewall through LTM/WAF/CFW/ELB/app/state/dependency/site;
6. four-tenant dedicated/shared device-count and blast-radius comparison;
7. explicit conclusions on cost efficiency versus isolation/common-mode risk.

## Lens 1 — end-to-end service impact/recovery

First regenerate [end_to_end_service_impact_analysis.md](./end_to_end_service_impact_analysis.md) as the primary output. It must lead with actor impact, service outage time and recoverability.

Then regenerate [common_failure_matrix.md](./common_failure_matrix.md) as the technical component appendix with:

1. topology shorthand;
2. timing model;
3. control-plane/ingress failure table;
4. LTM failure table;
5. WAF failure table;
6. CFW/backend/application failure table;
7. cross-site/dependency failure table;
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
7. CFW maintenance;
8. GTM maintenance;
9. WAF policy/signature strategy;
10. blue-green/canary feasibility;
11. application draining;
12. 99.95 maintainability test;
13. topology scorecard;
14. critical maintainability risks;
15. recommended operating model;
16. maintainability conclusions.

---

# Change-control rule

Before changing any analysis:

1. Ask: **Did canonical shorthand/topology change?**
   - Yes -> update `architecture_shorthand_topology_reference.md` first, then reconcile downstream documents.

2. Ask: **Did the real enterprise environment change?**
   - Yes -> update invariants.
   - No -> leave invariants untouched.

3. Ask: **Did a topology/health/timing assumption change?**
   - Yes -> update variables.
   - No -> leave variables untouched.

4. Regenerate the executive/deployment summaries.
5. Regenerate the end-to-end service impact/recoverability analysis.
6. Regenerate the technical common failure matrix that supports it.
7. Regenerate the maintainability/change-safety analysis from the same inputs.
8. Keep findings in their derived lens; promote a fact into invariants or variables only when it is genuinely a reusable input.

This separation is intended to prevent the baseline and terminology from drifting every time a new WAF option or failure scenario is considered.
