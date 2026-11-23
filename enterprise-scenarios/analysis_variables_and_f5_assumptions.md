# Enterprise WAF Analysis Variables and F5 Recovery Assumptions

**Status:** Changeable analysis inputs  
**Baseline:** [enterprise_scenario_invariants.md](./enterprise_scenario_invariants.md)  
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
+---+---+---+
|   |   |   |
W1  W2  W3 ... Wn
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

Per site, each tenant has its preferred WAF capacity behind its tenant LTM. One or more shared reserve WAFs may be available to multiple tenant pools.

```text
Tenant LTM pair
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

- Preferred tenant WAFs handle normal traffic.
- Shared reserve WAFs can join a tenant pool when preferred WAF capacity is lost.
- Shared reserve introduces cross-tenant capacity, policy-isolation and operational dependencies.
- The same logical preferred-plus-reserve model may exist in Site 2.
- Site-level GTM recovery remains available in addition to reserve-WAF recovery.

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

Model:

- member removal with defaults: up to roughly the configured timeout;
- new connections then use remaining healthy pool members;
- existing connections through the failed member may reset.

Tune monitor intervals only after testing false-positive/flapping risk.

## T3 — BIG-IP DNS direct health monitor

BIG-IP DNS HTTP/HTTPS/TCP-style monitor documentation commonly shows defaults around:

- Interval: **30 seconds**
- Timeout: **120 seconds**

Therefore a standalone direct GTM monitor can be materially slower than local LTM health detection unless tuned.

For F5-to-F5 environments, prefer integrating BIG-IP DNS with LTM health via the BIG-IP monitor/iQuery where appropriate, and add application-level readiness checks where infrastructure health alone is insufficient.

## T4 — DNS/site failover convergence

End-user site recovery is:

```text
health detection
 + GTM decision/update
 + DNS TTL / recursive-cache expiry
 + client/application DNS cache
 + connection retry/re-resolution
 + alternate-site application readiness
```

Therefore GTM failover is not a single product failover number.

A manual passive-site application startup can dominate the total RTO even when GTM detects the failure quickly.

## T5 — failback

F5 traffic-group auto-failback supports configurable delay; F5 documentation shows a default of 60 seconds when auto-failback is enabled and notes 40–60 seconds can allow state mirroring to re-establish.

For critical services, prefer controlled failback rather than immediate oscillation.

# 6. F5 connection mirroring implications

F5 recommends connection mirroring where failover would significantly disrupt a long-lived session, and generally does not recommend it for short-lived HTTP/UDP because of performance overhead.

Important Advanced WAF/ASM limitations documented by F5 21.1 include:

- traffic is mirrored to only one standby peer;
- third-device/multiple failover does not preserve the connection;
- failback resets the connection;
- some AWAF features have additional mirroring limitations.

Therefore:

- W2 can improve continuity for a two-device HA event;
- W4's third/spare WAF does **not** mean an existing connection can transparently survive every transition;
- W1/W3 should assume connections on a failed independent WAF must reconnect;
- application reconnect/state-recovery logic remains mandatory for socket/WebSocket designs.

# 7. F5 WAF policy/configuration consistency

F5 supports synchronizing Advanced WAF/ASM security policy/configuration across multiple BIG-IP systems using an ASM-enabled Sync-Only device group.

Key modelling assumptions:

- all WAF pool members must enforce equivalent policy for a protected service;
- reserve/shared WAFs must have validated tenant policy before receiving production traffic;
- configuration synchronization is itself a common-mode risk: a bad policy pushed everywhere can fail the whole WAF service even when hardware is healthy;
- F5 documentation requires members of an ASM-enabled device group to run the same ASM version/hotfix level.

# 8. F5 HA design practices to preserve

- Configure redundant HA failover communication paths; F5 recommends management plus TMM/self-IP network failover paths.
- Use health monitors that validate the service you actually need, not merely node reachability.
- For local/remote preferred-member designs, use priority groups rather than ad-hoc manual routing where practical.
- Consider MAC masquerade/appropriate network design to reduce ARP/network convergence effects after traffic-group failover.
- Use connection mirroring selectively for long-lived/high-impact connections rather than assuming it should be enabled for all traffic.

# 9. F5 source references

Official F5 references reviewed for this analysis:

- BIG-IP LTM health/performance monitoring: https://techdocs.f5.com/en-us/bigip-17-0-0/big-ip-local-traffic-manager-implementations/implementing-health-and-performance-monitoring.html
- BIG-IP LTM monitor settings: https://techdocs.f5.com/en-us/bigip-16-0-0/big-ip-local-traffic-manager-monitors-reference/monitors-settings-reference.html
- BIG-IP DNS monitor settings: https://techdocs.f5.com/en-us/bigip-14-0-0/big-ip-dns-monitors-reference/monitors-settings-reference.html
- BIG-IP DNS + LTM integration/iQuery: https://techdocs.f5.com/en-us/bigip-17-5-0/big-ip-dns-implementations/integrating-big-ip-dns-into-a-network-with-big-ip-ltm-systems.html
- BIG-IP DNS Global Availability: https://techdocs.f5.com/en-us/bigip-15-0-0/big-ip-dns-load-balancing/about-load-balancing-and-resource-availability.html
- BIG-IP DNS Topology load balancing: https://techdocs.f5.com/en-us/bigip-15-0-0/big-ip-dns-load-balancing/using-topology-load-balancing-to-distribute-dns-requests-to-specific-resources.html
- LTM Priority Group Activation: https://techdocs.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/ltm-basics-11-6-0/4.html
- Device Service Clustering failover: https://techdocs.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/bigip-system-device-service-clustering-administration-13-0-0/6.html
- Connection mirroring: https://techdocs.f5.com/en-us/bigip-14-1-0/big-ip-device-service-clustering-administration-14-1-0/managing-connection-mirroring.html
- Advanced WAF/ASM connection-mirroring limitations (21.1): https://techdocs.f5.com/en-us/bigip-21-1-0/big-ip-asm-implementations/connection-mirroring-with-asm/connection-mirroring-limitations.html
- Advanced WAF/ASM config synchronization: https://techdocs.f5.com/en-us/bigip-21-1-0/big-ip-asm-implementations/automatically-synchronizing-application-security-configurations.html


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

For BIG-IP DNS/GTM synchronization groups, use the version-specific F5 upgrade procedure because software compatibility and probing/synchronization behavior can constrain how long versions may differ.

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

F5 LTM supports a disabled member state in which new general traffic is stopped while active/persistent connections can continue, which should be considered for planned drain workflows.

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
