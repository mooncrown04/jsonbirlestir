import requests
import json
from datetime import datetime

# Kaynak URL ve isim eşleşmeleri
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
            # ID varsa devam et
            if not isinstance(plugin, dict) or "id" not in plugin:
                continue

            etiket = f"[{kaynak_adi}]"

            for field in ["name", "internalName"]:
                if field in plugin:
                    if etiket not in plugin[field]:
                        plugin[field] = f"{plugin[field]}{etiket}"
                else:
                    plugin[field] = etiket

            eski_aciklama = plugin.get("description", "").strip()
            plugin["description"] = f"[{bugun_tarih}] {eski_aciklama}"

            birlesik_plugins.append(plugin)

    except Exception as e:
        print(f"❌ {url} indirilemedi: {e}")

# Aynı id'ye sahip olanlardan sadece sonuncusunu tut
unique_plugins = {}
for plugin in birlesik_plugins:
    pid = plugin.get("id")
    if pid:
        unique_plugins[pid] = plugin

birlesik_liste = list(unique_plugins.values())

with open("birlesik_plugins.json", "w", encoding="utf-8") as f:
    json.dump(birlesik_liste, f, indent=4, ensure_ascii=False)

print(f"\n✅ {len(birlesik_liste)} plugin başarıyla birleştirildi → birlesik_plugins.json")
