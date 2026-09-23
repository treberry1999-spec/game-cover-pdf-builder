import requests,json,re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
H={"User-Agent":"Mozilla/5.0"}
def get(url):
 r=requests.get(url,headers=H,timeout=60); print(url,r.status_code,len(r.content),r.url); r.raise_for_status(); return r
# Unkut
u="https://unkut.com/2021/01/looking-back-at-the-first-hundred-issues-of-the-source-magazine/"
r=get(u); s=BeautifulSoup(r.text,"html.parser")
imgs=[]
for im in s.find_all("img"):
 src=im.get("data-src") or im.get("data-lazy-src") or im.get("src")
 if src:
  imgs.append({"src":urljoin(r.url,src),"alt":im.get("alt",""),"w":im.get("width"),"h":im.get("height"),"cls":im.get("class")})
print("UNKUT IMGS",json.dumps(imgs,indent=2)[:50000])
# Rap Style Archeology collection product links
r=get("https://rapstylearcheology.com/collections")
s=BeautifulSoup(r.text,"html.parser")
links=[]
for a in s.find_all("a",href=True):
 href=urljoin(r.url,a["href"])
 txt=" ".join(a.stripped_strings)
 if "/products/" in href and href not in [x["url"] for x in links]:
  links.append({"url":href,"anchor":txt})
print("PRODUCT LINKS",len(links))\nopen("rapstyle_links.json","w").write(json.dumps(links,indent=2))\nprint("FIRST LINKS",json.dumps(links[:100],indent=2)[:30000])
records=[]
for i,x in enumerate(links):
 if not any(k in x["anchor"].lower() for k in ["source magazine","vibe magazine","xxl magazine"]):
  continue
 try:
  pr=get(x["url"]); ps=BeautifulSoup(pr.text,"html.parser")
  title=(ps.find("meta",property="og:title") or {}).get("content") or (ps.find("h1").get_text(" ",strip=True) if ps.find("h1") else x["anchor"])
  img=(ps.find("meta",property="og:image") or {}).get("content")
  if not img:
   tag=ps.find("img")
   img=urljoin(pr.url,tag.get("src")) if tag and tag.get("src") else None
  records.append({"title":title,"url":pr.url,"image":img,"anchor":x["anchor"]})
 except Exception as e:
  print("ERR",x["url"],e)
print("RECORDS",len(records))
open("rapstyle_index.json","w").write(json.dumps(records,indent=2))
