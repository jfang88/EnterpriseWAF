# High-Level EnterpriseWAF Architecture

**Status:** Canonical high-level entity/relationship and traffic-path view  
**Scope:** Consumers, DNS, network ingress, LTM/WAF, private-cloud security, application hosting, dependencies and cross-site recovery  
**Canonical shorthand/timing:** [architecture_shorthand_topology_reference.md](./architecture_shorthand_topology_reference.md)  
**Detailed resilience analysis:** [end_to_end_service_impact_analysis.md](./end_to_end_service_impact_analysis.md)  
**Topology options:** [deployment_options_resilience_summary.md](./deployment_options_resilience_summary.md)  
**Executive recommendation:** [executive_recommendation.md](./executive_recommendation.md)

# 1. Purpose

This document is the top-level architecture view for the EnterpriseWAF analysis.

Use it to answer:

- who consumes the applications;
- which DNS namespace each consumer uses;
- which network path each consumer follows;
- where LTM, WAF, CFW and ELB sit;
- where applications are hosted;
- how App A -> B -> C/D dependencies are reached;
- which layers are generic shared infrastructure versus application-coupled controls;
- where cross-site recovery can occur.

It intentionally stays above the detailed W1/W2/W3/W4/S1/S2 implementation choices. Those IDs have one canonical meaning in [architecture_shorthand_topology_reference.md](./architecture_shorthand_topology_reference.md).

# 2. Core architectural principle: shared WAF platform, application-coupled policy

The WAF has two distinct architectural identities.

## 2.1 WAF runtime / enforcement capacity

The appliances or virtual WAF nodes can be operated as a **shared application-security platform** within an approved security/trust zone.

Examples:

- an Internet-facing WAF pool;
- an Intranet/Extranet WAF pool;
- separate pools where regulatory, capacity, criticality or blast-radius requirements demand it.

This layer behaves like shared infrastructure:

~~~text
shared WAF nodes
  WAF-1 / WAF-2 / WAF-3 / ...
~~~

## 2.2 WAF application policy

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
- bot/rate-limit policy;
- release/change timing.

Therefore:

> **Share WAF enforcement capacity where the failure domain is acceptable, but isolate policy, release, health and rollback by application.**

Conceptually:

~~~text
                 shared WAF enforcement platform
                /             |              \
       App A policy      App B policy      App C policy
            |                 |                 |
          App A             App B             App C
~~~

A shared WAF pool must **not** imply one monolithic security policy or one global change blast radius.

# 3. Layering model

The architecture should be understood as separate layers:

| Layer | Primary role | Typical coupling |
|---|---|---|
| DNS / routing / leased line / VPN | reachability and endpoint selection | low application coupling |
| Edge firewall | network/security-zone ingress and VIP/NAT | low-medium |
| LTM / service VIP | application delivery, health and load balancing | medium |
| **WAF enforcement platform** | shared application-security execution capacity | medium as infrastructure |
| **WAF policy** | application/API-specific protection | **high application coupling** |
| Platform/cloud firewall (CFW) | cloud/network security boundary | medium |
| ELB / Kubernetes ingress / VM LB | workload distribution | high platform/application coupling |
| Application | business service | complete |
| State/data/dependencies | service continuity and transaction correctness | complete |

This distinction is important for ownership and change management:

- network teams can own common routing/LTM/WAF runtime standards;
- application/security teams must coordinate application-specific WAF policy changes with releases;
- WAF policy should support canary/staging/rollback independently of unrelated applications.

# 4. Canonical end-to-end entity and relationship view

The diagram below is the primary high-level logical architecture.

~~~mermaid
flowchart TB

  EU[External human users]
  ES[External systems / API clients]
  IU[Internal users / systems]

  EDNS[External / customer DNS]
  IDNS[Internal enterprise DNS]
  GTM[Enterprise BIG-IP DNS / GTM]

  EXTNET[Private leased line / VPN / external network]
  EFW[Edge firewall / external application VIP]

  ILTM[Internal LTM / service VIP]
  ELTM[External / application LTM HA pair]

  WAF[WAF enforcement platform]
  WPA[Application-specific WAF policy]

  CFW[Platform / cloud firewall - CFW]
  ELB[Private-cloud ELB / service tier]

  APPA[Application A]
  APPB[Application B]
  APPC[Application C]
  APPD[Application D]

  STATE[Session / state / database / event services]

  EU --> EDNS
  ES --> EDNS
  EDNS --> GTM
  GTM --> EXTNET
  EXTNET --> EFW
  EFW --> ELTM
  ELTM --> WAF
  WAF --> WPA
  WPA --> CFW
  CFW --> ELB
  ELB --> APPA

  IU --> IDNS
  IDNS --> ILTM
  ILTM --> CFW

  APPA --> IDNS
  APPD --> IDNS
  IDNS --> ILTM
  ILTM --> APPB
  APPB --> APPC

  APPA --> STATE
  APPB --> STATE
  APPC --> STATE
~~~

Interpretation:

- external users and API clients use the **external namespace**;
- internal users and application dependencies use the **internal namespace**;
- DNS/GTM is a resolution/control plane, not an inline HTTP hop;
- internal consumers may bypass the external WAF path;
- private-cloud hosted applications traverse CFW before ELB/service endpoints;
- application dependencies such as A -> B -> C are a separate recovery dimension from north-south WAF/LTM resilience.

# 5. External-user path

Representative north-south flow:

~~~text
External human/API client
  -> external/customer DNS
  -> enterprise GTM / BIG-IP DNS
  -> returned external/firewall VIP
  -> private leased line / VPN / external network path
  -> edge firewall
  -> external/application LTM
  -> WAF enforcement platform
  -> application-specific WAF policy
  -> platform/cloud firewall (CFW)
  -> ELB/service
  -> application
~~~

The WAF policy belongs logically to the protected application even when WAF compute is shared.

# 6. Internal-user path

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

Internal traffic does **not** automatically traverse the external WAF tier.

A WAF should be placed on an internal path only where the threat model and application-security requirement justify it.

# 7. Application-to-application dependency path

Dependencies must be modeled separately from user ingress.

Example:

~~~text
App A @ Site 1
  -> internal DNS
  -> B service VIP / health-aware service endpoint
       |
       +-- App B @ Site 1 preferred
       |
       +-- App B @ Site 2 fallback
  -> App B
  -> App C

App D @ Site 1
  -> same B service
~~~

A failure of App B @ Site 1 should ideally remain a **B recovery event**, not turn into A + C + D site failover.

The preferred pattern is a stable internal service abstraction with:

- local preferred dependency;
- remote fallback where safe;
- bounded timeout/retry;
- state/data compatibility;
- downstream dependency validation;
- capacity for fallback traffic.

# 8. App A/B/C/D cascade relationship

Without dependency-local recovery:

~~~text
                    App B @ Site 1 fails
                            |
                +-----------+-----------+
                |           |           |
             App A       App C       App D
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

With a local-preferred / remote-fallback B service:

~~~text
App A / App C / App D @ Site 1
              |
         B service VIP
          /          \
App B @ Site 1    App B @ Site 2
    preferred        fallback

local B failure -> withdraw local B -> retry remote B
                -> A/C/D remain in Site 1
~~~

This is why cross-site **dependency reachability** should be an early platform capability even though it should not be required during healthy normal operation.

# 9. Two-site relationship

Both sites should remain separate failure domains.

~~~mermaid
flowchart LR

  subgraph SITE1[Site 1]
    LTM1[LTM HA]
    WAFA[WAF platform]
    CFW1[CFW]
    ELB1[ELB]
    APPS1[Apps A/B/C/D]
    LTM1 --> WAFA --> CFW1 --> ELB1 --> APPS1
  end

  subgraph SITE2[Site 2]
    LTM2[LTM HA]
    WAFB[WAF platform]
    CFW2[CFW]
    ELB2[ELB]
    APPS2[Apps / DR instances]
    LTM2 --> WAFB --> CFW2 --> ELB2 --> APPS2
  end

  GTM2[GTM / DNS] --> LTM1
  GTM2 --> LTM2

  LTM1 -. X2A remote WAF contingency .-> WAFB
  LTM2 -. X2B route-back when Site 1 app healthy .-> CFW1
  APPS1 -. XD1 dependency fallback .-> APPS2
~~~

Cross-site capability is a **recovery mechanism**, not a steady-state dependency.

Healthy Site 1 services should remain healthy if the inter-site route is lost.

# 10. Target-state security-zone view

If applications converge onto common private on-premise clouds, the preferred sharing boundary should be reviewed.

A likely target is to separate runtime failure domains by **security/trust zone or cloud platform**, rather than automatically preserving every historic tenant stack.

Illustrative target:

~~~text
                       Enterprise DNS / GTM
                      /                    \
            external namespace          internal namespace
                    |                         |
          Internet / external            Internal / partner
              consumers                    consumers
                    |                         |
        ====================        =========================
          INTERNET STACK             INTRANET/EXTRANET STACK
        ====================        =========================
          edge firewall                firewall/security edge
                |                              |
             LTM HA                         LTM HA
                |                              |
        independent active              independent active
           WAF pool                        WAF pool
                |                              |
       app-specific policies            app-specific policies
                |                              |
          Internet CFW                  Internal/Extranet CFW
                |                              |
          cloud ELB/apps                  cloud ELB/apps
~~~

This is a **target-state option**, not yet a fixed invariant.

Important design principle:

> Do not merge Internet and Intranet/Extranet WAF runtime failure domains merely to reduce appliance count.

The stacks may share:

- management tooling;
- policy standards;
- automation;
- observability;
- engineering processes.

They should remain separately capacity-isolated where an Internet attack, emergency policy change or runtime failure must not consume or disable internal application delivery.

# 11. Implications for W1/W2/W3/S1/S2

The W1-W4 labels describe per-site WAF topology patterns. S1/S2 describe sharing/tenancy patterns. Their canonical meanings are defined in [architecture_shorthand_topology_reference.md](./architecture_shorthand_topology_reference.md).

The target-state cloud model may change **where those patterns are applied**.

For example:

- W1 may become an independent active WAF pool per security zone;
- S1 may mean several application/LTM domains share the WAF pool within one zone;
- W3 becomes less attractive if historical tenants no longer need dedicated preferred WAF capacity;
- S2 should be treated cautiously because sharing both LTM and WAF can create a large common failure/change domain.

Do not preserve historical tenant-specific appliances unless they still provide a useful boundary such as:

- security/trust separation;
- regulatory isolation;
- criticality;
- ownership/change cadence;
- capacity;
- unacceptable common-mode blast radius.

# 12. Architecture review questions

Before final target-state approval, answer:

1. What are the real security/trust zones: Internet, Extranet, Intranet, or additional regulatory zones?
2. Which applications live in each private cloud?
3. Which applications require WAF on north-south traffic?
4. Which internal east-west flows genuinely require WAF rather than API/mTLS/CFW/application controls?
5. What is the desired LTM failure-domain size: per tenant, per criticality group, or per cloud/security zone?
6. What is the maximum acceptable WAF runtime blast radius?
7. Can WAF policy be independently versioned, canaried and rolled back per application?
8. Can Site 1 applications safely reach Site 2 dependencies without making the inter-site path a normal dependency?
9. Are Internet and Intranet/Extranet capacity and change domains isolated?
10. Does Site 2 have sufficient capacity for the aggregate failure domain created by sharing?

# 13. Source-of-truth relationship

Use this document for the **high-level entity/relationship and traffic-path picture**.

Use [architecture_shorthand_topology_reference.md](./architecture_shorthand_topology_reference.md) for **canonical W/S/X/T/AT identifiers and timing semantics**.

Then use:

- [enterprise_scenario_invariants.md](./enterprise_scenario_invariants.md) for stable environment facts;
- [analysis_variables_and_f5_assumptions.md](./analysis_variables_and_f5_assumptions.md) for topology/timing choices;
- [executive_recommendation.md](./executive_recommendation.md) for the decision recommendation;
- [deployment_options_resilience_summary.md](./deployment_options_resilience_summary.md) for option comparison;
- [end_to_end_service_impact_analysis.md](./end_to_end_service_impact_analysis.md) for failure/user impact;
- [cross_site_routing_and_dependency_recovery.md](./cross_site_routing_and_dependency_recovery.md) for X2A/X2B/X2C/XD1 detail.
