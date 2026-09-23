import requests,io,json,re,math
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from bs4 import BeautifulSoup

OUT=Path("magazine_output/vibe_authoritative")
COV=OUT/"covers"
OUT.mkdir(parents=True,exist_ok=True);COV.mkdir(exist_ok=True)
S=requests.Session();S.headers.update({"User-Agent":"Mozilla/5.0 Chrome/152 Safari/537.36"})

# Exact BuzzFeed retrospective image URLs + captions. These map directly to the user's VIBE selections.
M={
"vibe_01":("VIBE","#1","Snoop Dogg - September 1993","https://img.buzzfeed.com/buzzfeed-static/static/enhanced/webdr06/2013/5/14/15/enhanced-buzz-13616-1368559246-30.jpg?downsize=1400:*&output-format=jpg&output-quality=95"),
"vibe_03":("VIBE","1994 - 2Pac","Tupac Shakur - February 1994","https://img.buzzfeed.com/buzzfeed-static/static/enhanced/webdr06/2013/5/14/15/enhanced-buzz-12077-1368559480-20.jpg?downsize=1400:*&output-format=jpg&output-quality=95"),
"vibe_04":("VIBE","1994 - Ice Cube","Ice Cube - March 1994","https://img.buzzfeed.com/buzzfeed-static/static/enhanced/webdr03/2013/5/14/15/enhanced-buzz-30877-1368559665-7.jpg?downsize=1400:*&output-format=jpg&output-quality=95"),
"vibe_05":("VIBE","1994 - Prince","Prince - August 1994","https://img.buzzfeed.com/buzzfeed-static/static/enhanced/webdr03/2013/5/14/15/enhanced-buzz-29715-1368559621-6.jpg?downsize=1400:*&output-format=jpg&output-quality=95"),
"vibe_07":("VIBE","1995 - Mary J. Blige","Mary J. Blige - February 1995","https://img.buzzfeed.com/buzzfeed-static/static/enhanced/webdr01/2013/5/14/15/enhanced-buzz-31465-1368560741-14.jpg?downsize=1400:*&output-format=jpg&output-quality=95"),
"vibe_08":("VIBE","1995 - 2Pac","Tupac Shakur - April 1995","https://img.buzzfeed.com/buzzfeed-static/static/enhanced/webdr05/2013/5/14/15/enhanced-buzz-23356-1368560176-9.jpg?downsize=1400:*&output-format=jpg&output-quality=95"),
"vibe_09":("VIBE","1995 - Michael Jackson","Michael Jackson - June/July 1995","https://img.buzzfeed.com/buzzfeed-static/static/enhanced/webdr02/2013/5/14/15/enhanced-buzz-17579-1368559587-19.jpg?downsize=1400:*&output-format=jpg&output-quality=95"),
"vibe_10":("VIBE","1995 - Biggie & Faith Evans","The Notorious B.I.G. & Faith Evans - October 1995","https://img.buzzfeed.com/buzzfeed-static/static/enhanced/webdr05/2013/5/14/15/enhanced-buzz-orig-22925-1368560099-9.jpg?downsize=1400:*&output-format=jpg&output-quality=95"),
"vibe_11":("VIBE","1996 - Death Row","Snoop/Dre/2Pac/Suge - February 1996","https://img.buzzfeed.com/buzzfeed-static/static/enhanced/webdr06/2013/5/10/2/enhanced-buzz-7207-1368168044-14.jpg?downsize=1400:*&output-format=jpg&output-quality=95"),
"vibe_15":("VIBE","1996 - Dream Team II","Dream Team II - August 1996","https://img.buzzfeed.com/buzzfeed-static/static/enhanced/webdr02/2013/5/14/15/enhanced-buzz-8644-1368559789-8.jpg?downsize=1400:*&output-format=jpg&output-quality=95"),
"vibe_16":("VIBE","1996 - Biggie & Puff Daddy","Biggie & Puffy - September 1996","https://img.buzzfeed.com/buzzfeed-static/static/enhanced/webdr03/2013/5/14/15/enhanced-buzz-29561-1368559170-5.jpg?downsize=1400:*&output-format=jpg&output-quality=95"),
"vibe_18":("VIBE","1997 - The Notorious B.I.G.","The Notorious B.I.G. - May 1997","https://img.buzzfeed.com/buzzfeed-static/static/enhanced/webdr02/2013/5/14/15/enhanced-buzz-17599-1368559726-9.jpg?downsize=1400:*&output-format=jpg&output-quality=95"),
"vibe_19":("VIBE","1997 - Janet Jackson","Janet Jackson - November 1997","https://img.buzzfeed.com/buzzfeed-static/static/enhanced/webdr01/2013/5/14/15/enhanced-buzz-31517-1368559450-0.jpg?downsize=1400:*&output-format=jpg&output-quality=95"),
"vibe_22":("VIBE","1997 - Michael Jordan / Chris Rock","Chris Rock & Michael Jordan - February 1997","https://img.buzzfeed.com/buzzfeed-static/static/enhanced/webdr02/2013/5/14/19/enhanced-buzz-orig-18437-1368575202-10.jpg?downsize=1400:*&output-format=jpg&output-quality=95"),
"vibe_23":("VIBE","1998 - Rap Reigns","Rap Reigns - February 1998","https://img.buzzfeed.com/buzzfeed-static/static/enhanced/webdr06/2013/5/14/19/enhanced-buzz-orig-418-1368572561-20.jpg?downsize=1400:*&output-format=jpg&output-quality=95"),
}

audit=[];bad=[]
for key,(mag,label,title,url) in M.items():
    try:
        r=S.get(url,timeout=60);r.raise_for_status()
        im=Image.open(io.BytesIO(r.content));im.load();im=im.convert("RGB")
        if im.width<200 or im.height<250:raise RuntimeError(f"too small {im.size}")
        im.thumbnail((1200,1650),Image.Resampling.LANCZOS)
        p=COV/f"{key}.jpg";im.save(p,"JPEG",quality=90,optimize=True,progressive=True)
        audit.append({"key":key,"mag":mag,"label":label,"title":title,"source":"BuzzFeed retrospective","url":url,"file":p.name,"w":im.width,"h":im.height})
        print("SAVED",key,label,im.size)
    except Exception as e:
        bad.append({"key":key,"label":label,"error":repr(e)});print("ERR",key,e)

# Pull Q-Tip March 2000 and Jay-Z December 2000 from the Rapzines archive page using alt/product ordering.
archive="https://www.rapzines.com/copy-of-xxl"
try:
    r=S.get(archive,timeout=60);r.raise_for_status()
    soup=BeautifulSoup(r.text,"html.parser")
    html=r.text
    targets={
      "vibe_25":("2000 - Q-Tip",["march 2000","q-tip","q tip"]),
      "vibe_26":("2000 - Jay-Z",["december 2000","jay-z","jay z"]),
    }
    # Extract Wix media URLs and nearby context from img tags / JSON-ish source
    imgs=[]
    for im in soup.find_all("img"):
        text=" ".join(filter(None,[im.get("alt",""),im.get("title","")]))
        urls=[]
        for attr in ["src","data-src","srcset"]:
            val=im.get(attr) or ""
            for part in val.split(","):
                u=part.strip().split(" ")[0]
                if u.startswith("http"):urls.append(u)
        if urls:imgs.append((text,urls))
    for key,(label,toks) in targets.items():
        picked=None
        for txt,urls in imgs:
            low=txt.lower()
            if any(t in low for t in toks):
                for u in reversed(urls):
                    try:
                        rr=S.get(u,timeout=60)
                        if rr.status_code!=200 or len(rr.content)<5000:continue
                        im=Image.open(io.BytesIO(rr.content));im.load();im=im.convert("RGB")
                        if im.width<180 or im.height<250:continue
                        picked=(u,im,txt);break
                    except:pass
            if picked:break
        # fallback: find media URLs near exact text in raw HTML
        if not picked:
            lowhtml=html.lower()
            for tok in toks:
                pos=lowhtml.find(tok)
                if pos<0:continue
                chunk=html[max(0,pos-10000):pos+10000]
                urls=re.findall(r'https://static\.wixstatic\.com/media/[^"\\\\ ]+',chunk)
                for u in urls:
                    u=u.replace("\\/","/").replace("\\u0026","&")
                    try:
                        rr=S.get(u,timeout=60)
                        if rr.status_code!=200 or len(rr.content)<5000:continue
                        im=Image.open(io.BytesIO(rr.content));im.load();im=im.convert("RGB")
                        if im.width<180 or im.height<250:continue
                        picked=(u,im,tok);break
                    except:pass
                if picked:break
        if picked:
            u,im,txt=picked
            im.thumbnail((1200,1650),Image.Resampling.LANCZOS)
            p=COV/f"{key}.jpg";im.save(p,"JPEG",quality=90,optimize=True)
            audit.append({"key":key,"mag":"VIBE","label":label,"title":txt,"source":"Rapzines archive","url":u,"file":p.name,"w":im.width,"h":im.height})
            print("SAVED ARCHIVE",key,label,im.size,txt)
        else:bad.append({"key":key,"label":label,"error":"archive image not found"})
except Exception as e: print("ARCHIVE ERR",e)

(OUT/"audit.json").write_text(json.dumps(audit,indent=2))
(OUT/"unresolved.json").write_text(json.dumps(bad,indent=2))
print("SAVED",len(audit),"BAD",len(bad))

font=ImageFont.load_default()
sheet=Image.new("RGB",(1500,1600),"white");d=ImageDraw.Draw(sheet)
for j,a in enumerate(audit[:20]):
    im=Image.open(COV/a["file"]).convert("RGB");im.thumbnail((250,330),Image.Resampling.LANCZOS)
    col=j%5;row=j//5;x=col*300+(300-im.width)//2;y=row*400+10;sheet.paste(im,(x,y))
    d.text((col*300+8,row*400+345),a["label"][:42],fill="black",font=font)
sheet.save(OUT/"contact.jpg","JPEG",quality=88)
