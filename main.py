# ==========================================
# AI COIN ASSISTANT - V6 | ERKEN PUAN + ASSISTANT ANA AL + %4 KAR
# Taban: main (21).py
# 21 sadeligi + 13 AL/SAT/Kar Koru + 1-3-5-10 dk erken yakalama
# Giris/Devam skorları sadece bilgi, AL için veto DEGIL
# Fast Scan V1: 60 sn hızlı ön tarama + 5 dk tam tarama
# AL Relax V1: normal AL için ADX 27 / AI 80
# Final Cleanup / Core Candidate Scanner
# Candidate thresholds synced with latest working Coin Radar
# Learning Contribution V1: vr310 + stair5 + 3dk + 60dk relative strength + RSI; small ranking bonus, no AL veto
# ==========================================

import os
import time
import json
import requests
import feedparser
import statistics
import html


BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

CHAT_IDS = [2097448038]

TARAMA_SURESI = 60
TAM_TARAMA_DONGUSU = 5          # 5 x 60 sn = yaklaşık 5 dk
HIZLI_HAREKET_ESIGI = 0.40      # 1 dakikalık fiyat değişimi %0.40+ ise hemen derin analiz
son_fiyatlar = {}
tarama_sayaci = 0
SON_PIYASA_MEDYAN_60 = 0.0  # Son tam taramadaki TRY coinleri 60dk medyanı

# Early Capture V1: önceki taramadaki hızlanmayı ölçmek için hafıza.
onceki_tarama = {}

# Kalıcılık V1: yalnızca bilgi amaçlıdır; Radar/AL filtrelerini DEĞİŞTİRMEZ.
kalicilik_gecmisi = {}
KALICILIK_GECMIS_UZUNLUK = 5

# Çoklu Güç Havuzu:
# Güçlenme işareti veren coin 5 dakika boyunca, 1 dk fiyat hareketi %0.40 altında kalsa bile izlenir.
guc_izleme_havuzu = {}
GUC_IZLEME_SURESI = 5 * 60

# Aynı kararın tekrar Telegram gönderimini engeller.
son_ai_kararlar = {}

# Sade birleşik: açık AL takibi
AL_TAKIP = {}

# 5+ Güç Fiyat Teyidi: SADECE görsel/izleme katmanı.
# AL/BEKLE/SAT kriterlerini, aday filtrelerini veya sıralamayı değiştirmez.
BES_FIYAT_TEYIT = {}
BES_FIYAT_TEYIT_SURESI = 5 * 60
BES_FIYAT_TEYIT_HEDEF = 0.50
BES_FIYAT_TEYIT_TUTUNMA = 0.35
BES_FIYAT_TEYIT_ARDISIK = 2

POZISYON_TAKIP_SURESI = 15
KAR_BILDIR_ESIK = 5.0
KAR_KORU_ORAN = 40
ILK_ZARAR_KES = -0.8
TEPE_GERI_VERME = -1.4
MIN_KAR_KORUMA = 2.5

# AL Rejim / Seçicilik Öğrenmesi
# AL öğrenme verisini Railway Volume varsa kalıcı alanda tut.
# AL_OGRENME_DOSYA env ile özel yol verilmişse onu kullanır.
_RAILWAY_VOLUME = os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "").strip()
_AL_DEFAULT_DIR = _RAILWAY_VOLUME if _RAILWAY_VOLUME else ("/data" if os.path.isdir("/data") else ".")
AL_OGRENME_DOSYA = os.getenv("AL_OGRENME_DOSYA", os.path.join(_AL_DEFAULT_DIR, "al_ogrenme_rejim.json"))
AL_TAKIP_DOSYA = os.getenv("AL_TAKIP_DOSYA", os.path.join(_AL_DEFAULT_DIR, "v11_al_takip.json"))
AL_OGRENME_SURESI = 3 * 60 * 60
REJIM_RAPOR_ARALIGI = 24 * 60 * 60
SON_REJIM_RAPOR_ZAMANI = time.time()

# Assistant Kod Geliştirme Öneri Motoru
# Son 7 günlük AL sonuçlarını mevcut dosya kuralları ve piyasa rejimiyle birlikte karşılaştırır; AL mantığını otomatik değiştirmez.
# Telegram'da EKLE / GÜÇLENDİR / AZALT / ÇIKAR / REJİME GÖRE AYIR önerisi üretir.
GELISTIRME_RAPOR_ARALIGI = 7 * 24 * 60 * 60
GELISTIRME_PENCERE = 7 * 24 * 60 * 60
GELISTIRME_MIN_KAYIT = 20
GELISTIRME_MIN_GRUP = 5

# Geliştirme motoru V2:
# - küçük örneklemde aşırı güven yazmaz
# - tek gün/tek rejim sonucuyla "çıkar" demez
# - aynı yöndeki sonucu günler ve rejimler arasında tekrar test eder
# - korelasyon/puan şişmesi ve aşırı yüksek skor paradoksunu ayrıca arar
# - önerilere öncelik verir; kodu otomatik değiştirmez
GELISTIRME_MIN_GUN_GUCLU = 3
GELISTIRME_MIN_REJIM_GUCLU = 2
GELISTIRME_DUSUK_N = 20
GELISTIRME_ORTA_N = 50
GELISTIRME_YUKSEK_N = 100

# Haftalık raporda aynı kalite yapısını tekrar eden dört puanı ayrı ayrı
# ödüllendirmeden tek gölge blok olarak sınar. Canlı AL filtresine bağlı değil.
DEVAM_KALITE_GENEL_MIN = 67.50
DEVAM_KALITE_DEVAM_MIN = 81.45
DEVAM_KALITE_ODAK_MIN = 74.50
DEVAM_KALITE_D10_MIN = 0.90
DEVAM_KALITE_KARAR_MIN = 30

STRATEJI_SURUMU = "V11_ERKEN_YAKALA_DEVAM_GUCU"

# V11 CANLI YUMUŞAK SÜZGEÇ
# Amaç V11'in hareket yakalama gücünü koruyup, yalnız birkaç zayıflığın aynı
# anda bulunduğu en düşük kaliteli yaklaşık %20-25'lik mesaj grubunu ayıklamak.
# Tek bir eşik veya düşük ADX tek başına veto değildir.
V11_FILTRE_AI_ESIK = 83.69
V11_FILTRE_DEVAM_ESIK = 71.20
V11_FILTRE_YANLIS_TEPKI = -1.5
V11_ASIRI_REL_ESIK = 4.0
V11_TEMIZ_MOM_MIN_POZITIF = 3
V11_TEKRAR_SOGUMA = 30 * 60
V11_TEKRAR_HIT5_BEKLEME = 3 * 60 * 60
V11_TEKRAR_YENI_HAREKET = 1.5

# V11 GİRİŞ ZAMANI KORUMASI
# V11 adayı, hareket zaten büyük ölçüde yaşandıktan sonra gelirse AL değildir.
# Aday Telegram'da uyarı olarak görünür ve gölgede ölçülür; canlı AL takibine
# veya ilerideki otomatik gerçek-emir kapısına girmez.
V11_GEC_D5_MAX = 3.0
V11_GEC_D10_MAX = 4.5
V11_GEC_RSI_MAX = 72.0
V11_UST_DUZEY_ERKEN_MIN = 60
V11_SEVIYE2_AI_MIN = 90.0
V11_SEVIYE2_DEVAM_MIN = 80.0
V11_SEVIYE2_RADAR_MIN = 60.0
# Üst Düzey AL içindeki daha kontrollü alt profil. Bu sınıf yalnız mesaj ve
# öğrenme ayrımıdır; otomatik/gerçek emir üretmez ve V11 AL kapısını değiştirmez.
V11_KONTROLLU_DEVAM_MIN = 82.0
V11_KONTROLLU_KALICILIK_MIN = 88.0
V11_KONTROLLU_KALICILIK_MAX = 94.0
V11_KONTROLLU_ADX_MIN = 30.0
V11_KONTROLLU_RSI_MIN = 52.0
V11_KONTROLLU_RSI_MAX = 70.0

# 3 günlük ortak karşılaştırma raporu

# ORTAK 3 GÜNLÜK RAPOR TAKVİMİ
# İlk karşılaştırma: 06.10.2026 08:00 Türkiye saati (UTC+3).
# Sonraki raporlar her 3 günde bir yine 08:00'de.
ILK_3GUN_RAPOR_TS = 1791262800.0
YUZDE5_RAPOR_ARALIGI = 3 * 24 * 60 * 60

# BIST/BTCTurk ekranındaki gibi, günlük değişime göre ilk 10'a giren TRY
# coinlerini gölgede izler. Bu katman AL üretmez; yalnız kaçan hareketin ilk
# görüldüğü andaki profilini, hangi V11 kapısında kaldığını ve sonraki 3 saatte
# ne yaptığını 3 günlük rapora taşır.
TOP10_GOLGE_SURESI = 3 * 60 * 60
TOP10_GOLGE_DOSYA = os.getenv(
    "TOP10_GOLGE_DOSYA",
    os.path.join(_AL_DEFAULT_DIR, "v11_top10_kacan_hareket.json"),
)
TOP10_GOLGE_MAX_KAYIT = 3000
TOP10_KOD_ONERI_MIN_ORNEK = 8
_TOP10_AKTIF_SYMBOLLER = set()

# Rolling ilk 10'a günlük en az +%1 ile giren coinleri normal Radar/tam tarama
# kapısını beklemeden beş dakika boyunca yalnız gölgede inceler. Bu havuz canlı
# aday listesine eklenmez, Telegram veya gerçek emir üretmez.
TOP10_HIZLI_GUNLUK_MIN = 1.0
TOP10_HIZLI_TAKIP_SURESI = 5 * 60
TOP10_HIZLI_DONUS_TEYIDI = 0.5
TOP10_HIZLI_CEKILISLER = (1.0, 1.5, 2.0)
TOP10_HIZLI_KARAR_MIN = 30

# Telegram Üst/Güçlü AL ve İZLE mesajından sonra giriş zamanını ölçen gölge
# deney. Sınıflar ayrı raporlanır; canlı mesajı, AL kararını veya gerçek emri
# değiştirmez.
GIRIS_DENEYI_DOSYA = os.getenv(
    "GIRIS_DENEYI_DOSYA",
    os.path.join(_AL_DEFAULT_DIR, "v11_al_giris_zamani_deneyi.json"),
)
GIRIS_DENEYI_SURESI = 3 * 60 * 60
GIRIS_DENEYI_CEKILIS_PENCERESI = 30 * 60
GIRIS_DENEYI_CEKILISLER = (1.0, 1.5, 2.0, 2.5, 3.0)
GIRIS_DENEYI_DONUS_TEYIDI = 0.5
GIRIS_DENEYI_KARAR_MIN = 30
GIRIS_DENEYI_MAX_KAYIT = 3000


def _top10_golge_yukle():
    try:
        if os.path.exists(TOP10_GOLGE_DOSYA):
            with open(TOP10_GOLGE_DOSYA, "r", encoding="utf-8") as f:
                veri = json.load(f)
            return veri if isinstance(veri, list) else []
    except Exception as e:
        print("Top10 gölge dosyası okunamadı:", e)
    return []


def _top10_golge_kaydet():
    try:
        klasor = os.path.dirname(os.path.abspath(TOP10_GOLGE_DOSYA))
        if klasor:
            os.makedirs(klasor, exist_ok=True)
        gecici = TOP10_GOLGE_DOSYA + ".tmp"
        with open(gecici, "w", encoding="utf-8") as f:
            json.dump(TOP10_GOLGE_KAYITLARI[-TOP10_GOLGE_MAX_KAYIT:], f, ensure_ascii=False)
        os.replace(gecici, TOP10_GOLGE_DOSYA)
    except Exception as e:
        print("Top10 gölge dosyası yazılamadı:", e)


def _top10_gun_anahtari(ts=None):
    # Railway UTC çalışsa da rapor günü Türkiye saatine göre ayrılsın.
    return time.strftime("%Y-%m-%d", time.gmtime(float(ts or time.time()) + 3 * 3600))


def _ticker_gunluk_yuzde(coin):
    try:
        if coin.get("dailyPercent") is not None:
            return float(coin.get("dailyPercent") or 0)
        son = float(coin.get("last", 0) or 0)
        acilis = float(coin.get("open", 0) or 0)
        return _pct(son, acilis) if son > 0 and acilis > 0 else 0.0
    except Exception:
        return 0.0


def _top10_hizli_varyant_anahtari(esik):
    return f"donus_{float(esik):.1f}"


def _top10_hizli_varyantlar_yeni():
    return {
        _top10_hizli_varyant_anahtari(esik): {
            "esik": float(esik), "kuruldu": False, "dip_fiyat": None,
            "giris": None, "giris_zamani": None, "max_getiri": None,
            "min_getiri": None, "son_getiri": None,
        }
        for esik in TOP10_HIZLI_CEKILISLER
    }


def _top10_bugunku_kayit(symbol):
    gun = _top10_gun_anahtari()
    return next(
        (k for k in reversed(TOP10_GOLGE_KAYITLARI)
         if k.get("symbol") == symbol and k.get("gun") == gun),
        None,
    )


def top10_hizli_aktif_mi(symbol=None):
    """İlk 5 dakikalık hızlı gölge havuzunun aktif olup olmadığını döndürür."""
    simdi = time.time()
    for k in TOP10_GOLGE_KAYITLARI:
        if symbol and k.get("symbol") != symbol:
            continue
        if not k.get("hizli_takip_uygun") or k.get("tamamlandi"):
            continue
        if simdi - float(k.get("zaman", simdi) or simdi) <= TOP10_HIZLI_TAKIP_SURESI:
            return True
    return False


def top10_hizli_fiyat_guncelle(ticker):
    """Hızlı havuzda çekiliş+dönüş girişini ve sonraki getiriyi gölgede ölçer."""
    if not TOP10_GOLGE_KAYITLARI:
        return
    fiyatlar = {}
    for coin in ticker:
        try:
            symbol = str(coin.get("pair", ""))
            fiyat = float(coin.get("last", 0) or 0)
            if symbol and fiyat > 0:
                fiyatlar[symbol] = fiyat
        except Exception:
            continue

    simdi = time.time()
    degisti = False
    for k in TOP10_GOLGE_KAYITLARI:
        if not k.get("hizli_takip_uygun") or k.get("tamamlandi"):
            continue
        fiyat = fiyatlar.get(k.get("symbol"))
        ilk = float(k.get("giris", 0) or 0)
        if not fiyat or ilk <= 0:
            continue
        gecen = simdi - float(k.get("zaman", simdi) or simdi)
        varyantlar = k.setdefault("hizli_donuslar", _top10_hizli_varyantlar_yeni())

        if gecen <= TOP10_HIZLI_TAKIP_SURESI:
            k["hizli_dip"] = min(float(k.get("hizli_dip", ilk) or ilk), fiyat)
            k["hizli_tepe"] = max(float(k.get("hizli_tepe", ilk) or ilk), fiyat)
            ilk_getiri = _pct(fiyat, ilk)
            for esik in TOP10_HIZLI_CEKILISLER:
                anahtar = _top10_hizli_varyant_anahtari(esik)
                v = varyantlar.setdefault(anahtar, _top10_hizli_varyantlar_yeni()[anahtar])
                if ilk_getiri <= -float(esik):
                    v["kuruldu"] = True
                    eski_dip = v.get("dip_fiyat")
                    v["dip_fiyat"] = fiyat if not eski_dip else min(float(eski_dip), fiyat)
                if v.get("kuruldu") and not v.get("giris"):
                    dip = float(v.get("dip_fiyat", 0) or 0)
                    if dip > 0 and _pct(fiyat, dip) >= TOP10_HIZLI_DONUS_TEYIDI:
                        v["giris"] = fiyat
                        v["giris_zamani"] = simdi
                        v["max_getiri"] = 0.0
                        v["min_getiri"] = 0.0
            k["hizli_son_fiyat"] = fiyat
            k["hizli_son_guncelleme"] = simdi

        for v in varyantlar.values():
            giris = float(v.get("giris", 0) or 0)
            if giris <= 0:
                continue
            getiri = _pct(fiyat, giris)
            v["max_getiri"] = round(max(float(v.get("max_getiri", 0) or 0), getiri), 3)
            v["min_getiri"] = round(min(float(v.get("min_getiri", 0) or 0), getiri), 3)
            v["son_getiri"] = round(getiri, 3)
        degisti = True

    if degisti:
        _top10_golge_kaydet()


def top10_hizli_teknik_kaydet(symbol, mikro=None, teknik=None, **alanlar):
    """Canlı kararı etkilemeden ilk 5 dakikanın teknik fotoğrafını saklar."""
    kayit = _top10_bugunku_kayit(symbol)
    if not kayit or not kayit.get("hizli_takip_uygun"):
        return
    if time.time() - float(kayit.get("zaman", 0) or 0) > TOP10_HIZLI_TAKIP_SURESI:
        return
    mikro = mikro or {}
    teknik = teknik or {}
    ornek = {
        "zaman": time.time(),
        "d1": round(float(mikro.get("d1", 0) or 0), 3),
        "d3": round(float(mikro.get("d3", 0) or 0), 3),
        "d5": round(float(mikro.get("d5", 0) or 0), 3),
        "d10": round(float(mikro.get("d10", 0) or 0), 3),
        "rsi": round(float(teknik.get("rsi", 0) or 0), 3),
        "adx": round(float(teknik.get("adx", 0) or 0), 3),
        "ema_yukari": bool(
            teknik.get("ema20") is not None and teknik.get("ema50") is not None
            and float(teknik.get("ema20")) > float(teknik.get("ema50"))
        ),
    }
    ornek.update({k: v for k, v in alanlar.items() if v is not None})
    kayit.setdefault("hizli_teknik_ornekler", []).append(ornek)
    kayit["hizli_teknik_ornekler"] = kayit["hizli_teknik_ornekler"][-6:]
    _top10_golge_kaydet()


def top10_golge_ticker_guncelle(ticker):
    """Mevcut ticker isteğiyle rolling ilk 10'u açar ve 3 saatlik sonucu günceller."""
    global _TOP10_AKTIF_SYMBOLLER
    simdi = time.time()
    gun = _top10_gun_anahtari(simdi)
    uygun = []
    fiyatlar = {}
    for coin in ticker:
        try:
            symbol = str(coin.get("pair", ""))
            fiyat = float(coin.get("last", 0) or 0)
            if (
                not symbol.endswith("TRY")
                or symbol == "BTCTRY"
                or stable_coin_mi(symbol)
                or fiyat <= 0
            ):
                continue
            gunluk = _ticker_gunluk_yuzde(coin)
            uygun.append((gunluk, symbol, fiyat))
            fiyatlar[symbol] = fiyat
        except Exception:
            continue

    uygun.sort(reverse=True)
    ilk10 = uygun[:10]
    _TOP10_AKTIF_SYMBOLLER = {x[1] for x in ilk10}

    degisti = False
    # Önce açık gözlemlerin fiyat sonucunu güncelle.
    for k in TOP10_GOLGE_KAYITLARI:
        if k.get("tamamlandi"):
            continue
        fiyat = fiyatlar.get(k.get("symbol"))
        giris = float(k.get("giris", 0) or 0)
        if fiyat and giris > 0:
            getiri = _pct(fiyat, giris)
            k["max_getiri"] = round(max(float(k.get("max_getiri", 0) or 0), getiri), 3)
            k["min_getiri"] = round(min(float(k.get("min_getiri", 0) or 0), getiri), 3)
            k["son_getiri"] = round(getiri, 3)
            degisti = True
        if simdi - float(k.get("zaman", simdi) or simdi) >= TOP10_GOLGE_SURESI:
            k["tamamlandi"] = True
            k["tamamlanma_zamani"] = simdi
            degisti = True

    # Coin aynı gün rolling ilk 10'a ilk kez girdiğinde tek olay aç.
    for sira, (gunluk, symbol, fiyat) in enumerate(ilk10, 1):
        mevcut = next(
            (
                k for k in reversed(TOP10_GOLGE_KAYITLARI)
                if k.get("symbol") == symbol and k.get("gun") == gun
            ),
            None,
        )
        if mevcut is None:
            hizli_uygun = gunluk >= TOP10_HIZLI_GUNLUK_MIN
            TOP10_GOLGE_KAYITLARI.append({
                "symbol": symbol,
                "gun": gun,
                "zaman": simdi,
                "giris": fiyat,
                "ilk_sira": sira,
                "son_sira": sira,
                "ilk_gunluk_degisim": round(gunluk, 3),
                "max_gunluk_degisim": round(gunluk, 3),
                "max_getiri": 0.0,
                "min_getiri": 0.0,
                "son_getiri": 0.0,
                "tamamlandi": False,
                "asama": "tam_tarama_bekliyor",
                "telegram_al": False,
                "telegram_izle": False,
                "hizli_takip_uygun": bool(hizli_uygun),
                "hizli_dip": fiyat,
                "hizli_tepe": fiyat,
                "hizli_donuslar": _top10_hizli_varyantlar_yeni() if hizli_uygun else {},
                "hizli_teknik_ornekler": [],
                "strateji_surumu": STRATEJI_SURUMU,
            })
            degisti = True
        else:
            mevcut["son_sira"] = sira
            mevcut["max_gunluk_degisim"] = round(
                max(float(mevcut.get("max_gunluk_degisim", gunluk) or gunluk), gunluk), 3
            )
            degisti = True

    if degisti:
        _top10_golge_kaydet()

    # İlk 10'a yeni giren kayıt da aynı ticker turunda hızlı ölçüme başlasın.
    top10_hizli_fiyat_guncelle(ticker)


def top10_golge_asama_guncelle(symbol, asama, **alanlar):
    """Bugünkü en yeni ilk-10 olayına tarama kapısını ve ilk teknik resmi yazar."""
    if symbol not in _TOP10_AKTIF_SYMBOLLER:
        return
    gun = _top10_gun_anahtari()
    kayit = next(
        (
            k for k in reversed(TOP10_GOLGE_KAYITLARI)
            if k.get("symbol") == symbol and k.get("gun") == gun
        ),
        None,
    )
    if not kayit:
        return
    kayit["asama"] = str(asama)
    for anahtar, deger in alanlar.items():
        if deger is not None:
            kayit[anahtar] = deger


def _top10_kapi_etiketi(kayit):
    asama = str(kayit.get("asama", ""))
    return {
        "tam_tarama_bekliyor": "tam tarama bekledi",
        "on_havuz_disinda": "Radar/ön havuza giremedi",
        "on_havuz_adayi": "ön havuza girdi",
        "mikro_teyitsiz": "mikro teyit alamadı",
        "h_bekle": "H motoru BEKLE dedi",
        "yumusa_filtre": "yumuşak filtre eledi",
        "tekrar_koruma": "tekrar koruması",
        "gec_teyit": "geç teyit",
        "telegram_izle": "Telegram İZLE",
        "telegram_al": "Telegram AL",
    }.get(asama, asama or "neden kaydedilemedi")


def top10_kacan_hareket_raporu(pencere_bas, pencere_son):
    """En yüksek 10 rolling hareketi ve tekrar eden kaçırma kapısını raporlar."""
    pencere = [
        k for k in TOP10_GOLGE_KAYITLARI
        if pencere_bas <= float(k.get("zaman", 0) or 0) < pencere_son
    ]
    tamam = [k for k in pencere if k.get("tamamlandi")]
    if not pencere:
        return (
            "🔎 İLK 10 KAÇAN HAREKET ANALİZİ\n"
            "• Bu dönem kayıt oluşmadı; yeni sürüm rolling ilk 10'u gölgede toplamaya başlayacak."
        )

    liderler = sorted(
        tamam or pencere,
        key=lambda k: (
            float(k.get("max_gunluk_degisim", 0) or 0),
            float(k.get("max_getiri", 0) or 0),
        ),
        reverse=True,
    )[:10]
    art3 = [k for k in tamam if float(k.get("max_getiri", 0) or 0) >= 3.0]
    art5 = [k for k in tamam if float(k.get("max_getiri", 0) or 0) >= 5.0]
    al_yakaladi = [k for k in art3 if k.get("telegram_al")]
    izle_yakaladi = [k for k in art3 if k.get("telegram_izle")]
    kacan = [k for k in art3 if not k.get("telegram_al") and not k.get("telegram_izle")]

    neden_say = {}
    for k in kacan:
        etiket = _top10_kapi_etiketi(k)
        neden_say[etiket] = neden_say.get(etiket, 0) + 1
    nedenler = sorted(neden_say.items(), key=lambda x: (x[1], x[0]), reverse=True)

    satirlar = [
        "🔎 İLK 10 KAÇAN HAREKET ANALİZİ — YALNIZ GÖLGE",
        f"• Rolling ilk 10 olayı={len(pencere)} | tamamlanan={len(tamam)} | bekleyen={len(pencere)-len(tamam)}",
        f"• İlk 10'a girdikten sonra +%3={len(art3)} | +%5={len(art5)} | Telegram AL yakaladı={len(al_yakaladi)} | İZLE yakaladı={len(izle_yakaladi)} | hiç görünmeyen={len(kacan)}",
        "",
        "🏁 DÖNEMİN EN YÜKSEK 10'U",
    ]
    for k in liderler:
        coin = str(k.get("symbol", "")).replace("TRY", "")
        gorunum = "AL" if k.get("telegram_al") else ("İZLE" if k.get("telegram_izle") else "KAÇTI")
        satirlar.append(
            f"• {coin}: gün içi %{float(k.get('max_gunluk_degisim',0) or 0):+.2f} | "
            f"ilk-10 sonrası tepe %{float(k.get('max_getiri',0) or 0):+.2f} | {gorunum} | {_top10_kapi_etiketi(k)}"
        )

    satirlar.extend(["", "🚧 EN SIK KAÇIRMA KAPILARI"])
    if nedenler:
        for etiket, n in nedenler[:5]:
            satirlar.append(f"• {etiket}: n={n}")
    else:
        satirlar.append("• Tamamlanmış +%3 kaçan hareket yok.")

    # Kod önerisi yalnız ilk-10'a girdikten SONRA yükselenleri kullanır. Coin
    # listeye zaten +%5 ile girmişse eşik gevşetme delili sayılmaz.
    on_havuz = sum(1 for k in kacan if k.get("asama") == "on_havuz_disinda")
    h_bekle = sum(1 for k in kacan if k.get("asama") == "h_bekle")
    gec = sum(1 for k in kacan if k.get("asama") == "gec_teyit")
    satirlar.extend(["", "🧩 KOD ÖNERİSİ"])
    if len(kacan) < TOP10_KOD_ONERI_MIN_ORNEK:
        satirlar.append(
            f"• Karar için örnek yetersiz: kaçan +%3 n={len(kacan)}, en az {TOP10_KOD_ONERI_MIN_ORNEK} tamamlanmış kaçan hareket bekleniyor."
        )
    if on_havuz:
        satirlar.append(
            f"• GÖLGE TEST ADAYI (n={on_havuz}): `ilk10 and gunluk>=1` coinlerini 5 dk teknik izleme havuzuna al; doğrudan AL verme."
        )
    if h_bekle:
        satirlar.append(
            f"• GÖLGE TEST ADAYI (n={h_bekle}): ilk10 + risk uygun + 3/5dk pozitif H-BEKLE grubunu ayrı ölç; H kapısını henüz gevşetme."
        )
    if gec:
        satirlar.append(
            f"• ZAMANLAMA ADAYI (n={gec}): geç teyidi kaldırma; coin ilk10'a girer girmez ön havuzu açarak daha erken profil üret."
        )
    if not (on_havuz or h_bekle or gec):
        satirlar.append("• Tekrarlanan ortak kaçırma kapısı henüz oluşmadı; canlı koda eşik önerilmiyor.")
    satirlar.append(
        "• Öneriler kodu otomatik değiştirmez; yalnız ilk görülme anından sonraki +%3/+%5 sonuçlarıyla doğrulanır."
    )

    hizli = [k for k in pencere if k.get("hizli_takip_uygun")]
    hizli_tamam = [k for k in hizli if k.get("tamamlandi")]
    teknikli = [k for k in hizli if k.get("hizli_teknik_ornekler")]
    satirlar.extend([
        "",
        "⚡ İLK 10 HIZLI TAKİP + DÖNÜŞ — YALNIZ GÖLGE",
        f"• Günlük ≥+%{TOP10_HIZLI_GUNLUK_MIN:.0f}: aday={len(hizli)} | "
        f"tamamlanan={len(hizli_tamam)} | teknik profil alınan={len(teknikli)}",
        f"• İlk-10 fiyatından: +%3 %{_hedef_orani(hizli_tamam, 3):.1f} | "
        f"+%5 %{_hedef_orani(hizli_tamam, 5):.1f} | yanlış %{_yanlis_orani(hizli_tamam):.1f}",
        f"• Hızlı pencere={TOP10_HIZLI_TAKIP_SURESI//60}dk | "
        f"dönüş teyidi=dipten +%{TOP10_HIZLI_DONUS_TEYIDI:.1f} | Telegram/AL yok",
    ])
    for esik in TOP10_HIZLI_CEKILISLER:
        anahtar = _top10_hizli_varyant_anahtari(esik)
        giren = []
        for k in hizli_tamam:
            v = (k.get("hizli_donuslar") or {}).get(anahtar) or {}
            if v.get("giris"):
                giren.append(v)
        p3 = (
            sum(1 for v in giren if float(v.get("max_getiri", 0) or 0) >= 3)
            / len(giren) * 100 if giren else 0.0
        )
        p5 = (
            sum(1 for v in giren if float(v.get("max_getiri", 0) or 0) >= 5)
            / len(giren) * 100 if giren else 0.0
        )
        yanlis = (
            sum(
                1 for v in giren
                if float(v.get("max_getiri", 0) or 0) < 5
                and float(v.get("min_getiri", 0) or 0) <= -2.5
            ) / len(giren) * 100 if giren else 0.0
        )
        satirlar.append(
            f"• -%{esik:.1f} + dönüş: giriş n={len(giren)} | +%3 %{p3:.1f} | "
            f"+%5 %{p5:.1f} | yanlış %{yanlis:.1f}"
        )
    dogrudan = [
        k for k in hizli_tamam
        if not ((k.get("hizli_donuslar") or {}).get(
            _top10_hizli_varyant_anahtari(1.0)
        ) or {}).get("kuruldu")
        and float(k.get("max_getiri", 0) or 0) >= 3.0
    ]
    satirlar.append(f"• -%1 çekilmeden doğrudan +%3 yapan={len(dogrudan)}")
    if len(hizli_tamam) < TOP10_HIZLI_KARAR_MIN:
        satirlar.append(
            f"• Canlı değişiklik yok: karar için en az {TOP10_HIZLI_KARAR_MIN} "
            "tamamlanmış hızlı takip bekleniyor."
        )
    else:
        satirlar.append(
            "• Yeterli örnek oluştu; başarı, yanlış ve kazanan koruma birlikte incelenmeli."
        )
    return "\n".join(satirlar)


def _giris_deneyi_yukle():
    try:
        if os.path.exists(GIRIS_DENEYI_DOSYA):
            with open(GIRIS_DENEYI_DOSYA, "r", encoding="utf-8") as f:
                veri = json.load(f)
            return veri if isinstance(veri, list) else []
    except Exception as e:
        print("AL giriş zamanı deneyi okunamadı:", e)
    return []


def _giris_deneyi_kaydet():
    try:
        klasor = os.path.dirname(os.path.abspath(GIRIS_DENEYI_DOSYA))
        if klasor:
            os.makedirs(klasor, exist_ok=True)
        gecici = GIRIS_DENEYI_DOSYA + ".tmp"
        with open(gecici, "w", encoding="utf-8") as f:
            json.dump(
                GIRIS_ZAMANI_DENEY_KAYITLARI[-GIRIS_DENEYI_MAX_KAYIT:],
                f,
                ensure_ascii=False,
            )
        os.replace(gecici, GIRIS_DENEYI_DOSYA)
    except Exception as e:
        print("AL giriş zamanı deneyi yazılamadı:", e)


def _giris_varyant_anahtari(tur, esik):
    return f"{tur}_{float(esik):.1f}"


def giris_zamani_deneyi_baslat(aday):
    """Telegram'a giden Üst/Güçlü AL ve İZLE için ayrı deney açar."""
    seviye = int(aday.get("v11_seviye", 0) or 0)
    symbol = str(aday.get("symbol", ""))
    fiyat = float(aday.get("fiyat", 0) or 0)
    if seviye not in (1, 2, 3) or not symbol or fiyat <= 0:
        return

    event_id = str(aday.get("_sinyal_event_id", "") or "")
    if event_id and any(str(k.get("event_id", "")) == event_id for k in GIRIS_ZAMANI_DENEY_KAYITLARI):
        return
    # Restart/event-id bulunamaması halinde aynı coinde yakın çift kayıt açma.
    simdi = time.time()
    if any(
        k.get("symbol") == symbol
        and not k.get("tamamlandi")
        and simdi - float(k.get("zaman", 0) or 0) < GIRIS_DENEYI_CEKILIS_PENCERESI
        for k in GIRIS_ZAMANI_DENEY_KAYITLARI[-100:]
    ):
        return

    varyantlar = {}
    for esik in GIRIS_DENEYI_CEKILISLER:
        for tur in ("limit", "donus"):
            varyantlar[_giris_varyant_anahtari(tur, esik)] = {
                "tur": tur,
                "esik": float(esik),
                "kuruldu": False,
                "giris": None,
                "giris_zamani": None,
                "dip_fiyat": None,
                "max_getiri": None,
                "min_getiri": None,
                "son_getiri": None,
            }

    GIRIS_ZAMANI_DENEY_KAYITLARI.append({
        "symbol": symbol,
        "event_id": event_id,
        "zaman": simdi,
        "sinyal_fiyati": fiyat,
        "v11_seviye": seviye,
        "sinif": (
            "Üst Düzey AL" if seviye == 1
            else ("Güçlü AL" if seviye == 2 else "İZLE")
        ),
        "ilk30_dip": fiyat,
        "ilk30_tepe": fiyat,
        "ilk30_max_cekilis": 0.0,
        "hemen_max_getiri": 0.0,
        "hemen_min_getiri": 0.0,
        "hemen_son_getiri": 0.0,
        "varyantlar": varyantlar,
        "tamamlandi": False,
        "strateji_surumu": STRATEJI_SURUMU,
    })
    _giris_deneyi_kaydet()


def giris_zamani_deneyi_aktif_mi():
    return any(not k.get("tamamlandi") for k in GIRIS_ZAMANI_DENEY_KAYITLARI)


def giris_zamani_deneyi_guncelle(ticker):
    """15 sn ticker akışında hemen/limit/dönüş girişlerini aynı üç saatte izler."""
    if not GIRIS_ZAMANI_DENEY_KAYITLARI:
        return
    fiyatlar = {}
    for coin in ticker:
        try:
            symbol = str(coin.get("pair", ""))
            fiyat = float(coin.get("last", 0) or 0)
            if symbol and fiyat > 0:
                fiyatlar[symbol] = fiyat
        except Exception:
            continue

    simdi = time.time()
    degisti = False
    for kayit in GIRIS_ZAMANI_DENEY_KAYITLARI:
        if kayit.get("tamamlandi"):
            continue
        fiyat = fiyatlar.get(kayit.get("symbol"))
        sinyal = float(kayit.get("sinyal_fiyati", 0) or 0)
        if not fiyat or sinyal <= 0:
            continue
        gecen = simdi - float(kayit.get("zaman", simdi) or simdi)

        hemen = _pct(fiyat, sinyal)
        kayit["hemen_max_getiri"] = round(max(float(kayit.get("hemen_max_getiri", 0) or 0), hemen), 3)
        kayit["hemen_min_getiri"] = round(min(float(kayit.get("hemen_min_getiri", 0) or 0), hemen), 3)
        kayit["hemen_son_getiri"] = round(hemen, 3)

        varyantlar = kayit.get("varyantlar") or {}
        if gecen <= GIRIS_DENEYI_CEKILIS_PENCERESI:
            kayit["ilk30_dip"] = min(float(kayit.get("ilk30_dip", sinyal) or sinyal), fiyat)
            kayit["ilk30_tepe"] = max(float(kayit.get("ilk30_tepe", sinyal) or sinyal), fiyat)
            kayit["ilk30_max_cekilis"] = round(
                min(float(kayit.get("ilk30_max_cekilis", 0) or 0), hemen), 3
            )

            for esik in GIRIS_DENEYI_CEKILISLER:
                limit_v = varyantlar.get(_giris_varyant_anahtari("limit", esik), {})
                donus_v = varyantlar.get(_giris_varyant_anahtari("donus", esik), {})
                esik_fiyat = sinyal * (1.0 - float(esik) / 100.0)
                if fiyat <= esik_fiyat:
                    if not limit_v.get("giris"):
                        # Sıçramalı düşüşte görülen daha düşük son fiyatı kullanmak
                        # sonucu yapay iyileştirebilir. Emrin varsayılan dolumunu
                        # konservatif biçimde önceden belirlenen limit seviyesinden yaz.
                        limit_v["giris"] = esik_fiyat
                        limit_v["giris_zamani"] = simdi
                        limit_v["max_getiri"] = 0.0
                        limit_v["min_getiri"] = 0.0
                    donus_v["kuruldu"] = True
                    eski_dip = donus_v.get("dip_fiyat")
                    donus_v["dip_fiyat"] = fiyat if not eski_dip else min(float(eski_dip), fiyat)

                if donus_v.get("kuruldu") and not donus_v.get("giris"):
                    dip = float(donus_v.get("dip_fiyat", 0) or 0)
                    if dip > 0 and _pct(fiyat, dip) >= GIRIS_DENEYI_DONUS_TEYIDI:
                        donus_v["giris"] = fiyat
                        donus_v["giris_zamani"] = simdi
                        donus_v["max_getiri"] = 0.0
                        donus_v["min_getiri"] = 0.0

        # Kurulmuş bütün gerçekçi girişlerin kalan üç saatlik sonucunu ölç.
        for v in varyantlar.values():
            giris = float(v.get("giris", 0) or 0)
            if giris <= 0:
                continue
            getiri = _pct(fiyat, giris)
            v["max_getiri"] = round(max(float(v.get("max_getiri", 0) or 0), getiri), 3)
            v["min_getiri"] = round(min(float(v.get("min_getiri", 0) or 0), getiri), 3)
            v["son_getiri"] = round(getiri, 3)

        if gecen >= GIRIS_DENEYI_SURESI:
            kayit["tamamlandi"] = True
            kayit["tamamlanma_zamani"] = simdi
        degisti = True

    if degisti:
        _giris_deneyi_kaydet()


def _giris_deneyi_oran(kayitlar, alan, hedef):
    return (
        sum(1 for k in kayitlar if float(k.get(alan, 0) or 0) >= hedef) / len(kayitlar) * 100.0
        if kayitlar else 0.0
    )


def giris_zamani_deneyi_raporu(pencere_bas, pencere_son):
    pencere = [
        k for k in GIRIS_ZAMANI_DENEY_KAYITLARI
        if pencere_bas <= float(k.get("zaman", 0) or 0) < pencere_son
    ]
    tamam_tumu = [k for k in pencere if k.get("tamamlandi")]
    tamam_al = [k for k in tamam_tumu if int(k.get("v11_seviye", 0) or 0) in (1, 2)]
    tamam_izle = [k for k in tamam_tumu if int(k.get("v11_seviye", 0) or 0) == 3]
    pencere_al = [k for k in pencere if int(k.get("v11_seviye", 0) or 0) in (1, 2)]
    pencere_izle = [k for k in pencere if int(k.get("v11_seviye", 0) or 0) == 3]
    # Aşağıdaki ayrıntılı eşik tablosu gerçek AL grubuna aittir. İZLE grubu
    # raporun sonunda ayrıca hesaplanır; iki sınıfın başarı oranı karışmaz.
    tamam = tamam_al
    if not pencere:
        return (
            "⏱️ AL/İZLE GİRİŞ ZAMANI DENEYİ — YALNIZ GÖLGE\n"
            "• Yeni sürümden sonraki Üst Düzey/Güçlü AL ve İZLE mesajlarında ölçüm başlayacak."
        )

    hemen3 = _giris_deneyi_oran(tamam, "hemen_max_getiri", 3.0)
    hemen5 = _giris_deneyi_oran(tamam, "hemen_max_getiri", 5.0)
    hemen_dip = (
        sum(float(k.get("hemen_min_getiri", 0) or 0) for k in tamam) / len(tamam)
        if tamam else 0.0
    )
    hemen_kazanan = [k for k in tamam if float(k.get("hemen_max_getiri", 0) or 0) >= 3.0]
    satirlar = [
        "⏱️ AL/İZLE GİRİŞ ZAMANI DENEYİ — YALNIZ GÖLGE",
        f"• Gerçek AL={len(pencere_al)} | İZLE={len(pencere_izle)} | toplam tamamlanan={len(tamam_tumu)} | bekleyen={len(pencere)-len(tamam_tumu)}",
        "",
        "💎 ÜST DÜZEY/GÜÇLÜ AL",
        f"• Hemen giriş: +%3 %{hemen3:.1f} | +%5 %{hemen5:.1f} | ort. dip %{hemen_dip:+.2f}",
        f"• Pencere: AL mesajından sonraki 30dk | dönüş teyidi: dipten +%{GIRIS_DENEYI_DONUS_TEYIDI:.1f}",
        "",
        "📉 ÇEKİLİŞ SEVİYELERİ",
    ]

    aday_sonuclari = []
    for esik in GIRIS_DENEYI_CEKILISLER:
        parcalar = []
        for tur, tur_ad in (("limit", "limit"), ("donus", "dönüş")):
            anahtar = _giris_varyant_anahtari(tur, esik)
            giren = []
            korunan = 0
            avantajlar = []
            for k in tamam:
                v = (k.get("varyantlar") or {}).get(anahtar) or {}
                if not v.get("giris"):
                    continue
                vv = dict(v)
                vv["_kayit"] = k
                giren.append(vv)
                sinyal = float(k.get("sinyal_fiyati", 0) or 0)
                giris = float(v.get("giris", 0) or 0)
                if sinyal > 0 and giris > 0:
                    avantajlar.append(_pct(sinyal, giris))
                if k in hemen_kazanan and float(v.get("max_getiri", 0) or 0) >= 3.0:
                    korunan += 1
            p3 = (
                sum(1 for v in giren if float(v.get("max_getiri", 0) or 0) >= 3.0) / len(giren) * 100.0
                if giren else 0.0
            )
            p5 = (
                sum(1 for v in giren if float(v.get("max_getiri", 0) or 0) >= 5.0) / len(giren) * 100.0
                if giren else 0.0
            )
            dip = (
                sum(float(v.get("min_getiri", 0) or 0) for v in giren) / len(giren)
                if giren else 0.0
            )
            avantaj = sum(avantajlar) / len(avantajlar) if avantajlar else 0.0
            kazanan_koruma = korunan / len(hemen_kazanan) * 100.0 if hemen_kazanan else 0.0
            kabul = len(giren) / len(tamam) * 100.0 if tamam else 0.0
            parcalar.append(
                f"{tur_ad} n={len(giren)} (+%3 %{p3:.1f}, +%5 %{p5:.1f}, avantaj %{avantaj:+.2f})"
            )
            if tur == "donus" and len(giren) >= 3:
                aday_sonuclari.append({
                    "esik": esik,
                    "n": len(giren),
                    "p3": p3,
                    "p5": p5,
                    "dip": dip,
                    "avantaj": avantaj,
                    "koruma": kazanan_koruma,
                    "kabul": kabul,
                })
        satirlar.append(f"• -%{esik:.1f}: " + " | ".join(parcalar))

    dogrudan_giden = 0
    for k in tamam:
        v = (k.get("varyantlar") or {}).get(_giris_varyant_anahtari("limit", 1.0)) or {}
        if not v.get("giris") and float(k.get("hemen_max_getiri", 0) or 0) >= 3.0:
            dogrudan_giden += 1
    satirlar.extend([
        "",
        f"🚀 -%1 çekilmeden doğrudan +%3 yapan: {dogrudan_giden}/{len(hemen_kazanan)}",
        "🧠 GEÇİCİ KARAR",
    ])

    if len(tamam) < GIRIS_DENEYI_KARAR_MIN:
        satirlar.append(
            f"• Canlı giriş değişmez: tamamlanan n={len(tamam)}, karar için en az {GIRIS_DENEYI_KARAR_MIN} gerçek AL bekleniyor."
        )
    elif not aday_sonuclari:
        satirlar.append("• Çekiliş-dönüş yöntemi yeterli giriş üretmedi; hemen giriş korunmalı.")
    else:
        en_iyi = max(
            aday_sonuclari,
            key=lambda x: (x["p3"] - hemen3, x["koruma"], x["n"]),
        )
        if en_iyi["p3"] >= hemen3 + 8.0 and en_iyi["koruma"] >= 75.0:
            karar = f"-%{en_iyi['esik']:.1f} çekiliş + dönüş teyidi, hemen girişten daha güçlü aday."
        elif en_iyi["p3"] > hemen3 and en_iyi["koruma"] >= 50.0:
            karar = f"Kademeli giriş adayı: küçük kısmı AL'de, kalan kısmı -%{en_iyi['esik']:.1f} dönüşte."
        else:
            karar = "Beklemek yeterli kazananı korumadı; hemen giriş şimdilik daha uygun."
        satirlar.append(
            f"• {karar} Dönüş +%3 %{en_iyi['p3']:.1f} | kazanan koruma %{en_iyi['koruma']:.1f} | n={en_iyi['n']}."
        )
    # İZLE ayrı tutulur: amaç, bu erken uyarılarda hemen giriş yerine hangi
    # çekiliş-dönüş bandının sonradan daha iyi fırsat verdiğini keşfetmektir.
    izle3 = _giris_deneyi_oran(tamam_izle, "hemen_max_getiri", 3.0)
    izle5 = _giris_deneyi_oran(tamam_izle, "hemen_max_getiri", 5.0)
    izle_dip = (
        sum(float(k.get("hemen_min_getiri", 0) or 0) for k in tamam_izle) / len(tamam_izle)
        if tamam_izle else 0.0
    )
    izle_kazanan = [k for k in tamam_izle if float(k.get("hemen_max_getiri", 0) or 0) >= 3.0]
    izle_adaylari = []
    for esik in GIRIS_DENEYI_CEKILISLER:
        anahtar = _giris_varyant_anahtari("donus", esik)
        giren = []
        avantajlar = []
        for k in tamam_izle:
            v = (k.get("varyantlar") or {}).get(anahtar) or {}
            if not v.get("giris"):
                continue
            giren.append(v)
            sinyal = float(k.get("sinyal_fiyati", 0) or 0)
            giris = float(v.get("giris", 0) or 0)
            if sinyal > 0 and giris > 0:
                avantajlar.append(_pct(sinyal, giris))
        p3 = (
            sum(1 for v in giren if float(v.get("max_getiri", 0) or 0) >= 3.0) / len(giren) * 100.0
            if giren else 0.0
        )
        p5 = (
            sum(1 for v in giren if float(v.get("max_getiri", 0) or 0) >= 5.0) / len(giren) * 100.0
            if giren else 0.0
        )
        avantaj = sum(avantajlar) / len(avantajlar) if avantajlar else 0.0
        if len(giren) >= 3:
            izle_adaylari.append({"esik": esik, "n": len(giren), "p3": p3, "p5": p5, "avantaj": avantaj})

    izle_dogrudan = 0
    for k in tamam_izle:
        v = (k.get("varyantlar") or {}).get(_giris_varyant_anahtari("limit", 1.0)) or {}
        if not v.get("giris") and float(k.get("hemen_max_getiri", 0) or 0) >= 3.0:
            izle_dogrudan += 1

    satirlar.extend([
        "",
        "🌱 İZLE — AYRI ÖLÇÜM",
        f"• Tamamlanan={len(tamam_izle)} | mesaj fiyatından +%3 %{izle3:.1f} | +%5 %{izle5:.1f} | ort. dip %{izle_dip:+.2f}",
        f"• -%1 çekilmeden doğrudan +%3 yapan: {izle_dogrudan}/{len(izle_kazanan)}",
    ])
    if izle_adaylari:
        izle_en_iyi = max(izle_adaylari, key=lambda x: (x["p3"], x["p5"], x["n"]))
        satirlar.append(
            f"• Geçici en iyi dönüş: -%{izle_en_iyi['esik']:.1f} + dipten %{GIRIS_DENEYI_DONUS_TEYIDI:.1f} | "
            f"n={izle_en_iyi['n']} | +%3 %{izle_en_iyi['p3']:.1f} | +%5 %{izle_en_iyi['p5']:.1f} | "
            f"fiyat avantajı %{izle_en_iyi['avantaj']:+.2f}"
        )
    else:
        satirlar.append("• Dönüş bandı için henüz en az 3 gerçekleşmiş İZLE girişi yok.")
    if len(tamam_izle) < GIRIS_DENEYI_KARAR_MIN:
        satirlar.append(
            f"• İZLE için karar yok: en az {GIRIS_DENEYI_KARAR_MIN} tamamlanmış kayıt bekleniyor."
        )
    satirlar.append("• AL ve İZLE sonuçları birbirine karıştırılmaz; deney mesaj veya gerçek emir üretmez.")
    return "\n".join(satirlar)

def _planli_3gun_rapor_zamani(simdi, meta):
    """İlk raporu 06.10.2026 08:00 TR'de, sonra her 72 saatte bir gönderir."""
    if simdi < ILK_3GUN_RAPOR_TS:
        return False, ILK_3GUN_RAPOR_TS
    idx = int((simdi - ILK_3GUN_RAPOR_TS) // YUZDE5_RAPOR_ARALIGI)
    planli = ILK_3GUN_RAPOR_TS + idx * YUZDE5_RAPOR_ARALIGI
    son_planli = float(meta.get("son_planli_rapor_ts", 0) or 0)
    return son_planli < planli, planli

YUZDE5_RAPOR_ETIKETI = "V11 Erken+Devam"
_YUZDE5_META_DOSYA = os.path.join(_AL_DEFAULT_DIR, "yuzde5_basariraporu_v11.json")

def _yuzde5_meta_yukle():
    try:
        if os.path.exists(_YUZDE5_META_DOSYA):
            with open(_YUZDE5_META_DOSYA, "r", encoding="utf-8") as f:
                d = json.load(f)
                return d if isinstance(d, dict) else {}
    except Exception as e:
        print("+%5 rapor meta okunamadı:", e)
    return {}

def _yuzde5_meta_kaydet(meta):
    try:
        os.makedirs(os.path.dirname(_YUZDE5_META_DOSYA), exist_ok=True)
        with open(_YUZDE5_META_DOSYA, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False)
    except Exception as e:
        print("+%5 rapor meta yazılamadı:", e)

_YUZDE5_META = _yuzde5_meta_yukle()
if not _YUZDE5_META.get("baslangic"):
    _YUZDE5_META["baslangic"] = time.time()
    _YUZDE5_META["son_rapor"] = _YUZDE5_META["baslangic"]
    _yuzde5_meta_kaydet(_YUZDE5_META)

def yuzde5_basariraporu_gerekirse_gonder():
    """Her 3 günde bir saat 08:00 TR'de V11 performansını ortak cetvelle raporlar."""
    global _YUZDE5_META

    simdi = time.time()
    gonder, planli_ts = _planli_3gun_rapor_zamani(simdi, _YUZDE5_META)
    if not gonder:
        return

    pencere_bas = planli_ts - YUZDE5_RAPOR_ARALIGI
    pencere_son = planli_ts

    tum = [
        x for x in AL_OGRENME_KAYITLARI
        if x.get("strateji_surumu") == STRATEJI_SURUMU
        and pencere_bas <= float(x.get("zaman", 0) or 0) < pencere_son
    ]

    # Ana V11 başlığı yalnız gerçekten Telegram'a gönderilen sinyalleri ölçer.
    # Canlı süzgecin elediği gölge kayıtlar bu başarıya karıştırılmaz.
    canli_tum = [
        x for x in tum
        if str(x.get("kayit_tipi", "telegram")) == "telegram"
    ]
    tamam = [x for x in canli_tum if x.get("tamamlandi")]
    acik = [x for x in canli_tum if not x.get("tamamlandi")]
    basarili = [x for x in tamam if float(x.get("max_getiri", 0) or 0) >= 5.0]
    yanlis = [
        x for x in tamam
        if float(x.get("max_getiri", 0) or 0) < 5.0
        and float(x.get("min_getiri", 0) or 0) <= -2.5
    ]
    notr = [x for x in tamam if x not in basarili and x not in yanlis]

    ham_oran = (len(basarili) / len(tamam) * 100.0) if tamam else 0.0
    yanlis_oran = (len(yanlis) / len(tamam) * 100.0) if tamam else 0.0
    net_taban = len(basarili) + len(yanlis)
    net_kalite = (len(basarili) / net_taban * 100.0) if net_taban else 0.0
    ort_tepe = (
        sum(float(x.get("max_getiri", 0) or 0) for x in tamam) / len(tamam)
        if tamam else 0.0
    )
    ort_dip = (
        sum(float(x.get("min_getiri", 0) or 0) for x in tamam) / len(tamam)
        if tamam else 0.0
    )

    def _hedef_orani(grup, hedef):
        return (
            sum(1 for x in grup if float(x.get("max_getiri", 0) or 0) >= hedef)
            / len(grup) * 100.0
        ) if grup else 0.0

    def _yanlis_orani(grup):
        return (
            sum(
                1 for x in grup
                if float(x.get("max_getiri", 0) or 0) < 5.0
                and float(x.get("min_getiri", 0) or 0) <= -2.5
            ) / len(grup) * 100.0
        ) if grup else 0.0

    # Yeni canlı süzgecin gönderdiği ve elediği bütün V11 AL adayları aynı
    # giriş fiyatından üç saat izlenir. Böylece +%2/+%3 hareketler kaybolmaz.
    filtre_tamam = [
        x for x in tum
        if x.get("tamamlandi") and bool(x.get("v11_filtre_adayi"))
    ]
    gec_teyit_tamam = [
        x for x in filtre_tamam
        if str(x.get("kayit_tipi", "")) == "v11_gec_teyit"
        or bool(x.get("v11_gec_teyit"))
    ]
    erken_izle_tamam = [
        x for x in filtre_tamam
        if str(x.get("kayit_tipi", "")) == "v11_erken_izle"
        or int(x.get("v11_seviye", 0) or 0) == 3
    ]
    kontrollu_ust_tamam = [
        x for x in filtre_tamam if bool(x.get("v11_kontrollu_ust_duzey"))
    ]
    seviye1_tamam = [
        x for x in filtre_tamam
        if int(x.get("v11_seviye", 0) or 0) == 1
        and not bool(x.get("v11_kontrollu_ust_duzey"))
    ]
    seviye2_tamam = [
        x for x in filtre_tamam if int(x.get("v11_seviye", 0) or 0) == 2
    ]
    kalite_kabul = [
        x for x in filtre_tamam if bool(x.get("v11_filtre_kabul"))
    ]
    canli_al_tamam = [
        x for x in filtre_tamam
        if bool(x.get("v11_filtre_kabul"))
        and x not in gec_teyit_tamam
        and x not in erken_izle_tamam
    ]
    filtre_veto = [x for x in filtre_tamam if not bool(x.get("v11_filtre_kabul"))]
    filtre_acik = [
        x for x in tum
        if not x.get("tamamlandi") and bool(x.get("v11_filtre_adayi"))
    ]
    asiri_rel_yolu = [
        x for x in filtre_tamam if bool(x.get("v11_yol_asiri_rel"))
    ]
    temiz_mom_yolu = [
        x for x in filtre_tamam if bool(x.get("v11_yol_temiz_momentum"))
    ]
    eleme_orani = (
        len(filtre_veto) / len(filtre_tamam) * 100.0
        if filtre_tamam else 0.0
    )
    toplam_iki = sum(
        1 for x in filtre_tamam if float(x.get("max_getiri", 0) or 0) >= 2.0
    )
    korunan_iki = sum(
        1 for x in kalite_kabul if float(x.get("max_getiri", 0) or 0) >= 2.0
    )
    iki_koruma = (korunan_iki / toplam_iki * 100.0) if toplam_iki else 0.0
    veto_yanlis = sum(
        1 for x in filtre_veto
        if float(x.get("max_getiri", 0) or 0) < 2.0
        and float(x.get("min_getiri", 0) or 0) <= V11_FILTRE_YANLIS_TEPKI
    )
    veto_yanlis_oran = (
        veto_yanlis / len(filtre_veto) * 100.0 if filtre_veto else 0.0
    )

    # Telegram'daki üç sade sınıfın özellikle kısa +%3 hareket başarısını
    # karşılaştır. Küçük örneklemde yalnız geçici lider gösterilir; canlı
    # eşikler veya mesaj kapıları otomatik değiştirilmez.
    seviye_gruplari = [
        ("🛡️ Kontrollü Üst Düzey AL", kontrollu_ust_tamam),
        ("🏆 Üst Düzey AL", seviye1_tamam),
        ("💎 Güçlü AL", seviye2_tamam),
        ("🌱 İzle", erken_izle_tamam),
    ]
    dolu_seviyeler = [(ad, grup) for ad, grup in seviye_gruplari if grup]
    if dolu_seviyeler:
        uc_lider_ad, uc_lider_grup = max(
            dolu_seviyeler,
            key=lambda item: (_hedef_orani(item[1], 3), len(item[1])),
        )
        uc_lider_metni = (
            f"• Geçici +%3 lideri: {uc_lider_ad} | "
            f"+%3 %{_hedef_orani(uc_lider_grup, 3):.1f} | "
            f"n={len(uc_lider_grup)}\n"
        )
    else:
        uc_lider_metni = "• Geçici +%3 lideri: henüz tamamlanan ölçüm yok.\n"

    filtre_metni = (
        "\n\n🧹 V11 CANLI YUMUŞAK SÜZGEÇ\n"
        f"• Tamamlanan aday={len(filtre_tamam)} | kalite kabul={len(kalite_kabul)} | "
        f"kalite veto={len(filtre_veto)} | veto %{eleme_orani:.1f} | bekleyen={len(filtre_acik)}\n"
        f"• Kalite kabul: +%2 %{_hedef_orani(kalite_kabul, 2):.1f} | "
        f"+%3 %{_hedef_orani(kalite_kabul, 3):.1f} | +%5 %{_hedef_orani(kalite_kabul, 5):.1f}\n"
        f"• Kalite veto: +%2 %{_hedef_orani(filtre_veto, 2):.1f} | "
        f"+%3 %{_hedef_orani(filtre_veto, 3):.1f} | +%5 %{_hedef_orani(filtre_veto, 5):.1f}\n"
        f"• Kabul dağılımı: canlı AL={len(canli_al_tamam)} | "
        f"İZLE={len(erken_izle_tamam)} | geç teyit={len(gec_teyit_tamam)}\n"
        "\n⏱️ V11 GİRİŞ ZAMANI KORUMASI\n"
        f"• Geç teyit: n={len(gec_teyit_tamam)} | "
        f"+%2 %{_hedef_orani(gec_teyit_tamam, 2):.1f} | "
        f"+%3 %{_hedef_orani(gec_teyit_tamam, 3):.1f} | "
        f"+%5 %{_hedef_orani(gec_teyit_tamam, 5):.1f} | "
        f"yanlış %{_yanlis_orani(gec_teyit_tamam):.1f}\n"
        f"• Koruma: 5dk >%{V11_GEC_D5_MAX:.1f} veya "
        f"10dk >%{V11_GEC_D10_MAX:.1f} veya RSI >{V11_GEC_RSI_MAX:.0f}; "
        "Telegram'a gönderilmez; gölgede ölçülür.\n"
        "\n🧭 V11 MESAJ SINIFLARI — +%3 KARŞILAŞTIRMASI\n"
        f"• 🛡️ Kontrollü Üst Düzey AL: n={len(kontrollu_ust_tamam)} | "
        f"+%2 %{_hedef_orani(kontrollu_ust_tamam, 2):.1f} | "
        f"+%3 %{_hedef_orani(kontrollu_ust_tamam, 3):.1f} | "
        f"+%5 %{_hedef_orani(kontrollu_ust_tamam, 5):.1f} | "
        f"yanlış %{_yanlis_orani(kontrollu_ust_tamam):.1f}\n"
        f"• 🏆 Üst Düzey AL: n={len(seviye1_tamam)} | "
        f"+%2 %{_hedef_orani(seviye1_tamam, 2):.1f} | "
        f"+%3 %{_hedef_orani(seviye1_tamam, 3):.1f} | "
        f"+%5 %{_hedef_orani(seviye1_tamam, 5):.1f} | "
        f"yanlış %{_yanlis_orani(seviye1_tamam):.1f}\n"
        f"• 💎 Güçlü AL: n={len(seviye2_tamam)} | "
        f"+%2 %{_hedef_orani(seviye2_tamam, 2):.1f} | "
        f"+%3 %{_hedef_orani(seviye2_tamam, 3):.1f} | "
        f"+%5 %{_hedef_orani(seviye2_tamam, 5):.1f} | "
        f"yanlış %{_yanlis_orani(seviye2_tamam):.1f}\n"
        f"• 🌱 İzle: n={len(erken_izle_tamam)} | "
        f"+%2 %{_hedef_orani(erken_izle_tamam, 2):.1f} | "
        f"+%3 %{_hedef_orani(erken_izle_tamam, 3):.1f} | "
        f"+%5 %{_hedef_orani(erken_izle_tamam, 5):.1f} | "
        f"yanlış %{_yanlis_orani(erken_izle_tamam):.1f}\n"
        f"{uc_lider_metni}"
        "• Kalıcı +%3 lideri için dört grupta da en az 8 tamamlanmış sinyal beklenir; "
        "ölçüm canlı kararı otomatik değiştirmez.\n"
        "• Erken Yakalama puanı tek başına geç kalma vetosu değildir; "
        "zamanlama gerçek 5/10dk hareketi ve RSI ile, kalite ayrı puanlarla ölçülür.\n"
        f"• BEAM yolu (60dk iki fark ≥+{V11_ASIRI_REL_ESIK:.0f}): n={len(asiri_rel_yolu)} | "
        f"+%2 %{_hedef_orani(asiri_rel_yolu, 2):.1f} | "
        f"+%3 %{_hedef_orani(asiri_rel_yolu, 3):.1f} | "
        f"+%5 %{_hedef_orani(asiri_rel_yolu, 5):.1f}\n"
        f"• HOT yolu (3/5dk pozitif, 4 vadenin ≥{V11_TEMIZ_MOM_MIN_POZITIF}'ü pozitif): "
        f"n={len(temiz_mom_yolu)} | +%2 %{_hedef_orani(temiz_mom_yolu, 2):.1f} | "
        f"+%3 %{_hedef_orani(temiz_mom_yolu, 3):.1f} | "
        f"+%5 %{_hedef_orani(temiz_mom_yolu, 5):.1f}\n"
        f"• Kalite süzgeci +%2 hareket koruma %{iki_koruma:.1f} | "
        f"elenenlerde yanlış tepki %{veto_yanlis_oran:.1f}\n"
        "• BEAM/HOT yolu kalite süzgecinde korunur; fakat giriş zamanı korumasını "
        "geçmek zorundadır. Parçalı/sönen momentum ve birleşik zayıflık ayrıca ayıklanır."
    )

    mesaj = (
        f"📊 3 GÜNLÜK +%5 / YANLIŞ SİNYAL RAPORU — {YUZDE5_RAPOR_ETIKETI}\n\n"
        f"Tamamlanan sinyal: {len(tamam)}\n"
        f"✅ +%5 yapan: {len(basarili)}\n"
        f"❌ Yanlış sinyal (-%2.5): {len(yanlis)}\n"
        f"➖ Nötr/yetersiz: {len(notr)}\n"
        f"🎯 Ham +%5 başarı: %{ham_oran:.1f}\n"
        f"⚠️ Yanlış sinyal oranı: %{yanlis_oran:.1f}\n"
        f"🧠 Net sinyal kalitesi: %{net_kalite:.1f}\n"
        f"📈 Ortalama tepe getiri: %{ort_tepe:+.2f}\n"
        f"📉 Ortalama dip getiri: %{ort_dip:+.2f}\n"
        f"⏳ Henüz tamamlanmayan: {len(acik)}"
        f"{filtre_metni}\n\n"
        f"Not: Başarı = AL sonrası 3 saat içinde en az +%5 tepe. "
        f"Yanlış = +%5 görmeden en az -%2.5 ters hareket."
    )
    print(mesaj)
    telegram_gonder(mesaj)

    # Telegram'ın tek mesaj sınırını zorlamamak için aynı raporun Top10 keşif
    # bölümü hemen arkasından ayrı mesaj olarak gider.
    top10_raporu = top10_kacan_hareket_raporu(pencere_bas, pencere_son)
    print(top10_raporu)
    telegram_gonder(top10_raporu)

    giris_raporu = giris_zamani_deneyi_raporu(pencere_bas, pencere_son)
    print(giris_raporu)
    telegram_gonder(giris_raporu)

    _YUZDE5_META["son_rapor"] = planli_ts
    _YUZDE5_META["son_planli_rapor_ts"] = planli_ts
    _yuzde5_meta_kaydet(_YUZDE5_META)


_PIYASA_DEVAM_HAFIZA = []
PIYASA_DEVAM_HAFIZA_SN = 180

_GELISTIRME_META_DOSYA = os.path.join(_AL_DEFAULT_DIR, "assistant_gelistirme_meta.json")

# 48 saatlik aynı-coin sinyal sırası.
# İlk AL = 1️⃣, aynı coin 48 saat içinde tekrar AL verirse 2️⃣/3️⃣...
# 48 saatten eski sinyaller yeni döngüye taşınmaz. Önceki sinyal +%5 gördüyse başlıkta belirtilir.
SINYAL_SIRA_PENCERE = 48 * 60 * 60
SINYAL_SIRA_DOSYA = os.path.join(_AL_DEFAULT_DIR, "assistant_sinyal_sira_48s.json")

def _sinyal_sira_yukle():
    try:
        if os.path.exists(SINYAL_SIRA_DOSYA):
            with open(SINYAL_SIRA_DOSYA, "r", encoding="utf-8") as f:
                veri = json.load(f)
                return veri if isinstance(veri, dict) else {}
    except Exception as e:
        print("Sinyal sıra dosyası okunamadı:", e)
    return {}

def _sinyal_sira_kaydet():
    try:
        os.makedirs(os.path.dirname(os.path.abspath(SINYAL_SIRA_DOSYA)), exist_ok=True)
        with open(SINYAL_SIRA_DOSYA, "w", encoding="utf-8") as f:
            json.dump(SINYAL_SIRA_GECMISI, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Sinyal sıra dosyası yazılamadı:", e)

def _sinyal_sira_hazirla(symbol):
    now = time.time()
    gecmis = SINYAL_SIRA_GECMISI.get(symbol, [])
    aktif = [x for x in gecmis if now - float(x.get("ts", 0) or 0) <= SINYAL_SIRA_PENCERE]
    SINYAL_SIRA_GECMISI[symbol] = aktif
    sira = len(aktif) + 1
    onceki_5 = any(bool(x.get("hit5")) for x in aktif)
    return sira, onceki_5

def _sinyal_sira_ekle(symbol, fiyat):
    now = time.time()
    aktif = [x for x in SINYAL_SIRA_GECMISI.get(symbol, []) if now - float(x.get("ts", 0) or 0) <= SINYAL_SIRA_PENCERE]
    event_id = f"{symbol}-{int(now*1000)}"
    aktif.append({"id": event_id, "ts": now, "fiyat": float(fiyat or 0), "hit5": False})
    SINYAL_SIRA_GECMISI[symbol] = aktif
    _sinyal_sira_kaydet()
    return event_id

def _sinyal_sira_hit5_isaretle(symbol, event_id=None):
    degisti = False
    for x in reversed(SINYAL_SIRA_GECMISI.get(symbol, [])):
        if event_id is None or x.get("id") == event_id:
            if not x.get("hit5"):
                x["hit5"] = True
                degisti = True
            break
    if degisti:
        _sinyal_sira_kaydet()

def _sira_etiketi(n):
    return f"{int(n)}️⃣"

SINYAL_SIRA_GECMISI = _sinyal_sira_yukle()

def _gelistirme_son_zaman_yukle():
    try:
        if os.path.exists(_GELISTIRME_META_DOSYA):
            with open(_GELISTIRME_META_DOSYA, "r", encoding="utf-8") as f:
                return float((json.load(f) or {}).get("son_rapor", 0) or 0)
    except Exception:
        pass
    return 0.0

def _gelistirme_son_zaman_kaydet(ts):
    try:
        klasor = os.path.dirname(os.path.abspath(_GELISTIRME_META_DOSYA))
        if klasor:
            os.makedirs(klasor, exist_ok=True)
        with open(_GELISTIRME_META_DOSYA, "w", encoding="utf-8") as f:
            json.dump({"son_rapor": float(ts)}, f)
    except Exception as e:
        print("Geliştirme rapor zamanı kaydedilemedi:", e)

SON_GELISTIRME_RAPOR_ZAMANI = _gelistirme_son_zaman_yukle()

# Haftalık rapor başlangıcı:
# Meta dosyası ilk kez yoksa deploy anını başlangıç kabul eder.
# Böylece yeterli kayıt olsa bile ilk açılışta hemen rapor göndermez;
# ilk rapor 7 gün sonra gelir. /data volume varsa tarih deploylarda korunur.
if not SON_GELISTIRME_RAPOR_ZAMANI:
    SON_GELISTIRME_RAPOR_ZAMANI = time.time()
    _gelistirme_son_zaman_kaydet(SON_GELISTIRME_RAPOR_ZAMANI)





def _pct(yeni, eski):
    try:
        yeni = float(yeni)
        eski = float(eski)
        return ((yeni / eski) - 1.0) * 100 if eski else 0.0
    except Exception:
        return 0.0


def dakika_veri_getir(symbol, dakika=20):
    simdi = int(time.time())
    url = (
        f"https://graph-api.btcturk.com/v1/klines/history?"
        f"symbol={symbol}&resolution=1&from={simdi - (dakika * 60)}&to={simdi}"
    )
    r = requests.get(url, timeout=8)
    r.raise_for_status()
    return r.json()


def _pct_son(c, n):
    if len(c) <= n or not c[-1-n]:
        return 0.0
    return ((c[-1] - c[-1-n]) / c[-1-n]) * 100


def mikro_ivme_hesapla(symbol):
    """1-3-5-10 dk fiyat/hacim ivmesi. Ana motoru bozmaz, erken adayı destekler."""
    try:
        d = dakika_veri_getir(symbol, 20)
        c = d.get("c", [])
        l = d.get("l", [])
        v = d.get("v", [])
        if len(c) < 12 or len(v) < 12:
            return {}

        d1 = _pct_son(c, 1)
        d3 = _pct_son(c, 3)
        d5 = _pct_son(c, 5)
        d10 = _pct_son(c, 10)

        prev5 = sum(v[-6:-1]) / 5 if sum(v[-6:-1]) > 0 else 0
        hacim1x = (v[-1] / prev5) if prev5 > 0 else 0
        son3 = sum(v[-3:]) / 3
        once3 = sum(v[-6:-3]) / 3
        hacim_ivme = (son3 / once3) if once3 > 0 else 0

        # Öğrenme botuyla aynı mantıkta 3dk hacim / 10dk ortalama oranı.
        son10_ort = (sum(v[-10:]) / 10) if len(v) >= 10 and sum(v[-10:]) > 0 else 0
        vr310 = (son3 / son10_ort) if son10_ort > 0 else 0

        # Son 5 kapanıştaki yükselen adım yüzdesi (0/25/50/75/100).
        stair5 = None
        if len(c) >= 5:
            ks5 = c[-5:]
            stair5 = sum(1 for i in range(1, 5) if ks5[i] >= ks5[i-1]) / 4 * 100

        basamak = False
        if len(c) >= 6:
            ks = c[-5:]
            ds = l[-5:] if len(l) >= 5 else ks
            yukselen_k = sum(1 for i in range(1, 5) if ks[i] >= ks[i-1]) >= 3
            yukselen_d = sum(1 for i in range(1, 5) if ds[i] >= ds[i-1]) >= 3
            basamak = yukselen_k and yukselen_d

        fiyat_ivme = d1 > 0 and d3 > 0 and (
            d1 >= (d3 / 3.0) * 1.15 or (d3 / 3.0) >= (d5 / 5.0) * 1.10
        )
        hacim_ivmeleniyor = hacim1x >= 1.35 or hacim_ivme >= 1.25
        sisti = d10 >= 6.5 or d5 >= 5.0 or d3 >= 4.0

        skor = 0
        if d1 >= 0.15: skor += 10
        if d1 >= 0.30: skor += 8
        if d3 >= 0.45: skor += 12
        if d3 >= 0.80: skor += 8
        if d5 >= 0.70: skor += 10
        if 0.8 <= d10 <= 5.5: skor += 8
        if hacim1x >= 1.35: skor += 12
        if hacim1x >= 1.80: skor += 8
        if hacim_ivme >= 1.25: skor += 10
        if fiyat_ivme: skor += 7
        if hacim_ivmeleniyor: skor += 7
        if basamak: skor += 10
        if sisti: skor -= 30

        return {
            "d1": round(d1, 3), "d3": round(d3, 3),
            "d5": round(d5, 3), "d10": round(d10, 3),
            "hacim1x": round(hacim1x, 2),
            "hacim_ivme": round(hacim_ivme, 2),
            "vr310": round(vr310, 2),
            "stair5": round(stair5, 1) if stair5 is not None else None,
            "fiyat_ivme": fiyat_ivme,
            "hacim_ivmeleniyor": hacim_ivmeleniyor,
            "basamak": basamak,
            "sisti": sisti,
            "skor": max(0, min(100, skor)),
        }
    except Exception as e:
        print(f"[MIKRO] {symbol}: {e}")
        return {}


def destek_skorlari(aday):
    """Giriş/Devam puanları bilgi amaçlıdır; tek başına AL'ı engellemez."""
    t = aday.get("teknik") or {}
    m = aday.get("mikro") or {}
    rsi = t.get("rsi")
    adx = t.get("adx")
    macd = t.get("macd_hist")
    ema20, ema50 = t.get("ema20"), t.get("ema50")
    fiyat = float(aday.get("fiyat", 0) or 0)

    ema_ok = ema20 is not None and ema50 is not None and ema20 > ema50 and fiyat > ema20
    macd_ok = macd is not None and macd > 0

    giris = 40
    if ema_ok: giris += 15
    if macd_ok: giris += 12
    if rsi is not None and 50 <= rsi <= 68: giris += 12
    elif rsi is not None and 68 < rsi <= 75: giris += 5
    elif rsi is not None and rsi > 78: giris -= 12
    if adx is not None and adx >= 30: giris += 10
    elif adx is not None and adx >= 25: giris += 6
    if m.get("basamak"): giris += 6
    if float(m.get("hacim_ivme", 0) or 0) >= 1.25: giris += 5

    devam = 35
    devam += min(20, max(0, float(aday.get("ai_skoru", 0) or 0) - 70) * 0.5)
    devam += min(15, max(0, float(aday.get("radar_skoru", 0) or 0) - 55) * 0.35)
    if adx is not None and adx >= 30: devam += 10
    if macd_ok: devam += 8
    if aday.get("btcden_guclu"): devam += 6
    if aday.get("momentum_hizlaniyor"): devam += 4
    if aday.get("hacim_hizlaniyor"): devam += 4

    return round(max(0, min(100, giris)), 1), round(max(0, min(100, devam)), 1)



def bes_plus_benzerlik_skoru(aday):
    """
    +%5 ve üstü giden örneklerde tekrar eden yapıya benzerliği yalnızca ETİKETLEMEK için hesaplar.
    KRİTİK: Bu skor AL/BEKLE/SAT kararını, aday havuzunu, sıralamayı veya Telegram gönderim filtresini DEĞİŞTİRMEZ.
    """
    m = aday.get("mikro") or {}
    devam = float(aday.get("devam_gucu", 0) or 0)
    kal = float(aday.get("kalicilik_skoru", 0) or 0)
    rel = int(aday.get("goreceli_guc_bonus", 0) or 0)
    hacim = float(aday.get("hacim", 0) or 0)
    radar = float(aday.get("radar_skoru", 0) or 0)
    d1 = float(m.get("d1", 0) or 0)
    d3 = float(m.get("d3", 0) or 0)
    d5 = float(m.get("d5", 0) or 0)
    d10 = float(m.get("d10", 0) or 0)

    skor = 0.0
    nedenler = []

    # En belirgin ortaklıklar: Devam + Kalıcılık + 60dk göreceli güç.
    if devam >= 80:
        skor += 22; nedenler.append("Devam 80+")
    elif devam >= 70:
        skor += 18; nedenler.append("Devam 70+")
    elif devam >= 65:
        skor += 14; nedenler.append("Devam 65+")
    elif devam >= 60:
        skor += 7

    # Kalıcılıkta "daha yüksek = daha iyi" varsayımını kaldır.
    # 95+ bölgesi doygun/geç kalmış hareket ihtimali taşıdığı için ek ödül almaz.
    if kal >= 95:
        skor += 8; nedenler.append("Kalıcılık 95+ (doygunluk izle)")
    elif kal >= 90:
        skor += 16; nedenler.append("Kalıcılık 90-94")
    elif kal >= 88:
        skor += 13; nedenler.append("Kalıcılık 88-89")

    if rel >= 2:
        skor += 18; nedenler.append("60dk göreceli güç +2")
    elif rel == 1:
        skor += 7

    # Çoklu momentum: tek pencere yerine birkaç pencerenin aynı yönü desteklemesi.
    poz = sum(x > 0 for x in (d1, d3, d5, d10))
    if poz == 4:
        skor += 14; nedenler.append("1/3/5/10dk birlikte pozitif")
    elif poz >= 3:
        skor += 10; nedenler.append("çoklu momentum pozitif")
    elif d3 > 0 and d5 > 0:
        skor += 6

    # Basamaklı trend artık tek başına pozitif bonus değildir.
    # Son öğrenme sonuçlarında ayırıcı olmadığı / ters çalışabildiği görüldüğü için
    # yalnız gözlem bilgisi olarak tutulur.
    if aday.get("basamakli_trend"):
        nedenler.append("basamaklı trend")
    if aday.get("momentum_hizlaniyor"):
        skor += 6; nedenler.append("momentum hızlanıyor")
    if aday.get("btc_farki_aciliyor"):
        skor += 5; nedenler.append("BTC farkı açılıyor")
    if aday.get("hacim_hizlaniyor"):
        skor += 4; nedenler.append("hacim hızlanıyor")
    if aday.get("lider_gucleniyor"):
        skor += 3

    # Radar/hacim destekleyici; sert şart değil. ZK/ALLO/ARX gibi örnekleri kaybetmemek için düşük ağırlık.
    if hacim >= 8:
        skor += 8; nedenler.append("hacim 8x+")
    elif hacim >= 4:
        skor += 6
    elif hacim >= 1.8:
        skor += 3

    if radar >= 85:
        skor += 6
    elif radar >= 65:
        skor += 4
    elif radar >= 50:
        skor += 2

    return round(max(0, min(100, skor)), 1), nedenler

def kalicilik_skoru_hesapla(aday):
    """Kalıcılık skoru yalnızca bilgi üretir; karar ve filtreleri değiştirmez."""
    symbol = aday.get("symbol", "")
    t = aday.get("teknik") or {}
    m = aday.get("mikro") or {}

    fiyat = float(aday.get("fiyat", 0) or 0)
    hacim = float(aday.get("hacim", 0) or 0)
    d1 = float(m.get("d1", 0) or 0)
    d3m = float(m.get("d3", 0) or 0)
    d5m = float(m.get("d5", 0) or 0)
    d10m = float(m.get("d10", 0) or 0)
    degisim3 = float(aday.get("degisim3", 0) or 0)
    btc_fark3 = float(aday.get("btc_fark3", 0) or 0)
    adx = t.get("adx")
    rsi = t.get("rsi")
    macd = t.get("macd_hist")
    ema20, ema50 = t.get("ema20"), t.get("ema50")

    ema_ok = ema20 is not None and ema50 is not None and fiyat > 0 and ema20 > ema50 and fiyat > ema20
    macd_ok = macd is not None and macd > 0

    skor = 35.0
    nedenler = []

    if ema_ok:
        skor += 8; nedenler.append("EMA trendi korunuyor")
    if macd_ok:
        skor += 7; nedenler.append("MACD pozitif")
    if adx is not None:
        if adx >= 40:
            skor += 14; nedenler.append("ADX çok güçlü")
        elif adx >= 30:
            skor += 10; nedenler.append("ADX güçlü")
        elif adx >= 25:
            skor += 5
        elif adx < 20:
            skor -= 8

    if hacim >= 8:
        skor += 10; nedenler.append("hacim çok güçlü")
    elif hacim >= 5:
        skor += 8; nedenler.append("hacim güçlü")
    elif hacim >= 2:
        skor += 4
    elif hacim < 0.8:
        skor -= 6

    if aday.get("hacim_hizlaniyor"):
        skor += 5; nedenler.append("hacim hızlanıyor")
    if aday.get("momentum_hizlaniyor"):
        skor += 4; nedenler.append("momentum hızlanıyor")
    if aday.get("btc_farki_aciliyor"):
        skor += 4; nedenler.append("BTC farkı açılıyor")
    if aday.get("lider_gucleniyor"):
        skor += 4; nedenler.append("liderlik güçleniyor")
    if aday.get("basamakli_trend"):
        nedenler.append("basamaklı yapı")

    if btc_fark3 >= 2:
        skor += 7; nedenler.append("BTC'den belirgin güçlü")
    elif btc_fark3 >= 0.5:
        skor += 4
    elif btc_fark3 < -1:
        skor -= 7

    if d3m > 0 and d5m > 0 and d10m > 0:
        skor += 5
    if 0.5 <= d10m <= 5.5:
        skor += 4
    # Mikro basamak da artık tek başına puan artırmaz.
    if m.get("basamak"):
        pass
    if m.get("sisti") or d10m >= 7 or d5m >= 5:
        skor -= 12; nedenler.append("kısa vadede şişme riski")
    if d1 < -0.8 and d3m < 0:
        skor -= 5

    if rsi is not None:
        if 52 <= rsi <= 70:
            skor += 5
        elif 70 < rsi <= 77:
            skor += 1
        elif rsi > 82:
            skor -= 10; nedenler.append("RSI aşırı sıcak")
        elif rsi < 45:
            skor -= 6

    hist = kalicilik_gecmisi.setdefault(symbol, [])
    if hist:
        sonlar = hist[-3:]
        hacim_koruma = sum(1 for x in sonlar if hacim >= x.get("hacim", hacim) * 0.80)
        trend_koruma = sum(1 for x in sonlar if degisim3 >= x.get("degisim3", degisim3) - 0.50)
        btc_koruma = sum(1 for x in sonlar if btc_fark3 >= x.get("btc_fark3", btc_fark3) - 0.40)
        n = len(sonlar)
        if n >= 2 and hacim_koruma >= n - 1:
            skor += 6; nedenler.append("hacim birkaç taramadır korunuyor")
        if n >= 2 and trend_koruma >= n - 1:
            skor += 7; nedenler.append("3s güç birkaç taramadır korunuyor")
        if n >= 2 and btc_koruma >= n - 1:
            skor += 4
        if n >= 2 and hacim_koruma == 0 and trend_koruma == 0:
            skor -= 8; nedenler.append("güç hızlı sönüyor")

    hist.append({"zaman": time.time(), "hacim": hacim, "degisim3": degisim3, "btc_fark3": btc_fark3, "d1": d1, "d3m": d3m})
    if len(hist) > KALICILIK_GECMIS_UZUNLUK:
        del hist[:-KALICILIK_GECMIS_UZUNLUK]

    skor = round(max(0, min(100, skor)), 1)

    # Aşırı yüksek Kalıcılık geçmişte her zaman daha iyi devam anlamına gelmedi.
    # 95+ olduğunda doygunluk/geç kalma riski için yumuşak ceza uygula.
    # Bu sert veto değildir; yalnız bilgi skorunu yeniden kalibre eder.
    if skor >= 95:
        skor = round(max(0, skor - 8), 1)
        nedenler.append("kalıcılık doygunluk cezası")

    if skor >= 80:
        etiket = "Uzun devam adayı"
    elif skor >= 68:
        etiket = "Devam güçlü"
    elif skor >= 55:
        etiket = "Orta / izle"
    else:
        etiket = "Hızlı hareket / dönüş riski"
    return skor, etiket, nedenler[:4]


def bes_fiyat_teyit_baslat(aday, bes_skor=None):
    """90+ 5+ Benzer profili için fiyat devam teyidini başlatır; işlem kararına ETKİ ETMEZ."""
    try:
        symbol = aday.get("symbol")
        fiyat = float(aday.get("fiyat", 0) or 0)
    except Exception:
        return

    if not symbol or fiyat <= 0:
        return

    # Aynı güçlü profil için aktif teyidi yeniden başlatıp süreyi uzatma.
    mevcut = BES_FIYAT_TEYIT.get(symbol)
    if mevcut and mevcut.get("aktif"):
        return

    BES_FIYAT_TEYIT[symbol] = {
        "aktif": True,
        "baslangic_fiyati": fiyat,
        "baslangic_zamani": time.time(),
        "maks_getiri": 0.0,
        "ardisik_tutunma": 0,
        "teyit_gonderildi": False,
    }


def bes_fiyat_teyit_guncelle(fiyatlar):
    """Mevcut 15 sn ticker akışıyla gönderilmiş AL sonrası gerçek fiyat devamını teyit eder."""
    if not BES_FIYAT_TEYIT:
        return

    simdi = time.time()
    for symbol, p in list(BES_FIYAT_TEYIT.items()):
        if not p.get("aktif"):
            continue

        if simdi - float(p.get("baslangic_zamani", simdi)) > BES_FIYAT_TEYIT_SURESI:
            p["aktif"] = False
            continue

        fiyat = fiyatlar.get(symbol)
        if not fiyat:
            continue

        baslangic = float(p.get("baslangic_fiyati", fiyat) or fiyat)
        if baslangic <= 0:
            continue

        getiri = _pct(fiyat, baslangic)
        p["maks_getiri"] = max(float(p.get("maks_getiri", 0) or 0), getiri)

        # +%0.35 üzerinde iki ardışık 15 sn kontrol = tutunma;
        # teyit için ayrıca pencere içinde en az +%0.50 görülmüş olmalı.
        if getiri >= BES_FIYAT_TEYIT_TUTUNMA:
            p["ardisik_tutunma"] = int(p.get("ardisik_tutunma", 0) or 0) + 1
        else:
            p["ardisik_tutunma"] = 0

        if (
            not p.get("teyit_gonderildi")
            and float(p.get("maks_getiri", 0) or 0) >= BES_FIYAT_TEYIT_HEDEF
            and int(p.get("ardisik_tutunma", 0) or 0) >= BES_FIYAT_TEYIT_ARDISIK
        ):
            p["teyit_gonderildi"] = True
            p["aktif"] = False
            gorunen = symbol[:-3] if symbol.endswith("TRY") else symbol
            mesaj = (
                f"🚀 {kalin_coin_yazisi(gorunen)} | ✅ FİYAT DEVAMI TEYİTLİ\n"
                f"Başlangıç: {baslangic:.4f} | Güncel: {fiyat:.4f} | Devam: %{getiri:+.2f}\n"
                f"📈 AL sonrası fiyat devamı onaylandı."
            )
            print(mesaj)
            telegram_gonder(mesaj)


def _al_takip_yukle():
    """Deploy/restart sonrasında açık +%5 takiplerini Railway Volume'dan geri yükler."""
    try:
        if os.path.exists(AL_TAKIP_DOSYA):
            with open(AL_TAKIP_DOSYA, "r", encoding="utf-8") as f:
                veri = json.load(f)
            if isinstance(veri, dict):
                return {
                    str(symbol): kayit
                    for symbol, kayit in veri.items()
                    if isinstance(kayit, dict)
                    and kayit.get("aktif")
                    and not kayit.get("kar_bildirildi")
                    and float(kayit.get("giris", 0) or 0) > 0
                }
    except Exception as e:
        print("AL takip dosyası okunamadı:", e)
    return {}


def _al_takip_kaydet():
    """Açık +%5 takiplerini atomik yazar; yarım JSON ile takip kaybını önler."""
    try:
        klasor = os.path.dirname(os.path.abspath(AL_TAKIP_DOSYA))
        if klasor:
            os.makedirs(klasor, exist_ok=True)
        gecici = AL_TAKIP_DOSYA + ".tmp"
        with open(gecici, "w", encoding="utf-8") as f:
            json.dump(AL_TAKIP, f, ensure_ascii=False, indent=2)
        os.replace(gecici, AL_TAKIP_DOSYA)
    except Exception as e:
        print("AL takip dosyası yazılamadı:", e)


def _al_takip_ogrenmeden_tamamla():
    """Takip dosyası yoksa son 3 saatteki gerçek Telegram AL kayıtlarından onarır."""
    simdi = time.time()
    degisti = False
    for k in AL_OGRENME_KAYITLARI:
        if str(k.get("kayit_tipi", "telegram")) != "telegram" or k.get("tamamlandi"):
            continue
        if simdi - float(k.get("zaman", 0) or 0) >= AL_OGRENME_SURESI:
            continue
        symbol = str(k.get("symbol", "") or "")
        giris = float(k.get("giris", 0) or 0)
        if not symbol or giris <= 0 or symbol in AL_TAKIP:
            continue
        AL_TAKIP[symbol] = {
            "aktif": True,
            "giris": giris,
            "kar_bildirildi": False,
            "sinyal_event_id": k.get("sinyal_event_id"),
            "baslangic_zamani": float(k.get("zaman", simdi) or simdi),
        }
        degisti = True
    if degisti:
        _al_takip_kaydet()


def al_takip_baslat(aday):
    """Gerçek AL mesajı gönderilen coini yalnızca +%5 kâr bildirimi için takip eder."""
    symbol = aday.get("symbol")
    fiyat = float(aday.get("fiyat", 0) or 0)
    if not symbol or fiyat <= 0:
        return

    mevcut = AL_TAKIP.get(symbol)
    if mevcut and mevcut.get("aktif"):
        return

    AL_TAKIP[symbol] = {
        "aktif": True,
        "giris": fiyat,
        "kar_bildirildi": False,
        "sinyal_event_id": aday.get("_sinyal_event_id"),
        "baslangic_zamani": time.time(),
    }
    _al_takip_kaydet()


def al_takip_guncelle(ticker):
    """
    Otomatik SAT/ÇIK yok.
    Sadece ilk AL fiyatına göre +%5 görülünce tek seferlik ara kâr mesajı yollar.
    """
    if not AL_TAKIP:
        return

    fiyatlar = {}
    for coin in ticker:
        try:
            sym = coin.get("pair", "")
            f = float(coin.get("last", 0) or 0)
            if sym and f > 0:
                fiyatlar[sym] = f
        except Exception:
            pass

    # Aynı 15 sn fiyat akışıyla 90+ profil sonrası gerçek fiyat devamını da kontrol et.
    bes_fiyat_teyit_guncelle(fiyatlar)

    for symbol, p in AL_TAKIP.items():
        if not p.get("aktif") or p.get("kar_bildirildi"):
            continue

        fiyat = fiyatlar.get(symbol)
        if not fiyat:
            continue

        giris = float(p.get("giris", fiyat))
        getiri = _pct(fiyat, giris)

        if getiri >= KAR_BILDIR_ESIK:
            mesaj = (
                f"💰 +%5 KÂR BÖLGESİ - {kalin_coin_yazisi(symbol[:-3] if symbol.endswith('TRY') else symbol)}\n"
                f"İlk AL: {giris:.4f} | Güncel: {fiyat:.4f}\n"
                f"Getiri: %{getiri:+.2f}\n"
                f"Not: Çık emri değil; kârı değerlendirmek / çıkışa hazırlanmak için ara uyarı."
            )
            print(mesaj)
            if telegram_gonder(mesaj):
                p["kar_bildirildi"] = True
                p["aktif"] = False
                _sinyal_sira_hit5_isaretle(symbol, p.get("sinyal_event_id"))
                _al_takip_kaydet()
            else:
                print(symbol, "+%5 mesajı gönderilemedi; sonraki 15 sn kontrolde tekrar denenecek.")

    # Aynı 15 sn ticker akışı AL öğrenmesini de günceller; ekstra API isteği oluşturmaz.
    al_ogrenme_guncelle(ticker)
    rejim_raporu_gerekirse_gonder()


def _rejim_etiketi(x, guclu=1.0, zayif=-1.0):
    try:
        x = float(x)
    except Exception:
        x = 0.0
    if x >= guclu:
        return "Güçlü"
    if x <= zayif:
        return "Zayıf"
    return "Yatay"


def _al_ogrenme_yukle():
    try:
        if os.path.exists(AL_OGRENME_DOSYA):
            with open(AL_OGRENME_DOSYA, "r", encoding="utf-8") as f:
                veri = json.load(f)
                if isinstance(veri, list):
                    return veri
    except Exception as e:
        print("AL öğrenme dosyası okunamadı:", e)
    return []


def _al_ogrenme_kaydet():
    try:
        klasor = os.path.dirname(os.path.abspath(AL_OGRENME_DOSYA))
        if klasor:
            os.makedirs(klasor, exist_ok=True)
        # Kümülatif öğrenme için geniş geçmiş tut.
        with open(AL_OGRENME_DOSYA, "w", encoding="utf-8") as f:
            json.dump(AL_OGRENME_KAYITLARI[-20000:], f, ensure_ascii=False)
    except Exception as e:
        print("AL öğrenme dosyası yazılamadı:", e)


def al_ogrenme_baslat(
    aday, btc_d, piyasa_fiyatlari, piyasa_medyan3, btc_giris,
    kayit_tipi="telegram",
):
    symbol = aday.get("symbol")
    giris = float(aday.get("fiyat", 0) or 0)
    if not symbol or giris <= 0:
        return

    # Aynı aktif Telegram veya aynı filtre gölgesi için ikinci kayıt açma.
    # Filtre gölgesi gerçek Telegram kaydını engellemez.
    for k in reversed(AL_OGRENME_KAYITLARI[-100:]):
        if (
            k.get("symbol") == symbol
            and not k.get("tamamlandi")
            and str(k.get("kayit_tipi", "telegram")) == str(kayit_tipi)
        ):
            return

    simdi = time.time()
    kayit = {
        "symbol": symbol,
        "zaman": simdi,
        "giris": giris,
        "max_getiri": 0.0,
        "min_getiri": 0.0,
        "son_getiri": None,
        "tamamlandi": False,
        "kayit_tipi": str(kayit_tipi),
        "btc_rejim": _rejim_etiketi(btc_d.get("3s", 0)),
        "btc_3s": round(float(btc_d.get("3s", 0) or 0), 3),
        "piyasa_rejim": _rejim_etiketi(piyasa_medyan3),
        "piyasa_medyan_3s": round(float(piyasa_medyan3 or 0), 3),
        "piyasa_giris_fiyatlari": piyasa_fiyatlari,
        "btc_giris": float(btc_giris or 0),
        "ai": float(aday.get("ai_skoru", 0) or 0),
        "erken": float(aday.get("erken_puan", 0) or 0),
        "giris_skoru": float(aday.get("giris_kalitesi", 0) or 0),
        "devam": float(aday.get("devam_gucu", 0) or 0),
        "kalicilik": float(aday.get("kalicilik_skoru", 0) or 0),
        # Genel Güç yalnız bilgi/öğrenme metriğidir; AL filtresini değiştirmez.
        "genel_guc": float(aday.get("genel_guc_skoru", 0) or 0),
        # Genel Güç alt bileşenleri: haftalık motor puanın hangi bloktan şiştiğini görebilsin.
        "skor_kalite": float(aday.get("genel_skor_kalite", 0) or 0),
        "momentum_kalite": float(aday.get("genel_momentum_kalite", 0) or 0),
        "piyasa_kalite": float(aday.get("genel_piyasa_kalite", 0) or 0),
        "neden_kalite": float(aday.get("genel_neden_kalite", 0) or 0),
        "neden_sayisi": int(aday.get("neden_sayisi", 0) or 0),
        "onemli_neden_sayisi": int(aday.get("onemli_neden_sayisi", 0) or 0),
        "neden_agirlikli_toplam": float(aday.get("neden_agirlikli_toplam", 0) or 0),
        "strateji_surumu": STRATEJI_SURUMU,
        "genel_devam_bilesen": float(aday.get("genel_devam_bilesen", 0) or 0),
        "genel_rel_bilesen": float(aday.get("genel_rel_bilesen", 0) or 0),
        "genel_kalicilik_bant": float(aday.get("genel_kalicilik_bant", 0) or 0),
        "genel_hareket_bilesen": float(aday.get("genel_hareket_bilesen", 0) or 0),
        "genel_adx_bilesen": float(aday.get("genel_adx_bilesen", 0) or 0),
        "al_odak_puani": float(aday.get("al_odak_puani", 0) or 0),
        "erken_yakalama_puani": float(aday.get("erken_yakalama_puani", 0) or 0),
        "btc_sok_puani": float(aday.get("btc_sok_puani", 0) or 0),
        "piyasa_devam_ceza": float(aday.get("piyasa_devam_ceza", 0) or 0),
        "piyasa_geri_verme": float(aday.get("piyasa_geri_verme", 0) or 0),
        "piyasa_pozitif_oran": float(aday.get("piyasa_pozitif_oran", 0) or 0),
        "kategori": aday.get("radar_kategori", ""),
        # 60dk göreceli güç bonusu AL filtresi değildir; yalnız ölçüm/öncelik bilgisidir.
        "goreceli_guc_bonus": int(aday.get("goreceli_guc_bonus", 0) or 0),
        "coin_btc_60": round(float(aday.get("coin_btc_60", 0) or 0), 3),
        "coin_piyasa_60": round(float(aday.get("coin_piyasa_60", 0) or 0), 3),
        # Kod geliştirme öneri motoru için AL anındaki ham özellikler.
        "radar": round(float(aday.get("radar_skoru", 0) or 0), 3),
        "hacim": round(float(aday.get("hacim", 0) or 0), 3),
        "d1": round(float((aday.get("mikro") or {}).get("d1", 0) or 0), 3),
        "d3": round(float((aday.get("mikro") or {}).get("d3", 0) or 0), 3),
        "d5": round(float((aday.get("mikro") or {}).get("d5", 0) or 0), 3),
        "d10": round(float((aday.get("mikro") or {}).get("d10", 0) or 0), 3),
        "vr310": round(float((aday.get("mikro") or {}).get("vr310", 0) or 0), 3),
        "stair5": bool((aday.get("mikro") or {}).get("stair5")),
        "momentum_hizlaniyor": bool(aday.get("momentum_hizlaniyor")),
        "hacim_hizlaniyor": bool(aday.get("hacim_hizlaniyor")),
        "btc_farki_aciliyor": bool(aday.get("btc_farki_aciliyor")),
        "lider_gucleniyor": bool(aday.get("lider_gucleniyor")),
        "basamakli_trend": bool(aday.get("basamakli_trend") or (aday.get("mikro") or {}).get("basamak")),
        "rsi": round(float(((aday.get("teknik") or {}).get("rsi", 0) or 0)), 3),
        "adx": round(float(((aday.get("teknik") or {}).get("adx", 0) or 0)), 3),
        "neden_metin": " | ".join(str(x) for x in (aday.get("nedenler") or [])),
        "v11_filtre_adayi": bool(aday.get("v11_filtre_adayi")),
        "v11_filtre_kabul": bool(aday.get("v11_filtre_kabul", True)),
        "v11_filtre_nedenleri": list(aday.get("v11_filtre_nedenleri", [])),
        "v11_filtre_ai_zayif": bool(aday.get("v11_filtre_ai_zayif")),
        "v11_filtre_devam_zayif": bool(aday.get("v11_filtre_devam_zayif")),
        "v11_filtre_rel_yok": bool(aday.get("v11_filtre_rel_yok")),
        "v11_filtre_ek_risk": bool(aday.get("v11_filtre_ek_risk")),
        "v11_yol_asiri_rel": bool(aday.get("v11_yol_asiri_rel")),
        "v11_yol_temiz_momentum": bool(aday.get("v11_yol_temiz_momentum")),
        "v11_momentum_pozitif_sayisi": int(aday.get("v11_momentum_pozitif_sayisi", 0) or 0),
        "v11_gec_teyit": bool(aday.get("v11_gec_teyit")),
        "v11_gec_teyit_nedenleri": list(aday.get("v11_gec_teyit_nedenleri", [])),
        "v11_seviye": int(aday.get("v11_seviye", 0) or 0),
        "v11_kontrollu_ust_duzey": bool(aday.get("v11_kontrollu_ust_duzey")),
    }
    AL_OGRENME_KAYITLARI.append(kayit)
    _al_ogrenme_kaydet()


def al_ogrenme_guncelle(ticker):
    if not AL_OGRENME_KAYITLARI:
        return

    simdi = time.time()
    fiyatlar = {}
    for coin in ticker:
        try:
            sym = coin.get("pair", "")
            f = float(coin.get("last", 0) or 0)
            if sym and f > 0:
                fiyatlar[sym] = f
        except Exception:
            pass

    degisti = False
    for k in AL_OGRENME_KAYITLARI:
        if k.get("tamamlandi"):
            continue
        symbol = k.get("symbol")
        fiyat = fiyatlar.get(symbol)
        giris = float(k.get("giris", 0) or 0)
        if fiyat and giris > 0:
            getiri = _pct(fiyat, giris)
            k["max_getiri"] = round(max(float(k.get("max_getiri", 0) or 0), getiri), 3)
            k["min_getiri"] = round(min(float(k.get("min_getiri", 0) or 0), getiri), 3)
            degisti = True

        if simdi - float(k.get("zaman", simdi)) < AL_OGRENME_SURESI:
            continue

        if fiyat and giris > 0:
            k["son_getiri"] = round(_pct(fiyat, giris), 3)

        piyasa_getirileri = []
        for sym, ilk in (k.get("piyasa_giris_fiyatlari") or {}).items():
            son = fiyatlar.get(sym)
            try:
                ilk = float(ilk)
                if ilk > 0 and son:
                    piyasa_getirileri.append(_pct(son, ilk))
            except Exception:
                pass
        piyasa_3s = statistics.median(piyasa_getirileri) if piyasa_getirileri else 0.0
        k["piyasa_3s_getiri"] = round(piyasa_3s, 3)

        btc_giris = float(k.get("btc_giris", 0) or 0)
        btc_son = float(fiyatlar.get("BTCTRY", 0) or 0)
        k["btc_3s_son_getiri"] = round(_pct(btc_son, btc_giris), 3) if btc_giris > 0 and btc_son > 0 else None

        if k.get("son_getiri") is not None:
            k["piyasa_ustu"] = round(float(k["son_getiri"]) - piyasa_3s, 3)
        k["tamamlandi"] = True
        k["tamamlanma_zamani"] = simdi
        degisti = True

    if degisti:
        _al_ogrenme_kaydet()


def _grup_satiri(baslik, kayitlar):
    if not kayitlar:
        return f"{baslik}: veri yok"
    n = len(kayitlar)
    p4 = sum(1 for x in kayitlar if float(x.get("max_getiri", 0) or 0) >= 4) / n * 100
    p7 = sum(1 for x in kayitlar if float(x.get("max_getiri", 0) or 0) >= 7) / n * 100
    p10 = sum(1 for x in kayitlar if float(x.get("max_getiri", 0) or 0) >= 10) / n * 100
    son = [float(x.get("son_getiri", 0) or 0) for x in kayitlar if x.get("son_getiri") is not None]
    ust = [float(x.get("piyasa_ustu", 0) or 0) for x in kayitlar if x.get("piyasa_ustu") is not None]
    ort_son = sum(son) / len(son) if son else 0.0
    ort_ust = sum(ust) / len(ust) if ust else 0.0
    return f"{baslik}: n={n} | +%4 %{p4:.1f} | +%7 %{p7:.1f} | +%10 %{p10:.1f} | 3s %{ort_son:+.2f} | piyasa üstü %{ort_ust:+.2f}"


def rejim_raporu_gerekirse_gonder():
    global SON_REJIM_RAPOR_ZAMANI
    simdi = time.time()
    if simdi - SON_REJIM_RAPOR_ZAMANI < REJIM_RAPOR_ARALIGI:
        return

    SON_REJIM_RAPOR_ZAMANI = simdi
    tamam = [
        x for x in AL_OGRENME_KAYITLARI
        if x.get("tamamlandi")
        and x.get("son_getiri") is not None
        and str(x.get("kayit_tipi", "telegram")) == "telegram"
    ]
    # Ana rapor artık KÜMÜLATİF: eldeki tüm tamamlanmış AL kayıtlarını kullanır.
    # Son 24 saat sayısı ayrıca bilgi olarak gösterilir.
    gunluk = [x for x in tamam if simdi - float(x.get("tamamlanma_zamani", 0) or 0) <= 24 * 60 * 60]
    if not tamam:
        return

    rapor_kayitlari = tamam

    btc_guclu = [x for x in rapor_kayitlari if x.get("btc_rejim") == "Güçlü"]
    btc_yatay = [x for x in rapor_kayitlari if x.get("btc_rejim") == "Yatay"]
    btc_zayif = [x for x in rapor_kayitlari if x.get("btc_rejim") == "Zayıf"]
    piy_guclu = [x for x in rapor_kayitlari if x.get("piyasa_rejim") == "Güçlü"]
    piy_yatay = [x for x in rapor_kayitlari if x.get("piyasa_rejim") == "Yatay"]
    piy_zayif = [x for x in rapor_kayitlari if x.get("piyasa_rejim") == "Zayıf"]

    # 60dk göreceli güç bonusunu da tüm geçmiş tamamlanmış AL'larda ölç.
    rel2 = [x for x in rapor_kayitlari if int(x.get("goreceli_guc_bonus", 0) or 0) >= 2]
    rel1 = [x for x in rapor_kayitlari if int(x.get("goreceli_guc_bonus", 0) or 0) == 1]
    rel0 = [x for x in rapor_kayitlari if int(x.get("goreceli_guc_bonus", 0) or 0) == 0]

    edge = [float(x.get("piyasa_ustu", 0) or 0) for x in rapor_kayitlari if x.get("piyasa_ustu") is not None]
    ort_edge = sum(edge) / len(edge) if edge else 0.0
    piy = [float(x.get("piyasa_3s_getiri", 0) or 0) for x in rapor_kayitlari]
    ort_piy = sum(piy) / len(piy) if piy else 0.0

    if ort_edge >= 1.0:
        secicilik = "Güçlü"
    elif ort_edge >= 0.30:
        secicilik = "Orta"
    elif ort_edge > 0:
        secicilik = "Zayıf pozitif"
    else:
        secicilik = "Yok / negatif"

    if ort_piy >= 1.0 and ort_edge < 0.5:
        piyasa_etkisi = "Yüksek"
    elif abs(ort_piy) < 0.5 and ort_edge >= 0.5:
        piyasa_etkisi = "Düşük"
    else:
        piyasa_etkisi = "Orta / karışık"

    mesaj = (
        "📊 AL REJİM / SEÇİCİLİK RAPORU\n\n"
        + _grup_satiri("BTC Güçlü", btc_guclu) + "\n"
        + _grup_satiri("BTC Yatay", btc_yatay) + "\n"
        + _grup_satiri("BTC Zayıf", btc_zayif) + "\n\n"
        + _grup_satiri("Piyasa Güçlü", piy_guclu) + "\n"
        + _grup_satiri("Piyasa Yatay", piy_yatay) + "\n"
        + _grup_satiri("Piyasa Zayıf", piy_zayif) + "\n\n"
        + "🎯 60dk GÖRECELİ GÜÇ BONUSU\n"
        + _grup_satiri("Bonus +2 (BTC ve piyasa eşiği birlikte)", rel2) + "\n"
        + _grup_satiri("Bonus +1 (eşiklerden biri)", rel1) + "\n"
        + _grup_satiri("Bonus 0", rel0) + "\n\n"
        + f"🤖 Bot seçiciliği: {secicilik}\n"
        + f"🌍 Piyasa etkisi: {piyasa_etkisi}\n"
        + f"AL coinlerinin ortalama piyasa üstü 3s getirisi: %{ort_edge:+.2f}\n"
        + f"Bugün tamamlanan AL: {len(gunluk)}\n"
        + f"Toplam öğrenilmiş AL: {len(tamam)}"
    )
    print(mesaj)
    telegram_gonder(mesaj)


def _basari_orani(kayitlar):
    if not kayitlar:
        return 0.0
    return sum(1 for x in kayitlar if float(x.get("max_getiri", 0) or 0) >= 5.0) / len(kayitlar) * 100.0

def _medyan_deger(kayitlar, alan):
    vals = []
    for x in kayitlar:
        try:
            v = x.get(alan)
            if v is not None:
                vals.append(float(v))
        except Exception:
            pass
    return statistics.median(vals) if vals else None

def _ozellik_var(k, anahtar):
    """Özelliği önce doğrudan kayıttan, eski kayıtlar için metinden okur."""
    dogrudan = {
        "momentum hızlanıyor": "momentum_hizlaniyor",
        "hacim hızlanıyor": "hacim_hizlaniyor",
        "btc farkı açılıyor": "btc_farki_aciliyor",
        "lider güçleniyor": "lider_gucleniyor",
        "stair5": "basamakli_trend",
    }
    alan = dogrudan.get(anahtar)
    if alan and alan in k:
        return bool(k.get(alan))
    metin = str(k.get("neden_metin", "") or "").lower()
    if anahtar == "stair5":
        return bool(k.get("stair5")) or "basamak" in metin
    return anahtar.lower() in metin

# Mevcut dosyadaki gerçek karar yapısının kısa özeti.
# Öneri motoru istatistiği bu tabloyla birleştirir; böylece yalnız "özellik iyi" demek yerine
# dosyada halihazırda kullanılıyor mu ve nasıl değiştirilmesi gerektiğini söyler.
MEVCUT_KOD_KURALLARI = {
    "Genel Güç": (False, "yalnız bilgi/öğrenme puanı; AL filtresi değil"),
    "Devam Gücü": (False, "AL kapısında doğrudan veto değil; destek/izleme bilgisi"),
    "Kalıcılık": (False, "AL kapısında doğrudan kullanılmıyor"),
    "Giriş skoru": (False, "AL kapısında doğrudan kullanılmıyor"),
    "Erken skor": (False, "erken yakalama bilgisi; ana AL puanına doğrudan eşik değil"),
    "Radar skoru": (True, "AI skorunda (Radar-55) katkısı ve Elit/Yıldız eşiklerinde aktif"),
    "Hacim çarpanı": (False, "ana H karar kapısında doğrudan eşik değil"),
    "1dk momentum": (True, "H karar motorunda deg1 ile puanlanıyor"),
    "3dk momentum": (True, "H karar motorunda deg3 ile puanlanıyor; Yıldız istisnasında da aktif"),
    "5dk momentum": (False, "ana H karar kapısında doğrudan kullanılmıyor"),
    "10dk momentum": (False, "ana H karar kapısında doğrudan kullanılmıyor"),
    "3dk hacim / 10dk ort": (False, "öğrenme/erken yapı bilgisi; ana AL kapısında doğrudan yok"),
    "Coin-BTC 60dk göreceli güç": (False, "ölçüm/öncelik bilgisi; ana AL filtresi değil"),
    "Coin-Piyasa 60dk göreceli güç": (False, "ölçüm/öncelik bilgisi; ana AL filtresi değil"),
    "RSI": (True, "H karar motorunda aralık bazlı puan ve AL kapılarında eşik aktif"),
    "ADX": (True, "H karar motorunun ana ayırıcılarından; AL kapılarında aktif"),
    "BTC 3s": (False, "rejim/piyasa desteği bilgisi; ana AL kapısında doğrudan yok"),
    "Piyasa 3s": (False, "rejim/piyasa desteği bilgisi; ana AL kapısında doğrudan yok"),
    "Momentum hızlanıyor": (False, "Devam bilgisinde destekleyici; ana H AL kapısında zorunlu değil"),
    "Hacim hızlanıyor": (False, "Devam bilgisinde destekleyici; ana H AL kapısında zorunlu değil"),
    "BTC farkı açılıyor": (False, "mesaj/destek bilgisi; ana H AL kapısında zorunlu değil"),
    "Lider güçleniyor": (False, "liderlik yapısına katkı var; tek başına AL şartı değil"),
    "Basamaklı trend": (False, "mikro/erken yapıda destekleyici; ana H AL kapısında zorunlu değil"),
}

def _kod_durumu(ad):
    aktif, aciklama = MEVCUT_KOD_KURALLARI.get(ad, (False, "mevcut karar motorunda özel eşik tanımlı değil"))
    return aktif, aciklama

def _eylem_sec(ad, fark, rejim=None):
    aktif, _ = _kod_durumu(ad)
    if fark > 0:
        if aktif:
            return "MEVCUT KURALI GÜÇLENDİR"
        return "KODA EKLE / BONUS VER"
    if aktif:
        return "MEVCUT KURALI AZALT / ÇIKAR ADAYI"
    return "NEGATİF BONUS / KAÇINMA KURALI DENE"

def _gun_anahtari(k):
    try:
        ts = float(k.get("tamamlanma_zamani", 0) or k.get("zaman", 0) or 0)
        if ts <= 0:
            return None
        return time.strftime("%Y-%m-%d", time.localtime(ts))
    except Exception:
        return None

def _yon_tekrari_sayisal(kayitlar, alan, genel_yon):
    """Özelliğin aynı yönü kaç farklı günde ve piyasa rejiminde tekrar ettiğini sayar."""
    gunler = {}
    for x in kayitlar:
        g = _gun_anahtari(x)
        if not g:
            continue
        gunler.setdefault(g, []).append(x)

    ayni_gun = 0
    toplam_gun = 0
    for _, grup in gunler.items():
        e = _sayisal_etki(grup, alan)
        if not e:
            continue
        toplam_gun += 1
        fark = e[3]
        if (genel_yon > 0 and fark > 0) or (genel_yon < 0 and fark < 0):
            ayni_gun += 1

    ayni_rejim = 0
    toplam_rejim = 0
    for rejim in ("Güçlü", "Yatay", "Zayıf"):
        grup = [x for x in kayitlar if x.get("piyasa_rejim") == rejim]
        e = _sayisal_etki(grup, alan)
        if not e:
            continue
        toplam_rejim += 1
        fark = e[3]
        if (genel_yon > 0 and fark > 0) or (genel_yon < 0 and fark < 0):
            ayni_rejim += 1

    return ayni_gun, toplam_gun, ayni_rejim, toplam_rejim

def _yon_tekrari_bayrak(kayitlar, anahtar, genel_yon):
    gunler = {}
    for x in kayitlar:
        g = _gun_anahtari(x)
        if not g:
            continue
        gunler.setdefault(g, []).append(x)

    ayni_gun = 0
    toplam_gun = 0
    for _, grup in gunler.items():
        e = _bayrak_etki(grup, anahtar)
        if not e:
            continue
        toplam_gun += 1
        fark = e[2]
        if (genel_yon > 0 and fark > 0) or (genel_yon < 0 and fark < 0):
            ayni_gun += 1

    ayni_rejim = 0
    toplam_rejim = 0
    for rejim in ("Güçlü", "Yatay", "Zayıf"):
        grup = [x for x in kayitlar if x.get("piyasa_rejim") == rejim]
        e = _bayrak_etki(grup, anahtar)
        if not e:
            continue
        toplam_rejim += 1
        fark = e[2]
        if (genel_yon > 0 and fark > 0) or (genel_yon < 0 and fark < 0):
            ayni_rejim += 1

    return ayni_gun, toplam_gun, ayni_rejim, toplam_rejim

def _guven_hesapla(fark, n, ayni_gun=0, toplam_gun=0, ayni_rejim=0, toplam_rejim=0):
    """Örneklem + etki + gün/rejim tekrarıyla temkinli güven seviyesi üretir."""
    etki = abs(float(fark or 0))
    puan = 0

    if n >= GELISTIRME_YUKSEK_N:
        puan += 3
    elif n >= GELISTIRME_ORTA_N:
        puan += 2
    elif n >= GELISTIRME_DUSUK_N:
        puan += 1

    if etki >= 30:
        puan += 2
    elif etki >= 18:
        puan += 1

    if ayni_gun >= 5:
        puan += 3
    elif ayni_gun >= GELISTIRME_MIN_GUN_GUCLU:
        puan += 2
    elif ayni_gun >= 2:
        puan += 1

    if ayni_rejim >= GELISTIRME_MIN_REJIM_GUCLU:
        puan += 2
    elif ayni_rejim >= 1:
        puan += 1

    if n < 20:
        seviye = "DÜŞÜK"
    elif puan >= 7:
        seviye = "ÇOK YÜKSEK"
    elif puan >= 5:
        seviye = "YÜKSEK"
    elif puan >= 3:
        seviye = "ORTA"
    else:
        seviye = "DÜŞÜK"

    return {
        "seviye": seviye,
        "n": int(n),
        "etki": round(etki, 1),
        "ayni_gun": int(ayni_gun),
        "toplam_gun": int(toplam_gun),
        "ayni_rejim": int(ayni_rejim),
        "toplam_rejim": int(toplam_rejim),
    }

def _eylem_stabilize(eylem, fark, guven):
    """Tek haftalık/küçük örneklem sonucu yüzünden agresif 'çıkar' önerisini engeller."""
    guven_seviye = guven.get("seviye", "DÜŞÜK") if isinstance(guven, dict) else "DÜŞÜK"
    gun = guven.get("ayni_gun", 0) if isinstance(guven, dict) else 0
    rejim = guven.get("ayni_rejim", 0) if isinstance(guven, dict) else 0

    tekrarlı = (gun >= GELISTIRME_MIN_GUN_GUCLU) or (rejim >= GELISTIRME_MIN_REJIM_GUCLU)
    if fark < 0:
        if not tekrarlı or guven_seviye in ("DÜŞÜK", "ORTA"):
            return "AZALT / TEST ET"
        if "ÇIKAR" in eylem:
            return "AZALT / ÇIKAR ADAYI"
    else:
        if guven_seviye == "DÜŞÜK":
            return "BONUSU TEST ET"
    return eylem

def _sayisal_etki(kayitlar, alan):
    vals=[]
    for x in kayitlar:
        try:
            if x.get(alan) is not None:
                vals.append(float(x.get(alan)))
        except Exception:
            pass
    if len(vals) < GELISTIRME_MIN_KAYIT:
        return None
    esik=statistics.median(vals)
    ust=[x for x in kayitlar if x.get(alan) is not None and float(x.get(alan)) >= esik]
    alt=[x for x in kayitlar if x.get(alan) is not None and float(x.get(alan)) < esik]
    if len(ust) < GELISTIRME_MIN_GRUP or len(alt) < GELISTIRME_MIN_GRUP:
        return None
    ru,ra=_basari_orani(ust),_basari_orani(alt)
    return esik,ru,ra,ru-ra,len(ust),len(alt)


def _kayit_kimligi(k):
    return f"{k.get('symbol','')}|{float(k.get('zaman',0) or 0):.3f}|{k.get('kayit_tipi','')}"


def _onerilerde_ayni_grubu_birlestir(oneriler):
    """Aynı coin kümesini seçen Devam/Kalite metriklerini tek öneriye indirir."""
    aile = {"genel_guc", "genel_devam_bilesen", "al_odak_puani", "devam"}
    adaylar = [
        o for o in oneriler
        if o.get("alan") in aile
        and o.get("rejim") == "TÜM PİYASA"
        and float(o.get("fark", 0) or 0) > 0
        and o.get("uyeler")
    ]
    if len(adaylar) < 2:
        return oneriler

    # En güçlü önerinin seçtiği kümeyle en az %90 örtüşenleri aynı keşif say.
    lider = max(adaylar, key=lambda o: float(o.get("puan", 0) or 0))
    lider_uye = set(lider.get("uyeler") or [])
    benzer = []
    for o in adaylar:
        uye = set(o.get("uyeler") or [])
        birlesim = lider_uye | uye
        jaccard = len(lider_uye & uye) / len(birlesim) if birlesim else 0.0
        if jaccard >= 0.90:
            benzer.append(o)
    if len(benzer) < 2:
        return oneriler

    adlar = [str(o.get("ozellik", "")) for o in benzer]
    esikler = [f"{o.get('ozellik')} ≥{float(o.get('esik',0) or 0):.2f}" for o in benzer]
    birlesik = dict(lider)
    birlesik.update({
        "puan": max(float(o.get("puan", 0) or 0) for o in benzer) + 2.0,
        "eylem": "BİRLEŞİK BONUSU TEST ET",
        "ozellik": "Devam Kalitesi (birleşik)",
        "aciklama": (
            f"Aynı/çok benzer coin grubunu seçen {len(benzer)} ölçüm tek keşifte birleştirildi: "
            + ", ".join(adlar)
            + f". Lider ayrım: +%5 %{float(lider.get('ust_oran',0) or 0):.1f} / "
              f"alt %{float(lider.get('alt_oran',0) or 0):.1f} "
              f"(n={int(lider.get('n_ust',0) or 0)}/{int(lider.get('n_alt',0) or 0)})."
        ),
        "kod": (
            "Ayrı ayrı puan/bonus verme. Tek Devam Kalitesi gölge etiketi kullan: "
            + " + ".join(esikler)
            + ". Canlı AL kapısını değiştirme."
        ),
        "birlesen_alanlar": [o.get("alan") for o in benzer],
    })
    benzer_id = {id(o) for o in benzer}
    sonuc = [o for o in oneriler if id(o) not in benzer_id]
    sonuc.append(birlesik)
    return sonuc


def _devam_kalitesi_golge_raporu(kayitlar):
    """Sabit birleşik kalite eşiğini ve 10dk ek teyidini canlı kodu değiştirmeden ölçer."""
    if not kayitlar:
        return ["🧪 DEVAM KALİTESİ BİRLEŞİK GÖLGE TESTİ", "• Ölçülebilir kayıt yok."]

    def kalite(k):
        return (
            float(k.get("genel_guc", 0) or 0) >= DEVAM_KALITE_GENEL_MIN
            and float(k.get("devam", 0) or 0) >= DEVAM_KALITE_DEVAM_MIN
            and float(k.get("al_odak_puani", 0) or 0) >= DEVAM_KALITE_ODAK_MIN
        )

    tum = list(kayitlar)
    q = [k for k in tum if kalite(k)]
    q10 = [k for k in q if float(k.get("d10", 0) or 0) >= DEVAM_KALITE_D10_MIN]
    dis = [k for k in tum if k not in q]
    kazananlar = [k for k in tum if float(k.get("max_getiri", 0) or 0) >= 5.0]

    def satir(ad, grup):
        n = len(grup)
        p3 = sum(1 for k in grup if float(k.get("max_getiri", 0) or 0) >= 3.0) / n * 100.0 if n else 0.0
        p5 = _basari_orani(grup)
        yanlis = (
            sum(
                1 for k in grup
                if float(k.get("max_getiri", 0) or 0) < 5.0
                and float(k.get("min_getiri", 0) or 0) <= -2.5
            ) / n * 100.0
            if n else 0.0
        )
        kacirilan = sum(1 for k in kazananlar if k not in grup)
        return f"• {ad}: n={n} | +%3 %{p3:.1f} | +%5 %{p5:.1f} | yanlış %{yanlis:.1f} | dışarıda kalan +%5={kacirilan}"

    gunler = {g for g in (_gun_anahtari(k) for k in q) if g}
    rejimler = {str(k.get("piyasa_rejim")) for k in q if k.get("piyasa_rejim")}
    satirlar = [
        "🧪 DEVAM KALİTESİ BİRLEŞİK GÖLGE TESTİ",
        satir("Devam Kalitesi", q),
        satir(f"Devam Kalitesi + 10dk ≥%{DEVAM_KALITE_D10_MIN:.2f}", q10),
        satir("Kalite dışı karşılaştırma", dis),
        (
            f"• Eşik: Genel ≥{DEVAM_KALITE_GENEL_MIN:.2f} + Devam ≥{DEVAM_KALITE_DEVAM_MIN:.2f} "
            f"+ Ana odak ≥{DEVAM_KALITE_ODAK_MIN:.2f}"
        ),
    ]
    if len(q) < DEVAM_KALITE_KARAR_MIN or len(gunler) < 3 or len(rejimler) < 2:
        satirlar.append(
            f"• KARAR YOK: kalite n={len(q)}/{DEVAM_KALITE_KARAR_MIN} | gün={len(gunler)}/3 | rejim={len(rejimler)}/2."
        )
    else:
        satirlar.append("• Doğrulama eşiği tamamlandı; canlı bonus öncesi kaçırılan kazananlar manuel incelenmeli.")
    satirlar.append("• Tek birleşik etikettir; dört metriğe ayrı bonus verilmez ve canlı AL değişmez.")
    return satirlar

def _bayrak_etki(kayitlar, anahtar):
    var=[x for x in kayitlar if _ozellik_var(x,anahtar)]
    yok=[x for x in kayitlar if not _ozellik_var(x,anahtar)]
    if len(var) < GELISTIRME_MIN_GRUP or len(yok) < GELISTIRME_MIN_GRUP:
        return None
    rv,ry=_basari_orani(var),_basari_orani(yok)
    return rv,ry,rv-ry,len(var),len(yok)

def _pearson(kayitlar, a, b):
    cift=[]
    for x in kayitlar:
        try:
            va=x.get(a); vb=x.get(b)
            if va is None or vb is None:
                continue
            cift.append((float(va), float(vb)))
        except Exception:
            pass
    if len(cift) < GELISTIRME_MIN_KAYIT:
        return None
    xs=[z[0] for z in cift]; ys=[z[1] for z in cift]
    mx=sum(xs)/len(xs); my=sum(ys)/len(ys)
    dx=[v-mx for v in xs]; dy=[v-my for v in ys]
    sx=sum(v*v for v in dx); sy=sum(v*v for v in dy)
    if sx <= 0 or sy <= 0:
        return None
    r=sum(dx[i]*dy[i] for i in range(len(dx))) / ((sx*sy) ** 0.5)
    return max(-1.0, min(1.0, r))


def _puan_sismesi_onerileri(kayitlar):
    """Yüksek görünen sinyallerde aynı hareketi tekrar ödüllendiren skor çiftlerini arar.
    Amaç yeni veto üretmek değil; korelasyonlu bileşenleri grup/tavan puanına çevirmeyi önermektir.
    """
    if len(kayitlar) < GELISTIRME_MIN_KAYIT:
        return []

    # 80+ Genel Güç özellikle kullanıcıya 'çok güçlü' görünür; burada başarısız olanları ayrı inceliyoruz.
    yuksek=[x for x in kayitlar if float(x.get("genel_guc",0) or 0) >= 80.0]
    if len(yuksek) < GELISTIRME_MIN_GRUP * 2:
        return []
    basarili=[x for x in yuksek if float(x.get("max_getiri",0) or 0) >= 5.0]
    basarisiz=[x for x in yuksek if float(x.get("max_getiri",0) or 0) < 5.0]
    if len(basarisiz) < GELISTIRME_MIN_GRUP:
        return []

    alanlar=[
        ("ai","AI"),("giris_skoru","Giriş"),("devam","Devam"),("kalicilik","Kalıcılık"),
        ("radar","Radar"),("rsi","RSI"),("adx","ADX"),
        ("skor_kalite","Skor bloğu"),("momentum_kalite","Momentum bloğu"),
        ("neden_kalite","Neden bloğu"),
    ]
    medyan={}
    for alan,_ in alanlar:
        medyan[alan]=_medyan_deger(kayitlar,alan)

    adaylar=[]
    for i in range(len(alanlar)):
        for j in range(i+1,len(alanlar)):
            a,ad_a=alanlar[i]; b,ad_b=alanlar[j]
            # Bileşen bloklarını kendi içindeki ham alanlarla eşleştirince korelasyon doğal;
            # rapor için daha anlamlı ham-ham veya blok-blok çiftleri tercih edilir.
            if (a.endswith("_kalite") != b.endswith("_kalite")):
                continue
            r=_pearson(kayitlar,a,b)
            if r is None or r < 0.72:
                continue
            ea,eb=medyan.get(a),medyan.get(b)
            if ea is None or eb is None:
                continue
            def ikisi_yuksek(grup):
                if not grup: return 0.0
                n=0
                for x in grup:
                    try:
                        if float(x.get(a,0) or 0) >= ea and float(x.get(b,0) or 0) >= eb:
                            n+=1
                    except Exception:
                        pass
                return n/len(grup)*100.0
            fb=ikisi_yuksek(basarisiz)
            fs=ikisi_yuksek(basarili)
            fark=fb-fs
            # Yalnız başarısız yüksek-puan sinyallerinde belirgin biçimde daha sık birlikteyse 'şişme' de.
            if fark < 20.0:
                continue
            adaylar.append({
                "puan": abs(fark) + r*20,
                "eylem":"PUAN ŞİŞMESİNİ AZALT / GRUPLA",
                "ozellik":f"{ad_a} + {ad_b}",
                "rejim":"YÜKSEK GENEL GÜÇ",
                "aciklama":(
                    f"Genel Güç 80+ sinyallerde bu ikili +%5 yapmayanların %{fb:.1f}'inde, "
                    f"+%5 yapanların %{fs:.1f}'inde birlikte yüksek. Korelasyon r={r:.2f} "
                    f"(yüksek grup n={len(yuksek)}, başarısız={len(basarisiz)}, başarılı={len(basarili)})."
                ),
                "kod":(
                    "İki göstergenin ayrı ayrı tam puan vermesi yerine ortak grup puanı/tavanı dene; "
                    "sert veto yapma. Genel Güç ve AL kriterini otomatik değiştirme."
                ),
                "guven":_guven_hesapla(fark,len(yuksek),0,0,0,0),
            })

    # Yüksek Genel Güç kendi başına başarısızları yeterince ayırmıyorsa ayrıca kalibrasyon uyarısı üret.
    genel=_basari_orani(kayitlar); yuksek_oran=_basari_orani(yuksek)
    if len(yuksek) >= GELISTIRME_MIN_GRUP*2 and yuksek_oran <= genel + 5.0:
        adaylar.append({
            "puan": 30 + max(0, genel-yuksek_oran),
            "eylem":"GENEL GÜÇ AĞIRLIKLARINI YENİDEN KALİBRE ET",
            "ozellik":"Genel Güç 80+",
            "rejim":"TÜM PİYASA",
            "aciklama":f"Genel başarı %{genel:.1f}; Genel Güç 80+ başarı %{yuksek_oran:.1f} (n={len(yuksek)}). Yüksek puan beklenen ayrımı üretmiyor.",
            "kod":"Skor/Momentum/Piyasa/Neden ağırlıklarını haftalık sonuçlara göre yeniden tart; önce bilgi puanı olarak kalsın.",
            "guven":_guven_hesapla(abs(yuksek_oran-genel),len(yuksek),0,0,0,0),
        })

    adaylar.sort(key=lambda x:(x.get("puan",0), {"DÜŞÜK":0,"ORTA":1,"YÜKSEK":2,"ÇOK YÜKSEK":3}.get((x.get("guven") or {}).get("seviye","DÜŞÜK") if isinstance(x.get("guven"),dict) else "DÜŞÜK",0)),reverse=True)
    return adaylar[:3]



def _asiri_yuksek_paradoks_onerileri(kayitlar):
    """Çok yüksek görünen değerlerin geç kalmış/doygun hareket işareti olup olmadığını test eder."""
    if len(kayitlar) < GELISTIRME_MIN_KAYIT:
        return []

    testler = [
        ("kalicilik", "Kalıcılık", 95.0),
        ("genel_guc", "Genel Güç", 80.0),
        ("rsi", "RSI", 80.0),
        ("adx", "ADX", 45.0),
        ("devam", "Devam Gücü", 85.0),
    ]
    cikti = []
    for alan, ad, esik in testler:
        yuksek = []
        alt = []
        for x in kayitlar:
            try:
                v = float(x.get(alan, 0) or 0)
            except Exception:
                continue
            (yuksek if v >= esik else alt).append(x)

        if len(yuksek) < GELISTIRME_MIN_GRUP or len(alt) < GELISTIRME_MIN_GRUP:
            continue

        ry = _basari_orani(yuksek)
        ra = _basari_orani(alt)
        fark = ry - ra

        # "çok yüksek" grup belirgin biçimde daha kötüyse olgunluk/geç kalmış hareket ihtimali.
        if fark > -15.0:
            continue

        gun, tg, rej, tr = _yon_tekrari_sayisal(kayitlar, alan, -1)
        guven = _guven_hesapla(fark, len(kayitlar), gun, tg, rej, tr)
        eylem = _eylem_stabilize("AŞIRI YÜKSEK / GEÇ KALMIŞ HAREKET TESTİ", fark, guven)

        cikti.append({
            "puan": abs(fark) + 8,
            "eylem": eylem,
            "ozellik": f"{ad} {esik:g}+",
            "rejim": "TÜM PİYASA",
            "aciklama": (
                f"{ad} >= {esik:g} grubunda +%5 başarı %{ry:.1f}; altında %{ra:.1f} "
                f"(n={len(yuksek)}/{len(alt)}). Çok yüksek değer 'daha güçlü' yerine "
                f"hareketin olgunlaştığı/geç kalındığı bölgeyi temsil ediyor olabilir."
            ),
            "kod": (
                "Sert veto yapma. Önce bu bölgeye doygunluk/geç-kalma eksi puanı veya tavan puanı dene; "
                "sonucu farklı gün ve rejimlerde tekrar doğrula."
            ),
            "guven": guven,
        })
    return cikti


def _gelistirme_onerileri_uret(kayitlar):
    """+%5 sonucunu hem mevcut kod kurallarıyla hem piyasa rejimiyle birlikte yorumlar."""
    if len(kayitlar) < GELISTIRME_MIN_KAYIT:
        return []
    oneriler=[]
    sayisal=[
        ("genel_guc","Genel Güç"),("skor_kalite","Genel Güç / Skor bloğu"),("momentum_kalite","Genel Güç / Momentum bloğu"),
        ("piyasa_kalite","Genel Güç / Piyasa bloğu"),("neden_kalite","Genel Güç / Neden bloğu"),
        ("neden_sayisi","Neden sayısı"),("onemli_neden_sayisi","Önemli neden sayısı"),
        ("neden_agirlikli_toplam","Ağırlıklı neden puanı"),
        ("genel_devam_bilesen","Genel Güç / Devam bileşeni"),
        ("genel_rel_bilesen","Genel Güç / Göreceli güç bileşeni"),
        ("genel_kalicilik_bant","Genel Güç / Kalıcılık bant bileşeni"),
        ("genel_hareket_bilesen","Genel Güç / Hareket teyidi bileşeni"),
        ("genel_adx_bilesen","Genel Güç / ADX bileşeni"),
        ("erken_yakalama_puani","Erken Yakalama puanı"),
        ("al_odak_puani","Devam Gücü / Ana odak puanı"),
        ("btc_sok_puani","BTC Şok / Piyasa baskı puanı"),
        ("piyasa_devam_ceza","Piyasa Devamı / Teyitsizlik cezası"),
        ("piyasa_geri_verme","Piyasa geri verme"),
        ("piyasa_pozitif_oran","Piyasa devam pozitif oranı"),
        ("devam","Devam Gücü"),("kalicilik","Kalıcılık"),("giris_skoru","Giriş skoru"),("erken","Erken skor"),
        ("radar","Radar skoru"),("hacim","Hacim çarpanı"),("d1","1dk momentum"),("d3","3dk momentum"),
        ("d5","5dk momentum"),("d10","10dk momentum"),("vr310","3dk hacim / 10dk ort"),
        ("coin_btc_60","Coin-BTC 60dk göreceli güç"),("coin_piyasa_60","Coin-Piyasa 60dk göreceli güç"),
        ("rsi","RSI"),("adx","ADX"),("btc_3s","BTC 3s"),("piyasa_medyan_3s","Piyasa 3s"),
    ]
    bayraklar=[
        ("momentum hızlanıyor","Momentum hızlanıyor"),("hacim hızlanıyor","Hacim hızlanıyor"),
        ("btc farkı açılıyor","BTC farkı açılıyor"),("lider güçleniyor","Lider güçleniyor"),("stair5","Basamaklı trend"),
    ]

    # 1) Tüm piyasa boyunca genel kod etkisi.
    for alan,ad in sayisal:
        etki=_sayisal_etki(kayitlar,alan)
        if not etki:
            continue
        esik,ru,ra,fark,nu,na=etki
        if abs(fark) < 12.0:
            continue
        aktif,kod_aciklama=_kod_durumu(ad)
        gun,tg,rej,tr = _yon_tekrari_sayisal(kayitlar, alan, fark)
        guven = _guven_hesapla(fark, len(kayitlar), gun, tg, rej, tr)
        eylem = _eylem_stabilize(_eylem_sec(ad,fark), fark, guven)
        uyeler = [
            _kayit_kimligi(x) for x in kayitlar
            if x.get(alan) is not None and float(x.get(alan)) >= esik
        ]
        oneriler.append({
            "puan":abs(fark),"eylem":eylem,"ozellik":ad,"rejim":"TÜM PİYASA",
            "aciklama":f"{ad} >= {esik:.2f} grubunda +%5 başarı %{ru:.1f}; altında %{ra:.1f} (n={nu}/{na}).",
            "kod":kod_aciklama,"guven":guven,
            "alan":alan,"fark":fark,"esik":esik,"ust_oran":ru,"alt_oran":ra,
            "n_ust":nu,"n_alt":na,"uyeler":uyeler,
        })

    for anahtar,ad in bayraklar:
        etki=_bayrak_etki(kayitlar,anahtar)
        if not etki:
            continue
        rv,ry,fark,nv,ny=etki
        if abs(fark) < 12.0:
            continue
        _,kod_aciklama=_kod_durumu(ad)
        gun,tg,rej,tr = _yon_tekrari_bayrak(kayitlar, anahtar, fark)
        guven = _guven_hesapla(fark, len(kayitlar), gun, tg, rej, tr)
        eylem = _eylem_stabilize(_eylem_sec(ad,fark), fark, guven)
        oneriler.append({
            "puan":abs(fark),"eylem":eylem,"ozellik":ad,"rejim":"TÜM PİYASA",
            "aciklama":f"{ad} varken +%5 başarı %{rv:.1f}; yokken %{ry:.1f} (n={nv}/{ny}).",
            "kod":kod_aciklama,"guven":guven
        })

    # 2) Aynı özellik piyasa rejimine göre gerçekten değişiyor mu?
    # Böylece güçlü/yatay/zayıf piyasa için ayrı kod önerisi üretilebilir.
    for rejim in ("Güçlü","Yatay","Zayıf"):
        grup=[x for x in kayitlar if x.get("piyasa_rejim") == rejim]
        if len(grup) < max(GELISTIRME_MIN_KAYIT, GELISTIRME_MIN_GRUP*2):
            continue
        for alan,ad in sayisal:
            etki=_sayisal_etki(grup,alan)
            if not etki:
                continue
            esik,ru,ra,fark,nu,na=etki
            if abs(fark) < 15.0:
                continue
            _,kod_aciklama=_kod_durumu(ad)
            oneriler.append({
                "puan":abs(fark)+4,"eylem":_eylem_sec(ad,fark,rejim),"ozellik":ad,"rejim":rejim.upper(),
                "aciklama":f"{rejim} piyasada {ad} >= {esik:.2f}: +%5 başarı %{ru:.1f}; altında %{ra:.1f} (n={nu}/{na}). Bu değişikliği yalnız {rejim.lower()} rejimde uygula.",
                "kod":kod_aciklama,"guven":_guven_hesapla(fark,len(grup),0,0,1,1)
            })
        for anahtar,ad in bayraklar:
            etki=_bayrak_etki(grup,anahtar)
            if not etki:
                continue
            rv,ry,fark,nv,ny=etki
            if abs(fark) < 15.0:
                continue
            _,kod_aciklama=_kod_durumu(ad)
            oneriler.append({
                "puan":abs(fark)+4,"eylem":_eylem_sec(ad,fark,rejim),"ozellik":ad,"rejim":rejim.upper(),
                "aciklama":f"{rejim} piyasada {ad} varken +%5 başarı %{rv:.1f}; yokken %{ry:.1f} (n={nv}/{ny}). Bu değişikliği yalnız {rejim.lower()} rejimde uygula.",
                "kod":kod_aciklama,"guven":_guven_hesapla(fark,len(grup),0,0,1,1)
            })

    # 3) Rejimin kendisi büyük fark yaratıyorsa kodda rejim ağırlığı öner.
    rejimler={r:[x for x in kayitlar if x.get("piyasa_rejim")==r] for r in ("Güçlü","Yatay","Zayıf")}
    yeterli={r:g for r,g in rejimler.items() if len(g) >= GELISTIRME_MIN_GRUP}
    if len(yeterli) >= 2:
        oranlar={r:_basari_orani(g) for r,g in yeterli.items()}
        en_iyi=max(oranlar,key=oranlar.get); en_kotu=min(oranlar,key=oranlar.get)
        fark=oranlar[en_iyi]-oranlar[en_kotu]
        if fark >= 12:
            oneriler.append({
                "puan":fark+6,"eylem":"REJİME GÖRE KODU AYIR","ozellik":"Piyasa rejimi","rejim":"ORTAK",
                "aciklama":f"{en_iyi} piyasada +%5 başarı %{oranlar[en_iyi]:.1f}, {en_kotu} piyasada %{oranlar[en_kotu]:.1f}. Aynı AL eşiğini her rejimde kullanma; önce bonus/eksi puan olarak dene.",
                "kod":"Mevcut dosyada piyasa desteği mesajlanıyor; ana H AL kapısına doğrudan rejim ağırlığı bağlı değil.",
                "guven":_guven_hesapla(fark,len(kayitlar),0,0,len(yeterli),len(yeterli))
            })

    # 4) Yüksek görünen ama +%5 yapmayan sinyallerde puan şişmesi/korelasyon analizi.
    # Aynı yükselişi birden fazla gösterge tekrar ödüllüyorsa "grup/tavan puanı" önerisi üretir.
    oneriler.extend(_puan_sismesi_onerileri(kayitlar))

    # 5) Aşırı yüksek skorların "daha güçlü" değil, geç/doygun hareket işareti olduğu paradoksları ara.
    oneriler.extend(_asiri_yuksek_paradoks_onerileri(kayitlar))

    # Aynı coin kümesini seçen Genel/Devam/Ana odak ölçümlerini beş ayrı
    # keşif gibi yazma; tek birleşik kalite önerisine indir.
    oneriler = _onerilerde_ayni_grubu_birlestir(oneriler)

    # Güven ve tekrar sayısını öncelik puanına da yansıt.
    for o in oneriler:
        g = o.get("guven") or {}
        seviye = g.get("seviye", "DÜŞÜK") if isinstance(g, dict) else "DÜŞÜK"
        bonus = {"DÜŞÜK": 0, "ORTA": 4, "YÜKSEK": 9, "ÇOK YÜKSEK": 14}.get(seviye, 0)
        tekrar_bonus = 2 * int(g.get("ayni_gun", 0) or 0) + 3 * int(g.get("ayni_rejim", 0) or 0) if isinstance(g, dict) else 0
        o["puan"] = float(o.get("puan", 0) or 0) + bonus + min(10, tekrar_bonus)

    # En güçlü, tekrarsız 5 geliştirme önerisini seç.
    oneriler.sort(key=lambda x:(x.get("puan",0), {"DÜŞÜK":0,"ORTA":1,"YÜKSEK":2,"ÇOK YÜKSEK":3}.get((x.get("guven") or {}).get("seviye","DÜŞÜK") if isinstance(x.get("guven"),dict) else "DÜŞÜK",0)),reverse=True)
    secilen=[]; gorulen=set()
    for o in oneriler:
        anahtar=(o.get("ozellik"),o.get("rejim"))
        if anahtar in gorulen:
            continue
        gorulen.add(anahtar); secilen.append(o)
        if len(secilen)>=5:
            break
    return secilen


def _mesaj_gelistirme_onerileri(kayitlar, kod_onerileri):
    """
    Haftalık veriye göre Telegram mesajının hangi alanlarının öne çıkarılması,
    geri plana alınması veya birleştirilmesi gerektiğini önerir.
    Mesaj formatını otomatik değiştirmez; yalnız öneri üretir.
    """
    if len(kayitlar) < GELISTIRME_MIN_KAYIT:
        return []

    gorunen = {
        "Genel Güç", "Devam Gücü", "Kalıcılık", "Giriş skoru", "Erken skor",
        "Radar skoru", "Hacim çarpanı", "1dk momentum", "3dk momentum",
        "5dk momentum", "10dk momentum", "BTC 3s", "Piyasa 3s", "Neden sayısı",
        "Genel Güç / Skor bloğu", "Genel Güç / Momentum bloğu",
        "Genel Güç / Piyasa bloğu", "Genel Güç / Neden bloğu",
    }

    # Kod önerilerinden mesaj tarafına anlamlı olanları dönüştür.
    adaylar = []
    for o in kod_onerileri:
        ad = o.get("ozellik", "")
        if not ad:
            continue
        g = o.get("guven") or {}
        seviye = g.get("seviye", "DÜŞÜK") if isinstance(g, dict) else "DÜŞÜK"
        eylem = str(o.get("eylem", ""))
        puan = float(o.get("puan", 0) or 0)

        # Mesajda zaten görünen ve pozitif ayıran verileri öne çıkar.
        pozitif = not any(k in eylem for k in ("AZALT", "ÇIKAR", "NEGATİF", "KAÇINMA"))
        if ad in gorunen and pozitif and seviye in ("ORTA", "YÜKSEK", "ÇOK YÜKSEK"):
            adaylar.append({
                "puan": puan + 8,
                "eylem": "MESAJDA ÖNE ÇIKAR",
                "ozellik": ad,
                "neden": f"+%5 yapanlarla yapmayanları ayırmada anlamlı görünüyor; güven {seviye}.",
                "onerilen": "Mesajın üst bölümünde veya ilk bakışta görülen alanda tut."
            })

        # Negatif/yararsız görünen ama mesajda yer kaplayan alanı ikinci plana al.
        if ad in gorunen and not pozitif:
            if seviye in ("YÜKSEK", "ÇOK YÜKSEK"):
                etiket = "MESAJDAN KALDIR ADAYI"
                onerilen = "Ana mesajdan çıkarıp yalnız detay/öğrenme verisinde tutmayı test et."
            else:
                etiket = "MESAJDA İKİNCİ PLANA AL"
                onerilen = "Şimdilik kaldırma; alt satıra veya daha az görünür alana taşı."
            adaylar.append({
                "puan": puan + 5,
                "eylem": etiket,
                "ozellik": ad,
                "neden": f"Yüksek görünmesi +%5 başarısını artırmıyor veya ters ilişki gösteriyor; güven {seviye}.",
                "onerilen": onerilen
            })

    # Teknik trend göstergeleri birbirini çok tekrar ediyorsa tek mesaj özetine dönüştürme önerisi.
    teknik_alanlar = [("rsi","RSI"), ("adx","ADX")]
    mevcut = []
    for alan, ad in teknik_alanlar:
        e = _sayisal_etki(kayitlar, alan)
        if e:
            mevcut.append((alan, ad, e))

    # EMA/MACD neden bloğunda zaten görüldüğü için trend özetini ayrıca önerebiliriz.
    if len(mevcut) >= 2:
        adaylar.append({
            "puan": 18,
            "eylem": "MESAJDA BİRLEŞTİR",
            "ozellik": "Trend teknikleri",
            "neden": "RSI / ADX ile EMA-MACD aynı trend gücünü kısmen tekrar ediyor; mesaj kalabalığını azaltabilir.",
            "onerilen": "Tek tek tekrar etmek yerine gerektiğinde 'Trend Gücü: Güçlü / Orta / Zayıf' özeti göster; ham değerleri öğrenmede tut."
        })

    # Genel Güç yüksekken sonuçlar kötüleşiyorsa, mesajda tek başına karar işareti gibi görünmemesini öner.
    e = _sayisal_etki(kayitlar, "genel_guc")
    if e:
        esik, ru, ra, fark, nu, na = e
        if fark <= -12:
            adaylar.append({
                "puan": abs(fark) + 20,
                "eylem": "MESAJDA UYARIYLA GÖSTER",
                "ozellik": "Genel Güç",
                "neden": f"Genel Güç >= {esik:.0f} grubunda +%5 başarı %{ru:.1f}, altında %{ra:.1f}; tek başına kalite etiketi gibi okunmamalı.",
                "onerilen": "Genel Güç kalsın ama karar verdiren ana işaret gibi büyütme; geliştirme motoru yeniden kalibre edene kadar destek metriği olarak göster."
            })

    # Tekrarsız en fazla 4 mesaj önerisi.
    adaylar.sort(key=lambda x: x.get("puan", 0), reverse=True)
    sonuc = []
    gorulen = set()
    for x in adaylar:
        k = (x.get("eylem"), x.get("ozellik"))
        if k in gorulen:
            continue
        gorulen.add(k)
        sonuc.append(x)
        if len(sonuc) >= 4:
            break
    return sonuc


def gelistirme_oneri_raporu_gerekirse_gonder():
    global SON_GELISTIRME_RAPOR_ZAMANI
    simdi = time.time()
    if SON_GELISTIRME_RAPOR_ZAMANI and simdi - SON_GELISTIRME_RAPOR_ZAMANI < GELISTIRME_RAPOR_ARALIGI:
        return
    son7_tumu = [
        x for x in AL_OGRENME_KAYITLARI
        if x.get("tamamlandi")
        and str(x.get("kayit_tipi", "telegram")) == "telegram"
        and float(x.get("tamamlanma_zamani", 0) or 0) > 0
        and simdi - float(x.get("tamamlanma_zamani", 0) or 0) <= GELISTIRME_PENCERE
    ]

    # Eski veriyi silme; ama yeterli V7 örneği birikince haftalık öneriyi
    # yalnız mevcut strateji sürümünden üret. Böylece kod değişikliği raporu bozmaz.
    son7_mevcut = [x for x in son7_tumu if x.get("strateji_surumu") == STRATEJI_SURUMU]
    son7 = son7_mevcut if len(son7_mevcut) >= GELISTIRME_MIN_KAYIT else son7_tumu

    if len(son7) < GELISTIRME_MIN_KAYIT:
        return
    oneriler = _gelistirme_onerileri_uret(son7)
    mesaj_onerileri = _mesaj_gelistirme_onerileri(son7, oneriler)
    devam_kalite_mesaj = "\n".join(_devam_kalitesi_golge_raporu(son7))
    if not oneriler:
        satirlar = [
            "🧠 ASSISTANT HAFTALIK KOD + PİYASA GELİŞTİRME ÖNERİSİ",
            "",
            "Bu hafta +%5 yapanlarla yapmayanlar arasında kodu değiştirecek kadar güçlü ve tekrarlı bir fark oluşmadı.",
            "🟰 KOD ÖNERİSİ: Mevcut kurallara dokunma; veri toplamaya devam et.",
        ]
        if mesaj_onerileri:
            satirlar.extend(["", "💬 MESAJ GELİŞTİRME ÖNERİSİ", ""])
            for i, m in enumerate(mesaj_onerileri, 1):
                satirlar.append(f"{i}) {m['eylem']}: {m['ozellik']}")
                satirlar.append(f"   Neden: {m['neden']}")
                satirlar.append(f"   Öneri: {m['onerilen']}")
        mesaj = "\n".join(satirlar)
    else:
        satirlar = ["🧠 ASSISTANT HAFTALIK KOD + PİYASA GELİŞTİRME ÖNERİSİ", ""]
        for i, o in enumerate(oneriler, 1):
            g = o.get("guven") or {}
            seviye = g.get("seviye", "DÜŞÜK") if isinstance(g, dict) else str(g)
            tekrar = ""
            if isinstance(g, dict):
                tekrar = f" | n={g.get('n',0)} | aynı yön gün {g.get('ayni_gun',0)}/{g.get('toplam_gun',0)} | rejim {g.get('ayni_rejim',0)}/{g.get('toplam_rejim',0)}"
            satirlar.append(f"Öncelik {i}) {o['eylem']}: {o['ozellik']} [{o.get('rejim','TÜM PİYASA')}]")
            satirlar.append(f"   Veri: {o['aciklama']}")
            satirlar.append(f"   Dosyada: {o.get('kod','-')}")
            satirlar.append(f"   Güven: {seviye}{tekrar}")
        if mesaj_onerileri:
            satirlar.append("")
            satirlar.append("💬 MESAJ GELİŞTİRME ÖNERİSİ")
            satirlar.append("")
            for i, m in enumerate(mesaj_onerileri, 1):
                satirlar.append(f"{i}) {m['eylem']}: {m['ozellik']}")
                satirlar.append(f"   Neden: {m['neden']}")
                satirlar.append(f"   Öneri: {m['onerilen']}")
        satirlar.append("")
        satirlar.append("Not: Motor mevcut Assistant kuralını + piyasa rejimini + +%5 sonuçlarını birlikte değerlendirir; küçük örneklemde agresif 'çıkar' demez, aynı yönü gün/rejim bazında tekrar test eder, yüksek puanlı başarısız sinyallerde korelasyon/puan şişmesi ve geç/doygun hareket paradoksunu arar. Ayrıca Telegram mesajında hangi verinin öne çıkarılması, geri plana alınması veya birleştirilmesi gerektiğini önerir. Kodu ve mesaj formatını otomatik değiştirmez.")
        mesaj = "\n".join(satirlar)
    print(mesaj)
    telegram_gonder(mesaj)
    # Ana haftalık mesaj Telegram sınırını aşmasın; birleşik gölge testi hemen
    # arkasından ayrı fakat aynı haftalık raporun parçası olarak gönderilir.
    print(devam_kalite_mesaj)
    telegram_gonder(devam_kalite_mesaj)
    SON_GELISTIRME_RAPOR_ZAMANI = simdi
    _gelistirme_son_zaman_kaydet(simdi)


AL_OGRENME_KAYITLARI = _al_ogrenme_yukle()
TOP10_GOLGE_KAYITLARI = _top10_golge_yukle()
GIRIS_ZAMANI_DENEY_KAYITLARI = _giris_deneyi_yukle()
AL_TAKIP.update(_al_takip_yukle())
_al_takip_ogrenmeden_tamamla()


STABLE_COINLER = [
    "USDT", "USDC", "FDUSD", "TUSD", "DAI", "USDP"
]




RSS_KAYNAKLARI = [
    "https://cointelegraph.com/rss",
    "https://www.coindesk.com/arc/outboundfeeds/rss/?outputType=xml"
]

POZITIF = [
    "listing", "listed", "binance", "coinbase", "partnership",
    "etf", "airdrop", "burn", "launch", "mainnet", "upgrade",
    "integration", "support", "investment", "funding", "approval",
    "adoption", "bullish", "surge", "rally"
]

NEGATIF = [
    "hack", "exploit", "lawsuit", "delist", "sec", "attack",
    "scam", "fraud", "investigation", "outage", "halted",
    "stopped", "shutdown", "pressure", "bearish", "loss",
    "dump", "decline", "crash", "selloff", "down", "weakness"
]



def kalin_coin_yazisi(metin):
    """Telegram parse_mode kullanmadan coin adını Unicode kalın gösterir."""
    normal = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    bold = "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"
    tablo = str.maketrans(normal, bold)
    return str(metin).upper().translate(tablo)

def telegram_gonder(mesaj, parse_mode=None):
    if not BOT_TOKEN:
        print("BOT_TOKEN bulunamadı. Railway Variables kontrol et.")
        return False

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    basarili = False
    tumu_basarili = True

    for chat_id in CHAT_IDS:
        try:
            params = {"chat_id": chat_id, "text": mesaj}
            if parse_mode:
                params["parse_mode"] = parse_mode
            r = requests.get(
                url,
                params=params,
                timeout=10
            )
            print(chat_id, r.text)
            r.raise_for_status()
            cevap = r.json()
            if not cevap.get("ok"):
                raise RuntimeError(cevap.get("description", "Telegram gönderimi başarısız"))
            basarili = True
        except Exception as e:
            tumu_basarili = False
            print(chat_id, e)
    return basarili and tumu_basarili


def veri_getir(symbol, saat=24):
    simdi = int(time.time())
    url = (
        f"https://graph-api.btcturk.com/v1/klines/history?"
        f"symbol={symbol}&resolution=60&from={simdi - (saat * 3600)}&to={simdi}"
    )
    return requests.get(url, timeout=10).json()



def btc_degisimleri():
    """
    V4.25 BTC Gücü V2 için BTC'nin 1s, 3s ve 24s değişimini hesaplar.
    """
    try:
        d = veri_getir("BTCTRY", 24)
        c = d["c"]

        if len(c) < 24:
            return {"1s": 0, "3s": 0, "24s": 0}

        return {
            "1s": ((c[-1] - c[-2]) / c[-2]) * 100,
            "3s": ((c[-1] - c[-4]) / c[-4]) * 100,
            "24s": ((c[-1] - c[-24]) / c[-24]) * 100
        }
    except Exception:
        return {"1s": 0, "3s": 0, "24s": 0}


def btc_gucu_v2_hesapla(degisim1, degisim3, degisim24, btc_d):
    """
    V4.25 BTC Gücü V2.
    Sadece BTC'den güçlü mü sorusuna bakmaz; 1s, 3s ve 24s farkını 0-10 puana çevirir.
    """
    fark1 = degisim1 - btc_d.get("1s", 0)
    fark3 = degisim3 - btc_d.get("3s", 0)
    fark24 = degisim24 - btc_d.get("24s", 0)

    puan = 0

    if fark1 >= 0.5:
        puan += 2
    elif fark1 >= 0:
        puan += 1

    if fark3 >= 3:
        puan += 4
    elif fark3 >= 1.5:
        puan += 3
    elif fark3 >= 0.5:
        puan += 2

    if fark24 >= 5:
        puan += 4
    elif fark24 >= 3:
        puan += 3
    elif fark24 >= 1:
        puan += 2

    return min(puan, 10), fark1, fark3, fark24


def lider_skoru_hesapla(hacim_kat, degisim1, degisim3, degisim24, btc_fark1, btc_fark3, btc_fark24, zirve_yakin, yeni_zirve):
    """
    V4.25 Lider Skoru.
    Coinin sadece hareket edip etmediğini değil, piyasanın liderlerinden biri olup olmadığını ölçer.
    """
    puan = 0

    if btc_fark24 >= 5:
        puan += 3
    elif btc_fark24 >= 2:
        puan += 2

    if btc_fark3 >= 2:
        puan += 2
    elif btc_fark3 >= 1:
        puan += 1

    if degisim24 >= 6:
        puan += 2
    elif degisim24 >= 3:
        puan += 1

    if hacim_kat >= 10 and degisim1 >= 0 and degisim3 > 0:
        puan += 2
    elif hacim_kat >= 5 and degisim3 > 0:
        puan += 1

    if yeni_zirve:
        puan += 1
    elif zirve_yakin:
        puan += 0.5

    return min(puan, 10)





def guc_skoru_hesapla(
    hacim_kat,
    degisim1,
    degisim3,
    degisim24,
    btc_guc_skoru,
    lider_skoru,
    haber_skoru,
    satis_baskisi,
    btc_fark3=0,
    zirve_yakin=False,
    yeni_zirve=False
):
    """
    Son çalışan Coin Radar eşiklerine uyarlanmış 0-100 aday skoru.
    Momentum daha ağır, yüksek hacim ise momentum/liderlik teyidi olmadan tek başına ödüllendirilmez.
    """
    hacim_puan = min(hacim_kat / 10, 1) * 18
    momentum_puan = min(max(degisim3, 0) / 6, 1) * 34
    btc_puan = (btc_guc_skoru / 10) * 20
    lider_puan = (lider_skoru / 10) * 15
    haber_puan = (min(haber_skoru, 20) / 20) * 10

    toplam = hacim_puan + momentum_puan + btc_puan + lider_puan + haber_puan

    # Son Coin Radar: 3s momentum ana ayırıcı.
    if degisim3 >= 6:
        toplam += 6
    elif degisim3 >= 4:
        toplam += 3
    elif degisim3 >= 2:
        toplam += 1

    # Çok yüksek hacim tek başına güçlü aday sayılmaz.
    if hacim_kat >= 15 and degisim3 >= 6:
        toplam += 2
    elif hacim_kat >= 10 and degisim3 >= 4:
        toplam += 1
    elif hacim_kat >= 10 and degisim3 < 4 and lider_skoru < 7:
        toplam -= 4

    if btc_fark3 >= 4:
        toplam += 2
    elif btc_fark3 >= 2:
        toplam += 1

    if lider_skoru >= 7:
        toplam += 2
    elif lider_skoru >= 5:
        toplam += 1

    if zirve_yakin or yeni_zirve:
        toplam += 1

    if satis_baskisi:
        toplam -= 12

    return round(max(min(toplam, 100), 0), 2)


def stable_coin_mi(symbol):
    coin = symbol.replace("TRY", "")
    return coin in STABLE_COINLER


def haber_puani(symbol):
    coin = symbol.replace("TRY", "").lower()
    puan = 0
    negatif_haber = False

    for kaynak in RSS_KAYNAKLARI:
        try:
            feed = feedparser.parse(kaynak)

            for item in feed.entries[:25]:
                baslik = item.title.lower()

                if coin in baslik:
                    puan += 8

                    for kelime in POZITIF:
                        if kelime in baslik:
                            puan += 5

                    for kelime in NEGATIF:
                        if kelime in baslik:
                            puan -= 15
                            negatif_haber = True
        except:
            pass

    puan = max(min(puan, 20), 0)

    if negatif_haber and puan < 10:
        puan = 0

    return puan



# ==========================================
# H MANTIĞI - TEKNİK ANALİZ KATMANI
# Commit: AI AL V3.2 - Roket RSI ust siniri 75
# Bu katman aday seçimini değiştirmez; Top 10 adayı analiz için zenginleştirir.
# ==========================================

def ema_hesapla(veriler, periyot):
    if len(veriler) < periyot:
        return None
    ema = sum(veriler[:periyot]) / periyot
    k = 2 / (periyot + 1)
    for fiyat in veriler[periyot:]:
        ema = fiyat * k + ema * (1 - k)
    return ema


def ema_serisi(veriler, periyot):
    if len(veriler) < periyot:
        return []
    sonuc = [None] * (periyot - 1)
    ema = sum(veriler[:periyot]) / periyot
    sonuc.append(ema)
    k = 2 / (periyot + 1)
    for fiyat in veriler[periyot:]:
        ema = fiyat * k + ema * (1 - k)
        sonuc.append(ema)
    return sonuc


def rsi_hesapla(kapanislar, periyot=14):
    if len(kapanislar) < periyot + 1:
        return None
    farklar = [kapanislar[i] - kapanislar[i - 1] for i in range(1, len(kapanislar))]
    kazanclar = [max(x, 0) for x in farklar]
    kayiplar = [max(-x, 0) for x in farklar]
    ort_kazanc = sum(kazanclar[:periyot]) / periyot
    ort_kayip = sum(kayiplar[:periyot]) / periyot
    for i in range(periyot, len(farklar)):
        ort_kazanc = ((ort_kazanc * (periyot - 1)) + kazanclar[i]) / periyot
        ort_kayip = ((ort_kayip * (periyot - 1)) + kayiplar[i]) / periyot
    if ort_kayip == 0:
        return 100.0
    rs = ort_kazanc / ort_kayip
    return 100 - (100 / (1 + rs))


def macd_hesapla(kapanislar):
    ema12 = ema_serisi(kapanislar, 12)
    ema26 = ema_serisi(kapanislar, 26)
    if not ema12 or not ema26:
        return None, None, None
    macd_seri = []
    for i in range(len(kapanislar)):
        if i < len(ema12) and i < len(ema26) and ema12[i] is not None and ema26[i] is not None:
            macd_seri.append(ema12[i] - ema26[i])
    if len(macd_seri) < 9:
        return None, None, None
    sinyal = ema_hesapla(macd_seri, 9)
    macd = macd_seri[-1]
    histogram = macd - sinyal if sinyal is not None else None
    return macd, sinyal, histogram


def atr_adx_hesapla(yuksekler, dusukler, kapanislar, periyot=14):
    if len(kapanislar) < (periyot * 2) + 1:
        return None, None
    tr, arti_dm, eksi_dm = [], [], []
    for i in range(1, len(kapanislar)):
        yukari = yuksekler[i] - yuksekler[i - 1]
        asagi = dusukler[i - 1] - dusukler[i]
        arti_dm.append(yukari if yukari > asagi and yukari > 0 else 0)
        eksi_dm.append(asagi if asagi > yukari and asagi > 0 else 0)
        tr.append(max(
            yuksekler[i] - dusukler[i],
            abs(yuksekler[i] - kapanislar[i - 1]),
            abs(dusukler[i] - kapanislar[i - 1])
        ))

    atr = sum(tr[:periyot]) / periyot
    arti_s = sum(arti_dm[:periyot])
    eksi_s = sum(eksi_dm[:periyot])
    dxler = []

    for i in range(periyot, len(tr)):
        atr = ((atr * (periyot - 1)) + tr[i]) / periyot
        arti_s = arti_s - (arti_s / periyot) + arti_dm[i]
        eksi_s = eksi_s - (eksi_s / periyot) + eksi_dm[i]
        arti_di = 100 * (arti_s / (atr * periyot)) if atr else 0
        eksi_di = 100 * (eksi_s / (atr * periyot)) if atr else 0
        toplam = arti_di + eksi_di
        dxler.append(100 * abs(arti_di - eksi_di) / toplam if toplam else 0)

    if len(dxler) < periyot:
        return atr, None
    adx = sum(dxler[:periyot]) / periyot
    for dx in dxler[periyot:]:
        adx = ((adx * (periyot - 1)) + dx) / periyot
    return atr, adx


def teknik_analiz_hesapla(symbol):
    try:
        d = veri_getir(symbol, 120)
        c = d.get("c", [])
        h = d.get("h", [])
        l = d.get("l", [])
        if len(c) < 55 or len(h) != len(c) or len(l) != len(c):
            return None

        ema20 = ema_hesapla(c, 20)
        ema50 = ema_hesapla(c, 50)
        rsi = rsi_hesapla(c, 14)
        macd, macd_sinyal, macd_hist = macd_hesapla(c)
        atr, adx = atr_adx_hesapla(h, l, c, 14)
        fiyat = c[-1]
        atr_yuzde = (atr / fiyat) * 100 if atr is not None and fiyat else None

        return {
            "ema20": round(ema20, 6) if ema20 is not None else None,
            "ema50": round(ema50, 6) if ema50 is not None else None,
            "rsi": round(rsi, 2) if rsi is not None else None,
            "macd": round(macd, 6) if macd is not None else None,
            "macd_sinyal": round(macd_sinyal, 6) if macd_sinyal is not None else None,
            "macd_hist": round(macd_hist, 6) if macd_hist is not None else None,
            "adx": round(adx, 2) if adx is not None else None,
            "atr": round(atr, 6) if atr is not None else None,
            "atr_yuzde": round(atr_yuzde, 2) if atr_yuzde is not None else None
        }
    except Exception as e:
        print(f"Teknik analiz hata ({symbol}):", e)
        return None


# ==========================================
# H MANTIĞI - KARAR MOTORU
# Radar ilk adayları bulur; bu katman teknik yapıyı AL / BEKLE / SAT-PAS kararına çevirir.
# ==========================================

def h_karar_hesapla(aday):
    """
    AI karar motoru V3 - bağımsız AL teyidi.
    Amaç: Coin Radar adayını otomatik onaylamak yerine bağımsız teknik AL teyidi vermek.
    AVNT/ENA gibi zayıf devam teyitlerinde AL'ı zorlaştırır;
    NAP/MIRA gibi güçlü trendleri ve H gibi istisnai Yıldız devamlarını korur.
    """
    teknik = aday.get("teknik")
    if not teknik:
        return {
            "ai_skoru": 0,
            "karar": "🟡 BEKLE",
            "risk": "Bilinmiyor",
            "nedenler": ["Teknik veri yetersiz"]
        }

    ema20 = teknik.get("ema20")
    ema50 = teknik.get("ema50")
    rsi = teknik.get("rsi")
    macd_hist = teknik.get("macd_hist")
    adx = teknik.get("adx")
    atr_yuzde = teknik.get("atr_yuzde")

    fiyat = aday.get("fiyat", 0)
    radar = aday.get("radar_skoru", 0)
    kategori = aday.get("radar_kategori", "")
    lider = aday.get("lider_skoru", 0)
    deg1 = aday.get("degisim1", 0)
    deg3 = aday.get("degisim3", 0)
    deg24 = aday.get("degisim24", 0)

    skor = 20.0
    nedenler = []

    # 1) Radar kalitesi: artık taban skoru şişirmiyor.
    skor += max(0, min((radar - 55) * 0.50, 20))

    # Radar alarm seviyesine küçük kalite bonusu.
    if "Yıldız" in kategori:
        skor += 10
        nedenler.append("Radar Yıldız")
    elif "Elit" in kategori:
        skor += 6
    elif "Trader" in kategori:
        skor += 4
    elif "Roket" in kategori:
        skor += 2

    # 2) EMA: önemli ama tek başına veto değil.
    if ema20 is not None and ema50 is not None:
        if ema20 > ema50:
            skor += 12
            nedenler.append("EMA trendi yukarı")
        else:
            skor -= 8
            nedenler.append("EMA trendi aşağı")

        if fiyat and ema20:
            if fiyat > ema20:
                skor += 4
            else:
                skor -= 5

    # 3) RSI: 50-65 en temiz giriş bölgesi.
    if rsi is not None:
        if 50 <= rsi <= 65:
            skor += 12
            nedenler.append("RSI sağlıklı güçlü bölgede")
        elif 45 <= rsi < 50:
            skor += 5
        elif 65 < rsi <= 72:
            skor += 6
            nedenler.append("RSI güçlü ama ısınıyor")
        elif 72 < rsi <= 78:
            skor += 1
            nedenler.append("RSI yüksek")
        elif 78 < rsi <= 85:
            skor -= 7
            nedenler.append("RSI aşırı alıma yakın")
        elif rsi > 85:
            skor -= 12
            nedenler.append("RSI aşırı alım")
        elif rsi < 40:
            skor -= 10
            nedenler.append("RSI zayıf")

    # 4) MACD: devam teyidi.
    macd_pozitif = macd_hist is not None and macd_hist > 0
    if macd_hist is not None:
        if macd_pozitif:
            skor += 12
            nedenler.append("MACD pozitif")
        else:
            skor -= 14
            nedenler.append("MACD negatif")

    # 5) ADX: AL kararının ana ayırıcılarından biri.
    if adx is not None:
        if adx >= 40:
            skor += 18
            nedenler.append("Trend çok güçlü")
        elif adx >= 30:
            skor += 14
            nedenler.append("Trend çok güçlü")
        elif adx >= 25:
            skor += 9
            nedenler.append("Trend güçlü")
        elif adx >= 20:
            skor += 3
            nedenler.append("Trend orta")
        else:
            skor -= 8
            nedenler.append("Trend gücü düşük")

    # 6) ATR: sağlıklı hareketi ödüllendir, aşırı oynaklığı azalt.
    if atr_yuzde is not None:
        if 1 <= atr_yuzde <= 4.5:
            skor += 5
        elif atr_yuzde > 7:
            skor -= 10
            nedenler.append("Volatilite çok yüksek")
        elif atr_yuzde > 5:
            skor -= 5
            nedenler.append("Volatilite yüksek")

    # 7) Göreceli güç ve liderlik.
    if aday.get("btcden_guclu"):
        skor += 4

    if lider >= 7:
        skor += 5
    elif lider >= 5:
        skor += 2

    # 8) Momentum kalitesi.
    # Çok yükselmiş olmak tek başına kötü değildir; devam gücü varsa H gibi hareketler korunur.
    if 1 <= deg1 <= 4:
        skor += 5
    elif 4 < deg1 <= 8:
        skor += 2
    elif deg1 > 8:
        skor -= 4

    if 3 <= deg3 <= 8:
        skor += 7
    elif 8 < deg3 <= 15:
        skor += 4
    elif deg3 > 15:
        skor += 1

    if deg24 > 30:
        skor -= 5

    # ADX düşükken 100/100 görünmesini engelle.
    if adx is not None:
        if adx < 20:
            skor = min(skor, 74)
        elif adx < 25:
            skor = min(skor, 82)
        elif adx < 30 and "Yıldız" not in kategori:
            skor = min(skor, 90)

    skor = round(max(0, min(skor, 100)), 1)

    # --------------------------------------------------
    # AL KAPISI V3
    # Radar adayı bulur; AI Assistant bağımsız teknik teyit ister.
    # Amaç: Radar'a düşen her coine otomatik AL dememek.
    # --------------------------------------------------
    ema_yukari = (
        ema20 is not None
        and ema50 is not None
        and ema20 > ema50
        and fiyat > ema20
    )

    rsi_temiz = rsi is not None and 48 <= rsi <= 75
    rsi_kabul = rsi is not None and 45 <= rsi <= 75

    # Normal Radar adayında artık daha sıkı teknik teyit:
    # EMA yukarı + sağlıklı RSI + güçlü ADX + pozitif MACD + yüksek AI skoru.
    normal_al = (
        not aday.get("erken_aday", False)
        and ema_yukari
        and rsi_temiz
        and macd_pozitif
        and adx is not None
        and adx >= 27
        and skor >= 80
    )

    # Çok güçlü Elit sinyalde RSI biraz daha geniş olabilir,
    # ama EMA ve trend teyidi yine zorunlu.
    elit_al = (
        "Elit" in kategori
        and radar >= 82
        and ema_yukari
        and rsi_kabul
        and macd_pozitif
        and adx is not None
        and adx >= 28
        and skor >= 85
    )

    # Yıldız istisnası:
    # H örneğinde olduğu gibi çok güçlü devam hareketlerinde EMA aşağı olsa bile
    # Radar + liderlik + ADX + MACD + momentum birlikte güçlü ise AL korunabilir.
    yildiz_istisna = (
        "Yıldız" in kategori
        and radar >= 90
        and lider >= 7
        and aday.get("btcden_guclu")
        and macd_pozitif
        and adx is not None
        and adx >= 28
        and rsi is not None
        and rsi >= 50
        and deg3 >= 8
        and skor >= 85
    )

    # Early Capture ayrı tutulur:
    # erken yakalamanın amacı daha düşük Radar skorunda teknik güçlenmeyi yakalamak.
    # Bu yüzden Radar yüksekliği değil, temiz teknik yapı aranır.
    erken_al = (
        aday.get("erken_aday", False)
        and ema_yukari
        and rsi is not None
        and 48 <= rsi <= 70
        and macd_pozitif
        and adx is not None
        and adx >= 30
        and skor >= 80
    )

    # Mikro Erken istisnası:
    # Dakikalık hareket henüz saatlik Radar skorunu tam oluşturmadan yakalanabilir.
    # ADX gecikmeli bir gösterge olduğu için eşik biraz daha düşük; buna karşılık
    # güçlü mikro skor + fiyat/hacim ivmesi birlikte zorunludur.
    mikro = aday.get("mikro") or {}
    mikro_erken_al = (
        aday.get("mikro_aday", False)
        and "Mikro Erken" in kategori
        and ema_yukari
        and rsi is not None
        and 47 <= rsi <= 72
        and macd_pozitif
        and adx is not None
        and adx >= 24
        and skor >= 76
        and float(mikro.get("skor", 0) or 0) >= 62
        and float(mikro.get("d1", 0) or 0) >= 0.15
        and float(mikro.get("d3", 0) or 0) >= 0.35
        and float(mikro.get("d5", 0) or 0) >= 0.45
        and not mikro.get("sisti", False)
        and (mikro.get("fiyat_ivme") or mikro.get("basamak"))
        and (mikro.get("hacim_ivmeleniyor") or float(mikro.get("hacim1x", 0) or 0) >= 1.40)
    )

    if normal_al or elit_al or yildiz_istisna or erken_al or mikro_erken_al:
        karar = "🟢 AL"
    elif skor >= 55:
        karar = "🟡 BEKLE"
    else:
        karar = "🔴 SAT / PAS"

    # Risk sadece bilgilendirme; Telegram yalnızca AL kararında konuşuyor.
    if atr_yuzde is None:
        risk = "Bilinmiyor"
    elif atr_yuzde <= 3:
        risk = "Düşük"
    elif atr_yuzde <= 5:
        risk = "Orta"
    else:
        risk = "Yüksek"

    if not nedenler:
        nedenler.append("Teknik göstergeler karışık")

    return {
        "ai_skoru": skor,
        "karar": karar,
        "risk": risk,
        "nedenler": nedenler[:4]
    }


def v11_canli_yumusak_filtre(aday):
    """BEAM/HOT tipini korur, parçalı ve sönük alt kaliteyi ayıklar.

    BEAM yolu iki 60dk göreceli farkın da çok güçlü olmasını; HOT yolu ise
    3/5dk pozitifken dört kısa vadenin en az üçünün pozitif olmasını arar.
    Bu iki yoldan biri varsa aday doğrudan korunur. İkisi de yoksa CVC/ilk ZRO
    gibi parçalı-sönen momentum veya eski birleşik zayıflık vetoya dönüşür.
    """
    mikro = aday.get("mikro") or {}
    ai = float(aday.get("ai_skoru", 0) or 0)
    devam = float(aday.get("devam_gucu", 0) or 0)
    coin_btc_60 = float(aday.get("coin_btc_60", 0) or 0)
    coin_piyasa_60 = float(aday.get("coin_piyasa_60", 0) or 0)
    ai_zayif = ai < V11_FILTRE_AI_ESIK
    devam_zayif = devam < V11_FILTRE_DEVAM_ESIK

    d1 = float(mikro.get("d1", 0) or 0)
    d3 = float(mikro.get("d3", 0) or 0)
    d5 = float(mikro.get("d5", 0) or 0)
    d10 = float(mikro.get("d10", 0) or 0)
    pozitif_sayisi = sum(1 for x in (d1, d3, d5, d10) if x > 0)

    asiri_rel_yolu = (
        coin_btc_60 >= V11_ASIRI_REL_ESIK
        and coin_piyasa_60 >= V11_ASIRI_REL_ESIK
    )
    temiz_momentum_yolu = (
        d3 > 0
        and d5 > 0
        and pozitif_sayisi >= V11_TEMIZ_MOM_MIN_POZITIF
    )
    rel_yok = not asiri_rel_yolu

    # CVC: 1/5dk negatif; ilk ZRO: 1/3dk sıfır-negatif. Bu iki yapı,
    # aşırı göreceli güçle korunmuyorsa kısa hareketin parçalı olduğunu söyler.
    parcalı_momentum = (
        (d1 <= 0 and d5 <= 0)
        or (d1 < 0 and d3 <= 0)
        or pozitif_sayisi <= 1
    )
    momentum_sonuyor = (
        (d1 < -0.15 and d3 <= 0.10)
        or (d3 <= 0.0 and d5 <= 0.0)
    )
    sisti = bool(mikro.get("sisti", False))
    yuksek_risk = str(aday.get("risk", "")).strip().lower() == "yüksek"
    hareket_teyitsiz = (
        int(aday.get("dinamik_teyit_sayisi", 0) or 0) == 0
        and not bool(aday.get("basamakli_trend"))
        and not bool(aday.get("momentum_hizlaniyor"))
        and not bool(aday.get("btc_farki_aciliyor"))
        and not bool(aday.get("lider_gucleniyor"))
    )
    ek_nedenler = []
    if yuksek_risk:
        ek_nedenler.append("yüksek risk")
    if sisti:
        ek_nedenler.append("kısa hareket şişmiş")
    if momentum_sonuyor:
        ek_nedenler.append("kısa momentum sönüyor")
    if hareket_teyitsiz:
        ek_nedenler.append("hareket teyidi yok")

    eski_birlesik_veto = (
        rel_yok and ai_zayif and devam_zayif and bool(ek_nedenler)
    )
    veto = (
        not asiri_rel_yolu
        and not temiz_momentum_yolu
        and (parcalı_momentum or eski_birlesik_veto)
    )
    nedenler = []
    if asiri_rel_yolu:
        nedenler.append(
            f"BEAM yolu: 60dk BTC {coin_btc_60:+.2f} / piyasa {coin_piyasa_60:+.2f}"
        )
    if temiz_momentum_yolu:
        nedenler.append(
            f"HOT yolu: 3/5dk pozitif, {pozitif_sayisi}/4 vade pozitif"
        )
    if not asiri_rel_yolu and not temiz_momentum_yolu:
        nedenler.append("BEAM/HOT yolu yok")
    if parcalı_momentum:
        nedenler.append(f"parçalı momentum ({pozitif_sayisi}/4 pozitif)")
    if ai_zayif:
        nedenler.append(f"AI {ai:.1f} < {V11_FILTRE_AI_ESIK:.2f}")
    if devam_zayif:
        nedenler.append(f"Devam {devam:.1f} < {V11_FILTRE_DEVAM_ESIK:.2f}")
    nedenler.extend(ek_nedenler)

    aday["v11_filtre_adayi"] = True
    aday["v11_filtre_kabul"] = not veto
    aday["v11_filtre_nedenleri"] = nedenler
    aday["v11_filtre_ai_zayif"] = ai_zayif
    aday["v11_filtre_devam_zayif"] = devam_zayif
    aday["v11_filtre_rel_yok"] = rel_yok
    aday["v11_filtre_ek_risk"] = bool(ek_nedenler)
    aday["v11_yol_asiri_rel"] = asiri_rel_yolu
    aday["v11_yol_temiz_momentum"] = temiz_momentum_yolu
    aday["v11_momentum_pozitif_sayisi"] = pozitif_sayisi
    return not veto, nedenler


def v11_tekrar_mesaji_uygun(aday):
    """Aynı coinin birkaç dakika arayla yeniden AL diye konuşmasını önler."""
    symbol = aday.get("symbol", "")
    now = time.time()
    aktif = [
        x for x in SINYAL_SIRA_GECMISI.get(symbol, [])
        if now - float(x.get("ts", 0) or 0) <= SINYAL_SIRA_PENCERE
    ]
    if not aktif:
        return True, ""

    son = max(aktif, key=lambda x: float(x.get("ts", 0) or 0))
    gecen = now - float(son.get("ts", 0) or 0)
    if gecen < V11_TEKRAR_SOGUMA:
        return False, f"son AL üzerinden {gecen / 60:.0f}dk geçti"
    if bool(son.get("hit5")) and gecen < V11_TEKRAR_HIT5_BEKLEME:
        return False, "önceki AL +%5 yaptı; 3 saat yeni giriş yok"

    onceki_fiyat = float(son.get("fiyat", 0) or 0)
    simdiki_fiyat = float(aday.get("fiyat", 0) or 0)
    yeni_hareket = (
        ((simdiki_fiyat / onceki_fiyat) - 1.0) * 100.0
        if onceki_fiyat > 0 and simdiki_fiyat > 0 else 0.0
    )
    mikro = aday.get("mikro") or {}
    yeniden_temiz = (
        float(mikro.get("d3", 0) or 0) > 0
        and float(mikro.get("d5", 0) or 0) > 0
    )
    if gecen < V11_TEKRAR_HIT5_BEKLEME and (
        yeni_hareket < V11_TEKRAR_YENI_HAREKET or not yeniden_temiz
    ):
        return False, (
            f"yeni bağımsız hareket yok ({yeni_hareket:+.2f}%, 3/5dk teyit={yeniden_temiz})"
        )
    return True, ""


# Railway deploy / yeniden baslatma kontrolu: Telegram baglantisini aninda dogrula.
telegram_gonder("✅ V11 Erken+Devam başladı ve aktif. Tek bot taramaya başlıyor.")

while True:
    try:
        print()
        print("AI COIN ASSISTANT - CORE")
        print("--------------------------------")

        btc_d = btc_degisimleri()
        btc = btc_d.get("3s", 0)

        tarama_sayaci += 1
        tam_tarama = (tarama_sayaci == 1 or tarama_sayaci % TAM_TARAMA_DONGUSU == 0)

        if tam_tarama:
            print("Tarama modu: TAM PIYASA TARAMASI")
        else:
            print("Tarama modu: HIZLI HAREKET TARAMASI")

        ticker_response = requests.get(
            "https://api.btcturk.com/api/v2/ticker",
            timeout=10
        )
        ticker_response.raise_for_status()
        ticker = ticker_response.json().get("data", [])

        # Mevcut ticker cevabını öğrenme katmanında da kullan; ekstra API isteği yok.
        al_ogrenme_guncelle(ticker)
        top10_golge_ticker_guncelle(ticker)
        giris_zamani_deneyi_guncelle(ticker)
        rejim_raporu_gerekirse_gonder()
        gelistirme_oneri_raporu_gerekirse_gonder()
        yuzde5_basariraporu_gerekirse_gonder()

        ticker_fiyat_haritasi = {}
        for _coin in ticker:
            try:
                _sym = _coin.get("pair", "")
                _f = float(_coin.get("last", 0) or 0)
                if _sym and _f > 0:
                    ticker_fiyat_haritasi[_sym] = _f
            except Exception:
                pass

        piyasa_fiyatlari = {}
        piyasa_degisim1leri = []
        piyasa_degisim3leri = []
        adaylar = []
        top10_hizli_golge_adaylar = []

        for coin in ticker:
            try:
                symbol = coin.get("pair", "")

                if not symbol.endswith("TRY"):
                    continue
                if symbol == "BTCTRY":
                    continue
                if stable_coin_mi(symbol):
                    continue
                if len(symbol) > 15:
                    continue

                # 1 dakikalık hızlı ön tarama:
                # Ticker fiyatını önceki dakikayla karşılaştır.
                try:
                    ticker_fiyat = float(coin.get("last", 0) or 0)
                except (TypeError, ValueError):
                    ticker_fiyat = 0

                onceki_fiyat = son_fiyatlar.get(symbol)
                hizli_degisim = 0.0

                if ticker_fiyat > 0 and onceki_fiyat and onceki_fiyat > 0:
                    hizli_degisim = ((ticker_fiyat - onceki_fiyat) / onceki_fiyat) * 100

                if ticker_fiyat > 0:
                    son_fiyatlar[symbol] = ticker_fiyat

                # 5 dakikalık tam taramalar arasında:
                # - %0.40+ hızlı hareket eden coinler,
                # - veya Çoklu Güç Havuzu'nda bulunan coinler
                # derin analiz edilir.
                simdi = time.time()
                izleme_bitis = guc_izleme_havuzu.get(symbol, 0)
                havuzda = izleme_bitis > simdi

                if izleme_bitis and not havuzda:
                    guc_izleme_havuzu.pop(symbol, None)

                top10_hizli_golge = top10_hizli_aktif_mi(symbol)
                if (
                    not tam_tarama
                    and abs(hizli_degisim) < HIZLI_HAREKET_ESIGI
                    and not havuzda
                    and not top10_hizli_golge
                ):
                    continue

                if not tam_tarama:
                    kaynak = "HAVUZ" if havuzda and abs(hizli_degisim) < HIZLI_HAREKET_ESIGI else "HIZLI"
                    print(f"[{kaynak}] {symbol} | 1dk: %{hizli_degisim:.2f}")

                d = veri_getir(symbol, 24)
                o = d.get("o", [])
                h = d.get("h", [])
                c = d.get("c", [])
                v = d.get("v", [])

                if min(len(o), len(h), len(c), len(v)) < 24:
                    continue

                fiyat = c[-1]
                if not fiyat or not c[-2] or not c[-4] or not c[-24]:
                    continue

                degisim1 = ((c[-1] - c[-2]) / c[-2]) * 100
                degisim3 = ((c[-1] - c[-4]) / c[-4]) * 100
                degisim24 = ((c[-1] - c[-24]) / c[-24]) * 100

                piyasa_fiyatlari[symbol] = fiyat
                piyasa_degisim1leri.append(degisim1)
                piyasa_degisim3leri.append(degisim3)

                # Mikro veri artık tüm piyasada çağrılmaz.
                # Önce saatlik/Radar motoru adayları daraltır; 1-3-5-10 dk veri yalnız teknik havuza kalanlarda çekilir.
                mikro = {}
                mikro_skor = 0.0

                son_hacim = v[-1]
                ort_hacim = sum(v[-6:-1]) / 5
                if ort_hacim <= 0:
                    continue

                hacim_kat = son_hacim / ort_hacim

                btc_guc_skoru, btc_fark1, btc_fark3, btc_fark24 = btc_gucu_v2_hesapla(
                    degisim1, degisim3, degisim24, btc_d
                )

                btcden_guclu = btc_guc_skoru >= 4 and btc_fark3 >= 0.5
                son_mum_yesil = c[-1] > o[-1]
                zirve_yakin = fiyat > max(h[-12:-1]) * 0.995
                yeni_zirve = fiyat >= max(h[-24:-1])
                satis_baskisi = son_hacim > ort_hacim * 5 and degisim1 < 0
                haber_skoru = haber_puani(symbol)

                hacim_skoru = min(hacim_kat * 2, 10)
                momentum_skoru = max(0, degisim3 * 2)
                mum_skoru = 1 if son_mum_yesil else 0
                zirve_skoru = 1 if zirve_yakin else 0

                genel_skor = (
                    hacim_skoru * 0.50
                    + momentum_skoru * 0.20
                    + btc_guc_skoru * 0.15
                    + haber_skoru * 0.20
                    + mum_skoru
                    + zirve_skoru
                )

                kalite_skoru = (
                    hacim_skoru * 0.55
                    + momentum_skoru * 0.30
                    + btc_guc_skoru * 0.15
                    + mum_skoru
                    + zirve_skoru
                )

                if hacim_kat >= 5:
                    genel_skor += 4
                if hacim_kat >= 8:
                    genel_skor += 6

                if haber_skoru >= 15:
                    genel_skor += 4
                if haber_skoru > 0 and hacim_kat > 3:
                    genel_skor += 5

                if degisim24 > 10:
                    genel_skor -= 4
                if degisim3 > 7:
                    genel_skor -= 4
                if degisim1 > 4:
                    genel_skor -= 4
                if degisim24 > 0 and degisim3 > degisim24 * 0.85:
                    genel_skor -= 2
                if degisim3 > 0 and degisim1 > degisim3 * 0.65:
                    genel_skor -= 2
                if hacim_kat > 7 and degisim3 > 6:
                    genel_skor -= 3
                if satis_baskisi:
                    genel_skor -= 5

                if btc_fark3 >= 4:
                    genel_skor += 2
                elif btc_fark3 >= 2:
                    genel_skor += 1

                lider_skoru = lider_skoru_hesapla(
                    hacim_kat, degisim1, degisim3, degisim24,
                    btc_fark1, btc_fark3, btc_fark24,
                    zirve_yakin, yeni_zirve
                )

                if lider_skoru >= 7:
                    genel_skor += 2
                elif lider_skoru >= 5:
                    genel_skor += 1

                if zirve_yakin or yeni_zirve:
                    genel_skor += 1

                radar_skoru = guc_skoru_hesapla(
                    hacim_kat, degisim1, degisim3, degisim24,
                    btc_guc_skoru, lider_skoru, haber_skoru,
                    satis_baskisi, btc_fark3, zirve_yakin, yeni_zirve
                )

                # --------------------------------------------------
                # Early Capture V1 + gerçek Coin Radar alarm kapıları
                # --------------------------------------------------
                onceki = onceki_tarama.get(symbol)

                hacim_hizlaniyor = False
                momentum_hizlaniyor = False
                btc_farki_aciliyor = False
                lider_gucleniyor = False

                if onceki:
                    eski_hacim = onceki.get("hacim", hacim_kat)
                    eski_degisim3 = onceki.get("degisim3", degisim3)
                    eski_btc_fark3 = onceki.get("btc_fark3", btc_fark3)
                    eski_lider = onceki.get("lider_skoru", lider_skoru)

                    hacim_hizlaniyor = (
                        eski_hacim > 0
                        and hacim_kat >= eski_hacim * 1.25
                        and hacim_kat - eski_hacim >= 0.8
                    )
                    momentum_hizlaniyor = degisim3 - eski_degisim3 >= 0.45
                    btc_farki_aciliyor = btc_fark3 - eski_btc_fark3 >= 0.35
                    lider_gucleniyor = lider_skoru - eski_lider >= 1

                onceki_tarama[symbol] = {
                    "hacim": hacim_kat,
                    "degisim3": degisim3,
                    "btc_fark3": btc_fark3,
                    "lider_skoru": lider_skoru,
                    "zaman": time.time()
                }

                # Dinamik hareket teyitleri:
                # Bunlar RED/ATM tipi "nedenleri dolu" sinyallerin hareket tarafını oluşturur.
                dinamik_teyit_sayisi = sum([
                    bool(hacim_hizlaniyor),
                    bool(momentum_hizlaniyor),
                    bool(btc_farki_aciliyor),
                    bool(lider_gucleniyor),
                ])

                # Mevcut Early yolu korunuyor; sadece 3s üst sınırı 3'ten 5'e açıldı.
                # Böylece güçlenmeye devam eden coin Early ile Roket arasında boşluğa düşmez.
                erken_aday = (
                    2.5 <= hacim_kat < 8
                    and 0.5 <= degisim3 < 5
                    and degisim1 > 0
                    and btc_guc_skoru >= 3
                    and btc_fark3 >= 0
                    and radar_skoru >= 45
                    and kalite_skoru >= 6
                    and not satis_baskisi
                    and (
                        (hacim_hizlaniyor and momentum_hizlaniyor)
                        or (momentum_hizlaniyor and btc_farki_aciliyor)
                        or (hacim_hizlaniyor and lider_gucleniyor)
                    )
                )

                # ENA tipi basamaklı güçlenme:
                # Bir anda %0.40 sıçramasa bile 3s momentumunu koruyan,
                # hacmi canlı, BTC'ye göre zayıflamayan ve liderliği oluşan coinleri izler.
                basamakli_trend = False
                if onceki:
                    eski_degisim3 = onceki.get("degisim3", degisim3)
                    eski_hacim = onceki.get("hacim", hacim_kat)
                    basamakli_trend = (
                        1.0 <= degisim3 <= 10
                        and degisim1 > 0
                        and hacim_kat >= 1.8
                        and hacim_kat >= eski_hacim * 0.90
                        and degisim3 >= eski_degisim3 - 0.15
                        and btc_fark3 >= 0
                        and lider_skoru >= 4
                        and not satis_baskisi
                    )

                # Çoklu Güç Havuzu adayı:
                # Radar kategorisine girmese bile en az 2 dinamik teyidi olan
                # veya basamaklı trendi koruyan coin teknik motora alınır.
                guc_havuzu_adayi = (
                    not satis_baskisi
                    and radar_skoru >= 40
                    and kalite_skoru >= 5
                    and 0.5 <= degisim3 <= 10
                    and degisim1 > -0.5
                    and hacim_kat >= 1.8
                    and btc_fark3 >= -0.5
                    and (
                        (
                            dinamik_teyit_sayisi >= 2
                            and (hacim_hizlaniyor or momentum_hizlaniyor)
                        )
                        or basamakli_trend
                    )
                )

                # Mikro Ön Alarm V2:
                # Coin henüz klasik Radar / Güç Havuzu kapısına girmemiş olsa bile
                # ticker'da belirgin hızlanma gösteriyorsa yalnız o coin için 1-3-5-10 dk
                # mikro analiz açılır. Böylece bütün piyasaya 1 dk mum isteği atılmadan
                # LAYER tipi yeni başlayan patlamalar daha erken incelenebilir.
                mikro_on_alarm = (
                    not satis_baskisi
                    and degisim3 <= 10
                    and degisim1 <= 6
                    and (
                        (hizli_degisim >= 0.30 and hacim_kat >= 1.20 and btc_fark3 >= -1.0)
                        or (
                            0.70 <= degisim1 <= 4.5
                            and 0.40 <= degisim3 <= 7.0
                            and hacim_kat >= 1.50
                            and btc_fark3 >= -0.8
                        )
                    )
                )

                mikro_aday = False

                if erken_aday or guc_havuzu_adayi or mikro_on_alarm:
                    guc_izleme_havuzu[symbol] = time.time() + GUC_IZLEME_SURESI

                yildiz_adayi = (
                    radar_skoru >= 88
                    and lider_skoru >= 7
                    and btc_guc_skoru >= 7
                    and kalite_skoru >= 14
                    and hacim_kat >= 5
                    and degisim1 > 1
                    and degisim3 >= 4
                    and zirve_yakin
                )

                elit_adayi = (
                    radar_skoru >= 74
                    and lider_skoru >= 5
                    and btc_guc_skoru >= 5
                    and kalite_skoru >= 10
                    and hacim_kat >= 8
                    and degisim1 > 0
                    and degisim3 >= 3
                    and btcden_guclu
                )

                trader_adayi = (
                    radar_skoru >= 55
                    and hacim_kat >= 15
                    and btcden_guclu
                    and btc_guc_skoru >= 4
                    and degisim3 >= 6
                )

                roket_adayi = (
                    radar_skoru >= 62
                    and kalite_skoru >= 8
                    and hacim_kat >= 5
                    and degisim1 > 0
                    and degisim3 >= 1.5
                    and not (hacim_kat >= 10 and degisim3 < 4 and lider_skoru < 7)
                    and btcden_guclu
                    and btc_guc_skoru >= 4
                    and (haber_skoru > 0 or lider_skoru >= 5)
                )

                assistant_ana_aday = (
                    erken_aday
                    or guc_havuzu_adayi
                    or yildiz_adayi
                    or elit_adayi
                    or trader_adayi
                    or roket_adayi
                )

                # Rolling ilk 10 için, daha aday olmadan önceki kapıyı sakla.
                # Böylece rapor yalnız Telegram'a kadar gelebilen coinleri değil,
                # Radar/ön havuzda kaybolan gerçek kaçakları da açıklayabilir.
                top10_golge_asama_guncelle(
                    symbol,
                    "on_havuz_adayi" if (assistant_ana_aday or mikro_on_alarm) else "on_havuz_disinda",
                    radar=round(float(radar_skoru or 0), 3),
                    hacim=round(float(hacim_kat or 0), 3),
                    degisim1=round(float(degisim1 or 0), 3),
                    degisim3=round(float(degisim3 or 0), 3),
                    btc_fark3=round(float(btc_fark3 or 0), 3),
                    lider=round(float(lider_skoru or 0), 3),
                    erken_aday=bool(erken_aday),
                    guc_havuzu_adayi=bool(guc_havuzu_adayi),
                    mikro_on_alarm=bool(mikro_on_alarm),
                )

                # Klasik aday değilse bile Mikro Ön Alarm teknik ön havuza sokabilir.
                # Asıl adaylık biraz aşağıda gerçek 1-3-5-10 dk verisiyle doğrulanır.
                if not assistant_ana_aday and not mikro_on_alarm:
                    if top10_hizli_golge:
                        top10_hizli_golge_adaylar.append({
                            "symbol": symbol,
                            "fiyat": fiyat,
                            "radar_skoru": radar_skoru,
                            "hacim": round(hacim_kat, 2),
                            "degisim1": round(degisim1, 2),
                            "degisim3": round(degisim3, 2),
                            "btc_fark3": round(btc_fark3, 2),
                            "lider_skoru": round(lider_skoru, 2),
                        })
                    continue

                if yildiz_adayi:
                    radar_kategori = "⭐ Yıldız"
                elif elit_adayi:
                    radar_kategori = "🔥 Elit Roket"
                elif trader_adayi:
                    radar_kategori = "📊 Trader Hacim"
                elif roket_adayi:
                    radar_kategori = "🚀 Roket Adayı"
                elif erken_aday:
                    radar_kategori = "🌱 Erken Aday"
                else:
                    radar_kategori = "⚡ Güçleniyor"

                adaylar.append({
                    "symbol": symbol,
                    "fiyat": fiyat,
                    "radar_skoru": radar_skoru,
                    "radar_kategori": radar_kategori,
                    "orijinal_erken_aday": erken_aday,
                    "erken_aday": erken_aday,
                    "assistant_ana_aday": assistant_ana_aday,
                    "mikro_on_alarm": mikro_on_alarm,
                    "mikro_aday": mikro_aday,
                    "mikro": mikro,
                    "guc_havuzu_adayi": guc_havuzu_adayi,
                    "basamakli_trend": basamakli_trend,
                    "dinamik_teyit_sayisi": dinamik_teyit_sayisi,
                    "hacim_hizlaniyor": hacim_hizlaniyor,
                    "momentum_hizlaniyor": momentum_hizlaniyor,
                    "btc_farki_aciliyor": btc_farki_aciliyor,
                    "lider_gucleniyor": lider_gucleniyor,
                    "genel_skor": round(genel_skor, 2),
                    "kalite_skoru": round(kalite_skoru, 2),
                    "hacim": round(hacim_kat, 2),
                    "degisim1": round(degisim1, 2),
                    "degisim3": round(degisim3, 2),
                    "degisim24": round(degisim24, 2),
                    "btcden_guclu": btcden_guclu,
                    "btc_fark3": round(btc_fark3, 2),
                    "btc_guc_skoru": btc_guc_skoru,
                    "lider_skoru": round(lider_skoru, 2),
                    "haber_skoru": haber_skoru,
                    "zirve_yakin": zirve_yakin,
                    "yeni_zirve": yeni_zirve
                })

            except Exception as e:
                print(f"Coin hata ({coin.get('pair', '?')}):", e)

        # --------------------------------------------------
        # 60DK BAĞIMSIZ GÖRECELİ GÜÇ BONUSU
        # Öğrenme raporunda en güçlü eşikler:
        #   Coin - BTC 60dk > +0.98
        #   Coin - piyasa 60dk > +0.87
        # Bu bonus AL kapısını / AI skorunu DEĞİŞTİRMEZ. Yalnız bilgi ve eşit
        # Radar skorlarında öncelik amacıyla tutulur; gerçek sonucu AL öğrenmesi ölçer.
        # Hızlı taramada piyasa medyanı yalnız hareket eden coinlerden sapmasın diye
        # son TAM taramanın medyanı kullanılır.
        if tam_tarama and piyasa_degisim1leri:
            SON_PIYASA_MEDYAN_60 = statistics.median(piyasa_degisim1leri)
        piyasa_medyan60 = SON_PIYASA_MEDYAN_60
        btc60 = float(btc_d.get("1s", 0) or 0)

        for _a in adaylar:
            _coin60 = float(_a.get("degisim1", 0) or 0)
            _btc_rel60 = _coin60 - btc60
            _piy_rel60 = _coin60 - piyasa_medyan60
            _bonus = int(_btc_rel60 > 0.98) + int(_piy_rel60 > 0.87)
            _a["coin_btc_60"] = round(_btc_rel60, 2)
            _a["coin_piyasa_60"] = round(_piy_rel60, 2)
            _a["goreceli_guc_bonus"] = _bonus

            # ÖĞRENME KATKISI V1
            # Canlı AL kapısını değiştirmez. Yalnız aday sıralamasına küçük katkı verir.
            # Günlük öğrenme raporlarında tekrar tekrar öne çıkan yapıların kesişimi kullanılır.
            _m = _a.get("mikro") or {}
            _vr = float(_m.get("vr310", 0) or 0)
            _stair = _m.get("stair5")
            _d3 = float(_m.get("d3", 0) or 0)

            _learn = 0
            _learn_neden = []
            if 0.60 <= _vr <= 3.00:
                _learn += 2
                _learn_neden.append("hacim 0.6-3.0")
            if _stair is not None and float(_stair) < 75:
                _learn += 2
                _learn_neden.append("stair<75")
            if _d3 > 0:
                _learn += 1
                _learn_neden.append("3dk>0")
            if _piy_rel60 > 0.90:
                _learn += 1
                _learn_neden.append("piyasa+60")
            if _btc_rel60 > 0.95:
                _learn += 1
                _learn_neden.append("BTC+60")

            _a["ogrenme_katkisi"] = _learn
            _a["ogrenme_nedenleri"] = _learn_neden
            # Radar hâlâ ana skor. Öğrenme en fazla +4.2 eşdeğer puanla yakın adayları yeniden sıralar.
            _a["aday_siralama_skoru"] = float(_a.get("radar_skoru", 0) or 0) + min(_learn, 7) * 0.60

        adaylar.sort(
            key=lambda x: (
                x.get("aday_siralama_skoru", x.get("radar_skoru", 0)),
                x.get("radar_skoru", 0),
                x.get("goreceli_guc_bonus", 0),
                x.get("genel_skor", 0),
            ),
            reverse=True
        )

        radar_top10 = adaylar[:10]

        # Radar Top10 dışında, hareket teyidi yüksek coinleri de teknik motora sok.
        guc_top10 = sorted(
            [a for a in adaylar if a.get("guc_havuzu_adayi")],
            key=lambda x: (
                x.get("dinamik_teyit_sayisi", 0),
                x.get("genel_skor", 0),
                x.get("radar_skoru", 0),
            ),
            reverse=True
        )[:10]

        # Radar dışında Mikro Ön Alarm'a düşen en güçlü coinleri de ayrıca koru.
        # Böylece düşük Radar skoru nedeniyle Top10 dışında kalıp erken hareket kaçmaz.
        mikro_on_top = sorted(
            [a for a in adaylar if a.get("mikro_on_alarm")],
            key=lambda x: (
                x.get("degisim1", 0),
                x.get("hacim", 0),
                x.get("radar_skoru", 0),
            ),
            reverse=True
        )[:8]

        # Aynı coin listelerde varsa tek kez analiz edilir.
        top10 = []
        gorulenler = set()
        for aday in radar_top10 + guc_top10 + mikro_on_top:
            symbol = aday.get("symbol")
            if symbol in gorulenler:
                continue
            gorulenler.add(symbol)
            top10.append(aday)

        print(
            f"Teknik havuz: RadarTop10={len(radar_top10)} | "
            f"ÇokluGüç={len(guc_top10)} | MikroÖn={len(mikro_on_top)} | Benzersiz={len(top10)}"
        )

        # API optimizasyonu: pahalı 1 dk mum çağrısı yalnız gerçekten teknik motora kalan coinlerde yapılır.
        for a in top10:
            mikro = mikro_ivme_hesapla(a["symbol"])
            a["mikro"] = mikro
            mikro_skor = float(mikro.get("skor", 0) or 0)
            a["mikro_aday"] = bool(
                mikro
                and not mikro.get("sisti", False)
                and mikro_skor >= 55
                and float(mikro.get("d3", 0) or 0) >= 0.25
                and float(mikro.get("d5", 0) or 0) >= 0.35
                and (mikro.get("fiyat_ivme") or mikro.get("basamak"))
                and (mikro.get("hacim_ivmeleniyor") or float(mikro.get("hacim1x", 0) or 0) >= 1.30)
                and float(a.get("btc_fark3", 0) or 0) >= -0.8
            )

            # Normal Radar kapısından gelmeyen coin ancak gerçek mikro teyit aldıysa
            # teknik AL motoruna geçebilir. Mikro teyit yoksa burada elenir.
            if a.get("mikro_on_alarm") and not a.get("assistant_ana_aday"):
                if a["mikro_aday"]:
                    a["erken_aday"] = True
                    a["radar_kategori"] = "🌱 Mikro Erken"
                    a["assistant_ana_aday"] = True
                else:
                    a["mikro_on_alarm_reddedildi"] = True
                    top10_golge_asama_guncelle(
                        a.get("symbol"),
                        "mikro_teyitsiz",
                        d1=round(float(mikro.get("d1", 0) or 0), 3),
                        d3=round(float(mikro.get("d3", 0) or 0), 3),
                        d5=round(float(mikro.get("d5", 0) or 0), 3),
                    )

        # Mikro ön alarmdan gelip teyit alamayanları teknik API çağrısından önce çıkar.
        top10 = [
            a for a in top10
            if a.get("assistant_ana_aday") and not a.get("mikro_on_alarm_reddedildi")
        ]

        # İlk 10 hızlı havuzu canlı aday üretmez. Normal havuza giremeyen coinler
        # için yalnız ilk beş dakikanın mikro/teknik fotoğrafını kaydeder.
        canli_havuz_symbol = {a.get("symbol") for a in top10}
        for _g in top10_hizli_golge_adaylar:
            if _g.get("symbol") in canli_havuz_symbol:
                continue
            try:
                _gm = mikro_ivme_hesapla(_g["symbol"])
                _gt = teknik_analiz_hesapla(_g["symbol"])
                top10_hizli_teknik_kaydet(
                    _g["symbol"], mikro=_gm, teknik=_gt,
                    radar=round(float(_g.get("radar_skoru", 0) or 0), 3),
                    hacim=round(float(_g.get("hacim", 0) or 0), 3),
                    degisim1=round(float(_g.get("degisim1", 0) or 0), 3),
                    degisim3=round(float(_g.get("degisim3", 0) or 0), 3),
                    btc_fark3=round(float(_g.get("btc_fark3", 0) or 0), 3),
                )
            except Exception as e:
                print(f"[TOP10 HIZLI GÖLGE] {_g.get('symbol')} teknik hata:", e)

        # H mantığı: Radar Top10 + Çoklu Güç + teyitli Mikro Erken üzerinde teknik analiz + karar motoru.
        for a in top10:
            teknik = teknik_analiz_hesapla(a["symbol"])
            a["teknik"] = teknik

            # RSI 50-72, öğrenme raporlarında kombinasyon içinde tekrar eden sağlıklı bölge.
            # Kararı değiştirmez; yalnız öğrenme uyum bilgisini tamamlar.
            _rsi = teknik.get("rsi") if teknik else None
            _uyum = int(a.get("ogrenme_katkisi", 0) or 0)
            if _rsi is not None and 50 <= float(_rsi) <= 72:
                _uyum += 2
                a.setdefault("ogrenme_nedenleri", []).append("RSI50-72")
            a["ogrenme_uyum"] = _uyum
            karar = h_karar_hesapla(a)
            a.update(karar)
            giris_k, devam_g = destek_skorlari(a)
            a["giris_kalitesi"] = giris_k
            a["devam_gucu"] = devam_g
            a["erken_puan"] = round(float((a.get("mikro") or {}).get("skor", 0) or 0), 1)
            kal_skor, kal_etiket, kal_nedenler = kalicilik_skoru_hesapla(a)
            a["kalicilik_skoru"] = kal_skor
            a["kalicilik_etiket"] = kal_etiket
            a["kalicilik_nedenler"] = kal_nedenler

            top10_golge_asama_guncelle(
                a.get("symbol"),
                "h_al" if a.get("karar") == "🟢 AL" else "h_bekle",
                h_karar=str(a.get("karar", "🟡 BEKLE")),
                ai=round(float(a.get("ai_skoru", 0) or 0), 3),
                devam=round(float(a.get("devam_gucu", 0) or 0), 3),
                kalicilik=round(float(a.get("kalicilik_skoru", 0) or 0), 3),
                rsi=round(float((teknik or {}).get("rsi", 0) or 0), 3),
                adx=round(float((teknik or {}).get("adx", 0) or 0), 3),
                d1=round(float((a.get("mikro") or {}).get("d1", 0) or 0), 3),
                d3=round(float((a.get("mikro") or {}).get("d3", 0) or 0), 3),
                d5=round(float((a.get("mikro") or {}).get("d5", 0) or 0), 3),
                d10=round(float((a.get("mikro") or {}).get("d10", 0) or 0), 3),
            )
            top10_hizli_teknik_kaydet(
                a.get("symbol"), mikro=a.get("mikro") or {}, teknik=teknik or {},
                radar=round(float(a.get("radar_skoru", 0) or 0), 3),
                hacim=round(float(a.get("hacim", 0) or 0), 3),
                degisim1=round(float(a.get("degisim1", 0) or 0), 3),
                degisim3=round(float(a.get("degisim3", 0) or 0), 3),
                btc_fark3=round(float(a.get("btc_fark3", 0) or 0), 3),
            )


            # --------------------------------------------------
            # AL DEBUG LOG
            # Telegram'a hiçbir şey göndermez.
            # Railway logunda coin neden AL / BEKLE olduğunu gösterir.
            # --------------------------------------------------
            if teknik:
                ema20 = teknik.get("ema20")
                ema50 = teknik.get("ema50")
                rsi = teknik.get("rsi")
                macd_hist = teknik.get("macd_hist")
                adx = teknik.get("adx")
                fiyat = a.get("fiyat", 0)
                kategori = a.get("radar_kategori", "")
                ai_skor = a.get("ai_skoru", 0)

                ema_ok = (
                    ema20 is not None
                    and ema50 is not None
                    and fiyat
                    and ema20 > ema50
                    and fiyat > ema20
                )
                macd_ok = macd_hist is not None and macd_hist > 0

                if a.get("erken_aday"):
                    rsi_ok = rsi is not None and 48 <= rsi <= 70
                    adx_ok = adx is not None and adx >= 30
                    skor_ok = ai_skor >= 80
                elif "Elit" in kategori:
                    rsi_ok = rsi is not None and 45 <= rsi <= 75
                    adx_ok = adx is not None and adx >= 28
                    skor_ok = ai_skor >= 85
                elif "Yıldız" in kategori:
                    # Yıldızlarda normal teknik kapıyı göster.
                    # H tipi istisnai devam varsa karar motoru ayrıca AL verebilir.
                    rsi_ok = rsi is not None and 48 <= rsi <= 70
                    adx_ok = adx is not None and adx >= 30
                    skor_ok = ai_skor >= 85
                else:
                    rsi_ok = rsi is not None and 48 <= rsi <= 75
                    adx_ok = adx is not None and adx >= 27
                    skor_ok = ai_skor >= 80

                def durum(ok):
                    return "✅" if ok else "❌"

                rsi_txt = "NA" if rsi is None else f"{rsi:.1f}"
                adx_txt = "NA" if adx is None else f"{adx:.1f}"
                macd_txt = "NA" if macd_hist is None else f"{macd_hist:.5f}"

                print(
                    f"[AL DEBUG] {a['symbol']} | {a.get('karar', '🟡 BEKLE')} | "
                    f"{kategori} | "
                    f"EMA {durum(ema_ok)} | "
                    f"RSI {rsi_txt} {durum(rsi_ok)} | "
                    f"MACD {macd_txt} {durum(macd_ok)} | "
                    f"ADX {adx_txt} {durum(adx_ok)} | "
                    f"AI {ai_skor}/100 {durum(skor_ok)} | "
                    f"Radar {a.get('radar_skoru', 0)}"
                )
            else:
                print(
                    f"[AL DEBUG] {a['symbol']} | 🟡 BEKLE | "
                    f"Teknik veri alınamadı"
                )

        # AL kalite koruması: Assistant AL bekletilmez.
        # Yalnızca çok düşük hacim + kısa vade aynı anda sönüyorsa bariz zayıflık veto edilir.
        for _a in top10:
            if _a.get("karar") == "🟢 AL":
                _m = _a.get("mikro") or {}
                if _m:
                    _gh = float(_a.get("hacim", 0) or 0)
                    _d1 = float(_m.get("d1", 0) or 0)
                    _d3 = float(_m.get("d3", 0) or 0)
                    _h1 = float(_m.get("hacim1x", 0) or 0)
                    _hi = float(_m.get("hacim_ivme", 0) or 0)

                    cok_zayif_hacim = _gh < 0.30 and _h1 < 0.80 and _hi < 1.00
                    mikro_sonuyor = _d1 < -0.15 and _d3 <= 0.10

                    if cok_zayif_hacim and mikro_sonuyor:
                        print(
                            f"[AL MIKRO VETO] {_a.get('symbol')} | "
                            f"Hacim={_gh:.2f}x | 1dkHacim={_h1:.2f}x | İvme={_hi:.2f}x | "
                            f"1dk={_d1:+.2f}% | 3dk={_d3:+.2f}%"
                        )
                        _a["karar"] = "🟡 BEKLE"

        # İlk aday sıralamasını Radar yapar; H motorundan sonra en güçlü teknik fırsat üste çıkar.
        top10.sort(
            key=lambda x: (
                x.get("ai_skoru", 0),
                x.get("ogrenme_uyum", 0),
                x.get("radar_skoru", 0),
            ),
            reverse=True
        )

        if not top10:
            print("Şu an uygun aday yok.")
        else:
            gonderilecekler = []
            filtrelenenler = []

            for a in top10:
                symbol = a["symbol"]
                karar = a.get("karar", "🟡 BEKLE")
                onceki_karar = son_ai_kararlar.get(symbol)
                son_ai_kararlar[symbol] = karar

                # Telegram yalnızca gerçek AL kararlarında konuşur.
                # BEKLE ve SAT/PAS arka planda/loglarda izlenmeye devam eder.
                if "🟢 AL" not in karar:
                    top10_golge_asama_guncelle(symbol, "h_bekle")
                    continue

                # Aynı AL kararını tekrar gönderme.
                if onceki_karar == karar:
                    continue

                # V11'in erken/hareketli yapısını koruyan canlı yumuşak süzgeç.
                # Yalnız birleşik zayıf profil Telegram'dan çıkar; sonuç gölgede
                # aynı giriş fiyatından üç saat boyunca ayrıca ölçülür.
                filtre_kabul, filtre_nedenleri = v11_canli_yumusak_filtre(a)
                if not filtre_kabul:
                    # Koşullar sonraki taramada düzelirse aynı coin yeniden
                    # değerlendirilebilsin; filtre veto durumu gerçek AL sayılmaz.
                    son_ai_kararlar[symbol] = "🟡 FİLTRE BEKLE"
                    print(
                        f"[V11 YUMUŞAK FİLTRE] {symbol} | ELENDİ | "
                        + "; ".join(filtre_nedenleri)
                    )
                    filtrelenenler.append(a)
                    top10_golge_asama_guncelle(
                        symbol,
                        "yumusa_filtre",
                        filtre_nedenleri=list(filtre_nedenleri),
                    )
                    continue

                tekrar_kabul, tekrar_nedeni = v11_tekrar_mesaji_uygun(a)
                if not tekrar_kabul:
                    # Tekrar engeli gerçek bir BEKLE kararı değildir. Coin yeni,
                    # bağımsız hareket kurarsa sonraki taramalarda yeniden sınanır.
                    son_ai_kararlar[symbol] = "🟡 TEKRAR BEKLE"
                    print(f"[V11 TEKRAR KORUMASI] {symbol} | {tekrar_nedeni}")
                    top10_golge_asama_guncelle(
                        symbol, "tekrar_koruma", tekrar_nedeni=str(tekrar_nedeni)
                    )
                    continue

                gonderilecekler.append(a)

            # Elenen adaylar Telegram ve +%5 kâr bildirimi üretmez. Yalnız
            # +%2/+%3/+%5 ve yanlış tepki karşılaştırması için izlenir.
            piyasa_medyan3 = statistics.median(piyasa_degisim3leri) if piyasa_degisim3leri else 0.0
            btc_giris_fiyati = ticker_fiyat_haritasi.get("BTCTRY", 0)
            for _a in filtrelenenler:
                al_ogrenme_baslat(
                    _a,
                    btc_d,
                    piyasa_fiyatlari,
                    piyasa_medyan3,
                    btc_giris_fiyati,
                    kayit_tipi="v11_kalite_veto",
                )

            if not gonderilecekler:
                print("Yeni AL kararı yok. Telegram sessiz.")
            else:
                # Her coin Telegram'a AYRI mesaj olarak gider.
                # Böylece aynı taramada bulunan coinler tek uzun mesajda birleşmez.
                gonderilenler = []
                gec_teyitler = []
                erken_izleler = []

                for a in gonderilecekler:
                    teknik = a.get("teknik")
                    if not teknik:
                        continue

                    mesaj = ""

                    ema_yon = "Yukarı" if teknik["ema20"] > teknik["ema50"] else "Aşağı"
                    macd_yon = "Pozitif" if teknik["macd_hist"] is not None and teknik["macd_hist"] > 0 else "Negatif"
                    nedenler = list(a.get("nedenler", []))
                    hizlar = []

                    if a.get("hacim_hizlaniyor"):
                        hizlar.append("hacim hızlanıyor")
                    if a.get("momentum_hizlaniyor"):
                        hizlar.append("momentum hızlanıyor")
                    if a.get("btc_farki_aciliyor"):
                        hizlar.append("BTC farkı açılıyor")
                    if a.get("lider_gucleniyor"):
                        hizlar.append("lider güçleniyor")
                    if a.get("basamakli_trend"):
                        hizlar.append("basamaklı trend korunuyor")

                    if hizlar:
                        baslik = "Erken yakalama" if a.get("orijinal_erken_aday") else "Hareket teyidi"
                        nedenler.insert(0, baslik + ": " + ", ".join(hizlar))

                    rel_bonus = int(a.get("goreceli_guc_bonus", 0) or 0)
                    if rel_bonus:
                        nedenler.insert(0,
                            f"60dk göreceli güç +{rel_bonus} "
                            f"(BTC {a.get('coin_btc_60', 0):+.2f} / piyasa {a.get('coin_piyasa_60', 0):+.2f})"
                        )

                    # NEDEN ÖNCELİĞİ V1
                    # Ham neden sayısı korunur; fakat mesaj sırası ve Genel Güç içindeki
                    # neden kalitesi "hangi neden" geldiğine göre ağırlıklandırılır.
                    # Böylece EMA/MACD/basamak gibi benzer trend nedenleri puanı yapay şişirmez.
                    def _neden_onem_puani(metin):
                        s = str(metin or "").lower()

                        # En ayırıcı / erken devam nedenleri
                        if "60dk göreceli güç +2" in s:
                            return 10
                        if "momentum hızlanıyor" in s:
                            return 9
                        if "btc farkı açılıyor" in s:
                            return 9
                        if "lider güçleniyor" in s or "liderlik güçleniyor" in s:
                            return 8
                        if "adx" in s or "trend çok güçlü" in s:
                            return 8
                        if "hacim hızlanıyor" in s:
                            return 7
                        if "rsi sağlıklı" in s:
                            return 7
                        if "60dk göreceli güç +1" in s:
                            return 6

                        # Destekleyici ama tek başına güçlü ayrım sayılmayanlar
                        if "macd pozitif" in s:
                            return 4
                        if "ema trendi yukarı" in s or "ema trendi korunuyor" in s:
                            return 4
                        if "radar yıldız" in s:
                            return 4
                        if "basamak" in s:
                            return 2

                        # Aşırı sıcak / doygunluk nedenleri pozitif kalite sayılmaz.
                        if "aşırı" in s or "doygunluk" in s or "ısınıyor" in s:
                            return 0
                        return 3

                    def _neden_parcalari_ve_sira(teknik_nedenler, hareketler, rel_bonus):
                        parcalar = []

                        # Göreceli güç tek parça ve yüksek öncelik.
                        if rel_bonus:
                            parcalar.append(
                                f"60dk göreceli güç +{rel_bonus} "
                                f"(BTC {a.get('coin_btc_60', 0):+.2f} / piyasa {a.get('coin_piyasa_60', 0):+.2f})"
                            )

                        # Hareket teyitlerini artık tek uzun cümlede saklamak yerine
                        # öğrenme/önem hesabı için ayrı nedenler olarak ele al.
                        for h in hareketler:
                            parcalar.append(h)

                        # Teknik nedenler
                        for t in teknik_nedenler:
                            parcalar.append(str(t))

                        # Önemli olanlar önce.
                        parcalar.sort(key=lambda x: _neden_onem_puani(x), reverse=True)
                        return parcalar

                    # Neden sayısı: teknik nedenler + hareket teyitleri + göreceli güç.
                    # Ham toplam sayıyı koruyoruz; fakat "önemli neden" sayısını ayrıca hesaplıyoruz.
                    toplam_neden_sayisi = (
                        len(a.get("nedenler", []))
                        + len(hizlar)
                        + (1 if rel_bonus else 0)
                    )

                    _neden_parcalari = _neden_parcalari_ve_sira(
                        a.get("nedenler", []),
                        hizlar,
                        rel_bonus,
                    )
                    _neden_puanlari = [_neden_onem_puani(x) for x in _neden_parcalari]
                    _onemli_nedenler = [
                        x for x, p in zip(_neden_parcalari, _neden_puanlari)
                        if p >= 7
                    ]
                    _onemli_neden_sayisi = len(_onemli_nedenler)

                    # 10 adet ham nedenden ziyade ağırlıklı kalite:
                    # teorik üst sınır 10 neden x 10 puan = 100.
                    _neden_agirlikli_toplam = sum(_neden_puanlari)
                    _neden_kalite_agirlikli = max(0.0, min(100.0, _neden_agirlikli_toplam))

                    # Alarm önemli neden sayısına göre.
                    neden_alarm = "🚨 🚨 " if _onemli_neden_sayisi >= 4 else ""

                    # Telegram'da yalnız gerçekten önemli nedenleri göster.
                    # Düşük öncelikli nedenler arka planda öğrenme/rapor için tutulmaya devam eder.
                    neden = " • ".join(_onemli_nedenler)

                    mikro = a.get("mikro") or {}
                    mikro_satir = ""
                    if mikro:
                        mikro_satir = (
                            f"⏱ 1dk %{mikro.get('d1', 0)} | 3dk %{mikro.get('d3', 0)} | "
                            f"5dk %{mikro.get('d5', 0)} | 10dk %{mikro.get('d10', 0)}\n"
                        )

                    gorunen_coin = a['symbol'][:-3] if a['symbol'].endswith("TRY") else a['symbol']
                    # 5+ benzerlik skoru öğrenme/arka plan için hesaplanmaya devam eder;
                    # Telegram mesajında artık elmas/5+ etiketi olarak gösterilmez.
                    bes_skor, bes_nedenler = bes_plus_benzerlik_skoru(a)
                    risk = a.get('risk', 'Bilinmiyor')
                    risk = risk.replace("🟢 ", "").replace("🟡 ", "").replace("🔴 ", "")

                    # Piyasa desteği yalnız MESAJ BİLGİSİDİR; AL filtresini/skorları değiştirmez.
                    # BTC ve piyasa 3 saatlik hareketi birlikte değerlendirilir.
                    _piyasa3_anlik = statistics.median(piyasa_degisim3leri) if piyasa_degisim3leri else 0.0
                    _btc3_anlik = float(btc_d.get("3s", 0) or 0)
                    if _btc3_anlik >= 1.0 and _piyasa3_anlik >= 1.0:
                        piyasa_destek_satir = (
                            f"🌍 Piyasa desteği: 🟢 GÜÇLÜ | "
                            f"BTC 3s %{_btc3_anlik:+.2f} | Piyasa 3s %{_piyasa3_anlik:+.2f}"
                        )
                    elif _btc3_anlik <= -1.0 or _piyasa3_anlik <= -1.0:
                        piyasa_destek_satir = (
                            f"🌍 Piyasa desteği: 🔴 ZAYIF | "
                            f"BTC 3s %{_btc3_anlik:+.2f} | Piyasa 3s %{_piyasa3_anlik:+.2f}"
                        )
                    else:
                        piyasa_destek_satir = (
                            f"🌍 Piyasa desteği: 🟡 SINIRLI / YATAY | "
                            f"BTC 3s %{_btc3_anlik:+.2f} | Piyasa 3s %{_piyasa3_anlik:+.2f}"
                        )

                    # Nedenleri artık temizleyip düşürme: teknik nedenler dahil hepsi görünür.
                    # Böylece haftalık geliştirme analizinde hangi özelliklerin eşlik ettiği
                    # Telegram üzerinden de açıkça izlenebilir.
                    _neden_temiz = neden or "Belirgin önemli neden yok."

                    # Telefon ekranında daha okunaklı kompakt 2x2 düzen:
                    # her satırda en fazla iki özellik, Neden bölümü ayrı paragraf.
                    _d1 = mikro.get('d1', 0) if mikro else 0
                    _d3 = mikro.get('d3', 0) if mikro else 0
                    _d5 = mikro.get('d5', 0) if mikro else 0
                    _d10 = mikro.get('d10', 0) if mikro else 0

                    # Destek etiketi tek başına; BTC/Piyasa değerleri aşağıda 2'li satırda.
                    if _btc3_anlik >= 1.0 and _piyasa3_anlik >= 1.0:
                        _destek_etiket = "🟢 GÜÇLÜ"
                    elif _btc3_anlik <= -1.0 or _piyasa3_anlik <= -1.0:
                        _destek_etiket = "🔴 ZAYIF"
                    else:
                        _destek_etiket = "🟡 SINIRLI / YATAY"

                    # GENEL GÜÇ V1 — yalnız bilgi/öğrenme puanıdır, AL filtresine dokunmaz.
                    # Skor kalitesi %30 + momentum %25 + piyasa desteği %20 + neden kalitesi %25.
                    def _clamp100(v):
                        try:
                            return max(0.0, min(100.0, float(v)))
                        except Exception:
                            return 0.0

                    _kal_raw = _clamp100(a.get('kalicilik_skoru', 0))
                    # 95+ Kalıcılık artık "daha da güçlü" diye sınırsız ödüllendirilmez.
                    _kal_genel = 82.0 if _kal_raw >= 95 else _kal_raw

                    _skor_kalite = sum([
                        _clamp100(a.get('ai_skoru', 0)),
                        _clamp100(a.get('giris_kalitesi', 0)),
                        _clamp100(a.get('devam_gucu', 0)),
                        _kal_genel,
                    ]) / 4.0

                    # Yüzdesel momentumları ortak 0-100 ölçeğine taşı. 0%% yaklaşık nötr=50.
                    def _momentum_puani(x):
                        return _clamp100(50.0 + 12.0 * float(x or 0))
                    _momentum_kalite = (
                        0.15 * _momentum_puani(_d1) +
                        0.25 * _momentum_puani(_d3) +
                        0.30 * _momentum_puani(_d5) +
                        0.30 * _momentum_puani(_d10)
                    )

                    if _destek_etiket.startswith("🟢"):
                        _piyasa_kalite = 85.0
                    elif _destek_etiket.startswith("🔴"):
                        _piyasa_kalite = 25.0
                    else:
                        _piyasa_kalite = 55.0

                    _neden_kalite = _clamp100(_neden_kalite_agirlikli)

                    # GENEL GÜÇ V2
                    # Öncelik: Devam > 60dk göreceli güç > sağlıklı Kalıcılık bandı >
                    # hareket teyitleri > ADX > neden kalabalığı.
                    _devam_g = _clamp100(a.get("devam_gucu", 0))
                    _rel_bonus_val = float(rel_bonus or 0)
                    _rel_guc = 100.0 if _rel_bonus_val >= 2 else (65.0 if _rel_bonus_val == 1 else 25.0)

                    _kal_raw2 = _clamp100(a.get("kalicilik_skoru", 0))
                    if 88 <= _kal_raw2 <= 94:
                        _kal_bant = 100.0
                    elif 84 <= _kal_raw2 < 88:
                        _kal_bant = 75.0
                    elif 95 <= _kal_raw2 <= 97:
                        _kal_bant = 55.0
                    elif _kal_raw2 > 97:
                        _kal_bant = 35.0
                    else:
                        _kal_bant = 50.0

                    _hareket_teyit_sayisi = len(hizlar)
                    _hareket_guc = min(100.0, _hareket_teyit_sayisi * 20.0)
                    try:
                        _adx_val = float(a.get("adx", 0) or 0)
                    except Exception:
                        _adx_val = 0.0
                    _adx_guc = min(100.0, max(0.0, (_adx_val - 20.0) * 4.0))

                    # Neden adedi artık ana sürücü değil; destekleyici %10.
                    _genel_guc = round(
                        0.30 * _devam_g +
                        0.20 * _rel_guc +
                        0.18 * _kal_bant +
                        0.12 * _hareket_guc +
                        0.10 * _adx_guc +
                        0.10 * _neden_kalite
                    )
                    a["genel_guc_skoru"] = int(_genel_guc)
                    # Haftalık geliştirme motoru yalnız toplamı değil, puanı hangi blokların şişirdiğini de görsün.
                    a["genel_skor_kalite"] = round(_skor_kalite, 2)
                    a["genel_momentum_kalite"] = round(_momentum_kalite, 2)
                    a["genel_piyasa_kalite"] = round(_piyasa_kalite, 2)
                    a["genel_neden_kalite"] = round(_neden_kalite, 2)
                    a["genel_devam_bilesen"] = round(_devam_g, 2)
                    a["genel_rel_bilesen"] = round(_rel_guc, 2)
                    a["genel_kalicilik_bant"] = round(_kal_bant, 2)
                    a["genel_hareket_bilesen"] = round(_hareket_guc, 2)
                    a["genel_adx_bilesen"] = round(_adx_guc, 2)
                    a["neden_sayisi"] = int(toplam_neden_sayisi)
                    a["onemli_neden_sayisi"] = int(_onemli_neden_sayisi)
                    a["neden_agirlikli_toplam"] = round(_neden_agirlikli_toplam, 2)

                    # PİYASA DEVAM TEYİDİ V1
                    # Anlık pozitif görüntü yerine son ~60 saniyedeki devamlılığı ölçer.
                    # Sert veto değildir; sahte kırılım/geri vermede AL Gücü'nden ceza düşer.
                    def _piyasa_devam_hafiza_guncelle(btc3, piyasa3):
                        simdi_local = time.time()
                        try:
                            _PIYASA_DEVAM_HAFIZA.append({
                                "t": simdi_local,
                                "btc3": float(btc3 or 0),
                                "piyasa3": float(piyasa3 or 0),
                            })
                            alt_sinir = simdi_local - PIYASA_DEVAM_HAFIZA_SN
                            _PIYASA_DEVAM_HAFIZA[:] = [
                                x for x in _PIYASA_DEVAM_HAFIZA
                                if float(x.get("t", 0) or 0) >= alt_sinir
                            ]
                        except Exception:
                            pass

                    def _piyasa_devam_analiz(btc3, piyasa3):
                        _piyasa_devam_hafiza_guncelle(btc3, piyasa3)
                        veri = list(_PIYASA_DEVAM_HAFIZA)
                        if len(veri) < 3:
                            return {
                                "etiket": "⏳ İZLENİYOR",
                                "ceza": 0,
                                "teyit": False,
                                "geri_verme": 0.0,
                                "pozitif_oran": 0.0,
                            }

                        simdi_local = time.time()
                        son60 = [x for x in veri if simdi_local - float(x.get("t", 0) or 0) <= 60]
                        if len(son60) < 3:
                            son60 = veri[-6:]

                        btc_vals = [float(x.get("btc3", 0) or 0) for x in son60]
                        piy_vals = [float(x.get("piyasa3", 0) or 0) for x in son60]

                        pozitif = sum(1 for b, p in zip(btc_vals, piy_vals) if b > 0 and p > 0)
                        pozitif_oran = pozitif / max(1, len(son60))

                        btc_tepe = max(btc_vals)
                        piy_tepe = max(piy_vals)
                        btc_son = btc_vals[-1]
                        piy_son = piy_vals[-1]

                        btc_geri = max(0.0, btc_tepe - btc_son)
                        piy_geri = max(0.0, piy_tepe - piy_son)
                        geri_verme = max(btc_geri, piy_geri)

                        teyit = (
                            len(son60) >= 3
                            and pozitif_oran >= 0.60
                            and btc_son >= 0
                            and piy_son >= 0
                            and geri_verme < 0.35
                        )

                        ceza = 0
                        if not teyit:
                            ceza += 6
                        if pozitif_oran < 0.50:
                            ceza += 6
                        if geri_verme >= 0.25:
                            ceza += 6
                        if geri_verme >= 0.45:
                            ceza += 6
                        if btc_son < 0 and piy_son < 0:
                            ceza += 6

                        ceza = min(24, ceza)

                        if teyit:
                            etiket = "✅ TEYİTLİ"
                        elif geri_verme >= 0.45:
                            etiket = "↩️ SAHTE KIRILIM"
                        else:
                            etiket = "⚠️ TEYİTSİZ"

                        return {
                            "etiket": etiket,
                            "ceza": ceza,
                            "teyit": teyit,
                            "geri_verme": round(geri_verme, 2),
                            "pozitif_oran": round(pozitif_oran, 2),
                        }

                    # BTC ŞOK KORUMASI V1
                    # Amaç: BTC'de ani aşağı hızlanma + piyasa zayıflaması varken
                    # coin ne kadar güçlü görünürse görünsün AL gücünün yapay yüksek kalmasını önlemek.
                    # Sert veto değildir; yalnız AL Gücü puanına dinamik ceza ve görünür uyarı ekler.
                    try:
                        _btc3 = float(a.get("btc_3s", 0) or 0)
                    except Exception:
                        _btc3 = 0.0
                    try:
                        _piyasa3 = float(a.get("piyasa_3s", 0) or 0)
                    except Exception:
                        _piyasa3 = 0.0

                    _piyasa_devam = _piyasa_devam_analiz(_btc3, _piyasa3)
                    _piyasa_devam_etiket = _piyasa_devam.get("etiket", "⏳ İZLENİYOR")
                    _piyasa_devam_ceza = int(_piyasa_devam.get("ceza", 0) or 0)
                    _piyasa_geri_verme = float(_piyasa_devam.get("geri_verme", 0) or 0)
                    _piyasa_pozitif_oran = float(_piyasa_devam.get("pozitif_oran", 0) or 0)

                    # Kademeli şok skoru:
                    # BTC ve piyasa aynı anda negatife hızlanıyorsa ceza büyür.
                    _btc_sok_puani = 0
                    if _btc3 <= -0.20:
                        _btc_sok_puani += 10
                    if _btc3 <= -0.40:
                        _btc_sok_puani += 10
                    if _btc3 <= -0.70:
                        _btc_sok_puani += 10
                    if _piyasa3 <= -0.25:
                        _btc_sok_puani += 8
                    if _piyasa3 <= -0.50:
                        _btc_sok_puani += 7

                    # BTC-piyasa birlikte aşağıysa ekstra risk.
                    if _btc3 < 0 and _piyasa3 < 0:
                        _btc_sok_puani += 5

                    _btc_sok_puani = min(40, _btc_sok_puani)

                    if _btc_sok_puani >= 30:
                        _btc_sok_etiket = "🚨 BTC ŞOKU"
                    elif _btc_sok_puani >= 18:
                        _btc_sok_etiket = "⚠️ BTC ZAYIFLAMA"
                    elif _btc_sok_puani >= 8:
                        _btc_sok_etiket = "🟡 BTC BASKISI"
                    else:
                        _btc_sok_etiket = ""

                    # ERKEN YAKALAMA V1
                    # Eski Assistant'ın aday üretme hassasiyetini ayrı bir skor olarak korur.
                    # Amaç: hareketin erken fark edilmesini ölçmek; devam kalitesiyle karıştırmamak.
                    try:
                        _erken_raw = float(a.get("erken_skor", a.get("erken_skoru", 0)) or 0)
                    except Exception:
                        _erken_raw = 0.0
                    try:
                        _giris_raw = float(a.get("giris_kalitesi", 0) or 0)
                    except Exception:
                        _giris_raw = 0.0
                    try:
                        _radar_raw = float(a.get("radar_skoru", 0) or 0)
                    except Exception:
                        _radar_raw = 0.0
                    try:
                        _hacim_raw = float(a.get("hacim_kat", a.get("hacim_kat_son", 0)) or 0)
                    except Exception:
                        _hacim_raw = 0.0

                    # Hacim katkısı sınırlı; tek başına erken yakalama skorunu şişirmesin.
                    _hacim_erken = max(0.0, min(100.0, (_hacim_raw / 3.0) * 100.0))

                    # Mikro/erken kategori varsa küçük destek.
                    _kat_text = str(a.get("radar_kategori", "") or "")
                    _mikro_bonus = 100.0 if ("Mikro" in _kat_text or "Erken" in _kat_text) else 55.0

                    _erken_yakalama_puani = round(max(0, min(100,
                        0.35 * _erken_raw +
                        0.30 * _giris_raw +
                        0.20 * _radar_raw +
                        0.10 * _hacim_erken +
                        0.05 * _mikro_bonus
                    )))

                    if _erken_yakalama_puani >= 85:
                        _erken_yakalama_etiket = "⚡ ÇOK ERKEN"
                    elif _erken_yakalama_puani >= 72:
                        _erken_yakalama_etiket = "🟢 ERKEN"
                    elif _erken_yakalama_puani >= 60:
                        _erken_yakalama_etiket = "✅ ZAMANINDA"
                    else:
                        _erken_yakalama_etiket = "🟡 GEÇ / ZAYIF"

                    a["erken_yakalama_puani"] = int(_erken_yakalama_puani)
                    a["erken_yakalama_etiket"] = _erken_yakalama_etiket

                    # AL ODAĞI V1
                    # Mesajın en üstünde görünen ana kalite özeti.
                    # Neden adedi ve Genel Güç'ten bağımsızdır; videolarda daha ayırıcı görünen
                    # Devam + 60dk göreceli güç + sağlıklı Kalıcılık bandı + hareket teyidi + ADX kullanılır.
                    _al_odak_ham = (
                        0.35 * _devam_g +
                        0.25 * _rel_guc +
                        0.20 * _kal_bant +
                        0.10 * _hareket_guc +
                        0.10 * _adx_guc
                    )
                    _al_odak_puani = round(max(0, min(
                        100,
                        _al_odak_ham - _btc_sok_puani - _piyasa_devam_ceza
                    )))

                    if _al_odak_puani >= 82:
                        _al_odak_etiket = "🚀 ÇOK GÜÇLÜ"
                    elif _al_odak_puani >= 72:
                        _al_odak_etiket = "🟢 GÜÇLÜ"
                    elif _al_odak_puani >= 62:
                        _al_odak_etiket = "✅ UYGUN"
                    else:
                        _al_odak_etiket = "🟡 TEMKİNLİ"

                    a["al_odak_puani"] = int(_al_odak_puani)
                    a["al_odak_etiket"] = _al_odak_etiket
                    a["btc_sok_puani"] = int(_btc_sok_puani)
                    a["btc_sok_etiket"] = _btc_sok_etiket
                    a["piyasa_devam_ceza"] = int(_piyasa_devam_ceza)
                    a["piyasa_devam_etiket"] = _piyasa_devam_etiket
                    a["piyasa_geri_verme"] = float(_piyasa_geri_verme)
                    a["piyasa_pozitif_oran"] = float(_piyasa_pozitif_oran)

                    # V11 SADE MESAJ V1
                    # Motor/filtre/öğrenme mantığına dokunmaz; yalnız Telegram sunumunu sadeleştirir.
                    _sinyal_sira, _onceki_5 = _sinyal_sira_hazirla(a.get("symbol", ""))
                    _sira_prefix = _sira_etiketi(_sinyal_sira)
                    _onceki_5_etiket = " | Önceki +%5 ✅" if _onceki_5 else ""

                    _rsi = teknik.get("rsi")
                    _adx = teknik.get("adx")
                    _ema_yon = "Yukarı" if teknik.get("ema20") is not None and teknik.get("ema50") is not None and teknik.get("ema20") > teknik.get("ema50") else "Aşağı"
                    _macd_yon = "Pozitif" if teknik.get("macd_hist") is not None and teknik.get("macd_hist") > 0 else "Negatif"

                    _rsi_txt = "NA" if _rsi is None else f"{float(_rsi):.1f}"
                    _adx_txt = "NA" if _adx is None else f"{float(_adx):.1f}"

                    _btc_sok_satir = ""
                    if _btc_sok_etiket:
                        _btc_sok_satir = (
                            f"{_btc_sok_etiket} | BTC 3s %{_btc3:+.2f} | Piyasa 3s %{_piyasa3:+.2f}\n"
                        )

                    _geri_txt = (
                        f" | Geri verme %{_piyasa_geri_verme:.2f}"
                        if _piyasa_geri_verme > 0 else ""
                    )

                    # EN İYİ PROFİL EŞLEŞME ORANI
                    # Bu skor yalnız mesaj işaretidir; AL filtresini veya motor kararını değiştirmez.
                    _kalicilik = float(a.get("kalicilik_skoru", 0) or 0)
                    _rel = int(rel_bonus or 0)
                    _risk_yuksek = str(risk).strip().lower() == "yüksek"
                    _hacim = float(a.get("hacim", 0) or 0)
                    _adx_num = float(_adx or 0)

                    _profil_puan = 0

                    # 1) Devam Gücü — en önemli blok (20)
                    if _al_odak_puani >= 85:
                        _profil_puan += 20
                    elif _al_odak_puani >= 80:
                        _profil_puan += 16
                    elif _al_odak_puani >= 72:
                        _profil_puan += 10

                    # 2) Göreceli güç +2 (15)
                    if _rel >= 2:
                        _profil_puan += 15
                    elif _rel >= 1:
                        _profil_puan += 8

                    # 3) Sağlıklı kalıcılık 88–94 (15)
                    if 88 <= _kalicilik <= 94:
                        _profil_puan += 15
                    elif 84 <= _kalicilik <= 97:
                        _profil_puan += 8

                    # 4) Erken yakalama (10)
                    if _erken_yakalama_puani >= 72:
                        _profil_puan += 10
                    elif _erken_yakalama_puani >= 60:
                        _profil_puan += 7

                    # 5) BTC şok yok / çok düşük (10)
                    if _btc_sok_puani < 8:
                        _profil_puan += 10
                    elif _btc_sok_puani < 18:
                        _profil_puan += 6

                    # 6) Piyasa devamı (10)
                    if "TEYİTLİ" in str(_piyasa_devam_etiket):
                        _profil_puan += 10
                    elif "SAHTE KIRILIM" not in str(_piyasa_devam_etiket):
                        _profil_puan += 6

                    # 7) Risk (5)
                    if not _risk_yuksek:
                        _profil_puan += 5

                    # 8) Trend gücü / ADX (5)
                    if _adx_num >= 30:
                        _profil_puan += 5
                    elif _adx_num >= 27:
                        _profil_puan += 3

                    # 9) EMA + MACD birlikte olumlu (5)
                    if _ema_yon == "Yukarı" and _macd_yon == "Pozitif":
                        _profil_puan += 5
                    elif _ema_yon == "Yukarı" or _macd_yon == "Pozitif":
                        _profil_puan += 2

                    # 10) Hacim desteği (5)
                    if _hacim >= 3.0:
                        _profil_puan += 5
                    elif _hacim >= 1.8:
                        _profil_puan += 3

                    _profil_puan = min(100, int(round(_profil_puan)))

                    if _profil_puan >= 90:
                        _kalite_isareti = f"💎 EN İYİ PROFİLE %{_profil_puan} UYUM\n"
                    else:
                        _kalite_isareti = ""

                    # Canlı kalite seviyesinin iki V11 geçiş yolunu kaydet.
                    _beam_yolu = bool(a.get("v11_yol_asiri_rel"))
                    _hot_yolu = bool(a.get("v11_yol_temiz_momentum"))

                    # Güçlü görünmek ile erken giriş olmak aynı şey değildir.
                    # Zamanlama yalnız gerçek kısa hareket ve RSI ile ölçülür.
                    # Erken Yakalama puanı kalite sınıfına katkıdır; tek başına
                    # geç kalma vetosu değildir (AMP gibi fırsatları korur).
                    _gec_nedenleri = []
                    if float(_d5 or 0) > V11_GEC_D5_MAX:
                        _gec_nedenleri.append(f"5dk %{float(_d5):.2f}")
                    if float(_d10 or 0) > V11_GEC_D10_MAX:
                        _gec_nedenleri.append(f"10dk %{float(_d10):.2f}")
                    if _rsi is not None and float(_rsi) > V11_GEC_RSI_MAX:
                        _gec_nedenleri.append(f"RSI {float(_rsi):.1f}")

                    _gec_teyit = bool(_gec_nedenleri)
                    a["v11_gec_teyit"] = _gec_teyit
                    a["v11_gec_teyit_nedenleri"] = list(_gec_nedenleri)

                    _seviye1 = bool(
                        _beam_yolu
                        and _hot_yolu
                        and not _gec_teyit
                        and _erken_yakalama_puani >= V11_UST_DUZEY_ERKEN_MIN
                        and _ema_yon == "Yukarı"
                    )
                    _seviye2 = bool(
                        not _gec_teyit
                        and not _seviye1
                        and _ema_yon == "Yukarı"
                        and not _risk_yuksek
                        and float(a.get("ai_skoru", 0) or 0) >= V11_SEVIYE2_AI_MIN
                        and float(a.get("devam_gucu", 0) or 0) >= V11_SEVIYE2_DEVAM_MIN
                        and float(a.get("radar_skoru", 0) or 0) >= V11_SEVIYE2_RADAR_MIN
                    )

                    # KONTROLLÜ ÜST DÜZEY AL
                    # Mevcut Üst Düzey AL'ı değiştirmez; onun içinden devam,
                    # kalıcılık, trend sağlığı ve piyasa desteği birlikte uygun
                    # olanları görünür ve ayrı ölçülebilir bir alt profil yapar.
                    # Otomatik/gerçek emir üretmez.
                    _kontrollu_piyasa_uygun = bool(
                        _destek_etiket != "🔴 ZAYIF"
                        and _btc_sok_puani < 18
                        and "SAHTE KIRILIM" not in str(_piyasa_devam_etiket)
                    )
                    _kontrollu_ust_duzey = bool(
                        _seviye1
                        and _al_odak_puani >= V11_KONTROLLU_DEVAM_MIN
                        and _rel >= 2
                        and V11_KONTROLLU_KALICILIK_MIN
                        <= _kalicilik <= V11_KONTROLLU_KALICILIK_MAX
                        and _ema_yon == "Yukarı"
                        and _macd_yon == "Pozitif"
                        and _adx_num >= V11_KONTROLLU_ADX_MIN
                        and _rsi is not None
                        and V11_KONTROLLU_RSI_MIN
                        <= float(_rsi) <= V11_KONTROLLU_RSI_MAX
                        and float(_d3 or 0) > 0
                        and float(_d5 or 0) > 0
                        and _kontrollu_piyasa_uygun
                    )
                    a["v11_kontrollu_ust_duzey"] = _kontrollu_ust_duzey
                    a["v11_kontrollu_piyasa_uygun"] = _kontrollu_piyasa_uygun

                    if _gec_teyit:
                        _seviye = 0
                        _seviye_basligi = "⚠️ GEÇ TEYİT — ALMA / OTOMATİK EMİR YOK\n"
                    elif _kontrollu_ust_duzey:
                        _seviye = 1
                        _seviye_basligi = "🛡️ KONTROLLÜ ÜST DÜZEY AL\n"
                    elif _seviye1:
                        _seviye = 1
                        _seviye_basligi = "🏆 ÜST DÜZEY AL\n"
                    elif _seviye2:
                        _seviye = 2
                        _seviye_basligi = "💎 GÜÇLÜ AL\n"
                    else:
                        _seviye = 3
                        _seviye_basligi = "🌱 İZLE\n"
                    a["v11_seviye"] = int(_seviye)
                    # Seviye hesabında yalnız BEAM/HOT ve V11 kalite koşulları
                    # çalışır; başka bot teyidi kullanılmaz.
                    _yol_basligi = ""

                    if _gec_teyit:
                        _karar_gorunumu = "⚠️ İZLE / ALMA"
                    elif _seviye == 3:
                        _karar_gorunumu = "🟡 İZLE"
                    else:
                        _karar_gorunumu = "🟢 AL"
                    _gec_neden_satiri = (
                        "⏱️ Geç kalma nedeni: " + " • ".join(_gec_nedenleri) + "\n"
                        if _gec_teyit else ""
                    )

                    # Eski Assistant gibi düz ve hızlı okunur; V11'in önemli yeni bilgileri üstte kalır.
                    mesaj = (
                        f"{_seviye_basligi}{_yol_basligi}"
                        f"{_sira_prefix} {gorunen_coin} | {a.get('radar_kategori', '')} + {_karar_gorunumu}{_onceki_5_etiket}\n"\
                        f"{_kalite_isareti}\n"
                        f"{_gec_neden_satiri}"
                        f"{_btc_sok_satir}"
                        f"🎯 Devam Gücü: {_al_odak_puani}/100 | {_al_odak_etiket}\n"
                        f"⚡ Erken Yakalama: {_erken_yakalama_puani}/100 | {_erken_yakalama_etiket}\n"
                        f"🌍 Piyasa: {_destek_etiket} | Devam: {_piyasa_devam_etiket}{_geri_txt}\n"
                        f"⚡ Devam {a.get('devam_gucu', 0)} | Rel +{int(rel_bonus or 0)} | Kalıcılık {a.get('kalicilik_skoru', 0)}\n\n"
                        f"AI: {a.get('ai_skoru', 0)} | Risk: {risk}\n"
                        f"Radar: {a.get('radar_skoru', 0)}/100 | Fiyat: {round(a.get('fiyat', 0), 4)} | Hacim: {a.get('hacim', 0)}x\n"
                        f"1dk: %{_d1} | 3dk: %{_d3} | 5dk: %{_d5} | 10dk: %{_d10}\n"
                        f"BTC 3s: %{_btc3_anlik:+.2f} | Piyasa 3s: %{_piyasa3_anlik:+.2f}\n"
                        f"EMA: {_ema_yon} | RSI: {_rsi_txt} | ADX: {_adx_txt} | MACD: {_macd_yon}\n\n"
                        f"{neden_alarm}Neden: {_neden_temiz}\n"
                    )

                    if _gec_teyit:
                        # Telegram'ı doldurmaz; AL sırasına, +%5 kâr bildirimine
                        # ve gerçek-emir adaylığına girmez. Gölgede ölçülür.
                        print(
                            f"[V11 GEÇ TEYİT/GÖLGE] {symbol} | "
                            + " • ".join(_gec_nedenleri)
                        )
                        gec_teyitler.append(a)
                        top10_golge_asama_guncelle(
                            symbol,
                            "gec_teyit",
                            gec_nedenleri=list(_gec_nedenleri),
                        )
                        continue
                    # Telegram'da yalnız erken Üst Düzey/Güçlü/İzle sınıfları
                    # sade tek başlıkla gösterilir.
                    print(mesaj)
                    telegram_gonder(mesaj)
                    if _seviye == 3:
                        # Erken fakat kalite puanları henüz yeterli değil.
                        # Görünür izleme mesajıdır; canlı AL ve gerçek emir değildir.
                        erken_izleler.append(a)
                        giris_zamani_deneyi_baslat(a)
                        top10_golge_asama_guncelle(
                            symbol, "telegram_izle", telegram_izle=True, v11_seviye=3
                        )
                        continue
                    # Mesaj gönderildikten sonra sıra olayını kalıcı kayda al.
                    a["_sinyal_event_id"] = _sinyal_sira_ekle(a.get("symbol", ""), a.get("fiyat", 0))
                    # Gönderilmiş her AL için fiyat devamını izler; AL kararını değiştirmez.
                    bes_fiyat_teyit_baslat(a)
                    gonderilenler.append(a)
                    top10_golge_asama_guncelle(
                        symbol,
                        "telegram_al",
                        telegram_al=True,
                        v11_seviye=int(_seviye),
                        v11_kontrollu_ust_duzey=bool(_kontrollu_ust_duzey),
                    )

                # Yalnızca gerçekten gönderilen AL'ları +%5 kâr bildirimi ve 3 saatlik rejim öğrenmesi için takip et.
                for _a in gonderilenler:
                    al_takip_baslat(_a)
                    al_ogrenme_baslat(_a, btc_d, piyasa_fiyatlari, piyasa_medyan3, btc_giris_fiyati)
                    giris_zamani_deneyi_baslat(_a)

                # Geç teyitler yalnız gölgede üç saat ölçülür; ana canlı AL
                # başarı oranına, +%5 ara mesajına ve gerçek-emir kapısına girmez.
                for _a in gec_teyitler:
                    al_ogrenme_baslat(
                        _a,
                        btc_d,
                        piyasa_fiyatlari,
                        piyasa_medyan3,
                        btc_giris_fiyati,
                        kayit_tipi="v11_gec_teyit",
                    )

                # PUMP benzeri erken fakat düşük kaliteli adaylar kaybolmaz;
                # Telegram'da 3. Seviye olarak görünür ve gölgede ayrıca ölçülür.
                for _a in erken_izleler:
                    al_ogrenme_baslat(
                        _a,
                        btc_d,
                        piyasa_fiyatlari,
                        piyasa_medyan3,
                        btc_giris_fiyati,
                        kayit_tipi="v11_erken_izle",
                    )

        # Bu taramada eklenen kapı/teknik açıklamalarını tek yazımla kalıcılaştır.
        _top10_golge_kaydet()

        # Ana tarama 60 sn; kâr bildirimi için açık AL'lar 15 sn'de bir kontrol edilir.
        beklenen = 0
        while beklenen < TARAMA_SURESI:
            sure = min(POZISYON_TAKIP_SURESI, TARAMA_SURESI - beklenen)
            time.sleep(sure)
            beklenen += sure

            if AL_TAKIP or giris_zamani_deneyi_aktif_mi() or top10_hizli_aktif_mi():
                try:
                    r = requests.get("https://api.btcturk.com/api/v2/ticker", timeout=10)
                    r.raise_for_status()
                    _ara_ticker = r.json().get("data", [])
                    al_takip_guncelle(_ara_ticker)
                    giris_zamani_deneyi_guncelle(_ara_ticker)
                    top10_hizli_fiyat_guncelle(_ara_ticker)
                except Exception as e:
                    print("Kâr/giriş zamanı takip hatası:", e)

    except Exception as e:
        print("Bot genel hata:", e)
        time.sleep(30)
