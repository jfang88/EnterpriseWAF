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
DARK=RGBColor(22,36,50); ORANGE=RGBColor(209,119,20); WHITE=RGBColor(255,255,255); RED=RGBColor(190,49,68)
SLATE=RGBColor(74,91,107)

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

def box(s,text,x,y,w,h,fill=CYAN,line=NAVY,size=11,bold=True):
    return add_text(s,text,x,y,w,h,size,bold,DARK,PP_ALIGN.CENTER,fill,line)

def arrow(s,x1,y1,x2,y2,color=NAVY,width=2,dash=False):
    ln=s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,Inches(x1),Inches(y1),Inches(x2),Inches(y2))
    ln.line.color.rgb=color; ln.line.width=Pt(width)
    if dash: ln.line.dash_style=MSO_LINE_DASH_STYLE.DASH
    ln.line._get_or_add_ln().append(parse_xml(f'<a:headEnd {nsdecls("a")} type="none"/>'))
    ln.line._get_or_add_ln().append(parse_xml(f'<a:tailEnd {nsdecls("a")} type="triangle"/>'))
    return ln

def title(s,t,st=None):
    add_text(s,t,.48,.22,12.3,.42,25,True,NAVY,radius=False)
    if st: add_text(s,st,.5,.67,12.2,.3,10.5,False,SLATE,radius=False)

def footer(s,n):
    add_text(s,'EnterpriseWAF management summary',.5,7.16,3,.18,7.5,False,SLATE,radius=False)
    add_text(s,f'Nov 2026  •  {n}',11.7,7.16,1.1,.18,7.5,False,SLATE,PP_ALIGN.RIGHT,radius=False)

def bullet_block(s,heading,items,x,y,w,h,fill=LIGHT,line=MID,headfill=NAVY):
    add_text(s,heading,x,y,w,.38,13,True,WHITE,PP_ALIGN.CENTER,headfill,headfill)
    add_text(s,'\n'.join('• '+i for i in items),x,y+.44,w,h-.44,10.5,False,DARK,PP_ALIGN.LEFT,fill,line)

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

# 1
s=slide()
add_text(s,'EnterpriseWAF',.5,.55,12.2,.55,30,True,WHITE,PP_ALIGN.LEFT,NAVY,NAVY)
add_text(s,'Management summary — architecture, resilience & 99.95% availability',.55,1.22,12,.48,20,False,NAVY,radius=False)
bullet_block(s,'Recommended balance',['Retain tenant-specific LTM failure domains.','Evaluate a shared independent active WAF pool (S1).','Require aggregate N-2 capacity and tenant policy isolation.'],.65,2.2,3.8,2.25,GREEN)
bullet_block(s,'Highest isolation',['Dedicated W1: 2 LTMs + 3 independent active WAFs per tenant/site.','Best change headroom and smallest cross-tenant blast radius.'],4.78,2.2,3.8,2.25,LIGHT)
bullet_block(s,'Core management message',['Topology alone does not deliver 99.95%.','Health-check depth, dependency recovery, app reconnect/state and change sequencing determine service availability.'],8.92,2.2,3.75,2.25,LIGHT)
add_text(s,'Decision requested: validate S1 as the cost/resilience target; retain dedicated W1 as the fallback if shared WAF controls cannot be proven.',.9,5.55,11.6,.65,15,True,NAVY,PP_ALIGN.CENTER,RGBColor(235,248,233),RGBColor(92,164,82)); footer(s,1)

# 2
s=slide(); title(s,'Decision in one page','Two target architectures; everything else is a trade-off or fallback.')
bullet_block(s,'Preferred cost / resilience target — S1',['4 tenants • 2 sites','Tenant-specific 2-LTM HA pairs','Shared independent active WAF pool','4+ WAF nodes/site initially','Size survivors for aggregate N-2'],.6,1.35,5.8,4.8,GREEN)
bullet_block(s,'Fallback / high-isolation target — dedicated W1',['Per tenant/site: 2-LTM HA pair + 3 independent active WAFs','Use when cross-tenant shared-policy/configuration risk is unacceptable','Higher device count; simpler blast-radius reasoning'],6.9,1.35,5.8,4.8,LIGHT); footer(s,2)

# 3
s=slide(); title(s,'What the topology names mean','Management shorthand used throughout the analysis.')
cards=[('W1','Dedicated LTM pair → independent active WAF pool','Horizontal scale; strong maintenance flexibility'),('W2','WAF HA/DSC cluster','One active owner per traffic group; peer failover'),('W3','Tenant preferred WAFs + shared reserve','Dedicated normal path; shared spare capacity'),('W4','Site 1 cluster + extra WAF; Site 2 cluster only','Asymmetric primary-site strength'),('S1','Tenant LTMs → shared independent active WAF pool','Preferred shared-resilience candidate'),('S2','Shared LTM + shared active WAF pool','Lowest device count; future consolidation only')]
for i,(k,d,r) in enumerate(cards):
    x=.6+(i%3)*4.2; y=1.45+(i//3)*2.45
    add_text(s,k,x,y,3.8,.42,16,True,NAVY,PP_ALIGN.LEFT,GREEN if k in ('W1','S1') else LIGHT,NAVY)
    add_text(s,d,x,y+.5,3.8,.8,11,True,DARK,PP_ALIGN.LEFT,WHITE,MID)
    add_text(s,r,x,y+1.35,3.8,.55,9.5,False,SLATE,PP_ALIGN.LEFT,WHITE,MID)
add_text(s,'Key distinction: W1 / S1 / S2 are active WAF pools; W2 / W4 are HA-cluster patterns; W3 combines preferred active WAFs with reserve capacity.',.75,6.45,11.85,.48,10.5,True,NAVY,PP_ALIGN.CENTER,RGBColor(235,248,233),RGBColor(92,164,82)); footer(s,3)

# 4
s=slide(); title(s,'Grounded end-to-end architecture','DNS/control plane is separate from application data; internal network is outside the private cloud.')
box(s,'External users /\nAPI clients',.25,1.35,1.25,.75,LIGHT,size=11); box(s,'External /\ncustomer DNS',1.65,1.35,1.25,.75,LIGHT,size=11); box(s,'Private leased line /\nVPN / extranet',3.05,1.35,1.35,.75,LIGHT,size=10); arrow(s,1.5,1.73,1.65,1.73); arrow(s,2.9,1.73,3.05,1.73)
add_text(s,'Enterprise internal network — outside private cloud',.25,4.55,4.3,.34,10.5,True,WHITE,PP_ALIGN.CENTER,NAVY,NAVY)
for txt,x,w in [('Internal users /\nsystems',.3,1.0),('Internal\nenterprise DNS',1.4,1.05),('Internal LTM /\nservice VIP',2.55,1.0),('Internal\nfirewall',3.65,.9)]: box(s,txt,x,5.0,w,.68,LIGHT if x<2.5 else CYAN,size=10)
arrow(s,1.3,5.34,1.4,5.34); arrow(s,2.45,5.34,2.55,5.34); arrow(s,3.55,5.34,3.65,5.34)
site1x=4.65; site2x=9.0; colw=3.9
for x,name in [(site1x,'Site 1 — Primary'),(site2x,'Site 2 — DR / Secondary')]:
    add_text(s,name,x,1.0,colw,.38,16,True,WHITE,PP_ALIGN.CENTER,NAVY,NAVY)
    box(s,'2 × HA edge-firewall pairs\n(2 devices per pair)',x+.25,1.55,3.4,.54,CYAN,size=10)
    box(s,'GTM / DNS cluster\n(edge service)',x+.25,2.2,1.55,.62,GREEN,size=10)
    box(s,'Tenant LTM HA\nservice',x+2.0,2.2,1.65,.62,CYAN,size=10)
    box(s,'WAF tier',x+2.0,2.95,1.65,.52,RGBColor(206,241,239),size=11)
    arrow(s,x+1.95,2.09,x+1.0,2.2,ORANGE,dash=True); arrow(s,x+2.95,2.09,x+2.83,2.2); arrow(s,x+2.83,2.82,x+2.83,2.95)
    bd=s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,Inches(x+.15),Inches(3.7),Inches(3.6),Inches(2.65)); bd.fill.solid();bd.fill.fore_color.rgb=PURPLE;bd.fill.transparency=25;bd.line.color.rgb=PURPLE_LINE;bd.line.width=Pt(1.5)
    add_text(s,'Private cloud boundary',x+.55,3.72,2.8,.3,10,True,WHITE,PP_ALIGN.CENTER,PURPLE_LINE,PURPLE_LINE)
    box(s,'CFW',x+.45,4.15,1.05,.48,CYAN,size=10); box(s,'ELB / service',x+1.75,4.15,1.55,.48,CYAN,size=10); arrow(s,x+1.5,4.39,x+1.75,4.39)
    box(s,'App A',x+.45,4.85,1.0,.5,GREEN,size=10); box(s,'App D',x+1.55,4.85,.9,.5,GREEN,size=10); box(s,'B service VIP',x+2.55,4.85,.8,.5,CYAN,size=8.5)
    arrow(s,x+2.52,4.63,x+.95,4.85); arrow(s,x+2.52,4.63,x+2.0,4.85)
    box(s,'App B',x+.75,5.65,1.0,.48,GREEN,size=10); box(s,'App C / deps',x+2.0,5.65,1.15,.48,GREEN,size=9); arrow(s,x+2.95,5.35,x+1.25,5.65); arrow(s,x+1.75,5.89,x+2.0,5.89)
    arrow(s,x+2.83,3.47,x+.98,4.15)
arrow(s,4.4,1.73,site1x+.25,1.82)
arrow(s,2.0,5.0,site1x+1.0,2.82,ORANGE,dash=True); add_text(s,'selected internal names\nuse same edge GTM',2.55,4.28,1.65,.36,8,False,ORANGE,radius=False)
arrow(s,4.4,5.34,site1x+.45,4.39)
arrow(s,site1x+1.8,2.48,site2x+.25,2.48,TEAL,dash=True); arrow(s,site2x+.25,2.60,site1x+1.8,2.60,TEAL,dash=True)
arrow(s,site1x+3.65,3.15,site2x+2.0,3.15,TEAL,dash=True); add_text(s,'X2A remote-WAF\ncontingency',7.55,2.95,1.25,.34,8,True,TEAL,PP_ALIGN.CENTER,WHITE,TEAL)
arrow(s,site2x+2.0,3.48,site1x+1.48,4.38,TEAL,dash=True); add_text(s,'X2B route-back',7.62,3.45,1.05,.34,8,True,TEAL,PP_ALIGN.CENTER,WHITE,TEAL)
arrow(s,site1x+3.35,5.1,site2x+1.25,5.65,TEAL,dash=True); add_text(s,'XD1 B2\nfallback',7.7,5.40,1.0,.4,8,True,TEAL,PP_ALIGN.CENTER,WHITE,TEAL)
add_text(s,'Fixed facts: GTM clusters synchronize across sites • GTM is inside the edge-firewall boundary • both sites have 2 × 2 edge firewalls • same edge GTM serves selected external + internal DNS names • internal firewall is distinct from CFW',.35,6.72,12.55,.42,9.0,True,NAVY,PP_ALIGN.CENTER,RGBColor(235,248,233),RGBColor(92,164,82)); footer(s,4)

# 5
s=slide(); title(s,'99.95% availability: what management should expect','The SLO is an end-to-end service budget, not a device-uptime claim.')
add_text(s,'Availability budget',.65,1.45,2.4,.45,14,True,WHITE,PP_ALIGN.CENTER,NAVY,NAVY); add_text(s,'4h 22m 48s\nper year',.65,1.95,2.4,1.15,22,True,WHITE,PP_ALIGN.CENTER,NAVY2,NAVY2)
rows=[('Dedicated W1, 3 WAF','Very strong','Excellent','Low'),('S1 shared active pool','Very strong*','Excellent','Medium'),('W3 preferred + reserve','Strong','Very good','Medium'),('W2 2-node cluster','Strong / less margin','Moderate','Low'),('W4 asymmetric','Strong / asymmetric','Mixed','Low'),('Shared LTM + shared WAF','Conditional','Mixed','High')]
simple_table(s,['Architecture','99.95 potential','Maintenance margin','Common-mode risk'],rows,3.45,1.45,[3.0,2.0,2.0,1.8],.56,8.5)
add_text(s,'Management test: remove one component for planned change and still tolerate one additional credible failure without a material service outage.',.85,5.65,11.7,.65,13,True,NAVY,PP_ALIGN.CENTER,RGBColor(255,247,220),RGBColor(226,191,80)); footer(s,5)

# 6
s=slide(); title(s,'Most likely / credible failure modes and target recovery','Routine failures should remain local; broader recovery only when the local failure domain is exhausted.')
bullet_block(s,'Tier A — absorb locally',['1 LTM / WAF / CFW member','1 backend/Pod/VM','one circuit/path','planned rolling maintenance'],.55,1.4,3.8,4.7,GREEN)
bullet_block(s,'Tier B — automatic component / dependency recovery',['2 WAFs / whole WAF tier','App B dependency failure','front-end tier failure with healthy app','prefer R2 component/dependency recovery'],4.75,1.4,3.8,4.7,LIGHT)
bullet_block(s,'Tier C — true DR',['whole site / local platform unavailable','unrecoverable CFW/application/data path','full application/site recovery'],8.95,1.4,3.8,4.7,RGBColor(255,235,221),ORANGE); footer(s,6)

# 7
s=slide(); title(s,'A shared application dependency can cause a multi-application outage','The dependency graph can dominate availability even when WAF/LTM/CFW and the applications themselves are healthy.')
add_text(s,'Without XD1 dependency fallback',.65,1.35,5.8,.42,14,True,RED,PP_ALIGN.CENTER,RGBColor(255,240,240),RED)
box(s,'App B @ Site 1\nFAILS',2.2,2.0,2.5,.72,RGBColor(255,225,225),RED,11); arrow(s,3.45,2.72,1.6,3.4,RED); arrow(s,3.45,2.72,3.45,3.4,RED); arrow(s,3.45,2.72,5.3,3.4,RED)
for txt,x in [('App A\ntimeout/retry',.65),('App C\ntimeout/retry',2.7),('App D\ntimeout/retry',4.75)]: box(s,txt,x,3.4,1.6,.7,RGBColor(255,247,220),ORANGE,10)
add_text(s,'threads / connection pools fill → readiness checks may fail → GTM withdraws multiple VIPs → several apps move to Site 2',.75,4.55,5.5,1.0,11,True,RED,PP_ALIGN.CENTER,RGBColor(255,240,240),RED)
add_text(s,'With XD1 dependency fallback',6.85,1.35,5.8,.42,14,True,TEAL,PP_ALIGN.CENTER,RGBColor(235,248,233),TEAL)
box(s,'A / C / D stay local',7.2,2.0,2.2,.72,GREEN,size=11); box(s,'B service VIP /\nhealth-aware discovery',9.8,2.0,2.4,.72,CYAN,size=10); arrow(s,9.4,2.36,9.8,2.36)
box(s,'B1 Site 1\npreferred',8.0,3.25,1.6,.7,GREEN,size=10); box(s,'B2 Site 2\nfallback',10.3,3.25,1.6,.7,GREEN,size=10); arrow(s,11.0,2.72,8.8,3.25); arrow(s,11.0,2.72,11.1,3.25,TEAL,dash=True)
add_text(s,'B1 failure → withdraw B1 → bounded retry to B2 → A/C/D remain in Site 1',7.25,4.55,5.3,.82,11,True,NAVY,PP_ALIGN.CENTER,RGBColor(235,248,233),RGBColor(92,164,82)); footer(s,7)

# 8
s=slide(); title(s,'Cross-site capability should be designed early','Build routes, security policy, health checks and service abstractions early; use them as contingency rather than normal dependency.')
bullet_block(s,'Without cross-site component routing',['local WAF tier failure can force whole-site/application recovery','DNS/GTM convergence + reconnect/login surge','healthy local app may move unnecessarily'],.65,1.45,5.6,4.8,RGBColor(255,240,240),RED)
bullet_block(s,'With X2A / X2B / XD1',['X2A: local LTM can borrow remote WAF','X2B: remote front-end can route back to healthy local CFW/app','XD1: local A/C/D can use remote B2'],6.85,1.45,5.6,4.8,GREEN)
add_text(s,'Cross-site paths are contingency only. Healthy local service must continue if the inter-site path fails.',1.1,6.35,11.1,.48,12,True,NAVY,PP_ALIGN.CENTER,RGBColor(235,248,233),RGBColor(92,164,82)); footer(s,8)

# 9
s=slide(); title(s,'Application type determines the real recovery time','Infrastructure recovery is not complete until the application has recovered its session, state or protocol.')
cols=[('Stateless web',['safe retry','idempotency','external/shared state']),('Stateful web',['portable/replicated session state','re-auth / reconstruction','transaction reconciliation']),('WebSocket / long-lived',['reconnect + backoff/jitter','re-auth + resubscribe','sequence/gap/replay']),('Non-web / L4',['protocol reconnect','DNS/service re-resolution','safe transaction replay'])]
for i,(h,items) in enumerate(cols): bullet_block(s,h,items,.5+i*3.2,1.5,2.85,4.7,[GREEN,RGBColor(225,238,252),PURPLE,RGBColor(224,244,242)][i],MID)
footer(s,9)

# 10
s=slide(); title(s,'Four-tenant infrastructure efficiency vs blast radius','Illustrative LTM + WAF device units across two sites — not vendor pricing.')
rows=[('Dedicated W1 — 3 WAF/tenant','40','Low'),('W3 — preferred + reserve','36','Medium'),('Dedicated W1 — 2 WAF/tenant','32','Low'),('S1 — tenant LTMs + shared WAF pool','24','High at WAF tier'),('S2 — shared LTM + shared WAF pool','12','Very high'),('Shared LTM + shared WAF HA cluster','8','Very high')]
simple_table(s,['Architecture','Device units','Blast radius'],rows,.7,1.4,[6.4,2.2,3.2],.7,10)
add_text(s,'Interpretation: cost falls as sharing rises, but shared policy/configuration/capacity failure can affect more tenants simultaneously.',1.0,6.25,11.3,.55,12,True,NAVY,PP_ALIGN.CENTER,RGBColor(255,247,220),RGBColor(226,191,80)); footer(s,10)

# 11
s=slide(); title(s,'Change strategy is part of the availability design','99.95% is lost just as easily through poor change sequencing as through hardware failure.')
steps=['Never change both sites at once','Drain one active member at a time','Keep one known-good path during WAF policy changes','Separate WAF/LTM/CFW/application high-risk changes','Use staging/canary/Policy Diff before broad enforcement','Do not start shared-service changes when alternate site/reserve is degraded','Validate business transactions after each change','For long-lived apps, trigger controlled reconnect rather than waiting indefinitely']
for i,st in enumerate(steps):
    x=.7+(i%2)*6.1; y=1.35+(i//2)*1.15
    add_text(s,str(i+1),x,y,.45,.45,12,True,WHITE,PP_ALIGN.CENTER,NAVY2,NAVY2); add_text(s,st,x+.6,y,5.2,.5,10.5,True,DARK,PP_ALIGN.LEFT,LIGHT,MID)
add_text(s,'Management acceptance test: can one component be deliberately removed for change and one additional unplanned failure still occur without a material service outage?',1.0,6.05,11.3,.68,11.5,True,NAVY,PP_ALIGN.CENTER,RGBColor(255,247,220),RGBColor(226,191,80)); footer(s,11)

# 12
s=slide(); title(s,'Recommendation and decision gates','Approve a target architecture only after the failure and maintenance behaviours are demonstrated.')
bullet_block(s,'Recommended balanced target',['Tenant-specific 2-LTM HA pair','Shared independent active WAF pool (4+ nodes/site initially)','Aggregate N-2 capacity','Tenant-isolated policy/routing','X2A / XD1 where approved'],.6,1.35,5.8,2.8,GREEN)
bullet_block(s,'Fallback when shared WAF controls are not acceptable',['Dedicated W1: 2 LTM + 3 independent active WAFs per tenant/site','Highest isolation and maintenance confidence'],6.9,1.35,5.8,2.8,LIGHT)
checks=['Peak + failure-mode WAF throughput','One/two WAF failures and N-2 capacity','LTM pair and CFW failure','Cross-site WAF route-back','App A/B/C/D dependency graph + B1→B2 fallback','Stateless/stateful/WebSocket/non-web recovery','Bad WAF policy rollback/canary','Site 2 aggregate DR capacity','Planned maintenance + one additional injected failure']
add_text(s,'Before claiming 99.95%',.7,4.45,3.2,.42,13,True,NAVY,radius=False)
for i,ch in enumerate(checks):
    x=.75+(i%3)*4.05; y=4.95+(i//3)*.57
    add_text(s,'✓',x,y,.28,.28,10,True,TEAL,PP_ALIGN.CENTER,radius=False); add_text(s,ch,x+.32,y,3.55,.3,8.7,False,DARK,radius=False)
footer(s,12)

# 13
s=slide(); title(s,'GTM health quality determines failover quality','A synchronized GTM cluster can still advertise the wrong site when the health signal is too shallow.')
add_text(s,'Fixed architecture',.5,1.35,3.8,.42,15,True,WHITE,PP_ALIGN.CENTER,NAVY,NAVY); box(s,'Site 1 GTM\ncluster',.75,2.0,1.35,.65,GREEN,size=11); box(s,'Site 2 GTM\ncluster',2.7,2.0,1.35,.65,GREEN,size=11); arrow(s,2.1,2.32,2.7,2.32,TEAL,dash=True); arrow(s,2.7,2.48,2.1,2.48,TEAL,dash=True); add_text(s,'sync config / global\navailability view',1.55,2.75,1.7,.42,8.5,True,TEAL,PP_ALIGN.CENTER,radius=False); box(s,'Same edge GTM service is used for selected\nexternal and internal DNS names',.75,3.45,3.3,.75,LIGHT,size=10)
add_text(s,'Health signal depth',4.75,1.35,3.8,.42,15,True,WHITE,PP_ALIGN.CENTER,NAVY,NAVY); box(s,'TCP / port-up\nonly',5.0,2.0,1.45,.65,RGBColor(255,235,221),ORANGE,11); box(s,'HTTP / L7 check',6.65,2.0,1.45,.65,CYAN,size=11); add_text(s,'False-green risk',5.0,2.82,1.45,.35,9,True,RED,PP_ALIGN.CENTER,radius=False); add_text(s,'WAF listener may be up while CFW / ELB / app is broken.',4.95,3.25,3.3,.78,10,False,DARK,PP_ALIGN.CENTER,LIGHT,MID); add_text(s,'Application teams must define the check contract: URI/host, expected response, auth and dependency semantics.',4.95,4.25,3.3,.95,10,True,NAVY,PP_ALIGN.CENTER,RGBColor(235,248,233),RGBColor(92,164,82))
add_text(s,'Convergence impact',9.0,1.35,3.8,.42,15,True,WHITE,PP_ALIGN.CENTER,NAVY,NAVY); box(s,'Cross-site / distributed health observation',9.25,2.0,3.3,.65,GREEN,size=10); add_text(s,'Both sites can see relevant health directly; global decisions can converge more consistently.',9.25,2.8,3.3,.75,10,False,DARK,PP_ALIGN.CENTER,LIGHT,MID); box(s,'Site-local probes only',9.25,3.85,3.3,.65,RGBColor(255,235,221),ORANGE,10); add_text(s,'Remote GTM may learn failure through synchronization / timeout behavior. Add this delay before DNS TTL and client recovery.',9.25,4.65,3.3,1.02,10,True,NAVY,PP_ALIGN.CENTER,LIGHT,MID)
add_text(s,'Management implication: do not count “GTM/WAF green” as service availability unless the health model represents the agreed business-service readiness boundary.',.55,6.25,12.25,.62,12,True,WHITE,PP_ALIGN.CENTER,NAVY2,NAVY2); footer(s,13)

# 14
s=slide(); title(s,'Appendix — timing shorthand used in the analysis','Planning values, not SLAs. Measure end-to-end recovery to a successful business transaction.')
rows=[('T1','BIG-IP HA peer/device failover','~3s+ detection + convergence'),('T2','LTM/WAF member detection','commonly up to ~16s'),('T3','GTM health observation','monitor/config specific'),('T4','GTM global-state + DNS convergence','sync/decision + TTL + re-resolution'),('T5','Manual / warm / cold recovery','minutes+; procedure dependent'),('T6','Application recovery','retry/reconnect/re-auth/state/replay'),('T7','Failback','controlled return'),('T8','DNS/cache/existing connection','behaviour modifier'),('T9','CFW recovery','product/config-specific; measure')]
simple_table(s,['ID','Meaning','Management interpretation'],rows,.7,1.4,[1.0,5.0,5.8],.54,9.2)
add_text(s,'Important: if GTM probes only locally, include the measured GTM synchronization/learning delay before DNS TTL and T6.',1.0,6.65,11.3,.42,10.5,True,NAVY,PP_ALIGN.CENTER,RGBColor(235,248,233),RGBColor(92,164,82)); footer(s,14)

prs.save(OUT)
print(OUT)
