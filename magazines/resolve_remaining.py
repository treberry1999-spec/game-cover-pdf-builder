import requests,re,json,io,time,calendar
from pathlib import Path
from urllib.parse import quote_plus,urljoin
from bs4 import BeautifulSoup
from PIL import Image,ImageDraw,ImageFont

S=requests.Session()
S.headers.update({"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/152 Safari/537.36"})
OUT=Path("magazine_output/remaining")
COV=OUT/"covers"; COV.mkdir(parents=True,exist_ok=True)

SOURCE=[100,102,112,113,116,117,118,119,121,123,126,127,160,166,167]
VIBE=[
(1,"#1","September 1993","Snoop Dogg",["snoop","dogg"]),
(2,"#2","October 1993","Wesley Snipes",["wesley","snipes"]),
(3,"1994 - 2Pac","February 1994","2Pac Tupac",["2pac","tupac"]),
(4,"1994 - Ice Cube","March 1994","Ice Cube",["ice","cube"]),
(5,"1994 - Prince","August 1994","Prince",["prince"]),
(6,"1994 - Janet Jackson","October 1994","Janet Jackson",["janet","jackson"]),
(7,"1995 - Mary J. Blige","February 1995","Mary J Blige",["mary","blige"]),
(8,"1995 - 2Pac","April 1995","2Pac Tupac",["2pac","tupac"]),
(9,"1995 - Michael Jackson","June July 1995","Michael Jackson",["michael","jackson"]),
(10,"1995 - Biggie & Faith Evans","October 1995","Biggie Faith Evans",["biggie","faith"]),
(11,"1996 - Death Row","February 1996","Death Row Tupac Snoop Dr Dre Suge Knight",["death","row"]),
(12,"1996 - Mariah Carey","April 1996","Mariah Carey",["mariah","carey"]),
(13,"May 1996 - Bone Thugs-N-Harmony","May 1996","Bone Thugs-N-Harmony",["bone","thugs"]),
(14,"1996 - Fugees","June July 1996","Fugees",["fugees"]),
(15,"1996 - Dream Team II","August 1996","Dream Team Olympic basketball",["dream","team"]),
(16,"1996 - Biggie & Puff Daddy","September 1996","Biggie Puff Daddy",["biggie","puff"]),
(17,"1997 - Wu-Tang Clan","September 1997","Wu-Tang Clan",["wu","tang"]),
(18,"1997 - The Notorious B.I.G.","May 1997","Notorious BIG Biggie",["biggie","notorious"]),
(19,"1997 - Janet Jackson","November 1997","Janet Jackson",["janet","jackson"]),
(20,"1997 - Erykah Badu","August 1997","Erykah Badu",["erykah","badu"]),
(21,"1997 - Toni Braxton","June July 1997","Toni Braxton",["toni","braxton"]),
(22,"1997 - Michael Jordan / Chris Rock","February 1997","Michael Jordan Chris Rock",["jordan","chris","rock"]),
(23,"1998 - Rap Reigns","February 1998","Rap Reigns",["rap","reigns"]),
(24,"1999 - Biggie / 2Pac","October 1999","Biggie Tupac 2Pac",["biggie","tupac"]),
(25,"2000 - Q-Tip","March 2000","Q-Tip",["tip"]),
(26,"2000 - Jay-Z","December 2000","Jay-Z",["jay"]),
(27,"2002 - Alicia Keys","September 2002","Alicia Keys",["alicia","keys"]),
(28,"2003 - Jay-Z","January 2003","Jay-Z",["jay"]),
(29,"2003 - The Neptunes / Timbaland / Missy Elliott","September 2003","The Neptunes Timbaland Missy Elliott",["neptunes","timbaland","missy"]),
(30,"2004 - Alicia Keys","March 2004","Alicia Keys",["alicia","keys"]),
(31,"2004 - Shyne","September 2004","Shyne",["shyne"]),
(32,"2006 - Eminem / 50 Cent","December 2006","Eminem 50 Cent",["eminem","50"]),
(33,"2006 - Allen Iverson","March 2006","Allen Iverson",["iverson"]),
(34,"2006 - Keyshia Cole","August 2006","Keyshia Cole",["keyshia","cole"]),
]

def norm(s): return re.sub(r"[^a-z0-9]+"," ",(s or "").lower()).strip()

def get(url,**kw):
    r=S.get(url,timeout=50,**kw); r.raise_for_status(); return r

def fetch_img(url,referer=None):
    if not url:return None
    try:
        r=S.get(url,headers={"Referer":referer or "https://www.google.com/"},timeout=60)
        if r.status_code!=200 or len(r.content)<5000:return None
        im=Image.open(io.BytesIO(r.content)); im.load(); im=im.convert("RGB")
        if im.width<180 or im.height<220:return None
        return im
    except Exception:return None

def save(key,im):
    # keep full cover but normalize size
    if im.width/im.height>1.08:
        # don't accept obvious landscape/montage
        return None
    im.thumbnail((1100,1500),Image.Resampling.LANCZOS)
    p=COV/f"{key}.jpg"; im.save(p,"JPEG",quality=89,optimize=True)
    return p

def bing_web(q):
    url="https://www.bing.com/search?q="+quote_plus(q)+"&count=30"
    r=get(url)
    soup=BeautifulSoup(r.text,"html.parser")
    out=[]
    for li in soup.select("li.b_algo"):
        a=li.find("a",href=True)
        if not a:continue
        title=a.get_text(" ",strip=True)
        sn=li.get_text(" ",strip=True)
        out.append({"url":a["href"],"title":title,"text":sn})
    return out

def bing_images(q):
    url="https://www.bing.com/images/async?q="+quote_plus(q)+"&async=1&first=1&count=50"
    r=get(url)
    soup=BeautifulSoup(r.text,"html.parser")
    out=[]
    for a in soup.select("a.iusc"):
        try:m=json.loads(a.get("m") or "{}")
        except:continue
        if m.get("murl"):out.append(m)
    return out

def page_og(url):
    try:
        r=get(url)
        s=BeautifulSoup(r.text,"html.parser")
        title=(s.find("meta",property="og:title") or {}).get("content") if s.find("meta",property="og:title") else ""
        img=(s.find("meta",property="og:image") or {}).get("content") if s.find("meta",property="og:image") else ""
        return title or (s.title.get_text(" ",strip=True) if s.title else ""),img,r.url
    except Exception:return "","",url

def source_date(n):
    # Issue 100 was Jan 1998; Source generally monthly thereafter.
    k=n-100
    y=1998+k//12
    m=1+k%12
    return f"{calendar.month_name[m]} {y}"

def resolve_product_page(query,required_tokens,year=None):
    # restrict to known magazine resale/reference sites
    sites=["rapzines.com/product-page","rapstylearcheology.com/products"]
    candidates=[]
    for site in sites:
        try: rows=bing_web(f'site:{site} "{query}"')
        except Exception: rows=[]
        for rank,x in enumerate(rows):
            blob=norm(x["title"]+" "+x["text"]+" "+x["url"])
            score=100-rank
            hits=sum(1 for t in required_tokens if norm(t) in blob)
            score+=hits*35
            if year and str(year) in blob: score+=25
            if "vibe" in norm(query) and "vibe" in blob:score+=35
            if "source" in norm(query) and "source" in blob:score+=35
            candidates.append((score,x))
    for score,x in sorted(candidates,key=lambda z:z[0],reverse=True)[:10]:
        title,img,url=page_og(x["url"])
        blob=norm(title+" "+x["text"]+" "+url)
        hits=sum(1 for t in required_tokens if norm(t) in blob)
        if hits<max(1,min(2,len(required_tokens))): continue
        im=fetch_img(img,url)
        if im is not None and im.height>im.width*1.05:
            return im,{"method":"product-page","score":score,"title":title,"page_url":url,"image_url":img}
    return None,None

def resolve_images(query,required_tokens,year=None,mag=None,issue=None):
    try: cs=bing_images(query)
    except Exception as e:
        print("IMAGE SEARCH ERR",query,e);return None,None
    scored=[]
    for rank,c in enumerate(cs):
        blob=norm(" ".join([c.get("purl",""),c.get("desc",""),c.get("t",""),c.get("murl","")]))
        score=100-rank
        if mag and mag.lower() in blob: score+=45
        hits=sum(1 for t in required_tokens if norm(t) in blob)
        score+=hits*35
        if year and str(year) in blob:score+=25
        if issue and re.search(rf"\b{issue}\b",blob):score+=75
        scored.append((score,c,blob,hits))
    for score,c,blob,hits in sorted(scored,key=lambda z:z[0],reverse=True)[:18]:
        if hits<max(1,min(2,len(required_tokens))):continue
        im=fetch_img(c.get("murl"),c.get("purl"))
        if im is None:continue
        if im.height<=im.width*1.05:continue
        return im,{"method":"bing-image","score":score,"title":c.get("desc") or c.get("t",""),"page_url":c.get("purl"),"image_url":c.get("murl")}
    return None,None

audit=[];unresolved=[]

# Source missing list
for n in SOURCE:
    key=f"source_{n:03d}"
    date=source_date(n)
    req=[str(n)]
    q=f'The Source magazine issue {n} {date}'
    im,meta=resolve_product_page(q,req,year=int(date[-4:]))
    if im is None:
        im,meta=resolve_images(q,req,year=int(date[-4:]),mag="source",issue=n)
    if im is not None and save(key,im):
        meta.update({"key":key,"mag":"THE SOURCE","label":f"#{n}","query":q})
        audit.append(meta);print("SOURCE SAVED",n,meta["method"],meta.get("title"))
    else:
        unresolved.append({"key":key,"mag":"THE SOURCE","label":f"#{n}","query":q});print("SOURCE UNRESOLVED",n)
    time.sleep(.15)

for idx,label,date,subject,toks in VIBE:
    key=f"vibe_{idx:02d}"
    # no need overwrite existing if this workflow is later merged, but resolve all consistently
    year=int(re.findall(r"\d{4}",date)[0])
    q=f'VIBE magazine {date} {subject} cover'
    im,meta=resolve_product_page(q,toks,year=year)
    if im is None:
        im,meta=resolve_images(q,toks,year=year,mag="vibe")
    if im is not None and save(key,im):
        meta.update({"key":key,"mag":"VIBE","label":label,"date":date,"subject":subject,"query":q})
        audit.append(meta);print("VIBE SAVED",idx,label,meta["method"],meta.get("title"))
    else:
        unresolved.append({"key":key,"mag":"VIBE","label":label,"date":date,"subject":subject,"query":q});print("VIBE UNRESOLVED",idx,label)
    time.sleep(.15)

# XXL Summer Jam 2004 Special
key="xxl_22"
q='XXL Magazine Summer Jam 2004 Special cover'
im,meta=resolve_product_page(q,["summer","jam"],year=2004)
if im is None: im,meta=resolve_images(q,["summer","jam"],year=2004,mag="xxl")
if im is not None and save(key,im):
    meta.update({"key":key,"mag":"XXL","label":"Summer Jam 2004 Special","query":q});audit.append(meta)
else:
    unresolved.append({"key":key,"mag":"XXL","label":"Summer Jam 2004 Special","query":q})

(OUT/"audit.json").write_text(json.dumps(audit,indent=2))
(OUT/"unresolved.json").write_text(json.dumps(unresolved,indent=2))

# contact sheets
font=ImageFont.load_default()
for mag in ["THE SOURCE","VIBE","XXL"]:
    arr=[a for a in audit if a["mag"]==mag]
    for pg in range((len(arr)+19)//20):
        chunk=arr[pg*20:(pg+1)*20]
        sheet=Image.new("RGB",(1500,1600),"white");d=ImageDraw.Draw(sheet)
        for j,a in enumerate(chunk):
            im=Image.open(COV/f'{a["key"]}.jpg').convert("RGB"); im.thumbnail((250,330),Image.Resampling.LANCZOS)
            col=j%5; row=j//5; x=col*300+(300-im.width)//2; y=row*400+10
            sheet.paste(im,(x,y))
            d.text((col*300+8,row*400+345),a["label"],fill="black",font=font)
            d.text((col*300+8,row*400+363),a["method"],fill="black",font=font)
        sheet.save(OUT/f'contact_{mag.lower().replace(" ","_")}_{pg+1}.jpg',"JPEG",quality=88)
print("DONE",len(audit),"resolved",len(unresolved),"unresolved")
print("UNRESOLVED",json.dumps(unresolved))
