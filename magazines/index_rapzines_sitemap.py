import requests, re, json, xml.etree.ElementTree as ET
from pathlib import Path
from bs4 import BeautifulSoup

OUT=Path("magazine_output/rapzines_sitemap")
OUT.mkdir(parents=True,exist_ok=True)
S=requests.Session()
S.headers.update({"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/152 Safari/537.36"})

urls_to_try=[
 "https://www.rapzines.com/robots.txt",
 "https://www.rapzines.com/sitemap.xml",
 "https://www.rapzines.com/product-page-sitemap.xml",
 "https://www.rapzines.com/store-products-sitemap.xml",
]
found=[]
for u in urls_to_try:
    try:
        r=S.get(u,timeout=60)
        print("FETCH",u,r.status_code,r.url,r.headers.get("content-type"),len(r.content))
        fn=OUT/(re.sub(r"[^a-z0-9]+","_",u.lower()).strip("_")+".txt")
        fn.write_bytes(r.content)
        if r.status_code==200 and b"<loc>" in r.content:
            try:
                root=ET.fromstring(r.content)
                for el in root.iter():
                    if el.tag.endswith("loc") and el.text:
                        found.append(el.text.strip())
            except Exception as e: print("XMLERR",e)
    except Exception as e: print("ERR",u,e)

# recursively fetch sitemap children
sitemaps=[u for u in found if "sitemap" in u.lower()]
seen=set(found)
for sm in sitemaps[:50]:
    try:
        r=S.get(sm,timeout=60)
        print("CHILD",sm,r.status_code,len(r.content))
        if r.status_code!=200: continue
        root=ET.fromstring(r.content)
        for el in root.iter():
            if el.tag.endswith("loc") and el.text:
                seen.add(el.text.strip())
    except Exception as e: print("CHILDERR",sm,e)

all_urls=sorted(seen)
(OUT/"all_urls.json").write_text(json.dumps(all_urls,indent=2))
products=[u for u in all_urls if "/product-page/" in u]
print("PRODUCT URLS",len(products))
for u in products[:500]: print(u)
(OUT/"product_urls.json").write_text(json.dumps(products,indent=2))
