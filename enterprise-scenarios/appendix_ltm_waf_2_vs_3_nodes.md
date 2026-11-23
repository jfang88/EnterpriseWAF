
# Appendix — Two vs Three BIG-IP LTM and WAF Nodes

**Status:** Supporting design appendix  
**Baseline:** The enterprise default remains **two LTMs per site**. Three-device LTM is an optional comparison only.  
**Primary inputs:** enterprise_scenario_invariants.md and analysis_variables_and_f5_assumptions.md

# 1. Why this distinction matters

The term **cluster** can mean two very different things:

1. a **DSC Sync-Failover group**, where a floating traffic group/VIP has one active owner at a time and can fail to another BIG-IP; or
2. a set of **independent active WAF pool members behind an LTM**, where the LTM distributes new connections across multiple WAF devices at the same time.

These designs should not be described interchangeably.

The key rule is:

> A larger DSC group gives more failover/maintenance targets. It does not automatically make one floating VIP active on every device.

# 2. Default enterprise LTM model

The default design remains:

~~~text
Per site

             Tenant/application VIP
                     |
             BIG-IP LTM DSC
             +-------------+
             |             |
           LTM-A         LTM-B
           active        standby
             |
           WAF tier
~~~

For a conventional single traffic group:

- one LTM owns the floating traffic group/VIP;
- the other is standby for that traffic group;
- failover moves the traffic group to the peer;
- the pair is not packet/connection load-balancing that same floating VIP across both appliances.

This is the normal **2-device active/standby** interpretation used by the current EnterpriseWAF baseline.

# 3. Can two LTMs both be active?

Yes, but F5 DSC **active-active** means different traffic groups can be active on different devices.

Example:

~~~text
LTM-A                       LTM-B
-----                       -----
TG-App1 ACTIVE              TG-App1 standby
TG-App2 standby             TG-App2 ACTIVE
~~~

Both appliances are processing traffic, but:

- App1's floating traffic group is active on LTM-A;
- App2's floating traffic group is active on LTM-B;
- each individual traffic group still has one active owner.

If LTM-A fails:

~~~text
LTM-B
-----
TG-App1 ACTIVE
TG-App2 ACTIVE
~~~

This can use both appliances efficiently across several applications/VIPs, but it is not equivalent to horizontally load-balancing one VIP across both LTMs.

# 4. Optional three-device LTM DSC group

F5 Sync-Failover device groups support more than two members, with a documented maximum of eight.

An optional three-device design could be:

~~~text
                   Tenant VIP / TG1
                         |
                    active owner
                         |
              +----------+----------+
              |          |          |
            LTM-A      LTM-B      LTM-C
            ACTIVE     standby    standby
~~~

For one traffic group/VIP:

- one device is active;
- another can be selected as next-active;
- the third is an additional failover target;
- the traffic is **not** divided three ways for that traffic group.

With several traffic groups:

~~~text
             LTM-A        LTM-B        LTM-C
             -----        -----        -----
TG-App1      ACTIVE       standby      standby
TG-App2      standby      ACTIVE       standby
TG-App3      standby      standby      ACTIVE
~~~

This is where a 3-device DSC group can provide useful active utilisation.

## Main benefits of a third LTM

1. **Maintenance headroom**
   - one LTM can be upgraded/drained;
   - two devices still remain in the local DSC group.

2. **Second-failure tolerance during maintenance**
   - subject to capacity and correct failover configuration, another device can fail while one is already unavailable.

3. **Distribution of multiple traffic groups**
   - several application traffic groups can be spread across the three devices.

4. **More local recovery before GTM/site failover**
   - loss of one or even two devices need not automatically remove the tenant LTM service.

## Main drawbacks

- more DSC, failover-order and capacity-management complexity;
- more configuration/synchronization scope;
- bad synchronized config/iRules can still affect all devices;
- connection-mirroring behavior is not equivalent to three-way live connection replication;
- extra cost for comparatively little benefit if there are only a few traffic groups and alternate-site recovery is already acceptable.

## EnterpriseWAF conclusion for LTMs

**Default: two LTMs per site.**

A third LTM should be treated as an optional availability/maintainability enhancement, not part of the baseline.

Its strongest justification is:

> preserve local redundancy during maintenance and tolerate another local LTM fault,

not:

> increase the throughput of one floating VIP by 50%.

# 5. Two-node WAF HA cluster

A WAF HA pair using DSC behaves similarly at the traffic-group level.

~~~text
             WAF service VIP / traffic group
                         |
                +--------+--------+
                |                 |
             WAF-A              WAF-B
             ACTIVE             standby
~~~

For that traffic group:

- one WAF is processing the service;
- the peer is the failover target;
- it is not normally a 50/50 load-balanced service across the HA pair.

Multiple traffic groups can be arranged active-active across a pair, but again each traffic group has one active owner.

Benefits:

- simple HA;
- configuration/state relationship is easy to understand;
- supported connection mirroring can reduce interruption for some two-device failures.

Limitations:

- only the active owner processes that traffic group's workload;
- a two-device pair temporarily loses redundancy while one device is being maintained;
- cluster capacity must allow the surviving device to carry all traffic after failover.

# 6. Three-node WAF DSC cluster

A 3-device WAF DSC group is technically possible as a DSC topology, but it should not be confused with a 3-way active WAF pool.

For one protected traffic group:

~~~text
            Protected service TG
                    |
                WAF-A ACTIVE
                 /       \
           WAF-B standby  WAF-C additional failover
~~~

The third device can provide another failover target and/or host a different active traffic group.

However, for Advanced WAF/ASM connection mirroring, F5 documents important limits:

- traffic is mirrored to only **one standby device**;
- only two devices are supported for mirrored-connection continuity;
- a subsequent failover from device 2 to device 3 resets the connection;
- failback also resets the mirrored connection.

Therefore a 3-device WAF DSC group can improve **device availability**, but should not be presented as providing three-way transparent WebSocket/TCP connection preservation.

# 7. Independent WAF pool behind LTM — true horizontal traffic distribution

This is materially different.

## Two independent WAFs

~~~text
                 LTM VIP
                   |
              load balance
             /            \
          WAF-1          WAF-2
          ACTIVE         ACTIVE
             \            /
              application
~~~

Both WAFs can process the same application's new connections concurrently.

The LTM:

- monitors each WAF;
- distributes new connections/requests according to the selected load-balancing method;
- stops selecting a failed WAF after health withdrawal.

This provides both:

- **capacity scaling**, and
- **failure isolation**.

Affected existing connections on a failed independent WAF generally need to reconnect.

## Three independent WAFs

~~~text
                    LTM VIP
                      |
                  load balance
              /       |       \
           WAF-1    WAF-2    WAF-3
           ACTIVE   ACTIVE   ACTIVE
              \      |      /
                 application
~~~

All three can process traffic simultaneously.

Benefits:

- more horizontal capacity;
- N-1 maintenance can still leave two active WAFs;
- N-2 design is possible if each remaining WAF can carry the required load;
- one WAF can be used as an upgrade/canary target;
- no requirement for one WAF to carry the full service merely because a peer failed.

Trade-offs:

- more policy/config consistency work;
- more health monitoring;
- affected long-lived connections reconnect rather than transparently migrating;
- a bad synchronized WAF policy can still create a common-mode outage.

This is the key architectural distinction:

> **3 independent WAF pool members can genuinely share one service's traffic. A 3-device DSC failover group does not normally share one floating traffic group across all three devices.**

# 8. W3 interpretation

The EnterpriseWAF W3 baseline should be read as:

~~~text
Per site

              Tenant LTM pair
            (2 devices by default)
                     |
           +---------+---------+
           |                   |
     preferred WAF-1     preferred WAF-2
         ACTIVE              ACTIVE
           \                   /
            \                 /
             shared reserve WAF(s)
~~~

The tenant LTM pair is HA for the **front-end VIP**.

The preferred WAFs are independent active pool members and can both process production traffic.

The shared reserve WAF is typically:

- lower priority;
- reserved/not normally selected;
- or activated according to the chosen capacity model.

So W3 deliberately combines:

- **LTM failover clustering** at the front;
- **active load-balanced WAF pool members** behind it.

That is why losing one WAF is normally a local pool-member event, while losing the complete LTM pair is a much larger failure.

# 9. W4 interpretation

W4 is different again:

~~~text
Site 1

             LTM pair
                |
        +-------+-------+
        |               |
  WAF HA cluster    extra WAF
  one TG active     independent
~~~

If the LTM is configured to treat:

- the WAF HA-cluster service, and
- the extra independent WAF

as separate eligible pool targets, both service paths can potentially carry traffic according to priority/load-balancing design.

Inside the WAF HA cluster itself, however, the protected traffic group still has one active owner.

If there is **no ingress LTM**, the mechanism that distributes traffic between the cluster and extra WAF must be explicitly engineered at the firewall/routing layer.

# 10. Comparison table

| Design | Same service traffic processed concurrently by multiple devices? | One VIP/TG active owner? | Main reason to add 3rd device | Maintenance effect |
|---|---|---|---|---|
| **2-LTM DSC pair** | No, not for one floating traffic group | **Yes** | N/A baseline | One device down leaves one local LTM |
| **3-LTM DSC group** | Not for one TG; yes across different TGs | **Yes** | maintenance + second-failure headroom; distribute multiple TGs | One device down can still leave two LTMs |
| **2-WAF HA DSC pair** | Not for one protected TG | **Yes** | N/A | one device down leaves cluster on one active owner |
| **3-WAF DSC group** | Not for one TG; different TGs can be active elsewhere | **Yes** | extra failover target / multiple TG distribution | better node headroom; connection mirroring still only 2-device continuity |
| **2 independent WAFs behind LTM** | **Yes** | LTM VIP owns ingress; both WAFs active | horizontal capacity + N-1 | drain one, one remains |
| **3 independent WAFs behind LTM** | **Yes — all three** | LTM VIP owns ingress | horizontal capacity + N-1/N-2 + canary | strongest rolling-maintenance flexibility |
| **W3 preferred + reserve WAFs** | **Yes for preferred active pool** | LTM TG has one active owner | reserve capacity shared across tenants | good if reserve is policy-ready/capacity-governed |
| **W4 WAF cluster + extra WAF** | cluster TG itself: no; cluster service + extra WAF: potentially yes behind LTM | cluster TG: **Yes** | layered local resilience | strong Site 1 maintenance option |

# 11. Practical recommendation

For the current enterprise model:

1. **Keep two LTMs per site as the baseline.**
2. Use DSC failover for the LTM front-end VIP.
3. Do not describe a 2- or 3-device LTM DSC group as load-balancing one floating VIP across all appliances.
4. Where horizontal WAF utilisation is desired, use **independent active WAF pool members behind the LTM**.
5. Use a 3rd LTM only where the availability/maintenance benefit is worth the additional DSC complexity.
6. Use a 3rd independent WAF when additional active capacity, N-2 resilience or canary/rolling-maintenance flexibility is required.
7. Treat a 3rd WAF in a DSC HA group as additional failover/traffic-group capacity, **not** as equivalent to a 3-member active WAF pool.
8. For WebSocket/long-lived services, do not rely on a third DSC WAF to preserve an established connection; application reconnect/state recovery remains mandatory.

# 12. F5 references

Official F5 documentation supporting this appendix:

- Device Service Clustering introduction — multiple devices and traffic groups:
  https://techdocs.f5.com/en-us/bigip-14-1-0/big-ip-device-service-clustering-administration-14-1-0/introducing-big-ip-device-service-clustering.html
- Sync-Failover device groups — maximum eight devices:
  https://techdocs.f5.com/en-us/bigip-14-1-0/big-ip-device-service-clustering-administration-14-1-0/working-with-device-groups.html
- Active-active DSC — different active traffic groups on different devices:
  https://techdocs.f5.com/en-us/bigip-14-1-0/big-ip-device-service-clustering-administration-14-1-0/creating-an-active-active-configuration-using-the-configuration-utility.html
- Managing failover / balancing traffic groups:
  https://techdocs.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/bigip-device-service-clustering-admin-12-0-0/6.html
- Advanced WAF/ASM connection mirroring limitations:
  https://techdocs.f5.com/en-us/bigip-17-0-0/big-ip-asm-implementations/connection-mirroring-with-asm/connection-mirroring-limitations.html
- Advanced WAF/ASM configuration synchronization across redundant pairs:
  https://techdocs.f5.com/en-us/bigip-17-5-0/big-ip-asm-implementations/synchronizing-application-security-configurations-across-lans.html
