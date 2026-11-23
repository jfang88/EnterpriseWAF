# End-to-End Service Impact and Recoverability Analysis

**Status:** Primary derived output for failure/recovery  
**Stable baseline:** [enterprise_scenario_invariants.md](./enterprise_scenario_invariants.md)  
**Changeable assumptions:** [analysis_variables_and_f5_assumptions.md](./analysis_variables_and_f5_assumptions.md)  
**Technical component matrix:** [common_failure_matrix.md](./common_failure_matrix.md)  
**Cross-site/dependency detail:** [cross_site_routing_and_dependency_recovery.md](./cross_site_routing_and_dependency_recovery.md)

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
      -> application ELB/service
      -> VM / Kubernetes / PaaS workload
      -> dependencies such as App B / App C
      -> data/state services

## Internal path

    internal user/system
      -> internal enterprise DNS
      -> optional delegation/conditional forward to GTM
      -> internal LTM/ELB/service VIP
      -> application
      -> dependencies such as App B / App C
      -> data/state services

## Internal application dependency path

    App A
      -> internal enterprise DNS
      -> optional GTM lookup for internal B service
      -> B service VIP / endpoint
      -> App B
      -> optional internal DNS/GTM lookup for C
      -> App C

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

This can convert a 10–20 second class member/pool problem into a DNS/site/manual-DR event.

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

Overall: XD1 can turn application cascade into **R1/R2**.

## Example 4 — complete Site 1 loss

If Site 2 is ready:

- external clients re-resolve/reconnect;
- internal users route to Site 2;
- App A/B/C use Site 2 or valid remote dependencies;
- stateful/socket recovery still applies.

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
