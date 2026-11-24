# Executive Recommendation — EnterpriseWAF Architecture and 99.95% Availability

**Status:** Executive decision summary  
**Primary comparison:** [deployment_options_resilience_summary.md](./deployment_options_resilience_summary.md)  
**Detailed service recovery:** [end_to_end_service_impact_analysis.md](./end_to_end_service_impact_analysis.md)  
**Maintainability:** [maintainability_change_management_analysis.md](./maintainability_change_management_analysis.md)

# 1. Executive decision

## 1.0 Architectural principle — shared WAF runtime, application-coupled policy

The WAF should not be treated as identical to a generic router or firewall.

Use this distinction:

- **WAF runtime/enforcement capacity** may be shared within an approved cloud/security zone;
- **WAF policy** is tightly coupled to the protected application/API and should have application-specific ownership, testing, canary/staging and rollback.

Therefore the target is not "one monolithic shared WAF policy." It is:

> **shared WAF enforcement capacity with application-isolated policies and change blast radius.**

See [current_architecture_and_invariants.md](./current_architecture_and_invariants.md) for the canonical current-state architecture and [future_architecture_improvements.md](./future_architecture_improvements.md) for the target health-monitoring and platform-rebuild model.

The current architecture focus is the **four-tenant extranet estate** (currently running **BIG-IP 17.5.x**, with a target rebuild onto newer devices/software such as rSeries/VELOS F5OS + BIG-IP 21.1.x+ — see [future_architecture_improvements.md §15A](./future_architecture_improvements.md#15a-platform-rebuild-impact-big-ip-175x-current-vs-newer-devices-and-big-ip-211x--f5os-future)). Retain the existing GTM and tenant LTM boundaries in the current target recommendation. Consolidating GTM/LTM may be a valid future optimisation if applications converge onto common private-cloud platforms, but it requires participation from the GTM/LTM/network owners and is not assumed by this WAF analysis.

### Ownership constraint

This WAF architecture can recommend WAF topology, capacity, policy isolation and recovery behavior, but it cannot unilaterally commit:

- GTM/LTM redesign;
- cross-site LTM steering;
- firewall/routing/NAT changes;
- DNS/GTM health-policy changes.

X2A/X2B are therefore **candidate target capabilities** until the owning teams validate them. See [current_architecture_and_invariants.md](./current_architecture_and_invariants.md) and [future_architecture_improvements.md](./future_architecture_improvements.md).

There is no single topology that guarantees 99.95% availability. The target is credible only when:

- common failures recover locally and automatically;
- routine maintenance does not consume all redundancy;
- a second failure can still be tolerated during important maintenance windows where required;
- WAF/LTM/CFW/application health checks represent the real service path;
- applications retry/reconnect/recover state correctly;
- alternate-site applications, dependencies and data are actually ready;
- common-mode configuration changes are staged and reversible.

## 1.1 Topology names used in this document

The shorthand is used only to keep the comparison tables compact. Read the descriptions below before the ranking.

| ID | Plain-English description | Normal traffic model | Main trade-off |
|---|---|---|---|
| **W1** | **Tenant/dedicated LTM pair in front of independent active WAFs** | LTM load-balances the same service across 2..N active WAFs | Strong horizontal scale and maintenance flexibility; failed sockets normally reconnect |
| **W2** | **WAF HA/DSC cluster**, optionally behind an LTM | One WAF owns a traffic group; peer is HA standby for that traffic group | Simple HA and possible connection mirroring (requires licensed LTM+AWAF), but pair/cluster is a hard local boundary |
| **W3** | **Tenant LTM pair + tenant-preferred WAFs + shared reserve WAFs** | Preferred WAFs serve normally; shared reserve is contingency capacity | Keeps normal-state tenant separation but introduces shared reserve governance/contention |
| **W4** | **Asymmetric cluster design**: Site 1 WAF HA cluster + extra WAF; Site 2 cluster only | Site 1 has extra local capacity; Site 2 has only the cluster | Stronger Site 1 resilience but asymmetric DR/maintenance |
| **S1** | **Existing tenant-specific LTM pairs feeding one shared independent active WAF pool** | The current four extranet tenant LTM pairs remain; WAF capacity is shared behind them | Best shared-WAF candidate without redesigning LTM/GTM ownership boundaries (note: future rSeries/VELOS F5OS multi-tenancy can deliver S1-like hardware consolidation with Dedicated-W1 OS/upgrade isolation) |
| **S2** | **Shared LTM pair + shared independent active WAF pool** | Tenants share both ingress LTM and WAF capacity | Comparison only; LTM consolidation is outside current scope and has a much larger common failure/change domain |

### W1 — dedicated independent WAF pool

~~~text
Tenant firewall/VIP
       |
  2-LTM HA pair
       |
 +-----+-----+-----+
 |     |     |     |
WAF1  WAF2  WAF3  ...   all active pool members
       |
      CFW
       |
     ELB/app
~~~

### W2 — WAF HA cluster

~~~text
Tenant firewall/VIP
       |
 [2-LTM HA pair]
       |
 WAF-A ACTIVE
 WAF-B standby
       |
      CFW
       |
     ELB/app
~~~

A traffic group has one active WAF owner. This is not the same as W1 where several independent WAFs process the same service concurrently.

### W3 — preferred tenant WAFs plus shared reserve

~~~text
      Tenant 2-LTM HA pair
               |
      +--------+--------+
      |                 |
preferred WAF1/WAF2   shared reserve WAF(s)
(higher priority)     (lower priority contingency)
      \                 /
       +-------+-------+
               |
          CFW -> ELB/app
~~~

Each tenant retains its preferred WAF capacity. Reserve WAFs sit in parallel as lower-priority contingency capacity for failure/maintenance.

### W4 — asymmetric cluster + extra Site 1 WAF

~~~text
Site 1                              Site 2
2-LTM pair                          2-LTM pair
    |                                   |
    +---------------+               WAF HA cluster
    |               |                   |
WAF HA cluster  extra WAF (parallel)  CFW -> ELB/app
    \               /
     +------+------+
            |
       CFW -> ELB/app
~~~

### S1 — tenant LTMs + shared active WAF pool

~~~text
Tenant 1 LTM pair --\
Tenant 2 LTM pair ---\
Tenant 3 LTM pair ----> shared WAF1/WAF2/WAF3/WAF4...
Tenant 4 LTM pair ---/             |
                                  CFW/ELB/app paths
~~~

The shared WAFs are **independent active pool members**, not one HA cluster. This is the current preferred cost/resilience option to validate.

### S2 — shared LTM + shared active WAF pool

~~~text
Tenants 1..4
     |
 shared 2-LTM HA pair
     |
 shared active WAF pool
     |
 tenant/application CFW/ELB paths
~~~

This saves more devices than S1 but also makes the LTM tier a four-tenant common failure/change domain.

### Cross-site shorthand used later

- **X2A** — local LTM borrows a remote-site WAF and routes back to the healthy local CFW/application.
- **X2B** — remote-site front end (firewall/LTM/WAF) serves the client and routes back to the healthy primary-site CFW/application.
- **X2C** — conventional full application/site failover.
- **XD1** — App A stays local but uses a healthy App B in the alternate site.

For the detailed topology/cost analysis see [deployment_options_resilience_summary.md](./deployment_options_resilience_summary.md).

For the current four-tenant comparison, the recommended decision order is:

| Rank | Option | Recommendation |
|---|---|---|
| **1 — best cost/resilience balance** | **Tenant-specific 2-LTM HA pair + shared independent active WAF pool (S1)** | **Preferred option to evaluate first** if multi-tenant WAF policy/routing isolation and aggregate N-2 capacity can be proven |
| **1A — best isolation / simplest blast radius** | **Dedicated W1 with 2 LTMs + 3 independent WAFs per tenant/site** | **Preferred high-isolation option** where appliance cost is secondary to tenant independence |
| **2 — dedicated normal path + shared spare** | **W3: 2 LTMs + 2 preferred WAFs/tenant + shared reserve** | Good resilience, but more operational complexity and only modest device saving versus dedicated 3-WAF W1 |
| **3 — simple HA pair** | **W2b: 2 LTMs + 2-node WAF HA cluster** | Credible for 99.95 with disciplined changes and site recovery; best where simplicity and first-failure connection mirroring matter more than horizontal WAF scale |
| **4 — asymmetric primary-site enhancement** | **W4a** | Use only where stronger Site 1 resilience is deliberately preferred over symmetric DR; not the default recommendation |
| **Not preferred for critical four-tenant service** | **Shared LTM + shared WAF pool/cluster** | Lowest device count but largest common-mode and change blast radius; use only when business accepts multi-tenant outage domain |

The strongest overall recommendation is therefore:

> **Keep the LTM failure domain tenant-specific, and share WAF capacity only if the shared WAF pool is large enough for aggregate N-1/N-2 load and has strong per-tenant policy/change isolation.**

If that operational maturity cannot be demonstrated, use **dedicated W1 with three independent WAFs per tenant/site**.

# 2. What 99.95% means here

99.95% availability permits approximately:

- **4h 22m 48s per year**;
- **21m 54s per average month**;
- **5m 2s per week**.

This is an end-to-end service budget, not a device budget.

A topology that survives hardware failures but causes a user-visible outage during every firmware or policy change can still miss the target.

For a credible 99.95 design:

1. **routine node maintenance should normally be no-outage or seconds-scale**;
2. **single-node failures should stay R0/R1** — no impact or automatic local recovery;
3. **whole WAF-tier/dependency failures should preferably use R2 cross-site component recovery** rather than moving the entire application;
4. **R3 site failover should be reserved for genuine site/application failures**;
5. **R4 manual recovery should be exceptional**.

# 3. Most important operational failure modes

No production incident-rate data is available, so this analysis does not claim statistical probabilities.

For architecture selection, prioritise the failures and changes that are **routine or credible operational events**, then verify the rarer high-impact cases.

## Tier A — design to absorb with little or no user-visible outage

These should not consume meaningful portions of the 99.95 budget:

- one LTM HA member failure;
- one WAF member failure;
- one CFW HA member failure;
- one backend/VM/Pod member failure;
- one circuit/path failure affecting only its user population;
- planned node firmware maintenance;
- planned WAF policy/signature change;
- planned backend/application rolling maintenance.

Preferred outcome:

> **R0/R1: local automatic recovery, stable VIP, no DNS/site failover.**

## Tier B — design to recover automatically without unnecessary application DR

These are less routine but important because they expose topology quality:

- two WAF failures;
- entire local WAF pool/cluster failure;
- one application dependency such as B1 failing;
- full local front-end/LTM tier failure while application remains healthy;
- local CFW service failure while application behind it remains healthy.

Preferred outcome where technically safe:

> **R2: use remote WAF/front-end/dependency capacity while keeping healthy application components in place.**

## Tier C — true DR events

These legitimately require site/application recovery:

- complete site loss;
- application/data service unavailable locally;
- unrecoverable local CFW/platform path;
- multiple correlated infrastructure failures;
- disaster requiring passive application startup.

Preferred outcome:

> **R3 automatic site/application recovery. R4 manual recovery only where business RTO explicitly allows it.**

# 4. 99.95 availability potential by option

The ratings below are **architectural potential**, not measured SLAs.

| Option | Single-node failures | Maintenance while retaining redundancy | 2-WAF / tier failure | Common-mode change risk | 99.95 potential | Executive view |
|---|---|---|---|---|---|---|
| **Dedicated W1, 3 WAF/tenant/site** | Excellent | **Excellent** — drain one WAF and retain two | **Strong** if N-2 capacity | Low tenant blast radius; policy sync still matters | **Very strong** | Best technical/isolation option |
| **S1 tenant LTM + shared 4+ WAF active pool** | Excellent | **Excellent** if aggregate capacity remains | **Strong** if surviving shared nodes carry aggregate N-2 | Higher because WAF config/policy is shared | **Very strong if controls mature** | Best cost/resilience candidate |
| **W3 preferred pair + shared reserve** | Excellent | **Very good** while reserve is free | **Strong for one tenant** if reserve available | Reserve/policy governance shared | **Strong** | Good, but complexity and reserve contention must be managed |
| **W2b 2-node WAF cluster** | Very good | **Moderate** — maintenance leaves one WAF owner | Pair loss causes local WAF outage/site recovery | HA pair/config is common domain | **Strong but less margin** | Simple and credible, not best maintenance headroom |
| **W4a** | Very good | Site 1 very good; Site 2 moderate | Site 1 stronger; Site 2 pair boundary | Asymmetry complicates operations | **Strong but asymmetric** | Niche rather than standard |
| **S2 shared LTM + shared active WAF pool** | Good | WAF maintenance good; shared LTM remains common boundary | Can be strong if pool sized N-2 | **High multi-tenant blast radius** | **Conditional** | Too much shared ingress risk for default critical design |
| **Shared LTM + shared 2-node WAF cluster** | Good for first failure | **Weakest maintenance headroom** | loss of pair removes all tenants' local WAF service | **Very high common-mode blast radius** | **Lowest confidence** | Cost-led design, not recommended default |

# 5. Why W1/S1 generally score best

Independent active WAF pools have an operational advantage over a two-node HA WAF cluster:

~~~text
LTM
 |
 +-- WAF1 active
 +-- WAF2 active
 +-- WAF3 active
~~~

One WAF can be:

- drained;
- upgraded;
- policy-tested;
- removed due to failure;

while the other members continue serving.

With three dedicated WAFs, one can be maintained and another can fail while one still remains, subject to capacity.

With a shared four-node pool, one or two WAFs can be removed only if the remaining pool is sized for the aggregate four-tenant load.

This is the key 99.95 maintainability advantage.

# 6. Why W2 is still valid but not the preferred general default

A W2 pair has a simpler operational model:

~~~text
WAF-A active
WAF-B standby
~~~

Advantages:

- clear HA ownership;
- simple configuration model;
- connection mirroring may improve first-failure WebSocket continuity.

But during maintenance:

~~~text
WAF-A under maintenance
WAF-B serving production
~~~

there is no remaining local WAF peer.

Another WAF failure, bad synchronized policy, or cluster-wide issue can force site recovery.

This does not prevent W2 meeting 99.95, but it leaves **less error and maintenance margin** than a 3+ independent WAF pool.

# 7. Why W3 is not automatically the best compromise

For four tenants, the illustrative counts are:

- dedicated W1 with 3 WAFs/tenant/site: **40 LTM+WAF device-units**;
- W3 with 2 preferred WAFs/tenant + 2 shared reserves/site: **36 units**;
- S1 tenant LTMs + 4 shared active WAFs/site: **24 units**.

W3 saves only four device-units versus fully dedicated 3-WAF W1 in this example, while adding:

- shared reserve admission/prioritisation;
- cross-tenant reserve contention;
- reserve policy readiness;
- more complicated failure interpretation.

W3 remains attractive when the organisation specifically wants:

> dedicated normal-state WAFs for each tenant, but shared spare capacity for maintenance/failure.

If normal-state WAF sharing is acceptable, S1 is more infrastructure-efficient.

# 8. Cross-site capability materially improves the recommendation

Cross-site routing should be a **contingency**, not a dependency for normal service.

## X2A — remote WAF borrowing

Recommended where routing/security permits it.

~~~text
Site 1 LTM
  -> Site 2 WAF
  -> route back
  -> Site 1 CFW/ELB/app
~~~

This can turn:

- complete local WAF-tier loss;

from:

- **~46–150s + T6** site/DNS recovery, or T5/manual DR;

into approximately:

- **~16s-class + T6** component recovery;

while the healthy application remains in Site 1.

## XD1 — remote dependency fallback

Also strongly recommended where application semantics allow it.

~~~text
A1 -> B service VIP
      +-- B1 preferred
      +-- B2 remote fallback
~~~

This prevents one B1 failure from cascading into A/C/D failures and unnecessary site moves.

## X2B — remote front-end route-back

Useful as a secondary contingency if the local LTM/WAF front end is lost while the local CFW/application remains healthy.

It still requires GTM/DNS convergence, so X2A is preferable when the local LTM survives.

# 9. Application type changes whether 99.95 is achievable

Infrastructure HA alone cannot make every application 99.95.

| Application | Infrastructure outcome required | Application requirement |
|---|---|---|
| **Stateless web** | local pool/member failover | safe retry, idempotency, external/shared state |
| **Stateful web** | path/site failover plus state availability | portable session/state, re-auth, transaction reconciliation |
| **WebSocket / long-lived** | connectivity restored | reconnect, backoff+jitter, re-auth, resubscribe, sequence/gap recovery, replay/snapshot |
| **Non-web/L4** | protocol endpoint restored | protocol-specific reconnect, re-resolution and safe transaction replay |

For WebSocket/stateful applications, a topology should not receive a "high 99.95" rating unless the application has been tested for those recovery behaviours.

# 10. Change strategy required to protect 99.95

Regardless of topology:

1. **Never change both sites at once.**
2. **Drain one active member at a time.**
3. **Retain one known-good path while changing WAF policy.**
4. **Do not combine WAF, LTM, CFW and application high-risk changes in one wave.**
5. **Use staging/canary/Policy Diff before global WAF enforcement.**
6. **Do not start a shared-service change if the alternate site/reserve is already degraded.**
7. **Measure business transactions after each change, not only device health.**
8. **For long-lived applications, deliberately trigger reconnect during maintenance rather than waiting indefinitely for sockets to drain.**

The key maintenance acceptance test is:

> Can one component be deliberately removed for change and can one additional unplanned failure still occur without a material service outage?

W1 with 3+ independent WAFs and a sufficiently large shared active pool score best against this test.

# 11. Final recommendation

## Recommended balanced four-tenant target

If shared WAF tenancy is operationally acceptable:

~~~text
Per tenant / per site:
  2-LTM HA pair
        |
        +------------------+
                           |
                 shared active WAF pool
                 4+ WAFs/site initially
                 sized to required aggregate N-2
                           |
                  tenant-specific policy/routing
                           |
                         CFW
                           |
                         ELB
                           |
                    application
~~~

Add:

- X2A remote-WAF contingency where routing/security permits;
- XD1 dependency fallback for suitable App A -> B chains;
- full X2C site DR;
- through-path readiness including CFW/application;
- staged tenant-aware WAF policy deployment.

This is the **preferred cost/resilience option to validate** for four tenants.

## Recommended highest-isolation target

If WAF sharing or cross-tenant policy/change blast radius is unacceptable:

~~~text
Per tenant / per site:
  2-LTM HA pair
        |
  3 independent active WAFs
        |
       CFW
        |
       ELB/app
~~~

This is the **cleanest high-confidence 99.95 architecture** among the compared WAF designs, assuming capacity and application compliance are proven.

## Options not selected as the general default

- **W2b:** acceptable and simple, especially for WebSocket mirroring, but less maintenance/failure headroom.
- **W3:** strong but comparatively complex for modest four-tenant device savings.
- **W4:** strong Site 1 but asymmetric Site 2 makes it harder to operate and prove consistently.
- **shared LTM + shared WAF:** attractive cost, but too large a common-mode tenant blast radius for the default critical-service recommendation.

# 12. Decision gates before final approval

Before selecting S1 or dedicated W1, prove:

1. peak and failure-mode WAF throughput;
2. N-1 and N-2 capacity;
3. one-WAF and two-WAF fault injection;
4. one-LTM failure and full LTM-pair recovery;
5. CFW HA and complete CFW-path failure;
6. cross-site WAF route-back;
7. App A -> B remote fallback;
8. Site 2 aggregate DR capacity;
9. WAF bad-policy rollback/canary;
10. stateless/stateful/WebSocket/non-web recovery;
11. actual end-to-end p95/p99 fault-to-successful-transaction times;
12. planned maintenance with one additional injected failure.

Only after those tests should the design be described as meeting 99.95 rather than merely having **high 99.95 potential**.
