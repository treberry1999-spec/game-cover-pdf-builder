import requests,re,json
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathlib import Path

S=requests.Session();S.headers["User-Agent"]="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/152 Safari/537.36"
u="https://www.buzzfeed.com/briangalindo/20-vibe-magazine-covers-that-perfectly-define-the-90s"
r=S.get(u,timeout=60);print("STATUS",r.status_code,len(r.content),r.url);r.raise_for_status()
Path("magazine_output/buzzfeed").mkdir(parents=True,exist_ok=True)
Path("magazine_output/buzzfeed/page.html").write_bytes(r.content)
s=BeautifulSoup(r.text,"html.parser")
rows=[]
for im in s.find_all("img"):
    src=im.get("src") or im.get("data-src") or im.get("data-bfa-src") or ""
    srcset=im.get("srcset") or im.get("data-srcset") or ""
    alt=im.get("alt","")
    # find nearby text
    par=im.parent
    nearby=""
    for _ in range(5):
        if not par:break
        txt=" ".join(par.stripped_strings)
        if txt:nearby=txt[:1000]
        par=par.parent
    if src or srcset:
        rows.append({"alt":alt,"src":src,"srcset":srcset,"nearby":nearby})
Path("magazine_output/buzzfeed/images.json").write_text(json.dumps(rows,indent=2))
for i,x in enumerate(rows):
    print("\\nIMG",i,"ALT",x["alt"],"SRC",x["src"],"SRCSET",x["srcset"][:500],"NEAR",x["nearby"][:500])
