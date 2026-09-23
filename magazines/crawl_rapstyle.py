import requests,json,re,io
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
S=requests.Session(); S.headers["User-Agent"]="Mozilla/5.0"
OUT=Path("magazine_output/rapstyle_crawl");COV=OUT/"covers";COV.mkdir(parents=True,exist_ok=True)
products=[]
for page in range(1,20):
    u="https://rapstylearcheology.com/products.json"
    r=S.get(u,params={"limit":250,"page":page},timeout=60)
    print("PAGE",page,r.status_code,len(r.content))
    if r.status_code!=200: break
    js=r.json(); arr=js.get("products",[])
    if not arr: break
    products.extend(arr)
print("PRODUCTS",len(products))
records=[]
for p in products:
    title=p.get("title","")
    if any(k in title.lower() for k in ["vibe","source","xxl"]):
        imgs=p.get("images",[])
        records.append({"id":p.get("id"),"title":title,"handle":p.get("handle"),"url":"https://rapstylearcheology.com/products/"+p.get("handle",""),"image":imgs[0].get("src") if imgs else ""})
(OUT/"index.json").write_text(json.dumps(records,indent=2))
print("RELEVANT",len(records))
for r in records: print(r["title"],r["image"])
