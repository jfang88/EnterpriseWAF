# High-Level EnterpriseWAF Architecture

**Status:** Canonical high-level entity/relationship and traffic-path view  
**Primary scope:** Four-tenant **extranet** application-delivery architecture across two sites  
**Detailed resilience analysis:** [end_to_end_service_impact_analysis.md](./end_to_end_service_impact_analysis.md)  
**Topology options:** [deployment_options_resilience_summary.md](./deployment_options_resilience_summary.md)  
**Executive recommendation:** [executive_recommendation.md](./executive_recommendation.md)

# 1. Purpose and scope

This document is the top-level architecture view for the EnterpriseWAF analysis.

The main discussion is the existing/future **four-tenant extranet environment**. External partner/customer users reach applications over private leased-line/VPN style networks. Internal users and internal application dependencies use separate internal DNS and service paths.

Use this document to answer:

- who consumes the applications;
- which DNS namespace each consumer uses;
- which network path each consumer follows;
- where GTM, firewall, LTM, WAF, CFW and ELB sit;
- where applications are hosted;
- how App A -> B -> C/D dependencies are reached;
- which layers are owned by this WAF work versus other infrastructure/application teams;
- where cross-site recovery can occur;
- where the WAF is shared infrastructure versus application-coupled security policy.

It intentionally stays above the detailed W1/W2/W3/W4/S1/S2 implementation choices.

# 2. Current scope boundary: retain GTM/LTM, optimise WAF within it

The current four-tenant extranet design already has GTM/LTM/network ownership outside the WAF work.

For the **current target recommendation**:

> **Retain the existing GTM and tenant LTM service boundaries. Do not assume LTM/GTM consolidation as part of the WAF decision.**

Consolidating or restructuring GTM/LTM remains a valid future target-state question, especially if applications converge onto a common private-cloud platform, but it requires participation from the teams that own:

- GTM / BIG-IP DNS;
- LTM;
- edge firewall / routing;
- WAN / leased-line / VPN connectivity.

Those teams have not yet joined this design exercise, so the WAF analysis must not silently redesign their services.

The WAF architecture can still progress independently by comparing:

- dedicated tenant WAF capacity;
- tenant LTMs feeding a shared active WAF pool;
- shared reserve WAF models;
- WAF HA clusters;
- cross-site WAF contingency where upstream owners later validate the required routing/LTM behavior.

# 3. Architecture ownership boundary

The architecture is intentionally split into ownership domains.

~~~mermaid
flowchart TB

  subgraph EXT[Joint / external-owner infrastructure]
    DNS[External + internal DNS / GTM]
    NET[Leased line / VPN / routing]
    FW[Edge firewall / VIP / NAT]
    LTM[LTM HA / service VIPs]
    DNS --> NET --> FW --> LTM
  end

  subgraph WAFS[EnterpriseWAF scope]
    WR[WAF runtime / enforcement capacity]
    WP[Application-specific WAF policies]
    WC[WAF capacity, HA, change, rollback, monitoring]
    LTM --> WR
    WR --> WP
    WP --> WC
  end

  subgraph PLATFORM[Platform / application-owner scope]
    CFW[Platform/cloud firewall - CFW]
    ELB[ELB / service / ingress]
    APP[Applications A/B/C/D]
    STATE[State / database / identity / event services]
    WC --> CFW --> ELB --> APP
    APP --> STATE
  end
~~~

## 3.1 What this WAF work can decide

This analysis can recommend:

- WAF topology and node-count pattern;
- shared versus dedicated WAF runtime capacity;
- application-policy isolation;
- WAF health, capacity and failure behavior;
- WAF maintenance/drain/canary/rollback model;
- cross-site WAF contingency as a **candidate capability**;
- application recovery requirements needed after WAF/path failure.

## 3.2 What requires other owners

The following cannot be committed unilaterally by the WAF work:

- GTM redesign or consolidation;
- LTM consolidation or service-boundary changes;
- new cross-site LTM steering;
- new inter-site routing/NAT/SNAT behavior;
- firewall route/policy changes;
- DNS/GTM health-policy changes;
- application-platform CFW/ELB changes.

Therefore X2A/X2B and similar front-end cross-site patterns should be described as:

> **Candidate target capabilities subject to GTM/LTM/network/firewall-owner validation.**

# 4. Core WAF principle: shared runtime, application-coupled policy

The WAF has two distinct architectural identities.

## 4.1 WAF runtime / enforcement capacity

The appliances or virtual WAF nodes can be operated as a **shared application-security platform** for the four-tenant extranet environment if the shared failure domain is acceptable.

This layer behaves like infrastructure:

~~~text
shared WAF nodes
  WAF1 / WAF2 / WAF3 / ...
~~~

## 4.2 WAF application policy

The policy enforced on that platform is **application-coupled**.

Each application can have different:

- URLs and routes;
- HTTP methods;
- API schemas;
- authentication patterns;
- WebSocket endpoints;
- upload/body-size limits;
- false-positive exceptions;
- signatures;
- bot/rate-limit controls;
- release/change timing.

Therefore:

> **Share WAF enforcement capacity where appropriate, but isolate policy, release, health and rollback by application.**

Conceptually:

~~~text
                 shared WAF enforcement platform
                /             |              \
       App A policy      App B policy      App C policy
            |                 |                 |
          App A             App B             App C
~~~

A shared WAF pool must **not** imply one monolithic security policy or one global application-policy change blast radius.

# 5. Layering model

| Layer | Primary role | Typical coupling | Ownership in this study |
|---|---|---|---|
| External/internal DNS, GTM | endpoint selection / namespace control | low-medium | other team / joint |
| Leased line / VPN / routing | reachability | low | other team |
| Edge firewall / VIP / NAT | network/security ingress | low-medium | other team |
| LTM / service VIP | delivery, health, load balancing | medium | other team / retained |
| **WAF enforcement platform** | shared application-security execution capacity | medium as infrastructure | **EnterpriseWAF** |
| **WAF policy** | application/API-specific protection | **high application coupling** | **EnterpriseWAF + application/security** |
| Platform/cloud firewall (CFW) | cloud security boundary | medium | platform/network |
| ELB / Kubernetes ingress / VM LB | workload distribution | high platform/application coupling | platform/application |
| Application | business service | complete | application |
| State/data/dependencies | transaction/service continuity | complete | application/platform |

# 6. Canonical end-to-end extranet topology

This is the primary high-level entity/relationship diagram for the four-tenant extranet design.

~~~mermaid
flowchart TB

  EU[External partner / customer users]
  ES[External systems / API clients]
  IU[Internal users / systems]

  EDNS[External / customer DNS]
  IDNS[Internal enterprise DNS]
  GTM[Enterprise BIG-IP DNS / GTM]

  EXTNET[Private leased line / VPN / extranet network]
  EFW[Edge firewall / external application VIP]

  T1LTM[Tenant 1 LTM HA]
  T2LTM[Tenant 2 LTM HA]
  T3LTM[Tenant 3 LTM HA]
  T4LTM[Tenant 4 LTM HA]

  WAF[WAF runtime / enforcement platform]
  POL[Application-specific WAF policies]

  ILTM[Internal LTM / service VIP]
  CFW[Private-cloud CFW]
  ELB[Private-cloud ELB / service tier]

  A[Application A]
  B[Application B]
  C[Application C]
  D[Application D]

  STATE[Session / state / DB / identity / event services]

  EU --> EDNS
  ES --> EDNS
  EDNS --> GTM
  GTM --> EXTNET
  EXTNET --> EFW

  EFW --> T1LTM
  EFW --> T2LTM
  EFW --> T3LTM
  EFW --> T4LTM

  T1LTM --> WAF
  T2LTM --> WAF
  T3LTM --> WAF
  T4LTM --> WAF

  WAF --> POL
  POL --> CFW
  CFW --> ELB

  ELB --> A
  ELB --> B
  ELB --> C
  ELB --> D

  IU --> IDNS
  IDNS --> ILTM
  ILTM --> CFW

  A --> IDNS
  D --> IDNS
  IDNS --> ILTM
  ILTM --> B
  B --> C

  A --> STATE
  B --> STATE
  C --> STATE
  D --> STATE
~~~

## 6.1 How to read the diagram

- the **four tenant LTM HA services remain in place** in the current target model;
- the WAF may be dedicated per tenant or shared across tenant LTMs depending the chosen W1/W2/W3/S1 pattern;
- the WAF runtime can be shared while application policies remain isolated;
- private-cloud applications sit behind CFW and ELB/service tiers;
- internal users use internal DNS/service paths and may bypass the external WAF;
- App A/B/C/D dependencies use internal service discovery/VIPs rather than being assumed to traverse the external WAF;
- GTM/LTM consolidation is not assumed.

# 7. External extranet-user path

Representative path:

~~~text
External partner/customer or API client
  -> external/customer DNS
  -> enterprise GTM / BIG-IP DNS
  -> returned external/firewall application VIP
  -> private leased line / VPN / extranet network path
  -> edge firewall
  -> existing tenant LTM HA service
  -> selected WAF topology
  -> application-specific WAF policy
  -> platform/cloud firewall (CFW)
  -> ELB/service
  -> application
~~~

The WAF policy belongs logically to the protected application even where WAF compute is shared.

# 8. Internal-user path

Representative internal flow:

~~~text
Internal user/system
  -> internal enterprise DNS
  -> optional delegation/conditional forward to GTM
  -> internal LTM/service VIP
  -> CFW
  -> ELB/service
  -> application
~~~

Internal traffic does **not** automatically traverse the external/extranet WAF tier.

# 9. Application-to-application dependency path

Dependencies must be modeled separately from north-south extranet ingress.

~~~text
App A
  -> internal DNS
  -> B service VIP / health-aware service endpoint
       |
       +-- B1 Site 1 preferred
       |
       +-- B2 Site 2 fallback
  -> App B
  -> App C

App D
  -> same B service
~~~

The preferred design goal is:

> **A B1 failure remains a B recovery event; it should not automatically become an A/C/D site-failover event.**

This requires:

- stable service abstraction;
- bounded timeout/retry;
- state/data compatibility;
- downstream dependency readiness;
- capacity for fallback traffic;
- cross-site dependency routing where approved.

# 10. App A/B/C/D cascading failure

Without dependency-local recovery:

~~~text
                         B1 fails
                            |
                +-----------+-----------+
                |           |           |
               A1          C1          D1
          timeout/retry timeout/retry timeout/retry
                \           |           /
                 connection/thread pools
                         fill
                          |
                  readiness may fail
                          |
                  GTM/site withdrawals
                          |
             multiple applications move
                          |
             Site 2 reconnect/login surge
~~~

With local-preferred / remote-fallback dependency routing:

~~~text
A1 / C1 / D1
      |
  B service VIP
    /       \
 B1         B2
Site 1     Site 2
preferred fallback

B1 failure -> withdraw B1 -> retry B2
            -> A/C/D remain in Site 1
~~~

Cross-site dependency reachability should therefore be designed **early as a candidate platform capability**, but its implementation requires the relevant network/LTM/firewall/application owners.

It must not become a mandatory steady-state dependency: healthy Site 1 services should continue if the inter-site path fails.

# 11. Two-site extranet relationship

~~~mermaid
flowchart LR

  GTM2[GTM / DNS]

  subgraph SITE1[Site 1]
    FW1[Extranet firewall/VIPs]
    L1[Four tenant LTM HA services]
    W1[WAF capacity]
    F1[CFW]
    E1[ELB/services]
    APP1[Apps A/B/C/D]
    FW1 --> L1 --> W1 --> F1 --> E1 --> APP1
  end

  subgraph SITE2[Site 2]
    FW2[Extranet firewall/VIPs]
    L2[Four tenant LTM HA services]
    W2[WAF capacity]
    F2[CFW]
    E2[ELB/services]
    APP2[Apps / DR instances]
    FW2 --> L2 --> W2 --> F2 --> E2 --> APP2
  end

  GTM2 --> FW1
  GTM2 --> FW2

  L1 -. X2A candidate: remote WAF .-> W2
  L2 -. X2B candidate: route back .-> APP1
  APP1 -. XD1 candidate: remote dependency .-> APP2
~~~

Interpretation:

- Site 1 and Site 2 remain separate infrastructure failure domains;
- each site retains the current extranet tenant LTM/GTM concept;
- cross-site routing is contingency capability, not normal dependency;
- X2A/X2B require GTM/LTM/network-owner validation;
- XD1 additionally requires application/state/dependency validation.

# 12. Target-state question: should LTM/GTM eventually consolidate?

This remains a valid future architecture question, especially if the four extranet tenants ultimately host applications on the same private-cloud platform.

However, the current WAF analysis does **not** recommend changing those services because their owning teams have not participated.

For now:

~~~text
Keep:
  existing GTM model
  existing four tenant LTM HA services

Optimise within/behind them:
  WAF node topology
  WAF sharing model
  application policy isolation
  CFW/ELB readiness
  application dependency resilience
~~~

Future joint review can ask:

- are four tenant LTM pairs still required as independent failure/change domains?
- can some VIP/service groups safely share an LTM platform?
- should GTM health/monitoring be changed?
- can X2A/X2B be supported safely?
- what routing/NAT/firewall changes would be required?

Until those owners participate, these remain **future optimisation opportunities**, not assumptions.

# 13. Implications for W1/W2/W3/S1/S2

The current four-tenant extranet boundary remains the comparison baseline.

- **W1:** independent active WAF pool behind a tenant LTM.
- **W2:** WAF HA cluster behind/with the existing tenant delivery path.
- **W3:** tenant-preferred WAFs plus shared reserve.
- **S1:** the existing four tenant LTM HA services feed a shared independent active WAF pool.
- **S2:** shared LTM + shared WAF remains a comparison only; it is **not** the current target because LTM consolidation is outside scope.

This makes S1 the natural shared-WAF comparison without redesigning LTM/GTM ownership boundaries.

# 14. Architecture review questions

Before target-state approval, answer:

1. Is the shared WAF runtime sized for aggregate four-tenant N-1/N-2 load?
2. Are application WAF policies independently versioned, canaried and rolled back?
3. What is the maximum acceptable common WAF runtime blast radius?
4. Can one tenant/application traffic surge exhaust another tenant?
5. Is CFW/ELB health included in end-to-end readiness?
6. Can App A/C/D use B2 safely when B1 fails?
7. What cross-site routing capability is technically possible?
8. Which cross-site capabilities require LTM/GTM/network/firewall-owner approval?
9. Does Site 2 have capacity for the credible aggregate failover event?
10. At a future joint architecture review, do the existing four LTM/GTM tenant boundaries still provide useful isolation?

# 15. Diagram and visualisation index

The repository currently keeps most architecture visualisations **inside the Markdown documents**, using Mermaid and ASCII/text diagrams rather than separate PNG/SVG files.

Primary locations:

| Visualisation | Location |
|---|---|
| **Canonical end-to-end consumers/DNS/network/apps diagram** | this document — sections 6 and 11 |
| W1/W2/W3/W4/S1/S2 topology diagrams | [deployment_options_resilience_summary.md](./deployment_options_resilience_summary.md) and [executive_recommendation.md](./executive_recommendation.md) |
| App A/B/C/D cascade | this document section 10 and [end_to_end_service_impact_analysis.md](./end_to_end_service_impact_analysis.md) |
| X2A/X2B/X2C/XD1 cross-site routing | [cross_site_routing_and_dependency_recovery.md](./cross_site_routing_and_dependency_recovery.md) |
| LTM/WAF 2-vs-3 node diagrams | [appendix_ltm_waf_2_vs_3_nodes.md](./appendix_ltm_waf_2_vs_3_nodes.md) |
| WebSocket state/reconnect diagrams | [../waf_websocket_resilience_cloud_patterns.md](../waf_websocket_resilience_cloud_patterns.md) |
| Management visuals | generated PowerPoint/PDF deck; currently an artifact, not the Markdown source of truth |

For architecture maintenance, the **Markdown/Mermaid diagrams are the source of truth**. Rendered slide diagrams should be regenerated from the current architecture rather than treated as independent design inputs.

# 16. Source-of-truth relationship

Use this document for the **high-level entity/relationship, ownership-boundary and traffic-path picture**.

Then use:

- [enterprise_scenario_invariants.md](./enterprise_scenario_invariants.md) for stable environment facts;
- [analysis_variables_and_f5_assumptions.md](./analysis_variables_and_f5_assumptions.md) for topology/timing choices;
- [executive_recommendation.md](./executive_recommendation.md) for the decision recommendation;
- [deployment_options_resilience_summary.md](./deployment_options_resilience_summary.md) for option comparison;
- [end_to_end_service_impact_analysis.md](./end_to_end_service_impact_analysis.md) for failure/user impact;
- [cross_site_routing_and_dependency_recovery.md](./cross_site_routing_and_dependency_recovery.md) for X2A/X2B/X2C/XD1 detail.
