import csv, os, re, json, time, hashlib, urllib.parse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from PIL import Image, ImageOps
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"output"; COVERS=ROOT/"covers"; CONSOLES=ROOT/"console_images"
OUT.mkdir(exist_ok=True); COVERS.mkdir(exist_ok=True); CONSOLES.mkdir(exist_ok=True)

DIR_MAP={
"Atari 2600":["Atari - 2600"],
"Vectrex":["GCE - Vectrex"],
"Nintendo Entertainment System":["Nintendo - Nintendo Entertainment System"],
"NES":["Nintendo - Nintendo Entertainment System"],
"Super Nintendo Entertainment System":["Nintendo - Super Nintendo Entertainment System"],
"SNES":["Nintendo - Super Nintendo Entertainment System"],
"Sega Genesis":["Sega - Mega Drive - Genesis"],
"Genesis":["Sega - Mega Drive - Genesis"],
"Sega 32X":["Sega - 32X"],
"Game Boy":["Nintendo - Game Boy"],
"Game Boy Color":["Nintendo - Game Boy Color"],
"Game Gear":["Sega - Game Gear"],
"TurboGrafx-16":["NEC - PC Engine - TurboGrafx 16"],
"TurboGrafx-CD":["NEC - PC Engine CD - TurboGrafx-CD"],
"PC Engine":["NEC - PC Engine - TurboGrafx 16"],
"Neo Geo":["SNK - Neo Geo"],
"3DO":["The 3DO Company - 3DO"],
"PlayStation":["Sony - PlayStation"],
"PlayStation 1":["Sony - PlayStation"],
"Nintendo 64":["Nintendo - Nintendo 64"],
"Sega Dreamcast":["Sega - Dreamcast"],
"Dreamcast":["Sega - Dreamcast"],
"PlayStation 2":["Sony - PlayStation 2"],
"Xbox":["Microsoft - Xbox"],
"Nintendo GameCube":["Nintendo - Nintendo GameCube"],
"GameCube":["Nintendo - Nintendo GameCube"],
"Nintendo DS":["Nintendo - Nintendo DS"],
"PlayStation Portable":["Sony - PlayStation Portable"],
"PSP":["Sony - PlayStation Portable"],
"Xbox 360":["Microsoft - Xbox 360"],
"PlayStation 3":["Sony - PlayStation 3"],
"Wii":["Nintendo - Wii"],
"Nintendo 3DS":["Nintendo - Nintendo 3DS"],
"PlayStation 4":["Sony - PlayStation 4"],
"PS4":["Sony - PlayStation 4"],
"Nintendo Switch":["Nintendo - Nintendo Switch"],
}
SKIP_PLATFORMS={"Magnavox Odyssey","PlayStation 4/5","Nintendo Switch 2","Platform Not Specified"}
ALIASES={
"Dr Robotonik":"Dr. Robotnik's Mean Bean Machine","Musha":"M.U.S.H.A.",
"MGS2":"Metal Gear Solid 2 - Sons of Liberty","MGS3":"Metal Gear Solid 3 - Snake Eater",
"DMC 1":"Devil May Cry","DMC 2":"Devil May Cry 2","DMC 3":"Devil May Cry 3 - Dante's Awakening",
"DMC 5":"Devil May Cry 5","Final Fantasy 16":"Final Fantasy XVI","Neir":"Nier","Nier Autotmata":"Nier - Automata",
"GTA 3":"Grand Theft Auto III","GTA IV":"Grand Theft Auto IV","Modern Warfare":"Call of Duty 4 - Modern Warfare",
"Modern Warfare 2":"Call of Duty - Modern Warfare 2","Modern Warfare 3":"Call of Duty - Modern Warfare 3",
"Black Ops":"Call of Duty - Black Ops","Blacks Ops II":"Call of Duty - Black Ops II","World At War":"Call of Duty - World at War",
"Megaman":"Mega Man","Megaman 2":"Mega Man 2","Megaman V":"Mega Man V","Kirby Adventure":"Kirby's Adventure",
"Kirby Dreamland 3":"Kirby's Dream Land 3","Kirby Planet Robot":"Kirby - Planet Robobot","Luigi Mansion":"Luigi's Mansion",
"Paper Mario 1000 Year Door":"Paper Mario - The Thousand-Year Door","Paper Mario Origami King":"Paper Mario - The Origami King",
"Ocarina Of Time":"Legend of Zelda, The - Ocarina of Time","Majora's Mask":"Legend of Zelda, The - Majora's Mask",
"Link 2 The Past":"Legend of Zelda, The - A Link to the Past","Minish Cap":"Legend of Zelda, The - The Minish Cap",
"Legend Of Zelda Oracle Of Ages":"Legend of Zelda, The - Oracle of Ages","Zelda Breath Of The Wild":"Legend of Zelda, The - Breath of the Wild",
"Zelda Tears Of The Kingdom":"Legend of Zelda, The - Tears of the Kingdom","Zelda Ocarina Of Time":"Legend of Zelda, The - Ocarina of Time",
"Donkey Kong Bonanza":"Donkey Kong Bananza","Sayanora Wild Hearts":"Sayonara Wild Hearts","Shocking Troopers":"Shock Troopers",
"Samurai Showdown II":"Samurai Shodown II","Samurai Showdown V":"Samurai Shodown V","Tsunoko vs Capcom":"Tatsunoko vs. Capcom - Ultimate All-Stars",
"Warios Land Shake It":"Wario Land - Shake It!","God Of War Ascension":"God of War - Ascension",
"Shadow Of Colossus":"Shadow of the Colossus","Shadow Of The Colossus":"Shadow of the Colossus",
"Final Fantasy 7":"Final Fantasy VII","Final Fantasy 8":"Final Fantasy VIII","Final Fantasy 9":"Final Fantasy IX",
"Final Fantasy XIII 2":"Final Fantasy XIII-2","Star War Knights Of The Old Republic II":"Star Wars - Knights of the Old Republic II - The Sith Lords",
"Jet Set Future Radio":"Jet Set Radio Future","Canon Spike":"Cannon Spike","Powerstone":"Power Stone","Powerstone 2":"Power Stone 2",
"PaRappa The Rappa":"PaRappa the Rapper","Katamari Damcacy":"Katamari Damacy","Mirrors Edge":"Mirror's Edge",
"Kill Zone 2":"Killzone 2","Kill Zone 3":"Killzone 3","Little Big Planet":"LittleBigPlanet","Little Big Planet 2":"LittleBigPlanet 2",
"Little Big Planet 3":"LittleBigPlanet 3","Infamous":"inFamous","Infamous 2":"inFamous 2","Infamous Second Son":"inFamous Second Son",
"Wolfenstein New Ordrr":"Wolfenstein - The New Order","DBZ Kakarot":"Dragon Ball Z - Kakarot",
"Dbz kakaraot":"Dragon Ball Z - Kakarot","Dbz xenoverse":"Dragon Ball Xenoverse","Dbz xenoverse 2":"Dragon Ball Xenoverse 2",
"Dbz Ultimate Tenkaichi":"Dragon Ball Z - Ultimate Tenkaichi","Berserk":"Berzerk","Hyperchase":"HyperChase - Auto Race"
}
BASE="https://thumbnails.libretro.com"
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0 game-cover-catalog-builder/1.0"})

def safe_title(s):
    return re.sub(r'[&*/:\`<>?\\\\|"]','_',s)

def variants(row):
    vals=[]
    for k in ("canonical_title","original_title","source_text"):
        t=(row.get(k) or "").strip().lstrip("*").strip()
        if t: vals.append(t)
    expanded=[]
    for t in vals:
        a=ALIASES.get(t,t)
        expanded += [a,t]
        expanded += [a.replace("’","'"), a.replace("&","and"), a.replace(" and "," & ")]
        expanded += [re.sub(r"\\bBros\\b","Bros.",a), re.sub(r"\\bDr\\b","Dr.",a)]
        if a.lower().startswith("the "): expanded.append(a[4:]+", The")
        if a.lower().startswith("a "): expanded.append(a[2:]+", A")
    out=[]
    for x in expanded:
        x=re.sub(r"\\s+"," ",x).strip()
        if x and x not in out: out.append(x)
    return out[:12]

SUFFIXES=[" (USA).png"," (USA, Europe).png"," (World).png"," (USA) (Rev 1).png"," (Europe).png"," (Japan).png",".png"]

def candidate_urls(row):
    exact=(row.get("cover_source_url") or "").strip()
    if exact: yield exact,"saved-exact"
    platform=row.get("platform","")
    for d in DIR_MAP.get(platform,[]):
        for t in variants(row):
            for suf in SUFFIXES:
                name=safe_title(t)+suf
                url=BASE+"/"+urllib.parse.quote(d,safe="")+"/Named_Boxarts/"+urllib.parse.quote(name,safe="")
                yield url,f"{d}/{name}"

def fetch_one(row):
    eid=row["entry_id"]; platform=row.get("platform","")
    if platform in SKIP_PLATFORMS or platform not in DIR_MAP:
        return eid,None,"unresolved-platform"
    dest=COVERS/(eid+".png")
    if dest.exists() and dest.stat().st_size>5000: return eid,str(dest),"cached"
    for url,label in candidate_urls(row):
        try:
            r=S.get(url,timeout=12)
            if r.status_code==200 and r.headers.get("content-type","").startswith("image") and len(r.content)>4000:
                dest.write_bytes(r.content)
                try:
                    im=Image.open(dest); im.verify()
                    return eid,str(dest),label
                except Exception:
                    dest.unlink(missing_ok=True)
        except Exception:
            pass
    return eid,None,"not-found"

def console_image(system):
    fn=CONSOLES/(re.sub(r"[^A-Za-z0-9]+","_",system).strip("_")+".jpg")
    if fn.exists(): return fn
    try:
        params={"action":"query","generator":"search","gsrsearch":system+" video game console","gsrlimit":4,
                "prop":"pageimages","piprop":"thumbnail|original","pithumbsize":700,"format":"json","formatversion":2}
        j=S.get("https://en.wikipedia.org/w/api.php",params=params,timeout=12).json()
        pages=(j.get("query") or {}).get("pages") or []
        p=next((p for p in pages if p.get("thumbnail") or p.get("original")),None)
        if p:
            u=(p.get("thumbnail") or p.get("original"))["source"]
            b=S.get(u,timeout=12).content
            fn.write_bytes(b); Image.open(fn).verify(); return fn
    except Exception: pass
    return None

def wrap(c,text,maxw,font="Helvetica",size=7.3,maxlines=2):
    words=text.split(); lines=[]; cur=""
    for w in words:
        test=(cur+" "+w).strip()
        if stringWidth(test,font,size)<=maxw: cur=test
        else:
            if cur: lines.append(cur)
            cur=w
            if len(lines)>=maxlines-1: break
    if cur and len(lines)<maxlines: lines.append(cur)
    if len(lines)==maxlines and words:
        while stringWidth(lines[-1]+"...",font,size)>maxw and len(lines[-1])>1: lines[-1]=lines[-1][:-1]
        lines[-1]=lines[-1].rstrip()+"..."
    return lines

def draw_cover(c,path,x,y,w,h):
    try:
        im=Image.open(path).convert("RGB")
        iw,ih=im.size; scale=min(w/iw,h/ih)
        dw,dh=iw*scale,ih*scale
        c.drawImage(ImageReader(im),x+(w-dw)/2,y+(h-dh)/2,width=dw,height=dh,preserveAspectRatio=True,mask='auto')
    except Exception: pass

def build_pdf(decade, rows, resolved):
    path=OUT/(decade.replace("–","-").replace("/","_")+".pdf")
    c=canvas.Canvas(str(path),pagesize=letter)
    W,H=letter; margin=36; header_h=54
    systems=sorted({r["platform"] for r in rows if r["platform"]}, key=lambda s:min([float(r["system_release_year"] or 9999) for r in rows if r["platform"]==s]))
    page_no=0
    for system in systems:
        sr=[r for r in rows if r["platform"]==system and resolved.get(r["entry_id"])]
        if not sr: continue
        sr.sort(key=lambda r:(r["canonical_title"] or r["original_title"]).lower())
        for page_start in range(0,len(sr),12):
            page_no+=1
            c.setFillColorRGB(.07,.07,.07); c.rect(0,H-header_h,W,header_h,fill=1,stroke=0)
            img=console_image(system)
            if img: draw_cover(c,img,margin,H-header_h+6,52,42)
            c.setFillColorRGB(1,1,1); c.setFont("Helvetica-Bold",17)
            c.drawString(margin+(62 if img else 0),H-29,system)
            year=next((r["system_release_year"] for r in sr if r["system_release_year"]), "")
            c.setFont("Helvetica",8); c.drawRightString(W-margin,H-28,str(year))
            c.setFillColorRGB(.1,.1,.1)
            avail_w=W-2*margin; col_gap=12; cols=4
            cell_w=(avail_w-col_gap*(cols-1))/cols
            cover_w=cell_w; cover_h=126; title_h=28; row_gap=12
            top=H-header_h-18
            for i,r in enumerate(sr[page_start:page_start+12]):
                rr=i//4; cc=i%4
                x=margin+cc*(cell_w+col_gap); y=top-(rr+1)*(cover_h+title_h+row_gap)+title_h+row_gap
                draw_cover(c,resolved[r["entry_id"]],x,y,cover_w,cover_h)
                title=(r["canonical_title"] or r["original_title"]).strip()
                c.setFont("Helvetica",7.3)
                ty=y-9
                for line in wrap(c,title,cell_w, size=7.3):
                    c.drawCentredString(x+cell_w/2,ty,line); ty-=8.5
            c.setFont("Helvetica",6.5); c.setFillColorRGB(.45,.45,.45)
            c.drawRightString(W-margin,14,f"{decade} • {page_no}")
            c.showPage()
    unresolved=[r for r in rows if not resolved.get(r["entry_id"])]
    if unresolved:
        unresolved.sort(key=lambda r:(float(r["system_release_year"] or 9999),r["platform"],(r["canonical_title"] or r["original_title"]).lower()))
        per=54
        for start in range(0,len(unresolved),per):
            c.setFillColorRGB(.07,.07,.07); c.rect(0,H-54,W,54,fill=1,stroke=0)
            c.setFillColorRGB(1,1,1); c.setFont("Helvetica-Bold",16); c.drawString(margin,H-31,"Unresolved / edition review")
            c.setFont("Helvetica",7.5); c.drawRightString(W-margin,H-29,"No substitute artwork used")
            c.setFillColorRGB(.1,.1,.1); c.setFont("Helvetica",7.2)
            chunk=unresolved[start:start+per]
            colw=(W-2*margin-24)/2
            for i,r in enumerate(chunk):
                col=i//27; row=i%27
                x=margin+col*(colw+24); y=H-72-row*24
                c.setFont("Helvetica-Bold",7.2); c.drawString(x,y,(r["canonical_title"] or r["original_title"])[:56])
                c.setFont("Helvetica",6.5); c.setFillColorRGB(.35,.35,.35); c.drawString(x,y-8,(r["platform"] or "Platform not specified")[:58]); c.setFillColorRGB(.1,.1,.1)
            c.showPage()
    c.save()
    return path

def main():
    rows=[]
    with open(ROOT/"master_manifest.csv",encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f)
        for r in rd:
            if not r.get("entry_id") and r.get("index")=="index": continue
            rows.append(r)
    print("entries",len(rows),flush=True)
    resolved={}; labels={}
    with ThreadPoolExecutor(max_workers=32) as ex:
        futs=[ex.submit(fetch_one,r) for r in rows]
        done=0
        for f in as_completed(futs):
            eid,p,label=f.result(); done+=1
            if p: resolved[eid]=p; labels[eid]=label
            if done%50==0: print("resolved",done,"found",len(resolved),flush=True)
    decades=["1970s-1980s","1990s","2000s","2010s-2020s"]
    summary={"entries":len(rows),"covers_found":len(resolved),"unresolved":len(rows)-len(resolved),"decades":{}}
    for d in decades:
        rr=[r for r in rows if (r.get("decade") or "").replace("–","-")==d]
        p=build_pdf(d,rr,resolved)
        summary["decades"][d]={"entries":len(rr),"resolved":sum(1 for r in rr if resolved.get(r["entry_id"])),"pdf":p.name}
    (OUT/"build_summary.json").write_text(json.dumps(summary,indent=2))
    with open(OUT/"resolved_sources.csv","w",newline="",encoding="utf-8") as f:
        w=csv.writer(f); w.writerow(["entry_id","source"])
        for eid in sorted(labels): w.writerow([eid,labels[eid]])
    print(json.dumps(summary,indent=2),flush=True)

if __name__=="__main__": main()
