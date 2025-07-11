import requests
import json
from datetime import datetime

# Kaynak listesi: (URL, isim)
plugin_sources = [
    ("https://raw.githubusercontent.com/GitLatte/Sinetech/refs/heads/builds/plugins.json", "sinetech"),
    ("https://raw.githubusercontent.com/feroxx/Kekik-cloudstream/refs/heads/builds/plugins.json", "kekikan"),
    ("https://raw.githubusercontent.com/Kraptor123/cs-kekikanime/refs/heads/builds/plugins.json", "kekikanime"),
    ("https://raw.githubusercontent.com/nikyokki/nik-cloudstream/builds/plugins.json", "nikyokki"),
]

birlesik_plugins = []

for url, kaynak_adi in plugin_sources:
    try:
        print(f"[+] {url} indiriliyor...")
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, list):
            for plugin in data:
                # Kaynak ismini köşeli parantezle name ve internalName'e ekle
                etiket = f"[{kaynak_adi}]"
                for key in ["name", "internalName"]:
                    if key in plugin:
                        plugin[key] = f"{plugin[key]}{etiket}"
                
                # Açıklama kısmına bugünün tarihini ekle
                bugun = datetime.now().strftime("[%d.%m.%Y]")
                aciklama = plugin.get("description", "")
                if bugun not in aciklama:
                    plugin["description"] = f"{bugun} {aciklama}".strip()

                birlesik_plugins.append(plugin)
        else:
            print(f"⚠️ {url} JSON dizisi değil! Atlandı.")
    except Exception as e:
        print(f"❌ {url} indirilemedi: {e}")

# Aynı id'ye sahip eklentileri filtrele, sonuncuyu tut
unique_plugins = {plugin["id"]: plugin for plugin in birlesik_plugins if "id" in plugin}
birlesik_liste = list(unique_plugins.values())

# JSON dosyasına yaz
with open("birlesik_plugins.json", "w", encoding="utf-8") as f:
    json.dump(birlesik_liste, f, indent=4, ensure_ascii=False)

print(f"\n✅ {len(birlesik_liste)} plugin başarıyla birleştirildi → birlesik_plugins.json")
