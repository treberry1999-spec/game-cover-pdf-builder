import requests
from pathlib import Path
url="https://images.squarespace-cdn.com/content/v1/5ec324ea292e052eacb5ef35/1723083940981-MQV3CAVZEQFQOJRDF64Z/Vibe%2BCover%2B%28Snipes%29.jpg"
out=Path("vibe_wesley_1993.jpg")
r=requests.get(url,timeout=60,headers={"User-Agent":"Mozilla/5.0"})
r.raise_for_status()
out.write_bytes(r.content)
print(out, len(r.content))
