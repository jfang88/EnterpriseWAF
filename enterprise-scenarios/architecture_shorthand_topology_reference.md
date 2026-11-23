# Canonical Architecture Shorthand and End-to-End Topology Reference

**Status:** Canonical terminology/topology reference  
**Use this document when a shorthand definition or path diagram differs elsewhere.**  
**Baseline:** [enterprise_scenario_invariants.md](./enterprise_scenario_invariants.md)  
**Variables:** [analysis_variables_and_f5_assumptions.md](./analysis_variables_and_f5_assumptions.md)

# 1. Naming rules

The current analysis uses three separate shorthand families:

- **W1-W4** — per-site WAF topology patterns;
- **S1-S3 / D1** — tenancy/sharing patterns layered on top of the WAF topology;
- **T1-T9** — timing/recovery categories.

Cross-site recovery uses **X1/X2A/X2B/X2C/XD1**.

Do not reuse W1/W2/W3 as individual WAF-node names. Use **WAF-1, WAF-2, WAF-3...** instead.

Do not use S1/S2 as generic Site-1/Site-2 labels in current documents. Use **Site 1 / Site 2**.

For application instances, prefer explicit notation such as **App A @ Site 1** and **App B @ Site 2** rather than `A1` / `B2` where the meaning could be confused with application-type shorthand.

# 2. Canonical topology shorthand

| ID | Canonical meaning | Key behavior |
|---|---|---|
| **W1** | Tenant/dedicated LTM HA pair in front of an **independent active WAF pool** | 2..N WAFs can process the same service concurrently; LTM withdraws failed members |
| **W2** | **WAF HA/DSC cluster**, optionally behind an ingress LTM | one active owner per traffic group; peer is HA failover target |
| **W3** | Tenant LTM HA pair + **tenant-preferred active WAFs + shared reserve WAF capacity** | preferred WAFs serve normally; shared reserve is contingency capacity |
| **W4** | Asymmetric: Site 1 WAF HA cluster + extra independent WAF; Site 2 WAF HA cluster only | stronger Site 1 local headroom; asymmetric DR/maintenance |
| **D1** | Fully dedicated tenant LTM/WAF capacity | strongest tenant isolation; duplicated spare capacity |
| **S1** | **Tenant-specific LTM HA pairs feeding one shared independent active WAF pool** | preferred four-tenant cost/resilience option if aggregate capacity and tenant isolation are proven |
| **S2** | **Shared LTM HA pair feeding a shared independent active WAF pool** | lowest active-pool device count, but larger common failure/change domain |
| **S3** | Shared WAF HA/DSC cluster | device-efficient, but shared cluster is a multi-tenant failure domain |

Important distinction:

- **W1 / S1 / S2 active pool:** multiple independent WAFs can process the same service concurrently.
- **W2 / W4 HA cluster:** one device owns a traffic group; another device is the failover target.
- **W3:** tenant-preferred active WAFs plus shared reserve capacity.

# 3. Canonical cross-site shorthand

| ID | Canonical meaning |
|---|---|
| **X1** | local-only dataplane; local delivery-tier loss requires local repair or broader site/application recovery |
| **X2A** | surviving local LTM uses a remote-site WAF, then routes back through the healthy local CFW/ELB/application path |
| **X2B** | remote-site front end serves the client, then routes back to the healthy primary-site CFW/ELB/application path |
| **X2C** | conventional full application/site failover to the alternate site |
| **XD1** | App A stays local but uses a healthy App B in the alternate site through a stable dependency service abstraction |

Cross-site capability is a **contingency path**, not a normal-path dependency. A healthy local site should continue without requiring the inter-site path.

# 4. Canonical timing shorthand

These are engineering modelling categories, not SLAs.

| ID | Canonical meaning | Planning interpretation |
|---|---|---|
| **T1** | BIG-IP HA peer/device failover | approximately **3+ seconds peer-loss detection**, plus traffic-group/network convergence; measure end to end |
| **T2** | LTM pool-member / WAF-member health detection | commonly **up to ~16s** with 5s interval / 16s timeout defaults |
| **T3** | direct BIG-IP DNS/GTM health monitor | common HTTP/HTTPS/TCP defaults around **30s interval / 120s timeout** |
| **T4** | **DNS/site-selection convergence after the health decision** | GTM answer change + residual DNS TTL/cache + client re-resolution/retry; **does not include manual app startup or application state restoration** |
| **T5** | warm/cold/manual operational recovery | operator action, passive-site startup, routing repair, config/policy rollback; minutes or longer unless measured otherwise |
| **T6** | application recovery | retry, reconnect, re-authentication, session/state restore, resubscription, replay/reconciliation |
| **T7** | failback | controlled return to preferred device/site; auto-failback delay is configurable and should not be treated as a service-failover SLA |
| **T8** | DNS/cache/existing-connection behavior | behavior modifier, not a duration |
| **T9** | platform/cloud firewall (CFW) recovery | product/configuration specific; measure CFW HA and full-context recovery separately |

## 4.1 How to combine the timers

Use only sequential terms.

- **T2 + T6** — member failure detection/withdrawal, then application/client recovery.
- **T4 + T6** — DNS/site selection changes, then application/client recovery.
- **T5 + T4 + T6** — manual/startup work, then DNS/site convergence, then application recovery.
- **~46s + T6** — illustrative fast-health site move: about 16s health + up to 30s residual DNS TTL + application recovery.
- **up to ~150s + T6** — default-style direct GTM health timeout (~120s) + up to 30s residual DNS TTL + application recovery.

**T4 must not also include T5/T6 work**, otherwise recovery is double-counted.

# 5. Canonical end-to-end topology

The drawing below is the reference logical layout for a private-cloud-hosted application. Individual applications may bypass some layers, but a document must say so explicitly rather than silently removing a layer.

```text
                            EXTERNAL USER / API CLIENT
                                      |
                           recursive/customer DNS
                                      |
                     external enterprise DNS / GTM
                                      |
                        leased line / VPN / route
                                      |
                         edge firewall / app VIP
                                      |
                             tenant LTM HA pair
                                      |
                      WAF topology (W1/W2/W3/W4)
                                      |
                         platform/cloud firewall
                                   (CFW)
                                      |
                              ELB / service VIP
                                      |
                              APP A @ SITE 1
                                      |
                         internal dependency DNS
                                      |
                             B service VIP
                              /          \
                    preferred /            \ fallback XD1
                            /                \
                 APP B @ SITE 1       APP B @ SITE 2
                       |                      |
                       +----------+-----------+
                                  |
                           APP C dependency
                                  |
                        APP C @ healthy site


INTERNAL USER / SYSTEM
        |
 internal enterprise DNS
        |
 optional internal GTM / service name
        |
 internal LTM / service VIP
        |
      CFW
        |
  ELB / service VIP
        |
      APP A
```

# 6. Two-site topology with application hosting and cross-site contingency

```text
                    +---------------- EXTERNAL DNS / GTM ----------------+
                    |                                                     |
                    v                                                     v
                 SITE 1                                                SITE 2
        +----------------------+                              +----------------------+
        | edge firewall / VIP  |                              | edge firewall / VIP  |
        +----------+-----------+                              +----------+-----------+
                   |                                                     |
              LTM HA pair                                          LTM HA pair
                   |                                                     |
             local WAF tier                                        local WAF tier
                   |                                                     |
                  CFW                                                   CFW
                   |                                                     |
                  ELB                                                   ELB
                   |                                                     |
             App A @ Site 1                                       App A @ Site 2
                   |                                                     |
             B service VIP ------------- XD1 fallback ------------------+
             /             \
    B @ Site 1          B @ Site 2
             \             /
                App C / shared dependencies

X2A: Site 1 LTM -> Site 2 WAF -> inter-site route -> Site 1 CFW -> Site 1 ELB/App
X2B: Site 2 front end -> inter-site route -> Site 1 CFW -> Site 1 ELB/App
X2C: users/applications move fully to Site 2
```

# 7. Dependency-cascade view

Without XD1 or another safe remote-dependency path:

```text
B @ Site 1 fails
  |
  +--> App A waits/retries
  +--> App C waits/retries
  +--> App D waits/retries
          |
          v
   thread / connection pools fill
          |
          v
   readiness checks may fail
          |
          v
   GTM may withdraw A/C/D Site 1 VIPs
          |
          v
   multiple applications move to Site 2
          |
          v
   reconnect + login + DB/dependency surge
```

With XD1:

```text
App A / C / D
      |
B service VIP
   |       |
 B local   B remote
preferred fallback

B local fails -> withdraw local member -> retry remote B -> A/C/D stay in Site 1
```

This is why cross-site dependency reachability is an **early resilience requirement for critical shared dependencies**, even though the remote path should remain contingency-only in normal operation.

# 8. Document precedence

When terminology differs:

1. this canonical shorthand/topology reference;
2. `enterprise_scenario_invariants.md` for stable enterprise facts;
3. `analysis_variables_and_f5_assumptions.md` for changeable design/timing assumptions;
4. derived analyses;
5. root WebSocket specialist paper;
6. archived documents last.

Archived files may contain historical node labels such as `W1`, `W2`, `S1`, or `S2` that do **not** mean the current topology/sharing IDs. Do not reuse those historical labels in new analysis.
