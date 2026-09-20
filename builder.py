import csv, os, re, json, time, hashlib, urllib.parse, html
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from PIL import Image, ImageOps
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from rapidfuzz import fuzz, process

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"output"; COVERS=ROOT/"covers"; CONSOLES=ROOT/"console_images"
OUT.mkdir(exist_ok=True); COVERS.mkdir(exist_ok=True); CONSOLES.mkdir(exist_ok=True)

DIR_MAP={
"Fairchild Channel F":["Fairchild - Channel F"],
"Atari 2600":["Atari - 2600"],
"Vectrex":["GCE - Vectrex"],
"ColecoVision":["Coleco - ColecoVision"],
"Nintendo Entertainment System":["Nintendo - Nintendo Entertainment System"],
"Super Nintendo Entertainment System":["Nintendo - Super Nintendo Entertainment System"],
"Sega Master System":["Sega - Master System - Mark III"],
"Sega Genesis":["Sega - Mega Drive - Genesis"],
"Sega 32X":["Sega - 32X"],
"Game Boy":["Nintendo - Game Boy"],
"Game Boy Color":["Nintendo - Game Boy Color"],
"Game Boy Advance":["Nintendo - Game Boy Advance"],
"Sega Game Gear":["Sega - Game Gear"],
"TurboGrafx-16 ecosystem (source label)":["NEC - PC Engine - TurboGrafx 16","NEC - PC Engine CD - TurboGrafx-CD"],
"Neo Geo (AES/MVS not specified)":["SNK - Neo Geo"],
"Panasonic 3DO":["The 3DO Company - 3DO"],
"PlayStation":["Sony - PlayStation"],
"Nintendo 64":["Nintendo - Nintendo 64"],
"Sega Saturn":["Sega - Saturn"],
"Sega Dreamcast":["Sega - Dreamcast"],
"PlayStation 2":["Sony - PlayStation 2"],
"Xbox":["Microsoft - Xbox"],
"Nintendo GameCube":["Nintendo - GameCube"],
"Nintendo DS":["Nintendo - Nintendo DS"],
"PlayStation Portable":["Sony - PlayStation Portable"],
"Xbox 360":["Microsoft - Xbox 360"],
"PlayStation 3":["Sony - PlayStation 3"],
"Wii":["Nintendo - Wii"],
"Nintendo 3DS":["Nintendo - Nintendo 3DS"],
"PlayStation 4":["Sony - PlayStation 4"]
}
SKIP_PLATFORMS={"Magnavox Odyssey","Platform Not Specified","TBA","PlayStation 5","Nintendo Switch 2"}
ALIASES={
"Dissidia 012 Final Fantasy":"Dissidia 012 - Duodecim Final Fantasy",
"NBA Inside 09":"NBA 09 - The Inside",
"Outrun 2006":"OutRun 2006 - Coast 2 Coast",
"Pop n Music":"Pop'n Music Portable",
"Sonic 1":"Sonic the Hedgehog","Sonic 2":"Sonic the Hedgehog 2","Golden Axe 2":"Golden Axe II","The Simpsons: Bart vs Space Mutants":"The Simpsons: Bart vs. the Space Mutants",
"Dr Robotonik":"Dr. Robotnik's Mean Bean Machine","Musha":"M.U.S.H.A.",
"MGS2":"Metal Gear Solid 2 - Sons of Liberty","MGS3":"Metal Gear Solid 3 - Snake Eater",
"DMC 1":"Devil May Cry","DMC 2":"Devil May Cry 2","DMC 3":"Devil May Cry 3 - Dante's Awakening",
"DMC 5":"Devil May Cry 5","Final Fantasy 16":"Final Fantasy XVI","Neir":"Nier","Nier Autotmata":"Nier - Automata",
"GTA 3":"Grand Theft Auto III","GTA IV":"Grand Theft Auto IV","Modern Warfare":"Call of Duty 4 - Modern Warfare",
"Modern Warfare 2":"Call of Duty - Modern Warfare 2","Modern Warfare 3":"Call of Duty - Modern Warfare 3",
"Black Ops":"Call of Duty - Black Ops","Blacks Ops II":"Call of Duty - Black Ops II","World At War":"Call of Duty - World at War",
"Megaman":"Mega Man","Megaman 2":"Mega Man 2","Megaman V":"Mega Man V","Kirby Adventure":"Kirby's Adventure",
"Kirby Dreamland 3":"Kirby's Dream Land 3","Kirby Planet Robot":"Kirby - Planet Robobot","Luigi Mansion":"Luigi's Mansion",
"Paper Mario 1000 Year Door":"Paper Mario - The Thousand-Year Door","Paper Mario Origami King":"Paper Mario - The Origami King",
"Ocarina Of Time":"Legend of Zelda, The - Ocarina of Time","Majora's Mask":"Legend of Zelda, The - Majora's Mask",
"Link 2 The Past":"Legend of Zelda, The - A Link to the Past","Minish Cap":"Legend of Zelda, The - The Minish Cap",
"Legend Of Zelda Oracle Of Ages":"Legend of Zelda, The - Oracle of Ages","Zelda Breath Of The Wild":"Legend of Zelda, The - Breath of the Wild",
"Zelda Tears Of The Kingdom":"Legend of Zelda, The - Tears of the Kingdom","Zelda Ocarina Of Time":"Legend of Zelda, The - Ocarina of Time",
"Donkey Kong Bonanza":"Donkey Kong Bananza","Sayanora Wild Hearts":"Sayonara Wild Hearts","Shocking Troopers":"Shock Troopers",
"Samurai Showdown II":"Samurai Shodown II","Samurai Showdown V":"Samurai Shodown V","Tsunoko vs Capcom":"Tatsunoko vs. Capcom - Ultimate All-Stars",
"Warios Land Shake It":"Wario Land - Shake It!","God Of War Ascension":"God of War - Ascension",
"Shadow Of Colossus":"Shadow of the Colossus","Shadow Of The Colossus":"Shadow of the Colossus",
"Final Fantasy 7":"Final Fantasy VII","Final Fantasy 8":"Final Fantasy VIII","Final Fantasy 9":"Final Fantasy IX",
"Final Fantasy XIII 2":"Final Fantasy XIII-2","Star War Knights Of The Old Republic II":"Star Wars - Knights of the Old Republic II - The Sith Lords",
"Jet Set Future Radio":"Jet Set Radio Future","Canon Spike":"Cannon Spike","Powerstone":"Power Stone","Powerstone 2":"Power Stone 2",
"PaRappa The Rappa":"PaRappa the Rapper","Katamari Damcacy":"Katamari Damacy","Mirrors Edge":"Mirror's Edge",
"Kill Zone 2":"Killzone 2","Kill Zone 3":"Killzone 3","Little Big Planet":"LittleBigPlanet","Little Big Planet 2":"LittleBigPlanet 2",
"Little Big Planet 3":"LittleBigPlanet 3","Infamous":"inFamous","Infamous 2":"inFamous 2","Infamous Second Son":"inFamous Second Son",
"Wolfenstein New Ordrr":"Wolfenstein - The New Order","DBZ Kakarot":"Dragon Ball Z - Kakarot",
"Dbz kakaraot":"Dragon Ball Z - Kakarot","Dbz xenoverse":"Dragon Ball Xenoverse","Dbz xenoverse 2":"Dragon Ball Xenoverse 2",
"Dbz Ultimate Tenkaichi":"Dragon Ball Z - Ultimate Tenkaichi","Berserk":"Berzerk","Hyperchase":"HyperChase - Auto Race"
}

PS5_TITLES={"Assassin's Creed Shadows","Astro Bot","Final Fantasy VII Rebirth","Final Fantasy XVI","Monster Hunter Wilds","Marvel's Spider-Man 2","Synth Riders"}
PS4_TITLES={"Cyberpunk 2077","Death Stranding","Dragon Ball Z: Kakarot","Devil May Cry 5","Ghost Of Tsushima","Hitman 3","Infamous Second Son","Injustice 2","It Takes Two","The Last of Us Part II","Life Is Strange","NieR:Automata","Nioh","Nioh 2","Persona 5 Royal","One Piece: Pirate Warriors 4","Psychonauts 2","Shadow Of The Colossus","Shadow Of The Tomb Raider","Spider-Man Miles Morales","The Witcher 3","Wolfenstein: The New Order","Wolfenstein II: The New Colossus"}
SWITCH2_TITLES={"Donkey Kong Bananza","Mario Kart World"}
SWITCH_TITLES={"Bayonetta 2","Bayonetta 3","Donkey Kong Country Tropical Freeze","Hades","Kirby and the Forgotten Land","Luigi's Mansion 3","Mario Kart 8","Metroid Dread","Paper Mario Origami King","Pikmin 3","Pikmin 4","Sayonara Wild Hearts","Super Smash Bros. Ultimate","Super Mario Bros. Wonder","Super Mario Odyssey","Xenoblade Chronicles","The Legend of Zelda: Breath of the Wild","The Legend of Zelda: Tears of the Kingdom"}

def apply_platform_correction(row):
    p=row.get("platform",""); t=(row.get("canonical_title") or row.get("original_title") or "").strip()
    if p=="PlayStation 4/5 (source combined)":
        if t in PS5_TITLES:
            row["platform"]="PlayStation 5"; row["system_release_year"]="2020"
        elif t in PS4_TITLES:
            row["platform"]="PlayStation 4"; row["system_release_year"]="2013"
        else:
            row["platform"]="TBA"; row["system_release_year"]="9999"
    elif p=="Nintendo Switch 2 (source section)":
        if t in SWITCH2_TITLES:
            row["platform"]="Nintendo Switch 2"; row["system_release_year"]="2025"
        elif t in SWITCH_TITLES:
            row["platform"]="Nintendo Switch"; row["system_release_year"]="2017"
        else:
            row["platform"]="TBA"; row["system_release_year"]="9999"
    return row

BASE="https://thumbnails.libretro.com"
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0 game-cover-catalog-builder/1.0"})

def safe_title(s):
    return re.sub(r'[&*/:\`<>?\\\\|"]','_',s)

def variants(row):
    vals=[]
    for k in ("canonical_title","original_title","source_text"):
        t=(row.get(k) or "").strip().lstrip("*").strip()
        if t: vals.append(t)
    expanded=[]
    for t in vals:
        a=ALIASES.get(t,t)
        expanded += [a,t]
        expanded += [a.replace("’","'"), a.replace("&","and"), a.replace(" and "," & ")]
        expanded += [re.sub(r"\\bBros\\b","Bros.",a), re.sub(r"\\bDr\\b","Dr.",a)]
        if a.lower().startswith("the "): expanded.append(a[4:]+", The")
        if a.lower().startswith("a "): expanded.append(a[2:]+", A")
    out=[]
    for x in expanded:
        x=re.sub(r"\\s+"," ",x).strip()
        if x and x not in out: out.append(x)
    return out[:12]

SUFFIXES=[" (USA).png"," (USA, Europe).png"," (World).png"," (USA) (Rev 1).png"," (Europe).png"," (Japan).png",".png"]


INDEXES={}
INDEX_LOOKUPS={}
PS3_MAP=None
X360_MAP=None
SWITCH_MAP=None
MOBY_MAP=None

def normkey(x):
    x=urllib.parse.unquote(x or "")
    x=re.sub(r"\.png$|\.jpg$","",x,flags=re.I)
    x=re.sub(r"\([^)]*\)|\[[^]]*\]"," ",x)
    x=x.replace("_"," ").replace("-"," ")
    return re.sub(r"[^a-z0-9]+","",x.lower())

def repo_slug(d):
    return d.replace(" - ","_-_").replace(" ","_")

def load_index(d):
    if d in INDEXES: return INDEXES[d]
    names=[]
    slug=repo_slug(d)
    try:
        api=f"https://api.github.com/repos/libretro-thumbnails/{slug}/git/trees/master?recursive=1"
        j=S.get(api,timeout=30).json()
        names=[Path(x.get("path","")).name for x in j.get("tree",[]) if x.get("path","").startswith("Named_Boxarts/") and x.get("path","").lower().endswith(".png")]
    except Exception:
        names=[]
    if not names:
        u=BASE+"/"+urllib.parse.quote(d,safe="")+"/Named_Boxarts/"
        try:
            r=S.get(u,timeout=30); r.raise_for_status()
            names=[urllib.parse.unquote(x) for x in re.findall(r'href="([^"]+\.png)"',r.text,re.I)]
        except Exception:
            names=[]
    INDEXES[d]=set(names)
    lu={}
    for n in names:
        k=normkey(n)
        if k: lu.setdefault(k,[]).append(n)
    INDEX_LOOKUPS[d]=lu
    return INDEXES[d]

def cover_download_urls(d,name):
    slug=repo_slug(d)
    q=urllib.parse.quote(name,safe="")
    return [
        BASE+"/"+urllib.parse.quote(d,safe="")+"/Named_Boxarts/"+q,
        f"https://raw.githubusercontent.com/libretro-thumbnails/{slug}/master/Named_Boxarts/{q}"
    ]

def preferred_names(row,d):
    names=load_index(d)
    seen=set()
    for t in variants(row):
        for suf in SUFFIXES:
            n=safe_title(t)+suf
            if n in names and n not in seen:
                seen.add(n); yield n
        k=normkey(t)
        cands=INDEX_LOOKUPS.get(d,{}).get(k,[])
        cands=sorted(cands,key=lambda n:(0 if "(USA)" in n else 1 if "(USA, Europe)" in n else 2 if "(World)" in n else 3 if "(Europe)" in n else 4, len(n)))
        for n in cands[:3]:
            if n not in seen:
                seen.add(n); yield n


def numeric_tokens(x):
    return tuple(re.findall(r"\d+", (x or "").lower()))

def fuzzy_names(row,d):
    load_index(d)
    lu=INDEX_LOOKUPS.get(d,{})
    if not lu: return
    keys=list(lu.keys())
    seen=set(); scored=[]
    for t in variants(row):
        q=normkey(t)
        if not q: continue
        for k,score,_ in process.extract(q,keys,scorer=fuzz.WRatio,limit=8,score_cutoff=86):
            qnums=numeric_tokens(t); knums=numeric_tokens(k)
            if qnums and knums and qnums!=knums: continue
            if (qnums and not knums) or (knums and not qnums): continue
            scored.append((score,k))
    scored.sort(reverse=True)
    if not scored: return
    best=scored[0][0]
    for score,k in scored:
        if score < max(88,best-3): continue
        for n in sorted(lu.get(k,[]),key=lambda n:(0 if "(USA)" in n else 1 if "(USA, Europe)" in n else 2 if "(World)" in n else 3 if "(Europe)" in n else 4,len(n))):
            if n not in seen:
                seen.add(n); yield n
                if len(seen)>=4: return

def candidate_urls(row):
    if platform in {"PlayStation 4","PlayStation 5","Nintendo Switch 2"}:
        for url,label in moby_candidates(row) or []:
            try:
                r=S.get(url,timeout=15)
                if r.status_code==200 and r.headers.get("content-type","").startswith("image") and len(r.content)>4000:
                    dest.write_bytes(r.content); Image.open(dest).verify()
                    return eid,str(dest),label
            except Exception:
                dest.unlink(missing_ok=True)
    exact=(row.get("cover_source_url") or "").strip()
    if exact: yield exact,"saved-exact"
    platform=row.get("platform","")
    for d in DIR_MAP.get(platform,[]):
        for t in variants(row):
            for suf in SUFFIXES:
                name=safe_title(t)+suf
                url=BASE+"/"+urllib.parse.quote(d,safe="")+"/Named_Boxarts/"+urllib.parse.quote(name,safe="")
                yield url,f"{d}/{name}"


def ps3_candidates(row):
    global PS3_MAP
    if PS3_MAP is None:
        PS3_MAP={}
        try:
            txt=S.get("https://www.gametdb.com/ps3tdb.txt?LANG=EN",timeout=30).text
            for line in txt.splitlines():
                if " = " in line:
                    gid,title=line.split(" = ",1)
                    PS3_MAP.setdefault(normkey(title),[]).append(gid.strip())
        except Exception:
            pass
        # Reliable fallback title/serial index from GameDB-PS3 release assets.
        try:
            data=S.get("https://github.com/niemasd/GameDB-PS3/releases/latest/download/PS3.titles.json",timeout=45).json()
            if isinstance(data,dict):
                for gid,title in data.items():
                    if isinstance(title,str):
                        PS3_MAP.setdefault(normkey(title),[]).append(str(gid).replace("-",""))
                    elif isinstance(title,list):
                        for t in title:
                            if isinstance(t,str):
                                PS3_MAP.setdefault(normkey(t),[]).append(str(gid).replace("-",""))
            elif isinstance(data,list):
                for item in data:
                    if not isinstance(item,dict): continue
                    gid=str(item.get("serial") or item.get("id") or item.get("product_code") or "").replace("-","")
                    title=item.get("title") or item.get("name")
                    if gid and isinstance(title,str):
                        PS3_MAP.setdefault(normkey(title),[]).append(gid)
        except Exception:
            pass
    keys=[]
    for t in variants(row):
        k=normkey(t)
        if k in PS3_MAP: keys.append(k)
    if not keys: keys=fuzzy_db_matches(row,PS3_MAP,86)
    for k in keys:
        for gid in PS3_MAP.get(k,[]):
            gid=gid.strip()
            pref=[]
            if gid.startswith(("BLUS","BCUS","NPUB","NPUA")): pref=["US","EN"]
            elif gid.startswith(("BLES","BCES","NPEB","NPEA")): pref=["EN","US"]
            elif gid.startswith(("BLJM","BLJS","BCJS","NPJB","NPJA")): pref=["JA","EN","US"]
            else: pref=["US","EN","JA"]
            regs=[]
            for reg in pref+["FR","DE","ES","IT","AU"]:
                if reg not in regs: regs.append(reg)
            for reg in regs:
                for typ in ("coverHQ","coverM","cover"):
                    for ext in ("jpg","png"):
                        yield f"https://art.gametdb.com/ps3/{typ}/{reg}/{gid}.{ext}",f"GameTDB PS3 {gid} {typ} {reg}"

def x360_candidates(row):
    global X360_MAP
    if X360_MAP is None:
        X360_MAP={}
        arr=[]
        local=ROOT/"x360db_games.json"
        if local.exists():
            try:
                data=json.loads(local.read_text(encoding="utf-8"))
                arr=data if isinstance(data,list) else (data.get("games") or data.get("titles") or [])
            except Exception:
                arr=[]
        if not arr:
            for dburl in (
                "https://raw.githubusercontent.com/xenia-manager/x360db/main/games.json",
                "https://xenia-manager.github.io/x360db/games.json",
            ):
                try:
                    data=S.get(dburl,timeout=45).json()
                    if isinstance(data,list):
                        arr=data; break
                    if isinstance(data,dict):
                        arr=data.get("games") or data.get("titles") or []
                        if isinstance(arr,list) and arr: break
                except Exception:
                    continue
        for g in arr:
            if isinstance(g,dict):
                X360_MAP.setdefault(normkey(g.get("title","")),[]).append(g)
    keys=[]
    for t in variants(row):
        k=normkey(t)
        if k in X360_MAP: keys.append(k)
    if not keys: keys=fuzzy_db_matches(row,X360_MAP,86)
    for k in keys:
        for g in X360_MAP.get(k,[]):
            gid=(g.get("id") or "").strip()
            u=g.get("boxart")
            if u and str(u).startswith("http"):
                u=str(u).replace("http://download.xbox.com:80","https://download.xbox.com").replace("http://download.xbox.com","https://download.xbox.com")
                yield u,f"x360db index {gid}"
            if gid:
                yield f"https://xenia-manager.github.io/x360db/titles/{gid}/artwork/boxart.jpg",f"x360db pages {gid}"
                yield f"https://raw.githubusercontent.com/xenia-manager/x360db/main/titles/{gid}/artwork/boxart.jpg",f"x360db raw {gid}"


def fuzzy_db_matches(row, mapping, cutoff=87):
    if not mapping: return []
    keys=list(mapping.keys()); out=[]; seen=set()
    for t in variants(row):
        q=normkey(t)
        if not q: continue
        for k,score,_ in process.extract(q,keys,scorer=fuzz.WRatio,limit=5,score_cutoff=cutoff):
            qnums=numeric_tokens(t); knums=numeric_tokens(k)
            if qnums and knums and qnums!=knums: continue
            if (qnums and not knums) or (knums and not qnums): continue
            if k not in seen:
                seen.add(k); out.append((score,k))
    out.sort(reverse=True)
    if not out: return []
    best=out[0][0]
    return [k for score,k in out[:4] if score >= max(cutoff,best-4)]

def switch_candidates(row):
    global SWITCH_MAP
    if SWITCH_MAP is None:
        SWITCH_MAP={}
        local=ROOT/"switchtdb.txt"
        if local.exists():
            try:
                txt=local.read_text(encoding="utf-8",errors="ignore")
                for line in txt.splitlines():
                    if " = " in line:
                        gid,title=line.split(" = ",1)
                        SWITCH_MAP.setdefault(normkey(title),[]).append(gid.strip())
            except Exception:
                pass
        if not SWITCH_MAP:
            try:
                txt=S.get("https://www.gametdb.com/switchtdb.txt?LANG=EN",timeout=40).text
                for line in txt.splitlines():
                    if " = " in line:
                        gid,title=line.split(" = ",1)
                        SWITCH_MAP.setdefault(normkey(title),[]).append(gid.strip())
            except Exception: pass
    keys=[]
    for t in variants(row):
        k=normkey(t)
        if k in SWITCH_MAP: keys.append(k)
    if not keys: keys=fuzzy_db_matches(row,SWITCH_MAP,86)
    for k in keys:
        for gid in SWITCH_MAP.get(k,[]):
            for reg,typ in [("US","coverHQ"),("US","coverM"),("EN","coverM")]:
                yield f"https://art.gametdb.com/switch/{typ}/{reg}/{gid}.jpg",f"GameTDB Switch {gid} {reg}"



def load_moby_map():
    global MOBY_MAP
    if MOBY_MAP is not None:
        return MOBY_MAP
    MOBY_MAP={}
    pages=ROOT/"moby_pages"
    if not pages.exists():
        return MOBY_MAP
    for fp in pages.glob("*.html"):
        try:
            txt=fp.read_text(encoding="utf-8",errors="ignore")
            m=re.search(r'<meta property="og:title" content="([^"]+)"',txt,re.I)
            if not m:
                continue
            title=html.unescape(m.group(1))
            title=re.sub(r'\\s*\\(\\d{4}\\)\\s*-\\s*MobyGames\\s*$', '', title).strip()
            pm=re.search(r":platforms='(\\[.*?\\])'\\s+:game-id=",txt,re.S)
            if not pm:
                continue
            arr=json.loads(html.unescape(pm.group(1)))
            key=normkey(title)
            for item in arr:
                if not isinstance(item,dict):
                    continue
                plat=(item.get("name") or "").strip()
                main=item.get("main_cover") or {}
                url=main.get("image_url")
                if key and plat and url:
                    MOBY_MAP.setdefault(key,[]).append({"platform":plat,"url":url,"title":title})
        except Exception:
            continue
    print("moby titles",len(MOBY_MAP),flush=True)
    return MOBY_MAP

def moby_candidates(row):
    mapping=load_moby_map()
    platform=row.get("platform","")
    platform_alias={
        "PlayStation 4":"PlayStation 4",
        "PlayStation 5":"PlayStation 5",
        "Nintendo Switch 2":"Nintendo Switch 2",
    }.get(platform)
    if not platform_alias or not mapping:
        return
    keys=[]
    for t in variants(row):
        k=normkey(t)
        if k in mapping and k not in keys:
            keys.append(k)
    if not keys:
        keys=fuzzy_db_matches(row,mapping,90)
    seen=set()
    for k in keys[:4]:
        for item in mapping.get(k,[]):
            if item.get("platform")==platform_alias:
                u=item.get("url")
                if u and u not in seen:
                    seen.add(u)
                    yield u,f"MobyGames mirror {platform_alias}: {item.get('title','')}"

def fallback_actual_image(row, dest):
    """Last resort: real game/media image from Wikipedia; otherwise real platform/hardware image."""
    title=(row.get("canonical_title") or row.get("original_title") or "").strip()
    platform=row.get("platform","")
    queries=[]
    if title:
        if platform and platform not in {"TBA","Platform Not Specified"}:
            queries += [f"{title} {platform} video game", f"{title} video game"]
        else:
            queries += [f"{title} video game"]
    for q in queries:
        try:
            params={"action":"query","generator":"search","gsrsearch":q,"gsrlimit":6,
                    "prop":"pageimages","piprop":"thumbnail|original","pithumbsize":900,
                    "format":"json","formatversion":2}
            j=S.get("https://en.wikipedia.org/w/api.php",params=params,timeout=10).json()
            pages=(j.get("query") or {}).get("pages") or []
            for p in pages:
                img=(p.get("thumbnail") or p.get("original") or {}).get("source")
                if not img:
                    continue
                try:
                    r=S.get(img,timeout=10)
                    if r.status_code==200 and r.headers.get("content-type","").startswith("image") and len(r.content)>4000:
                        dest.write_bytes(r.content)
                        Image.open(dest).verify()
                        return str(dest),f"Wikipedia page image: {p.get('title','')}"
                except Exception:
                    dest.unlink(missing_ok=True)
        except Exception:
            pass
    hint=platform
    if platform=="TBA":
        hint="PlayStation 5"
    elif platform=="Platform Not Specified":
        hint="video game cartridge"
    if hint:
        p=console_image(hint)
        if p and Path(p).exists():
            try:
                import shutil
                shutil.copyfile(p,dest)
                Image.open(dest).verify()
                return str(dest),f"physical-media fallback: {hint}"
            except Exception:
                dest.unlink(missing_ok=True)
    try:
        u="https://commons.wikimedia.org/wiki/Special:Redirect/file/Game_Boy_with_Tetris_cartridge.jpg?width=900"
        r=S.get(u,timeout=15)
        if r.status_code==200 and r.headers.get("content-type","").startswith("image") and len(r.content)>4000:
            dest.write_bytes(r.content)
            Image.open(dest).verify()
            return str(dest),"generic physical game-media fallback"
    except Exception:
        dest.unlink(missing_ok=True)
    return None,None

def fetch_one(row):
    eid=row["entry_id"]; platform=row.get("platform","")
    dest=COVERS/(eid+".png")
    if eid in {"VG-0014","VG-0015","VG-0016"}:
        return eid,None,"unresolved-special-case"
    if platform in SKIP_PLATFORMS and platform not in {"Nintendo Switch 2","PlayStation 5"}:
        return eid,None,"unresolved-platform"
    if platform not in DIR_MAP and platform not in {"Nintendo Switch","Nintendo Switch 2","PlayStation 5"}:
        return eid,None,"unresolved-platform"
    if dest.exists() and dest.stat().st_size>5000: return eid,str(dest),"cached"
    if platform in {"PlayStation 4","PlayStation 5","Nintendo Switch 2"}:
        for url,label in moby_candidates(row) or []:
            try:
                r=S.get(url,timeout=15)
                if r.status_code==200 and r.headers.get("content-type","").startswith("image") and len(r.content)>4000:
                    dest.write_bytes(r.content)
                    Image.open(dest).verify()
                    return eid,str(dest),label
            except Exception:
                dest.unlink(missing_ok=True)
    exact=(row.get("cover_source_url") or "").strip()
    if exact:
        try:
            r=S.get(exact,timeout=20)
            if r.status_code==200 and r.headers.get("content-type","").startswith("image") and len(r.content)>4000:
                dest.write_bytes(r.content); Image.open(dest).verify()
                return eid,str(dest),"saved-exact"
        except Exception: dest.unlink(missing_ok=True)
    if platform=="PlayStation 3":
        for url,label in ps3_candidates(row):
            try:
                r=S.get(url,timeout=8)
                if r.status_code==200 and r.headers.get("content-type","").startswith("image") and len(r.content)>4000:
                    dest.write_bytes(r.content); Image.open(dest).verify()
                    return eid,str(dest),label
            except Exception: dest.unlink(missing_ok=True)
    if platform=="Xbox 360":
        digital_only={"Castle Crashers","Scott Pilgrim"}
        if (row.get("original_title") or "") not in digital_only:
            for url,label in x360_candidates(row):
                try:
                    r=S.get(url,timeout=15)
                    if r.status_code==200 and r.headers.get("content-type","").startswith("image") and len(r.content)>4000:
                        dest.write_bytes(r.content); Image.open(dest).verify()
                        return eid,str(dest),label
                except Exception: dest.unlink(missing_ok=True)
    if platform in {"Nintendo Switch","Nintendo Switch 2"}:
        for url,label in switch_candidates(row):
            try:
                r=S.get(url,timeout=8)
                if r.status_code==200 and r.headers.get("content-type","").startswith("image") and len(r.content)>4000:
                    dest.write_bytes(r.content); Image.open(dest).verify()
                    return eid,str(dest),label
            except Exception: dest.unlink(missing_ok=True)
    for d in DIR_MAP.get(platform,[]):
        names=list(preferred_names(row,d))
        if not names: names=list(fuzzy_names(row,d) or [])
        for name in names:
            for url in cover_download_urls(d,name):
                try:
                    r=S.get(url,timeout=10)
                    if r.status_code==200 and r.headers.get("content-type","").startswith("image") and len(r.content)>4000:
                        dest.write_bytes(r.content); Image.open(dest).verify()
                        return eid,str(dest),f"{d}/{name}"
                except Exception:
                    dest.unlink(missing_ok=True)
    return eid,None,"not-found"

def console_image(system):
    fn=CONSOLES/(re.sub(r"[^A-Za-z0-9]+","_",system).strip("_")+".jpg")
    if fn.exists(): return fn
    try:
        params={"action":"query","generator":"search","gsrsearch":system+" video game console","gsrlimit":4,
                "prop":"pageimages","piprop":"thumbnail|original","pithumbsize":700,"format":"json","formatversion":2}
        j=S.get("https://en.wikipedia.org/w/api.php",params=params,timeout=12).json()
        pages=(j.get("query") or {}).get("pages") or []
        p=next((p for p in pages if p.get("thumbnail") or p.get("original")),None)
        if p:
            u=(p.get("thumbnail") or p.get("original"))["source"]
            b=S.get(u,timeout=12).content
            fn.write_bytes(b); Image.open(fn).verify(); return fn
    except Exception: pass
    return None

def wrap(c,text,maxw,font="Helvetica",size=7.3,maxlines=2):
    words=text.split(); lines=[]; cur=""
    for w in words:
        test=(cur+" "+w).strip()
        if stringWidth(test,font,size)<=maxw: cur=test
        else:
            if cur: lines.append(cur)
            cur=w
            if len(lines)>=maxlines-1: break
    if cur and len(lines)<maxlines: lines.append(cur)
    if len(lines)==maxlines and words:
        while stringWidth(lines[-1]+"...",font,size)>maxw and len(lines[-1])>1: lines[-1]=lines[-1][:-1]
        lines[-1]=lines[-1].rstrip()+"..."
    return lines

def draw_cover(c,path,x,y,w,h):
    try:
        im=Image.open(path).convert("RGB")
        iw,ih=im.size; scale=min(w/iw,h/ih)
        dw,dh=iw*scale,ih*scale
        c.drawImage(ImageReader(im),x+(w-dw)/2,y+(h-dh)/2,width=dw,height=dh,preserveAspectRatio=True,mask='auto')
    except Exception: pass

def build_pdf(decade, rows, resolved):
    path=OUT/(decade.replace("–","-").replace("/","_")+".pdf")
    c=canvas.Canvas(str(path),pagesize=letter)
    W,H=letter; margin=36; header_h=54
    systems=sorted({r["platform"] for r in rows if r["platform"]}, key=lambda s:min([float(r["system_release_year"] or 9999) for r in rows if r["platform"]==s]))
    page_no=0
    for system in systems:
        sr=[r for r in rows if r["platform"]==system and resolved.get(r["entry_id"])]
        if not sr: continue
        sr.sort(key=lambda r:(r["canonical_title"] or r["original_title"]).lower())
        for page_start in range(0,len(sr),12):
            page_no+=1
            c.setFillColorRGB(.07,.07,.07); c.rect(0,H-header_h,W,header_h,fill=1,stroke=0)
            img=console_image(system)
            if img: draw_cover(c,img,margin,H-header_h+6,52,42)
            c.setFillColorRGB(1,1,1); c.setFont("Helvetica-Bold",17)
            c.drawString(margin+(62 if img else 0),H-29,system)
            year=next((r["system_release_year"] for r in sr if r["system_release_year"]), "")
            c.setFont("Helvetica",8); c.drawRightString(W-margin,H-28,str(year))
            c.setFillColorRGB(.1,.1,.1)
            avail_w=W-2*margin; col_gap=12; cols=4
            cell_w=(avail_w-col_gap*(cols-1))/cols
            cover_w=cell_w; cover_h=126; title_h=28; row_gap=12
            top=H-header_h-18
            for i,r in enumerate(sr[page_start:page_start+12]):
                rr=i//4; cc=i%4
                x=margin+cc*(cell_w+col_gap); y=top-(rr+1)*(cover_h+title_h+row_gap)+title_h+row_gap
                draw_cover(c,resolved[r["entry_id"]],x,y,cover_w,cover_h)
                title=(r["canonical_title"] or r["original_title"]).strip()
                c.setFont("Helvetica",7.3)
                ty=y-9
                for line in wrap(c,title,cell_w, size=7.3):
                    c.drawCentredString(x+cell_w/2,ty,line); ty-=8.5
            c.setFont("Helvetica",6.5); c.setFillColorRGB(.45,.45,.45)
            c.drawRightString(W-margin,14,f"{decade} • {page_no}")
            c.showPage()
    unresolved=[r for r in rows if not resolved.get(r["entry_id"])]
    if unresolved:
        unresolved.sort(key=lambda r:(float(r["system_release_year"] or 9999),r["platform"],(r["canonical_title"] or r["original_title"]).lower()))
        per=54
        for start in range(0,len(unresolved),per):
            c.setFillColorRGB(.07,.07,.07); c.rect(0,H-54,W,54,fill=1,stroke=0)
            c.setFillColorRGB(1,1,1); c.setFont("Helvetica-Bold",16); c.drawString(margin,H-31,"Unresolved / edition review")
            c.setFont("Helvetica",7.5); c.drawRightString(W-margin,H-29,"No substitute artwork used")
            c.setFillColorRGB(.1,.1,.1); c.setFont("Helvetica",7.2)
            chunk=unresolved[start:start+per]
            colw=(W-2*margin-24)/2
            for i,r in enumerate(chunk):
                col=i//27; row=i%27
                x=margin+col*(colw+24); y=H-72-row*24
                c.setFont("Helvetica-Bold",7.2); c.drawString(x,y,(r["canonical_title"] or r["original_title"])[:56])
                c.setFont("Helvetica",6.5); c.setFillColorRGB(.35,.35,.35); c.drawString(x,y-8,(r["platform"] or "Platform not specified")[:58]); c.setFillColorRGB(.1,.1,.1)
            c.showPage()
    c.save()
    return path

def main():
    rows=[]
    with open(ROOT/"master_manifest.csv",encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f)
        for r in rd:
            if not r.get("entry_id") and r.get("index")=="index": continue
            apply_platform_correction(r)
            rows.append(r)
    print("entries",len(rows),flush=True)
    dirs=sorted({d for r in rows for d in DIR_MAP.get(r.get("platform",""),[])})
    print("loading",len(dirs),"system indexes",flush=True)
    with ThreadPoolExecutor(max_workers=8) as ix:
        list(ix.map(load_index,dirs))
    print("indexes loaded",flush=True)
    resolved={}; labels={}
    target_decades={"2000s","2010s-2020s"}
    work_rows=[r for r in rows if (r.get("decade") or "").replace("–","-") in target_decades]
    print("target entries",len(work_rows),flush=True)
    load_moby_map()
    with ThreadPoolExecutor(max_workers=24) as ex:
        futs=[ex.submit(fetch_one,r) for r in work_rows]
        done=0
        for f in as_completed(futs):
            eid,p,label=f.result(); done+=1
            if p: resolved[eid]=p; labels[eid]=label
            if done%50==0: print("resolved",done,"found",len(resolved),flush=True)
    decades=["2000s","2010s-2020s"]
    summary={"entries":len(rows),"covers_found":len(resolved),"unresolved":len(rows)-len(resolved),"decades":{},"systems":{}}
    for d in decades:
        rr=[r for r in rows if (r.get("decade") or "").replace("–","-")==d]
        p=build_pdf(d,rr,resolved)
        summary["decades"][d]={"entries":len(rr),"resolved":sum(1 for r in rr if resolved.get(r["entry_id"])),"pdf":p.name}
    for system in sorted({r.get("platform","") for r in rows}):
        sr=[r for r in rows if r.get("platform","")==system]
        summary["systems"][system]={"entries":len(sr),"resolved":sum(1 for r in sr if resolved.get(r["entry_id"]))}
    (OUT/"build_summary.json").write_text(json.dumps(summary,indent=2))
    with open(OUT/"resolved_sources.csv","w",newline="",encoding="utf-8") as f:
        w=csv.writer(f); w.writerow(["entry_id","source"])
        for eid in sorted(labels): w.writerow([eid,labels[eid]])
    print(json.dumps(summary,indent=2),flush=True)

if __name__=="__main__": main()
