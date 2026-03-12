# USRP E310 ile LoRaWAN Sinyal Analizi ve NOMA Çoklu Erişim Projesi

Bu proje, **USRP E310** Yazılım Tanımlı Radyo (SDR) platformu kullanarak **LoRaWAN 868 MHz** sinyallerinin yakalanması, analiz edilmesi ve **NOMA (Non-Orthogonal Multiple Access)** çoklu erişim tekniğinin uygulanmasını kapsamaktadır.

## Proje Hedefi

- LoRa modülünden gelen 868 MHz sinyallerini USRP E310 ile yakalama ve demodüle etme
- 698–960 MHz ve 1710–2700 MHz frekans bantlarında geniş bant tarama
- NOMA (Superposition Coding + SIC) ile çoklu kullanıcı erişimi simülasyonu ve gerçek zamanlı testi
- NOMA vs OMA performans karşılaştırması (BER, kapasite, throughput)

## Donanım

| Bileşen | Model | Açıklama |
|---------|-------|----------|
| **SDR** | USRP E310 (Embedded) | Alıcı/Verici platform |
| **LoRa Modülü** | Ebyte E220-900T22D | 868–915 MHz, 22 dBm, LLCC68 |
| **Anten** | MRTK-Q7027I28 | 7 dBi, SMA, 698–960 / 1710–2700 MHz |
| **Host PC** | Linux (Arch) | Ethernet ile bağlı |
| **Bağlantı** | Ethernet + USB-Seri | Veri akışı + konsol |

## Yazılım Gereksinimleri

- **Python 3.8+**
- **UHD** (USRP Hardware Driver) — sistem paketi olarak
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
```

## Proje Yapısı

```
BitirmeProjesi-main/
│
├── main.py                     # CLI ana giriş noktası (argparse, 12 alt komut)
├── setup.py                    # Paket kurulum dosyası
├── requirements.txt            # Python bağımlılıkları
├── .gitignore                  # Git yoksayma kuralları
├── LICENSE                     # MIT Lisans
├── README.md                   # Bu dosya
├── PROJE_RAPORU.md             # Detaylı akademik proje raporu
│
├── docs/                       # Dokümanlar
│   └── antenbilgisi.txt        # Anten veri sayfası
│
├── data/                       # IQ veri dosyaları (.npy)
├── results/                    # Çıktı grafikleri ve CSV dosyaları
│
└── usrp_noma/                  # Ana Python paketi
    ├── __init__.py             # Paket tanımı, versiyon bilgisi
    ├── config.py               # Merkezi konfigürasyon (USRP, NOMA, LoRa, anten)
    ├── utils.py                # Yardımcı fonksiyonlar (dB dönüşüm, I/O, loglama)
    │
    ├── core/                   # Donanım etkileşim katmanı
    │   ├── __init__.py
    │   ├── usrp_controller.py  # UHD ile USRP E310 cihaz yönetimi
    │   ├── signal_capture.py   # IQ veri yakalama (tek seferlik + sürekli)
    │   └── signal_generator.py # Test sinyali üretimi (ton, chirp, LoRa, gürültü)
    │
    ├── analysis/               # Sinyal analiz katmanı
    │   ├── __init__.py
    │   ├── spectrum_analyzer.py  # FFT/Welch PSD spektrum analizi
    │   ├── waterfall_display.py  # Waterfall (şelale) diyagramı
    │   └── frequency_scanner.py  # Geniş bant frekans tarama (698–2700 MHz)
    │
    ├── lora/                   # LoRa demodülasyon katmanı
    │   ├── __init__.py
    │   └── decoder.py          # LoRa CSS demodülasyon (preamble, dechirp, payload)
    │
    ├── noma/                   # NOMA çoklu erişim katmanı
    │   ├── __init__.py
    │   ├── modulation.py       # Konstelasyon tabloları (QPSK, 16QAM, 64QAM)
    │   ├── transmitter.py      # Verici: Superposition Coding
    │   ├── receiver.py         # Alıcı: SIC (Successive Interference Cancellation)
    │   └── analyzer.py         # Monte Carlo simülasyon ve performans analizi
    │
    └── streaming/              # Veri akış katmanı
        ├── __init__.py
        └── zmq_streamer.py     # ZMQ PUB/SUB IQ veri akışı (GNU Radio uyumlu)
```

## Kurulum

### 1. Paket Kurulumu

```bash
# Proje dizininde
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

## Kullanım

`main.py` tüm modülleri CLI üzerinden birleştirir. İki çalışma modu desteklenir:

- **`--mode embedded`**: Betik doğrudan USRP E310 üzerinde çalışır
- **`--mode network`**: Host PC'den Ethernet üzerinden USRP'ye bağlanır (varsayılan)

### Cihaz ve Anten Bilgisi

```bash
python3 main.py info
```

### IQ Veri Yakalama

```bash
# 868 MHz'de 2 saniye yakalama, dosyaya kaydet
python3 main.py capture --freq 868e6 --duration 2 --output data/test.npy

# Farklı kazanç ve örnekleme hızı ile
python3 main.py capture --freq 915e6 --gain 50 --rate 2e6 --duration 5
```

### Spektrum Analizi

```bash
# Canlı yakalama ve spektrum grafiği
python3 main.py spectrum --freq 868e6 --save results/spectrum.png

# Önceden kaydedilmiş dosyadan analiz
python3 main.py spectrum --input data/test.npy --save spectrum.png

# Canlı (gerçek zamanlı) spektrum görüntüsü
python3 main.py spectrum --freq 868e6 --live
```

### Waterfall Diyagramı

```bash
python3 main.py waterfall --freq 868e6 --duration 5 --save results/waterfall.png
python3 main.py waterfall --freq 868e6 --live
```

### LoRa Sinyal Demodülasyonu

```bash
# Canlı LoRa yakalama ve çözme
python3 main.py lora --freq 868e6 --sf 7 --duration 10

# Otomatik SF tahmini ile
python3 main.py lora --freq 868e6 --auto-sf

# Dosyadan çözümleme
python3 main.py lora --input data/lora_capture.npy
```

### Test Sinyali Üretme

```bash
# CW ton sinyali
python3 main.py generate --type tone --freq 868e6 --offset 10000

# LoRa preamble
python3 main.py generate --type lora --sf 7

# Sürekli iletim
python3 main.py generate --type tone --freq 868e6 --continuous
```

### Frekans Tarama

```bash
# Alt bant (698-960 MHz)
python3 main.py scan --band low --plot --save results/scan_low.png

# Üst bant (1710-2700 MHz)
python3 main.py scan --band high

# Tam tarama (her iki bant)
python3 main.py scan --band full --export results/scan.csv --save results/scan.png
```

### ZMQ Veri Akışı

```bash
# USRP E310 üzerinde (yayınlayıcı)
python3 main.py stream --role pub --freq 868e6

# Host PC üzerinde (alıcı)
python3 main.py stream --role sub --sub-host 192.168.10.2
```

### NOMA Simülasyonu (Donanım Gerektirmez)

```bash
# BER vs SNR simülasyonu — 2 kullanıcı, QPSK
python3 main.py noma-sim --users 2 --modulation QPSK

# 3 kullanıcı, 16-QAM, geniş SNR aralığı
python3 main.py noma-sim --users 3 --modulation 16QAM --snr-min -10 --snr-max 35

# Belirli sembol sayısı ile (daha hızlı test)
python3 main.py noma-sim --users 2 --symbols 10000
```

### NOMA vs OMA Karşılaştırma Raporu

```bash
# Tam rapor: tüm grafik ve CSV dosyaları üretilir
python3 main.py noma-compare --users 2 --modulation QPSK

# Çıktılar (results/ dizininde):
#   noma_ber_vs_snr.png      — BER vs SNR eğrileri
#   noma_vs_oma_ber.png      — NOMA vs OMA BER karşılaştırma
#   capacity_comparison.png  — Shannon kapasite karşılaştırma
#   throughput_comparison.png — Throughput karşılaştırma
#   power_allocation.png     — Güç tahsis diyagramı
#   constellation_tx.png     — TX konstelasyon
#   constellation_rx.png     — RX konstelasyon (SNR=20 dB)
#   sic_stages.png           — SIC aşamaları
#   noma_ber_results.csv     — BER sayısal verileri
#   capacity_results.csv     — Kapasite sayısal verileri
```

### NOMA Konstelasyon Diyagramları

```bash
python3 main.py noma-constellation --snr 20 --users 2 --modulation QPSK
```

### NOMA Gerçek Zamanlı Test (USRP)

```bash
python3 main.py noma-live --freq 868e6 --users 2 --duration 5
```

## Paket Mimari Yapısı

Proje, katmanlı bir mimari ile tasarlanmıştır:

```
Katman 3 — Uygulama       : main.py (CLI — 12 alt komut)
Katman 2 — İşleme         : analysis/ (spektrum, waterfall, tarama)
                             lora/ (CSS demodülasyon)
                             noma/ (verici, alıcı-SIC, analizci)
Katman 1 — Veri Erişim     : core/ (yakalama, sinyal üretimi)
                             streaming/ (ZMQ PUB/SUB)
Katman 0 — Donanım         : core/usrp_controller (UHD API)
Altyapı                    : config, utils
```

### Modüller Arası Bağımlılık

```
usrp_noma/config ──── usrp_noma/utils
        │                    │
        └────────┬───────────┘
                 │
    usrp_noma/core/usrp_controller
                 │
        ┌────────┼──────────────────────┐
        │        │                      │
  core/signal_   core/signal_     streaming/
  capture        generator        zmq_streamer
        │                               │
  ┌─────┼───────────┐                   │
  │     │           │                   │
analysis/     analysis/           noma/
spectrum      waterfall         modulation
analyzer      display         ┌────┴────┐
  │                          noma/     noma/
analysis/                transmitter  receiver
frequency                     │           │
scanner                       └─────┬─────┘
  │                                 │
  │                           noma/analyzer
  │                                 │
lora/decoder                        │
  │                                 │
  └───────────────┬─────────────────┘
                  │
              main.py (CLI)
```

### Python Import Örnekleri

```python
# Doğrudan sınıf import'u
from usrp_noma.core import USRPController, SignalCapture, SignalGenerator
from usrp_noma.analysis import SpectrumAnalyzer, WaterfallDisplay, FrequencyScanner
from usrp_noma.lora import LoRaDecoder
from usrp_noma.noma import NOMATransmitter, NOMAReceiver, NOMAnalyzer
from usrp_noma.streaming import ZMQStreamer

# Konfigürasyon ve yardımcı fonksiyonlar
from usrp_noma import config
from usrp_noma.utils import setup_logger, freq_to_str, load_iq_data
```

## Dosya Açıklamaları

### `usrp_noma/config.py`
Tüm projenin merkezi konfigürasyon dosyasıdır. USRP bağlantı bilgileri, SDR parametreleri (örnekleme hızı, kazanç, frekans), anten teknik verileri, LoRa parametreleri (SF, BW, sync word), frekans tarama ayarları, ZMQ parametreleri ve NOMA konfigürasyonu (güç katsayıları, modülasyon, simülasyon aralıkları) bu dosyada tanımlıdır.

### `usrp_noma/utils.py`
Projede tekrar eden işlemler için yardımcı fonksiyonlar sunar: dB dönüşümleri (`linear_to_dB`, `dB_to_linear`, `amplitude_to_dB`), IQ veri dosyalama (`save_iq_data`, `load_iq_data` — `.npy` + metadata), zaman damgalı dosya adı oluşturma, loglama yapılandırması, güç hesaplama ve SNR tahmini.

### `usrp_noma/core/usrp_controller.py`
UHD Python API kullanarak USRP E310 ile donanım etkileşimini soyutlar. `USRPController` sınıfı RX/TX frekans, kazanç, örnekleme hızı ve anten ayarlarını yönetir. Hem embedded hem network modunu destekler. Context manager (`with` bloku) desteği vardır.

### `usrp_noma/core/signal_capture.py`
`USRPController` üzerinden IQ veri yakalama işlemlerini yönetir. Tek seferlik yakalama (`capture`), dosyaya kayıtlı yakalama (`capture_to_file`) ve ayrı thread'de çalışan sürekli yakalama (`continuous_capture` + callback) modları sunar.

### `usrp_noma/core/signal_generator.py`
USRP E310 üzerinden test amaçlı sinyal üretir. CW sinüzoidal ton, lineer chirp, LoRa preamble ve beyaz Gauss gürültüsü üretebilir. Tek seferlik ve sürekli iletim modlarını destekler.

### `usrp_noma/analysis/spectrum_analyzer.py`
IQ verisinden Güç Yoğunluk Spektrumu (PSD) hesaplar. Welch ve temel FFT yöntemlerini destekler. Tepe noktası bulma, bant gücü hesaplama ve matplotlib ile statik/canlı spektrum görüntüleme sağlar.

### `usrp_noma/analysis/waterfall_display.py`
Zaman-frekans görselleştirmesi yapan waterfall (şelale) diyagramı modülüdür. Dairesel tampon kullanarak geçmiş verileri saklar. Statik grafik, canlı güncelleme ve PNG kayıt özelliklerine sahiptir.

### `usrp_noma/analysis/frequency_scanner.py`
Antenin desteklediği frekans bantlarını adım adım tarar. Alt bant (698–960 MHz), üst bant (1710–2700 MHz) veya tam tarama yapabilir. Aktif sinyalleri tespit eder, bilinen servislerle eşleştirir. Sonuçları matplotlib grafiği veya CSV dosyasına aktarır.

### `usrp_noma/lora/decoder.py`
LoRa CSS (Chirp Spread Spectrum) sinyallerinin demodülasyonunu gerçekleştirir. Up/down chirp üretimi, preamble tespiti (korelasyon tabanlı), dechirp işlemi, header ve payload çözümleme fonksiyonlarını içerir. SF otomatik tahmin özelliği vardır.

### `usrp_noma/noma/modulation.py`
QPSK, 16-QAM ve 64-QAM konstelasyon tablolarını içerir. Gray kodlu ve birim enerji normalize edilmiştir. Verici ve alıcı tarafından ortak kullanılır.

### `usrp_noma/noma/transmitter.py`
NOMA vericisi: QPSK/16QAM/64QAM modülasyon, güç tahsisi ve superposition coding (sinyallerin güç alanında toplanması). 2–4 kullanıcı destekler.

### `usrp_noma/noma/receiver.py`
NOMA alıcısı: SIC (Successive Interference Cancellation) algoritmasını uygular. En güçlü kullanıcıyı önce çözer, yeniden oluşturup kalan sinyalden çıkarır. AWGN kanal modeli, ML demodülasyon ve BER hesaplama içerir.

### `usrp_noma/noma/analyzer.py`
Monte Carlo simülasyonu ile BER vs SNR eğrileri üretir. NOMA vs OMA performans karşılaştırması, Shannon kapasite hesabı, throughput analizi yapar. Akademik kalitede 7 farklı grafik türü ve CSV çıktı üretir.

### `usrp_noma/streaming/zmq_streamer.py`
ZeroMQ (ZMQ) üzerinden IQ veri akışı sağlar. PUB/SUB paterniyle çalışır. GNU Radio ZMQ Source/Sink blokları ile uyumlu complex64 formatında veri iletir.

### `main.py`
Tüm modülleri `argparse` tabanlı CLI ile birleştirir. 12 alt komut sunar: `info`, `capture`, `spectrum`, `waterfall`, `lora`, `generate`, `scan`, `stream`, `noma-sim`, `noma-compare`, `noma-constellation`, `noma-live`. Çalışma modunu otomatik algılar (embedded/network).

## Sorun Giderme

| Sorun | Çözüm |
|:------|:------|
| SSH terminal hataları | `export TERM=xterm` |
| Veri kaybı / taşma (overflow) | `sudo ethtool -s eno1 autoneg on speed 1000 duplex full` |
| UHD modülü bulunamadı | `sudo apt install python3-uhd` veya ilgili paket yöneticisi |
| ZMQ bağlantı hatası | Firewall kurallarını kontrol edin, port 5555 açık olmalı |
| Matplotlib GUI hatası | `matplotlib.use("TkAgg")` — headless ortamda `Agg` otomatik kullanılır |
| NOMA BER çok yüksek | SNR değerini artırın, daha az kullanıcı deneyin |

## Lisans

MIT License — detaylar için `LICENSE` dosyasına bakınız.
