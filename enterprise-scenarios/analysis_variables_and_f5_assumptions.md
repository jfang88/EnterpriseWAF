# Enterprise WAF Analysis Variables and F5 Recovery Assumptions

**Status:** Changeable analysis inputs  
**Baseline:** [current_architecture_and_invariants.md](./current_architecture_and_invariants.md)  
**F5 documentation reviewed:** 23 November 2026

This file contains architecture choices and tunable assumptions. Change this file when comparing a new design; do not alter the invariant file unless the real enterprise context changes.

# 1. Candidate WAF topologies

## Common two-site rule

W1-W4 are **per-site WAF topology patterns**. Unless explicitly stated otherwise, the same logical topology is present in both Site 1 and Site 2, with similar GTM/LTM roles per site.

For example, W1 means:

```text
                    BIG-IP DNS / GTM
                   /                 \
               Site 1               Site 2
                 |                    |
            LTM HA pair          LTM HA pair
                 |                    |
            WAF pool 2..N        WAF pool 2..N
                 |                    |
             local apps           local/DR apps
```

Site-level GTM recovery is therefore part of W1 itself. It is not a separate WAF topology.

## W1 — LTM-fronted scalable independent WAF pool

Per site:

```text
Firewall VIP
    |
LTM HA pair
    |
+----+----+----+
|    |    |    |
WAF1 WAF2 WAF3 ... WAFn
    |
application
```

- Starts with two WAFs per site and can scale to three or more.
- WAFs are independent active pool members.
- LTM removes failed members using health monitors.
- Capacity must be sized for N-1 and, where required, N-2.
- Policy/configuration consistency across all WAF nodes is critical.
- Site 2 normally has the same logical LTM/WAF-pool design.
- If the local WAF service cannot recover, GTM can select the alternate site's firewall/LTM/WAF path when that application/site is ready.

## W2 — WAF HA cluster, with or without LTM in front

The selected W2 variant is normally repeated in both sites.

### W2a — no ingress LTM

Per site:

```text
Firewall VIP
    |
WAF HA cluster
    |
application
```

### W2b — LTM in front

Per site:

```text
Firewall VIP
    |
LTM HA pair
    |
WAF HA cluster
    |
application
```

- WAF pair is a clustered HA service/failure domain.
- Connection/persistence mirroring can improve continuity for supported traffic.
- Horizontal scale and third-node continuity need special care; F5 documents explicit ASM/AWAF mirroring limits.
- The alternate site provides the same logical W2 service for site-level recovery.

## W3 — tenant-preferred WAFs plus shared enterprise reserve

Per site, each tenant has its preferred WAF capacity behind a **tenant LTM service**. One or more shared reserve WAFs may be available to multiple tenant pools.

```text
Tenant LTM DSC service
    |
+---+---+
|       |
WAF1   WAF2
   \   /
 shared reserve
 +-----+-----+
 |           |
R-WAF1     R-WAF2
```

Preferred tenant WAFs handle normal traffic. Shared reserve WAFs can join a tenant pool when preferred WAF capacity is lost.

### W3-L2 — two-device tenant LTM Sync-Failover pair

This is the baseline/default W3 LTM model.

```text
Tenant VIP / traffic group
          |
      LTM-A active
      LTM-B standby
          |
 preferred/reserve WAFs
```

Benefits:

- simplest DSC operating model;
- mature active/standby failover;
- one LTM member can be maintained while the peer serves traffic.

Limitation:

- during maintenance of one LTM, the tenant LTM service is effectively single-device;
- complete loss of the LTM pair removes access to both preferred and reserve WAFs behind it.

### Optional W3-L3 comparison — three-device tenant LTM Sync-Failover group

F5 DSC supports up to **eight devices** in a Sync-Failover device group.

For one tenant traffic group/VIP:

```text
Tenant VIP / traffic group
          |
      active: LTM-A
 next-active: LTM-B
 additional: LTM-C
          |
 preferred/reserve WAFs
```

A single traffic group is active on one BIG-IP at a time; three devices do **not** mean one tenant VIP is simultaneously active on all three.

For multiple traffic groups, active load can be distributed:

```text
TG-A active on LTM-A
TG-B active on LTM-B
TG-C active on LTM-C
```

F5 supports ordered and load-aware next-active selection.

Benefits:

- one LTM can be removed for maintenance while **two LTMs still remain**;
- subject to capacity, a second LTM failure during maintenance can be survived locally;
- multiple traffic groups can be distributed across devices for better hardware utilisation;
- lowers the chance that an ordinary LTM failure escalates into GTM/site recovery;
- particularly useful in W3 because reserve WAFs are otherwise unreachable if the entire tenant LTM service is lost.

Trade-offs:

- all three devices remain a **single DSC/configuration change domain**;
- a bad synchronized LTM/iRule/configuration can affect all three;
- each traffic group still has one active owner and one next-active target at a time;
- connection/state mirroring behavior must be validated for the chosen traffic-group/next-active design;
- more failover order, capacity and operational testing is required;
- three devices improve availability/maintenance headroom more than they improve a single VIP's throughput.

### W3-LI — multiple independent LTMs

Multiple independent LTMs are technically possible only when another mechanism distributes traffic to them, for example distinct VIPs, upstream routing/ECMP, firewall steering or GTM/DNS.

This is **not** the preferred default for one tenant service because:

- the front-door VIP/traffic ownership problem has to be solved elsewhere;
- connection/persistence state is not shared automatically as one DSC service;
- config consistency and rollback become more complex;
- upstream health and routing become another failure domain;
- troubleshooting becomes harder.

Independent LTMs can make sense when they intentionally serve **different tenants, applications, VIP sets or fault domains**, rather than trying to behave as one HA LTM service.

### W3 recommendation

Use **W3-L2 (two LTMs per site)** as the enterprise baseline/default. W3-L3 is only an optional comparison and should not be assumed in failure or capacity calculations unless explicitly selected.

Consider **W3-L3** when:

- 99.95%/maintenance requirements justify retaining redundancy while one LTM is out for change;
- there are enough traffic groups to distribute useful active load;
- the third device's capacity is genuinely available during failure;
- operational teams can manage/test the additional DSC complexity.

Do not add a third LTM solely to make a two-device HA pair "more clustered." Its strongest business case is **maintenance + second-failure tolerance** and multi-traffic-group utilisation.

For the detailed distinction between DSC clustering and true load-balanced WAF pools, see [appendix_ltm_waf_2_vs_3_nodes.md](./appendix_ltm_waf_2_vs_3_nodes.md).

Shared reserve WAF risks remain:

- cross-tenant capacity contention;
- policy isolation;
- reserve policy readiness;
- reserve exhaustion during concurrent tenant failures/maintenance.

The same logical preferred-plus-reserve model may exist in Site 2. Site-level GTM recovery remains available in addition to local LTM/WAF recovery.

## W4 — asymmetric WAF cluster plus extra active/spare node in Site 1

W4 is the intentional asymmetry case.

Site 1 has:

- a WAF HA cluster; plus
- one additional independently active/spare WAF.

Site 2 has:

- the WAF HA cluster only.

Two front-end variants should be analysed.

### W4a — LTM in front of both sites

```text
Site 1                               Site 2
Firewall VIP                         Firewall VIP
    |                                    |
LTM HA pair                          LTM HA pair
    |                                    |
    +-- WAF HA cluster (2)               +-- WAF HA cluster (2)
    |
    +-- extra active/spare WAF
```

The Site 1 LTM can steer traffic between the WAF cluster service and the extra WAF according to the selected pool/priority design.

### W4b — no ingress LTM in front of the WAF tier

```text
Site 1                               Site 2
Firewall VIP                         Firewall VIP
    |                                    |
    +-- WAF HA cluster (2)               +-- WAF HA cluster (2)
    |
    +-- extra active/spare WAF
```

For W4b, the exact steering mechanism that decides when/how the extra independent WAF receives traffic must be defined explicitly (for example firewall/VIP/routing behavior). Do not assume LTM-style health-based pool activation if there is no ingress LTM.

### W4 behavior

- The WAF cluster handles the normal clustered HA function.
- The extra Site 1 WAF adds local capacity/resilience beyond the two-node cluster.
- Site 2 deliberately has less local WAF capacity because it has only the cluster.
- If the extra Site 1 WAF is hot and policy-ready, Site 1 can survive a broader set of local WAF failures without GTM/site failover.
- If Site 1 is lost, Site 2 still provides the normal WAF cluster but does **not** have the same extra-node headroom.
- Capacity planning must therefore account for this asymmetry, especially when Site 2 becomes the active/DR site.
- Connection mirroring across the clustered pair does not imply transparent migration to the extra independent WAF.
- Moving traffic from the cluster to the extra WAF should assume reconnect for affected long-lived connections unless a tested F5-supported mechanism proves otherwise.
- W4 should be assessed separately for:
  - one cluster member failed;
  - both cluster members failed;
  - extra active/spare WAF failed;
  - cluster plus extra WAF failed;
  - Site 1 failed and Site 2 must carry load using only its WAF cluster.

# 1A. Tenancy and sharing variables

W1-W4 describe WAF topology. **Tenancy/sharing is a separate design axis.**

For cost and blast-radius analysis, compare the following deployment patterns across an illustrative **four-tenant** estate. Four tenants is a planning case, not a new enterprise invariant.

## D1 — fully dedicated per tenant

Each tenant/site has its own:

- two-LTM HA pair where LTM is used;
- dedicated WAF pair/pool/cluster;
- independent change and capacity boundary.

This maximizes tenant isolation but duplicates standby/spare capacity.

## S1 — tenant LTM pairs + shared active WAF pool

Each tenant retains its own LTM HA pair and routing/VIP boundary, while multiple tenants feed a shared independent active WAF pool.

Advantages:

- shares horizontally useful WAF capacity;
- reduces WAF appliance count;
- retains tenant-specific LTM ingress failure domains.

Risks:

- shared WAF policy/configuration and capacity become cross-tenant failure domains;
- N-1/N-2 must be assessed against **aggregate** tenant load;
- Site 2 must be sized for simultaneous failover of the credible shared blast radius.

## S2 — shared LTM pair + shared WAF pool

Multiple tenants share both the LTM service and the WAF pool.

This minimizes device count but maximizes common-mode blast radius. Treat it as a deliberate shared-service architecture rather than an implicit cost optimization.

## S3 — shared WAF HA cluster

Multiple tenants use one WAF HA/DSC cluster per site, with either dedicated tenant LTMs or a shared LTM pair.

A shared two-node cluster tolerates one WAF member failure, but complete cluster loss affects every tenant using it. It is not equivalent to an independent active WAF pool for horizontal scale.

## W3 hybrid — dedicated preferred WAFs + shared reserve

Each tenant keeps dedicated preferred WAF capacity while reserve WAFs are shared.

For four-tenant cost modelling, the useful comparison is:

- two dedicated preferred WAFs/tenant/site + shared reserve;
- versus three dedicated WAFs/tenant/site;
- versus a shared active WAF pool.

The shared reserve should be counted as a common capacity/failure dependency and must not be treated as if every tenant owns the full reserve simultaneously.

See [deployment_options_resilience_summary.md](./deployment_options_resilience_summary.md) for the four-tenant device-count and resilience comparison.

# 1B. WAF platform versus application-policy coupling

Treat the WAF as two layers for target-state design.

## Shared enforcement platform

WAF compute/runtime may be pooled within an approved security zone when:

- aggregate N-1/N-2 capacity is proven;
- application policies remain isolated;
- per-application health, logging and rollback are available;
- one application's traffic or emergency change cannot exhaust unrelated applications;
- the shared blast radius is acceptable.

## Application-coupled policy

WAF policy must be managed as part of the application/API lifecycle because it can depend on:

- routes/URLs and methods;
- schemas;
- authentication flows;
- WebSocket endpoints;
- uploads/body sizes;
- application-specific exceptions;
- rate/bot controls.

A shared WAF pool must not imply a single common application policy or one global enforcement change.

## Extranet sharing boundary and LTM/GTM constraint

The current design focus is the **four-tenant extranet estate**.

For current option analysis:

- retain the existing GTM model;
- retain the four tenant LTM HA service boundaries;
- compare dedicated versus shared WAF capacity behind those LTM services;
- treat S2/shared-LTM consolidation only as a future comparison, not the current target.

If applications later converge onto a common private-cloud platform, LTM/GTM consolidation can be revisited as a joint target-state question. It must not be assumed until the GTM/LTM/network owners participate.

This is a scope/ownership constraint, not a statement that the existing LTM/GTM design is permanently optimal.

See [current_architecture_and_invariants.md](./current_architecture_and_invariants.md) for the authoritative current-state architecture and invariants.

# 2. Cross-site dataplane variables

Cross-site routing is not a single design. Model the following separately.

## X1 — local-only

LTM/WAF/application traffic remains in the local site.

Loss of a whole local WAF tier normally requires local restoration or application/site recovery.

## X2A — surviving local LTM borrows a remote WAF

Normal:

    Site 1 firewall -> Site 1 LTM -> Site 1 WAF -> Site 1 app

Contingency:

    Site 1 firewall -> Site 1 LTM -> Site 2 WAF -> route back -> Site 1 app

Use remote WAFs as lower-priority contingency members where routing and policy allow it.

F5 Priority Group Activation and the Virtual Location monitor are suitable building blocks for local-preferred / remote-fallback behavior.

Primary benefit:

- avoids DNS change and avoids moving a healthy application.

Primary risk:

- inter-site path, remote WAF capacity, SNAT/return-route symmetry and policy readiness become part of service recovery.

## X2B — remote front-end routes back to the primary application

Normal:

    GTM -> Site 1 firewall -> Site 1 LTM -> Site 1 WAF -> Site 1 app

Contingency:

    GTM -> Site 2 firewall -> Site 2 LTM -> Site 2 WAF
        -> inter-site route -> Site 1 app

Use when the local front-end/LTM/WAF tier is unavailable but the primary application remains healthy.

Primary benefit:

- can avoid application DR/startup even after local delivery-tier loss.

Primary risks:

- DNS/GTM convergence;
- split-site front-end/backend;
- inter-site network dependency;
- more complex routing and troubleshooting.

## X2C — conventional full site/application failover

    GTM -> Site 2 firewall -> Site 2 LTM -> Site 2 WAF -> Site 2 app

Use when the primary application is unhealthy, its data/state cannot remain in Site 1, or route-back is unsafe/unavailable.

## XD1 — App A -> App B local-preferred / remote-fallback dependency routing

Normal:

    A1 -> B service VIP -> B1

Contingency:

    A1 -> B service VIP -> B2

This is separate from external WAF recovery.

A stable LTM/service VIP with local B1 at higher priority and B2 as lower-priority contingency can prevent a B1 failure from forcing A1 and other dependent applications to fail site.

Cross-site dependency use requires:

- B2 capacity;
- acceptable latency;
- data/state consistency;
- authentication/service identity;
- firewall/routing rules;
- bounded timeouts;
- safe retries;
- connection refresh/re-resolution;
- idempotency/reconciliation.

If the application cannot safely retry/reconnect to B2, do not count XD1 as a valid end-to-end recovery path.

## Common cross-site validation

For X2A, X2B and XD1 explicitly validate:

- forward route;
- return route;
- stateful firewall symmetry;
- NAT/SNAT;
- original-client-IP requirements;
- latency;
- inter-site bandwidth/capacity;
- remote WAF/application capacity;
- policy/configuration readiness;
- application state/data locality;
- behavior when the inter-site link fails while contingency is active.

# 3. GTM/DNS health models

## G1 — IP/port health only

GTM considers an application endpoint healthy when the target IP/service port responds.

Advantages:

- simple;
- low application dependency;
- easy to operate.

Risk:

- **false green**: TCP/HTTPS listener may be up while the application, dependency, login flow or business function is broken.

Use only where port availability is a sufficient definition of service readiness.

## G2 — full application-level health

GTM or the integrated LTM status represents an application-level readiness endpoint or transaction.

Examples:

- HTTP(S) health URL that validates application readiness;
- expected response body/status;
- application health that includes critical dependencies.

Advantages:

- substantially better site-selection signal;
- avoids advertising a site whose network stack is alive but application is unusable.

Risks:

- overly deep checks can create false negatives if a non-critical dependency is included;
- expensive synthetic transactions can create load;
- monitor credentials/secrets may be required for deep checks.

Recommended pattern: expose a lightweight **readiness** endpoint that represents whether the instance/site can safely accept new traffic.

## G3 — local authoritative health plus distributed/cross-site observation

Recommended analysis model for two sites:

1. Each site's LTM performs local member/application health checking.
2. BIG-IP DNS/GTM integrates with BIG-IP LTM using the BIG-IP monitor/iQuery so GTM can use LTM virtual-server health.
3. Where path-awareness is needed, additional probers/cross-site checks observe the remote endpoint.
4. Do not make a healthy site's availability depend solely on the inter-site path. Otherwise an inter-site network failure can incorrectly mark healthy local services down.

BIG-IP DNS supports multiple health monitors and availability requirements such as **All**, **At Least**, and **Require** successful probes. Use these deliberately so a cross-site probe failure does not create an unnecessary site outage.

## G4 — internal namespace / internal endpoint resolution

Internal DNS/GTM behavior is a separate analysis variable from the external namespace.

For each internal service/application, record one of these models:

### G4A — enterprise DNS resolves directly

    App/User -> internal DNS -> internal VIP/endpoint

### G4B — enterprise DNS delegates/forwards selected name to GTM

    App/User -> internal DNS
             -> GTM/BIG-IP DNS
             -> internal service VIP/endpoint

### G4C — stable internal service VIP with GTM behind the service abstraction

    App/User -> internal DNS -> stable service name/VIP
                              -> health-aware local/remote members

Analyse:

- internal DNS availability;
- conditional-forward/delegation availability;
- GTM internal-name availability;
- internal TTL/application DNS cache;
- whether applications re-resolve after dependency failure;
- whether GTM returns only endpoints reachable from the internal network;
- whether internal and external names have different health policies;
- whether App A/B/C dependencies should use local-preferred/remote-fallback internal answers;
- whether an internal GTM/DNS failure can cascade across multiple applications even while external ingress remains healthy.

Do not assume the internal DNS architecture must be changed merely because GTM is available. The analysis should identify the dependency and failure behavior first.

# 4. GTM DNS response preference

## Active/passive applications

Use a health-gated primary/secondary model.

F5 BIG-IP DNS **Global Availability** selects the first available pool/resource and moves to the next only when the preferred resource is unavailable.

Model:

```text
Primary Site 1 application pool
   -> if unavailable
DR Site 2 application pool
```

Do not return Site 2 merely because its firewall/LTM is alive when the application is still stopped.

## Active/active or locality-preferred applications

Use **Topology** load balancing where the client's LDNS/resolver source can reliably map to the desired site, then fall back to another healthy site.

Important: do not infer "in-site" from whichever GTM appliance happened to answer the DNS query. Preference should be based on application mode and/or topology records tied to resolver/client network context.

# 5. F5 monitoring and recovery-time assumptions

These are **engineering modelling assumptions**, not guaranteed SLA values. Validate on the actual BIG-IP release, hardware, VLAN/routing design and application.

## T1 — BIG-IP HA peer/device failover

F5 DSC network failover uses HA communication between devices. F5 support documentation shows that interruption of failover communication for roughly **3 seconds** can trigger expected HA behavior, and recommends redundant failover communication using management and TMM/self-IP paths.

Model:

- peer-loss detection: approximately 3+ seconds under common/default-style network failover settings;
- service restoration: detection plus traffic-group takeover plus upstream/downstream network convergence;
- use a **seconds-scale** target, but measure it in the real network.

Do not publish an exact RTO without failover testing.

## T2 — LTM pool-member/WAF-member health detection

Many BIG-IP LTM active monitor types use defaults around:

- Interval: **5 seconds**
- Timeout: **16 seconds**

F5 documentation states the timeout should generally be about three times the interval plus one second for these monitors.

Validated behavior:

- while a failed member is still considered healthy, some new connections/requests can still be selected to it and fail;
- once the member is marked down, BIG-IP LTM stops sending new connections to that member and redirects new traffic to another healthy pool member;
- this can make a pool-member failure a relatively short **local recovery event** when healthy capacity remains;
- already-established TCP/WebSocket connections on the failed member are **not automatically migrated** to another member;
- F5's default pool `Action On Service Down` behavior is `None`, so an existing connection may remain until it ends, resets, or its TCP/application timeout expires (`K15095`). For **W1/S1/W3 independent WAF pools** and **XD1 `App A -> B` pools**, configure `Action On Service Down = Reject` so BIG-IP LTM sends an immediate TCP RST to affected clients when a member fails, cutting dead-socket hang time and triggering prompt `T6` reconnect. Do **not** use `Reselect` on full-proxy HTTP/TLS virtual servers (`K15095`: `Reselect` does not establish a new TCP/TLS handshake to the replacement member and is ignored on Standard virtual servers with TCP and address/port translation enabled).
- On the **LTM Virtual Server itself**, F5's default `Immediate Action On Service Down` is `None` (`K40554304`), meaning the virtual server continues answering TCP 3-way handshakes even when **all** pool members are down — creating a **false-green** risk for upstream firewall or L4 GTM checks. Set `Immediate Action On Service Down = Reject` (or `Drop`) where upstream TCP reachability must reflect pool availability.

Planning model:

- **new requests/connections:** up to approximately the configured member-monitor timeout (often ~16s with the documented defaults), then healthy-member selection;
- **existing connection on failed member:** monitor timing does not bound the user outage unless `Action On Service Down = Reject` is configured; add client/application timeout + reconnect/retry (T6);
- **unaffected existing connections on healthy members:** no direct interruption.

Do not describe this as "zero interruption" unless the affected connection is preserved by a tested HA/mirroring mechanism or the client/application retry is effectively transparent.

Tune monitor intervals only after testing false-positive/flapping risk.

## T3 — BIG-IP DNS direct health monitor

BIG-IP DNS HTTP/HTTPS/TCP-style monitor documentation commonly shows defaults around:

- Interval: **30 seconds**
- Timeout: **120 seconds**

Therefore a standalone direct GTM monitor can be materially slower than local LTM health detection unless tuned.

For F5-to-F5 environments, prefer integrating BIG-IP DNS with LTM health via the BIG-IP monitor/iQuery where appropriate, and add application-level readiness checks where infrastructure health alone is insufficient.

## T4 — DNS/site failover convergence

### DNS answer TTL

F5's current iControl REST reference for BIG-IP DNS/GTM A-record pools documents a default pool **TTL of 30 seconds**.

The TTL means the returned IP address is valid in the resolver/client cache for that period before a fresh DNS lookup is required.

Therefore, after GTM decides that Site 1 is unhealthy:

- **new uncached DNS queries** can receive the healthy Site 2 answer immediately after the GTM health state changes;
- a resolver/client that already cached the Site 1 answer may continue using it for the **remaining TTL**, up to approximately 30 seconds if the configured TTL is left at the documented default;
- an already-established TCP/TLS/WebSocket connection does **not** move merely because the DNS TTL expires;
- an application may continue using an old connection or its own DNS cache beyond the authoritative TTL, so client/application behavior must be tested.

Do not confuse:

- **GTM health-monitor interval/timeout** — how long GTM takes to decide an endpoint is unavailable; with many direct GTM HTTP/HTTPS/TCP monitors the documented defaults are 30s interval / 120s timeout; and
- **DNS answer TTL** — how long an already-returned IP can remain cached; the documented GTM pool default is 30s.

End-user site recovery is therefore:

```text
health detection
 + GTM decision/update
 + residual DNS TTL/cache
 + client/application reconnect or retry
 + alternate-site application readiness
```

### Validated planning examples

These are calculations from documented defaults, **not F5 SLAs**:

1. **Direct GTM monitor model**
   - health withdrawal: up to ~120s with default-style direct GTM monitor timeout;
   - residual DNS answer TTL: up to ~30s;
   - planning boundary before fresh DNS resolution: roughly **up to ~150s + T6**, assuming alternate site is already ready.

2. **LTM health exported to GTM / iQuery model**
   - local application/WAF-path health may be detected on the LTM's faster monitor timescale (for example ~16s with common defaults);
   - GTM/iQuery propagation must still be measured;
   - if GTM changes its answer at about that point, residual DNS TTL can add up to ~30s;
   - an illustrative lower-latency planning case is therefore **~46s + T6**, but this is not a vendor guarantee and must be measured end-to-end.

3. **Manual passive-site application**
   - add T5 before the alternate site can safely be advertised/used;
   - T5 can dominate the RTO and make DNS/F5 timing a minor component.

A manual passive-site application startup can therefore dominate the total RTO even when GTM detects failure quickly.

## T5 — warm/cold/manual server-side & operational recovery

Use **T5** where recovery depends on **manual operator action or slow warm/cold server-side startup**, including:

- passive-site application or service startup;
- manual database failover, promotion, or data/transaction reconciliation;
- manual clearing of hung server thread/connection pools or operator restarts;
- loading configuration/policy onto a spare or rolling back a bad change;
- network/routing repair.

**Expectation:** `T5` has no fixed F5 product duration — it is typically **minutes to hours** and must be measured from the actual operational runbook. Any routine failure or planned change that triggers `T5` rapidly consumes the **99.95% (`4h 22m 48s / year`)** combined budget.

## T6 — application recovery (`T6a` client-side vs. `T6b` server-side)

**T6** measures application-specific recovery *after* the network/LTM/WAF/ELB infrastructure path is restored. Always separate **`T6a` (client-side)** from **`T6b` (server-side)** — and explicitly flag when poor architecture forces **manual user or operator steps**:

| Sub-Code | Scope | Automated / Well-Architected (Seconds — Supports 99.95%) | Poorly Architected / Manual (Minutes to Hours — Breaches 99.95%) |
|---|---|---|---|
| **`T6a` — Client-Side Recovery** | Browser SPA, thick desktop client, mobile app, partner API/WebSocket client | Automated retry with backoff/jitter (`AT1`/`AT2`), DNS re-resolution, silent token refresh, WebSocket reconnect + resubscribe + sequence-gap replay (`AT3`) — **typically seconds** | **Manual user steps required:** hard browser refresh, re-login, restarting a desktop client or partner job, or re-entering lost form/transaction work — **minutes+ (human-speed outage)** |
| **`T6b` — Server-Side App & State Recovery** | Backend service tier, session store, caches, message queues, DB connections | Externalized/replicated session store (Redis/DB), clean DB/service connection-pool reset, Pod/VM warmup, idempotent transaction reconciliation — **typically seconds to ~1–2 min** | **Escalates to `T5` manual server-side recovery:** passive-site app startup, manual DB failover/promotion, manual restart of hung pools, or manual data reconciliation — **minutes to hours** |

**Rule:** Total user-visible RTO is `Infrastructure Recovery (T1–T4 / T9–T12) + T5 (if manual server/DR) + T6b (server app/state) + T6a (client/user)`. Poor client-side recovery (`T6a` manual) or manual server-side recovery (`T5` / `T6b` manual) can dominate user-visible RTO even when F5 failover completes in **3–16 seconds**.

## T7 — failback

F5 traffic-group auto-failback supports configurable delay; F5 documentation shows a default of 60 seconds when auto-failback is enabled and notes 40–60 seconds can allow state mirroring to re-establish.

For critical services, prefer controlled failback rather than immediate oscillation.

## T8 — DNS cache versus existing connection behavior

Treat these separately in every failure scenario:

| Client state | What DNS failover changes |
|---|---|
| No cached answer / new lookup | Receives the new healthy GTM answer after health withdrawal |
| Cached old answer | Can continue selecting the old IP until remaining TTL/cache expires |
| Existing TCP/TLS/WebSocket connection | DNS does not move it; it continues until the path fails, closes or times out |
| Application with its own DNS/connection pool | May retain old endpoint longer than DNS TTL; must explicitly refresh/re-resolve |
| Stateless retrying client | Can recover quickly once it re-resolves/opens a new connection |
| Long-lived/stateful client | Requires T6 reconnect/state/session recovery |

This is why a 30-second DNS TTL does **not** mean "30-second site failover" and does **not** cap the outage of an existing connection.

## T9 — platform/cloud firewall (CFW) recovery

CFW recovery is a separate timing domain from F5 LTM/WAF and application ELB recovery.

The CFW is one logical private-cloud edge/security boundary available in both sites, represented by site-local enforcement paths. ELB/service endpoints sit behind that boundary. This does not establish a stretched physical firewall, shared state, automatic alternate-site routing, or independent failure domains: local and common-mode failures must be validated separately.

No numeric default is assumed because the platform firewall product, HA mode, state synchronization, route convergence and health integration are deployment-specific.

Analyse three distinct cases:

### T9A — one CFW HA member fails

If the CFW HA service keeps the same logical path/VIP and state/routing converges correctly:

- **no DNS TTL should be involved**;
- new connections should continue through the surviving CFW member;
- existing TCP/WebSocket connections may survive only if firewall/NAT/session state is preserved;
- otherwise add T6 reconnect/re-auth/replay.

Target: keep this as a **local seconds-scale HA event**, but use measured CFW data rather than inventing a default.

### T9B — entire local CFW context/service fails

If the CFW is the only path to the local ELB/application:

- the local application can be healthy but unreachable;
- X2A remote-WAF route-back does **not** help if traffic must still traverse the failed Site 1 CFW;
- recovery requires an alternate local CFW path, alternate application/site path, or CFW restoration.

If site failover is required and CFW failure is promptly reflected in the GTM/application health state:

- use the existing **~46s + T6 illustrative fast-health case** or **up to ~150s + T6 direct-GTM-default case**;
- add T5 if the alternate application/site is not ready.

### T9C — CFW false green

This is the critical case:

```text
GTM/LTM/WAF healthy
        |
        v
CFW path broken
        |
        v
ELB/app unreachable
```

If monitoring stops at the WAF/front-end, the bad site can remain advertised and recovery can be **unbounded until another monitor or operator detects the problem**.

Recommendation:

- application/site readiness must prove reachability through the CFW to the ELB/application, or otherwise consume an authoritative signal that represents that full path;
- internal service health must also include CFW reachability where internal App A -> B/C traffic traverses the same CFW.

## T10 — private-cloud ELB recovery (Huawei on-premises platform: TBD / measure)

| Scenario | Timing placeholder | Recovery boundary |
|---|---|---|
| ELB backend member failure | T10a = detection + member withdrawal + routing convergence: TBD | Same service VIP; no DNS change if healthy capacity remains |
| ELB instance/HA failure | T10b = HA detection + takeover + VIP/state convergence: TBD | Validate existing connections and NAT/session continuity |
| Entire ELB service/VIP failure | T10c = service recovery or alternate endpoint readiness: TBD | Add T3/T4 only if published DNS/site selection changes |
 
## T11 — Kubernetes workload/platform recovery (Huawei on-premises platform: TBD / measure)

- T11a: readiness failure, endpoint withdrawal and ingress/ELB propagation — TBD.
- T11b: worker loss detection, eviction/rescheduling, image pull, storage attach and pod readiness — TBD; these may overlap.
- T11c: ingress/controller, control-plane or shared storage/network failure — TBD; distinguish surviving data plane from impaired scheduling and total service loss.

## T12 — VM / hypervisor recovery (Huawei on-premises platform: TBD / measure)

- T12a: guest/app failure detection and backend withdrawal — TBD.
- T12b: host failure detection, HA restart/placement, boot, storage/network and service readiness — TBD.
- T12c: shared compute/storage/network domain failure and alternate capacity — TBD.

For T9–T12, Cloud Platform and application owners must record configured monitors, actual detection and convergence, surviving capacity, state/session loss, and p50/p95/p99 fault-to-first-success under load. Do not substitute F5 timers for Huawei private-cloud timings. A healthy alternate member may restore service before failed workload replacement; report service restoration separately from redundancy restoration. Compose only stages on the critical recovery path (avoid double-counting overlapping detection, readiness, T6b or DNS). Add T6a for client retry/reconnect/replay and T6b only for additional application/state recovery. A logical two-site CFW boundary does not prove route-back or cross-site state continuity; test local and shared/common-mode failures separately.

# 6. F5 connection mirroring implications

F5 recommends connection mirroring where failover would significantly disrupt a long-lived session, and generally does not recommend it for short-lived HTTP/UDP because of performance overhead.

Important Advanced WAF/ASM limitations documented by F5 BIG-IP 17.5.x and 21.1.x include:

- **LTM licensing/provisioning prerequisite:** connection mirroring works fully **only with a licensed and provisioned LTM**; on a standalone ASM or standalone AWAF license (directly affecting **W2a** and **W4b**), mirroring degrades to non-floating Self-IP behavior even when a floating Self-IP is configured;
- **only 2 devices supported:** traffic is mirrored to only one standby peer;
- **no multiple failover support:** third-device/multiple failover resets the connection;
- **no failback support:** failback resets the connection;
- **no default SSL cert/key support** and additional per-feature AWAF mirroring limitations.

**AT3 WebSocket profile caveats (official F5 MyF5 KBs):**

- A **WebSocket profile** must be attached alongside the HTTP and ASM policy for BIG-IP AWAF to inspect WebSocket traffic (`K000132320`, `K84421441`);
- Do **not** combine a **OneConnect** profile with a WebSocket profile (`K000151124` — causes WebSocket failures);
- Removing an ASM policy while leaving a `websecurity` profile attached can stall WebSocket traffic (`K000140381`).

Therefore:

- W2 can improve continuity for a two-device HA event **only where LTM+AWAF are licensed/provisioned and mirroring constraints are met**;
- W4's third/spare WAF does **not** mean an existing connection can transparently survive every transition;
- W1/W3/S1 should assume connections on a failed independent WAF must reconnect;
- application reconnect/state-recovery logic remains mandatory for socket/WebSocket designs on both BIG-IP 17.5.x and 21.1.x.

# 7. F5 WAF policy/configuration consistency and multi-tenant isolation

F5 supports synchronizing Advanced WAF/ASM security policy/configuration across multiple BIG-IP systems using an ASM-enabled Sync-Only device group.

Native F5 mechanisms supporting the **shared WAF runtime + application-coupled policy** model:

- **Parent / Child Security Policies (BIG-IP 17.5 / 21.1):** enforce mandatory enterprise baseline controls via a parent policy while allowing isolated application-specific child policies, exceptions, and release cadence;
- **Administrative Partitions + Route Domains:** provide logical L3/VLAN/RBAC separation per tenant on shared BIG-IP LTM/AWAF appliances (note: F5 does **not** support route domains on standalone BIG-IP DNS);
- **F5OS Tenants (confirmed `r2800` pizza-box rebuild, `F5OS-A 1.8.0+`, no blade chassis):** `r2800` supports up to **2 isolated BIG-IP TMOS tenants/box** (`4 vCPU / 12 GB RAM` each) or 1 full-box tenant (`8 vCPU / 24 GB RAM`), has a **single 480 GB NVMe SSD (~447 GB usable, no RAID-1)**, and **does not support Spanning Tree Protocol (`STP`)** (1 interface/LAG per VLAN, `K000152319`, `K1689`) — see [future_architecture_improvements.md](./future_architecture_improvements.md).

Key modelling assumptions:

- all WAF pool members must enforce equivalent policy for a protected service;
- reserve/shared WAFs must have validated tenant policy before receiving production traffic;
- configuration synchronization is itself a common-mode risk: a bad policy pushed everywhere can fail the whole WAF service even when hardware is healthy;
- **ASM Live Update (`K82512024`):** `liveupdate.allowautoinstallonsecondary` defaults to `false` on DSC groups; avoid uncontrolled `Real Time` signature installation in production and prefer **Scheduled or Manual** Live Updates combined with the **Enforcement Readiness Period (default 7 days staging)** and Policy Diff before enforcement;
- F5 documentation requires members of an ASM-enabled device group to run the same ASM version/hotfix level.

# 8. F5 HA and routing design practices to preserve

- **Redundant HA failover communication:** F5 recommends failover communication over both management IP and TMM/self-IP paths (`K10095`, `K7249`, `K000161390`, default `Failover.NetTimeoutSec = 3s`).
- **Gateway and VLAN Fail-safe (`K16049`, BIG-IP 21.1 HA Fail-safe):** where Gateway Fail-safe is used, F5 recommends `1s` interval / `11s` timeout (greater than the `10s` TMM heartbeat) to avoid premature failover on transient stalls; note **VLAN Fail-safe defaults to `Reboot`** rather than `Failover` unless explicitly changed.
- **BIG-IP VE hypervisor discipline (`K10095`, `K00421514`, `K22658205`):** if BIG-IP VE is used, reserve vCPU/RAM and prohibit live hypervisor VM snapshots, which freeze TMM and trigger clock-advance false failovers.
- **Service-accurate health monitoring:** use L7 readiness monitors plus `Immediate Action On Service Down = Reject/Drop` on LTM virtual servers (`K40554304`) to prevent TCP false-greens, and `Action On Service Down = Reject` on active WAF/dependency pools (`K15095`).
- **Cross-site X2A/X2B & one-arm routing symmetry (`K13876`, `K95573163`, `K7820`, `K8246`, `K4816`):** `Auto Last Hop` preserves L2 MAC return symmetry locally, whereas routed L3 asymmetry (one-arm tiers, cross-site `X2A`/`X2B`, overlapping partner/cloud IP space) requires a **multi-IP SNAT Pool** — never rely on single-IP `SNAT Automap` under high throughput or 4-tenant failover load (~65,535 ephemeral ports per SNAT IP per backend socket, divided across TMM cores per `K33355231`/`K35043645`). Always pair SNAT with **HTTP `X-Forwarded-For` (`XFF`) insertion** on LTM (stripping untrusted external `XFF`) and **`Trust X-Forwarded-For`** in AWAF policies (`K4816`), or PROXY Protocol for `AT4` TCP services; avoid or pin SNAT for legacy `AT4` protocols requiring raw client IP ACLs or consistent single SNAT IP (e.g., passive FTP `K15249`, `K21151342`).
- **Multi-layer sticky-session alignment & `OneConnect` (`K7208`, `K7964`, `K83419154`, `K9816`, `K11362`, `K000149855`):** For `AT2` stateful web, designate a **single authoritative app-node sticky owner** (typically Cloud ELB/Ingress or app cookie passed untouched through WAF) backed by an externalized/replicated session store (so stickiness optimizes locality/throughput rather than acting as a SPOF). Between LTM and the active WAF pool, use stateless deterministic **`CARP` hashing** (`K11362`, zero persistence-table RAM/mirroring) or **Least Connections + `OneConnect`**; avoid Source-IP stickiness for partner web behind shared NAT gateways. Enable **`OneConnect`** on HTTP/1.1 virtual servers using cookie persistence so Keep-Alive connections evaluate persistence per request (`K7964`); when LTM runs `OneConnect` in front of AWAF, pair with **SNAT Pool + `XFF`** (`Trust XFF` on AWAF) or `Source Mask = 255.255.255.255` (`K9816`, `K85357500`). **Never enable `OneConnect` on `AT3` WebSockets (`K000151124`)** or full-proxy HTTP/2 (`K95032535`).
- **High-throughput TCP / TLS / L4 profile hygiene (`K10281257`, `K37412295`, `K09948701`):** Use split-TCP optimization (**`f5-tcp-wan`** client-side + **`f5-tcp-lan`** server-side) with TLS 1.3 session resumption and persistent server-side keep-alive pools from LTM → WAF → CFW → ELB, aligning stateful firewall and ELB idle timeouts above application/WAF keep-alives. For `AT4` non-web L4 bypassing WAF, use **Performance (Layer 4) + `FastL4`** (`K09948701` — software TMM on `r2800` since `r2800` has no ePVA FPGA).
- **Local/remote preference:** use Priority Group Activation (and Virtual Location monitor where appropriate) rather than ad-hoc manual routing.
- **MAC masquerade:** reduce ARP/L2 convergence disruption after traffic-group failover (noting `K000159606` when LTM probers run non-`bigip` monitors locally without SNAT).
- **Selective connection mirroring:** enable mirroring only for long-lived/high-impact connections where LTM+AWAF licensing and 2-device limits are satisfied.

# 9. F5 official documentation verification summary

Official F5 TechDocs and MyF5 Knowledge Base sources verified for both the **current BIG-IP 17.5.x baseline** and the **confirmed `r2800` (`F5OS-A 1.8.0+`, no blade chassis) / BIG-IP 21.1.x+ rebuild**:

| Product area | Capability / Verified Fact | Version scope | Official F5 Source |
|---|---|---|---|
| **LTM / Monitoring** | Active monitor default `5s` interval / `16s` timeout (`3×interval + 1`); Virtual Location monitor + Priority Group Activation | 17.5.x & 21.1.x | [BIG-IP 21.1 Monitors Settings Reference](https://techdocs.f5.com/en-us/bigip-21-1-0/big-ip-local-traffic-manager-monitors-reference/monitors-settings-reference.html), [Monitors Concepts](https://techdocs.f5.com/en-us/bigip-16-0-0/big-ip-local-traffic-manager-monitors-reference/monitors-concepts.html) |
| **LTM / Pool & VS Failover** | Default `Action On Service Down = None`; use `Reject` for fast dead-socket cutoff; do not use `Reselect` on full-proxy HTTP/TLS VS; VS `Immediate Action On Service Down` stops TCP 3WHS false-greens | 17.5.x & 21.1.x | [MyF5 K15095](https://my.f5.com/manage/s/article/K15095), [MyF5 K40554304](https://my.f5.com/manage/s/article/K40554304) |
| **LTM / Maintenance Drain** | `Disabled` still accepts new persistent connections; `Forced Offline` blocks all new connections; `Receive Disable String` enables app-driven graceful drain | 17.5.x & 21.1.x | [MyF5 K13310](https://my.f5.com/manage/s/article/K13310), [MyF5 K12818](https://my.f5.com/manage/s/article/K12818) |
| **LTM / Routing Symmetry & SNAT** | `Auto Last Hop` handles local L2 return; L3 asymmetry & cross-site `X2A`/`X2B` require multi-IP **SNAT Pool** (avoids ~65k port exhaustion per IP / per TMM) + `XFF` (`Trust XFF` in AWAF); passive FTP SNAT caveat | 17.5.x & 21.1.x | [MyF5 K13876](https://my.f5.com/manage/s/article/K13876), [MyF5 K95573163](https://my.f5.com/manage/s/article/K95573163), [MyF5 K7820](https://my.f5.com/manage/s/article/K7820), [K8246](https://my.f5.com/manage/s/article/K8246), [K33355231](https://my.f5.com/manage/s/article/K33355231), [K35043645](https://my.f5.com/manage/s/article/K35043645), [K15249](https://my.f5.com/manage/s/article/K15249), [K4816](https://my.f5.com/manage/s/article/K4816) |
| **LTM / Persistence, OneConnect & Throughput** | `OneConnect` required for Keep-Alive cookie persistence (`K7964`, `K000149855`); LTM→AWAF OneConnect needs SNAT+`XFF` or `/32` mask (`K9816`, `K85357500`); stateless `CARP` (`K11362`); split-TCP `f5-tcp-wan`/`lan` (`K10281257`, `K37412295`); HTTP/2 full-proxy caveats (`K95032535`); `FastL4` (`K09948701`) | 17.5.x & 21.1.x | [MyF5 K7208](https://my.f5.com/manage/s/article/K7208), [K7964](https://my.f5.com/manage/s/article/K7964), [K83419154](https://my.f5.com/manage/s/article/K83419154), [K000149855](https://my.f5.com/manage/s/article/K000149855), [K9816](https://my.f5.com/manage/s/article/K9816), [K85357500](https://my.f5.com/manage/s/article/K85357500), [K11362](https://my.f5.com/manage/s/article/K11362), [K10281257](https://my.f5.com/manage/s/article/K10281257), [K37412295](https://my.f5.com/manage/s/article/K37412295), [K95032535](https://my.f5.com/manage/s/article/K95032535), [K09948701](https://my.f5.com/manage/s/article/K09948701) |
| **DSC / HA Failover** | Max 8 devices in Sync-Failover group; `Failover.NetTimeoutSec = 3s`; redundant TMM + mgmt failover paths; Gateway Fail-safe (`1s`/`11s` > `10s` TMM heartbeat); VLAN fail-safe defaults to `Reboot`; VE clock-advance/snapshot caution | 17.5.x & 21.1.x | [BIG-IP 21.1 HA Fail-safe](https://techdocs.f5.com/en-us/bigip-21-1-0/big-ip-system-essentials/high-availability-fail-safe.html), [MyF5 K7249](https://my.f5.com/manage/s/article/K7249), [K16049](https://my.f5.com/manage/s/article/K16049), [K10095](https://my.f5.com/manage/s/article/K10095), [K000161390](https://my.f5.com/manage/s/article/K000161390), [DSC Device Groups](https://techdocs.f5.com/en-us/bigip-14-1-0/big-ip-device-service-clustering-administration-14-1-0/working-with-device-groups.html) |
| **BIG-IP DNS (GTM) / Monitors & TTL** | Direct monitor default `30s`/`120s`; A-record pool default TTL `30s`; Global Availability & Topology LB; avoid duplicate LTM+GTM VS monitors | 17.5.x & 21.1.x | [MyF5 K15408](https://my.f5.com/manage/s/article/K15408), [K5431](https://my.f5.com/manage/s/article/K5431), [iControl REST GTM Pool A](https://clouddocs.f5.com/api/icontrol-rest/APIRef_tm_gtm_pool_a.html), [BIG-IP 17.5 DNS+LTM](https://techdocs.f5.com/en-us/bigip-17-5-0/big-ip-dns-implementations/integrating-big-ip-dns-into-a-network-with-big-ip-ltm-systems.html) |
| **BIG-IP DNS / Firewall NAT & Prober Pools** | NAT `Translation` disables VS Auto-Discovery (TCP 4353 iQuery required); explicit `Specific Prober Pool` prevents unroutable `big3d` fallback (`no route`) and local non-`bigip` MAC flapping | 17.5.x & 21.1.x | [MyF5 K14707](https://my.f5.com/manage/s/article/K14707), [K55502976](https://my.f5.com/manage/s/article/K55502976), [K8170](https://my.f5.com/manage/s/article/K8170), [K08433560](https://my.f5.com/manage/s/article/K08433560), [K000163083](https://my.f5.com/manage/s/article/K000163083), [K000159606](https://my.f5.com/manage/s/article/K000159606) |
| **BIG-IP DNS / Upgrade Order** | `big3d` is only backwards compatible: upgrade **BIG-IP DNS first**, then run `big3d_install` on monitored LTMs | 17.5.x & 21.1.x | [MyF5 K25923322](https://my.f5.com/manage/s/article/K25923322), [K13703](https://my.f5.com/manage/s/article/K13703), [K000161226](https://my.f5.com/manage/s/article/K000161226) |
| **AWAF / ASM Mirroring & WebSockets** | Mirroring requires licensed+provisioned LTM; max 2 devices; 3rd-device failover & failback reset connections; WebSocket profile required & incompatible with OneConnect | 17.5.x & 21.1.x | [BIG-IP 21.1 ASM Mirroring Limitations](https://techdocs.f5.com/en-us/bigip-21-1-0/big-ip-asm-implementations/connection-mirroring-with-asm/connection-mirroring-limitations.html), [MyF5 K84421441](https://my.f5.com/manage/s/article/K84421441), [K000151124](https://my.f5.com/manage/s/article/K000151124), [K000140381](https://my.f5.com/manage/s/article/K000140381) |
| **AWAF / ASM Policies, Sync & Live Update** | Parent/Child policies; 7-day Enforcement Readiness staging; ASM Sync-Only groups; `liveupdate.allowautoinstallonsecondary = false` default; Route Domains unsupported on standalone DNS | 17.5.x & 21.1.x | [BIG-IP 21.1 Policy Settings](https://techdocs.f5.com/en-us/bigip-21-1-0/big-ip-asm-implementations/changing-security-policy-settings.html), [Auto Sync](https://techdocs.f5.com/en-us/bigip-21-1-0/big-ip-asm-implementations/automatically-synchronizing-application-security-configurations.html), [MyF5 K82512024](https://my.f5.com/manage/s/article/K82512024), [Route Domains](https://techdocs.f5.com/en-us/bigip-17-5-0/big-ip-dns-implementations/configuring-big-ip-dns-on-a-network-with-one-route-domain.html) |
| **Confirmed Rebuild: `r2800` / `F5OS-A 1.8.0+` / 21.1.x** | 17.5.x EoTS Jan 1, 2029; 21.1.x EoTS May 5, 2029; BIG-IP Next 20.x EoTS Apr 30, 2025; 21.x drops iSeries/VIPRION/vCMP; `r2800` max 2 tenants (`F5OS-A 1.8.0+`), `8` cores / `24 GB` tenant RAM (`4 vCPU / 12 GB` min/tenant), single 480 GB NVMe SSD (~447 GB, no RAID-1), no STP / 1 LAG per VLAN, `.tar.bundle` format, ≥ 88 GB disk for 21.1.x; `cloud-init`; `platform-migrate validate`; experimental in-place upgrade in 21.1.x (full in 22.0.x); ACMEv2, OpenAPI 3.1, HTTP/3 WAF, MCP, hybrid PQC TLS, Multi-RPZ | 21.1.x / F5OS-A | [BIG-IP 21.1.0 New Features](https://techdocs.f5.com/en-us/bigip-21-1-0/big-ip-release-notes/big-ip-new-features.html), [Upgrade 21.1](https://techdocs.f5.com/en-us/bigip-21-1-0/big-ip-release-notes/big-ip-upgrade.html), [F5OS-A 1.8.4 Tenant Mgmt](https://techdocs.f5.com/en-us/f5os-a-1-8-4/f5-rseries-systems-administration-configuration/title-tenant-management.html), [MyF5 K15643](https://my.f5.com/manage/s/article/K15643), [K000163422](https://my.f5.com/manage/s/article/K000163422), [K82540512](https://my.f5.com/manage/s/article/K82540512), [K45191957](https://my.f5.com/manage/s/article/K45191957), [K000152319](https://my.f5.com/manage/s/article/K000152319), [K1689](https://my.f5.com/manage/s/article/K1689), [K000158849](https://my.f5.com/manage/s/article/K000158849) |


# 10. Maintainability and change-management variables

These variables are intentionally separate from the stable baseline so different operating models can be compared without changing the enterprise facts.

## M1 — change-management authority

Compare:

- native BIG-IP configuration management only;
- BIG-IQ Centralized Management as the deployment/source-of-truth layer;
- external infrastructure/configuration-as-code tooling where supported by enterprise standards.

For BIG-IQ-managed environments, evaluate:

- pre-deployment evaluation;
- snapshots;
- object-level/partial deployment;
- scheduled deployment;
- audit history;
- rollback from a known snapshot;
- drift caused by direct local BIG-IP changes.

Do not mix multiple sources of truth without an explicit ownership model.

## M2 — configuration synchronization mode

For LTM/GTM/WAF device groups, record:

- automatic sync;
- manual sync;
- Sync-Failover;
- Sync-Only;
- no native config sync / externally managed.

Important design consideration:

- automatic synchronization improves consistency but can propagate a bad configuration rapidly;
- manual/staged synchronization creates a validation gate but increases operational effort and drift risk;
- all members of a BIG-IP device group used for config sync must be version-compatible according to the deployed F5 release.

## M3 — WAF policy deployment strategy

Compare:

### M3A — direct synchronized production change

Change policy on the authoritative device/tool and synchronize to all production WAFs.

- simplest;
- fastest consistency;
- highest common-mode change blast radius.

### M3B — WAF staging / enforcement-readiness

Use Advanced WAF staging for new/changed entities/signatures so matching traffic is observed without immediately blocking it.

- reduces false-positive outage risk;
- requires observation and an explicit promotion/enforcement process.

### M3C — policy blue-green / canary

Maintain a current production policy and a candidate policy.

Use Policy Diff, inactive/staging policy copies, a dedicated WAF member/pool or limited test/canary traffic where the topology permits.

Promote only after:

- configuration diff review;
- functional test;
- security test;
- traffic observation;
- false-positive review;
- rollback validation.

## M4 — firmware/software upgrade strategy

BIG-IP software/firmware upgrades should be treated as node-out-of-service operations unless the version-specific F5 procedure explicitly states otherwise.

### HA pair / cluster

Use a release-specific F5-supported rolling sequence, typically based on:

1. verify config sync/HA health;
2. back up configuration;
3. move or drain traffic away from the node being changed;
4. upgrade the non-serving/standby node first where supported;
5. validate device, interfaces, monitors, policies and application path;
6. move traffic to the upgraded node;
7. observe;
8. upgrade the former active node;
9. resynchronize only using the version-supported process;
10. validate failover/failback.

Do not assume prolonged mixed-version operation inside one sync/failover group is supported.

### Independent WAF pool

Possible rolling pattern:

1. disable/drain one WAF pool member;
2. confirm active/persistent connections drain or hit the agreed maximum drain time;
3. upgrade the node;
4. validate policy/config/version;
5. re-enable with small/canary load if possible;
6. observe;
7. repeat one node at a time.

This is operationally easier when N-1 capacity is sufficient.

## M5 — LTM/GTM stagger strategy

Do not change both members of an HA pair or both sites concurrently for routine maintenance.

Preferred sequence:

- one node/device at a time;
- one site at a time;
- observe before continuing;
- retain the other site as an unmodified fallback where feasible.

**Mandatory F5 BIG-IP DNS / LTM upgrade order (`K25923322`, `K13703`):** Because the `big3d` agent is only backwards compatible, always upgrade **BIG-IP DNS (GTM) devices first**, immediately followed by running `big3d_install` to update `big3d` on monitored BIG-IP LTM devices before upgrading the LTM software. Use the version-specific F5 synchronization-group upgrade procedure because probing and config-sync constrain how long versions may differ.

## M6 — drain policy

Define a maximum drain policy per application class.

### Stateless web

- stop new connections/requests to the member;
- allow short in-flight requests to complete;
- force-close only after a bounded drain period.

### Stateful web

- preserve persistence/session routing while draining where required;
- verify session state is portable before final removal.

### Socket/WebSocket

- stop accepting new sockets;
- allow existing sockets to drain for a bounded period where business-appropriate;
- if the maintenance window cannot wait, trigger graceful reconnect behavior;
- confirm clients reconnect/re-authenticate/replay correctly.

### Non-web / L4

- use protocol-specific drain behavior;
- document whether existing long-lived connections can be terminated safely.

**F5 LTM member drain states (`K13310`, `K12818`):**

- **`Disabled` (`session user-disabled`):** stops new general connections, but **still accepts new connections matching an existing persistence session** (e.g., cookie/source-IP persistence).
- **`Forced Offline` (`session user-disabled state user-down`):** blocks **all** new connections (including persistent sessions) while letting existing active sockets finish — or immediately resets them if pool `Action On Service Down = Reject` is set (`K15095`).
- **`Receive Disable String` (`K12818`):** lets an application/WAF readiness endpoint self-signal `Up (disabled)` to drain cleanly during automated rolling waves without manual LTM intervention.

## M7 — maintenance capacity policy

For each topology define:

- minimum serving capacity during one-node maintenance;
- whether one additional failure can still be tolerated while maintenance is in progress;
- whether N-1 is enough or N-2 is required;
- whether cross-site capacity may be used during maintenance;
- whether maintenance is prohibited when the remote site/reserve is already degraded.

A component may be "highly available" in steady state but fail the maintainability objective if taking one node down leaves no headroom for another fault.

## M8 — change wave policy

Use independent waves such as:

1. non-production/test;
2. canary node/pool where topology permits;
3. one production node;
4. remaining nodes in the same site;
5. observation period;
6. second site.

For WAF security changes, attack-signature updates and policy changes may use a separate staging/promotion timeline from device firmware.

## M9 — rollback requirement

Before each material change identify:

- configuration snapshot/UCS backup;
- prior software boot volume/image;
- prior WAF policy;
- previous LTM/GTM config;
- rollback trigger;
- maximum time to decide rollback;
- who has authority to roll back.

Rollback should be tested, not only documented.

## M10 — monitoring/observability requirement

At minimum monitor:

- HA active/standby/traffic-group state;
- config-sync status;
- device CPU/memory/interface health;
- pool/member/virtual-server health;
- WAF policy/sync status;
- WAF violations/false-positive indicators;
- GTM wide-IP/pool/virtual availability;
- DNS probe/iQuery health;
- connection counts and drain progress;
- cross-site contingency activation;
- shared-reserve utilization;
- application readiness;
- end-to-end synthetic transactions;
- external versus internal user path health.

Prefer service-level dashboards that show both **component state** and **actual end-to-end application availability**.


# 11. Legacy inputs retained for confirmation

The older root-level architecture papers contained some useful requirements and planning assumptions. They are preserved here only where they may still influence the current analysis.

## L1 — user-impact threshold from earlier analysis

An earlier design document used a business rule that the service/trading operation could remain open only while **less than 25% of users were affected**.

This is **not currently treated as an invariant** because it has not been reconfirmed in the current baseline.

If the requirement still applies, promote it into `current_architecture_and_invariants.md` and analyse every external access failure domain against it.

Important consequence:

- four equal client/access pools imply one pool = 25%;
- a strict `<25%` rule would therefore fail if one complete equal-sized pool is lost;
- a firewall pair serving two such pools could create roughly 50% blast radius, depending on actual routing/population allocation.

Do not assume 25% from circuit count. Use the real user distribution.

## L2 — earlier candidate recovery bands

An earlier paper proposed these **acceptance-test planning bands**, not measured SLAs:

- local automated-path recovery: approximately **<=2 minutes p95**;
- alternate-ingress/site recovery: approximately **<=15 minutes p95**, only where the alternate application/data are already ready and reachable;
- manual DR/dependency recovery: no defensible upper bound until an application-specific RTO/runbook exists.

These values are **not current committed recovery objectives**. Keep them only as candidate benchmarks until business/application owners agree targets.

The current authoritative timing model remains T1-T7 in this file, and measured end-to-end service RTO should replace planning estimates.

## L3 — older topology-specific timing tables

The old V3/V4 failure matrices assumed a specific topology of clustered plus standalone GTM/LTM/WAF services and used release-era defaults such as GTM 30s/90s.

Those exact matrices are not current design inputs.

Retain only the general lessons:

- monitor choice materially changes recovery time;
- application-level health is stronger than port-only health;
- DNS cache/resolver behavior is part of site recovery;
- user/session recovery may exceed infrastructure recovery.

Use the current F5 timing assumptions and validate against the actual deployed BIG-IP version/configuration.
