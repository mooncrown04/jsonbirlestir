import requests
import json
import hashlib
from datetime import datetime
import os

# Birleştirilecek plugins.json URL listesi (URL: kaynak_adi)
plugin_urls = {
    "https://raw.githubusercontent.com/GitLatte/Sinetech/refs/heads/builds/plugins.json": "Latte",
    "https://raw.githubusercontent.com/feroxx/Kekik-cloudstream/refs/heads/builds/plugins.json": "feroxx",
    "https://raw.githubusercontent.com/Kraptor123/cs-kekikanime/refs/heads/builds/plugins.json": "kekikan",
    "https://raw.githubusercontent.com/nikyokki/nik-cloudstream/builds/plugins.json": "nikstream"
}

# Önceki içeriklerin hash'lerini saklayan cache dosyası
CACHE_FILE = "plugin_cache.json"
bugun_tarih = datetime.now().strftime("%d.%m.%Y")

# Önceki hash'leri yükle
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        plugin_hashes = json.load(f)
else:
    plugin_hashes = {}

birlesik_plugins = {}

for url, kaynak_adi in plugin_urls.items():
    try:
        print(f"[+] {url} indiriliyor...")
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if not isinstance(data, list):
            print(f"⚠️ {url} JSON dizisi değil! Atlandı.")
            continue

        print(f"🔍 {url} → Tür: {type(data)} | Uzunluk: {len(data)}")

        for plugin in data:
            plugin_id = plugin.get("id") or plugin.get("internalName")
            if not plugin_id:
                print(f"⚠️ 'id' veya 'internalName' yok, atlandı → {plugin}")
                continue

            plugin_copy = dict(plugin)
            plugin_str = json.dumps(plugin_copy, sort_keys=True)
            plugin_hash = hashlib.sha256(plugin_str.encode("utf-8")).hexdigest()

            onceki_hash = plugin_hashes.get(plugin_id)

            kaynak_tag = f"[{kaynak_adi}]"
            for field in ["name", "internalName"]:
                if field in plugin and kaynak_tag not in plugin[field]:
                    plugin[field] += kaynak_tag
                elif field not in plugin:
                    plugin[field] = kaynak_tag

            if plugin_hash != onceki_hash:
                print(f"🆕 Değişiklik algılandı: {plugin_id}")
                eski_aciklama = plugin.get("description", "").strip()
                plugin["description"] = f"[{bugun_tarih}] {eski_aciklama}"

            birlesik_plugins[plugin_id] = plugin
            plugin_hashes[plugin_id] = plugin_hash

    except Exception as e:
        print(f"❌ {url} indirilemedi: {e}")

# JSON çıktısını yaz
birlesik_liste = list(birlesik_plugins.values())
with open("birlesik_plugins.json", "w", encoding="utf-8") as f:
    json.dump(birlesik_liste, f, indent=4, ensure_ascii=False)

# Cache dosyasını güncelle
with open(CACHE_FILE, "w", encoding="utf-8") as f:
    json.dump(plugin_hashes, f, indent=4, ensure_ascii=False)

print(f"\n✅ {len(birlesik_liste)} plugin başarıyla birleştirildi → birlesik_plugins.json")
