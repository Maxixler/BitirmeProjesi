# Gerçek Hayat Uygulama Kılavuzu — Kaçak Repeater Tespit Sistemi

Bu kılavuz, SDR tabanlı kaçak repeater tespit sisteminin gerçek hayatta nasıl kullanılacağını adım adım anlatır. Donanımsız (simülasyon), GNU Radio veri dosyaları ve gerçek donanım (USRP E310) ile kullanım senaryolarını kapsar.

---

## 1. Sistem Genel Bakışı

Kaçak repeater tespit sistemi üç temel işlev sunar:

```
┌─────────────────────────────────────────────────┐
│              Veri Kaynağı                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │ USRP E310│  │GNU Radio │  │ Simülasyon   │  │
│  │ (gerçek  │  │ IQ dosya │  │ (sentetik    │  │
│  │  zaman)  │  │ (.cf32)  │  │  sinyaller)  │  │
│  └────┬─────┘  └────┬─────┘  └──────┬───────┘  │
│       │              │               │          │
│       └──────────────┼───────────────┘          │
│                      │                          │
│              ┌───────┴───────┐                  │
│              │ IQ Veri (cf32)│                  │
│              └───────┬───────┘                  │
│                      │                          │
│  ┌───────────────────┼───────────────────────┐  │
│  │           Tespit Katmanı                  │  │
│  │  ┌─────────────┐  ┌──────────────────┐   │  │
│  │  │  Spektrum   │  │ Sinyal           │   │  │
│  │  │  Gözetleme  │  │ Sınıflandırma    │   │  │
│  │  └──────┬──────┘  └────────┬─────────┘   │  │
│  │         │                  │              │  │
│  │  ┌──────┴──────────────────┴──────────┐  │  │
│  │  │        Anomali Tespit              │  │  │
│  │  │  (yasal/şüpheli ayrıştırma)        │  │  │
│  │  └────────────────┬───────────────────┘  │  │
│  └───────────────────┼──────────────────────┘  │
│                      │                          │
│  ┌───────────────────┼───────────────────────┐  │
│  │        Lokalizasyon Katmanı               │  │
│  │  ┌─────────────┐  ┌──────────────────┐   │  │
│  │  │ RSSI Mesafe │  │   Yön Bulma      │   │  │
│  │  │  Tahmini    │  │  (RSSI profil)   │   │  │
│  │  └─────────────┘  └──────────────────┘   │  │
│  └───────────────────────────────────────────┘  │
│                                                 │
│              ┌──────────────┐                   │
│              │RAPOR + GRAFİK│                   │
│              └──────────────┘                   │
└─────────────────────────────────────────────────┘
```

---

## 2. Hızlı Başlangıç: Simülasyon Modu (Donanımsız)

Simülasyon modu, sistemin tüm işlevlerini sentetik sinyallerle test etmenizi sağlar. Sunum ve savunma için idealdir.

### 2.1. Sistem Bilgilerini Görüntüleme

```bash
python repeater_detector/main.py --sim info
```

Çıktı: alt bantlar, bilinen frekans sayısı, anomali eşikleri, ortam modelleri.

### 2.2. Senaryo Bazlı Demo

```bash
# 1. Temiz spektrum — kaçak yok, tüm sinyaller yasal
python repeater_detector/main.py --sim simulate --scenario temiz_spektrum --plot

# 2. Tek kaçak — 1 kaçak repeater tespit edilmeli
python repeater_detector/main.py --sim simulate --scenario tek_kacak --plot

# 3. Çoklu kaçak — 3 kaçak, farklı güç seviyeleri
python repeater_detector/main.py --sim simulate --scenario coklu_kacak --plot

# 4. Zayıf kaçak — gürültüye yakın, tespit etmesi zor
python repeater_detector/main.py --sim simulate --scenario zayif_kacak --plot

# 5. Yakındaki kaçak — yasal frekansa çok yakın
python repeater_detector/main.py --sim simulate --scenario yakindaki_kacak --plot
```

Her komut şunları gösterir:
- Tespit edilen toplam sinyal sayısı
- Yasal / şüpheli ayrımı
- Anomali skorları ve güven seviyeleri
- Ground truth ile karşılaştırma (tespit oranı, yanlış alarm)
- `--plot` ile spektrum grafiği

### 2.3. Mesafe Tahmini Demosu

```bash
# Farklı RSSI değerleri ile mesafe tahmini
python repeater_detector/main.py distance --freq 900e6 --rssi -50 --env kentsel --plot
python repeater_detector/main.py distance --freq 900e6 --rssi -65 --env kentsel --plot
python repeater_detector/main.py distance --freq 900e6 --rssi -80 --env kirsal --plot

# Yol kaybı model karşılaştırması (6 ortam)
python repeater_detector/main.py path-loss --freq 900e6 --save results/pathloss.png
```

### 2.4. Yön Bulma Demosu

```bash
# 135° yönünden gelen sinyal — sistem bu yönü tespit etmeli
python repeater_detector/main.py --sim direction --freq 900e6 --true-angle 135 --plot

# 45° yönünden gelen sinyal
python repeater_detector/main.py --sim direction --freq 900e6 --true-angle 45 --plot

# Çıktılar:
#   - 36 noktada RSSI ölçümleri (tablo + ASCII bar)
#   - Tespit edilen sinyal yönü (derece + pusula yönü)
#   - Güven skoru, hüzme genişliği, dinamik aralık
#   - Kutupsal RSSI diyagramı (--plot ile)
```

---

## 3. GNU Radio IQ Verileriyle Çalışma

### 3.1. GNU Radio'da Veri Kaydetme

GNU Radio Companion (GRC) üzerinden bir flow graph oluşturun:

**Yöntem A: Doğrudan UHD ile Kayıt**
```
UHD: USRP Source → File Sink
```

UHD Source ayarları:
- Device Address: `addr=192.168.10.2`
- Samp Rate: `1e6`
- Center Freq: `900e6`
- Gain: `40`

File Sink ayarları:
- File: `/home/user/captures/scan_900mhz.complex64`
- Output Type: Complex Float32

**Yöntem B: UHD rx_samples_to_file**
```bash
# UHD komut satırı aracı ile doğrudan yakalama
uhd_rx_cfile --freq 900e6 --rate 1e6 --gain 40 --nsamps 1000000 \
    /home/user/captures/scan_900mhz.complex64
```

### 3.2. Kaydedilen Veriyi Analiz Etme

```bash
# Spektrum tarama ve anomali tespiti
python repeater_detector/main.py scan \
    --input data/scan_900mhz.complex64 \
    --freq 900e6 \
    --plot

# Çıktı: tespit edilen sinyaller, yasal/şüpheli sınıflandırma, anomali skorları, grafik
```

### 3.3. Farklı Frekans Bantlarından Kayıtlar

```bash
# GSM 900 bant taraması
python repeater_detector/main.py scan \
    --input data/gsm900_capture.fc32 \
    --freq 900e6

# LTE 1800 bant taraması
python repeater_detector/main.py scan \
    --input data/lte1800_capture.complex64 \
    --freq 1842e6

# UMTS 2100 bant taraması
python repeater_detector/main.py scan \
    --input data/umts2100_capture.npy \
    --freq 2140e6
```

### 3.4. Mesafe Tahmini (IQ Verisinden)

```bash
# IQ verisinden RSSI hesapla ve mesafe tahmin et
python repeater_detector/main.py distance \
    --input data/suspect_signal.complex64 \
    --freq 900e6 \
    --env kentsel \
    --plot
```

---

## 4. Gerçek Donanım ile Saha Çalışması

### 4.1. Hazırlık

```bash
# 1. USRP bağlantısını doğrula
python repeater_detector/main.py info

# 2. Anten bağlantısını kontrol et
#    - RX2 portuna omni-directional anten bağlı olmalı
#    - SMA konektör sıkı olmalı
```

### 4.2. Saha Taraması — Kaçak Repeater Arama

#### Adım 1: Geniş Bant Tarama

```bash
# Tüm frekans bantlarını tara
python repeater_detector/main.py scan --band full --threshold -45 --plot

# Belirli alt bant tarama
python repeater_detector/main.py scan --band "698-960 MHz" --threshold -45
python repeater_detector/main.py scan --band "1710-1800 MHz"
python repeater_detector/main.py scan --band "1800-2100 MHz"
python repeater_detector/main.py scan --band "2100-2700 MHz"
```

#### Adım 2: Şüpheli Sinyal Tespiti

Tarama sonucunda şüpheli sinyal tespit edilirse:
- **Anomali skoru > 0.6**: Yüksek ihtimalle kaçak repeater
- **Anomali skoru 0.3-0.6**: Dikkatli inceleme gerekir
- **Anomali skoru < 0.3**: Muhtemelen yasal kaynaklı

```bash
# Şüpheli frekans civarında daha detaylı tarama
python repeater_detector/main.py scan \
    --freq 450e6 --rate 2e6 --duration 5 --plot
```

#### Adım 3: Sürekli Gözetleme

Şüpheli bölgede sürekli izleme başlatın:

```bash
# 30 saniye aralıklarla sürekli tarama
python repeater_detector/main.py monitor --interval 30 --band full

# Ctrl+C ile durdurun
```

### 4.3. Mesafe Tahmini

Şüpheli sinyalin RSSI değerini kullanarak kaynağa olan mesafeyi tahmin edin:

```bash
# Otomatik: IQ verisinden RSSI hesapla
python repeater_detector/main.py distance \
    --freq 900e6 --input data/suspect.npy --env kentsel --plot

# Manuel: Tarama sonucundaki RSSI değerini girin
python repeater_detector/main.py distance \
    --freq 450e6 --rssi -55 --env yogun_kentsel --plot
```

Mesafe tahmini sonuçlarını yorumlama:
- **FSPL modeli**: İdeal (engelsiz) koşul tahmini — genellikle gerçekten uzak
- **Log-distance modeli**: Ortam parametrelerine göre daha gerçekçi tahmin
- **Güven aralığı**: min–max mesafe aralığı (shadowing etkisi)

### 4.4. Yön Bulma

Şüpheli sinyal tespit edildikten sonra kaynağın yönünü belirleyin:

```bash
# İnteraktif yön bulma oturumu
python repeater_detector/main.py direction --freq 450e6

# Adımlar:
# 1. Sistem 36 yönde (her 10°'de) RSSI ölçümü ister
# 2. Anteni belirtilen yöne çevirin, ENTER'a basın
# 3. Tüm ölçümler tamamlandığında sinyal yönü rapor edilir
```

#### Yön Bulma Prosedürü

```
         0° (Kuzey)
          │
   315°   │   45°
     \    │    /
      \   │   /
       \  │  /
270° ────┼──── 90°
       /  │  \
      /   │   \
     /    │    \
   225°   │   135°
          │
       180° (Güney)

1. Başlangıç noktası: Kuzey'e (0°) bakın
2. Saat yönünde her 10°'de ölçüm alın
3. 36 ölçüm sonunda sistem yönü raporlar
```

**Dikkat**: Yansımalar (multipath) birden fazla tepe yaratabilir. Sistem ikincil tepe noktalarını da raporlar.

### 4.5. Kalibrasyon (Doğruluk Artırma)

Bilinen bir vericiyle sistemi kalibre ederek mesafe tahmininin doğruluğunu artırın:

```bash
# Bilinen mesafeden (100 m) ve ölçülen RSSI ile kalibrasyon
python repeater_detector/main.py distance \
    --freq 900e6 --rssi -55 --env kentsel \
    --calibrate --cal-distance 100 --cal-rssi -55
```

---

## 5. Raporlama ve Çıktılar

### 5.1. Tespit Raporu Oluşturma

```bash
# JSON ve metin raporu
python repeater_detector/main.py report \
    --input results/repeater_reports/scan.json \
    --output results/repeater_reports/rapor.txt
```

### 5.2. Grafik Çıktıları

Sistem şu grafikleri üretir:

| Grafik | Komut | Açıklama |
|--------|-------|----------|
| Spektrum + Anomali | `scan --plot` | PSD grafiği + şüpheli sinyal işaretleri |
| Mesafe Tahmini | `distance --plot` | FSPL vs Log-distance + güven aralığı |
| Yol Kaybı Karşılaştırma | `path-loss` | 6 ortam modeli karşılaştırma |
| Kutupsal RSSI | `direction --plot` | 360° RSSI profili |
| Kartezyen RSSI | `direction --plot` | RSSI vs açı grafiği |

### 5.3. Çıktı Dosya Konumları

```
results/repeater_reports/
├── sim_tek_kacak.png               # Simülasyon grafikleri
├── sim_coklu_kacak.png
├── distance_estimate.png           # Mesafe tahmini grafiği
├── direction_polar.png             # Kutupsal RSSI diyagramı
├── direction_polar_cartesian.png   # Kartezyen RSSI grafiği
├── detections_20260315_143025.csv  # Tespit sonuçları (CSV)
└── detections_20260315_143025.json # Tespit sonuçları (JSON)
```

---

## 6. Tipik Saha Operasyonu İş Akışı

```
┌──────────────────────────────────┐
│ 1. GENİŞ BANT TARAMA            │
│    scan --band full              │
│    → Tüm bantları tara          │
│    → Şüpheli sinyalleri listele │
└──────────┬───────────────────────┘
           │ Şüpheli sinyal var mı?
           │
     ┌─────┴─────┐
     │ EVET      │ HAYIR → Son
     └─────┬─────┘
           │
┌──────────┴───────────────────────┐
│ 2. DETAYLI ANALİZ               │
│    scan --freq 450e6             │
│    → Dar bant detaylı tarama    │
│    → Anomali skoru hesapla      │
│    → Sinyal tipi sınıflandır    │
└──────────┬───────────────────────┘
           │
┌──────────┴───────────────────────┐
│ 3. MESAFE TAHMİNİ               │
│    distance --rssi -55           │
│    → FSPL ve log-distance       │
│    → Tahmini mesafe aralığı     │
└──────────┬───────────────────────┘
           │
┌──────────┴───────────────────────┐
│ 4. YÖN BULMA                    │
│    direction --freq 450e6        │
│    → 36 noktada RSSI ölçümü     │
│    → Sinyal yönü tespiti        │
│    → "Saat yönünde X° dönün"    │
└──────────┬───────────────────────┘
           │
┌──────────┴───────────────────────┐
│ 5. YAKLAŞMA                     │
│    → Yön bulma tekrarla         │
│    → RSSI arttıkça yaklaşıyor   │
│    → Mesafe tahmini güncelle    │
└──────────┬───────────────────────┘
           │
┌──────────┴───────────────────────┐
│ 6. RAPORLAMA                    │
│    report --output rapor.txt     │
│    → Tespit sonuçları           │
│    → Frekans, güç, konum        │
│    → Zaman bilgisi              │
└──────────────────────────────────┘
```

---

## 7. İpuçları ve En İyi Uygulamalar

### 7.1. Ölçüm Ortamı

- Ölçüm noktasını açık alanda, bina gölgesinden uzakta seçin
- Anteni zemine dik tutun (omni-directional anten için)
- Yön bulma sırasında anteni yavaş ve düzgün döndürün
- Her noktada en az 0.5 saniye bekleyin (varsayılan)

### 7.2. Frekans Seçimi

| Hedef | Taranacak Bant | Neden |
|-------|----------------|-------|
| GSM kaçak repeater | 698-960 MHz | GSM 900 bant |
| LTE kaçak repeater | 1710-2100 MHz | LTE Band 3, 7 |
| Telsiz/PMR | 440-470 MHz | UHF PMR bant |
| WiFi repeater | 2400-2500 MHz | 2.4 GHz WiFi |

### 7.3. Ortam Modeli Seçimi

| Ortam | Model | Tipik Kullanım |
|-------|-------|----------------|
| Açık alan, görüş hattı var | `serbest_uzay` | Kırsal ölçüm |
| Tarla, az yapı | `kirsal` | Kırsal alan |
| Banliyö yerleşim | `banliyo` | Konut bölgesi |
| Şehir içi | `kentsel` | Cadde kenarı |
| Şehir merkezi | `yogun_kentsel` | AVM, gökdelen |
| Bina içi | `bina_ici` | Kapalı alan |

### 7.4. Sonuçları Doğrulama

- Aynı ölçümü birden fazla kez tekrarlayın
- Farklı konumlardan ölçüm alıp karşılaştırın
- Çoklu RSSI ölçümü ile mesafe tahmin doğruluğunu artırın:

```bash
# 5 farklı RSSI ölçümünün ortalaması ile mesafe tahmin et
python repeater_detector/main.py distance \
    --freq 900e6 --rssi -55,-57,-53,-56,-54 --env kentsel
```

---

## 8. Sık Karşılaşılan Senaryolar

### Senaryo A: "Operatör Şikayeti — GSM 900 Bandında Girişim"

```bash
# 1. 900 MHz bandını tara
python repeater_detector/main.py scan \
    --freq 900e6 --rate 2e6 --duration 5 --plot

# 2. Şüpheli sinyal varsa mesafe tahmin et
python repeater_detector/main.py distance \
    --freq 900e6 --rssi -48 --env kentsel --plot

# 3. Yön bul
python repeater_detector/main.py direction --freq 900e6

# 4. Rapor oluştur
python repeater_detector/main.py report --output rapor_gsm900.txt
```

### Senaryo B: "Bir Önceki GNU Radio Kaydını Analiz Et"

```bash
# GNU Radio ile daha önce kaydedilmiş veriyi analiz et
python repeater_detector/main.py scan \
    --input data/previous_capture.complex64 \
    --freq 900e6 --plot

# Aynı veriyi ana proje ile detaylı analiz
python main.py spectrum --input data/previous_capture.complex64 --freq 900e6
python main.py analyze-data --input data/previous_capture.complex64 --freq 900e6
```

### Senaryo C: "Sunum / Tez Savunması Demosu"

```bash
# Terminal 1: Tüm senaryoları sırayla çalıştır
python repeater_detector/main.py --sim simulate --scenario temiz_spektrum --plot
python repeater_detector/main.py --sim simulate --scenario tek_kacak --plot
python repeater_detector/main.py --sim simulate --scenario coklu_kacak --plot

# Terminal 2: Mesafe tahmini demosu
python repeater_detector/main.py distance --freq 900e6 --rssi -65 --env kentsel --plot
python repeater_detector/main.py path-loss --freq 900e6 --save pathloss_demo.png

# Terminal 3: Yön bulma demosu
python repeater_detector/main.py --sim direction --freq 900e6 --true-angle 135 --plot
```
