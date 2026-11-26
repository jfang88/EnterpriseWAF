# Phase 0 (Days 1–30) — Discovery, Benchmark & Sign-Off Checklist

**Status:** Target Execution Checklist (used to validate **unknown / validate** items in [current_architecture_and_invariants.md](./current_architecture_and_invariants.md) before locking Phase 1 design and hardware/topology choices).

Every major architecture decision — **Shared 6-WAF pool (`S1+2`) vs. Dedicated 3-WAF pool (`W1-3`)**, GTM Layer-7 remediation, client-IP/`XFF` header ownership, SNAT pool sizing, and which applications qualify for **99.95% availability** — depends on closing these Phase 0 facts in Days 1–30.

---

## 1. F5 BIG-IP DNS (GTM) & LTM Current-State Audit (`F5 / ADC Team`)

| # | Audit Item | How to Verify (`tmsh` / Inspection) | Required Output / Gate | Owner | Status |
|---|---|---|---|---|---|
| 1.1 | **Current GTM monitors & depth** | `tmsh list gtm monitor` & `tmsh list gtm pool` | Confirm TCP/port vs. HTTP Layer-7 per external & internal wide-IP; flag any false-green port checks | F5 / ADC | `[ ]` |
| 1.2 | **NAT Address / Translation maps** | `tmsh list gtm server` | Confirm `Address` + `Translation` (`K14707`) and VS Auto-Discovery off for NAT'd edge-FW VIPs | F5 / ADC | `[ ]` |
| 1.3 | **iQuery & Prober Pools** | `tmsh show gtm iquery` & `tmsh list gtm prober-pool` | Verify TCP 4353 reachability, `big3d` versions (`K25923322`), local vs. cross-site probing, and `Specific Prober Pools` (`K08433560`) | F5 / ADC + NetSec | `[ ]` |
| 1.4 | **LTM false-green & drain settings** | `tmsh list ltm virtual` & `tmsh list ltm pool` | Check VS `Immediate Action On Service Down = Reject/Drop` (`K40554304`), pool `Action On Service Down = Reject` (`K15095`), and `Receive Disable` strings (`K12818`) | F5 / ADC | `[ ]` |
| 1.5 | **SNAT, XFF, OneConnect & Sticky map** | `tmsh list ltm virtual profiles persist source-address-translation` | Document per VIP: TLS termination hop, SNAT Automap vs. Pool (`K7820`), `OneConnect` (`K7964` / excluded on WebSockets `K000151124`), `CARP`, and `Trust XFF` (`K4816`) | F5 / ADC + Cloud | `[ ]` |
| 1.6 | **Delegated internal DNS names** | Inspect internal DNS forwarders + GTM internal wide-IPs | Map every internal delegated name and confirm whether it has an independent internal-VIP L7 check (`H4`) | F5 / ADC + NetSec | `[ ]` |

---

## 2. Confirmed `r2800` Hardware, Network & AWAF Sizing Gate (`F5 / ADC + NetSec + SecOps`)

| # | Gate Item | Verification Activity | Decision Impact | Owner | Status |
|---|---|---|---|---|---|
| 2.1 | **AWAF RAM & CPU benchmark on `r2800`** | Replay heaviest tenant's AWAF policy + live traffic profile (with remote HSL logging enabled) inside **`4 vCPU / 12 GB RAM`** vs. **`8 vCPU / 24 GB RAM`** | **Direct topology gate:** If heaviest tenant exceeds `12 GB` RAM/CPU headroom, 2-tenant `W1-3` (`20 × r2800`) is disqualified and **`S1+2` full-box (`20 × r2800`)** or 1-box-per-WAF `W1-3` (`40 × r2800`) is required | F5 / ADC + SecOps | `[ ]` |
| 2.2 | **Peak throughput, TLS TPS & WebSocket sizing** | Measure peak per-tenant HTTP RPS, TLS handshake TPS, concurrent WebSockets, and `SNAT` port concurrency (remember: `r2800` has **no FPGA** and 8 vCPU total) | Sizes `K` peak capacity, **`K + 2` degraded capacity**, **100% single-site DR surge**, and multi-IP `SNAT` pool counts | F5 / ADC + App | `[ ]` |
| 2.3 | **Switch MC-LAG / LACP readiness (No STP)** | Audit top-of-rack switches in Site 1 & Site 2 | Confirm dual-homed **LACP LAGs** (1 LAG per VLAN; `r2800` does **not** support Spanning Tree Protocol, `K000152319`) | NetSec | `[ ]` |
| 2.4 | **Single-SSD rebuild & remote HSL readiness** | Test `cloud-init` provisioning + `platform-migrate validate` + remote HSL log pipeline | Proves fast automated rebuild after an `r2800` single-SSD failure without losing forensic WAF logs | F5 / ADC + SecOps | `[ ]` |

---

## 3. Application Portfolio, TLS/mTLS & Recovery Contracts (`Application + Cloud + SecOps`)

| # | Contract Item | Required Artifact / Answer per Application | Why It Matters | Owner | Status |
|---|---|---|---|---|---|
| 3.1 | **App Class & Invariants (`AT1`–`AT4`)** | Classify each app: Stateless Web/API, Stateful Web (sticky sessions?), WebSocket/Real-Time, or Non-Web L4; declare **real client-IP tracking** method (no-SNAT, `XFF`, or PROXY Protocol) | Locks exact per-layer LTM/WAF/ELB profile stack and confirms whether Cloud ELB must inject its own `XFF` | App + Cloud | `[ ]` |
| 3.2 | **App Tiering & 99.95% SLO Eligibility** | Classify each app as **Tier 1 (Active/Active + automated `T6a`/`T6b` → 99.95% eligible)**, **Tier 2 (Active/Passive warm DR / manual `T5` → 99.9%/99.5%)**, or **Tier 3 (Standard)** | Prevents promising 99.95% on apps whose DB or startup requires manual `T5` DR | App + Mgmt | `[ ]` |
| 3.3 | **Client (`T6a`) & Server (`T6b`) Recovery Audit** | Confirm automated client retry with backoff/**jitter**, DNS TTL respect, WebSocket reconnect/replay (avoiding manual user refresh/re-login), and externalized server sessions | Prevents seconds-scale infra failovers from turning into minutes+ human outages or retry storms | App Teams | `[ ]` |
| 3.4 | **`/health/ready` & Dependency Map** | Publish versioned L7 readiness endpoint (critical vs. optional deps separated) + map `App A/D → B → C` chains for cross-site fallback (`XD1`) eligibility | Eliminates false-greens (TCP up / app dead) and false-reds (optional dep cascading into site withdrawal) | App + Cloud | `[ ]` |
| 3.5 | **TLS / Partner mTLS & Cert Automation** | Inventory every external/internal cert, partner mTLS validation hop, and current renewal automation (Venafi/ACME/BIG-IP 21.1 ACMEv2) | Eliminates 100% expired-cert outages that blow the annual 99.95% budget | F5 + Cloud + App | `[ ]` |
| 3.6 | **WAF Config-as-Code & Emergency `403` Runbook** | Confirm Git/AS3/Declarative WAF tooling, 1-node canary staging sign-off flow, and emergency false-positive bypass authority | Eliminates manual GUI drift across 12–24 boxes and turns silent WAF `403` outages into minute-scale mitigations | SecOps + F5 | `[ ]` |
| 3.7 | **Observability & `X-Correlation-ID` Standard** | Confirm `X-Correlation-ID` injection/forwarding (`LTM → AWAF Support ID → CFW → ELB → App`) and `H6` business-transaction synthetic probes | Cuts cross-team incident triage (MTTR) from 30–60+ minutes to minutes | All Teams | `[ ]` |

---

## 4. Phase 0 Exit Sign-Off (Day 30 Gate)

Phase 1 design lock requires written sign-off on:

1. **Selected WAF target topology:** **Shared 6-WAF pool (`S1+2`, 20 × `r2800`)** vs. **Dedicated 3-WAF pool (`W1-3`, 20 × `r2800` at 2-tenant F5OS or 40 × `r2800` dedicated)** backed by benchmark #2.1–2.2.
2. **Signed Joint Responsibility & RACI Matrix** ([future_architecture_improvements.md §15C & §15D](./future_architecture_improvements.md#15c-joint-responsibility--fault-domain-recovery-matrix-infrastructure-vs-application-per-layer)) across **F5/ADC, Network/Security, Cloud Platform, Application Teams, and Security Ops**.
3. **Approved Tier 1 (99.95%-eligible) vs. Tier 2/3 Application Inventory** and **BIG-IP 17.5.x → `r2800` parallel cutover schedule** (completing well ahead of the **January 1, 2029** 17.5.x End of Technical Support date).

---

## 5. Cloud Platform Discovery & Recovery Placeholders (`T9`–`T12` — Huawei On-Premises Cloud)

Do **not** reuse F5 timers (`T1`–`T4`) for Huawei private-cloud tiers. Cloud Platform and Application owners must fill in **Measured Timing (`p50/p95/p99`)** and verify **Expected Behaviour** during Phase 0 fault injection:

| # | Layer / Code | Failure Scope to Inject | Measured Timing (`TBD`) | Expected Behaviour to Confirm | Owner | Status |
|---|---|---|---|---|---|---|
| 5.1 | **Logical CFW Boundary** | Physical enforcement across Site 1 & Site 2 | `N/A (topology map)` | Map physical HA pairs, tenant contexts, routing/NAT/state sync, and any shared control-plane common-mode failure risk across both sites | Cloud + NetSec | `[ ]` |
| 5.2 | **Cloud Firewall (`T9A/B/C`)** | 1 HA member (`T9A`), local path loss (`T9B`), false-green (`T9C`) | `TBD (p50/p95/p99)` | Confirm `T9A` session survival vs. reset (`+T6a`), `T9B` GTM withdrawal via through-path L7 probe (zero `T9C` false-green), and two-site common-mode risk | Cloud + F5 | `[ ]` |
| 5.3 | **Cloud ELB / Ingress (`T10a/b/c`)** | 1 backend target (`T10a`), ELB HA/VIP takeover (`T10b`), full ELB loss (`T10c`) | `TBD (p50/p95/p99)` | Record probe interval × threshold, target withdrawal time, sticky/WebSocket behaviour on HA takeover, `XFF` header injection & `Slow Start` drain | Cloud + App | `[ ]` |
| 5.4 | **Kubernetes Pod & Worker (`T11a/b/c`)** | Pod crash/roll (`T11a`), worker-node loss (`T11b`), Ingress/CNI/control-plane (`T11c`) | `TBD (p50/p95/p99)` | Confirm `preStop` + `PDB` zero-drop rollouts, Endpoint→ELB withdrawal timing, worker eviction + image pull + PVC attach + warmup (separate service vs. redundancy restoration) | Cloud + App | `[ ]` |
| 5.5 | **VM & Hypervisor (`T12a/b/c`)** | Single VM crash (`T12a`), host HA restart (`T12b`), shared cluster/storage (`T12c`) | `TBD (p50/p95/p99)` | Confirm anti-affinity across physical hosts, ELB withdrawal timing, host HA restart + OS boot + storage re-attach + app warmup vs. manual `T5` rebuild | Cloud + App | `[ ]` |

All Huawei on-premises values remain **`TBD`** until measured under representative load. Separate **service restoration** (surviving peers absorb traffic) from **redundancy restoration** (failed Pod/VM replaced), and compose only critical-path stages without double counting.
