import requests
import json
from datetime import datetime
from urllib.parse import urlparse

# 🔗 URL ve kaynak ismi eşleşmeleri
plugin_urls = {
    ("https://raw.githubusercontent.com/GitLatte/Sinetech/refs/heads/builds/plugins.json", "Latte"),
    ("https://raw.githubusercontent.com/feroxx/Kekik-cloudstream/refs/heads/builds/plugins.json", "feroxx"),
    ("https://raw.githubusercontent.com/Kraptor123/cs-kekikanime/refs/heads/builds/plugins.json", "kekikan"),
    ("https://raw.githubusercontent.com/nikyokki/nik-cloudstream/builds/plugins.json", "nikstream"),
    # Yeni ekle: "URL": "isim"
}

birlesik_plugins = []
bugun = datetime.now().strftime("%d.%m.%Y")

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
            if not isinstance(plugin, dict) or "id" not in plugin:
                print(f"⚠️ Geçersiz plugin formatı atlandı: {plugin}")
                continue

            # 🔁 Kaynak etiketini internalName ve name'e ekle
            etiket = f"[{kaynak_adi}]"
            for alan in ("internalName", "name"):
                if alan in plugin:
                    plugin[alan] = f"{plugin[alan]}{etiket}" if etiket not in plugin[alan] else plugin[alan]

            # 📆 Description'a tarih ekle
            eski_desc = plugin.get("description", "").strip()
            plugin["description"] = f"[{bugun}] {eski_desc}".strip()

            birlesik_plugins.append(plugin)

    except Exception as e:
        print(f"❌ {url} indirilemedi: {e}")

# 🔄 Aynı ID'ye sahiplerden sadece sonuncuyu al
unique_plugins = {plugin["id"]: plugin for plugin in birlesik_plugins}
birlesik_liste = list(unique_plugins.values())

# 💾 Dosyaya yaz
with open("birlesik_plugins.json", "w", encoding="utf-8") as f:
    json.dump(birlesik_liste, f, indent=4, ensure_ascii=False)

print(f"\n✅ {len(birlesik_liste)} plugin başarıyla birleştirildi → birlesik_plugins.json")
