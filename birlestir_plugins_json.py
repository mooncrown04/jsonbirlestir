import requests
import json

# Birleştirilecek plugins.json URL listesi
plugin_urls = [
    "https://raw.githubusercontent.com/GitLatte/Sinetech/refs/heads/builds/plugins.json",
   "https://raw.githubusercontent.com/feroxx/Kekik-cloudstream/refs/heads/builds/plugins.json",
   "https://raw.githubusercontent.com/Kraptor123/cs-kekikanime/refs/heads/builds/plugins.json",
   "https://raw.githubusercontent.com/nikyokki/nik-cloudstream/builds/plugins.json",
    # Buraya ek URL'leri ekleyebilirsin
    # "https://example.com/another/plugins.json"
]

birlesik_plugins = []

for url in plugin_urls:
    try:
        print(f"[+] {url} indiriliyor...")
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, list):
            birlesik_plugins.extend(data)
        else:
            print(f"⚠️ {url} JSON dizisi değil! Atlandı.")
    except Exception as e:
        print(f"❌ {url} indirilemedi: {e}")
for plugin in birlesik_plugins:
    if "id" not in plugin:
        if "internalName" in plugin:
            plugin["id"] = plugin["internalName"]
        elif "name" in plugin:
            plugin["id"] = plugin["name"]

# Aynı id'ye sahipleri eleyip sadece sonuncuyu tut
unique_plugins = {plugin["id"]: plugin for plugin in birlesik_plugins}
birlesik_liste = list(unique_plugins.values())

# Çıktıyı yaz
with open("birlesik_plugins.json", "w", encoding="utf-8") as f:
    json.dump(birlesik_liste, f, indent=4, ensure_ascii=False)

print(f"\n✅ {len(birlesik_liste)} plugin başarıyla birleştirildi → birlesik_plugins.json")
