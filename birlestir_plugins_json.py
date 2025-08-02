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
    "https://raw.githubusercontent.com/Sertel392/Makotogecici/refs/heads/main/plugins.json": "makoto",
    "https://raw.githubusercontent.com/sarapcanagii/Pitipitii/builds/plugins.json": "sarapcanagii",
    "https://raw.githubusercontent.com/nikyokki/nik-cloudstream/builds/plugins.json": "nikstream"
}

# Önceki içeriklerin hash'lerini saklayan cache dosyası
CACHE_FILE = "plugin_cache.json" # Bu dosya artık tam plugin objelerini saklayacak
MERGED_PLUGINS_FILE = "birlesik_plugins.json"
bugun_tarih = datetime.now().strftime("%d.%m.%Y")

# Önceki önbelleklenmiş plugin verilerini yükle (tam objeler)
previous_cached_plugins_data = {} # plugin_id -> tam plugin objesi
if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cached_list = json.load(f)
            previous_cached_plugins_data = {p.get("id") or p.get("internalName"): p for p in cached_list}
        print(f"✅ Cache dosyası '{CACHE_FILE}' başarıyla yüklendi. Toplam önbelleklenmiş plugin: {len(previous_cached_plugins_data)}")
    except json.JSONDecodeError:
        print(f"⚠️ {CACHE_FILE} bozuk veya geçersiz JSON içeriyor. Yeniden oluşturulacak.")
        previous_cached_plugins_data = {}
    except Exception as e:
        print(f"❌ Cache dosyası yüklenirken beklenmeyen hata: {e}")
        previous_cached_plugins_data = {}
else:
    print(f"ℹ️ Cache dosyası '{CACHE_FILE}' bulunamadı. Yeni bir tane oluşturulacak.")

birlesik_plugins = {} # Son birleştirilmiş pluginler (plugin_id -> tam plugin objesi)

for url, kaynak_adi in plugin_urls.items():
    try:
        print(f"\n[+] {url} indiriliyor...")
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if not isinstance(data, list):
            print(f"⚠️ {url} JSON dizisi değil! Atlandı.")
            continue

        print(f"🔍 {url} → Toplam plugin: {len(data)}")

        for plugin in data:
            plugin_id = plugin.get("id") or plugin.get("internalName")
            if not plugin_id:
                print(f"⚠️ 'id' veya 'internalName' yok, atlandı → {plugin}")
                continue

            # Orijinal açıklamayı al
            source_description = plugin.get("description", "").strip()
            
            # Hash hesaplaması için açıklamayı tarih etiketinden temizle
            description_for_hash = re.sub(r"^\[\d{2}\.\d{2}\.\d{4}\]\s*", "", source_description).strip()

            # Mevcut plugin için hash hesapla (açıklama ve diğer hariç tutulan alanlar temizlenmiş haliyle)
            current_plugin_copy_for_hash = dict(plugin)
            current_plugin_copy_for_hash["description"] = description_for_hash
            for remove_field in ["fileSize", "status"]:
                current_plugin_copy_for_hash.pop(remove_field, None)
            
            try:
                current_plugin_str_for_hash = json.dumps(current_plugin_copy_for_hash, sort_keys=True, ensure_ascii=False)
            except TypeError as e:
                print(f"❌ Hata: Plugin '{plugin_id}' için mevcut hash oluşturulurken TypeError: {e}. Plugin verisi: {current_plugin_copy_for_hash}")
                continue
            current_source_hash = hashlib.sha256(current_plugin_str_for_hash.encode("utf-8")).hexdigest()

            # Önbellekteki plugin için hash hesapla (varsa)
            previous_cached_plugin = previous_cached_plugins_data.get(plugin_id)
            previous_cached_hash = None

            if previous_cached_plugin:
                cached_description_for_hash = re.sub(r"^\[\d{2}\.\d{2}\.\d{4}\]\s*", "", previous_cached_plugin.get("description", "")).strip()
                cached_plugin_copy_for_hash = dict(previous_cached_plugin)
                cached_plugin_copy_for_hash["description"] = cached_description_for_hash
                for remove_field in ["fileSize", "status"]:
                    cached_plugin_copy_for_hash.pop(remove_field, None)
                
                try:
                    cached_plugin_str_for_hash = json.dumps(cached_plugin_copy_for_hash, sort_keys=True, ensure_ascii=False)
                except TypeError as e:
                    print(f"❌ Hata: Plugin '{plugin_id}' için önbelleklenmiş hash oluşturulurken TypeError: {e}. Plugin verisi: {cached_plugin_copy_for_hash}")
                    # Eğer önbelleklenmiş pluginin hash'i hesaplanamazsa, bunu değişiklik olarak kabul et
                    previous_cached_hash = "ERROR_HASH" 
                else:
                    previous_cached_hash = hashlib.sha256(cached_plugin_str_for_hash.encode("utf-8")).hexdigest()

            print(f"--- Plugin: {plugin_id} ---")
            print(f"    Kaynak Açıklama (Ham): '{source_description}'")
            print(f"    Hash için Açıklama (Temiz): '{description_for_hash}'")
            print(f"    Mevcut Hash (Kaynak): {current_source_hash}")
            print(f"    Önceki Cache Hash: {previous_cached_hash}")
            print(f"    Hash Karşılaştırma Sonucu (Mevcut != Önceki): {current_source_hash != previous_cached_hash}")


            # İsimlere kaynak etiketi ekle (bu kısım her zaman çalışmalı)
            kaynak_tag = f"[{kaynak_adi}]"
            for field in ["name", "internalName"]:
                if field in plugin and kaynak_tag not in plugin[field]:
                    plugin[field] += kaynak_tag
                # Eğer alan yoksa ve plugin_id internalName ise, name alanına da kaynak_tag ekle
                elif field == "name" and "name" not in plugin and plugin_id == plugin.get("internalName"):
                    plugin["name"] = f"{plugin_id}{kaynak_tag}"

            # Açıklama yönetimi
            if current_source_hash != previous_cached_hash:
                # Plugin değişti veya yeni, açıklamayı bugünkü tarihle güncelle
                print(f"🆕 Değişiklik algılandı: {plugin_id} - Açıklama güncelleniyor.")
                plugin["description"] = f"[{bugun_tarih}] {description_for_hash}"
            else:
                # Plugin değişmedi, önceki önbelleklenmiş listeden açıklamasını al
                if previous_cached_plugin:
                    plugin["description"] = previous_cached_plugin.get("description", source_description)
                    print(f"✅ Değişiklik yok: {plugin_id} - Önceki açıklama korunuyor: '{plugin['description']}'")
                else:
                    # Bu durum, cache dosyası yoksa veya plugin_id ilk kez işleniyorsa ortaya çıkar.
                    # Bu durumda, kaynak açıklamayı olduğu gibi bırakırız.
                    plugin["description"] = source_description
                    print(f"ℹ️ Yeni plugin (önbelleklenmiş listede yok): {plugin_id} - Kaynak açıklama kullanılıyor: '{source_description}'")

            birlesik_plugins[plugin_id] = plugin # Birleşmiş listeye ekle/güncelle

    except requests.exceptions.RequestException as e:
        print(f"❌ {url} indirilirken ağ hatası oluştu: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ {url} JSON ayrıştırma hatası: {e}")
    except Exception as e:
        print(f"❌ {url} işlenirken beklenmeyen hata oluştu: {e}")

# JSON çıktısını yaz
birlesik_liste = list(birlesik_plugins.values())
with open(MERGED_PLUGINS_FILE, "w", encoding="utf-8") as f:
    json.dump(birlesik_liste, f, indent=4, ensure_ascii=False)

# Cache dosyasını güncelle (artık tam plugin objelerini saklayacak)
with open(CACHE_FILE, "w", encoding="utf-8") as f:
    json.dump(birlesik_liste, f, indent=4, ensure_ascii=False) # Tüm birleştirilmiş listeyi kaydet

print(f"\n✅ {len(birlesik_liste)} plugin başarıyla birleştirildi → {MERGED_PLUGINS_FILE}")
print(f"✅ Önbellek dosyası '{CACHE_FILE}' güncellendi.")
