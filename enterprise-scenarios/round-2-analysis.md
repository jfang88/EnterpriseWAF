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
| Failed component | Component or tier that failed |
| What remains healthy | Explicit unaffected services |
| Detection | Which layer notices the failure |
| Option 1 result | Clustered WAF + local-only |
| Option 2 result | LB WAF + local-only |
| Option 3 result | LB WAF + cross-site contingency |
| External-user impact | Which leased-line populations are affected |
| Internal-user impact | Whether internal ELB/service access remains available |
| A -> B impact | Dependency behaviour |
| Session impact | HTTP retry, TCP reset, WebSocket reconnect, etc. |
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
- a full site move should remain the final recovery level.

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
4. explicit external-user, internal-user and App A -> App B outcomes;
5. cascading-failure analysis;
6. cross-site routing pros/cons and prerequisites;
7. recommended architecture and unresolved decisions;
8. updates to the canonical architecture/failure documents only after this analysis has been reviewed.
