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


# Slide 1 — Executive Summary (Joint Responsibility • End-to-End Application Delivery)
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
    "Joint responsibility across Infra & App teams • Phase 1 focus: WAF tier • BIG-IP 17.5.x → r2800 (21.1.x+) • 99.95% & ≤ 25% impact",
    0.52,
    1.14,
    12.30,
    0.42,
    12.4,
    False,
    NAVY,
    radius=False,
)
bullet_block(
    s,
    "Joint responsibility & scope",
    [
        "Infrastructure teams deliver resilient, rolling-upgradeable tiers, deterministic SNAT/XFF headers, and layer-accurate health steering.",
        "App teams build failure-tolerant apps (T6 retries, external state, WS replay) and own L7 readiness & protocol contracts.",
        "99.95% (managed + unmanaged) & potential ≤ 25% impact cap: evaluate S1+2 (6/site, 24 GB) vs. W1-3 (both 20 r2800s on rebuild).",
    ],
    0.55,
    1.85,
    3.92,
    3.32,
    GREEN,
    MID,
    NAVY,
    9.7,
)
bullet_block(
    s,
    "Health & recovery at the right layer",
    [
        "Use 6 coordinated health layers (H1–H6) so infra & app teams architect against clear contracts, not guesswork.",
        "BIG-IP DNS (GTM) owns global site choice via L7 external & internal VIP health with Specific Prober Pools.",
        "LTM & Cloud ELB eject failed nodes locally (Action=Reject; VS Reject on all-down) and pass/inject XFF & sticky cookies cleanly.",
    ],
    4.70,
    1.85,
    3.92,
    3.32,
    CYAN,
    MID,
    NAVY,
    9.7,
)
bullet_block(
    s,
    "Key management risks to close",
    [
        "Current BIG-IP 17.5.x GTM monitor depth, NAT Translation maps (K14707), TLS termination/XFF & SNAT baselines remain to validate.",
        "Port-up / TCP handshake checks (K40554304) show false green while Cloud FW, ELB, or the application is broken.",
        "2-WAF designs (W1-2/W2b) lose local N-2 during 4/yr upgrades; S1+2 needs Parent/Child canary gates to stay ≤ 25% impact.",
    ],
    8.85,
    1.85,
    3.92,
    3.32,
    PALEYELLOW,
    ORANGE,
    NAVY,
    9.7,
)
add_text(
    s,
    "Key decision: audit current 17.5.x health/SNAT/XFF baselines, sign joint Infra + App contracts per fault domain (Slide 14), and choose S1+2 vs. W1-3 on the confirmed r2800 standard (Glossary on Slide 17).",
    0.55,
    5.50,
    12.22,
    0.76,
    11.4,
    True,
    NAVY,
    PP_ALIGN.CENTER,
    PALEGREEN,
    RGBColor(92, 164, 82),
)
footer(s, 1)

# Slide 2 — Separate Current Invariants from Target Controls (+ Joint Responsibility)
s = slide()
title(
    s,
    "Separate baseline invariants from target layer controls",
    "Keep validated current facts & enterprise invariants distinct from target-state infra/app improvements and r2800 rebuild.",
)
bullet_block(
    s,
    "CURRENT baseline & enterprise invariants",
    [
        "2 sites; edge GTM cluster/site; 2×2 HA edge FWs & separate internal FW (NetSec); Cloud FW → ELB (Cloud); App A/B/C/D (Apps)",
        "F5/ADC: tenant LTM HA pairs (2/tenant/site) + WAF tier (Phase 1 focus) on BIG-IP 17.5.x (EoTS Jan 2029)",
        "Invariant — Client IP tracking: some apps require real external IP (via no-SNAT, SNAT+XFF at 1st L7 hop, or ELB-injected headers)",
        "Invariant — App classes: stateless (AT1), stateful + potential sticky sessions (AT2), WebSockets (AT3), non-web L4 (AT4)",
        "Targets: 99.95% combined (managed + unmanaged) & potential ≤ 25% max impact (1 of 4 tenants / ≤ 25% canary exposure)",
        "Unknown / validate in Phase 0: current GTM monitor depth, probers, TLS termination, SNAT & sticky-session config",
    ],
    0.55,
    1.22,
    5.92,
    4.76,
    LIGHT,
    MID,
    NAVY,
    9.8,
)
bullet_block(
    s,
    "TARGET controls (Joint Infra + App) & r2800 rebuild",
    [
        "Infra — Layered L7 health (H1–H6), Specific Prober Pools, NAT Translation maps & separate ext/int VIP state",
        "Infra — Consistent sticky path (ELB cookie + LTM OneConnect/CARP), multi-IP SNAT Pools, XFF/ELB header injection & App B XD1",
        "App — Own /health/ready + Receive Disable drain (K12818), externalized session state (AT2), WS reconnect/replay (AT3) & retries",
        "Topology — S1+2 (4+2=6 WAFs/site for rolling + outage + canary) vs. W1-3 (strict ≤ 25% tenant cap); W1-2 needs X2A",
        "Confirmed rebuild: rSeries r2800 pizza boxes ONLY (F5OS-A 1.8.0+; max 2 tenants/box; no blade chassis)",
        "r2800 guardrails: single 480 GB SSD (no RAID-1) + no STP → K+2 spread, remote HSL logs, LACP LAGs & cloud-init",
    ],
    6.86,
    1.22,
    5.92,
    4.76,
    PALEGREEN,
    RGBColor(92, 164, 82),
    TEAL,
    9.8,
)
add_text(
    s,
    "Joint Responsibility Rule: Infrastructure delivers resilient layers, routing/XFF & health steering; Applications deliver T6 recovery & readiness contracts — never draw target controls as deployed facts.",
    0.55,
    6.20,
    12.23,
    0.56,
    10.1,
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

# Slide 12 — End-to-End Multi-Layer Path Consistency, Sticky Sessions, Client-IP Headers, SNAT & Throughput (AT1-AT4)
s = slide()
title(
    s,
    "End-to-end sticky sessions, client-IP headers, SNAT & throughput",
    "Target multi-layer alignment (Network/FW → LTM → WAF → CFW/ELB → App): high throughput in steady state + clean recovery on failure.",
    tsize=20.0,
)
at_rows = [
    (
        "AT1:\nStateless\nWeb / API",
        "5-tuple LACP LAG (no STP); f5-tcp-wan/lan + TLS 1.3 reuse; OneConnect + Least Conn (or CARP); SNAT Pool + strip/inject XFF if LTM terminates TLS",
        "Stateless active pool; Trust XFF (K4816); server keep-alive + TLS cache to ELB; disable extra WAF caching/gzip to save r2800 CPU",
        "Least Conn / LOR; no sticky cookie; preserve/append XFF (inject own XFF if ELB terminates TLS); fast H2 eject + graceful drain",
        "Stateless service; external/shared state only; idempotent writes; automated client retry with backoff/jitter; read trusted XFF",
    ),
    (
        "AT2:\nStateful\nWeb",
        "f5-tcp-wan/lan + OneConnect (mandatory so Keep-Alive honors cookies, K7964); LTM→WAF stateless CARP (K11362); SNAT Pool + XFF (K9816)",
        "Pass ELB/app sticky cookie untouched; Trust XFF; keep-alive + TLS reuse to ELB; Disabled / Receive Disable (K12818) drains sticky flows",
        "Single app-node sticky owner: ELB/Ingress cookie routes ANY WAF node to exact right App Node; preserve/inject XFF; Slow Start + drain",
        "Externalized/replicated session store (Redis/DB) makes sticky a speed/locality optimization (not SPOF); graceful re-auth & reconcile",
    ),
    (
        "AT3:\nWebSocket /\nReal-Time",
        "FW/NAT idle timeouts > app ping; WebSocket profile (K84421441); NEVER enable OneConnect (K000151124); Action=Reject (K15095); SNAT Pool + XFF",
        "WebSocket profile + AWAF policy (K000140381); Trust XFF; no mirroring on N>2 pools (2-device / no-failback limit unchanged in 21.1)",
        "Pin established WS TCP stream to target node; ELB idle timeout > ping; preserve/inject XFF on Upgrade; fast reset on crash",
        "Client reconnect + exponential backoff/jitter + re-auth + resubscribe + sequence-gap replay (mandatory)",
    ),
    (
        "AT4:\nNon-Web /\nLayer-4",
        "Perf L4 VS + FastL4 (K09948701, SW TMM on r2800); Source-IP/CARP; inline no-SNAT for IP ACLs/FTP (K15249), else SNAT Pool + PROXY Proto",
        "Bypasses external WAF tier (where permitted by policy) to avoid L7 proxy overhead & non-HTTP protocol breakage",
        "CFW stateful allow + L4 ELB (NLB/TCP passthrough) keeping raw IP or PROXY Protocol; 5-tuple/Source-IP hash; fast H2 removal",
        "Protocol-native reconnect, DNS/service re-resolution, safe transaction replay & PROXY Protocol parsing if behind SNAT",
    ),
]
# y=1.12, headh=0.42, 4 rows * 1.09 = 4.36 => ends at y=5.90 (clean gap before banner at y=6.04!)
simple_table(
    s,
    [
        "App Class",
        "Network, LTM & SNAT",
        "WAF Pool (AWAF)",
        "CFW & Cloud ELB",
        "Application Tier (T6)",
    ],
    at_rows,
    0.38,
    1.12,
    [1.40, 3.15, 2.65, 2.75, 2.62],
    rowh=1.09,
    fs=8.0,
    headh=0.42,
    aligns=[PP_ALIGN.CENTER, PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.LEFT],
)
add_text(
    s,
    "Client-IP & SNAT Rules: First L7 TLS terminator (LTM, WAF, or Cloud ELB) strips untrusted XFF & injects real client IP (if ELB terminates TLS, upstream must keep raw IP or pass PROXY Protocol). Use multi-IP SNAT Pools (not Automap — ~65k port cap/IP, K7820/K8246) for L3 asymmetry, X2A/X2B & LTM→AWAF OneConnect (K9816). Never mix OneConnect with WebSocket (K000151124) or HTTP/2 full-proxy (K95032535).",
    0.38,
    6.02,
    12.57,
    0.84,
    8.3,
    True,
    NAVY,
    PP_ALIGN.CENTER,
    PALEYELLOW,
    GOLD,
)
footer(s, 12)

# Slide 13 — Four-Tenant Topology Variant Scorecard (25% Impact, 99.95%, Longest Outage, Auto/Manual, Pros/Cons)
s = slide()
title(
    s,
    "Topology variant scorecard: 25% impact, 99.95% & longest outage",
    "4-tenant / 2-site LTM + WAF comparison (excludes GTM & FWs) including W1-2 sub-variant & S1+2 (rolling + outage + canary).",
    tsize=20.2,
)
score_rows = [
    (
        "W1-3 (3 WAF/tenant/site)",
        "16 + 24 = 40",
        "PASS (≤25% / 1 tenant; 1 node ≤8%)",
        "Very Strong (N-2)",
        "1–2 WAF: 0–16s+T6 (Auto R0/R1)\nFull tier: ~16s X2A / ~46–150s R3",
        "Pro: hard ≤25% isolation & 24 GB RAM\nCon: highest box count (40 units)",
    ),
    (
        "W1-2 sub-variant (2 WAF/tenant)",
        "16 + 16 = 32",
        "PARTIAL (tenant ≤25%, but 1 fault = 50% cap)",
        "Moderate (needs X2A)",
        "1 WAF: 0–16s+T6 (Auto R1); Maint+fault:\n~16s X2A / ~46–150s R3 / T5 Manual DR",
        "Pro: saves 8 WAFs vs W1-3\nCon: 0 local N-2 on 4/yr upgrades",
    ),
    (
        "r2800 2-tenant F5OS (W1-3)*",
        "8* + 12* = 20*",
        "PASS (policy ≤25%; 1 box = 0% outage)",
        "Very Strong (if ≤12 GB)",
        "1 box/host reboot: 0–16s+T6 (Auto R0/R1)\nMulti-box: ~16s X2A / R3 / Manual T5",
        "Pro: halves W1-3 to 20 r2800s\nCon: 12 GB RAM cap; 2 tenants/box",
    ),
    (
        "S1+2 (4+2=6 shared WAF/site)*",
        "16 (8*) + 12 = 28 (20*)",
        "COND. PASS (1 canary ≤17%; needs policy gates)",
        "Very Strong (+2 buffer)",
        "1–2 WAF (roll+SSD+canary): 0–16s+T6 (Auto)\nFull tier: ~16s X2A / ~46–150s R3 (4-ten)",
        "Pro: full 24 GB RAM + canary/N-2 @ 20*\nCon: bad global push can >25%",
    ),
    (
        "S1 base (4 shared WAF/site)",
        "16 + 8 = 24",
        "TIGHT (1 node = 25%; no canary cushion)",
        "Strong if K≤2 only",
        "1 WAF: 0–16s+T6 (Auto R1); Maint+fault\n(K>2): throttled / X2A / Manual T5",
        "Pro: lowest shared WAF count (8)\nCon: no +2 rolling/canary margin",
    ),
    (
        "W3 (2 pref + 2 reserve/site)",
        "16 + 20 = 36",
        "PASS normal / MED reserve risk",
        "Strong (if free)",
        "1–2 WAF: ~16s+T6 via reserve (Auto PG)\nContention/drift: R2/R3 or Manual T5",
        "Pro: dedicated normal path\nCon: saves only 4 WAFs; complex",
    ),
    (
        "W2b (DSC pair) / W4a (asym)",
        "16+16=32 / 16+20=36",
        "PARTIAL (0 maint N-2; W4a S2 fragile)",
        "Moderate / Asym.",
        "1st WAF: ~3s T1 (Auto); Maint+fault:\n~16s X2A / R3 / Manual T5 (+WS reset)",
        "Pro: simple HA / 1st-fault WS mirror\nCon: no canary or horizontal scale",
    ),
    (
        "S2 (Shared LTM+WAF — OOS)",
        "4 + 8 = 12",
        "FAIL (100% — all 4 tenants at risk)",
        "Lowest Confidence",
        "1 peer: ~3–16s (Auto); Bad LTM/WAF push:\nmins+ Manual T5 across all 4 tenants",
        "Pro: lowest device count (12)\nCon: breaks tenant LTM & 25% cap",
    ),
]
# y=1.10, headh=0.42, 8 rows * 0.57 = 4.56 => ends at y=6.08 (clean gap before banner at y=6.18!)
simple_table(
    s,
    [
        "Topology Variant (Slide 9)",
        "LTM + WAF\n(2 sites)",
        "≤ 25% Impact Cap",
        "99.95%\n(4 chg/yr)",
        "Longest Outage & Auto / Manual",
        "Key Pros / Cons",
    ],
    score_rows,
    0.38,
    1.10,
    [2.50, 1.38, 1.92, 1.32, 2.95, 2.50],
    rowh=0.57,
    fs=7.6,
    headh=0.42,
    aligns=[PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.LEFT, PP_ALIGN.LEFT],
)
add_text(
    s,
    "*Confirmed r2800 rebuild (no blade chassis): BOTH W1-3 (2-tenant F5OS @ 4c/12G) AND S1+2 (full-box @ 8c/24G) land at 20 r2800s total (8 LTM @ 2/box + 12 WAF). Whole-site DR is Auto R3 (~46–150s+T6) for Active/Active or Manual R4/T5 (mins+) for passive-startup apps.",
    0.38,
    6.18,
    12.57,
    0.66,
    8.5,
    True,
    NAVY,
    PP_ALIGN.CENTER,
    PALEYELLOW,
    GOLD,
)
footer(s, 13)

# Slide 14 — NEW: Joint Responsibility & Fault-Domain Recovery Matrix (Infra vs. App per Layer)
s = slide()
title(
    s,
    "Joint responsibility: infra & app obligations per fault domain",
    "Infrastructure delivers resilient layers & accurate health steering; App teams deliver T6 recovery & contracts at every fault domain.",
    tsize=20.5,
)
fd_rows = [
    (
        "1. DNS / BIG-IP GTM\n(H3 / H4)",
        "Node: 0–3s\nSite: ~46–150s+T6",
        "Automated\n(R1 / R3)",
        "Dual-site GTM; Specific Prober Pools (K08433560); NAT Translation maps (K14707); separate ext/int wide-IPs; 30s TTL; upgrade GTM first",
        "Respect DNS TTLs (no infinite JVM/pool IP pinning); re-resolve on socket error; own & version /health/ready contract",
    ),
    (
        "2. Network & Edge FW\n(H1)",
        "Link/peer: 0–10s+T6\nFull edge: ~46–150s",
        "Automated\n(R0/R1 / R3)",
        "2×2 HA edge FW pairs/tenant; dual-homed F5OS-A LACP LAGs (no STP on r2800, K000152319); FW idle timeouts > LTM/ELB keep-alives & WS ping",
        "Client retry with backoff/jitter (AT1/AT2); WebSocket ping & reconnect/replay (AT3); tolerate brief packet loss",
    ),
    (
        "3. Tenant LTM HA Pair\n(H1 / H2)",
        "1 peer: ~3s (T1)+T6\nBoth: ~46–150s+T6",
        "Auto (R1/R3)\nManual if no X2B",
        "Redundant TMM+mgmt HA; MAC masq; VS Immediate Action=Reject (K40554304); Action=Reject; OneConnect+CARP (no WS); SNAT Pool + XFF strip/inject",
        "Idempotent writes on HA failover resets; reconnect dropped sockets (AT3/AT2); read trusted XFF header position",
    ),
    (
        "4. WAF Tier (AWAF)\n(H2 / r2800)",
        "1–2 WAF: 0–16s+T6\nTier: ~16s X2A / R3",
        "Auto (R0–R3)\nManual rollback/DR",
        "Size S1+2 or W1-3 (single-SSD/host-reboot safety); remote HSL + cloud-init; Trust XFF (K4816); pass ELB sticky cookies; 1-node canary ≤17–25%",
        "Co-own canary policy sign-off (7-day staging, K82512024); never rely on AWAF mirroring for AT3 WS; handle reconnects",
    ),
    (
        "5. Internal FW & CFW\n(H4 / T9)",
        "Member: ~3–10s+T6\nWhole CFW: ~46–150s",
        "Auto HA / R3\n(unbounded if green!)",
        "Separate int-VIP (H4) from ext-VIP (H3); L7 probes MUST cross CFW→ELB→App (no T9C false-green); note X2A cannot bypass local CFW",
        "Expose lightweight /health/ready behind CFW so CFW outage triggers automatic steering; tolerate site failover on CFW loss",
    ),
    (
        "6. Cloud ELB / Ingress\n(H2)",
        "Node: 0–10s+T6\nWhole ELB: ~46–150s",
        "Automated\n(R0/R1 / R3)",
        "Own single AT2 app-node sticky cookie; inject/append own XFF if terminating TLS (preserve upstream XFF); Slow Start + graceful drain",
        "Implement Pod/VM readiness & preStop drain hooks (Receive Disable / HTTP 503) so rolling app updates stay R0/R1",
    ),
    (
        "7. App & Shared Deps\n(App A/D→B→C, H5)",
        "Node: 0–10s (R0/R1)\nApp B1: ~5–16s XD1",
        "Auto (R0–R2)\nManual DB reconcile",
        "Stable App B service VIP (H5) with Action=Reject (K15095) + pre-approved B1→B2 cross-site routing/FW rules (XD1)",
        "Separate critical vs optional deps in /health/ready (no cascades); circuit breakers; external session store (AT2); rolling DB/app updates",
    ),
    (
        "8. Whole Site / DR\n(X2C)",
        "Active/Act: ~46–150s\nPassive: mins+ (T5)",
        "Auto (R3 Act/Act)\nManual (R4 Passive)",
        "Size Site 2 r2800 LTM/WAF (S1+2 or W1-3), SNAT Pools, CFW & ELB for 100% 4-tenant DR surge; keep policies & certs synced",
        "Replicate state/data within RPO; automate passive-site startup & DB promotion (manual DR rapidly burns 262.8 min/yr budget)",
    ),
]
# y=1.10, headh=0.40, 8 rows * 0.58 = 4.64 => ends at y=6.14 (clean gap before banner at y=6.22!)
simple_table(
    s,
    [
        "Fault Domain / Layer",
        "Longest Outage",
        "Auto / Manual",
        "Specific Infrastructure Obligations",
        "Specific Application Obligations",
    ],
    fd_rows,
    0.38,
    1.10,
    [1.82, 1.50, 1.30, 4.10, 3.85],
    rowh=0.58,
    fs=7.5,
    headh=0.40,
    aligns=[PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.CENTER, PP_ALIGN.LEFT, PP_ALIGN.LEFT],
)
add_text(
    s,
    "Joint Accountability: Health checks & recovery must be built at the exact right layer — infrastructure prevents false-greens & single-node outages; applications own T6 recovery & readiness contracts.",
    0.38,
    6.22,
    12.57,
    0.58,
    9.4,
    True,
    NAVY,
    PP_ALIGN.CENTER,
    PALEGREEN,
    RGBColor(92, 164, 82),
)
footer(s, 14)

# Slide 15 — End-to-End Implementation Sequence & Cross-Team Gates
s = slide()
title(
    s,
    "End-to-end implementation sequence (Phase 1: WAF & F5 tier)",
    "Start with F5/WAF & GTM validation we own directly, while aligning Network/Security, Cloud Platform, and App teams on contracts.",
)
phases = [
    ("0", "Inventory monitors,\nSNAT/XFF, probers &\nr2800 AWAF RAM"),
    ("1", "Phase 1: S1+2/W1-3\ndesign + app L7\ncontracts"),
    ("2", "Implement ext +\nint L7 VIP health\n(F5 + NetSec)"),
    ("3", "Add Specific\nProber Pools &\nH6 synthetics"),
    ("4", "Pilot App B1→B2\nXD1 recovery\n(App + Cloud)"),
    ("5", "Execute r2800\n21.1.x+ rebuild &\nX2A/X2B"),
    ("6", "Fault-inject &\nprove 99.95% &\n≤25% impact"),
]
for i, (n, t) in enumerate(phases):
    x = 0.45 + i * 1.82
    add_text(s, n, x + 0.56, 1.18, 0.36, 0.34, 10.5, True, WHITE, PP_ALIGN.CENTER, TEAL, TEAL)
    add_text(s, t, x, 1.58, 1.48, 1.02, 8.3, True, DARK, PP_ALIGN.CENTER, LIGHT, MID)
    if i < 6:
        arrow(s, x + 1.52, 2.09, x + 1.78, 2.09, TEAL, width=2.0)

checks = [
    "external + internal VIP health contracts signed with App/NetSec",
    "1 WAF or backend failure stays local R0/R1 (Action=Reject)",
    "GTM never advertises a broken required service path",
    "inter-site link loss never withdraws a healthy local site",
    "GTM / prober / sync convergence time measured end-to-end",
    "App A / B / C / D cascade & XD1 fallback tested with App teams",
    "AT1–AT4 sticky, XFF/ELB headers, SNAT Pool & no-OneConnect WS",
    "managed maintenance + extra failure + 1-node canary ≤ 25% tested",
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
footer(s, 15)

# Slide 16 — Appendix A: Recovery Timing Shorthand (T1-T9)
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
footer(s, 16)

# Slide 17 — Appendix B: Executive Glossary of Acronyms & Shorthand Codes
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
    ("STP / LACP LAG", "Spanning Tree Protocol (unsupported on r2800; use dual-homed LACP LAG)"),
    ("SNAT / OneConnect", "Source NAT (multi-IP SNAT Pool avoids 65k port cap) • HTTP TCP reuse"),
    ("iQuery / big3d", "F5 protocol & agent sharing LTM/VS health metrics with GTM"),
    ("CFW / ELB / XFF", "Cloud FW / Cloud Load Balancer / X-Forwarded-For client IP header"),
]
right_terms = [
    ("H1 / H2", "Health layers: H1 = Device HA failover • H2 = Local LTM/ELB pool member"),
    ("H3 / H4", "Health layers: H3 = External VIP (GTM) • H4 = Internal VIP (GTM/LTM)"),
    ("H5 / H6", "Health layers: H5 = Shared dependency (App B) • H6 = Independent synthetic SLO"),
    ("R0 / R1", "Recovery classes: R0 = Zero user impact • R1 = Auto local recovery (secs)"),
    ("R2 / R3 / R4", "R2 = Cross-site component • R3 = Auto site/DNS failover • R4 = Manual DR"),
    ("W1-3 / W1-2 / W2–4", "Dedicated WAFs: W1-3 (3/site, N-2) vs W1-2 (2/site, N-1); W2 DSC; W3/W4"),
    ("S1 / S1+2 / S2", "Shared WAFs: S1 (4/site), S1+2 (+2 for rolling/outage/canary), S2 (OOS)"),
    ("X2A / X2B / XD1", "Cross-site R2 patterns: remote WAF, remote front-end, App B fallback"),
    ("CARP / FastL4", "Stateless consistent hash persistence • Low-overhead L4 forwarding"),
    ("AT1 – AT4 / SLO", "App types (stateless, stateful, WebSocket, L4) • Service Level Objective"),
]
simple_table(
    s,
    ["Term / Code", "Plain-English definition"],
    left_terms,
    0.45,
    1.16,
    [1.85, 4.20],
    rowh=0.47,
    fs=8.3,
    headh=0.40,
    aligns=[PP_ALIGN.CENTER, PP_ALIGN.LEFT],
)
simple_table(
    s,
    ["Code / Layer", "Plain-English definition"],
    right_terms,
    6.75,
    1.16,
    [1.75, 4.38],
    rowh=0.47,
    fs=8.3,
    headh=0.40,
    aligns=[PP_ALIGN.CENTER, PP_ALIGN.LEFT],
)
add_text(
    s,
    "Note: Reference codes (e.g., K14707, K12818, K7964, K9816, K7820) refer to official MyF5 Knowledge Base articles summarized in the repository’s F5 documentation reference tables.",
    0.45,
    6.42,
    12.43,
    0.44,
    9.2,
    True,
    NAVY,
    PP_ALIGN.CENTER,
    LIGHT,
    MID,
)
footer(s, 17)

prs.save(OUT)
print(OUT)
