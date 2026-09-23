import requests,re,json,io,math
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image,ImageDraw,ImageFont

OUT=Path("magazine_output/rapzines_exact")
COV=OUT/"covers"
OUT.mkdir(parents=True,exist_ok=True);COV.mkdir(exist_ok=True)
S=requests.Session()
S.headers.update({"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/152 Safari/537.36"})

M={}

def add(key,mag,label,slug):
    M[key]={"mag":mag,"label":label,"url":"https://www.rapzines.com/product-page/"+slug}

# THE SOURCE exact requested matches
for n,slug in {
100:"the-source-100-ll-cool-j",102:"the-source-102-the-lox-mase",103:"the-source-103-snoop-dogg",
105:"the-source-105-dmx-kurupt-silkk",106:"the-source-106-master-p-1",107:"the-source-107c-def-squad-variant",
108:"the-source-108-lauryn-hill",110:"the-source-110-bizzy-bone",111:"the-source-111-method-man-redman",
113:"the-source-113-puffy-russell-simmons-master-p",117:"the-source-117-snoop-dogg-1",119:"the-source-119-dr-dre",
122:"the-source-122-a-mos-def-black-thought-pharoahe-monch-variant-cover",125:"the-source-125-a-dmx-variant-cover",
126:"the-source-126-rza-ghostface",128:"the-source-128-big-pun",130:"the-source-130-eminem",
134:"the-source-134-scarface",135:"the-source-135-eve",142:"the-source-142-2001-summer-preview",
148:"the-source-148-outkast",150:"the-source-150",152:"the-source-152-eminem",
156:"the-source-156a-jay-z-beanie-sigel",160:"the-source-160-baby",163:"the-source-163a-snoop-dogg",
166:"the-source-166-ashanti",167:"the-source-167-15th-anniversary",169:"the-source-169-50-cent",
175:"the-source-175-kanye-west",185:"the-source-185-jay-z-damon-dash"
}.items(): add(f"source_{n:03d}","THE SOURCE",f"#{n}",slug)

# VIBE requested matches
for key,label,slug in [
("vibe_04","1994 - Ice Cube","vibe-magazine-march-1994-ice-cube"),
("vibe_18","1997 - The Notorious B.I.G.","vibe-magazine-may-1997-notorious-b-i-g"),
("vibe_22","1997 - Michael Jordan / Chris Rock","vibe-magazine-february-1997-michael-jordan-chris-rock"),
("vibe_24","1999 - Biggie / 2Pac","vibe-magazine-october-1999-tupac-shakur-2pac-notorious-b-i-g"),
("vibe_27","2002 - Alicia Keys","vibe-magazine-sept-2002-alicia-keys"),
("vibe_28","2003 - Jay-Z","vibe-magazine-jan-2003-jay-z"),
("vibe_29","2003 - The Neptunes / Timbaland / Missy Elliott","vibe-magazine-sept-2003-7-10-timbaland-missy-elliott-the-neptunes"),
("vibe_30","2004 - Alicia Keys","vibe-magazine-march-2004-alicia-keys"),
("vibe_31","2004 - Shyne","vibe-magazine-sept-2004-shyne"),
("vibe_33","2006 - Allen Iverson","vibe-magazine-march-2006-allen-iverson"),
("vibe_34","2006 - Keyshia Cole","vibe-magazine-august-2006-keyshia-cole"),
("vibe_32","2006 - Eminem / 50 Cent","vibe-magazine-eminem-50-cent"),
]: add(key,"VIBE",label,slug)

# XXL requested exact matches. A/B suffixes preserved where explicitly requested.
for key,label,slug in [
("xxl_01","#0 - Preview Issue","xxl-magazine-0-preview-issue-notorious-b-i-g"),
("xxl_02","#2 - Cover A","xxl-magazine-02-redman"),
("xxl_03","#2 - Cover B","xxl-magazine-02-too-short-variant"),
("xxl_04","#3","xxl-magazine-3-goodie-mob"),
("xxl_05","#6 - Busta Rhymes","xxl-magazine-6-busta-rhymes"),
("xxl_07","#13","xxl-magazine-13-dmx"),
("xxl_08","#16","xxl-magazine-16-snoop-dogg"),
("xxl_09","#17","xxl-magazine-17-eminem"),
("xxl_10","#22","xxl-magazine-22-dmx"),
("xxl_11","#23","xxl-magazine-23-hot-boys-1"),
("xxl_12","#24","xxl-magazine-24-nas"),
("xxl_13","#25","xxl-magazine-25-nelly"),
("xxl_14","#29","xxl-magazine-29-juvenile"),
("xxl_15","#32","xxl-magazine-32-ludacris"),
("xxl_16","#34","xxl-magazine-34-wu-tang-clan-1"),
("xxl_18","#43","xxl-magazine-43-jay-z"),
("xxl_19","#49","xxl-magazine-49-foxy-brown"),
("xxl_20","#51","xxl-magazine-51-nas"),
("xxl_21","#63","xxl-magazine-63-dave-chappelle-kanye-west"),
("xxl_22","Summer Jam 2004 Special","xxl-magazine-summer-jam-2004-special"),
("xxl_23","#72","xxl-magazine-72-jay-z-kanye-lebron-foxy"),
("xxl_24","#73","xxl-magazine-73-the-game"),
("xxl_25","#78","xxl-magazine-78-cam-ron"),
("xxl_26","#85","xxl-magazine-85-2pac"),
("xxl_27","#87","xxl-magazine-87-jay-z"),
("xxl_28","#93A","xxl-magazine-93a-t-i-variant"),
("xxl_29","#96","xxl-magazine-96-kanye-west"),
("xxl_30","#97","xxl-magazine-97-saigon-plies-rich-boy-lupe-fiasco-lil-boosie"),
("xxl_31","#98","xxl-magazine-98-jay-z"),
("xxl_32","#99C","xxl-magazine-99c-lil-wayne-variant"),
("xxl_35","#111","xxl-magazine-111-juelz-santana-jim-jones-freekey-zekey"),
("xxl_37","#123","xxl-magazine-123-drake-nicki-minaj"),
("xxl_39","#127","xxl-magazine-127-kanye-west"),
("xxl_43","#134","xxl-magazine-134-lil-wayne"),
("xxl_44","#136","xxl-magazine-136a-rick-ross-variant"),
("xxl_46","#141","xxl-magazine-141-lil-wayne"),
("xxl_47","#146","xxl-magazine-146-b-chris-brown-variant-cover"),
("xxl_53","#154","xxl-magazine-154-freshman-class-2014-lil-durk-kevin-gates"),
("xxl_54","#155","xxl-magazine-155-lil-wayne"),
("xxl_56","#159","xxl-magazine-159-freshman-class-2015-vince-staples"),
("xxl_57","#160","xxl-magazine-160-future"),
]: add(key,"XXL",label,slug)

def pick_image(soup):
    candidates=[]
    for prop in ["og:image","twitter:image","twitter:image:src"]:
        for m in soup.find_all("meta"):
            if (m.get("property") or m.get("name") or "").lower()==prop:
                u=(m.get("content") or "").strip()
                if u:candidates.append(u)
    # Wix often stores high-res product image urls in scripts
    html=str(soup)
    for u in re.findall(r'https://static\.wixstatic\.com/media/[^"\\\\ ]+\.(?:jpg|jpeg|png|webp)[^"\\\\ ]*',html,re.I):
        candidates.append(u.replace("\\u0026","&").replace("\\/","/"))
    # unique
    out=[]
    for u in candidates:
        if u.startswith("//"):u="https:"+u
        if u not in out:out.append(u)
    return out

def fetch_image(url,referer):
    try:
        r=S.get(url,headers={"Referer":referer},timeout=60)
        if r.status_code!=200 or len(r.content)<7000:return None
        im=Image.open(io.BytesIO(r.content));im.load()
        if im.width<250 or im.height<300:return None
        ratio=im.width/im.height
        if ratio<0.42 or ratio>1.10:return None
        return im.convert("RGB")
    except Exception:return None

audit=[];bad=[]
for i,(key,e) in enumerate(M.items(),1):
    print(f"{i}/{len(M)} {key} {e['label']} {e['url']}")
    try:
        r=S.get(e["url"],timeout=60);r.raise_for_status()
        soup=BeautifulSoup(r.text,"html.parser")
        title=(soup.find("meta",property="og:title") or {}).get("content") if soup.find("meta",property="og:title") else ""
        chosen=None
        for u in pick_image(soup):
            im=fetch_image(u,e["url"])
            if im is not None:
                chosen=(u,im);break
        if not chosen:
            bad.append({**e,"key":key,"reason":"no-cover-image"});continue
        u,im=chosen
        im.thumbnail((1200,1650),Image.Resampling.LANCZOS)
        p=COV/f"{key}.jpg";im.save(p,"JPEG",quality=90,optimize=True,progressive=True)
        rec={**e,"key":key,"title":title,"image_url":u,"file":p.name,"w":im.width,"h":im.height}
        audit.append(rec)
        print("SAVED",p,im.size,title)
    except Exception as ex:
        bad.append({**e,"key":key,"reason":repr(ex)})
        print("ERR",ex)

(OUT/"audit.json").write_text(json.dumps(audit,indent=2))
(OUT/"unresolved.json").write_text(json.dumps(bad,indent=2))
print("TOTAL",len(M),"SAVED",len(audit),"BAD",len(bad))

font=ImageFont.load_default()
for mag in ["THE SOURCE","VIBE","XXL"]:
    rs=[a for a in audit if a["mag"]==mag]
    for pg in range(math.ceil(len(rs)/20)):
        chunk=rs[pg*20:(pg+1)*20]
        sheet=Image.new("RGB",(1500,1600),"white");d=ImageDraw.Draw(sheet)
        for j,a in enumerate(chunk):
            im=Image.open(COV/a["file"]).convert("RGB");im.thumbnail((250,330),Image.Resampling.LANCZOS)
            col=j%5;row=j//5;x=col*300+(300-im.width)//2;y=row*400+10;sheet.paste(im,(x,y))
            d.text((col*300+8,row*400+345),a["label"][:42],fill="black",font=font)
            d.text((col*300+8,row*400+360),a["title"][:42],fill="black",font=font)
        sheet.save(OUT/f'contact_{mag.lower().replace(" ","_")}_{pg+1}.jpg',"JPEG",quality=88)
