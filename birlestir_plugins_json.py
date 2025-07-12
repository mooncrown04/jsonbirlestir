import requests
import json
import hashlib
from datetime import datetime
import os

plugin_urls = {
    "https://raw.githubusercontent.com/GitLatte/Sinetech/refs/heads/builds/plugins.json": "Latte",
    "https://raw.githubusercontent.com/feroxx/Kekik-cloudstream/refs/heads/builds/plugins.json": "feroxx",
    "https://raw.githubusercontent.com/Kraptor123/cs-kekikanime/refs/heads/builds/plugins.json": "kekikan",
    "https://raw.githubusercontent.com/nikyokki/nik-cloudstream/builds/plugins.json": "nikstream"
}

bugun_tarih = datetime.now().strftime("%d.%m.%Y")
gecmis_dosya = "plugin_cache.json"
gecmis_hashlar = {}

# Önceki hash'leri oku
if os.path.exists(gecmis_dosya):
    with open(gecmis_dosya, "r", encoding="utf-8") as f:
        gecmis_hashlar = json.load(f)

yeni_hashlar = {}
birlesik_plugins = []

def plugin_hash(plugin):
    return hashlib.md5(json.dumps(plugin, sort_keys=True).encode("utf-8")).hexdigest()

for url, kaynak_adi in plugin_urls.items():
    try:
        print(f"[+] {url} indiriliyor...")
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if not isinstance(data, list):
            print(f"⚠️ {url} JSON dizisi değil! Atlandı.")
            continue

        for plugin in data:
            plugin_id = plugin.get("id")
            if not plugin_id:
                continue

            eski_hash = gecmis_hashlar.get(plugin_id)
            yeni_hash = plugin_hash(plugin)
            yeni_hashlar[plugin_id] = yeni_hash

            # Değişiklik varsa description'a bugünkü tarihi ekle
            if eski_hash != yeni_hash:
                plugin["description"] = f"[{bugun_tarih}] {plugin.get('description', '').strip()}"

            # name ve internalName'e kaynak etiketi ekle
            kaynak_tag = f"[{kaynak_adi}]"
            for field in ["name", "internalName"]:
                if field in plugin and kaynak_tag not in plugin[field]:
                    plugin[field] = f"{plugin[field]}{kaynak_tag}"
                elif field not in plugin:
                    plugin[field] = kaynak_tag

            birlesik_plugins.append(plugin)

    except Exception as e:
        print(f"❌ {url} indirilemedi: {e}")

# Aynı id'ye sahip son plugin'i al
unique_plugins = {}
for plugin in birlesik_plugins:
    plugin_id = plugin.get("id")
    if plugin_id:
        unique_plugins[plugin_id] = plugin

birlesik_liste = list(unique_plugins.values())

# JSON'u yaz
with open("birlesik_plugins.json", "w", encoding="utf-8") as f:
    json.dump(birlesik_liste, f, indent=4, ensure_ascii=False)

# Yeni hash'leri cache dosyasına yaz
with open(gecmis_dosya, "w", encoding="utf-8") as f:
    json.dump(yeni_hashlar, f, indent=2, ensure_ascii=False)

print(f"\n✅ {len(birlesik_liste)} plugin başarıyla birleştirildi → birlesik_plugins.json")
