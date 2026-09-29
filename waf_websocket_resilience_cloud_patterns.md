# WebSocket Resilience Through Enterprise WAF and Load-Balancer Tiers

**Status:** Design guidance / architecture decision record  
**Last reviewed:** 2026-09-29  
**Scope:** Dual-site Enterprise WAF architecture supporting HTTP/HTTPS and WebSocket traffic

## Related repository documents

This document is a companion to:

- [Enterprise WAF Architecture Options and Cross-Site Resilience](./waf_architecture_options_cross_site_resilience.md)
- [F5 Failover Failure V4 Matrix and Footnotes](./f5_failover_failure_V4_matrix_footnotes.md)

The existing documents cover broader WAF topology, cross-site routing, GTM/LTM failure domains, and application failover. This document focuses specifically on long-lived WebSocket connections and how to design for infrastructure failures.

---

# 1. Executive summary

The principal design conclusion is:

> **Do not treat preservation of an individual WebSocket/TCP connection as the primary availability mechanism. Design the application so the logical user/session can reconnect quickly to another healthy infrastructure path.**

A WebSocket begins with an HTTP Upgrade handshake and then becomes a persistent, bidirectional connection over TCP. Once established, the connection is stateful across every proxy/load-balancer hop in the path.

The major cloud-provider patterns reviewed for this document do not expose a customer-facing guarantee that an arbitrary established WebSocket is synchronously migrated between WAF or load-balancer nodes after an abrupt proxy-node failure. Instead, the documented patterns emphasize:

1. redundant load-balancing infrastructure;
2. health checking;
3. connection draining for planned removal;
4. client reconnect after connection loss at the client, firewall, network, proxy or backend;
5. session/application state outside an individual proxy or application instance;
6. retry with backoff and jitter;
7. message acknowledgement, sequencing, replay or recovery where message loss matters;
8. idempotent handling of retryable client commands and duplicate events.

F5 connection mirroring remains an available additional protection where preservation of a connection is genuinely important, but current F5 Advanced WAF documentation lists material limitations. It should therefore be treated as an enhancement rather than the only recovery mechanism.

---

# 2. Environment assumed by this design

The enterprise topology is assumed to contain:

- two sites operating primarily active/passive;
- a GTM/BIG-IP DNS service at each site, reached through clients' recursive DNS;
- external clients, their firewalls/proxies and DNS connected through private-network services;
- four physical/logical ingress circuits;
- two enterprise firewall HA pairs total (one per site for this analysis); actual circuit/firewall mapping to be verified;
- two WAF appliances in each site;
- either:
  - **Design A:** a WAF active/standby cluster owning the site external VIP, without a separate ingress LTM, or
  - **Design B:** an ingress LTM HA pair owning the site external VIP and balancing independent active WAFs;
- an on-premises application ELB internal VIP behind the WAF, operating as L3/L4 forwarder/TCP passthrough or L7 terminating proxy;
- DCS (Huawei VMware) VM applications, and/or HCS (Huawei private cloud) VM applications or Kubernetes ingress/Services/Pods;
- applications using a mixture of HTTPS and secure WebSockets.

Representative flow at either site:

~~~text
External client -> client DNS/firewall/proxy -> four private circuits/VPN (as routed)
  -> enterprise site firewall HA -> site external VIP

A: external VIP on WAF active/standby cluster -> application ELB internal VIP
B: external VIP on LTM HA -> independent WAF pool -> application ELB internal VIP

ELB -> DCS VMware VM pool OR HCS VM pool OR HCS Kubernetes ingress -> Pods
~~~

See the [full logical flow and two-design comparison](./waf_architecture_options_cross_site_resilience.md#24-explicit-end-to-end-topology-and-ownership). The other site's GTM and VIP provide an alternate only when the client can reach that site and its application/data services are ready.

---

# 3. HTTP versus WebSocket failure semantics

Normal HTTP traffic and WebSocket traffic should not use the same availability assumptions.

A normal HTTP request is a discrete transaction. A failed request can often be retried through another healthy load-balancer/WAF/backend path.

A WebSocket is different:

~~~text
HTTP request
client -> proxy -> server
request ends

WebSocket
client ================= proxy ================= server
                 long-lived TCP state
~~~

RFC 6455 defines WebSocket as an HTTP opening handshake followed by bidirectional message transfer over the established connection.

Therefore:

| Event | Normal HTTP | Established WebSocket |
|---|---|---|
| WAF node fails | Request may fail; next request can use another node | Connection through failed node may be lost |
| Backend Pod/VM fails | Request may be retried | Socket terminating on that backend is lost |
| Site fails | New requests can move after GTM/DNS convergence | Existing Site-A sockets do not migrate to Site B |
| DNS answer changes | New connections can use new site | Existing connection is unchanged |
| Pool member is drained | New requests use another member | Existing socket can remain during drain if supported |
| Load-balancer node fails | New flows use healthy infrastructure | Do not assume live connection migration unless explicitly guaranteed |

**Reference:** RFC 6455, The WebSocket Protocol  
https://www.rfc-editor.org/info/rfc6455/

---

# 4. Three different kinds of synchronization

The architecture must clearly distinguish:

~~~text
WAF policy/config synchronization
              !=
application/session state synchronization
              !=
live TCP/WebSocket connection synchronization
~~~

## 4.1 WAF policy/configuration synchronization

This ensures multiple WAF nodes apply consistent security policy.

F5 documents Advanced WAF / ASM security-policy synchronization through device groups, including use of an ASM-enabled Sync-Only group for multiple systems processing similar traffic behind a router or load balancer.

This supports a horizontally active WAF pool, but configuration synchronization does not by itself preserve a TCP/WebSocket connection when one WAF node fails.

**Reference:** F5, Automatically Synchronizing Application Security Configurations  
https://techdocs.f5.com/en-us/bigip-17-5-0/big-ip-asm-implementations/automatically-synchronizing-application-security-configurations.html

## 4.2 Application/session-state synchronization

This is the state required for a newly connected application instance to continue serving the user.

Examples include:

- login/session state;
- authorization context;
- subscription information;
- logical conversation/session identifier;
- progress/checkpoint state;
- last acknowledged event/message number.

Where rapid recovery is required, this state should not exist only in the memory of one Pod, VM, WAF or load-balancer node.

## 4.3 Live connection synchronization

This attempts to preserve the current TCP/application connection after a stateful infrastructure device fails.

F5 supports connection mirroring, but current Advanced WAF documentation lists limitations including:

- mirroring to only one standby device;
- only two devices for this connection-mirroring behavior;
- no multiple-failover preservation;
- connection reset on failback;
- differences/limitations for some AWAF runtime security features.

F5 also states that full connection mirroring requires licensed/provisioned LTM, and its documented best-practice arrangement is an LTM + AWAF deployment with floating Self IPs.

**References:**

- F5, Connection Mirroring with ASM  
  https://techdocs.f5.com/en-us/bigip-14-1-0/big-ip-asm-implementations-14-1-0/connection-mirroring-with-asm.html
- F5, Connection mirroring limitations with ASM  
  https://techdocs.f5.com/en-us/bigip-17-0-0/big-ip-asm-implementations/connection-mirroring-with-asm/connection-mirroring-limitations.html

---

# 5. What the major cloud providers do

The public cloud services provide useful reference patterns because they operate large shared fleets of WAF and load-balancing infrastructure.

The important conclusion is not that every provider implements its internal nodes identically. Their internal implementations are deliberately abstracted.

The useful architectural observation is:

> **Their customer-facing availability patterns rely on managed redundancy, health checking, draining, reconnect/retry and recoverable application state rather than asking applications to depend on transparent migration of every existing WebSocket between proxy nodes.**

## 5.1 AWS Application Load Balancer

AWS Application Load Balancer natively supports WebSockets.

AWS states that after an HTTP connection is upgraded, the TCP connections from client to load balancer and load balancer to target become a persistent WebSocket connection.

AWS further documents that WebSocket connections are inherently sticky: the target that returns HTTP 101 for the upgrade is the target used for that WebSocket connection.

This means a WebSocket is naturally tied to one selected backend for its lifetime.

AWS supports target deregistration delay / connection draining. A deregistering target stops receiving new requests while in-flight requests and active connections are given time to complete. The default deregistration delay is 300 seconds.

**References:**

- AWS, Application Load Balancer listeners - WebSockets  
  https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-listeners.html
- AWS, Application Load Balancer target group attributes - WebSocket stickiness and deregistration delay  
  https://docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-target-group-attributes.html
- AWS, Register targets - connection draining  
  https://docs.aws.amazon.com/elasticloadbalancing/latest/application/target-group-register-targets.html

### AWS design lesson

Do not require cookie persistence just to keep an already-established WebSocket on the same target; the connection itself is already pinned.

Persistence becomes relevant when the client has to establish a **new** connection and application state is still local to a backend.

---

## 5.2 Azure Application Gateway

Azure Application Gateway supports WebSockets and provides connection draining.

Microsoft explicitly documents that connection draining is honored for WebSocket connections. When a backend is deregistering, new requests/connections are directed elsewhere while existing connections can continue until the configured timeout expires.

Microsoft documents a configurable connection-draining timeout of 1 to 3,600 seconds when enabled.

**References:**

- Microsoft, Azure Application Gateway features - Connection draining  
  https://learn.microsoft.com/en-us/azure/application-gateway/features
- Microsoft, Application Gateway Backend Settings - Connection draining  
  https://learn.microsoft.com/en-us/azure/application-gateway/configuration-http-settings

### Azure Web PubSub shows the stronger application-layer recovery pattern

Azure Web PubSub provides a reliable WebSocket subprotocol specifically designed to recover from dropped connections and message loss.

The documented reliable protocol provides:

- connectionId;
- reconnectionToken;
- connection recovery;
- publisher acknowledgement IDs;
- subscriber sequence IDs;
- message-loss recovery.

Microsoft's reliability documentation explicitly states that zone failovers, region failovers and transient faults can drop active connections and recommends safe reconnect behavior.

**References:**

- Microsoft, Azure Web PubSub reliable WebSocket subprotocol  
  https://learn.microsoft.com/en-us/azure/azure-web-pubsub/reference-json-reliable-webpubsub-subprotocol
- Microsoft, Reliability in Azure Web PubSub Service  
  https://learn.microsoft.com/en-us/azure/reliability/reliability-web-pubsub

### Azure design lesson

Even a service built specifically for WebSockets treats connection loss as a recoverable event. The logical client/session is recovered above the TCP layer.

---

## 5.3 Google Cloud Load Balancing

Google Cloud documentation is particularly explicit about long-lived WebSocket behavior.

For Application Load Balancers, Google notes that serving proxy tasks can be restarted or changed during routine maintenance and that longer-lived connections are more likely to encounter TCP termination during those activities.

Google also provides connection draining so removed backend instances/endpoints stop receiving new connections while existing connections are allowed time to complete.

For passthrough load balancing, Google documents that when connection tracking is removed and packets subsequently reach another backend, that backend has no record of the original TCP connection and can send a TCP reset. This is a clear demonstration of why selecting another healthy backend does not recreate an existing TCP connection.

**References:**

- Google Cloud, Request distribution for external Application Load Balancers - WebSocket timeout and maintenance behavior  
  https://docs.cloud.google.com/load-balancing/docs/https/request-distribution
- Google Cloud, Connection draining  
  https://docs.cloud.google.com/load-balancing/docs/enabling-connection-draining
- Google Cloud, Internal passthrough Network Load Balancer traffic distribution and failover  
  https://docs.cloud.google.com/load-balancing/docs/internal/int-netlb-traffic-distribution

### Google design lesson

Load-balancer availability and connection availability are different things. A load-balancing service can remain available for new connections while an individual established TCP/WebSocket connection is disrupted.

---

# 6. Recommended enterprise pattern

For a normal WebSocket application, **Design B is preferred when the additional ingress LTM and independent WAF pool are justified, healthy, fully monitored and capacity-tested**. Design A remains valid for a WAF cluster with an external VIP and no ingress LTM:

~~~text
                         GTM
                          |
                    Site A ingress
                          |
                     LTM HA pair
                          |
              +-----------+-----------+
              |                       |
            WAF-1                   WAF-2
        active member           active member
              |                       |
              +-----------+-----------+
                          |
                     platform ELB
                          |
                 ingress / VM LB
                          |
                  application pool
                          |
            shared/recoverable state
~~~

The design principle is:

> **Infrastructure protects service availability. The application protects logical-session and message continuity.**

This allows:

- both WAFs to provide usable capacity;
- LTM to health-check and remove failed WAF members;
- individual WAFs to be drained for maintenance;
- application instances to be scaled horizontally;
- Pods/VMs to be replaced;
- site failover to occur without requiring the original TCP socket to survive.

---

## End-to-end reliability controls

The WAF design is one part of the application delivery service. Each layer must restore **new connections** after its own failure; no layer should promise to preserve an established socket through every possible fault. Design A has WAF cluster HA with no separate ingress LTM; Design B has LTM HA in front of independent WAFs. The [full fault analysis](./waf_architecture_options_cross_site_resilience.md#16a-end-to-end-failure-analysis-for-designs-a-and-b) models both.

| Layer / failure domain | Reliability control | Recovery boundary and verification |
|---|---|---|
| Browser, device and client network | Detect offline/online transitions and page suspension; use an application heartbeat or deadline to find silent dead paths; reconnect with backoff and jitter when connectivity returns | A sleeping device, browser restart, Wi-Fi/mobile handoff or local proxy reset may lose the socket without any data-centre fault. Browser restart may also lose in-memory cursors; persist a suitable cursor or fetch an authoritative snapshot. |
| Private circuit, routing, VPN and firewalls | Diversify routes/circuits where possible; test both site VIPs from each client pool; use firewall HA and state synchronization where supported; configure and measure TCP idle and session age limits | A firewall failover or path change can reset or silently blackhole flows even if a VIP stays reachable. Verify symmetric return path, NAT ownership and policy for the chosen recovery path; reconnect still required. |
| DNS/GTM and site ingress | Service-specific health, redundant resolvers, reachable fallback VIPs and measured client re-resolution | DNS only steers a new connection; cached answers, private-network reachability and application readiness determine actual site recovery. |
| Ingress LTM and WAF pool | Redundant LTM/WAF nodes, through-path health checks, policy sync, planned draining and capacity for a failed member | Withdraw an unhealthy path for new connections; test active flow loss and reconnect separately from VIP availability. |
| Platform ELB and ingress or VM load balancer | Redundant nodes, backend health/readiness and draining; coordinate idle and request timeouts through all hops | Confirm implementation-specific behavior for long-lived streams and abrupt node loss. A new backend must restore user and subscription state. |
| Kubernetes Pods or VM pool | Spread replicas across failure domains; readiness before admission; graceful termination with bounded drain; spare capacity | Pod/VM and node loss may close sockets. Avoid keeping the only copy of session, subscription or cursor state on that instance. |
| Identity, state and event services | Available authentication/token verification, durable event retention or snapshot, shared session state, per-operation deduplication | Reconnection is useless if authentication or replay cannot run at the secondary site; define retention, recovery-point and degraded-mode behavior. |

Set explicit targets for **detect → DNS/routing convergence → reconnect → resubscribe → reconcile**, including the worst supported client population and four-circuit failure cases. Health must represent application readiness, not merely an open TCP port. Separate deliberate drain from abrupt failure; neither replaces client recovery.

---

## Application state placement and recovery contract

A WAF HA pair can protect the **WAF service VIP** and, for a supported and tested mirroring event, may preserve some connections through one WAF member failure. It cannot preserve a socket through an application ELB failure, Pod or VM termination, client/firewall path loss or a full site failure. The selected backend owns a live TCP/WebSocket endpoint. After that endpoint disappears, the application must accept a new connection on another healthy instance and reconstruct the logical session.

| State | Normal owner and durability | Required recovery behavior |
|---|---|---|
| TCP/WebSocket transport, TLS, firewall/NAT/LTM/WAF/ELB connection tables | Ephemeral state on the selected path; optional device-specific mirroring has a narrow failure scope | Assume the old socket is lost after a stateful hop or backend fails. A new connection selects a healthy path. Do not use a live socket as the only record of a business action. |
| Authentication and authorization | Available identity service or portable, verifiable token; revocation/expiry policy shared with the DR site | Reauthenticate or renew on every new connection and reauthorize each subscription/command. Reconnect must work on another Pod/VM and at the ready DR site. |
| Logical user/session and workflow state | Shared or replicated session store and authoritative database, not only app-process or WAF memory | Rebuild by stable session/user identifier. Define expiry, write consistency and the data recovery point for the passive site. |
| Desired subscriptions and per-connection routing | Client retains desired topics (or a recoverable subscription store); a broker/connection registry may hold transient delivery mappings | Client resubscribes after authentication. Server rejects unauthorized topics. A new backend builds fresh connection mappings and resumes from the agreed cursor. |
| Server-to-client events and cursor | Durable event log or authoritative snapshot per stream/partition; client stores last **safely processed** cursor | Replay within documented retention; deduplicate and detect gaps. If cursor expired or cross-site log lags, return an explicit gap response and fetch/reconcile a snapshot. |
| Client commands and business outcome | Authoritative transaction store plus durable operation-ID/idempotency record, ideally committed atomically with the business effect | A lost acknowledgement is ambiguous. Query by operation ID; retry with the same ID within its defined scope/window and return the recorded outcome. Never blindly submit a second order/payment. |

The state services themselves need HA, capacity and cross-site consistency appropriate to each application's RTO/RPO. A shared cache is not automatically durable; specify persistence, replication and recovery after loss of that cache. A passive site's WAF and ELB being healthy is insufficient if its identity, event log or authoritative data is not ready. Avoid dual writers or split-brain during promotion and failback.

### Application-team implementation sequence

1. **Before failure:** Identify every WebSocket stream and command, its ordering scope, replay retention, maximum tolerable gap and authoritative lookup. Persist the cursor only after the consumer has safely applied the event. Keep an operation ID through client retries. Store recoverable session/workflow data outside a single Pod or VM.
2. **Detect:** Handle close/error, browser resume and network changes. Use heartbeat or an application message deadline for silent blackholes. Set activity/heartbeat periods against the shortest intended idle timeout across client proxy, firewall, LTM, WAF, ELB and ingress; do not assume protocol Ping/Pong is accessible from browser JavaScript.
3. **Reconnect:** Use one bounded reconnect loop per logical session with exponential backoff and jitter. Re-resolve the service when possible, reconnect only to a ready endpoint, refresh credentials and cap concurrent handshakes. Avoid retry storms and unbounded in-memory queues.
4. **Restore:** Authenticate, restore the logical session, reauthorize and recreate subscriptions, then request replay from the last safely processed cursor. If replay is unavailable, fetch an authoritative snapshot and reconcile before showing the view as current.
5. **Reconcile writes:** For commands whose acknowledgement was lost, query authoritative outcome by operation ID. Retry only according to the operation's idempotency contract, with the same key. A new socket or a successful subscription does not settle a pending business transaction.
6. **Resume and observe:** Expose a clear catching-up/degraded state while replay or snapshot runs. Record disconnect cause, detect-to-connect and connect-to-consistent-state times, gaps, duplicates, pending commands and peak reconnects per second.

### VM affinity and durable state

For a VM pool behind an application ELB, each established WebSocket is tied to the backend VM selected for that connection. This is **connection affinity for its lifetime**: messages on that socket reach the same application process while the path is alive. AWS ALB describes upgraded WebSockets as persistent connections to the selected target and calls them inherently sticky. The on-premises ELB's exact L3/L4 or L7 behavior must be verified, rather than inferred from AWS.

A *new* WebSocket, separate HTTP request, or reconnect can land on a different VM. If the application needs multiple independent requests to reach one VM during a transition, configure and test the appropriate ELB persistence mechanism, cookie/affinity scope and expiry. Do not rely on stickiness as the only copy of session or subscription state: it cannot route to a dead VM. The same principle applies to Pod affinity. On VM/process loss, the ELB withdraws the target for new connections; existing sockets anchored there fail, and another VM reconstructs the session from the shared/replicated store or from client resubscription. Backend health/readiness and drain determine when targets receive new sockets.

**Source boundary:** [AWS ALB listeners](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-listeners.html) describe the persistent upgraded connection; [AWS ALB target attributes](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-target-group-attributes.html) describe inherent WebSocket stickiness. These illustrate the connection principle; test the actual on-premises Huawei/application ELB and any Kubernetes ingress.

### Concrete reconnect and catch-up protocol

The following is an **illustrative application protocol**, not a WebSocket standard. Agree its fields, ordering scope, retention and error responses per application. A bare “current sequence number” identifies a gap but cannot supply the missing messages.

1. **Track state while connected:** For each stream/partition and generation (epoch), retain the last sequence safely *applied* by the client, not merely received. If the consumer must survive a browser/app restart, persist the cursor appropriately. Treat duplicate event IDs as harmless. Keep pending commands and their operation IDs until the authoritative result is known.
2. **Detect and schedule:** On close, error, missed heartbeat/deadline, browser resume or network change, close the stale transport and run **one** reconnect attempt at a time. An example full-jitter delay is `random(0, min(cap, base × 2^attempt))`, with illustrative base 0.5–1 second and cap 30 seconds. Set a per-attempt connection timeout; cap concurrency and queued commands. Use the application's measured RTO, fleet size and authentication capacity to tune the values. Continue controlled retries for a transient outage, respect server retry guidance, and stop or prompt for a permanent authorization/policy error. Reset escalation after a stable session, not every brief handshake.
3. **Resolve and authenticate:** Re-resolve the endpoint where the client platform permits. Obtain a fresh, short-lived credential when expired and authenticate the new `wss://` upgrade. A valid portable token or server-side session may permit fast authentication, but the new endpoint must validate identity, expiry and authorization again. Browser WebSocket APIs cannot set arbitrary request headers; use an approved secure cookie or a short-lived ticket obtained via HTTPS as appropriate. Do not embed reusable bearer secrets in a URL. If a token refresh fails, do not spin on failed upgrades.
4. **Resume request:** After authentication, send the logical session ID, desired subscriptions and a cursor for each stream such as `{stream, epoch, lastAppliedSeq}`. The server checks authorization and replies with its stream epoch, `headSeq` (current high-water mark), `firstAvailableSeq` (earliest retained), and either replay acceptance or an explicit snapshot-required response. These names are examples; avoid trusting client-supplied cursors for access to another tenant's events.
5. **Replay and verify:** If epoch matches and `lastAppliedSeq + 1 >= firstAvailableSeq`, replay events from `lastAppliedSeq + 1` through the agreed catch-up boundary. Client verifies each next per-stream sequence or detects a gap, applies events in order, deduplicates overlap and advances its durable cursor **after** applying. Buffer or sequence live events during catch-up so none fall between replay and live mode; bound the buffer and signal overflow.
6. **Snapshot fallback:** If the cursor is too old, the epoch changed, or replay cannot bridge a replication gap, return a versioned authoritative snapshot with an associated sequence/epoch. Apply the snapshot and then events after its boundary, or perform an atomic snapshot-to-live handoff. Do not silently jump the cursor to `headSeq` and call the view recovered.
7. **Reconcile commands:** Query uncertain command outcome by operation ID against the authoritative store. A retry uses the same key only under a documented idempotency window and scope. The service persists the deduplication/result record with the business effect where possible. Mark the UI consistent only after event catch-up and pending business outcomes are resolved.

Illustrative exchange for one ordered stream:

~~~text
Client reconnects and authenticates over a new WebSocket
Client: RESUME {stream:"orders:123", epoch:"e7", lastAppliedSeq:1042}
Server: RESUME_OK {epoch:"e7", firstAvailableSeq:1000, headSeq:1045}
Server: EVENT {seq:1043, id:"..."}
Server: EVENT {seq:1044, id:"..."}
Server: EVENT {seq:1045, id:"..."}
Client: ACK {stream:"orders:123", appliedThrough:1045}
Server: LIVE {nextSeq:1046}

If firstAvailableSeq were 1050, or epoch differed:
Server: SNAPSHOT_REQUIRED {currentEpoch:"e8", headSeq:1100}
Client: fetch an authorized snapshot and resume after its consistent boundary
~~~

Sequence numbers are scoped to a named stream/partition and epoch; independent streams do not have a single global sequence. Define what happens when two sites disagree about the head or event-log replication lags. Authentication on reconnect and replay access checks must run before sending any retained messages. Azure Web PubSub's [reliable WebSocket subprotocol](https://learn.microsoft.com/en-us/azure/azure-web-pubsub/reference-json-reliable-webpubsub-subprotocol) demonstrates reconnection tokens, sequence acknowledgements and replay-oriented recovery, but these fields and guarantees are **service-specific**, not native WebSocket behavior.

### What an ELB or application-node failure means

| Fault | New path selected by infrastructure | Application responsibility |
|---|---|---|
| One application ELB member/proxy process fails | Its HA peer or surviving ELB path takes new connections if healthy. L3/L4 pass-through and L7 proxy modes have different termination, timeout and drain behavior. | Treat affected sockets and in-flight HTTP writes as lost or ambiguous. Reconnect to a healthy backend, restore state and look up uncertain write outcomes. |
| Whole application ELB tier fails | No new backend connection until its own HA/recovery or an approved alternate application path is ready; WAF VIP health alone must not advertise the app. | Retry with jitter within client limits, surface unavailable/degraded status, retain cursor/operation IDs and reconcile when service returns. |
| Pod, Kubernetes node, VM or app process fails | ELB/ingress withdraws unhealthy target for new connections; replicas take new connections after readiness. | Recover on a different instance. Recreate subscriptions and replay/snapshot. Graceful shutdown drains or closes sockets; abrupt failure still requires the same client recovery contract. |
| Identity, session, event or authoritative store fails | An ingress path may remain green while application recovery is impossible. | Fail readiness where required, avoid pretending a reconnected socket is consistent, and enter the documented degraded mode until the state service is available. |
| Site 1 becomes unavailable | GTM may advertise Site 2 only after application, state and dependencies are ready and client networks can reach its VIP. | New connection, reauthentication, resubscription and replay/snapshot against Site 2's consistent state; reconcile pending commands before retry. |

Application teams should demonstrate these behaviors with a real long-lived socket while abruptly terminating the selected ELB path and selected Pod/VM, not just by taking a backend out of rotation. Repeat with graceful drain, a silent blackhole, expired replay cursor, lost command acknowledgement, passive-site promotion and a mass reconnect. Measure both **time to reconnect** and **time to correct business state**. See [Section 17](#17-minimum-application-requirements-for-resilient-websockets), [Section 19](#19-testing-plan) and the [main paper's end-to-end failure table](./waf_architecture_options_cross_site_resilience.md#16a-end-to-end-failure-analysis-for-designs-a-and-b).

---

# 7. When F5 connection mirroring is still justified

Connection mirroring can still be valuable when losing even one established flow creates unusually high impact.

Possible reasons include:

- an application cannot reconnect automatically;
- reconnection performs an expensive external transaction;
- protocol semantics make retry difficult;
- a connection loss causes a significant manual recovery event;
- business requirements explicitly demand best-effort preservation through a single appliance failure.

In that case:

~~~text
                      WAF HA pair
                  active <====> standby
                         state
                       mirroring
                          |
                     application
~~~

may reduce disruption from one supported failover event.

However:

1. client reconnect must still exist for failures outside the mirrored pair;
2. whole-site failure still destroys the connection;
3. backend Pod/VM failure still destroys the backend connection;
4. path/firewall/circuit failures can still interrupt the flow;
5. current F5 documentation says failback can reset the mirrored connection;
6. current F5 documentation says multiple sequential failovers are not preserved.

Therefore connection mirroring should not be treated as a substitute for application recovery.

---

# 8. Application reconnect pattern

The client should treat a dropped WebSocket as an expected recoverable event, whether the fault originates in the client or anywhere along the delivery path. Browser sleep/restart, device network handoff, a failed client-side proxy, firewall state loss, circuit interruption and infrastructure maintenance all require a new connection.

Recommended logical flow:

~~~text
CONNECTED
    |
socket lost / heartbeat failure
    |
    v
DISCONNECTED
    |
bounded exponential backoff + jitter
    |
    v
CONNECTING
    |
authenticate / validate token
    |
restore logical session
    |
restore subscriptions
    |
request/reconcile missed events if required
    |
    v
CONNECTED
~~~

On reconnect, resolve the service endpoint again where the platform permits, refresh or validate credentials, restore subscriptions and send the last **safely processed** event cursor. If a saved cursor has expired, fetch an authoritative snapshot and reconcile before accepting live events. Browser lifecycle and offline events can prompt a retry, but heartbeat deadlines are still needed for silent failures.

Do not reconnect all clients immediately with a fixed identical delay.

Use bounded exponential backoff with random jitter to reduce synchronized retry storms. AWS documents full jitter specifically as a method to avoid a thundering-herd retry burst.

**References:**

- AWS SDK retry behavior - Why jitter matters  
  https://docs.aws.amazon.com/sdkref/latest/guide/feature-retry-behavior.html
- AWS Well-Architected - Control and limit retry calls  
  https://docs.aws.amazon.com/wellarchitected/2022-03-31/framework/rel_mitigate_interaction_failure_limit_retries.html

---

# 9. Reconnect is not enough when messages matter

A successful reconnect only restores transport.

It does not prove that messages sent immediately before a failure were received exactly once.

Example:

~~~text
Server sends:

1001
1002
1003
1004
1005

Client receives:

1001
1002
1003

--- infrastructure failure ---

client reconnects
~~~

Without an application recovery mechanism the client cannot know whether 1004 and 1005 were lost.

Where message delivery is business-critical, add logical delivery semantics such as:

- message/event ID;
- monotonic sequence number;
- acknowledgement ID;
- idempotency key for retryable writes;
- last-received sequence checkpoint;
- bounded event replay;
- duplicate detection.

Conceptually:

~~~text
reconnect
   |
client: last acknowledged event = 1003
   |
server/event service:
   |
replay 1004
replay 1005
   |
resume live stream
~~~

Distinguish three recovery cases:

1. **Server → client:** Assign stable event IDs, durably retain events for the agreed replay window, and advance the client cursor only after processing. Replay may redeliver the last event; consumers must detect duplicates. Define the gap response when the cursor is too old (for example, a full state refresh).
2. **Client → server:** A command may have succeeded even if its acknowledgement was lost. Send a stable operation ID/idempotency key on retry, record the outcome durably within the business transaction where possible, and return the recorded result for duplicate submissions. Bound the key's scope and lifetime.
3. **After recovery:** Reconcile state against an authoritative API or snapshot when ordering, retention or cross-site replication prevents exact replay. Ordering is meaningful only within the defined stream/partition; do not imply global order across independent producers.

Aim for effectively-once **business effects** through durable deduplication and reconciliation; a live WebSocket transport does not guarantee exactly-once delivery.

Azure Web PubSub's reliable protocol is a concrete provider example of this pattern: connection identifiers, reconnection tokens, acknowledgement IDs and sequence acknowledgements are used to recover logical connection/message state after a network interruption.

## 9.1 Verified financial-services WebSocket examples

These are provider-authored WebSocket API specifications or samples. They describe consumer-facing behavior; they do **not** establish how a provider's internal WAF, load balancer, or cross-site connection failover works.

| Provider and verified WebSocket evidence | Documented recovery behavior | Requirement illustrated |
|---|---|---|
| **Coinbase Exchange:** [WebSocket feed overview](https://docs.cdp.coinbase.com/exchange/websocket-feed/overview) gives `wss://` endpoints, subscribe messages, per-product sequence numbers and a heartbeat channel. | A sequence gap can arise upstream despite TCP delivery to the client; consumers detect gaps/out-of-order updates or select a delivery-guaranteed channel such as `level2`. | **WS-006/007/008:** restore subscriptions, check completeness with sequence numbers, monitor stream health. |
| **Coinbase Prime:** [market-data guide](https://docs.cdp.coinbase.com/prime/concepts/trading/market-data) explicitly identifies its WebSocket `l2_data` stream. | It instructs clients to reconnect for a fresh order-book snapshot on a sequence gap and to reconnect if subscribed heartbeats stop. | **WS-001/007/008:** reconnect after a dead path, reject an incomplete book, rebuild from an authoritative snapshot. This is snapshot recovery, not a promise of message replay. |
| **LSEG/Refinitiv:** [WebSocket API](https://developers.lseg.com/en/api-catalog/real-time-opnsrc/websocket-api) and its [official Java RTO example](https://github.com/Refinitiv/websocket-api/blob/master/Applications/Examples/RTO/java/MarketPriceRTOClientCredAuth/src/main/java/org/example/MarketPriceRTOClientCredAuth.java) use WebSocket connections to discovered real-time endpoints. | The example illustrates endpoint discovery, optional dual hot-standby connections, login, token renewal and reconnect. LSEG explicitly warns that its examples are illustrative and that production applications must implement **item and connection recovery** themselves. | **WS-001/004/006/007:** rediscover, authenticate, restore item requests and validate state after reconnect; do not treat sample code as a production retry policy. |
| **Alpaca:** [trading WebSocket stream](https://docs.alpaca.markets/us/docs/websocket-streaming) documents `wss://` endpoints, authentication, `trade_updates` subscriptions and order lifecycle events. Its [order lookup by client order ID](https://docs.alpaca.markets/us/reference/getorderbyclientorderid) is an HTTP recovery path. | Following an ambiguous disconnect, restore the subscription and query authoritative order state by `client_order_id` before deciding whether an order needs further action. The cited WebSocket page does not promise gap-free replay. | **WS-006/007/007A:** restore subscriptions and reconcile orders and fills; an order ID enables lookup but does not itself prove retry idempotency. |
| **Interactive Brokers:** [Web API WebSocket topics](https://ibkrcampus.com/docs/web-api/v1/ws/introduction) explicitly list market data (`smd`), order updates (`sor`) and trades (`str`) and require an active brokerage session for these topics. | Re-establish the brokerage session and relevant subscriptions after a dropped connection; consult authoritative order/trade endpoints to reconcile a gap. These latter steps are design inferences, not a documented IBKR replay guarantee. | **WS-004/006/007:** session validity, topic recovery and authoritative reconciliation. |
| **CME Group:** [Real-Time Futures & Options Data API](https://www.cmegroup.com/market-data/market-data-api.html) explicitly identifies a WebSocket API carrying JSON market data. | The public product description establishes protocol use, but does not specify cursor replay, missed-message guarantees or failover behavior. | **Evidence boundary:** define and test those guarantees in the application contract; WebSocket adoption alone does not supply them. |

**Nasdaq qualification:** [Nasdaq's hackathon repository](https://github.com/Nasdaq/hackathons) contains an explicit WebSocket client example, but it is a hackathon demo using an unencrypted `ws://` sample endpoint and is **not** evidence of a production architecture or recovery guarantee. Nasdaq's [Data Link Streaming API Java SDK](https://github.com/Nasdaq/NasdaqCloudDataService-SDK-Java) documents Kafka configuration (`bootstrap.servers` on port 9094), so that product should not be cited as a WebSocket example. Do not use the hackathon endpoint in an enterprise reference architecture.

**Design implication:** Market-data views may be rebuilt from a fresh snapshot after a gap (Coinbase Prime). Order submissions, fills, cancellations and balances need reconciliation against authoritative business state before any retry (Alpaca/IBKR). Specify separately for each stream whether replay exists, how long it lasts, the scope of its sequence or cursor, and the result when recovery is impossible.

---

# 10. Connection draining for planned maintenance

Planned infrastructure work should not be handled as an abrupt failure.

For a load-balanced WAF tier:

~~~text
Before maintenance

          +--> WAF-1
LTM ------+
          +--> WAF-2


Drain WAF-1

existing sockets ----------> WAF-1
new connections -----------> WAF-2


After drain window

WAF-1 -> maintenance
WAF-2 -> all new service
~~~

The same model applies to:

- WAF patching;
- LTM/backend maintenance where supported;
- platform ELB backend removal;
- ingress-controller replacement;
- Pod rolling deployment;
- VM replacement.

Cloud-provider documentation demonstrates this pattern:

- AWS ALB target deregistration delay;
- Azure Application Gateway connection draining, explicitly including WebSocket;
- Google Cloud connection draining.

A WebSocket can be held much longer than a normal HTTP request, so the selected drain time needs to reflect actual application connection duration and operational goals.

Do not assume a one-hour drain means every connection must remain connected for one hour. It means the infrastructure gives existing connections a window to finish gracefully.

---

# 11. Kubernetes termination and WebSocket draining

For Kubernetes applications, planned Pod termination should combine Kubernetes lifecycle controls with ingress/load-balancer draining.

Kubernetes documents that:

- terminating Pod endpoints are marked as terminating;
- terminating endpoints have ready=false for compatibility;
- consumers can use serving/terminating state to support connection draining;
- Pods can use PreStop;
- terminationGracePeriodSeconds controls the total graceful shutdown window.

Recommended design:

~~~text
deployment removes Pod
        |
endpoint becomes terminating/not-ready
        |
new connections stop
        |
application begins graceful shutdown
        |
existing sockets drain or receive controlled close
        |
grace period expires
        |
Pod exits
~~~

**References:**

- Kubernetes, Pod Lifecycle  
  https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/
- Kubernetes, EndpointSlices  
  https://kubernetes.io/docs/concepts/services-networking/endpoint-slices/
- Kubernetes, Container Lifecycle Hooks  
  https://kubernetes.io/docs/concepts/containers/container-lifecycle-hooks

The exact WebSocket drain behavior still depends on the chosen Kubernetes ingress/load-balancer implementation and must be verified against that controller's documentation.

---

# 12. Heartbeats and dead-path detection

A path can fail without immediately delivering a clean TCP close to the application.

The WebSocket/application should therefore use heartbeat/keepalive behavior appropriate to the application.

Conceptually:

~~~text
client                  server

      ping / heartbeat
-------------------------->

      pong / response
<--------------------------

      ping
-------------------------->
          X

heartbeat threshold exceeded
          |
      reconnect
~~~

In browsers, the native WebSocket API does not expose protocol Ping/Pong frames to JavaScript; browser applications can use an application-level heartbeat or message deadline, while the server may use protocol Ping/Pong. Coordinate the chosen mechanism with mobile/browser suspension behavior so a suspended client reconnects on resume.

The heartbeat policy should be coordinated with infrastructure idle timeouts.

A practical requirement is:

> **A healthy WebSocket should generate activity more frequently than the shortest intended idle timeout in the end-to-end proxy path, unless the relevant infrastructure is explicitly configured for a longer idle connection.**

The complete timeout chain should be documented:

~~~text
client
  |
LTM
  |
WAF
  |
platform ELB
  |
Kubernetes ingress / VM LB
  |
application
~~~

---

# 13. Site failover

GTM/DNS can steer a **new** connection to another site. It cannot migrate an existing WebSocket.

Normal state:

~~~text
Client ================= Site A WebSocket
~~~

Site A fails:

~~~text
Client ================X Site A
          |
          | detect loss
          | reconnect with jitter
          v
      DNS / GTM
          |
          v
        Site B
          |
     new WebSocket
~~~

Requirements for useful Site-B recovery include:

- Site B has enough connection-creation/TLS capacity;
- WAF capacity can accept the reconnect surge;
- authentication services remain available;
- application state is accessible/replicated as required;
- subscriptions can be recreated;
- critical messages can be reconciled/replayed where necessary.

DNS TTL alone does not define recovery time. Client DNS caching, resolver caching, existing connection behavior and application reconnect policy also affect the result.

---

# 14. Reconnect storms / thundering herd

A full-site failure can create a new availability problem.

Example:

~~~text
100,000 active clients
          |
      Site A fails
          |
100,000 simultaneous reconnect attempts
          |
      Site B overload
~~~

Countermeasures:

1. exponential backoff;
2. random jitter;
3. bounded retry rate;
4. server-side connection-rate limiting where appropriate;
5. sufficient TLS handshake capacity;
6. sufficient WAF new-connection capacity;
7. sufficient authentication capacity;
8. sufficient ingress and application scale;
9. pre-warmed passive-site capacity where failover RTO requires it.

Capacity testing must therefore measure both:

- **steady-state concurrent WebSockets**, and
- **new WebSocket connections per second during recovery**.

---

# 15. Failure scenarios and expected WebSocket impact

This concise table applies to both topologies. For node-versus-entire-pair failures, the two site firewall HA pairs, client DNS/circuits, DCS/HCS backends, application ELB L3/L4 versus L7 behavior and proposed recovery-time bands, use the [complete two-design failure analysis](./waf_architecture_options_cross_site_resilience.md#16a-end-to-end-failure-analysis-for-designs-a-and-b). Design A has no ingress LTM; its WAF HA cluster owns the external VIP. Design B has an LTM HA external VIP and independent WAF members.

| Failure | Existing HTTP | Existing WebSocket | Recovery / mitigation |
|---|---|---|---|
| Browser tab/device sleeps, restarts or changes network | Requests resume when client returns | Socket may close or silently stall | Detect on resume/heartbeat; reconnect, restore credentials/cursor or fetch snapshot |
| Client-side proxy or local firewall fails | New requests may fail until path recovers | Socket may reset or blackhole | Alternate permitted client path; heartbeat and retry with jitter |
| Stateful enterprise firewall fails over or ages a session | In-flight requests may fail | Socket may reset, stall or survive depending on state sync, NAT and path | HA/state sync where supported; verify idle timers, symmetric routing and reconnect |
| One private circuit or VPN tunnel drops | In-flight requests may fail | Existing socket may fail even if another route exists | Route convergence/reachable alternate VIP, re-resolution and reconnect |
| One load-balanced WAF fails abruptly | Some in-flight requests may fail | Sockets through that WAF should be assumed lost | LTM withdraws member; clients reconnect to healthy WAF |
| One WAF is drained for maintenance | New requests use other WAF | Existing sockets may remain through drain window | Disable/drain before maintenance |
| Mirrored active WAF fails | New traffic handled by standby | Connection may survive supported first failover | F5 mirroring plus client reconnect fallback |
| Mirrored WAF fails back | New traffic continues | F5 documents reset limitation on failback | Drain/plan failback; do not rely on transparency |
| LTM active member fails | Some flows may reset | Depends on LTM mirroring/configuration | HA LTM plus client reconnect |
| One physical circuit fails | Routing may converge | Existing flow may survive or may break depending on path/state | Diverse circuits; verify with live-socket testing |
| All ingress circuits to active site fail | New requests fail until alternate path/site selected | Active-site sockets fail | GTM/site failover plus reconnect |
| Platform ELB member/process fails | In-flight request may fail | Sockets on failed path may fail | ELB HA plus reconnect |
| Kubernetes ingress instance fails | Some connections affected | Connections through failed ingress may fail | Multiple ingress replicas plus reconnect |
| Pod becomes unready | New traffic avoids Pod | Existing socket behavior depends on ingress/controller | Readiness plus drain |
| Pod gracefully terminates | New traffic moves | Existing socket can be drained/closed cleanly | PreStop, termination grace, ingress drain |
| Pod crashes | Current request fails | Socket is lost | Replicas plus reconnect and external state |
| Kubernetes node fails | Workloads reschedule | Sockets terminating on node are lost | Multi-node replicas plus reconnect |
| VM app process fails | Request may retry | Socket is lost | VM pool redundancy plus reconnect |
| Backend LB fails | New flow uses HA peer if available | Existing flows may reset unless preserved by that LB implementation | LB HA plus reconnect |
| Full Site A failure | GTM can direct new sessions to Site B | All Site-A WebSockets are lost | Site-B reconnect, shared state, capacity for reconnection surge |
| GTM/DNS node failure while DNS service remains redundant | Usually none | Existing WebSockets unaffected | Redundant GTM/DNS |
| GTM changes DNS answer | New sessions use selected site | Existing WebSocket unchanged | Reconnect uses new resolution when needed |
| WAF policy/config mismatch | Requests can be treated differently by nodes | Reconnected socket may be treated differently | Automated/synchronized WAF policy deployment |
| Session store unavailable | New HTTP login/session may fail | Reconnect may fail to restore logical session | HA session/state service |
| Authentication service unavailable during failover | Existing session might continue | New reconnect may fail authentication | HA auth service; token design; controlled retry |
| Reconnect storm | New HTTP/TLS load spikes | Large connection-establishment spike | Backoff+jitter and failover capacity |
| Message sent at instant of failure | Transaction outcome can be ambiguous | Message may be lost/duplicated around reconnect | IDs, ack, idempotency and replay |

---

# 16. Architecture decision: clustered WAF versus load-balanced WAF

## Option A - WAF active/standby cluster owning external VIP

~~~text
Client -> site firewall HA -> external VIP on WAF active <====> WAF standby
                                              |
                                     application ELB internal VIP
                                              |
                                     DCS/HCS VM or HCS Kubernetes
~~~

Connection mirroring is optional and conditional on the supported F5 version, profiles, license and tested topology. This design has **no ingress LTM**. Loss of both WAF members removes the external VIP; remote WAF capacity requires an explicitly engineered alternate ingress or other-site VIP.

### Advantages

- best opportunity to preserve a connection through a single supported WAF failover;
- tightly integrated HA model;
- useful where reconnect is operationally difficult.

### Disadvantages

- standby capacity is less efficiently used;
- connection-mirroring complexity;
- current F5 limitations on failback and sequential failovers;
- does not solve backend, network or site failure;
- application still needs recovery.

## Option B - LTM-balanced active WAF pool

~~~text
                                    +--> WAF-1 --+
Client -> site firewall -> LTM HA --+            +--> ELB internal VIP --> DCS/HCS app
                                    +--> WAF-2 --+
~~~

The LTM HA pair owns the external VIP. Its pool monitors must withdraw a broken WAF or WAF-to-ELB path. Loss of the complete LTM pair removes ingress even when both WAFs are healthy; loss of the complete WAF pool makes the application unavailable unless a separately approved remote WAF path exists.

### Advantages

- both WAFs contribute production capacity;
- simple horizontal scaling;
- easy member drain/maintenance;
- one failed WAF is a pool-member failure rather than loss of the logical WAF service;
- aligns closely with managed-cloud service patterns;
- WAF policy can be synchronized separately from dataplane state.

### Disadvantages

- active sockets through an abruptly failed WAF require reconnect;
- reconnect behavior becomes an application requirement;
- session/message recovery must be designed.

## Recommended decision rule

Use **load-balanced active WAFs** as the preferred general architecture when the extra ingress LTM tier, through-path health, capacity, policy consistency and applications' WebSocket recovery are justified and verified. Design A remains a valid simpler ingress design when the cluster failure domain and single-event mirroring limitations are acceptable. See the [comparison and failure-time model](./waf_architecture_options_cross_site_resilience.md#16a-end-to-end-failure-analysis-for-designs-a-and-b).

Use **connection mirroring** where a documented business/technical requirement justifies the extra complexity and testing.

In both cases, keep client reconnect as the final recovery mechanism.

---

# 17. Minimum application requirements for resilient WebSockets

The following should be treated as architecture requirements rather than optional enhancements.

## WS-001 - Automatic reconnect

Clients shall automatically reconnect after unexpected socket loss.

## WS-002 - Bounded retry

Reconnect shall use bounded retry behavior and shall not retry infinitely at a high fixed rate.

## WS-003 - Jitter

Reconnect delays shall include random jitter to reduce synchronized reconnect storms.

## WS-004 - Portable authentication

A reconnect to another WAF/application instance shall be able to authenticate without relying on state held only on the failed instance.

## WS-005 - Portable logical session

Where the application requires session continuity, logical session state shall not depend exclusively on one WAF, ELB, ingress controller, Pod or VM.

## WS-006 - Subscription recovery

Applications using topic/channel/subscription state shall either recreate subscriptions after reconnect or retain that state in a recoverable service.

## WS-007 - Message recovery

Where lost/duplicated messages create material business impact, messages shall have stable IDs, bounded durable retention, acknowledged processing position, duplicate detection and a replay or snapshot recovery path appropriate to the application. The replay gap and cross-site consistency behavior shall be documented.

## WS-007A - Idempotent client commands

Every retryable operation that changes business state shall carry an operation ID/idempotency key. The server shall durably deduplicate within the agreed scope/window and return or reconcile the original result when the first acknowledgement was lost.

## WS-008 - Heartbeat

The application shall detect stale/dead connections within the required recovery objective.

## WS-009 - Graceful close

Planned application shutdown should use an orderly WebSocket close where practical rather than simply killing the TCP connection.

## WS-010 - Drain support

Infrastructure and application deployment procedures shall drain long-lived connections during planned maintenance where supported.

## WS-011 - Full-stack recovery and business state

Application recovery shall be tested after client/DNS/firewall, circuit, full WAF HA pair or WAF pool, full LTM HA pair (Design B), application ELB L3/L4 or L7, DCS VM/cluster, HCS VM/cluster, Kubernetes ingress/Pod/node/cluster and full-site failures. HTTP clients must distinguish safe retries from ambiguous writes and use authoritative result lookup. WebSocket clients must not infer message delivery or order outcome from a successful reconnect. Measure the recovery-time components and proposed acceptance bands in [Section 16A of the main paper](./waf_architecture_options_cross_site_resilience.md#16a-end-to-end-failure-analysis-for-designs-a-and-b).

---

# 18. Minimum infrastructure requirements

## INF-001 - WAF WebSocket awareness

The WAF must explicitly support WebSocket handshake and message enforcement as required by policy.

F5 documents allowed WebSocket URLs and text/JSON content-profile enforcement.

**Reference:**  
F5, Securing Applications That Use WebSocket  
https://techdocs.f5.com/kb/en-us/products/big-ip_asm/manuals/product/asm-implementations-12-1-0/28.html

## INF-002 - Consistent WAF policy

All WAF nodes serving the same application must have consistent policy/configuration.

## INF-003 - Application-aware monitoring

Health monitoring should test meaningful application readiness where possible, not only TCP port availability.

## INF-004 - Planned draining

Operational procedures shall remove a WAF/ELB/ingress/backend from new-connection selection before planned shutdown.

## INF-005 - Timeout register

Maintain a documented table of:

- client-side proxy and firewall session timeouts;
- enterprise firewall TCP idle timeout and maximum session age;
- private circuit/VPN recovery and route convergence;
- LTM TCP idle timeout (Design B only);
- WAF WebSocket/TCP timeout;
- platform ELB timeout;
- ingress-controller timeout;
- backend LB timeout;
- application heartbeat interval.

## INF-006 - Recovery capacity

The passive site and shared services must support the expected new-connection rate after a failover.

## INF-007 - Failure-domain isolation

Failure of one Pod, one application target or one WAF should not automatically trigger site failover if healthy capacity remains locally.

## INF-008 - Observability

Capture:

- concurrent WebSockets;
- client-side network/offline and heartbeat timeout events where observable;
- firewall failover, session expiration and circuit/path changes;
- connection establishment rate;
- abnormal disconnects;
- reconnect attempts;
- reconnect success rate;
- authentication failures during reconnect;
- WAF-node connection counts;
- message replay/duplicate counts where applicable.

## INF-009 - Application ELB mode and backend failure domains

Document whether the on-premises ELB forwards at L3/L4 with a selected TCP flow or terminates at L7 and creates a new HTTP/TLS/backend connection. Pure L3 IP routing alone is not application load balancing. Validate TLS/mTLS termination and re-encryption, original-client trust, NAT and return symmetry, health, WebSocket upgrade, idle/maximum connection age and draining. DCS VMware VMs, HCS VMs and HCS Kubernetes ingress/Services/Pods must be monitored and failed independently; losing an ELB, ingress, VM or Pod can still destroy an established socket. See the [mode-specific failure rows](./waf_architecture_options_cross_site_resilience.md#16a3-ingress-waf-and-application-elb).

---

# 19. Testing plan

Production acceptance should test with real long-lived WebSockets, not only HTTP health checks.

Minimum tests:

1. put a browser/device to sleep, resume it, restart it and switch its client network;
2. silently blackhole a client path and then restore it;
3. fail over each stateful firewall pair, including NAT and return-path validation;
4. expire a firewall/enterprise-proxy session while a WebSocket is quiet;
5. gracefully drain WAF-1;
6. abruptly stop WAF-1;
7. fail active WAF in mirrored HA mode, if used;
8. fail back the mirrored WAF pair, if used;
9. fail active LTM;
10. disconnect each of the four circuits individually;
11. test relevant correlated two-circuit failures;
12. fail platform ELB component/path;
13. restart an ingress-controller instance;
14. gracefully terminate a Pod;
15. abruptly kill a Pod;
16. fail a Kubernetes node;
17. perform a rolling Kubernetes deployment;
18. terminate a VM application process;
19. fail the backend VM load balancer;
20. isolate the active site;
21. verify GTM directs a new connection to the passive site;
22. restore the active site without unnecessarily moving existing Site-B sessions back;
23. verify heartbeat/dead-path detection;
24. verify reconnect backoff/jitter;
25. simulate a large reconnect surge;
26. verify authentication under reconnect load;
27. verify subscription restoration;
28. verify message replay/duplicate handling where required;
29. drop the server's acknowledgement after committing a client command, then retry with the same idempotency key;
30. reconnect with a cursor older than replay retention and verify snapshot reconciliation;
31. repeat relevant tests with identity, session and event services failed or degraded at the passive site.

Capture separately:

| Measurement | Required |
|---|---|
| HTTP request impact | Yes |
| WebSocket disconnect count | Yes |
| Time to detect connection loss | Yes |
| Time to successful reconnect | Yes |
| Authentication success after reconnect | Yes |
| Logical session restored | Yes |
| Subscriptions restored | If applicable |
| Messages lost | If applicable |
| Messages duplicated | If applicable |
| Peak reconnects/second | Yes |
| WAF CPU/connection usage | Yes |
| ELB/ingress/application load | Yes |

---

# 20. Recommended enterprise statement

The following wording can be used as an architecture requirement:

> Loss of a WAF, load-balancer, application instance, network path or site may terminate an established WebSocket connection. Clients shall automatically detect connection loss and establish a new connection through available infrastructure. Application session state shall not depend solely on a specific WAF, load-balancer, Pod or VM. Planned infrastructure maintenance shall use connection draining where supported. Where message delivery is business-critical, the application shall implement durable event IDs, a bounded replay or snapshot path and idempotent retry of client commands sufficient to reconcile messages and business effects after reconnection. Client failures, firewall/session-table failover and private-network path loss are included in the recovery scope. Connection mirroring may be used as an additional availability control but shall not replace application reconnect capability.

---

# 21. Design conclusion for EnterpriseWAF

For this environment, the strategic design for applications that require WebSocket is **Design B where its extra tier is justified and validated**; otherwise Design A uses a WAF cluster VIP without ingress LTM. The Design B path is:

~~~text
GTM
 |
LTM HA
 |
+---------------------+
|                     |
WAF-1               WAF-2
active              active
|                     |
+----------+----------+
           |
          ELB
           |
 Kubernetes / VM application tier
           |
 recoverable logical session/event state
~~~

with:

- synchronized WAF policy;
- WebSocket-aware WAF configuration;
- member draining for maintenance;
- automatic client reconnect;
- retry backoff with jitter;
- heartbeat/dead-path detection;
- portable application/session state;
- message acknowledgement/replay where required;
- capacity testing for failover reconnect storms;
- explicit failure testing of all stateful tiers.

Use Design A where its simpler ingress and HA operational model fit the requirements. Enable connection mirroring only where preserving a socket across a supported single WAF failover has enough value to justify its documented limitations and exact-version tests. Both designs require client reconnection and business-state recovery.

---

# 22. References

## Standards

1. RFC 6455 - The WebSocket Protocol  
   https://www.rfc-editor.org/info/rfc6455/

## F5

2. F5 - Automatically Synchronizing Application Security Configurations  
   https://techdocs.f5.com/en-us/bigip-17-5-0/big-ip-asm-implementations/automatically-synchronizing-application-security-configurations.html

3. F5 - Connection Mirroring with ASM  
   https://techdocs.f5.com/en-us/bigip-14-1-0/big-ip-asm-implementations-14-1-0/connection-mirroring-with-asm.html

4. F5 - Connection mirroring limitations with ASM  
   https://techdocs.f5.com/en-us/bigip-17-0-0/big-ip-asm-implementations/connection-mirroring-with-asm/connection-mirroring-limitations.html

5. F5 - Securing Applications That Use WebSocket  
   https://techdocs.f5.com/kb/en-us/products/big-ip_asm/manuals/product/asm-implementations-12-1-0/28.html

## AWS

6. AWS - Listeners for Application Load Balancers / WebSockets  
   https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-listeners.html

7. AWS - Application Load Balancer Target Group Attributes  
   https://docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-target-group-attributes.html

8. AWS - Register targets / Connection draining  
   https://docs.aws.amazon.com/elasticloadbalancing/latest/application/target-group-register-targets.html

9. AWS - Retry behavior / Full jitter  
   https://docs.aws.amazon.com/sdkref/latest/guide/feature-retry-behavior.html

10. AWS Well-Architected - Control and limit retry calls  
    https://docs.aws.amazon.com/wellarchitected/2022-03-31/framework/rel_mitigate_interaction_failure_limit_retries.html

## Microsoft Azure

11. Microsoft - Azure Application Gateway Features  
    https://learn.microsoft.com/en-us/azure/application-gateway/features

12. Microsoft - Application Gateway Backend Settings / Connection draining  
    https://learn.microsoft.com/en-us/azure/application-gateway/configuration-http-settings

13. Microsoft - Azure Web PubSub Reliable WebSocket subprotocol  
    https://learn.microsoft.com/en-us/azure/azure-web-pubsub/reference-json-reliable-webpubsub-subprotocol

14. Microsoft - Reliability in Azure Web PubSub Service  
    https://learn.microsoft.com/en-us/azure/reliability/reliability-web-pubsub

## Google Cloud

15. Google Cloud - Application Load Balancer request distribution / WebSocket behavior  
    https://docs.cloud.google.com/load-balancing/docs/https/request-distribution

16. Google Cloud - Connection draining  
    https://docs.cloud.google.com/load-balancing/docs/enabling-connection-draining

17. Google Cloud - Internal passthrough Network Load Balancer traffic distribution  
    https://docs.cloud.google.com/load-balancing/docs/internal/int-netlb-traffic-distribution

## Kubernetes

18. Kubernetes - Pod Lifecycle  
    https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/

19. Kubernetes - EndpointSlices  
    https://kubernetes.io/docs/concepts/services-networking/endpoint-slices/

20. Kubernetes - Container Lifecycle Hooks  
    https://kubernetes.io/docs/concepts/containers/container-lifecycle-hooks/

---

# Appendix A. Alternative target state: HTTPS APIs plus Server-Sent Events

## A.1 Decision and scope

Use ordinary HTTPS APIs for client → server operations and consider **Server-Sent Events (SSE)** for server → browser updates when one-way streaming meets the product's latency and interaction needs. Keep WebSocket for genuine continuous bidirectional use (for example, collaborative editing or interactive terminal control). Polling remains a sound option when a few seconds of delay are acceptable and the expected request load is manageable.

| Application need | Candidate | Operational consequence |
|---|---|---|
| Normal reads and commands | HTTPS API | Finite requests; design ambiguous write retries using idempotency keys. |
| Periodic status with modest latency | HTTPS polling with cursor/ETag | Simple connection recovery; size polling interval and fleet load. |
| Near-real-time server → browser events | HTTPS API + SSE | One long-lived HTTP response per stream; native browser EventSource reconnects, while the server must implement event retention/replay. |
| Continuous bidirectional low-latency exchange | WebSocket | Application owns reconnect, resubscription, message recovery and deduplication. |

This is an **alternative application target state**, not a change to the two-site ingress/WAF design. The same GTM, client circuits, firewalls, LTM, WAF, ELB, ingress and application failure domains still apply to an open SSE response.

## A.2 Reference request path

~~~text
Browser HTTPS POST/GET --------> GTM -> site VIP -> firewall -> LTM -> WAF
Browser HTTPS GET /events ----->                         |
                                                       ELB
                                                        |
                                                Kubernetes or VM app
                                                        |
                                           durable event store / snapshot
~~~

A server emits a response with `Content-Type: text/event-stream`, for example:

~~~text
id: order-92834
event: order-status
data: {"orderId":1234,"status":"approved"}

: heartbeat

~~~

On a lost stream, a browser `EventSource` normally retries. For an event stream that supplies `id:` fields, it sends the last event ID on reconnection as `Last-Event-ID`; the application must interpret the cursor and provide missed events. Automatic reconnect **does not** create a durable event log, guarantee delivery, preserve state across browser restart, or make duplicate processing safe.

Example flow: client has safely processed event 92833 → firewall state is lost → stream stalls or closes → client detects loss/reconnects (respecting backoff) → GTM/new route selects a healthy path → server validates identity and the cursor → server replays available events 92834 onward → client deduplicates and continues. If replay retention has elapsed or the site cannot serve a consistent cursor, return an explicit recovery signal and load an authoritative snapshot before resuming live events.

## A.3 Reliability and security requirements

- **HTTP intermediaries:** Test the WAF, client proxy, firewall, LTM, ELB and ingress for streaming support, response buffering/compression, request/response timeouts, idle timeouts and maximum stream duration. Keepalives (SSE comments are valid) should occur sooner than the shortest applicable idle timeout; heartbeat monitoring also detects silent stalls. Inspect the authentication request and apply appropriate WAF controls, but validate the actual product's treatment of a long-lived response; HTTP framing alone does not guarantee deep inspection of every event.
- **Authentication:** Authorize both the event stream and every write API. Native `EventSource` does not provide a general custom-request-header interface; for browser use, same-origin cookies or an approved credential flow are common, with CSRF protections for cookie-authenticated writes. Short-lived tokens, renewal and reauthorization after reconnect need an explicit design; do not put reusable bearer secrets in event-stream URLs.
- **Replay:** Use stable event IDs/cursors, a durable event store shared or replicated according to the site-failover recovery objective, bounded retention, access-controlled replay and snapshot fallback. Check cursor scope per tenant/user and avoid disclosing another subscriber's events. Define ordering per stream or partition, duplicate handling, and what happens during a replication lag or partition.
- **Writes and acknowledgements:** Commands remain normal HTTPS operations. If a connection fails after commit but before the response arrives, retry with the same operation key and return/reconcile the committed result. SSE updates do not replace write acknowledgement.
- **Capacity:** Size open SSE connections, file descriptors, memory and egress, plus reconnections per second. Test connection limits (especially browser HTTP/1.1 per-origin limits), HTTP/2 behavior where used, slow consumers, proxy buffers and the passive site's event/identity capacity.
- **Operational acceptance:** Inject browser sleep/network switch, firewall failover, silent path loss, WAF/ELB/ingress failure, Pod/VM restart and full site failover. Measure time to live updates, missed/duplicate events, stale-cursor recovery and load under mass reconnect.

For the enterprise workflow examples in scope—approvals, job progress, notifications and dashboard updates—pilot HTTPS APIs plus SSE first where updates are predominantly server → browser. Decide per application based on actual bidirectional requirements and a tested end-to-end streaming path.

**Primary references:**

- WHATWG HTML Standard, Server-sent events (connection processing, retry, IDs and `Last-Event-ID`): https://html.spec.whatwg.org/multipage/server-sent-events.html
- MDN, Using server-sent events (stream format, reconnection and browser connection limits): https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events
- Microsoft, Using Server-Sent Events with Application Gateway (backend request timeout): https://learn.microsoft.com/en-us/azure/application-gateway/use-server-sent-events
- AWS, Ensuring idempotency in API requests (retryable write pattern): https://docs.aws.amazon.com/ec2/latest/devguide/ec2-api-idempotency.html
