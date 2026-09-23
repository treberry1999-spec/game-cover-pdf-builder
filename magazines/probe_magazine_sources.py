import requests, re, json
from bs4 import BeautifulSoup

H={"User-Agent":"Mozilla/5.0"}

def fetch(url):
    r=requests.get(url,headers=H,timeout=60)
    print("\nURL",url,"STATUS",r.status_code,"CT",r.headers.get("content-type"),"LEN",len(r.content))
    print("FINAL",r.url)
    return r

# The Source archive
r=fetch("https://the-source.net/archive/")
open("source_archive.html","wb").write(r.content)
s=BeautifulSoup(r.text,"html.parser")
links=[]
for a in s.find_all("a",href=True):
    href=a["href"]
    txt=" ".join(a.stripped_strings)
    if "pdf" in href.lower() or "archive" in href.lower() or re.search(r"issue|edition|199\d|200\d",txt,re.I):
        links.append((txt,href))
print("SOURCE LINKS",json.dumps(links[:300],indent=2)[:20000])

# XXL all covers
r=fetch("https://www.xxlmag.com/xxl-magazine-covers/")
open("xxl_covers.html","wb").write(r.content)
s=BeautifulSoup(r.text,"html.parser")
imgs=[]
for im in s.find_all("img"):
    src=im.get("data-src") or im.get("src") or im.get("data-lazy-src")
    alt=im.get("alt","")
    title=im.get("title","")
    if src:
        imgs.append((alt,title,src))
print("XXL IMAGES",json.dumps(imgs[:500],indent=2)[:30000])

# Google Books API VIBE probe
for q in ['VIBE magazine 1994 Tupac','VIBE magazine 1994 Janet Jackson','VIBE magazine 1995 Mary J Blige']:
    u="https://www.googleapis.com/books/v1/volumes"
    rr=requests.get(u,params={"q":q,"maxResults":10},headers=H,timeout=60)
    print("\nGOOGLE",q,rr.status_code)
    js=rr.json()
    for item in js.get("items",[]):
        v=item.get("volumeInfo",{})
        print(v.get("title"),v.get("publishedDate"),v.get("imageLinks",{}).get("thumbnail"),item.get("id"))
