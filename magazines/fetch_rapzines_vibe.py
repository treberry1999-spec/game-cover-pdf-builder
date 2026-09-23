import requests, re, json, io, os
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from PIL import Image, ImageDraw, ImageFont

URL="https://www.rapzines.com/copy-of-xxl"
OUT=Path("magazine_output/rapzines_vibe_archive")
OUT.mkdir(parents=True,exist_ok=True)
S=requests.Session()
S.headers.update({"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/152 Safari/537.36"})
r=S.get(URL,timeout=60); r.raise_for_status()
open(OUT/"page.html","wb").write(r.content)
soup=BeautifulSoup(r.text,"html.parser")

items=[]
for img in soup.find_all("img"):
    alt=(img.get("alt") or "").strip()
    if "vibe magazine" not in alt.lower(): continue
    src=img.get("src") or img.get("data-src") or ""
    srcset=img.get("srcset") or ""
    candidates=[]
    for part in srcset.split(","):
        u=part.strip().split(" ")[0].strip()
        if u: candidates.append(u)
    if src: candidates.append(src)
    # de-dup preserving order, prefer last/largest srcset first by reversing
    cand=[]
    for u in reversed(candidates):
        if u not in cand: cand.append(u)
    saved=None
    for u in cand:
        if u.startswith("//"): u="https:"+u
        if not u.startswith("http"): u=urljoin(URL,u)
        try:
            rr=S.get(u,timeout=60)
            if rr.status_code!=200 or len(rr.content)<5000: continue
            im=Image.open(io.BytesIO(rr.content)); im.load()
            if im.width<180 or im.height<180: continue
            saved=(u,im.convert("RGB")); break
        except Exception:
            continue
    if not saved: continue
    u,im=saved
    safe=re.sub(r"[^a-z0-9]+","_",alt.lower()).strip("_")[:100]
    path=OUT/f"{len(items)+1:03d}_{safe}.jpg"
    im.thumbnail((1200,1600),Image.Resampling.LANCZOS)
    im.save(path,"JPEG",quality=90,optimize=True)
    items.append({"alt":alt,"file":path.name,"src":u,"w":im.width,"h":im.height})

(OUT/"index.json").write_text(json.dumps(items,indent=2))
print("COUNT",len(items))
for x in items: print(x["file"],x["alt"],x["w"],x["h"])

# contact sheets
font=ImageFont.load_default()
for pg in range((len(items)+19)//20):
    chunk=items[pg*20:(pg+1)*20]
    sheet=Image.new("RGB",(1500,1600),"white"); d=ImageDraw.Draw(sheet)
    for j,x in enumerate(chunk):
        im=Image.open(OUT/x["file"]).convert("RGB")
        im.thumbnail((250,330),Image.Resampling.LANCZOS)
        col=j%5; row=j//5; xx=col*300+(300-im.width)//2; yy=row*400+10
        sheet.paste(im,(xx,yy))
        label=x["alt"]
        d.text((col*300+8,row*400+345),label[:42],fill="black",font=font)
        if len(label)>42:d.text((col*300+8,row*400+360),label[42:84],fill="black",font=font)
    sheet.save(OUT/f"contact_{pg+1:02d}.jpg","JPEG",quality=88)
