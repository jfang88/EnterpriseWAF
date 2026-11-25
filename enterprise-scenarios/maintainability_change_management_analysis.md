# Maintainability, Change Safety and Availability Analysis

**Status:** Derived analysis — second lens after failure/recovery  
**Stable baseline:** [current_architecture_and_invariants.md](./current_architecture_and_invariants.md)  
**Target improvements:** [future_architecture_improvements.md](./future_architecture_improvements.md)  
**Changeable assumptions:** [analysis_variables_and_f5_assumptions.md](./analysis_variables_and_f5_assumptions.md)  
**Failure analysis:** [common_failure_matrix.md](./common_failure_matrix.md)

## 1. Purpose

This document evaluates how safely each WAF topology can be monitored, patched, upgraded and changed while preserving service availability.

The first analysis lens asks:

> What happens when something fails?

This second lens asks:

> Can we make routine and emergency changes without creating an outage, exhausting redundancy, or extending recovery time?

The two lenses are related but not identical. A topology can survive hardware failure yet still be difficult to maintain safely.

---

# 2. Availability objective

Evaluate **99.95% total availability** at:

1. component/service tier;
2. tenant application-delivery path;
3. end-to-end application service.

The **99.95% target explicitly includes BOTH managed outages (planned maintenance, patching, upgrades, certificate rotations, policy changes) AND unmanaged outages (unplanned hardware/SSD, software, network, or dependency failures) combined**:

| Period | Maximum unavailable time at 99.95% (managed + unmanaged) |
|---|---:|
| Year | 4h 22m 48s (`262.8 min`) |
| Average month | 21m 54s |
| Week | 5m 2s |

### End-to-end 4 changes/year per major tech stack check

Across the 9 major end-to-end tech stacks (Edge FW, GTM, Tenant LTM HA, WAF, Internal FW, Cloud FW `CFW`, Cloud `ELB`/Platform, Application tier `A/B/C/D`, and Database/State), **4 planned updates/year per stack = ~36 managed change waves/year per active site** (plus `F5OS-A` host upgrades on `r2800` pizza boxes):

- **If every stack supports rolling drain or clean HA failover:** ~36 planned waves/year consume only **~4–12 min/year** (~2%–5% of the `262.8 min` budget), leaving **~250 min/year** for unmanaged failures — **99.95% is achievable for Tier 1 (Active/Active + automated `T6a`/`T6b`) services**.
- **If Apps (`A/B/C/D`), DB, or `CFW` require 15–30 min offline restarts (manual `T5`), or poorly architected clients force manual user refresh/re-login (`T6a` manual):** just 2–3 stacks × 4 changes/year consume **180–240+ min/year**, breaching 99.95% before a single unmanaged failure occurs — regardless of WAF topology.
- **`K + 2` (`N-2`) active-pool sizing & `≤ 25%` canary rule:** In **`S1+2` (`4 + 2 = 6` active shared WAFs/site)** or **`W1-3` (`3` dedicated WAFs/tenant/site)**, deploying **`K + 2` active pool members** simultaneously absorbs **1 planned rolling upgrade + 1 simultaneous unplanned `r2800` single-SSD/host-reboot outage + 1-node canary testing (`≤ 17%` exposure in `S1+2`, `≤ 8%` in `W1-3`)** with `0 sec` planned WAF outage. By contrast, **`W1-2` (2 WAFs/tenant)** and **`W2b` (DSC pair)** drop to `N+0` during upgrades and require `X2A` remote-WAF borrow to survive a second fault.
- **Declarative config-as-code, certificate automation & parallel `17.5.x → r2800` cutover (`future_architecture_improvements.md §15D`):** Manual GUI edits across 12–24 WAFs create config drift and false-positive `403` outages; use **Git-backed AS3 / Declarative WAF / `cloud-init`**, automated TLS/mTLS certificate renewal (preventing 100% expired-cert outages), emergency `403` mitigation runbooks, and a **parallel greenfield `r2800` (`F5OS-A 1.8.0+` + BIG-IP 21.1.x+) build with phased per-tenant canary cutover** ahead of BIG-IP 17.5.x End of Technical Support (**January 1, 2029**, `K15643`).

Component availability is not the same as end-to-end availability. For illustration, five independent serial components each operating at 99.95% would yield only about **99.75%** end-to-end availability before accounting for redundancy, failover, common-mode failures or application recovery.

Therefore the relevant question is not whether each F5 appliance is 99.95% available. The relevant question is whether the **redundant service path** remains available while failures and planned changes occur.

---

# 3. F5 operational capabilities relevant to maintainability

## 3.1 Node/pool-member drain (`K13310`, `K12818`)

BIG-IP LTM supports two distinct maintenance drain states plus monitor-driven draining:

- **`Disabled` (`session user-disabled`):** stops new general connections, but **still accepts new connections matching an existing persistence session** (e.g., cookie/source-IP persistence);
- **`Forced Offline` (`session user-disabled state user-down`):** blocks **all** new connections (including persistent sessions) while allowing existing active sockets to finish — or resets them immediately when pool `Action On Service Down = Reject` (`K15095`);
- **`Receive Disable String` (`K12818`):** lets an application or WAF readiness endpoint signal `Up (disabled)` so LTM drains the member automatically during CI/CD or rolling waves.

Operational implication:

- draining is preferable to immediately forcing a healthy serving member offline;
- each application type needs a maximum drain time;
- long-lived sockets may require explicit graceful reconnect rather than waiting indefinitely.

## 3.2 Configuration synchronization

BIG-IP Device Service Clustering supports configuration synchronization across device groups.

Operational implications:

- synchronized configuration prevents drift;
- automatic synchronization can also turn a bad change into a common-mode failure very quickly;
- manual synchronization provides a validation gate but requires stricter process discipline;
- F5 requires device-group members used for configuration synchronization to run compatible/same BIG-IP software versions according to the deployed release.

For risky changes, consistency and blast-radius reduction must be balanced deliberately.

## 3.3 Advanced WAF policy synchronization and Live Update (`K82512024`)

Advanced WAF/ASM can synchronize security policies/configuration across multiple systems using ASM-enabled device groups, including Sync-Only groups for scaled deployments.

This is useful for W1/W3/S1 independent WAF pools, but it means:

> "Independent dataplane nodes" do not automatically mean "independent change failure domains."

If the same policy change is automatically synchronized to every node, a logical policy error can still affect the entire pool.

For **ASM Live Update** (`K82512024`), `liveupdate.allowautoinstallonsecondary` defaults to `false` on DSC device groups; prefer **Scheduled or Manual** signature installation paired with staging rather than uncontrolled `Real Time` installation in production.

## 3.4 WAF policy staging

Advanced WAF supports an enforcement-readiness/staging period (default **7 days**) for new/changed policy entities and attack signatures.

While staged, violations can be observed without immediately applying blocking behavior.

This is one of the strongest controls for reducing WAF rule-change outages caused by false positives.

## 3.5 WAF Policy Diff

Advanced WAF Policy Diff can compare active, inactive, staging and exported policies.

Use it as part of:

- pre-change review;
- blue/green policy comparison;
- audit;
- rollback verification.

## 3.6 BIG-IQ centralized change management

Where BIG-IQ is deployed as the management plane, it can provide:

- centralized device/configuration management;
- pre-deployment evaluation;
- scheduled deployment;
- partial/object-level deployment;
- snapshots;
- audit history;
- configuration-difference review;
- software-image management for BIG-IP devices.

BIG-IQ evaluation is valuable because it allows changes to be reviewed before deployment.

Important operational caveat:

> Cancelling a deployment is not the same as rollback; some changes may already have deployed.

Rollback needs a separate known-good snapshot/configuration strategy.

## 3.7 BIG-IP software upgrade behavior and GTM-first order (`K25923322`)

BIG-IP upgrades should not be assumed to be in-service at the individual appliance level on current **BIG-IP 17.5.x** or target **BIG-IP 21.1.x**:

- F5 documents that **in-place upgrade in BIG-IP 21.1.x is experimental** and components requiring reboot still take the device offline (full in-place upgrade support starts in **BIG-IP 22.0.x**);
- **Mandatory upgrade order across BIG-IP DNS (GTM) and LTM (`K25923322`, `K13703`):** because `big3d` is only backwards compatible, always upgrade **BIG-IP DNS first**, immediately followed by running `big3d_install` on monitored BIG-IP LTM devices before upgrading LTM.

Availability during upgrades therefore comes from:

- HA peer;
- independent pool members;
- spare/reserve capacity;
- alternate site;
- correct traffic draining and sequencing.

---

# 4. Maintainability principles

Use these as design requirements.

## MC1 — never consume all redundancy for routine change

If a topology requires all WAF/LTM/GTM nodes to be taken through a coordinated outage, it is not suitable for continuous 99.95%-style operation without another serving path.

## MC2 — one change unit at a time

Where supported:

1. remove/drain one unit;
2. change it;
3. validate it;
4. return it to service;
5. observe;
6. only then proceed.

## MC3 — one site at a time

Do not perform routine firmware or high-risk policy changes simultaneously in both sites.

The unmodified site is an important rollback/fallback domain.

## MC4 — keep failure reserve during maintenance

An N+1 topology can become N+0 when one device is intentionally offline.

For critical services, consider whether the design needs **N+2** or remote/site reserve so it can tolerate one unplanned fault during one planned maintenance event.

## MC5 — separate firmware and policy blast radius

Do not combine:

- firmware upgrade;
- LTM configuration change;
- WAF policy rewrite;
- major application change;

into the same maintenance wave unless there is a compelling reason.

Separate waves make diagnosis and rollback much easier.

## MC6 — use canary/staging where the topology permits

A safe change path should preferably expose a small percentage of traffic or a controlled test population before full rollout.

## MC7 — monitor service, not only device health

"All BIG-IP devices are green" is insufficient.

Monitor:

- end-to-end synthetic application transaction;
- external-user path;
- internal-user path;
- dependency path;
- WAF security behavior;
- GTM response correctness.

---

## MC8 — shared-service change blast radius must be explicit

For four-tenant shared LTM/WAF designs, maintenance and policy changes must be evaluated against **simultaneous multi-tenant impact**.

A shared pool can reduce appliance count, but a bad change to:

- shared LTM policy/iRule;
- shared WAF policy/signature/configuration;
- shared routing;
- shared reserve capacity;
- shared management/synchronization plane

can affect several tenants at once.

Require:

- tenant-aware canary scope where possible;
- per-tenant health/transaction validation;
- aggregate capacity headroom during maintenance;
- rollback that does not depend on the same failed shared configuration;
- explicit block on shared maintenance when the alternate site/shared reserve is degraded.

# 5. Monitoring complexity by topology

| Topology | Monitoring difficulty | Why |
|---|---|---|
| **W1 — independent WAF pool per site** | **Medium** | More individual WAF nodes, but simple pool/member state; easy to expose capacity and drain state |
| **W2 — WAF HA cluster per site** | **Low-Medium** | Fewer logical services; need cluster/traffic-group/sync/mirroring visibility |
| **W3 — tenant WAFs + shared reserve** | **High** | Must monitor tenant pools, shared reserve capacity, policy residency, cross-tenant allocation and reserve contention |
| **W4 — Site 1 cluster + extra WAF; Site 2 cluster only** | **High** | Asymmetric topology; extra Site 1 node has different role/change path; Site 2 has lower maintenance headroom |

Minimum dashboard view should include:

- GTM health/status per app/site;
- LTM virtual/pool/member state;
- WAF node/cluster state;
- WAF config/policy sync state;
- current serving capacity versus required capacity;
- connection count per node;
- devices draining/disabled/forced offline;
- cross-site contingency status;
- reserve/spare state;
- application readiness;
- end-to-end synthetic health.

---

# 6. Firmware upgrade strategy by topology

## W1 — independent WAF pool

### Recommended rolling process

    Pool: WAF1 WAF2 WAF3 ...

    Drain WAF1
       -> upgrade WAF1
       -> validate
       -> canary/re-enable
       -> observe

    Drain WAF2
       -> upgrade
       -> validate
       -> re-enable

    Continue one node at a time

### Strengths

- strongest natural rolling/blue-green behavior;
- traffic can remain on unchanged pool members;
- easy to stop rollout after first node;
- one upgraded node can act as canary;
- 3+ nodes provide more maintenance headroom than a 2-node pool.

### Weaknesses

- WAF policy/config synchronization across mixed software versions must follow F5-supported version rules;
- if only two nodes exist, taking one offline means there is no local WAF redundancy during maintenance;
- canary firmware is only useful if the upgraded node can safely rejoin while peers are on the prior release.

### 99.95 view

**Good**, especially with 3+ nodes and N-1 capacity.

A 2-node pool can remain serving during one-node maintenance, but it is operating without local failure redundancy until the second node is restored.

---

## W2 — clustered WAF pair

### Recommended pattern

Use the F5 release-specific active/standby upgrade process.

Conceptually:

    active old version
    standby old version

        |
        v

    upgrade standby / non-serving node
        |
    validate
        |
    controlled failover
        |
    observe upgraded active node
        |
    upgrade former active
        |
    restore/sync/validate pair

F5's documented active-standby upgrade procedures use a standby-first approach in supported workflows, but the exact target-release procedure is authoritative.

### Strengths

- fewer nodes to coordinate;
- established HA failover model;
- easy operational mental model;
- connection mirroring may reduce disruption for supported traffic.

### Weaknesses

- during upgrade, the pair temporarily loses its normal redundancy;
- config/device-group version compatibility limits how long mixed software can remain;
- a bad synchronized WAF/LTM configuration can affect both nodes;
- true device-level blue-green is weaker because cluster peers are intended to operate consistently.

### 99.95 view

**Good if upgrades are tightly controlled and the alternate site remains healthy.**

The maintenance window itself may not produce service downtime, but it creates a period of elevated risk because the local cluster is effectively single-node.

---

## W3 — tenant WAFs + shared reserve

### W3 LTM service: 2-device versus 3-device DSC

A two-device tenant LTM pair is easier to operate, but taking one device out for firmware/change leaves no local LTM redundancy.

A three-device Sync-Failover group can improve maintainability:

- take one LTM out of service;
- retain two local LTMs;
- validate/upgrade the first device;
- return it;
- proceed to the next device.

This is valuable for a 99.95% objective because planned maintenance no longer consumes the entire local LTM redundancy budget.

With multiple traffic groups, active ownership can also be spread across the three devices and F5 load-aware/ordered failover can choose a next-active device.

Trade-offs:

- more DSC/failover-order testing;
- larger synchronized configuration blast radius;
- more capacity planning;
- not equivalent to three independent active copies of the same VIP.

**Maintainability conclusion:** W3-L3 is attractive when the business wants to remain locally redundant during LTM maintenance. W3-L2 remains simpler where alternate-site recovery is acceptable during the maintenance risk window.



### Recommended pattern

Use shared reserve as controlled maintenance capacity:

    Tenant preferred WAFs: A1 A2
    Shared reserve: R1 R2

    move/drain traffic from A1 -> R1/A2
        |
    upgrade A1
        |
    validate A1
        |
    return A1
        |
    repeat A2

A reserve WAF can also be used as a blue/green target for a new firmware/policy combination if policy isolation is sound.

### Strengths

- excellent maintenance flexibility;
- reserve capacity can preserve local redundancy while a preferred WAF is offline;
- canary changes can be run on a reserve or one preferred node;
- potentially minimizes service interruption.

### Weaknesses

- maintenance consumes the same reserve needed for real failures;
- two tenants must not simultaneously assume the same spare capacity;
- reserve WAF must have the correct tenant policy/config;
- operational scheduling becomes a shared enterprise resource problem;
- mixed firmware/policy combinations can become complex.

### 99.95 view

**Potentially very strong**, but only if reserve capacity is governed.

Maintenance should be blocked or escalated when:

- a reserve is already serving another tenant;
- another site is degraded;
- the remaining reserve cannot tolerate a concurrent failure.

---

## W4 — Site 1 cluster + extra active/spare WAF; Site 2 cluster only

### Site 1

The extra WAF provides a powerful maintenance tool.

Possible change sequence:

    Site 1 cluster = production
    Extra WAF = blue/canary

        |
    load target firmware/policy on extra WAF
        |
    validate
        |
    send limited traffic
        |
    shift/drain cluster if required
        |
    upgrade cluster members
        |
    restore preferred topology

### Site 2

Site 2 has only the WAF cluster.

Maintenance therefore behaves much more like W2.

### Strengths

- strongest local blue/green option in Site 1;
- extra WAF can be used to prove firmware/policy before touching the cluster;
- can preserve Site 1 service while cluster members are changed.

### Weaknesses

- operational processes differ between sites;
- Site 2 does not have equivalent blue/green headroom;
- if DR is active in Site 2, maintenance is less forgiving;
- extra WAF and clustered pair may require different config/sync handling;
- W4b without an ingress LTM has a much harder traffic-shift/drain problem.

### 99.95 view

**Very strong in Site 1; weaker operationally in Site 2.**

The asymmetry must be explicitly reflected in maintenance runbooks and SLO risk.

---

# 7. LTM maintenance and rule changes

## Firmware

For an LTM HA pair:

1. confirm pair health/config sync;
2. capture backup;
3. move active traffic groups away from node under change;
4. upgrade non-serving node;
5. validate interfaces, routes, pools, monitors, virtual servers and application transaction;
6. move traffic to upgraded node;
7. observe;
8. upgrade former active;
9. restore desired traffic-group placement;
10. test failover.

Do not upgrade both LTM members together for routine maintenance.

## LTM configuration / iRules / policies

Prefer:

- centralized change control;
- pre-deployment diff/evaluation;
- object-level changes where possible;
- test virtual/pool or canary application before production;
- explicit rollback.

For HA peers, do **not** deliberately leave active and standby on materially different production traffic configurations merely to simulate blue-green. The safer blue-green boundary is normally:

- a separate virtual server/pool;
- separate WAF member;
- separate application target;
- separate site;
- or controlled BIG-IQ deployment object set.

---

# 8A. Platform/cloud firewall (CFW) maintenance

For private-cloud applications, the CFW is an inline stateful tier immediately before the ELB/service endpoint.

Maintenance/change analysis must therefore include:

- CFW HA/member upgrades;
- policy/rule changes;
- NAT/SNAT ownership;
- session/state synchronization where supported;
- route changes;
- drain/connection-aging behavior;
- certificate/TLS inspection changes where applicable;
- validation from both external and internal paths;
- application dependency flows through the CFW;
- full CFW context/service rollback.

A CFW maintenance event can have a larger application blast radius than an ELB member change because several ELBs/applications may share the same CFW context.

Preferred sequence:

1. confirm CFW peer/context health;
2. verify surviving CFW capacity;
3. drain or move state where supported;
4. change one member/context unit at a time;
5. validate NAT, routing and representative application transactions;
6. validate App A -> B/C internal flows;
7. observe before changing the peer;
8. retain the alternate site as a rollback/fallback domain.

Do not combine high-risk CFW policy/NAT changes with WAF, LTM and application releases in the same wave unless required.

# 8. GTM / BIG-IP DNS maintenance

GTM is control-plane infrastructure, so maintenance must preserve DNS resolution even when one GTM/device/site is unavailable.

Preferred pattern:

- stagger one GTM node at a time;
- stagger sites;
- confirm authoritative DNS remains reachable externally;
- confirm iQuery/LTM visibility after each change;
- validate actual returned VIPs for representative clients/resolvers;
- do not perform a GTM-wide change simultaneously with a site-wide LTM/WAF change unless necessary.

Firmware/software compatibility and synchronization behavior can differ by BIG-IP release, so use the version-specific BIG-IP DNS upgrade procedure.

A GTM change should be validated with:

- direct DNS query;
- health status;
- expected primary/secondary answer;
- TTL;
- external resolver path;
- failure of one GTM/site during the maintenance state.

---

# 9. WAF rule and signature deployment

## Lowest-risk pattern

    Candidate change
       |
    Policy Diff / review
       |
    staging / enforcement-readiness
       |
    test / observe false positives
       |
    canary traffic where topology allows
       |
    promote/enforce
       |
    staged sync / wider rollout
       |
    observe
       |
    second site / remaining nodes

## Signature updates

Prefer staging of new/updated signatures where the threat/risk model allows it.

This preserves current protection while observing whether the new signature creates false positives before full enforcement.

## Policy synchronization

### Automatic sync

Best for:

- low-risk consistency;
- mature/well-tested policy;
- rapid drift prevention.

Risk:

- a bad policy can become a multi-node outage quickly.

### Manual/staged sync

Best for:

- high-risk rule changes;
- major policy refactor;
- canary validation.

Risk:

- drift;
- operator complexity;
- longer period where nodes intentionally differ.

For W1/W3, consider whether one node can be held outside the main change wave as a known-good rollback pool member.

For W2 clustered pairs, policy canary should preferably occur in:

- a test/inactive policy;
- staging mode;
- separate test virtual;
- separate site;
- or external pre-production environment,

rather than leaving HA peers inconsistent.

---

# 10. Blue-green feasibility matrix

| Change type | W1 | W2 | W3 | W4 |
|---|---|---|---|---|
| WAF firmware | **Strong** node-by-node | **Moderate** rolling HA pair | **Strong** using reserve | **Strong Site 1 / Moderate Site 2** |
| WAF policy | **Strong** if one member/canary path can be isolated | **Moderate**; use staging/policy diff more than peer divergence | **Strong** if reserve policy isolation is mature | **Strong Site 1** using extra WAF |
| LTM firmware | Rolling HA pair | Rolling HA pair where W2b | Rolling HA pair | Rolling HA pair in W4a; N/A at WAF tier for W4b |
| LTM config | Staged/synced HA change | Same | Same | Same |
| GTM firmware/config | Stagger device/site | Same | Same | Same |
| App change | drain backend/app pool; canary/blue-green behind CFW/ELB/application path | same | same | same |
| Emergency rollback | high if known-good WAF remains | high if prior image/config and peer healthy | high if reserve remains known-good | high in Site 1 if extra node is known-good |

---

# 11. Application draining and planned changes

## Stateless web

Ideal for rolling maintenance.

Requirements:

- stop new requests to draining member;
- allow in-flight requests to finish;
- clients retry safe failures;
- state shared/external.

## Stateful web

Additional checks:

- session persistence destination;
- shared session store;
- transaction completion;
- re-authentication behavior;
- maximum session drain time.

If session state is local to the member, planned maintenance may become a user-visible outage.

## WebSocket / long-lived sockets

A normal "wait until connection count reaches zero" strategy may never complete.

Use one of:

- bounded drain window;
- server-initiated graceful close;
- client reconnect instruction;
- rolling reconnect;
- scheduled reconnect event.

Clients must reconnect, re-authenticate and restore state.

A socket application that cannot tolerate deliberate connection movement should be marked **maintenance non-compliant**, even if it survives hardware failures sometimes through connection mirroring.

## App A -> App B

When changing B:

- drain B1;
- verify A automatically uses another healthy B;
- observe retry/circuit-breaker behavior;
- confirm no retry storm;
- confirm connection pools refresh;
- then change the next B instance/site.

This is one of the best practical tests of whether dependency resilience is real.

---

# 12. 99.95 maintainability test

For each topology ask:

### During one-node planned maintenance

- Is service still available?
- Is required capacity still available?
- Can one additional node fail?
- Is the alternate site still untouched?
- Can a bad change be rolled back within the remaining SLO budget?

### During site maintenance

- Can the other site carry production?
- Is its WAF/LTM capacity sufficient?
- Are applications already running?
- Does DNS/GTM converge within the objective?
- Are long-lived sessions recoverable?

### During WAF policy maintenance

- Can false positives be observed before blocking?
- Can one known-good policy path remain?
- Can policy rollback be performed without waiting for a full device rollback?

### During firmware maintenance

- Can the changed node be validated before the next node is touched?
- Is mixed-version duration supported?
- Is config sync frozen/controlled appropriately?
- Does one failure during the upgrade create an outage?

---

# 13. Maintainability scorecard

| Area | W1 | W2 | W3 | W4 |
|---|---|---|---|---|
| Monitoring simplicity | Good | **Very good** | Fair | Fair |
| Rolling firmware | **Very good with 3+ nodes** | Good | **Very good** | **Very good Site 1 / Good Site 2** |
| Blue-green WAF change | **Very good** | Fair-Good | **Very good** | **Excellent Site 1 / Fair-Good Site 2** |
| Config consistency | Good with disciplined sync | **Very good** | Fair-Good | Fair-Good |
| Change blast-radius control | **Very good** if canary member isolated | Fair; synchronized pair is common domain | Good if reserve isolation mature | **Very good Site 1** |
| Drain flexibility | **Very good** | Good | **Very good** | **Very good Site 1** |
| Capacity during maintenance | Good with N+1/N+2 | Fair-Good | **Very good if reserve available** | **Very good Site 1 / Fair-Good Site 2** |
| Operational complexity | Medium | **Low-Medium** | **High** | **High** |
| 99.95 maintainability potential | **High** | **High with careful sequencing** | **High if reserve governance is strong** | **High but asymmetric** |

---

# 13A. Four-tenant maintainability and cost trade-off

Device-count efficiency changes the maintenance risk:

| Pattern | Maintenance advantage | Maintenance risk |
|---|---|---|
| 4x dedicated tenant W1 | tenant-by-tenant rolling change; smallest blast radius | duplicated capacity and more devices to patch |
| W3 preferred + shared reserve | reserve can carry one tenant during maintenance | concurrent maintenance/incidents can exhaust reserve |
| tenant LTMs + shared active WAF pool | fewer WAFs to patch; easy node-by-node WAF rolling changes | each shared WAF change can affect four tenants; aggregate capacity must survive one/two nodes removed |
| shared LTM + shared WAF pool | lowest device/change count | one change wave can affect every tenant; highest common-mode operational risk |
| shared WAF HA cluster | simple pair upgrade | while one node is out, all tenants depend on one active WAF owner/capacity boundary |

For business-critical tenants, reduced device count is only a benefit when the organization can prove that the larger shared change domain still meets the availability target.

See [deployment_options_resilience_summary.md](./deployment_options_resilience_summary.md) for the four-tenant device-count model.

# 13B. Executive 99.95 verdict

This is an **architectural-potential** assessment. It is not a measured SLA.

| Option | 99.95 maintainability potential | Reason |
|---|---|---|
| **Dedicated W1 with 3+ independent WAFs** | **Very strong** | one WAF can be drained while two remain; best canary/rolling flexibility and tenant isolation |
| **Tenant LTM + shared active WAF pool sized for aggregate N-2** | **Very strong if controls mature** | excellent rolling capacity, but shared policy/configuration must not create a four-tenant common-mode outage |
| **W3 preferred + shared reserve** | **Strong** | reserve can preserve redundancy during maintenance; depends on reserve admission, policy readiness and non-contention |
| **W2b two-node WAF HA cluster** | **Strong but less margin** | coordinated rolling change is practical, but one WAF maintenance event leaves only one local WAF owner |
| **W4a** | **Strong but asymmetric** | Site 1 has strong change headroom; Site 2 falls back to W2-like pair behavior |
| **Shared LTM + shared active WAF pool** | **Conditional** | WAF pool may be resilient, but shared LTM/change domain can affect all tenants |
| **Shared LTM + shared two-node WAF cluster** | **Lowest confidence for critical service** | both ingress and WAF tiers have large shared common-mode blast radius |

To protect the 99.95 budget, routine maintenance should normally contribute **seconds or zero outage**, not planned multi-minute outages.

The decision criterion is:

> Can one component be removed for change while the service still tolerates one additional credible failure without forcing broad site recovery?

See [executive_recommendation.md](./executive_recommendation.md) for the final ranked architecture recommendation.

# 14. Critical maintainability failure points

## 14.1 Automatic config sync as a common-mode outage mechanism

A synchronized cluster/pool can be physically redundant but logically fragile.

Bad policy/rule -> sync everywhere -> all healthy appliances reject legitimate traffic.

Controls:

- Policy Diff;
- staging;
- pre-production test;
- canary;
- manual approval for high-risk changes;
- rollback snapshot.

## 14.2 Two-node design during maintenance

Two healthy nodes can meet HA requirements in steady state.

Take one down for maintenance and the system becomes single-node.

This is not necessarily unacceptable, but it must be an explicit risk decision.

For 99.95-sensitive services, 3-node W1, W3 reserve, W4 Site 1 extra WAF, or alternate-site fallback provides more maintenance tolerance.

## 14.3 Shared reserve is not free capacity

In W3, reserve WAFs must be capacity-booked.

Do not schedule maintenance that consumes R1/R2 if:

- another tenant already uses reserve;
- one site is degraded;
- expected peak load exceeds remaining capacity.

## 14.4 Site asymmetry in W4

Site 1 can use the extra WAF for blue-green/canary maintenance.

Site 2 cannot.

If Site 2 is carrying DR traffic, its maintenance strategy must revert to clustered-pair sequencing or use cross-site/return-to-primary capacity.

## 14.5 Application drain incompatibility

Infrastructure may support graceful drain while the application does not.

Examples:

- WebSocket never reconnects;
- stateful session is node-local;
- App A holds a persistent B1 connection forever;
- client does not re-resolve DNS.

These should be recorded as **application maintainability non-compliance**.

## 14.6 Simultaneous change waves

Do not combine:

- Site 1 WAF upgrade;
- Site 2 WAF upgrade;
- GTM rule change;
- major app release;

into one change window without strong justification.

Staggered change is itself a resilience control.

---

# 15. Recommended operating model

## Routine firmware

    pre-check
      -> snapshot/UCS
      -> drain one unit
      -> upgrade
      -> validate component health
      -> validate end-to-end transaction
      -> canary traffic
      -> observe
      -> continue one unit at a time
      -> second site last

## WAF policy/rules

    policy diff
      -> stage
      -> observe
      -> canary
      -> enforce
      -> sync/promote wider
      -> observe
      -> second site/change wave
      -> rollback if thresholds exceeded

## LTM/GTM config

    evaluate/diff
      -> deploy smallest object set
      -> validate virtual/pool/DNS response
      -> observe
      -> propagate
      -> retain snapshot for rollback

## Application release

    deploy new backend version
      -> health/readiness check
      -> add to pool at low/canary weight
      -> observe
      -> shift traffic
      -> drain old version
      -> remove after session/socket criteria met

---

# 16. Maintainability conclusion

The topology with the best failure behavior is not automatically the easiest to operate.

- **W1** provides the cleanest rolling-change model, especially with 3+ WAF nodes.
- **W2** is operationally simple and consistent, but a two-node cluster loses its normal redundancy during member maintenance.
- **W3** provides excellent maintenance flexibility but requires the strongest operational governance because shared reserves become a scheduled resource.
- **W4** provides excellent blue-green flexibility in Site 1 because of the extra WAF, but the asymmetry means Site 2 has a different and less forgiving maintenance process.

For a 99.95% service objective, the preferred design characteristic is not merely "two devices."

It is:

> enough independent serving capacity that one unit can be deliberately removed, the change can be validated, and at least one credible recovery path remains if another fault occurs during the maintenance window.

Application drain/reconnect/state behavior must be included in this assessment. If the application cannot move safely during a planned change, the infrastructure topology alone cannot provide end-to-end maintainability.

---

# 17. F5 references

Official F5 references used for this analysis:

- BIG-IP configuration synchronization:
  https://techdocs.f5.com/en-us/bigip-14-1-0/big-ip-device-service-clustering-administration-14-1-0/managing-configuration-synchronization.html
- Advanced WAF automatic configuration synchronization:
  https://techdocs.f5.com/en-us/bigip-21-1-0/big-ip-asm-implementations/automatically-synchronizing-application-security-configurations.html
- Advanced WAF manual synchronization:
  https://techdocs.f5.com/en-us/bigip-17-5-0/big-ip-asm-implementations/manually-synchronizing-application-security-configurations.html
- Advanced WAF policy maintenance / Policy Diff:
  https://techdocs.f5.com/en-us/bigip-17-5-0/big-ip-asm-implementations/maintaining-security-policies.html
- Advanced WAF staging/enforcement readiness:
  https://techdocs.f5.com/en-us/bigip-17-5-0/big-ip-asm-implementations/changing-security-policy-settings.html
- BIG-IQ core/evaluate/deploy/snapshots/audit:
  https://techdocs.f5.com/en-us/bigiq-7-1-0/big-iq-core-concepts/understanding-core-features-of-big-iq-centralized-management.html
- BIG-IQ pool-member management:
  https://techdocs.f5.com/en-us/bigiq-8-4-1/managing-ltm-and-network-objects-using-big-iq/managing-pools-and-pool-members.html
- BIG-IQ BIG-IP software upgrades:
  https://techdocs.f5.com/en-us/bigiq-8-3-0/managing-big-ip-devices-from-big-iq/big-ip-software-upgrades.html
- BIG-IP in-place upgrade behavior:
  https://techdocs.f5.com/en-us/bigip-21-1-0/big-ip-release-notes/bigip-inplace-upgrades.html
