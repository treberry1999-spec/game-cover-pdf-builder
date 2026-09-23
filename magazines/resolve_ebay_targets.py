import requests,re,json,io,time
from pathlib import Path
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from PIL import Image,ImageDraw,ImageFont

S=requests.Session()
S.headers.update({"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/152 Safari/537.36"})
OUT=Path("magazine_output/ebay_targets");COV=OUT/"covers";COV.mkdir(parents=True,exist_ok=True)

targets=[
("vibe_02","#2","VIBE October 1993 Wesley Snipes magazine",["vibe","wesley","snipes","1993"]),
("vibe_06","1994 - Janet Jackson","VIBE October 1994 Janet Jackson magazine",["vibe","janet","1994"]),
("vibe_12","1996 - Mariah Carey","VIBE April 1996 Mariah Carey magazine",["vibe","mariah","1996"]),
("vibe_13","May 1996 - Bone Thugs-N-Harmony","VIBE May 1996 Bone Thugs N Harmony magazine",["vibe","bone","1996"]),
("vibe_14","1996 - Fugees","VIBE June July 1996 Fugees magazine",["vibe","fugees","1996"]),
("vibe_17","1997 - Wu-Tang Clan","VIBE September 1997 Wu Tang Clan magazine",["vibe","wu","tang","1997"]),
("vibe_20","1997 - Erykah Badu","VIBE August 1997 Erykah Badu magazine",["vibe","erykah","badu","1997"]),
("vibe_29","2003 - The Neptunes / Timbaland / Missy Elliott","VIBE September 2003 Neptunes Timbaland Missy Elliott magazine",["vibe","2003","timbaland","missy"]),
("vibe_30","2004 - Alicia Keys","VIBE March 2004 Alicia Keys magazine",["vibe","alicia","2004"]),
]
for n in [100,102,116,123,127,160,166,167]:
    targets.append((f"source_{n:03d}",f"#{n}",f"The Source Magazine issue {n}",["source",str(n)]))

def norm(s):return re.sub(r"[^a-z0-9]+"," ",(s or "").lower()).strip()

def image_from_url(url):
    try:
        r=S.get(url,timeout=60)
        if r.status_code!=200 or len(r.content)<5000:return None
        im=Image.open(io.BytesIO(r.content));im.load();return im.convert("RGB")
    except Exception:return None

audit=[];unresolved=[]
for key,label,q,toks in targets:
    url="https://www.ebay.com/sch/i.html?_nkw="+quote_plus(q)+"&_sop=12"
    try:
        r=S.get(url,timeout=60); print("QUERY",key,r.status_code,len(r.content))
        soup=BeautifulSoup(r.text,"html.parser")
    except Exception as e:
        unresolved.append({"key":key,"label":label,"query":q,"error":str(e)});continue
    candidates=[]
    for li in soup.select("li.s-item"):
        title_el=li.select_one(".s-item__title")
        img=li.select_one("img.s-item__image-img")
        if not title_el or not img:continue
        title=title_el.get_text(" ",strip=True)
        src=img.get("src") or img.get("data-src") or img.get("data-defer-load")
        if not src:continue
        blob=norm(title)
        hits=sum(1 for t in toks if norm(t) in blob)
        score=hits*30
        # Reject obviously wrong years for VIBE targets
        years=re.findall(r"\b(19\d{2}|20\d{2})\b",q)
        if years and years[0] in blob:score+=30
        if key.startswith("source_"):
            n=key.split("_")[1].lstrip("0")
            if re.search(rf"\b{n}\b",blob):score+=60
        candidates.append((score,title,src))
    candidates.sort(reverse=True,key=lambda z:z[0])
    chosen=None
    for score,title,src in candidates[:10]:
        required=max(2,len(toks)-1) if len(toks)>=3 else len(toks)
        hits=sum(1 for t in toks if norm(t) in norm(title))
        if hits<required:continue
        im=image_from_url(src)
        if im is None:continue
        if im.width/im.height>1.1:continue
        chosen=(score,title,src,im);break
    if chosen:
        score,title,src,im=chosen
        im.thumbnail((1200,1600),Image.Resampling.LANCZOS)
        im.save(COV/f"{key}.jpg","JPEG",quality=90,optimize=True)
        audit.append({"key":key,"label":label,"query":q,"score":score,"title":title,"image":src})
        print("SAVED",key,title,im.size)
    else:
        unresolved.append({"key":key,"label":label,"query":q,"top":[{"score":s,"title":t,"image":u} for s,t,u in candidates[:5]]})
        print("UNRESOLVED",key,candidates[:3])
    time.sleep(.25)
(OUT/"audit.json").write_text(json.dumps(audit,indent=2))
(OUT/"unresolved.json").write_text(json.dumps(unresolved,indent=2))
# contact sheet
font=ImageFont.load_default()
for pg in range((len(audit)+19)//20):
    chunk=audit[pg*20:(pg+1)*20]
    sheet=Image.new("RGB",(1500,1600),"white");d=ImageDraw.Draw(sheet)
    for j,a in enumerate(chunk):
        im=Image.open(COV/f'{a["key"]}.jpg').convert("RGB");im.thumbnail((250,330),Image.Resampling.LANCZOS)
        col=j%5;row=j//5;x=col*300+(300-im.width)//2;y=row*400+10
        sheet.paste(im,(x,y));d.text((col*300+8,row*400+345),a["label"],fill="black",font=font)
        d.text((col*300+8,row*400+362),a["title"][:40],fill="black",font=font)
    sheet.save(OUT/f"contact_{pg+1}.jpg","JPEG",quality=88)
print("RESOLVED",len(audit),"UNRESOLVED",len(unresolved))
