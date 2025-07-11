import requests
import json

# URL ve isim listesi
plugin_sources = [
    ("https://raw.githubusercontent.com/GitLatte/Sinetech/refs/heads/builds/plugins.json", "Latte"),
    ("https://raw.githubusercontent.com/feroxx/Kekik-cloudstream/refs/heads/builds/plugins.json", "feroxx"),
    ("https://raw.githubusercontent.com/Kraptor123/cs-kekikanime/refs/heads/builds/plugins.json", "kekikan"),
    ("https://raw.githubusercontent.com/nikyokki/nik-cloudstream/builds/plugins.json", "nikstream"),
]

birlesik_plugins = []

for url, kaynak_ismi in plugin_sources:
    try:
        print(f"[+] {url} indiriliyor...")
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if not isinstance(data, list):
            print(f"⚠️ {url} JSON dizisi değil! Atlandı.")
            continue

        for plugin in data:
            if "name" in plugin and "internalName" in plugin:
                plugin["name"] = f"{plugin['name']}[{kaynak_ismi}]"
                plugin["internalName"] = f"{plugin['internalName']}[{kaynak_ismi}]"
            birlesik_plugins.append(plugin)

    except Exception as e:
        print(f"❌ {url} indirilemedi: {e}")

# Aynı ID’ye sahip içerikler de dahil edilir (sonuncular öncelikli)
unique_plugins = {}
for plugin in birlesik_plugins:
    plugin_id = plugin.get("id")
    if plugin_id:
        unique_plugins.setdefault(plugin_id, []).append(plugin)

# Her ID için sonuncuyu tut
birlesik_liste = [v[-1] for v in unique_plugins.values()]

# JSON olarak kaydet
with open("birlesik_plugins.json", "w", encoding="utf-8") as f:
    json.dump(birlesik_liste, f, indent=4, ensure_ascii=False)

print(f"\n✅ {len(birlesik_liste)} plugin başarıyla birleştirildi → birlesik_plugins.json")
