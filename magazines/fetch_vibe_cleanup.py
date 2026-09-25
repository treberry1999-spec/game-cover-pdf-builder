import requests,re,io
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image
S=requests.Session()
S.headers.update({"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/152 Safari/537.36"})
OUT=Path("vibe_cleanup"); OUT.mkdir(exist_ok=True)
pages={
"vibe_17":"https://www.rapzines.com/product-page/vibe-magazine-september-1997-wu-tang-clan",
"vibe_23":"https://www.rapzines.com/product-page/vibe-magazine-february-1998-rap-reigns-cover-our-biggest-baddest-picks-of-the-year",
}
def candidates(soup):
    out=[]
    for m in soup.find_all("meta"):
        k=(m.get("property") or m.get("name") or "").lower()
        if k in ("og:image","twitter:image","twitter:image:src"):
            u=(m.get("content") or "").strip()
            if u: out.append(u)
    html=str(soup)
    out += re.findall(r'https://static\.wixstatic\.com/media/[^"\\ ]+\.(?:jpg|jpeg|png|webp)[^"\\ ]*',html,re.I)
    seen=[]
    for u in out:
        u=u.replace("\\u0026","&").replace("\\/","/")
        if u not in seen: seen.append(u)
    return seen
def fetch_img(u,ref):
    try:
        r=S.get(u,headers={"Referer":ref},timeout=60)
        if r.status_code!=200 or len(r.content)<7000:return None
        im=Image.open(io.BytesIO(r.content));im.load();im=im.convert("RGB")
        if im.width<250 or im.height<300:return None
        return im
    except Exception:return None
for key,url in pages.items():
    r=S.get(url,timeout=60);r.raise_for_status()
    soup=BeautifulSoup(r.text,"html.parser")
    chosen=None
    for u in candidates(soup):
        im=fetch_img(u,url)
        if im is not None and 0.45 <= im.width/im.height <= 1.05:
            chosen=(u,im);break
    if not chosen: raise RuntimeError(f"no image for {key}")
    u,im=chosen
    im.thumbnail((1400,1800),Image.Resampling.LANCZOS)
    im.save(OUT/f"{key}.jpg","JPEG",quality=92,optimize=True)
    print(key, im.size, u)
