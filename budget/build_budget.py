from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import os, math

USD_CAD=1.39; HST=1.13; CONTING=1.10; DMG=30.0; SUBS=180.0; MEGABUS=110.0
def rooms(n): return math.ceil(n/4)
def cars(n): return math.ceil(n/4)
def vld_car(rt,days):
    t=46+37*(days-1); t=min(t,220) if days>=6 else t
    return (t+0.29*min(rt,300)+0.19*max(0,rt-300)+DMG)*HST

# cur: USD or CAD ; mode: DRIVE/FLY/BUS ; fixed: forced headcount or None
CONF={
"UPMUNC":dict(full="UPMUNC – Penn",city="Philadelphia, PA",dates="Oct 15-18, 2026",cur="USD",mode="DRIVE",km=617,days=4,hotel=200,deleg=95,perdel=110,free=None,fixed=None,dh="6.5h",note="Verify dates (usually Nov). Off-block $20/del/nt."),
"CIAC":dict(full="CIAC – Cornell",city="Ithaca, NY",dates="Oct 22-25, 2026",cur="USD",mode="DRIVE",km=297,days=4,hotel=149,deleg=75,perdel=90,free=10,fixed=None,dh="3.5h",note="Delegates 11+ FREE. Closest. $149/nt incl breakfast."),
"NCSC":dict(full="NCSC – Georgetown",city="Washington, DC",dates="Nov 5-8, 2026",cur="USD",mode="DRIVE",km=814,days=4,hotel=366,deleg=90,perdel=110,free=None,fixed=None,dh="8h",note="Washington Hilton; off-block $150/school/nt. Priciest hotel."),
"UNCMUNC":dict(full="UNCMUNC – UNC",city="Chapel Hill, NC",dates="Nov 19-22, 2026",cur="USD",mode="FLY",km=1350,days=6,flight=425,hotel=140,deleg=100,perdel=105,free=None,fixed=None,dh="fly",note="14-15h each way = fly. No host hotel block."),
"MCMUN":dict(full="McMUN – McGill",city="Montreal, QC",dates="Jan 28-31, 2027",cur="CAD",mode="BUS",hotel=234,deleg=80,perdel=125,free=None,fixed=20,dh="Megabus 3.5h",note="FIXED 20 del. Per-del EST (2027 table unposted, incl $20 social). Sheraton quad $234."),
"BUCKMUN":dict(full="BUCKMUN – Ohio State",city="Columbus, OH",dates="Feb 4-7, 2027",cur="USD",mode="DRIVE",km=951,days=5,hotel=150,deleg=75,perdel=75,free=None,fixed=None,dh="9h",note="INAUGURAL – fees ESTIMATED. Confirm w/ organizers."),
"CONMUN":dict(full="ConMUN – Concordia",city="Montreal, QC",dates="~Mar 11-14, 2027",cur="CAD",mode="BUS",hotel=229,deleg=100,perdel=125,free=None,fixed=20,dh="Megabus 3.5h",note="FIXED 20 del. 2027 dates TBD (2026 figs). DoubleTree $229/rm."),
"CHOMUN":dict(full="ChoMUN – UChicago",city="Chicago, IL",dates="Mar 25-28, 2027",cur="USD",mode="DRIVE",km=1088,days=5,hotel=201,deleg=50,perdel=110,free=None,fixed=None,dh="10h",note="Palmer House $201/quad. First-time deleg $50. 5% CC surcharge."),
"VICS":dict(full="VICS – UVA",city="Charlottesville, VA",dates="~Mar 25-28, 2027",cur="USD",mode="DRIVE",km=1000,days=5,hotel=189,deleg=85,perdel=105,free=None,fixed=None,dh="11-13h",note="VICS 31 dates TBD. Blocks $169-222; used $189."),
}
order=["UPMUNC","CIAC","NCSC","UNCMUNC","MCMUN","BUCKMUN","CONMUN","CHOMUN","VICS"]

def eff_n(k,scn): 
    f=CONF[k]['fixed']; return f if f else scn
def bd(k,n):
    c=CONF[k]; return c['free'] if (c['free'] and n>c['free']) else n
def m(x): return "$"+format(int(round(x)),",")

def parts(k,scn):
    c=CONF[k]; n=eff_n(k,scn)
    reg=c['deleg']+bd(k,n)*c['perdel']; hotel=rooms(n)*3*c['hotel']
    base_cad=(reg+hotel)*USD_CAD if c['cur']=="USD" else (reg+hotel)
    if c['mode']=="DRIVE": trans=vld_car(c['km']*2,c['days'])*cars(n)
    elif c['mode']=="FLY": trans=n*c['flight']*USD_CAD+850
    else: trans=n*MEGABUS
    sub=base_cad+trans; tot=sub*CONTING
    return dict(n=n,reg=reg,hotel=hotel,base=base_cad,trans=trans,sub=sub,tot=tot)

# styles
wb=Workbook()
NAVY=PatternFill("solid",fgColor="1F3864");BLUE=PatternFill("solid",fgColor="2E5496")
LBLUE=PatternFill("solid",fgColor="D9E1F2");GREY=PatternFill("solid",fgColor="F2F2F2")
YEL=PatternFill("solid",fgColor="FFF2CC");GREEN=PatternFill("solid",fgColor="E2EFDA");ORANGE=PatternFill("solid",fgColor="FCE4D6")
white=Font(color="FFFFFF",bold=True);bold=Font(bold=True)
thin=Side(style="thin",color="BFBFBF");border=Border(left=thin,right=thin,top=thin,bottom=thin)
def autos(ws,w):
    for i,x in enumerate(w,1): ws.column_dimensions[get_column_letter(i)].width=x

# ---------- SUMMARY ----------
ws=wb.active; ws.title="Summary"
hdr=[["Queen's Model United Nations – Conference Budget 2026-27","","","","","","","",""],
["Transport: US confs = Communauto Value plan + Long Distance · Montreal confs = Megabus · UNCMUNC = fly. Kingston origin. Sourced June 2026.","","","","","","","",""],
["4 del/room · 4 del/car · 3 nights · USD>CAD 1.39 · +10% contingency · McMUN & ConMUN FIXED at 20 del · excl. meals & faculty.","","","","","","","",""],
["","","","","","","","",""],
["Conference","City","Dates","Travel","8-del* – CAD","8-del* – USD","12-del* – CAD","12-del* – USD","Key note"]]
for r in hdr: ws.append(r)
g8=g12=0
for k in order:
    c=CONF[k]; p8=parts(k,8); p12=parts(k,12); g8+=p8['tot']; g12+=p12['tot']
    trav={"DRIVE":"Commauto "+c['dh'],"FLY":"Fly (YYZ-RDU)","BUS":c['dh']}[c['mode']]
    fx="  (20 fixed)" if c['fixed'] else ""
    ws.append([c['full'],c['city'],c['dates'],trav,m(p8['tot']),m(p8['tot']/USD_CAD),m(p12['tot']),m(p12['tot']/USD_CAD),(("FIXED 20 DEL. " if c['fixed'] else "")+c['note'])])
ws.append(["Conferences subtotal (9)","","","",m(g8),m(g8/USD_CAD),m(g12),m(g12/USD_CAD),"*US confs at 8 or 12; Montreal confs always 20"])
ws.append(["+ Communauto Value subscriptions","","","",m(SUBS),m(SUBS/USD_CAD),m(SUBS),m(SUBS/USD_CAD),"3 accts x $60/yr ($5/mo plan unlocks Long Distance)"])
ws.append(["PROGRAM TOTAL","","","",m(g8+SUBS),m((g8+SUBS)/USD_CAD),m(g12+SUBS),m((g12+SUBS)/USD_CAD),"+3 x $500 refundable Communauto bonds (not a cost)"])
ws.append(["","","","","","","","",""])
ws.append(["FLAGS: McMUN/ConMUN fees CAD-native, partly prior-year (2027 tables unposted) · BUCKMUN inaugural (estimated) · UPMUNC Oct dates unusual · VICS/ConMUN dates TBD.","","","","","","","",""])
# style
ws.merge_cells("A1:I1");ws["A1"].font=Font(bold=True,size=15,color="FFFFFF");ws["A1"].fill=NAVY;ws.row_dimensions[1].height=24
ws.merge_cells("A2:I2");ws.merge_cells("A3:I3");ws["A2"].font=Font(italic=True,size=9);ws["A3"].font=Font(italic=True,size=9)
for cc in range(1,10):
    x=ws.cell(row=5,column=cc);x.fill=BLUE;x.font=white;x.border=border;x.alignment=Alignment(wrap_text=True,vertical="center")
ws.row_dimensions[5].height=28
nrows=len(order)
for i in range(nrows):  # conf rows 6..6+nrows-1
    rr=6+i
    for cc in range(1,10): ws.cell(row=rr,column=cc).border=border
    ws.cell(row=rr,column=9).alignment=Alignment(wrap_text=True);ws.row_dimensions[rr].height=26
    if CONF[order[i]]['fixed']:
        for cc in range(1,10): ws.cell(row=rr,column=cc).fill=YEL
subrow=6+nrows; subsrow=subrow+1; progrow=subrow+2
for cc in range(1,10): ws.cell(row=subrow,column=cc).fill=LBLUE;ws.cell(row=subrow,column=cc).font=bold
for cc in range(1,10): ws.cell(row=progrow,column=cc).fill=NAVY;ws.cell(row=progrow,column=cc).font=white
ws.cell(row=progrow+2,column=1).font=Font(bold=True,color="C00000")
autos(ws,[24,17,17,17,12,12,12,12,52])

# ---------- DETAIL TABS ----------
def detail(scn):
    ws=wb.create_sheet(f"{scn} Delegates")
    ws.append([f"LINE-ITEM DETAIL – {scn}-delegate scenario (Montreal confs fixed at 20)","","","","",""])
    ws.append(["US confs USD>CAD @1.39. Montreal confs CAD-native (USD col = equiv). Communauto/Megabus native CAD, incl tax.","","","","",""])
    ws.append(["","","","","",""])
    ws.append(["Conference / Line item","Basis","Rate","Qty","USD","CAD"])
    def pair(amt,cur):
        return (m(amt),m(amt*USD_CAD)) if cur=="USD" else (m(amt/USD_CAD),m(amt))
    grand=0
    for k in order:
        c=CONF[k];p=parts(k,scn);n=p['n'];cur=c['cur']
        tag=f"  [FIXED {n} DEL]" if c['fixed'] else ""
        ws.append([f"▼ {c['full']}  ({c['city']}, {c['dates']}){tag}","","","","",""])
        u,cd=pair(c['deleg'],cur); ws.append(["   Delegation fee","flat","$"+str(c['deleg'])+f" {cur}","1",u,cd])
        b=bd(k,n);u,cd=pair(b*c['perdel'],cur);fn=" (11+ free)" if (c['free'] and n>c['free']) else ""
        ws.append(["   Delegate fees"+fn,f"{b} billable","$"+str(c['perdel'])+f" {cur}",str(b),u,cd])
        u,cd=pair(c['hotel']*rooms(n)*3,cur);ws.append(["   Hotel",f"{rooms(n)} rms x 3 nts","$"+str(c['hotel'])+f" {cur}",str(rooms(n)*3),u,cd])
        if c['mode']=="FLY":
            ws.append(["   Flights (RT YYZ)",f"{n} delegates","$"+str(c['flight'])+" USD",str(n),m(n*c['flight']),m(n*c['flight']*USD_CAD)])
            ws.append(["   Ground (KGN<>YYZ + xfer)","flat","—","—","~"+m(850/USD_CAD),m(850)])
        elif c['mode']=="BUS":
            ws.append(["   Megabus RT (Kingston<>Montreal)",f"{n} delegates","$110 CAD",str(n),m(n*MEGABUS/USD_CAD),m(n*MEGABUS)])
        else:
            pc=vld_car(c['km']*2,c['days']);t=46+37*(c['days']-1);t=min(t,220) if c['days']>=6 else t
            km=0.29*min(c['km']*2,300)+0.19*max(0,c['km']*2-300)
            ws.append([f"   Communauto Value+LongDist",f"{cars(n)} cars x {m(pc)}/car","gas incl",str(cars(n)),"—",m(pc*cars(n))])
            ws.append([f"      (per car: ${t:.0f} time + ${km:.0f} km + ${pc/HST-t-km:.0f} dmg, x13% HST)","","","","",""])
        ws.append(["   Subtotal","","","",m(p['sub']/USD_CAD),m(p['sub'])])
        ws.append(["   Contingency 10%","","","",m(p['sub']*0.10/USD_CAD),m(p['sub']*0.10)])
        ws.append([f"   TOTAL – {c['full']} ({c['mode']}, {n} del)","","","",m(p['tot']/USD_CAD),m(p['tot'])])
        ws.append(["","","","","",""])
        grand+=p['tot']
    ws.append(["+ Communauto Value subscriptions (3 accts x $60/yr)","","","",m(SUBS/USD_CAD),m(SUBS)])
    ws.append([f"PROGRAM TOTAL – {scn}-del scenario","","","",m((grand+SUBS)/USD_CAD),m(grand+SUBS)])
    # style
    ws.merge_cells("A1:F1");ws["A1"].font=Font(bold=True,size=12,color="FFFFFF");ws["A1"].fill=NAVY
    ws.merge_cells("A2:F2");ws["A2"].font=Font(italic=True,size=9)
    for cc in range(1,7): x=ws.cell(row=4,column=cc);x.fill=BLUE;x.font=white;x.border=border
    for rr in range(5,ws.max_row+1):
        a=str(ws.cell(row=rr,column=1).value or "")
        if a.startswith("▼"):
            fill=YEL if "[FIXED" in a else LBLUE
            for cc in range(1,7): ws.cell(row=rr,column=cc).fill=fill;ws.cell(row=rr,column=cc).font=bold
        elif a.strip().startswith("TOTAL") or a.startswith("PROGRAM"):
            fill=NAVY if a.startswith("PROGRAM") else GREY
            for cc in range(1,7): ws.cell(row=rr,column=cc).fill=fill
            if a.startswith("PROGRAM"):
                for cc in range(1,7): ws.cell(row=rr,column=cc).font=white
            else: ws.cell(row=rr,column=1).font=bold
        elif "Subtotal" in a or "Contingency" in a or a.strip().startswith("(per car") or a.startswith("+ Comm"):
            ws.cell(row=rr,column=1).font=Font(italic=True,size=9)
    autos(ws,[48,22,16,8,13,13])
detail(8); detail(12)

# ---------- SELECTED SLATE ----------
slate=[("NCSC",8),("CIAC",12),("VICS",12),("CHOMUN",8),("MCMUN",20),("CONMUN",20)]
ws=wb.create_sheet("Selected Slate")
ws.append(["SELECTED SLATE – NCSC(8) · CIAC(12) · VICS(12) · ChoMUN(8) · McMUN(20) · ConMUN(20)","","","",""])
ws.append(["Your chosen 6 conferences. US confs = Communauto Value+LongDist · Montreal confs = Megabus. CAD.","","","",""])
ws.append(["","","","",""])
ws.append(["Conference","Delegates","Travel","Reg+Hotel (CAD)","Total +10% (CAD)"])
st=0; trips=0
for k,n in slate:
    p=parts(k,n); st+=p['tot']; trips+=p['n']
    travel={"DRIVE":"Communauto","FLY":"Fly","BUS":"Megabus"}[CONF[k]['mode']]
    ws.append([CONF[k]['full'],str(p['n']),travel,m(p['base']),m(p['tot'])])
nslate=len(slate)
subrow=5+nslate; totrow=subrow+1
ws.append(["+ Communauto Value subscriptions (3 accts)","","","",m(SUBS)])
ws.append(["SLATE TOTAL",f"{trips} delegate-trips","","",m(st+SUBS)])
ws.append(["","","","",""])
ws.append([f"SLATE TOTAL: {m(st+SUBS)} CAD   ({m((st+SUBS)/USD_CAD)} USD)","","","",""])
ws.append(["Communauto: 3 Value accounts (1 driver/car for the US trips). Montreal trips by Megabus need no car/account.","","","",""])
ws.merge_cells("A1:E1");ws["A1"].font=Font(bold=True,size=12,color="FFFFFF");ws["A1"].fill=NAVY
ws.merge_cells("A2:E2");ws["A2"].font=Font(italic=True,size=9)
for cc in range(1,6): x=ws.cell(row=4,column=cc);x.fill=BLUE;x.font=white;x.border=border
for rr in range(5,5+nslate):
    for cc in range(1,6): ws.cell(row=rr,column=cc).border=border
    if CONF[slate[rr-5][0]]['mode']=="BUS":
        for cc in range(1,6): ws.cell(row=rr,column=cc).fill=YEL
for cc in range(1,6): ws.cell(row=subrow,column=cc).fill=LBLUE;ws.cell(row=subrow,column=cc).font=bold
for cc in range(1,6): ws.cell(row=totrow,column=cc).fill=NAVY;ws.cell(row=totrow,column=cc).font=white
ws.cell(row=totrow+2,column=1).font=Font(bold=True,size=12,color="1F3864")
ws.cell(row=totrow+3,column=1).font=Font(italic=True,size=9,color="C00000")
autos(ws,[24,16,14,18,18])

# ---------- ASSUMPTIONS ----------
ws=wb.create_sheet("Assumptions & Sources")
A=[["ASSUMPTIONS & SOURCES","",""],["","",""],
["GLOBAL","",""],
["Exchange rate","USD > CAD","1.39"],
["Rooming / car","delegates per room / car","4 / 4 (8>2 rms, 12>3, 20>5)"],
["Nights","Thu-Sun","3"],["Contingency","on subtotal","10%"],
["Montreal confs","McMUN & ConMUN","FIXED 20 delegates each"],
["Excluded","per scope","meals/per-diem, faculty travel"],
["","",""],
["TRANSPORT – US CONFS: COMMUNAUTO VALUE PLAN + LONG DISTANCE","",""],
["Plan","cheapest unlocking Long Distance","Value $5/mo (12-mo min $60/yr/account)"],
["Long Distance time / km","low season Oct16-Jun14","$46 d1 +$37/day · 29c/km <300, 19c after · gas incl"],
["Cars / accounts","1 driver-member per car","8 del=2 / 12 del=3 accounts"],
["Subscriptions","3 Value accts x $60/yr","$180/yr (in PROGRAM TOTAL)"],
["Bonds","per account, refundable","3 x $500 = $1,500 tied up (not a cost)"],
["Why not Open plan","Rules §9.7 + Plan Perks","$500 limit < single long-trip car AND no Long Distance -> unusable"],
["UNCMUNC","14-15h each way","FLY (YYZ-RDU ~$425 RT USD) + $850 ground"],
["","",""],
["TRANSPORT – MONTREAL CONFS: MEGABUS","",""],
["Route","Kingston <> Montreal direct, ~3.5h","Megabus/FlixBus, Kingston term 1175 John Counter"],
["Fare","RT per delegate, book early/together","$110 CAD (no group discount under 40 pax)"],
["","",""],
["PER-CONFERENCE SOURCES & FEES","",""],
["Conference","Registration source","Hotel"]]
src={"UPMUNC":["upmunc.org/conference-registration","Element/W Philadelphia Downtown"],
"CIAC":["ciaconline.org/register","Cayuga Blu Hotel, Ithaca ($149 incl bkfst)"],
"NCSC":["ncsc.modelun.org/registration","Washington Hilton (Dupont Circle)"],
"UNCMUNC":["uncmunc.org/registration","No block – 3-star Chapel Hill ~$140"],
"MCMUN":["mcmun.org (2027 fee table TBD)","Le Centre Sheraton, quad $234 CAD"],
"BUCKMUN":["buckmun.com (fees TBD – buckmun@ccwaosu.org)","Hyatt Place Columbus/OSU ~$150"],
"CONMUN":["conmun.org/en/registration (2026 figs)","DoubleTree by Hilton Montreal $229 CAD"],
"CHOMUN":["chomun.org/registration","Palmer House Hilton ($201/quad)"],
"VICS":["iro-vics.org / iro-vics.app","Hampton/Draftsman/Fairfield ($169-222)"]}
for k in order:
    c=CONF[k];cu=c['cur']
    A.append([f"{c['full']} – deleg ${c['deleg']} / del ${c['perdel']} / hotel ${c['hotel']} ({cu})",src[k][0],src[k][1]])
A+=[["","",""],["HOTEL SOURCING QUALITY","",""],
["Actual published block rate","ChoMUN $201, VICS $189, McMUN $234, ConMUN $229","CIAC $149 = prior-year block"],
["Proxy at known host hotel","NCSC $366 (Georgetown group rate), UPMUNC $200",""],
["Open-market estimate (no block exists)","BUCKMUN $150, UNCMUNC $140",""],
["","",""],["FLAGS / TO CONFIRM","",""],
["McMUN 2027 per-del fee","table unposted; used $125 CAD est","finance@mcmun.org"],
["ConMUN 2027 dates+fees","2026 figures used","conmun.org"],
["BUCKMUN inaugural","fees estimated","buckmun@ccwaosu.org"],
["UPMUNC Oct 15-18","unusual (usually Nov)","reconfirm"],
["CIAC delegates 11+ free","12-del pays for 10",""],
["Communauto: 1 account per car","credit limit + driver rule","8 del=2, 12 del=3 accounts"]]
for r in A: ws.append(r)
ws.merge_cells("A1:C1");ws["A1"].font=Font(bold=True,size=12,color="FFFFFF");ws["A1"].fill=NAVY;ws["A1"].alignment=Alignment(vertical="center")
heads={"GLOBAL","TRANSPORT – US CONFS: COMMUNAUTO VALUE PLAN + LONG DISTANCE","TRANSPORT – MONTREAL CONFS: MEGABUS","PER-CONFERENCE SOURCES & FEES","HOTEL SOURCING QUALITY","FLAGS / TO CONFIRM"}
for rr in range(1,ws.max_row+1):
    a=str(ws.cell(row=rr,column=1).value or "")
    if a in heads:
        for cc in range(1,4): ws.cell(row=rr,column=cc).fill=LBLUE;ws.cell(row=rr,column=cc).font=bold
    if a=="Conference":
        for cc in range(1,4): ws.cell(row=rr,column=cc).fill=BLUE;ws.cell(row=rr,column=cc).font=white
    if a.startswith("Why not Open"): ws.cell(row=rr,column=1).font=Font(bold=True,color="C00000")
autos(ws,[52,42,44])

# ---------- TRANSPORT OPTIONS ----------
def open_car(rt,d): return (60+55*(d-1)+0.34*max(0,rt-75)+DMG)*HST
def van(rt,toll,n): 
    v=1 if n==8 else 2; return v*4*170+v*(rt*12/100*1.50)+v*toll
tolls={"UPMUNC":40,"CIAC":15,"NCSC":30,"BUCKMUN":50,"CHOMUN":70,"VICS":25}
ws=wb.create_sheet("Transport Options")
ws.append(["TRANSPORT OPTIONS – US drive confs only (Communauto), total CAD","","","","",""])
ws.append(["A=Communauto OPEN (free plan). B=Rental van(s). C=Communauto VALUE + Long Distance (used in budget; needs $5/mo plan + bond).","","","","",""])
ws.append(["","","","","",""])
for scn in (8,12):
    ws.append([f"— {scn} DELEGATES ({cars(scn)} Commauto cars / {1 if scn==8 else 2} van) —","","","","",""])
    ws.append(["Conference","RT km","A: Open","B: Van","C: Value+LD","Cheapest"])
    for k in ["UPMUNC","CIAC","NCSC","BUCKMUN","CHOMUN","VICS"]:
        c=CONF[k];rt=c['km']*2
        Aa=open_car(rt,c['days'])*cars(scn);Bb=van(rt,tolls[k],scn);Cc=vld_car(rt,c['days'])*cars(scn)
        best=min([("Open",Aa),("Van",Bb),("Value-LD",Cc)],key=lambda t:t[1])[0]
        ws.append([c['full'],str(rt),m(Aa),m(Bb),m(Cc),best])
    ws.append(["","","","","",""])
ws.append(["READ-OUT","","","","",""])
ws.append(["• Open never wins and can't clear its own $500 credit limit on long trips. Value+LD used in budget.","","","","",""])
ws.append(["• At 8 del a single van is cheapest; at 12 del Value+LD (3 small cars on Long Distance) edges 2 vans.","","","","",""])
ws.append(["• Montreal confs (McMUN/ConMUN) use Megabus $110 CAD RT/delegate – not shown here.","","","","",""])
ws.merge_cells("A1:F1");ws["A1"].font=Font(bold=True,size=12,color="FFFFFF");ws["A1"].fill=NAVY
ws.merge_cells("A2:F2");ws["A2"].font=Font(italic=True,size=9)
for rr in range(1,ws.max_row+1):
    a=str(ws.cell(row=rr,column=1).value or "")
    if a.startswith("—"): 
        for cc in range(1,7): ws.cell(row=rr,column=cc).fill=LBLUE;ws.cell(row=rr,column=cc).font=bold
    if a=="Conference":
        for cc in range(1,7): x=ws.cell(row=rr,column=cc);x.fill=BLUE;x.font=white;x.border=border
    if a=="READ-OUT": ws.cell(row=rr,column=1).font=Font(bold=True,color="C00000")
autos(ws,[24,8,12,12,14,11])


# ---------- PAYMENT TIMELINE ----------
ws=wb.create_sheet("Payment Timeline")
ws.append(["PAYMENT TIMELINE – Selected Slate (6 confs)  ·  today: Jun 10, 2026","","","",""])
ws.append(["Chronological money + action schedule. Amounts = budgeted (regular-window) fees. Register in EARLY/PRIORITY windows to save ~$10-15/del where noted.","","","",""])
ws.append(["","","","",""])
ws.append(["When","Conference","Action / Milestone","Amount due","Notes"])
T=[
("PHASE 1 — REGISTER EARLY (lock rates, pay delegation deposits)","","","",""),
("now → Aug 23, 2026","NCSC","Register (Regular window) + delegation deposit","$90 USD","Priority closed Apr 26; deposit non-refundable"),
("now → Jul 31, 2026","CIAC","Register (Early) + delegation deposit","$75 USD","Early locks $80/del vs $90; delegates 11+ free"),
("Jun 1 → Sep 6, 2026","ChoMUN","Register (Priority) + delegation deposit","$50 USD","First-time-school discount; locks $95/del priority"),
("summer → Sep 2026","McMUN","Register when 2027 portal opens + deposit","$80 CAD","Watch mcmun.org; priority wave cheapest"),
("~Sep 2026","ConMUN","Register (Early) + delegation deposit","$100 CAD","2027 portal TBD; early ~$110/del"),
("PHASE 2 — SET UP TRANSPORT (before first trip, Oct 2026)","","","",""),
("by mid-Oct 2026","Communauto","Open 3 Value accounts ($5/mo) + post bonds","$1,500 CAD","Bonds REFUNDABLE; lifts credit limit to $1,000/acct"),
("PHASE 3 — FALL CONFERENCES","","","",""),
("by Oct 7, 2026","NCSC","Final delegate payment due","$880 USD","8 x $110; hard payment deadline"),
("by Oct 9, 2026","CIAC","Late reg closes / balance due","$900 USD","10 x $90 (12 del, 2 free)"),
("Oct 22-25, 2026","CIAC","CONFERENCE — Communauto trip + hotel","~$1,463 CAD","+ hotel $1,341 USD to Cayuga Blu"),
("Nov 5-8, 2026","NCSC","CONFERENCE — Communauto trip + hotel","~$1,770 CAD","+ hotel $2,196 USD to Washington Hilton"),
("PHASE 4 — WINTER / SPRING CONFERENCES","","","",""),
("by ~Dec 25, 2026","McMUN","Hotel block cutoff (Le Centre Sheraton)","$3,510 CAD","5 rms x 3 nts x $234; reconfirm 2027 cutoff date"),
("by ~late Dec 2026","McMUN","Book Megabus (~1 mo out) + final delegate pay","$2,200 + $2,500 CAD","Bus 20x$110; del fees 20x$125 (est)"),
("Jan 10, 2027","ChoMUN","Regular registration closes","—","Late window after = higher per-del fee"),
("Jan 19, 2027","VICS","Delegate fees refundable until this date","—","After: owed in full even if you withdraw"),
("Jan 28-31, 2027","McMUN","CONFERENCE — Megabus + hotel","(paid above)","Sheraton, Montreal"),
("by ~Feb 2027","ConMUN","Book Megabus + final delegate payment","$2,200 + $2,500 CAD","Hotel $3,435 CAD to DoubleTree"),
("Mar 1, 2027","VICS","Late registration closes","—","VICS 31 dates/windows TBD — verify"),
("Mar 5, 2027","ChoMUN","Payment deadline","$880 USD","8 x $110; +5% if paying by credit card"),
("Mar 11-14, 2027","ConMUN","CONFERENCE — Megabus + hotel","(paid above)","DoubleTree, Montreal (2027 dates TBD)"),
("Mar 25-28, 2027","ChoMUN","CONFERENCE — Communauto + hotel","~$2,315 CAD","+ hotel $1,206 USD to Palmer House"),
("Mar 25-28, 2027","VICS","CONFERENCE — Communauto + hotel + balance","~$3,270 CAD","+ del fees $1,260 USD + hotel $1,701 USD"),
("AFTER SEASON","Communauto","Reclaim 3 x $500 bonds","+$1,500 CAD","Refundable after 1 yr (3 mo notice)"),
]
for r in T: ws.append(r)
ws.merge_cells("A1:E1");ws["A1"].font=Font(bold=True,size=13,color="FFFFFF");ws["A1"].fill=NAVY
ws.merge_cells("A2:E2");ws["A2"].font=Font(italic=True,size=9)
for cc in range(1,6): x=ws.cell(row=4,column=cc);x.fill=BLUE;x.font=white;x.border=border
for rr in range(5,ws.max_row+1):
    a=str(ws.cell(row=rr,column=1).value or "")
    b=str(ws.cell(row=rr,column=3).value or "")
    if a.startswith("PHASE"):
        ws.merge_cells(start_row=rr,start_column=1,end_row=rr,end_column=5)
        ws.cell(row=rr,column=1).fill=LBLUE;ws.cell(row=rr,column=1).font=bold
    elif "CONFERENCE" in b:
        for cc in range(1,6): ws.cell(row=rr,column=cc).fill=YEL
        ws.cell(row=rr,column=2).font=bold
    elif a=="AFTER SEASON":
        for cc in range(1,6): ws.cell(row=rr,column=cc).fill=GREEN
    for cc in range(1,6): ws.cell(row=rr,column=cc).border=border
    ws.cell(row=rr,column=5).alignment=Alignment(wrap_text=True)
    ws.cell(row=rr,column=4).font=Font(bold=True)
autos(ws,[20,14,40,18,40])

# ---------- RAIL SCREEN ----------
ws=wb.create_sheet("Rail Screen")
ws.append(["RAIL SCREEN – can we take the train instead of driving/flying?  (excl. McMUN/ConMUN, which use Megabus)","","","","",""])
ws.append(["Verdict: NON-STARTER for all US confs. Kingston has NO Amtrak — every trip = VIA Rail to a gateway + Amtrak cross-border, which forces 1-2 hotel overnights before you reach the US. Sourced June 2026.","","","","",""])
ws.append(["","","","","",""])
ws.append(["THE STRUCTURAL KILLER","","","","",""])
ws.append(["• Only cross-border trains: Maple Leaf (Toronto>NYC) & Adirondack (Montreal>NYC) — both ~12-13h incl. ~2h border stop.","","","","",""])
ws.append(["• Both depart their Canadian gateway in the MORNING and arrive NYC at NIGHT — too late for any same-day southbound leg.","","","","",""])
ws.append(["• Result: a Toronto/Montreal overnight before the US, then a 2nd NYC overnight before going south. No US conf reachable by train in under 2 days.","","","","",""])
ws.append(["","","","","",""])
ws.append(["Conference","City","Current plan","Best train (moving time)","Rail fare ~1-way","Verdict"])
RAIL=[
("CIAC","Ithaca, NY","Drive 3.5h","No rail to city — nearest Amtrak is Syracuse + 60 mi by car","n/a","ABSURD — Ithaca has zero Amtrak service"),
("UPMUNC","Philadelphia, PA","Drive 6.5h","~16h, 2 transfers","US$185-210","Non-starter (1-2 overnights each way)"),
("NCSC","Washington, DC","Drive 8h","~18h, 2 transfers","US$200-230","Non-starter (1-2 overnights each way)"),
("BUCKMUN","Columbus, OH","Drive 9h","No rail to city at all","n/a","IMPOSSIBLE — Columbus has zero Amtrak (largest US metro w/ none)"),
("CHOMUN","Chicago, IL","Drive 10h","~34h, 3 transfers","US$300+","Non-starter (2 hotels + on-train overnight)"),
("VICS","Charlottesville, VA","Drive 11-13h","~22-26h, 2-3 transfers","US$215-250","Non-starter (closest call; drive is also brutal)"),
("UNCMUNC","Durham/Raleigh, NC","Fly $425 RT","~26h, 3 transfers","~US$240 (~$480 RT)","Non-starter — RT fare ~matches flight, +4 hotel nights & ~5x the time"),
]
for r in RAIL: ws.append(r)
ws.append(["","","","","",""])
ws.append(["REFERENCE LEGS (verified 2026)","","","","",""])
ws.append(["VIA Rail Kingston>Toronto","~2h","~C$44-65 econ","Frequent daily corridor service","",""])
ws.append(["VIA Rail Kingston>Montreal","~2.5h","~C$30-70 econ","","",""])
ws.append(["Amtrak Maple Leaf Toronto>NYC","~12-13h","~US$90-150","Dep Toronto 08:20, arr NY Penn ~21:15; ~2h border @ Niagara. Running 2026.","",""])
ws.append(["Amtrak Adirondack Montreal>NYC","~11-12h","~US$70-130","Resumed after 2023-24 suspension; running 2026.","",""])
ws.append(["Amtrak NE Regional NYC>DC / >Philadelphia","3.5h / 1.5h","from US$20 / US$25","Frequent same-day once on the NEC","",""])
ws.append(["Amtrak Lake Shore Limited NYC>Chicago","~19-20h","from US$172","Dep NY 15:40 — hours before Maple Leaf arrives, so no same-day connect","",""])
ws.append(["Amtrak Carolinian NYC/DC>Durham NC","~11-13h / ~7h","from US$86 / US$59","One-seat ride; the NC end is good, the Kingston>NEC end is the problem","",""])
ws.append(["","","","","",""])
ws.append(["TWO NEAR-MISSES (still rejected)","","","","",""])
ws.append(["• UNCMUNC: NC end is great (Carolinian one-seat to Durham), but RT rail ~= the $425 flight and adds ~4 hotel nights + days of transit. Fly stays correct.","","","","",""])
ws.append(["• VICS: only one where rail's downside shrinks — because a 13h drive is itself miserable. Still 2 overnights each way. Not viable for a student team.","","","","",""])
ws.append(["","","","","",""])
ws.append(["NET: nothing changes in the budget. Communauto wins the close US trips, flying wins UNCMUNC, Megabus wins Montreal. Rail beats none of them.","","","","",""])
ws.merge_cells("A1:F1");ws["A1"].font=Font(bold=True,size=12,color="FFFFFF");ws["A1"].fill=NAVY
ws.merge_cells("A2:F2");ws["A2"].font=Font(italic=True,size=9);ws.row_dimensions[2].height=28;ws["A2"].alignment=Alignment(wrap_text=True,vertical="center")
for rr in range(3,ws.max_row+1):
    a=str(ws.cell(row=rr,column=1).value or "")
    if a in ("THE STRUCTURAL KILLER","REFERENCE LEGS (verified 2026)","TWO NEAR-MISSES (still rejected)"):
        for cc in range(1,7): ws.cell(row=rr,column=cc).fill=LBLUE;ws.cell(row=rr,column=cc).font=bold
    elif a=="Conference":
        for cc in range(1,7): x=ws.cell(row=rr,column=cc);x.fill=BLUE;x.font=white;x.border=border
    elif a.startswith("NET:"):
        for cc in range(1,7): ws.cell(row=rr,column=cc).fill=GREEN
        ws.cell(row=rr,column=1).font=Font(bold=True,color="1F3864")
for i in range(len(RAIL)):
    rr=10+i
    for cc in range(1,7): ws.cell(row=rr,column=cc).border=border
    ws.cell(row=rr,column=6).alignment=Alignment(wrap_text=True);ws.cell(row=rr,column=4).alignment=Alignment(wrap_text=True)
    ws.row_dimensions[rr].height=28
    v=str(ws.cell(row=rr,column=6).value or "")
    if v.startswith("ABSURD") or v.startswith("IMPOSSIBLE"):
        ws.cell(row=rr,column=6).font=Font(bold=True,color="C00000")
autos(ws,[14,18,14,40,15,40])

# ---------- DELEGATE FEES ----------
FEES=[100,200,250,300,350,400]
def sm(x):  # signed money
    x=int(round(x)); s="-" if x<0 else ""; return f"{s}${abs(x):,}"
ws=wb.create_sheet("Delegate Fees")
ws.append(["DELEGATE FEES – what charging each delegate $X to attend covers  ·  Selected Slate (6 confs, 80 delegate-trips)","","","","","","","","",""])
ws.append(["NET = fee x delegates − club's all-in cost for that conference (reg + hotel + travel +10%). NEGATIVE (red) = club still subsidizes; POSITIVE (green) = surplus. CAD.","","","","","","","","","",""])
ws.append(["Break-even col = the per-delegate fee that exactly covers THAT conference. For reference, Jack has paid ~$300-450/conf as a delegate in prior years.","","","","","","","","","",""])
ws.append(["","","","","","","","","",""])
ws.append(["Conference","Del","Club cost (CAD)","Break-even /del","Net @ $100","Net @ $200","Net @ $250","Net @ $300","Net @ $350","Net @ $400"])
TN=0; TC=0
netrows=[]
for k,n in slate:
    p=parts(k,n); cost=p['tot']; TN+=n; TC+=cost
    cpd=cost/n
    nets=[f*n-cost for f in FEES]
    netrows.append((CONF[k]['full'],n,cost,cpd,nets))
    ws.append([CONF[k]['full'],n,m(cost),m(cpd)]+[sm(v) for v in nets])
TC+=SUBS  # subscriptions are a program cost, covered only by delegate revenue
Tnets=[f*TN-TC for f in FEES]
ws.append(["+ Communauto subscriptions","",m(SUBS),"","","","","","",""])
ws.append(["TOTAL (slate)",TN,m(TC),m(TC/TN)]+[sm(v) for v in Tnets])
ws.append(["","","","","","","","","",""])
ws.append(["REVENUE vs COST AT A FLAT FEE (whole slate)","","","","","","","","",""])
ws.append(["Flat fee / delegate","Total revenue (80 del)","Slate cost","Surplus / (shortfall)","% of cost covered","","","","",""])
for f in FEES:
    rev=f*TN; net=rev-TC; pct=rev/TC*100
    ws.append([f"${f}",m(rev),m(TC),sm(net),f"{pct:.0f}%","","","","",""])
beven=TC/TN
ws.append(["","","","","","","","","",""])
ws.append([f"BOTTOM LINE: a flat fee fully covers the slate only at ~${beven:,.0f}/delegate. At $300 the club still raises {m(TC-300*TN)}; at $400, {m(TC-400*TN)}. The Montreal/cheap-headcount confs throw off surplus that offsets the expensive flying/long-drive ones.","","","","","","","","",""])
ws.append(["NOTE: fee levels are GROSS to the club — they do NOT change any cost above; they show how much delegate revenue offsets the program. Tiering (charge more for pricier trips) would close the gap at a lower average fee; ask if you want that modelled.","","","","","","","","",""])
# style
ws.merge_cells("A1:J1");ws["A1"].font=Font(bold=True,size=12,color="FFFFFF");ws["A1"].fill=NAVY;ws.row_dimensions[1].height=22
ws.merge_cells("A2:J2");ws.merge_cells("A3:J3");ws["A2"].font=Font(italic=True,size=9);ws["A3"].font=Font(italic=True,size=9)
ws["A2"].alignment=Alignment(wrap_text=True);ws.row_dimensions[2].height=26
hdrrow=5
for cc in range(1,11): x=ws.cell(row=hdrrow,column=cc);x.fill=BLUE;x.font=white;x.border=border;x.alignment=Alignment(wrap_text=True,vertical="center")
ws.row_dimensions[hdrrow].height=26
nsl=len(slate)
for i in range(nsl):
    rr=hdrrow+1+i
    for cc in range(1,11):
        cell=ws.cell(row=rr,column=cc);cell.border=border
        if cc>=5:
            val=netrows[i][4][cc-5]
            cell.fill=GREEN if val>=0 else ORANGE
            if val<0: cell.font=Font(color="C00000")
subsrow=hdrrow+1+nsl; totrow=subsrow+1
for cc in range(1,11): ws.cell(row=subsrow,column=cc).fill=GREY;ws.cell(row=subsrow,column=cc).font=Font(italic=True,size=9)
for cc in range(1,11):
    cell=ws.cell(row=totrow,column=cc);cell.fill=NAVY;cell.font=white;cell.border=border
for rr in range(hdrrow,ws.max_row+1):
    a=str(ws.cell(row=rr,column=1).value or "")
    if a=="REVENUE vs COST AT A FLAT FEE (whole slate)":
        for cc in range(1,11): ws.cell(row=rr,column=cc).fill=LBLUE;ws.cell(row=rr,column=cc).font=bold
    elif a=="Flat fee / delegate":
        for cc in range(1,6): x=ws.cell(row=rr,column=cc);x.fill=BLUE;x.font=white;x.border=border
    elif a.startswith("$") and len(a)<6:
        for cc in range(1,6): ws.cell(row=rr,column=cc).border=border
        ws.cell(row=rr,column=4).font=Font(bold=True)
    elif a.startswith("BOTTOM LINE"):
        ws.merge_cells(start_row=rr,start_column=1,end_row=rr,end_column=10)
        c=ws.cell(row=rr,column=1);c.fill=YEL;c.font=Font(bold=True,color="1F3864");c.alignment=Alignment(wrap_text=True,vertical="center");ws.row_dimensions[rr].height=42
    elif a.startswith("NOTE:"):
        ws.merge_cells(start_row=rr,start_column=1,end_row=rr,end_column=10)
        c=ws.cell(row=rr,column=1);c.font=Font(italic=True,size=9);c.alignment=Alignment(wrap_text=True,vertical="center");ws.row_dimensions[rr].height=30
autos(ws,[24,6,15,15,12,12,12,12,12,12])

# ---------- OPERATING BUDGET (non-conference, full year) ----------
OPS=[
 ("SOCIALS & FORMAL  (trimmed 40%)",[
   ("Welcome / clubs-fair recruitment social","~80 ppl · venue + light food",240),
   ("Fall bonding mixer","team social night",150),
   ("Winter mixer","team social night",150),
   ("Year-end formal / awards banquet","~80 guests · leaner venue/catering (no ticket charge)",2640),
   ("Exec appreciation / transition dinner","~12 execs",180),
 ]),
 ("MERCH & MARKETING",[
   ("Branded banner + tablecloth","one-time, reusable",300),
   ("Recruitment promo","posters, business cards, stickers, clubs fair",200),
   ("Website domain + hosting","annual",100),
   ("Team apparel","bulk order, sold AT COST to members (cash-neutral)",0),
 ]),
 ("ADMIN & AWARDS",[
   ("AMS ratification / club registration","annual",50),
   ("Payment-processing fees","Square ~2.9% on delegate-fee collection",150),
   ("Banquet awards / gavels","superlatives at the year-end formal",200),
   ("Misc / office supplies","",100),
 ]),
]
ws=wb.create_sheet("Operating Budget")
ws.append(["OPERATING BUDGET 2026-27 – non-conference, full year  ·  club size ~60-100","",""])
ws.append(["The year's running costs OUTSIDE conference travel. Formal is fully club-funded (no ticket charge). CAD. The conference program lives on the other tabs.","",""])
ws.append(["","",""])
ws.append(["Category / Line item","Basis","Cost (CAD)"])
opscats={c for c,_ in OPS}
ops_net=0
for cat,items in OPS:
    ws.append([cat,"",""])
    for it,basis,amt in items:
        ws.append(["   "+it,basis,(sm(amt) if amt<0 else m(amt))])
        ops_net+=amt
conting_ops=round(ops_net*0.10)
ops_total=ops_net+conting_ops
ws.append(["Subtotal (net)","",m(ops_net)])
ws.append(["Contingency 10% (on net operating)","",m(conting_ops)])
ws.append(["OPERATING TOTAL","",m(ops_total)])
ws.append(["","",""])
ws.append(["Note: team apparel is bulk-bought and resold to members at cost, so it nets ~$0 cash. The year-end formal is the single biggest non-conference line and is fully club-funded (no ticket charge). Even so, operating spend stays small next to the travel program.","",""])
ws.merge_cells("A1:C1");ws["A1"].font=Font(bold=True,size=12,color="FFFFFF");ws["A1"].fill=NAVY;ws.row_dimensions[1].height=22
ws.merge_cells("A2:C2");ws["A2"].font=Font(italic=True,size=9);ws["A2"].alignment=Alignment(wrap_text=True);ws.row_dimensions[2].height=26
for cc in range(1,4): x=ws.cell(row=4,column=cc);x.fill=BLUE;x.font=white;x.border=border
for rr in range(5,ws.max_row+1):
    a=str(ws.cell(row=rr,column=1).value or "")
    if a in opscats:
        for cc in range(1,4): ws.cell(row=rr,column=cc).fill=LBLUE;ws.cell(row=rr,column=cc).font=bold
    elif a=="OPERATING TOTAL":
        for cc in range(1,4): c=ws.cell(row=rr,column=cc);c.fill=NAVY;c.font=white;c.border=border
    elif a.startswith("Subtotal") or a.startswith("Contingency"):
        for cc in range(1,4): ws.cell(row=rr,column=cc).font=Font(italic=True,size=9)
        ws.cell(row=rr,column=3).font=bold
    elif a.startswith("Note:"):
        ws.merge_cells(start_row=rr,start_column=1,end_row=rr,end_column=3)
        c=ws.cell(row=rr,column=1);c.font=Font(italic=True,size=9);c.alignment=Alignment(wrap_text=True,vertical="center");ws.row_dimensions[rr].height=42
    elif a.strip().startswith("less:"):
        ws.cell(row=rr,column=3).font=Font(color="C00000")
autos(ws,[46,42,14])

# ---------- FUNDRAISING & NET POSITION ----------
slate_total=sum(parts(k,n)['tot'] for k,n in slate)+SUBS
slate_trips=sum(parts(k,n)['n'] for k,n in slate)
total_cost=slate_total+ops_total
AMS_GRANT=1500          # EDITABLE placeholder — replace with confirmed allotment
MEMBER_FEE=10; MEMBERS=80; member_rev=MEMBER_FEE*MEMBERS   # $10 club joining fee x 80
BAR_NIGHTS=3; bar_low,bar_mid,bar_high=300,550,800
bar_season=bar_mid*BAR_NIGHTS
ws=wb.create_sheet("Fundraising & Net")
ws.append(["FUNDRAISING & NET POSITION 2026-27  ·  all-in club cash picture","","","",""])
ws.append(["Ties it together: TOTAL CLUB COST (conference program + operating) vs FUNDING (AMS grant + delegate fees + bar nights). Aim is to subsidize, not break even — the gap is what the club funds from treasury. CAD.","","","",""])
ws.append(["","","","",""])
ws.append(["A · BAR / PERCENTAGE NIGHTS  (the modelled fundraiser)","","","",""])
ws.append(["Scenario","Net / night","# nights","Season total","How it gets there"])
ws.append(["Conservative",m(bar_low),str(BAR_NIGHTS),m(bar_low*BAR_NIGHTS),"percentage night, ~15% of a light turnout"])
ws.append(["Expected (used below)",m(bar_mid),str(BAR_NIGHTS),m(bar_mid*BAR_NIGHTS),"mix of % night + small cover; ~60-80 out"])
ws.append(["Optimistic",m(bar_high),str(BAR_NIGHTS),m(bar_high*BAR_NIGHTS),"ticketed social, venue deal, strong turnout"])
ws.append(["","","","",""])
ws.append(["B · ALL-IN NET POSITION  (at each delegate fee level)","","","",""])
ws.append(["Conference program (selected slate)","",m(slate_total),"","fixed — Selected Slate tab"])
ws.append(["Operating budget (socials/training/merch/admin)","",m(ops_total),"","fixed — Operating Budget tab"])
ws.append(["TOTAL CLUB COST","",m(total_cost),"","what the year costs, all-in"])
ws.append(["AMS / society grant   [EDIT THIS CELL]","",m(AMS_GRANT),"","illustrative — replace with your confirmed allotment"])
ws.append([f"Club joining fee  (${MEMBER_FEE} x {MEMBERS} members)","",m(member_rev),"","one-time membership dues, separate from delegate fees"])
ws.append([f"Bar/percentage nights (expected, {BAR_NIGHTS} nights)","",m(bar_season),"","from section A"])
ws.append(["","","","",""])
base_funding=AMS_GRANT+member_rev+bar_season
ws.append(["Delegate fee","Fee revenue (80 trips)","+ grant/dues/bar","Funding total","Club funds (gap)"])
for f in FEES:
    rev=f*slate_trips; funding=rev+base_funding; gap=total_cost-funding
    ws.append([f"${f}/delegate",m(rev),m(base_funding),m(funding),m(gap)])
ws.append(["","","","",""])
ws.append([f"BOTTOM LINE: travel is the cost driver — operating is only {m(ops_total)} ({ops_total/total_cost*100:.0f}% of the {m(total_cost)} all-in). AMS grant + ${MEMBER_FEE} joining fee + bar nights chip ~{m(base_funding)} off whatever you set, before any delegate fees. Every $50 on the delegate fee moves the gap by {m(50*slate_trips)} (80 trips). Set the fee for affordability; the remaining gap is the planned subsidy, not a shortfall to fix.","","","",""])
ws.merge_cells("A1:E1");ws["A1"].font=Font(bold=True,size=13,color="FFFFFF");ws["A1"].fill=NAVY;ws.row_dimensions[1].height=22
ws.merge_cells("A2:E2");ws["A2"].font=Font(italic=True,size=9);ws["A2"].alignment=Alignment(wrap_text=True);ws.row_dimensions[2].height=28
for rr in range(3,ws.max_row+1):
    a=str(ws.cell(row=rr,column=1).value or "")
    if a.startswith("A ·") or a.startswith("B ·"):
        ws.merge_cells(start_row=rr,start_column=1,end_row=rr,end_column=5)
        ws.cell(row=rr,column=1).fill=LBLUE;ws.cell(row=rr,column=1).font=bold
    elif a in ("Scenario","Delegate fee"):
        for cc in range(1,6): x=ws.cell(row=rr,column=cc);x.fill=BLUE;x.font=white;x.border=border
    elif a=="TOTAL CLUB COST":
        for cc in range(1,6): c=ws.cell(row=rr,column=cc);c.fill=NAVY;c.font=white;c.border=border
    elif a.startswith("AMS"):
        for cc in range(1,6): ws.cell(row=rr,column=cc).fill=YEL
        ws.cell(row=rr,column=3).font=bold
    elif a.endswith("/delegate"):
        for cc in range(1,6): ws.cell(row=rr,column=cc).border=border
        ws.cell(row=rr,column=5).font=bold;ws.cell(row=rr,column=5).fill=GREEN
    elif a.startswith("Conference program") or a.startswith("Operating budget") or a.startswith("Bar/percentage") or a.startswith("Club joining"):
        ws.cell(row=rr,column=3).font=bold
    elif a.startswith("BOTTOM LINE"):
        ws.merge_cells(start_row=rr,start_column=1,end_row=rr,end_column=5)
        c=ws.cell(row=rr,column=1);c.fill=YEL;c.font=Font(bold=True,color="1F3864");c.alignment=Alignment(wrap_text=True,vertical="center");ws.row_dimensions[rr].height=56
autos(ws,[32,18,18,16,40])

# ---------- REGISTRATION WINDOWS ----------
ws=wb.create_sheet("Registration Windows")
ws.append(["REGISTRATION WINDOWS & DEADLINES – Selected Slate (6 confs)  ·  sourced June 2026","","","",""])
ws.append(["Budget uses each conference's REGULAR-window fee (conservative). Earlier windows save where shown. 2027 portals partly unposted — verify any row marked TBD/est before relying on a date.","","","",""])
ws.append(["","","","",""])
ws.append(["Conference","Window / milestone","Closes","Per-del fee","Status / note"])
REGWIN=[
 ("NCSC – Georgetown",[
   ("Priority","Apr 26, 2026 (CLOSED)","lower","missed — priority wave already shut"),
   ("Regular  (budgeted)","Aug 23, 2026","$110 USD","current open window = the budget rate"),
   ("Final delegate payment","Oct 7, 2026","—","hard balance deadline, all 8 delegates"),
 ]),
 ("CIAC – Cornell",[
   ("Early","Jul 31, 2026","$80 USD","saves $10/del vs budget; delegates 11+ free"),
   ("Regular  (budgeted)","after Jul 31, 2026","$90 USD","budget rate (conservative)"),
   ("Late / balance due","Oct 9, 2026","$90 USD","full balance, billable delegates only"),
 ]),
 ("ChoMUN – UChicago",[
   ("Priority","Sep 6, 2026","$95 USD","first-time-school discount; saves $15/del"),
   ("Regular  (budgeted)","Jan 10, 2027","$110 USD","budget rate; +5% if paying by credit card"),
   ("Late","after Jan 10, 2027","higher","avoid — per-del fee steps up"),
   ("Payment deadline","Mar 5, 2027","—","full balance due"),
 ]),
 ("McMUN – McGill   (2027 TBD)",[
   ("Portal opens","~summer 2026","—","watch mcmun.org; 2027 fee table unposted"),
   ("Priority wave","~Sep-Oct 2026 (est)","cheapest","register here when it opens"),
   ("Regular  (budgeted)","TBD","$125 CAD est","estimate — confirm finance@mcmun.org"),
   ("Hotel block cutoff","~Dec 25, 2026","—","Le Centre Sheraton; reconfirm 2027 date"),
   ("Final delegate payment","~late Dec 2026","—","paid with Megabus booking"),
 ]),
 ("ConMUN – Concordia   (2027 TBD)",[
   ("Early","~Sep 2026 (est)","~$110 CAD","2027 portal not yet open"),
   ("Regular  (budgeted)","TBD","$125 CAD","2026 figures used as placeholder"),
   ("Final payment","~Feb 2027","—","paid with Megabus booking"),
 ]),
 ("VICS – UVA   (VICS 31 windows TBD)",[
   ("Early / regular","TBD","$105 USD","windows unposted; $105 used as budget rate"),
   ("Refund cutoff","Jan 19, 2027","—","fees owed in full even if you withdraw after"),
   ("Late registration closes","Mar 1, 2027","—","verify — VICS 31 dates not yet published"),
 ]),
]
confhdrs=set()
for conf,wins in REGWIN:
    ws.append([conf,"","","",""]); confhdrs.add(conf)
    for w,closes,fee,note in wins:
        ws.append(["",w,closes,fee,note])
ws.append(["","","","",""])
ws.append(["EARLY-REGISTRATION SAVINGS (not yet banked in budget)","","","",""])
ws.append(["CIAC early","by Jul 31, 2026","$10/del x 10 billable","= $100 USD","budget assumes the $90 regular rate"])
ws.append(["ChoMUN priority","by Sep 6, 2026","$15/del x 8","= $120 USD","budget assumes the $110 regular rate"])
ws.append(["McMUN / ConMUN priority","when 2027 portals open","unquantified","TBD","priority waves cheapest; amount not yet posted"])
ws.append(["NET: registering in the early/priority windows saves ~$220 USD (~$305 CAD) on the two US confs alone, before McMUN/ConMUN. The budget deliberately omits this so it lands as upside, not a number you have to hit.","","","",""])
ws.merge_cells("A1:E1");ws["A1"].font=Font(bold=True,size=12,color="FFFFFF");ws["A1"].fill=NAVY;ws.row_dimensions[1].height=22
ws.merge_cells("A2:E2");ws["A2"].font=Font(italic=True,size=9);ws["A2"].alignment=Alignment(wrap_text=True);ws.row_dimensions[2].height=28
for cc in range(1,6): x=ws.cell(row=4,column=cc);x.fill=BLUE;x.font=white;x.border=border
for rr in range(5,ws.max_row+1):
    a=str(ws.cell(row=rr,column=1).value or "")
    b=str(ws.cell(row=rr,column=2).value or "")
    if a in confhdrs:
        ws.merge_cells(start_row=rr,start_column=1,end_row=rr,end_column=5)
        ws.cell(row=rr,column=1).fill=LBLUE;ws.cell(row=rr,column=1).font=bold
    elif a=="EARLY-REGISTRATION SAVINGS (not yet banked in budget)":
        for cc in range(1,6): ws.cell(row=rr,column=cc).fill=GREEN;ws.cell(row=rr,column=cc).font=bold
    elif a.startswith("NET:"):
        ws.merge_cells(start_row=rr,start_column=1,end_row=rr,end_column=5)
        c=ws.cell(row=rr,column=1);c.fill=YEL;c.font=Font(bold=True,color="1F3864");c.alignment=Alignment(wrap_text=True,vertical="center");ws.row_dimensions[rr].height=42
    elif b:
        for cc in range(1,6): ws.cell(row=rr,column=cc).border=border
        ws.cell(row=rr,column=5).alignment=Alignment(wrap_text=True)
        if "(budgeted)" in b:
            for cc in range(2,6): ws.cell(row=rr,column=cc).fill=YEL
        ws.cell(row=rr,column=3).font=bold
autos(ws,[26,22,20,14,46])

path=os.path.expanduser("~/Downloads/Queens_MUN_Budget_2026-27.xlsx")
wb.save(path)
print("SAVED",path,os.path.getsize(path)); print("TABS:",wb.sheetnames)
print(f"8-scn program total: C${g8+SUBS:,.0f} (US${(g8+SUBS)/USD_CAD:,.0f})")
print(f"12-scn program total: C${g12+SUBS:,.0f} (US${(g12+SUBS)/USD_CAD:,.0f})")
st=sum(parts(k,n)['tot'] for k,n in slate)+SUBS
print(f"Selected slate: C${st:,.0f} (US${st/USD_CAD:,.0f})")
print("McMUN@20:",m(parts('MCMUN',8)['tot']),"ConMUN@20:",m(parts('CONMUN',8)['tot']))
