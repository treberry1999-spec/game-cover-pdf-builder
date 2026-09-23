import requests, json, os
from pathlib import Path
H={"User-Agent":"Mozilla/5.0"}
u="https://www.xxlmag.com/rest/carbon/api/gallery/6334a4900385ac5f4a8a5678"
r=requests.get(u,headers=H,timeout=60); r.raise_for_status()
photos=r.json()["gallery"][0]["photo"]
out=Path("magazine_output/xxl_history_pages"); out.mkdir(parents=True,exist_ok=True)
for i,p in enumerate(photos,1):
    url=p["photo-url"]
    rr=requests.get(url,headers=H,timeout=90); rr.raise_for_status()
    fn=out/f"{i:02d}.jpg"; fn.write_bytes(rr.content)
    print(i,url,len(rr.content),fn)
