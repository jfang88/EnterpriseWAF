# Common Failure Matrix — Enterprise WAF Topology Options

**Role:** Technical component-level appendix for Failure/Recovery Lens 1  
**Primary service/user outcome:** [end_to_end_service_impact_analysis.md](./end_to_end_service_impact_analysis.md)  
**Separate Lens 2:** [maintainability_change_management_analysis.md](./maintainability_change_management_analysis.md)

> This matrix explains how infrastructure components detect and recover from failures. It is **not** the primary service story. Use the end-to-end service impact analysis for external-user, external-system/API, internal-user, App A/B/C, outage-time and recoverability conclusions.

**Inputs**

- Stable baseline: [enterprise_scenario_invariants.md](./enterprise_scenario_invariants.md)
- Changeable topology/F5 assumptions: [analysis_variables_and_f5_assumptions.md](./analysis_variables_and_f5_assumptions.md)

**Purpose**

Apply the same failure scenarios to each candidate WAF topology without changing the enterprise baseline.

# 1. Topology shorthand

| ID | Topology |
|---|---|
| **W1** | LTM-fronted scalable independent WAF pool (2..N) |
| **W2** | WAF HA cluster; W2a without ingress LTM, W2b with LTM |
| **W3** | Tenant-preferred WAFs plus shared enterprise reserve WAFs |
| **W4** | Asymmetric: Site 1 WAF HA cluster + extra active/spare WAF; Site 2 WAF HA cluster only |

**Common site rule:** W1-W3 normally use the same logical WAF topology in both sites. W4 is deliberately asymmetric: Site 1 has a WAF HA cluster plus an extra active/spare WAF, while Site 2 has only the WAF HA cluster. GTM/LTM roles remain similar per site.

Cross-site dataplane routing is evaluated separately as:

- **X1** local-only
- **X2A** surviving local LTM borrows a remote WAF
- **X2B** remote front-end routes back to the healthy primary-site application
- **X2C** conventional full application/site failover
- **XD1** App A uses remote App B as dependency fallback

# 2. Timing shorthand

These are modelling categories, not guaranteed SLAs.

| Timing ID | Meaning |
|---|---|
| **T1 — HA peer failover** | roughly 3+ seconds peer-loss detection under common/default-style BIG-IP HA behavior, plus traffic-group/network convergence; validate in production design |
| **T2 — local pool-member health** | often up to the configured LTM monitor timeout; many monitor types default around 5s interval / 16s timeout |
| **T3 — direct GTM monitor** | BIG-IP DNS direct HTTP/HTTPS/TCP monitoring commonly defaults around 30s interval / 120s timeout unless tuned |
| **T4 — DNS/site convergence** | health detection + GTM decision + residual DNS TTL/cache + client re-resolution/retry + alternate-site readiness. F5 GTM A-record pool TTL default is 30s; direct GTM monitor defaults can be 30s/120s |
| **T5 — warm/cold/manual** | operator/startup/configuration dependent; may be minutes or longer |
| **T6 — application recovery** | application-specific retry/reconnect/session/state/replay behavior; can dominate RTO even after infrastructure is healthy |

## 2.1 Validated numeric planning windows

Use these explicit planning calculations where applicable:

| Recovery pattern | Planning timing |
|---|---|
| BIG-IP HA peer/member takeover | **~3s+** peer-loss detection plus traffic-group/network convergence and T6 for affected flows |
| LTM withdraws one failed pool/WAF member | **up to ~16s + T6** with common 5s/16s monitor defaults; no DNS term if VIP is unchanged |
| X2A remote WAF behind surviving local LTM | **~16s-class + T6**, assuming remote member already healthy/policy-ready; no DNS term |
| GTM site move using fast LTM-health-informed state | illustrative **~16s health + up to 30s residual TTL = ~46s + T6**, plus unmeasured iQuery/propagation |
| GTM site move using default direct GTM monitor | **up to ~120s health + up to 30s residual TTL = ~150s + T6** |
| Manual passive-site startup | **T5 + ~46–150s + T6** depending health model; T5 may dominate |
| App B local-preferred -> B2 through stable LTM service VIP | **~16s-class + App A retry T6** |
| App B1 -> B2 through DNS/GTM | **~46–150s + T6**, plus application-specific DNS/connection-pool caching |

Important:

- a 30s DNS TTL does not migrate an existing TCP/WebSocket connection;
- clients with cached old answers can continue to select the failed VIP until the remaining TTL expires;
- applications can retain addresses/connections beyond authoritative TTL;
- after LTM marks a member down, new traffic uses healthy members, but established connections on the failed member can still reset/hang until client/application recovery.

# 3. Control-plane, namespace and ingress failures

External and internal DNS namespaces are separate control-plane dependencies. The same failure can have very different user/application outcomes depending on which namespace is affected.

| ID | Failure | Detection / recovery path | Indicative timing | W1 | W2 | W3 | W4 |
|---|---|---|---|---|---|---|---|
| F00A | External namespace/GTM resolution fails | Remaining external DNS/GTM path must answer; cached/existing sessions may continue | T3/T4 + cache | No direct WAF-topology difference | Same | Same | Same |
| F00B | Internal enterprise DNS fails | Restore internal resolver service; GTM may be healthy but unreachable via failed resolver path | resolver recovery + T6 | No direct WAF-topology difference | Same | Same | Same |
| F00C | Internal DNS delegation/conditional forward to GTM fails | Restore forwarding/delegation; directly resolved internal names may remain healthy | DNS recovery + T6 | No direct WAF-topology difference | Same | Same | Same |
| F00D | Internal GTM returns unreachable/wrong-site endpoint | Correct health/reachability selection; clients/apps must re-resolve/reconnect | T3/T4/T6 | No direct WAF-topology difference | Same | Same | Same |



| ID | Failure | Detection / recovery path | Indicative timing | W1 | W2 | W3 | W4 |
|---|---|---|---|---|---|---|---|
| F01 | One GTM/DNS node fails | Remaining GTM/DNS peer(s) continue answering; DNS service redundancy must be independent of app WAF topology | T1/T4 depending GTM HA design; existing cached answers unaffected | No WAF impact | No WAF impact | No WAF impact | No WAF impact |
| F02 | All GTM/DNS service in one site fails | Other GTM site/listener must answer queries; customer/corporate DNS must be able to reach it | DNS resolver retry + cache behavior; usually T4 | Existing app sessions continue; new DNS resolution depends on remaining GTM | Same | Same | Same |
| F03 | GTM IP/port monitor is green but application is broken | No recovery until app-level signal or operator detects failure; GTM may keep advertising bad site | Potentially unbounded from GTM perspective | Critical false-green risk | Critical false-green risk | Critical false-green risk | Critical false-green risk |
| F04 | GTM full application-readiness monitor marks local app down | GTM stops returning unhealthy site and selects next healthy eligible site/pool | app monitor detection + T4 | Site switch if alternate ready | Same | Same | Same |
| F05 | One leased line fails | Only user population routed through that line loses reachability unless customer/network reroutes | carrier/routing convergence; not a WAF recovery | App remains healthy for other users | Same | Same | Same |
| F06 | One edge-firewall member fails | Firewall HA pair takes over VIP/state according to firewall design | firewall HA timing, outside F5 WAF/LTM timing | Downstream F5 stack unchanged | Same | Same | Same |
| F07 | Entire edge-firewall pair/path fails | Remaining leased-line/firewall path or alternate site must be reachable; GTM cannot solve missing network reachability by itself | routing/firewall convergence or T4 if site selection changes | Potential partial/full external outage | Same | Same | Same |

# 4. LTM failures

| ID | Failure | Recovery path | Indicative timing | W1 | W2 | W3 | W4 |
|---|---|---|---|---|---|---|---|
| F08 | One LTM node in HA pair fails | BIG-IP DSC traffic group fails to peer; use redundant HA communication | T1; validate actual ARP/MAC/network convergence | **High resilience**; WAF pool unchanged | W2a N/A; W2b cluster remains behind surviving LTM | **High**; preferred/reserve pools unchanged | **High** |
| F09 | Entire local LTM HA pair unavailable | No local traffic steering through that LTM tier; use alternate site or a separately reachable service path | T4 if GTM/site switch; otherwise outage | Local WAF pool unreachable through normal design | W2a may avoid this failure domain; W2b affected | Preferred + reserve WAFs are useless if all require failed tenant LTM | W4a: cluster/extra WAF unavailable through failed Site 1 LTM; site switch may use Site 2 LTM+cluster. W4b has no ingress LTM failure domain at WAF tier |
| F10 | LTM health monitor falsely marks healthy WAF down | Capacity reduced; may activate lower-priority/reserve members | T2 | Remaining WAF pool handles load | W2b can withdraw whole cluster VIP/member if monitor design poor; W2a N/A | May unnecessarily consume reserve | W4a may activate the extra Site 1 WAF; W4b depends on its non-LTM steering mechanism |

**Critical observation:** An LTM pair is itself a tenant-level service failure domain. W3 shared spare WAFs do not protect against total tenant-LTM loss unless there is another traffic-steering path.

# 5. WAF failures

| ID | Failure | Recovery path | Indicative timing | W1 | W2 | W3 | W4 |
|---|---|---|---|---|---|---|---|
| F11 | One WAF node/member fails | LTM withdraws member or clustered peer takes over | W1/W3: T2; W2/W4 cluster: T1/T2 depending failure mode | **Very good** if remaining capacity sufficient | **Very good** for first HA-pair failure; mirroring may preserve supported connections | **Very good**; preferred peer remains, reserve available | **Very good in Site 1**; cluster peer and extra WAF provide layered recovery. **Site 2** has cluster peer only |
| F12 | Two WAF nodes fail / preferred tenant WAF pair lost | Use remaining independent members, reserve, local spare or site recovery | T2; T5 if spare not hot; T4 if site switch | Good only if pool has 3+ and N-2 capacity; 2-node pool = complete local WAF loss | HA pair lost = complete local WAF service loss | **Strong** if reserve WAFs are hot, configured and have capacity | **Strong in Site 1** if extra WAF is hot/configured; after Site 1 failure, Site 2 has only its WAF cluster |
| F13 | Entire local WAF service unavailable | Local alternate WAF path, cross-site WAF if X2, or GTM site failover | T2/T4/T5 depending design | X1: site failover; X2: remote WAF possible | Site failover unless separate WAF service exists | Reserve may recover locally if independent from failure cause | Site 1 extra WAF may recover locally; otherwise use Site 2 WAF cluster |
| F14 | Bad WAF policy/configuration pushed to all WAFs | Roll back policy; use independently controlled unaffected pool/site only if bad config not replicated there | operator/change rollback; often T5 | **Common-mode critical risk** | **Common-mode critical risk** | Reserve is not useful if it receives same bad policy | Spare/site not useful if same bad policy replicated everywhere |
| F15 | WAF CPU/throughput exhaustion | LTM sends to remaining/added members; reserve or site capacity may absorb load | T2 if monitor detects; scale/ops dependent | **Best horizontal scale** | Cluster capacity may be fixed; scaling less flexible | Good if reserve capacity available | Site 1 extra WAF gives bounded extra capacity; Site 2 does not have the same headroom |
| F16 | Shared reserve WAFs exhausted by another tenant | No reserve available; tenant falls back to preferred survivors/site recovery | capacity event; T4/T5 if site move | N/A | N/A | **Critical W3 shared-capacity risk** | N/A unless spare shared |

# 6. Platform firewall, backend and application-platform failures

For private-cloud applications, model this path explicitly:

```text
WAF/LTM
  -> platform/cloud firewall (CFW)
  -> application ELB/service
  -> VM / Kubernetes / PaaS workload
```

CFW and ELB are separate failure domains. A healthy WAF and healthy ELB do not make the application reachable when the CFW path, NAT/session state or policy is unavailable.

| ID | Failure | Recovery path | Timing | W1 | W2 | W3 | W4 |
|---|---|---|---|---|---|---|---|
| F17 | One application VM/pod/member fails | ELB/application LB selects another member; WAF topology should not change | backend monitor timeout + T6 | No topology change | No topology change | No topology change | No topology change |
| F18 | One CFW member/node fails but CFW HA remains healthy | CFW peer/state/routing takeover; retain same ELB/app path | **CFW-product-specific; measure HA/route convergence + T6** | No WAF topology change if CFW HA succeeds | Same | Same | Same |
| F18A | Entire local CFW context/service/path fails while ELB/app remain healthy | Restore CFW, use approved alternate CFW/cross-site path, or fail application/site | CFW detection/recovery; otherwise T4/T5/T6 | Healthy app can become unreachable despite healthy WAF/LTM | Same | Same | Same |
| F18B | Local application ELB/service fails behind healthy CFW | Select redundant ELB/service or alternate ready site | backend detection + T4/T6 | Site/app failover unless alternate backend path exists | Same | Same | Same |
| F19 | Application is network-up but business-not-ready | Requires app-level readiness monitor; IP/port monitoring creates false green | potentially unbounded if only L4 monitor | All options equally vulnerable | Same | Same | Same |
| F20 | Shared session/state store fails | Application-level recovery, alternate state store/site; WAF/LTM failover alone does not help | T6; data-platform RTO | Infrastructure may stay green while app fails | Same | Same | Same |
| F21 | App B local service fails while App A remains healthy | A should use healthy B2/service VIP if supported; otherwise A may fail/cascade | dependency monitor + T6; X2 if remote B used | WAF topology irrelevant to east-west dependency unless path uses it | Same | Same | Same |

# 7. Cross-site and dependency-routing failures

| ID | Failure | Recovery path | Timing | W1 | W2 | W3 | W4 |
|---|---|---|---|---|---|---|---|
| XS01 | One local WAF fails while other local WAF capacity remains | Recover locally; do not invoke cross-site merely because it exists | T2 / cluster HA | Strong local recovery | Strong cluster recovery | Strong local preferred recovery | Strong cluster recovery |
| XS02 | All local WAFs fail; local LTM and primary app healthy | **X2A:** local LTM activates remote WAF and routes back to primary app | T2 if remote WAF already monitored/configured | **High benefit** | Medium; only after whole cluster loss | **Very high benefit** if reserve/remote WAF available | High after local cluster/spare exhausted |
| XS03 | Local LTM + WAF tier fail; primary app healthy | **X2B:** GTM moves ingress to Site 2 LTM/WAF, which routes back to Site 1 app | T4 + new connection; may still beat manual app DR | High if designed | High for W2b; W2a depends on front-end path | High | High |
| XS04 | Primary app fails but remote WAF route-back is available | Do not use route-back to failed app; use X2C application/site recovery | T4 + T6 | No route-back benefit | Same | Same | Same |
| XS05 | Inter-site link fails while all local services healthy | Keep local path up; withdraw only remote contingency | route detection; no DNS/site change | No normal impact | Same | Shared remote reserve unavailable only | Site 1 cluster/extra WAF stays healthy; Site 2 cluster remains independent |
| XS06 | Inter-site link fails while X2A/X2B is active | Contingency path fails; restore local tier or move full application/site | route detection + T2/T4/T6 | Existing remote sessions fail | Same | Remote reserve traffic fails | Remote contingency collapses; W4 Site 2 still has only the base WAF cluster |
| XS07 | Cross-site path is asymmetric through stateful firewall/NAT | Correct routing/SNAT before using path; endpoint health alone is insufficient | potentially T5/network repair | Critical X2 risk | Critical X2 risk | Critical if reserve remote | Critical for remote tier |
| XS08 | Remote WAF is healthy but lacks correct tenant/app policy | Treat remote WAF as unavailable; do not activate | config/validation dependent | Critical configuration gate | Same | **Major W3 reserve risk** | Extra Site 1 WAF / Site 2 cluster policy-readiness gate |
| XS09 | Remote WAF capacity is exhausted | Keep/restore local service or fail application/site | capacity dependent | X2 unavailable | Same | **Major shared-reserve risk** | Site 2 cluster capacity risk; no equivalent extra WAF exists there |
| XS10 | Bad WAF policy is synchronized to local and remote WAFs | Roll back policy; topology/routing cannot solve a common-mode logical failure | T5/operator/change rollback | Critical | Critical | Critical | Critical |

## 7.1 Application A -> Application B dependency recovery

| ID | Dependency failure | Without remote dependency routing | With XD1 local-preferred / remote-fallback | Application-code requirement |
|---|---|---|---|---|
| DEP01 | B1 fails; B2 healthy | A1 may fail or force site move | A1 stays in Site 1 and uses B2 | bounded timeout + retry + connection refresh |
| DEP02 | A1->B1 network path fails but B1 itself is healthy | A1 can fail despite healthy B | LTM/service VIP can select B2 if remote path healthy | retry must be safe/idempotent |
| DEP03 | B1 slow/hung rather than hard-down | Threads can hang and cascade | Health monitor/circuit breaker can remove B1 and use B2 | connect/read timeout + circuit breaker |
| DEP04 | B1 fails and many apps depend on it | A/C/D can all fail site simultaneously | Each dependent app can remain local and use B2 | retry budgets/backoff to avoid B2 storm |
| DEP05 | B2 reachable but data/state not safe for remote use | Site/app failover required | **Do not use XD1** | state consistency is a hard prerequisite |
| DEP06 | Inter-site link fails while A1 is using B2 | Dependency fails again | revert to B1 if recovered; otherwise degrade/fail A safely | reconnection, retry budget, graceful degradation |
| DEP07 | A uses persistent connection to B1 | DNS/LTM update does not move existing connection automatically | connection must fail/refresh and reconnect to B2 | connection-pool refresh/reconnect |
| DEP08 | A request is non-idempotent | retry may duplicate transaction | routing alone is insufficient | idempotency key or reconciliation required |

### Dependency-routing conclusion

XD1 can provide **very high resilience benefit** because it prevents a single dependency failure from becoming a multi-application or site failover.

However, this benefit is valid only when the application protocol supports bounded failure detection and safe retry/reconnect.

# 8. Full-site failures

| ID | Failure | Recovery path | Timing | W1 | W2 | W3 | W4 |
|---|---|---|---|---|---|---|---|
| F25 | Entire Site 1 fails and Site 2 app is ready | GTM returns Site 2 healthy VIP; client re-resolves/reconnects | T4 + T6 | Good if Site 2 equivalent exists/capacity | Good if Site 2 cluster exists | Good if Site 2 capacity exists | **Strong if Site 2 cluster is sized for full DR load; note Site 2 lacks Site 1's extra WAF headroom** |
| F26 | Entire Site 1 fails but passive Site 2 application is stopped | Start app, validate dependencies/readiness, then GTM may advertise it | **T5 dominates** + T4/T6 | Infrastructure HA cannot meet short RTO | Same | Same | Same |
| F27 | Site 1 remains partially reachable but critical app dependency/data is unavailable | App-level health must withdraw site only for affected application; avoid global site-down decision | app readiness + T4/T6 | Per-app GTM health required | Same | Same | Same |

# 9. Long-lived/socket behavior

Infrastructure recovery and application recovery must be separated.

| Failure | W1 | W2 | W3 | W4 |
|---|---|---|---|---|
| One WAF fails | Existing sockets on failed WAF normally reconnect to another WAF | Two-device mirroring may preserve some supported connections, but F5 AWAF has mirroring limits | Reconnect to preferred/reserve WAF | Cluster peer may preserve supported connection; move to the extra Site 1 WAF should assume reconnect |
| LTM HA peer fails | LTM connection mirroring can help if configured/supported; app should still tolerate reconnect | Same for W2b; W2a N/A | Same | Same |
| WAF cluster fails completely | Reconnect via new WAF/site | Mirroring cannot preserve connection when whole pair is gone | Reconnect via reserve/site | Move to extra Site 1 WAF or Site 2 cluster; **assume reconnect** |
| Site failover | DNS change does not move existing socket; client must reconnect/re-resolve | Same | Same | Same |

**F5 limitation to treat as architecture-significant:** Advanced WAF/ASM connection mirroring is documented as two-device mirroring; a third-device failover and failback reset the connection. Therefore W4 and larger pool topologies must not promise transparent multi-hop socket preservation.

# 10. Non-web applications bypassing WAF

For approved non-web traffic:

```text
Client/system
 -> firewall
 -> LTM/ELB/service VIP
 -> application
```

Consequences:

- WAF node/tier failure may have **no direct effect**.
- LTM, firewall, DNS, route, ELB and backend failures still matter.
- Recovery behavior depends on the protocol/client.
- Long-lived TCP/SFTP/middleware connections may benefit from LTM connection mirroring where supported, but client retry/reconnect should still be implemented.
- Do not use a WAF outage as a reason to declare a non-web application down when its approved path bypasses WAF.

# 11. Application resilience requirements and compliance impact

Infrastructure resilience cannot compensate for missing application recovery behavior.

## 11.1 Stateless web applications

**Required/expected**

- requests can be retried safely;
- state is absent or external/shared;
- idempotency is used for retried operations where duplicate submission is possible;
- readiness endpoint reflects whether the app can accept traffic;
- short client/server timeouts prevent hanging on failed paths.

**If non-compliant**

If "stateless" applications store critical session/workflow state only in process memory:

- WAF/ELB/backend failover can log users out or lose workflows;
- the effective service RTO becomes session/application recovery rather than F5 failover time;
- topology ratings should be downgraded from highly recoverable to stateful behavior.

## 11.2 Stateful web applications

**Required/expected**

- explicit session/state location documented;
- state externalized/replicated or recoverable;
- persistence/affinity used only where necessary;
- session re-authentication/reconstruction supported;
- transactions are idempotent or safely reconciled after retry;
- alternate site has compatible data/state before GTM advertises it.

**If non-compliant**

- infrastructure may fail over in seconds while users remain broken;
- sessions/workflows may be lost;
- automated site failover may be unsafe;
- RTO may become operator/manual recovery;
- application may need to be marked **not DR-compliant** even though the F5 layers are HA.

## 11.3 Socket/WebSocket/long-lived applications

**Required/expected application logic**

1. detect disconnect;
2. reconnect automatically;
3. exponential backoff with jitter;
4. re-resolve endpoint when appropriate;
5. re-authenticate or perform fast re-authentication;
6. re-establish subscriptions;
7. maintain sequence/offset/checkpoint information;
8. detect gaps;
9. replay missed messages or fetch a fresh snapshot;
10. make commands/retries idempotent;
11. keep durable state outside one socket process/VM/pod.

**If non-compliant**

- any WAF/LTM/backend/site failure can become a user-visible outage until manual restart;
- messages/events can be lost silently;
- WAF connection mirroring may mask only a subset of first-device failures;
- W4/multi-node hardware resilience provides little end-to-end benefit if clients cannot reconnect.

**Compliance conclusion:** socket applications without reconnect + state reconciliation should be explicitly classified as **infrastructure-HA only, not end-to-end resilient**.

## 11.4 Application A -> Application B dependencies

**Required/expected**

- bounded connection/read timeouts;
- retries with backoff/jitter and retry budgets;
- circuit breaker/bulkhead behavior where appropriate;
- service discovery or stable service VIP;
- health-aware local/remote selection;
- idempotent requests for retries;
- dependency degradation/fallback where business-safe;
- avoid synchronous cascading retries from many applications.

**If non-compliant**

A B1 failure can cause A1, C1, D1 to fail simultaneously and potentially trigger unnecessary site failover/capacity surge.

This is a major cascading-failure risk independent of WAF topology.

## 11.5 Non-web protocols

**Required/expected**

- client reconnect/retry semantics documented;
- safe transaction replay behavior;
- DNS re-resolution or alternate endpoint behavior;
- persistence/affinity requirements documented;
- protocol-specific state recovery;
- no assumption that a failed TCP connection will transparently migrate.

**If non-compliant**

LTM/firewall/site failover may restore infrastructure while clients remain disconnected until manual intervention.

# 12. GTM health-check comparison

| Model | Strength | Weakness | Recommended use |
|---|---|---|---|
| IP/port only | Simple and cheap | Can advertise a broken application | Only where port-up genuinely means service-ready |
| Full app readiness | Best application correctness | Must avoid overly deep/fragile checks | Preferred for business-critical web apps |
| LTM/iQuery health + app readiness | Reuses local LTM visibility and gives GTM F5-native status | Depends on iQuery/monitor design | Recommended F5-to-F5 baseline |
| Local + cross-site distributed probing | Detects path-specific failures and provides multiple viewpoints | If configured with "all probes required", inter-site failure can falsely withdraw healthy local service | Use as corroborating/availability-requirement signal, not sole local-health gate |

## Recommended GTM model

For this environment:

1. LTM performs **local full-service health** for the WAF/application path where practical.
2. GTM integrates with LTM over iQuery/BIG-IP monitor for F5-native virtual-server state.
3. Business-critical services also have an application-readiness signal.
4. Cross-site probers validate remote reachability/path health.
5. Availability requirements should tolerate loss of the cross-site probe when local service is healthy.
6. Active/passive apps use health-gated **Global Availability**.
7. Active/active/locality apps may use **Topology** based on LDNS/network source mapping.
8. Never prefer a site merely because the DNS query happened to land on that site's GTM.

# 13. Resilience summary by topology

Ratings assume correct health monitoring, adequate capacity, alternate-site application readiness and compliant applications.

| Topology | Single WAF failure | Dual/local WAF failure | Site failure | Horizontal scale | Long-lived continuity | Tenant isolation | Operational complexity | Overall |
|---|---|---|---|---|---|---|---|---|
| **W1 scalable pool in each site** | **High** | **Medium-High** with 3+ / N-2 capacity; a 2-node pool loses the local WAF service after both fail | **High** when Site 2 application is ready and sized | **High** | Medium; reconnect expected for failed independent WAF | High if tenant-dedicated | Medium | **Strong default: simple scale-out + symmetric site design** |
| **W2 HA cluster in each site** | **High** | Low locally once the whole pair is lost; then use cross-site/site recovery | **High** when Site 2 application is ready | Low-Medium | **Best first-failure continuity** where supported mirroring applies; limited beyond pair | High | Low-Medium | **Good simple HA, weaker scale-out/common-mode boundary** |
| **W3 preferred WAFs + shared reserve in each site** | **High** | **High** if reserve is available, policy-ready and sized | **High** when Site 2 application is ready | High shared efficiency | Medium; reconnect to reserve/remote WAF expected | Medium because reserve is shared | **High** | **High resilience but shared-capacity/cross-tenant risk** |
| **W4 asymmetric: Site 1 cluster + extra WAF; Site 2 cluster only** | **Very High in Site 1** if extra WAF is hot/policy-ready | **High in Site 1**; lower local redundancy once running in Site 2 | **Medium-High**, but Site 2 must be sized to carry production with only the cluster | Medium | High for first clustered failover; reconnect expected when moving to extra WAF or Site 2 | High | **High** | **Strong primary-site resilience, but asymmetric DR capacity must be explicit** |

The second site is common to every design. The meaningful W1-W4 differences are therefore:

- local WAF failure-domain size;
- scale-out model;
- dedicated/shared/spare capacity;
- connection-mirroring behavior;
- common-mode policy exposure;
- recovery complexity before GTM/site failover;
- and, for W4, the intentional **capacity asymmetry between Site 1 and Site 2**.

# 14. Critical failure points

Across all options, the most important residual risks are:

1. **GTM false green** from IP/port-only monitoring.  
   Healthy TCP does not prove the application is usable.

2. **DNS cache and client behavior.**  
   GTM may make the correct decision while recursive resolvers/clients keep stale answers.

3. **Manual passive-site application startup.**  
   This can dominate RTO and makes fast F5 failover irrelevant at site level.

4. **LTM-pair total loss.**  
   In any topology that depends on one tenant LTM pair, complete LTM loss removes access to every downstream WAF option behind it.

5. **Common-mode WAF policy/configuration error.**  
   More WAF nodes do not help if the same bad policy is pushed everywhere.

6. **Shared reserve exhaustion in W3.**  
   Two shared spares are not equivalent to two spares per tenant.

7. **Connection/state assumptions.**  
   F5 mirroring helps selected pair failures but does not provide unlimited connection preservation across a third WAF, failback or site failover.

8. **Application state/session design.**  
   A stateful application without portable state can have an RTO far longer than the F5 layer.

9. **Socket/WebSocket client non-compliance.**  
   Missing reconnect/re-auth/replay logic can turn every infrastructure failure into an extended application outage.

10. **App A -> App B cascading dependency.**  
    Poor timeout/retry/service-discovery logic can cause one B failure to bring down many otherwise healthy applications. XD1 local-preferred/remote-fallback routing can prevent this, but only when B2 is safe to use and App A implements bounded timeout, safe retry and connection refresh.

11. **Split-site front-end/backend recovery.**  
    X2B can preserve a healthy Site 1 application after Site 1 LTM/WAF loss, but it couples Site 2 ingress to Site 1 backend and the inter-site network. This should be treated as a degraded contingency state, not a preferred steady state.

12. **Cross-site routing asymmetry/capacity.**  
    X2 adds resilience only if stateful firewalls, NAT, routes, capacity and return paths are deliberately engineered.

13. **Platform/cloud firewall (CFW) blast radius.**  
    A shared or tenant-wide CFW failure can make multiple otherwise-healthy ELBs/applications unreachable and can trigger several GTM/application failovers at once. CFW HA, NAT/state, routing and policy health must therefore be tested independently.

14. **Cross-tenant shared infrastructure.**  
    Shared GTM/LTM/WAF/reserve components can expand one failure from one application suite to several tenants.

# 15. Architecture conclusion

No WAF topology alone creates end-to-end resilience.

All W1-W4 designs have a second-site recovery path with similar GTM/LTM roles. W1-W3 normally repeat the same WAF topology in both sites. W4 deliberately does not: Site 1 has the WAF cluster plus an extra active/spare WAF, while Site 2 has only the WAF cluster.

- **W1** is a strong default for horizontal scale and clean failure-domain reasoning.
- **W2** is attractive where simple two-node HA and supported connection mirroring are valuable, but the cluster pair remains the key local failure boundary.
- **W3** can provide strong resilience with efficient shared reserve capacity, but reserve exhaustion and cross-tenant policy isolation become enterprise risks.
- **W4** provides the strongest **Site 1 local WAF redundancy** of these patterns, especially if the extra WAF is hot and policy-ready. Its main trade-off is asymmetric DR: once operating in Site 2, only the WAF cluster is available unless capacity is added.

Cross-site routing is most valuable when it prevents a healthy application from moving merely because its local WAF/LTM path failed, or prevents a healthy App A from moving because App B1 failed. X2A is preferable to X2B when the local LTM survives because it avoids DNS convergence and keeps client ingress stable. X2B is a useful second-tier contingency when application DR is slower than front-end failover, but it should remain a temporary degraded state.

For W4 specifically, capacity tests must prove that the Site 2 WAF cluster alone can carry the required DR load, because Site 2 does not have Site 1's extra active/spare WAF.

For business-critical systems, **application compliance is part of the architecture acceptance criteria**. A topology should not receive a "high resilience" rating unless the application type meets the retry/state/reconnect requirements needed to exploit the infrastructure recovery path.
