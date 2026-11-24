from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.oxml import parse_xml
from pptx.oxml.ns import nsdecls

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'EnterpriseWAF_Management_Summary.pptx'
prs=Presentation(); prs.slide_width=Inches(13.333); prs.slide_height=Inches(7.5)

NAVY=RGBColor(6,55,95); NAVY2=RGBColor(11,76,116); TEAL=RGBColor(15,139,141)
CYAN=RGBColor(220,245,248); GREEN=RGBColor(223,245,193); PURPLE=RGBColor(237,232,255)
PURPLE_LINE=RGBColor(92,76,210); LIGHT=RGBColor(246,249,252); MID=RGBColor(219,230,239)
DARK=RGBColor(22,36,50); ORANGE=RGBColor(209,119,20); WHITE=RGBColor(255,255,255)
RED=RGBColor(190,49,68); SLATE=RGBColor(74,91,107); GOLD=RGBColor(226,191,80)
PALEGREEN=RGBColor(235,248,233); PALEYELLOW=RGBColor(255,247,220); PALERED=RGBColor(255,240,240)


def slide(): return prs.slides.add_slide(prs.slide_layouts[6])
def add_text(s,text,x,y,w,h,size=14,bold=False,color=DARK,align=PP_ALIGN.LEFT,fill=None,line=None,radius=True):
    sh=s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE, Inches(x),Inches(y),Inches(w),Inches(h))
    if fill is None: sh.fill.background()
    else: sh.fill.solid(); sh.fill.fore_color.rgb=fill
    if line is None: sh.line.fill.background()
    else: sh.line.color.rgb=line; sh.line.width=Pt(1)
    tf=sh.text_frame; tf.clear(); tf.word_wrap=True; tf.vertical_anchor=MSO_ANCHOR.MIDDLE
    tf.margin_left=tf.margin_right=Inches(.07); tf.margin_top=tf.margin_bottom=Inches(.04)
    p=tf.paragraphs[0]; p.text=text; p.alignment=align; p.font.name='Aptos'; p.font.size=Pt(size); p.font.bold=bold; p.font.color.rgb=color
    return sh

def box(s,text,x,y,w,h,fill=CYAN,line=NAVY,size=11,bold=True): return add_text(s,text,x,y,w,h,size,bold,DARK,PP_ALIGN.CENTER,fill,line)
def arrow(s,x1,y1,x2,y2,color=NAVY,width=2,dash=False,both=False):
    ln=s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,Inches(x1),Inches(y1),Inches(x2),Inches(y2))
    ln.line.color.rgb=color; ln.line.width=Pt(width)
    if dash: ln.line.dash_style=MSO_LINE_DASH_STYLE.DASH
    l=ln.line._get_or_add_ln(); l.append(parse_xml(f'<a:headEnd {nsdecls("a")} type="triangle"/>' if both else f'<a:headEnd {nsdecls("a")} type="none"/>'))
    l.append(parse_xml(f'<a:tailEnd {nsdecls("a")} type="triangle"/>'))
    return ln

def title(s,t,st=None):
    add_text(s,t,.45,.18,12.4,.43,24,True,NAVY,radius=False)
    if st: add_text(s,st,.47,.65,12.2,.32,10.5,False,SLATE,radius=False)

def footer(s,n):
    add_text(s,'EnterpriseWAF management summary',.48,7.18,3.1,.16,7.5,False,SLATE,radius=False)
    add_text(s,f'Nov 2026  •  {n}',11.7,7.18,1.05,.16,7.5,False,SLATE,PP_ALIGN.RIGHT,radius=False)

def bullet_block(s,heading,items,x,y,w,h,fill=LIGHT,line=MID,headfill=NAVY,fs=10.5):
    add_text(s,heading,x,y,w,.38,13,True,WHITE,PP_ALIGN.CENTER,headfill,headfill)
    add_text(s,'\n'.join('• '+i for i in items),x,y+.44,w,h-.44,fs,False,DARK,PP_ALIGN.LEFT,fill,line)

def simple_table(s,headers,rows,x,y,colw,rowh=.46,fs=9):
    xx=x
    for i,h in enumerate(headers):
        add_text(s,h,xx,y,colw[i],rowh,fs,True,WHITE,PP_ALIGN.CENTER,NAVY,NAVY); xx+=colw[i]
    yy=y+rowh
    for r,row in enumerate(rows):
        xx=x; f=LIGHT if r%2==0 else WHITE
        for i,v in enumerate(row):
            add_text(s,str(v),xx,yy,colw[i],rowh,fs,False,DARK,PP_ALIGN.CENTER,f,MID); xx+=colw[i]
        yy+=rowh

def layer_row(s,label,desc,owner,y,fill):
    add_text(s,label,.7,y,1.15,.46,11,True,WHITE,PP_ALIGN.CENTER,NAVY,NAVY)
    add_text(s,desc,1.95,y,7.65,.46,10.2,True,DARK,PP_ALIGN.LEFT,fill,MID)
    add_text(s,owner,9.75,y,2.85,.46,9.5,False,SLATE,PP_ALIGN.CENTER,WHITE,MID)

# 1 Executive
s=slide(); add_text(s,'EnterpriseWAF',.5,.48,12.25,.58,30,True,WHITE,PP_ALIGN.LEFT,NAVY,NAVY)
add_text(s,'Management summary — current state, target health model, resilience & 99.95%',.55,1.18,12,.48,19,False,NAVY,radius=False)
bullet_block(s,'Primary architecture recommendation',['Retain tenant-specific LTM failure domains.','Evaluate S1 shared independent active WAF pool first.','Keep dedicated W1 as high-isolation fallback.'],.65,2.05,3.8,2.45,GREEN)
bullet_block(s,'Health-monitoring recommendation',['Use layered health, not one monitor.','GTM owns site/DNS health at external + internal VIPs using L7 readiness.','LTM/ELB owns fast local member withdrawal.'],4.78,2.05,3.8,2.45,CYAN)
bullet_block(s,'Management risk to close',['Current GTM monitor depth/prober model is not yet treated as known.','Port-up can be false green.','App teams must own readiness contracts.'],8.92,2.05,3.75,2.45,PALEYELLOW,ORANGE)
add_text(s,'Key decision: validate the current GTM health model first, then implement a layered target without turning local member failures into unnecessary site failovers.',.85,5.65,11.7,.68,14,True,NAVY,PP_ALIGN.CENTER,PALEGREEN,RGBColor(92,164,82)); footer(s,1)

# 2 current vs target
s=slide(); title(s,'Separate current state from target state','Management should be able to see what exists today versus what is proposed.')
bullet_block(s,'CURRENT / validated baseline',['2 sites; GTM cluster per site','2 × HA edge-firewall pairs/site','same edge GTM used for selected external + internal DNS names','internal users/DNS outside private cloud','separate internal firewall then CFW','current GTM health depth/probers: validate'],.65,1.35,5.75,4.9,LIGHT, MID, NAVY,10.6)
bullet_block(s,'TARGET / to-be improvement',['GTM L7 check of external VIP','GTM or authoritative iQuery L7 check of internal VIP','cross-site/prober diversity without cross-site dependency','app-team readiness contract','dependency-local B1→B2 recovery where safe','independent user-like synthetics for SLO'],6.9,1.35,5.75,4.9,GREEN,MID,TEAL,10.6)
add_text(s,'Rule: target-state health arrows and X2A/X2B/XD1 must not appear on the current-state diagram unless deployment is confirmed.',1.0,6.4,11.3,.45,11.2,True,NAVY,PP_ALIGN.CENTER,PALEYELLOW,GOLD); footer(s,2)

# 3 layers
s=slide(); title(s,'Architecture layer breakdown','Health ownership follows the layer: local recovery low in the stack, global DNS decisions at GTM.')
add_text(s,'Layer',.7,1.15,1.15,.36,10,True,WHITE,PP_ALIGN.CENTER,NAVY,NAVY); add_text(s,'Role',1.95,1.15,7.65,.36,10,True,WHITE,PP_ALIGN.CENTER,NAVY,NAVY); add_text(s,'Primary owner / decision',9.75,1.15,2.85,.36,10,True,WHITE,PP_ALIGN.CENTER,NAVY,NAVY)
rows=[('L0','Users / resolvers — external users, external DNS, internal users, internal DNS','customer / enterprise DNS',LIGHT),('L1','Global DNS/site selection — GTM clusters and delegated namespaces','GTM / DNS',GREEN),('L2','Site edge — leased line/VPN, 2×2 edge firewalls, external VIPs','network / security',CYAN),('L3','Local delivery/security — tenant LTM and WAF','LTM / WAF',LIGHT),('L4','Internal access boundary — internal LTM + internal firewall','internal network/security',CYAN),('L5','Private-cloud delivery — CFW + ELB/service','platform/network',PURPLE),('L6','Applications/state — App A/B/C/D, DB, identity, events','app/platform',GREEN),('L7','Dependencies — App A/D → B → C/shared services','application architecture',LIGHT)]
for i,(a,b,c,f) in enumerate(rows): layer_row(s,a,b,c,1.58+i*.58,f)
add_text(s,'Cross-cutting health/observability: H1 local HA • H2 local member • H3 external GTM L7 • H4 internal GTM/iQuery L7 • H5 dependency health • H6 independent synthetic',.75,6.4,11.85,.48,9.4,True,NAVY,PP_ALIGN.CENTER,PALEGREEN,RGBColor(92,164,82)); footer(s,3)

# 4 current architecture
s=slide(); title(s,'Current-state end-to-end architecture','DNS control plane is separate from application data; target health probes are intentionally not shown here.')
box(s,'External users /\nAPI clients',.18,1.35,1.16,.72,LIGHT,size=10); box(s,'External /\ncustomer DNS',1.48,1.35,1.15,.72,LIGHT,size=10); box(s,'Private leased line /\nVPN',2.78,1.35,1.22,.72,LIGHT,size=9.5)
arrow(s,1.34,1.71,1.48,1.71); arrow(s,2.63,1.71,2.78,1.71)
add_text(s,'Enterprise internal network — outside private cloud',.18,4.65,3.95,.34,10.2,True,WHITE,PP_ALIGN.CENTER,NAVY,NAVY)
for txt,x,w in [('Internal users',.25,.85),('Internal DNS',1.2,.82),('Internal LTM / VIP',2.12,1.0),('Internal firewall',3.22,.82)]: box(s,txt,x,5.15,w,.62,LIGHT if x<2 else CYAN,size=9.5)
arrow(s,1.1,5.46,1.2,5.46); arrow(s,2.02,5.46,2.12,5.46); arrow(s,3.12,5.46,3.22,5.46)
for x,name in [(4.35,'Site 1 — Primary'),(8.85,'Site 2 — DR / Secondary')]:
    add_text(s,name,x,1.02,4.15,.38,15.5,True,WHITE,PP_ALIGN.CENTER,NAVY,NAVY)
    box(s,'2 × HA edge-firewall pairs\n(2 devices/pair)',x+.25,1.55,3.65,.55,CYAN,size=9.7)
    box(s,'GTM / DNS cluster',x+.25,2.22,1.55,.58,GREEN,size=10)
    box(s,'Tenant LTM HA',x+2.0,2.22,1.9,.58,CYAN,size=10)
    box(s,'WAF tier',x+2.0,2.92,1.9,.50,RGBColor(206,241,239),size=10.5)
    arrow(s,x+1.98,2.10,x+1.02,2.22,ORANGE,dash=True); arrow(s,x+2.95,2.10,x+2.95,2.22); arrow(s,x+2.95,2.80,x+2.95,2.92)
    bd=s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,Inches(x+.12),Inches(3.65),Inches(3.83),Inches(2.55)); bd.fill.solid(); bd.fill.fore_color.rgb=PURPLE; bd.fill.transparency=25; bd.line.color.rgb=PURPLE_LINE; bd.line.width=Pt(1.4)
    add_text(s,'Private cloud',x+.65,3.68,2.8,.30,10,True,WHITE,PP_ALIGN.CENTER,PURPLE_LINE,PURPLE_LINE)
    box(s,'CFW',x+.4,4.15,1.0,.48,CYAN,size=10); box(s,'ELB / service',x+1.65,4.15,1.45,.48,CYAN,size=9.5); arrow(s,x+1.4,4.39,x+1.65,4.39)
    box(s,'App A',x+.45,4.85,.9,.45,GREEN,size=9.5); box(s,'App D',x+1.5,4.85,.9,.45,GREEN,size=9.5); box(s,'App B',x+2.55,4.85,.9,.45,GREEN,size=9.5); box(s,'App C',x+2.55,5.48,.9,.45,GREEN,size=9.5)
    arrow(s,x+2.38,4.63,x+.9,4.85); arrow(s,x+2.38,4.63,x+1.95,4.85); arrow(s,x+2.4,5.08,x+2.55,5.08); arrow(s,x+3.0,5.30,x+3.0,5.48)
    arrow(s,x+2.95,3.42,x+.9,4.15)
arrow(s,4.0,1.71,4.6,1.82)
arrow(s,1.61,5.15,5.35,2.52,ORANGE,dash=True); add_text(s,'selected internal names\nmay delegate to same edge GTM',2.4,4.35,1.6,.42,7.8,False,ORANGE,radius=False)
arrow(s,4.04,5.46,4.75,4.39)
arrow(s,5.9,2.51,9.1,2.51,TEAL,dash=True,both=True); add_text(s,'GTM synchronization',6.95,2.16,1.8,.3,8.3,True,TEAL,PP_ALIGN.CENTER,radius=False)
add_text(s,'Current-state unknown to validate: TCP/port vs L7 monitor depth • external/internal VIP checks • iQuery • cross-site probing • intervals/timeouts • app readiness endpoints',.35,6.55,12.55,.42,8.8,True,NAVY,PP_ALIGN.CENTER,PALEYELLOW,GOLD); footer(s,4)

# 5 target health
s=slide(); title(s,'Target health-monitoring model','Layered health: local tiers recover members; GTM makes site/DNS decisions from L7 endpoint health.')
box(s,'External DNS\n/ users',.2,1.35,1.1,.65,LIGHT,size=9.5); box(s,'Internal DNS\n/ users',.2,4.55,1.1,.65,LIGHT,size=9.5)
for x,name in [(1.65,'Site 1'),(6.45,'Site 2')]:
    add_text(s,name,x,1.08,4.25,.36,15,True,WHITE,PP_ALIGN.CENTER,NAVY,NAVY)
    box(s,'Edge FW 2×2',x+.15,1.62,1.3,.50,CYAN,size=9); box(s,'GTM cluster',x+1.62,1.62,1.18,.50,GREEN,size=9); box(s,'Tenant LTM',x+2.98,1.62,1.12,.50,CYAN,size=9)
    box(s,'WAF',x+2.98,2.33,1.12,.48,RGBColor(206,241,239),size=9); arrow(s,x+3.54,2.12,x+3.54,2.33)
    bd=s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,Inches(x+.1),Inches(3.05),Inches(4.05),Inches(2.3)); bd.fill.solid(); bd.fill.fore_color.rgb=PURPLE; bd.fill.transparency=25; bd.line.color.rgb=PURPLE_LINE
    box(s,'CFW',x+.35,3.55,.85,.45,CYAN,size=9); box(s,'ELB',x+1.45,3.55,.85,.45,CYAN,size=9); box(s,'App',x+2.55,3.55,1.05,.45,GREEN,size=9); arrow(s,x+1.2,3.77,x+1.45,3.77); arrow(s,x+2.3,3.77,x+2.55,3.77)
    box(s,'Internal VIP',x+.35,4.35,1.2,.45,CYAN,size=8.7); box(s,'B service VIP',x+1.8,4.35,1.35,.45,CYAN,size=8.7); box(s,'App B/C deps',x+3.25,4.35,.7,.45,GREEN,size=7.8)
    arrow(s,x+3.54,2.81,x+.75,3.55)
arrow(s,4.45,1.86,8.07,1.86,TEAL,dash=True,both=True); add_text(s,'GTM sync / shared probing responsibility',4.72,1.43,3.0,.28,7.8,True,TEAL,PP_ALIGN.CENTER,radius=False)
arrow(s,1.3,1.68,3.27,1.86,ORANGE,dash=True); arrow(s,1.3,4.87,3.27,1.86,ORANGE,dash=True)
arrow(s,3.27,2.12,4.63,2.58,TEAL,dash=True); add_text(s,'H3 external VIP L7',3.1,2.58,1.45,.3,8,True,TEAL,PP_ALIGN.CENTER,radius=False)
arrow(s,3.27,2.12,2.55,4.57,TEAL,dash=True); add_text(s,'H4 internal VIP L7',1.45,3.90,1.55,.3,8,True,TEAL,PP_ALIGN.CENTER,radius=False)
add_text(s,'H2 local LTM/ELB member health',2.15,5.58,3.2,.35,8.8,True,NAVY,PP_ALIGN.CENTER,PALEGREEN,RGBColor(92,164,82))
arrow(s,3.45,4.57,4.9,4.57,TEAL,dash=True); add_text(s,'H5 dependency health',3.45,4.92,1.55,.25,7.7,True,TEAL,PP_ALIGN.CENTER,radius=False)
bullet_block(s,'App-team readiness contract',['Host/SNI + URI','expected status/body','auth/cert/token if needed','critical dependencies only','maintenance/drain semantics','named app owner'],10.95,1.25,2.15,3.45,PALEGREEN,MID,NAVY,9.3)
bullet_block(s,'H6 independent synthetic',['external user-like transaction','internal user-like transaction','API/system transaction','SLO evidence, not normally sole steering trigger'],10.95,4.95,2.15,1.55,LIGHT,MID,TEAL,8.7)
add_text(s,'Avoid false green: WAF/LTM listener up while CFW/ELB/app is broken. Avoid false red: non-critical dependency causes broad withdrawal.',.65,6.55,9.9,.44,9.4,True,RED,PP_ALIGN.CENTER,PALERED,RED); footer(s,5)

# 6 placement table
s=slide(); title(s,'Where should health checks live?','Best answer: multiple layers, with a clear decision boundary.')
rows=[('H1 Device / HA','native HA','peer/process/interface','local takeover'),('H2 Local member','LTM / ELB','member L7 / protocol readiness','remove one member locally'),('H3 External endpoint','GTM prober','external VIP L7 through WAF→CFW→ELB→app','external DNS/site choice'),('H4 Internal endpoint','GTM or LTM+iQuery','internal VIP L7 through internal FW→CFW→ELB→app','internal delegated-name/site choice'),('H5 Dependency','service VIP / discovery','B1/B2 and critical downstream service','dependency-local recovery'),('H6 SLO synthetic','independent monitoring','real user/API business transaction','SLO/alerting/confirmation')]
simple_table(s,['Layer','Best place','Check','Action'],rows,.45,1.35,[1.55,2.1,5.0,3.65],.66,8.5)
add_text(s,'GTM is the right place for the site-level L7 decision because it controls DNS/site selection; it should not replace fast local LTM/ELB member health.',.75,6.25,11.85,.55,11.2,True,NAVY,PP_ALIGN.CENTER,PALEGREEN,RGBColor(92,164,82)); footer(s,6)

# 7 GTM convergence
s=slide(); title(s,'GTM probing and convergence must be explicit','Synchronization helps global state, but does not automatically mean every GTM directly probes every remote endpoint.')
box(s,'Site 1\nGTM cluster',.75,1.55,2.0,.75,GREEN,size=12); box(s,'Site 2\nGTM cluster',10.55,1.55,2.0,.75,GREEN,size=12); arrow(s,2.75,1.92,10.55,1.92,TEAL,dash=True,both=True); add_text(s,'sync group: configuration / health state / probing responsibility',4.25,1.5,4.8,.34,9,True,TEAL,PP_ALIGN.CENTER,radius=False)
steps=[('1','Path fails'),('2','Local detector sees failure'),('3','GTM gets authoritative state'),('4','GTM global state converges'),('5','DNS answer changes'),('6','TTL/cache + re-resolution'),('7','T6 app recovery')]
for i,(n,t) in enumerate(steps):
    x=.55+i*1.8
    add_text(s,n,x,3.05,.4,.4,11,True,WHITE,PP_ALIGN.CENTER,NAVY2,NAVY2); add_text(s,t,x+.48,2.87,1.23,.78,8.8,True,DARK,PP_ALIGN.CENTER,LIGHT,MID)
    if i<6: arrow(s,x+1.71,3.25,x+1.82,3.25)
bullet_block(s,'If probes are site-local only',['remote GTM may learn failure through synchronization/timeout behavior','measure that learning delay','do not assume DNS TTL is total failover time'],.75,4.45,5.75,1.75,PALEYELLOW,ORANGE,NAVY,9.8)
bullet_block(s,'Target prober rule',['use >1 independent health perspective where routing permits','local health remains authoritative','loss of inter-site link alone must not withdraw healthy local service'],6.85,4.45,5.75,1.75,PALEGREEN,RGBColor(92,164,82),NAVY,9.8); footer(s,7)

# 8 dependency cascade
s=slide(); title(s,'Shared dependency failure can create a multi-application outage','Health design must avoid turning one B failure into A/C/D site withdrawals.')
add_text(s,'Current / no dependency-local fallback',.6,1.25,5.9,.42,14,True,RED,PP_ALIGN.CENTER,PALERED,RED)
box(s,'App B local\nFAILS',2.35,1.95,2.35,.7,PALERED,RED,11); arrow(s,3.52,2.65,1.45,3.3,RED); arrow(s,3.52,2.65,3.52,3.3,RED); arrow(s,3.52,2.65,5.55,3.3,RED)
for txt,x in [('App A',.75),('App C',2.75),('App D',4.75)]: box(s,txt+'\ntimeout/retry',x,3.3,1.55,.68,PALEYELLOW,ORANGE,10)
add_text(s,'connection pools fill → readiness may fail → GTM can withdraw multiple VIPs → Site 2 surge',.8,4.45,5.45,.9,10.6,True,RED,PP_ALIGN.CENTER,PALERED,RED)
add_text(s,'Target: dependency-local recovery',6.8,1.25,5.9,.42,14,True,TEAL,PP_ALIGN.CENTER,PALEGREEN,TEAL)
box(s,'App A / D stay local',7.1,2.0,2.15,.65,GREEN,size=11); box(s,'B service VIP / discovery',9.7,2.0,2.4,.65,CYAN,size=10); arrow(s,9.25,2.32,9.7,2.32)
box(s,'B1 Site 1\npreferred',7.75,3.3,1.7,.68,GREEN,size=10); box(s,'B2 Site 2\nfallback',10.2,3.3,1.7,.68,GREEN,size=10); arrow(s,10.9,2.65,8.6,3.3); arrow(s,10.9,2.65,11.05,3.3,TEAL,dash=True)
add_text(s,'B1 failure → withdraw B1 → bounded retry to B2 → A/D remain in Site 1',7.25,4.55,5.3,.8,10.7,True,NAVY,PP_ALIGN.CENTER,PALEGREEN,RGBColor(92,164,82))
add_text(s,'Health contract caution: A should not become globally unhealthy merely because an optional B/C feature is degraded.',1.05,6.15,11.2,.5,10.2,True,NAVY,PP_ALIGN.CENTER,PALEYELLOW,GOLD); footer(s,8)

# 9 topology names
s=slide(); title(s,'WAF topology options remain a separate decision','Health-monitoring target applies regardless of which WAF topology is selected.')
cards=[('W1','Tenant LTM → independent active WAF pool','best dedicated maintenance headroom'),('W2','WAF HA / DSC cluster','simple HA; pair boundary'),('W3','Preferred WAFs + shared reserve','dedicated normal path + shared spare'),('W4','Site 1 cluster + extra WAF','asymmetric'),('S1','Tenant LTMs → shared active WAF pool','preferred cost/resilience candidate'),('S2','Shared LTM + shared WAF pool','future consolidation; largest common domain')]
for i,(k,d,r) in enumerate(cards):
    x=.55+(i%3)*4.2; y=1.35+(i//3)*2.5
    add_text(s,k,x,y,3.85,.42,16,True,NAVY,PP_ALIGN.LEFT,GREEN if k in ('W1','S1') else LIGHT,NAVY)
    add_text(s,d,x,y+.5,3.85,.82,10.5,True,DARK,PP_ALIGN.LEFT,WHITE,MID)
    add_text(s,r,x,y+1.42,3.85,.52,9.3,False,SLATE,PP_ALIGN.LEFT,WHITE,MID)
add_text(s,'Recommendation remains: validate S1 first; use dedicated W1 when shared WAF policy/configuration/capacity risk cannot be accepted.',.8,6.48,11.75,.45,10.5,True,NAVY,PP_ALIGN.CENTER,PALEGREEN,RGBColor(92,164,82)); footer(s,9)

# 10 99.95 failures
s=slide(); title(s,'99.95% availability depends on recovery domain','Routine failures should remain local; GTM/site failover is for endpoint/site failure, not every member failure.')
add_text(s,'99.95 budget',.55,1.28,2.25,.42,14,True,WHITE,PP_ALIGN.CENTER,NAVY,NAVY); add_text(s,'4h 22m 48s\nper year',.55,1.76,2.25,1.0,20,True,WHITE,PP_ALIGN.CENTER,NAVY2,NAVY2)
rows=[('1 backend/Pod/VM','local ELB/LTM','R0/R1'),('1 WAF node','local LTM WAF pool','R0/R1'),('1 LTM peer','HA peer','R1'),('whole external endpoint path','GTM external L7','R3 or X2'),('whole internal endpoint path','GTM/internal L7','internal endpoint move'),('App B local','service VIP/discovery','XD1 target'),('whole site','GTM + DR','R3')]
simple_table(s,['Failure','Best recovery domain','Target class'],rows,3.1,1.3,[4.3,3.4,2.2],.61,9.0)
add_text(s,'Management test: planned maintenance should usually be no-outage or seconds-scale, with enough redundancy left for one additional credible failure where required.',.8,6.22,11.75,.58,11,True,NAVY,PP_ALIGN.CENTER,PALEYELLOW,GOLD); footer(s,10)

# 11 cross-site
s=slide(); title(s,'Cross-site capability is a target contingency, not current-state dependency','Design early where it materially reduces failure-domain escalation.')
bullet_block(s,'X2A remote WAF',['local LTM survives','borrow remote WAF','route back to local CFW/app','avoids DNS/app move'],.55,1.4,3.75,4.7,PALEGREEN,MID,TEAL,9.8)
bullet_block(s,'X2B remote front-end',['local front-end lost','remote edge/LTM/WAF serves client','route back to healthy local app','still needs GTM/DNS convergence'],4.8,1.4,3.75,4.7,LIGHT,MID,TEAL,9.8)
bullet_block(s,'XD1 dependency fallback',['A/D remain local','B1 preferred','B2 remote fallback','dependency-local recovery before broad DR'],9.05,1.4,3.75,4.7,GREEN,MID,TEAL,9.8)
add_text(s,'Invariant: healthy local service must not depend on the inter-site link. Test network partition while both sites are otherwise healthy.',.85,6.35,11.65,.48,11,True,NAVY,PP_ALIGN.CENTER,PALEYELLOW,GOLD); footer(s,11)

# 12 app types
s=slide(); title(s,'Application type determines the real recovery time','Infrastructure can recover first while sessions, sockets or transactions are still broken.')
cols=[('AT1 Stateless web',['safe retry','idempotency','external/shared state']),('AT2 Stateful web',['portable session/state','re-auth / reconstruction','transaction reconciliation']),('AT3 WebSocket',['reconnect + backoff/jitter','re-auth + resubscribe','sequence/gap/replay']),('AT4 Non-web / L4',['protocol reconnect','DNS/service re-resolution','safe transaction replay'])]
for i,(h,items) in enumerate(cols): bullet_block(s,h,items,.5+i*3.2,1.5,2.85,4.65,[GREEN,RGBColor(225,238,252),PURPLE,RGBColor(224,244,242)][i],MID,NAVY,10.2)
add_text(s,'GTM L7 health should answer “can this endpoint accept new traffic?”; application recovery T6 answers “has the user/business flow actually recovered?”',.85,6.35,11.65,.48,10.5,True,NAVY,PP_ALIGN.CENTER,PALEGREEN,RGBColor(92,164,82)); footer(s,12)

# 13 cost
s=slide(); title(s,'Four-tenant infrastructure efficiency vs blast radius','Illustrative LTM + WAF device units across two sites — not vendor pricing.')
rows=[('Dedicated W1 — 3 WAF/tenant','40','Low'),('W3 — preferred + reserve','36','Medium'),('Dedicated W1 — 2 WAF/tenant','32','Low'),('S1 — tenant LTMs + shared WAF pool','24','High at WAF tier'),('S2 — shared LTM + shared WAF pool','12','Very high'),('Shared LTM + 2-node WAF HA cluster','8','Very high')]
simple_table(s,['Architecture','Device units','Cross-tenant blast radius'],rows,.65,1.4,[6.2,2.2,3.55],.70,10)
add_text(s,'Health design does not remove shared-platform risk: a bad shared WAF policy/configuration or exhausted shared capacity can still affect several tenants at once.',.85,6.25,11.65,.55,10.5,True,NAVY,PP_ALIGN.CENTER,PALEYELLOW,GOLD); footer(s,13)

# 14 change/gates
s=slide(); title(s,'Target implementation sequence and decision gates','Inventory first; then health contracts; then Layer-7 steering; then cross-site contingency.')
phases=[('0','Inventory current monitors / probes'),('1','Define app readiness contracts'),('2','Implement external + internal L7 endpoint health'),('3','Add prober diversity / cross-site visibility'),('4','Pilot B1→B2 dependency recovery'),('5','Pilot X2A/X2B where approved'),('6','Fault-inject and measure 99.95 evidence')]
for i,(n,t) in enumerate(phases):
    x=.55+i*1.78
    add_text(s,n,x,1.45,.42,.42,11,True,WHITE,PP_ALIGN.CENTER,TEAL,TEAL); add_text(s,t,x+.48,1.28,1.2,1.02,8.7,True,DARK,PP_ALIGN.CENTER,LIGHT,MID)
    if i<6: arrow(s,x+1.68,1.66,x+1.78,1.66,TEAL)
checks=['external + internal VIP health contracts documented','one member failure remains local','GTM never advertises broken required service path','inter-site link loss does not withdraw healthy local site','GTM/prober convergence measured','App A/B/C/D cascade tested','WebSocket/stateful T6 tested','planned maintenance + extra failure tested','rollback/failback tested']
add_text(s,'Before claiming target readiness',.7,3.05,3.3,.42,13,True,NAVY,radius=False)
for i,ch in enumerate(checks):
    x=.75+(i%3)*4.05; y=3.55+(i//3)*.72
    add_text(s,'✓',x,y,.28,.28,10,True,TEAL,PP_ALIGN.CENTER,radius=False); add_text(s,ch,x+.32,y,3.55,.42,8.8,False,DARK,radius=False)
add_text(s,'Change safety remains part of the SLO: never change both sites together; drain one member at a time; preserve a known-good rollback path.',.85,6.25,11.65,.55,10.5,True,NAVY,PP_ALIGN.CENTER,PALEYELLOW,GOLD); footer(s,14)

# 15 timing
s=slide(); title(s,'Appendix — timing shorthand','Planning categories, not SLAs. Measure end-to-end to a successful business transaction.')
rows=[('T1','BIG-IP HA peer/device failover','~3s+ detection + convergence'),('T2','LTM/WAF member detection','commonly up to ~16s'),('T3','GTM health observation','monitor/config specific'),('T4','GTM state + DNS convergence','state learning/sync + answer + TTL/re-resolution'),('T5','Manual / warm / cold recovery','minutes+; procedure dependent'),('T6','Application recovery','retry/reconnect/re-auth/state/replay'),('T7','Failback','controlled return'),('T8','DNS/cache/existing connection','behaviour modifier'),('T9','CFW recovery','product/config specific; measure')]
simple_table(s,['ID','Meaning','Management interpretation'],rows,.7,1.3,[1.0,4.9,5.9],.54,9.1)
add_text(s,'Critical addition: where GTM health is site-local only, include the measured GTM synchronization/state-learning delay before DNS TTL and T6.',.95,6.55,11.4,.44,10.3,True,NAVY,PP_ALIGN.CENTER,PALEGREEN,RGBColor(92,164,82)); footer(s,15)

prs.save(OUT)
print(OUT)
