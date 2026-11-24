from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.oxml import parse_xml
from pptx.oxml.ns import nsdecls

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "EnterpriseWAF_Management_Summary.pptx"
prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

NAVY = RGBColor(6, 55, 95)
NAVY2 = RGBColor(11, 76, 116)
TEAL = RGBColor(15, 139, 141)
CYAN = RGBColor(220, 245, 248)
GREEN = RGBColor(223, 245, 193)
PURPLE = RGBColor(237, 232, 255)
PURPLE_LINE = RGBColor(92, 76, 210)
LIGHT = RGBColor(246, 249, 252)
MID = RGBColor(219, 230, 239)
DARK = RGBColor(22, 36, 50)
ORANGE = RGBColor(209, 119, 20)
WHITE = RGBColor(255, 255, 255)
RED = RGBColor(190, 49, 68)
SLATE = RGBColor(74, 91, 107)
GOLD = RGBColor(226, 191, 80)
PALEGREEN = RGBColor(235, 248, 233)
PALEYELLOW = RGBColor(255, 247, 220)
PALERED = RGBColor(255, 240, 240)
FONT = "Liberation Sans"


def slide():
    return prs.slides.add_slide(prs.slide_layouts[6])


def add_text(
    s,
    text,
    x,
    y,
    w,
    h,
    size=14,
    bold=False,
    color=DARK,
    align=PP_ALIGN.LEFT,
    fill=None,
    line=None,
    radius=True,
    anchor=MSO_ANCHOR.MIDDLE,
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
    tf.margin_left = tf.margin_right = Inches(0.10)
    tf.margin_top = tf.margin_bottom = Inches(0.06)
    p = tf.paragraphs[0]
    p.text = text
    p.alignment = align
    p.font.name = FONT
    p.font.size = Pt(size)
    p.font.bold = bold
    p.font.color.rgb = color
    return sh


def box(s, text, x, y, w, h, fill=CYAN, line=NAVY, size=11, bold=True):
    return add_text(s, text, x, y, w, h, size, bold, DARK, PP_ALIGN.CENTER, fill, line)


def arrow(s, x1, y1, x2, y2, color=NAVY, width=2, dash=False, both=False):
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


def title(s, t, st=None, tsize=22):
    add_text(s, t, 0.45, 0.16, 12.45, 0.46, tsize, True, NAVY, radius=False)
    if st:
        add_text(s, st, 0.47, 0.66, 12.35, 0.30, 10.3, False, SLATE, radius=False)


def footer(s, n):
    add_text(s, "End-to-end application delivery summary", 0.48, 7.18, 4.2, 0.18, 8.0, False, SLATE, radius=False)
    add_text(s, f"Nov 2026  •  {n}", 11.55, 7.18, 1.25, 0.18, 8.0, False, SLATE, PP_ALIGN.RIGHT, radius=False)


def bullet_block(s, heading, items, x, y, w, h, fill=LIGHT, line=MID, headfill=NAVY, fs=10.5):
    add_text(s, heading, x, y, w, 0.42, 12.5, True, WHITE, PP_ALIGN.CENTER, headfill, headfill)
    sh = s.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(x),
        Inches(y + 0.48),
        Inches(w),
        Inches(h - 0.48),
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
    tf.margin_left = tf.margin_right = Inches(0.18)
    tf.margin_top = Inches(0.16)
    tf.margin_bottom = Inches(0.10)
    for idx, item in enumerate(items):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        p.text = "• " + item
        p.alignment = PP_ALIGN.LEFT
        p.space_after = Pt(7)
        p.font.name = FONT
        p.font.size = Pt(fs)
        p.font.color.rgb = DARK


def simple_table(s, headers, rows, x, y, colw, rowh=0.46, fs=9.2, headh=None, aligns=None):
    hh = headh if headh is not None else rowh
    xx = x
    for i, h in enumerate(headers):
        add_text(s, h, xx, y, colw[i], hh, fs + 0.3, True, WHITE, PP_ALIGN.CENTER, NAVY, NAVY)
        xx += colw[i]
    yy = y + hh
    for r, row in enumerate(rows):
        xx = x
        f = LIGHT if r % 2 == 0 else WHITE
        for i, v in enumerate(row):
            al = aligns[i] if aligns else PP_ALIGN.CENTER
            add_text(s, str(v), xx, yy, colw[i], rowh, fs, False, DARK, al, f, MID)
            xx += colw[i]
        yy += rowh


# Slide 1 — Executive Summary (End-to-End Application Delivery; Initial Focus: WAF Tier)
s = slide()
add_text(
    s,
    "Resilient End-to-End Application Delivery",
    0.5,
    0.42,
    12.3,
    0.62,
    28,
    True,
    WHITE,
    PP_ALIGN.LEFT,
    NAVY,
    NAVY,
)
add_text(
    s,
    "Management summary — full end-to-end delivery (initial Phase 1 focus: WAF tier) • BIG-IP 17.5.x → 21.1.x+ rebuild • 99.95% availability",
    0.52,
    1.14,
    12.30,
    0.42,
    13.0,
    False,
    NAVY,
    radius=False,
)
bullet_block(
    s,
    "End-to-end scope & Phase 1 WAF focus",
    [
        "99.95% availability (managed + unmanaged outages) requires end-to-end resilience across DNS, firewalls, LTM, WAF, private cloud, and apps.",
        "Phase 1 execution focuses on the F5 WAF tier (and LTM/GTM interfaces); firewalls, Cloud FW/ELB, and apps are owned by partner teams.",
        "Keep tenant Local Traffic Manager (LTM) boundaries; evaluate S1 full-box (24 GB) vs. r2800 2-tenant F5OS WAFs (12 GB each) on rebuild.",
    ],
    0.55,
    1.85,
    3.92,
    3.32,
    GREEN,
    MID,
    NAVY,
    9.9,
)
bullet_block(
    s,
    "Target layered health monitoring",
    [
        "Use 6 coordinated health layers (H1–H6), not one monitor.",
        "BIG-IP DNS (GTM) owns global site choice using Layer-7 checks of external & internal Virtual IPs (VIPs) with Specific Prober Pools.",
        "LTM & Cloud Load Balancer (ELB) withdraw failed nodes locally (Action On Service Down = Reject; VS Reject on all-down).",
    ],
    4.70,
    1.85,
    3.92,
    3.32,
    CYAN,
    MID,
    NAVY,
    9.9,
)
bullet_block(
    s,
    "Key management risks to close",
    [
        "Current BIG-IP 17.5.x GTM monitor depth, firewall NAT Translation mappings (K14707), and prober behavior remain unknown / to validate.",
        "Port-up / default TCP handshake checks (K40554304) can show false green while the application is broken.",
        "Partner teams must agree on Layer-7 readiness, graceful drain, and shared-dependency (App B) recovery contracts.",
    ],
    8.85,
    1.85,
    3.92,
    3.32,
    PALEYELLOW,
    ORANGE,
    NAVY,
    9.9,
)
add_text(
    s,
    "Key decision: validate current BIG-IP 17.5.x GTM health first, deliver Phase 1 WAF resilience + layered L7 health, and benchmark AWAF on the confirmed r2800 standard (no blade chassis; Glossary on Slide 16).",
    0.55,
    5.50,
    12.22,
    0.76,
    12.0,
    True,
    NAVY,
    PP_ALIGN.CENTER,
    PALEGREEN,
    RGBColor(92, 164, 82),
)
footer(s, 1)

# Slide 2 — Separate Current State from Target State (+ Team Ownership)
s = slide()
title(
    s,
    "Separate current state from target state (and team boundaries)",
    "Management should clearly see what exists today (BIG-IP 17.5.x) versus what is proposed for the end-to-end target and r2800 rebuild.",
)
bullet_block(
    s,
    "CURRENT / validated baseline (BIG-IP 17.5.x)",
    [
        "2 sites; one BIG-IP DNS (GTM) cluster per site inside the edge firewall",
        "Network/Security team: 2 × HA edge-firewall pairs/site (external VIPs) + separate internal firewall",
        "F5/ADC team: tenant LTM HA pairs (2/tenant/site) + WAF tier (Phase 1 focus) + edge GTM",
        "Cloud Platform team: private-cloud Cloud Firewall (CFW) → Cloud Load Balancer (ELB)",
        "App teams: App A / B / C / D dependencies (mostly active/passive)",
        "BIG-IP 17.5.x (EoTS Jan 2029); current GTM monitor depth & probers: validate",
    ],
    0.55,
    1.22,
    5.92,
    4.72,
    LIGHT,
    MID,
    NAVY,
    10.3,
)
bullet_block(
    s,
    "TARGET / to-be improvement & r2800 rebuild (21.1.x+)",
    [
        "GTM Layer-7 health of external VIPs + NAT Translation & Specific Prober Pools",
        "GTM or authoritative internal LTM / iQuery Layer-7 health of internal VIPs",
        "App-team readiness contracts + Receive Disable graceful drain (K12818)",
        "Dependency-local App B1 → B2 recovery (XD1) where state/data allow",
        "Confirmed hardware rebuild: rSeries r2800 pizza boxes ONLY (F5OS-A 1.8.0+; max 2 tenants/box; no blade chassis)",
        "Single 480 GB SSD (no RAID-1) + no STP → K+2 spread, remote HSL logs, LACP LAGs & cloud-init",
    ],
    6.86,
    1.22,
    5.92,
    4.72,
    PALEGREEN,
    RGBColor(92, 164, 82),
    TEAL,
    10.3,
)
add_text(
    s,
    "Rule: target-state health probes, r2800 F5OS-A rebuild features, and cross-site paths (X2A/X2B/XD1) must not appear on the current-state diagram until deployed and validated.",
    0.55,
    6.20,
    12.23,
    0.56,
    10.6,
    True,
    NAVY,
    PP_ALIGN.CENTER,
    PALEYELLOW,
    GOLD,
)
footer(s, 2)

# Slides 3, 4, 5, 6 — Populated by replace_management_slides.py from authoritative SVGs
for _placeholder_title in (
    "Slide 3 placeholder — replaced by EnterpriseWAF_Architecture_Planes.svg",
    "Slide 4 placeholder — replaced by EnterpriseWAF_End_to_End_Topology.svg",
    "Slide 5 placeholder — replaced by EnterpriseWAF_Target_Health_Monitoring.svg",
    "Slide 6 placeholder — replaced by EnterpriseWAF_Health_Check_Placement.svg",
):
    s = slide()
    add_text(s, _placeholder_title, 1.0, 3.2, 11.3, 0.6, 14, False, SLATE, PP_ALIGN.CENTER, radius=False)

# Slide 7 — GTM Probing & Convergence
s = slide()
title(
    s,
    "BIG-IP DNS (GTM) probing and convergence must be explicit",
    "Cluster synchronization shares global state, but does not automatically mean every GTM directly probes every remote endpoint.",
)
box(s, "Site 1\nGTM cluster", 0.65, 1.38, 2.05, 0.76, GREEN, NAVY, 12)
box(s, "Site 2\nGTM cluster", 10.63, 1.38, 2.05, 0.76, GREEN, NAVY, 12)
arrow(s, 2.74, 1.76, 10.59, 1.76, TEAL, width=2.4, dash=True, both=True)
add_text(
    s,
    "sync group: configuration / health state / probing responsibility",
    4.1,
    1.36,
    5.1,
    0.34,
    9.5,
    True,
    TEAL,
    PP_ALIGN.CENTER,
    radius=False,
)

steps = [
    ("1", "Path fails"),
    ("2", "Local detector\nsees failure"),
    ("3", "GTM gets\nhealth state"),
    ("4", "GTM global state\nconverges"),
    ("5", "DNS answer\nchanges"),
    ("6", "DNS TTL cache\n+ re-lookup"),
    ("7", "App recovery\n(T6)"),
]
for i, (n, t) in enumerate(steps):
    x = 0.45 + i * 1.82
    add_text(s, n, x + 0.56, 2.52, 0.36, 0.34, 10.5, True, WHITE, PP_ALIGN.CENTER, NAVY2, NAVY2)
    add_text(s, t, x, 2.92, 1.48, 0.82, 8.8, True, DARK, PP_ALIGN.CENTER, LIGHT, MID)
    if i < 6:
        arrow(s, x + 1.52, 3.33, x + 1.78, 3.33, NAVY, width=2.0)

bullet_block(
    s,
    "If probes are site-local only",
    [
        "Remote GTM learns failure through synchronization / timeout behavior",
        "Measure that state-learning delay before DNS Time-to-Live (TTL)",
        "Do not assume 30s DNS TTL equals total user failover time",
        "Upgrade BIG-IP DNS before LTM + push big3d health agent (K25923322)",
    ],
    0.65,
    4.18,
    5.8,
    2.48,
    PALEYELLOW,
    ORANGE,
    NAVY,
    9.9,
)
bullet_block(
    s,
    "Target prober rule (official F5 guardrails)",
    [
        "Configure Specific Prober Pools per zone (K08433560; avoid K000163083 fallback)",
        "External FW NAT VIPs need Address + Translation (auto-discovery off, K14707)",
        "Avoid duplicate monitors on both LTM & GTM Virtual Servers (K5431)",
        "Loss of inter-site link alone must never withdraw a healthy local site",
    ],
    6.88,
    4.18,
    5.8,
    2.48,
    PALEGREEN,
    RGBColor(92, 164, 82),
    NAVY,
    9.9,
)
footer(s, 7)

# Slide 8 — Shared Dependency Cascade
s = slide()
title(
    s,
    "Shared dependency failure can create a multi-application outage",
    "End-to-end health design must avoid turning one shared App B failure into App A / C / D site withdrawals (App & Cloud team alignment).",
)
add_text(s, "Current / no dependency-local fallback", 0.6, 1.25, 5.9, 0.42, 13.0, True, RED, PP_ALIGN.CENTER, PALERED, RED)
box(s, "App B local\nFAILS", 2.35, 1.95, 2.35, 0.7, PALERED, RED, 11)
arrow(s, 3.52, 2.65, 1.52, 3.28, RED)
arrow(s, 3.52, 2.65, 3.52, 3.28, RED)
arrow(s, 3.52, 2.65, 5.52, 3.28, RED)
for txt, x in [("App A", 0.75), ("App C", 2.75), ("App D", 4.75)]:
    box(s, txt + "\ntimeout/retry", x, 3.3, 1.55, 0.68, PALEYELLOW, ORANGE, 10)
add_text(
    s,
    "connection pools fill → readiness may fail → GTM can withdraw multiple VIPs → Site 2 surge",
    0.75,
    4.42,
    5.55,
    0.88,
    10.4,
    True,
    RED,
    PP_ALIGN.CENTER,
    PALERED,
    RED,
)
add_text(s, "Target: dependency-local recovery (XD1)", 6.8, 1.25, 5.9, 0.42, 13.0, True, TEAL, PP_ALIGN.CENTER, PALEGREEN, TEAL)
box(s, "App A / D stay local", 7.05, 2.0, 2.15, 0.65, GREEN, NAVY, 11)
box(s, "App B service VIP /\ndiscovery (H5)", 9.65, 2.0, 2.45, 0.65, CYAN, NAVY, 9.8)
arrow(s, 9.22, 2.32, 9.62, 2.32)
box(s, "App B1 (Site 1)\npreferred", 7.75, 3.3, 1.75, 0.68, GREEN, NAVY, 9.8)
box(s, "App B2 (Site 2)\nfallback", 10.2, 3.3, 1.75, 0.68, GREEN, NAVY, 9.8)
arrow(s, 10.88, 2.65, 8.62, 3.28)
arrow(s, 10.88, 2.65, 11.08, 3.28, TEAL, dash=True)
add_text(
    s,
    "B1 failure → withdraw B1 (LTM Reject, K15095) → bounded retry to B2 → App A / D stay in Site 1",
    7.05,
    4.42,
    5.45,
    0.88,
    10.3,
    True,
    NAVY,
    PP_ALIGN.CENTER,
    PALEGREEN,
    RGBColor(92, 164, 82),
)
add_text(
    s,
    "Health contract caution: App A should not report globally unhealthy merely because an optional App B / C feature is degraded.",
    0.85,
    6.08,
    11.63,
    0.54,
    10.4,
    True,
    NAVY,
    PP_ALIGN.CENTER,
    PALEYELLOW,
    GOLD,
)
footer(s, 8)

# Slide 9 — Populated by replace_management_slides.py from EnterpriseWAF_Topology_Options.svg (visual diagrams for W1-W4, S1-S2, F5OS!)
s = slide()
add_text(
    s,
    "Slide 9 placeholder — replaced by EnterpriseWAF_Topology_Options.svg",
    1.0,
    3.2,
    11.3,
    0.6,
    14,
    False,
    SLATE,
    PP_ALIGN.CENTER,
    radius=False,
)

# Slide 10 — 99.95% Availability (Managed + Unmanaged Outages) & Recovery Classes (R0-R4 Explained!)
s = slide()
title(
    s,
    "99.95% total availability (managed + unmanaged outages)",
    "Target benchmark (active WAF pool + layered L7 + X2A/XD1); at 4 changes/yr per stack (~36 waves/yr), every tier must roll cleanly.",
)
# Left panel: 99.95% Total Budget + inline Recovery Class Key (R0-R4)
add_text(s, "99.95% TOTAL budget", 0.45, 1.18, 3.35, 0.38, 12.5, True, WHITE, PP_ALIGN.CENTER, NAVY, NAVY)
add_text(
    s,
    "4h 22m 48s / year\n(21m 54s/mo • ~5m 2s/wk)",
    0.45,
    1.60,
    3.35,
    0.78,
    12.0,
    True,
    WHITE,
    PP_ALIGN.CENTER,
    NAVY2,
    NAVY2,
)
add_text(
    s,
    "Includes BOTH managed (planned changes/patching) & unmanaged (unplanned) outages combined",
    0.45,
    2.44,
    3.35,
    0.66,
    8.9,
    True,
    RED,
    PP_ALIGN.CENTER,
    PALERED,
    RED,
)
bullet_block(
    s,
    "Recovery classes (R0–R4)",
    [
        "R0 — Zero user impact (hidden by HA/pool)",
        "R1 — Auto local recovery (seconds-scale)",
        "R2 — Auto cross-site component / dependency (X2A / X2B / XD1)",
        "R3 — Auto site / DNS failover (TTL + app)",
        "R4 — Manual / warm-DR recovery (minutes+)",
    ],
    0.45,
    3.22,
    3.35,
    2.78,
    LIGHT,
    MID,
    TEAL,
    8.5,
)

rows = [
    ("Planned node maintenance", "Rolling drain (Receive Disable, K12818)", "R0 / R1 (no outage)"),
    ("1 backend / Pod / VM", "Local Cloud ELB / LTM pool (H2)", "R0 / R1 (local auto)"),
    ("1 WAF node", "Local LTM WAF pool (Action=Reject)", "R0 / R1 (local auto)"),
    ("1 LTM HA peer", "HA peer failover (~3s + convergence)", "R1 (local auto)"),
    ("Whole local WAF tier", "Cross-site WAF borrow (X2A) or GTM", "R2 (X2A) or R3"),
    ("Whole external / internal path", "BIG-IP DNS (GTM) L7 steering (H3/H4)", "R3 (site/VIP move)"),
    ("Shared App B local failure", "App B service VIP fallback (H5 / XD1)", "R2 (XD1 local stay)"),
    ("Whole site failure", "BIG-IP DNS (GTM) + Site 2 DR", "R3 (or R4 if manual)"),
]
# y=1.18, headh=0.44, 8 rows * 0.54 = 4.32 => ends at y=5.94 (clean gap before banner at y=6.18!)
simple_table(
    s,
    ["Outage / failure event", "Best recovery domain & tier", "Target recovery class"],
    rows,
    4.00,
    1.18,
    [2.95, 3.65, 2.25],
    rowh=0.54,
    fs=8.8,
    headh=0.44,
)
add_text(
    s,
    "Management test: at 4 updates/yr per stack, rolling R0/R1 changes use ~4–12 min/yr — but offline App/DB restarts can burn 180+ min/yr before 1 failure (K+2 active WAFs protect r2800 single-SSD & host reboots).",
    0.45,
    6.18,
    12.40,
    0.62,
    9.8,
    True,
    NAVY,
    PP_ALIGN.CENTER,
    PALEYELLOW,
    GOLD,
)
footer(s, 10)

# Slide 11 — Cross-Site Contingency Capability (Target R2 Patterns)
s = slide()
title(
    s,
    "Cross-site capability (R2): target contingency, not dependency",
    "Design early where it avoids full site failover; requires Source NAT (SNAT) Pool + X-Forwarded-For (XFF) trust for route-back.",
    tsize=21.5,
)
bullet_block(
    s,
    "X2A — Remote WAF borrow",
    [
        "Local LTM survives; borrows Site 2 WAF pool",
        "Routes traffic back to healthy local Cloud FW / app",
        "Avoids DNS TTL delay & full application DR move",
        "Requires SNAT Pool + HTTP X-Forwarded-For (XFF) + AWAF Trust XFF (K4816)",
        "Cannot bypass a failed local Cloud Firewall (CFW)",
    ],
    0.55,
    1.28,
    3.8,
    4.55,
    PALEGREEN,
    MID,
    TEAL,
    10.0,
)
bullet_block(
    s,
    "X2B — Remote front-end route-back",
    [
        "Local edge FW / LTM / WAF tier lost",
        "Site 2 edge / LTM / WAF receives external client",
        "Routes back over inter-site link to healthy Site 1 Cloud FW / app",
        "Still incurs GTM / DNS Time-to-Live (TTL) convergence",
        "Degraded split-site state; validate firewall symmetry",
    ],
    4.76,
    1.28,
    3.8,
    4.55,
    LIGHT,
    MID,
    TEAL,
    10.0,
)
bullet_block(
    s,
    "XD1 — Dependency fallback (App B)",
    [
        "App A and App D remain running in Site 1",
        "App B service VIP prefers local Site 1 (B1)",
        "Site 2 (B2) acts as lower-priority fallback",
        "Prevents shared App B cascade across multiple apps",
        "Requires bounded timeouts, retry budget & compatible state",
    ],
    8.98,
    1.28,
    3.8,
    4.55,
    GREEN,
    MID,
    TEAL,
    10.0,
)
add_text(
    s,
    "Invariant: healthy local service must never depend on the inter-site link. Always test inter-site network partition while both sites are healthy.",
    0.55,
    6.18,
    12.23,
    0.56,
    10.5,
    True,
    NAVY,
    PP_ALIGN.CENTER,
    PALEYELLOW,
    GOLD,
)
footer(s, 11)

# Slide 12 — Application Types (AT1-AT4) & End-to-End Recovery
s = slide()
title(
    s,
    "Application type (AT1–AT4) determines real recovery time",
    "Infrastructure can recover first while sessions, WebSockets, or business transactions remain broken (App Team responsibility).",
)
cols = [
    (
        "AT1: Stateless web",
        [
            "Safe automated client retry",
            "Idempotency on write calls",
            "External / shared state only",
            "Fast LTM pool member withdrawal",
        ],
    ),
    (
        "AT2: Stateful web",
        [
            "Portable or replicated session state",
            "Re-authentication & session rebuild",
            "Transaction reconciliation",
            "Confirm state parity before DR",
        ],
    ),
    (
        "AT3: WebSocket / real-time",
        [
            "Reconnect + backoff / jitter",
            "Re-auth + resubscribe + replay",
            "AWAF needs WebSocket profile; NO OneConnect (K000151124)",
            "Mirroring max 2 devices & resets on failback (21.1 unchanged)",
        ],
    ),
    (
        "AT4: Non-web / Layer-4",
        [
            "May bypass external WAF tier",
            "Protocol-specific reconnect",
            "DNS / service re-resolution",
            "Safe transaction replay",
        ],
    ),
]
fills = [GREEN, RGBColor(225, 238, 252), PURPLE, RGBColor(224, 244, 242)]
for i, (h, items) in enumerate(cols):
    bullet_block(s, h, items, 0.5 + i * 3.16, 1.28, 2.86, 4.55, fills[i], MID, NAVY, 9.8)
add_text(
    s,
    "GTM Layer-7 health answers “can this endpoint accept new traffic?”; Application recovery (T6) answers “has the user/business flow actually recovered?”",
    0.5,
    6.18,
    12.33,
    0.56,
    10.4,
    True,
    NAVY,
    PP_ALIGN.CENTER,
    PALEGREEN,
    RGBColor(92, 164, 82),
)
footer(s, 12)

# Slide 13 — Four-Tenant Device Counts (EXPLICIT LTM vs WAF Breakdown!)
s = slide()
title(
    s,
    "Four-tenant device counts (LTM + WAF) vs blast radius",
    "Explicit 2-site breakdown across 4 tenants (LTM + WAF devices only; excludes GTM clusters & firewalls) — not vendor pricing.",
)
rows = [
    ("W1 (3 WAF/tenant/site) — dedicated active pool", "16", "24", "40", "Low (per-tenant)"),
    ("W3 — 2 preferred/tenant + 2 shared reserve/site", "16", "20", "36", "Medium (shared reserve)"),
    ("W4a — asymmetric (3 WAF S1 / 2 WAF S2 per tenant)", "16", "20", "36", "Low (weaker Site 2 DR)"),
    ("W1 (2 WAF/tenant) or W2b (2-node WAF cluster + LTM)", "16", "16", "32", "Low (tight maintenance)"),
    ("S1 — tenant LTMs + 4 shared active WAFs/site", "16", "8", "24", "High at WAF tier"),
    ("Rebuild: r2800 2-tenant F5OS WAFs (4c/12G each)*", "8* (2/box)", "12* (2/box)", "20 r2800s*", "Low OS/policy; 2 tenants/box"),
    ("S2 — shared LTM + shared WAF (out of current scope)", "4", "8", "12", "Very high (all tenants)"),
]
# y=1.18, headh=0.46, 7 rows * 0.54 = 3.78 => ends at y=5.42 (clean gap before note & callout!)
simple_table(
    s,
    ["Topology option (see Slide 9 diagrams)", "LTM devices\n(2 sites)", "WAF devices\n(2 sites)", "Total LTM+WAF\n(2 sites)", "Cross-tenant\nblast radius"],
    rows,
    0.45,
    1.18,
    [4.75, 1.50, 1.60, 1.85, 2.75],
    rowh=0.54,
    fs=8.9,
    headh=0.50,
    aligns=[PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.CENTER, PP_ALIGN.CENTER, PP_ALIGN.CENTER],
)
add_text(
    s,
    "*Confirmed r2800 standard (F5OS-A 1.8.0+; no blade chassis): max 2 tenants/r2800 (4 vCPU/12 GB each) halves W1-3 WAF boxes (24→12) & LTM boxes (16→8). If AWAF needs >12 GB RAM, use S1 full-box (8 vCPU/24 GB; K+2 active boxes/site). Single 480 GB SSD (no RAID-1) & no STP.",
    0.45,
    5.50,
    12.45,
    0.54,
    8.4,
    False,
    SLATE,
    PP_ALIGN.LEFT,
    radius=False,
)
add_text(
    s,
    "Health design does not eliminate shared-platform blast radius: a bad shared WAF policy/config or capacity surge in S1/S2 can still impact multiple tenants simultaneously.",
    0.45,
    6.16,
    12.45,
    0.58,
    10.2,
    True,
    NAVY,
    PP_ALIGN.CENTER,
    PALEYELLOW,
    GOLD,
)
footer(s, 13)

# Slide 14 — End-to-End Implementation Sequence & Cross-Team Gates
s = slide()
title(
    s,
    "End-to-end implementation sequence (Phase 1: WAF & F5 tier)",
    "Start with F5/WAF & GTM validation we own directly, while aligning Network/Security, Cloud Platform, and App teams on contracts.",
)
phases = [
    ("0", "Inventory monitors,\nNAT, probers &\nr2800 AWAF RAM"),
    ("1", "Phase 1: WAF tier\ndesign + app L7\ncontracts"),
    ("2", "Implement ext +\nint L7 VIP health\n(F5 + NetSec)"),
    ("3", "Add Specific\nProber Pools &\nH6 synthetics"),
    ("4", "Pilot App B1→B2\nXD1 recovery\n(App + Cloud)"),
    ("5", "Execute r2800\n21.1.x+ rebuild &\nX2A/X2B"),
    ("6", "Fault-inject &\nprove 99.95%\n(mgmt + unmgmt)"),
]
for i, (n, t) in enumerate(phases):
    x = 0.45 + i * 1.82
    add_text(s, n, x + 0.56, 1.18, 0.36, 0.34, 10.5, True, WHITE, PP_ALIGN.CENTER, TEAL, TEAL)
    add_text(s, t, x, 1.58, 1.48, 1.02, 8.4, True, DARK, PP_ALIGN.CENTER, LIGHT, MID)
    if i < 6:
        arrow(s, x + 1.52, 2.09, x + 1.78, 2.09, TEAL, width=2.0)

checks = [
    "external + internal VIP health contracts signed with App/NetSec",
    "1 WAF or backend failure stays local R0/R1 (Action=Reject)",
    "GTM never advertises a broken required service path",
    "inter-site link loss never withdraws a healthy local site",
    "GTM / prober / sync convergence time measured end-to-end",
    "App A / B / C / D cascade & XD1 fallback tested with App teams",
    "AT3 WebSocket / stateful T6 & no-OneConnect verified",
    "managed maintenance + extra failure tested (GTM upgraded first)",
    "r2800 LACP LAG (no STP), HSL logs & platform-migrate validated",
]
add_text(s, "Cross-team acceptance gates before claiming 99.95% readiness", 0.55, 2.95, 7.5, 0.38, 12.5, True, NAVY, radius=False)
for i, ch in enumerate(checks):
    x = 0.55 + (i % 3) * 4.12
    y = 3.48 + (i // 3) * 0.78
    add_text(s, "✓", x, y, 0.30, 0.34, 11, True, TEAL, PP_ALIGN.CENTER, radius=False)
    add_text(s, ch, x + 0.32, y, 3.65, 0.54, 8.8, False, DARK, radius=False)
add_text(
    s,
    "Managed-change safety is part of the 99.95% SLO: never change both sites together; upgrade BIG-IP DNS before LTM (big3d_install); drain one node at a time; preserve rollback.",
    0.55,
    6.16,
    12.25,
    0.60,
    10.0,
    True,
    NAVY,
    PP_ALIGN.CENTER,
    PALEYELLOW,
    GOLD,
)
footer(s, 14)

# Slide 15 — Appendix A: Recovery Timing Shorthand (T1-T9)
s = slide()
title(
    s,
    "Appendix A — recovery timing shorthand (T1–T9)",
    "Planning categories, not vendor SLAs. Always measure end-to-end from fault to the first successful business transaction.",
)
rows = [
    ("T1", "BIG-IP HA peer / device failover", "~3s+ detection (Failover.NetTimeoutSec=3) + convergence"),
    ("T2", "LTM / WAF pool member detection", "commonly up to ~16s (5s/16s default); set Action=Reject"),
    ("T3", "GTM health observation", "monitor / config specific (direct default 30s / 120s)"),
    ("T4", "GTM state + DNS convergence", "state learning/sync + answer + DNS TTL (30s default) / re-lookup"),
    ("T5", "Manual / warm / cold recovery", "minutes+; procedure and passive-app startup dependent"),
    ("T6", "Application recovery", "client retry / reconnect / re-auth / session state / replay"),
    ("T7", "Failback", "controlled return to primary (auto-failback default 60s if enabled)"),
    ("T8", "DNS / cache / existing sockets", "behavior modifier (existing TCP sockets stay pinned), not a duration"),
    ("T9", "Cloud Firewall (CFW) recovery", "product/config specific; measure separately from internal firewall"),
]
simple_table(
    s,
    ["Code", "Meaning", "Management interpretation"],
    rows,
    0.55,
    1.18,
    [0.95, 4.15, 7.15],
    rowh=0.48,
    fs=8.9,
    headh=0.44,
    aligns=[PP_ALIGN.CENTER, PP_ALIGN.LEFT, PP_ALIGN.LEFT],
)
add_text(
    s,
    "Critical addition: where GTM health is site-local only, include the measured GTM synchronization/state-learning delay before DNS TTL and T6.",
    0.55,
    6.28,
    12.25,
    0.50,
    10.0,
    True,
    NAVY,
    PP_ALIGN.CENTER,
    PALEGREEN,
    RGBColor(92, 164, 82),
)
footer(s, 15)

# Slide 16 — Appendix B: Executive Glossary of Acronyms & Shorthand Codes (NEW!)
s = slide()
title(
    s,
    "Appendix B — executive glossary of acronyms & codes",
    "Plain-English definitions of every F5, infrastructure, health-layer, topology, and recovery code used in this deck.",
)
left_terms = [
    ("GTM / BIG-IP DNS", "Global Traffic Manager — F5 DNS control plane for site selection"),
    ("LTM", "Local Traffic Manager — F5 local load balancer & Virtual IP tier"),
    ("WAF / AWAF", "Web Application Firewall / F5 Advanced WAF (formerly ASM)"),
    ("VIP / VS", "Virtual IP / Virtual Server — published application endpoint"),
    ("DSC", "Device Service Clustering — F5 HA synchronization/failover group"),
    ("F5OS-A (r2800)", "F5 appliance hypervisor on r2800 pizza boxes (max 2 tenants on 1.8+)"),
    ("STP / LACP LAG", "Spanning Tree Protocol (L2 loop prevention — unsupported on r2800; use LACP LAG)"),
    ("iQuery / big3d", "F5 protocol & agent sharing LTM/VS health metrics with GTM"),
    ("CFW / ELB / XFF", "Cloud FW / Cloud Load Balancer / X-Forwarded-For client IP header"),
]
right_terms = [
    ("H1 / H2", "Health layers: H1 = Device HA failover • H2 = Local LTM/ELB pool member"),
    ("H3 / H4", "Health layers: H3 = External VIP (GTM) • H4 = Internal VIP (GTM/LTM)"),
    ("H5 / H6", "Health layers: H5 = Shared dependency (App B) • H6 = Independent synthetic SLO"),
    ("R0 / R1", "Recovery classes: R0 = Zero user impact • R1 = Auto local recovery (secs)"),
    ("R2 / R3 / R4", "R2 = Cross-site component • R3 = Auto site/DNS failover • R4 = Manual DR"),
    ("W1 – W4", "Dedicated WAF topologies (active pool, DSC cluster, reserve, asymmetric)"),
    ("S1 / S2 / K+2", "Shared WAF topologies • K+2 active WAFs/site survives 2 simultaneous losses"),
    ("X2A / X2B / XD1", "Cross-site R2 patterns: remote WAF, remote front-end, App B fallback"),
    ("AT1 – AT4 / SLO", "App types (stateless, stateful, WebSocket, L4) • Service Level Objective"),
]
simple_table(
    s,
    ["Term / Code", "Plain-English definition"],
    left_terms,
    0.45,
    1.18,
    [1.80, 4.25],
    rowh=0.52,
    fs=8.5,
    headh=0.42,
    aligns=[PP_ALIGN.CENTER, PP_ALIGN.LEFT],
)
simple_table(
    s,
    ["Code / Layer", "Plain-English definition"],
    right_terms,
    6.75,
    1.18,
    [1.70, 4.43],
    rowh=0.52,
    fs=8.5,
    headh=0.42,
    aligns=[PP_ALIGN.CENTER, PP_ALIGN.LEFT],
)
add_text(
    s,
    "Note: Reference codes (e.g., K14707, K12818, K08433560) refer to official MyF5 Knowledge Base articles summarized in the repository’s F5 documentation reference tables.",
    0.45,
    6.42,
    12.43,
    0.44,
    9.4,
    True,
    NAVY,
    PP_ALIGN.CENTER,
    LIGHT,
    MID,
)
footer(s, 16)

prs.save(OUT)
print(OUT)
