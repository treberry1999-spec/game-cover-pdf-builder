import requests,json,re,io,math
from pathlib import Path
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from PIL import Image,ImageDraw,ImageFont

OUT=Path("magazine_output/source_missing");OUT.mkdir(parents=True,exist_ok=True)
COV=OUT/"covers";COV.mkdir(exist_ok=True)
S=requests.Session();S.headers.update({"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/152 Safari/537.36"})

# Exact high-confidence Shopify images from Rap Style Archeology index
DIRECT={
109:("A Tribe Called Quest - October 1998","https://cdn.shopify.com/s/files/1/0355/4315/4821/files/IMG-4672.jpg?v=1789846006"),
124:("Jay-Z - January 2000","https://cdn.shopify.com/s/files/1/0355/4315/4821/products/image_b09b11b8-b092-4778-9dcb-41d904d09924.jpg?v=1599675064"),
136:("Wu-Tang Clan - January 2001","https://cdn.shopify.com/s/files/1/0355/4315/4821/products/image_c666209e-c74a-4fcb-9bec-712096f65d9d.jpg?v=1616249125"),
154:("Nelly - July 2002","https://cdn.shopify.com/s/files/1/0355/4315/4821/files/FullSizeRender_fff27abf-fe4c-41da-9e73-234c0c9e7d25.jpg?v=1782219536"),
165:("Pharrell - June 2003","https://cdn.shopify.com/s/files/1/0355/4315/4821/products/image_57d5b693-8b73-4077-8ee0-33a5a6cab9ad.jpg?v=1598549093"),
}
# Remaining exact issue/month/cover queries
Q={
112:("DMX - January 1999",'The Source magazine issue 112 January 1999 DMX cover'),
116:("Nas - May 1999",'The Source magazine issue 116 May 1999 Nas cover'),
118:("Missy Elliott & Timbaland - July 1999",'The Source magazine issue 118 July 1999 Missy Elliott Timbaland cover'),
121:("Eve - October 1999",'The Source magazine issue 121 October 1999 Eve cover'),
123:("Lil Kim - December 1999",'The Source magazine issue 123 December 1999 Lil Kim cover'),
127:("Ice Cube / Snoop Dogg / Dr. Dre - April 2000",'The Source magazine issue 127 April 2000 Ice Cube Snoop Dogg Dr Dre cover'),
}

def save(n,title,url,source):
    r=S.get(url,timeout=60,headers={"Referer":source if source.startswith("http") else "https://www.google.com/"})
    r.raise_for_status()
    im=Image.open(io.BytesIO(r.content));im.load();im=im.convert("RGB")
    if im.width<230 or im.height<300: raise RuntimeError(f"too small {im.size}")
    ratio=im.width/im.height
    if not .45<=ratio<=1.0: raise RuntimeError(f"ratio {ratio}")
    im.thumbnail((1200,1650),Image.Resampling.LANCZOS)
    p=COV/f"source_{n:03d}.jpg";im.save(p,"JPEG",quality=90,optimize=True)
    return {"key":f"source_{n:03d}","label":f"#{n}","title":title,"file":p.name,"url":url,"source":source,"size":im.size}

audit=[];unresolved=[]
for n,(title,url) in DIRECT.items():
    try:
        rec=save(n,title,url,"Rap Style Archeology");audit.append(rec);print("DIRECT",n,rec["size"])
    except Exception as e:
        unresolved.append({"issue":n,"reason":repr(e)});print("DIRECT ERR",n,e)

def bing(q):
    u="https://www.bing.com/images/async?"+urlencode({"q":q,"async":"1","first":1,"count":50})
    r=S.get(u,timeout=50);r.raise_for_status();s=BeautifulSoup(r.text,"html.parser");out=[]
    for a in s.select("a.iusc"):
        try:m=json.loads(a.get("m") or "{}")
        except:continue
        if m.get("murl"):out.append(m)
    return out

def fetch_img(u,ref):
    try:
        r=S.get(u,headers={"Referer":ref or "https://www.bing.com/"},timeout=45)
        if r.status_code!=200 or len(r.content)<7000:return None
        im=Image.open(io.BytesIO(r.content));im.load();im=im.convert("RGB")
        if im.width<230 or im.height<300:return None
        ratio=im.width/im.height
        if not .45<=ratio<=1.0:return None
        return im
    except:return None

candidates={}
for n,(title,q) in Q.items():
    cs=bing(q);saved=[];scored=[]
    for rank,c in enumerate(cs):
        blob=re.sub(r"[^a-z0-9]+"," "," ".join([c.get("purl",""),c.get("desc",""),c.get("t",""),c.get("murl","")]).lower())
        score=100-rank
        for tok in ["source",str(n)]: 
            if tok in blob:score+=45
        for tok in re.findall(r"[a-z]+",title.lower()):
            if len(tok)>2 and tok in blob:score+=10
        scored.append((score,rank,c))
    for score,rank,c in sorted(scored,reverse=True,key=lambda x:x[0]):
        im=fetch_img(c.get("murl"),c.get("purl"))
        if im is None:continue
        fn=OUT/f"source_{n:03d}_cand{len(saved)+1}.jpg"
        im.thumbnail((1000,1400),Image.Resampling.LANCZOS);im.save(fn,"JPEG",quality=88,optimize=True)
        saved.append({"file":fn.name,"score":score,"purl":c.get("purl"),"murl":c.get("murl"),"desc":c.get("desc",""),"size":im.size})
        if len(saved)>=5:break
    candidates[str(n)]={"label":f"#{n}","title":title,"query":q,"candidates":saved}
    print("CANDS",n,len(saved))
(OUT/"candidates.json").write_text(json.dumps(candidates,indent=2))
(OUT/"audit.json").write_text(json.dumps(audit,indent=2))
(OUT/"unresolved.json").write_text(json.dumps(unresolved,indent=2))

font=ImageFont.load_default()
for n,rec in candidates.items():
    sheet=Image.new("RGB",(1550,760),"white");d=ImageDraw.Draw(sheet)
    d.text((15,10),f"Source #{n} - {rec['title']}",fill="black",font=font)
    for j,c in enumerate(rec["candidates"]):
        im=Image.open(OUT/c["file"]).convert("RGB");im.thumbnail((260,600),Image.Resampling.LANCZOS)
        x=15+j*300+(260-im.width)//2;y=45;sheet.paste(im,(x,y))
        d.text((15+j*300,655),f"C{j+1} score {c['score']}",fill="black",font=font)
        d.text((15+j*300,675),(c["purl"] or "")[:42],fill="black",font=font)
    sheet.save(OUT/f"source_{int(n):03d}_contact.jpg","JPEG",quality=88)
