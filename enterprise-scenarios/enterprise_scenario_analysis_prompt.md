# Enterprise WAF Scenario Analysis Prompt

## Purpose

Use this document as the **canonical scenario-analysis prompt** for the EnterpriseWAF repository.

The goal is to keep the underlying enterprise environment stable, change only a small number of architecture decisions, and then apply the **same failure scenarios** to each option.

The main comparison should normally include:

1. **No cross-site contingency routing**
2. **Controlled cross-site contingency routing**

Other architecture choices, such as clustered versus LTM-balanced WAFs, DNS access model, and active/passive versus active/active applications, should be treated as explicit variables rather than silently changing the base topology.

---

# 1. Analysis rules

When analysing an option:

- Do not change the invariants unless the scenario explicitly says to.
- Separate **DNS/control-plane resolution** from **application data-plane traffic**.
- Distinguish:
  - external users;
  - internal users;
  - external systems/API clients;
  - internal system-to-system flows such as Application A -> Application B.
- Distinguish:
  - component failure;
  - tier failure;
  - application failure;
  - dependency failure;
  - cross-site network failure;
  - full-site failure.
- Prefer the smallest possible recovery domain.
- Do not assume that failure of one application or one dependency means the whole site is unhealthy.
- Do not assume DNS/GTM can create network reachability.
- Do not assume an established TCP/WebSocket connection moves because DNS changes.
- For active/passive applications, do not advertise the passive site until the application is actually started and ready.
- Treat cross-site routing as a **contingency capability**, not a normal dependency, unless explicitly stated otherwise.

---

# 2. Canonical enterprise invariants

These assumptions remain fixed across the architecture options unless explicitly overridden.

## 2.1 Sites

There are two enterprise sites:

- **Site 1**
- **Site 2**

Most applications are active/passive, with some requiring manual startup at the passive site.

Some applications are active/active.

The two sites are separate infrastructure and routing failure domains.

---

## 2.2 Hosting-environment ingress

In this document, a **tenant means an internal hosting environment for a suite of enterprise systems/applications**. It does **not** mean an external customer or user organisation.

A hosting environment may contain multiple systems such as Application A, Application B and other related services. Those systems may share parts of the ingress, LTM, WAF, application-delivery and private-cloud infrastructure, so failures of shared components must be analysed for their multi-application blast radius.

For each hosting environment, **per site**:

- there are **4 incoming private leased lines / routes** used primarily by external users to reach applications in that hosting environment;
- the leased lines terminate into the enterprise ingress environment;
- there are **2 HA firewall pairs per hosting environment per site**;
- the 4 lines/routes are distributed across the two HA firewall pairs and associated primary/secondary routing paths;
- the external customer/user population is deliberately distributed across the four leased-line paths so that loss of a single line or route should affect only the users assigned/routed through that path, rather than the full external population;
- the exact percentage of users affected by a line failure depends on the real population/routing allocation and must be measured rather than assumed to be exactly 25%;
- primary and secondary routes/firewalls should be treated as separate ingress paths only where the physical carrier, termination, route and firewall design provides genuine independence.

This same ingress pattern is replicated in the other site.

Conceptually:

```text
External customer/user population
        |
        +---- user population / route group 1 ---- Line 1 ----+
        +---- user population / route group 2 ---- Line 2 ----+--> Firewall HA Pair A
        |                                                       |
        +---- user population / route group 3 ---- Line 3 ----+--> Firewall HA Pair B
        +---- user population / route group 4 ---- Line 4 ----+
                                                                |
                                                     Firewall-owned application VIP(s)
                                                                |
                                                    suite of hosted applications
```

The four leased lines are therefore **access failure domains for subsets of external users**, while the hosting environment is the shared platform containing multiple applications.

Do not assume the four lines are truly independent unless carrier, physical route, termination, routing and firewall failure domains are confirmed. Also do not assume that losing one line affects only one application: the affected external-user subset may lose access to multiple applications hosted in the same environment.

---

## 2.3 External application VIP ownership

The externally reachable application VIPs **live on the firewall tier**.

Therefore the external application data path begins:

```text
External client
    |
leased line / VPN
    |
Firewall-owned application VIP
    |
enterprise application delivery tiers
```

The firewall tier may provide:

- ingress routing;
- NAT;
- stateful inspection;
- VIP exposure;
- HA between firewall members;
- route selection between leased-line paths.

---

# 3. DNS / GTM control plane

DNS/GTM is a **resolution/control plane**, not an inline application-data hop.

There may be **two GTM/DNS instances or listeners per site**:

```text
Site 1                    Site 2

GTM-1A                    GTM-2A
GTM-1B                    GTM-2B
```

These GTM/DNS services may all be authoritative for the relevant application zones, depending on the selected DNS design.

GTM should return a healthy, client-reachable application VIP.

## 3.1 DNS option D1 - external client / customer DNS queries GTM directly

```text
External client / customer resolver
          |
          | DNS query
          v
Enterprise GTM/DNS
          |
          v
Healthy Site 1 or Site 2 firewall VIP
```

## 3.2 DNS option D2 - corporate / customer DNS queries enterprise GTM

```text
External client
      |
Customer / corporate recursive DNS
      |
delegation or conditional forwarding
      |
Enterprise GTM/DNS
      |
Healthy Site 1 or Site 2 firewall VIP
```

## 3.3 DNS requirements

Analyse:

- whether the client can reach GTM in both sites;
- whether the client can reach every application VIP that GTM might return;
- resolver caching;
- GTM TTL;
- application DNS caching;
- DNS retry behaviour;
- GTM health propagation/convergence;
- application-specific health rather than a single site-wide state.

For active/passive systems, a passive-site endpoint is eligible only when:

```text
network path healthy
AND firewall/VIP healthy
AND relevant LTM/WAF/application path healthy
AND application started
AND application ready
```

---

# 4. Application data-plane actors

Analyse at least these actors separately.

## A1 - External user

External users belong to customer/user populations that are distributed across the four leased-line access paths. A failure may therefore affect only one subset of external users while the application itself remains healthy and reachable by other external populations and by internal users.

Typical path:

```text
External user
  -> leased line / VPN
  -> firewall-owned VIP
  -> LTM
  -> WAF
  -> application path
```

## A2 - External system / API client

Same basic ingress as external users, but may use:

- persistent TLS;
- APIs;
- long-lived HTTP;
- WebSockets;
- automated retry behaviour.

## A3 - Internal user

Internal users may bypass the external WAF path and connect directly to an internal service or ELB endpoint.

Typical path:

```text
Internal user
  -> internal DNS / service resolution
  -> internal ELB / service VIP
  -> application
```

Depending on application placement, this may include the private-cloud firewall.

Internal availability must therefore be analysed separately from external WAF availability.

## A4 - Internal Application A

Application A may need to call Application B.

## A5 - Internal Application B

Application B may itself depend on A or other services.

System-to-system dependencies are first-class availability paths, not secondary edge cases.

---

# 5. Enterprise LTM -> WAF -> application layer

The main architecture discussion begins behind the firewall-owned VIP.

Base logical path:

```text
Firewall-owned VIP
      |
      v
Enterprise LTM
      |
      v
WAF tier
      |
      v
Application destination
```

The exact WAF behaviour is an architecture option.

---

# 6. Application hosting patterns

## H1 - Traditional on-premises application

```text
WAF
 |
On-premises application ELB / LB / VIP
 |
VMs / servers / application cluster
```

## H2 - Private-cloud VM application

```text
WAF
 |
Private-cloud edge firewall
 |
Private-cloud ELB
 |
VM pool
```

Site 1 and Site 2 normally have distinct ELB and backend addresses.

## H3 - Private-cloud Kubernetes application

```text
WAF
 |
Private-cloud edge firewall
 |
Private-cloud ELB
 |
Kubernetes ingress / Service
 |
Pods
```

Site 1 and Site 2 are separate Kubernetes/application failure domains unless a platform-specific design says otherwise.

## H4 - PaaS service behind a stable/floating ELB address

```text
WAF
 |
Private-cloud edge firewall
 |
Fixed / logical PaaS ELB address
 |
PaaS platform
 |
Site 1 or Site 2 workload
```

The PaaS platform may move the backend while keeping the service address stable.

Do not treat this the same as site-specific VM/Kubernetes ELBs.

---

# 7. Internal Application A -> Application B patterns

The analysis must include interconnected applications.

## AB1 - hard-coded / site-local dependency

```text
A1 -> B1
```

If B1 fails, A1 has no remote alternative.

This may force A itself to fail over.

## AB2 - DNS/GTM-based service discovery

```text
A1
 |
DNS lookup
 |
GTM / internal DNS
 |
+--> B1
+--> B2
```

Analyse:

- DNS caching;
- application re-resolution;
- persistent connections;
- retry;
- site health;
- whether B2 is actually reachable from A1.

## AB3 - stable local service VIP with remote fallback

```text
A1
 |
B-Service VIP
 |
+---- B1 local / preferred
|
+==== B2 remote / contingency
```

This model allows B to move without necessarily moving A.

Use this pattern when analysing cascading-failure reduction.

---

# 8. Architecture decision variables

Change these deliberately and record the selected value before analysis.

## Decision W - WAF model

### W1 - clustered WAF

```text
Firewall VIP
   |
LTM
   |
WAF HA cluster
   |
application
```

### W2 - LTM-balanced active WAF nodes

```text
Firewall VIP
   |
LTM
   |
+---- WAF1
+---- WAF2
   |
application
```

WAF policies/configuration must remain synchronised even if the dataplane nodes are independently active.

---

## Decision X - cross-site contingency

### X1 - no cross-site routing

No supported contingency path exists from Site 1 LTM/WAF/application dependency to Site 2 equivalents.

Examples:

```text
Site1 LTM -> Site1 WAF only

A1 -> B1 only
```

### X2 - controlled cross-site contingency routing

Normal traffic remains local, but approved remote resources may be used when required.

Examples:

```text
Site1 LTM
  |
  +---- Site1 WAF1 / WAF2 preferred
  |
  +==== Site2 WAF pool contingency
```

and:

```text
A1
 |
B-Service VIP
 |
+---- B1 preferred
|
+==== B2 contingency
```

Cross-site rules must be:

- explicit;
- least privilege;
- health checked;
- capacity tested;
- symmetric through stateful devices;
- removable without breaking healthy local paths.

Loss of the cross-site network should remove contingency capacity but should not mark healthy local applications down.

---

## Decision D - DNS access model

- **D1:** customer/client resolver queries GTM directly.
- **D2:** customer/corporate DNS forwards/delegates to enterprise GTM.

This decision is orthogonal to the WAF/cross-site model.

---

## Decision A - application site mode

- **A1:** active/passive with manual passive-site startup.
- **A2:** active/passive with automated readiness/failover.
- **A3:** active/active.

Choose independently per application.

---

# 9. Recommended baseline options for comparison

Use these three as the default architecture comparison.

## Option 1 - Clustered WAF + local-only routing

- WAF = W1
- Cross-site = X1
- DNS = D1 or D2, held constant during comparison
- Applications may be active/passive or active/active as specified

## Option 2 - LTM-balanced WAF + local-only routing

- WAF = W2
- Cross-site = X1
- DNS held constant

## Option 3 - LTM-balanced WAF + controlled cross-site contingency

- WAF = W2
- Cross-site = X2
- DNS held constant

Do not change the DNS or application mode between options unless that is the explicit purpose of the comparison.

---

# 10. Canonical traffic-path catalogue

Use these IDs when building scenarios.

| Path ID | Actor | Resolution | Typical data path |
|---|---|---|---|
| P1 | External user | Direct GTM | leased line -> firewall VIP -> LTM -> WAF -> on-prem app |
| P2 | External user | Corporate DNS -> GTM | leased line -> firewall VIP -> LTM -> WAF -> on-prem app |
| P3 | External user | Either DNS model | firewall -> LTM -> WAF -> cloud FW -> ELB -> VM |
| P4 | External user | Either DNS model | firewall -> LTM -> WAF -> cloud FW -> ELB -> Kubernetes |
| P5 | External user | Either DNS model | firewall -> LTM -> WAF -> cloud FW -> fixed PaaS ELB |
| P6 | Internal user | Internal DNS / GTM | internal network -> on-prem ELB/service -> app |
| P7 | Internal user | Internal DNS / GTM | internal network -> cloud FW -> ELB -> VM/K8s |
| P8 | Internal user | Internal DNS | fixed PaaS ELB -> active PaaS backend |
| P9 | App A | local/static | A1 -> B1 |
| P10 | App A | local service VIP | A1 -> B-Service VIP -> B1 |
| P11 | App A | local VIP + remote fallback | A1 -> B-Service VIP -> B1/B2 |
| P12 | App A | DNS/GTM | A1 -> DNS -> B1/B2 |
| P13 | Active-active external app | GTM | clients distributed between Site 1 and Site 2 |

---

# 11. Canonical failure catalogue

Apply the same failures to every selected architecture option.

## F1 - client / DNS failures

- client cannot reach a DNS resolver;
- corporate DNS unavailable;
- direct GTM endpoint unavailable;
- one GTM unavailable;
- both GTMs in one site unavailable;
- GTMs disagree on application health;
- stale DNS cache;
- GTM advertises an endpoint the client cannot route to.

## F2 - leased-line / route failures

- one leased line fails;
- one customer/user population assigned to that line loses access while other leased-line populations continue;
- two leased lines sharing a route/provider fail;
- one primary route fails;
- route to one firewall pair fails;
- a shared carrier/physical path defeats the assumed independence of multiple logical leased lines;
- all ingress connectivity to one site fails.

For each failure, identify:
- which external-user population(s) are affected;
- which applications in the hosting environment those users can no longer reach;
- whether unaffected external populations can still use the same applications;
- whether internal users remain unaffected;
- whether traffic can use another leased line automatically or requires customer/network reconfiguration.

Quantify the percentage of the external customer/user population affected from the actual routing/population distribution rather than assuming an equal 25% split.

## F3 - firewall failures

- one firewall node fails;
- firewall HA failover;
- entire firewall pair fails;
- firewall VIP unavailable;
- NAT/state issue;
- asymmetric path through different firewall pairs.

## F4 - LTM failures

- one LTM node fails;
- whole LTM HA pair fails;
- VIP fails;
- health monitor incorrectly removes a healthy WAF;
- health monitor leaves a failed WAF active.

## F5 - WAF failures

- one WAF fails;
- WAF policy process fails;
- WAF overloaded;
- one WAF has bad configuration;
- all local WAFs fail;
- WAF is alive but cannot reach application;
- remote WAF exists but cross-site route is unavailable.

## F6 - cloud firewall failures

- one node fails;
- cloud firewall pair/service fails;
- policy blocks WAF -> ELB traffic;
- asymmetric return path.

## F7 - ELB failures

- ELB node/service fails;
- ELB VIP unavailable;
- target/member fails;
- incorrect target health;
- site-specific ELB unavailable.

## F8 - VM/Kubernetes failures

- application process;
- VM;
- hypervisor;
- Kubernetes pod;
- Kubernetes node;
- ingress;
- Service;
- entire site/cluster.

## F9 - PaaS floating-service failures

- Site 1 backend fails;
- service moves to Site 2 behind same ELB address;
- stable ELB exists but both backends unhealthy;
- platform failover is slower than upstream monitors expect.

## F10 - application failures

- App A member fails;
- entire App A Site 1 service fails;
- App B member fails;
- entire App B Site 1 service fails;
- application healthy at infrastructure level but not business-ready.

## F11 - dependency failures

- A1 cannot reach B1;
- B1 unavailable but B2 healthy;
- B1 unavailable and cross-site route unavailable;
- A1 currently uses B2 and the cross-site link fails;
- DNS returns B2 but A1 cannot route there;
- B moves but A has stale persistent connection/state.

## F12 - cross-site failures

- inter-site link fails;
- one direction fails;
- cross-site firewall rule fails;
- capacity becomes insufficient;
- return path becomes asymmetric;
- remote WAF/app resource is unhealthy.

## F13 - entire-site failure

- Site 1 power/network failure;
- Site 1 isolated;
- Site 1 application stack unavailable;
- GTM must select Site 2;
- passive Site 2 app is not yet started;
- active-active Site 2 continues with reduced total capacity.

## F14 - long-lived connection failures

For WebSockets/persistent TCP:

- WAF node loss;
- LTM node loss;
- firewall failover;
- ELB/backend loss;
- site change;
- client must reconnect;
- authentication/resubscription/state recovery required.

---

# 12. Required analysis output

For every scenario, produce a table with:

| Field | Required analysis |
|---|---|
| Scenario ID | Failure being tested |
| Actor/path | P1-P13 or other declared path |
| Failed component | Exact component/tier |
| Detection layer | Firewall/LTM/WAF/GTM/ELB/app |
| What remains healthy | Explicitly state unaffected components |
| Option 1 behaviour | Clustered WAF + local-only |
| Option 2 behaviour | LB WAF + local-only |
| Option 3 behaviour | LB WAF + cross-site contingency |
| Convergence | Detection + routing/failover assumptions |
| Existing sessions | survive, reset, retry, reconnect |
| Internal-user impact | if different from external |
| App A -> B impact | if applicable |
| Cascading-failure risk | low/medium/high + explanation |
| Capacity effect | local/remote spare capacity needed |
| Manual action | required/not required |
| Observability | logs/metrics/health checks needed |
| Recommendation | preferred recovery behaviour |

---

# 13. Cascading-failure test

Shared ingress components can also create population-level rather than application-level outages. A leased-line failure should first be analysed as **loss of reachability for a subset of external users**, not as an application failure. If the same hosting environment carries multiple applications, that same user subset may lose access to several applications at once even though all applications remain healthy.

For every application dependency scenario, explicitly ask:

> If this component fails, do we move only the failed component/service, or do we force unrelated applications to fail site?

Example without cross-site dependency recovery:

```text
B1 fails
 |
 +--> A1 loses B
 +--> C1 loses B
 +--> D1 loses B
 |
 +--> A/C/D fail to Site 2
 |
 +--> Site 2 capacity spike
```

Example with cross-site dependency recovery:

```text
B1 fails
 |
B-Service VIP
 |
+==== B2

A1 remains Site 1
C1 remains Site 1
D1 remains Site 1
```

Prefer the smallest recovery domain unless latency, data consistency, security or capacity constraints make it unsafe.

---

# 14. Cross-site routing analysis questions

When comparing X1 versus X2, answer:

1. Which failures can be contained locally in both designs?
2. Which failures force application/site failover when X1 is used?
3. Which of those can instead use a remote WAF, remote ELB or remote dependency under X2?
4. Does X2 introduce asymmetric routing?
5. Does return traffic traverse the same stateful firewall/WAF path?
6. Is SNAT required?
7. Is original client identity preserved safely?
8. Is the cross-site link sized for contingency traffic?
9. What happens if X2 is already being used and the inter-site link then fails?
10. Can X2 itself cause a cascade?
11. Which remote resources should be lower-priority rather than normally active?
12. Does an application dependency have data-consistency constraints that make remote B unsafe?
13. What monitoring proves the full remote path is usable?
14. How quickly can the remote path be withdrawn if unhealthy?

---

# 15. External versus internal availability questions

For every failure, answer separately:

### External
Can the user:

```text
resolve -> route -> reach firewall VIP -> LTM -> WAF -> app?
```

### Internal
Can the internal user:

```text
resolve -> reach internal ELB/service -> app?
```

A WAF outage may therefore produce:

```text
External users = unavailable
Internal users = healthy
```

Do not automatically declare the application itself down.

---

# 16. Recommended design principles

Use these as evaluation criteria:

1. **Local-first normal routing.**
2. **Cross-site routing, if enabled, is contingency rather than a normal dependency.**
3. **One component failure should not cause unrelated applications to change sites.**
4. **One application dependency failure should not trigger full-site failover if a safe remote dependency can be used.**
5. **GTM health is application/service specific.**
6. **GTM advertises only endpoints that are both healthy and client-reachable.**
7. **Internal and external paths are monitored independently.**
8. **WAF health checks should validate usable application paths where feasible.**
9. **Passive-site applications are not advertised before readiness.**
10. **Long-lived applications must reconnect and recover state rather than relying solely on infrastructure connection preservation.**
11. **Cross-site paths require explicit capacity, security, symmetry and failure testing.**
12. **Full-site failover is the final recovery level, not the default response to a component fault.**

---

# 17. Prompt to run an analysis

Copy the section below into an AI session and change only the selected architecture values and scenarios.

---

## Analysis prompt

You are reviewing a dual-site enterprise application-delivery architecture.

Use the invariants, actors, hosting patterns and failure catalogue in this document. Do not silently change the topology.

### Selected architecture

- DNS model: **[D1 direct GTM / D2 corporate DNS -> GTM]**
- WAF model: **[W1 clustered / W2 LTM-balanced active WAFs]**
- Cross-site routing: **[X1 none / X2 controlled contingency]**
- Application A mode: **[manual active/passive / automated active/passive / active-active]**
- Application B mode: **[manual active/passive / automated active/passive / active-active]**
- Application A hosting: **[H1/H2/H3/H4]**
- Application B hosting: **[H1/H2/H3/H4]**
- A -> B dependency model: **[AB1/AB2/AB3]**
- Internal-user path: **[direct ELB / internal VIP / PaaS service / other]**

### Analyse

Analyse the following failure scenarios:

**[insert F1-F14 scenarios or specific failures]**

For each failure:

1. trace the normal end-to-end path before the failure;
2. identify the failed component and the monitoring layer that detects it;
3. identify what remains healthy;
4. describe the recovery path;
5. explain whether DNS/GTM changes;
6. explain whether external users and internal users see different outcomes;
7. explain what happens to App A -> App B;
8. identify any cascading failure;
9. identify whether another application or the whole site must fail over;
10. describe expected convergence drivers rather than inventing precise timings;
11. describe behaviour of existing HTTP, persistent TCP and WebSocket sessions;
12. identify cross-site capacity, symmetry, NAT/firewall and security requirements;
13. identify manual actions;
14. identify monitoring and test evidence required;
15. compare the result with the alternative cross-site routing setting.

Finish with:

- a comparison matrix;
- major failure-domain differences;
- likely cascading-failure scenarios;
- operational complexity;
- capacity requirements;
- key assumptions/TBDs;
- recommended architecture and reasons.

---

# 18. Example focused study - cross-site routing

A useful first analysis is:

### Baseline

- DNS: D2
- WAF: W2
- application mode: active/passive
- A -> B: AB3 where available

### Compare

**Scenario X1:** no cross-site routing

versus

**Scenario X2:** controlled cross-site contingency routing

Run at least:

1. one WAF node fails;
2. all local WAF nodes fail;
3. App B1 fails while A1 remains healthy;
4. local ELB for B fails;
5. cloud firewall path to B1 fails;
6. cross-site route fails while all local services are healthy;
7. cross-site route fails while A1 is already using B2;
8. local WAF tier fails at the same time as cross-site routing;
9. Site 1 is lost entirely;
10. passive Site 2 application is not yet started;
11. internal user can reach B internally while external WAF path is unavailable;
12. GTM returns a healthy VIP that one customer/leased-line population cannot route to.

The analysis should show exactly where X2 prevents a small failure from turning into application or site failover, and where X2 introduces additional routing, capacity or operational risk.
