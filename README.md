# USRP E310 ile LoRaWAN Sinyal Analizi ve NOMA Çoklu Erişim Projesi

Bu proje, **USRP E310** Yazılım Tanımlı Radyo (SDR) platformu kullanarak **LoRaWAN 868 MHz** sinyallerinin yakalanması, analiz edilmesi ve **NOMA (Non-Orthogonal Multiple Access)** çoklu erişim tekniğinin uygulanmasını kapsamaktadır.

Proje iki ana bileşenden oluşur:
1. **Ana Proje (`usrp_noma/`)**: SDR kontrol, sinyal analizi, LoRa demodülasyon, NOMA simülasyon ve deep learning sınıflandırma
2. **Alt Proje (`repeater_detector/`)**: Kaçak repeater tespit sistemi — spektrum gözetleme, RSSI mesafe tahmini, yön bulma

## Proje Hedefi

- LoRa modülünden gelen 868 MHz sinyallerini USRP E310 ile yakalama ve demodüle etme
- 698–960 MHz ve 1710–2700 MHz frekans bantlarında geniş bant tarama
- NOMA (Superposition Coding + SIC) ile çoklu kullanıcı erişimi simülasyonu ve gerçek zamanlı testi
- NOMA vs OMA performans karşılaştırması (BER, kapasite, throughput)
- Deep Learning ile sinyal tipi sınıflandırma (LoRa, NOMA, CW, OFDM, gürültü)
- Kaçak repeater tespiti, frekans anomali analizi ve lokalizasyon (alt proje)

## Donanım

| Bileşen | Model | Açıklama |
|---------|-------|----------|
| **SDR** | USRP E310 (Embedded) | AD9361 RF çip, 70 MHz–6 GHz, alıcı/verici |
| **LoRa Modülü** | Ebyte E220-900T22D | 868–915 MHz, 22 dBm, LLCC68 |
| **Anten** | MRTK-Q7027I28 | 7 dBi, SMA, 698–960 / 1710–2700 MHz |
| **Host PC** | Linux veya Windows | Ethernet ile bağlı |
| **Bağlantı** | Ethernet + USB-Seri | Veri akışı + konsol |

## Yazılım Gereksinimleri

- **Python 3.8+**
- **UHD** (USRP Hardware Driver) — donanım ile çalışırken gerekli
- Python paketleri:

```bash
pip install -r requirements.txt
```

`requirements.txt` içeriği:
```
numpy>=1.21.0
scipy>=1.7.0
matplotlib>=3.4.0
pyzmq>=22.0.0
torch>=1.12.0
scikit-learn>=1.0.0
pandas>=1.3.0
```

## Proje Yapısı

```
BitirmeProjesi/
│
├── main.py                         # Ana CLI giriş noktası (15 alt komut)
├── setup.py                        # Paket kurulum dosyası
├── requirements.txt                # Python bağımlılıkları
├── .gitignore
├── LICENSE                         # MIT Lisans
├── README.md                       # Bu dosya
├── PROJE_RAPORU.md                 # Detaylı akademik proje raporu
├── CLAUDE_PROJECT_CONTEXT.md       # AI bağlam dokümanı
│
├── docs/                           # Dokümanlar
│   ├── antenbilgisi.txt            # Anten veri sayfası
│   ├── walkthrough_anaproje.md     # Ana proje gerçek hayat kılavuzu
│   └── walkthrough_detector.md     # Repeater detector gerçek hayat kılavuzu
│
├── data/                           # IQ veri dosyaları (.npy, .complex64 vb.)
├── results/                        # Çıktı grafikleri, modeller, CSV dosyaları
│
├── tests/                          # Birim testleri
│   ├── test_project.py             # Ana proje testleri (21 test)
│   └── test_repeater_detector.py   # Repeater detector testleri (36 test)
│
├── usrp_noma/                      # Ana Python paketi
│   ├── __init__.py
│   ├── config.py                   # Merkezi konfigürasyon
│   ├── utils.py                    # Yardımcı fonksiyonlar + GNU Radio format desteği
│   │
│   ├── core/                       # Donanım etkileşim katmanı
│   │   ├── usrp_controller.py      # UHD ile USRP E310 cihaz yönetimi
│   │   ├── signal_capture.py       # IQ veri yakalama
│   │   └── signal_generator.py     # Test sinyali üretimi
│   │
│   ├── analysis/                   # Sinyal analiz katmanı
│   │   ├── spectrum_analyzer.py    # FFT/Welch PSD spektrum analizi
│   │   ├── waterfall_display.py    # Waterfall diyagramı
│   │   ├── frequency_scanner.py    # Geniş bant frekans tarama
│   │   ├── data_analysis.py        # IQ veri analizi, 25 özellik çıkarımı
│   │   └── synthetic_data.py       # Sentetik IQ veri üretimi
│   │
│   ├── deep_learning/              # Deep Learning sinyal sınıflandırma
│   │   ├── models.py               # 1D CNN ve ResNet modelleri
│   │   └── trainer.py              # Eğitim/tahmin pipeline
│   │
│   ├── lora/                       # LoRa demodülasyon katmanı
│   │   └── decoder.py              # LoRa CSS demodülasyon
│   │
│   ├── noma/                       # NOMA çoklu erişim katmanı
│   │   ├── modulation.py           # Konstelasyon tabloları (QPSK, 16QAM, 64QAM)
│   │   ├── transmitter.py          # Superposition Coding verici
│   │   ├── receiver.py             # SIC alıcı
│   │   └── analyzer.py             # Monte Carlo simülasyon ve analiz
│   │
│   └── streaming/                  # ZMQ veri akış katmanı
│       └── zmq_streamer.py         # GNU Radio uyumlu ZMQ PUB/SUB
│
└── repeater_detector/              # Alt proje: Kaçak Repeater Tespit Sistemi
    ├── __init__.py
    ├── config.py                   # Türkiye operatör frekansları, anomali eşikleri
    ├── main.py                     # Ayrı CLI (8 komut)
    ├── utils.py                    # Frekans sınıflandırma, 10 IQ format desteği
    ├── README.md                   # Alt proje dokümantasyonu
    │
    ├── detection/                  # Tespit katmanı
    │   ├── spectrum_surveillance.py # Spektrum gözetleme + anomali tespiti
    │   └── signal_classifier.py    # Sinyal tipi sınıflandırma
    │
    ├── localization/               # Lokalizasyon katmanı
    │   ├── rssi_distance.py        # RSSI → mesafe tahmini (FSPL + log-distance)
    │   └── direction_finder.py     # Yön bulma (RSSI vs açı profili)
    │
    └── simulation/                 # Simülasyon katmanı
        ├── repeater_simulator.py   # Sentetik repeater sinyali üretimi
        └── scenario_generator.py   # 5 önceden tanımlı test senaryosu
```

## GNU Radio ve IQ Veri Formatı Desteği

Proje, GNU Radio ile tam uyumlu çalışacak şekilde tasarlanmıştır:

### Desteklenen IQ Dosya Formatları

| Format | Uzantı | Açıklama |
|--------|--------|----------|
| NumPy | `.npy` | Proje varsayılan formatı |
| GNU Radio cf32 | `.complex64`, `.cf32`, `.fc32` | Complex float32, GNU Radio File Sink çıktısı |
| GNU Radio cf64 | `.cf64` | Complex float64 |
| Ham binary | `.raw`, `.bin` | Düz complex64 binary |
| UHD sc16 | `.s16`, `.sc16`, `.cs16` | Signed 16-bit interleaved I/Q |

### GNU Radio ile Veri Kaydetme

GNU Radio Companion (GRC) üzerinden yakalanan IQ verilerini projeye yüklemek için:

1. GNU Radio'da **File Sink** bloku kullanarak `.complex64` formatında kaydedin
2. Kaydedilen dosyayı `data/` klasörüne koyun
3. Analiz komutlarında `--input` parametresiyle kullanın:

```bash
# Ana proje ile analiz
python main.py spectrum --input data/gnuradio_capture.complex64 --freq 868e6

# Repeater detector ile analiz
python repeater_detector/main.py scan --input data/gnuradio_capture.complex64 --freq 900e6
```

### ZMQ Entegrasyonu

ZMQ streamer, GNU Radio'nun `ZMQ PUB Sink` / `ZMQ SUB Source` blokları ile doğrudan uyumludur:

```bash
# USRP'den ZMQ üzerinden yayınla
python main.py stream --role pub --freq 868e6

# GNU Radio'da ZMQ SUB Source ile al:
#   Address: tcp://192.168.10.2:5555
#   Output Type: Complex Float32
```

## Kurulum

### 1. Paket Kurulumu

```bash
pip install -e .
```

veya bağımlılıkları ayrı yüklemek için:

```bash
pip install -r requirements.txt
```

### 2. Fiziksel Bağlantılar

```
USRP E310 (eth0) ──── Ethernet kablosu ──── Host PC (eno1)
USRP E310 (USB)  ──── USB-Seri kablosu ──── Host PC (/dev/ttyUSB0)
Anten (SMA)      ──── SMA konektör     ──── USRP E310 (RX2 / TX/RX)
```

### 3. Ağ Konfigürasyonu

```bash
# USRP E310 tarafı (seri konsol ile)
sudo screen /dev/ttyUSB0 115200
ip addr add 192.168.10.2/24 dev eth0

# Host PC tarafı
ip addr add 192.168.10.1/24 dev eno1
sudo ethtool -s eno1 autoneg on speed 1000 duplex full
```

### 4. Bağlantı Doğrulama

```bash
ssh root@192.168.10.2
export TERM=xterm
uhd_find_devices
# Beklenen çıktı: Product: e310_sg3
```

## Kullanım — Ana Proje

`main.py` tüm modülleri CLI üzerinden birleştirir. İki çalışma modu desteklenir:

- **`--mode embedded`**: Betik doğrudan USRP E310 üzerinde çalışır
- **`--mode network`**: Host PC'den Ethernet üzerinden USRP'ye bağlanır (varsayılan)

### Cihaz ve Anten Bilgisi

```bash
python main.py info
```

### IQ Veri Yakalama

```bash
# 868 MHz'de 2 saniye yakalama, dosyaya kaydet
python main.py capture --freq 868e6 --duration 2 --output data/test.npy

# GNU Radio uyumlu formatta kaydet
python main.py capture --freq 915e6 --duration 5 --output data/capture.complex64
```

### Spektrum Analizi

```bash
# Canlı yakalama ve spektrum grafiği
python main.py spectrum --freq 868e6 --save results/spectrum.png

# GNU Radio'dan kaydedilmiş dosyadan analiz
python main.py spectrum --input data/gnuradio.complex64 --save spectrum.png

# Canlı (gerçek zamanlı) spektrum görüntüsü
python main.py spectrum --freq 868e6 --live
```

### Waterfall Diyagramı

```bash
python main.py waterfall --freq 868e6 --duration 5 --save results/waterfall.png
python main.py waterfall --freq 868e6 --live
```

### LoRa Sinyal Demodülasyonu

```bash
# Canlı LoRa yakalama ve çözme
python main.py lora --freq 868e6 --sf 7 --duration 10

# Otomatik SF tahmini ile
python main.py lora --freq 868e6 --auto-sf

# Dosyadan çözümleme
python main.py lora --input data/lora_capture.npy
```

### Test Sinyali Üretme

```bash
python main.py generate --type tone --freq 868e6 --offset 10000
python main.py generate --type lora --sf 7
python main.py generate --type tone --freq 868e6 --continuous
```

### Frekans Tarama

```bash
# Alt bant (698-960 MHz)
python main.py scan --band low --plot --save results/scan_low.png

# Tam tarama (her iki bant)
python main.py scan --band full --export results/scan.csv --save results/scan.png
```

### ZMQ Veri Akışı

```bash
# USRP E310 üzerinde (yayınlayıcı)
python main.py stream --role pub --freq 868e6

# Host PC üzerinde (alıcı)
python main.py stream --role sub --sub-host 192.168.10.2
```

### NOMA Simülasyonu (Donanım Gerektirmez)

```bash
# BER vs SNR simülasyonu
python main.py noma-sim --users 2 --modulation QPSK

# 3 kullanıcı, 16-QAM
python main.py noma-sim --users 3 --modulation 16QAM --snr-min -10 --snr-max 35
```

### NOMA vs OMA Karşılaştırma Raporu

```bash
# Tam rapor: tüm grafik ve CSV dosyaları üretilir
python main.py noma-compare --users 2 --modulation QPSK
```

### Deep Learning Sinyal Sınıflandırma

```bash
# Veri seti üretimi
python main.py generate-dataset --samples 300 --length 4096

# CNN modeli eğitimi
python main.py train-model --data-dir data --model cnn --epochs 30

# IQ veri analizi
python main.py analyze-data --input data/sample.npy --freq 868e6
```

## Kullanım — Kaçak Repeater Tespit Sistemi

Alt proje ayrı bir CLI'ye sahiptir. Detaylı bilgi için `repeater_detector/README.md` dosyasına bakınız.

```bash
# Sistem bilgisi
python repeater_detector/main.py --sim info

# Simülasyon ile tarama
python repeater_detector/main.py --sim scan --scenario coklu_kacak --plot

# GNU Radio verisinden analiz
python repeater_detector/main.py scan --input data/capture.complex64 --freq 900e6

# RSSI mesafe tahmini
python repeater_detector/main.py distance --freq 900e6 --rssi -65 --env kentsel --plot

# Simülasyon ile yön bulma
python repeater_detector/main.py --sim direction --freq 900e6 --true-angle 135 --plot

# Yol kaybi model karşılaştırması
python repeater_detector/main.py path-loss --freq 900e6 --save pathloss.png
```

## Mimari Yapı

```
Katman 3 — Uygulama       : main.py (Ana CLI — 15 komut)
                             repeater_detector/main.py (Detector CLI — 8 komut)
Katman 2 — İşleme         : analysis/ (spektrum, waterfall, tarama, deep learning)
                             lora/ (CSS demodülasyon)
                             noma/ (verici, alıcı-SIC, analizci)
                             detection/ (spektrum gözetleme, sınıflandırma)
                             localization/ (RSSI mesafe, yön bulma)
Katman 1 — Veri Erişim     : core/ (yakalama, sinyal üretimi)
                             streaming/ (ZMQ PUB/SUB)
                             simulation/ (sentetik sinyal üretimi)
Katman 0 — Donanım         : core/usrp_controller (UHD API)
Altyapı                    : config, utils (GNU Radio uyumlu IQ formatları)
```

## Testler

```bash
# Ana proje testleri (21 test)
python -m unittest tests.test_project -v

# Repeater detector testleri (36 test)
python -m unittest tests.test_repeater_detector -v

# Tüm testler
python -m unittest discover tests -v
```

## Sorun Giderme

| Sorun | Çözüm |
|:------|:------|
| SSH terminal hataları | `export TERM=xterm` |
| Veri kaybı / taşma (overflow) | `sudo ethtool -s eno1 autoneg on speed 1000 duplex full` |
| UHD modülü bulunamadı | `sudo apt install python3-uhd` veya ilgili paket yöneticisi |
| ZMQ bağlantı hatası | Firewall kurallarını kontrol edin, port 5555 açık olmalı |
| Matplotlib GUI hatası | `matplotlib.use("TkAgg")` — headless ortamda `Agg` otomatik kullanılır |
| NOMA BER çok yüksek | SNR değerini artırın, daha az kullanıcı deneyin |
| NumPy/PyTorch uyumsuzluğu | `pip install numpy<2` veya PyTorch güncellemesi |
| GNU Radio dosyası okunamıyor | Uzantıyı kontrol edin: `.complex64`, `.fc32`, `.sc16` desteklenir |

## Lisans

MIT License — detaylar için `LICENSE` dosyasına bakınız.
