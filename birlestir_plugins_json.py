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

def create_stable_hash(plugin):
    """
    Sadece pluginin kararlı bilgilerini içeren bir hash oluşturur.
    fileSize, date gibi değişken alanları hariç tutar.
    """
    hash_data = {
        "id": plugin.get("id"),
        "internalName": plugin.get("internalName"),
        "version": plugin.get("version"),
        "url": plugin.get("url"),
        "lang": plugin.get("lang"),
        "iconUrl": plugin.get("iconUrl"),
        "status": plugin.get("status"),
        # Açıklamayı hash'e dahil etmeden önce tarih etiketini temizle
        "description_clean": re.sub(r"^\[\d{2}\.\d{2}\.\d{4}\]\s*", "", plugin.get("description", "")).strip()
    }
    hash_str = json.dumps(hash_data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(hash_str.encode("utf-8")).hexdigest()

def compare_versions(version1, version2):
    """
    İki versiyon numarasını karşılaştırır (örnek: "1.2.3").
    version1 > version2 ise 1, version1 < version2 ise -1, eşitse 0 döndürür.
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

            # Mevcut birleştirilmiş listede aynı ID'ye sahip plugin var mı kontrol et
            if plugin_id in birlesik_plugins:
                current_merged_plugin = birlesik_plugins[plugin_id]
                current_merged_version = current_merged_plugin.get("version", "0.0.0")
                incoming_version = plugin.get("version", "0.0.0")

                # Gelen pluginin versiyonu, birleştirilmiş listedekinden daha eski mi?
                if compare_versions(incoming_version, current_merged_version) <= 0:
                    print(f"⏩ {plugin_id} için daha yeni bir versiyon mevcut. Bu plugin atlanıyor.")
                    continue

                print(f"🔄 {plugin_id} için daha yeni versiyon ({incoming_version}) bulundu. Eski versiyon ({current_merged_version}) güncelleniyor.")

            # Hata olmadığından emin olmak için try/except bloklarına aldım
            try:
                # Mevcut plugin için hash hesapla
                current_source_hash = create_stable_hash(plugin)

                # Önbellekteki plugin için hash hesapla (varsa)
                previous_cached_plugin = previous_cached_plugins_data.get(plugin_id)
                previous_cached_hash = None
                if previous_cached_plugin:
                    previous_cached_hash = create_stable_hash(previous_cached_plugin)
                
                # İsimlere kaynak etiketi ekle
                kaynak_tag = f"[{kaynak_adi}]"
                plugin_name = plugin.get("name") or plugin.get("internalName")
                if plugin_name and kaynak_tag not in plugin_name:
                    plugin["name"] = f"{plugin_name}{kaynak_tag}"

                # Açıklama yönetimi
                if current_source_hash != previous_cached_hash:
                    # Plugin değişti veya yeni, açıklamayı bugünkü tarihle güncelle
                    print(f"🆕 Değişiklik veya yeni plugin algılandı: {plugin_id} - Açıklama güncelleniyor.")
                    # Orijinal açıklamayı al ve tarih etiketini ekle
                    source_description = re.sub(r"^\[\d{2}\.\d{2}\.\d{4}\]\s*", "", plugin.get("description", "")).strip()
                    plugin["description"] = f"[{bugun_tarih}] {source_description}"
                else:
                    # Plugin değişmedi, önceki önbelleklenmiş listeden açıklamasını al
                    if previous_cached_plugin:
                        plugin["description"] = previous_cached_plugin.get("description", plugin.get("description"))
                        print(f"✅ Değişiklik yok: {plugin_id} - Önceki açıklama korunuyor: '{plugin['description']}'")
                    else:
                        # Bu durum, cache dosyası yoksa veya plugin_id ilk kez işleniyorsa ortaya çıkar.
                        print(f"ℹ️ Yeni plugin (önbelleklenmiş listede yok): {plugin_id} - Kaynak açıklama kullanılıyor: '{plugin.get('description', '')}'")

            except Exception as e:
                print(f"❌ Plugin '{plugin_id}' işlenirken hata oluştu: {e}. Bu plugin atlandı.")
                continue

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
