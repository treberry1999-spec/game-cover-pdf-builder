import requests,json,re,io,math
from pathlib import Path
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from PIL import Image,ImageDraw,ImageFont

OUT=Path("magazine_output/vibe_missing_candidates"); OUT.mkdir(parents=True,exist_ok=True)
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/152 Safari/537.36"})

T=[
("vibe_02","#2 - Wesley Snipes","VIBE magazine October 1993 Wesley Snipes cover",["vibe","wesley","snipes","1993"]),
("vibe_06","1994 - Janet Jackson","VIBE magazine October 1994 Janet Jackson cover",["vibe","janet","1994"]),
("vibe_12","1996 - Mariah Carey","VIBE magazine April 1996 Mariah Carey cover",["vibe","mariah","1996"]),
("vibe_13","May 1996 - Bone Thugs-N-Harmony","VIBE magazine May 1996 Bone Thugs N Harmony cover",["vibe","bone","1996"]),
("vibe_14","1996 - Fugees","VIBE magazine June July 1996 Fugees cover",["vibe","fugees","1996"]),
("vibe_17","1997 - Wu-Tang Clan","VIBE magazine September 1997 Wu Tang Clan cover",["vibe","wu","tang","1997"]),
("vibe_20","1997 - Erykah Badu","VIBE magazine August 1997 Erykah Badu cover",["vibe","erykah","1997"]),
("vibe_21","1997 - Toni Braxton","VIBE magazine June July 1997 Toni Braxton cover",["vibe","toni","braxton","1997"]),
]

def bing(q):
    u="https://www.bing.com/images/async?"+urlencode({"q":q,"async":"1","first":1,"count":60})
    r=S.get(u,timeout=50); r.raise_for_status()
    soup=BeautifulSoup(r.text,"html.parser"); out=[]
    for a in soup.select("a.iusc"):
        try:m=json.loads(a.get("m") or "{}")
        except:continue
        if m.get("murl"):out.append(m)
    return out

def getim(u,ref):
    try:
        r=S.get(u,headers={"Referer":ref or "https://www.bing.com/"},timeout=40)
        if r.status_code!=200 or len(r.content)<8000:return None
        im=Image.open(io.BytesIO(r.content));im.load();im=im.convert("RGB")
        if im.width<250 or im.height<300:return None
        ratio=im.width/im.height
        if not .48<=ratio<=.95:return None
        return im
    except:return None

audit=[]
font=ImageFont.load_default()
for key,label,q,toks in T:
    cs=bing(q); saved=[]
    scored=[]
    for rank,c in enumerate(cs):
        blob=re.sub(r"[^a-z0-9]+"," "," ".join([c.get("purl",""),c.get("desc",""),c.get("t",""),c.get("murl","")]).lower())
        score=100-rank+sum(35 for t in toks if t in blob)
        scored.append((score,rank,c))
    for score,rank,c in sorted(scored,reverse=True,key=lambda x:x[0]):
        im=getim(c.get("murl"),c.get("purl"))
        if im is None: continue
        # simple duplicate rejection by URL
        fn=OUT/f"{key}_cand{len(saved)+1}.jpg"
        im.thumbnail((1000,1350),Image.Resampling.LANCZOS);im.save(fn,"JPEG",quality=88,optimize=True)
        saved.append({"file":fn.name,"score":score,"rank":rank,"murl":c.get("murl"),"purl":c.get("purl"),"desc":c.get("desc",""),"size":im.size})
        if len(saved)>=6:break
    audit.append({"key":key,"label":label,"query":q,"candidates":saved})
    print(key,label,"saved",len(saved))
(OUT/"candidates.json").write_text(json.dumps(audit,indent=2))

# one contact sheet per target
for rec in audit:
    sheet=Image.new("RGB",(1800,760),"white");d=ImageDraw.Draw(sheet)
    d.text((15,10),rec["label"],fill="black",font=font)
    for j,c in enumerate(rec["candidates"]):
        im=Image.open(OUT/c["file"]).convert("RGB");im.thumbnail((260,600),Image.Resampling.LANCZOS)
        x=15+j*295+(260-im.width)//2;y=45;sheet.paste(im,(x,y))
        d.text((15+j*295,655),f"C{j+1} score {c['score']}",fill="black",font=font)
        d.text((15+j*295,675),(c["purl"] or "")[:38],fill="black",font=font)
    sheet.save(OUT/f'{rec["key"]}_contact.jpg',"JPEG",quality=88)
