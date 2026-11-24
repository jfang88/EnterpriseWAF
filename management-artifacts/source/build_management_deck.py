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


def title(s, t, st=None, tsize=23):
    add_text(s, t, 0.45, 0.16, 12.45, 0.46, tsize, True, NAVY, radius=False)
    if st:
        add_text(s, st, 0.47, 0.66, 12.35, 0.30, 10.5, False, SLATE, radius=False)


def footer(s, n):
    add_text(s, "EnterpriseWAF management summary", 0.48, 7.18, 3.6, 0.18, 8.0, False, SLATE, radius=False)
    add_text(s, f"Nov 2026  •  {n}", 11.55, 7.18, 1.25, 0.18, 8.0, False, SLATE, PP_ALIGN.RIGHT, radius=False)


def bullet_block(s, heading, items, x, y, w, h, fill=LIGHT, line=MID, headfill=NAVY, fs=10.8):
    add_text(s, heading, x, y, w, 0.42, 13, True, WHITE, PP_ALIGN.CENTER, headfill, headfill)
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
    tf.margin_top = Inches(0.18)
    tf.margin_bottom = Inches(0.12)
    for idx, item in enumerate(items):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        p.text = "• " + item
        p.alignment = PP_ALIGN.LEFT
        p.space_after = Pt(8)
        p.font.name = FONT
        p.font.size = Pt(fs)
        p.font.color.rgb = DARK


def simple_table(s, headers, rows, x, y, colw, rowh=0.46, fs=9.2, headh=None):
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
            add_text(s, str(v), xx, yy, colw[i], rowh, fs, False, DARK, PP_ALIGN.CENTER, f, MID)
            xx += colw[i]
        yy += rowh


# Slide 1 — Executive Summary
s = slide()
add_text(s, "EnterpriseWAF", 0.5, 0.44, 12.3, 0.62, 30, True, WHITE, PP_ALIGN.LEFT, NAVY, NAVY)
add_text(
    s,
    "Management summary — current state (BIG-IP 17.5.x), target health model, rebuild & 99.95%",
    0.52,
    1.18,
    12.25,
    0.45,
    17,
    False,
    NAVY,
    radius=False,
)
bullet_block(
    s,
    "Primary architecture recommendation",
    [
        "Retain tenant-specific LTM failure domains.",
        "Evaluate S1 shared active WAF pool on current hardware; on rSeries/VELOS F5OS rebuild, evaluate hardware-isolated per-tenant WAF tenants.",
        "Keep dedicated W1 (3 WAFs/tenant) as highest-isolation fallback.",
    ],
    0.6,
    1.95,
    3.85,
    3.15,
    GREEN,
    MID,
    NAVY,
    10.4,
)
bullet_block(
    s,
    "Health-monitoring recommendation",
    [
        "Use layered health (H1–H6), not one monitor.",
        "GTM owns site/DNS health at external + internal VIPs using L7 readiness and Specific Prober Pools.",
        "LTM/ELB owns fast local member withdrawal (Action On Service Down = Reject; VS Reject on all-down).",
    ],
    4.74,
    1.95,
    3.85,
    3.15,
    CYAN,
    MID,
    NAVY,
    10.4,
)
bullet_block(
    s,
    "Management risk to close",
    [
        "Current GTM monitor depth, NAT Translation mappings (K14707), and prober model remain unknown/validate.",
        "Port-up / default VS TCP 3WHS (K40554304) can be false green.",
        "App teams must own L7 readiness & Receive Disable drain contracts.",
    ],
    8.88,
    1.95,
    3.85,
    3.15,
    PALEYELLOW,
    ORANGE,
    NAVY,
    10.4,
)
add_text(
    s,
    "Key decision: validate the current BIG-IP 17.5.x GTM health model first, then implement layered L7 health and evaluate F5OS tenant isolation during the hardware rebuild.",
    0.6,
    5.55,
    12.13,
    0.72,
    13,
    True,
    NAVY,
    PP_ALIGN.CENTER,
    PALEGREEN,
    RGBColor(92, 164, 82),
)
footer(s, 1)

# Slide 2 — Separate Current State from Target State
s = slide()
title(
    s,
    "Separate current state from target state",
    "Management should clearly see what exists today (BIG-IP 17.5.x) versus what is proposed for the target rebuild.",
)
bullet_block(
    s,
    "CURRENT / validated baseline (BIG-IP 17.5.x)",
    [
        "2 sites; one BIG-IP DNS/GTM cluster per site inside edge firewall",
        "2 × HA edge-firewall pairs/site (2 devices/pair); external VIPs on FW",
        "Same edge GTM used for selected external + delegated internal names",
        "Internal users, internal DNS & internal LTM outside private cloud",
        "Separate internal firewall then private-cloud CFW → ELB → apps",
        "BIG-IP 17.5.x (EoTS Jan 2029); current GTM monitor depth/probers: validate",
    ],
    0.6,
    1.25,
    5.85,
    4.65,
    LIGHT,
    MID,
    NAVY,
    11.0,
)
bullet_block(
    s,
    "TARGET / to-be improvement & rebuild (21.1.x+ / F5OS)",
    [
        "GTM L7 health of external VIPs + NAT Translation & Specific Prober Pools",
        "GTM or authoritative internal LTM/iQuery L7 health of internal VIPs",
        "App-team readiness contracts + Receive Disable drain (K12818)",
        "Dependency-local B1 → B2 recovery (XD1) where state/data allow",
        "Hardware rebuild to rSeries/VELOS F5OS (21.1.x+; 21.x drops iSeries/VIPRION/vCMP)",
        "F5OS hardware-isolated tenants, cloud-init, ACMEv2 & independent SLO synthetics",
    ],
    6.88,
    1.25,
    5.85,
    4.65,
    PALEGREEN,
    RGBColor(92, 164, 82),
    TEAL,
    11.0,
)
add_text(
    s,
    "Rule: target-state health arrows, F5OS rebuild features, and X2A/X2B/XD1 must not appear on the current-state diagram until deployed and validated.",
    0.6,
    6.20,
    12.13,
    0.56,
    11.0,
    True,
    NAVY,
    PP_ALIGN.CENTER,
    PALEYELLOW,
    GOLD,
)
footer(s, 2)

# Slides 3, 4, 5, 6 — Populated by replace_management_slides.py from the 4 authoritative SVGs
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
    "GTM probing and convergence must be explicit",
    "Synchronization shares global state, but does not automatically mean every GTM directly probes every remote endpoint.",
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
    ("3", "GTM gets\nauthoritative state"),
    ("4", "GTM global state\nconverges"),
    ("5", "DNS answer\nchanges"),
    ("6", "TTL / cache +\nre-resolution"),
    ("7", "T6 app\nrecovery"),
]
# 7 steps across x=0.45..12.88: each box w=1.48, gap=0.35 (room for crisp 0.27" arrow!)
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
        "Remote GTM learns failure through synchronization/timeout behavior",
        "Measure that state-learning delay before DNS TTL",
        "Do not assume 30s DNS TTL equals total failover time",
        "Upgrade BIG-IP DNS first + big3d_install on LTMs (K25923322)",
    ],
    0.65,
    4.18,
    5.8,
    2.45,
    PALEYELLOW,
    ORANGE,
    NAVY,
    10.0,
)
bullet_block(
    s,
    "Target prober rule (official F5 guardrails)",
    [
        "Configure Specific Prober Pools per zone (K08433560; avoid K000163083 fallback)",
        "External FW NAT VIPs require Address + Translation (auto-discovery off, K14707)",
        "Avoid duplicate monitors on both LTM VS & GTM VS (K5431)",
        "Loss of inter-site link alone must never withdraw healthy local service",
    ],
    6.88,
    4.18,
    5.8,
    2.45,
    PALEGREEN,
    RGBColor(92, 164, 82),
    NAVY,
    10.0,
)
footer(s, 7)

# Slide 8 — Shared Dependency Cascade
s = slide()
title(
    s,
    "Shared dependency failure can create a multi-application outage",
    "Health design must avoid turning one App B failure into A / C / D site withdrawals.",
)
add_text(s, "Current / no dependency-local fallback", 0.6, 1.25, 5.9, 0.42, 13.5, True, RED, PP_ALIGN.CENTER, PALERED, RED)
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
    10.6,
    True,
    RED,
    PP_ALIGN.CENTER,
    PALERED,
    RED,
)
add_text(s, "Target: dependency-local recovery", 6.8, 1.25, 5.9, 0.42, 13.5, True, TEAL, PP_ALIGN.CENTER, PALEGREEN, TEAL)
box(s, "App A / D stay local", 7.05, 2.0, 2.15, 0.65, GREEN, NAVY, 11)
box(s, "B service VIP / discovery", 9.65, 2.0, 2.45, 0.65, CYAN, NAVY, 10)
arrow(s, 9.22, 2.32, 9.62, 2.32)
box(s, "B1 Site 1\npreferred", 7.75, 3.3, 1.75, 0.68, GREEN, NAVY, 10)
box(s, "B2 Site 2\nfallback", 10.2, 3.3, 1.75, 0.68, GREEN, NAVY, 10)
arrow(s, 10.88, 2.65, 8.62, 3.28)
arrow(s, 10.88, 2.65, 11.08, 3.28, TEAL, dash=True)
add_text(
    s,
    "B1 failure → withdraw B1 (LTM Reject, K15095) → bounded retry to B2 → A / D remain in Site 1",
    7.05,
    4.42,
    5.45,
    0.88,
    10.5,
    True,
    NAVY,
    PP_ALIGN.CENTER,
    PALEGREEN,
    RGBColor(92, 164, 82),
)
add_text(
    s,
    "Health contract caution: App A should not become globally unhealthy merely because an optional B/C feature is degraded.",
    0.85,
    6.08,
    11.63,
    0.54,
    10.5,
    True,
    NAVY,
    PP_ALIGN.CENTER,
    PALEYELLOW,
    GOLD,
)
footer(s, 8)

# Slide 9 — WAF Topology Options
s = slide()
title(
    s,
    "WAF topology options remain a separate decision",
    "Health-monitoring target applies regardless of WAF topology; F5OS rebuild reframes S1 vs. Dedicated W1.",
)
cards = [
    ("W1", "Tenant LTM → independent active WAF pool", "Best dedicated maintenance headroom; F5OS tenants on rSeries/VELOS can lower hardware footprint"),
    ("W2", "WAF HA / DSC cluster", "Simple HA; pair boundary; AWAF mirroring requires licensed+provisioned LTM (max 2 devices)"),
    ("W3", "Preferred WAFs + shared reserve (parallel)", "Dedicated normal path + lower-priority shared spare; reserve contention must be governed"),
    ("W4", "Site 1 cluster + parallel extra WAF", "Stronger Site 1 headroom, but asymmetric DR capacity in Site 2"),
    ("S1", "Tenant LTMs → shared active WAF pool", "Preferred 17.5.x cost/resilience candidate; use Parent/Child policies + Route Domains"),
    ("S2", "Shared LTM + shared WAF pool", "Future consolidation only; largest common-mode blast radius across tenants"),
]
for i, (k, d, r) in enumerate(cards):
    x = 0.55 + (i % 3) * 4.18
    y = 1.25 + (i // 3) * 2.45
    add_text(s, k, x, y, 3.88, 0.42, 15.5, True, NAVY, PP_ALIGN.LEFT, GREEN if k in ("W1", "S1") else LIGHT, NAVY)
    add_text(s, d, x, y + 0.48, 3.88, 0.72, 10.3, True, DARK, PP_ALIGN.LEFT, WHITE, MID)
    add_text(s, r, x, y + 1.26, 3.88, 0.82, 8.9, False, SLATE, PP_ALIGN.LEFT, WHITE, MID)
add_text(
    s,
    "Recommendation: validate S1 on current 17.5.x hardware; for the rSeries/VELOS F5OS rebuild, evaluate dedicated per-tenant F5OS WAF tenants spread across physical hosts.",
    0.55,
    6.28,
    12.24,
    0.58,
    10.4,
    True,
    NAVY,
    PP_ALIGN.CENTER,
    PALEGREEN,
    RGBColor(92, 164, 82),
)
footer(s, 9)

# Slide 10 — 99.95% Availability & Recovery Domains (fixed table clearance!)
s = slide()
title(
    s,
    "99.95% availability depends on recovery domain",
    "Routine failures should remain local; GTM/site failover is for endpoint/site failure, not every member failure.",
)
add_text(s, "99.95% budget", 0.55, 1.28, 2.25, 0.42, 14, True, WHITE, PP_ALIGN.CENTER, NAVY, NAVY)
add_text(s, "4h 22m 48s\nper year", 0.55, 1.76, 2.25, 1.05, 19, True, WHITE, PP_ALIGN.CENTER, NAVY2, NAVY2)
add_text(s, "21m 54s / month\n~5m 2s / week", 0.55, 2.88, 2.25, 0.72, 10.5, True, NAVY, PP_ALIGN.CENTER, LIGHT, MID)
rows = [
    ("1 backend / Pod / VM", "local ELB / LTM", "R0 / R1"),
    ("1 WAF node", "local LTM WAF pool (Action=Reject)", "R0 / R1"),
    ("1 LTM peer", "HA peer (3s default + convergence)", "R1"),
    ("whole external endpoint path", "GTM external L7", "R3 or X2"),
    ("whole internal endpoint path", "GTM / internal L7", "internal endpoint move"),
    ("App B local", "service VIP / discovery", "XD1 target"),
    ("whole site", "GTM + DR", "R3"),
]
# y=1.28, headh=0.50, 7 rows * 0.56 = 3.92 => ends at y=5.70 (0.52" clean gap before banner at y=6.22!)
simple_table(s, ["Failure", "Best recovery domain", "Target class"], rows, 3.05, 1.28, [3.95, 3.75, 2.05], rowh=0.56, fs=9.2, headh=0.50)
add_text(
    s,
    "Management test: planned maintenance should usually be no-outage or seconds-scale, with enough redundancy left for one additional credible failure (in-place upgrade remains experimental in 21.1.x).",
    0.55,
    6.20,
    12.25,
    0.62,
    10.4,
    True,
    NAVY,
    PP_ALIGN.CENTER,
    PALEYELLOW,
    GOLD,
)
footer(s, 10)

# Slide 11 — Cross-Site Capability (fixed single-line title + top-aligned bullets!)
s = slide()
title(
    s,
    "Cross-site capability: target contingency, not dependency",
    "Design early where it materially reduces failure-domain escalation; require SNAT Pool + XFF trust for route-back.",
    tsize=22,
)
bullet_block(
    s,
    "X2A remote WAF",
    [
        "Local LTM survives; borrows Site 2 WAF",
        "Routes back to healthy local CFW / app",
        "Avoids DNS TTL & application DR move",
        "Requires SNAT Pool + HTTP XFF + AWAF Trust XFF (K4816)",
        "Cannot bypass a failed local CFW",
    ],
    0.55,
    1.28,
    3.8,
    4.55,
    PALEGREEN,
    MID,
    TEAL,
    10.4,
)
bullet_block(
    s,
    "X2B remote front-end",
    [
        "Local edge / LTM / WAF tier lost",
        "Remote edge / LTM / WAF serves client",
        "Routes back across inter-site link to healthy Site 1 CFW / app",
        "Still incurs GTM / DNS TTL convergence",
        "Degraded split-site state; validate firewall symmetry",
    ],
    4.76,
    1.28,
    3.8,
    4.55,
    LIGHT,
    MID,
    TEAL,
    10.4,
)
bullet_block(
    s,
    "XD1 dependency fallback",
    [
        "App A / D remain in Site 1",
        "B service VIP prefers local B1",
        "B2 in Site 2 acts as lower-priority fallback",
        "Prevents shared-B cascade across apps",
        "Requires bounded timeouts, retry budget & compatible state",
    ],
    8.98,
    1.28,
    3.8,
    4.55,
    GREEN,
    MID,
    TEAL,
    10.4,
)
add_text(
    s,
    "Invariant: healthy local service must not depend on the inter-site link. Test network partition while both sites are otherwise healthy.",
    0.55,
    6.18,
    12.23,
    0.56,
    10.8,
    True,
    NAVY,
    PP_ALIGN.CENTER,
    PALEYELLOW,
    GOLD,
)
footer(s, 11)

# Slide 12 — Application Types (top-aligned bullets, clean spacing!)
s = slide()
title(
    s,
    "Application type determines the real recovery time",
    "Infrastructure can recover first while sessions, sockets or transactions remain broken.",
)
cols = [
    (
        "AT1 Stateless web",
        [
            "Safe automated retry",
            "Idempotency on writes",
            "External / shared state only",
            "Fast LTM member withdrawal",
        ],
    ),
    (
        "AT2 Stateful web",
        [
            "Portable / replicated session state",
            "Re-authentication & reconstruction",
            "Transaction reconciliation",
            "Confirm state parity before DR",
        ],
    ),
    (
        "AT3 WebSocket",
        [
            "Reconnect + backoff / jitter",
            "Re-auth + resubscribe + replay",
            "AWAF needs WS profile; NO OneConnect (K000151124)",
            "Mirroring max 2 devices & resets on failback (21.1 unchanged)",
        ],
    ),
    (
        "AT4 Non-web / L4",
        [
            "May bypass external WAF",
            "Protocol-specific reconnect",
            "DNS / service re-resolution",
            "Safe transaction replay",
        ],
    ),
]
fills = [GREEN, RGBColor(225, 238, 252), PURPLE, RGBColor(224, 244, 242)]
for i, (h, items) in enumerate(cols):
    bullet_block(s, h, items, 0.5 + i * 3.16, 1.28, 2.86, 4.55, fills[i], MID, NAVY, 10.0)
add_text(
    s,
    "GTM L7 health answers “can this endpoint accept new traffic?”; application recovery T6 answers “has the user/business flow actually recovered?”",
    0.5,
    6.18,
    12.33,
    0.56,
    10.5,
    True,
    NAVY,
    PP_ALIGN.CENTER,
    PALEGREEN,
    RGBColor(92, 164, 82),
)
footer(s, 12)

# Slide 13 — Four-Tenant Cost vs Blast Radius (fixed table-vs-callout overlap!)
s = slide()
title(
    s,
    "Four-tenant infrastructure efficiency vs blast radius",
    "Illustrative LTM + WAF device units across two sites — not vendor pricing (see F5OS note for target rebuild).",
)
rows = [
    ("Dedicated W1 — 3 WAF/tenant (physical/VE)", "40", "Low"),
    ("W3 — 2 preferred + shared reserve", "36", "Medium"),
    ("Dedicated W1 — 2 WAF/tenant", "32", "Low"),
    ("S1 — tenant LTMs + shared active WAF pool", "24", "High at WAF tier"),
    ("Rebuild option: F5OS per-tenant WAFs on shared rSeries/VELOS*", "Fewer hosts", "Low OS/policy; host-spread required"),
    ("S2 — shared LTM + shared WAF pool (out of current scope)", "12", "Very high"),
]
# y=1.25, headh=0.52, 6 rows * 0.62 = 3.72 => ends at y=5.49 (0.68" clean gap before banner at y=6.17!)
simple_table(
    s,
    ["Architecture", "Device units", "Cross-tenant blast radius"],
    rows,
    0.55,
    1.25,
    [6.15, 2.05, 4.05],
    rowh=0.62,
    fs=9.6,
    headh=0.52,
)
add_text(
    s,
    "*On rSeries (r4000–r12000; not r2000) or VELOS, F5OS tenants isolate OS, policy and upgrades per tenant while consolidating hardware — spread each tenant’s WAFs across physical hosts.",
    0.55,
    5.62,
    12.25,
    0.42,
    9.0,
    False,
    SLATE,
    PP_ALIGN.LEFT,
    radius=False,
)
add_text(
    s,
    "Health design does not remove shared-platform risk: a bad shared WAF policy/configuration or exhausted shared capacity can still affect several tenants at once.",
    0.55,
    6.16,
    12.25,
    0.58,
    10.4,
    True,
    NAVY,
    PP_ALIGN.CENTER,
    PALEYELLOW,
    GOLD,
)
footer(s, 13)

# Slide 14 — Target Implementation Sequence & Decision Gates (clean arrow spacing!)
s = slide()
title(
    s,
    "Target implementation sequence and decision gates",
    "Inventory first; then health contracts; then Layer-7 steering; then rebuild / cross-site contingency.",
)
phases = [
    ("0", "Inventory current\nmonitors, NAT &\nprobers"),
    ("1", "Define app\nreadiness & drain\ncontracts"),
    ("2", "Implement ext +\nint L7 endpoint\nhealth"),
    ("3", "Add Specific\nProber Pools &\nvisibility"),
    ("4", "Pilot B1 → B2\ndependency\nrecovery"),
    ("5", "Plan rSeries/VELOS\n21.1.x+ rebuild &\nX2A/X2B"),
    ("6", "Fault-inject &\nmeasure 99.95%\nevidence"),
]
for i, (n, t) in enumerate(phases):
    x = 0.45 + i * 1.82
    add_text(s, n, x + 0.56, 1.18, 0.36, 0.34, 10.5, True, WHITE, PP_ALIGN.CENTER, TEAL, TEAL)
    add_text(s, t, x, 1.58, 1.48, 1.02, 8.6, True, DARK, PP_ALIGN.CENTER, LIGHT, MID)
    if i < 6:
        arrow(s, x + 1.52, 2.09, x + 1.78, 2.09, TEAL, width=2.0)

checks = [
    "external + internal VIP health contracts documented",
    "one member failure remains local (Action=Reject)",
    "GTM never advertises broken required service path",
    "inter-site link loss does not withdraw healthy site",
    "GTM / prober / sync convergence measured",
    "App A / B / C / D cascade & XD1 tested",
    "AT3 WebSocket / stateful T6 & no-OneConnect verified",
    "planned maintenance + extra failure tested (GTM first)",
    "platform-migrate validate & rollback/failback tested",
]
add_text(s, "Before claiming target readiness", 0.55, 2.95, 4.5, 0.38, 13, True, NAVY, radius=False)
for i, ch in enumerate(checks):
    x = 0.55 + (i % 3) * 4.12
    y = 3.48 + (i // 3) * 0.78
    add_text(s, "✓", x, y, 0.30, 0.34, 11, True, TEAL, PP_ALIGN.CENTER, radius=False)
    add_text(s, ch, x + 0.32, y, 3.65, 0.52, 9.0, False, DARK, radius=False)
add_text(
    s,
    "Change safety remains part of the SLO: never change both sites together; upgrade BIG-IP DNS before LTM (big3d_install); drain one member at a time; preserve rollback.",
    0.55,
    6.16,
    12.25,
    0.60,
    10.2,
    True,
    NAVY,
    PP_ALIGN.CENTER,
    PALEYELLOW,
    GOLD,
)
footer(s, 14)

# Slide 15 — Timing Shorthand Appendix (fixed table-vs-callout overlap!)
s = slide()
title(
    s,
    "Appendix — timing shorthand",
    "Planning categories, not SLAs. Measure end-to-end from fault to the first successful business transaction.",
)
rows = [
    ("T1", "BIG-IP HA peer / device failover", "~3s+ detection (Failover.NetTimeoutSec=3) + convergence"),
    ("T2", "LTM / WAF member detection", "commonly up to ~16s (5s/16s default); set Action=Reject"),
    ("T3", "GTM health observation", "monitor / config specific (direct default 30s / 120s)"),
    ("T4", "GTM state + DNS convergence", "state learning/sync + answer + TTL (30s default) / re-resolution"),
    ("T5", "Manual / warm / cold recovery", "minutes+; procedure and passive-app startup dependent"),
    ("T6", "Application recovery", "retry / reconnect / re-auth / state / replay"),
    ("T7", "Failback", "controlled return (auto-failback default 60s when enabled)"),
    ("T8", "DNS / cache / existing connection", "behaviour modifier, not a duration"),
    ("T9", "CFW recovery", "product/config specific; measure separately from internal FW"),
]
# y=1.18, headh=0.44, 9 rows * 0.48 = 4.32 => ends at y=5.94 (0.34" clean gap before banner at y=6.28!)
simple_table(s, ["ID", "Meaning", "Management interpretation"], rows, 0.55, 1.18, [0.95, 4.15, 7.15], rowh=0.48, fs=8.9, headh=0.44)
add_text(
    s,
    "Critical addition: where GTM health is site-local only, include the measured GTM synchronization/state-learning delay before DNS TTL and T6.",
    0.55,
    6.28,
    12.25,
    0.50,
    10.2,
    True,
    NAVY,
    PP_ALIGN.CENTER,
    PALEGREEN,
    RGBColor(92, 164, 82),
)
footer(s, 15)

prs.save(OUT)
print(OUT)
