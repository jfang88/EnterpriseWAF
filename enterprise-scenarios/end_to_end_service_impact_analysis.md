# End-to-End Service Impact and Recoverability Analysis

**Status:** Primary derived output for failure/recovery  
**Stable baseline:** [current_architecture_and_invariants.md](./current_architecture_and_invariants.md)  
**Target improvements:** [future_architecture_improvements.md](./future_architecture_improvements.md)  
**Changeable assumptions:** [analysis_variables_and_f5_assumptions.md](./analysis_variables_and_f5_assumptions.md)  
**Technical component matrix:** [common_failure_matrix.md](./common_failure_matrix.md)  
**Cross-site/dependency detail:** [cross_site_routing_and_dependency_recovery.md](./cross_site_routing_and_dependency_recovery.md)  
**Deployment/topology summary:** [deployment_options_resilience_summary.md](./deployment_options_resilience_summary.md)

## 1. Purpose

This is the primary business/service view of the failure analysis.

The question is not:

> What happens to the WAF?

The question is:

> What do users and applications experience when any part of the end-to-end service fails, how long is the interruption, and does the solution recover automatically, manually, partially, or not at all?

Every infrastructure failure must therefore be translated into:

- impact to **external human users**;
- impact to **external systems/API clients**;
- impact to **internal users/systems**;
- impact to dependent applications such as **App A -> App B -> App C**;
- outage/degradation duration;
- automatic versus manual recovery;
- cross-site versus local-only outcome;
- application-code/state requirements;
- residual risk after infrastructure recovery.

---

# 2. End-to-end service paths

## External human/API path

    external human/API client
      -> external/customer DNS
      -> enterprise GTM for published external service where delegated
      -> leased-line/VPN path
      -> edge firewall / application VIP
      -> LTM where present
      -> WAF where applicable
      -> platform/cloud firewall (CFW) where private-cloud hosted
      -> application ELB/service
      -> VM / Kubernetes / PaaS workload
      -> dependencies such as App B / App C
      -> data/state services

## Internal path

    internal user/system
      -> internal enterprise DNS
      -> optional delegation/conditional forward to GTM
      -> internal LTM/service VIP
      -> internal firewall
      -> platform/cloud firewall (CFW) where private-cloud hosted
      -> ELB/service VIP
      -> application
      -> dependencies such as App B / App C
      -> data/state services

## Internal application dependency path

    App A
      -> internal enterprise DNS
      -> optional GTM lookup for internal B service
      -> B service VIP / endpoint
      -> platform/cloud firewall (CFW) where B is private-cloud hosted
      -> B ELB/service endpoint
      -> App B
      -> optional internal DNS/GTM lookup for C
      -> App C

## Internal firewall boundary

Internal users, desktops, internal enterprise DNS and the internal LTM/service VIP are outside the private cloud. Private-cloud access crosses a distinct **internal firewall** before the **private-cloud CFW**. These must be analysed as separate failure domains: an internal-firewall outage can isolate internal users from otherwise healthy private-cloud applications while external/extranet access may remain healthy; a CFW outage can affect both external and internal paths after they reach the private-cloud boundary.

The external and internal namespaces are separate. A DNS/GTM problem can therefore affect:

- external users only;
- internal users/applications only;
- or both, depending on which namespace, delegation and GTM service is involved.

The internal path may bypass the internet-facing WAF layer.

Therefore a WAF outage may be:

- an **external-user outage**;
- while the application itself remains healthy;
- while internal users remain fully operational.

That distinction must be visible in every scenario.

---

# 3. User-impact classifications

Use the following service-impact labels.

| Label | Meaning |
|---|---|
| **No impact** | Users/applications continue normally |
| **Transient retry** | One or more requests/connections may fail, but automatic retry/reconnect restores service |
| **Partial outage** | Only a user population, protocol, application function or dependency is unavailable |
| **Degraded service** | Service continues through remote/degraded path with extra latency/capacity risk |
| **Session loss** | Service returns but user must re-authenticate/restart workflow |
| **Connection loss** | Long-lived connection resets and must reconnect |
| **Application outage** | Application is unavailable to the affected actor |
| **Tenant-wide outage** | Several applications/users in the tenant lose service |
| **Site-level outage** | Services require alternate-site recovery |
| **Manual recovery required** | Infrastructure cannot fully restore service without operator/application action |
| **Not recoverable by infrastructure alone** | Application/data/protocol design prevents successful automatic recovery |

---

# 4. Timing model: what users actually experience

Infrastructure detection time is only one part of user-visible outage.

Model total service interruption as:

    detection
      + infrastructure failover / traffic steering
      + DNS/cache convergence where used
      + new TCP/TLS/application connection
      + application retry/re-authentication
      + session/state/dependency recovery
      + manual startup where required

Timing shorthand from the assumptions file:

| ID | Meaning | Typical modelling basis |
|---|---|---|
| **T1** | BIG-IP HA peer/device failover | seconds-scale; approximately 3+ sec peer-loss detection plus network convergence |
| **T2** | LTM/WAF pool-member detection | commonly around configured monitor timeout; many F5 monitor defaults around 5s interval / 16s timeout |
| **T3** | Direct GTM monitor detection | commonly much slower; example defaults around 30s interval / 120s timeout |
| **T4** | DNS/site convergence | health detection + GTM decision + TTL/cache + re-resolution + alternate-site readiness |
| **T5** | Warm/cold/manual recovery | minutes or longer depending operational procedure |
| **T6** | Application recovery | retry/reconnect/re-auth/state/replay/reconciliation |
| **T7** | Failback | controlled restoration to preferred path/site |

These are not guaranteed SLAs.

For each service, measured RTO should eventually replace modelled timing.

## 4.1 Recovery-time decomposition

The earlier architecture analysis used a useful decomposition that remains valid and is now retained here:

```text
T_service_recovery
  = T_detect
  + T_path
  + T_DNS       (only where DNS/site selection changes)
  + T_retry
  + T_auth
  + T_restore
  + T_ready     (only where alternate app/data must become ready)
```

Where:

- **T_detect** — infrastructure/application/heartbeat detects the fault;
- **T_path** — HA, pool withdrawal, routing or traffic steering converges;
- **T_DNS** — authoritative DNS decision, resolver/client cache and re-resolution;
- **T_retry** — HTTP/API retry or socket reconnect/backoff;
- **T_auth** — re-authentication or session restoration;
- **T_restore** — workflow/subscription/message replay/snapshot/business reconciliation;
- **T_ready** — passive application, dependency, state or data becomes safe to serve.

Only add terms that are actually sequential. If steps overlap, measure the real end-to-end recovery rather than double-counting.

Measure p50/p95/p99 separately for:

- external human-user populations;
- external API/system clients;
- internal users/systems;
- App A -> B -> C dependency transactions;
- stateless HTTP;
- stateful sessions;
- WebSocket/long-lived traffic.

The acceptance measure is the first successful **business transaction**, not the time an F5 component reports green.

## 4.2 Validated recovery timing matrix

The table below makes the timing assumptions explicit. Values are **planning boundaries derived from documented defaults**, not guaranteed SLAs.

Important distinction:

- if the **service VIP stays the same** and LTM can select another healthy member, there is **no DNS TTL term**;
- if recovery requires **GTM to return a different VIP/site**, add GTM health detection + residual DNS TTL/cache + client retry/re-resolution;
- existing TCP/TLS/WebSocket connections are not moved merely because DNS changes or a pool member is marked down.

| Failure / recovery use case | Infrastructure detection / steering | DNS TTL involved? | User-visible planning boundary | What existing clients experience |
|---|---|---|---|---|
| **One BIG-IP HA peer fails; service VIP remains on surviving peer** | HA peer loss is seconds-scale; F5 logs commonly show ~3.1s peer timeout before failover, plus traffic-group/network convergence | **No** | roughly **3s+ + T6** for affected flows; measure real convergence | Unaffected/mirrored connections may survive; other affected connections can reset/retry |
| **One independent WAF member behind LTM fails (W1/W3)** | LTM active monitor commonly **5s interval / 16s timeout** | **No** | new traffic: **up to ~16s** before member withdrawal, then healthy member; affected connection adds T6 | Requests during detection window can hit failed member; established connection on failed WAF may reset or wait on app/TCP timeout |
| **One WAF cluster member fails (W2/W4)** | WAF HA peer failover is seconds-scale; LTM may see the cluster service remain healthy | **No** | usually **seconds-scale + T6** for affected connections | Supported mirroring may preserve some sessions; otherwise reconnect |
| **One CFW HA member fails; same local application path remains** | CFW HA/state/route convergence; product-specific | **No** | target **seconds-scale + T6** if HA works; actual value **TBD/measure** | Existing sockets survive only if firewall/NAT/session state survives; otherwise reconnect |
| **Whole local CFW service fails; ELB/app healthy; GTM health sees through-path failure** | withdraw site/path and use alternate CFW/site | **Yes if site/VIP changes** | **~46s + T6** illustrative fast-health case or **up to ~150s + T6** direct-GTM-default case; add T5 if DR app not ready | Existing connections through failed CFW are lost; cached clients may retry old VIP until TTL expires |
| **CFW fails but health remains false-green** | front-end remains advertised although app path is broken | DNS may continue returning bad site | **potentially unbounded** until through-path readiness/operator detects failure | Clients can repeatedly reconnect to the same broken site/path |
| **One app/backend member behind LTM fails** | If using equivalent LTM active monitor defaults: **up to ~16s**; other ELB/platform monitor timing must be measured separately | **No** if service VIP is stable | **monitor timeout + T6** | New traffic goes to healthy member after withdrawal; in-flight request may fail |
| **All local WAF members fail but local LTM can use preconfigured remote WAF (X2A)** | local LTM detects loss/priority threshold, commonly on **~16s-class** monitor timing | **No** | approximately **~16s + T6** if remote WAF is already healthy/policy-ready | Existing WAF connections break/reconnect; no site DNS move required |
| **All local WAF members fail and no cross-site WAF is available** | must recover local WAF or trigger site/front-end recovery | **Yes if site/VIP changes** | with direct GTM default monitor: **up to ~120s health + up to 30s residual TTL = ~150s + T6**; with faster LTM/iQuery health and prompt propagation, an illustrative case is **~16s + up to 30s = ~46s + T6** | Cached clients can keep using old Site 1 VIP until TTL/cache expires; existing connections need failure/retry before re-resolution |
| **Whole local LTM pair fails; use Site 2 front-end (X2B/X2C)** | GTM/site health withdrawal | **Yes** | same site-change boundary: roughly **~46s + T6** in a fast LTM-health-informed model, or **up to ~150s + T6** with default direct GTM monitor timing | Existing connections to Site 1 fail; cached clients may retry Site 1 until TTL/cache expires |
| **Whole Site 1 fails; Site 2 app already ready** | GTM detects Site 1 unavailable, returns Site 2 | **Yes** | **~46s + T6** illustrative fast-health case; **up to ~150s + T6** default-direct-monitor case | New uncached clients recover first; cached clients are slower; sockets reconnect/re-auth/replay |
| **Whole Site 1 fails; Site 2 app requires manual startup** | same DNS/site timing, but application readiness adds T5 | **Yes** | **T5 + ~46–150s + T6**, with T5 potentially minutes or longer | Infrastructure may be ready before business service is ready |
| **App B1 fails behind stable internal LTM service VIP; B2 reachable** | local LTM member monitor, commonly **up to ~16s** | **No** | approximately **~16s + App A retry T6** | A may see failed/slow calls during detection; new calls use B2 after withdrawal |
| **App B1 fails and A discovers B via internal DNS/GTM** | GTM/internal service health detection | **Yes** | direct GTM default model: **up to ~150s + T6**; faster LTM/iQuery-informed model can approach **~46s + T6**, subject to application DNS cache | A can keep old B1 address/connection until its own cache/connection refreshes; TTL alone does not force re-resolution |
| **External namespace GTM answer changes Site 1 -> Site 2** | authoritative answer changes after health withdrawal | **Yes: default GTM pool TTL 30s** | add **0–30s residual TTL** after the health decision, plus T6 | Newly resolving users get Site 2; cached users may still hit Site 1 |
| **Internal namespace/GTM answer changes B1 -> B2 or Site 1 -> Site 2** | same principle, but internal resolver/app cache also matters | **Yes if GTM/DNS changes endpoint** | add **0–30s GTM TTL by default** plus any internal/app caching and T6 | application connection pools/JVMs may retain old address longer; must test |
| **Bad WAF/LTM policy/configuration** | health monitors may remain green | Usually **No useful DNS fix** | **T5 rollback/manual recovery**; potentially unbounded without detection/rollback | Users can remain down despite all devices being physically healthy |
| **Application listener green but business function broken** | port/IP monitor may not detect it | DNS may keep returning bad site | potentially **unbounded** until readiness monitor/operator detects it | Users get errors/hangs; classic false-green condition |
| **WebSocket/long-lived connection loses any stateful hop** | underlying infrastructure timing as above | only if endpoint/site changes | **infra timing + reconnect/re-auth/resubscribe/replay T6** | TTL does not migrate the live socket; app logic determines real recovery |

### 4.3 What the 30-second TTL does and does not mean

A default 30-second GTM pool TTL means:

```text
GTM returned Site 1 VIP at t=0
failure happens at t=1
GTM later decides Site 1 is down
resolver/client may still legally use cached Site 1 VIP
until the remaining TTL expires
```

But:

```text
existing TCP/WebSocket to Site 1
    !=
DNS cache entry
```

An established connection can remain pinned to the failed path until it receives a reset, detects a dead path, or reaches an application/TCP timeout. Only then does reconnect/re-resolution behavior matter.

Conversely, if the endpoint does **not** change:

```text
same LTM VIP
   |
failed member X
healthy member Y
```

DNS should not be part of recovery. LTM health withdrawal and client retry are the relevant timing terms.

### 4.4 CFW changes the preferred recovery target

Adding CFW as an explicit layer changes the recovery decision in two ways.

**1. A single CFW member failure should remain local.**

If the CFW HA service survives:

```text
same DNS answer / same F5 VIP
        |
        v
surviving CFW peer
        |
        v
same ELB/application
```

Do **not** invoke GTM/site failover merely because one CFW appliance/member failed. The desired outcome is seconds-scale local HA plus T6 only for connections whose firewall state was lost.

**2. Complete CFW failure invalidates remote-WAF route-back to the same site.**

```text
Site 1 WAF tier fails
  -> remote WAF can help if Site 1 CFW is healthy

Site 1 CFW fails
  -> remote WAF still cannot reach Site 1 ELB/app through the failed CFW
  -> use alternate CFW path or Site 2 application path
```

Therefore the service-health decision must distinguish:

- WAF failure with healthy CFW/app: X2A can be fast (~16s-class + T6);
- CFW failure with healthy app behind it: X2A is not sufficient; likely site/app path recovery (~46–150s + T6 if health is correctly detected);
- CFW false-green: potentially unbounded until through-path monitoring detects the failure.

This strengthens the recommendation for an application-readiness signal that represents the full delivery path through CFW.

---

# 5. Primary end-to-end failure matrix

The table below intentionally describes the **service/user outcome first**.

| Scenario | External human users | External API/system clients | Internal users/systems | App A/B/C dependency impact | Indicative user-visible interruption | Recoverable? |
|---|---|---|---|---|---|---|
| **External namespace / external GTM resolution fails** | New external sessions/name lookups fail; existing connections may continue until reconnect/name refresh | External API clients needing new DNS resolution fail/retry; cached/existing connections may continue | **No direct impact** if internal namespace is independent | App A/B/C internal calls may continue if they use internal DNS/GTM | DNS recovery + cache/TTL; potentially T3/T4 depending design | **Yes** if external DNS/GTM redundancy works; otherwise external-only outage |
| **Internal enterprise DNS fails** | External users may remain fully healthy | External API may remain healthy | Internal users cannot resolve new internal names unless cached | App A/B/C dependency calls using internal DNS can fail/cascade | internal DNS recovery + application cache/retry | **Conditional**; not solved by WAF/LTM HA |
| **Internal DNS delegation/forward to GTM fails** | External namespace may remain healthy | External API may remain healthy | Internal endpoints delegated to GTM fail to resolve; directly resolved internal names may still work | Only dependencies using delegated GTM names fail; can create selective A/B/C outage | internal DNS/forwarder recovery + T6 | **Conditional**; depends on redundant forwarding/GTM path |
| **Internal GTM is up but returns unreachable/wrong-site internal endpoint** | External users may be unaffected | External API may be unaffected | Internal users receive timeout/connection failure | App A may fail B calls despite healthy B elsewhere | health detection + DNS/cache + T6 | **Recoverable only with correct reachability-aware health/selection and re-resolution** |
| **One leased line fails** | Only users routed through that path lose/retry service; other external populations remain healthy | Same for API clients on failed path | Usually no impact | Usually no impact unless dependency path shares line | carrier/routing recovery; not fundamentally a WAF issue | **Yes**, if alternate network path exists; otherwise partial population outage |
| **One edge-firewall node fails** | Usually transient or no visible impact if firewall HA works | Same | Usually no impact | No app dependency impact | firewall HA convergence | **Yes** through firewall HA |
| **Whole edge-firewall pair/path fails** | External users on that ingress may be unavailable even while app is healthy | Same | Internal may remain healthy | Dependencies may remain healthy | routing recovery or T4 if alternate site/VIP used | **Conditional** on alternate external reachability |
| **One LTM node fails** | Usually transient/no impact after HA takeover | Same | If internal path uses same LTM, similar transient impact | If dependency VIP uses failed LTM pair member, HA takeover | T1 + connection recovery | **Yes** if HA peer healthy |
| **Whole local LTM pair fails** | External path through that LTM is down | Same | Internal impact depends on whether it shares this LTM | App A->B may be affected if dependency service VIP uses same pair | X2B/T4 or site recovery; could be longer if app DR manual | **Yes only with another front-end/site path** |
| **One WAF member fails in W1/W3** | Some requests/connections on failed WAF may reset; new traffic uses healthy WAF | Same | Usually no impact if internal bypasses WAF | Usually none unless east-west flow uses WAF | T2 + T6 for affected sessions/connections | **Yes**, assuming remaining WAF capacity and app retry/reconnect |
| **One WAF cluster member fails in W2/W4** | Usually minimal; supported mirroring may reduce connection loss | Same | Usually no impact if bypassing WAF | Usually none | T1/T2 + T6 where connection resets | **Yes**, first clustered failure |
| **All local WAF capacity fails; LTM healthy** | External service unavailable until alternate WAF/site used | Same | Internal may remain fully healthy | Application/dependencies may remain healthy | X2A can be T2+T6; otherwise T4/T5/T6 | **Yes** if remote WAF or alternate site is pre-ready; **No automatic recovery** if neither exists |
| **Local LTM + WAF tier fails; application healthy** | External users lose primary front-end | Same | Internal may remain healthy | App A/B/C may continue internally | X2B = T4+T6; full DR may add T5 | **Conditional**: remote front-end route-back or full site recovery |
| **Bad WAF policy pushed to all WAFs** | External application may appear fully down although hardware is healthy | Same | Internal users may remain healthy if bypassing WAF | Internal dependencies may remain healthy | rollback/change recovery = T5, not device failover | **Only by policy rollback/independent unaffected path** |
| **Application VM/pod fails** | Usually brief/transient if ELB has healthy members | Same | Same | Downstream callers retry another instance | backend monitor + T6 | **Yes** if app is horizontally resilient |
| **One CFW member/node fails but CFW HA survives** | Usually transient/no impact if platform firewall HA/state/routing converges correctly | Same | Internal calls traversing CFW may see same transient impact | App A/B/C calls through the CFW may retry | **CFW HA/route convergence + T6; product/config specific, measure** | **Yes** if CFW HA is correctly designed |
| **Whole local CFW service/context fails; ELB/app healthy** | External app path fails after WAF even though app is healthy | Same | Internal users/apps traversing the same CFW also fail | Several apps/dependencies behind the CFW can fail together | local CFW restoration or cross-site/site recovery; **TBD/T5/T4 + T6** depending design | **Conditional**; this can be a tenant/platform-wide blast radius |
| **Application ELB/service tier fails** | Application unavailable through that site/path | Same | Internal users may also fail if same ELB used | Dependent apps may fail/cascade | alternate ELB/site + T4/T6 | **Conditional** on redundant application service path |
| **App is listener-up but business-not-ready** | Users get errors/hangs despite green infrastructure | Same | Same | Dependencies may propagate failure | potentially unbounded if only IP/port health is used | **No reliable auto recovery** without application-readiness health |
| **Session/state store fails** | Users may be logged out, lose workflow or receive errors | Same | Same | Multiple apps may fail together if store shared | data/state recovery + T6; often much longer than F5 failover | **Not by WAF/LTM/GTM alone** |
| **App B fails; App A is healthy; no cross-site B routing** | Users of App A functions needing B may fail; unrelated A functions may remain | API callers of A may see dependency errors | Internal A users see same business failure | A/C/etc. may cascade if all depend on B | application timeout/retry, then potentially T4/T5 if whole apps are failed over | **Poorly recoverable** if A is hard-coded/local-only to B1 |
| **App B fails; App A is healthy; XD1 remote B enabled** | Users may see transient delay/retry but A stays up | Same | Same | A/C remain Site 1 and use B2 | dependency monitor + application retry; often T2/T6 class rather than site failover | **Yes**, if B2 state/capacity and A retry logic are compliant |
| **App B is slow/hung, not hard down** | Users may experience long waits/timeouts | API clients may exhaust connection pools | Internal same | A/C can thread-starve and cascade | determined by app timeout/circuit breaker, not F5 failover | **Only if app has bounded timeouts/circuit breaking** |
| **Inter-site link fails while local services healthy** | No impact if local path does not depend on remote resources | Same | Same | Local dependencies remain healthy; remote fallback unavailable | none for local service | **Yes**, provided health logic does not falsely withdraw local site |
| **Inter-site link fails while using remote WAF or B2** | Existing degraded recovery path fails | Same | Internal/dependent apps using remote service also fail | App A may lose B2; remote WAF route-back disappears | route detection + T4/T6 or local restoration | **Conditional**, second failure while degraded |
| **Primary site front-end fails; primary app healthy; X2B available** | Users move to Site 2 ingress then route back to Site 1 app | Same | Internal may continue directly to Site 1 app | Dependencies can remain Site 1 | T4 + T6 | **Yes**, but degraded split-site state |
| **Primary application fails; front-end healthy** | Users cannot be restored by WAF/LTM failover alone | Same | Internal also affected | Dependencies/callers may cascade | application/site recovery = T4 + T5 + T6 depending readiness | **Only through application/DR recovery** |
| **Whole Site 1 fails; Site 2 app already ready** | New/retrying users move to Site 2 | Same | Internal users require Site 2 route/DNS/service path | A/B/C must all have compatible Site 2 state/dependencies or selective remote dependency paths | T4 + T6 | **Yes**, if Site 2 is genuinely ready |
| **Whole Site 1 fails; Site 2 app stopped/manual DR** | Full outage until application/dependencies are started and advertised | Same | Same | A/B/C startup order/dependencies can dominate RTO | T5 + T4 + T6; potentially minutes or longer | **Yes manually**, but not short-RTO automatic recovery |
| **WebSocket/socket path component fails** | Existing connection resets unless supported HA/mirroring preserves it | Same for long-lived API/socket clients | Same where applicable | App-to-app sockets also reset | infrastructure recovery + T6 | **Yes only if reconnect/re-auth/replay logic exists** |
| **Non-web service bypassing WAF; WAF fails** | Not applicable unless user consumes WAF-protected companion service | Non-web client should be unaffected | Internal/system traffic unaffected | No impact | none | **Yes / no impact** |
| **Non-web service LTM/route/backend fails** | Protocol-specific | Protocol-specific reconnect | Internal/system impact depends on protocol | Dependencies may fail | T1/T2/T4 + protocol-specific T6 | **Conditional** on client retry/reconnect semantics |

---

## 5.1 Shared multi-tenant service failures

When LTM or WAF capacity is shared across tenants, the same hardware failure can have a larger service impact than in a dedicated topology.

| Shared failure | Dedicated-tenant outcome | Shared-service outcome | Recovery implication |
|---|---|---|---|
| one shared WAF node | one tenant normally unaffected unless its own pool loses capacity | all tenants share reduced capacity | prove aggregate N-1 capacity |
| two shared WAF nodes | dedicated failure stays within one tenant | several/all tenants can become capacity constrained or lose WAF service | prove aggregate N-2 or invoke cross-site capacity |
| shared WAF policy/config error | one tenant if policy boundary is dedicated | several/all tenants may fail simultaneously | topology redundancy does not fix common-mode policy error |
| shared WAF pool lost | one tenant loses local WAF tier | four-tenant external ingress can fail together | Site 2/cross-site WAF must absorb aggregate load |
| shared LTM service lost | tenant-specific pair only affects one tenant | all tenants behind shared LTM lose local ingress | much larger GTM/site failover blast radius |
| shared reserve exhausted | dedicated tenants remain independent | one tenant's recovery can consume another tenant's contingency capacity | reserve admission/prioritization required |

For a four-tenant shared pool, cross-site recovery must be sized for the **credible simultaneous tenant blast radius**, not just the largest single tenant.

A shared pool can reduce device count and improve aggregate utilisation, but the service RTO may worsen if one shared common-mode failure causes multiple applications/tenants to perform GTM/site failover together.

## 6.1 Namespace-specific failure interpretation

A DNS failure should not be reported generically as "GTM down" without identifying the namespace and actor.

Examples:

    External namespace failure
      -> external users/API may fail
      -> internal users may continue
      -> App A/B/C internal calls may continue

    Internal namespace failure
      -> external users may continue
      -> internal users may fail
      -> App A/B/C may fail even though all external WAF/LTM paths are healthy

    Internal GTM/delegated-name failure
      -> only selected internal services may fail
      -> directly resolved internal names can remain healthy
      -> dependency blast radius depends on which applications consume the affected internal endpoint

For every DNS/GTM failure record:

- namespace: external / internal / both;
- resolver path;
- GTM delegation/forwarding path;
- returned endpoint type;
- reachability from the requester;
- TTL/cache behavior;
- application re-resolution behavior;
- affected users/applications.

# 6. Cross-site capability changes the user story

## Local-only design

With **X1 local-only**, loss of the local delivery tier can force a much larger recovery event even while the application itself is healthy.

Example:

    local WAF tier fails
      -> external users lose access
      -> internal users may remain healthy
      -> app itself remains healthy
      -> without X2A/X2B:
            recover local WAF
            OR fail application/site

This can convert a roughly **16-second-class local pool withdrawal** into a **~46–150 second DNS/site recovery event plus application recovery**, or into a minutes-long manual DR event if the passive application is not already ready.

### Failure amplification when cross-site routing is unavailable

| Initial failure | Smallest recovery if cross-site capability exists | Without cross-site routing | Cascading effect |
|---|---|---|---|
| One WAF member | local pool/cluster recovery | same local recovery | normally contained |
| Entire local WAF tier; app healthy | X2A remote WAF, ~16s-class + T6 | local repair or move whole service/site via GTM | a WAF failure becomes external service/site recovery |
| Local LTM/WAF front-end loss; app healthy | X2B remote front-end route-back | full application/site failover | healthy application is moved because delivery tier failed |
| B1 dependency fails; A1 healthy | XD1 route A1 to B2, ~16s-class + retry when using stable service VIP | A1 loses dependency or A must fail site | B failure can make A/C/D appear unhealthy |
| B1 fails and A/C/D all depend on B | all remain local and use B2 if capacity/state permit | multiple applications can fail together | many apps hit Site 2 simultaneously; DR capacity/reconnect storm risk |
| B2 exists but no route from A1 | route can use B2 if approved | B2 is unusable despite being healthy | no benefit from remote capacity; A outage persists |
| Site 1 WAF maintenance with local capacity exhausted | temporary remote WAF capacity | maintenance can consume last local redundancy | planned change plus one fault becomes outage |
| Site 1 application member fails | local ELB/member recovery | local ELB/member recovery | no cross-site required if local app capacity remains |
| Whole Site 1 CFW fails; ELB/app healthy | alternate CFW/site path if engineered | healthy ELB/app becomes unreachable; GTM may move whole application/site | **CFW failure amplification:** shared CFW outage can make many apps look failed and trigger multiple site moves |
| Whole Site 1 fails | full Site 2 recovery | same full Site 2 recovery | cross-site route-back cannot help a lost site |

The design objective is therefore to prevent **failure-domain escalation**:

```text
WAF failure
  X should not become application DR

B dependency failure
  X should not become A + C + D site failover

single local delivery failure
  X should not become tenant-wide DNS/site movement
```

Cross-site capability should not be mandatory for normal service, but where it is safe it can keep the recovery domain proportional to the original failure.

## Remote-WAF route-back: X2A

    external user
      -> Site 1 firewall
      -> Site 1 LTM
      -> Site 2 WAF
      -> route back
      -> Site 1 application

Expected user outcome:

- external users may see transient failed requests/connections;
- internal users normally see no impact;
- application remains Site 1;
- no DNS site move;
- recovery can be closer to local LTM monitor timing plus application reconnect.

This is particularly valuable when Site 1 application DR is slow/manual.

## Remote front-end route-back: X2B

    external user
      -> GTM selects Site 2
      -> Site 2 firewall/LTM/WAF
      -> route back
      -> healthy Site 1 application

Expected user outcome:

- external users experience DNS/site-convergence interruption;
- internal users may continue using Site 1 directly;
- application does not have to start in Site 2;
- service is degraded because the request path now spans sites.

## Conventional site failover: X2C

    external/internal users
      -> Site 2 front-end
      -> Site 2 application

Expected user outcome depends heavily on:

- whether Site 2 app is already running;
- data/state readiness;
- dependency readiness;
- DNS/client cache;
- socket reconnect;
- application-specific recovery.

---

# 7. App A -> App B -> App C cascade analysis

The application dependency graph is often more important than the WAF topology.

Example:

    App A
      |
      v
    App B
      |
      v
    App C

## No dependency failover

If B1 fails and A1 is hard-coded to B1:

    B1 fails
      -> A1 requests hang/fail
      -> A may become unhealthy
      -> users of A see outage
      -> A may fail to Site 2
      -> C/D/E that also depend on B1 may fail
      -> Site 2 receives many applications at once
      -> capacity surge / cascade

User story:

- infrastructure for A may be completely healthy;
- users still see A as failed because one dependency is unavailable;
- failing A's WAF/LTM/site does not fix the root cause if B dependency design is unchanged.

## No cross-site dependency path: cascading service failure

Assume A1, C1 and D1 all consume B1 and there is no usable route/service abstraction to B2.

```text
B1 fails
  |
  +--> A1 waits for timeout / retries B1
  +--> C1 waits for timeout / retries B1
  +--> D1 waits for timeout / retries B1
           |
           v
   threads / connection pools fill
           |
           v
   A/C/D readiness may fail
           |
           v
   GTM may withdraw multiple application VIPs
           |
           v
   multiple apps move to Site 2
           |
           v
   Site 2 receives reconnect + login + dependency surge
```

The initial B1 fault may therefore cascade through several timing layers:

1. each application's own connect/read timeout;
2. retry/backoff period;
3. readiness-health failure;
4. GTM site withdrawal;
5. residual DNS TTL (up to ~30s at the documented default);
6. client reconnect/re-login;
7. Site 2 B/database/state readiness.

This can turn a dependency-member failure that could have been a **~16s-class local service-VIP event** into a **~46–150s+ site recovery**, or R4/manual recovery if Site 2 dependencies are not already ready.

Site failover may also fail to solve the root problem if Site 2 A/C/D still resolve B incorrectly or if B2 depends on an unavailable C/data service.

## Local-preferred / remote-fallback dependency

    A1 -> B service VIP
             |
             +-- B1 preferred
             +-- B2 remote fallback

Then:

    B1 fails
      -> service VIP withdraws B1
      -> A retries/connects to B2
      -> A remains in Site 1
      -> users experience transient delay/retry instead of full A outage

This is a major resilience improvement.

## App C dependency

If B depends on C, B2 is only a valid recovery target if B2 can also reach a healthy compatible C.

Therefore dependency recovery must test the **whole dependency chain**, not one hop.

For each App A/B/C chain record:

- preferred local dependency;
- alternate dependency;
- health signal;
- retry timeout;
- connection refresh behavior;
- state/data locality;
- capacity;
- cross-site route;
- failure of the fallback path;
- user-visible behavior when dependency is degraded.

---

# 8. Application-type-specific outage expectations

## Stateless web

If designed correctly:

- a failed WAF/LTM/backend member should normally cause a transient failed request or short retry window;
- users should not lose session/workflow state;
- local pool recovery should generally be seconds-to-monitor-timeout scale.

If state is actually local:

- reclassification to stateful is required;
- users may be logged out or lose workflow;
- effective outage is longer than infrastructure failover.

## Stateful web

Infrastructure may recover in seconds while users remain broken.

Expected user impact may include:

- forced re-login;
- lost workflow;
- transaction reconciliation;
- inability to use remote site until state/data is consistent.

State portability is therefore a hard recovery dependency.

## WebSocket / long-lived

Expected during many failures:

    connection resets
      -> client reconnects
      -> re-authenticates
      -> resubscribes
      -> checks sequence
      -> replays/fetches missed state
      -> resumes

Without that application logic:

- the infrastructure can be healthy again;
- users can still remain disconnected indefinitely;
- the service is not end-to-end resilient.

## Non-web/L4

The WAF may be irrelevant.

Recovery must be expressed in protocol terms:

- TCP reconnect;
- SFTP reconnect/restart;
- middleware consumer reconnect;
- database reconnect/failover;
- transaction replay/reconciliation.

---

# 9. Recoverability classification

Use this classification for every application/service.

| Class | Meaning |
|---|---|
| **R0 — no user impact** | Redundancy hides the failure |
| **R1 — automatic local recovery** | Local HA/pool/ELB recovers automatically |
| **R2 — automatic cross-site component/dependency recovery** | Remote WAF, remote front-end route-back or remote dependency recovers service |
| **R3 — automatic site/application recovery** | Alternate site app is ready and GTM/service routing recovers |
| **R4 — manual recovery** | Application/startup/routing/config/operator action required |
| **R5 — not recoverable with current design** | Missing application/state/network capability prevents valid recovery |

The target should be to move common single failures toward **R0/R1**, dependency failures toward **R1/R2**, and reserve R3/R4 for genuine site/application disasters.

---

# 10. Solution-level examples

## Example 1 — one WAF fails

Infrastructure result:

- W1/W3: LTM removes member;
- W2/W4: cluster peer continues.

User result:

- external stateless users: usually transient retry;
- external stateful users: possible session interruption depending persistence/state;
- external WebSocket users: affected sockets reconnect;
- internal users: usually no impact if WAF bypassed;
- App A/B/C: normally no impact unless dependency path traverses same WAF.

Indicative timing: independent LTM-balanced WAF member **up to ~16s + retry**; clustered peer failure **seconds-scale + retry**. DNS TTL is not involved while the service VIP remains stable.

Overall: **recoverable automatically**, typically R0/R1.

## Example 2 — entire local WAF service fails but application healthy

Without cross-site WAF:

- external users: outage;
- internal users: may remain healthy;
- app: healthy;
- recovery: local repair or full site/application failover.

With X2A:

- external users: short interruption/reconnect;
- internal users: no impact;
- app remains local;
- remote WAF becomes temporary inspection path.

With X2A, indicative recovery can remain around the **local ~16s monitor class + T6** with no DNS change.

Without X2A, the same healthy application can require GTM/site recovery: approximately **~46s + T6** in a fast LTM-health-informed model or **up to ~150s + T6** using default direct GTM monitor + default DNS TTL assumptions; add T5 if the DR application is not ready.

Overall: X2A can turn a potentially R3/R4 event into **R2**.

## Example 3 — App B fails

Without XD1:

- external/internal users of A functions needing B fail;
- App A infrastructure may still be healthy;
- several apps may cascade;
- site failover may not solve root cause.

With XD1 and compliant apps:

- A retries B service;
- traffic moves to B2;
- A remains local;
- user impact is transient/degraded latency.

If B is behind a stable internal LTM service VIP, the infrastructure part can remain approximately **~16s-class + App A retry**, without DNS TTL.

If A uses DNS/GTM to move B1 -> B2, add GTM detection + residual DNS TTL and application re-resolution; this can be **~46–150s + T6** depending on the health model and cache behavior.

Overall: XD1 can turn application cascade into **R1/R2**.

## Example 4 — complete Site 1 loss

If Site 2 is ready:

- external clients re-resolve/reconnect;
- internal users route to Site 2;
- App A/B/C use Site 2 or valid remote dependencies;
- stateful/socket recovery still applies.

Indicative timing if Site 2 is already ready: **~46s + T6** for a fast LTM-health-informed GTM model, or **up to ~150s + T6** with default direct GTM monitor + 30s TTL assumptions.

Overall: **R3**.

If Site 2 applications require manual startup:

- full outage persists through startup/readiness;
- F5 failover speed is no longer the dominant RTO.

Overall: **R4**.

---

# 11. What should be measured in production testing

For each scenario capture:

1. fault injection time;
2. infrastructure detection time;
3. routing/failover completion time;
4. first successful external transaction;
5. first successful internal transaction;
6. first successful App A -> B transaction;
7. session preservation/re-login outcome;
8. WebSocket reconnect time;
9. message gap/replay result;
10. percentage of users affected;
11. whether recovery was automatic;
12. whether operator action was required;
13. whether another component/site remained able to tolerate a second fault.

The most useful RTO is:

> time from fault to successful business transaction for each actor.

Not:

> time for the WAF/LTM/GTM to report green.

---

## 11.1 Earlier user-impact threshold

The earlier architecture paper contained a possible business rule that service may remain open only while **less than 25% of users are affected**.

That requirement is currently recorded as a **legacy candidate input**, not a confirmed invariant.

If it still applies:

- map the real external-user population to leased lines, firewall pairs and sites;
- calculate actual blast radius per failure domain;
- do not assume four circuits means four exactly equal 25% populations;
- a strict `<25%` threshold means losing exactly 25% would not meet the requirement;
- test the rule against external DNS, access circuits, firewall pairs and site reachability.

## 11.2 Validation and failure-injection catalogue

The earlier main architecture/WebSocket analyses contained a strong failure-injection test set. Keep these tests as acceptance evidence for the current W1-W4 model.

### Client and DNS

1. client sleep/reboot/network handoff;
2. external resolver failure and external GTM/DNS failure;
3. internal enterprise DNS failure;
4. internal DNS -> GTM delegation/forwarding failure;
5. stale/incorrect internal or external DNS answer;
6. application DNS cache that does not promptly re-resolve.

### Network and firewall

7. each leased-line/circuit failure individually;
8. correlated circuit/carrier failure;
9. one edge-firewall member failure;
10. full firewall-pair failure;
11. NAT/asymmetric-return-path fault;
12. inter-site route loss while local service is healthy;
13. inter-site route loss while remote WAF or remote dependency is in use.

### LTM/WAF

14. one LTM HA member failure and full LTM-pair failure;
15. one independent WAF member failure;
16. one WAF-cluster member failure;
17. complete local WAF service failure;
18. bad WAF policy/configuration common-mode failure;
19. planned WAF/LTM drain and rolling maintenance;
20. capacity test while one WAF is removed.

### Application/platform

21. ELB/LB member and complete service failure;
22. VM/app-process failure;
23. Kubernetes ingress, Pod, node and cluster failure;
24. application listener healthy but business readiness failed;
25. session/authentication/database/event-store failure;
26. passive application not ready when site failover is requested.

### Dependency and cross-site

27. B1 fails while A1 remains healthy and no remote B is available;
28. B1 fails and A1 uses B2 successfully;
29. B1 fails when A/C/D all depend on B and retry simultaneously;
30. B2 is reachable but its required C dependency is unavailable;
31. remote WAF route-back and remote App B fallback under peak-like load.

### Long-lived/application recovery

32. WebSocket abrupt disconnect;
33. graceful drain of long-lived connections;
34. reconnect backoff/jitter and reconnect storm;
35. re-authentication after reconnect;
36. subscription restoration;
37. lost acknowledgement after a committed write with idempotent retry;
38. stale replay cursor and snapshot reconciliation;
39. duplicate/lost message detection.

### Whole-site and failback

40. complete active-site isolation/loss;
41. Site 2 ready and automatic recovery;
42. Site 2 application stopped/manual startup;
43. failback after service restoration without unnecessarily moving healthy existing sessions.

For each test record:

- fault-injection timestamp;
- detection time;
- traffic/path convergence;
- first successful external-user transaction;
- first successful external API transaction;
- first successful internal-user transaction;
- first successful App A -> B -> C transaction where relevant;
- percentage of each user population affected;
- session/login outcome;
- WebSocket disconnect/reconnect/replay outcome;
- manual actions;
- capacity of surviving components/site;
- p95/p99 service-recovery time;
- whether a second fault could still be tolerated.

# 12. Primary conclusions

1. **WAF topology is only one layer of service resilience.**  
   A healthy application can be externally unavailable because its ingress path failed, while internal users remain unaffected.

2. **External and internal user impact must always be stated separately.**  
   WAF/front-end failure often affects external users much more than internal users.

3. **App A/B/C dependencies can dominate user availability.**  
   Dependency routing, timeout/retry and state design can prevent much larger outages than adding another WAF.

4. **Cross-site routing is most valuable when it avoids moving a healthy application.**  
   X2A/X2B can reduce a delivery-tier failure from site/application DR to a smaller degraded recovery.

5. **Application compliance determines whether infrastructure recovery becomes service recovery.**  
   Stateful and WebSocket applications can remain broken after the infrastructure has recovered.

6. **The service RTO must be measured end-to-end.**  
   The correct measure is successful user/application transaction after the fault, not F5 component convergence alone.

7. **The technical component matrix remains necessary, but it is supporting evidence.**  
   The main architecture story should be the end-to-end service/user outcome in this document.
