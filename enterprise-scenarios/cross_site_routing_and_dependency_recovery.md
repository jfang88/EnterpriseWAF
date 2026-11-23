# Cross-Site WAF/LTM Routing and Application Dependency Recovery

Status: Derived design study

Stable baseline: enterprise_scenario_invariants.md  
Changeable assumptions: analysis_variables_and_f5_assumptions.md  
Related matrix: common_failure_matrix.md

## 1. Purpose

This document evaluates whether controlled cross-site routing can improve recoverability without forcing otherwise-healthy applications to fail over.

It covers two separate use cases:

1. Cross-site LTM/WAF recovery while the primary application remains healthy.
2. Application A -> Application B dependency recovery.

Design objective:

> Move the smallest failed layer possible. Do not move the application or entire site unless the application itself, its state, or a required dependency cannot safely remain where it is.

## 2. Key conclusion

Controlled cross-site routing can provide a major resilience benefit when:

- the primary application is healthy;
- the local WAF/LTM/security path is the failed layer;
- the alternate site's WAF/LTM has spare capacity;
- routing is symmetric or deliberately SNATed;
- the alternate security devices have the correct tenant/application policy;
- the inter-site network is healthy and sized for contingency traffic.

It can avoid this unnecessarily large recovery:

    Site 1 WAF failure
           |
           v
    Fail healthy Site 1 application to Site 2

A smaller recovery is:

    Site 1 application remains active
           ^
           |
    remote Site 2 WAF provides temporary inspection

Cross-site routing adds new dependencies:

- inter-site network availability;
- latency and bandwidth;
- stateful-firewall/NAT symmetry;
- remote WAF capacity;
- tenant/policy correctness on the remote WAF;
- more complex troubleshooting.

It should therefore be a controlled contingency path, not an uncontrolled any-to-any normal path.

## 3. Pattern X2A - local LTM survives; borrow remote WAF

Normal:

    External user
        |
    Site 1 edge firewall VIP
        |
    Site 1 LTM HA pair
        |
    +---+---+
    |       |
    WAF1   WAF2       preferred/local
        |
    Site 1 application

Contingency:

    External user
        |
    Site 1 edge firewall VIP
        |
    Site 1 LTM HA pair
        |
        +--------------------> Site 2 WAF
                                  |
                                  | route back
                                  v
                            Site 1 application

This is the cleanest cross-site WAF-borrowing pattern because the client's firewall VIP and local LTM remain unchanged.

### F5 fit

BIG-IP LTM supports reachable remote pool members. F5 also documents the Virtual Location monitor for distinguishing local and remote members, together with Priority Group Activation so local members can remain preferred and lower-priority remote members activate only when local membership drops below a threshold.

### Recovery timing

If the remote WAF is already configured, monitored, policy-ready and reachable, recovery is primarily driven by the local LTM member-health timeout.

For many BIG-IP LTM active monitors, the documented default-style timing is around a 5-second interval and 16-second timeout. Treat this only as an engineering reference; the configured and measured value is authoritative.

### Benefits

- no GTM/DNS change;
- no DNS TTL/cache delay;
- primary application does not move;
- potentially much faster than application/site DR;
- same Site 1 firewall VIP remains in use;
- remote WAF capacity can remain lower priority until needed.

### Drawbacks

- inter-site network becomes part of the application path;
- route-back may hairpin traffic;
- return path must be deterministic;
- SNAT may be needed;
- original client IP requirements must be considered;
- failed WAF connections do not magically migrate;
- socket/WebSocket clients still need reconnect logic;
- remote WAF must already have the correct application/tenant policy;
- remote capacity may be contended.

## 4. Pattern X2B - local LTM/WAF tier fails; use remote front-end and route back

Normal:

    GTM
      |
    Site 1 firewall VIP
      |
    Site 1 LTM
      |
    Site 1 WAF
      |
    Site 1 application

Contingency:

    GTM
      |
    Site 2 firewall VIP
      |
    Site 2 LTM
      |
    Site 2 WAF
      |
      +---- inter-site route ----> Site 1 application

This pattern can recover from complete Site 1 delivery-tier loss while keeping the Site 1 application running.

### Benefits

- avoids starting/moving a healthy primary application;
- can be useful when DR application startup is manual or slow;
- separates front-end failure from application failure.

### Drawbacks

- requires GTM/DNS convergence;
- external clients must be able to route to Site 2;
- resolver/client caching affects RTO;
- front end and application are now in different sites;
- depends simultaneously on Site 2 front end, Site 1 app and the inter-site link;
- operational diagnosis is more complex;
- if the Site 1 app then fails, another recovery is needed.

### Timing

Typical timing driver:

    GTM health detection
      + DNS decision
      + DNS/cache convergence
      + client reconnect/re-resolution
      + remote LTM/WAF availability

This is generally slower than X2A but may still be much faster than manual application DR.

## 5. Pattern X2C - full site/application failover

    GTM
      |
    Site 2 firewall
      |
    Site 2 LTM
      |
    Site 2 WAF
      |
    Site 2 application

Use this when the Site 1 application itself is unhealthy, its required data/state cannot safely remain in Site 1, route-back is unavailable, or full site recovery is operationally safer.

## 6. Recovery decision tree

    Failure detected
           |
           v
    Is Site 1 application healthy?
       |                 |
      no                yes
       |                 |
       v                 v
    Fail app/site    Is Site 1 LTM healthy?
                         |             |
                        yes           no
                         |             |
                         v             v
                 Remote WAF valid?   Can GTM use Site 2 front end?
                    |       |           |           |
                   yes     no          yes         no
                    |       |           |           |
                    v       +------> Can Site 2     outage/local
                 X2A               LTM/WAF route    recovery
                                    back safely?
                                      |      |
                                     yes    no
                                      |      |
                                      v      v
                                     X2B   fail app/site

The question is not "Is Site 1 down?" The question is "Which layer failed, and can the healthy application continue behind another delivery/security path?"

## 7. Cross-site benefit by WAF topology

W1-W3 are assumed to exist with the same logical topology in both sites. W4 is intentionally asymmetric: Site 1 has the WAF cluster plus an extra active/spare WAF; Site 2 has only the WAF cluster.

| Topology | Benefit from route-back | Main drawback |
|---|---|---|
| W1 - independent WAF pool in each site | High. A Site 1 LTM can use a Site 2 WAF as lower-priority contingency if routing/policy allow it | Connection reset on failed member; routing/capacity complexity |
| W2 - WAF HA cluster in each site | Medium. Most useful after whole local cluster loss | First failure already handled locally; remote transition is larger |
| W3 - preferred WAFs + shared reserves in each site | Very high. Reserve WAF can be local or remote | Reserve exhaustion and cross-tenant policy/capacity risk |
| W4 - Site 1 cluster + extra WAF; Site 2 cluster only | High while Site 1 is active because the extra WAF provides another local recovery tier | Site 2 has less local headroom during DR/site failover; asymmetry complicates capacity and testing |

Practical interpretation:

- W1 and W3 benefit most from X2A.
- W4 should normally consume the extra Site 1 WAF before crossing sites when Site 1 is active. After failover to Site 2, that extra local tier is no longer present.
- W2 gains less from remote borrowing because the first device failure is already handled by the WAF cluster.
- Conventional GTM failover remains available for all designs, but W4 fails to a **smaller Site 2 WAF topology** unless Site 2 is separately expanded.

## 8. App A -> App B dependency routing

Baseline:

    App A1 --------------> App B1
                             X failed

    App B2 remains healthy in Site 2

If A1 is hard-coded to B1:

    B1 fails
      -> A1 loses dependency
      -> A1 may be declared unhealthy
      -> A may fail to Site 2
      -> other B-dependent applications may also fail
      -> unnecessary cascade

Preferred pattern:

    App A1
       |
       v
    B Service VIP / LTM
       |
       +---- preferred ----> B1 Site 1
       |
       +---- fallback -----> B2 Site 2

Normal:

    A1 -> B Service VIP -> B1

B1 failure:

    A1 -> B Service VIP -> B2

A1 remains in Site 1.

### Benefits

- prevents a B1 failure from forcing A1 to move;
- avoids cascading movement of A/C/D if they all depend on B;
- local LTM health can withdraw B1 faster than DNS-cache-based discovery;
- Priority Group Activation is a good F5 building block for local preferred and remote lower-priority members;
- keeps the recovery domain at B rather than A + B.

### Drawbacks

- B2 must be safe for remote consumers;
- state/database consistency may prohibit remote-active access;
- cross-site latency may affect synchronous calls;
- B2 must have contingency capacity;
- A1 -> B2 firewall/routing must exist;
- authentication, certificate trust and service identity must work cross-site;
- App A still needs timeouts, retries and connection refresh;
- long-lived A->B connections need reconnect behavior.

## 9. LTM service VIP versus DNS/GTM for A -> B

### LTM/service VIP

Prefer when:

- B1 and B2 are reachable through the same service layer;
- fast failover is important;
- local-preferred/remote-fallback is desired;
- DNS caching would create unacceptable delay.

Recovery is mainly driven by LTM member-monitor timing.

### DNS/GTM

Prefer when:

- B endpoints sit in separate routing domains;
- applications already re-resolve correctly;
- site selection is naturally DNS-based;
- coupling to a local LTM should be reduced.

Risks:

- DNS/application caches;
- persistent connections continue using the old endpoint until failure;
- app may not promptly re-resolve;
- TTL becomes part of RTO.

For critical synchronous A -> B dependencies, prefer a stable internal service VIP or service-discovery abstraction rather than exposing B1/B2 addresses directly.

## 10. Application-code requirements

Routing alone does not make A -> B resilient.

App A should have:

1. bounded connect timeout;
2. bounded request/read timeout;
3. safe retries only;
4. exponential backoff and jitter;
5. retry budgets;
6. idempotency for operations that may be retried;
7. circuit breaker/bulkhead behavior where appropriate;
8. connection-pool refresh after failure;
9. DNS re-resolution where DNS discovery is used;
10. observability showing local versus remote dependency use.

App B should have:

- remote-site requests supported;
- site-independent authentication/authorization;
- data/state safe for remote access;
- duplicate request handling;
- sufficient contingency capacity;
- readiness health that proves B can service A.

### Non-compliance impact

| Missing behavior | Recoverability impact |
|---|---|
| No timeout | A hangs on dead B1; rerouting does not fix the already-hung call |
| No retry | A fails even though B2 is available |
| Aggressive/unbounded retry | Retry storm can overload B2 and cascade |
| Non-idempotent retry | Duplicate transaction risk |
| Site-bound state | B2 is reachable but unsafe/unusable |
| No connection refresh | A can remain pinned to dead B1 |
| Hard-coded B1 | Infrastructure cannot redirect cleanly |
| No circuit breaker | Many A instances can overwhelm B/recovery path |

If A cannot safely retry/reconnect to B2, cross-site routing must not be counted as a valid end-to-end recovery mechanism.

## 11. Failure-mode overlay

    +-------------------------- SITE 1 --------------------------+
    | Edge FW -> LTM -> Local WAF -> App A1                    |
    |              |                       |                    |
    |              |                       +--> App B1          |
    +--------------|--------------------------------------------+
                   |
                   | X2A: remote WAF contingency
                   v
    +-------------------------- SITE 2 --------------------------+
    | Edge FW -> LTM -> Remote WAF -> App A2 / App B2          |
    +--------------------------|--------------------------------+
                               |
                               +---- X2B route-back ---> App A1

    GTM can move external ingress Site 1 -> Site 2.
    App A1 can independently move dependency B1 -> B2.

These are independent recovery paths and should be tested independently.

## 12. Cross-site scenario matrix

| Scenario | Without cross-site route-back | With controlled cross-site routing | Benefit | New risk |
|---|---|---|---|---|
| One local WAF fails | Local pool/cluster handles | Usually do not use cross-site | Low | Avoid needless complexity |
| All local WAFs fail; LTM healthy | App/site failover or outage | X2A uses remote WAF, primary app stays | High | Hairpin/inter-site dependency |
| Local LTM + WAF fail; app healthy | App/site failover | X2B uses remote front end and routes back | High if DR app startup is slow | DNS delay and split-site path |
| Local app fails | App/site failover | Route-back does not help | None | Must not route to failed app |
| App B1 fails; B2 healthy | A may fail/cascade | Route A1 -> B2 | Very high | State/latency/capacity |
| Inter-site link fails while local healthy | No impact | Remove contingency only | Good isolation | Bad health logic can cause false outage |
| Inter-site link fails while X2 active | Recovery path fails | Need local restoration or full site recovery | None | Second failure while degraded |
| Bad WAF policy pushed everywhere | Logical WAF outage | Remote WAF with same bad policy does not help | None | Common-mode config |
| Site 1 fully lost | GTM -> Site 2 app | Route-back impossible | None | Full DR required |

## 13. Recommended recovery hierarchy

    1. Survive member failure locally
       |
    2. Use local spare capacity
       |
    3. Use remote WAF or remote dependency contingency if safe
       |
    4. Use remote front end and route back if primary app is healthy
       |
    5. Fail the application/site only when required

This keeps the recovery domain proportional to the failure.

## 14. F5-specific design basis

The F5 building blocks used by this design are supported in current F5 documentation:

- remote LTM pool members are feasible when routing is valid;
- SNAT can make the return route deterministic;
- Virtual Location monitoring can distinguish local and remote members;
- Priority Group Activation can keep local members preferred and activate lower-priority remote members;
- BIG-IP DNS integrates with LTM using iQuery;
- Global Availability can implement primary/secondary site preference;
- Topology can implement locality-based GSLB.

References:

- https://techdocs.f5.com/en-us/bigip-16-0-0/big-ip-local-traffic-manager-monitors-reference/monitors-concepts.html
- https://techdocs.f5.com/en-us/bigip-16-0-0/big-ip-dns-implementations/integrating-big-ip-dns-into-a-network-with-big-ip-ltm-systems.html
- https://techdocs.f5.com/en-us/bigip-15-0-0/big-ip-dns-load-balancing/about-load-balancing-and-resource-availability.html
- https://techdocs.f5.com/en-us/bigip-15-0-0/big-ip-dns-load-balancing/using-topology-load-balancing-to-distribute-dns-requests-to-specific-resources.html
