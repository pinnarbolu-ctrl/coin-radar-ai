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

STRATEJI_SURUMU = "V11_ERKEN_YAKALA_DEVAM_GUCU"

# 24 saatlik +%5 yakalama başarı raporu
YUZDE5_RAPOR_ARALIGI = 24 * 60 * 60
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
    """Her 24 saatte yalnız bu strateji sürümünün +%5 yakalama oranını raporlar."""
    global _YUZDE5_META
    simdi = time.time()
    son_rapor = float(_YUZDE5_META.get("son_rapor", _YUZDE5_META.get("baslangic", simdi)) or simdi)
    if simdi - son_rapor < YUZDE5_RAPOR_ARALIGI:
        return

    pencere_bas = son_rapor
    pencere_son = simdi

    # Bu 24 saat içinde başlayan, bu strateji sürümüne ait sinyaller.
    tum = [
        x for x in AL_OGRENME_KAYITLARI
        if x.get("strateji_surumu") == STRATEJI_SURUMU
        and pencere_bas <= float(x.get("zaman", 0) or 0) < pencere_son
    ]

    tamam = [x for x in tum if x.get("tamamlandi")]
    acik = [x for x in tum if not x.get("tamamlandi")]
    basarili = [x for x in tamam if float(x.get("max_getiri", 0) or 0) >= 5.0]
    basarisiz = [x for x in tamam if float(x.get("max_getiri", 0) or 0) < 5.0]

    oran = (len(basarili) / len(tamam) * 100.0) if tamam else 0.0
    ort_tepe = (
        sum(float(x.get("max_getiri", 0) or 0) for x in tamam) / len(tamam)
        if tamam else 0.0
    )

    mesaj = (
        f"📊 24 SAATLİK +%5 YAKALAMA RAPORU — {YUZDE5_RAPOR_ETIKETI}\n\n"
        f"Tamamlanan sinyal: {len(tamam)}\n"
        f"+%5 yapan: {len(basarili)}\n"
        f"+%5 yapamayan: {len(basarisiz)}\n"
        f"🎯 +%5 başarı: %{oran:.1f}\n"
        f"Ortalama tepe getiri: %{ort_tepe:+.2f}\n"
        f"Henüz tamamlanmayan: {len(acik)}\n\n"
        f"Not: Başarı = AL fiyatından sonra izleme süresi içinde en az +%5 tepe görmek."
    )
    print(mesaj)
    telegram_gonder(mesaj)

    _YUZDE5_META["son_rapor"] = simdi
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
    }


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
            p["kar_bildirildi"] = True
            _sinyal_sira_hit5_isaretle(symbol, p.get("sinyal_event_id"))
            mesaj = (
                f"💰 +%5 KÂR BÖLGESİ - {kalin_coin_yazisi(symbol[:-3] if symbol.endswith('TRY') else symbol)}\n"
                f"İlk AL: {giris:.4f} | Güncel: {fiyat:.4f}\n"
                f"Getiri: %{getiri:+.2f}\n"
                f"Not: Çık emri değil; kârı değerlendirmek / çıkışa hazırlanmak için ara uyarı."
            )
            print(mesaj)
            telegram_gonder(mesaj)

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


def al_ogrenme_baslat(aday, btc_d, piyasa_fiyatlari, piyasa_medyan3, btc_giris):
    symbol = aday.get("symbol")
    giris = float(aday.get("fiyat", 0) or 0)
    if not symbol or giris <= 0:
        return

    # Aynı aktif AL için ikinci öğrenme kaydı açma.
    for k in reversed(AL_OGRENME_KAYITLARI[-100:]):
        if k.get("symbol") == symbol and not k.get("tamamlandi"):
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
    tamam = [x for x in AL_OGRENME_KAYITLARI if x.get("tamamlandi") and x.get("son_getiri") is not None]
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
        oneriler.append({
            "puan":abs(fark),"eylem":eylem,"ozellik":ad,"rejim":"TÜM PİYASA",
            "aciklama":f"{ad} >= {esik:.2f} grubunda +%5 başarı %{ru:.1f}; altında %{ra:.1f} (n={nu}/{na}).",
            "kod":kod_aciklama,"guven":guven
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
    son7_tumu = [x for x in AL_OGRENME_KAYITLARI if x.get("tamamlandi") and float(x.get("tamamlanma_zamani", 0) or 0) > 0 and simdi - float(x.get("tamamlanma_zamani", 0) or 0) <= GELISTIRME_PENCERE]

    # Eski veriyi silme; ama yeterli V7 örneği birikince haftalık öneriyi
    # yalnız mevcut strateji sürümünden üret. Böylece kod değişikliği raporu bozmaz.
    son7_mevcut = [x for x in son7_tumu if x.get("strateji_surumu") == STRATEJI_SURUMU]
    son7 = son7_mevcut if len(son7_mevcut) >= GELISTIRME_MIN_KAYIT else son7_tumu

    if len(son7) < GELISTIRME_MIN_KAYIT:
        return
    oneriler = _gelistirme_onerileri_uret(son7)
    mesaj_onerileri = _mesaj_gelistirme_onerileri(son7, oneriler)
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
    SON_GELISTIRME_RAPOR_ZAMANI = simdi
    _gelistirme_son_zaman_kaydet(simdi)


AL_OGRENME_KAYITLARI = _al_ogrenme_yukle()


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
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

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
        except Exception as e:
            print(chat_id, e)


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


# Railway deploy / yeniden baslatma kontrolu: Telegram baglantisini aninda dogrula.
telegram_gonder("✅ RADAR başladı ve aktif. Tarama başlıyor.")

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

                if not tam_tarama and abs(hizli_degisim) < HIZLI_HAREKET_ESIGI and not havuzda:
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

                # Klasik aday değilse bile Mikro Ön Alarm teknik ön havuza sokabilir.
                # Asıl adaylık biraz aşağıda gerçek 1-3-5-10 dk verisiyle doğrulanır.
                if not assistant_ana_aday and not mikro_on_alarm:
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

        # Mikro ön alarmdan gelip teyit alamayanları teknik API çağrısından önce çıkar.
        top10 = [
            a for a in top10
            if a.get("assistant_ana_aday") and not a.get("mikro_on_alarm_reddedildi")
        ]

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

            for a in top10:
                symbol = a["symbol"]
                karar = a.get("karar", "🟡 BEKLE")
                onceki_karar = son_ai_kararlar.get(symbol)
                son_ai_kararlar[symbol] = karar

                # Telegram yalnızca gerçek AL kararlarında konuşur.
                # BEKLE ve SAT/PAS arka planda/loglarda izlenmeye devam eder.
                if "🟢 AL" not in karar:
                    continue

                # Aynı AL kararını tekrar gönderme.
                if onceki_karar == karar:
                    continue

                gonderilecekler.append(a)

            if not gonderilecekler:
                print("Yeni AL kararı yok. Telegram sessiz.")
            else:
                # Her coin Telegram'a AYRI mesaj olarak gider.
                # Böylece aynı taramada bulunan coinler tek uzun mesajda birleşmez.
                gonderilenler = []

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

                    # İki ana sütun: solda Skorlar / sağda Piyasa; altta Momentum.
                    # Her sütunun kendi bilgileri alt alta kalır.
                    _sol1 = [
                        f"AI {a.get('ai_skoru', 0)}",
                        f"Risk {risk}",
                        f"Erken {a.get('erken_puan', 0)}",
                        f"Giriş {a.get('giris_kalitesi', 0)}",
                        f"Devam {a.get('devam_gucu', 0)}",
                        f"Kalıcılık {a.get('kalicilik_skoru', 0)}",
                        f"Öğrenme {a.get('ogrenme_uyum', 0)}",
                    ]
                    _sag1 = [
                        f"Fiyat {round(a['fiyat'], 4)}",
                        f"Hacim {a['hacim']}x",
                        f"Radar {a['radar_skoru']}/100",
                        f"BTC 3s %{_btc3_anlik:+.2f}",
                        f"Piyasa 3s %{_piyasa3_anlik:+.2f}",
                        f"Destek {_destek_etiket}",
                    ]
                    _sol2 = [
                        f"1dk %{_d1}",
                        f"3dk %{_d3}",
                        f"5dk %{_d5}",
                        f"10dk %{_d10}",
                    ]
                    # Teknik göstergeler sütunda tekrar gösterilmez.
                    # EMA / RSI / ADX / MACD ile ilgili en fazla 4 teknik neden zaten
                    # a["nedenler"] içinde bulunur ve aşağıdaki Neden bölümünde görünür.

                    def _iki_sutun_baslik_ve_satirlar(sol_baslik, sag_baslik, sol, sag, genislik=18):
                        # Telegram normal yazı tipi orantılı olduğu için boşluklarla sütunlar kayıyordu.
                        # Bu blok HTML <pre> içinde monospace gönderilir; sağ sütun her satırda aynı hizada başlar.
                        sat = [f"{sol_baslik:<{genislik}}│ {sag_baslik}"]
                        n = max(len(sol), len(sag))
                        for i in range(n):
                            l = sol[i] if i < len(sol) else ""
                            r = sag[i] if i < len(sag) else ""
                            sat.append(f"{l:<{genislik}}│ {r}")
                        return "\n".join(sat)

                    _blok_ust = _iki_sutun_baslik_ve_satirlar("📊 SKORLAR", "📈 PİYASA", _sol1, _sag1)
                    # Alt bölüm artık yalnız momentumdur; Teknik tekrarları Neden kısmındadır.
                    _blok_alt = "⏱ MOMENTUM\n" + "\n".join(_sol2)

                    # Aynı coin 48 saat içinde yeniden AL verirse sıra numarası devam eder.
                    # 48 saatten eski geçmiş yeni döngü sayılır ve tekrar 1️⃣ başlar.
                    _sinyal_sira, _onceki_5 = _sinyal_sira_hazirla(a.get("symbol", ""))
                    _sira_prefix = _sira_etiketi(_sinyal_sira)
                    _onceki_5_etiket = " | Önceki +%5 ✅" if _onceki_5 else ""

                    # Yalnız bu AL mesajı HTML olarak gönderilir. Dinamik alanlar escape edilir.
                    # Böylece <pre> bloğunda iki sütun gerçekten düz görünür; diğer Telegram mesajlarına dokunulmaz.
                    mesaj_html = (
                        f"{html.escape(_sira_prefix)} {html.escape(kalin_coin_yazisi(gorunen_coin))} | {html.escape(str(a.get('radar_kategori', '')))} + 🟢 AL{html.escape(_onceki_5_etiket)}\n\n"
                        f"{(html.escape(_btc_sok_etiket) + ' | ' + 'BTC 3s ' + format(_btc3, '+.2f') + '% | Piyasa 3s ' + format(_piyasa3, '+.2f') + '%' + chr(10)) if _btc_sok_etiket else ''}"
                        f"🌍 Piyasa Devamı: {html.escape(_piyasa_devam_etiket)}"
                        f"{(' | Geri verme ' + format(_piyasa_geri_verme, '.2f') + '%') if _piyasa_geri_verme > 0 else ''}\n"
                        f"⚡ ERKEN YAKALAMA: {_erken_yakalama_puani}/100 | {html.escape(_erken_yakalama_etiket)}\n"
                        f"🎯 DEVAM GÜCÜ: {_al_odak_puani}/100 | {html.escape(_al_odak_etiket)}\n"
                        f"⚡ Devam {a.get('devam_gucu', 0)} | Rel +{int(rel_bonus or 0)} | Kalıcılık {a.get('kalicilik_skoru', 0)}\n"
                        f"🔥 Genel Güç: {_genel_guc}/100 | 🌍 Piyasa: {html.escape(_destek_etiket)}\n\n"
                        f"<pre>{html.escape(_blok_ust)}</pre>\n"
                        f"<pre>{html.escape(_blok_alt)}</pre>\n"
                        f"{html.escape(neden_alarm)}📌 Önemli Neden ({_onemli_neden_sayisi}/7): {html.escape(_neden_temiz)}\n"
                    )

                    # Konsolda düz metin; Telegram'da hizalı monospace sütun.
                    mesaj = (
                        f"{_sira_prefix} {kalin_coin_yazisi(gorunen_coin)} | {a.get('radar_kategori', '')} + 🟢 AL{_onceki_5_etiket}\n\n"
                        f"{(_btc_sok_etiket + ' | BTC 3s ' + format(_btc3, '+.2f') + '% | Piyasa 3s ' + format(_piyasa3, '+.2f') + '%' + chr(10)) if _btc_sok_etiket else ''}"
                        f"🌍 Piyasa Devamı: {_piyasa_devam_etiket}"
                        f"{(' | Geri verme ' + format(_piyasa_geri_verme, '.2f') + '%') if _piyasa_geri_verme > 0 else ''}\n"
                        f"⚡ ERKEN YAKALAMA: {_erken_yakalama_puani}/100 | {_erken_yakalama_etiket}\n"
                        f"🎯 DEVAM GÜCÜ: {_al_odak_puani}/100 | {_al_odak_etiket}\n"
                        f"⚡ Devam {a.get('devam_gucu', 0)} | Rel +{int(rel_bonus or 0)} | Kalıcılık {a.get('kalicilik_skoru', 0)}\n"
                        f"🔥 Genel Güç: {_genel_guc}/100 | 🌍 Piyasa: {_destek_etiket}\n\n"
                        f"{_blok_ust}\n\n"
                        f"{_blok_alt}\n\n"
                        f"{neden_alarm}📌 Önemli Neden ({_onemli_neden_sayisi}/7): {_neden_temiz}\n"
                    )
                    print(mesaj)
                    telegram_gonder(mesaj_html, parse_mode="HTML")
                    # Mesaj gönderildikten sonra sıra olayını kalıcı kayda al.
                    a["_sinyal_event_id"] = _sinyal_sira_ekle(a.get("symbol", ""), a.get("fiyat", 0))
                    # Gönderilmiş her AL için fiyat devamını izler; AL kararını değiştirmez.
                    bes_fiyat_teyit_baslat(a)
                    gonderilenler.append(a)

                # Yalnızca gerçekten gönderilen AL'ları +%5 kâr bildirimi ve 3 saatlik rejim öğrenmesi için takip et.
                piyasa_medyan3 = statistics.median(piyasa_degisim3leri) if piyasa_degisim3leri else 0.0
                btc_giris_fiyati = ticker_fiyat_haritasi.get("BTCTRY", 0)
                for _a in gonderilenler:
                    al_takip_baslat(_a)
                    al_ogrenme_baslat(_a, btc_d, piyasa_fiyatlari, piyasa_medyan3, btc_giris_fiyati)

        # Ana tarama 60 sn; kâr bildirimi için açık AL'lar 15 sn'de bir kontrol edilir.
        beklenen = 0
        while beklenen < TARAMA_SURESI:
            sure = min(POZISYON_TAKIP_SURESI, TARAMA_SURESI - beklenen)
            time.sleep(sure)
            beklenen += sure

            if AL_TAKIP:
                try:
                    r = requests.get("https://api.btcturk.com/api/v2/ticker", timeout=10)
                    r.raise_for_status()
                    al_takip_guncelle(r.json().get("data", []))
                except Exception as e:
                    print("Kâr bildirim takip hatası:", e)

    except Exception as e:
        print("Bot genel hata:", e)
        time.sleep(30)
