import os, re, io, json, time, math, html, csv, hashlib
from pathlib import Path
from urllib.parse import urlencode, quote_plus
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageOps, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors

ROOT=Path("magazine_output")
COV=ROOT/"covers"
ROOT.mkdir(exist_ok=True); COV.mkdir(exist_ok=True)
S=requests.Session()
S.headers.update({"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/152 Safari/537.36"})

SOURCE_NUMS=[11,12,13,16,18,19,21,24,25,28,29,30,33,34,35,36,37,38,39,40,46,47,48,50,51,55,56,58,60,62,63,65,68,69,70,71,72,73,76,78,82,83,84,85,86,87,88,89,91,92,93,94,95,96,97,99,100,102,103,105,106,107,108,109,110,111,112,113,116,117,118,119,121,122,123,124,125,126,127,128,130,134,135,136,142,148,150,152,154,156,160,163,165,166,167,169,175,185]
VIBE=[
"#1","#2","1994 - 2Pac","1994 - Ice Cube","1994 - Prince","1994 - Janet Jackson",
"1995 - Mary J. Blige","1995 - 2Pac","1995 - Michael Jackson","1995 - Biggie & Faith Evans",
"1996 - Death Row","1996 - Mariah Carey","May 1996 - Bone Thugs-N-Harmony","1996 - Fugees",
"1996 - Dream Team II","1996 - Biggie & Puff Daddy","1997 - Wu-Tang Clan","1997 - The Notorious B.I.G.",
"1997 - Janet Jackson","1997 - Erykah Badu","1997 - Toni Braxton","1997 - Michael Jackson / Chris Rock",
"1998 - Rap Reigns","1999 - Biggie / 2Pac","2000 - Q-Tip","2000 - Jay-Z","2002 - Alicia Keys",
"2003 - Jay-Z","2003 - The Neptunes / Timbaland / Missy Elliott","2004 - Alicia Keys","2004 - Shyne",
"2006 - Eminem / 50 Cent","2006 - Allen Iverson","2006 - Keyshia Cole"]
XXL=[
"#0 - Preview Issue","#2 - Cover A","#2 - Cover B","#3","#6 - Busta Rhymes","#7 - Greatest Day in Hip-Hop History",
"#13","#16","#17","#22","#23","#24","#25","#29","#32","#34","#35","#43","#49","#51","#63",
"Summer Jam 2004 Special","#72","#73","#78","#85","#87","#93A","#96","#97","#98","#99C","#104","#105",
"#111","#122","#123","#126","#127","#130","#131","#132","#134","#136","#140","#141","#146","#147A",
"#148","#149","#150","#151","#154","#155","#157","#159","#160","XXL 2016"]

entries=[]
for n in SOURCE_NUMS:
    entries.append({"mag":"THE SOURCE","label":f"#{n}","query":f'The Source hip hop magazine issue {n} cover',"key":f"source_{n:03d}","num":str(n)})
for i,label in enumerate(VIBE):
    if label=="#1":
        q='VIBE magazine premiere issue 1993 cover Quincy Jones'
    elif label=="#2":
        q='VIBE magazine issue 2 1993 cover'
    else:
        q=f'VIBE magazine cover {label}'
    entries.append({"mag":"VIBE","label":label,"query":q,"key":f"vibe_{i+1:02d}","num":""})
for i,label in enumerate(XXL):
    if label.startswith("#"):
        m=re.match(r"#(\d+)([A-Z]?)",label)
        num=m.group(1); suffix=m.group(2)
        desc=label.split(" - ",1)[1] if " - " in label else ""
        q=f'XXL magazine issue {num} {suffix} cover {desc}'.strip()
    else:
        q=f'XXL magazine cover {label}'
        num=""
    entries.append({"mag":"XXL","label":label,"query":q,"key":f"xxl_{i+1:02d}","num":num})

print("COUNTS",len(SOURCE_NUMS),len(VIBE),len(XXL),"TOTAL",len(entries))
if len(entries)!=190:
    raise RuntimeError(f"manifest count {len(entries)} != 190")

def bing(query):
    url="https://www.bing.com/images/async?"+urlencode({"q":query,"async":"1","first":1,"count":35})
    r=S.get(url,timeout=45)
    r.raise_for_status()
    soup=BeautifulSoup(r.text,"html.parser")
    out=[]
    for a in soup.select("a.iusc"):
        try:
            m=json.loads(a.get("m") or "{}")
        except Exception:
            continue
        if m.get("murl"):
            out.append({"murl":m.get("murl"),"turl":m.get("turl"),"purl":m.get("purl"),"desc":m.get("desc","")})
    return out

def norm(s): return re.sub(r"\s+"," ",re.sub(r"[^a-z0-9#]+"," ",(s or "").lower())).strip()

def issue_score(e,c,rank):
    blob=norm(" ".join([c.get("purl",""),c.get("desc",""),c.get("murl","")]))
    score=max(0,20-rank)
    if e["mag"]=="THE SOURCE":
        if "source" in blob: score+=25
        if "magazine" in blob: score+=8
        n=e["num"]
        if re.search(rf"(?:issue|no|number|#)\s*0*{re.escape(n)}\b",blob): score+=80
        elif re.search(rf"\b0*{re.escape(n)}\b",blob): score+=35
    elif e["mag"]=="VIBE":
        if "vibe" in blob: score+=30
        # favor year and subject words
        yrs=re.findall(r"\b(19\d{2}|20\d{2})\b",e["label"])
        if yrs and yrs[0] in blob: score+=25
        subj=re.sub(r"^(?:may\s+)?\d{4}\s*-\s*","",e["label"],flags=re.I)
        toks=[t for t in norm(subj).split() if len(t)>2 and t not in {"the","and","cover"}]
        score += min(30, sum(7 for t in toks if t in blob))
    else:
        if "xxl" in blob: score+=30
        n=e.get("num")
        if n:
            if re.search(rf"(?:issue|no|number|#)\s*0*{re.escape(n)}\b",blob): score+=80
            elif re.search(rf"\b0*{re.escape(n)}\b",blob): score+=35
        desc=e["label"].split(" - ",1)[1] if " - " in e["label"] else e["label"]
        toks=[t for t in norm(desc).split() if len(t)>2 and t not in {"cover","issue","xxl"}]
        score += min(25,sum(6 for t in toks if t in blob))
    return score

def fetch_img(url, referer=None):
    if not url:return None
    h={"Referer":referer} if referer else {}
    try:
        r=S.get(url,headers=h,timeout=35)
        if r.status_code!=200 or len(r.content)<8000:return None
        im=Image.open(io.BytesIO(r.content))
        im.load()
        if im.width<220 or im.height<280:return None
        ratio=im.width/im.height
        if ratio<0.48 or ratio>1.02:return None
        return im.convert("RGB")
    except Exception:
        return None

def save_cover(e,im):
    # Preserve whole cover; normalize for compact PDF.
    im.thumbnail((1100,1500),Image.Resampling.LANCZOS)
    path=COV/(e["key"]+".jpg")
    im.save(path,"JPEG",quality=86,optimize=True,progressive=True)
    return path

audit=[]
unresolved=[]
for idx,e in enumerate(entries,1):
    path=COV/(e["key"]+".jpg")
    meta_path=COV/(e["key"]+".json")
    if path.exists() and path.stat().st_size>10000 and meta_path.exists():
        meta=json.loads(meta_path.read_text())
        audit.append(meta); print("CACHED",idx,e["mag"],e["label"]); continue
    print(f"RESOLVE {idx}/{len(entries)} {e['mag']} {e['label']} :: {e['query']}")
    try:
        cs=bing(e["query"])
    except Exception as ex:
        cs=[]; print("SEARCH ERR",ex)
    ranked=sorted([(issue_score(e,c,r),r,c) for r,c in enumerate(cs)],reverse=True,key=lambda x:x[0])
    chosen=None
    for score,rank,c in ranked[:15]:
        for u in [c.get("murl"),c.get("turl")]:
            im=fetch_img(u,c.get("purl"))
            if im is not None:
                chosen=(score,rank,c,u,im);break
        if chosen:break
    if not chosen:
        # alternate queries
        alts=[]
        if e["mag"]=="THE SOURCE": alts=[f'"The Source" magazine #{e["num"]} hip hop',f'The Source magazine number {e["num"]}']
        elif e["mag"]=="XXL": alts=[e["query"]+" hip hop",e["query"].replace("issue","number")]
        else: alts=[e["query"]+" hip hop R&B",e["query"].replace("cover","")]
        for aq in alts:
            try: cs=bing(aq)
            except: cs=[]
            ranked=sorted([(issue_score(e,c,r),r,c) for r,c in enumerate(cs)],reverse=True,key=lambda x:x[0])
            for score,rank,c in ranked[:15]:
                for u in [c.get("murl"),c.get("turl")]:
                    im=fetch_img(u,c.get("purl"))
                    if im is not None:
                        chosen=(score,rank,c,u,im);break
                if chosen:break
            if chosen:break
    if not chosen:
        unresolved.append(e); print("UNRESOLVED",e); continue
    score,rank,c,u,im=chosen
    save_cover(e,im)
    meta={**e,"score":score,"rank":rank,"image_url":u,"page_url":c.get("purl"),"desc":c.get("desc",""),"w":im.width,"h":im.height}
    meta_path.write_text(json.dumps(meta,indent=2))
    audit.append(meta)
    print("SAVED",e["key"],score,rank,im.size,c.get("purl"))
    time.sleep(0.12)

with open(ROOT/"audit.csv","w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=["mag","label","query","key","num","score","rank","image_url","page_url","desc","w","h"])
    w.writeheader()
    for a in audit:w.writerow({k:a.get(k,"") for k in w.fieldnames})

if unresolved:
    (ROOT/"unresolved.json").write_text(json.dumps(unresolved,indent=2))
    raise RuntimeError(f"UNRESOLVED {len(unresolved)}: "+", ".join(x["mag"]+" "+x["label"] for x in unresolved))

# Contact sheets for verification
FONT=ImageFont.load_default()
for mag in ["THE SOURCE","VIBE","XXL"]:
    rows=[e for e in entries if e["mag"]==mag]
    for page in range(math.ceil(len(rows)/24)):
        chunk=rows[page*24:(page+1)*24]
        cellw,cellh=260,390; cols=6; rr=4
        sheet=Image.new("RGB",(cellw*cols,cellh*rr),(240,240,240))
        d=ImageDraw.Draw(sheet)
        for j,e in enumerate(chunk):
            im=Image.open(COV/(e["key"]+".jpg")).convert("RGB")
            im.thumbnail((220,315),Image.Resampling.LANCZOS)
            x=(j%cols)*cellw+(cellw-im.width)//2
            y=(j//cols)*cellh+12
            sheet.paste(im,(x,y))
            d.text(((j%cols)*cellw+8,(j//cols)*cellh+334),e["label"],fill=(0,0,0),font=FONT)
            m=next(a for a in audit if a["key"]==e["key"])
            d.text(((j%cols)*cellw+8,(j//cols)*cellh+350),f'score {m["score"]}',fill=(0,0,0),font=FONT)
        sheet.save(ROOT/f'contact_{mag.lower().replace(" ","_")}_{page+1}.jpg',"JPEG",quality=86)

# PDF
OUT=ROOT/"Hip_Hop_Magazine_Cover_Master_190.pdf"
W,H=letter
c=canvas.Canvas(str(OUT),pagesize=letter)
c.setTitle("Master Hip-Hop Magazine Cover Checklist - The Source, VIBE, XXL")
c.setAuthor("Catalog generated from user authoritative manifest")
margin=28
header_h=58
cols=4; rows_per=3
gapx=12; gapy=12
cellw=(W-2*margin-gapx*(cols-1))/cols
cellh=(H-margin-header_h-28-gapy*(rows_per-1))/rows_per

def draw_page_header(mag,page_num,total_pages):
    c.setFillColorRGB(.055,.055,.055); c.rect(0,H-header_h,W,header_h,fill=1,stroke=0)
    c.setFillColor(colors.white); c.setFont("Helvetica-Bold",22); c.drawString(margin,H-35,mag)
    c.setFont("Helvetica",8); c.drawRightString(W-margin,H-31,f"{page_num}/{total_pages}")
    c.setFillColor(colors.black)

for mag in ["THE SOURCE","VIBE","XXL"]:
    mag_entries=[e for e in entries if e["mag"]==mag]
    pages=math.ceil(len(mag_entries)/(cols*rows_per))
    for p in range(pages):
        draw_page_header(mag,p+1,pages)
        chunk=mag_entries[p*cols*rows_per:(p+1)*cols*rows_per]
        for j,e in enumerate(chunk):
            col=j%cols; row=j//cols
            x=margin+col*(cellw+gapx)
            top=H-header_h-12-row*(cellh+gapy)
            label_h=30
            box_h=cellh-label_h
            im=Image.open(COV/(e["key"]+".jpg"))
            iw,ih=im.size
            scale=min((cellw-4)/iw,(box_h-4)/ih)
            dw,dh=iw*scale,ih*scale
            c.drawImage(str(COV/(e["key"]+".jpg")),x+(cellw-dw)/2,top-box_h+(box_h-dh)/2,width=dw,height=dh,preserveAspectRatio=True,mask="auto")
            c.setFont("Helvetica",7.5)
            label="[ ] "+e["label"]
            # simple wrap max 2 lines
            words=label.split(); lines=[]; cur=""
            for w in words:
                t=(cur+" "+w).strip()
                if c.stringWidth(t,"Helvetica",7.5)<=cellw-4: cur=t
                else:
                    if cur: lines.append(cur)
                    cur=w
            if cur: lines.append(cur)
            yy=top-box_h-10
            for line in lines[:2]:
                c.drawCentredString(x+cellw/2,yy,line); yy-=9
        c.setFont("Helvetica",6.5); c.setFillColor(colors.grey)
        c.drawRightString(W-margin,12,f"{mag} - {p+1}")
        c.showPage()
c.save()

print("FINAL",OUT,OUT.stat().st_size)
print("AUDIT",ROOT/"audit.csv")
