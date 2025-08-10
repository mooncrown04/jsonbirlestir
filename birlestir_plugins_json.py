import requests
import json
import hashlib
from datetime import datetime
import os
import re

# Birleştirilecek plugins.json URL listesi (URL: kaynak_adi)
plugin_urls = {
    "https://raw.githubusercontent.com/feroxx/Kekik-cloudstream/refs/heads/builds/plugins.json": "feroxx",
    "https://raw.githubusercontent.com/GitLatte/Sinetech/refs/heads/builds/plugins.json": "Latte",
    "https://raw.githubusercontent.com/Kraptor123/cs-kekikanime/refs/heads/builds/plugins.json": "kekikan",
    "https://raw.githubusercontent.com/Sertel392/Makotogecici/refs/heads/main/plugins.json": "makoto",
    "https://raw.githubusercontent.com/sarapcanagii/Pitipitii/builds/plugins.json": "sarapcanagii",
    "https://raw.githubusercontent.com/nikyokki/nik-cloudstream/builds/plugins.json": "nikstream"
}

CACHE_FILE = "plugin_cache.json"
MERGED_PLUGINS_FILE = "birlesik_plugins.json"
bugun_tarih = datetime.now().strftime("%d.%m.%Y")

previous_cached_plugins_data = {}
if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cached_list = json.load(f)
            # Önbellekteki verileri kaynak_adi ile birlikte anahtarla
            previous_cached_plugins_data = {
                f"{p.get('id') or p.get('internalName')}-{p.get('kaynak', 'bilinmiyor')}": p
                for p in cached_list
            }
        print(f"✅ Cache dosyası '{CACHE_FILE}' başarıyla yüklendi. Toplam önbelleklenmiş plugin: {len(previous_cached_plugins_data)}")
    except (json.JSONDecodeError, Exception) as e:
        print(f"⚠️ Cache dosyası '{CACHE_FILE}' okunurken bir sorun oluştu ({e}). Yeni bir tane oluşturulacak.")
        previous_cached_plugins_data = {}
else:
    print(f"ℹ️ Cache dosyası '{CACHE_FILE}' bulunamadı. Yeni bir tane oluşturulacak.")

birlesik_plugins = {}

def create_stable_hash(plugin):
    """
    Sadece pluginin kararlı bilgilerini içeren bir hash oluşturur.
    'description', 'fileSize', 'date' gibi değişken alanları hariç tutar.
    """
    hash_data = {
        "id": plugin.get("id"),
        "internalName": plugin.get("internalName"),
        "version": plugin.get("version"),
        "url": plugin.get("url"),
        "lang": plugin.get("lang"),
        "iconUrl": plugin.get("iconUrl"),
        "status": plugin.get("status"),
        # 'description' artık hash'e dahil edilmiyor
    }
    hash_str = json.dumps(hash_data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(hash_str.encode("utf-8")).hexdigest()

def compare_versions(version1, version2):
    """
    İki versiyon numarasını karşılaştırır (örnek: "1.2.3").
    """
    v1_parts = [int(p) for p in re.split(r'[.-]', version1)]
    v2_parts = [int(p) for p in re.split(r'[.-]', version2)]

    for p1, p2 in zip(v1_parts, v2_parts):
        if p1 > p2: return 1
        if p1 < p2: return -1

    if len(v1_parts) > len(v2_parts): return 1
    if len(v1_parts) < len(v2_parts): return -1

    return 0

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

            # Plugin'in kaynağını belirleyen benzersiz bir anahtar oluştur
            unique_key = f"{plugin_id}-{kaynak_adi}"

            # Plugin objesine kaynak_adi'ni ekle
            plugin["kaynak"] = kaynak_adi

            # İsimlere kaynak etiketi ekle
            kaynak_tag = f"[{kaynak_adi}]"
            plugin_name = plugin.get("name") or plugin.get("internalName")
            if plugin_name and kaynak_tag not in plugin_name:
                plugin["name"] = f"{plugin_name}{kaynak_tag}"
                
            try:
                current_source_hash = create_stable_hash(plugin)
                previous_cached_plugin = previous_cached_plugins_data.get(unique_key)
                previous_cached_hash = create_stable_hash(previous_cached_plugin) if previous_cached_plugin else None
                
                # Açıklama yönetimi
                if current_source_hash != previous_cached_hash:
                    # Plugin değişti veya yeni, açıklamayı bugünün tarihiyle güncelle
                    print(f"🆕 Değişiklik veya yeni plugin algılandı: {plugin_id} ({kaynak_adi}) - Açıklama güncelleniyor.")
                    source_description = re.sub(r"^\[\d{2}\.\d{2}\.\d{4}\]\s*", "", plugin.get("description", "")).strip()
                    plugin["description"] = f"[{bugun_tarih}] {source_description}"
                else:
                    # Plugin değişmedi, önbellekteki açıklamayı kullan
                    if previous_cached_plugin:
                        plugin["description"] = previous_cached_plugin.get("description", "")
                        print(f"✅ Değişiklik yok: {plugin_id} ({kaynak_adi}) - Önceki açıklama korunuyor.")
                    else:
                        print(f"⚠️ {plugin_id} ({kaynak_adi}) için hashler eşit olmasına rağmen önbellek yok. Açıklama güncelleniyor.")
                        source_description = re.sub(r"^\[\d{2}\.\d{2}\.\d{4}\]\s*", "", plugin.get("description", "")).strip()
                        plugin["description"] = f"[{bugun_tarih}] {source_description}"


            except Exception as e:
                print(f"❌ Plugin '{plugin_id}' ({kaynak_adi}) işlenirken hata oluştu: {e}. Bu plugin atlandı.")
                continue

            birlesik_plugins[unique_key] = plugin

    except requests.exceptions.RequestException as e:
        print(f"❌ {url} indirilirken ağ hatası oluştu: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ {url} JSON ayrıştırma hatası: {e}")
    except Exception as e:
        print(f"❌ {url} işlenirken beklenmeyen hata oluştu: {e}")

birlesik_liste = list(birlesik_plugins.values())
with open(MERGED_PLUGINS_FILE, "w", encoding="utf-8") as f:
    json.dump(birlesik_liste, f, indent=4, ensure_ascii=False)

with open(CACHE_FILE, "w", encoding="utf-8") as f:
    json.dump(birlesik_liste, f, indent=4, ensure_ascii=False)

print(f"\n✅ {len(birlesik_liste)} plugin başarıyla birleştirildi → {MERGED_PLUGINS_FILE}")
print(f"✅ Önbellek dosyası '{CACHE_FILE}' güncellendi.")
