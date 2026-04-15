import requests
import json
import hashlib
from datetime import datetime
import os
import re

# Ayarlar
plugin_urls = { 
    "https://raw.githubusercontent.com/kerimmkirac/cs-kerim/builds/plugins.json": "kerim",
    "https://raw.githubusercontent.com/feroxx/Kekik-cloudstream/refs/heads/builds/plugins.json": "feroxx",
    "https://raw.githubusercontent.com/GitLatte/Sinetech/refs/heads/builds/plugins.json": "Latte",
    "https://raw.githubusercontent.com/Kraptor123/cs-kraptor/refs/heads/builds/plugins.json": "Kraptor",
    "https://raw.githubusercontent.com/Sertel392/Makotogecici/refs/heads/main/plugins.json": "makoto",
    "https://raw.githubusercontent.com/sarapcanagii/Pitipitii/builds/plugins.json": "sarapcanagii"
}

CACHE_FILE = "plugin_cache.json"
MERGED_PLUGINS_FILE = "birlesik_plugins.json"
bugun_tarih = datetime.now().strftime("%d.%m.%Y")

# --- ÖNBELLEK YÜKLEME ---
previous_cached_plugins = {}
if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cached_list = json.load(f)
            # Cache anahtarı: (id, kaynak)
            for p in cached_list:
                p_id = p.get('id') or p.get('internalName')
                # Eğer internalName'de zaten etiket varsa onu temizleyip anahtar yapalım ki eşleşme sağlıklı olsun
                clean_id = re.sub(r"\[.*?\]", "", p_id).strip()
                previous_cached_plugins[(clean_id, p.get('kaynak'))] = p
        print(f"✅ Cache yüklendi: {len(previous_cached_plugins)} plugin.")
    except Exception as e:
        print(f"⚠️ Cache hatası: {e}")

birlesik_plugins = []

# --- ANA DÖNGÜ ---
for url, kaynak_adi in plugin_urls.items():
    try:
        print(f"\n[+] {url} işleniyor...")
        response = requests.get(url, timeout=10)
        data = response.json()

        for plugin in data:
            original_id = plugin.get("id") or plugin.get("internalName")
            if not original_id: continue

            current_version = str(plugin.get("version", "0.0.0"))
            unique_key = (original_id, kaynak_adi)
            
            # Önceki veriyi cache'den çek
            old_plugin = previous_cached_plugins.get(unique_key)
            
            # Değişim kontrolü
            is_updated = False
            if old_plugin:
                old_version = str(old_plugin.get("version", "0.0.0"))
                if current_version != old_version:
                    is_updated = True # Versiyon değişmiş
                else:
                    is_updated = False # Versiyon aynı
            else:
                is_updated = True # Tamamen yeni eklenti

            # Tarih ve Açıklama Yönetimi
            clean_desc = re.sub(r"^\[\d{2}\.\d{2}\.\d{4}\]\s*", "", plugin.get("description", "")).strip()
            
            if is_updated:
                # Yeni tarih ata
                plugin["description"] = f"[{bugun_tarih}] {clean_desc}"
                print(f"🆕 GÜNCELLEME: {original_id} ({current_version})")
            else:
                # Eski tarihi (description'ı) aynen koru
                plugin["description"] = old_plugin.get("description", clean_desc)
                print(f"✅ AYNI: {original_id} (v{current_version})")

            # Görsel Düzenlemeler (İsimlere kaynak ekleme)
            kaynak_tag = f"[{kaynak_adi}]"
            if kaynak_tag not in plugin.get("name", ""):
                plugin["name"] = f"{plugin.get('name', '')}{kaynak_tag}"
            
            if "internalName" in plugin and kaynak_tag not in plugin["internalName"]:
                plugin["internalName"] = f"{plugin['internalName']}{kaynak_tag}"
            
            plugin["kaynak"] = kaynak_adi
            birlesik_plugins.append(plugin)

    except Exception as e:
        print(f"❌ Hata ({kaynak_adi}): {e}")

# --- KAYDETME ---
with open(MERGED_PLUGINS_FILE, "w", encoding="utf-8") as f:
    json.dump(birlesik_plugins, f, indent=4, ensure_ascii=False)

with open(CACHE_FILE, "w", encoding="utf-8") as f:
    json.dump(birlesik_plugins, f, indent=4, ensure_ascii=False)

print(f"\n🚀 İşlem tamam: {len(birlesik_plugins)} plugin hazır.")
