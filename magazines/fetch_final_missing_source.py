import io, json, re
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from PIL import Image

OUT=Path("final_missing_source")
OUT.mkdir(exist_ok=True)
S=requests.Session()
S.headers.update({"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/152 Safari/537.36"})

pages={
"source_112":"https://rapstylearcheology.com/products/january-1999",
"source_118":"https://rapstylearcheology.com/products/july-1999",
"source_121":"https://rapstylearcheology.com/products/october-1999",
"source_123":"https://rapstylearcheology.com/products/december-1999",
"source_127":"https://www.originalmagazines.com/products/the-source-magazine-april-2000-ice-cube-snoop-dogg-and-dr-dre-no-label",
}
direct={
"source_116":"https://i.ebayimg.com/images/g/mCYAAOSwtAxktDxZ/s-l1600.webp",
}

def urls_from_page(url):
    r=S.get(url,timeout=60); r.raise_for_status()
    s=BeautifulSoup(r.text,"html.parser")
    us=[]
    for m in s.find_all("meta"):
        k=(m.get("property") or m.get("name") or "").lower()
        if k in ("og:image","twitter:image","twitter:image:src"):
            u=(m.get("content") or "").strip()
            if u: us.append(u)
    # Shopify / Wix / CDN image URLs embedded in HTML
    for pat in [
        r'https://cdn\.shopify\.com/[^"\\ ]+?\.(?:jpg|jpeg|png|webp)[^"\\ ]*',
        r'https://cdn\.shopify\.com/s/files/[^"\\ ]+',
        r'https://images\.squarespace-cdn\.com/[^"\\ ]+',
    ]:
        us += re.findall(pat,r.text,re.I)
    out=[]
    for u in us:
        u=u.replace("\\u0026","&").replace("\\/","/")
        if u.startswith("//"): u="https:"+u
        if u not in out: out.append(u)
    return out

def fetch_img(url,referer=None):
    r=S.get(url,headers={"Referer":referer} if referer else {},timeout=60)
    if r.status_code!=200 or len(r.content)<8000: return None
    try:
        im=Image.open(io.BytesIO(r.content)); im.load(); im=im.convert("RGB")
    except Exception: return None
    if im.width<250 or im.height<300: return None
    return im

audit=[]
for key,url in pages.items():
    chosen=None
    for u in urls_from_page(url):
        im=fetch_img(u,url)
        if im is None: continue
        # prefer portrait-ish reasonably large images
        if not (0.45 <= im.width/im.height <= 1.05): continue
        chosen=(u,im); break
    if not chosen: raise RuntimeError(f"No image for {key} {url}")
    u,im=chosen
    im.thumbnail((1400,1800),Image.Resampling.LANCZOS)
    p=OUT/f"{key}.jpg"; im.save(p,"JPEG",quality=92,optimize=True)
    audit.append({"key":key,"page":url,"image":u,"w":im.width,"h":im.height,"bytes":p.stat().st_size})

for key,u in direct.items():
    im=fetch_img(u)
    if im is None: raise RuntimeError(f"No image for {key} {u}")
    im.thumbnail((1400,1800),Image.Resampling.LANCZOS)
    p=OUT/f"{key}.jpg"; im.save(p,"JPEG",quality=92,optimize=True)
    audit.append({"key":key,"page":"eBay","image":u,"w":im.width,"h":im.height,"bytes":p.stat().st_size})

(OUT/"audit.json").write_text(json.dumps(audit,indent=2))
print(json.dumps(audit,indent=2))
