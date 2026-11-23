# Common Failure Matrix — Enterprise WAF Topology Options

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
| **W4** | Local WAF cluster + local spare + second-site WAF cluster |
| **W5** | Per-site scalable WAF pools + GTM site recovery |

Cross-site dataplane routing is evaluated separately as:

- **X1** local-only
- **X2** controlled cross-site contingency

# 2. Timing shorthand

These are modelling categories, not guaranteed SLAs.

| Timing ID | Meaning |
|---|---|
| **T1 — HA peer failover** | roughly 3+ seconds peer-loss detection under common/default-style BIG-IP HA behavior, plus traffic-group/network convergence; validate in production design |
| **T2 — local pool-member health** | often up to the configured LTM monitor timeout; many monitor types default around 5s interval / 16s timeout |
| **T3 — direct GTM monitor** | BIG-IP DNS direct HTTP/HTTPS/TCP monitoring commonly defaults around 30s interval / 120s timeout unless tuned |
| **T4 — DNS/site convergence** | health detection + GTM decision + TTL/cache + client re-resolution/retry + alternate-site readiness |
| **T5 — warm/cold/manual** | operator/startup/configuration dependent; may be minutes or longer |
| **T6 — application recovery** | application-specific retry/reconnect/session/state/replay behavior; can dominate RTO even after infrastructure is healthy |

# 3. Control-plane and ingress failures

| ID | Failure | Detection / recovery path | Indicative timing | W1 | W2 | W3 | W4 | W5 |
|---|---|---|---|---|---|---|---|---|
| F01 | One GTM/DNS node fails | Remaining GTM/DNS peer(s) continue answering; DNS service redundancy must be independent of app WAF topology | T1/T4 depending GTM HA design; existing cached answers unaffected | No WAF impact | No WAF impact | No WAF impact | No WAF impact | No WAF impact |
| F02 | All GTM/DNS service in one site fails | Other GTM site/listener must answer queries; customer/corporate DNS must be able to reach it | DNS resolver retry + cache behavior; usually T4 | Existing app sessions continue; new DNS resolution depends on remaining GTM | Same | Same | Same | Same |
| F03 | GTM IP/port monitor is green but application is broken | No recovery until app-level signal or operator detects failure; GTM may keep advertising bad site | Potentially unbounded from GTM perspective | Critical false-green risk | Critical false-green risk | Critical false-green risk | Critical false-green risk | Critical false-green risk |
| F04 | GTM full application-readiness monitor marks local app down | GTM stops returning unhealthy site and selects next healthy eligible site/pool | app monitor detection + T4 | Site switch if alternate ready | Same | Same | Same | Same; intended site-level behavior |
| F05 | One leased line fails | Only user population routed through that line loses reachability unless customer/network reroutes | carrier/routing convergence; not a WAF recovery | App remains healthy for other users | Same | Same | Same | Same |
| F06 | One edge-firewall member fails | Firewall HA pair takes over VIP/state according to firewall design | firewall HA timing, outside F5 WAF/LTM timing | Downstream F5 stack unchanged | Same | Same | Same | Same |
| F07 | Entire edge-firewall pair/path fails | Remaining leased-line/firewall path or alternate site must be reachable; GTM cannot solve missing network reachability by itself | routing/firewall convergence or T4 if site selection changes | Potential partial/full external outage | Same | Same | Same | Same |

# 4. LTM failures

| ID | Failure | Recovery path | Indicative timing | W1 | W2 | W3 | W4 | W5 |
|---|---|---|---|---|---|---|---|---|
| F08 | One LTM node in HA pair fails | BIG-IP DSC traffic group fails to peer; use redundant HA communication | T1; validate actual ARP/MAC/network convergence | **High resilience**; WAF pool unchanged | W2a N/A; W2b cluster remains behind surviving LTM | **High**; preferred/reserve pools unchanged | **High** | **High** |
| F09 | Entire local LTM HA pair unavailable | No local traffic steering through that LTM tier; use alternate site or a separately reachable service path | T4 if GTM/site switch; otherwise outage | Local WAF pool unreachable through normal design | W2a may avoid this failure domain; W2b affected | Preferred + reserve WAFs are useless if all require failed tenant LTM | Local spare/cluster unavailable through failed LTM; site switch required | Site switch is explicit recovery path |
| F10 | LTM health monitor falsely marks healthy WAF down | Capacity reduced; may activate lower-priority/reserve members | T2 | Remaining WAF pool handles load | W2b can withdraw whole cluster VIP/member if monitor design poor; W2a N/A | May unnecessarily consume reserve | May activate spare | Remaining pool handles load |

**Critical observation:** An LTM pair is itself a tenant-level service failure domain. W3 shared spare WAFs do not protect against total tenant-LTM loss unless there is another traffic-steering path.

# 5. WAF failures

| ID | Failure | Recovery path | Indicative timing | W1 | W2 | W3 | W4 | W5 |
|---|---|---|---|---|---|---|---|---|
| F11 | One WAF node/member fails | LTM withdraws member or clustered peer takes over | W1/W3/W5: T2; W2/W4 cluster: T1/T2 depending failure mode | **Very good** if remaining capacity sufficient | **Very good** for first HA-pair failure; mirroring may preserve supported connections | **Very good**; preferred peer remains, reserve available | **Very good**; cluster peer/spare available | **Very good** |
| F12 | Two WAF nodes fail / preferred tenant WAF pair lost | Use remaining independent members, reserve, local spare or site recovery | T2; T5 if spare not hot; T4 if site switch | Good only if pool has 3+ and N-2 capacity; 2-node pool = complete local WAF loss | HA pair lost = complete local WAF service loss | **Strong** if reserve WAFs are hot, configured and have capacity | **Strong** if local spare is hot/configured; otherwise T5/site | Good if local pool has 3+; otherwise site recovery |
| F13 | Entire local WAF service unavailable | Local alternate WAF path, cross-site WAF if X2, or GTM site failover | T2/T4/T5 depending design | X1: site failover; X2: remote WAF possible | Site failover unless separate WAF service exists | Reserve may recover locally if independent from failure cause | Local spare may recover; otherwise Site 2 cluster | Site 2 via GTM by design |
| F14 | Bad WAF policy/configuration pushed to all WAFs | Roll back policy; use independently controlled unaffected pool/site only if bad config not replicated there | operator/change rollback; often T5 | **Common-mode critical risk** | **Common-mode critical risk** | Reserve is not useful if it receives same bad policy | Spare/site not useful if same bad policy replicated everywhere | Both sites may fail if config is globally synchronized |
| F15 | WAF CPU/throughput exhaustion | LTM sends to remaining/added members; reserve or site capacity may absorb load | T2 if monitor detects; scale/ops dependent | **Best horizontal scale** | Cluster capacity may be fixed; scaling less flexible | Good if reserve capacity available | Spare gives bounded extra capacity | Good if both local pools sized with headroom |
| F16 | Shared reserve WAFs exhausted by another tenant | No reserve available; tenant falls back to preferred survivors/site recovery | capacity event; T4/T5 if site move | N/A | N/A | **Critical W3 shared-capacity risk** | N/A unless spare shared | N/A |

# 6. Backend/application-platform failures

| ID | Failure | Recovery path | Timing | W1 | W2 | W3 | W4 | W5 |
|---|---|---|---|---|---|---|---|---|
| F17 | One application VM/pod/member fails | ELB/application LB selects another member; WAF topology should not change | backend monitor timeout + T6 | No topology change | No topology change | No topology change | No topology change | No topology change |
| F18 | Local application ELB/cloud-edge path fails | WAF may see backend unavailable; GTM/app routing must select alternate ready service | backend detection + T4/T6 | Site/app failover unless alternate backend path exists | Same | Same | Same | W5 site failover naturally aligned |
| F19 | Application is network-up but business-not-ready | Requires app-level readiness monitor; IP/port monitoring creates false green | potentially unbounded if only L4 monitor | All options equally vulnerable | Same | Same | Same | Same |
| F20 | Shared session/state store fails | Application-level recovery, alternate state store/site; WAF/LTM failover alone does not help | T6; data-platform RTO | Infrastructure may stay green while app fails | Same | Same | Same | Same |
| F21 | App B local service fails while App A remains healthy | A should use healthy B2/service VIP if supported; otherwise A may fail/cascade | dependency monitor + T6; X2 if remote B used | WAF topology irrelevant to east-west dependency unless path uses it | Same | Same | Same | Same |

# 7. Cross-site failures

| ID | Failure | Recovery path | Timing | W1 | W2 | W3 | W4 | W5 |
|---|---|---|---|---|---|---|---|---|
| F22 | Inter-site link fails while all local services are healthy | Keep local services up; remove only remote contingency paths | route detection; no DNS change should be required | X1 no impact; X2 loses remote reserve only | Same | Shared reserve affected only if reserve depends on inter-site link | Site 1 local cluster/spare should remain healthy | **No dataplane impact by design** |
| F23 | Inter-site link fails while remote WAF/App B is already being used | Revert to local healthy capacity if possible; otherwise application/site recovery | route detection + T2/T4/T6 | Remote sessions fail/reconnect | Same | Reserve traffic may fail if reserve remote | Remote/site contingency may collapse | W5 normally avoids this state |
| F24 | Cross-site route becomes asymmetric through stateful firewall/NAT | Connections fail despite endpoints being healthy; must restore symmetric route/SNAT design | network troubleshooting; potentially T5 | X2 critical risk | X2 critical risk | Shared remote reserve critical risk | Cross-site use critical risk | Minimal if no remote dataplane borrowing |

# 8. Full-site failures

| ID | Failure | Recovery path | Timing | W1 | W2 | W3 | W4 | W5 |
|---|---|---|---|---|---|---|---|---|
| F25 | Entire Site 1 fails and Site 2 app is ready | GTM returns Site 2 healthy VIP; client re-resolves/reconnects | T4 + T6 | Good if Site 2 equivalent exists/capacity | Good if Site 2 cluster exists | Good if Site 2 capacity exists | **Strong explicit second-site cluster** | **Strong explicit design intent** |
| F26 | Entire Site 1 fails but passive Site 2 application is stopped | Start app, validate dependencies/readiness, then GTM may advertise it | **T5 dominates** + T4/T6 | Infrastructure HA cannot meet short RTO | Same | Same | Same | Same |
| F27 | Site 1 remains partially reachable but critical app dependency/data is unavailable | App-level health must withdraw site only for affected application; avoid global site-down decision | app readiness + T4/T6 | Per-app GTM health required | Same | Same | Same | Same |

# 9. Long-lived/socket behavior

Infrastructure recovery and application recovery must be separated.

| Failure | W1 | W2 | W3 | W4 | W5 |
|---|---|---|---|---|---|
| One WAF fails | Existing sockets on failed WAF normally reconnect to another WAF | Two-device mirroring may preserve some supported connections, but F5 AWAF has mirroring limits | Reconnect to preferred/reserve WAF | Cluster peer may preserve supported connection; move to third spare should assume reconnect | Reconnect to another local WAF |
| LTM HA peer fails | LTM connection mirroring can help if configured/supported; app should still tolerate reconnect | Same for W2b; W2a N/A | Same | Same | Same |
| WAF cluster fails completely | Reconnect via new WAF/site | Mirroring cannot preserve connection when whole pair is gone | Reconnect via reserve/site | Move to spare/site; **assume reconnect** | Reconnect via alternate member/site |
| Site failover | DNS change does not move existing socket; client must reconnect/re-resolve | Same | Same | Same | Same |

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
- W4/W5/multi-node hardware resilience provides little end-to-end benefit if clients cannot reconnect.

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

Ratings assume good capacity, correct health monitors and compliant applications.

| Topology | Single WAF failure | Dual/local WAF failure | Site failure | Horizontal scale | Long-lived continuity | Tenant isolation | Operational complexity | Overall |
|---|---|---|---|---|---|---|---|---|
| **W1 scalable pool** | **High** | **Medium-High** if 3+ / N-2 capacity; Low if only 2 | Medium unless paired with site design | **High** | Medium; reconnect expected | High if tenant-dedicated | Medium | **High local resilience** |
| **W2 HA cluster** | **High** | Low once whole pair lost | Medium | Low-Medium | **High for first supported mirrored failover**, but limited beyond 2 devices | High | Low-Medium | **Good simple HA, weaker scale/common-mode** |
| **W3 preferred + shared reserve** | **High** | **High** if reserve available | Medium-High | High shared efficiency | Medium; reconnect to reserve expected | Medium due shared reserve | **High** | **High resilience but shared-capacity risk** |
| **W4 cluster + spare + remote cluster** | **Very High** if spare hot | **High** | **High** | Medium | High for first cluster event; reconnect expected when moving to spare/site | High | **High** | **Very resilient, operationally complex** |
| **W5 per-site pools + GTM** | **High** | **High** if pools sized N-1/N-2 | **High** when app/site ready | **High** | Medium; site/member reconnect expected | **High** | Medium | **Strongest clean failure-domain model** |

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
    Poor timeout/retry/service-discovery logic can cause one B failure to bring down many otherwise healthy applications.

11. **Cross-site routing asymmetry/capacity.**  
    X2 adds resilience only if stateful firewalls, NAT, routes, capacity and return paths are deliberately engineered.

12. **Cross-tenant shared infrastructure.**  
    Shared GTM/LTM/WAF/reserve components can expand one failure from one application suite to several tenants.

# 15. Architecture conclusion

No WAF topology alone creates end-to-end resilience.

- **W1** is a strong default for horizontally scalable, stateless or reconnect-capable applications.
- **W2** is attractive where simple two-node HA and supported connection mirroring are valuable, but it has a clear pair/common-mode boundary and weaker scale-out behavior.
- **W3** improves asset efficiency and dual-WAF recoverability, but reserve capacity/policy isolation becomes an enterprise shared-risk problem.
- **W4** provides layered local and site resilience, especially if the spare is hot, but has the highest operational/configuration complexity and cannot promise transparent connection preservation through every tier.
- **W5** provides the cleanest fault-domain separation: handle member failures locally, keep normal dataplane traffic local, and use GTM for site-level failure. It costs more capacity but is easier to reason about and test.

For business-critical systems, **application compliance is part of the architecture acceptance criteria**. A topology should not receive a "high resilience" rating unless the application type meets the retry/state/reconnect requirements needed to exploit the infrastructure recovery path.
