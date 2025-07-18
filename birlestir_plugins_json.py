import requests
import json
import hashlib
from datetime import datetime
import os
import re

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

# Önceki hash'leri ve önceki birleşmiş plugin verilerini yükle
# Bu, daha önce birleştirilmiş ve tarih etiketi eklenmiş açıklamaları korumak için gerekli.
plugin_hashes = {}
previous_merged_plugins = {}

if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cache_data = json.load(f)
            plugin_hashes = cache_data.get("hashes", {})
    except json.JSONDecodeError:
        print(f"⚠️ {CACHE_FILE} bozuk veya geçersiz JSON içeriyor. Yeniden oluşturulacak.")
        plugin_hashes = {}

# Önceki birleştirilmiş pluginleri yükle (birlesik_plugins.json dosyasından)
# Bu, değişmeyen pluginlerin açıklama tarihlerini korumamızı sağlar.
if os.path.exists("birlesik_plugins.json"):
    try:
        with open("birlesik_plugins.json", "r", encoding="utf-8") as bf:
            previous_merged_plugins_list = json.load(bf)
            previous_merged_plugins = {p.get("id") or p.get("internalName"): p for p in previous_merged_plugins_list}
    except json.JSONDecodeError:
        print(f"⚠️ birlesik_plugins.json bozuk veya geçersiz JSON içeriyor. Yeniden oluşturulacak.")
        previous_merged_plugins = {}

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

            # Orijinal açıklamayı al
            source_description = plugin.get("description", "").strip()
            
            # Hash hesaplaması için açıklamayı tarih etiketinden temizle
            description_for_hash = re.sub(r"^\[\d{2}\.\d{2}\.\d{4}\]\s*", "", source_description)

            # Hash için gereksiz alanları çıkar
            plugin_copy_for_hash = dict(plugin)
            plugin_copy_for_hash["description"] = description_for_hash
            for remove_field in ["fileSize", "status"]:
                plugin_copy_for_hash.pop(remove_field, None)

            plugin_str_for_hash = json.dumps(plugin_copy_for_hash, sort_keys=True)
            current_source_hash = hashlib.sha256(plugin_str_for_hash.encode("utf-8")).hexdigest()
            previous_cached_hash = plugin_hashes.get(plugin_id)

            # İsimlere kaynak etiketi ekle (bu kısım her zaman çalışmalı)
            kaynak_tag = f"[{kaynak_adi}]"
            for field in ["name", "internalName"]:
                if field in plugin and kaynak_tag not in plugin[field]:
                    plugin[field] += kaynak_tag
                # Eğer alan yoksa ve plugin_id varsa, varsayılan olarak kaynak_tag ekleyebiliriz.
                # Ancak bu durumda, plugin_id zaten var olduğu için field'ın da var olması beklenir.

            # Açıklama yönetimi
            if current_source_hash != previous_cached_hash:
                # Plugin değişti veya yeni, açıklamayı bugünkü tarihle güncelle
                print(f"🆕 Değişiklik algılandı: {plugin_id}")
                plugin["description"] = f"[{bugun_tarih}] {description_for_hash}"
                plugin_hashes[plugin_id] = current_source_hash # Yeni hash'i kaydet
            else:
                # Plugin değişmedi, önceki birleştirilmiş listeden açıklamasını al
                # Eğer daha önce birleştirilmiş listede varsa, onun açıklamasını kullan.
                # Yoksa, kaynak açıklamayı kullan (zaten temizlenmiş haliyle).
                if plugin_id in previous_merged_plugins:
                    plugin["description"] = previous_merged_plugins[plugin_id].get("description", source_description)
                else:
                    # Bu durum, cache dosyası yoksa veya plugin_id ilk kez işleniyorsa ortaya çıkar.
                    # Bu durumda, kaynak açıklamayı olduğu gibi bırakırız.
                    plugin["description"] = source_description 

            birlesik_plugins[plugin_id] = plugin # Birleşmiş listeye ekle/güncelle

    except requests.exceptions.RequestException as e:
        print(f"❌ {url} indirilirken ağ hatası oluştu: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ {url} JSON ayrıştırma hatası: {e}")
    except Exception as e:
        print(f"❌ {url} işlenirken beklenmeyen hata oluştu: {e}")

# JSON çıktısını yaz
birlesik_liste = list(birlesik_plugins.values())
with open("birlesik_plugins.json", "w", encoding="utf-8") as f:
    json.dump(birlesik_liste, f, indent=4, ensure_ascii=False)

# Cache dosyasını güncelle (sadece hash'leri sakla)
with open(CACHE_FILE, "w", encoding="utf-8") as f:
    json.dump({"hashes": plugin_hashes}, f, indent=4, ensure_ascii=False)

print(f"\n✅ {len(birlesik_liste)} plugin başarıyla birleştirildi → birlesik_plugins.json")
