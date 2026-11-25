# Executive Recommendation — EnterpriseWAF Architecture and 99.95% Availability

**Status:** Executive decision summary  
**Primary comparison:** [deployment_options_resilience_summary.md](./deployment_options_resilience_summary.md)  
**Detailed service recovery:** [end_to_end_service_impact_analysis.md](./end_to_end_service_impact_analysis.md)  
**Maintainability:** [maintainability_change_management_analysis.md](./maintainability_change_management_analysis.md)

# 1. Executive decision

## 1.0 Architectural principle — joint responsibility, shared WAF runtime, application-coupled policy

End-to-end 99.95% availability is a **joint responsibility**:

- **Infrastructure teams** (F5/ADC, Network/Security, Cloud Platform) deliver resilient, rolling-upgradeable infrastructure, deterministic routing/SNAT/client-IP header propagation (`XFF` / ELB headers / PROXY Protocol), and layer-accurate health steering;
- **Application teams** build applications that tolerate and recover cleanly from failures (`T6`: retries/idempotency, externalized/replicated state, WebSocket reconnect/replay) and publish explicit Layer-7 readiness, session, and client-IP contracts;
- **Health checks and recovery controls** are built at the exact right layer and clearly articulated so every team can architect against unambiguous boundaries.

Within the WAF tier specifically, do not treat the WAF as identical to a generic router or firewall:

- **WAF runtime/enforcement capacity** may be shared within an approved cloud/security zone;
- **WAF policy** is tightly coupled to the protected application/API and should have application-specific ownership, testing, canary/staging and rollback.

Therefore the target is not "one monolithic shared WAF policy." It is:

> **shared WAF enforcement capacity with application-isolated policies and ≤ 25% change blast radius.**

See [current_architecture_and_invariants.md](./current_architecture_and_invariants.md) for the canonical current-state architecture and baseline invariants (including external client-IP tracking, stateful/sticky/WebSocket requirements, and the potential **≤ 25% maximum impact threshold**), and [future_architecture_improvements.md](./future_architecture_improvements.md) for the target layered health-monitoring, sticky-session/SNAT/header-injection, per-fault-domain Joint Responsibility Matrix (§15C), and `r2800` platform-rebuild model.

The current architecture focus is the **four-tenant extranet estate** (currently running **BIG-IP 17.5.x**, with a confirmed target rebuild standard of **F5 rSeries `r2800` pizza boxes only** running `F5OS-A 1.8.0+` + BIG-IP 21.1.x+, no blade chassis — see [future_architecture_improvements.md §15A](./future_architecture_improvements.md#15a-platform-rebuild-impact-big-ip-175x-current-vs-confirmed-r2800--big-ip-211x--f5os-a-target)). Retain the existing GTM and tenant LTM boundaries in the current target recommendation. Consolidating GTM/LTM may be a valid future optimisation if applications converge onto common private-cloud platforms, but it requires participation from the GTM/LTM/network owners and is not assumed by this WAF analysis.

### Ownership constraint

This WAF architecture can recommend WAF topology, capacity, policy isolation and recovery behavior, but it cannot unilaterally commit:

- GTM/LTM redesign;
- cross-site LTM steering;
- firewall/routing/NAT changes;
- DNS/GTM health-policy changes.

X2A/X2B are therefore **candidate target capabilities** until the owning teams validate them. See [current_architecture_and_invariants.md](./current_architecture_and_invariants.md) and [future_architecture_improvements.md](./future_architecture_improvements.md).

There is no single topology that guarantees 99.95% availability. The target is credible only when:

- common failures recover locally and automatically;
- routine maintenance (4 changes/yr per major stack) does not consume all redundancy;
- a second failure can still be tolerated during important maintenance windows where required (`K + 2` / `N-2`);
- WAF/LTM/CFW/application health checks represent the real service path;
- applications retry/reconnect/recover state correctly (`T6`);
- alternate-site applications, dependencies and data are actually ready;
- common-mode configuration changes are canary-staged (≤ 25% exposure) and reversible.

## 1.1 Topology names used in this document

The shorthand is used only to keep the comparison tables compact. Read the descriptions below before the ranking.

| ID | Plain-English description | Normal traffic model | Main trade-off |
|---|---|---|---|
| **W1-3** | **Tenant/dedicated LTM pair → 3 independent active WAFs/tenant/site** | LTM load-balances across 3 active WAFs per tenant | Hard ≤ 25% (1-tenant) blast radius + full local `N-2` rolling maintenance headroom (on `r2800` + `F5OS-A 1.8.0+`, 2 isolated WAF tenants/box halves WAF boxes 24 → 12 if AWAF fits `4 vCPU / 12 GB RAM`) |
| **W1-2** | **Sub-variant: Tenant LTM pair → 2 independent active WAFs/tenant/site** | LTM load-balances across 2 active WAFs per tenant | Keeps tenant blast radius ≤ 25% and saves 8 WAFs vs `W1-3`, **but** 1 WAF loss cuts that tenant's capacity by 50% and maintenance + 2nd fault removes 100% of that tenant's local WAF tier (requires `X2A`) |
| **W2** | **WAF HA/DSC cluster**, optionally behind an LTM | One WAF owns a traffic group; peer is HA standby for that traffic group | Simple HA and possible first-failure connection mirroring (requires licensed LTM+AWAF), but pair/cluster leaves 0 local WAF redundancy during maintenance |
| **W3** | **Tenant LTM pair + 2 preferred WAFs/tenant + shared reserve WAFs** | Preferred WAFs serve normally; shared reserve is contingency capacity | Keeps normal-state tenant separation but introduces shared reserve governance/contention for only 4 WAFs saved vs `W1-3` |
| **W4** | **Asymmetric cluster design**: Site 1 WAF HA cluster + extra WAF; Site 2 cluster only | Site 1 has extra local capacity; Site 2 has only the cluster | Stronger Site 1 resilience but weaker asymmetric Site 2 DR/maintenance |
| **S1 (baseline, P=4)** | **Existing tenant-specific LTM pairs → 4 shared active WAFs/site** | 4 tenant LTM pairs feed 4 shared active WAFs/site | Lowest shared-WAF box count (8 WAFs total), but no dedicated `+2` rolling + outage + canary buffer if peak load needs `K > 2` |
| **S1+2 (P=4+2=6)** | **Existing tenant-specific LTM pairs → `4 + 2 = 6` shared active WAFs/site (`K+2`)** | Adds **+2 active WAFs/site** above peak `K` for rolling upgrades, unplanned SSD outage & canary testing | **Recommended shared-pool option:** full `r2800` `24 GB` RAM/WAF, 0% outage on rolling + fault + 1-node canary (≤ 17% exposure); requires strict Parent/Child policy isolation & canary gating to respect ≤ 25% cap |
| **S2** | **Shared LTM pair + shared independent active WAF pool** | Tenants share both ingress LTM and WAF capacity | Comparison only; outside current scope; **fails 25% impact cap** at both LTM and WAF tiers |

### W1 — dedicated independent WAF pool (`W1-3` and `W1-2` sub-variant)

~~~text
Tenant firewall/VIP
       |
  2-LTM HA pair
       |
 +-----+-----+-----+
 |     |     |     |
WAF1  WAF2 [WAF3]  ...   W1-3 = 3 active WAFs (N-2) | W1-2 = 2 active WAFs (N-1 only)
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

### S1 & S1+2 — tenant LTMs + shared active WAF pool

~~~text
Tenant 1 LTM pair --\
Tenant 2 LTM pair ---\
Tenant 3 LTM pair ----> shared WAF1..4  [+ WAF5 + WAF6 in S1+2 for rolling / outage / canary]
Tenant 4 LTM pair ---/             |
                                  CFW/ELB/app paths
~~~

The shared WAFs are **independent active pool members**, not one HA cluster. **`S1+2` (`4 + 2 = 6`/site)** is the preferred shared-pool candidate to validate because the `+2` active nodes simultaneously absorb rolling upgrades, an unplanned `r2800` SSD/box outage, and isolated 1-node canary testing.

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

This saves more devices than S1 but also makes the LTM tier a four-tenant common failure/change domain (100% blast radius).

### Cross-site shorthand used later

- **X2A** — local LTM borrows a remote-site WAF and routes back to the healthy local CFW/application.
- **X2B** — remote-site front end (firewall/LTM/WAF) serves the client and routes back to the healthy primary-site CFW/application.
- **X2C** — conventional full application/site failover.
- **XD1** — App A stays local but uses a healthy App B in the alternate site.

For the detailed topology/cost and per-variant scorecard see [deployment_options_resilience_summary.md §8.7](./deployment_options_resilience_summary.md#87-topology-variant-scorecard-25-impact-9995-longest-outage-automanual--proscons).

For the current four-tenant comparison, the recommended decision order is:

| Rank | Option | Recommendation |
|---|---|---|
| **1 — Best cost/resilience + canary balance** | **`S1+2`: Tenant-specific 2-LTM HA pairs + `4 + 2 = 6` shared active WAFs/site** (`8 LTM + 12 WAF = 20 r2800`s on rebuild) | **Preferred shared option to evaluate first** — gives full `24 GB` RAM/WAF + rolling/outage/canary cushion (`≤ 17%` canary exposure) **provided Parent/Child policy isolation & 1-node canary gates keep changes ≤ 25% impact** |
| **1A — Best strict ≤ 25% tenant isolation** | **Dedicated `W1-3` (3 WAFs/tenant/site)** *(or **`r2800` 2-tenant F5OS** = `8 LTM + 12 WAF = 20 r2800`s if AWAF fits `12 GB` RAM)* | **Preferred high-isolation option** — guarantees hard ≤ 25% (1-tenant) blast-radius cap + full `N-2` maintenance headroom without cross-tenant policy risk |
| **2 — Low-cost dedicated sub-variant (conditional)** | **Dedicated `W1-2` (LTM HA → 2 active WAFs/tenant/site)** | Keeps tenant blast radius ≤ 25% and saves 8 WAFs vs `W1-3`, **but** 50% capacity loss on 1 fault & 0 local maintenance `N-2` — viable for 99.95% **only with `X2A`** |
| **3 — Dedicated normal path + shared spare** | **`W3`: 2 LTMs + 2 preferred WAFs/tenant + 2 shared reserves/site** | Good resilience, but more operational complexity and only 4 WAFs saved vs dedicated `W1-3` |
| **4 — Simple HA pair** | **`W2b`: 2 LTMs + 2-node WAF HA cluster** | Credible only with strict changes + `X2A`; zero local redundancy during maintenance; best only where first-failure WS mirroring is essential |
| **5 — Asymmetric primary-site enhancement** | **`W4a`** | Use only where stronger Site 1 resilience is deliberately preferred over symmetric DR; Site 2 DR remains fragile |
| **Not preferred / fails 25% cap** | **`S1` baseline (if `K>2`) & `S2` (shared LTM + shared WAF)** | `S1` (4/site) lacks canary+outage buffer if `K>2`; `S2` fails the 25% impact cap at both LTM and WAF tiers (100% blast radius) |

The strongest overall recommendation is therefore:

> **Keep the LTM failure domain tenant-specific, and choose between `S1+2` (full `24 GB` `r2800` boxes with `+2` rolling/outage/canary nodes + strict Parent/Child canary discipline) and dedicated `W1-3` (or `r2800` 2-tenant F5OS `W1-3` if Phase 0 AWAF benchmarking fits `12 GB` RAM) — both land at `20 × r2800` total on rebuild.**

If cross-tenant WAF policy maturity cannot be guaranteed to hold changes **≤ 25% impact**, select **dedicated `W1-3`** (3 independent WAFs per tenant/site).

# 2. What 99.95% means here

The **99.95% availability target covers BOTH managed (planned maintenance, firmware/OS upgrades, patching, certificate rotations, policy changes) AND unmanaged (unplanned hardware, software, network, or dependency failure) outages combined**. It permits approximately:

- **4h 22m 48s per year** (managed + unmanaged combined);
- **21m 54s per average month**;
- **5m 2s per week**.

This is an **end-to-end application-delivery service budget** across all teams (F5/ADC, Network/Security firewalls, Cloud Platform CFW/ELB, and Application teams), not a single-device budget — even though initial delivery execution focuses on the WAF tier.

A topology that survives unmanaged hardware failures but causes a user-visible outage during managed firmware or policy changes will still breach the 99.95% target.

For a credible 99.95 design:

1. **managed maintenance (planned changes/upgrades) must normally be zero-outage or seconds-scale** (`R0`/`R1`);
2. **single-node unmanaged failures must stay `R0`/`R1`** — zero user impact (`R0`) or automatic local recovery (`R1`);
3. **whole WAF-tier or dependency failures should preferably use `R2` cross-site component/dependency recovery** (`X2A`/`X2B`/`XD1`) rather than moving the entire application;
4. **`R3` automatic site/DNS failover should be reserved for genuine site/application failures**;
5. **`R4` manual/warm-DR recovery should be exceptional**.

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

# 4. 99.95% availability, 25% impact, longest outage & auto/manual potential by option

The ratings below are **architectural potential**, not measured SLAs. Full per-variant pros/cons are in [deployment_options_resilience_summary.md §8.7](./deployment_options_resilience_summary.md#87-topology-variant-scorecard-25-impact-9995-longest-outage-automanual--proscons) and per-fault-domain Infra vs. App obligations are in [future_architecture_improvements.md §15C](./future_architecture_improvements.md#15c-joint-responsibility--fault-domain-recovery-matrix-infrastructure-vs-application-per-layer).

| Option | ≤ 25% Impact Cap | Maintenance + 2nd Failure (`4/yr`) | Longest Expected Outage / Recovery | Auto vs. Manual | 99.95% Potential | Executive View |
|---|---|---|---|---|---|---|
| **Dedicated `W1-3` (3 WAF/tenant/site)** | **PASS** (1 tenant = 25% hard cap; 1 node ≤ 8% estate) | **Excellent** — drain 1 WAF and retain 2 (`N-2`) | 1–2 WAFs: **0s–16s + `T6`** (`R0`/`R1`); full tier: **~16s (`X2A`)** or **~46–150s (`R3`)**; Site DR: **`R3`/`R4`** | **Auto** (`R0`/`R1`/`R2`/`R3`); **Manual** only for warm DR (`T5`) / rollback | **Very Strong** | Best strict isolation option (`20 r2800`s if 2-tenant F5OS fits `12 GB` RAM) |
| **`S1+2`: Tenant LTMs + `4+2=6` shared WAFs/site** | **CONDITIONAL PASS** (1-node canary ≤ 17%; requires Parent/Child policy isolation + canary gates) | **Excellent** — `+2` active nodes absorb **rolling upgrade + unplanned SSD outage + canary** | 1–2 WAFs: **0s–16s + `T6`** (`R0`/`R1`); full shared tier: **~16s (`X2A`)** or **~46–150s (`R3` 4-tenant surge)** | **Auto** (`R0`/`R1`/`R2`/`R3`); **Manual** for canary promotion / rollback / warm DR | **Very Strong** *(with mature controls)* | Best cost/resilience + full `24 GB` `r2800` RAM (`20 r2800`s on rebuild) |
| **Dedicated `W1-2` (Sub-variant: 2 WAF/tenant/site)** | **PARTIAL** — tenant ≤ 25%, **but 1 WAF loss = 50% tenant capacity**; maint + fault = 100% of tenant | **Weak (0 local `N-2`)** — risky on single-SSD `r2800` during 4/yr upgrades without `X2A` | 1 WAF: **0s–16s + `T6`** (`R1`). Maint + 2nd fault: **~16s (`X2A`)** or **~46–150s (`R3`)** / **`T5` (mins+)** | **Auto** (1st WAF / `X2A` / `R3`); **Manual (`T5`)** if passive DR triggered | **Moderate (requires `X2A`)** | Lower-cost dedicated sub-variant; do not deploy without `X2A` |
| **`S1` baseline (`4` shared WAFs/site)** | **CONDITIONAL / TIGHT** (1 node = 25%; no canary+outage buffer if `K > 2`) | **Moderate** if peak `K > 2` (drops below 100% peak during rolling + fault) | 1 WAF: **0s–16s + `T6`**; maint + fault (`K > 2`): **throttled / `X2A` / `T5`** | **Auto** (`R1`/`R2`); **Manual** on capacity overload / policy rollback | **Strong only if `K ≤ 2`** | Upgrade to **`S1+2`** for safe canary + rolling + outage headroom |
| **`W3` preferred pair + 2 shared reserve/site** | **PASS (normal) / MEDIUM (contingency)** | **Very Good** while reserve is free & synced | 1–2 WAFs: **~16s + `T6`** (`R1` via reserve if uncontended); else **`R2`/`R3`** | **Auto** (LTM Priority Group); **Manual** reserve governance | **Strong** | Complex reserve governance for only 4 WAFs saved vs `W1-3` |
| **`W2b` 2-node WAF HA cluster** | **PARTIAL** (≤ 25% tenant, but 0 local redundancy during maintenance) | **Moderate** — maintenance leaves 1 active WAF owner | 1st WAF: **~3s (`T1`)**; maint + 2nd fault: **~16s (`X2A`)** or **~46–150s (`R3`)** / **`T5`** | **Auto** (`R1`/`R3`); **Manual** failback (resets mirrored WS) & warm DR | **Moderate** | Simple HA / first-failure WS mirroring; weak maintenance margin |
| **`W4a` asymmetric (3 S1 / 2 S2)** | **PASS (tenant ≤ 25%)**, but **Site 2 DR fragile** | Site 1 very good; Site 2 weak (`W2b` boundary) | Site 1: **0s–16s + `T6`**; Site 2 DR: **`R3`/`T5`** on 2nd fault | **Auto** (`R1`); **Manual (`T5`)** if Site 2 loses cluster during DR | **Asymmetric** | Niche; DR site fails symmetric maintenance test |
| **`S2` shared LTM + shared WAF (out of scope)** | **FAIL** — 100% (all 4 tenants) blast radius at LTM + WAF | WAF good; shared LTM = 4-tenant risk | 1 peer: **~3s–16s + `T6`**; bad LTM/WAF change: **minutes+ (`T5`) all 4 tenants** | **Auto** (`R1`); **Manual (`T5`)** multi-tenant rollback | **Lowest Confidence** | Fails 25% impact cap; not recommended default |

# 5. Why W1-3 and S1+2 generally score best

Independent active WAF pools have an operational advantage over a two-node HA WAF cluster:

~~~text
LTM
 |
 +-- WAF1 active
 +-- WAF2 active
 +-- WAF3 active  (or WAF1..4 + WAF5/6 in S1+2)
~~~

One WAF can be:

- drained;
- upgraded;
- isolated for **canary policy/firmware testing**;
- removed due to failure;

while the other members continue serving.

With **`W1-3`** (3 dedicated WAFs/tenant), one can be maintained and another can fail while one still remains (whereas **`W1-2`** leaves zero local WAFs if a second fault occurs during maintenance).

With **`S1+2`** (`4 + 2 = 6` active shared WAFs/site), the `+2` nodes simultaneously absorb **rolling upgrades (4/yr) + 1 unplanned `r2800` SSD outage + 1-node canary testing (≤ 17% exposure)** while keeping ≥ 100% peak capacity active.

This is the key 99.95% maintainability advantage.

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

This does not prevent W2 meeting 99.95, but it leaves **less error and maintenance margin** than **`W1-3`** or **`S1+2`**.

# 7. Why W3 is not automatically the best compromise

For four tenants across two sites (**LTM + WAF devices only; excludes GTM clusters and firewalls**), the illustrative counts are:

- dedicated **`W1-3`** (3 WAFs/tenant/site): **16 LTM + 24 WAF = 40 total LTM+WAF devices** *(or **8 LTM + 12 WAF = 20 `r2800`s** on rebuild at 2 tenants/box if AWAF fits `12 GB` RAM)*;
- **`W3`** (2 preferred WAFs/tenant + 2 shared reserves/site): **16 LTM + 20 WAF = 36 total LTM+WAF devices**;
- dedicated **`W1-2`** sub-variant (2 WAFs/tenant/site) or **`W2b`** HA cluster + LTM: **16 LTM + 16 WAF = 32 total LTM+WAF devices**;
- **`S1+2`** (tenant LTMs + `4 + 2 = 6` shared active WAFs/site for rolling + outage + canary): **16 LTM + 12 WAF = 28 total LTM+WAF devices** *(or **8 LTM + 12 WAF = 20 `r2800`s** on rebuild with 2-tenant LTMs + full-box `24 GB` WAFs)*;
- **`S1` baseline** (tenant LTMs + 4 shared active WAFs/site): **16 LTM + 8 WAF = 24 total LTM+WAF devices**;
- **`S2`** (shared LTM + 4 shared active WAFs/site — out of current scope): **4 LTM + 8 WAF = 12 total LTM+WAF devices**.

See [EnterpriseWAF_Topology_Options.svg](../management-artifacts/diagrams/EnterpriseWAF_Topology_Options.svg) for side-by-side visual topology diagrams of every option (`W1-3`/`W1-2`, `W2`–`W4`, `S1`/`S1+2`, `S2`, and the `r2800` rebuild option).

W3 saves only four WAF devices versus fully dedicated 3-WAF `W1-3` in this example, while adding:

- shared reserve admission/prioritisation;
- cross-tenant reserve contention;
- reserve policy readiness;
- more complicated failure interpretation.

W3 remains attractive when the organisation specifically wants:

> dedicated normal-state WAFs for each tenant, but shared spare capacity for maintenance/failure.

If normal-state WAF sharing is acceptable, **`S1+2`** is more infrastructure-efficient and gives built-in canary/rolling headroom.

# 8. Cross-site capability materially improves the recommendation

Cross-site routing should be a **contingency**, not a dependency for normal service.

## X2A — remote WAF borrowing

Recommended where routing/security permits it (and **mandatory** if deploying **`W1-2`** or **`W2b`** on single-SSD `r2800`s).

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

# 9. Joint responsibility: infrastructure + application requirements by class (`AT1`–`AT4`)

Infrastructure HA alone cannot make every application 99.95%, and application recovery alone cannot compensate for broken multi-hop routing, SNAT port exhaustion, or missing client-IP headers. Both sides have explicit layer-specific obligations (detailed in [future_architecture_improvements.md §15B & §15C](./future_architecture_improvements.md#15b-end-to-end-path-consistency-sticky-sessions-client-ip-headers-snat-and-high-throughput-optimization)):

| Application Class | Infrastructure Obligations (Network / LTM / WAF / CFW / ELB) | Application Obligations (`T6` Recovery & Contracts) |
|---|---|---|
| **AT1 — Stateless web / API** | Split-TCP (`f5-tcp-wan`/`lan`), TLS 1.3 reuse, `OneConnect` + Least Conn, multi-IP SNAT Pool + `XFF` injected at first L7 terminator (LTM, WAF, or **Cloud ELB** if ELB terminates TLS), fast `H2` withdrawal & graceful drain | Safe automated retry with backoff/jitter, idempotent writes, external/shared state only, `/health/ready` contract, read trusted `XFF` |
| **AT2 — Stateful web (sticky sessions)** | `OneConnect` (mandatory so Keep-Alive honors cookies, `K7964`), LTM→WAF stateless `CARP` (`K11362`), WAF passes ELB sticky cookie untouched + `Trust XFF` (`K4816`), **Cloud ELB/Ingress owns single app-node sticky cookie** (and injects `XFF` if terminating TLS), `Receive Disable` drain | **Externalized/replicated session store** (Redis/DB) so sticky sessions optimize speed/locality rather than acting as a SPOF; graceful re-auth & transaction reconciliation |
| **AT3 — WebSocket / long-lived** | Attach F5 **WebSocket profile** (`K84421441`), **NEVER enable `OneConnect`** (`K000151124`), FW/CFW/ELB idle timeouts > app ping, `Action=Reject` (`K15095`), `XFF` on Upgrade handshake, do not rely on AWAF mirroring across N>2 | Mandatory client reconnect + exponential backoff/jitter + re-auth + resubscribe + sequence-gap replay/snapshot |
| **AT4 — Non-web / Layer-4** | Performance (L4) + `FastL4` (`K09948701`), bypass external WAF where permitted, symmetric L4 hashing, no-SNAT inline routing (or SNAT Pool + PROXY Protocol; pin/avoid SNAT for IP ACLs & passive FTP `K15249`) | Protocol-native reconnect, DNS/service re-resolution, safe transaction replay, PROXY Protocol parsing if behind SNAT |

For WebSocket/stateful applications, a topology should not receive a "high 99.95" rating unless both the infrastructure multi-layer path and the application recovery behaviours have been tested together.

# 10. Change strategy required to protect 99.95% and ≤ 25% impact

Regardless of topology:

1. **Never change both sites at once.**
2. **Drain one active member at a time.**
3. **Retain known-good paths while canary-testing WAF policy on 1 node (≤ 17–25% exposure in `S1+2` / `W1-3`).**
4. **Do not combine WAF, LTM, CFW and application high-risk changes in one wave.**
5. **Use staging/canary/Policy Diff (7-day Enforcement Readiness, `K82512024`) before global WAF enforcement.**
6. **Do not start a shared-service change if the alternate site/reserve is already degraded.**
7. **Measure business transactions (`H6`) after each change, not only device health.**
8. **For long-lived applications, deliberately trigger reconnect during maintenance rather than waiting indefinitely for sockets to drain.**

The key maintenance acceptance test is:

> Can one component be deliberately removed for change/canary and can one additional unplanned failure still occur without a material service outage or exceeding the 25% impact cap?

**`W1-3`** and **`S1+2`** (`4 + 2 = 6` active WAFs/site) score best against this test.

# 11. Final recommendation

## Recommended balanced four-tenant target (`S1+2`)

If shared WAF tenancy with strict Parent/Child policy isolation and 1-node canary gating is operationally acceptable:

~~~text
Per tenant / per site:
  2-LTM HA pair (or 4 × r2800/site @ 2 LTM tenants/box on rebuild)
        |
        +------------------+
                           |
                 shared active WAF pool (S1+2)
                 4 + 2 = 6 active r2800s/site (24 GB RAM each)
                 [+2 nodes absorb rolling upgrades + 1 SSD outage + canary]
                           |
                  Parent/Child tenant policy & routing isolation
                           |
                         CFW
                           |
                         ELB (authoritative AT2 sticky cookie; injects XFF if terminating TLS)
                           |
                    application (T6 retry/session-store/WS-replay + /health/ready)
~~~

Add:

- X2A remote-WAF contingency where routing/security permits;
- XD1 dependency fallback for suitable App A -> B chains;
- full X2C site DR;
- through-path readiness including CFW/application;
- staged 1-node canary tenant-aware WAF policy deployment (keeping blast radius ≤ 25%).

This is the **preferred cost/resilience + full-RAM option to validate** for four tenants (**`20 × r2800` total** on rebuild).

## Recommended highest-isolation target (`W1-3`)

If shared WAF policy/change blast radius exceeding 25% is unacceptable:

~~~text
Per tenant / per site:
  2-LTM HA pair (or 4 × r2800/site @ 2 LTM tenants/box on rebuild)
        |
  3 independent active WAFs (W1-3; or 6 × r2800/site @ 2 WAF tenants/box if AWAF fits 12 GB RAM)
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

# 12. Decision gates & six operational guardrails before final approval

Before selecting **Shared 6-WAF (`S1+2`)** or **Dedicated 3-WAF (`W1-3`)**, execute [phase0_discovery_and_signoff_checklist.md](./phase0_discovery_and_signoff_checklist.md) and prove:

1. peak and failure-mode **`r2800` AWAF RAM (`12 GB` vs. `24 GB`), CPU, HTTP RPS, TLS TPS, and WebSocket** throughput (no FPGA, 8 vCPU);
2. `K + 2` (`N-2`) degraded capacity and **100% Site 2 aggregate DR surge**;
3. one-WAF and two-WAF fault injection (plus 1-node canary staging `≤ 25%` impact);
4. one-LTM failure and full LTM-pair recovery;
5. CFW HA and complete CFW-path failure (zero `T9C` false-green);
6. cross-site WAF route-back (`X2A`) and `App A -> B` remote fallback (`XD1`);
7. WAF false-positive `403` mitigation, **declarative config-as-code** (AS3 / Declarative WAF / `cloud-init`), and business-transaction `H6` synthetics;
8. **automated TLS/mTLS certificate lifecycle** and `XFF` / Cloud ELB header alignment;
9. **end-to-end `X-Correlation-ID` observability** (with AWAF Support ID) and **retry-storm jitter/rate-limiting** under failover;
10. stateless/stateful/WebSocket/non-web recovery (`AT1`–`AT4`), measuring **`T6a` (client auto vs. manual user steps)** + **`T6b` (server auto)** vs. **`T5` (manual startup/DB)**;
11. **Tier 1 (Active/Active → 99.95% eligible) vs. Tier 2/3 (Active/Passive warm DR → 99.9%/99.5%)** application classification and **signed cross-team RACI**;
12. **parallel greenfield `17.5.x → r2800 (21.1.x+)` cutover + instant rollback** (ahead of Jan 2029 EoTS) and planned maintenance with one additional injected failure.

See [future_architecture_improvements.md §15D](./future_architecture_improvements.md#15d-six-essential-operational--architectural-guardrails-target-state) for the full guardrail specifications and RACI matrix. Only after those tests pass should a **Tier 1** service be described as meeting 99.95% rather than merely having **high 99.95% potential**.
