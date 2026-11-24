# High-Level EnterpriseWAF Architecture

**Status:** Canonical high-level entity/relationship and traffic-path view  
**Primary scope:** Four-tenant **extranet** application-delivery architecture across two sites  
**Detailed resilience analysis:** [end_to_end_service_impact_analysis.md](./end_to_end_service_impact_analysis.md)  
**Topology options:** [deployment_options_resilience_summary.md](./deployment_options_resilience_summary.md)  
**Executive recommendation:** [executive_recommendation.md](./executive_recommendation.md)

# 1. Purpose and scope

This document is the top-level architecture view for the EnterpriseWAF analysis.

The primary discussion is the four-tenant extranet environment. External partner/customer users reach applications through private leased-line/VPN style connectivity. Internal desktops/users/systems use the enterprise internal network and internal DNS, which are **outside the private-cloud security boundary**.

The key boundary rule is:

> **Internal users, internal enterprise DNS and the internal LTM/service-VIP layer are outside the private cloud. A separate internal firewall separates the enterprise internal network from the private-cloud CFW.**

For a private-cloud hosted service, the representative internal path is therefore:

```text
Internal user/system
  -> internal enterprise DNS
  -> optional internal GTM / service-name resolution
  -> internal LTM / service VIP
  -> internal firewall
  -> private-cloud CFW
  -> ELB / service
  -> application
```

The internal firewall and the CFW are distinct security and failure domains. Do not collapse them into one firewall in diagrams or failure analysis.

# 2. Current scope boundary: retain GTM/LTM, optimise WAF within it

For the current target recommendation:

> **Retain the existing GTM and tenant LTM service boundaries. Do not assume LTM/GTM consolidation as part of the WAF decision.**

Consolidating or restructuring GTM/LTM remains a future joint architecture question requiring the teams that own GTM/BIG-IP DNS, LTM, edge firewall/routing and WAN/private-network connectivity.

The EnterpriseWAF work can proceed by comparing:

- dedicated tenant WAF capacity;
- tenant LTMs feeding a shared active WAF pool;
- shared-reserve WAF models;
- WAF HA clusters;
- cross-site WAF contingency where upstream owners validate the required routing/LTM/firewall behavior.

# 3. Architecture ownership and security boundaries

The architecture has distinct **DNS/control-plane**, enterprise-network, application-delivery and private-cloud boundaries.

The enterprise BIG-IP DNS/GTM service is an **edge service behind the edge firewall**. It is reachable from both:

- external/customer DNS over the private leased-line/VPN/extranet path; and
- internal enterprise DNS for selected delegated/forwarded names.

It is not an inline hop in the HTTP/TCP application data path.

~~~mermaid
flowchart LR

  subgraph EXTERNAL[External / customer environment]
    EU[External users / API clients]
    EDNS[External / customer DNS]
    EU --> EDNS
  end

  subgraph ENTERPRISE[Enterprise internal network - outside private cloud]
    IU[Internal users / desktops / systems]
    IDNS[Internal enterprise DNS]
    ILTM[Internal LTM / service VIP]
    IFW[Internal firewall]
    IU --> IDNS --> ILTM --> IFW
  end

  subgraph EDGE[Enterprise edge zone - inside edge firewall]
    NET[Private leased line / VPN]
    EFW[Edge firewall / application VIP]
    GTM[Edge BIG-IP DNS / GTM cluster]
    TLTM[Tenant LTM HA service]
    WAF[WAF runtime / enforcement]
    POL[Application-specific WAF policy]
    NET --> EFW
    EFW --> TLTM --> WAF --> POL
    EFW -. DNS query .-> GTM
  end

  subgraph PCLOUD[Private cloud boundary]
    CFW[Platform / cloud firewall - CFW]
    ELB[ELB / service / ingress]
    APP[Applications A/B/C/D]
    STATE[State / DB / identity / event services]
    CFW --> ELB --> APP --> STATE
  end

  EDNS -. delegated/query over private path .-> NET
  IDNS -. selected internal names .-> GTM
  POL --> CFW
  IFW --> CFW
~~~

## 3.1 EnterpriseWAF decisions

This analysis can recommend:

- WAF topology and node-count pattern;
- shared versus dedicated WAF runtime capacity;
- application-policy isolation;
- WAF health, capacity and failure behavior;
- WAF maintenance/drain/canary/rollback model;
- cross-site WAF contingency as a candidate capability;
- application recovery requirements after WAF/path failure.

## 3.2 Decisions requiring other owners

The following require the relevant owning teams:

- GTM redesign or consolidation;
- LTM consolidation or service-boundary changes;
- new cross-site LTM steering;
- inter-site routing/NAT/SNAT changes;
- edge-firewall or internal-firewall policy/routing changes;
- DNS/GTM health-policy changes;
- private-cloud CFW/ELB changes.

X2A/X2B are therefore **candidate target capabilities subject to GTM/LTM/network/firewall-owner validation**.

# 4. Core WAF principle: shared runtime, application-coupled policy

The WAF has two architectural identities.

## 4.1 Shared WAF runtime / enforcement capacity

WAF appliances or virtual nodes can be operated as shared application-security capacity for the four-tenant extranet environment when the shared failure domain is acceptable.

## 4.2 Application-coupled WAF policy

The policy is tightly coupled to the protected application/API. Applications can differ in URLs, methods, API schemas, authentication flows, WebSocket endpoints, upload limits, false-positive exceptions, signatures, bot/rate controls and release timing.

Therefore:

> **Share WAF enforcement capacity where appropriate, but isolate policy, release, health and rollback by application.**

# 5. Layering model

| Layer | Primary role | Boundary / ownership |
|---|---|---|
| External/customer DNS | external resolver / delegation | customer/external |
| Internal enterprise DNS | internal resolver / delegation | enterprise internal network |
| **Edge BIG-IP DNS / GTM cluster** | endpoint selection for selected external and internal names; located inside edge-firewall boundary | joint DNS/GTM infrastructure |
| Private leased line / VPN | external DNS/application reachability | network |
| Edge firewall / external VIP | protects/reaches edge GTM and extranet application VIPs | network/security |
| Tenant LTM | delivery, health and load balancing | retained infrastructure |
| WAF runtime | application-security enforcement capacity | EnterpriseWAF |
| WAF policy | application/API-specific protection | EnterpriseWAF + application/security |
| **Internal users + internal DNS** | enterprise desktop/system network and name resolution | **outside private cloud** |
| Internal LTM / service VIP | internal service delivery | enterprise/internal network |
| **Internal firewall** | boundary between internal network and private cloud | network/security |
| **Private-cloud CFW** | private-cloud security boundary | platform/network |
| ELB / ingress / service | workload distribution | platform/application |
| Applications / state / dependencies | business service and continuity | application/platform |

# 6. Canonical end-to-end topology

The diagram deliberately separates **DNS resolution** from the subsequent application data connection.

~~~mermaid
flowchart TB

  EU[External partner / customer users]
  ES[External systems / API clients]
  EDNS[External / customer DNS]

  subgraph SITE1EDGE[Site 1 edge zone]
    EXTNET1[Private leased line / VPN]
    EFW1[2 x HA edge-firewall pairs / application VIPs]
    GTM1[Site 1 BIG-IP DNS / GTM cluster]
    T1LTM[Tenant LTM HA services]
    WAF1[WAF runtime / enforcement]
    POL1[Application-specific WAF policies]
    EXTNET1 --> EFW1
    EFW1 --> T1LTM --> WAF1 --> POL1
    EFW1 -. DNS query .-> GTM1
  end

  subgraph INTERNAL[Enterprise internal network - outside private cloud]
    IU[Internal users / desktops / systems]
    IDNS[Internal enterprise DNS]
    ILTM[Internal LTM / service VIP]
    IFW[Internal firewall]
    IU --> IDNS --> ILTM --> IFW
  end

  subgraph PCLOUD1[Site 1 private cloud boundary]
    CFW1[Private-cloud CFW]
    ELB1[Private-cloud ELB / service tier]
    A1[Application A]
    D1[Application D]
    BVIP1[B service VIP / service discovery]
    B1[Application B - Site 1 preferred]
    C1[Application C / shared dependencies]
    STATE1[Session / state / DB / identity / event services]

    CFW1 --> ELB1
    ELB1 --> A1
    ELB1 --> D1
    A1 --> BVIP1
    D1 --> BVIP1
    BVIP1 --> B1
    B1 --> C1
    A1 --> STATE1
    B1 --> STATE1
    C1 --> STATE1
    D1 --> STATE1
  end

  subgraph SITE2[Site 2 / DR]
    EFW2[2 x HA edge-firewall pairs / application VIPs]
    GTM2[Site 2 BIG-IP DNS / GTM cluster]
    T2LTM[Tenant LTM HA services]
    WAF2[WAF runtime / enforcement]
    CFW2[Private-cloud CFW]
    ELB2[ELB / service]
    B2[Application B - XD1 fallback]
    APP2[Other DR application instances]
    EFW2 --> T2LTM --> WAF2 --> CFW2 --> ELB2 --> APP2
    ELB2 --> B2
    EFW2 -. DNS query .-> GTM2
  end

  EU --> EDNS
  ES --> EDNS

  EDNS -. DNS query over private path .-> EXTNET1
  EU --> EXTNET1
  ES --> EXTNET1

  IDNS -. selected names use same edge GTM service .-> GTM1

  POL1 --> CFW1
  IFW --> CFW1

  GTM1 <-. GTM/DNS synchronization .-> GTM2
  BVIP1 -. XD1 remote dependency fallback .-> B2
~~~

## 6.1 How to read the diagram

- each site has a **GTM/DNS cluster**, and the site clusters synchronize the enterprise GTM/DNS view;
- each site also has the same **2 x 2 edge-firewall arrangement**: two HA firewall pairs with two devices per pair;
- the **same edge GTM service** can answer selected external and internal names;
- the GTM sits **behind the edge firewall**, even though external/customer DNS can call it across the private network;
- DNS resolution is control-plane traffic; after an answer is returned, the application data connection follows the selected VIP/path and does not traverse GTM;
- the four tenant LTM HA services remain in place in the current target model;
- the WAF may be dedicated per tenant or shared across tenant LTMs depending on W1/W2/W3/S1;
- private-cloud applications sit behind **CFW and ELB/service tiers**;
- **internal users, internal DNS, internal GTM where used, and internal LTM are outside the private-cloud boundary**;
- internal traffic crosses a distinct **internal firewall** before reaching the private-cloud CFW;
- external and internal flows may converge at the CFW/ELB/application tier, but they do not share the same ingress path;
- application dependencies are modelled separately from external WAF ingress.

# 7. External extranet-user path

DNS resolution and application traffic are separate.

### External DNS control path

```text
External user/system
  -> external/customer DNS
  -> private leased line / VPN / extranet path
  -> edge firewall
  -> enterprise edge GTM / BIG-IP DNS cluster
  -> DNS answer: selected external/firewall application VIP
```

### External application data path

```text
External partner/customer or API client
  -> private leased line / VPN / extranet network
  -> edge firewall / selected application VIP
  -> tenant LTM HA service
  -> selected WAF topology
  -> application-specific WAF policy
  -> private-cloud CFW
  -> ELB/service
  -> application
```

The GTM is therefore **reachable through the edge firewall but not inline in the application session**.

# 8. Internal-user path

For selected internal service names, internal enterprise DNS uses the **same edge GTM/DNS service** as the external lookup path.

```text
Internal user / desktop / system
  -> internal enterprise DNS
  -> [optional delegation/conditional forward]
  -> enterprise edge GTM / BIG-IP DNS cluster
  -> DNS answer: internal LTM / service VIP
  -> internal LTM / service VIP
  -> internal firewall
  -> private-cloud CFW
  -> ELB/service
  -> application
```

Important implications:

- internal users and internal DNS are **outside the private-cloud boundary**;
- the edge GTM/DNS service is shared as a resolution service, but the internal and external namespaces/answers remain logically distinct;
- the internal firewall can fail independently of the CFW;
- a WAF outage does not automatically make the application unavailable to internal users;
- an internal-firewall outage can block internal users while the extranet path remains healthy;
- a CFW outage can block both external and internal callers if both paths converge on that CFW.

# 9. GTM cluster and health-state model

Each site has a BIG-IP DNS/GTM cluster. The Site 1 and Site 2 clusters synchronize the enterprise GTM/DNS configuration/global availability view, while the exact **probe source and health-monitor depth** are configuration choices.

The architecture must distinguish these cases:

| Health model | What GTM really knows | Main risk / effect |
|---|---|---|
| **Port/listener only** | WAF/LTM listener responds | can remain **false green** when CFW/ELB/application is broken |
| **HTTP/L7 front-door check** | selected URL/response works through some or all of the path | stronger, but application teams must define a stable health contract |
| **Authoritative application-readiness signal** | service is genuinely ready according to an agreed readiness boundary | strongest if it represents the right dependencies without over-checking |
| **Site-local probes only** | local GTM cluster has direct local observation | remote cluster may learn state through GTM synchronization/timeout behavior; convergence can be longer |
| **Cross-site/distributed probes** | both sites can directly observe alternate service health | potentially faster/clearer global state, but requires routing/security and careful failure-domain design |

A simple WAF port check is insufficient evidence that the business service is healthy.

If application-layer health is required, application teams must provide the health-check contract, including as applicable:

- hostname/URI;
- method;
- expected status/body;
- authentication behavior;
- whether critical dependencies are included;
- maintenance/drain semantics;
- expected response time.

The checked endpoint should represent the agreed **service readiness boundary**. A health check that is too shallow creates false green; a check that includes every non-critical downstream dependency can create false red.

For timing, separate:

```text
local health detection
  + GTM synchronization/global-state convergence
  + GTM answer change
  + residual DNS TTL/cache
  + client retry/re-resolution
  + application recovery (T6)
```

If GTM does not directly/cross-site observe the failed service, do not assume the remote cluster converges on the local monitor timeout alone.

# 10. Application-to-application dependency path

For applications hosted inside the private cloud, dependency traffic may remain inside the private-cloud/application-service domain rather than leaving through the internal-user firewall path.

Representative pattern:

```text
App A / App D
  -> B service VIP / service discovery
       |
       +-- App B @ Site 1 preferred
       |
       +-- App B @ Site 2 fallback (XD1)
  -> App C / downstream dependencies
```

If an application must resolve enterprise internal DNS, that DNS control-plane dependency remains outside the private-cloud boundary and must be modelled separately from the data path.

The preferred design goal is:

> **A B1 failure remains a B recovery event; it should not automatically become an A/C/D site-failover event.**

# 11. App A/B/C/D cascading failure

Without dependency-local recovery:

```text
B1 fails
  -> A/C/D timeout and retry
  -> connection/thread pools fill
  -> readiness may fail
  -> multiple GTM/site withdrawals
  -> several applications move
  -> Site 2 reconnect/login/dependency surge
```

With XD1 local-preferred / remote-fallback dependency routing:

```text
A / C / D
    |
B service VIP
  /       \
B1        B2
Site 1    Site 2
preferred fallback

B1 failure -> withdraw B1 -> retry B2
           -> A/C/D remain in Site 1
```

Cross-site dependency reachability should be designed early as a candidate capability, but healthy Site 1 services must not depend on the inter-site path during normal operation.

# 12. Two-site relationship, GTM synchronization and contingency paths

~~~mermaid
flowchart LR

  subgraph SITE1[Site 1]
    FW1[2 x HA edge-firewall pairs / VIPs]
    G1[GTM/DNS cluster]
    L1[Tenant LTM HA]
    WAFS1[WAF capacity]
    CFW1[Private-cloud CFW]
    E1[ELB/services]
    APP1[Apps A/B/C/D]
    FW1 --> L1 --> WAFS1 --> CFW1 --> E1 --> APP1
    FW1 -. DNS .-> G1
    G1 -. local health signal .-> WAFS1
  end

  subgraph SITE2[Site 2]
    FW2[2 x HA edge-firewall pairs / VIPs]
    G2[GTM/DNS cluster]
    L2[Tenant LTM HA]
    WAFS2[WAF capacity]
    CFW2[Private-cloud CFW]
    E2[ELB/services]
    APP2[Apps / DR instances]
    FW2 --> L2 --> WAFS2 --> CFW2 --> E2 --> APP2
    FW2 -. DNS .-> G2
    G2 -. local health signal .-> WAFS2
  end

  G1 <-. GTM configuration/global-state synchronization .-> G2

  L1 -. X2A candidate: remote WAF .-> WAFS2
  WAFS2 -. X2B candidate: route back .-> CFW1
  APP1 -. XD1 candidate: remote dependency .-> APP2
~~~

Interpretation:

- Site 1 and Site 2 are separate infrastructure failure domains with **symmetric 2 x 2 edge-firewall HA structures**;
- each site has a GTM/DNS cluster and the clusters synchronize the enterprise GTM/DNS view;
- the exact health signal may stop at WAF/LTM or represent deeper application readiness; this must be declared;
- cross-site GTM probing is **not assumed** simply because the clusters synchronize;
- without cross-site health observation, remote convergence may include additional synchronization/timeout delay;
- DNS TTL begins to matter **after** the GTM service has decided to return a different endpoint;
- X2A/X2B require GTM/LTM/network/firewall-owner validation;
- XD1 additionally requires application/state/dependency validation.

# 13. Implications for W1/W2/W3/S1/S2

- **W1:** independent active WAF pool behind a tenant LTM.
- **W2:** WAF HA cluster behind/with the existing tenant delivery path.
- **W3:** tenant-preferred WAFs plus shared reserve.
- **S1:** existing tenant LTM HA services feed a shared independent active WAF pool.
- **S2:** shared LTM + shared WAF remains a future comparison; LTM consolidation is outside current scope.

The internal-network firewall/CFW boundary is independent of the WAF topology choice and must remain explicit in every option.

# 14. Architecture review questions

Before target-state approval, answer:

1. Is the shared WAF runtime sized for aggregate four-tenant N-1/N-2 load?
2. Are application WAF policies independently versioned, canaried and rolled back?
3. What is the maximum acceptable common WAF runtime blast radius?
4. Can one tenant/application traffic surge exhaust another tenant?
5. Are the **internal firewall and CFW monitored as separate failure domains**?
6. Does end-to-end readiness test the correct path through CFW/ELB/application?
7. Can App A/C/D use B2 safely when B1 fails?
8. What cross-site routing capability is technically possible?
9. Which cross-site capabilities require LTM/GTM/network/firewall-owner approval?
10. Does Site 2 have capacity for the credible aggregate failover event?
11. Does each GTM cluster probe only locally, or can it directly observe services in the other site?
12. What does a "healthy" GTM/LTM/WAF monitor actually prove: port up, HTTP response, or business-service readiness?
13. Which application team owns each application-layer health-check contract and its change lifecycle?

# 15. Version-controlled diagrams and management artifacts

The Markdown/Mermaid diagrams remain the architecture source of truth. Management renderings are also stored in Git for traceability and review.

Version-controlled artifacts are under:

- [`../management-artifacts/`](../management-artifacts/)
- [`../management-artifacts/diagrams/`](../management-artifacts/diagrams/)

The current high-level topology diagram is:

- [`../management-artifacts/diagrams/EnterpriseWAF_End_to_End_Topology.svg`](../management-artifacts/diagrams/EnterpriseWAF_End_to_End_Topology.svg)
- `../management-artifacts/diagrams/EnterpriseWAF_End_to_End_Topology.png` — generated/rendered copy

The current management deck is available as both PowerPoint and PDF in the same version-controlled artifact set. The deck, PDF and PNG diagrams are regenerated by the version-controlled build workflow from the management artifact source.

# 16. Source-of-truth relationship

Use this document for the high-level entity/relationship, security-boundary and traffic-path picture.

Then use:

- [enterprise_scenario_invariants.md](./enterprise_scenario_invariants.md) for stable environment facts;
- [analysis_variables_and_f5_assumptions.md](./analysis_variables_and_f5_assumptions.md) for topology/timing choices;
- [executive_recommendation.md](./executive_recommendation.md) for the decision recommendation;
- [deployment_options_resilience_summary.md](./deployment_options_resilience_summary.md) for option comparison;
- [end_to_end_service_impact_analysis.md](./end_to_end_service_impact_analysis.md) for failure/user impact;
- [cross_site_routing_and_dependency_recovery.md](./cross_site_routing_and_dependency_recovery.md) for X2A/X2B/X2C/XD1 detail.
