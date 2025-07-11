import requests
import json
from urllib.parse import urlparse

# (url, kaynak_ismi) ikilisi olarak tanımla
plugin_sources = [
    ("https://raw.githubusercontent.com/GitLatte/Sinetech/refs/heads/builds/plugins.json", "Latte"),
    ("https://raw.githubusercontent.com/feroxx/Kekik-cloudstream/refs/heads/builds/plugins.json", "feroxx"),
    ("https://raw.githubusercontent.com/Kraptor123/cs-kekikanime/refs/heads/builds/plugins.json", "kekikan"),
    ("https://raw.githubusercontent.com/nikyokki/nik-cloudstream/builds/plugins.json", "nikstream"),
    # Diğer kaynaklar buraya eklenebilir
]

birlesik_plugins = []

for url, kaynak_ismi in plugin_sources:
    try:
        print(f"[+] {url} indiriliyor...")
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, list):
            for plugin in data:
                ek = f"[{kaynak_ismi}]"
                plugin["internalName"] = plugin.get("internalName", "") + ek
                plugin["name"] = plugin.get("name", "") + ek
                birlesik_plugins.append(plugin)
        else:
            print(f"⚠️ {url} JSON dizisi değil! Atlandı.")
    except Exception as e:
        print(f"❌ {url} indirilemedi: {e}")

# Aynı id'li eklentilerin sonuncusunu al
unique_plugins = {}
for plugin in birlesik_plugins:
    pid = plugin.get("id") or plugin.get("internalName")  # fallback
    if pid:
        unique_plugins[pid] = plugin

birlesik_liste = list(unique_plugins.values())

# JSON dosyasını kaydet
with open("birlesik_plugins.json", "w", encoding="utf-8") as f:
    json.dump(birlesik_liste, f, indent=4, ensure_ascii=False)

print(f"\n✅ {len(birlesik_liste)} plugin başarıyla birleştirildi → birlesik_plugins.json")
