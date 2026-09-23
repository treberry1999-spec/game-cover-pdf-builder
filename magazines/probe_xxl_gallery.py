import requests, json
H={"User-Agent":"Mozilla/5.0"}
base="https://www.xxlmag.com/rest/carbon/api/gallery/6334a4900385ac5f4a8a5678"
for params in [{},{"page":1},{"page":2},{"page":10},{"offset":0},{"offset":11}]:
 r=requests.get(base,params=params,headers=H,timeout=60)
 print("\nPARAMS",params,"URL",r.url,"STATUS",r.status_code,"LEN",len(r.content),r.headers.get("content-type"))
 print(r.text[:12000])
