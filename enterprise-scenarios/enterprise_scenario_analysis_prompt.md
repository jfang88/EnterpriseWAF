# Enterprise WAF Scenario Analysis — Regeneration Prompt

## Purpose

Regenerate EnterpriseWAF analysis without confusing **current state** with **future target state**.

# 1. Source hierarchy

## 1.1 Current state / stable facts

Read first:

- [current_architecture_and_invariants.md](./current_architecture_and_invariants.md)

Treat this as the authoritative description of the environment **today**.

Do not add a target feature to the current-state diagram unless it has been validated as deployed.

## 1.2 Future / target-state improvements

Read:

- [future_architecture_improvements.md](./future_architecture_improvements.md)

This contains desired improvements such as:

- GTM Layer-7 health of external/internal VIPs;
- cross-site/distributed prober visibility;
- app-team readiness contracts;
- dependency-local recovery;
- cross-site WAF/front-end contingency;
- SLO synthetic monitoring.

These must be labelled **target / to-be**, not current state.

## 1.3 Changeable technical variables

Read:

- [analysis_variables_and_f5_assumptions.md](./analysis_variables_and_f5_assumptions.md)

This contains selectable W1-W4/S1-S2 topologies, F5 behavior, timers, routing and maintenance assumptions.

# 2. Fixed architecture facts for every diagram

Ground every diagram in these facts unless the current-state baseline is explicitly updated:

- two sites;
- one BIG-IP DNS/GTM cluster per site;
- cross-site GTM synchronization;
- two HA edge-firewall pairs per tenant/site, two devices per pair (2 x 2);
- GTM/DNS is inside the edge-firewall boundary;
- external/customer DNS reaches edge GTM over private leased-line/VPN connectivity;
- internal clients use internal enterprise DNS;
- selected internal names/namespaces can be delegated/forwarded to the **same edge GTM service**;
- DNS/GTM is control plane, not an inline application-data hop;
- current tenant LTM HA boundary is retained;
- internal users/DNS/internal LTM are outside private cloud;
- a separate internal firewall sits before the private-cloud CFW;
- CFW and ELB/service are separate private-cloud layers;
- App A/B/C/D dependencies are first-class failure domains.

# 3. Mandatory current-state diagram

The current-state diagram must show:

- external users/API clients;
- external/customer DNS;
- private leased-line/VPN path;
- edge firewall;
- site GTM cluster;
- tenant LTM and WAF;
- internal users;
- internal enterprise DNS;
- delegated/forwarded internal names to edge GTM;
- internal LTM/service VIP;
- internal firewall;
- CFW;
- ELB/service;
- App A/B/C/D and shared state/dependencies;
- Site 1/Site 2 GTM synchronization.

Do **not** show X2A/X2B/XD1, GTM L7 monitor arrows or shared-S1 WAF as current-state features unless validated.

# 4. Mandatory target health-monitoring diagram

Create a separate target/to-be diagram based on [future_architecture_improvements.md](./future_architecture_improvements.md).

It must distinguish these health layers:

- **H1 device/HA liveness** - local HA only;
- **H2 local member health** - LTM/ELB fast local withdrawal;
- **H3 GTM external VIP L7 health** - site/DNS decision for external users;
- **H4 GTM/internal authoritative L7 health** - internal delegated-name/site decision;
- **H5 dependency health** - App A/D -> B -> C, including B1 -> B2 where selected;
- **H6 independent synthetic monitoring** - user/SLO evidence.

Make the action boundary explicit:

> GTM decides site/DNS; local LTM/ELB decides members.

# 5. Health-check design rules

For each protected application, state:

- whether the current check is known or unknown;
- current monitor location and type where known;
- target monitor location;
- external VIP checked;
- internal VIP checked;
- URI/host/SNI;
- expected status/body;
- authentication;
- critical dependencies included;
- non-critical dependencies excluded;
- interval/timeout;
- maintenance/drain semantics;
- app-team owner.

Avoid:

- **false green**: listener up while CFW/ELB/app is unusable;
- **false red**: one non-critical dependency causes broad site withdrawal.

# 6. GTM probing and convergence

Analyse separately:

1. local service/path health detection;
2. GTM receipt/derivation of unhealthy state;
3. synchronization/global-state convergence;
4. GTM DNS answer change;
5. residual DNS TTL/cache;
6. client retry/re-resolution;
7. application recovery T6.

Do not assume GTM synchronization implies direct cross-site probing.

Where health is site-local only, include measured synchronization/state-learning delay before DNS convergence.

# 7. Mandatory WAF topology comparison

Compare:

- **W1** - LTM-fronted independent active WAF pool;
- **W2** - WAF HA/DSC cluster;
- **W3** - tenant-preferred WAFs + shared reserve;
- **W4** - asymmetric Site 1 extra-WAF design;
- **S1** - tenant-specific LTMs -> shared active WAF pool;
- **S2** - shared LTM -> shared active WAF pool, future consolidation only.

For each show:

- N-1/N-2 capacity;
- complete-tier failure;
- change/maintenance headroom;
- cross-tenant blast radius;
- four-tenant LTM/WAF device-unit count;
- 99.95 potential;
- application recovery implications.

# 8. Mandatory application dependency analysis

Always model:

```text
App A ----\
          -> App B -> App C
App D ----/
```

For B failure show both:

- current/no-fallback cascade; and
- target B1 -> B2 dependency-local recovery where safe.

# 9. Mandatory actor/service outcome

For every material failure state the impact to:

- external humans;
- external systems/API clients;
- internal users/systems;
- App A/B/C/D dependencies.

Report:

- unaffected/degraded/unavailable;
- automatic/manual recovery;
- local versus cross-site recovery;
- recovery timing;
- retry/reconnect/re-auth/state/replay requirements;
- time to first successful business transaction.

# 10. Application classes

Use:

- **AT1 stateless web**;
- **AT2 stateful web**;
- **AT3 WebSocket/long-lived**;
- **AT4 non-web/L4**.

Do not call infrastructure failover successful until the applicable application recovery is complete.

# 11. 99.95 and change safety

Treat 99.95% as a target to prove, not an assumed result.

Assess:

- routine node maintenance;
- WAF policy/signature changes;
- LTM/GTM changes;
- CFW/platform changes;
- application rolling changes;
- one planned maintenance event plus one additional credible failure;
- canary/staging/rollback;
- external/internal synthetic success.

# 12. Derived outputs to keep aligned

Update as needed:

- [executive_recommendation.md](./executive_recommendation.md)
- [deployment_options_resilience_summary.md](./deployment_options_resilience_summary.md)
- [end_to_end_service_impact_analysis.md](./end_to_end_service_impact_analysis.md)
- [common_failure_matrix.md](./common_failure_matrix.md)
- [maintainability_change_management_analysis.md](./maintainability_change_management_analysis.md)
- [cross_site_routing_and_dependency_recovery.md](./cross_site_routing_and_dependency_recovery.md)

Management deck source must keep **current-state architecture** and **target-state health architecture** on separate slides.
