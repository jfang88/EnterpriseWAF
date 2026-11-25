"""Build the concise Executive & Tech-Lead Discussion Deck (9 slides + full Speaker Notes).

Structure:
  Part 1 — Core Themes in 3 Slides (for Technical Leadership / Management):
    Slide 1: Theme 1 — Joint Responsibility for 99.95% Availability & <= 25% Impact
    Slide 2: Theme 2 — Layered Health Checks & Proportional Recovery
    Slide 3: Theme 3 — WAF Topology Decision (S1+2 vs. W1-3) & 90-Day Roadmap

  Part 2 — Tech-Lead Deep-Dive Discussion Slides (Slides 4-9):
    Slide 4: Current-State End-to-End Topology (authoritative SVG + tech-lead notes)
    Slide 5: Target Layered Health Monitoring (authoritative SVG + tech-lead notes)
    Slide 6: Visual WAF Topology Options (authoritative SVG + r2800 rebuild notes)
    Slide 7: Topology Variant Scorecard (<= 25% impact, 99.95%, longest outage, auto/manual)
    Slide 8: End-to-End Path Consistency — Sticky Sessions, Client-IP Headers, SNAT & Throughput
    Slide 9: Joint Responsibility Matrix by Fault Domain (Infra vs. App obligations)

Technical details (r2800 hardware specs, BIG-IP 17.5.x -> 21.1.x+ migration, F5 KBs,
OneConnect/CARP/SNAT mechanics, and T1-T9 timings) are placed in PowerPoint Speaker Notes
so the slides stay clean and scannable while preserving full engineering depth.
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
OUT = ROOT / "EnterpriseWAF_Discussion_Deck.pptx"

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


def footer(s, n, total=9, bg_bar=False):
    if bg_bar:
        add_text(s, "", 0.0, 7.08, 13.333, 0.42, 8.0, False, SLATE, fill=BG_SVG, radius=False)
    add_text(
        s,
        "End-to-end application delivery — executive & tech-lead discussion  •  Hardware (r2800), F5 KBs & timings in Speaker Notes",
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
# PART 1 — CORE THEMES IN 3 SLIDES (FOR TECHNICAL LEADERSHIP / MANAGEMENT)
# =============================================================================

# Slide 1 — Theme 1: Joint Responsibility, 99.95% Availability & <= 25% Impact
s = new_slide()
header(
    s,
    "EXECUTIVE THEME 1 OF 3",
    "Resilience is a joint responsibility across infrastructure & apps",
    "Meeting 99.95% availability (including planned changes) and a ≤ 25% impact cap requires clear contracts at every layer.",
    badge_fill=TEAL,
)

# Top 3 KPI callout tiles
kpis = [
    ("99.95% Total Availability", "4h 23m / year combined\nmanaged + unmanaged outages", NAVY),
    ("≤ 25% Max Impact Cap", "Max 1 of 4 tenants affected\n& ≤ 25% canary / node blast radius", TEAL),
    ("4 Changes / Yr per Stack", "~36 change waves / year\nmust roll with zero user outage", NAVY2),
]
for i, (kt, ks, kc) in enumerate(kpis):
    kx = 0.45 + i * 4.22
    add_text(s, kt, kx, 1.30, 3.98, 0.36, 12.0, True, WHITE, PP_ALIGN.CENTER, kc, kc)
    add_text(s, ks, kx, 1.68, 3.98, 0.64, 10.0, True, DARK, PP_ALIGN.CENTER, LIGHT, MID)

# Two-pillar Joint Responsibility visual + Center Contract Bridge
card(
    s,
    "Infrastructure Teams Deliver",
    [
        "Resilient, rolling-upgradeable delivery tiers (DNS, firewalls, LTM, WAF, Cloud FW, ELB)",
        "Consistent high-throughput paths: sticky-session routing, SNAT pools, and real client-IP header propagation",
        "Layer-accurate health checks that stop false-greens and keep single-node failures local",
    ],
    0.45,
    2.50,
    4.65,
    3.28,
    CYAN,
    MID,
    NAVY,
    10.2,
    space_after=8,
)

add_text(
    s,
    "Shared\nContracts\n&\nLayered\nHealth",
    5.45,
    3.26,
    2.43,
    1.95,
    12.5,
    True,
    NAVY,
    PP_ALIGN.CENTER,
    PALEGREEN,
    GREEN_LINE,
)
arrow(s, 5.12, 4.24, 5.42, 4.24, TEAL, width=2.4, both=True)
arrow(s, 7.90, 4.24, 8.20, 4.24, TEAL, width=2.4, both=True)

card(
    s,
    "Application Teams Deliver",
    [
        "Client-side recovery (T6a): auto retry, DNS re-lookup & WS reconnect so users don't manually refresh/re-login",
        "Server-side recovery (T6b): externalized state, fast warmup & rolling updates (avoiding manual T5 restarts)",
        "App-owned L7 readiness (/health/ready) + declared invariants (client-IP tracking, sticky sessions, WS, L4)",
    ],
    8.23,
    2.50,
    4.65,
    3.28,
    GREEN,
    MID,
    TEAL,
    10.2,
    space_after=8,
)

add_text(
    s,
    "Initial delivery starts with the WAF & F5 tier (Phase 1) while aligning Network/Security, Cloud Platform, and Application teams on explicit contracts.",
    0.45,
    5.96,
    12.43,
    0.70,
    10.8,
    True,
    NAVY,
    PP_ALIGN.CENTER,
    PALEYELLOW,
    GOLD,
)
legend_bar(
    s,
    "Key:  LTM = Local Traffic Manager  •  WAF = Web App Firewall  •  ELB = Cloud Load Balancer  •  SNAT = Source NAT  •  T6a = Client recovery (auto vs manual user steps)  •  T6b = Server app/state recovery  •  T5 = Manual startup/DR",
)
footer(s, 1)
set_notes(
    s,
    """SPEAKER NOTES — SLIDE 1 (EXECUTIVE THEME 1: JOINT RESPONSIBILITY, 99.95% & 25% IMPACT)

1. Core Leadership Message:
   - Neither infrastructure HA alone nor application code alone can hit 99.95% (4h 22m 48s / year = 262.8 min/yr) when BOTH managed (planned changes/patching) and unmanaged (unplanned failures) outages count against the same budget.
   - At 4 planned updates/year across ~9 major technology stacks (~36 change waves/year):
     * Rolling zero-downtime R0/R1 maintenance across every tier consumes ~4–12 min/year, leaving ~250 min/yr for genuine unplanned incidents.
     * In contrast, offline App/DB restarts (15–30 min each, 4x/year) burn 180–240+ min/year BEFORE a single unplanned failure happens.
   - Application recovery (T6) MUST be split into two distinct expectations:
     * T6a (Client-Side): Automated retry/reconnect/re-auth/replay takes seconds; if poorly architected, users must manually refresh, re-login, restart clients, or re-enter lost work (minutes+ human-speed outage!).
     * T6b (Server-Side): Automated externalized session lookup, pool reset, and warmup takes seconds–2 min; if manual server/DB intervention is required, it escalates to T5 (minutes to hours).

2. Enterprise Baseline Invariants (Documented in current_architecture_and_invariants.md):
   - Four-tenant extranet estate across 2 independent sites (Site 1 & Site 2); existing tenant LTM HA pairs (2/tenant/site) are retained.
   - Portfolio includes stateless web (AT1), stateful web with potential sticky-session requirements (AT2), WebSocket / long-lived real-time apps (AT3), and non-web / L4 apps (AT4) that may bypass WAF.
   - Real external client-IP tracking is a baseline requirement for selected apps (security, compliance, audit, rate-limiting, IP ACLs) — requiring no-SNAT symmetry, SNAT + X-Forwarded-For (XFF) at the first L7 TLS terminator (LTM, WAF, or Cloud ELB), or PROXY Protocol for L4.
   - Potential <= 25% impact threshold: (a) max 1 of 4 tenants (25%) per fault/change, and (b) <= 25% capacity/canary user exposure.

3. Platform Context (Keep Current vs. Target Separate):
   - Current estate runs BIG-IP 17.5.x (EoTS Jan 1, 2029 per MyF5 K15643). Exact current GTM monitor depth, probers, SNAT, and XFF/TLS termination points are unverified (Phase 0 audit).
   - Confirmed hardware refresh standard: F5 rSeries r2800 pizza boxes ONLY (no VELOS blade chassis, no r4800/r5000+) running F5OS-A 1.8.0+ and BIG-IP 21.1.x+ (EoTS May 5, 2029; BIG-IP Next 20.x EoTS Apr 30, 2025).""",
)


# Slide 2 — Theme 2: Layered Health & Proportional Recovery
s = new_slide()
header(
    s,
    "EXECUTIVE THEME 2 OF 3",
    "Build health checks & recovery at the exact right layer",
    "Keep single-component failures local and automatic; prevent false-greens, path blind spots, and dependency cascades.",
    badge_fill=TEAL,
)

# 4-tier Recovery Ladder visual
tiers = [
    ("1. Local HA & Pool (R0/R1)", "Seconds • Automated", "1 WAF, LTM peer, FW,\nor app node fails\n→ stays inside site", PALEGREEN, GREEN_LINE),
    ("2. Cross-Site Component (R2)", "Seconds • Automated", "Full local WAF tier or\nshared App B fails\n→ X2A / XD1 (App B2)", CYAN, TEAL),
    ("3. Automated Site Move (R3)", "~1–3 min • Automated", "Whole local path, CFW,\nor site unavailable\n→ DNS steers to Site 2", LIGHT, NAVY),
    ("4. Manual / Warm DR (R4/T5)", "Minutes+ • Exception", "Passive app startup, DB\npromotion or manual user\n→ budget risk if frequent", PALERED, RED),
]
for i, (tt, tsub, tbody, tfill, tline) in enumerate(tiers):
    tx = 0.45 + i * 3.16
    add_text(s, tt, tx, 1.34, 2.90, 0.40, 10.6, True, WHITE, PP_ALIGN.CENTER, tline, tline)
    add_text(s, tsub, tx, 1.76, 2.90, 0.32, 9.4, True, tline, PP_ALIGN.CENTER, WHITE, tline)
    add_text(s, tbody, tx, 2.10, 2.90, 1.16, 9.8, False, DARK, PP_ALIGN.CENTER, tfill, tline)
    if i < 3:
        arrow(s, tx + 2.93, 2.34, tx + 3.13, 2.34, NAVY, width=2.2)

# Three clear architectural rules below
rules = [
    (
        "Eliminate False-Greens",
        [
            "A green TCP port on LTM or WAF does NOT prove Cloud FW, ELB, or the app is working.",
            "Global DNS (GTM) must steer on true Layer-7 application readiness crossing the full path.",
        ],
    ),
    (
        "Separate External & Internal Paths",
        [
            "External users traverse Edge FW → LTM → WAF → Cloud FW → ELB.",
            "Internal users traverse Internal FW → Cloud FW → ELB (often bypassing WAF) and need separate VIP health.",
        ],
    ),
    (
        "Contain Shared Dependencies",
        [
            "If shared App B fails in Site 1, App A / C / D must not cascade into a multi-app site failover.",
            "Use App B local-preferred / remote fallback (XD1: B1 → B2) plus bounded timeouts & circuit breakers.",
        ],
    ),
]
for i, (rh, ritems) in enumerate(rules):
    card(s, rh, ritems, 0.45 + i * 4.22, 3.48, 3.98, 2.24, WHITE, MID, NAVY, fs=9.8, space_after=6)

add_text(
    s,
    "Design rule: GTM owns the global site answer, but the health signal must cross the failure domain GTM is deciding about — backed by independent synthetics for true SLO measurement.",
    0.45,
    5.92,
    12.43,
    0.72,
    10.2,
    True,
    NAVY,
    PP_ALIGN.CENTER,
    PALEGREEN,
    GREEN_LINE,
)
legend_bar(
    s,
    "Key:  GTM = BIG-IP DNS  •  VIP = Virtual IP  •  CFW/ELB = Cloud FW / Load Balancer  •  X2A = Remote WAF borrow  •  XD1 = App B1→B2 fallback  •  R0–R4 = Recovery classes (local → manual DR)  •  T5 = Manual server/DR",
)
footer(s, 2)
set_notes(
    s,
    """SPEAKER NOTES — SLIDE 2 (EXECUTIVE THEME 2: LAYERED HEALTH & PROPORTIONAL RECOVERY)

1. Six Coordinated Health Layers (H1–H6):
   - H1 (Native HA): Device/peer liveness (LTM/FW/CFW HA failover; BIG-IP Failover.NetTimeoutSec = 3s, K7249/K10095).
   - H2 (Local Member Health): LTM WAF pool & Cloud ELB member monitors (default 5s/16s). Set LTM Action On Service Down = Reject (K15095) for fast dead-socket cutoff and VS Immediate Action On Service Down = Reject/Drop (K40554304) to stop TCP 3-way handshake false-greens.
   - H3 (External Published VIP): GTM L7 health from external-representative prober or authoritative LTM+iQuery. External FW NAT VIPs require Address + Translation in BIG-IP DNS + TCP 4353 iQuery, which automatically disables VS Auto-Discovery (K14707, K9138).
   - H4 (Internal Published VIP): Separate GTM wide-IP/monitor for delegated internal names crossing Internal FW -> CFW -> ELB -> App.
   - H5 (Shared Dependency): App B service VIP with B1 preferred / B2 fallback (XD1). App A /health/ready must not fail on optional App B degradation (no false-red cascade).
   - H6 (Independent Synthetic): External & internal business-transaction checks measuring actual 99.95% SLO (fault to first successful business transaction).

2. Critical F5 Operational Guardrails:
   - Configure Specific Prober Pools (K08433560) so GTM does not fall back to unroutable LTMs (no route, K000163083) or cause local MAC flapping (K000159606).
   - Avoid duplicate LTM + GTM VS monitors when using iQuery bigip monitor (K5431).
   - Inter-site link loss alone must NEVER withdraw a healthy local site.
   - Upgrade order: ALWAYS upgrade BIG-IP DNS (GTM) first, then run big3d_install on monitored LTMs (K25923322).
   - Graceful maintenance drain: App returns Receive Disable String (K12818); note LTM Disabled still accepts existing persistent sessions whereas Forced Offline blocks all new connections (K13310).

3. Indicative Recovery Timings (Planning Categories T1–T9):
   - Local HA (T1): ~3s+ + T6a/T6b. Local LTM pool eject (T2): up to ~16s + T6a/T6b.
   - Cross-site WAF borrow (X2A): ~16s + T6a/T6b (avoids DNS TTL & app DR; CANNOT bypass local CFW!).
   - Automated GTM site move (T4): ~46s + T6a/T6b (fast L7 + 30s DNS TTL) up to ~150s + T6a/T6b (default 120s direct GTM monitor).
   - T6a (Client-Side): seconds if auto retry/reconnect; minutes+ if users must manually refresh/re-login/restart!
   - T6b (Server-Side): seconds–2 min if automated external state/warmup; escalates to T5 (minutes to hours) if manual startup/DB failover.""",
)


# Slide 3 — Theme 3: WAF Topology Decision (S1+2 vs W1-3) & 90-Day Roadmap
s = new_slide()
header(
    s,
    "EXECUTIVE THEME 3 OF 3",
    "Recommended shortlist (S1+2 vs. W1-3) & 90-day decisions",
    "Retain tenant LTM boundaries; both finalists land at 20 standard appliances on hardware refresh — choice hinges on policy isolation vs. RAM.",
    badge_fill=TEAL,
    tsize=21.2,
)

# Left vs Right Finalist Comparison
card(
    s,
    "Option A — S1+2: Shared Active Pool (+2 Buffer)",
    [
        "4 separate tenant LTM pairs → 6 shared active WAFs/site (4 base + 2 extra)",
        "+2 nodes absorb rolling upgrades + 1 unplanned outage + isolated canary testing",
        "Full appliance memory per WAF; 20 total appliances on hardware refresh",
        "Meets ≤ 25% cap ONLY with strict per-tenant policies & 1-node canary gates (≤ 17%)",
        "Best if: WAF policies are heavy (>12 GB RAM) & change governance is mature",
    ],
    0.45,
    1.30,
    6.05,
    3.12,
    PALEGREEN,
    GREEN_LINE,
    TEAL,
    9.8,
    space_after=6,
)

card(
    s,
    "Option B — W1-3: Dedicated Per-Tenant Pool",
    [
        "Each tenant gets its own dedicated 3-WAF active pool per site (hard N-2)",
        "Hard ≤ 25% (1 of 4 tenants) blast-radius guarantee — zero cross-tenant policy risk",
        "2-tenant appliance virtualization also lands at 20 total boxes (if RAM fits)",
        "Lower-cost W1-2 sub-variant (2 WAFs/tenant) loses local N-2 — requires X2A borrow",
        "Best if: strict physical/policy tenant isolation outweighs shared-pool efficiency",
    ],
    6.83,
    1.30,
    6.05,
    3.12,
    CYAN,
    MID,
    NAVY,
    9.8,
    space_after=6,
)

# Why other options are not default (slim strip)
add_text(
    s,
    "Other variants evaluated (Slide 7):  W1-2 (2 WAF/tenant) lacks maintenance N-2 without X2A  •  W2b (DSC pair) has 0 maintenance N-2  •  W3/W4a save only 4 boxes with added complexity/asymmetry  •  S2 (shared LTM+WAF) fails 25% cap (100% blast radius).",
    0.45,
    4.56,
    12.43,
    0.48,
    9.0,
    False,
    SLATE,
    PP_ALIGN.CENTER,
    LIGHT,
    MID,
)

# 3 Immediate Leadership Decisions / Next 90 Days
steps = [
    ("Decision 1 — Audit (Days 1–30)", "Verify current GTM health, TLS termination/XFF, SNAT & sticky baselines; run WAF RAM benchmark"),
    ("Decision 2 — Contracts (Days 31–60)", "Sign Joint Infra + App fault-domain contracts (Slide 9) & select S1+2 vs. W1-3"),
    ("Decision 3 — Pilot & Prove (Days 61–90)", "Deploy Phase 1 layered L7 health + WAF target; fault-inject rolling upgrade + 2nd outage"),
]
for i, (sh, sb) in enumerate(steps):
    sx = 0.45 + i * 4.22
    add_text(s, sh, sx, 5.20, 3.98, 0.34, 10.4, True, WHITE, PP_ALIGN.CENTER, NAVY, NAVY)
    add_text(s, sb, sx, 5.56, 3.98, 1.08, 9.4, False, DARK, PP_ALIGN.CENTER, PALEYELLOW, GOLD)

legend_bar(
    s,
    "Key:  S1+2 = Shared WAF pool (+2 rolling/outage/canary)  •  W1-3 / W1-2 = Dedicated 3 or 2 WAFs/tenant  •  W2b = 2-node HA cluster  •  W3 = Pref + reserve  •  W4a = Asymmetric  •  S2 = Shared LTM+WAF  •  X2A = Remote WAF borrow",
)
footer(s, 3)
set_notes(
    s,
    """SPEAKER NOTES — SLIDE 3 (EXECUTIVE THEME 3: SHORTLIST, CONFIRMED r2800 REBUILD & 90-DAY PLAN)

1. Confirmed Hardware Refresh Standard (Locked Invariant — NO Blade Chassis):
   - Standard appliance: F5 rSeries r2800 pizza boxes ONLY (no VELOS blade chassis, no r4800/r5000+).
   - Software stack: F5OS-A 1.8.0+ (or 2.0.x) + BIG-IP 21.1.x+ (EoTS May 5, 2029; BIG-IP 21.x drops iSeries/VIPRION/vCMP so parallel rebuild is mandatory).
   - Compute & RAM envelope: 8 usable CPU cores (4 vCPU min/tenant), 32 GB system RAM -> 24 GB usable for tenants (12 GB min/tenant).
   - Multi-tenancy ceiling: Max 2 F5OS tenants per r2800 on F5OS-A 1.8.0+ (only 1 tenant on <= 1.7.x); requires .tar.bundle format (K000158849) and >= 88 GB virtual disk for 21.1.x ALL image (K45191957).

2. Why BOTH Finalists Land at 20 r2800 Appliances Total Across 2 Sites:
   - Tenant LTM tier (both options): 4 tenant HA pairs/site consolidated onto 4 x r2800/site (8 total vs. 16) at 2 isolated LTM tenants/box (A+B on pair 1; C+D on pair 2).
   - S1+2 (Full-Box WAFs): 6 x r2800/site = 12 WAF boxes (each gets full 8 vCPU / 24 GB RAM) -> 8 LTM + 12 WAF = 20 r2800s total.
   - W1-3 (2-Tenant F5OS WAFs): 6 x r2800/site = 12 WAF boxes (A+B on boxes #1-3, C+D on boxes #4-6; each tenant gets 3 isolated 4 vCPU / 12 GB WAFs/site) -> 8 LTM + 12 WAF = 20 r2800s total.
   - Phase 0 Mandatory Gate: Benchmark the heaviest tenant's AWAF policy + TLS load inside 4 vCPU / 12 GB RAM (with remote HSL logging). If it fits with headroom -> W1-3 2-tenant gives hard <= 25% isolation at the same 20-box cost! If AWAF needs > 12 GB RAM -> choose S1+2 full-box (24 GB) with strict Parent/Child policies + 1-node canary gating.

3. Critical r2800 Engineering Guardrails:
   - Single 480 GB NVMe SSD (~447 GB usable, NO RAID-1): 1 SSD failure takes down the entire box -> mandatory K+2 / N-2 multi-box spread, remote HSL logging, and automated cloud-init (BIG-IP 21.1.0+) + UCS rebuild.
   - No FPGA and NO Spanning Tree Protocol (STP) (K000152319, K000151396): max 1 interface/LAG per VLAN -> terminate dual-homed LACP LAGs to MC-LAG/vPC switches managed at the F5OS-A host layer (K1689).
   - Migration validation: Run 'tmsh load sys ucs <file> platform-migrate validate' (K82540512); note BIG-IP 21.1.x in-place upgrade is still experimental (full in 22.0.x), so rolling drain remains mandatory.""",
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
   - Site 1 and Site 2 are independent failure domains. GTM sync shares DNS/health view only — it does NOT sync LTM/WAF/CFW/app config.
   - Distinct security/failure boundaries: Edge Firewalls (2 x 2 HA pairs/tenant/site, NetSec) vs. Internal Firewall (NetSec) vs. Private-Cloud CFW (Cloud Platform).
   - Internal users may bypass the external WAF tier; an internal-FW failure impacts internal users only, whereas a CFW failure impacts BOTH external and internal traffic converging on that CFW.

2. Phase 0 Audit Items (Currently Unknown / Validate):
   - Current BIG-IP 17.5.x GTM monitor type (TCP port vs. HTTP/L7), targets, intervals, timeouts, and NAT Address/Translation mappings (K14707).
   - Whether GTM uses iQuery (TCP 4353) or direct monitors, and whether Site 1/Site 2 GTMs probe cross-site or site-locally only.
   - Current TLS termination hop per application (LTM vs. WAF vs. Cloud ELB), SNAT configuration, X-Forwarded-For injection/trust, and sticky-session ownership.""",
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
   - Because edge GTM sits inside the edge firewall, direct GTM probing validates downstream LTM->WAF->CFW->ELB->App readiness, while an external/extranet-representative vantage or independent synthetic (H6) validates leased-line & outside-in firewall reachability.
   - Keep external (H3) and internal (H4) wide-IP health state separate so an external WAF/edge fault does not withdraw healthy internal access (and vice versa).

2. F5 BIG-IP DNS + LTM Integration Checkpoints:
   - NAT Translation (K14707, K9138): External FW VIP = Address; Private LTM VIP = Translation; permits TCP 4353 iQuery; disables VS Auto-Discovery (manage via AS3/BIG-IQ).
   - Specific Prober Pools (K08433560): Pin exact probers per zone; validate reconnect fallback (K000163083) and avoid non-bigip local MAC flapping (K000159606).
   - No duplicate VS monitors (K5431) when consuming LTM state over iQuery.
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

1. Key Variant Differences to Walk Through with Tech Leads:
   - W1-3 vs. W1-2 sub-variant: W1-3 (3 active WAFs/tenant/site) gives full local N-2 rolling maintenance + hard <= 25% tenant isolation. W1-2 drops the 3rd WAF (saving 8 WAFs = 32 vs. 40), keeping tenant blast radius <= 25%, BUT losing 1 WAF removes 50% of that tenant's capacity and maintenance + 2nd fault removes 100% of that tenant's local WAF tier -> X2A remote WAF borrow is mandatory for 99.95%.
   - S1 baseline (4/site) vs. S1+2 (4+2 = 6/site): Adding +2 active WAFs/site ensures 1 node can run isolated canary policy/firmware tests (<= 17% exposure) and 1 node can suffer an unplanned r2800 SSD failure while K=4 nodes still carry 100% peak load with 0% outage.
   - W2b (DSC pair): Simple HA and possible first-failure WebSocket connection mirroring (ONLY with licensed+provisioned LTM+AWAF; max 2 devices; resets on 3rd failover and resets on failback — unchanged in BIG-IP 21.1.x). Leaves 0 local WAF redundancy during maintenance.
   - W3 (preferred pair + 2 shared reserve/site): Saves only 4 WAFs vs. W1-3 while introducing reserve contention and policy sync drift.
   - W4a (asymmetric 3 S1 / 2 S2): Weak Site 2 DR maintenance headroom.
   - S2 (shared LTM + shared WAF): Out of current scope; breaks tenant LTM boundaries and fails 25% impact cap (100% blast radius).

2. Confirmed r2800 Hardware Mapping (Bottom Band):
   - Max 2 F5OS tenants/r2800 (F5OS-A 1.8.0+) -> 4 tenant LTM pairs consolidate onto 4 r2800s/site (8 total).
   - WAF tier: W1-3 (2-tenant F5OS @ 4 vCPU / 12 GB) = 6 r2800s/site (12 total) vs. S1+2 (full-box @ 8 vCPU / 24 GB) = 6 r2800s/site (12 total).
   - Both finalists = 20 r2800 boxes total. Remember single 480 GB NVMe SSD (no RAID-1) and no STP (dual-homed F5OS-A LACP LAGs, K000152319).""",
)


# Slide 7 — Discussion 4: Clean Topology Variant Scorecard
s = new_slide()
header(
    s,
    "TECH-LEAD DISCUSSION • 4 OF 6",
    "Topology variant scorecard: 25% impact, 99.95% & recovery",
    "4-tenant / 2-site LTM + WAF comparison (excludes GTM & FWs). Exact T1–T9 & r2800 sizing formulas in Speaker Notes.",
    badge_fill=NAVY,
    tsize=21.0,
)
score_rows = [
    ("W1-3 (3 WAF / tenant / site)", "16 + 24 = 40\n(20 r2800s @ 2/box*)", "PASS\n(≤ 25% / 1 tenant)", "Very Strong\n(local N-2)", "1–2 WAF: 0–16s + T6a/b (Auto)\nFull tier: X2A or R3", "Hardest isolation & N-2;\nhighest box count if 1/box"),
    ("W1-2 sub-variant (2 WAF / tenant)", "16 + 16 = 32\n(16 r2800s @ 2/box*)", "PARTIAL (≤ 25% ten,\n50% cap loss on 1 fault)", "Moderate\n(requires X2A)", "1 WAF: 0–16s + T6a/b (Auto)\nMaint+fault: X2A / R3 / T5", "Saves 8 WAFs vs W1-3;\n0 local N-2 on 4/yr upgrades"),
    ("S1+2 (4+2 = 6 shared WAF / site)", "16 + 12 = 28\n(20 r2800s full-box*)", "COND. PASS (1 canary\n≤ 17%; needs policy gate)", "Very Strong\n(+2 buffer)", "1–2 WAF: 0–16s + T6a/b (Auto)\nFull tier: X2A / R3 (4-ten)", "Full 24 GB RAM + canary;\nbad global push can > 25%"),
    ("S1 baseline (4 shared WAF / site)", "16 + 8 = 24", "TIGHT (1 node = 25%;\nno canary cushion)", "Strong if K ≤ 2\nonly", "1 WAF: 0–16s + T6a/b (Auto)\nK>2 maint+fault: throttled", "Lowest shared WAF count;\nno +2 rolling/canary margin"),
    ("W3 (2 pref + 2 reserve / site)", "16 + 20 = 36", "PASS normal /\nMED reserve risk", "Strong\n(if uncontended)", "1–2 WAF: ~16s + T6a/b (res.)\nContention: R2 / R3 / T5", "Dedicated normal path;\nsaves only 4 WAFs; complex"),
    ("W2b (DSC pair) / W4a (asym)", "32 / 36", "PARTIAL (0 maint N-2;\nW4a Site 2 fragile)", "Moderate /\nAsymmetric", "1st WAF: ~3s + T6a/b (Auto)\nMaint+fault: X2A / R3 / T5", "Simple HA / 1st WS mirror;\nno canary or horizontal scale"),
    ("S2 (Shared LTM + WAF — OOS)", "4 + 8 = 12", "FAIL (100% —\nall 4 tenants)", "Lowest\nConfidence", "Bad LTM/WAF push:\nmins+ Manual rollback (T5)", "Fewest devices (12);\nbreaks tenant LTM & 25% cap"),
]
# y=1.26, headh=0.40, 7 rows * 0.64 = 4.48 => ends at y=6.14 (clean gap before banner at y=6.22!)
simple_table(
    s,
    ["Topology Variant", "LTM + WAF\n(2 sites)", "≤ 25% Impact Cap", "99.95%\n(4 chg/yr)", "Longest Outage &\nAuto / Manual", "Key Trade-Off"],
    score_rows,
    0.38,
    1.26,
    [2.45, 1.55, 2.00, 1.32, 2.60, 2.65],
    rowh=0.64,
    fs=8.1,
    headh=0.40,
    aligns=[PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.LEFT, PP_ALIGN.LEFT],
)
add_text(
    s,
    "*Confirmed r2800 refresh: W1-3 (2-tenant @ 12 GB/WAF) and S1+2 (full-box @ 24 GB/WAF) both need 20 boxes. Add T6a (client: secs auto vs mins+ manual user refresh) & T6b (server: secs–2m auto vs T5 manual startup/DB).",
    0.38,
    6.22,
    12.57,
    0.52,
    8.2,
    True,
    NAVY,
    PP_ALIGN.CENTER,
    PALEYELLOW,
    GOLD,
)
legend_bar(
    s,
    "Key:  X2A = Remote WAF borrow  •  R0/R1 = Zero-impact/local auto  •  R2 = Cross-site component  •  R3 = Auto site/DNS move  •  R4/T5 = Manual/warm DR  •  T6a/T6b = Client/Server app recovery  •  OOS = Out of Scope",
)
footer(s, 7)
set_notes(
    s,
    """SPEAKER NOTES — SLIDE 7 (TECH-LEAD DISCUSSION 4: VARIANT SCORECARD DETAILS)

1. Detailed Recovery Timings (ALWAYS Add Both T6a Client-Side and T6b Server-Side Recovery):
   - T6a (Client-Side): Seconds if client implements auto retry/backoff/reconnect/replay; minutes+ (human-speed outage!) if users must manually refresh, re-login, restart a desktop client, or re-enter lost work.
   - T6b (Server-Side): Seconds to ~1–2 min if externalized session store + fast warmup; escalates to T5 (minutes to hours) if passive-site app startup, manual DB promotion, or operator restarts are needed.
   - Single active WAF loss (W1-3, W1-2, S1, S1+2): 0s (planned graceful drain via Receive Disable K12818) to ~16s (unplanned LTM monitor timeout T2, 5s/16s default + Action On Service Down = Reject K15095). Automated R0/R1.
   - Maintenance + 2nd simultaneous WAF/SSD failure:
     * W1-3 & S1+2: 0s–16s + T6a/T6b (Automated R0/R1 — surviving pool carries peak load).
     * W1-2 & W2b: Entire local tenant WAF tier lost -> ~16s + T6a/T6b Automated R2 ONLY if X2A remote WAF borrow is pre-built; otherwise ~46–150s + T6a/T6b Automated R3 GTM site move (or Manual T5 minutes+ if passive-site app startup is required!).
     * S1 baseline (4/site): Survives if peak load fits K <= 2 WAFs; degrades/throttles if K = 3–4.
   - Whole site loss (X2C): ~46–150s + T6a/T6b Automated R3 for Active/Active apps; minutes to hours (T5 + T4 + T6a/T6b) Manual R4 for passive-startup apps.

2. Why S1+2 Requires Strict Change Governance to Pass the <= 25% Impact Cap:
   - Hardware failure of 1 node in S1+2 = 0% service impact (5 of 6 nodes still up).
   - Isolated 1-node canary testing = <= 17% exposure (passes <= 25% cap).
   - Risk: Pushing a broken global WAF config/signature update to all 6 nodes at once would impact 100% (all 4 tenants).
   - Mitigation: Parent/Child security policies, Administrative Partitions + Route Domains, Scheduled/Manual ASM Live Updates (liveupdate.allowautoinstallonsecondary=false, K82512024), 7-day Enforcement Readiness staging, and mandatory 1-node canary verification before rolling promotion.""",
)


# Slide 8 — Discussion 5: End-to-End Sticky Sessions, Client-IP Headers, SNAT & Throughput
s = new_slide()
header(
    s,
    "TECH-LEAD DISCUSSION • 5 OF 6",
    "Consistent path: sticky sessions, client-IP headers, SNAT & throughput",
    "Align every hop (Network/FW → LTM → WAF → Cloud FW/ELB → App) so traffic runs fast in steady state and fails cleanly.",
    badge_fill=NAVY,
    tsize=19.8,
)
path_rows = [
    (
        "AT1:\nStateless\nWeb / API",
        "Symmetric LACP/FW; split-TCP + TLS reuse; HTTP connection multiplexing; multi-IP SNAT + XFF",
        "Stateless active pool; trust XFF; keep-alive + TLS cache to ELB; offload heavy caching/gzip",
        "Least Conn; no sticky cookie; preserve XFF (or inject own XFF if ELB terminates TLS); fast drain",
        "T6a: auto client retry/backoff (no user refresh) • T6b: stateless, idempotent writes, read trusted XFF",
    ),
    (
        "AT2:\nStateful\nWeb",
        "Split-TCP + HTTP multiplexing (honors Keep-Alive cookies); stateless CARP hash to WAF; SNAT + XFF",
        "Pass ELB/app sticky cookie untouched; trust XFF; keep-alive to ELB; graceful sticky drain",
        "Single app-node sticky owner: ELB cookie routes ANY WAF to right App Node; preserve/inject XFF",
        "T6a: silent re-auth/resume (no manual re-login) • T6b: externalized session store (sticky = speed, not SPOF)",
    ),
    (
        "AT3:\nWebSocket /\nReal-Time",
        "FW/NAT timeouts > ping; WebSocket profile; NO HTTP multiplexing; fast reset on down; SNAT + XFF",
        "WebSocket profile + WAF policy; trust XFF; do not rely on connection mirroring across N > 2",
        "Pin established WS stream to target; ELB timeout > ping; preserve/inject XFF on Upgrade",
        "T6a: auto reconnect + backoff + resubscribe • T6b: durable cursor & sequence-gap replay (avoid manual restart)",
    ),
    (
        "AT4:\nNon-Web /\nLayer-4",
        "Low-overhead L4 forwarding; Source-IP / CARP affinity; inline no-SNAT (or SNAT + PROXY Protocol)",
        "Bypasses external WAF tier (where permitted by security policy) for lowest latency & L4 safety",
        "Cloud FW stateful allow + L4 ELB passthrough keeping raw IP or PROXY Protocol; fast H2 eject",
        "T6a: auto protocol reconnect & DNS re-lookup • T6b: safe transaction replay & PROXY Protocol parsing",
    ),
]
# y=1.26, headh=0.40, 4 rows * 1.04 = 4.16 => ends at y=5.82 (clean gap before banner at y=5.94!)
simple_table(
    s,
    ["App Class", "Network, LTM & SNAT", "WAF Pool (AWAF)", "CFW & Cloud ELB", "App Recovery (T6a Client / T6b Server)"],
    path_rows,
    0.38,
    1.26,
    [1.34, 3.00, 2.65, 2.70, 2.88],
    rowh=1.04,
    fs=8.3,
    headh=0.40,
    aligns=[PP_ALIGN.CENTER, PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.LEFT],
)
add_text(
    s,
    "Client-IP & SNAT Principle: The FIRST Layer-7 TLS terminator (LTM, WAF, or Cloud ELB) strips untrusted headers and injects X-Forwarded-For (XFF). Use multi-IP SNAT Pools (not single-IP Automap) for L3 asymmetry, cross-site route-back & HTTP multiplexing; keep raw IP or PROXY Protocol when TLS passes through to ELB or legacy L4.",
    0.38,
    5.94,
    12.57,
    0.78,
    8.7,
    True,
    NAVY,
    PP_ALIGN.CENTER,
    PALEYELLOW,
    GOLD,
)
legend_bar(
    s,
    "Key:  AT1–AT4 = Stateless / Stateful / WebSocket / L4 app classes  •  LACP = Link Aggregation  •  CARP = Stateless consistent hash  •  XFF = X-Forwarded-For  •  SNAT = Source NAT  •  T6a/T6b = Client/Server app recovery  •  H2 = Local health",
)
footer(s, 8)
set_notes(
    s,
    """SPEAKER NOTES — SLIDE 8 (TECH-LEAD DISCUSSION 5: STICKY SESSIONS, CLIENT-IP, SNAT & F5 PROFILES)

1. Client-IP Tracking by TLS Termination Point (Baseline Invariant):
   - Pattern A (TLS terminated at LTM — standard web): LTM strips untrusted external XFF & injects real external client IP -> AWAF enables Trust X-Forwarded-For (K4816) -> Cloud ELB preserves/appends XFF -> App reads trusted edge position.
   - Pattern B (TLS terminated at WAF): LTM->WAF must NOT use plain SNAT without PROXY Protocol; WAF strips/injects XFF; ELB preserves/appends.
   - Pattern C (TLS passthrough to Cloud ELB / K8s Ingress): Cloud ELB MUST inject its own XFF / X-Real-IP header, and upstream LTM/WAF/CFW MUST preserve raw external client IP (inline no-SNAT) or pass PROXY Protocol v2. (Note: WAF cannot inspect L7 payloads in TLS passthrough.)
   - Pattern D (AT4 Non-Web L4): Prefer inline no-SNAT where routing is symmetric, or SNAT Pool + PROXY Protocol; avoid rotating SNAT pools for IP-ACL apps or passive FTP (K15249, K21151342).

2. F5 High-Throughput & Persistence Engineering Details (Exact KBs):
   - Split-TCP optimization: f5-tcp-wan (client-side, K10281257) + f5-tcp-lan (server-side, K37412295) + TLS 1.3 session resumption.
   - OneConnect (K7208) + Cookie Persistence (K7964, K83419154, K000149855): Mandatory on HTTP/1.1 Keep-Alive virtual servers using cookie persistence so BIG-IP evaluates cookies per HTTP request rather than pinning reused TCP sockets to the first pool member.
   - CRITICAL LTM->AWAF OneConnect Rule (K9816): When LTM runs OneConnect in front of AWAF, you MUST pair it with SNAT Pool + XFF (and Trust XFF on AWAF) OR OneConnect Source Mask = 255.255.255.255 (K85357500), otherwise AWAF attributes Client B's requests to Client A's IP.
   - Stateless CARP Hash Persistence (K11362): Zero persistence-table RAM, zero mirroring needed across LTM HA peers, minimal disruption when 1 WAF node leaves/joins. Avoid Source-IP persistence for partner web behind shared NAT gateways (causes hot-spotting).
   - Hard Profile Incompatibilities: NEVER combine OneConnect with WebSocket profile (K000151124 — breaks AT3); HTTP/2 full-proxy is incompatible with OneConnect, Hash/SSL persistence, and HA connection mirroring (K95032535); FastL4 (K09948701) runs in software TMM on r2800 (no ePVA FPGA) and remains the lowest-overhead path for AT4.

3. SNAT Pool Port-Exhaustion Guardrail:
   - Single-IP SNAT Automap caps at ~65,535 concurrent connections per unique backend socket (K7820, K8246, K33355231), divided across TMM cores (K35043645).
   - Always size a multi-IP SNAT Pool per tenant/tier for one-arm L3 asymmetry, cross-site X2A/X2B (K95573163), or OneConnect multiplexing, and monitor 01010201 exhaustion warnings (K63275550). Auto Last Hop (K13876) solves L2 same-subnet return only, not routed L3 through stateful firewalls.""",
)


# Slide 9 — Discussion 6: Joint Responsibility Matrix by Fault Domain
s = new_slide()
header(
    s,
    "TECH-LEAD DISCUSSION • 6 OF 6",
    "Joint responsibility matrix: infra & app obligations per fault domain",
    "Clear ownership, expected outage duration (incl. T6a client vs. T6b server), and automation boundaries across every layer.",
    badge_fill=NAVY,
    tsize=20.2,
)
fd_rows = [
    ("1. DNS / BIG-IP GTM", "Node: 0–3s\nSite: ~1–3m + T6a/b", "Automated", "Dual-site GTM; zone-pinned probers; separate ext/int VIP L7 checks; 30s TTL; upgrade GTM first", "T6a: respect DNS TTLs & re-resolve on error • T6b: own & version /health/ready contract"),
    ("2. Network & Edge FW", "Link/peer: 0–10s\nEdge: ~1–3m + T6a/b", "Automated", "2×2 HA edge FWs; dual-homed LACP LAGs; align FW idle timeouts above app/WAF pings & keep-alives", "T6a: auto client retry + WS ping/reconnect (no manual user restart) • T6b: tolerate brief drops"),
    ("3. Tenant LTM HA", "1 peer: ~3s + T6a/b\nBoth: ~1–3m + T6a/b", "Auto (HA/R3)\nManual if no X2B", "Redundant HA; stop TCP false-greens; fast dead-socket reject; OneConnect/CARP; multi-IP SNAT + XFF", "T6a: auto reconnect dropped sockets • T6b: idempotent writes on HA resets; read trusted XFF"),
    ("4. WAF Pool (AWAF)", "1–2 WAF: 0–16s\nTier: ~16s X2A / R3", "Auto (pool/X2A)\nManual rollback", "S1+2 or W1-3 headroom; remote logs + automated rebuild; Trust XFF; pass sticky cookies; 1-node canary", "T6a: auto WS reconnect (no WAF mirroring reliance) • T6b: co-own canary policy sign-off"),
    ("5. Int. FW & Cloud FW", "Peer: ~3–10s\nCFW: ~1–3m + T6a/b", "Auto HA / R3\n(if no false-green)", "Separate internal VIP health from external; L7 probes MUST cross Cloud FW (X2A cannot bypass CFW)", "T6b: expose lightweight /health/ready behind Cloud FW so outage triggers automatic site steering"),
    ("6. Cloud ELB / Ingress", "Node: 0–10s\nELB: ~1–3m + T6a/b", "Automated", "Own single AT2 app-node sticky cookie; inject/append XFF if terminating TLS; Slow Start + drain", "T6b: expose Pod/VM readiness & graceful shutdown hooks (HTTP 503 / drain) for zero-downtime deploys"),
    ("7. App & Shared Deps", "Node: 0–10s\nApp B1: ~5–16s XD1", "Auto (R0–R2)\nManual DB (T5)", "Stable App B service VIP with fast reject + pre-approved B1 → B2 cross-site fallback routing", "T6b: separate critical vs optional deps; circuit breakers; external session store; rolling DB/app updates"),
    ("8. Whole Site / DR", "Act/Act: ~1–3m+T6\nPassive: mins+ (T5)", "Auto (Act/Act)\nManual (Passive)", "Size Site 2 LTM/WAF, SNAT Pools, Cloud FW & ELB for 100% 4-tenant DR surge; sync policies/certs", "T6a: client re-resolves cleanly • T6b/T5: replicate state & automate startup/DB failover (avoid manual DR)"),
]
# y=1.24, headh=0.38, 8 rows * 0.56 = 4.48 => ends at y=6.10 (clean gap before banner at y=6.18!)
simple_table(
    s,
    ["Fault Domain", "Longest Outage", "Auto / Manual", "Infrastructure Obligations", "Application Obligations (T6a Client / T6b Server)"],
    fd_rows,
    0.38,
    1.24,
    [1.76, 1.56, 1.28, 4.02, 3.95],
    rowh=0.56,
    fs=7.7,
    headh=0.38,
    aligns=[PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.CENTER, PP_ALIGN.LEFT, PP_ALIGN.LEFT],
)
add_text(
    s,
    "Warning: If client-side recovery (T6a) is poorly architected, even a 3–16s automated infra failover forces users into manual refresh/re-login/restart (minutes+); manual server/DB startup (T5) similarly breaks 99.95%.",
    0.38,
    6.18,
    12.57,
    0.54,
    8.7,
    True,
    NAVY,
    PP_ALIGN.CENTER,
    PALEGREEN,
    GREEN_LINE,
)
legend_bar(
    s,
    "Key:  T6a = Client recovery (secs auto vs mins+ manual user action)  •  T6b = Server app/state recovery (secs–2m auto)  •  T5 = Manual server/DB DR (mins–hrs)  •  X2A/X2B/X2C = Remote WAF / Remote Front-End / Site DR  •  XD1 = App B1→B2",
)
footer(s, 9)
set_notes(
    s,
    """SPEAKER NOTES — SLIDE 9 (TECH-LEAD DISCUSSION 6: FAULT-DOMAIN RUNBOOK & ACCEPTANCE GATES)

1. Codified T6a vs. T6b vs. T5 Recovery Expectations (Verify Per App in Phase 0–1):
   - T6a (Client-Side Application Recovery): Automated retry with backoff/jitter, DNS re-resolution, silent token refresh, WebSocket reconnect/resubscribe/replay = SECONDS (supports 99.95%). If NOT architected well -> users must manually refresh browsers, re-login, restart desktop clients, or re-enter lost work = MINUTES+ (human-speed outage).
   - T6b (Server-Side Application & State Recovery): Externalized/replicated session store, clean DB/service pool reset, Pod/VM warmup, idempotent transaction reconciliation = SECONDS to ~1–2 MIN (supports 99.95%).
   - T5 (Manual Server-Side / Operational Recovery): Passive-site app startup, manual DB failover/promotion, clearing hung server pools, bad-config rollback = MINUTES to HOURS (burns 262.8 min/yr budget fast).

2. Exact Technical Reference Map (Cross-Reference to Authoritative Markdown):
   - Full fault-domain matrix with all F5 KB links: enterprise-scenarios/future_architecture_improvements.md (§15B & §15C).
   - Full 17-slide technical reference deck (including Architecture Planes, Health Placement table, GTM Convergence flow, Cross-Site X2A/X2B/XD1 details, Implementation Sequence, Appendix A T1–T9 with T6a/T6b, and Appendix B Executive Glossary): management-artifacts/EnterpriseWAF_Management_Summary.pptx / .pdf.

3. Key Cross-Team Acceptance Gates Before Claiming 99.95% & <= 25% Impact Readiness:
   - Gate 1: External (H3) and Internal (H4) VIP Layer-7 readiness contracts signed by App + NetSec + F5 teams.
   - Gate 2: Single WAF / backend failure stays local R0/R1 (Action On Service Down = Reject, K15095; VS Immediate Action = Reject, K40554304).
   - Gate 3: Inter-site link loss alone tested while both sites are healthy — must NEVER withdraw a healthy local site.
   - Gate 4: AT1–AT4 sticky sessions, XFF/ELB header injection (per TLS termination hop), multi-IP SNAT Pool sizing, and NO OneConnect on WebSockets (K000151124) verified under load.
   - Gate 5: Rolling upgrade wave (including F5OS-A host reboot on r2800) + simultaneous injected 2nd node failure + 1-node canary (<= 25% cap) passed with GTM upgraded first + big3d_install (K25923322).
   - Gate 6: r2800 dual-homed LACP LAG (no STP, K000152319), remote HSL logging (single-SSD safety), cloud-init rebuild, and platform-migrate validate (K82540512) validated before production cutover.""",
)

prs.save(OUT)
print(OUT)
