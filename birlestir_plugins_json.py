import requests
import json
import hashlib
from datetime import datetime
import os
import re

# Birleştirilecek plugins.json URL liste (URL: kaynak_adi)
plugin_urls = {
    "https://raw.githubusercontent.com/feroxx/Kekik-cloudstream/refs/heads/builds/plugins.json": "feroxx",
    "https://raw.githubusercontent.com/GitLatte/Sinetech/refs/heads/builds/plugins.json": "Latte",
    "https://raw.githubusercontent.com/Kraptor123/cs-kraptor/refs/heads/builds/plugins.json": "Kraptor",
    "https://raw.githubusercontent.com/Sertel392/Makotogecici/refs/heads/main/plugins.json": "makoto",
    "https://raw.githubusercontent.com/sarapcanagii/Pitipitii/builds/plugins.json": "sarapcanagii",
    "https://raw.githubusercontent.com/nikyokki/nik-cloudstream/builds/plugins.json": "nikstream"
}

CACHE_FILE = "plugin_cache.json"
MERGED_PLUGINS_FILE = "birlesik_plugins.json"
# Bulunulan anın tarihi: 20.10.2025
bugun_tarih = datetime.now().strftime("%d.%m.%Y")

previous_cached_plugins = {}

# --- ÖNBELLEK YÜKLEME KISMI ---
if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cached_list = json.load(f)
            # Önbellekte, eklenti kimliği ve kaynak adını bir anahtar olarak kullanıyoruz
            previous_cached_plugins = {
                # Benzersiz anahtar: (id/internalName, kaynak_adi)
                (p.get('id') or p.get('internalName'), p.get('kaynak', 'bilinmiyor')): p
                for p in cached_list
            }
        print(f"✅ Cache dosyası '{CACHE_FILE}' başarıyla yüklendi. Toplam önbelleklenmiş plugin: {len(previous_cached_plugins)}")
    except (json.JSONDecodeError, Exception) as e:
        print(f"⚠️ Cache dosyası '{CACHE_FILE}' okunurken bir sorun oluştu ({e}). Yeni bir tane oluşturulacak.")
        previous_cached_plugins = {}
else:
    print(f"ℹ️ Cache dosyası '{CACHE_FILE}' bulunamadı. Yeni bir tane oluşturulacak.")

birlesik_plugins = {}

def create_version_hash(plugin):
    """
    Sadece eklentinin ID'si, kaynağı ve VERSION'ını içeren bir hash oluşturur.
    Diğer alanlardaki değişiklikler (URL, iconUrl vb.) tarihi güncellemeyecektir.
    """
    hash_data = {
        "id": plugin.get("id") or plugin.get("internalName"),
        "version": plugin.get("version"),
        # 'kaynak' alanını da hash'e dahil et, bu benzersizliği garanti eder
        "kaynak": plugin.get("kaynak"), 
    }
    # JSON verisini sıralı anahtarlarla (sort_keys=True) string'e dönüştür
    hash_str = json.dumps(hash_data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(hash_str.encode("utf-8")).hexdigest()

# --- PLUGIN İNDİRME VE BİRLEŞTİRME KISMI ---
for url, kaynak_adi in plugin_urls.items():
    try:
        print(f"\n[+] {url} indiriliyor...")
        response = requests.get(url)
        response.raise_for_status() # HTTP hatalarını yakalamak için
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

            plugin["kaynak"] = kaynak_adi
            unique_key = (plugin_id, kaynak_adi)
            kaynak_tag = f"[{kaynak_adi}]"
            
            # İsimlere kaynak etiketi ekle
            plugin_name = plugin.get("name") or plugin.get("internalName")
            if plugin_name and kaynak_tag not in plugin_name:
                plugin["name"] = f"{plugin_name}{kaynak_tag}"
            
            # internalName'e kaynak etiketi ekle (mevcut mantık korunuyor)
            internal_name = plugin.get("internalName")
            # internalName genellikle plugin_id'ye eşittir, ancak tutarlılık için bu da etiketlenebilir
            if internal_name and kaynak_tag not in internal_name:
                 # internalName'i etiketsiz tutmak daha temizdir, ama sizin önceki kodunuzda vardı, bu yüzden koruyorum.
                plugin["internalName"] = f"{internal_name}{kaynak_tag}" 


            # --- VERSİYON KONTROL MANTIĞI ---
            is_new_or_updated = False
            
            # Eklenti önbellekte var mı?
            previous_cached_plugin = previous_cached_plugins.get(unique_key)
            
            if previous_cached_plugin:
                # Eklenti önbellekte mevcut, SADECE versiyon bazlı hash'i karşılaştır
                current_hash = create_version_hash(plugin)
                cached_hash = create_version_hash(previous_cached_plugin)
                
                # SADECE versiyon hash'i değişmiş mi?
                if current_hash != cached_hash:
                    is_new_or_updated = True
                else:
                    # Versiyon aynıysa, eski açıklamayı koru (is_new_or_updated = False kalır)
                    pass
            else:
                # Eklenti yeni, önbellekte yok (ilk kez görülüyor)
                is_new_or_updated = True

            
            # --- DESCRIPTION GÜNCELLEME MANTIĞI ---
            if is_new_or_updated:
                # Yeni veya versiyonu değişmişse açıklamayı bugünün tarihiyle güncelle
                print(f"🆕 Versiyon değişikliği veya yeni plugin algılandı: {plugin_id} (v{plugin.get('version', '?.?')} / {kaynak_adi}) - Açıklama güncelleniyor.")
                
                # Mevcut açıklamadan önceki tarihi temizle (varsa)
                source_description = re.sub(r"^\[\d{2}\.\d{2}\.\d{4}\]\s*", "", plugin.get("description", "")).strip()
                
                # Açıklamayı bugünün tarihiyle yeniden ekle
                plugin["description"] = f"[{bugun_tarih}] {source_description}"
            else:
                # Versiyon değişikliği yoksa, önbellekteki tarihi (description) koru
                if previous_cached_plugin:
                    # Sadece description alanını önbellekten al
                    plugin["description"] = previous_cached_plugin.get("description", "")
                    print(f"✅ Versiyon değişikliği yok: {plugin_id} (v{plugin.get('version', '?.?')} / {kaynak_adi}) - Önceki açıklama korunuyor.")
                else:
                    # Bu durumda buraya düşmek beklenmez, ama hata önlemek için tekrar bugünün tarihini atalım
                    source_description = re.sub(r"^\[\d{2}\.\d{2}\.\d{4}\]\s*", "", plugin.get("description", "")).strip()
                    plugin["description"] = f"[{bugun_tarih}] {source_description}"

            
            # Cache'e ve birleştirilmiş listeye eklentinin güncel halini (tarihli hali) kaydet
            birlesik_plugins[unique_key] = plugin

    except requests.exceptions.RequestException as e:
        print(f"❌ {url} indirilirken ağ hatası oluştu: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ {url} JSON ayrıştırma hatası: {e}")
    except Exception as e:
        print(f"❌ {url} işlenirken beklenmeyen hata oluştu: {e}")

# --- SONUÇLARI KAYDETME KISMI ---

# Dictionary'deki tüm plugin'leri liste formatına dönüştür
birlesik_liste = list(birlesik_plugins.values())

# Birleştirilmiş plugin listesini kaydet
with open(MERGED_PLUGINS_FILE, "w", encoding="utf-8") as f:
    # ensure_ascii=False, Türkçe karakterlerin doğru yazılması için önemlidir.
    json.dump(birlesik_liste, f, indent=4, ensure_ascii=False)

# Güncel (tarihleri kontrol edilmiş) plugin listesini ÖNBELLEK dosyasına kaydet
with open(CACHE_FILE, "w", encoding="utf-8") as f:
    json.dump(birlesik_liste, f, indent=4, ensure_ascii=False)

print(f"\n✅ {len(birlesik_liste)} plugin başarıyla birleştirildi → {MERGED_PLUGINS_FILE}")
print(f"✅ Önbellek dosyası '{CACHE_FILE}' güncellendi.")
