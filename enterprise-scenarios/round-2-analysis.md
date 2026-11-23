# Enterprise Scenario Analysis — Round 2

**Status:** Working analysis on branch `analysis/enterprise-scenarios-round-2`

## Purpose

Use this page for the next round of EnterpriseWAF architecture analysis without changing `main` directly.

The base invariants and reusable scenario prompt remain in:

- [enterprise_scenario_analysis_prompt.md](./enterprise_scenario_analysis_prompt.md)

This round should focus on comparing the same enterprise environment under a small number of explicit design options.

## Primary comparison

### Option 1 — Clustered WAF + local-only routing

- firewall-owned external VIP;
- LTM in front of the WAF tier;
- WAF deployed as an HA cluster;
- normal application traffic remains in the local site;
- no cross-site WAF borrowing;
- no cross-site App A -> App B contingency unless separately declared.

### Option 2 — LTM-balanced active WAFs + local-only routing

- firewall-owned external VIP;
- LTM balances multiple active WAF nodes;
- normal application traffic remains in the local site;
- no cross-site WAF borrowing;
- no cross-site App A -> App B contingency unless separately declared.

### Option 3 — LTM-balanced active WAFs + controlled cross-site contingency

- firewall-owned external VIP;
- LTM balances local active WAF nodes;
- local resources remain preferred;
- remote WAF capacity may be available as lower-priority contingency;
- App A may use a healthy remote App B endpoint where explicitly permitted;
- inter-site routing is a recovery path, not a normal dependency.

## Common actors to analyse

1. External users distributed across the four private leased-line access paths.
2. External systems/API clients using the same private ingress fabric.
3. Internal users that may resolve and connect directly to an ELB/service endpoint without traversing the WAF.
4. Application A calling Application B.
5. Operations/support users where relevant.


## Application types to access / protect

The failure analysis must distinguish application behaviour because infrastructure failover can have very different user impact depending on where application state is kept.

### App Type 1 — Stateless web applications

A stateless web application does not depend on application-session state stored only in the specific web/application instance that handled the previous request.

Typical characteristics:

- HTTP/HTTPS request-response traffic;
- any application instance can normally process the next request;
- user/session state is either absent or stored in a shared/external service;
- requests can normally be retried through another healthy WAF, LTM, ELB or backend instance;
- application-instance failure should not require session affinity to the failed instance;
- horizontal scaling and member replacement are relatively straightforward.

Representative path:

```text
User
 |
Firewall-owned VIP
 |
LTM
 |
WAF pool / WAF service
 |
Application ELB
 |
+---- Web/App instance 1
+---- Web/App instance 2
```

Expected failure behaviour:

- failure of one WAF should cause new requests to use another healthy WAF;
- failure of one application instance should cause the ELB/LB to select another healthy instance;
- an in-flight request may fail and need retry;
- a local WAF-tier failure may use a remote WAF contingency path if that architecture option supports it;
- a site failure may require GTM/DNS to return the alternate site's reachable VIP;
- application recovery should not depend on recovering state from the failed web node.

For each stateless-web failure scenario, capture:

1. whether an in-flight request is lost;
2. whether the client/browser must retry;
3. whether a new connection is required;
4. whether authentication/session state is actually external/shared and therefore portable;
5. whether the next request can use any healthy backend instance;
6. whether DNS/GTM changes are required or a lower layer can recover locally;
7. whether internal users bypassing the WAF see a different outcome.

**Important:** classify an application as stateless only if the required business/session state is genuinely portable. An application that keeps login/session/cart/workflow state only in local process memory should be analysed as stateful even if most HTTP requests appear stateless.


### App Type 2 — Stateful web applications

A stateful web application retains user, workflow, transaction or session context that cannot be assumed to be immediately portable between arbitrary backend instances or sites.

Typical characteristics:

- HTTP/HTTPS traffic;
- session affinity or persistence may be required;
- session/workflow state may live:
  - in local application memory;
  - in a local cache;
  - in a shared cache/session store;
  - in a database;
  - in a site-specific state service;
- failover may require re-authentication, session recreation, workflow recovery or transaction reconciliation;
- cross-site recovery depends on whether state is replicated or otherwise accessible from the alternate site.

Representative path:

```text
User
 |
Firewall-owned VIP
 |
LTM
 |
WAF
 |
Application ELB
 |
+---- App instance 1 ---- local/shared state
+---- App instance 2 ---- local/shared state
```

Failure analysis must explicitly capture:

1. where application/session state is stored;
2. whether LTM/ELB persistence is required;
3. whether state survives backend-member failure;
4. whether state survives WAF/LTM failover;
5. whether state is portable across sites;
6. whether failover causes re-login or workflow restart;
7. whether partially completed transactions need reconciliation;
8. whether cross-site routing is safe before data/state services have failed over;
9. whether internal users and external users see the same state service.

A stateful application can still be highly available, but infrastructure failover alone is not enough unless the state design supports it.

---

### App Type 3 — Socket / WebSocket / long-lived connection applications

This class includes WebSocket and other long-lived TCP/TLS connections that remain attached to a specific network/proxy/backend path for a significant period.

Typical characteristics:

- persistent bidirectional connection;
- connection state exists across firewall, LTM, WAF, ELB and backend;
- abrupt failure of a device or backend normally breaks the established connection;
- moving DNS or a VIP does not migrate an existing socket;
- resilience depends on application reconnect and state-recovery behaviour.

Representative path:

```text
Client
 |
Firewall VIP
 |
LTM
 |
WAF
 |
ELB
 |
Socket/WebSocket backend
```

Failure analysis must capture:

1. whether the existing connection survives or resets;
2. how the client detects loss;
3. reconnect interval, exponential backoff and jitter;
4. whether the client must re-authenticate;
5. whether subscriptions/session context must be recreated;
6. whether sequence numbers, acknowledgements or replay are required;
7. whether missed messages/events can be recovered;
8. whether the backend state is durable outside one process/VM/Pod;
9. whether persistence/affinity is needed while a backend remains healthy;
10. what happens when reconnect lands on a different backend or different site;
11. whether a WAF/LTM/site failover requires a fresh TCP/TLS/WebSocket handshake;
12. whether cross-site routing reduces infrastructure failover but still requires socket reconnect.

For this application type, the design goal is generally:

```text
detect disconnect
 -> reconnect
 -> authenticate
 -> restore subscriptions/session
 -> verify current state
 -> recover/replay missed events
 -> resume normal operation
```

Do not assume clustered infrastructure can preserve every live socket. Connection preservation should be treated as an enhancement; application-level reconnect/recovery remains required.

---

### App Type 4 — Non-web applications that bypass the WAF layer

Some applications do not use HTTP/HTTPS and should not traverse the web-application firewall.

Examples may include:

- raw TCP services;
- message/middleware protocols;
- database connectivity;
- SFTP or managed file-transfer services;
- proprietary application protocols;
- internal service-to-service flows;
- other L4 services.

Representative external or partner path where allowed:

```text
Client / external system
 |
leased line / VPN
 |
Firewall-owned VIP
 |
LTM / L4 load-balancing or direct routed service
 |
Application
```

Representative internal path:

```text
Internal user / system
 |
internal DNS / service resolution
 |
LTM / ELB / service VIP
 |
Application
```

The WAF is intentionally absent.

Failure analysis must capture:

1. which security controls replace WAF inspection;
2. whether the firewall or LTM owns the service VIP;
3. L4 health-check behaviour;
4. persistence/affinity requirements;
5. whether the protocol supports safe retry;
6. how state is recovered after connection failure;
7. whether the service can use a remote-site endpoint;
8. whether GTM/DNS is used for site selection;
9. whether internal and external paths differ;
10. whether cross-site routing is allowed for the protocol;
11. whether return-path symmetry is required through stateful firewall/NAT devices;
12. whether a failure should be contained at the service layer rather than causing broader site failover.

This class must be analysed separately from WAF-protected web traffic. A WAF outage may have **no impact** on these services, while firewall, LTM, routing, ELB or application failures may still affect them.

---

### Application-type summary

| Type | WAF in path? | Connection model | State concern | Typical recovery |
|---|---|---|---|---|
| Stateless web | Yes | Short HTTP/HTTPS requests | Low if state is genuinely external/shared | Retry through healthy path/member |
| Stateful web | Yes | HTTP/HTTPS, often persistent sessions | Medium/High | Preserve/recover session, possibly re-login/reconcile |
| Socket/WebSocket | Usually yes for web sockets | Long-lived TCP/TLS | High connection/session continuity concern | Reconnect, re-authenticate, restore/replay state |
| Non-web | Usually no | Protocol-specific, often L4 | Protocol/application-specific | LTM/routing failover + protocol-specific retry/recovery |

For every failure scenario in this document, state which application type is being analysed because the same infrastructure failure can have very different user-visible outcomes.


### Application-type failure lens

Application type is a mandatory analysis dimension. The infrastructure recovery path may be identical while the application/user recovery is different.

| Failure event | Stateless web | Stateful web | Socket / WebSocket | Non-web bypassing WAF |
|---|---|---|---|---|
| One WAF node fails | Retry/new request through healthy WAF; usually low impact | New requests can move, but persistence/session portability must be checked | Existing sockets on failed path normally reconnect and restore state | Normally no impact because WAF is not in path |
| Entire local WAF tier fails | External web requires alternate WAF/site; internal direct-ELB users may remain healthy | Same infrastructure recovery, plus session/state portability check | All affected sockets reconnect; resubscription/replay may be required | Normally unaffected unless it shares the failed LTM/firewall/route |
| One LTM node fails | HA/LB recovery; in-flight request may retry | Same, but persistence mappings and session affinity must be validated | Connections through failed node may reset and reconnect | L4 service may reset/reconnect depending on protocol |
| Backend/VM/Pod fails | ELB/LB selects another healthy member | Requires state/persistence recovery if state was local | Socket reconnect may land on another backend; durable state/replay required | Protocol-specific retry and state recovery |
| ELB/service VIP fails | Select alternate healthy ELB/service or site | State service and persistence must also remain available | Reconnect to alternate endpoint and restore logical session | L4/DNS/routing recovery; WAF irrelevant |
| DNS/GTM changes site | Next/new requests use alternate reachable VIP | Alternate site must have compatible session/data state | Existing socket does not move; reconnect/re-resolve required | New connections use alternate endpoint if protocol/client re-resolves |
| Cross-site contingency activated | Usually transparent after retry if backend is reachable | Validate latency, persistence, data/state locality and transaction safety | Reconnect likely; remote latency/state recovery matters | Depends on whether protocol is approved for cross-site routing |
| Inter-site route fails while local healthy | No impact if local path remains selected | No impact if state is local/healthy | No impact to local sockets; remote sockets fail | No impact to local path |
| Inter-site route fails while remote contingency is active | Fall back locally if possible, otherwise fail/retry/site switch | Risk of losing remote state/session path; recovery may be larger | Remote sockets break and must reconnect to another valid path | Protocol-specific reconnect/failover |
| Full site fails | GTM/DNS selects ready alternate site | Requires state/data availability at alternate site | Reconnect, re-authenticate, restore/replay state | Reconnect/re-resolve using protocol-specific alternate-site design |

Every scenario should therefore answer **two separate questions**:

1. **Infrastructure recovery:** which firewall/LTM/WAF/ELB/site path becomes active?
2. **Application recovery:** what must this application type do after that infrastructure change?

Do not call an infrastructure failover successful until the application-type-specific recovery requirement is also satisfied.

## Common control-plane choices

Analyse DNS/GTM separately from the WAF architecture:

- external/customer resolver queries enterprise GTM directly; or
- customer/corporate DNS delegates/forwards to enterprise GTM.

Assume up to two GTM/DNS listeners or instances per site.

GTM returns a healthy, client-reachable application VIP; it is not an inline application-data hop.

## Common data-plane invariants

Per hosting environment, per site:

- four private leased lines/routes are used for external-user access;
- the external-user population is distributed across those paths so a single line failure should affect only a subset of users;
- two HA firewall pairs serve the hosting environment;
- externally reachable application VIPs live on the firewall tier;
- LTM and WAF sit behind the firewall tier;
- applications may be:
  - on-premises;
  - private-cloud VMs;
  - private-cloud Kubernetes;
  - PaaS behind a stable/floating ELB endpoint;
- private-cloud applications may add:
  - cloud-edge firewall;
  - ELB;
  - VM or Kubernetes backend;
- internal users may connect directly to an internal ELB/service path and bypass the external WAF tier.

## Round-2 failure studies

Apply each failure to all three topology options **and to each applicable application type**. A scenario is incomplete if it only states that the infrastructure failed over successfully without explaining the application-specific consequence.

At minimum, distinguish:

- stateless web;
- stateful web;
- socket/WebSocket/long-lived connection;
- non-web service bypassing WAF.

Where a failure is irrelevant to an application type (for example, a WAF-node failure for a non-web service that truly bypasses the WAF), record **No direct impact from this layer** rather than omitting the application type.

Apply each failure to all three options wherever relevant.

### Access and DNS

- one leased line fails;
- one leased-line user population loses reachability while other populations remain healthy;
- one firewall node fails;
- one entire firewall HA pair fails;
- one GTM/DNS listener fails;
- both GTM/DNS listeners in one site fail;
- GTM advertises a VIP that one external population cannot route to;
- customer/corporate DNS caches a stale answer.

### LTM/WAF

- one LTM node fails;
- one WAF node fails;
- all local WAF capacity becomes unavailable;
- WAF process is alive but application path through it is unhealthy;
- WAF capacity is exhausted;
- bad WAF policy/configuration affects one or all nodes.

### Application infrastructure

- on-premises application member fails;
- cloud-edge firewall fails;
- ELB member/service fails;
- VM fails;
- Kubernetes pod/node/ingress/cluster fails;
- PaaS moves behind a stable ELB address.

### Application dependencies

- App B1 fails while App A1 remains healthy;
- A1 -> B1 network path fails while both applications are individually healthy;
- B2 is healthy but cross-site routing is not available;
- A1 is using B2 and the inter-site route then fails;
- several local applications depend on B1, creating potential cascading failover.

### Site-level

- inter-site routing fails while all local resources are healthy;
- inter-site routing fails while remote contingency is already in use;
- whole Site 1 application tier fails;
- whole Site 1 ingress fails;
- whole Site 1 fails;
- passive Site 2 application has not yet been manually started.

## Required analysis fields

For every scenario capture:

| Field | Description |
|---|---|
| Scenario | Exact injected failure |
| Actor/path | External user, internal user, App A -> B, etc. |
| Application type | Stateless web, stateful web, socket/WebSocket, or non-web |
| State location | None/shared/local/session store/database/durable stream/etc. |
| Persistence/affinity | Whether LTM/ELB/backend affinity is required |
| Failed component | Component or tier that failed |
| What remains healthy | Explicit unaffected services |
| Detection | Which layer notices the failure |
| Option 1 result | Clustered WAF + local-only |
| Option 2 result | LB WAF + local-only |
| Option 3 result | LB WAF + cross-site contingency |
| External-user impact | Which leased-line populations are affected |
| Internal-user impact | Whether internal ELB/service access remains available |
| A -> B impact | Dependency behaviour |
| Session impact | HTTP retry, re-login, TCP reset, WebSocket reconnect, protocol reconnect, etc. |
| Application recovery | Retry only, restore session, re-authenticate, resubscribe, replay/reconcile, protocol-specific recovery |
| State portability | Whether required state is available after member/site change |
| Cascading risk | Whether unrelated apps/site are forced to move |
| Capacity impact | Remaining local/remote capacity |
| Manual action | Any operator action required |
| Recovery path | Smallest safe recovery domain |
| Evidence required | Health checks, logs, failover test, route verification |

## Design objective

The analysis should test whether each architecture achieves the following:

> Recover the smallest failed service or infrastructure tier possible without forcing unrelated applications or user populations to fail over.

In particular:

- loss of one leased line should be treated as a user-population reachability failure, not as an application failure;
- loss of one WAF should remain a WAF-node event;
- loss of the entire local WAF tier should not force application failover when a safe remote WAF path exists;
- failure of App B should not force App A and every other dependent application to move sites when a safe B2 contingency exists;
- loss of cross-site routing should remove contingency options but should not break healthy local services;
- a full site move should remain the final recovery level;
- infrastructure failover should not be considered complete until the relevant application type has recovered its required session, state, connection or protocol context;
- non-web services should not be marked unavailable merely because the WAF tier is unavailable when their approved path bypasses WAF.

## Working decisions / TBDs

Use this section to record changes before updating the canonical documents.

- [ ] Confirm exact leased-line-to-firewall-pair mapping.
- [ ] Confirm whether user populations are equally or unevenly distributed across the four leased lines.
- [ ] Confirm whether customers can automatically reroute between leased-line paths.
- [ ] Confirm the exact two-GTM-per-site arrangement: independent listeners, HA pairs, or another topology.
- [ ] Confirm which internal users bypass WAF and which services they resolve directly.
- [ ] Confirm which App A -> App B flows require WAF inspection versus internal service routing.
- [ ] Confirm which applications are manual active/passive, automated active/passive, or active/active.
- [ ] Confirm which PaaS ELB addresses can move workloads across sites without changing the upstream endpoint.
- [ ] Confirm which cross-site paths are technically possible through stateful firewall tiers.
- [ ] Confirm contingency capacity and symmetry requirements before recommending remote WAF or remote dependency use.

## Expected outputs

This branch should ultimately produce:

1. a stable end-to-end context diagram;
2. a three-option architecture comparison;
3. a common failure matrix applied across all options;
4. an application-type impact matrix showing how each failure differs for stateless web, stateful web, socket/WebSocket and non-web services;
5. explicit external-user, internal-user and App A -> App B outcomes;
6. cascading-failure analysis;
7. cross-site routing pros/cons and prerequisites;
8. recommended architecture and unresolved decisions;
9. updates to the canonical architecture/failure documents only after this analysis has been reviewed.
