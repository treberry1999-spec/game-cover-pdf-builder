from pathlib import Path
import requests

OUT=Path("output/90s_additions")
OUT.mkdir(parents=True,exist_ok=True)

covers={
"sonic_triple_trouble.png":"https://raw.githubusercontent.com/libretro-thumbnails/Sega_-_Game_Gear/refs/heads/master/Named_Boxarts/Sonic%20The%20Hedgehog%20-%20Triple%20Trouble%20%28USA%2C%20Europe%2C%20Brazil%29%20%28En%29.png",
"metal_slug.png":"https://raw.githubusercontent.com/libretro-thumbnails/SNK_-_Neo_Geo/refs/heads/master/Named_Boxarts/Metal%20Slug%20-%20Super%20Vehicle-001.png",
"neo_turf_masters.png":"https://raw.githubusercontent.com/libretro-thumbnails/SNK_-_Neo_Geo/refs/heads/master/Named_Boxarts/Neo%20Turf%20Masters%20_%20Big%20Tournament%20Golf.png",
"sengoku_3.png":"https://raw.githubusercontent.com/libretro-thumbnails/SNK_-_Neo_Geo/refs/heads/master/Named_Boxarts/Sengoku%203%20_%20Sengoku%20Densho%202001%20%28set%201%29.png",
"kof_98_slugfest.png":"https://raw.githubusercontent.com/libretro-thumbnails/SNK_-_Neo_Geo/refs/heads/master/Named_Boxarts/The%20King%20of%20Fighters%20%2798%20-%20The%20Slugfest%20_%20King%20of%20Fighters%20%2798%20-%20dream%20match%20never%20ends%20%28NGH-2420%29.png",
"final_fight_3.png":"https://raw.githubusercontent.com/libretro-thumbnails/Nintendo_-_Super_Nintendo_Entertainment_System/refs/heads/master/Named_Boxarts/Final%20Fight%203%20%28USA%29.png",
"madden_nfl_98.png":"https://raw.githubusercontent.com/libretro-thumbnails/Sony_-_PlayStation/refs/heads/master/Named_Boxarts/Madden%20NFL%2098%20%28USA%29.png",
"spyro_year_dragon.png":"https://raw.githubusercontent.com/libretro-thumbnails/Sony_-_PlayStation/refs/heads/master/Named_Boxarts/Spyro%20-%20Year%20of%20the%20Dragon%20%28USA%29.png",
"battle_for_naboo.png":"https://raw.githubusercontent.com/libretro-thumbnails/Nintendo_-_Nintendo_64/refs/heads/master/Named_Boxarts/Star%20Wars%20Episode%20I%20-%20Battle%20for%20Naboo%20%28USA%29.png",
}

s=requests.Session()
s.headers["User-Agent"]="Mozilla/5.0 catalog-cover-fetch/1.0"
for name,url in covers.items():
    r=s.get(url,timeout=60)
    r.raise_for_status()
    if not r.headers.get("content-type","").startswith("image"):
        raise RuntimeError(f"{name}: not image: {r.headers.get('content-type')}")
    (OUT/name).write_bytes(r.content)
    print(name,len(r.content),r.headers.get("content-type"))
