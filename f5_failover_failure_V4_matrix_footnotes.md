# F5 GTM/LTM/WAF Dual-Site Failure Matrix and Private DNS Considerations

This version uses a consistent reference style: inline bracketed references such as [^1] and [^5], with a clickable source table in the appendix.

## Overview

This design assumes a private dual-site B2B deployment across leased lines or VPNs, with a 2-node GTM cluster plus 1 standalone GTM in each site, a 2-node LTM cluster plus 1 standalone LTM in each site, and a 2-node WAF cluster plus 1 standalone WAF in each site. At the logical service layer, each clustered pair is presented as a **single service IP**, so the exposed design has four GTM service IPs in total, two LTM service IPs per site, and two WAF service IPs per site. An ALB exists in each site, and the application sits behind the ALB. [^1][^4][^5]

The timing assumptions use common defaults unless they are overridden in implementation: GTM BIG-IP monitor interval 30 seconds and timeout 90 seconds, LTM HTTP/HTTPS monitor interval 5 seconds and timeout 16 seconds, and ALB target-group health checks with a 30-second interval, 2 failed checks to mark a target unhealthy, and 5 successful checks to return a target to healthy state. [^1][^2][^3]

## Interpretation rules

- Detection delay = time until the relevant monitoring layer marks the object or path unhealthy.
- Failover time = time until new requests are expected to use an alternate healthy path.
- Failover SLA = planning target for user-visible redirection under the assumed defaults.
- For a **single node failure inside a healthy cluster**, the expected impact to new requests is normally none, because the cluster service IP should remain available through the surviving member. In-flight connections already anchored to the failed member may still see a reset or retry condition. [^1][^2]
- For application-path failures, failover quality depends on whether the monitor is a true end-to-end HTTP/HTTPS check with response validation, rather than only a TCP or TLS reachability test. [^2][^3]
- GTM behavior also depends on all GTM devices converging on the same current view of healthy service IPs, pools, and sites. If GTM state is inconsistent, different GTM service IPs may return different answers until convergence completes. [^1][^5]

## Updated solution

The recommended model is to keep **corporate recursive DNS** as the client-facing resolver layer and to delegate or conditionally forward only the application zones to GTM. GTM remains authoritative for the delegated application namespace, while corporate DNS handles the rest of the internal namespace and client-specific split-DNS behavior. [^4][^6][^7][^8]

The four GTM service IPs represent the application-resolution logic, not six separate client-visible DNS personalities. Two GTM service IPs prefer Site A and two prefer Site B. Each GTM service IP resolves to one of the LTM service IPs in the preferred site, and each LTM service IP selects one of the WAF service IPs in the same site before forwarding to the local ALB and then the application. [^1][^4][^5]

If the application is active/passive, GTM will usually prefer the Site A service IPs until Site A is judged unavailable or administratively lowered in preference. If the application is active/active, GTM may legitimately return both Site A and Site B answers at the same time, which changes the user experience because failover can look more like traffic rebalance than binary site cutover. [^1][^5]

## Topology diagram

```mermaid
flowchart LR
    C[Windows / Linux / macOS Client]
    R[Corporate Recursive DNS]

    subgraph GSLB[Delegated / Forwarded App Zone on GTM]
        G1[GTM Service IP P1\nSite A preference]
        G2[GTM Service IP P2\nSite A preference]
        G3[GTM Service IP S1\nSite B preference]
        G4[GTM Service IP S2\nSite B preference]
    end

    subgraph A[Site A - Primary]
        direction TB
        subgraph AG[GTM nodes]
            A_G1[GTM-A1]
            A_G2[GTM-A2]
            A_G3[GTM-A3 single]
        end
        subgraph ALSVC[Site A LTM service IPs]
            A_LC[LTM Cluster Service IP A-C]
            A_LS[LTM Single Service IP A-S]
        end
        subgraph ALN[Site A LTM nodes]
            A_L1[LTM-A1]
            A_L2[LTM-A2]
            A_L3[LTM-A3 single]
        end
        subgraph AWSVC[Site A WAF service IPs]
            A_WC[WAF Cluster Service IP A-C]
            A_WS[WAF Single Service IP A-S]
        end
        subgraph AWN[Site A WAF nodes]
            A_W1[WAF-A1]
            A_W2[WAF-A2]
            A_W3[WAF-A3 single]
        end
        A_ELB[ALB-A]
        A_APP[Application-A]
    end

    subgraph B[Site B - Secondary]
        direction TB
        subgraph BG[GTM nodes]
            B_G1[GTM-B1]
            B_G2[GTM-B2]
            B_G3[GTM-B3 single]
        end
        subgraph BLSVC[Site B LTM service IPs]
            B_LC[LTM Cluster Service IP B-C]
            B_LS[LTM Single Service IP B-S]
        end
        subgraph BLN[Site B LTM nodes]
            B_L1[LTM-B1]
            B_L2[LTM-B2]
            B_L3[LTM-B3 single]
        end
        subgraph BWSVC[Site B WAF service IPs]
            B_WC[WAF Cluster Service IP B-C]
            B_WS[WAF Single Service IP B-S]
        end
        subgraph BWN[Site B WAF nodes]
            B_W1[WAF-B1]
            B_W2[WAF-B2]
            B_W3[WAF-B3 single]
        end
        B_ELB[ALB-B]
        B_APP[Application-B]
    end

    C -->|Normal query| R
    R -->|Delegation or conditional forward| G1
    R -->|Delegation or conditional forward| G2
    R -->|Delegation or conditional forward| G3
    R -->|Delegation or conditional forward| G4

    G1 -->|Primary preference| A_LC
    G2 -->|Primary preference| A_LS
    G3 -->|Secondary preference| B_LC
    G4 -->|Secondary preference| B_LS

    A_LC --> A_L1
    A_LC --> A_L2
    A_LS --> A_L3
    A_L1 --> A_WC
    A_L2 --> A_WC
    A_L3 --> A_WS
    A_WC --> A_W1
    A_WC --> A_W2
    A_WS --> A_W3
    A_W1 --> A_ELB
    A_W2 --> A_ELB
    A_W3 --> A_ELB
    A_ELB --> A_APP

    B_LC --> B_L1
    B_LC --> B_L2
    B_LS --> B_L3
    B_L1 --> B_WC
    B_L2 --> B_WC
    B_L3 --> B_WS
    B_WC --> B_W1
    B_WC --> B_W2
    B_WS --> B_W3
    B_W1 --> B_ELB
    B_W2 --> B_ELB
    B_W3 --> B_ELB
    B_ELB --> B_APP
```

## Scenario numbering

```mermaid
flowchart TB
    subgraph Primary[Site A - Primary]
        S1[#1 One GTM node in Site A fails]
        S2[#2 GTM cluster service IP in Site A loses one node]
        S3[#3 GTM cluster service IP in Site A fails, single GTM service IP remains]
        S4[#4 One LTM node in Site A fails]
        S5[#5 LTM cluster service IP in Site A loses one node]
        S6[#6 LTM cluster service IP fails, single LTM service IP remains]
        S7[#7 One WAF node in Site A fails]
        S8[#8 WAF cluster service IP in Site A loses one node]
        S9[#9 WAF cluster service IP fails, single WAF service IP remains]
        S10[#10 One Site A LTM service IP fails]
        S11[#11 One Site A WAF service IP fails]
        S12[#12 ALB-A target/member failure]
        S13[#13 ALB-A or app path failure, detected end-to-end]
        S14[#14 Full Site A failure]
        S15[#15 Primary app failed, GTM returns Site B service IPs]
    end
```

## Failure matrix

| # | Failure scenario | Detection delay | Failover time for new requests | Expected user impact | User action likely required | Planning failover SLA |
|---|---|---:|---:|---|---|---:|
| 1 | One GTM node in Site A fails | Near-immediate operational event if the GTM cluster service IP or standalone GTM service IP still answers DNS. [^4][^9] | None for healthy DNS design. [^4] | Normally no impact. [^4] | None, or a retry if a resolver initially queried a failed listener path. [^6][^9] | 0-5 seconds |
| 2 | One node inside the Site A GTM cluster fails, but the GTM cluster service IP remains up | Normally no user-visible detection event because the cluster service IP still answers. [^4][^5] | None for new lookups. [^4] | Normally no impact. [^4] | None. | No user-visible failover expected |
| 3 | Site A GTM cluster service IP fails, but the Site A standalone GTM service IP remains | Depends on how corporate DNS or resolvers use the remaining authoritative service IPs. [^4][^9] | Normally none to near-immediate if the standalone GTM service IP remains reachable and authoritative. [^4][^9] | Normally no impact, but DNS redundancy is reduced. [^4][^9] | Retry only if a resolver initially chose the failed cluster service IP. [^6][^9] | 0-5 seconds |
| 4 | One LTM node in Site A fails | If the failed node is behind the clustered LTM service IP, the service IP can remain healthy through the surviving node; if the failed node is the standalone LTM, the standalone service IP is affected. [^1][^5] | None for new requests when the clustered service IP survives; otherwise GTM may take 30 seconds normally and 90 seconds worst-case to stop returning the affected standalone service IP. [^1] | Normally no impact when clustered service remains up. [^1][^2] | Retry/refresh only for flows already pinned to the failed node. [^2] | No user-visible failover for clustered-member loss; 30 seconds normal and 90 seconds worst-case for standalone service withdrawal |
| 5 | One node inside the Site A LTM cluster fails, but the LTM cluster service IP remains up | Normally no user-visible detection event because the LTM cluster service IP still accepts traffic. [^1][^2] | None for new requests. [^1][^2] | Normally no impact. [^1][^2] | None, or retry for in-flight sessions only. [^2] | No user-visible failover expected |
| 6 | The Site A LTM cluster service IP fails, and only the standalone Site A LTM service IP remains | GTM monitor defaults are 30-second interval and 90-second timeout. [^1] | New requests should continue through the standalone Site A LTM service IP after GTM withdraws the failed clustered service IP. [^1] | Normally low or no impact if the standalone service has enough capacity. [^1][^5] | Retry/refresh for in-flight sessions on the failed clustered service IP; full login only if state was not replicated. [^2] | 30 seconds normal; 90 seconds worst-case |
| 7 | One WAF node in Site A fails | If the failed node is behind the clustered WAF service IP, the clustered service IP can remain healthy through the surviving node; if it is the standalone WAF, the standalone WAF service IP is affected. [^2] | None for new requests when the clustered WAF service IP survives; otherwise LTM may need about 16 seconds to stop selecting the affected standalone WAF service IP. [^2] | Normally no impact when clustered service remains up. [^2] | Retry/refresh only for connections already on the failed WAF node. [^2] | No user-visible failover for clustered-member loss; under 16 seconds for standalone service withdrawal |
| 8 | One node inside the Site A WAF cluster fails, but the WAF cluster service IP remains up | Normally no user-visible detection event because the WAF cluster service IP still accepts traffic. [^2] | None for new requests. [^2] | Normally no impact. [^2] | None, or retry for in-flight sessions only. [^2] | No user-visible failover expected |
| 9 | The Site A WAF cluster service IP fails, and only the standalone Site A WAF service IP remains | LTM should detect the clustered WAF service IP loss in about 16 seconds. [^2] | New requests should continue through the standalone WAF service IP in Site A once LTM removes the failed clustered WAF service IP. [^2] | Normally low or no impact if the standalone WAF has enough capacity. [^2][^5] | Retry/refresh for in-flight sessions on the failed clustered WAF service IP. [^2] | Under 16 seconds |
| 10 | One Site A LTM service IP fails | If the surviving Site A LTM service IP remains healthy, GTM can keep traffic inside Site A without cross-site failover. [^1] | Normally within 30 seconds for GTM to stop preferring the failed service IP and keep using the surviving Site A LTM service IP. [^1] | Normally no impact if the remaining Site A LTM service IP has capacity. [^1][^5] | Retry/refresh only for requests directed to the failed service IP. [^2] | 30 seconds normal; 90 seconds worst-case |
| 11 | One Site A WAF service IP fails | If the surviving Site A WAF service IP remains healthy, LTM can keep service local to Site A. [^2] | Usually within about 16 seconds for LTM to stop selecting the failed service IP and use the surviving Site A WAF service IP. [^2] | Normally no impact if the remaining Site A WAF service IP has capacity. [^2][^5] | Retry/refresh only for requests already mapped to the failed WAF service IP. [^2] | Under 16 seconds |
| 12 | ALB-A target/member failure | ALB target health defaults use a 30-second interval and 2 failed checks, so unhealthy detection is about 60 seconds. [^3] | ALB removes that failed target from service in about 60 seconds while Site A remains active. [^3] | Normally no impact if other app targets remain healthy. [^3] | Usually none; at most a browser refresh if a request was in flight to the failed target. [^3] | Under 60 seconds |
| 13 | ALB-A or app path failure, detected by end-to-end F5 HTTP/HTTPS monitor | ALB target health alone would detect full target failure in about 60 seconds, while a true end-to-end F5 HTTP/HTTPS monitor can detect the broken path in about 16 seconds. [^2][^3] | About 16-46 seconds normally for Site B failover, or about 106 seconds worst-case if GTM waits for its full timeout after LTM sees the broken path. [^1][^2] | User-visible interruption during cross-site failover. [^1][^2] | Refresh/retry may be enough if sessions are shared across sites; full login is required if authentication or session state is local to Site A. [^2][^5] | 46 seconds normal; 106 seconds worst-case |
| 14 | Full Site A failure | GTM BIG-IP monitor defaults imply 30 seconds normal and 90 seconds worst-case to mark Site A down. [^1] | New requests should move to the two secondary GTM service IPs and then to Site B LTM service IPs once GTM withdraws Site A. [^1] | Short outage for fresh requests until GTM answers only with Site B service IPs. [^1] | Refresh/retry normally; full login often required if session state is not shared across sites. [^2][^5] | 30 seconds normal; 90 seconds worst-case |
| 15 | Primary application service failed and GTM returns the two Site B service IPs | With end-to-end HTTP/HTTPS monitoring, the broken application path can be detected in about 16 seconds; if detection relies only on ALB target health, it may begin around 60 seconds. [^2][^3] | About 16-46 seconds normally with end-to-end monitoring, or roughly 60-90 seconds with default-only ALB plus GTM-driven withdrawal. [^1][^2][^3] | User-visible failover unless the application is fully active-active and session-aware across sites. [^1][^5] | Refresh/retry if sessions are globally shared; full login if SSO, cookies, or session stores are site-local. [^2][^5] | 46 seconds target with end-to-end monitoring; 90 seconds conservative upper target otherwise |

## Direct client DNS behavior

The preferred model is for clients to use corporate recursive DNS and not query GTM service IPs directly. [^4][^6][^7] When clients query GTM DNS servers directly, behavior can differ by operating system, VPN client, resolver library, interface order, and local caching rules, which makes failover observations less consistent across Windows, Linux, and macOS. [^6][^7][^8]

Windows can apply namespace-specific DNS rules through the Name Resolution Policy Table, so a direct-to-GTM test from a Windows endpoint may not match the normal production path through corporate DNS. [^6] macOS uses a multi-resolver model and treats `.local` specially via mDNS, so direct resolution behavior can differ from application behavior and from tools such as `dig`. [^8] Linux behavior can vary depending on whether the system uses `systemd-resolved`, NetworkManager, or static `resolv.conf`, especially when split DNS is involved. [^7]

Direct client access to GTM can also bypass enterprise controls for delegation, forwarding, logging, recursion policy, and caching. In a private B2B design, that often creates inconsistent failover observations because some clients query a local corporate resolver while others query GTM listeners directly and receive answers based on different caches, retry timing, and reachable listener IPs. [^4][^9]

## GTM convergence and application mode

All GTM devices should converge on the same healthy set of application targets, service IPs, and site states before the platform can be considered operationally stable. [^1][^5] If one GTM service IP believes Site A is healthy while another already believes only Site B is healthy, different resolvers can receive different answers for the same name during the convergence window. [^1][^5]

This is especially important in private networks where multiple corporate DNS resolvers, leased-line latency, VPN failover, or intermittent reachability to individual GTM listeners can create different query paths. The design should validate monitor propagation, synchronization of GTM objects, and consistent health visibility from all GTM nodes before relying on any documented failover time. [^1][^4][^5]

Application operating mode also changes expected behavior. In active/passive mode, failover usually means a clearer transition from Site A answers to Site B answers after health thresholds are crossed. In active/active mode, both sites may already be in rotation and failover can look more like rebalancing than hard cutover. Site preference policy, persistence method, state replication, and whether sessions are portable across sites can therefore affect real user experience and observed failover time even when monitor timers are unchanged. [^1][^2][^5]

## Six GTM DNS servers

Using six DNS-capable GTM nodes across the two sites is not automatically a problem, because DNS zones are expected to have at least two authoritative name servers and more can be used. [^9] In this design, the six GTM nodes are the authoritative DNS platform behind a corporate recursive DNS tier, while the **four GTM service IPs** represent the client-visible application-resolution logic. [^4][^9]

The main risk with six GTM DNS nodes is operational consistency rather than protocol correctness. Every delegated or forwarded path must stay synchronized, all six nodes must answer authoritatively for the zone, and none of the advertised NS records should become lame delegations. [^4][^9]

## Login versus retry guidance

These scenarios normally need only a browser refresh, retry, or no action at all, provided the application session is not tied to the failed node: #1, #2, #3, #4 for clustered-member loss, #5, #7 for clustered-member loss, #8, #9, #10, #11, and #12. These are cases where a healthy peer node, service IP, or app target remains available in the same layer or site. [^1][^2][^3]

These scenarios may require a full HTTP login: #6, #13, #14, and #15, because they commonly result in a site change or a restart of the end-to-end transaction path. Whether a full login is truly required depends on shared session storage, replicated authentication state, common cookie domain, cross-site persistence, and whether Site B can honor the same authenticated session as Site A. [^2][^5]

## Practical validation notes

- For single-node failures behind clustered GTM, LTM, or WAF service IPs, the design expectation should be **no user-visible impact for new requests** if the clustered service IP remains healthy and capacity is sufficient. [^1][^2]
- Existing connections already on the failed member may still see a reset and need a retry. [^2]
- To make scenarios #13, #14, and #15 predictable, use an end-to-end HTTP/HTTPS monitor that validates a known-good application response rather than only a TCP or TLS handshake. [^2]
- If the business requirement is “alternative site must work without re-login,” the application must support cross-site session continuity; that outcome is not guaranteed by GTM/LTM/WAF health checks alone. [^2][^5]
- Validate not only monitor timers, but also GTM convergence across all authoritative GTM devices and all four GTM service IPs before accepting any failover SLA as operationally proven. [^1][^5]


## Footnotes

[^1]: F5 GTM/BIG-IP DNS monitor defaults and GTM health behavior. [Monitors Settings Reference (F5)](https://techdocs.f5.com/kb/en-us/products/big-ip_gtm/manuals/product/gtm-monitors-reference-11-5-0/3.html)
[^2]: F5 LTM HTTP/HTTPS monitor behavior and defaults. [Monitors Settings Reference (F5)](https://techdocs.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/ltm-monitors-reference-11-5-0/3.html)
[^3]: AWS ALB target-group health check defaults and thresholds. [Health checks for Application Load Balancer target groups](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/target-group-health-checks.html)
[^4]: F5 guidance for delegating DNS traffic to BIG-IP GTM. [Delegating DNS Traffic to BIG-IP GTM](https://techdocs.f5.com/kb/en-us/products/big-ip_gtm/manuals/product/gtm-implementations-11-5-0/4.html)
[^5]: F5 GTM configuration concepts and service behavior. [BIG-IP GTM Configuration](https://techdocs.f5.com/kb/en-us/products/big-ip_gtm/manuals/product/gtm-concepts-11-5-0/4.html)
[^6]: Microsoft VPN and Windows name-resolution behavior. [VPN name resolution (Microsoft Learn)](https://learn.microsoft.com/en-us/windows/security/operating-system-security/network-security/vpn/vpn-name-resolution)
[^7]: Linux split DNS and systemd-resolved behavior. [Understanding systemd-resolved, Split DNS, and VPN Configuration](https://blogs.gnome.org/mcatanzaro/2020/12/17/understanding-systemd-resolved-split-dns-and-vpn-configuration/)
[^8]: Apple resolver behavior and `.local` considerations. [Apple devices might not open your internal network's '.local' domain](https://support.apple.com/en-us/101903)
[^9]: DNS operational guidance for authoritative servers and delegation hygiene. [RFC 1912 - Common DNS Operational and Configuration Errors](https://datatracker.ietf.org/doc/html/rfc1912)
