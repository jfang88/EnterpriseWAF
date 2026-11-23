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
- private-cloud firewall contexts;
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

For a given tenant, assume the **same logical F5 delivery topology exists in both sites** unless a scenario explicitly says otherwise. In other words:

- BIG-IP DNS / GTM capability is available in both sites;
- BIG-IP LTM is deployed with the same logical role in both sites;
- the selected WAF topology for that tenant is replicated in both sites;
- edge-firewall/VIP concepts are equivalent in both sites;
- application-side infrastructure may still differ in active/passive readiness, capacity, IP addressing or startup state.

A topology label such as W1, W2, W3 or W4 therefore describes the **per-site WAF design pattern**, normally present in both Site 1 and Site 2. Site-level recovery is part of every topology and is not a separate WAF topology.

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

## 5. DNS / GTM access patterns

External users may resolve services using either of these supported patterns:

1. external/customer resolvers query enterprise BIG-IP DNS / GTM directly; or
2. external/customer corporate DNS forwards or delegates the relevant zones to enterprise BIG-IP DNS / GTM.

There may be two GTM/DNS instances or listeners per site for a tenant, or GTM may be shared. The exact tenancy model must be declared when cross-tenant blast radius matters.

DNS/GTM is a **control/resolution plane**. It is not an inline HTTP application hop.

A DNS answer is useful only when the client network can actually reach the returned application VIP.

## 6. External application path

The canonical external application path is:

```text
External user/system
  -> private leased line / VPN
  -> edge firewall / firewall-owned application VIP
  -> BIG-IP LTM where present
  -> BIG-IP WAF where applicable
  -> on-premises or private-cloud application delivery
```

The WAF topology is intentionally **not** fixed in this file.

## 7. Internal-user path

Internal users may use a different path and may bypass the WAF layer.

Typical internal path:

```text
Internal user
  -> internal DNS/service resolution
  -> internal LTM/ELB/service VIP
  -> application
```

A WAF outage therefore does not automatically mean the application is unavailable to internal users.

External and internal availability must be reported separately.

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
  -> private-cloud edge firewall
  -> ELB
  -> VM pool
```

### H3 — private-cloud Kubernetes application

```text
WAF/LTM
  -> private-cloud edge firewall
  -> ELB
  -> Kubernetes ingress/service
  -> pods
```

### H4 — PaaS service behind stable/floating ELB endpoint

```text
WAF/LTM
  -> private-cloud edge firewall
  -> stable/floating PaaS ELB address
  -> Site 1 or Site 2 workload
```

For ordinary VM/Kubernetes environments, Site 1 and Site 2 may have distinct IPs/ELBs.

For some PaaS services, the upstream ELB/service address can remain stable while the workload moves between data centres.

## 9. Application-to-application dependencies

Applications may be interconnected.

Example:

```text
Application A
   -> Application B
```

The dependency may use:

- a site-local/static endpoint;
- internal DNS/GTM;
- a stable internal service VIP;
- a local-preferred VIP with a remote lower-priority member.

Failure of Application B must not automatically imply that Application A should fail site if a safe and supported B recovery path exists.

Dependency health and dependency routing are first-class failure-analysis dimensions.

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
