# Deployment Options, Resilience and Four-Tenant Cost Summary

**Status:** Primary architecture comparison summary  
**Canonical shorthand/topology:** [architecture_shorthand_topology_reference.md](./architecture_shorthand_topology_reference.md)  
**Baseline:** [enterprise_scenario_invariants.md](./enterprise_scenario_invariants.md)  
**Detailed service impact:** [end_to_end_service_impact_analysis.md](./end_to_end_service_impact_analysis.md)  
**Technical failures:** [common_failure_matrix.md](./common_failure_matrix.md)  
**Cross-site detail:** [cross_site_routing_and_dependency_recovery.md](./cross_site_routing_and_dependency_recovery.md)

# 1. Executive summary

This document answers four architecture questions together:

1. Which deployment options tolerate **one node, two nodes, a complete local cluster/tier, or a complete site failure**?
2. How does the answer change with **cross-site routing** versus local-only routing?
3. What do **stateless web, stateful web, WebSocket/long-lived and non-web applications** experience?
4. For **four tenants**, what is the relative infrastructure cost and blast radius of dedicated versus shared LTM/WAF capacity?

The central conclusion is:

> The best design is not the topology with the most HA devices. It is the design that keeps the recovery domain proportional to the failed component, has enough surviving capacity, and is matched by application retry/state/reconnect behavior.

A single WAF or backend failure should remain a **local member failure**. It should not automatically become a DNS/site/application failover.

## Scope boundary for this decision

The current decision set is the **four existing Extranet tenant stacks**.

Keep the following assumptions fixed for this comparison:

- each of the four tenants keeps its current LTM/GTM failure domain;
- the current decision is whether WAF runtime capacity can be shared more efficiently while retaining application-specific WAF policy isolation;
- **S2 shared-LTM consolidation is a future option only**, not the current recommendation;
- wider Internet/Intranet consolidation is outside the current scope unless separately commissioned.

This prevents a WAF-pooling study from silently turning into a broader network consolidation programme.

## 1.1 Topology shorthand — read this before the comparison

The canonical definitions are maintained in [architecture_shorthand_topology_reference.md](./architecture_shorthand_topology_reference.md).

| ID | Meaning |
|---|---|
| **W1** | Dedicated/tenant LTM HA pair -> **independent active WAF pool** (2..N WAFs) |
| **W2** | **WAF HA/DSC cluster**, with or without ingress LTM; one active owner per traffic group |
| **W3** | Tenant LTM pair -> tenant-preferred active WAFs + **shared reserve WAF capacity** |
| **W4** | Asymmetric: Site 1 WAF HA cluster + extra WAF; Site 2 WAF HA cluster only |
| **S1** | **Tenant-specific LTM pairs -> shared independent active WAF pool** |
| **S2** | **Shared LTM pair -> shared independent active WAF pool**; future consolidation option, not current Extranet recommendation |
| **X2A** | Surviving local LTM uses remote WAF and routes back through the healthy local CFW/ELB/application path |
| **X2B** | Remote front end routes back to the healthy primary-site CFW/ELB/application path |
| **X2C** | Full application/site failover |
| **XD1** | Local App A uses remote App B fallback |

The important distinction is:

- **W1/S1/S2 active WAF pool:** multiple healthy independent WAFs can process the same service concurrently.
- **W2/W4 WAF HA cluster:** one device owns a traffic group; another device is the HA failover target.
- **W3:** combines tenant-preferred active WAFs with shared reserve capacity.

## 1.2 Timing reference — T1 to T9

The detailed timing definitions live in [analysis_variables_and_f5_assumptions.md](./analysis_variables_and_f5_assumptions.md#5-f5-monitoring-and-recovery-time-assumptions). The canonical definitions are also summarized in [architecture_shorthand_topology_reference.md](./architecture_shorthand_topology_reference.md).

| ID | Meaning | Planning value / interpretation | When to add it |
|---|---|---|---|
| **T1** | BIG-IP HA peer/device failover | approximately **3+ seconds peer-loss detection**, plus traffic-group/network convergence | LTM/WAF/GTM HA peer or traffic-group ownership change |
| **T2** | LTM pool-member / WAF-member health detection | commonly **up to ~16s** with 5s interval / 16s timeout defaults | failed independent WAF, backend or service member behind a stable LTM VIP |
| **T3** | Direct BIG-IP DNS/GTM health monitor | common HTTP/HTTPS/TCP defaults around **30s interval / 120s timeout** | GTM directly decides an endpoint/site is unavailable |
| **T4** | DNS/site-selection convergence **after the health decision** | GTM answer change + residual DNS TTL/cache + client re-resolution/retry; GTM A-record pool TTL default is **30s** | whenever recovery changes the returned site/VIP; add T5/T6 separately |
| **T5** | Warm/cold/manual recovery | **minutes or longer; no fixed product value** | operator action, passive-site startup, routing repair, config/policy rollback |
| **T6** | Application recovery | **application-specific** | retry, reconnect, re-auth, session/state restore, resubscribe, replay/reconciliation |
| **T7** | Failback | controlled restoration; F5 auto-failback delay is configurable and commonly modelled around **60s when enabled** | return to preferred device/site after recovery |
| **T8** | DNS cache vs existing-connection behavior | **behavior modifier, not a duration** | distinguishes new DNS lookup, cached old IP, existing TCP/WebSocket, and app connection-pool caching |
| **T9** | Platform/cloud firewall (CFW) recovery | **product/config specific; measure** | CFW HA member failure, full CFW-context failure or CFW false-green |

### How to read combined timings

- **~16s + T6** = LTM detects/withdraws the failed member, then the application/client still has to recover.
- **T3 + T4 + T6** = direct GTM health detection, then DNS/site-selection convergence, then application/client recovery.
- **T5 + T4 + T6** = manual/passive-site preparation, then DNS/site selection, then application recovery.
- **~46s + T6** = illustrative fast-health site move: ~16s local health + up to 30s residual DNS TTL, plus application recovery.
- **up to ~150s + T6** = default-style direct GTM health timeout (~120s) + up to 30s residual DNS TTL, plus application recovery.
- **T9 + T6** = CFW HA/recovery timing plus any socket/session/application recovery.

These are **engineering planning values, not SLAs**. Measure the end-to-end time from fault injection to the first successful business transaction for each actor/application type.

## 1.3 Executive recommendation

For the final ranked recommendation and 99.95% assessment, see [executive_recommendation.md](./executive_recommendation.md).

In summary:

| Priority | Preferred design | Why |
|---|---|---|
| **Best four-tenant cost/resilience balance** | tenant-specific 2-LTM HA pair + shared independent active WAF pool | preserves tenant ingress boundaries while sharing horizontally useful WAF capacity |
| **Best isolation / highest-confidence maintainability** | dedicated W1 with 2 LTMs + 3 independent WAFs per tenant/site | strongest local maintenance and N-2-style headroom with smallest cross-tenant blast radius |
| **Good but more complex** | W3 preferred WAFs + shared reserve | strong recovery if reserve is guaranteed, but shared reserve governance is complex |
| **Simple but less maintenance margin** | W2b two-node WAF HA cluster | good first-failure HA/mirroring; pair boundary leaves less redundancy during maintenance |
| **Not preferred as critical-service default** | S2 shared LTM + shared WAF service | lowest device count but largest common-mode/cross-tenant blast radius and outside the current four-tenant Extranet decision scope |

# 2. Common stack

For a private-cloud web application, analyse failures from top to bottom:

~~~text
External user/system
  -> external DNS / GTM
  -> leased line / VPN
  -> edge firewall / external VIP
  -> LTM HA pair where present
  -> WAF tier
  -> platform/cloud firewall (CFW)
  -> ELB/service
  -> VM / Kubernetes / PaaS workload
  -> session/state/data
  -> App B / App C dependencies
~~~

Internal users/applications may enter lower in the stack:

~~~text
Internal user / App A
  -> internal enterprise DNS
  -> optional internal GTM
  -> internal service/LTM VIP
  -> CFW where private-cloud hosted
  -> ELB/service
  -> App B / App C
~~~

# 3. WAF topology options

## W1 — independent active WAF pool behind LTM

~~~text
Firewall VIP
    |
LTM HA pair
    |
+-----+-----+-----+
|     |     |     |
WAF-1 WAF-2 WAF-3 ... WAF-n
    |
   CFW
    |
   ELB/app
~~~

- WAFs are independent active pool members.
- Two WAFs give **N-1**, but not local N-2.
- Three or more WAFs can tolerate two WAF failures only when remaining capacity is explicitly sized for N-2.
- Existing long-lived connections through a failed WAF normally reconnect.

## W2 — WAF HA/DSC cluster

~~~text
Firewall VIP
    |
[ LTM HA pair ]
    |
WAF HA pair
active/standby for a traffic group
    |
   CFW
    |
   ELB/app
~~~

- One protected traffic group has one active WAF owner.
- A pair tolerates one WAF member failure.
- Loss of both cluster members removes the local WAF service.
- Supported connection mirroring can improve first-failure continuity for some long-lived connections.

## W3 — tenant-preferred WAFs plus shared reserve

~~~text
Tenant LTM pair
    |
preferred WAF-1 + WAF-2
    |
shared reserve WAF capacity
    |
   CFW
    |
   ELB/app
~~~

Baseline remains **two LTMs per tenant per site**.

## W4 — Site 1 cluster + extra WAF; Site 2 cluster only

~~~text
Site 1                         Site 2
LTM pair                       LTM pair
   |                              |
WAF HA cluster                WAF HA cluster
   |                              |
extra independent WAF             |
   |                              |
  CFW                            CFW
   |                              |
 ELB/app                        ELB/app
~~~

# 4. One-node, two-node and cluster/tier failure comparison

Ratings assume correct health monitoring and adequate surviving capacity.

| Failure | W1 2-WAF pool | W1 3+ WAF pool | W2 2-node HA cluster | W3 preferred pair + reserve | W4 |
|---|---|---|---|---|---|
| **1 WAF node fails** | **Survives locally**; one WAF remains | **Survives locally** | **Survives locally** via peer | **Survives locally** | **Survives locally** |
| **2 WAF nodes fail** | **Local WAF tier lost** | **Can survive** if N-2 capacity remains | **Cluster lost** | **Can survive via reserve** if available | Site 1 may use extra WAF if failed nodes are cluster pair; Site 2 cluster is lost |
| **Entire local WAF cluster/pool lost** | No local WAF | No local WAF | No local WAF | Reserve may still provide local service if outside failed domain | Site 1 extra may survive cluster loss; otherwise no local WAF |
| **1 LTM node fails** | Survives via pair | Same | W2b survives; W2a has no ingress LTM | Survives via tenant LTM pair | W4a survives |
| **Both LTMs fail** | Entire local front end lost | Same | W2b front end lost; W2a unaffected by LTM failure | Preferred **and reserve** WAFs become unreachable through that tenant LTM service | W4a local front end lost |
| **1 CFW member fails** | Should remain local through CFW HA | Same | Same | Same | Same |
| **Whole CFW service/context fails** | WAF recovery alone cannot help | Same | Same | Same | Same |
| **Whole site fails** | Site 2 required | Site 2 required | Site 2 required | Site 2 required | Site 2 required; lower WAF headroom than Site 1 |

# 5. Cross-site versus no-cross-site capability

Cross-site capability should reduce **failure-domain escalation**. It should not be required for normal healthy operation.

| Local failure | No cross-site component/dependency routing | With cross-site capability | Typical difference |
|---|---|---|---|
| **One WAF fails** | Local pool/cluster recovers | Same | Cross-site not needed |
| **Both/all local WAFs fail; LTM+CFW+app healthy** | Restore WAF locally or move service/site | **X2A:** local LTM can use remote WAF and route back to healthy local CFW/app | Can change site-failover event into **~16s-class + T6** local-ingress recovery |
| **Local LTM+WAF tier fails; CFW/app healthy** | Full app/site move or outage | **X2B:** Site 2 front end can route back to Site 1 CFW/app | Avoids moving a healthy application; still needs GTM/DNS convergence |
| **Local CFW fails; local app healthy** | Restore CFW or move app/site | Remote WAF alone does **not** help; need alternate CFW/site application path | Cross-site WAF is not a substitute for CFW resilience |
| **App B @ Site 1 fails; App A @ Site 1 healthy** | A may fail/cascade/site-move | **XD1:** A stays local and uses App B @ Site 2 | Prevents dependency failure becoming application/site failure |
| **Whole site fails** | Site 2 full recovery | Site 2 full recovery | Route-back cannot recover a lost site |

## Indicative recovery classes

- local BIG-IP HA peer: **~3s+ + connection recovery**;
- local LTM WAF-member withdrawal: **up to ~16s + T6** with common monitor defaults;
- X2A remote WAF with same client VIP: **~16s-class + T6** if remote WAF and local CFW/app path are ready;
- GTM/site move using fast local health: illustrative **~46s + T6**;
- GTM/site move with default-style direct GTM monitoring: **up to ~150s + T6**;
- manual passive-site startup: **T5 + T4 + T6**, with T5 potentially dominant;
- CFW false-green or application false-green: potentially **unbounded** until correct readiness detects it.

# 6. Application-type comparison

| Application type | Single member failure | WAF/LTM/CFW path change | Site/dependency failover | Main acceptance requirement |
|---|---|---|---|---|
| **AT1 — Stateless web** | Usually one failed request/retry | New request can use healthy path | Re-resolve/retry to ready site | safe retry, external/shared state, idempotency |
| **AT2 — Stateful web** | May lose session/transaction affinity | Session may need reconstruction or re-login | State/data must exist at alternate path/site | portable/replicated state and transaction reconciliation |
| **AT3 — WebSocket / long-lived** | Socket on failed path normally breaks unless supported mirroring preserves it | reconnect + re-auth + resubscribe | re-resolve + reconnect + replay/snapshot | reconnect/backoff, durable cursor/state, replay, idempotency |
| **AT4 — Non-web / L4** | Protocol-specific connection loss | reconnect/retry; WAF may be irrelevant | protocol/DNS/service failover | documented protocol retry, re-resolution, transaction replay |

# 7. Failure scenarios up and down the stack

| Layer/failure | External users | Internal users / App A->B | Preferred local recovery | Cross-site recovery if local recovery exhausted | Cascade risk |
|---|---|---|---|---|---|
| **External DNS/GTM** | new resolution affected | usually unaffected if internal namespace independent | redundant DNS/GTM | alternate authoritative path | external-only outage if namespaces separated |
| **Internal DNS/GTM** | external may remain healthy | internal users/apps can fail | redundant internal DNS/GTM | remote internal endpoint if designed | many apps can fail dependencies together |
| **Leased line/VPN** | subset of external population affected | usually no impact | alternate circuit/routing | alternate site only if required | user-population blast radius |
| **Edge firewall member** | transient/no impact if HA succeeds | depends on path | firewall HA | alternate ingress/site | NAT/state loss can reset connections |
| **Whole edge firewall pair/path** | external ingress unavailable | internal may remain healthy | alternate local edge path | GTM/site | external outage while app stays healthy |
| **One LTM** | short HA event | internal/dependency VIPs using pair may see same | LTM peer | site/front-end recovery | normally contained |
| **Both LTMs** | local front-end unavailable | dependency VIPs on same pair fail | none within pair | X2B/site | all downstream WAF capacity becomes inaccessible |
| **One WAF** | transient failed requests/sockets | usually no internal impact if bypassed | peer/pool member | not required | low |
| **Two/all WAFs** | external application unavailable locally | internal app may remain healthy | W1 N-2/W3 reserve/W4 extra where available | X2A or site move | WAF fault can become application DR without X2A |
| **One CFW** | target seconds-scale HA | internal App A->B through CFW also affected | CFW peer | normally not needed | state/NAT loss can reset many sessions |
| **Whole CFW** | app unreachable despite healthy WAF/ELB | internal dependencies behind same CFW fail | alternate CFW | site/app path | multi-application platform blast radius |
| **ELB member/backend** | brief retry | same for dependent callers | healthy backend member | normally not needed | low if stateless/capacity sufficient |
| **Whole ELB/service** | app unavailable | dependent apps fail | redundant ELB/service | site/app recovery | dependency cascade |
| **App readiness false-green** | errors/hangs | dependencies error/hang | app readiness must withdraw service | site if alternate app ready | potentially unbounded |
| **State/session/data service** | sessions/workflows fail | multiple apps can fail | state/data HA | alternate state/site | high common-mode |
| **App B dependency** | App A features fail | A/C/D may all fail | stable service VIP/local alternate | XD1 remote App B | major cascade if timeouts/retries poor |
| **Whole site** | full site loss | internal/app dependencies also move | none | Site 2 full recovery | DR capacity/readiness dominates |

# 8. Four-tenant cost and sharing model

## 8.1 Cost metric

This section uses **device-unit count**, not vendor price.

- one physical/virtual LTM appliance = 1 LTM device-unit;
- one physical/virtual WAF appliance = 1 WAF device-unit;
- counts cover **two sites**;
- GTM, edge firewall, CFW, ELB, platform and application cost are excluded because their sharing/dedication model may differ;
- licensing, throughput tier, support and virtual contexts can materially change actual cost.

## 8.2 Four fully dedicated tenants

Assume each tenant/site has two LTMs and two WAFs.

Across two sites:

~~~text
4 tenants x 2 sites x (2 LTM + 2 WAF)
= 16 LTM + 16 WAF
= 32 device-units
~~~

If every tenant gets a third dedicated WAF:

~~~text
16 LTM + 24 WAF = 40 device-units
~~~

## 8.3 W3 hybrid: dedicated preferred capacity + shared reserve

With two preferred WAFs per tenant/site and **R** shared reserve WAFs per site:

~~~text
LTM total = 16
WAF total = 16 + 2R
Total = 32 + 2R device-units
~~~

For **R=2 shared reserve WAFs/site**:

~~~text
16 LTM + 20 WAF = 36 device-units
~~~

The benefit is **shared spare capacity**, not the absolute minimum device count.

## 8.4 Shared independent active WAF pool

### S1 — tenant LTM pairs, shared WAF pool

~~~text
Tenant1 LTM pair --\
Tenant2 LTM pair ---+--> shared active WAF pool --> tenant/app CFW/ELB
Tenant3 LTM pair ---+
Tenant4 LTM pair --/
~~~

Across two sites:

~~~text
16 LTM + 2P WAF
~~~

Illustrative **P=4**:

~~~text
16 LTM + 8 WAF = 24 device-units
~~~

If the four-WAF pool is sized so two surviving WAFs can carry required aggregate load, it can tolerate two WAF-node failures without losing the WAF service.

### S2 — shared LTM pair + shared WAF pool (**future option only**)

Illustrative across two sites:

~~~text
4 LTM + 2P WAF
~~~

With **P=4**:

~~~text
4 LTM + 8 WAF = 12 device-units
~~~

This has a much larger shared failure/change domain because both ingress LTM and WAF capacity are shared. It is outside the current four-tenant Extranet decision boundary.

## 8.5 Shared WAF HA cluster

With one shared LTM pair/site and one two-device WAF HA cluster/site:

~~~text
4 LTM + 4 WAF = 8 device-units across two sites
~~~

With four tenant LTM pairs feeding the shared WAF cluster:

~~~text
16 LTM + 4 WAF = 20 device-units
~~~

## 8.6 Four-tenant comparison

| Tenancy / topology pattern | LTM units | WAF units | Total | 1 WAF failure | 2 WAF failures | Tenant isolation | Cross-tenant blast radius |
|---|---:|---:|---:|---|---|---|---|
| **4x dedicated W1, 2 WAF/tenant/site** | 16 | 16 | **32** | Yes | No local WAF service for affected tenant | **High** | Low |
| **4x dedicated W1, 3 WAF/tenant/site** | 16 | 24 | **40** | Yes | Yes if N-2 capacity | **High** | Low |
| **4x dedicated W2a HA cluster, no ingress LTM** | 0 | 16 | **16** | Yes | Cluster lost for affected tenant | **High** | Low |
| **4x dedicated W2b HA cluster + LTM** | 16 | 16 | **32** | Yes | Cluster lost for affected tenant | **High** | Low |
| **4x dedicated W4a asymmetric** | 16 | 20 | **36** | Yes | Site 1 can use extra WAF after cluster loss; Site 2 cannot | **High** | Low |
| **W3: 2 preferred/tenant + 2 shared reserve/site** | 16 | 20 | **36** | Yes | Usually yes for one tenant if reserve free | Medium-High | Medium |
| **S1 tenant LTMs + shared active pool, P=4/site** | 16 | 8 | **24** | Yes | Yes if 2 remaining WAFs sized for aggregate load | LTM high / WAF shared | **High at WAF tier** |
| **S2 shared LTM + shared active pool, P=4/site — future only** | 4 | 8 | **12** | Yes | Yes if capacity | Low | **Very high** |
| **Shared LTM + shared 2-node WAF HA cluster — future only** | 4 | 4 | **8** | Yes | No; whole shared WAF service lost | Low | **Very high** |

These totals are planning examples, not purchase quotes or recommendations by themselves.

# 9. Resilience versus cost interpretation

## Best tenant isolation

Dedicated LTM/WAF per tenant provides the smallest cross-tenant blast radius and easiest capacity attribution, at the cost of duplicated standby/spare capacity.

## Best active-capacity efficiency within the current scope

A **shared independent active WAF pool** behind the existing tenant-specific LTM pairs can provide strong aggregate capacity efficiency without changing the LTM/GTM ownership boundary.

For four tenants, S1 is the primary sharing candidate:

> retain tenant-specific LTM pairs and routing boundaries, but share a sufficiently large active WAF pool with application-specific policy isolation.

## Best shared-spare model

W3 is attractive when the organisation wants dedicated preferred WAF capacity but does not want to buy a dedicated third WAF for every tenant.

# 10. Cascading failures without cross-site capability

## WAF tier cascade

~~~text
tenant local WAF tier fails
  -> local app/CFW/ELB still healthy
  -> no remote WAF route
  -> external service unavailable
  -> GTM moves whole application/site
  -> DNS cache/reconnect
  -> Site 2 load surge
~~~

With X2A, the local LTM can use a remote WAF and keep the local CFW/ELB/application in service.

## Shared WAF pool cascade

~~~text
shared WAF pool / shared policy fails
  -> Tenant 1 external service fails
  -> Tenant 2 external service fails
  -> Tenant 3 external service fails
  -> Tenant 4 external service fails
  -> multiple GTM/site failovers
  -> Site 2 aggregate surge
~~~

Shared cross-site capacity must therefore be sized for **aggregate tenant failover**, not one tenant only.

## Dependency cascade

~~~text
App B @ Site 1 fails
  -> App A / C / D @ Site 1 timeout/retry
  -> readiness fails
  -> several applications move site
  -> DNS/reconnect/login surge
  -> remote B / DB / identity surge
~~~

XD1 local-preferred/remote-fallback dependency routing keeps A/C/D local when remote App B is safe and reachable.

# 11. Recommended comparison set

For the current four-tenant Extranet decision, compare at least:

1. **Fully dedicated:** existing tenant-specific 2-LTM pairs + 2 or 3 independent WAFs/tenant/site.
2. **S1 tenant LTM + shared active WAF pool:** retains the existing tenant LTM/GTM boundary while sharing horizontally useful WAF capacity.
3. **W3 dedicated preferred + shared reserve:** dedicated normal-state WAF capacity plus shared failure/maintenance reserve.
4. **W2 clustered WAF:** useful where first-failure connection mirroring is more important than horizontal WAF scaling.

Treat **S2 shared-LTM consolidation** as a separate future architecture programme, not part of this decision.

# 12. Architecture recommendation

For the current four-tenant Extranet estate:

1. retain the tenant LTM/GTM failure domains;
2. define the maximum acceptable **cross-tenant WAF blast radius**;
3. define whether the shared pool must survive N-1 or N-2;
4. prove application-specific WAF policy isolation, canary and rollback;
5. decide whether healthy local applications may use **remote WAF/dependency capacity**;
6. validate AT1/AT2/AT3/AT4 recovery requirements;
7. size Site 2 for the **largest credible simultaneous failover**;
8. only then optimize WAF device count.

The most balanced shared option to evaluate is:

~~~text
existing tenant-specific LTM HA pair
        |
shared independent active WAF pool
        |
application-specific WAF policy
        |
tenant/application CFW + ELB/app paths
~~~

The dedicated W1 model remains the clearest choice when tenant isolation and predictable blast radius are more important than appliance efficiency.

W3 remains attractive when the enterprise specifically wants **dedicated normal-state WAFs plus shared failure/maintenance reserve**.

## 12.1 Longer-term target-state option — separate decision

If a later programme explicitly considers LTM/GTM consolidation, compare security-zone/cloud-level stacks separately.

A future option may share runtime by functional/security zone while retaining distinct tenant/policy boundaries, for example:

- Extranet/user-facing application delivery;
- Internet breakout/proxy/outbound services;
- other regulatory or criticality domains where required.

Do not treat that as the current four-tenant WAF-pooling recommendation.
