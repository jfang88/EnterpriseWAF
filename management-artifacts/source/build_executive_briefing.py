"""Build the primary 10-slide Executive Briefing & Tech-Lead Discussion Deck (+ full Speaker Notes).

Structure:
  Part 1 — Core Themes in 3 Slides (Plain-English Executive Briefing):
    Slide 1: Theme 1 — Joint Responsibility for Tier-1 99.95% Availability & <= 25% Impact
    Slide 2: Theme 2 — Layered Health Checks, Proportional Recovery & Operational Guardrails
    Slide 3: Theme 3 — WAF Topology Shortlist (Shared 6-WAF vs. Dedicated 3-WAF) & 90-Day Plan

  Part 2 — Tech-Lead Deep-Dive Discussion Slides (Slides 4-10):
    Slide 4: Current-State End-to-End Topology (authoritative SVG with spanning logical CFW + notes)
    Slide 5: Target Layered Health Monitoring (authoritative SVG with spanning logical CFW + notes)
    Slide 6: Visual WAF Topology Options (authoritative SVG + r2800 rebuild notes)
    Slide 7: Plain-English Topology Variant Scorecard (<= 25% impact, 99.95%, longest outage, auto/manual)
    Slide 8: End-to-End Path Consistency — Sticky Sessions, Client-IP Headers, Source NAT & Speed
    Slide 9: Joint Responsibility Matrix by Fault Domain (Infra vs. App obligations)
    Slide 10: Private-Cloud Platform Recovery Placeholders — CFW, ELB, Kubernetes & VM (T9–T12)

Technical details (r2800 hardware specs, BIG-IP 17.5.x -> 21.1.x+ parallel cutover, RACI, F5 KBs,
OneConnect/CARP/SNAT mechanics, and T1-T12 timings) are placed in PowerPoint Speaker Notes
so the slides stay plain-English and scannable while preserving full engineering depth.
"""

from pathlib import Path
import subprocess
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.oxml import parse_xml
from pptx.oxml.ns import nsdecls

ROOT = Path(__file__).resolve().parents[1]
DIAGRAMS = ROOT / "diagrams"
BUILD = ROOT / ".build_discussion"
BUILD.mkdir(exist_ok=True)
OUT = ROOT / "EnterpriseWAF_Executive_Briefing.pptx"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

NAVY = RGBColor(6, 55, 95)
NAVY2 = RGBColor(11, 76, 116)
TEAL = RGBColor(15, 139, 141)
CYAN = RGBColor(224, 245, 248)
GREEN = RGBColor(223, 245, 193)
PALEGREEN = RGBColor(235, 248, 233)
GREEN_LINE = RGBColor(92, 164, 82)
PURPLE = RGBColor(237, 232, 255)
LIGHT = RGBColor(246, 249, 252)
MID = RGBColor(214, 226, 236)
DARK = RGBColor(22, 36, 50)
ORANGE = RGBColor(209, 119, 20)
WHITE = RGBColor(255, 255, 255)
RED = RGBColor(190, 49, 68)
SLATE = RGBColor(74, 91, 107)
GOLD = RGBColor(226, 191, 80)
PALEYELLOW = RGBColor(255, 247, 220)
PALERED = RGBColor(255, 240, 240)
BG_SVG = RGBColor(248, 250, 252)
FONT = "Liberation Sans"


def new_slide():
    return prs.slides.add_slide(prs.slide_layouts[6])


def set_notes(s, text: str):
    notes_slide = s.notes_slide
    tf = notes_slide.notes_text_frame
    tf.text = text.strip()


def add_text(
    s,
    text,
    x,
    y,
    w,
    h,
    size=13,
    bold=False,
    color=DARK,
    align=PP_ALIGN.LEFT,
    fill=None,
    line=None,
    radius=True,
    anchor=MSO_ANCHOR.MIDDLE,
    margin_x=0.12,
    margin_y=0.06,
):
    sh = s.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE,
        Inches(x),
        Inches(y),
        Inches(w),
        Inches(h),
    )
    if radius and len(sh.adjustments) > 0:
        sh.adjustments[0] = 0.08
    if fill is None:
        sh.fill.background()
    else:
        sh.fill.solid()
        sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line
        sh.line.width = Pt(1.2)
    tf = sh.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(margin_x)
    tf.margin_top = tf.margin_bottom = Inches(margin_y)
    p = tf.paragraphs[0]
    p.text = text
    p.alignment = align
    p.font.name = FONT
    p.font.size = Pt(size)
    p.font.bold = bold
    p.font.color.rgb = color
    return sh


def arrow(s, x1, y1, x2, y2, color=NAVY, width=2.2, dash=False, both=False):
    ln = s.shapes.add_connector(
        MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2)
    )
    ln.line.color.rgb = color
    ln.line.width = Pt(width)
    if dash:
        ln.line.dash_style = MSO_LINE_DASH_STYLE.DASH
    l = ln.line._get_or_add_ln()
    l.append(
        parse_xml(
            f'<a:headEnd {nsdecls("a")} type="triangle"/>'
            if both
            else f'<a:headEnd {nsdecls("a")} type="none"/>'
        )
    )
    l.append(parse_xml(f'<a:tailEnd {nsdecls("a")} type="triangle"/>'))
    return ln


def header(s, badge_text, t, st, badge_fill=TEAL, tsize=22):
    add_text(s, badge_text, 0.45, 0.16, 2.75, 0.28, 8.5, True, WHITE, PP_ALIGN.CENTER, badge_fill, badge_fill)
    add_text(s, t, 0.45, 0.46, 12.43, 0.44, tsize, True, NAVY, radius=False, margin_x=0.02, margin_y=0.02)
    if st:
        add_text(s, st, 0.45, 0.92, 12.43, 0.30, 10.6, False, SLATE, radius=False, margin_x=0.02, margin_y=0.02)


def footer(s, n, total=10, bg_bar=False):
    if bg_bar:
        add_text(s, "", 0.0, 7.08, 13.333, 0.42, 8.0, False, SLATE, fill=BG_SVG, radius=False)
    add_text(
        s,
        "End-to-end application delivery — executive briefing & tech-lead discussion  •  Hardware (r2800), F5 KBs & timings in Speaker Notes",
        0.45,
        7.19,
        9.8,
        0.20,
        7.8,
        False,
        SLATE,
        radius=False,
        margin_x=0.0,
    )
    add_text(
        s,
        f"Nov 2026  •  {n} / {total}",
        11.15,
        7.19,
        1.73,
        0.20,
        7.8,
        False,
        SLATE,
        PP_ALIGN.RIGHT,
        radius=False,
        margin_x=0.0,
    )


def legend_bar(s, text):
    add_text(
        s,
        text,
        0.38,
        6.82,
        12.57,
        0.30,
        7.4,
        False,
        NAVY,
        PP_ALIGN.LEFT,
        RGBColor(238, 244, 249),
        MID,
        radius=True,
        margin_x=0.10,
        margin_y=0.02,
    )


def card(s, heading, items, x, y, w, h, fill=LIGHT, line=MID, headfill=NAVY, fs=10.8, space_after=8):
    add_text(s, heading, x, y, w, 0.44, 12.0, True, WHITE, PP_ALIGN.CENTER, headfill, headfill)
    sh = s.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(x),
        Inches(y + 0.50),
        Inches(w),
        Inches(h - 0.50),
    )
    if len(sh.adjustments) > 0:
        sh.adjustments[0] = 0.05
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    sh.line.color.rgb = line
    sh.line.width = Pt(1.2)
    tf = sh.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.TOP
    tf.margin_left = tf.margin_right = Inches(0.20)
    tf.margin_top = Inches(0.18)
    tf.margin_bottom = Inches(0.10)
    for idx, item in enumerate(items):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        p.text = "• " + item
        p.alignment = PP_ALIGN.LEFT
        p.space_after = Pt(space_after)
        p.font.name = FONT
        p.font.size = Pt(fs)
        p.font.color.rgb = DARK


def simple_table(s, headers, rows, x, y, colw, rowh=0.52, fs=8.8, headh=0.44, aligns=None):
    xx = x
    for i, h in enumerate(headers):
        add_text(s, h, xx, y, colw[i], headh, fs + 0.4, True, WHITE, PP_ALIGN.CENTER, NAVY, NAVY)
        xx += colw[i]
    yy = y + headh
    for r, row in enumerate(rows):
        xx = x
        f = LIGHT if r % 2 == 0 else WHITE
        for i, v in enumerate(row):
            al = aligns[i] if aligns else PP_ALIGN.LEFT
            add_text(s, str(v), xx, yy, colw[i], rowh, fs, False, DARK, al, f, MID, margin_x=0.10, margin_y=0.05)
            xx += colw[i]
        yy += rowh


def render_svg(svg_name: str, out_name: str) -> Path:
    src = DIAGRAMS / svg_name
    dst = BUILD / out_name
    subprocess.run(
        ["rsvg-convert", "-w", "1600", "-h", "900", str(src), "-o", str(dst)],
        check=True,
    )
    return dst


# =============================================================================
# PART 1 — CORE THEMES IN 3 SLIDES (PLAIN-ENGLISH EXECUTIVE BRIEFING)
# =============================================================================

# Slide 1 — Theme 1: Joint Responsibility, 99.95% Tier-1 Availability & <= 25% Impact
s = new_slide()
header(
    s,
    "EXECUTIVE THEME 1 OF 3",
    "Resilience is a joint responsibility across infrastructure & apps",
    "Meeting 99.95% availability (including planned changes) and a ≤ 25% blast-radius cap requires explicit contracts at every layer.",
    badge_fill=TEAL,
)

# Top 3 KPI callout tiles
kpis = [
    ("99.95% Total Availability", "4h 23m / year combined (managed + unmanaged)\nEligible for Tier 1 Active/Active apps only", NAVY),
    ("≤ 25% Max Impact Cap", "Max 1 of 4 tenants affected\n& ≤ 25% canary / node blast radius", TEAL),
    ("4 Changes / Yr per Stack", "~36 change waves / year\nmust roll with zero user outage", NAVY2),
]
for i, (kt, ks, kc) in enumerate(kpis):
    kx = 0.45 + i * 4.22
    add_text(s, kt, kx, 1.30, 3.98, 0.36, 12.0, True, WHITE, PP_ALIGN.CENTER, kc, kc)
    add_text(s, ks, kx, 1.68, 3.98, 0.64, 9.5, True, DARK, PP_ALIGN.CENTER, LIGHT, MID)

# Two-pillar Joint Responsibility visual + Center Contract Bridge
card(
    s,
    "Infrastructure Teams Deliver",
    [
        "Resilient, rolling-upgradeable tiers (Global DNS, firewalls, load balancers, Web App Firewall, Cloud Load Balancer)",
        "Fast, consistent traffic paths: sticky-session routing, multi-IP Source NAT pools, real client-IP headers & automated TLS certs",
        "Layer-accurate health checks + declarative config-as-code & end-to-end request correlation IDs",
    ],
    0.45,
    2.48,
    4.65,
    3.32,
    CYAN,
    MID,
    NAVY,
    9.6,
    space_after=7,
)

add_text(
    s,
    "Shared\nContracts,\nTiering\n&\nRACI",
    5.45,
    3.24,
    2.43,
    1.95,
    12.2,
    True,
    NAVY,
    PP_ALIGN.CENTER,
    PALEGREEN,
    GREEN_LINE,
)
arrow(s, 5.12, 4.22, 5.42, 4.22, TEAL, width=2.4, both=True)
arrow(s, 7.90, 4.22, 8.20, 4.22, TEAL, width=2.4, both=True)

card(
    s,
    "Application Teams Deliver",
    [
        "Client auto-recovery (seconds): retry with jitter, DNS re-lookup & WebSocket reconnect — avoiding manual user refresh/re-login",
        "Server auto-recovery (seconds–2 min): externalized sessions, fast warmup & rolling updates — avoiding manual startup/DB failover",
        "App-owned Layer-7 readiness checks (/health/ready), Tier 1 vs. Tier 2/3 SLO tiering & declared client-IP / sticky / WebSocket needs",
    ],
    8.23,
    2.48,
    4.65,
    3.32,
    GREEN,
    MID,
    TEAL,
    9.6,
    space_after=7,
)

add_text(
    s,
    "Initial delivery focuses on the Web App Firewall & F5 tier (Phase 1) while aligning Network/Security, Cloud Platform, Security Ops & Application teams under a signed RACI.",
    0.45,
    5.96,
    12.43,
    0.70,
    10.4,
    True,
    NAVY,
    PP_ALIGN.CENTER,
    PALEYELLOW,
    GOLD,
)
legend_bar(
    s,
    "Reference: Engineering codes (T1–T12, T6a/T6b/T5, H1–H6, AT1–AT4, F5 KBs), App Tiering & RACI matrix are in Speaker Notes and the 18-slide Engineering Reference Appendix.",
)
footer(s, 1)
set_notes(
    s,
    """SPEAKER NOTES — SLIDE 1 (EXECUTIVE THEME 1: JOINT RESPONSIBILITY, APP TIERING, 99.95% & 25% IMPACT)

1. Core Leadership Message:
   - Neither infrastructure HA alone nor application code alone can hit 99.95% (4h 22m 48s / year = 262.8 min/yr) when BOTH managed (planned changes/patching) and unmanaged (unplanned failures) outages count against the same budget.
   - At 4 planned updates/year across ~9 major technology stacks (~36 change waves/year):
     * Rolling zero-downtime R0/R1 maintenance across every tier consumes ~4–12 min/year, leaving ~250 min/yr for genuine unplanned incidents.
     * In contrast, offline App/DB restarts (15–30 min each, 4x/year) burn 180–240+ min/year BEFORE a single unplanned failure happens.
   - Application recovery (T6) MUST be split into two distinct expectations:
     * T6a (Client-Side): Automated retry with exponential backoff/jitter, DNS re-lookup, silent re-auth, WebSocket reconnect/replay takes seconds; if poorly architected, users must manually refresh, re-login, restart clients, or re-enter lost work (minutes+ human-speed outage!).
     * T6b (Server-Side): Automated externalized session lookup, pool reset, and warmup takes seconds–2 min; if manual server/DB intervention is required, it escalates to T5 (minutes to hours).

2. Application Tiering & 99.95% SLO Eligibility (Guardrail #4 — future_architecture_improvements.md §15D):
   - Tier 1 (Mission-Critical — 99.95% Eligible): Active/Active across Site 1 & Site 2, automated T6a/T6b recovery, zero-downtime rolling app/DB changes, automated L7 health & synthetics.
   - Tier 2 (Business-Important — Warm DR): Local HA stays seconds-scale, but Active/Passive whole-site DR requires manual/scripted T5 startup/DB promotion -> realistic SLO is 99.9%–99.5% (do NOT sell as 99.95% combined!).
   - Tier 3 (Standard / Legacy): Single-site, manual restarts, or clients requiring manual user steps -> best-effort / < 99.5%.

3. Enterprise Baseline Invariants & Platform Context:
   - Four-tenant extranet estate across 2 independent sites; existing tenant Local Traffic Manager (LTM) HA pairs (2/tenant/site) are retained.
   - Portfolio includes stateless web (AT1), stateful web with sticky sessions (AT2), WebSocket real-time apps (AT3), and non-web Layer-4 apps (AT4).
   - Real external client-IP tracking is a baseline invariant (no-SNAT symmetry, SNAT + X-Forwarded-For at first L7 TLS terminator, or PROXY Protocol).
   - Current estate runs BIG-IP 17.5.x (End of Technical Support: Jan 1, 2029 per MyF5 K15643). Confirmed refresh hardware: F5 rSeries r2800 pizza boxes ONLY (F5OS-A 1.8.0+ + BIG-IP 21.1.x+, no blade chassis).""",
)


# Slide 2 — Theme 2: Layered Health, Proportional Recovery & Operational Guardrails
s = new_slide()
header(
    s,
    "EXECUTIVE THEME 2 OF 3",
    "Build health checks, recovery & guardrails at the exact right layer",
    "Keep single-component failures local and automatic; prevent silent false-greens, dependency cascades & operational outages.",
    badge_fill=TEAL,
    tsize=21.2,
)

# 4-tier Recovery Ladder visual in FULL PLAIN ENGLISH
tiers = [
    ("1. Local Auto Recovery", "Seconds • Automated", "1 firewall, load balancer,\nWAF, or app node fails\n→ stays inside the site", PALEGREEN, GREEN_LINE),
    ("2. Cross-Site Component", "Seconds • Automated", "Full local WAF tier or shared\nApp B fails → borrow remote\nWAF or Site 2 App B", CYAN, TEAL),
    ("3. Automated Site Move", "~1–3 min • Automated", "Whole local path, Cloud\nFirewall, or site unavailable\n→ Global DNS steers to Site 2", LIGHT, NAVY),
    ("4. Manual / Warm DR", "Minutes–Hours • Exception", "Passive app startup, manual\nDB promotion or user refresh\n→ breaks 99.95% if routine", PALERED, RED),
]
for i, (tt, tsub, tbody, tfill, tline) in enumerate(tiers):
    tx = 0.45 + i * 3.16
    add_text(s, tt, tx, 1.32, 2.90, 0.38, 10.6, True, WHITE, PP_ALIGN.CENTER, tline, tline)
    add_text(s, tsub, tx, 1.72, 2.90, 0.32, 9.2, True, tline, PP_ALIGN.CENTER, WHITE, tline)
    add_text(s, tbody, tx, 2.06, 2.90, 1.14, 9.5, False, DARK, PP_ALIGN.CENTER, tfill, tline)
    if i < 3:
        arrow(s, tx + 2.93, 2.30, tx + 3.13, 2.30, NAVY, width=2.2)

# Three clear architectural & operational guardrail rules below
rules = [
    (
        "Stop Silent False-Greens",
        [
            "An open TCP port does NOT prove Cloud Firewall, Cloud Load Balancer, or the app works; Global DNS must check true Layer-7 readiness.",
            "Business-transaction synthetics + automated TLS/mTLS cert renewal + declarative WAF-as-code prevent silent 403 blocks & expired-cert outages.",
        ],
    ),
    (
        "Separate External & Internal Paths",
        [
            "External users cross Edge Firewall → Load Balancer → WAF → Cloud Firewall → Cloud Load Balancer.",
            "Internal users cross Internal Firewall → Cloud Firewall → Cloud Load Balancer (often bypassing WAF) and need separate endpoint health.",
        ],
    ),
    (
        "Contain Cascades & Retry Storms",
        [
            "If shared App B fails in Site 1, fail App B over to Site 2 locally rather than cascading App A / C / D into a site failover.",
            "Enforce client retry jitter, per-tenant rate limits & unified Request Correlation IDs across every hop to cut triage time (MTTR).",
        ],
    ),
]
for i, (rh, ritems) in enumerate(rules):
    card(s, rh, ritems, 0.45 + i * 4.22, 3.38, 3.98, 2.38, WHITE, MID, NAVY, fs=9.3, space_after=5)

add_text(
    s,
    "Design rule: Global DNS owns the site answer, but the health signal must cross the failure domain DNS is deciding about — backed by business synthetics, automated certs & correlation IDs.",
    0.45,
    5.92,
    12.43,
    0.72,
    9.9,
    True,
    NAVY,
    PP_ALIGN.CENTER,
    PALEGREEN,
    GREEN_LINE,
)
legend_bar(
    s,
    "Reference: Six health layers (H1–H6), recovery classes (R0–R4), cross-site patterns (X2A/X2B/XD1), six operational guardrails (§15D) & F5 KBs are in Speaker Notes & Appendix.",
)
footer(s, 2)
set_notes(
    s,
    """SPEAKER NOTES — SLIDE 2 (EXECUTIVE THEME 2: LAYERED HEALTH, PROPORTIONAL RECOVERY & SIX GUARDRAILS)

1. Six Coordinated Health Layers (H1–H6 — see Engineering Reference Appendix Slides 3, 5, 6):
   - H1 (Native HA): Device/peer liveness (LTM/FW/CFW HA failover; BIG-IP Failover.NetTimeoutSec = 3s, K7249/K10095).
   - H2 (Local Member Health): LTM WAF pool & Cloud ELB member monitors (default 5s/16s). Set LTM Action On Service Down = Reject (K15095) and VS Immediate Action On Service Down = Reject/Drop (K40554304) to stop TCP 3-way handshake false-greens.
   - H3 (External Published VIP): GTM L7 health from external-representative prober or authoritative LTM+iQuery. External FW NAT VIPs require Address + Translation in BIG-IP DNS + TCP 4353 iQuery, which automatically disables VS Auto-Discovery (K14707, K9138).
   - H4 (Internal Published VIP): Separate GTM wide-IP/monitor for delegated internal names crossing Internal FW -> CFW -> ELB -> App.
   - H5 (Shared Dependency): App B service VIP with B1 preferred / B2 fallback (XD1). App A /health/ready must not fail on optional App B degradation (no false-red cascade).
   - H6 (Independent Synthetic): External & internal business-transaction checks verifying HTTP 200 (catching WAF 403 false-positives & expired certs!) and measuring actual 99.95% SLO.

2. Six Operational Guardrails (future_architecture_improvements.md §15D):
   - Guardrail 1 (TLS/mTLS Cert Lifecycle): Automated PKI/CLM or BIG-IP 21.1 ACMEv2 renewal + 30/14/7-day alerts; explicit mTLS validation & XFF alignment per app.
   - Guardrail 2 (WAF Config-as-Code & False-Positive 403 Prevention): Git-backed AS3 / Declarative WAF / cloud-init (no manual GUI drift across 12–24 boxes), 1-node canary + 7-day staging (K82512024), fast emergency 403 bypass runbook.
   - Guardrail 3 (r2800 Performance Sizing & Retry-Storm Protection): Benchmark RPS/TLS-TPS/WS on software-only 8-vCPU r2800 (no FPGA); mandatory exponential backoff + randomized jitter on T6a clients + LTM/WAF rate limits & App B circuit breakers.
   - Guardrail 4 (App Tiering): Tier 1 Active/Active = 99.95% eligible; Tier 2 Active/Passive Warm DR = 99.9%–99.5%.
   - Guardrail 5 (End-to-End Correlation ID): Inject X-Correlation-ID at first L7 hop, log with AWAF Support ID via remote HSL, forward through CFW/ELB/App to cut cross-team triage MTTR.
   - Guardrail 6 (Parallel Zero-Downtime Cutover & RACI): Greenfield r2800 build + per-tenant canary swing + instant 17.5.x rollback ahead of Jan 2029 EoTS.

3. Critical F5 Guardrails & Indicative Timings (T1–T12):
   - Specific Prober Pools (K08433560; avoid K000163083 fallback / K000159606 MAC flap); no duplicate VS monitors (K5431); upgrade BIG-IP DNS before LTM + big3d_install (K25923322).
   - Local HA (T1): ~3s+ + T6a/T6b; Local pool eject (T2): ~16s + T6a/T6b; Cross-site WAF borrow (X2A): ~16s + T6a/T6b (cannot bypass local CFW); Auto GTM site move (T4): ~46–150s + T6a/T6b; Manual DR (T5): minutes–hours. Huawei private-cloud CFW (T9), ELB (T10), Kubernetes (T11) and VM (T12) timings: TBD / measure; do not reuse F5 timers.""",
)


# Slide 3 — Theme 3: Recommended Shortlist & 90-Day Decisions (Full Plain English)
s = new_slide()
header(
    s,
    "EXECUTIVE THEME 3 OF 3",
    "Recommended shortlist (Shared 6-WAF vs. Dedicated 3-WAF) & 90-day plan",
    "Keep separate tenant load balancers; both finalists need 20 standard appliances on refresh — choice hinges on policy isolation vs. memory.",
    badge_fill=TEAL,
    tsize=19.8,
)

# Left vs Right Finalist Comparison in FULL PLAIN ENGLISH
card(
    s,
    "Option A — Shared 6-WAF Active Pool (4 Base + 2 Buffer)",
    [
        "4 separate tenant load-balancer pairs → 6 shared active WAFs per site",
        "+2 active nodes absorb rolling upgrades, 1 unplanned disk/box failure & 1-node canary tests",
        "Full appliance memory (24 GB) per WAF; 20 standard appliances total across 2 sites",
        "Meets ≤ 25% cap ONLY with per-tenant policies, config-as-code & 1-node canary gates (≤ 17%)",
        "Best if: WAF policies need >12 GB memory & declarative change governance is mature",
    ],
    0.45,
    1.30,
    6.05,
    3.12,
    PALEGREEN,
    GREEN_LINE,
    TEAL,
    9.5,
    space_after=6,
)

card(
    s,
    "Option B — Dedicated 3-WAF Pool per Tenant (Hard Isolation)",
    [
        "Each tenant gets its own dedicated 3-WAF active pool per site (survives 2 simultaneous losses)",
        "Hard ≤ 25% (1 of 4 tenants) blast-radius guarantee — zero cross-tenant policy risk",
        "2-tenant appliance virtualization also lands at 20 standard boxes (if heaviest tenant fits 12 GB RAM)",
        "Lower-cost 2-WAF-per-tenant option loses local maintenance safety — requires remote WAF borrowing",
        "Best if: strict physical & policy tenant isolation outweighs shared-pool memory headroom",
    ],
    6.83,
    1.30,
    6.05,
    3.12,
    CYAN,
    MID,
    NAVY,
    9.5,
    space_after=6,
)

# Why other options are not default (slim strip in plain English)
add_text(
    s,
    "Not recommended as default (Slide 7):  Dedicated 2-WAF/tenant (0 maintenance N-2 without remote borrow)  •  2-node WAF HA pair (0 maintenance N-2)  •  Preferred+reserve / Asymmetric (complex for small savings)  •  Shared load balancer + WAF (100% 4-tenant blast radius).",
    0.45,
    4.56,
    12.43,
    0.50,
    8.7,
    False,
    SLATE,
    PP_ALIGN.CENTER,
    LIGHT,
    MID,
)

# 3 Immediate Leadership Decisions / Next 90 Days
steps = [
    ("Decision 1 — Phase 0 Audit (Days 1–30)", "Run Phase 0 checklist: verify DNS checks, certs/TLS/client-IP headers, Tier 1/2/3 app list & WAF RAM/TPS benchmark"),
    ("Decision 2 — Contracts & Pick (Days 31–60)", "Sign cross-team RACI & fault-domain contracts (Slide 9); pick Shared 6-WAF vs. Dedicated 3-WAF"),
    ("Decision 3 — Cutover & Prove (Days 61–90+)", "Parallel greenfield refresh (ahead of Jan 2029 17.5.x EoTS) with canary swing, instant rollback & fault injection"),
]
for i, (sh, sb) in enumerate(steps):
    sx = 0.45 + i * 4.22
    add_text(s, sh, sx, 5.20, 3.98, 0.34, 10.1, True, WHITE, PP_ALIGN.CENTER, NAVY, NAVY)
    add_text(s, sb, sx, 5.56, 3.98, 1.08, 9.2, False, DARK, PP_ALIGN.CENTER, PALEYELLOW, GOLD)

legend_bar(
    s,
    "Reference: Engineering codes (S1+2, W1-3, W1-2, W2b, W3, W4a, S2, X2A), confirmed r2800 specs, Phase 0 checklist & cutover details are in Speaker Notes & Appendix.",
)
footer(s, 3)
set_notes(
    s,
    """SPEAKER NOTES — SLIDE 3 (EXECUTIVE THEME 3: SHORTLIST, CONFIRMED r2800 REBUILD & PARALLEL CUTOVER)

1. Confirmed Hardware Refresh Standard (Locked Invariant — NO Blade Chassis):
   - Standard appliance: F5 rSeries r2800 pizza boxes ONLY (no VELOS blade chassis, no r4800/r5000+).
   - Software stack: F5OS-A 1.8.0+ (or 2.0.x) + BIG-IP 21.1.x+ (EoTS May 5, 2029; BIG-IP 17.5.x EoTS Jan 1, 2029 per K15643; BIG-IP 21.x drops iSeries/VIPRION/vCMP so parallel rebuild is mandatory).
   - Compute & RAM envelope: 8 usable CPU cores (4 vCPU min/tenant), 32 GB system RAM -> 24 GB usable for tenants (12 GB min/tenant).
   - Multi-tenancy ceiling: Max 2 F5OS tenants per r2800 on F5OS-A 1.8.0+ (only 1 tenant on <= 1.7.x); requires .tar.bundle format (K000158849) and >= 88 GB virtual disk for 21.1.x ALL image (K45191957).

2. Why BOTH Finalists Land at 20 r2800 Appliances Total Across 2 Sites:
   - Tenant LTM tier (both options): 4 tenant HA pairs/site consolidated onto 4 x r2800/site (8 total vs. 16) at 2 isolated LTM tenants/box (A+B on pair 1; C+D on pair 2).
   - Option A — Shared 6-WAF Pool (S1+2, Full-Box): 6 x r2800/site = 12 WAF boxes (each gets full 8 vCPU / 24 GB RAM) -> 8 LTM + 12 WAF = 20 r2800s total.
   - Option B — Dedicated 3-WAF Pool (W1-3, 2-Tenant F5OS): 6 x r2800/site = 12 WAF boxes (A+B on boxes #1-3, C+D on boxes #4-6; each tenant gets 3 isolated 4 vCPU / 12 GB WAFs/site) -> 8 LTM + 12 WAF = 20 r2800s total.
   - Phase 0 Mandatory Gate (enterprise-scenarios/phase0_discovery_and_signoff_checklist.md): Benchmark heaviest tenant's AWAF policy + peak HTTP RPS, TLS TPS & WebSockets inside 4 vCPU / 12 GB RAM (with remote HSL logging). If it fits with headroom -> Dedicated 3-WAF (W1-3 2-tenant) gives hard <= 25% isolation at the same 20-box count! If AWAF needs > 12 GB RAM -> choose Shared 6-WAF (S1+2 full-box, 24 GB) with declarative config-as-code + 1-node canary gating.

3. Parallel Zero-Downtime Cutover & Critical r2800 Guardrails:
   - Parallel cutover: Rack & dual-home new r2800s alongside 17.5.x -> validate with 'platform-migrate validate' (K82540512) + cloud-init + AS3/Declarative WAF -> swing 1 tenant, 1 site at a time via GTM/LTM canary with legacy 17.5.x kept warm for instant rollback.
   - Single 480 GB NVMe SSD (~447 GB usable, NO RAID-1): 1 SSD failure takes down the entire box -> mandatory K+2 / N-2 multi-box spread, remote HSL logging, and cloud-init rebuild.
   - No FPGA and NO Spanning Tree Protocol (STP) (K000152319, K000151396): max 1 interface/LAG per VLAN -> terminate dual-homed LACP LAGs to MC-LAG/vPC switches managed at the F5OS-A host layer (K1689).""",
)


# =============================================================================
# PART 2 — TECH-LEAD DEEP-DIVE DISCUSSION SLIDES (SLIDES 4-9)
# =============================================================================

# Slide 4 — Discussion 1: Current-State End-to-End Topology (Authoritative SVG)
s = new_slide()
img4 = render_svg("EnterpriseWAF_End_to_End_Topology.svg", "disc_slide4.png")
s.shapes.add_picture(str(img4), 0, 0, width=prs.slide_width, height=prs.slide_height)
footer(s, 4, bg_bar=True)
set_notes(
    s,
    """SPEAKER NOTES — SLIDE 4 (TECH-LEAD DISCUSSION 1: CURRENT-STATE BASELINE)

1. Current-State Rules (Preserve Strictly vs. Target State):
   - External and internal access are PARALLEL paths converging at the private-cloud CFW -> ELB tier, while BIG-IP DNS/GTM is a DNS control plane (NOT an inline data proxy).
   - CFW is one logical private-cloud edge available in both sites, with site-local enforcement and ELBs behind it. Physical HA, shared state and common-mode risks remain to be validated.
   - Site 1 and Site 2 are separate infrastructure failure domains; shared cloud services may introduce common-mode risk. GTM sync shares DNS/health view only — it does NOT sync LTM/WAF/CFW/app config.
   - Distinct security/failure boundaries: Edge Firewalls (2 x 2 HA pairs/tenant/site, NetSec) vs. Internal Firewall (NetSec) vs. Private-Cloud CFW (Cloud Platform).
   - Internal users may bypass the external WAF tier; an internal-FW failure impacts internal users only, whereas a CFW failure impacts BOTH external and internal traffic converging on that CFW.

2. Phase 0 Audit Items (enterprise-scenarios/phase0_discovery_and_signoff_checklist.md):
   - Current BIG-IP 17.5.x GTM monitor type (TCP port vs. HTTP/L7), targets, intervals, timeouts, and NAT Address/Translation mappings (K14707).
   - Whether GTM uses iQuery (TCP 4353) or direct monitors, and whether Site 1/Site 2 GTMs probe cross-site or site-locally only.
   - Current TLS/mTLS termination hop & cert renewal automation, SNAT configuration, X-Forwarded-For injection/trust, sticky-session ownership, peak RPS/TLS-TPS/WS baselines, and Active/Active vs. Active/Passive (Tier 1/2/3) app inventory.""",
)


# Slide 5 — Discussion 2: Target Layered Health Monitoring (Authoritative SVG)
s = new_slide()
img5 = render_svg("EnterpriseWAF_Target_Health_Monitoring.svg", "disc_slide5.png")
s.shapes.add_picture(str(img5), 0, 0, width=prs.slide_width, height=prs.slide_height)
footer(s, 5, bg_bar=True)
set_notes(
    s,
    """SPEAKER NOTES — SLIDE 5 (TECH-LEAD DISCUSSION 2: TARGET LAYERED HEALTH MONITORING)

1. Probe Origin vs. Decision Ownership:
   - GTM owns the DNS/site decision for external wide-IPs (H3) and selected delegated internal wide-IPs (H4), but the probe origin must exercise the failure domain being decided about.
   - Because edge GTM sits inside the edge firewall, direct GTM probing validates downstream LTM->WAF->CFW->ELB->App readiness, while an external/extranet-representative vantage or independent synthetic (H6) validates leased-line, outside-in firewall reachability, valid TLS certs, and catches WAF false-positive 403 blocks.
   - Keep external (H3) and internal (H4) wide-IP health state separate so an external WAF/edge fault does not withdraw healthy internal access (and vice versa).

2. F5 BIG-IP DNS + LTM Integration Checkpoints & Correlation ID:
   - NAT Translation (K14707, K9138): External FW VIP = Address; Private LTM VIP = Translation; permits TCP 4353 iQuery; disables VS Auto-Discovery (manage via declarative AS3/BIG-IQ).
   - Specific Prober Pools (K08433560): Pin exact probers per zone; validate reconnect fallback (K000163083) and avoid non-bigip local MAC flapping (K000159606).
   - No duplicate VS monitors (K5431) when consuming LTM state over iQuery.
   - Inject X-Correlation-ID at first L7 hop, log with AWAF Support ID via remote HSL, and forward across CFW/ELB/App for rapid cross-team MTTR.
   - Application-owned readiness contract: Host/SNI, URI (/health/ready), HTTP 200 + receive string, Receive Disable String (K12818), critical vs. non-critical dependency boundaries.""",
)


# Slide 6 — Discussion 3: Visual WAF Topology Options (Authoritative SVG)
s = new_slide()
img6 = render_svg("EnterpriseWAF_Topology_Options.svg", "disc_slide6.png")
s.shapes.add_picture(str(img6), 0, 0, width=prs.slide_width, height=prs.slide_height)
footer(s, 6, bg_bar=True)
set_notes(
    s,
    """SPEAKER NOTES — SLIDE 6 (TECH-LEAD DISCUSSION 3: VISUAL WAF TOPOLOGY OPTIONS & r2800 FIT)

1. Key Variant Differences to Walk Through with Tech Leads (Plain-English Name -> Code):
   - Dedicated 3-WAF/tenant (W1-3) vs. Dedicated 2-WAF/tenant (W1-2): W1-3 gives full local N-2 rolling maintenance + hard <= 25% tenant isolation. W1-2 drops the 3rd WAF (saving 8 WAFs = 32 vs. 40), keeping tenant blast radius <= 25%, BUT losing 1 WAF removes 50% of that tenant's capacity and maintenance + 2nd fault removes 100% of that tenant's local WAF tier -> Remote WAF borrow (X2A) is mandatory for 99.95%.
   - Shared 4-WAF baseline (S1) vs. Shared 6-WAF pool (+2 buffer, S1+2): Adding +2 active WAFs/site ensures 1 node can run isolated canary policy/firmware tests (<= 17% exposure) and 1 node can suffer an unplanned r2800 SSD failure while K=4 nodes still carry 100% peak load with 0% outage.
   - 2-Node WAF HA Pair (W2b): Simple HA and possible first-failure WebSocket connection mirroring (ONLY with licensed+provisioned LTM+AWAF; max 2 devices; resets on 3rd failover and resets on failback — unchanged in BIG-IP 21.1.x). Leaves 0 local WAF redundancy during maintenance.
   - Preferred 2 + 2 Reserve (W3): Saves only 4 WAFs vs. W1-3 while introducing reserve contention and policy sync drift.
   - Asymmetric 3 Site 1 / 2 Site 2 (W4a): Weak Site 2 DR maintenance headroom.
   - Shared Load Balancer + WAF (S2): Out of current scope; breaks tenant LTM boundaries and fails 25% impact cap (100% blast radius).

2. Confirmed r2800 Hardware Mapping (Bottom Band):
   - Max 2 F5OS tenants/r2800 (F5OS-A 1.8.0+) -> 4 tenant LTM pairs consolidate onto 4 r2800s/site (8 total).
   - WAF tier: W1-3 (2-tenant F5OS @ 4 vCPU / 12 GB) = 6 r2800s/site (12 total) vs. S1+2 (full-box @ 8 vCPU / 24 GB) = 6 r2800s/site (12 total).
   - Both finalists = 20 r2800 boxes total. Remember single 480 GB NVMe SSD (no RAID-1), no FPGA (benchmark TPS/RPS!), and no STP (dual-homed F5OS-A LACP LAGs, K000152319).""",
)


# Slide 7 — Discussion 4: Plain-English Topology Variant Scorecard
s = new_slide()
header(
    s,
    "TECH-LEAD DISCUSSION • 4 OF 7",
    "Topology variant scorecard: 25% impact, 99.95% & recovery",
    "4-tenant / 2-site Load Balancer + WAF comparison (excludes DNS & Firewalls). Exact timing codes & r2800 sizing formulas in Speaker Notes.",
    badge_fill=NAVY,
    tsize=20.8,
)
score_rows = [
    ("Dedicated 3-WAF / tenant (W1-3)", "16 + 24 = 40\n(20 r2800s @ 2/box*)", "PASS\n(≤ 25% / 1 tenant)", "Very Strong\n(local N-2)", "1–2 WAFs: 0–16s + App auto\nFull tier: Remote WAF / Site move", "Hardest isolation & N-2;\nhighest box count if 1/box"),
    ("Dedicated 2-WAF / tenant (W1-2)", "16 + 16 = 32\n(16 r2800s @ 2/box*)", "PARTIAL (≤ 25% ten,\n50% cap loss on 1 fault)", "Moderate\n(needs Remote WAF)", "1 WAF: 0–16s + App auto\nMaint+fault: Remote WAF / Site DR", "Saves 8 WAFs vs 3-WAF;\n0 local N-2 on 4/yr upgrades"),
    ("Shared 6-WAF (+2 buffer, S1+2)", "16 + 12 = 28\n(20 r2800s full-box*)", "COND. PASS (1 canary\n≤ 17%; needs policy gate)", "Very Strong\n(+2 buffer)", "1–2 WAFs: 0–16s + App auto\nFull tier: Remote WAF / Site move", "Full 24 GB RAM + canary;\nbad global push can > 25%"),
    ("Shared 4-WAF baseline (S1)", "16 + 8 = 24", "TIGHT (1 node = 25%;\nno canary cushion)", "Strong if peak\n≤ 2 WAFs only", "1 WAF: 0–16s + App auto\nMaint+fault (high load): throttled", "Lowest shared WAF count;\nno +2 rolling/canary margin"),
    ("Preferred 2 + 2 Reserve (W3)", "16 + 20 = 36", "PASS normal /\nMED reserve risk", "Strong\n(if uncontended)", "1–2 WAFs: ~16s via reserve\nContention: Site move / Manual DR", "Dedicated normal path;\nsaves only 4 WAFs; complex"),
    ("2-Node HA / Asymmetric (W2b/W4a)", "32 / 36", "PARTIAL (0 maint N-2;\nSite 2 fragile in W4a)", "Moderate /\nAsymmetric", "1st WAF: ~3s HA + App auto\nMaint+fault: Remote WAF / Site DR", "Simple HA / 1st WS mirror;\nno canary or horizontal scale"),
    ("Shared Load Bal + WAF (S2 — OOS)", "4 + 8 = 12", "FAIL (100% —\nall 4 tenants)", "Lowest\nConfidence", "Bad LB/WAF push:\nmins–hrs Manual rollback", "Fewest devices (12);\nbreaks tenant LB & 25% cap"),
]
# y=1.26, headh=0.40, 7 rows * 0.64 = 4.48 => ends at y=6.14 (clean gap before banner at y=6.22!)
simple_table(
    s,
    ["Topology Variant (Slide 6 Ref)", "LB + WAF\n(2 sites)", "≤ 25% Impact Cap", "99.95% Tier-1\n(4 chg/yr)", "Longest Outage &\nAuto / Manual", "Key Trade-Off"],
    score_rows,
    0.38,
    1.26,
    [2.60, 1.50, 1.95, 1.32, 2.65, 2.55],
    rowh=0.64,
    fs=8.0,
    headh=0.40,
    aligns=[PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.LEFT, PP_ALIGN.LEFT],
)
add_text(
    s,
    "*Confirmed r2800 refresh: Dedicated 3-WAF (2-tenant @ 12 GB) and Shared 6-WAF (full-box @ 24 GB) both need 20 boxes. Always add Client Recovery (secs auto vs mins+ manual user refresh) & Server Recovery (secs–2m auto vs mins–hrs manual DR).",
    0.38,
    6.22,
    12.57,
    0.52,
    8.1,
    True,
    NAVY,
    PP_ALIGN.CENTER,
    PALEYELLOW,
    GOLD,
)
legend_bar(
    s,
    "Key:  N-2 = Survives 2 simultaneous losses (maint + failure)  •  Tier-1 = Active/Active app (99.95% eligible)  •  OOS = Out of Scope  •  Engineering codes (W1–W4, S1–S2, T1–T12) in Speaker Notes & Appendix",
)
footer(s, 7)
set_notes(
    s,
    """SPEAKER NOTES — SLIDE 7 (TECH-LEAD DISCUSSION 4: VARIANT SCORECARD DETAILS)

1. Detailed Recovery Timings (ALWAYS Add Both T6a Client-Side and T6b Server-Side Recovery):
   - T6a (Client-Side): Seconds if client implements auto retry/backoff/jitter/reconnect/replay; minutes+ (human-speed outage!) if users must manually refresh, re-login, restart a desktop client, or re-enter lost work.
   - T6b (Server-Side): Seconds to ~1–2 min if externalized session store + fast warmup; escalates to T5 (minutes to hours) if passive-site app startup, manual DB promotion, or operator restarts are needed (Tier 2 Warm DR apps -> realistic 99.9%–99.5%, NOT 99.95% combined).
   - Single active WAF loss (W1-3, W1-2, S1, S1+2): 0s (planned graceful drain via Receive Disable K12818) to ~16s (unplanned LTM monitor timeout T2, 5s/16s default + Action On Service Down = Reject K15095). Automated R0/R1.
   - Maintenance + 2nd simultaneous WAF/SSD failure:
     * Dedicated 3-WAF (W1-3) & Shared 6-WAF (S1+2): 0s–16s + T6a/T6b (Automated R0/R1 — surviving pool carries peak load).
     * Dedicated 2-WAF (W1-2) & 2-Node HA (W2b): Entire local tenant WAF tier lost -> ~16s + T6a/T6b Automated R2 ONLY if Remote WAF borrow (X2A) is pre-built; otherwise ~46–150s + T6a/T6b Automated R3 GTM site move (or Manual T5 minutes–hours if passive-site app startup is required!).
     * Shared 4-WAF baseline (S1): Survives if peak load fits K <= 2 WAFs; degrades/throttles if K = 3–4.
   - Whole site loss (X2C): ~46–150s + T6a/T6b Automated R3 for Tier 1 Active/Active apps; minutes to hours (T5 + T4 + T6a/T6b) Manual R4 for Tier 2 passive-startup apps.

2. Why Shared 6-WAF (S1+2) Requires Declarative Governance to Pass the <= 25% Impact Cap:
   - Hardware failure of 1 node in S1+2 = 0% service impact (5 of 6 nodes still up).
   - Isolated 1-node canary testing = <= 17% exposure (passes <= 25% cap).
   - Risk: Pushing a broken global WAF config/signature update to all 6 nodes at once would impact 100% (all 4 tenants) with silent 403 blocks!
   - Mitigation: Declarative config-as-code (AS3 / Declarative WAF), Parent/Child security policies, Administrative Partitions + Route Domains, Scheduled/Manual ASM Live Updates (liveupdate.allowautoinstallonsecondary=false, K82512024), 7-day staging, business-transaction H6 synthetics, and fast emergency 403 bypass runbook.""",
)


# Slide 8 — Discussion 5: End-to-End Sticky Sessions, Client-IP Headers, Source NAT & Throughput
s = new_slide()
header(
    s,
    "TECH-LEAD DISCUSSION • 5 OF 7",
    "Consistent path: sticky sessions, client-IP headers, Source NAT & speed",
    "Align every hop (Network/FW → Load Balancer → WAF → Cloud FW/ELB → App) so traffic runs fast in steady state and recovers cleanly.",
    badge_fill=NAVY,
    tsize=19.6,
)
path_rows = [
    (
        "Stateless\nWeb / API",
        "Symmetric LACP/FW; split-TCP + TLS reuse; HTTP multiplexing; multi-IP Source NAT + X-Forwarded-For",
        "Stateless active pool; trust X-Forwarded-For; keep-alive + TLS cache to Cloud ELB; offload caching/gzip",
        "Least Conn; no sticky cookie; preserve X-Forwarded-For (or inject own if ELB terminates TLS); fast drain",
        "Client: auto retry + jitter (no user refresh) • Server: stateless, idempotent writes, read trusted client-IP header",
    ),
    (
        "Stateful Web\n(Sticky\nSessions)",
        "Split-TCP + HTTP multiplexing (honors Keep-Alive cookies); stateless CARP hash to WAF; Source NAT + XFF",
        "Pass Cloud ELB/app sticky cookie untouched; trust X-Forwarded-For; keep-alive to ELB; graceful sticky drain",
        "Single app-node sticky owner: ELB cookie routes ANY WAF to right App Node; preserve/inject XFF",
        "Client: silent re-auth/resume (no manual re-login) • Server: externalized session store (sticky = speed, not SPOF)",
    ),
    (
        "WebSocket /\nReal-Time",
        "FW/NAT timeouts > ping; WebSocket profile; NO HTTP multiplexing; fast reset on down; Source NAT + XFF",
        "WebSocket profile + WAF policy; trust X-Forwarded-For; do not rely on connection mirroring across >2 nodes",
        "Pin established WebSocket stream to target; ELB timeout > ping; preserve/inject XFF on Upgrade",
        "Client: auto reconnect + jitter + resubscribe • Server: durable cursor & gap replay (avoid manual restart)",
    ),
    (
        "Non-Web /\nLayer-4",
        "Low-overhead L4 forwarding; Source-IP / CARP affinity; inline no-SNAT (or Source NAT + PROXY Protocol)",
        "Bypasses external WAF tier (where permitted by security policy) for lowest latency & L4 safety",
        "Cloud FW stateful allow + L4 ELB passthrough keeping raw IP or PROXY Protocol; fast local eject",
        "Client: auto protocol reconnect + DNS re-lookup • Server: safe transaction replay & PROXY Protocol parsing",
    ),
]
# y=1.26, headh=0.40, 4 rows * 1.04 = 4.16 => ends at y=5.82 (clean gap before banner at y=5.94!)
simple_table(
    s,
    ["App Class", "Network, Load Balancer & Source NAT", "WAF Pool (AWAF)", "Cloud FW & Cloud ELB", "App Recovery (Client Auto / Server Auto)"],
    path_rows,
    0.38,
    1.26,
    [1.36, 3.00, 2.65, 2.68, 2.88],
    rowh=1.04,
    fs=8.2,
    headh=0.40,
    aligns=[PP_ALIGN.CENTER, PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.LEFT],
)
add_text(
    s,
    "Client-IP, TLS Cert & Correlation Rules: First Layer-7 TLS terminator (LTM, WAF, or Cloud ELB) strips untrusted headers, injects X-Forwarded-For (XFF) & X-Correlation-ID, and runs automated TLS/mTLS cert renewal. Use multi-IP Source NAT Pools (not single-IP Automap) for L3 asymmetry, remote WAF route-back & HTTP multiplexing.",
    0.38,
    5.94,
    12.57,
    0.78,
    8.5,
    True,
    NAVY,
    PP_ALIGN.CENTER,
    PALEYELLOW,
    GOLD,
)
legend_bar(
    s,
    "Key:  LACP = Link Aggregation  •  CARP = Stateless consistent hash  •  XFF = X-Forwarded-For client-IP header  •  ELB = Cloud Load Balancer  •  SPOF = Single Point of Failure  •  F5 KBs in Speaker Notes",
)
footer(s, 8)
set_notes(
    s,
    """SPEAKER NOTES — SLIDE 8 (TECH-LEAD DISCUSSION 5: STICKY SESSIONS, CLIENT-IP, TLS/mTLS, SNAT & F5 PROFILES)

1. Client-IP & TLS/mTLS Termination Contract (Baseline Invariant + Guardrail #1):
   - Pattern A (TLS terminated at LTM — standard web): LTM strips untrusted external XFF, injects real external client IP + X-Correlation-ID, and validates partner mTLS certs where required -> AWAF enables Trust X-Forwarded-For (K4816) -> Cloud ELB preserves/appends XFF -> App reads trusted edge position.
   - Pattern B (TLS terminated at WAF): LTM->WAF must NOT use plain SNAT without PROXY Protocol; WAF strips/injects XFF; ELB preserves/appends.
   - Pattern C (TLS passthrough to Cloud ELB / K8s Ingress): Cloud ELB MUST inject its own XFF / X-Real-IP header, and upstream LTM/WAF/CFW MUST preserve raw external client IP (inline no-SNAT) or pass PROXY Protocol v2. (Note: WAF cannot inspect L7 payloads in TLS passthrough.)
   - Pattern D (AT4 Non-Web L4): Prefer inline no-SNAT where routing is symmetric, or SNAT Pool + PROXY Protocol; avoid rotating SNAT pools for IP-ACL apps or passive FTP (K15249, K21151342).
   - Certificate Automation: Automate TLS/mTLS renewal via enterprise PKI/CLM or BIG-IP 21.1+ native ACMEv2 with 30/14/7-day alerts (expired cert = 100% outage!).

2. F5 High-Throughput & Persistence Engineering Details (Exact KBs — App Classes AT1–AT4):
   - Split-TCP optimization: f5-tcp-wan (client-side, K10281257) + f5-tcp-lan (server-side, K37412295) + TLS 1.3 session resumption.
   - OneConnect (K7208) + Cookie Persistence (K7964, K83419154, K000149855): Mandatory on HTTP/1.1 Keep-Alive virtual servers using cookie persistence so BIG-IP evaluates cookies per HTTP request rather than pinning reused TCP sockets to the first pool member.
   - CRITICAL LTM->AWAF OneConnect Rule (K9816): When LTM runs OneConnect in front of AWAF, you MUST pair it with SNAT Pool + XFF (and Trust XFF on AWAF) OR OneConnect Source Mask = 255.255.255.255 (K85357500), otherwise AWAF attributes Client B's requests to Client A's IP.
   - Stateless CARP Hash Persistence (K11362): Zero persistence-table RAM, zero mirroring needed across LTM HA peers, minimal disruption when 1 WAF node leaves/joins. Avoid Source-IP persistence for partner web behind shared NAT gateways (causes hot-spotting).
   - Hard Profile Incompatibilities: NEVER combine OneConnect with WebSocket profile (K000151124 — breaks AT3); HTTP/2 full-proxy is incompatible with OneConnect, Hash/SSL persistence, and HA connection mirroring (K95032535); FastL4 (K09948701) runs in software TMM on r2800 (no ePVA FPGA) and remains the lowest-overhead path for AT4.

3. SNAT Pool Port-Exhaustion & Retry-Storm Guardrails:
   - Single-IP SNAT Automap caps at ~65,535 concurrent connections per unique backend socket (K7820, K8246, K33355231), divided across TMM cores (K35043645). Size multi-IP SNAT Pools per tenant/tier, alert on 01010201 (K63275550). Auto Last Hop (K13876) solves L2 only, not routed L3.
   - Enforce client retry exponential backoff + jitter + LTM/WAF rate limits so T6a reconnect storms do not saturate 8-vCPU r2800s.""",
)


# Slide 9 — Discussion 6: Joint Responsibility Matrix by Fault Domain (Plain English)
s = new_slide()
header(
    s,
    "TECH-LEAD DISCUSSION • 6 OF 7",
    "Joint responsibility matrix: infra & app obligations per fault domain",
    "Clear ownership, expected outage duration (F5 measured vs. Huawei Cloud TBD on Slide 10), and automation boundaries across every layer.",
    badge_fill=NAVY,
    tsize=20.0,
)
fd_rows = [
    ("1. Global DNS (GTM)", "Node: 0–3s\nSite: ~1–3m + App", "Automated", "Dual-site DNS; zone-pinned probers; separate ext/int VIP L7 checks; 30s TTL; upgrade DNS first", "Client: respect DNS TTLs & re-resolve on error • Server: own & version /health/ready contract"),
    ("2. Network & Edge FW", "Link/peer: 0–10s\nEdge: ~1–3m + App", "Automated", "2×2 HA edge FWs; dual-homed LACP LAGs (no STP); align FW idle timeouts above app pings & keep-alives", "Client: auto retry + jitter & WebSocket reconnect (no manual restart) • Server: tolerate brief drops"),
    ("3. Tenant Load Bal HA", "1 peer: ~3s + App\nBoth: ~1–3m + App", "Auto (HA / Site)\nManual if no remote", "Redundant HA; stop TCP false-greens; fast dead-socket reject; multi-IP Source NAT + XFF + cert auto-renew", "Client: auto reconnect dropped sockets • Server: idempotent writes on resets; read trusted XFF"),
    ("4. WAF Pool (AWAF)", "1–2 WAFs: 0–16s\nTier: ~16s Remote", "Auto (Pool/Borrow)\nManual 403 bypass", "Shared 6-WAF or Dedicated 3-WAF; config-as-code (AS3); remote logs + auto rebuild; 1-node canary", "Client: auto WS reconnect (no WAF mirror reliance) • Server: co-own canary & 403 synthetic checks"),
    ("5. Int. FW & Cloud FW", "Int FW: ~3–10s\nCFW: TBD (Slide 10)", "Auto HA / Site\n(if no false-green)", "Separate internal VIP health from external; L7 probes MUST cross logical CFW (remote WAF cannot bypass CFW)", "Server: expose lightweight /health/ready behind Cloud FW so outage triggers automatic site steering"),
    ("6. Cloud ELB / Ingress", "Target / HA / Loss:\nTBD (Slide 10)", "Automated\n(measure T10)", "Own single stateful app-node sticky cookie; inject XFF & X-Correlation-ID if terminating TLS; Slow Start + drain", "Server: expose Pod/VM readiness & graceful shutdown hooks (HTTP 503 / drain) for zero-downtime deploys"),
    ("7. K8s / VM & Deps", "Pod/Node/VM: TBD\nApp B1: ~5–16s B2", "Auto (Local/B2)\nManual DB/Storage", "Enforce multi-node K8s & multi-host VM anti-affinity; stable App B VIP + pre-approved Site 1→2 fallback", "Server: PDB + preStop drain; split critical vs optional deps; circuit breakers; external sessions; rolling DB"),
    ("8. Whole Site / DR", "Tier 1: ~1–3m+App\nTier 2: mins–hrs", "Auto (Tier 1 Act/Act)\nManual (Tier 2 DR)", "Size Site 2 LB/WAF, Source NAT, Cloud FW & ELB for 100% 4-tenant DR surge; sync policies & certs", "Client: re-resolve cleanly • Server: replicate state & automate startup/DB failover for Tier 1 99.95%"),
]
# y=1.24, headh=0.38, 8 rows * 0.56 = 4.48 => ends at y=6.10 (clean gap before banner at y=6.18!)
simple_table(
    s,
    ["Fault Domain", "Longest Outage", "Auto / Manual", "Infrastructure Obligations", "Application Obligations (Client Auto / Server Auto)"],
    fd_rows,
    0.38,
    1.24,
    [1.76, 1.56, 1.32, 4.00, 3.93],
    rowh=0.56,
    fs=7.6,
    headh=0.38,
    aligns=[PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.CENTER, PP_ALIGN.LEFT, PP_ALIGN.LEFT],
)
add_text(
    s,
    "Warning: Poorly architected clients (forcing manual user refresh/re-login), manual Tier-2 server/DB DR, expired TLS certs, or unmonitored WAF 403 blocks turn seconds-scale infra failovers into minutes-to-hours outages.",
    0.38,
    6.18,
    12.57,
    0.54,
    8.5,
    True,
    NAVY,
    PP_ALIGN.CENTER,
    PALEGREEN,
    GREEN_LINE,
)
legend_bar(
    s,
    "Key:  Tier 1 = Active/Active (99.95% eligible)  •  Tier 2 = Active/Passive Warm DR (99.9–99.5%)  •  TBD = Huawei Cloud timings on Slide 10  •  Full RACI, T1–T12 & KBs in Speaker Notes & 18-slide Appendix",
)
footer(s, 9)
set_notes(
    s,
    """SPEAKER NOTES — SLIDE 9 (TECH-LEAD DISCUSSION 6: FAULT-DOMAIN RUNBOOK, RACI & ACCEPTANCE GATES)

1. Codified T6a vs. T6b vs. T5 Recovery Expectations (Verify Per App in Phase 0–1):
   - T6a (Client-Side Application Recovery): Automated retry with backoff/jitter, DNS re-resolution, silent token refresh, WebSocket reconnect/resubscribe/replay = SECONDS (supports 99.95%). If NOT architected well -> users must manually refresh browsers, re-login, restart desktop clients, or re-enter lost work = MINUTES+ (human-speed outage).
   - T6b (Server-Side Application & State Recovery): Externalized/replicated session store, clean DB/service pool reset, Pod/VM warmup, idempotent transaction reconciliation = SECONDS to ~1–2 MIN (supports 99.95%).
   - T5 (Manual Server-Side / Operational Recovery): Passive-site app startup, manual DB failover/promotion, clearing hung server pools, bad-config rollback = MINUTES to HOURS (burns 262.8 min/yr budget fast).

2. Cross-Team RACI Matrix (future_architecture_improvements.md §15D):
   - GTM / LTM / r2800 lifecycle, SNAT pools & X2A/X2B F5 config: F5/ADC = R/A; NetSec/Cloud/SecOps = C; App = I.
   - Edge FW, Internal FW, LACP LAGs & X2A/XD1 routing/FW rules: NetSec = R/A; F5/Cloud/SecOps = C; App = I.
   - Private-Cloud CFW, Cloud ELB sticky cookie, ELB XFF injection & T9–T12 measurements: Cloud Platform = R/A; F5/NetSec/App = C; SecOps = I.
   - /health/ready contract, Tier 1/2/3 classification, T6a/T6b automation & DB DR: Application Teams = R/A; F5/Cloud = C.
   - WAF Parent/Child policies, declarative config-as-code, canary sign-off & emergency 403 bypass: Security Ops = R/A; F5/App = C.
   - TLS/mTLS certificate lifecycle & expiry automation: F5/Cloud = R (per hop); App/Partner Owner = A.
   - End-to-end H6 business synthetics, X-Correlation-ID & 99.95% SLO reporting: F5/Cloud/App = R; Joint Accountability.

3. Exact Technical Reference Map (Option 2: Primary Deck + Engineering Reference Appendix):
   - Phase 0 Day 1–30 executable checklist: enterprise-scenarios/phase0_discovery_and_signoff_checklist.md.
   - Full fault-domain matrix & 6 operational guardrails: enterprise-scenarios/future_architecture_improvements.md (§15B, §15C, §15D).
   - 18-slide Engineering Reference Appendix (Architecture Planes, Health Placement H1–H6, GTM Convergence, App B Cascade, Cross-Site X2A/X2B/XD1, Implementation Sequence, Appendix A T1–T12, Appendix B Cloud Platform T9–T12 Placeholders, Appendix C Glossary): management-artifacts/EnterpriseWAF_Engineering_Reference.pptx / .pdf.""",
)


# Slide 10 — Discussion 7: Private-Cloud Platform Recovery Placeholders (CFW, ELB, Kubernetes & VM)
s = new_slide()
header(
    s,
    "TECH-LEAD DISCUSSION • 7 OF 7",
    "Private-cloud platform recovery: CFW, ELB, Kubernetes & VM",
    "Huawei private-cloud timings remain TBD until measured — do NOT substitute F5 timers. Expected behaviour & Phase 0 validation gates:",
    badge_fill=NAVY,
    tsize=20.2,
)
cloud_rows = [
    (
        "Cloud Firewall\n(Logical CFW\nEdge • T9)",
        "• Single HA member failover\n• Site-local CFW path loss\n• Two-site logical common-mode or false-green",
        "TBD — measure\n(p50 / p95 / p99)\nHuawei Cloud",
        "HA member: Automated — new flows continue; verify if in-flight TCP/WS survive state sync or reset (+Client retry). Local path loss: local app unreachable (remote WAF cannot bypass CFW) → Global DNS site move if L7 probes cross CFW (else unbounded false-green).",
        "Map physical HA pairs, state sync & shared control-plane blast radius across Site 1 & Site 2; verify L7 probes traverse CFW.",
    ),
    (
        "Cloud ELB /\nIngress\n(T10)",
        "• Single backend target eject\n• ELB instance HA / VIP takeover\n• Whole local ELB service loss",
        "TBD — measure\n(p50 / p95 / p99)\nHuawei Cloud",
        "Target eject: Automated (no DNS TTL); in-flight on failed target resets (+Client retry) & sticky cookie re-pins to healthy node. ELB HA: VIP stays up; verify TCP/WS persistence vs. reset. Whole ELB loss: triggers DNS site move ONLY if L7 probes cross ELB.",
        "Record probe interval × threshold, target withdrawal time, sticky/WS HA failover behaviour, XFF injection & Slow Start drain.",
    ),
    (
        "Kubernetes\nPod & Worker\nNode (T11)",
        "• Single Pod crash / rolling deploy\n• Worker-node loss & reschedule\n• Ingress / CNI / control-plane loss",
        "TBD — measure\nService vs.\nRedundancy",
        "Pod crash/deploy: Automated — surviving Pods serve traffic (preStop + PDB keeps rolling deploys zero-drop). Worker-node loss: service restores once ELB/Endpoints eject dead Pods (requires multi-node anti-affinity); redundancy restores after eviction + image pull + PVC attach + warmup.",
        "Measure Endpoint→ELB propagation, node-eviction timer, PVC detach/attach & warmup; enforce multi-node anti-affinity + PDB.",
    ),
    (
        "VM &\nHypervisor\nHost (T12)",
        "• Single VM crash behind ELB\n• Hypervisor host HA restart\n• Shared cluster / storage / rebuild",
        "TBD — measure\nService vs.\nRedundancy",
        "Single VM crash: Automated ELB eject (surviving VMs on other hosts absorb traffic). Host HA loss: Automated HA restarts VM on healthy host (minutes for OS boot + storage attach + app warmup + Slow Start). Cluster/storage loss: DNS site move (Tier 1) or manual DR/rebuild (Tier 2).",
        "Enforce VM anti-affinity across physical hosts; measure host HA detection, OS boot, storage re-attach & guest readiness.",
    ),
]
# y=1.24, headh=0.38, 4 rows * 1.08 = 4.32 => ends at y=5.94 (clean gap before banner at y=6.04!)
simple_table(
    s,
    [
        "Platform Layer",
        "Failure Scenarios",
        "Measured Timing",
        "Expected Behaviour (In-Flight vs. New Traffic & Auto / Manual)",
        "Phase 0 Validation Gate (Cloud + App)",
    ],
    cloud_rows,
    0.38,
    1.24,
    [1.48, 2.26, 1.32, 4.41, 3.10],
    rowh=1.08,
    fs=7.7,
    headh=0.38,
    aligns=[PP_ALIGN.CENTER, PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.LEFT, PP_ALIGN.LEFT],
)
add_text(
    s,
    "Measurement Rule: Separate SERVICE restoration (surviving peers absorb traffic) from REDUNDANCY restoration (failed Pod/VM replaced). Compose only critical-path stages without double-counting, then add Client (T6a) & Server (T6b) recovery.",
    0.38,
    6.04,
    12.57,
    0.66,
    8.5,
    True,
    NAVY,
    PP_ALIGN.CENTER,
    PALEYELLOW,
    GOLD,
)
legend_bar(
    s,
    "Key:  TBD = To Be Measured on Huawei Private Cloud (Phase 0 Checklist §5)  •  PDB = PodDisruptionBudget  •  PVC = Persistent Volume Claim  •  T9–T12 sub-codes in Engineering Reference Slides 16–17",
)
footer(s, 10)
set_notes(
    s,
    """SPEAKER NOTES — SLIDE 10 (TECH-LEAD DISCUSSION 7: PRIVATE-CLOUD PLATFORM RECOVERY PLACEHOLDERS T9–T12)

1. Why These Placeholders Matter (Do Not Invent or Reuse F5 Timers):
   - F5 timings (T1 ~3s HA, T2 ~16s pool, T4 ~46–150s GTM/DNS) apply ONLY to the F5 BIG-IP layer.
   - Huawei on-premises private-cloud tiers (CFW T9, Cloud ELB T10, Kubernetes T11, VM/Hypervisor T12) have completely separate health probes, state-sync mechanics, eviction timers, and HA restart characteristics — all MUST be measured under representative load in Phase 0 (enterprise-scenarios/phase0_discovery_and_signoff_checklist.md §5).

2. Exact Engineering Sub-Codes (analysis_variables_and_f5_assumptions.md & future_architecture_improvements.md §15C.1):
   - T9 (Logical CFW Edge across Site 1 & Site 2):
     * T9A: 1 CFW HA member fails -> new flows continue; validate whether active TCP/WS connections survive state sync or reset (+T6a).
     * T9B: Entire local CFW enforcement path fails -> local app unreachable (X2A remote WAF CANNOT bypass CFW) -> requires GTM R3 site move.
     * T9C: CFW false-green (monitoring stops at WAF) -> unbounded outage; ALSO test two-site shared control-plane common-mode failure risk.
   - T10 (Cloud ELB / Ingress):
     * T10a: Backend target withdrawal (probe interval x unhealthy threshold + routing propagation); sticky cookie re-pins to healthy node.
     * T10b: ELB instance HA / VIP takeover; validate existing TCP/WS/sticky survival vs. reset.
     * T10c: Whole local ELB service loss -> triggers GTM R3 site move only if H3/H4 L7 probes cross ELB.
   - T11 (Kubernetes Pod & Worker Node):
     * T11a: Single Pod crash / rolling deploy (readiness probe + Endpoints/kube-proxy/ELB withdrawal; preStop + PDB keeps deploys R0).
     * T11b: Worker-node failure (node-not-ready timeout + taint eviction + reschedule + image pull + PVC detach/attach + pod warmup). Service restores when Endpoints/ELB eject dead Pods (requires multi-node anti-affinity!); redundancy restores minutes later after rescheduling.
     * T11c: Ingress controller, CNI, control-plane, or shared storage failure (distinguish surviving data plane from full outage).
   - T12 (VM & Hypervisor Host):
     * T12a: Guest/app crash behind ELB (ELB health check withdrawal; surviving VMs on other hosts absorb traffic).
     * T12b: Hypervisor host failure -> HA detection + placement + OS boot + storage/network attach + app warmup + ELB Slow Start (requires multi-host anti-affinity so service stays up during minutes-scale VM restart).
     * T12c: Shared compute/storage failure or manual VM rebuild (R3 site move for Tier-1 Active/Active; manual T5 for Tier-2 Warm DR).""",
)

prs.save(OUT)
print(OUT)
