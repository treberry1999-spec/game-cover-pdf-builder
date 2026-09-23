import requests,re,json,io,time
from pathlib import Path
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor,as_completed
from bs4 import BeautifulSoup
from PIL import Image,ImageDraw,ImageFont

S=requests.Session()
S.headers.update({"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/152 Safari/537.36"})
OUT=Path("magazine_output/rapzines_crawl"); COV=OUT/"covers"; COV.mkdir(parents=True,exist_ok=True)

def get(url):
    r=S.get(url,timeout=60); r.raise_for_status(); return r

def norm(s): return re.sub(r"[^a-z0-9]+"," ",(s or "").lower()).strip()

# Crawl all shop pages and collect product URLs/titles.
products={}
def crawl_page(page):
    url=f"https://www.rapzines.com/shop?page={page}"
    try:
        r=get(url); soup=BeautifulSoup(r.text,"html.parser")
        rows=[]
        for a in soup.find_all("a",href=True):
            href=urljoin(r.url,a["href"])
            if "/product-page/" not in href: continue
            txt=" ".join(a.stripped_strings)
            if href not in products:
                rows.append((href,txt))
        return page,rows
    except Exception as e:
        return page,[]

with ThreadPoolExecutor(max_workers=12) as ex:
    futs=[ex.submit(crawl_page,p) for p in range(1,62)]
    for f in as_completed(futs):
        page,rows=f.result()
        for u,t in rows:
            if u not in products or len(t)>len(products[u]): products[u]=t
        print("PAGE",page,"ROWS",len(rows))

# Keep relevant URLs based on URL slug or link text.
relevant=[]
for u,t in products.items():
    blob=norm(u+" "+t)
    if "vibe magazine" in blob or "the source" in blob or ("xxl magazine" in blob and "summer jam" in blob):
        relevant.append((u,t))
print("RELEVANT LINKS",len(relevant))

def fetch_product(item):
    u,linktext=item
    try:
        r=get(u); s=BeautifulSoup(r.text,"html.parser")
        def meta(prop):
            m=s.find("meta",property=prop)
            return m.get("content","") if m else ""
        title=meta("og:title") or (s.title.get_text(" ",strip=True) if s.title else linktext)
        img=meta("og:image")
        return {"url":r.url,"title":title,"image":img,"linktext":linktext}
    except Exception:
        return None

records=[]
with ThreadPoolExecutor(max_workers=12) as ex:
    futs=[ex.submit(fetch_product,x) for x in relevant]
    for f in as_completed(futs):
        x=f.result()
        if x and x["image"]: records.append(x)
print("PRODUCT RECORDS",len(records))
(OUT/"product_index.json").write_text(json.dumps(records,indent=2))

# Target maps
SOURCE=[100,102,112,113,116,117,118,119,121,123,126,127,160,166,167]
VIBE=[
(1,"#1","September 1993","Snoop Dogg",["september","1993","snoop"]),
(2,"#2","October 1993","Wesley Snipes",["october","1993","wesley"]),
(3,"1994 - 2Pac","February 1994","2Pac",["february","1994","tupac"]),
(4,"1994 - Ice Cube","March 1994","Ice Cube",["march","1994","ice","cube"]),
(5,"1994 - Prince","August 1994","Prince",["august","1994","prince"]),
(6,"1994 - Janet Jackson","October 1994","Janet Jackson",["october","1994","janet"]),
(7,"1995 - Mary J. Blige","February 1995","Mary J. Blige",["february","1995","mary","blige"]),
(8,"1995 - 2Pac","April 1995","2Pac",["april","1995","tupac"]),
(9,"1995 - Michael Jackson","June/July 1995","Michael Jackson",["1995","michael","jackson"]),
(10,"1995 - Biggie & Faith Evans","October 1995","Biggie & Faith Evans",["october","1995","faith"]),
(11,"1996 - Death Row","February 1996","Death Row",["february","1996","death","row"]),
(12,"1996 - Mariah Carey","April 1996","Mariah Carey",["april","1996","mariah"]),
(13,"May 1996 - Bone Thugs-N-Harmony","May 1996","Bone Thugs-N-Harmony",["may","1996","bone"]),
(14,"1996 - Fugees","June/July 1996","Fugees",["1996","fugees"]),
(15,"1996 - Dream Team II","August 1996","Dream Team II",["august","1996","dream","team"]),
(16,"1996 - Biggie & Puff Daddy","September 1996","Biggie & Puff Daddy",["september","1996","biggie"]),
(17,"1997 - Wu-Tang Clan","September 1997","Wu-Tang Clan",["september","1997","wu","tang"]),
(18,"1997 - The Notorious B.I.G.","May 1997","The Notorious B.I.G.",["may","1997","notorious"]),
(19,"1997 - Janet Jackson","November 1997","Janet Jackson",["november","1997","janet"]),
(20,"1997 - Erykah Badu","August 1997","Erykah Badu",["august","1997","erykah"]),
(21,"1997 - Toni Braxton","June/July 1997","Toni Braxton",["1997","toni","braxton"]),
(22,"1997 - Michael Jordan / Chris Rock","February 1997","Michael Jordan & Chris Rock",["february","1997","jordan","rock"]),
(23,"1998 - Rap Reigns","February 1998","Rap Reigns",["february","1998","rap","reigns"]),
(24,"1999 - Biggie / 2Pac","October 1999","Biggie / 2Pac",["october","1999","tupac","biggie"]),
(25,"2000 - Q-Tip","March 2000","Q-Tip",["march","2000","tip"]),
(26,"2000 - Jay-Z","December 2000","Jay-Z",["december","2000","jay"]),
(27,"2002 - Alicia Keys","September 2002","Alicia Keys",["september","2002","alicia"]),
(28,"2003 - Jay-Z","January 2003","Jay-Z",["january","2003","jay"]),
(29,"2003 - The Neptunes / Timbaland / Missy Elliott","September 2003","The Neptunes / Timbaland / Missy Elliott",["september","2003","timbaland","missy"]),
(30,"2004 - Alicia Keys","March 2004","Alicia Keys",["march","2004","alicia"]),
(31,"2004 - Shyne","September 2004","Shyne",["september","2004","shyne"]),
(32,"2006 - Eminem / 50 Cent","December 2006","Eminem / 50 Cent",["december","2006","eminem","50"]),
(33,"2006 - Allen Iverson","March 2006","Allen Iverson",["march","2006","iverson"]),
(34,"2006 - Keyshia Cole","August 2006","Keyshia Cole",["august","2006","keyshia"]),
]

def dl_image(url):
    try:
        r=S.get(url,timeout=60)
        if r.status_code!=200 or len(r.content)<5000:return None
        im=Image.open(io.BytesIO(r.content));im.load();return im.convert("RGB")
    except Exception:return None

def save(key,rec):
    im=dl_image(rec["image"])
    if im is None:return False
    im.thumbnail((1200,1600),Image.Resampling.LANCZOS)
    im.save(COV/f"{key}.jpg","JPEG",quality=90,optimize=True)
    return True

def score_tokens(rec,toks,magword):
    b=norm(rec["title"]+" "+rec["url"]+" "+rec["linktext"])
    if magword not in b:return -999
    sc=0
    for t in toks:
        if norm(t) in b:sc+=25
    return sc

audit=[];unresolved=[]
# Source matching: issue number in title/URL
for n in SOURCE:
    candidates=[]
    for r in records:
        b=norm(r["title"]+" "+r["url"]+" "+r["linktext"])
        if "source" not in b:continue
        # recognize source #117, source 117, issue 117 etc
        if re.search(rf"\b(?:source|issue|no|number)\s*0*{n}\b",b) or re.search(rf"\b0*{n}\b",b):
            candidates.append((100,r))
    if candidates:
        rec=candidates[0][1]
        if save(f"source_{n:03d}",rec):
            audit.append({"key":f"source_{n:03d}","label":f"#{n}","mag":"THE SOURCE",**rec})
            print("SOURCE",n,rec["title"]);continue
    unresolved.append({"key":f"source_{n:03d}","label":f"#{n}","mag":"THE SOURCE"})

# VIBE exact token matching
for idx,label,date,subject,toks in VIBE:
    ranked=[]
    for r in records:
        sc=score_tokens(r,toks,"vibe")
        if sc<0:continue
        # extra subject synonyms
        b=norm(r["title"]+" "+r["url"])
        if idx in (3,8,24) and ("2pac" in b or "tupac" in b):sc+=25
        if idx in (10,16,18,24) and ("biggie" in b or "notorious" in b):sc+=20
        ranked.append((sc,r))
    ranked.sort(key=lambda x:x[0],reverse=True)
    # require most of date/subject tokens
    if ranked and ranked[0][0]>=75:
        rec=ranked[0][1]
        if save(f"vibe_{idx:02d}",rec):
            audit.append({"key":f"vibe_{idx:02d}","label":label,"mag":"VIBE","date":date,"subject":subject,"match_score":ranked[0][0],**rec})
            print("VIBE",idx,label,ranked[0][0],rec["title"]);continue
    unresolved.append({"key":f"vibe_{idx:02d}","label":label,"mag":"VIBE","date":date,"subject":subject,
                       "top":[{"score":s,"title":r["title"],"url":r["url"]} for s,r in ranked[:5]]})

# XXL Summer Jam
ranked=[]
for r in records:
    b=norm(r["title"]+" "+r["url"])
    if "xxl" in b and "summer" in b and "jam" in b and "2004" in b:
        ranked.append(r)
if ranked and save("xxl_22",ranked[0]):
    audit.append({"key":"xxl_22","label":"Summer Jam 2004 Special","mag":"XXL",**ranked[0]})
else:
    unresolved.append({"key":"xxl_22","label":"Summer Jam 2004 Special","mag":"XXL"})

(OUT/"audit.json").write_text(json.dumps(audit,indent=2))
(OUT/"unresolved.json").write_text(json.dumps(unresolved,indent=2))
# make one contact sheet for resolved items
font=ImageFont.load_default()
for mag in ["THE SOURCE","VIBE","XXL"]:
    arr=[a for a in audit if a["mag"]==mag]
    for pg in range((len(arr)+19)//20):
        chunk=arr[pg*20:(pg+1)*20]
        sheet=Image.new("RGB",(1500,1600),"white");d=ImageDraw.Draw(sheet)
        for j,a in enumerate(chunk):
            im=Image.open(COV/f'{a["key"]}.jpg').convert("RGB");im.thumbnail((250,330),Image.Resampling.LANCZOS)
            col=j%5;row=j//5;x=col*300+(300-im.width)//2;y=row*400+10
            sheet.paste(im,(x,y));d.text((col*300+8,row*400+345),a["label"],fill="black",font=font)
        sheet.save(OUT/f'contact_{mag.lower().replace(" ","_")}_{pg+1}.jpg',"JPEG",quality=88)
print("TOTAL PRODUCTS",len(products),"RELEVANT",len(records),"RESOLVED",len(audit),"UNRESOLVED",len(unresolved))
print(json.dumps(unresolved,indent=2))
