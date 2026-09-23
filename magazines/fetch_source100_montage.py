import requests, os
from pathlib import Path
H={"User-Agent":"Mozilla/5.0"}
out=Path("magazine_output/unkut_source100");out.mkdir(parents=True,exist_ok=True)
urls=[]
for i in [1,2,3]:
 for suffix in [f"Source-100-{i}.jpg",f"Source-100-{i}-450x628.jpg"]:
  urls.append((i,suffix,"https://www.unkut.com/wp-content/uploads/2020/07/"+suffix))
for i,suffix,u in urls:
 try:
  r=requests.get(u,headers=H,timeout=60)
  print(i,suffix,r.status_code,len(r.content),r.headers.get("content-type"))
  if r.status_code==200 and r.headers.get("content-type","").startswith("image"):
   fn=out/(suffix.replace(".jpg","")+".jpg"); fn.write_bytes(r.content)
 except Exception as e: print("ERR",u,e)
