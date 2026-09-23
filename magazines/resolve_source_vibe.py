import requests,json,re,io,calendar,time,math
from pathlib import Path
from urllib.parse import urlencode,urljoin
from bs4 import BeautifulSoup
from PIL import Image,ImageDraw,ImageFont

H={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/152 Safari/537.36"}
S=requests.Session(); S.headers.update(H)
OUT=Path("magazine_output/targeted"); OUT.mkdir(parents=True,exist_ok=True)
COV=OUT/"covers"; COV.mkdir(exist_ok=True)

SOURCE_NUMS=[100,102,103,105,106,107,108,109,110,111,112,113,116,117,118,119,121,122,123,124,125,126,127,128,130,134,135,136,142,148,150,152,154,156,160,163,165,166,167,169,175,185]
VIBE=[
("#1","Vibe magazine September 1993 Snoop Dogg first official issue cover",1993,["snoop"]),
("#2","Vibe magazine October 1993 Wesley Snipes second issue cover",1993,["wesley","snipes"]),
("1994 — 2Pac","Vibe magazine 1994 2Pac Tupac cover",1994,["2pac","tupac"]),
("1994 — Ice Cube","Vibe magazine 1994 Ice Cube cover",1994,["ice","cube"]),
("1994 — Prince","Vibe magazine 1994 Prince cover",1994,["prince"]),
("1994 — Janet Jackson","Vibe magazine 1994 Janet Jackson cover",1994,["janet"]),
("1995 — Mary J. Blige","Vibe magazine 1995 Mary J Blige cover",1995,["mary","blige"]),
("1995 — 2Pac","Vibe magazine 1995 Tupac 2Pac cover",1995,["tupac","2pac"]),
("1995 — Michael Jackson","Vibe magazine 1995 Michael Jackson cover",1995,["michael","jackson"]),
("1995 — Biggie & Faith Evans","Vibe magazine 1995 Biggie Faith Evans cover",1995,["biggie","faith"]),
("1996 — Death Row","Vibe magazine 1996 Death Row Tupac Snoop Dre Suge cover",1996,["death","row"]),
("1996 — Mariah Carey","Vibe magazine 1996 Mariah Carey cover",1996,["mariah"]),
("May 1996 — Bone Thugs-N-Harmony","Vibe magazine May 1996 Bone Thugs N Harmony cover",1996,["bone","thugs"]),
("1996 — Fugees","Vibe magazine 1996 Fugees cover",1996,["fugees"]),
("1996 — Dream Team II","Vibe magazine 1996 Dream Team II cover",1996,["dream","team"]),
("1996 — Biggie & Puff Daddy","Vibe magazine 1996 Biggie Puff Daddy cover",1996,["biggie","puff"]),
("1997 — Wu-Tang Clan","Vibe magazine 1997 Wu Tang Clan cover",1997,["wu","tang"]),
("1997 — The Notorious B.I.G.","Vibe magazine 1997 Notorious BIG Biggie cover",1997,["biggie","notorious"]),
("1997 — Janet Jackson","Vibe magazine 1997 Janet Jackson cover",1997,["janet"]),
("1997 — Erykah Badu","Vibe magazine 1997 Erykah Badu cover",1997,["erykah","badu"]),
("1997 — Toni Braxton","Vibe magazine 1997 Toni Braxton cover",1997,["toni","braxton"]),
("1997 — Michael Jackson / Chris Rock","Vibe magazine February 1997 Michael Jordan Chris Rock cover",1997,["chris","rock"]),
("1998 — Rap Reigns","Vibe magazine February 1998 Rap Reigns cover",1998,["rap","reigns"]),
("1999 — Biggie / 2Pac","Vibe magazine 1999 Biggie Tupac 2Pac cover",1999,["biggie","2pac"]),
("2000 — Q-Tip","Vibe magazine 2000 Q Tip cover",2000,["tip"]),
("2000 — Jay-Z","Vibe magazine 2000 Jay Z cover",2000,["jay"]),
("2002 — Alicia Keys","Vibe magazine 2002 Alicia Keys cover",2002,["alicia","keys"]),
("2003 — Jay-Z","Vibe magazine 2003 Jay Z cover",2003,["jay"]),
("2003 — The Neptunes / Timbaland / Missy Elliott","Vibe magazine 2003 Neptunes Timbaland Missy Elliott cover",2003,["neptunes","timbaland","missy"]),
("2004 — Alicia Keys","Vibe magazine 2004 Alicia Keys cover",2004,["alicia","keys"]),
("2004 — Shyne","Vibe magazine 2004 Shyne cover",2004,["shyne"]),
("2006 — Eminem / 50 Cent","Vibe magazine 2006 Eminem 50 Cent cover",2006,["eminem","50"]),
("2006 — Allen Iverson","Vibe magazine 2006 Allen Iverson cover",2006,["iverson"]),
("2006 — Keyshia Cole","Vibe magazine 2006 Keyshia Cole cover",2006,["keyshia","cole"]),
]

def norm(s): return re.sub(r"[^a-z0-9]+"," ",(s or "").lower())

def get(url):
    r=S.get(url,timeout=45)
    r.raise_for_status()
    return r

# scrape Rap Style Archeology product index
r=get("https://rapstylearcheology.com/collections")
s=BeautifulSoup(r.text,"html.parser")
links=[];seen=set()
for a in s.find_all("a",href=True):
    u=urljoin(r.url,a["href"])
    if "/products/" not in u or u in seen: continue
    seen.add(u)
    if any(k in u.lower() for k in ["source","vibe"]): links.append(u)
records=[]
for i,u in enumerate(links):
    try:
        pr=get(u); ps=BeautifulSoup(pr.text,"html.parser")
        ogt=ps.find("meta",property="og:title"); ogi=ps.find("meta",property="og:image")
        title=(ogt.get("content") if ogt else "") or (ps.find("h1").get_text(" ",strip=True) if ps.find("h1") else "")
        image=ogi.get("content") if ogi else None
        if title and image: records.append({"title":title,"url":u,"image":image})
    except Exception as e: print("RAP ERR",u,e)
print("RAP RECORDS",len(records))

def fetch_image(url):
    trials=[url]
    if "cdn.shopify.com" in url:
        sep="&" if "?" in url else "?"
        trials=[url+sep+"width=1400&format=jpg",url]
    for u in trials:
        try:
            r=S.get(u,timeout=50)
            if r.status_code!=200 or len(r.content)<6000: continue
            im=Image.open(io.BytesIO(r.content)); im.load(); im=im.convert("RGB")
            if im.width<180 or im.height<250: continue
            return im,u
        except Exception: pass
    return None,None

def bing(query):
    url="https://www.bing.com/images/async?"+urlencode({"q":query,"async":"1","first":1,"count":50})
    r=S.get(url,timeout=45); r.raise_for_status()
    soup=BeautifulSoup(r.text,"html.parser")
    out=[]
    for a in soup.select("a.iusc"):
        try:m=json.loads(a.get("m") or "{}")
        except:continue
        if m.get("murl"):out.append(m)
    return out

def save(key,im):
    im.thumbnail((1200,1600),Image.Resampling.LANCZOS)
    p=COV/f"{key}.jpg"; im.save(p,"JPEG",quality=90,optimize=True)
    return str(p)

audit=[]; unresolved=[]

# Expected source month/year, issue 100 = Jan 1998
def src_date(n):
    k=n-100; y=1998+k//12; m=1+k%12
    return calendar.month_name[m],y

def issue_in_title(title,n):
    t=norm(title)
    return bool(re.search(rf"\b(?:issue|no|number)\s*0*{n}\b",t)) or bool(re.search(rf"\b0*{n}\b",t))

for n in SOURCE_NUMS:
    key=f"source_{n:03d}"; chosen=None; method=""
    exact=[x for x in records if x["title"].lower().startswith("the source magazine") and issue_in_title(x["title"],n)]
    if exact:
        im,u=fetch_image(exact[0]["image"])
        if im: chosen=(im,u,exact[0]["url"],exact[0]["title"]); method="rapstyle-issue"
    if not chosen:
        mo,y=src_date(n)
        dated=[x for x in records if x["title"].lower().startswith("the source magazine") and mo.lower() in x["title"].lower() and str(y) in x["title"]]
        if len(dated)==1:
            im,u=fetch_image(dated[0]["image"])
            if im: chosen=(im,u,dated[0]["url"],dated[0]["title"]);method="rapstyle-date"
    if not chosen:
        mo,y=src_date(n)
        queries=[f'"The Source Magazine" "Issue {n}" cover',f'The Source Magazine issue {n} {mo} {y} cover']
        for q in queries:
            try: cs=bing(q)
            except Exception as e: print("BING ERR",q,e);cs=[]
            scored=[]
            for rank,c in enumerate(cs):
                blob=norm(" ".join([c.get("purl",""),c.get("desc",""),c.get("t",""),c.get("murl","")]))
                if "source" not in blob: continue
                score=100-rank
                if re.search(rf"\b{n}\b",blob):score+=120
                if str(y) in blob:score+=30
                if mo.lower() in blob:score+=20
                scored.append((score,c))
            for score,c in sorted(scored,reverse=True,key=lambda z:z[0])[:12]:
                if score<115: continue
                im,u=fetch_image(c.get("murl"))
                if not im: continue
                ratio=im.width/im.height
                if 0.48<=ratio<=1.05:
                    chosen=(im,u,c.get("purl"),c.get("desc") or c.get("t",""));method="bing-strict";break
            if chosen:break
    if chosen:
        im,u,page,title=chosen; save(key,im)
        audit.append({"key":key,"mag":"THE SOURCE","label":f"#{n}","method":method,"title":title,"image_url":u,"page_url":page})
        print("SAVED",key,method,title,im.size)
    else:
        unresolved.append({"key":key,"mag":"THE SOURCE","label":f"#{n}"});print("UNRESOLVED SOURCE",n)

for idx,(label,q,year,toks) in enumerate(VIBE,1):
    key=f"vibe_{idx:02d}"; chosen=None;method=""
    # use RapStyle if year and subject token match
    candidates=[]
    if label=="#1":
        # official first issue
        pass
    elif label=="#2":
        pass
    else:
        for x in records:
            t=norm(x["title"])
            if not x["title"].lower().startswith("vibe magazine"):continue
            if str(year) not in t:continue
            hit=sum(1 for tok in toks if norm(tok) in t)
            if hit>=max(1,min(2,len(toks))): candidates.append((hit,x))
        candidates.sort(reverse=True,key=lambda z:z[0])
        if candidates:
            im,u=fetch_image(candidates[0][1]["image"])
            if im:
                x=candidates[0][1]; chosen=(im,u,x["url"],x["title"]);method="rapstyle"
    if not chosen:
        queries=[q,q+" vintage"]
        for qq in queries:
            try:cs=bing(qq)
            except Exception as e:print("BING ERR",qq,e);cs=[]
            scored=[]
            for rank,c in enumerate(cs):
                blob=norm(" ".join([c.get("purl",""),c.get("desc",""),c.get("t",""),c.get("murl","")]))
                if "vibe" not in blob:continue
                score=100-rank
                if str(year) in blob:score+=35
                hit=sum(1 for tok in toks if norm(tok) in blob)
                score+=hit*35
                if label=="#1" and "snoop" in blob:score+=50
                if label=="#2" and "wesley" in blob:score+=50
                scored.append((score,c))
            for score,c in sorted(scored,reverse=True,key=lambda z:z[0])[:15]:
                if score<120:continue
                im,u=fetch_image(c.get("murl"))
                if not im:continue
                ratio=im.width/im.height
                if 0.48<=ratio<=1.05:
                    chosen=(im,u,c.get("purl"),c.get("desc") or c.get("t",""));method="bing-strict";break
            if chosen:break
    if chosen:
        im,u,page,title=chosen;save(key,im)
        audit.append({"key":key,"mag":"VIBE","label":label,"method":method,"title":title,"image_url":u,"page_url":page})
        print("SAVED",key,method,label,title,im.size)
    else:
        unresolved.append({"key":key,"mag":"VIBE","label":label});print("UNRESOLVED VIBE",label)

(OUT/"audit.json").write_text(json.dumps(audit,indent=2))
(OUT/"unresolved.json").write_text(json.dumps(unresolved,indent=2))

# contact sheets
font=ImageFont.load_default()
for mag,prefix,count in [("THE SOURCE","source_",len(SOURCE_NUMS)),("VIBE","vibe_",len(VIBE))]:
    records_mag=[a for a in audit if a["mag"]==mag]
    for pg in range(math.ceil(len(records_mag)/20)):
        chunk=records_mag[pg*20:(pg+1)*20]
        sheet=Image.new("RGB",(1500,1600),"white");d=ImageDraw.Draw(sheet)
        for j,a in enumerate(chunk):
            p=COV/f'{a["key"]}.jpg'; im=Image.open(p).convert("RGB")
            im.thumbnail((250,330),Image.Resampling.LANCZOS)
            col=j%5;row=j//5;x=col*300+(300-im.width)//2;y=row*400+10
            sheet.paste(im,(x,y))
            d.text((col*300+8,row*400+345),a["label"],fill="black",font=font)
            d.text((col*300+8,row*400+362),a["method"],fill="black",font=font)
        sheet.save(OUT/f'contact_{mag.lower().replace(" ","_")}_{pg+1}.jpg',"JPEG",quality=88)

print("AUDIT",len(audit),"UNRESOLVED",len(unresolved),unresolved)
