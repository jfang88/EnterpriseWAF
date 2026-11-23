# Enterprise Scenario Invariants

**Status:** Stable baseline for EnterpriseWAF scenario analysis  
**Change policy:** Change this file only when the real enterprise environment or supported application requirements change. Do not change it merely to make one topology look better.

## 1. Purpose

This file defines the enterprise facts that should remain stable while WAF topology, GTM health-check strategy, cross-site routing and failover mechanisms are compared.

All scenario analysis should reference this file rather than restating or silently changing the environment.

## 2. Enterprise scope

The wider organisation may operate approximately **3 or 4 tenants / hosting environments**.

A **tenant** means a network, infrastructure and security context used to host and protect a suite of related enterprise applications. It is not an external customer.

A tenant may have dedicated or logically isolated instances/contexts of:

- edge firewall HA pairs and firewall-owned VIPs;
- BIG-IP DNS / GTM;
- BIG-IP LTM;
- BIG-IP Advanced WAF / ASM;
- routing and leased-line termination;
- application ELB/service endpoints;
- private-cloud/platform firewall contexts (**CFW**), positioned in front of private-cloud ELB/service endpoints;
- application and dependency services.

Some components may be shared across multiple tenants. When a component is shared, the scenario analysis must explicitly state the cross-tenant blast radius.

### Default modelling rule

For readability, worked examples and failure matrices should use **one representative tenant** unless shared infrastructure materially changes the result.

The representative-tenant model can then be replicated for Tenant 2, Tenant 3 and Tenant 4.

## 3. Sites

There are two enterprise sites:

- **Site 1**
- **Site 2**

The two sites are separate infrastructure and routing failure domains.

For a given tenant, assume the **same logical F5 GTM/LTM role exists in both sites** unless a scenario explicitly says otherwise. In other words:

- BIG-IP DNS / GTM capability is available in both sites;
- BIG-IP LTM, where used for the selected topology, has the same logical role in both sites;
- the default BIG-IP LTM deployment is **two LTMs per site in an HA/Sync-Failover pair**; a 3-device LTM group is an optional design study, not the baseline;
- edge-firewall/VIP concepts are equivalent in both sites;
- W1-W3 normally use the same logical WAF topology in Site 1 and Site 2;
- W4 is the intentional exception: Site 1 may have a WAF HA cluster plus an additional independently active/spare WAF, while Site 2 has only the WAF HA cluster;
- application-side infrastructure may still differ in active/passive readiness, capacity, IP addressing or startup state.

Site-level GTM recovery is part of every topology and is not a separate WAF topology.

Most applications are active/passive. Some passive-site applications may require manual startup.

Some applications may be active/active.

Application readiness, data/state readiness and network reachability are separate from infrastructure device health.

## 4. External-user private-network ingress

For the representative tenant, per site:

- there are **4 incoming private leased-line / route paths** used primarily by external users;
- the external user population is deliberately distributed across the leased-line paths;
- loss of one line should therefore affect a subset of external users rather than automatically affecting the whole population;
- the real affected percentage must be calculated from the actual population/routing allocation rather than assumed to be exactly 25%;
- there are **2 HA edge-firewall pairs** per tenant per site;
- leased-line routes are distributed across the firewall/routing paths;
- externally reachable application VIPs live on the edge firewall tier.

A leased-line failure is first an **external-user reachability failure**, not automatically an application failure.

The same affected user population may lose access to several applications hosted in the same tenant even while the applications themselves remain healthy.

## 5. DNS / GTM access patterns and namespace separation

The enterprise has **separate external and internal DNS namespaces / resolution paths**. They must be analysed independently.

### External namespace

External users/systems may resolve externally published services using either of these supported patterns:

1. external/customer resolvers query enterprise BIG-IP DNS / GTM directly; or
2. external/customer corporate DNS forwards or delegates the relevant external zones to enterprise BIG-IP DNS / GTM.

Representative flow:

```text
External user/system
  -> external/customer DNS resolver
  -> enterprise GTM / BIG-IP DNS for published external endpoint
  -> returned external/firewall application VIP
```

### Internal namespace

Internal users/systems normally use **internal enterprise DNS**, not the external namespace.

For selected internal service names, internal DNS may delegate or conditionally forward to BIG-IP DNS / GTM, which returns the appropriate internal application/service endpoint.

Representative flow:

```text
Internal user/system
  -> internal enterprise DNS
  -> delegation / conditional forward for selected internal service name
  -> BIG-IP DNS / GTM
  -> internal LTM / ELB / service VIP
  -> application
```

Applications may use the same internal resolution pattern for application-to-application calls.

Representative dependency flow:

```text
Application A
  -> internal DNS
  -> GTM / BIG-IP DNS for internal service name
  -> B service VIP / internal endpoint
  -> Application B
  -> optional further internal DNS/GTM resolution
  -> Application C
```

It is **not an invariant** that every internal endpoint must use GTM. Some internal names may resolve directly in enterprise DNS, while selected internal endpoints may be delegated/forwarded to GTM.

There may be two GTM/DNS instances or listeners per site for a tenant, or GTM may be shared. The exact tenancy model must be declared when cross-tenant blast radius matters.

DNS/GTM is a **control/resolution plane**. It is not an inline HTTP application hop.

A DNS answer is useful only when the requesting actor can actually reach the returned VIP/endpoint.

External namespace availability and internal namespace availability must be reported separately.

## 6. External application path

The canonical external application path is:

```text
External user/system
  -> private leased line / VPN
  -> edge firewall / firewall-owned application VIP
  -> BIG-IP LTM where present
  -> BIG-IP WAF where applicable
  -> platform/cloud firewall (CFW) where the application is private-cloud hosted
  -> application ELB/service
  -> on-premises or private-cloud application workload
```

The WAF topology is intentionally **not** fixed in this file.

## 7. Internal-user path

Internal users may use a different path and may bypass the WAF layer.

Typical internal path:

```text
Internal user
  -> internal enterprise DNS
  -> [optional delegation/conditional forward to GTM for selected internal endpoint]
  -> internal LTM/service VIP
  -> platform/cloud firewall (CFW) where the application is private-cloud hosted
  -> ELB/service endpoint
  -> application
```

Typical internal application dependency path:

```text
App A
  -> internal enterprise DNS
  -> [optional GTM lookup for B internal service]
  -> B service VIP / endpoint
  -> platform/cloud firewall (CFW) where B is private-cloud hosted
  -> B ELB/service endpoint
  -> App B
```

A WAF outage therefore does not automatically mean the application is unavailable to internal users.

External and internal availability must be reported separately.

### Mandatory service-outcome reporting

Every failure scenario must report the outcome separately for:

- **external human users**;
- **external systems/API clients**;
- **internal users/systems**;
- **dependent applications**, including App A -> App B -> App C chains where relevant.

Do not stop the analysis at "component failed" or "component recovered."

For each actor, state:

- whether service is unaffected, degraded, partially unavailable or fully unavailable;
- expected user-visible interruption/recovery time;
- whether recovery is automatic or manual;
- whether local-only recovery is sufficient;
- whether cross-site capability changes the result;
- whether the application must retry, reconnect, re-authenticate, restore state or replay transactions/messages;
- whether the business service is actually recovered after the infrastructure is healthy.

## 8. Application hosting patterns

Applications may be hosted in one or more of these patterns.

### H1 — on-premises application

```text
WAF/LTM
  -> on-premises application LB/VIP
  -> servers/VMs
```

### H2 — private-cloud VM application

```text
WAF/LTM
  -> platform/cloud firewall (CFW)
  -> ELB
  -> VM pool
```

### H3 — private-cloud Kubernetes application

```text
WAF/LTM
  -> platform/cloud firewall (CFW)
  -> ELB
  -> Kubernetes ingress/service
  -> pods
```

### H4 — PaaS service behind stable/floating ELB endpoint

```text
WAF/LTM
  -> platform/cloud firewall (CFW)
  -> stable/floating PaaS ELB address
  -> Site 1 or Site 2 workload
```

For ordinary VM/Kubernetes environments, Site 1 and Site 2 may have distinct IPs/ELBs.

For some PaaS services, the upstream ELB/service address can remain stable while the workload moves between data centres.

The CFW and ELB are separate failure domains. A CFW failure can make an otherwise healthy ELB/application unreachable to both external and internal callers that traverse that platform firewall. Analyse CFW HA/member failure, full CFW context/service failure, routing/NAT state and cross-site reachability separately from ELB/application failure.

## 9. Application-to-application dependencies

Applications may be interconnected in one-hop or multi-hop chains.

Examples:

```text
Application A
   -> Application B

Application A
   -> Application B
      -> Application C

Application D
   -> Application B
```

The dependency may use:

- a site-local/static endpoint;
- internal enterprise DNS, with optional delegation/conditional forwarding to GTM for selected internal service names;
- a stable internal service VIP;
- a local-preferred VIP with a remote lower-priority member.

Failure of Application B must not automatically imply that Application A should fail site if a safe and supported B recovery path exists.

Likewise, a remote B2 is only a valid recovery target if its own required dependencies such as C are available and compatible.

Dependency health, dependency routing and cascading failure across App A / App B / App C are first-class failure-analysis dimensions.

## 10. Application types that must be supported

The WAF/infrastructure design must be assessed against all applicable application classes.

### A1 — stateless web applications

Characteristics:

- HTTP/HTTPS request-response traffic;
- next request can normally use any healthy backend instance;
- required state is absent or external/shared;
- retry through a new WAF/LTM/ELB member is usually acceptable.

A system is not truly stateless if important login/cart/workflow state exists only in one local process.

### A2 — stateful web applications

Characteristics:

- HTTP/HTTPS;
- session/workflow/transaction context may require affinity or shared state;
- state may reside in local memory, cache, shared session service or database;
- infrastructure failover is not sufficient unless required state is available after the move.

### A3 — socket / WebSocket / long-lived connection applications

Characteristics:

- persistent TCP/TLS/WebSocket connections;
- failure of a proxy/backend normally breaks the existing connection;
- DNS changes do not migrate an established socket;
- application reconnect and state restoration are required for robust recovery.

### A4 — non-web applications that bypass WAF

Examples include:

- raw TCP services;
- SFTP/MFT;
- middleware/message protocols;
- database connectivity;
- proprietary L4 services;
- internal system-to-system protocols.

These may use firewall, LTM, ELB or direct service routing without traversing WAF.

## 11. F5 technology assumption

Assume the core traffic-management/security hardware is F5:

- BIG-IP DNS / GTM;
- BIG-IP LTM;
- BIG-IP Advanced WAF / ASM.

Exact software version, appliance model, licensing and platform compatibility must be validated before implementation because some HA/mirroring capabilities are version/platform dependent.

## 12. What is deliberately NOT invariant

The following belong in the analysis-variable document, not here:

- WAF topology;
- clustered versus independent WAF nodes;
- number of WAF nodes;
- optional 3-device LTM DSC comparison beyond the default 2-LTM-per-site baseline;
- shared reserve WAF design;
- local-only versus cross-site WAF routing;
- GTM IP/port versus full-application health checking;
- local-only versus distributed/cross-site GTM probing;
- DNS load-balancing method;
- monitor intervals/timeouts;
- application-specific persistence;
- connection mirroring;
- recovery-time targets.

## 13. Stable design objectives

Use these objectives for all options:

1. Recover the **smallest failed component/service** possible.
2. Avoid turning one WAF failure into application/site failover.
3. Avoid turning one application dependency failure into a multi-application/site failover.
4. Keep healthy local services working when cross-site connectivity fails.
5. Keep tenant failures inside that tenant unless a documented shared dependency exists.
6. Distinguish external-user reachability, internal-user reachability and actual application health.
7. Do not advertise a passive-site application until the application and its required state/dependencies are ready.
8. Treat DNS convergence, connection recovery and application-state recovery as separate steps.
9. For long-lived connections, assume application reconnect/recovery is required even when infrastructure HA is present.
10. Full-site failover should be the final recovery domain, not the default response to a component fault.
11. The primary resilience measure is **time from fault to successful business transaction for each affected actor**, not time for an individual F5 component to return to green.
12. A failure analysis is incomplete unless it states external-human, external-system/API, internal-user and dependent-application impact where applicable.
13. Prefer dependency-local recovery (for example B1 -> B2) over moving healthy dependent applications (A/C/D) when the dependency and state model safely allow it.
14. Treat external namespace and internal namespace as separate control-plane dependencies; failure of one must not automatically be reported as failure of the other.
15. For App A/B/C dependencies, include internal DNS/GTM resolution behavior in the recovery path where the application resolves dependency endpoints dynamically.
16. Treat the platform/cloud firewall (CFW) in front of private-cloud ELB/service endpoints as a separate failure and maintenance domain from the ELB/application itself.


## 14. Maintainability and availability analysis objectives

Maintainability is a **second mandatory analysis lens** after failure/recovery analysis.

The architecture must be assessed not only for whether it survives unplanned failure, but also for whether normal operational changes can be performed without consuming all redundancy or creating an avoidable outage.

For every topology, evaluate:

- monitoring and operational visibility;
- firmware/software upgrades;
- WAF policy/signature changes;
- LTM/GTM configuration and iRule/policy changes;
- certificate/key changes where relevant;
- node draining and connection handling;
- staged, rolling, canary or blue-green change patterns;
- configuration synchronization and change-control tooling;
- rollback/recovery from a bad change;
- how many independent maintenance operations can occur before resilience is materially reduced;
- whether Site 1 and Site 2 can be changed on different schedules;
- whether application teams must coordinate draining, reconnect or readiness changes;
- whether planned maintenance can remain inside the required availability target.

### Availability target to test

Use **99.95% availability** as an explicit design target to evaluate at:

1. individual component/service tier;
2. tenant application-delivery path;
3. end-to-end application service.

Do not assume that every component being 99.95% available produces 99.95% end-to-end availability.

If planned maintenance counts against the SLO, 99.95% corresponds to approximately:

- **4 hours 22 minutes 48 seconds per year**;
- **21 minutes 54 seconds per average month**;
- **5 minutes 2 seconds per week**.

A simple series of five independent 99.95% components would be only about **99.75%** available before allowing for redundancy, common-mode failure or recovery behavior. Therefore the analysis must use the actual redundant topology rather than multiply vendor component claims or assume component SLO equals service SLO.

### Change-safety objective

A maintainable design should, where technically possible:

1. remove/drain one device or capacity unit;
2. retain enough capacity to meet service demand;
3. apply and validate the change;
4. return the changed unit to service;
5. observe it before proceeding;
6. stagger the next device/site/change wave;
7. preserve a known-good rollback path.

The analysis should explicitly identify topologies where maintenance temporarily removes the same redundancy needed to survive an unplanned failure.

### Application maintainability

Application behavior is part of planned-change resilience.

Where applications use long-lived connections, stateful sessions, persistent backend connections or App A -> App B dependencies, planned draining must account for:

- connection drain/graceful close;
- retry and reconnect behavior;
- re-authentication;
- session/state portability;
- DNS/service re-resolution;
- idempotency;
- transaction completion;
- dependency failover.

Applications that cannot tolerate planned member withdrawal should be marked as a maintainability constraint even if the F5 infrastructure itself is highly available.
