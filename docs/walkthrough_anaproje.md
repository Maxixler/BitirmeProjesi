# Gerçek Hayat Uygulama Kılavuzu — Ana Proje (usrp_noma)

Bu kılavuz, USRP E310 ve LoRaWAN donanımı ile projenin gerçek hayatta nasıl kullanılacağını adım adım anlatır.

---

## 1. Donanım Hazırlığı

### 1.1. Gerekli Ekipman

- USRP E310 (AD9361 RF çipli SDR)
- MRTK-Q7027I28 anten (698–960 / 1710–2700 MHz, 7 dBi)
- Ebyte E220-900T22D LoRa modülü (opsiyonel, LoRa testleri için)
- Ethernet kablosu (Cat5e veya üstü, Gigabit)
- USB-Seri dönüştürücü (konsol erişimi için)
- Host PC (Linux önerilir, Windows da desteklenir)

### 1.2. Fiziksel Bağlantılar

```
                      SMA Anten
                        │
                    ┌───┴───┐
                    │ USRP  │
                    │ E310  │
                    └┬────┬─┘
                     │    │
              Ethernet    USB-Seri
                     │    │
                    ┌┴────┴─┐
                    │ Host  │
                    │  PC   │
                    └───────┘
```

1. Anteni USRP E310'un **RX2** portuna bağlayın (sadece alım için)
2. TX/RX portunu sinyal üretme testlerinde kullanın
3. Ethernet kablosunu bağlayın (USRP eth0 ↔ Host PC)
4. USB-Seri kablosunu bağlayın (konsol erişimi için)

### 1.3. Ağ Konfigürasyonu

```bash
# 1. USB-Seri ile USRP konsoluna bağlanın
sudo screen /dev/ttyUSB0 115200

# 2. USRP üzerinde IP ayarlayın
ip addr add 192.168.10.2/24 dev eth0
ip link set eth0 up

# 3. Host PC üzerinde IP ayarlayın
sudo ip addr add 192.168.10.1/24 dev eno1
sudo ip link set eno1 up

# 4. Gigabit hız ayarı (veri kaybını önler)
sudo ethtool -s eno1 autoneg on speed 1000 duplex full

# 5. Bağlantı testi
ping 192.168.10.2
```

### 1.4. UHD ve Python Ortamı

```bash
# UHD kurulumu (Linux)
sudo apt install uhd-host python3-uhd

# USRP firmware kontrolü
uhd_find_devices
# Beklenen: Product: e310_sg3, Serial: XXXXXX

# Python bağımlılıkları
cd BitirmeProjesi
pip install -e .
```

---

## 2. İlk Çalıştırma ve Doğrulama

### 2.1. Sistem Bilgisi

```bash
python main.py info
```

Bu komut USRP'nin bağlantı durumunu, seri numarasını, firmware versiyonunu ve anten bilgilerini gösterir.

### 2.2. Hızlı İşlevsellik Testi

```bash
# 868 MHz'de 1 saniyelik veri yakala
python main.py capture --freq 868e6 --duration 1 --output data/test.npy

# Yakalanan veriyi analiz et
python main.py spectrum --input data/test.npy --save results/first_test.png

# Beklenecek çıktı: 868 MHz civarında PSD grafiği
```

---

## 3. Senaryo: LoRa Sinyal Yakalama ve Analiz

### 3.1. LoRa Modülü Konfigürasyonu

Ebyte E220-900T22D modülünü USB-Seri ile bilgisayara bağlayın ve 868 MHz, SF7, BW 125 kHz olarak yapılandırın.

### 3.2. LoRa Veri Yakalama

```bash
# LoRa modülü veri gönderirken, USRP ile yakala
python main.py capture --freq 868e6 --rate 1e6 --gain 40 --duration 10 \
    --output data/lora_868mhz.npy
```

### 3.3. LoRa Demodülasyon

```bash
# Otomatik SF tahmini ile demodülasyon
python main.py lora --input data/lora_868mhz.npy --auto-sf

# Bilinen SF ile demodülasyon
python main.py lora --input data/lora_868mhz.npy --sf 7

# Gerçek zamanlı demodülasyon (LoRa modülü aktif gönderimde iken)
python main.py lora --freq 868e6 --sf 7 --duration 30
```

### 3.4. Detaylı IQ Analizi

```bash
# 25 boyutlu özellik çıkarımı ve 6 panelli görselleştirme
python main.py analyze-data --input data/lora_868mhz.npy --freq 868e6 \
    --save results/lora_analysis.png

# Çıktı: zaman alanı, PSD, spektrogram, konstelasyon, histogram, otokorelasyon
```

---

## 4. Senaryo: Geniş Bant Frekans Tarama

### 4.1. Tüm Bantların Taranması

```bash
# Alt bant (698-960 MHz) — GSM 900, LoRa, LTE Band 20
python main.py scan --band low --plot --save results/scan_low.png

# Üst bant (1710-2700 MHz) — GSM 1800, UMTS 2100, LTE, WiFi
python main.py scan --band high --plot --save results/scan_high.png

# Tam tarama (her iki bant)
python main.py scan --band full --export results/scan_full.csv \
    --save results/scan_full.png
```

### 4.2. Tarama Sonuçlarını Yorumlama

CSV dosyasında her frekans adımı için güç seviyesi (dBm) raporlanır. Yüksek güçlü sinyaller aktif vericilere karşılık gelir. Bilinen frekanslar (GSM, LTE, WiFi vb.) otomatik etiketlenir.

### 4.3. Waterfall Görüntüsü

```bash
# 5 saniyelik waterfall diyagramı — zaman içinde frekans aktivitesini gösterir
python main.py waterfall --freq 868e6 --duration 5 --save results/waterfall.png

# Gerçek zamanlı waterfall (pencerede canlı güncellenir)
python main.py waterfall --freq 868e6 --live
```

---

## 5. Senaryo: NOMA Simülasyon ve Gerçek Zamanlı Test

### 5.1. NOMA BER vs SNR Simülasyonu (Donanımsız)

```bash
# 2 kullanıcı, QPSK modülasyon
python main.py noma-sim --users 2 --modulation QPSK \
    --snr-min -5 --snr-max 30 --save results/noma_ber.png

# 3 kullanıcı, 16-QAM
python main.py noma-sim --users 3 --modulation 16QAM
```

### 5.2. NOMA vs OMA Karşılaştırma

```bash
python main.py noma-compare --users 2 --modulation QPSK

# Otomatik üretilen dosyalar:
#   results/noma_ber_vs_snr.png      — BER eğrileri
#   results/noma_vs_oma_ber.png      — NOMA vs OMA karşılaştırma
#   results/capacity_comparison.png  — Shannon kapasite
#   results/throughput_comparison.png — Throughput
#   results/power_allocation.png     — Güç tahsis
#   results/constellation_tx.png     — TX konstelasyon
#   results/sic_stages.png           — SIC aşamaları
#   results/noma_ber_results.csv     — BER verileri
#   results/capacity_results.csv     — Kapasite verileri
```

### 5.3. Konstelasyon Diyagramları

```bash
# SNR=20 dB'de, TX/RX konstelasyonlarını karşılaştır
python main.py noma-constellation --snr 20 --users 2 --modulation QPSK \
    --save results/constellation.png
```

### 5.4. Gerçek Zamanlı NOMA Test (USRP Gerekli)

Bu test, USRP üzerinden NOMA sinyali gönderip alarak gerçek kanal koşullarında BER ölçer:

```bash
# USRP ile 868 MHz'de NOMA canlı test
python main.py noma-live --freq 868e6 --users 2 --duration 5

# İpuçları:
# - TX/RX anteni aynı USRP'ye bağlı olmalı
# - Loopback test için iki port arası SMA kablo kullanılabilir
# - Gerçek kanal testi için iki ayrı anten kullanın
```

---

## 6. Senaryo: Deep Learning Sinyal Sınıflandırma

### 6.1. Eğitim Verisi Üretimi

```bash
# 5 sinyal sınıfı (lora, noma, cw, ofdm, noise), sınıf başına 300 örnek
python main.py generate-dataset --samples 300 --length 4096 \
    --snr-min 0 --snr-max 25 --output data/training_dataset
```

### 6.2. Model Eğitimi

```bash
# 1D CNN modeli
python main.py train-model --data-dir data/training_dataset --model cnn \
    --epochs 30 --batch-size 32

# 1D ResNet modeli (daha derin mimari)
python main.py train-model --data-dir data/training_dataset --model resnet \
    --epochs 50

# Çıktılar:
#   results/best_model.pth           — En iyi validasyon modeli
#   results/final_model.pth          — Son epoch modeli
#   results/training_curves.png      — Loss/accuracy eğrileri
#   results/accuracy_vs_snr.png      — SNR'a göre doğruluk
#   results/confusion_matrix.png     — Karışıklık matrisi
```

### 6.3. Gerçek Veri ile Sınıflandırma

Eğitilmiş modeli USRP'den yakalanan gerçek IQ verileri üzerinde test etmek için:

```bash
# Önce gerçek veri yakala
python main.py capture --freq 868e6 --duration 5 --output data/real_capture.npy

# Detaylı analiz yap
python main.py analyze-data --input data/real_capture.npy --freq 868e6
```

---

## 7. Senaryo: GNU Radio Entegrasyonu

### 7.1. GNU Radio'dan Veri Kaydetme

GNU Radio Companion'da bir flow graph oluşturun:

```
UHD Source → [işleme blokları] → File Sink (.complex64)
```

File Sink ayarları:
- Type: Complex Float32
- File: `data/gnuradio_capture.complex64`

### 7.2. Kaydedilen Veriyi Projede Kullanma

```bash
# Spektrum analizi
python main.py spectrum --input data/gnuradio_capture.complex64 \
    --freq 868e6 --save results/gnuradio_spectrum.png

# LoRa demodülasyon
python main.py lora --input data/gnuradio_capture.complex64 --sf 7

# Özellik çıkarımı
python main.py analyze-data --input data/gnuradio_capture.complex64 --freq 868e6
```

### 7.3. ZMQ ile Gerçek Zamanlı Akış

```bash
# Terminal 1: USRP'den ZMQ üzerinden yayınla
python main.py stream --role pub --freq 868e6

# Terminal 2: GNU Radio'da ZMQ SUB Source bloku ile al
#   Address: tcp://192.168.10.2:5555
#   Output Type: Complex Float32

# VEYA Terminal 2: Python ile al
python main.py stream --role sub --sub-host 192.168.10.2
```

---

## 8. Veri Yönetimi

### 8.1. IQ Dosya Organizasyonu

```
data/
├── lora_868mhz_20260315.npy          # LoRa yakalama
├── lora_868mhz_20260315.npy.meta     # Metadata (sample_rate, center_freq)
├── scan_full_20260315.npy            # Tam bant tarama
├── gnuradio_capture.complex64        # GNU Radio kaydı
├── training_dataset/                 # DL eğitim verisi
│   ├── lora/                         # LoRa örnekleri
│   ├── noma/                         # NOMA örnekleri
│   └── ...
└── repeater_captures/                # Repeater detector verileri
```

### 8.2. Metadata Dosyası Formatı

Her `.npy` veya `.raw` dosyasının yanına otomatik oluşturulan `.meta` dosyası:

```
sample_rate=1000000.0
center_freq=868000000.0
timestamp=2026-03-15T14:30:25.123456
num_samples=1000000
dtype=complex64
```

---

## 9. Performans İpuçları

### 9.1. Örnekleme Hızı Seçimi

| Uygulama | Önerilen Hız | Neden |
|----------|-------------|-------|
| LoRa yakalama | 1 MHz | 125 kHz BW + kenar payı |
| GSM tarama | 1 MHz | 200 kHz kanal BW |
| LTE analiz | 5-20 MHz | Geniş bant |
| Genel tarama | 1 MHz | İyi çözünürlük, düşük veri |

### 9.2. Kazanç Ayarı

- **Başlangıç**: 40 dB (varsayılan)
- **Yakın verici**: 20-30 dB (doygunluk önleme)
- **Zayıf sinyal**: 50-60 dB (gürültü tabanı yükselebilir)
- **Tarama**: 40 dB (dengeli)

### 9.3. Veri Kayıplarını Önleme

```bash
# Gigabit Ethernet ayarı zorunlu
sudo ethtool -s eno1 autoneg on speed 1000 duplex full

# Sistem tampon boyutunu artır
sudo sysctl -w net.core.rmem_max=33554432
sudo sysctl -w net.core.rmem_default=33554432
```

---

## 10. Sorun Giderme Rehberi

| Belirti | Olası Neden | Çözüm |
|---------|-------------|-------|
| `uhd_find_devices` boş dönüyor | IP yapılandırması yanlış | Ağ ayarlarını kontrol edin |
| "Overflow" uyarıları | Ethernet hızı yetersiz | Gigabit hız ayarlayın |
| PSD grafiğinde güç çok düşük | Kazanç düşük veya anten bağlı değil | gain artırın, anten bağlayın |
| LoRa preamble bulunamıyor | SF veya frekans yanlış | `--auto-sf` deneyin |
| NOMA BER çok yüksek | SNR düşük | SNR değerini artırın |
| `import uhd` hatası | UHD yüklü değil | `sudo apt install python3-uhd` |
| Matplotlib penceresi açılmıyor | GUI backend yok | X11 forwarding veya `--save` kullanın |
