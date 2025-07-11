import requests
import json
from datetime import datetime

# Birleştirilecek plugins.json URL listesi (URL: kaynak_adi)
plugin_urls = {
    "https://raw.githubusercontent.com/GitLatte/Sinetech/refs/heads/builds/plugins.json": "Latte",
    "https://raw.githubusercontent.com/feroxx/Kekik-cloudstream/refs/heads/builds/plugins.json": "feroxx",
    "https://raw.githubusercontent.com/Kraptor123/cs-kekikanime/refs/heads/builds/plugins.json": "kekikan",
    "https://raw.githubusercontent.com/nikyokki/nik-cloudstream/builds/plugins.json": "nikstream"
}

birlesik_plugins = []

bugun_tarih = datetime.now().strftime("%d.%m.%Y")

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
            # Tag'lara [kaynak] ekle
            kaynak_tag = f"[{kaynak_adi}]"

            # name ve internalName'e kaynak etiketi eklenmiş mi, kontrol et
            for field in ["name", "internalName"]:
                if field in plugin and kaynak_tag not in plugin[field]:
                    plugin[field] = f"{plugin[field]}{kaynak_tag}"
                elif field not in plugin:
                    plugin[field] = kaynak_tag

            # description'a tarih bilgisi ekle
            plugin["description"] = f"[{bugun_tarih}] {plugin.get('description', '').strip()}"

            birlesik_plugins.append(plugin)

    except Exception as e:
        print(f"❌ {url} indirilemedi: {e}")

# Aynı id'ye sahipleri eleyip sadece sonuncuyu tut
unique_plugins = {}
for plugin in birlesik_plugins:
    plugin_id = plugin.get("id")
    if plugin_id:
        unique_plugins[plugin_id] = plugin

birlesik_liste = list(unique_plugins.values())

# JSON'u yaz
with open("birlesik_plugins.json", "w", encoding="utf-8") as f:
    json.dump(birlesik_liste, f, indent=4, ensure_ascii=False)

print(f"\n✅ {len(birlesik_liste)} plugin başarıyla birleştirildi → birlesik_plugins.json")
