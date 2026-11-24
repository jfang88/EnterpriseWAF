# Deployment Options, Resilience and Four-Tenant Cost Summary

**Status:** Primary architecture comparison summary  
**Baseline:** [current_architecture_and_invariants.md](./current_architecture_and_invariants.md)  
**Detailed service impact:** [end_to_end_service_impact_analysis.md](./end_to_end_service_impact_analysis.md)  
**Technical failures:** [common_failure_matrix.md](./common_failure_matrix.md)  
**Cross-site detail:** [cross_site_routing_and_dependency_recovery.md](./cross_site_routing_and_dependency_recovery.md)

# 1. Executive summary

## 1.0 Current scope and ownership constraint

The primary design is the **four-tenant extranet estate**.

For the current WAF target:

- retain the existing GTM model;
- retain the existing tenant LTM HA service boundaries;
- compare WAF topology/sharing behind those boundaries;
- treat shared-LTM/S2 consolidation as a future comparison only;
- treat X2A/X2B as candidate capabilities until GTM/LTM/network/firewall owners validate them.

This document therefore does **not** recommend LTM/GTM consolidation as part of the current WAF decision.

See [current_architecture_and_invariants.md](./current_architecture_and_invariants.md) for the authoritative current-state baseline, end-to-end topology and ownership-boundary diagram.

This document answers four architecture questions together:

1. Which deployment options tolerate **one node, two nodes, a complete local cluster/tier, or a complete site failure**?
2. How does the answer change with **cross-site routing** versus local-only routing?
3. What do **stateless web, stateful web, WebSocket/long-lived and non-web applications** experience?
4. For **four tenants**, what is the relative infrastructure cost and blast radius of dedicated versus shared LTM/WAF capacity?

The central conclusion is:

> The best design is not the topology with the most HA devices. It is the design that keeps the recovery domain proportional to the failed component, has enough surviving capacity, and is matched by application retry/state/reconnect behavior.

A single WAF or backend failure should remain a **local member failure**. It should not automatically become a DNS/site/application failover.

## 1.1 Topology shorthand — read this before the comparison

| ID | Meaning |
|---|---|
| **W1** | Dedicated/tenant LTM HA pair -> **independent active WAF pool** (2..N WAFs) |
| **W2** | **WAF HA/DSC cluster**, with or without ingress LTM; one active owner per traffic group |
| **W3** | Tenant LTM pair -> tenant-preferred WAFs + **shared reserve WAF capacity** |
| **W4** | Asymmetric: Site 1 WAF HA cluster + extra WAF; Site 2 WAF HA cluster only |
| **S1** | **Tenant-specific LTM pairs -> shared independent active WAF pool** |
| **S2** | **Shared LTM pair -> shared independent active WAF pool (future comparison; outside current LTM/GTM scope)** |
| **X2A** | Surviving local LTM uses remote WAF and routes back to the local application path |
| **X2B** | Remote front end routes back to the healthy primary-site application path |
| **X2C** | Full application/site failover |
| **XD1** | Local App A uses remote App B fallback |

The important distinction is:

- **W1/S1/S2 active WAF pool:** multiple healthy independent WAFs can process the same service concurrently.
- **W2/W4 WAF HA cluster:** one device owns a traffic group; another device is the HA failover target.
- **W3:** combines tenant-preferred active WAFs with shared reserve capacity.

Detailed diagrams are in section 3 below and in [executive_recommendation.md](./executive_recommendation.md).

## 1.2 Timing reference — T1 to T9

The detailed timing definitions live in [analysis_variables_and_f5_assumptions.md](./analysis_variables_and_f5_assumptions.md#5-f5-monitoring-and-recovery-time-assumptions). The table below is the quick reference used throughout this summary.

| ID | Meaning | Planning value / interpretation | When to add it |
|---|---|---|---|
| **T1** | BIG-IP HA peer/device failover | approximately **3+ seconds peer-loss detection**, plus traffic-group/network convergence | LTM/WAF/GTM HA peer or traffic-group ownership change |
| **T2** | LTM pool-member / WAF-member health detection | commonly **up to ~16s** with 5s interval / 16s timeout defaults | failed independent WAF, backend or service member behind a stable LTM VIP |
| **T3** | BIG-IP DNS/GTM health observation | direct monitor timing is configuration-specific; common HTTP/HTTPS/TCP defaults can be around **30s interval / 120s timeout** | site GTM directly observes an endpoint/path failure |
| **T4** | GTM global-state + DNS/site-selection convergence | health observation -> GTM synchronization/global-state convergence where required -> answer change -> residual DNS TTL/cache -> retry/re-resolution; GTM A-record pool TTL default is **30s** | whenever recovery changes the returned site/VIP |
| **T5** | Warm/cold/manual recovery | **minutes or longer; no fixed product value** | operator action, passive-site startup, routing repair, config/policy rollback |
| **T6** | Application recovery | **application-specific** | retry, reconnect, re-auth, session/state restore, resubscribe, replay/reconciliation |
| **T7** | Failback | controlled restoration; F5 auto-failback delay is configurable and commonly modelled around **60s when enabled** | return to preferred device/site after recovery |
| **T8** | DNS cache vs existing-connection behavior | **behavior modifier, not a duration** | distinguishes new DNS lookup, cached old IP, existing TCP/WebSocket, and app connection-pool caching |
| **T9** | Platform/cloud firewall (CFW) recovery | **product/config specific; measure** | CFW HA member failure, full CFW-context failure or CFW false-green |

### How to read combined timings

Examples:

- **~16s + T6** = LTM detects/withdraws the failed member, then the application/client still has to recover.
- **T4 + T6** = after health is known, the GTM/global state and DNS answer converge, then the application/client reconnects/restores state. If the remote GTM does not directly observe the failure, T4 must include the measured GTM synchronization/learning delay.
- **T5 + T4 + T6** = manual/passive-site preparation first, then DNS/site convergence, then application recovery.
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
| **Not preferred / outside current target scope** | shared LTM + shared WAF service | requires LTM-owner redesign and has the largest common-mode/cross-tenant blast radius |

The 99.95% target is most credible when normal changes are effectively no-outage, common failures stay R0/R1, and whole-tier/dependency failures can use R2 recovery rather than forcing a site move.

# 2. Common stack

For a private-cloud web application, separate **DNS/control-plane resolution** from the application data path.

External DNS control path:

~~~text
External user/system
  -> external/customer DNS
  -> private leased line / VPN
  -> Site 1 or Site 2 edge-firewall HA path
  -> site GTM/DNS cluster inside the edge boundary
  -> DNS answer: selected application VIP
~~~

External application data path:

~~~text
External user/system
  -> private leased line / VPN
  -> edge firewall / selected external VIP
  -> LTM HA pair where present
  -> WAF tier
  -> platform/cloud firewall (CFW)
  -> ELB/service
  -> VM / Kubernetes / PaaS workload
  -> session/state/data
  -> App B / App C dependencies
~~~

Each site has **two HA edge-firewall pairs, two devices per pair (2 x 2)** and a site GTM/DNS cluster. The two GTM clusters synchronize the enterprise GTM/DNS view.

Internal users enter through a **separate enterprise-internal path**. Internal users, internal DNS and the internal LTM/service-VIP layer are outside the private cloud. Selected internal names can use the **same edge GTM service** as the external DNS path:

~~~text
Internal user/system
  -> internal enterprise DNS
  -> [optional delegation/conditional forward to edge GTM]
  -> internal service/LTM VIP
  -> internal firewall
  -> private-cloud CFW
  -> ELB/service
  -> application
~~~

The **internal firewall and CFW are separate failure domains**. A WAF outage may leave the internal path healthy; an internal-firewall outage may block internal users while the external path remains healthy; a CFW outage can affect both paths if they converge on the same CFW.

Application-to-application dependencies are a separate data path. Do not assume an App A -> B call traverses the internal-user firewall unless the real routing does so.

Non-web applications may bypass WAF but still depend on DNS, LTM, internal firewall where applicable, CFW, ELB, backend and application recovery.

# 3. WAF topology options

## W1 — independent active WAF pool behind LTM

~~~text
Firewall VIP
    |
LTM HA pair
    |
+----+----+----+
|    |    |    |
WAF1 WAF2 WAF3 ... WAFn
    |
   CFW
    |
   ELB/app
~~~

- WAFs are independent active pool members.
- LTM distributes new traffic across healthy WAFs.
- Two WAFs give **N-1**, but not local N-2.
- Three or more WAFs can tolerate two WAF failures only when remaining capacity is explicitly sized for N-2.
- Existing long-lived connections through a failed WAF normally reconnect.

**Strength:** horizontal scale, clear failure domains, rolling maintenance.  
**Weakness:** no transparent socket preservation across an independent WAF failure.

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
- Supported connection mirroring can improve the first failover for some long-lived connections.
- Adding a third DSC device adds another failover target, but does not turn one traffic group into a three-way active pool; WAF connection mirroring is still limited in multi-device sequential failover.

**Strength:** simple HA, best first-pair-failure connection continuity where mirroring is supported.  
**Weakness:** pair/cluster is a hard local boundary and does not horizontally share one traffic group.

## W3 — tenant-preferred WAFs plus shared reserve

~~~text
      Tenant LTM pair
             |
     +-------+-------+
     |               |
preferred WAF1/WAF2  shared reserve WAF capacity
(higher priority)    (lower priority contingency)
     \               /
      +------+------+
             |
            CFW
             |
          ELB/app
~~~

Baseline remains **two LTMs per tenant per site**.

- Normal traffic uses tenant-preferred active WAFs.
- Shared reserve sits in parallel as lower-priority contingency capacity activated when tenant-preferred capacity is lost or maintained.
- Can survive loss of both preferred WAFs if reserve capacity is available, policy-ready and routable.
- Reserve exhaustion or a bad shared policy can affect multiple tenants.

**Strength:** good maintenance/N-2-style recovery without buying a dedicated third WAF for every tenant.  
**Weakness:** shared reserve becomes a cross-tenant capacity and governance dependency.

## W4 — Site 1 cluster + extra WAF; Site 2 cluster only

~~~text
Site 1                                 Site 2
LTM pair                               LTM pair
   |                                      |
   +-------------------+            WAF HA cluster
   |                   |                  |
WAF HA cluster  extra independent WAF    CFW
   \                   /                  |
    +--------+--------+                ELB/app
             |
            CFW
             |
          ELB/app
~~~

- Site 1 can survive broader WAF failure than a simple two-node cluster.
- Site 2 has less local WAF headroom.
- Whole-site DR must prove the Site 2 WAF cluster can carry required production load.

**Strength:** strong primary-site local WAF resilience.  
**Weakness:** asymmetric recovery/maintenance capacity.

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

A topology only truly survives two WAF failures when **capacity after those two failures is sufficient**.

# 5. Cross-site versus no-cross-site capability

Cross-site capability should reduce **failure-domain escalation**. It should not be required for normal healthy operation.

| Local failure | No cross-site component/dependency routing | With cross-site capability | Typical difference |
|---|---|---|---|
| **One WAF fails** | Local pool/cluster recovers | Same | Cross-site not needed |
| **Both/all local WAFs fail; LTM+CFW+app healthy** | Restore WAF locally or move service/site | **X2A:** local LTM can use remote WAF and route back to healthy local CFW/app | Can change site-failover event into **~16s-class + T6** local-ingress recovery |
| **Local LTM+WAF tier fails; CFW/app healthy** | Full app/site move or outage | **X2B:** Site 2 front end can route back to Site 1 CFW/app | Avoids moving a healthy application; still needs GTM/DNS convergence |
| **Local CFW fails; local app healthy** | Restore CFW or move app/site | Remote WAF alone does **not** help; need alternate CFW/site application path | Cross-site WAF is not a substitute for CFW resilience |
| **B1 fails; A1 healthy** | A may fail/cascade/site-move | **XD1:** A stays local and uses B2 | Prevents dependency failure becoming application/site failure |
| **Whole site fails** | Site 2 full recovery | Site 2 full recovery | Route-back cannot recover a lost site |

## Indicative recovery classes

- local BIG-IP HA peer: **~3s+ + connection recovery**;
- local LTM WAF-member withdrawal: **up to ~16s + T6** with common monitor defaults;
- X2A remote WAF with same client VIP: **~16s-class + T6**, if remote WAF and local CFW/app path are ready;
- GTM/site move using fast local health: illustrative **~46s + T6** including up to 30s residual DNS TTL;
- GTM/site move with default-style direct GTM monitoring: **up to ~150s + T6**;
- manual passive-site startup: **T5 + site recovery + T6**;
- CFW false-green or application false-green: potentially **unbounded** until correct readiness detects it.

# 6. Application-type comparison

| Application type | Single member failure | WAF/LTM/CFW path change | Site/dependency failover | Main acceptance requirement |
|---|---|---|---|---|
| **Stateless web** | Usually one failed request/retry | New request can use healthy path | Re-resolve/retry to ready site | safe retry, external/shared state, idempotency |
| **Stateful web** | May lose session/transaction affinity | Session may need reconstruction or re-login | State/data must exist at alternate path/site | portable/replicated state and transaction reconciliation |
| **WebSocket / long-lived** | Socket on failed path normally breaks unless supported mirroring preserves it | reconnect + re-auth + resubscribe | re-resolve + reconnect + replay/snapshot | reconnect/backoff, durable cursor/state, replay, idempotency |
| **Non-web / L4** | Protocol-specific connection loss | reconnect/retry; WAF may be irrelevant | protocol/DNS/service failover | documented protocol retry, re-resolution, transaction replay |

A W2 cluster can look better than W1 for the **first WAF failure** of a WebSocket because mirroring may preserve supported connections.

For stateless HTTP, W1 may be operationally simpler: a failed WAF is withdrawn and the next request uses another active WAF.

For stateful and WebSocket applications, the application design can dominate the RTO after any WAF/LTM/CFW/backend/site event.

## GTM health-check caveat

A site can remain **false green** if GTM health stops at a reachable WAF/LTM listener while the CFW, ELB or application behind it is broken.

For each protected service, declare whether GTM/global availability is based on:

- TCP/port availability;
- HTTP/L7 transaction health through WAF/LTM;
- an authoritative application-readiness signal.

Where application-layer checks are used, the application team must own the health-check contract (URI/host, method, expected response, authentication and dependency semantics).

Also declare whether each site GTM cluster probes only local services or can directly observe the other site. **GTM synchronization does not by itself prove cross-site probing.** If the remote cluster learns failure indirectly, add the measured synchronization/learning delay before residual DNS TTL.

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
| **Internal firewall member/path** | external path can remain healthy | internal users can lose private-cloud access; App A->B impact depends on actual dependency routing | internal-firewall HA / alternate internal path | alternate site/internal endpoint if designed | internal-user-only outage can be mistaken for app outage |
| **One CFW** | target seconds-scale HA | internal callers through the internal firewall converge on the same CFW | CFW peer | normally not needed | state/NAT loss can reset many sessions |
| **Whole CFW** | app unreachable despite healthy WAF/ELB | internal users and dependencies behind the same CFW also fail | alternate CFW | site/app path | multi-application platform blast radius |
| **ELB member/backend** | brief retry | same for dependent callers | healthy backend member | normally not needed | low if stateless/capacity sufficient |
| **Whole ELB/service** | app unavailable | dependent apps fail | redundant ELB/service | site/app recovery | dependency cascade |
| **App readiness false-green** | errors/hangs | dependencies error/hang | app readiness must withdraw service | site if alternate app ready | potentially unbounded |
| **State/session/data service** | sessions/workflows fail | multiple apps can fail | state/data HA | alternate state/site | high common-mode |
| **App B dependency** | App A features fail | A/C/D may all fail | stable service VIP/local alternate | XD1 B2 | major cascade if timeouts/retries poor |
| **Whole site** | full site loss | internal/app dependencies also move | none | Site 2 full recovery | DR capacity/readiness dominates |

# 8. Four-tenant cost and sharing model

## 8.1 Cost metric

This section uses **device-unit count**, not vendor price.

- one physical/virtual LTM appliance = 1 LTM device-unit;
- one physical/virtual WAF appliance = 1 WAF device-unit;
- counts cover **two sites**;
- GTM, edge firewall, internal firewall, CFW, ELB, platform and application cost are excluded because their sharing/dedication model may differ;
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

**Benefit:** strongest tenant isolation and predictable capacity.  
**Cost:** capacity/spares are stranded inside each tenant when unused.

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

This is more devices than the simple 32-unit two-WAF dedicated baseline, but fewer than the 40 units required to give every tenant a dedicated third WAF.

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

where **P = WAFs per shared site pool**.

Illustrative **P=4**:

~~~text
16 LTM + 8 WAF = 24 device-units
~~~

If the four-WAF pool is sized so two surviving WAFs can carry required aggregate load, it can tolerate two WAF-node failures without losing the WAF service.

**Benefits:** lower WAF count, shared aggregate spare capacity, horizontal scale.  
**Risks:** cross-tenant WAF blast radius, noisy-neighbour capacity, shared policy/configuration risk.

### S2 — shared LTM pair + shared WAF pool

Across two sites:

~~~text
4 LTM + 2P WAF
~~~

Illustrative **P=4**:

~~~text
4 LTM + 8 WAF = 12 device-units
~~~

This has a much larger shared failure/change domain because both ingress LTM and WAF capacity are shared.

## 8.5 Shared WAF HA cluster

With one shared LTM pair/site and one two-device WAF HA cluster/site:

~~~text
4 LTM + 4 WAF = 8 device-units across two sites
~~~

With four tenant LTM pairs feeding the shared WAF cluster:

~~~text
16 LTM + 4 WAF = 20 device-units
~~~

This is device-efficient, but the cluster is a common multi-tenant failure domain and only tolerates one WAF member failure before the shared WAF service is lost.

## 8.6 Four-tenant comparison

| Tenancy / topology pattern | LTM units | WAF units | Total | 1 WAF failure | 2 WAF failures | Tenant isolation | Cross-tenant blast radius |
|---|---:|---:|---:|---|---|---|---|
| **4x dedicated W1, 2 WAF/tenant/site** | 16 | 16 | **32** | Yes | No local WAF service for affected tenant | **High** | Low |
| **4x dedicated W1, 3 WAF/tenant/site** | 16 | 24 | **40** | Yes | Yes if N-2 capacity | **High** | Low |
| **4x dedicated W2a HA cluster, no ingress LTM** | 0 | 16 | **16** | Yes | Cluster lost for affected tenant | **High** | Low; WAF owns/receives ingress directly |
| **4x dedicated W2b HA cluster + LTM** | 16 | 16 | **32** | Yes | Cluster lost for affected tenant | **High** | Low |
| **4x dedicated W4a asymmetric** | 16 | 20 | **36** | Yes | Site 1 can use extra WAF after cluster loss; Site 2 cannot | **High** | Low |
| **W3: 2 preferred/tenant + 2 shared reserve/site** | 16 | 20 | **36** | Yes | Usually yes for one tenant if reserve free | Medium-High | Medium |
| **S1 tenant LTMs + shared active pool, P=4/site** | 16 | 8 | **24** | Yes | Yes if 2 remaining WAFs sized for aggregate load | LTM high / WAF shared | **High at WAF tier** |
| **S2 shared LTM + shared active pool, P=4/site** | 4 | 8 | **12** | Yes | Yes if capacity | Low | **Very high** |
| **Shared LTM + shared 2-node WAF HA cluster** | 4 | 4 | **8** | Yes | No; whole shared WAF service lost | Low | **Very high** |

These totals are planning examples, not purchase quotes or recommendations by themselves.

### W2/W4 dedicated count notes

- **W2a** has no ingress LTM at the WAF tier, so the F5 LTM count is zero in this narrow LTM/WAF device model. Edge firewall/VIP and other infrastructure still exist.
- **W2b** adds the normal two-LTM-per-site-per-tenant baseline.
- **W4a** uses 3 WAFs in Site 1 and 2 WAFs in Site 2 per tenant: 5 WAFs x 4 tenants = 20 WAF units across the two sites, plus 16 LTM units = 36.
- **W4b** removes the ingress LTM at the WAF tier and would therefore be 20 WAF units in this narrow device model, but requires an explicit non-LTM steering mechanism to the Site 1 extra WAF.

# 9. Resilience versus cost interpretation

## Lowest device count

A shared LTM + shared WAF HA cluster has the fewest devices, but concentrates tenant ingress, WAF policy, capacity, maintenance and bad-change risk into the fewest shared components.

Low device count is **not** the same as low availability risk.

## Best tenant isolation

Dedicated LTM/WAF per tenant provides the smallest cross-tenant blast radius and easiest capacity attribution, at the cost of duplicated standby/spare capacity.

## Best active-capacity efficiency

A **shared independent active WAF pool** can give better aggregate capacity efficiency than a shared HA cluster because all pool members can process traffic.

For four tenants, S1 is an important candidate:

> retain tenant-specific LTM pairs and routing boundaries, but share a sufficiently large active WAF pool.

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
B1 fails
  -> A1/C1/D1 timeout/retry
  -> readiness fails
  -> several applications move site
  -> DNS/reconnect/login surge
  -> B2/DB/identity surge
~~~

XD1 local-preferred/remote-fallback dependency routing keeps A/C/D local when B2 is safe and reachable.

# 11. Recommended comparison set

For four tenants, compare at least:

1. **Fully dedicated:** 2 LTMs/tenant/site + 2 or 3 independent WAFs/tenant/site.
2. **Tenant LTM + shared active WAF pool:** retains tenant ingress boundary while sharing horizontally useful WAF capacity.
3. **W3 dedicated preferred + shared reserve:** dedicated normal-state capacity plus shared failure/maintenance reserve.
4. **Shared LTM + shared WAF service:** lowest device count, largest common-mode failure domain.

W2 clustered WAF can be substituted in dedicated or shared models where first-failure connection mirroring is more important than horizontal WAF scaling.

# 12. Architecture recommendation

For business-critical four-tenant environments, avoid choosing solely on appliance count.

Use this decision order:

1. define maximum acceptable **cross-tenant blast radius**;
2. define whether each tenant needs local **N-1 or N-2 WAF capacity**;
3. decide whether a healthy local application may use **remote WAF/dependency capacity**;
4. validate stateless/stateful/WebSocket/non-web recovery requirements;
5. size Site 2 for the **largest credible simultaneous failover**, especially for shared WAF/LTM capacity;
6. only then optimize device count.

The most balanced shared option to evaluate is often:

~~~text
tenant-specific LTM HA pair
        |
shared independent active WAF pool
        |
tenant-specific / isolated CFW + ELB/app paths
~~~

because it preserves tenant ingress boundaries while sharing horizontally useful WAF capacity.

The dedicated W1 model remains the clearest choice when tenant isolation and predictable blast radius are more important than appliance efficiency.

W3 remains attractive when the enterprise specifically wants **dedicated normal-state WAFs plus shared failure/maintenance reserve**.

Any shared topology should be downgraded if a single policy/configuration push, shared CFW, shared LTM, or reserve-capacity exhaustion can take multiple tenants down simultaneously.
