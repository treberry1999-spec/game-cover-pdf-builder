import requests,json
from bs4 import BeautifulSoup
from urllib.parse import urljoin
H={"User-Agent":"Mozilla/5.0"}
def get(url):
    r=requests.get(url,headers=H,timeout=60)
    print(url,r.status_code,len(r.content),r.url)
    r.raise_for_status()
    return r
r=get("https://rapstylearcheology.com/collections")
s=BeautifulSoup(r.text,"html.parser")
links=[]
seen=set()
for a in s.find_all("a",href=True):
    href=urljoin(r.url,a["href"])
    if "/products/" not in href or href in seen:
        continue
    seen.add(href)
    links.append({"url":href,"anchor":" ".join(a.stripped_strings)})
open("rapstyle_links.json","w").write(json.dumps(links,indent=2))
print("PRODUCT LINKS",len(links))
print(json.dumps(links[:120],indent=2)[:50000])
records=[]
candidates=[x for x in links if any(k in x["url"].lower() for k in ["source","vibe","xxl"])]
print("CANDIDATES",len(candidates))
for i,x in enumerate(candidates):
    try:
        pr=get(x["url"])
        ps=BeautifulSoup(pr.text,"html.parser")
        ogt=ps.find("meta",property="og:title")
        title=(ogt.get("content") if ogt else None) or (ps.find("h1").get_text(" ",strip=True) if ps.find("h1") else x["anchor"])
        ogi=ps.find("meta",property="og:image")
        img=ogi.get("content") if ogi else None
        records.append({"title":title,"url":pr.url,"image":img,"anchor":x["anchor"]})
    except Exception as e:
        print("ERR",x["url"],repr(e))
open("rapstyle_index.json","w").write(json.dumps(records,indent=2))
print("RECORDS",len(records))
