import requests,json
H={"User-Agent":"Mozilla/5.0"}
for q in ["Vibe September 1993","Vibe February 1994","Vibe October 1995","Vibe February 1996","Vibe September 1997","Vibe October 1999","Vibe March 2000","Vibe September 2002","Vibe January 2003","Vibe September 2004","Vibe December 2006"]:
    r=requests.get("https://www.googleapis.com/books/v1/volumes",params={"q":q,"maxResults":40},headers=H,timeout=60)
    print("\nQUERY",q,"STATUS",r.status_code)
    for x in r.json().get("items",[]):
        v=x.get("volumeInfo",{})
        if "vibe" in (v.get("title") or "").lower():
            print(x.get("id"),"|",v.get("title"),"|",v.get("publishedDate"),"|",v.get("imageLinks",{}).get("thumbnail"))
