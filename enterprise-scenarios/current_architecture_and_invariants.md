# EnterpriseWAF Current Architecture and Stable Invariants

**Status:** Authoritative current-state architecture, topology and stable-invariant baseline  
**Change policy:** Change this file only when the real enterprise environment, ownership boundary, business requirement or supported application scope changes. Do not place target-state improvements or preferred design choices here.

**Future / target-state improvements:** [future_architecture_improvements.md](./future_architecture_improvements.md)

# 1. Purpose

This file is the single grounding source for **what exists today, how the current end-to-end application-delivery architecture is laid out, and what is treated as a stable enterprise fact**.

While the architecture evaluates **end-to-end application delivery** across every hop (DNS/GTM, edge firewalls, LTM, WAF, internal firewall, private-cloud CFW/ELB, and applications/dependencies), **initial implementation focuses on the WAF tier** (and F5 LTM/GTM interfaces) because edge/internal firewalls, private-cloud CFW/ELB, and applications are owned by partner teams and require coordinated cross-team contracts.

**Joint responsibility operating principle (enterprise baseline):** End-to-end resilience is a **shared responsibility**:
- **Infrastructure teams** (F5/ADC, Network/Security, Cloud Platform) deliver resilient, rolling-upgradeable infrastructure, deterministic routing/SNAT/header propagation, and accurate layer-appropriate health steering;
- **Application teams** build applications that tolerate and recover cleanly from infrastructure and site failures (`T6`) and publish explicit readiness, session, protocol, and client-IP contracts;
- **Health checks and recovery controls** are placed at the exact right layer and articulated clearly so both infrastructure and application teams can architect against explicit contracts.

Use it to ground:

- end-to-end application-delivery diagrams;
- management slides;
- WAF topology comparisons;
- failure and recovery analysis;
- health-check and DNS/GTM analysis;
- cross-site design studies.

Where the exact current implementation has not yet been confirmed, this file says **unknown / validate** rather than silently treating a desired future design as current state.

# 2. Stable current-state summary

| Area | Current-state / stable fact |
|---|---|
| **Sites** | Two sites: **Site 1** and **Site 2**, treated as separate infrastructure and routing failure domains |
| **Primary estate** | Four-tenant **extranet** end-to-end application-delivery environment; the wider estate may contain approximately 3-4 tenant/hosting contexts |
| **External access** | External partner/customer users and API clients primarily use private leased-line / VPN-style connectivity |
| **GTM / DNS** | One **BIG-IP DNS/GTM cluster per site**; the site clusters communicate/synchronize the enterprise GTM/DNS view |
| **GTM placement** | GTM/DNS is an **edge service inside the edge-firewall security boundary** |
| **External DNS use** | External/customer DNS reaches the enterprise edge GTM over the private leased-line/VPN path through the edge firewall |
| **Internal DNS use** | Internal users use **internal enterprise DNS**; selected endpoint names/namespaces can be delegated or conditionally forwarded to the **same edge GTM service** |
| **Edge firewalls** | Each tenant/site has **two HA edge-firewall pairs, two devices per pair (2 x 2 devices)** (*Network/Security team owned*) |
| **External VIPs** | Externally reachable application VIPs live on the edge-firewall tier |
| **LTM** | Existing tenant LTM HA boundaries are retained; the default model is **two LTMs per tenant/site in an HA/Sync-Failover pair** |
| **WAF / BIG-IP platform (current)** | Current deployed estate runs **BIG-IP 17.5.x** (LTM, BIG-IP DNS/GTM, Advanced WAF/ASM; EoTS Jan 1, 2029 per F5 `K15643`). Initial delivery focus is the WAF tier; exact WAF topology/sharing is a design variable |
| **Target rebuild hardware standard (confirmed invariant)** | Future hardware rebuild is standardized on **F5 rSeries `r2800` pizza boxes ONLY** (no VELOS blade chassis, no `r4800`/`r5000+`), running **`F5OS-A 1.8.0+`** + **BIG-IP 21.1.x+**: max **2 F5OS tenants/box** (`4 vCPU / 12 GB RAM` each, or 1 full-box tenant at `8 vCPU / 24 GB RAM`), **single 480 GB NVMe SSD (~447 GB usable, no RAID-1)**, **no FPGA and no Spanning Tree Protocol (`STP`)** (1 interface/LAG per VLAN, `K000152319`), ≥ 88 GB virtual disk per `21.1.x` tenant (`K45191957`), and `.tar.bundle` image format (`K000158849`). Detailed rebuild design is tracked in `future_architecture_improvements.md` |
| **Internal network** | Internal users/desktops/systems, internal DNS and internal service/LTM VIPs are **outside the private-cloud boundary** |
| **Internal firewall** | A distinct **internal firewall** separates the enterprise internal network from private cloud (*Network/Security team owned*) |
| **Private-cloud firewall** | **CFW** is the logical private-cloud edge available in both sites; site-local enforcement paths precede ELB/service endpoints (*Cloud Platform team owned*) |
| **Applications** | Applications may run on VMs, Kubernetes, PaaS or on-premises platforms (*Application teams*); App A/B/C/D dependency chains are first-class availability dependencies |
| **Application portfolio & protocol baseline (invariant)** | The enterprise portfolio includes **stateless web/API (`AT1`)**, **stateful web with potential sticky-session requirements (`AT2`)**, **WebSocket / long-lived real-time connections (`AT3`)**, and **non-web / L4 services (`AT4`)** that may bypass WAF |
| **External client-IP visibility (invariant)** | Some applications **require tracking the real external user/client IP address** (for security, audit, fraud/compliance, rate-limiting, or IP ACLs). Preserving client IP depends on SNAT usage and **where TLS/HTTP is terminated** — requiring raw L3 preservation (no SNAT), **SNAT + `X-Forwarded-For` (`XFF`)** injection at the first HTTP/TLS terminator (LTM, WAF, or **Cloud ELB/Ingress** injecting its own headers when ELB terminates TLS), or **PROXY Protocol** for L4 TCP |
| **Application mode** | Most applications are active/passive; some passive-site applications may require manual startup; some applications may be active/active |
| **Availability requirement** | Evaluate the end-to-end service against a **99.95% total availability target (`4h 22m 48s / year`) covering BOTH managed (planned maintenance/changes) and unmanaged (unplanned failure) outages combined** |
| **Blast-radius / impact threshold (potential requirement)** | Evaluate every topology variant against a **≤ 25% maximum impact threshold** (1 of 4 tenants = 25% estate blast radius, and/or ≤ 25% capacity/canary user exposure during a single failure, rolling upgrade, or canary wave) |
| **Cross-site routing** | Cross-site WAF/front-end/dependency routing is **not assumed to exist today** unless separately confirmed |

# 3. Architecture planes and parallel paths

Do **not** treat the architecture as one linear inline stack: external and internal access are **parallel ingress paths** that converge at the private-cloud delivery tier, while DNS/GTM and health/observability are **control planes**.

| Plane / Path | Current role | Current boundary |
|---|---|---|
| **Client / resolver plane** | external users/API clients, external/customer DNS, internal users, internal enterprise DNS | outside application-delivery/private-cloud stack |
| **DNS / site-selection control plane** | Site 1 and Site 2 BIG-IP DNS/GTM clusters; answers selected external and delegated internal names (not an inline data hop) | edge service inside edge-firewall boundary |
| **External ingress path** | private leased line/VPN -> 2 x 2 edge firewalls / external VIPs -> tenant LTM HA service -> WAF tier | extranet / site edge & tenant delivery |
| **Internal ingress path** | internal LTM/service VIP -> distinct **internal firewall** (may bypass external WAF) | enterprise internal network -> private cloud |
| **Private-cloud delivery tier** | distinct **CFW** -> ELB/service (where external and internal paths converge) | private-cloud boundary |
| **Application + dependency tier** | App A/B/C/D, sessions, state, DB, identity, event services, and App A/D -> B -> C chains | application/platform |
| **Health / observability / recovery plane** | cross-cutting across HA, local member, endpoint, dependency and synthetic tiers (not an inline hop) | cross-cutting |

# 4. Site and edge architecture

For a representative tenant, each site has the same core edge structure unless a design option explicitly says otherwise:

```text
Site
  -> 2 HA edge-firewall pairs
       -> 2 devices per HA pair (2 x 2 devices)
  -> site GTM/DNS cluster
  -> tenant LTM HA service
  -> WAF tier
  -> private-cloud CFW
  -> ELB/service
  -> application
```

The two sites remain separate failure domains.

The GTM synchronization relationship does **not** mean GTM synchronizes LTM/WAF/CFW/application configuration. Those remain separate service and configuration domains.

# 5. DNS / GTM current state

## 5.1 Control-plane rule

BIG-IP DNS/GTM is a **DNS control-plane / endpoint-selection service**. It is not an inline hop in the HTTP/TCP application session.

DNS resolution and subsequent application traffic must therefore be drawn as separate flows.

## 5.2 External DNS resolution

Representative control path:

```text
External user/system
  -> external/customer DNS resolver
  -> private leased line / VPN / extranet path
  -> edge firewall
  -> enterprise edge BIG-IP DNS / GTM cluster
  -> DNS answer containing selected external/firewall application VIP
```

The application connection then uses the returned VIP and does **not** pass through GTM as an inline proxy.

## 5.3 Internal DNS resolution

Internal users and systems use internal enterprise DNS.

For selected endpoint names or namespaces, internal DNS may delegate or conditionally forward to the **same enterprise edge GTM service** used for external endpoint selection.

Representative control path:

```text
Internal user/system
  -> internal enterprise DNS
  -> [selected delegated / conditionally forwarded name]
  -> enterprise edge BIG-IP DNS / GTM cluster
  -> DNS answer containing internal service/LTM VIP
```

The application data path then follows the internal service path described in section 8.

Internal and external DNS namespaces/answers are logically distinct even where the same GTM platform participates in both.

# 6. Current GTM health-check state: known facts and items to validate

The **architecture and placement of GTM are known**, but the exact current health-monitoring implementation has not yet been fully validated in this analysis.

Do **not** draw the following as current-state facts until confirmed.

| Item | Current status |
|---|---|
| GTM uses only TCP/port checks versus HTTP/L7 checks | **Unknown - validate** |
| GTM directly performs L7 health checks against each **external VIP** | **Unknown - validate** |
| GTM directly performs L7 health checks against each **internal VIP** used for delegated internal names | **Unknown - validate** |
| GTM consumes LTM virtual-server/application health using iQuery | **Unknown - validate** |
| Site 1 GTM probes Site 2 endpoints and Site 2 GTM probes Site 1 endpoints | **Unknown - validate** |
| GTM synchronization group/prober-pool behavior and availability requirements | **Unknown - validate** |
| Monitor intervals, timeouts and up/down thresholds | **Unknown - validate** |
| Application-owned readiness endpoints exist for all critical services | **Unknown - validate** |
| Health checks include CFW -> ELB -> application reachability | **Unknown - validate** |
| Health checks include critical App A -> B -> C dependencies | **Unknown - validate per application** |
| Independent external/user-like synthetic monitoring feeds the SLO | **Unknown - validate** |

### Why this matters

A TCP/port-only check can be green while the business service is unusable, for example:

```text
GTM sees listener UP
        |
        v
WAF/LTM TCP port responds
        |
        X
CFW / ELB / application unavailable
```

That is a **false-green health state**.

The target health-check design is therefore treated as a **future improvement** and is documented separately in [future_architecture_improvements.md](./future_architecture_improvements.md).

# 7. Canonical current-state topology

The CFW is one logical private-cloud edge/security boundary available in both sites, represented by site-local enforcement paths. ELB/service endpoints sit behind that boundary. This does not establish a stretched physical firewall, shared state, automatic alternate-site routing, or independent failure domains: local and common-mode failures must be validated separately.

```mermaid
flowchart LR

  subgraph EXT[External / customer environment]
    EU[External users / API clients]
    EDNS[External / customer DNS]
    EU -. DNS query .-> EDNS
  end

  subgraph INT[Enterprise internal network - outside private cloud]
    IU[Internal users / systems]
    IDNS[Internal enterprise DNS]
    ILTM[Internal LTM / service VIP]
    IFW[Internal firewall]
    IU -. DNS query .-> IDNS
    IU --> ILTM --> IFW
  end

  subgraph S1E[Site 1 edge / delivery]
    NET1[Private leased line / VPN]
    FW1[2 x HA edge-firewall pairs]
    GTM1[Site 1 GTM/DNS cluster]
    LTM1[Tenant LTM HA service]
    WAF1[WAF tier]
    NET1 --> FW1
    FW1 --> LTM1 --> WAF1
    FW1 -. DNS query .-> GTM1
  end

  subgraph S1C[Site 1 private cloud]
    CFW1[CFW - Site 1 enforcement]
    ELB1[ELB / service]
    A1[App A]
    D1[App D]
    B1[App B]
    C1[App C / shared dependencies]
    CFW1 --> ELB1
    ELB1 --> A1
    ELB1 --> D1
    A1 --> B1 --> C1
    D1 --> B1
  end

  subgraph S2E[Site 2 edge / delivery]
    NET2[Private leased line / VPN]
    FW2[2 x HA edge-firewall pairs]
    GTM2[Site 2 GTM/DNS cluster]
    LTM2[Tenant LTM HA service]
    WAF2[WAF tier]
    NET2 --> FW2
    FW2 --> LTM2 --> WAF2
    FW2 -. DNS query .-> GTM2
  end

  subgraph S2C[Site 2 private cloud / DR]
    CFW2[CFW - Site 2 enforcement]
    ELB2[ELB / service]
    APP2[DR application instances]
    CFW2 --> ELB2 --> APP2
  end

  EDNS -. DNS over private path .-> NET1
  EDNS -. DNS over private path .-> NET2
  EU --> NET1
  EU -. DR / alternate VIP .-> NET2
  IDNS -. selected delegated names .-> GTM1
  IDNS -. selected delegated names .-> GTM2

  WAF1 --> CFW1
  IFW --> CFW1
  IFW -. DR / alternate internal path .-> CFW2
  WAF2 --> CFW2

  CFWLOG[Logical private-cloud edge - both sites]
  CFWLOG -.- CFW1
  CFWLOG -.- CFW2
  GTM1 <-. GTM/DNS synchronization .-> GTM2
```

# 8. Current application data paths

## 8.1 External application path

```text
External partner/customer or API client
  -> private leased line / VPN / extranet path
  -> edge firewall / external application VIP
  -> tenant LTM HA service
  -> WAF tier
  -> private-cloud CFW
  -> ELB/service
  -> application workload
```

A WAF topology comparison may change how traffic is handled between LTM and CFW, but it must not silently change the surrounding stable layers.

## 8.2 Internal user path

Internal users may bypass the external WAF tier.

```text
Internal user / desktop / system
  -> internal enterprise DNS
  -> [optional GTM delegation/forwarding for selected names]
  -> internal LTM / service VIP
  -> internal firewall
  -> private-cloud CFW
  -> ELB/service
  -> application
```

Boundary rules:

- internal users, internal DNS and internal LTM/service VIPs are outside private cloud;
- the **internal firewall** and **CFW** are different security, state and failure domains;
- an internal-firewall failure can block internal users while the external path remains healthy;
- a CFW failure can affect both external and internal callers when both paths converge on the same private-cloud CFW.

# 9. Application hosting and dependency paths

Applications can be hosted using one or more of these patterns:

## H1 - on-premises

```text
WAF/LTM
  -> application LB/VIP
  -> servers/VMs
```

## H2 - private-cloud VM

```text
WAF/LTM
  -> CFW
  -> ELB
  -> VM pool
```

## H3 - private-cloud Kubernetes

```text
WAF/LTM
  -> CFW
  -> ELB
  -> Kubernetes ingress/service
  -> pods
```

## H4 - PaaS / stable service endpoint

```text
WAF/LTM
  -> CFW
  -> stable/floating ELB/service endpoint
  -> Site 1 or Site 2 workload
```

## 9.1 App A / B / C / D dependencies

Application-to-application calls must be analysed separately from north-south WAF ingress.

Representative dependency chain:

```text
Application A ----\
                  -> Application B -> Application C
Application D ----/
```

The dependency can use:

- a site-local/static endpoint;
- internal DNS;
- selected internal DNS delegation/forwarding to GTM;
- private-cloud service discovery;
- a stable internal service VIP.

The current existence of an automatic **B1 -> B2 cross-site fallback** is not assumed unless confirmed.

# 10. Application classes, baseline requirements, and invariant vs. layer-specific obligations

Every relevant failure scenario must distinguish:

- **AT1 - stateless web / API**;
- **AT2 - stateful web** (may have **sticky-session** requirements);
- **AT3 - WebSocket / socket / long-lived real-time connection**;
- **AT4 - non-web / L4 application** that may bypass WAF.

**Joint responsibility rule:** Infrastructure recovery is not considered complete until the application-specific recovery requirement is also satisfied. Infrastructure teams deliver resilient infrastructure, deterministic routing/SNAT/header propagation, and layer-accurate health steering; application teams build applications that tolerate infrastructure/site failures (`T6`) and publish explicit readiness and protocol contracts.

## 10.1 What is an enterprise invariant vs. layer-specific infrastructure or application requirements

| Requirement | Enterprise Invariant (Baseline Fact) | Extra Infrastructure Requirement (Per Layer — Target Design) | Extra Application Requirement (Per App Class — Target Design) |
|---|---|---|---|
| **External Client-IP Visibility** | **Invariant:** Some applications must track the real external user/client IP address (security, audit, fraud/compliance, rate-limiting, IP ACLs) | **Layer-dependent on TLS/HTTP termination & SNAT:** (1) No-SNAT inline routing preserves raw L3 IP where symmetric; (2) where SNAT is used, the **first L7 HTTP/TLS terminator** (LTM, WAF, or **Cloud ELB/Ingress** when TLS passes through to ELB) strips untrusted external headers and injects `X-Forwarded-For` (`XFF`), while downstream hops preserve/append `XFF` (WAF `Trust XFF`, `K4816`); (3) **Cloud ELB** must be able to inject/append its own `XFF` header when it terminates TLS; (4) `AT4` TCP behind SNAT uses PROXY Protocol where supported | Declare whether raw client IP, `XFF`, or PROXY Protocol is required; parse the agreed trusted header position rather than raw socket IP when behind SNAT; never trust client-spoofed `XFF` |
| **Stateless vs. Stateful Web & Sticky Sessions** | **Invariant:** Portfolio contains both stateless (`AT1`) and stateful (`AT2`) web apps, including apps with potential **sticky-session** affinity requirements | Designate a **single authoritative app-node sticky tier** (typically Cloud ELB/Ingress cookie passed intact through WAF) + LTM `OneConnect` (`K7964`) + stateless `CARP` (`K11362`) to WAF pool; avoid partner NAT Source-IP hot-spotting; graceful drain (`Receive Disable`, `K12818`) | `AT1`: stateless, idempotent writes, automated retry with backoff. `AT2`: **externalized/replicated session store** (Redis/DB) so sticky sessions remain a throughput/locality optimization rather than a SPOF; graceful re-auth & transaction reconciliation |
| **WebSockets / Long-Lived (`AT3`)** | **Invariant:** Portfolio includes WebSocket / persistent-socket apps sensitive to proxy idle timeouts, upgrades, and failover resets | Attach F5 **WebSocket profile** (`K84421441`); **never enable `OneConnect`** (`K000151124`); raise Edge FW / CFW / ELB idle timeouts above app heartbeat pings; `Action On Service Down = Reject` (`K15095`); do not rely on AWAF mirroring across N>2 pools or failback | Mandatory client reconnect + exponential backoff/jitter + re-authentication + re-subscription + sequence-gap replay/snapshot recovery |
| **Non-Web / Layer-4 (`AT4`)** | **Invariant:** Some non-HTTP/TCP/L4 applications bypass the external WAF tier | Performance (L4) + `FastL4` (`K09948701`), symmetric L4 hashing, `Action=Reject`, avoid SNAT (or pin SNAT IP) for legacy IP-ACL/multi-channel protocols (e.g., passive FTP `K15249`) | Protocol-native reconnect, DNS/service re-resolution, and safe transaction replay |
| **Health Checks & Recovery** | **Invariant:** Faults occur at every layer; device/port green does not equal business availability | Place health checks and recovery at the exact right layer (`H1` HA, `H2` local LTM/ELB member, `H3`/`H4` GTM external/internal L7 VIP, `H5` App B dependency, `H6` synthetic SLO) | Own and version the L7 readiness contract (`/health/ready`, status, receive string, `Receive Disable` maintenance semantics, critical vs. non-critical dependencies) |

**Current persistence, SNAT, header-injection, certificate, and operational baseline (`unknown / validate in Phase 0`):** The following items are **not assumed** as deployed facts and must be inventoried in [phase0_discovery_and_signoff_checklist.md](./phase0_discovery_and_signoff_checklist.md) before locking target designs:
- exact TLS termination point per app (LTM vs. WAF vs. Cloud ELB), partner **mTLS client-certificate** requirements, and current certificate renewal/expiry automation;
- `XFF`/ELB header injection config, sticky-session ownership across LTM/WAF/ELB, SNAT vs. inline routing, TCP optimization profiles (`f5-tcp-wan`/`f5-tcp-lan`), `OneConnect`, and `FastL4` settings per `AT1`–`AT4` app;
- current WAF policy deployment model (manual GUI vs. declarative config-as-code / AS3 / BIG-IQ) and emergency false-positive bypass runbooks;
- peak throughput baselines per tenant (HTTP RPS, TLS handshake TPS, AWAF CPU/RAM footprint, concurrent WebSockets) needed to size software-only `r2800` (no FPGA, 8 vCPU);
- cross-layer request correlation ID propagation across `LTM → WAF → CFW → ELB → App`;
- application-by-application **Active/Active vs. Active/Passive (manual `T5` DR)** inventory to determine which applications are eligible for a 99.95% SLO.

Target-state implementation design is documented in [future_architecture_improvements.md](./future_architecture_improvements.md).

# 11. Current availability requirement, 25% impact threshold, and reporting rule

Use **99.95% total availability** as the end-to-end service-level target to assess.

This **99.95% target explicitly includes BOTH managed outages (planned maintenance, patching, upgrades, certificate rotations, policy changes) AND unmanaged outages (unplanned hardware, software, network, or dependency failures) combined**. It corresponds approximately to:

- **4 hours 22 minutes 48 seconds per year** (managed + unmanaged combined);
- **21 minutes 54 seconds per average month**;
- **5 minutes 2 seconds per week**.

## 11.1 Potential 25% maximum impact threshold

Evaluate every topology option and change model against a **potential ≤ 25% maximum impact requirement**, assessed across two complementary dimensions:

1. **Estate / tenant blast-radius dimension:** In a four-tenant estate, **1 tenant = 25%**. A single infrastructure failure, maintenance error, or bad policy push should affect **at most 1 tenant (≤ 25%)** — never all 4 tenants (100%) simultaneously.
2. **Capacity / user-exposure dimension:** During a single-node outage, rolling upgrade wave, or canary test, capacity loss or canary blast radius should remain **≤ 25%** (and **0% user outage** whenever `K + 2` / `N-2` active capacity is maintained).

Every failure analysis must report outcomes separately for:

- external human users;
- external systems/API clients;
- internal users/systems;
- dependent applications such as App A -> B -> C.

The preferred service RTO measure is:

> **time from fault to the first successful business transaction for the affected actor**

not simply "device green" or "WAF recovered".

Always account separately for:
- **`T6a` (client-side recovery):** automated client retry/reconnect/re-auth/replay (seconds) vs. **manual user steps** (browser refresh, re-login, client restart, re-entering work — minutes+ if the client is poorly architected);
- **`T6b` (server-side application & state recovery):** automated session/state lookup, pool reset, warmup, and transaction reconciliation (seconds to ~1–2 min);
- **`T5` (manual server-side / operational recovery):** passive-site startup, manual DB failover/promotion, or manual reconciliation (minutes to hours).

# 12. Current ownership / scope constraints

The current WAF study does **not** assume:

- GTM/LTM consolidation;
- a new shared-LTM design;
- cross-site WAF route-back;
- cross-site application-dependency routing;
- a particular GTM L7 health-check implementation;
- a particular cross-site GTM prober model.

Those are target-state design choices requiring the relevant GTM/LTM/network/firewall/platform/application owners.

# 13. What belongs outside this current-state file

The following are **future / target-state improvements**, not stable current facts:

- target health-check placement and depth;
- GTM L7 checks against external/internal VIPs;
- cross-site/distributed GTM prober strategy;
- application health-check contracts;
- remote-WAF X2A/X2B routing;
- App B cross-site fallback XD1;
- preferred WAF sharing topology;
- maintenance/canary/rollback improvements;
- acceptance testing required before claiming 99.95%.

Document them in:

- [future_architecture_improvements.md](./future_architecture_improvements.md)

Topology and F5 implementation choices remain in:

- [analysis_variables_and_f5_assumptions.md](./analysis_variables_and_f5_assumptions.md)

Derived resilience conclusions remain in the executive, deployment, failure and maintainability documents.


# 14. Current-state diagram rules

Current-state diagrams must:

- keep DNS/GTM control-plane flows separate from application data paths;
- show external and internal DNS/VIP paths separately where they differ;
- retain the distinct internal firewall and private-cloud CFW boundaries;
- preserve Site 1 and Site 2 as separate failure domains;
- show application dependencies where they materially affect availability;
- avoid drawing target-state capabilities as deployed facts.

Do **not** silently show the following as current state unless validated:

- GTM Layer-7 checks of every external/internal VIP;
- direct cross-site GTM probing;
- X2A/X2B remote-WAF/front-end routing;
- automatic B1 -> B2 dependency fallback;
- a preferred shared-WAF target topology.

Those belong in [future_architecture_improvements.md](./future_architecture_improvements.md) and the relevant option-analysis documents.
