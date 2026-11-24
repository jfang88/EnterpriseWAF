# EnterpriseWAF Future Architecture Improvements

**Status:** Target-state / to-be architecture guidance  
**Current-state source:** [enterprise_scenario_invariants.md](./enterprise_scenario_invariants.md)  
**Purpose:** Separate future design improvements from the current-state baseline.

# 1. Executive recommendation

The target health model should be **layered**, not concentrated in one device or one monitor.

The recommended operating model is:

> **Local delivery tiers perform fast member-level recovery; BIG-IP DNS/GTM owns authoritative site/endpoint health for DNS steering using Layer-7 checks of the published external and internal VIPs; application teams own the readiness contract; independent synthetic monitoring verifies the real user outcome.**

For the current architecture, the most important future improvement is to make GTM health represent the **service path**, not simply a WAF/LTM port.

# 2. Recommended health-check placement

| Health layer | Best place | What it should check | What action it should drive |
|---|---|---|---|
| **H1 - device/HA liveness** | firewall/LTM/WAF/CFW native HA | peer/device/process/interface availability | local HA takeover only |
| **H2 - local pool/member health** | LTM / ELB / service tier closest to members | HTTP/L7 or protocol-aware member readiness | remove one failed WAF/backend/member locally; **do not invoke DNS/site failover** |
| **H3 - external published-service health** | **GTM/DNS prober** against the **external application VIP** | Layer-7 request through edge firewall -> LTM -> WAF -> CFW -> ELB -> application | external wide-IP/site selection |
| **H4 - internal published-service health** | **GTM/DNS prober** or authoritative LTM/iQuery health against the **internal service VIP** | Layer-7 request through internal LTM -> internal firewall -> CFW -> ELB -> application | internal delegated-name/site selection |
| **H5 - dependency/service health** | service VIP/LTM/service discovery; GTM only when GTM selects the dependency endpoint | App A/D -> B service -> critical downstream dependency readiness | B1 -> B2 or other dependency-local recovery |
| **H6 - independent user-like synthetic** | monitoring platform outside the traffic-management stack | login/business transaction from representative external/internal viewpoints | SLO validation, alerting and incident confirmation; normally not the only steering signal |

The key principle is:

> **GTM decides which site/endpoint DNS should return; local LTM/ELB decides which member should serve inside that site.**

Do not turn one failed backend, one WAF node, or one LTM pool member into a GTM/site failover when healthy local capacity remains.

# 3. Why GTM should own the site-level Layer-7 decision

BIG-IP DNS/GTM is the component that changes the DNS answer between Site 1 and Site 2. Therefore the health signal used for that decision should represent the endpoint GTM is advertising.

For this environment, that means two distinct endpoint checks per protected service where both paths exist:

1. **External VIP Layer-7 health** - proves the external/extranet path is usable.
2. **Internal VIP Layer-7 health** - proves the internal path is usable for internal DNS/delegated names.

These checks must be separate because the paths have different failure domains:

```text
External:
GTM prober
  -> edge firewall / external VIP
  -> tenant LTM
  -> WAF
  -> CFW
  -> ELB
  -> application readiness endpoint

Internal:
GTM prober or authoritative internal LTM health
  -> internal service VIP
  -> internal firewall
  -> CFW
  -> ELB
  -> application readiness endpoint
```

A service may therefore be:

- external-unhealthy but internal-healthy;
- internal-unhealthy but external-healthy;
- unhealthy on both paths.

The DNS policy should not automatically collapse those distinct states into one generic "application down" result.

# 4. Direct GTM L7 monitor versus LTM/iQuery

Both patterns are useful; the target should use the one that represents the required path most accurately.

## 4.1 Direct GTM Layer-7 monitor

Use when a GTM prober can legitimately reach the target VIP from a useful network perspective.

Advantages:

- GTM directly validates the endpoint it is advertising;
- can test Host/SNI, URI, expected status/body and TLS behavior;
- can distinguish external and internal VIPs.

Caution:

- a GTM located inside the edge boundary may not reproduce every customer-network failure;
- firewall/NAT/routing must allow the monitor path;
- the monitor should not depend on the inter-site path for healthy local service.

## 4.2 LTM health exported to GTM through iQuery

Use when the LTM is the better local observer of the service path, or when direct GTM probing cannot traverse the intended path safely.

Target pattern:

```text
LTM performs L7 application/path health
        |
        v
BIG-IP DNS/GTM consumes authoritative virtual-server health via iQuery
        |
        v
GTM makes site/DNS decision
```

This can provide faster local detection than a slow direct GTM monitor while still letting GTM own the global DNS decision.

## 4.3 Preferred target

Use a **hybrid layered model**:

- local LTM/ELB health for fast member withdrawal;
- GTM endpoint health for site/DNS decisions;
- iQuery where it provides an authoritative local service signal;
- independent synthetic monitoring for user outcome.

Do not make GTM the only health-check layer.

# 5. GTM synchronization group and prober strategy

The two site GTM clusters should be treated as one synchronized global-DNS control plane while retaining independent site failure domains.

The target design should explicitly document:

- which GTM devices/probers check Site 1 external VIPs;
- which check Site 2 external VIPs;
- which check internal VIPs;
- whether probing responsibility is shared across the synchronization group;
- whether probers are selected from inside, outside or either data centre;
- how many successful probes are required before a service is considered available;
- what happens if the inter-site link is unavailable but the local application remains healthy.

### Recommended rule

Use **more than one independent health perspective** for critical site-level decisions where routing permits, but configure availability requirements so that:

> **loss of the inter-site path alone does not mark a healthy local service unavailable.**

A practical target is:

- local authoritative health is required;
- remote/cross-site observation provides corroboration and faster global visibility where available;
- no single remote probe is allowed to make healthy local service dependent on cross-site reachability.

The actual F5 `All`, `At Least` or `Require` availability setting should be selected after testing the desired failure semantics.

# 6. Application-team health-check contract

Layer-7 health checks are only useful when the application team defines what "ready" means.

Each protected service should publish a health-check contract containing:

| Field | Required decision |
|---|---|
| **Hostname / SNI** | exact host name GTM/LTM should send |
| **URI** | stable readiness path, for example `/health/ready` |
| **Method** | normally GET/HEAD unless the service requires otherwise |
| **Expected status** | for example HTTP 200 |
| **Expected body/content** | small stable response/string where content verification is useful |
| **Authentication** | none, dedicated monitor credential, certificate or token as appropriate |
| **Critical dependencies** | dependencies that must be available for the service to accept new traffic |
| **Non-critical dependencies** | dependencies that should **not** make the whole service fail health |
| **Timeout** | response time expected under normal and degraded conditions |
| **Maintenance semantics** | how the app intentionally removes itself from service |
| **Version/change owner** | app team owner who approves changes to the health contract |

## Avoid two opposite errors

### Too shallow - false green

```text
TCP 443 works
  -> WAF/LTM green
  -> CFW/ELB/app broken
  -> users fail while GTM still advertises the site
```

### Too deep - false red / cascade

If App A's health endpoint fails whenever a non-critical App B/C feature is unavailable, one shared dependency can cause GTM to withdraw A, C and D together and create an unnecessary site failover.

The health contract must therefore represent the **minimum business capability required to accept new traffic**, not every downstream function.

# 7. Health and action boundaries by failure type

| Failure | Preferred detector | Preferred action |
|---|---|---|
| one backend/Pod/VM | ELB/LTM/service health | remove member locally |
| one independent WAF node | LTM WAF-pool monitor | remove WAF locally |
| one LTM peer | BIG-IP HA | local peer takeover |
| one CFW member | CFW HA | local firewall takeover |
| whole external VIP path unusable | GTM external L7 health | change external DNS/site answer |
| whole internal VIP path unusable | GTM/internal authoritative L7 health | change internal delegated endpoint/site answer |
| App B local instance fails | B service VIP/service-discovery health | B1 -> B2 dependency-local recovery where safe |
| whole site lost | GTM + infrastructure/site health | full Site 2 recovery |

This separation protects availability by keeping the recovery domain proportional to the failed component.

# 8. Target convergence model

For a DNS/site move, measure these separately:

```text
1. service/path failure occurs
2. local health detector notices failure
3. GTM receives/derives authoritative unhealthy state
4. GTM synchronization/global state converges where required
5. GTM returns alternate VIP/site
6. residual DNS TTL/client cache expires or client re-resolves
7. connection/session/application recovery completes (T6)
```

If GTM performs direct cross-site checks, step 3 may be faster and less dependent on synchronization delay.

If GTM only has site-local health and the remote site learns the state indirectly, the synchronization/learning delay must be measured and included.

Do **not** treat DNS TTL as the whole failover time.

# 9. Internal DNS target model

Internal clients continue to use internal enterprise DNS.

For selected names/namespaces:

```text
Internal client
  -> internal enterprise DNS
  -> delegated/conditional-forwarded name
  -> enterprise edge GTM/DNS
  -> healthy internal service VIP
```

The target is **not** to replace internal DNS with GTM.

The target is to use GTM only where global/site-aware endpoint selection is required, while retaining enterprise internal DNS as the normal resolver/control boundary.

Each delegated namespace must document:

- authoritative owner;
- TTL;
- GTM wide-IP/pool;
- internal VIPs returned;
- Layer-7 health check for those VIPs;
- client/application DNS caching behavior.

# 10. Independent synthetic monitoring

GTM/LTM health is necessary but does not prove the full user experience from outside the F5 stack.

Add independent synthetic tests for critical services from representative viewpoints:

- external/private-network user perspective;
- internal desktop/system perspective;
- important API/system perspective.

Use these for:

- 99.95% SLO measurement;
- end-to-end latency/error monitoring;
- detecting DNS, firewall, authentication or dependency problems missed by infrastructure monitors;
- validating failover tests.

Normally, independent synthetic monitoring should **confirm** business availability rather than being the sole automatic GTM failover trigger, unless its false-positive behavior and failover semantics are explicitly proven.

# 11. Dependency resilience improvement

For App A/D -> B -> C chains, implement dependency-local recovery before broad application/site failover where business semantics allow it.

Target example:

```text
App A / App D
      |
B service VIP / discovery
   /             \
B1 Site 1      B2 Site 2
preferred       fallback
      |
    App C
```

Requirements:

- B2 capacity and data/state compatibility;
- bounded connect/read timeouts;
- retry with backoff/jitter;
- circuit breaker/bulkhead;
- idempotency/reconciliation;
- authentication/service identity;
- routing/firewall readiness;
- no healthy-state dependency on the inter-site link.

# 12. Cross-site application-delivery improvement

Evaluate these as contingency capabilities, not current-state assumptions:

- **X2A** - surviving local LTM borrows a remote WAF and routes back to the healthy local application;
- **X2B** - remote front end routes back to a healthy primary-site application;
- **XD1** - App A/D stays local but uses remote App B;
- **X2C** - conventional full site/application failover.

Prefer the **smallest recovery domain** that restores the service safely.

# 13. WAF topology and maintainability improvement

Continue to evaluate:

1. **S1 - tenant-specific LTM pairs + shared independent active WAF pool** as the leading cost/resilience candidate;
2. **dedicated W1 with three independent WAFs per tenant/site** as the high-isolation fallback;
3. W3 where dedicated normal-state WAFs plus shared reserve are operationally preferred;
4. W2 where simple HA and connection mirroring matter more than horizontal WAF scale.

Whichever topology is selected must support:

- rolling maintenance;
- canary/staged WAF policy deployment;
- policy isolation by application;
- rollback;
- N-1 and required N-2 capacity;
- one planned maintenance event plus one credible unplanned failure where the 99.95% target requires it.

# 14. Implementation sequence

## Phase 0 - inventory current state

Confirm before changing behavior:

- current GTM monitor types and targets;
- external VIP health configuration;
- internal delegated namespaces and internal VIPs;
- iQuery/LTM integration;
- GTM prober selection and availability requirements;
- cross-site probing;
- monitor intervals/timeouts;
- existing app readiness endpoints;
- current synthetic monitoring.

## Phase 1 - define app health contracts

Prioritize critical applications and shared dependencies.

## Phase 2 - implement Layer-7 endpoint health

Implement GTM-authoritative external/internal endpoint health using direct L7 monitors and/or LTM/iQuery as appropriate.

## Phase 3 - add prober diversity and cross-site visibility

Validate synchronization/probing behavior under:

- application failure;
- WAF failure;
- CFW failure;
- site failure;
- inter-site network partition.

## Phase 4 - implement dependency-local recovery

Pilot B1 -> B2 where semantics and data allow it.

## Phase 5 - implement cross-site WAF/front-end contingency

Pilot X2A/X2B only after routing, stateful firewall, NAT/SNAT, capacity and operational ownership are agreed.

## Phase 6 - measure 99.95% evidence

Use fault injection and planned-maintenance tests to measure:

- p50/p95/p99 fault-to-successful-transaction time;
- external and internal recovery separately;
- WebSocket/stateful recovery;
- GTM convergence;
- dependency cascade behavior;
- maintenance plus second-failure behavior.

# 15. Acceptance gates

Before calling the target architecture ready:

1. external and internal VIP health checks are documented per application;
2. the monitor proves the intended service path, not just TCP reachability;
3. application teams own the readiness contract;
4. one failed local member stays a local recovery event;
5. GTM does not advertise a site whose required application path is unusable;
6. inter-site link failure does not falsely withdraw healthy local service;
7. GTM synchronization/prober convergence is measured;
8. external and internal DNS failover behavior is tested separately;
9. App A/B/C/D dependency cascades are tested;
10. SLO synthetic monitoring measures the real user outcome;
11. planned maintenance remains within the 99.95% budget;
12. rollback and failback are tested.

# 16. F5 implementation references

Official F5 documentation relevant to the target model:

- BIG-IP DNS/LTM integration and iQuery: https://techdocs.f5.com/en-us/bigip-16-0-0/big-ip-dns-implementations/integrating-big-ip-dns-into-a-network-with-big-ip-ltm-systems.html
- BIG-IP DNS synchronization groups and shared probing responsibility: https://techdocs.f5.com/en-us/bigip-17-5-0/big-ip-dns-implementations/adding-a-new-big-ip-dns-to-a-big-ip-dns-synchronization-group.html
- BIG-IP DNS prober selection / availability requirements: https://techdocs.f5.com/en-us/bigip-17-5-0/big-ip-dns-implementations/integrating-big-ip-dns-into-a-network-with-big-ip-ltm-systems.html
- BIG-IP LTM HTTP/HTTPS monitor concepts: https://techdocs.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/ltm-monitors-reference-12-0-0/2.html
