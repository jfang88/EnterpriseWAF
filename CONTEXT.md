# CONTEXT.md

## EnterpriseWAF project context

This file provides durable grounding for ChatGPT, Codex and other coding/documentation agents working on this repository. It deliberately includes the **current-state architecture and stable invariants** so an agent can recover the essential architecture from the repository root without relying on chat history.

Detailed evidence and analysis remain under `enterprise-scenarios/`.

## Source-of-truth model

Use these documents in this order:

1. `enterprise-scenarios/current_architecture_and_invariants.md` — authoritative current-state facts, topology, stable invariants and layer model
2. `enterprise-scenarios/future_architecture_improvements.md` — future/to-be architecture and target health-monitoring model
3. `enterprise-scenarios/executive_recommendation.md` — executive recommendation
4. `enterprise-scenarios/common_failure_matrix.md` — failure analysis
5. `enterprise-scenarios/cross_site_routing_and_dependency_recovery.md` — cross-site and dependency recovery
6. `enterprise-scenarios/analysis_variables_and_f5_assumptions.md` — assumptions and implementation variables
7. `waf_websocket_resilience_cloud_patterns.md` — WebSocket resilience patterns

The repository `README.md` contains the complete document map.

# CURRENT / STABLE ARCHITECTURE AND INVARIANTS

The following is the durable current-state baseline. Do not replace unknowns with preferred target-state behaviour.

## 1. Environment and failure domains

- There are **two sites: Site 1 and Site 2**.
- The two sites are separate infrastructure and routing failure domains.
- The primary study covers a **four-tenant extranet application-delivery environment**.
- The wider estate may contain approximately 3-4 tenant or hosting contexts.
- The service is assessed against an approximately **99.95% availability target**.
- Planned maintenance must be considered where it counts against the service target.
- Cross-site WAF, front-end or application-dependency routing is **not assumed to exist today** unless explicitly validated.

## 2. External connectivity and edge

- External partner/customer users and API clients primarily use **private leased-line / VPN-style connectivity**.
- Each tenant/site has **two HA edge-firewall pairs, two devices per pair (2 x 2 devices)**.
- Externally reachable application VIPs reside on the **edge-firewall tier**.
- GTM/DNS is an **edge service inside the edge-firewall security boundary**.

## 3. GTM / DNS

- Each site has a **BIG-IP DNS/GTM cluster**.
- The site GTM clusters communicate and synchronize the enterprise GTM/DNS view.
- GTM synchronization does **not** imply synchronization of LTM, WAF, CFW or application configuration.
- BIG-IP DNS/GTM is a **DNS control-plane / endpoint-selection service**, not an inline HTTP/TCP application hop.
- DNS resolution and application data traffic must therefore be shown as separate flows.

### External DNS path

Representative current control path:

```text
External user/system
  -> external/customer DNS resolver
  -> private leased line / VPN / extranet path
  -> edge firewall
  -> enterprise edge BIG-IP DNS / GTM cluster
  -> DNS answer containing selected external/firewall application VIP
```

The subsequent application connection uses the returned VIP and does not traverse GTM as an inline proxy.

### Internal DNS path

- Internal users and systems use **internal enterprise DNS**.
- For selected endpoint names or namespaces, internal DNS may **delegate or conditionally forward** resolution to the **same enterprise edge GTM service**.
- Internal and external DNS namespaces/answers are logically distinct even when the same GTM platform participates in both.

Representative current control path:

```text
Internal user/system
  -> internal enterprise DNS
  -> [selected delegated / conditionally forwarded name]
  -> enterprise edge BIG-IP DNS / GTM cluster
  -> DNS answer containing internal service/LTM VIP
```

## 4. LTM and WAF

- Existing tenant LTM HA boundaries are retained.
- The default current model is **two LTMs per tenant/site in an HA/Sync-Failover pair**.
- BIG-IP Advanced WAF/ASM is part of the application-delivery path.
- The exact WAF topology, sharing model and preferred target design are **design variables**, not stable current-state invariants.

## 5. Internal network and private cloud

- Internal users, desktops, systems, internal DNS and internal service/LTM VIPs are **outside the private-cloud boundary**.
- A distinct **internal firewall** separates the enterprise internal network from private cloud.
- A separate **private-cloud firewall (CFW)** sits in front of private-cloud ELB/service endpoints.
- The internal firewall and CFW are different security, state and failure domains.
- Applications may run on VMs, Kubernetes, PaaS or on-premises platforms.

## 6. Current application data paths

### External path

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

A WAF topology option may change how traffic is handled around the LTM/WAF portion, but must not silently change the surrounding stable layers.

### Internal path

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

Important implications:

- an internal-firewall failure can affect internal users while the external path remains healthy;
- a CFW failure can affect both external and internal callers where both paths converge on the same private-cloud CFW.

## 7. Application hosting patterns

The current estate may include:

### H1 — on-premises

```text
WAF/LTM
  -> application LB/VIP
  -> servers/VMs
```

### H2 — private-cloud VM

```text
WAF/LTM
  -> CFW
  -> ELB
  -> VM pool
```

### H3 — private-cloud Kubernetes

```text
WAF/LTM
  -> CFW
  -> ELB
  -> Kubernetes ingress/service
  -> pods
```

### H4 — PaaS / stable service endpoint

```text
WAF/LTM
  -> CFW
  -> stable/floating ELB/service endpoint
  -> Site 1 or Site 2 workload
```

## 8. Application dependencies

Application-to-application dependencies are first-class availability dependencies and must be analysed separately from north-south WAF ingress.

Representative chain:

```text
Application A ----\
                  -> Application B -> Application C
Application D ----/
```

A dependency may use:

- a site-local/static endpoint;
- internal DNS;
- selected internal DNS delegation/forwarding to GTM;
- private-cloud service discovery;
- a stable internal service VIP.

The current existence of automatic **B1 -> B2 cross-site fallback is not assumed** unless explicitly confirmed.

## 9. Application classes

Failure and recovery analysis must distinguish:

- **AT1 — stateless web**
- **AT2 — stateful web**
- **AT3 — WebSocket/socket/long-lived connection**
- **AT4 — non-web/L4 application that may bypass WAF**

Infrastructure recovery is not complete until application-specific recovery succeeds.

Typical implications:

- stateless web: retry and idempotency;
- stateful web: session/state portability and transaction reconciliation;
- WebSocket: reconnect, re-authenticate, re-subscribe, sequence/gap recovery and replay;
- non-web/L4: protocol-specific reconnect, re-resolution and replay behaviour.

## 10. Current architecture layer model

Use this layer breakdown when creating or reviewing diagrams and slides:

| Layer | Current role | Current boundary |
|---|---|---|
| **L0 — users / resolvers** | external users/API clients, external/customer DNS, internal users, internal enterprise DNS | outside application-delivery/private-cloud stack |
| **L1 — global DNS / site selection** | Site 1 and Site 2 BIG-IP DNS/GTM clusters; selected external/internal names | edge service behind edge firewall |
| **L2 — site edge / ingress** | private leased line/VPN, 2 x 2 edge firewalls, external application VIPs | site edge/security |
| **L3 — local delivery/security** | tenant LTM HA service and WAF tier | tenant application-delivery path |
| **L4 — internal access boundary** | internal LTM/service VIP and internal firewall | enterprise internal network -> private cloud |
| **L5 — private-cloud delivery** | CFW and ELB/service | private-cloud boundary |
| **L6 — business application** | App A/B/C/D, sessions, state, DB, identity, event services | application/platform |
| **L7 — application dependencies** | App A/D -> B -> C and other shared services | application/service architecture |

Health and observability are **cross-cutting concerns**, not an additional inline network layer.

## 11. Current availability reporting rule

Use **99.95% availability** as the service-level target to assess.

If planned maintenance counts against the target, 99.95% corresponds approximately to:

- 4 hours 22 minutes 48 seconds per year;
- 21 minutes 54 seconds per average month;
- 5 minutes 2 seconds per week.

Failure analyses should report outcomes separately for:

- external human users;
- external systems/API clients;
- internal users/systems;
- dependent applications such as App A -> B -> C.

Preferred RTO measure:

> time from fault to the first successful business transaction for the affected actor

Do not treat “device green”, “port up” or “WAF recovered” as equivalent to full service recovery.

# CURRENT HEALTH-CHECK STATE — KNOWN AND UNKNOWN

The architecture and placement of GTM are known, but the exact current health-monitoring implementation has **not yet been fully validated**.

The following must remain **unknown / validate** until evidence is added:

| Item | Current status |
|---|---|
| GTM uses TCP/port checks versus HTTP/L7 checks | **Unknown — validate** |
| GTM directly performs L7 checks against each external VIP | **Unknown — validate** |
| GTM directly performs L7 checks against each internal VIP used by delegated internal names | **Unknown — validate** |
| GTM consumes LTM virtual-server/application health using iQuery | **Unknown — validate** |
| Site 1 GTM probes Site 2 endpoints and Site 2 GTM probes Site 1 endpoints | **Unknown — validate** |
| GTM synchronization group/prober-pool behaviour and availability rules | **Unknown — validate** |
| Monitor intervals, timeouts and up/down thresholds | **Unknown — validate** |
| Application-owned readiness endpoints exist for all critical services | **Unknown — validate** |
| Health checks prove CFW -> ELB -> application reachability | **Unknown — validate** |
| Health checks include critical App A -> B -> C dependencies | **Unknown — validate per application** |
| Independent external/user-like synthetic monitoring feeds the SLO | **Unknown — validate** |

A port-level check can therefore be green while the business service is unusable:

```text
GTM sees listener UP
        |
        v
WAF/LTM TCP port responds
        |
        X
CFW / ELB / application unavailable
```

This is a **false-green health state**.

# TARGET / TO-BE HEALTH-MONITORING DIRECTION

The intended target is a layered health model.

## 1. Local service/member health

- LTM and ELB perform fast local member/service checks and recovery.

## 2. External service health

- GTM makes DNS/site decisions using **Layer-7 health of the published external VIP/service**.

## 3. Internal service health

- Internal delegated names use **Layer-7 health of the corresponding internal VIP/service**.
- This may be direct from GTM or via authoritative LTM/iQuery health where appropriate.

## 4. Application endpoint health

- Important applications expose stable readiness endpoints.
- Application teams define what constitutes healthy service behaviour.

## 5. Dependency health

- Shared/downstream dependencies are monitored at the appropriate dependency/service layer.
- Do not make every top-level endpoint fail because a non-critical downstream dependency failed.

## 6. Independent validation

- Synthetic/end-to-end monitoring validates the actual user/SLO outcome independently of infrastructure health.

The target must minimise both:

- **false green** — infrastructure appears reachable while the business service is unusable; and
- **false red** — over-deep checks withdraw a usable service because a non-critical dependency has failed.

## Target health ownership

A useful ownership model is:

- **GTM** — site/DNS availability decision
- **LTM** — local VIP/pool/member availability
- **WAF** — security enforcement and local processing health
- **ELB/service platform** — backend service/member health
- **application** — readiness semantics
- **synthetic monitoring** — user-visible end-to-end outcome

Where internal DNS delegates application namespaces to GTM, the GTM health decision must represent the **internal published service path**, not automatically reuse an external-path health signal unless the paths are proven equivalent.

# NOT CURRENT-STATE FACTS

Do not show the following as already deployed unless separately validated:

- GTM Layer-7 synthetic checks of every external/internal VIP;
- cross-site/distributed GTM probing;
- a particular iQuery health model;
- X2A/X2B remote-WAF/front-end routing;
- automatic B1 -> B2 cross-site dependency fallback;
- a preferred shared WAF topology such as S1;
- GTM/LTM consolidation;
- a new shared-LTM design;
- maintenance/canary/rollback improvements;
- acceptance testing not yet completed.

These belong in the target-state and option-analysis documents.

# DIAGRAM AND SLIDE GROUNDING

Management artifacts live under `management-artifacts/`.

When diagrams or slides are updated:

- distinguish **current state** from **target state**;
- keep DNS control-plane paths separate from application data paths;
- represent external and internal DNS/VIP paths separately where they differ;
- show GTM, edge firewall, LTM, WAF, internal firewall, CFW, ELB/service and application layers distinctly where useful;
- do not imply that a TCP listener or device being reachable proves application availability;
- keep health-check ownership visible by layer;
- preserve Site 1 and Site 2 as separate failure domains;
- keep application dependencies visible where they materially affect recovery;
- ensure the slide layer breakdown matches the canonical architecture layer model above.

If a diagram or slide conflicts with the current-state Markdown, the Markdown wins until the discrepancy is deliberately resolved.

# WORKING CONVENTION

Use `AGENTS.md` as the operating instructions for automated agents.

Use this file as durable root-level project grounding.

Use the detailed Markdown under `enterprise-scenarios/` as the authoritative evidence and source of truth for architecture decisions.

When new current-state facts are validated, update `enterprise-scenarios/current_architecture_and_invariants.md` first, then update this root context, diagrams and management artifacts as required.
