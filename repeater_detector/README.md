# SDR Tabanlı Kaçak Repeater Tespit Sistemi

Ana projenin (`usrp_noma/`) alt projesi olarak geliştirilmiş, SDR (Yazılım Tanımlı Radyo) tabanlı kaçak repeater (tekrarlayıcı) tespit sistemidir.

## Amaç

Yetkisiz repeater cihazlarının yasal iletişim frekanslarına yarattığı girişimleri tespit etmek, sinyal kaynağına olan mesafeyi tahmin etmek ve yön bulma rehberliği sağlamak.

### Temel Yetenekler

1. **Spektrum Gözetleme ve Anomali Tespiti**: Frekans tarama, bilinen/bilinmeyen sinyal ayrıştırma, anomali skorlama
2. **RSSI Tabanlı Mesafe Tahmini**: FSPL ve Log-Distance modelleri ile sinyal kaynağına mesafe
3. **Yazılım Tabanlı Yön Bulma**: RSSI-açı profili ile sinyal kaynağının yönünü belirleme
4. **Sinyal Sınıflandırma**: FM/AM/dijital modulasyon tipi tahmini

## Çalışma Modları

| Mod | Açıklama | Kullanım |
|-----|----------|----------|
| **Simülasyon** | Sentetik sinyallerle çalışır, donanım gerektirmez | `--sim` bayrağı |
| **Dosyadan Analiz** | GNU Radio / USRP ile kaydedilmiş IQ verilerini analiz eder | `--input dosya.complex64` |
| **Donanım** | USRP E310 ile gerçek zamanlı tarama | Varsayılan (UHD gerektirir) |

## Desteklenen IQ Dosya Formatları

| Format | Uzantılar | Kaynak |
|--------|-----------|--------|
| GNU Radio cf32 | `.complex64`, `.cf32`, `.fc32` | GNU Radio File Sink |
| GNU Radio cf64 | `.cf64` | GNU Radio File Sink (64-bit) |
| NumPy | `.npy` | Proje varsayılan |
| Ham binary | `.raw`, `.bin` | Genel |
| UHD sc16 | `.s16`, `.sc16`, `.cs16` | UHD uhd_rx_cfile, RTL-SDR |

## Kurulum

Ana proje ile birlikte kurulur:

```bash
cd BitirmeProjesi
pip install -e .
```

## CLI Kullanımı

```bash
python repeater_detector/main.py [--sim] <komut> [seçenekler]
```

### Komutlar

| Komut | Açıklama | Donanım Gereksinimi |
|-------|----------|:-------------------:|
| `info` | Sistem bilgileri | Hayır |
| `scan` | Tek seferlik tarama + tespit | Evet / `--sim` / `--input` |
| `monitor` | Sürekli gözetleme | Evet / `--sim` |
| `distance` | RSSI → mesafe tahmini | Evet / `--rssi` / `--input` |
| `direction` | Yön bulma oturumu | Evet / `--sim` |
| `simulate` | Senaryo demosu | Hayır |
| `report` | Tespit raporu oluştur | Hayır |
| `path-loss` | Yol kaybı grafikleri | Hayır |

### Örnekler

#### Sistem Bilgisi
```bash
python repeater_detector/main.py --sim info
```

#### Simülasyon ile Senaryo Testi
```bash
# Tek kaçak repeater senaryosu
python repeater_detector/main.py --sim simulate --scenario tek_kacak --plot

# Çoklu kaçak repeater senaryosu
python repeater_detector/main.py --sim simulate --scenario coklu_kacak --plot

# Tüm senaryolar: temiz_spektrum, tek_kacak, coklu_kacak, zayif_kacak, yakindaki_kacak
```

#### GNU Radio Verisinden Analiz
```bash
# IQ dosyasından tarama
python repeater_detector/main.py scan --input data/capture.complex64 --freq 900e6

# IQ dosyasından mesafe tahmini
python repeater_detector/main.py distance --input data/capture.npy --freq 900e6 --env kentsel
```

#### RSSI Mesafe Tahmini (Manuel)
```bash
python repeater_detector/main.py distance --freq 900e6 --rssi -65 --env kentsel --plot
```

#### Yön Bulma (Simülasyon)
```bash
python repeater_detector/main.py --sim direction --freq 900e6 --true-angle 135 --plot
```

#### Yol Kaybı Model Karşılaştırması
```bash
python repeater_detector/main.py path-loss --freq 900e6 --save outputs/pathloss.png
```

#### Donanım ile Tarama (USRP E310)
```bash
# Tek seferlik tarama
python repeater_detector/main.py scan --band full --threshold -45

# Sürekli gözetleme (30 saniye aralıklarla)
python repeater_detector/main.py monitor --interval 30 --band full

# Yön bulma oturumu
python repeater_detector/main.py direction --freq 450e6
```

## Simülasyon Senaryoları

| Senaryo | Açıklama | Zorluk |
|---------|----------|--------|
| `temiz_spektrum` | Sadece yasal sinyaller, kaçak yok | Kolay |
| `tek_kacak` | 1 kaçak + 4 yasal sinyal | Orta |
| `coklu_kacak` | 3 kaçak + 4 yasal, farklı güç seviyeleri | Orta |
| `zayif_kacak` | Gürültüye yakın zayıf kaçak sinyal | Zor |
| `yakindaki_kacak` | Yasal frekansa çok yakın 2 kaçak | Zor |

## Ortam Modelleri (Yol Kaybı)

| Ortam | n | σ (dB) | Açıklama |
|-------|---|--------|----------|
| `serbest_uzay` | 2.0 | 0 | Engelsiz açık alan (FSPL) |
| `kirsal` | 2.5 | 3 | Kırsal / açık alan |
| `banliyo` | 2.8 | 4 | Banliyö, az yoğunluklu yerleşim |
| `kentsel` | 3.2 | 5 | Şehir içi, orta yoğunluk |
| `yogun_kentsel` | 3.8 | 7 | Yoğun şehir merkezi |
| `bina_ici` | 4.5 | 8 | Bina içi yayılım |

## Modül Yapısı

```
repeater_detector/
├── config.py                    # Türkiye operatör frekansları (36 entry), anomali eşikleri
├── utils.py                     # classify_frequency(), load_iq_file() (10 format)
├── main.py                      # CLI (8 komut, argparse)
│
├── detection/
│   ├── spectrum_surveillance.py # SpectrumSurveillance — adaptif eşik, anomali skorlama
│   └── signal_classifier.py     # SignalClassifier — FM/AM/dijital, bant genişliği tahmini
│
├── localization/
│   ├── rssi_distance.py         # RSSIDistanceEstimator — FSPL, log-distance, kalibrasyon
│   └── direction_finder.py      # DirectionFinder — polar profil, parabolik interpolasyon
│
└── simulation/
    ├── repeater_simulator.py    # RepeaterSimulator — FM/DMR sentetik sinyal üretimi
    └── scenario_generator.py    # ScenarioGenerator — 5 önceden tanımlı senaryo
```

## Anomali Tespit Algoritması

1. Frekans tarama (PSD hesabı + adaptif eşik ile tepe bulma)
2. Her tespit edilen sinyal için bilinen frekans veritabanı ile karşılaştırma
3. Eşleşmeyen sinyaller için anomali skoru hesaplama:
   - Frekans sapması (%40 ağırlık)
   - Sinyal gücü (%35 ağırlık)
   - Bant uyumu (%25 ağırlık)
4. Skor > eşik → kaçak repeater şüphesi

## Testler

```bash
# 36 birim testi (donanımsız, tümü simülasyon tabanlı)
python -m unittest tests.test_repeater_detector -v
```

Test kapsamı: config doğrulama, frekans sınıflandırma, IQ dosya okuma, RSSI dönüşüm, sinyal üretimi (FM/DMR/GSM), senaryo üretimi, spektrum gözetleme, sinyal sınıflandırma, RSSI mesafe tahmini (FSPL/log-distance/çoklu ölçüm), kalibrasyon, yön bulma (tepe bulma, pusula dönüşüm, rehberlik metni).

## Lisans

MIT License — ana proje ile aynı.
