# USRP E310 ile LoRaWAN Sinyal Analizi ve NOMA Çoklu Erişim — Proje Raporu

## 1. Giriş

### 1.1 Projenin Amacı

Bu bitirme projesi, **Yazılım Tanımlı Radyo (SDR)** teknolojisi kullanarak kablosuz iletişim sinyallerinin yakalanması, analiz edilmesi ve ileri düzey çoklu erişim tekniklerinin uygulanmasını hedeflemektedir. Proje iki ana eksende ilerler:

1. **LoRaWAN Sinyal Analizi**: Ebyte E220-900T22D LoRa modülünden gelen 868 MHz sinyallerinin USRP E310 ile yakalanması, spektral analizi ve CSS (Chirp Spread Spectrum) demodülasyonu.

2. **NOMA Çoklu Erişim**: Non-Orthogonal Multiple Access tekniğinin Python ortamında simülasyonu ve USRP E310 üzerinde gerçek zamanlı uygulaması. Superposition coding ile çoklu kullanıcı sinyallerinin oluşturulması, SIC (Successive Interference Cancellation) ile alıcı tarafında kullanıcı ayrıştırılması ve OMA ile performans karşılaştırması.

### 1.2 Motivasyon

IoT (Nesnelerin İnterneti) cihazlarının hızla artmasıyla birlikte, sınırlı frekans kaynaklarının verimli kullanımı kritik bir ihtiyaç haline gelmiştir. LoRaWAN uzun menzilli düşük güçlü iletişim sağlarken, NOMA aynı frekans-zaman kaynağını birden fazla kullanıcının paylaşmasına olanak tanır. Bu projede her iki teknoloji SDR platformunda birleştirilerek deneysel bir araştırma ortamı oluşturulmuştur.

### 1.3 Kapsam

- USRP E310 ile 698–960 MHz ve 1710–2700 MHz bantlarında sinyal yakalama ve tarama
- LoRa CSS sinyallerinin demodülasyonu
- NOMA verici (superposition coding) ve alıcı (SIC) tasarımı
- QPSK, 16-QAM ve 64-QAM modülasyon desteği
- Monte Carlo simülasyonu ile BER/kapasite/throughput analizi
- NOMA vs OMA karşılaştırmalı performans değerlendirmesi
- ZMQ tabanlı veri akışı ile GNU Radio entegrasyonu

---

## 2. Donanım Mimarisi

### 2.1 USRP E310

Ettus Research USRP E310, gömülü (embedded) bir SDR platformudur. Xilinx Zynq-7020 SoC (ARM Cortex-A9 + FPGA), AD9361 RF alıcı-verici ve 70 MHz – 6 GHz frekans aralığı sunar. Doğrudan üzerinde Linux çalıştırabilir veya Ethernet üzerinden host bilgisayardan kontrol edilebilir.

**Temel Özellikler:**
- RF Aralığı: 70 MHz – 6 GHz
- Bant genişliği: 56 MHz (anlık)
- ADC/DAC: 12 bit
- Bağlantı: Gigabit Ethernet, USB, GPIO
- İşlemci: Dual ARM Cortex-A9 @ 866 MHz

### 2.2 Anten (MRTK-Q7027I28)

Projede kullanılan anten, LTE/4G uyumlu çift bantlı omni-directional bir antendir.

| Parametre | Değer |
|-----------|-------|
| Frekans Aralığı | 698–960 MHz / 1710–2700 MHz |
| Kazanç | 7 dBi |
| VSWR | ≤ 2.0 |
| Empedans | 50 Ω |
| Polarizasyon | Dikey (Vertical) |
| Yayılım | Omni-Directional |
| Konektör | SMA Male |
| Kablo | RG174, 3 metre |
| Maks. Giriş Gücü | 50 W |
| Çalışma Sıcaklığı | -40°C ile +70°C |

### 2.3 LoRa Modülü (Ebyte E220-900T22D)

- Çip: LLCC68 (Semtech)
- Frekans: 868–915 MHz
- Çıkış gücü: 22 dBm (max)
- Modülasyon: LoRa (CSS)
- Arayüz: UART

### 2.4 Sistem Topolojisi

```
┌──────────────────────┐          ┌──────────────────────┐
│   LoRa Modülü        │          │   Host PC (Arch)     │
│   E220-900T22D       │          │                      │
│   868 MHz TX         │~~waves~~→│   main.py CLI        │
│                      │          │   GNU Radio           │
└──────────────────────┘          │                      │
                                  │   Ethernet           │
         ┌────────────────────────┤   192.168.10.1       │
         │                        └──────────────────────┘
         │ Ethernet
         │ 192.168.10.2
┌────────┴─────────────┐
│   USRP E310          │
│   AD9361 RF           │←── SMA ── MRTK-Q7027I28 Anten
│   UHD Driver          │
│   Python / Embedded   │
└──────────────────────┘
```

---

## 3. Yazılım Mimarisi

### 3.1 Genel Yapı

Proje, Python paketi olarak modüler ve katmanlı bir mimari ile tasarlanmıştır. Tüm modüller `usrp_noma` paketi altında organize edilmiş olup, `main.py` CLI üzerinden birleşik kullanım sağlanır.

```
BitirmeProjesi-main/
├── main.py                          # CLI ana giriş noktası
├── setup.py                         # Paket kurulum dosyası
├── requirements.txt                 # Bağımlılıklar
├── docs/                            # Dokümanlar
├── data/                            # IQ veri dosyaları
├── results/                         # Çıktı grafikleri ve CSV
│
└── usrp_noma/                       # Ana Python paketi
    ├── config.py                    # Merkezi konfigürasyon
    ├── utils.py                     # Yardımcı fonksiyonlar
    ├── core/                        # Donanım etkileşim katmanı
    │   ├── usrp_controller.py       #   UHD cihaz yönetimi
    │   ├── signal_capture.py        #   IQ veri yakalama
    │   └── signal_generator.py      #   Test sinyali üretimi
    ├── analysis/                    # Sinyal analiz katmanı
    │   ├── spectrum_analyzer.py     #   FFT/Welch PSD analizi
    │   ├── waterfall_display.py     #   Waterfall diyagramı
    │   └── frequency_scanner.py     #   Geniş bant frekans tarama
    ├── lora/                        # LoRa demodülasyon katmanı
    │   └── decoder.py               #   CSS demodülasyon
    ├── noma/                        # NOMA çoklu erişim katmanı
    │   ├── modulation.py            #   Konstelasyon tabloları
    │   ├── transmitter.py           #   Superposition Coding verici
    │   ├── receiver.py              #   SIC alıcı
    │   └── analyzer.py              #   Performans analizi
    └── streaming/                   # Veri akış katmanı
        └── zmq_streamer.py          #   ZMQ PUB/SUB akışı
```

Katmanlı mimari:

```
Katman 3 (Uygulama)      : main.py (CLI — 12 alt komut)
Katman 2 (İşleme)        : usrp_noma/analysis/ (spektrum, waterfall, tarama)
                            usrp_noma/lora/ (CSS demodülasyon)
                            usrp_noma/noma/ (verici, alıcı-SIC, analizci)
Katman 1 (Veri Erişim)   : usrp_noma/core/ (yakalama, sinyal üretimi)
                            usrp_noma/streaming/ (ZMQ PUB/SUB)
Katman 0 (Donanım)       : usrp_noma/core/usrp_controller (UHD API)
Altyapı                   : usrp_noma/config, usrp_noma/utils
```

### 3.2 Modüller Arası Bağımlılık

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

Paket içi import örnekleri:

```python
from usrp_noma.core import USRPController, SignalCapture
from usrp_noma.analysis import SpectrumAnalyzer
from usrp_noma.noma import NOMATransmitter, NOMAReceiver, NOMAnalyzer
from usrp_noma.lora import LoRaDecoder
from usrp_noma.streaming import ZMQStreamer
```

### 3.3 Çalışma Modları

| Mod | Açıklama | UHD Argümanları |
|-----|----------|-----------------|
| **Embedded** | Python doğrudan USRP E310 üzerinde çalışır | `args=""` |
| **Network** | Host PC'den Ethernet üzerinden bağlanır | `args="addr=192.168.10.2"` |

Mod otomatik olarak algılanır (`detect_mode()`) veya `--mode` parametresiyle belirtilir.

---

## 4. LoRaWAN Sinyal İşleme

### 4.1 LoRa Modülasyonu (CSS)

LoRa, Chirp Spread Spectrum modülasyonunu kullanır. Temel parametreler:

- **Spreading Factor (SF)**: 7–12 arası. SF arttıkça menzil artar, veri hızı azalır.
- **Bant Genişliği (BW)**: 125 kHz (varsayılan), 250 kHz veya 500 kHz.
- **Sembol Süresi**: T_s = 2^SF / BW
- **Sembol Başına Örnek**: N = T_s × F_s (F_s = örnekleme hızı)

### 4.2 Chirp Üretimi

Up-chirp frekansı -BW/2'den +BW/2'ye doğru lineer artar:

```
f(t) = f_0 + (f_1 - f_0) / (2 × T_s) × t
φ(t) = 2π × [f_0 × t + (chirp_rate / 2) × t²]
chirp(t) = exp(j × φ(t))
```

Down-chirp ise tersidir (f_1 → f_0).

### 4.3 Demodülasyon Pipeline

```
IQ Verisi → Preamble Tespiti → Dechirp → FFT Sembol → Header → Payload
                  ↓
         Up-chirp korelasyonu
         Ardışık ≥4 chirp kontrolü
                  ↓
         Down-chirp ile çarpma
         FFT → tepe bin = sembol değeri
```

1. **Preamble Tespiti**: Kayar pencere korelasyonu ile ardışık up-chirp'lerin tespiti (eşik > 0.6).
2. **Dechirp**: Her sembol down-chirp referansı ile çarpılarak tek frekansa dönüştürülür.
3. **FFT Sembol Çıkarma**: Dechirp sonrası FFT'nin tepe noktası sembol değerini verir (0 ile 2^SF-1 arası).
4. **Header/Payload**: İlk 5 sembol header, kalanlar payload olarak çözümlenir.

### 4.4 SF Tahmini

Farklı SF değerleri (7–12) için referans chirp'ler oluşturulup IQ verisiyle korelasyon hesaplanır. En yüksek korelasyonu veren SF değeri tahmin edilen SF'dir.

---

## 5. NOMA (Non-Orthogonal Multiple Access)

### 5.1 Teori

NOMA, 5G ve ötesi iletişim sistemleri için önerilen bir çoklu erişim tekniğidir. Geleneksel OMA (Orthogonal Multiple Access — OFDMA, TDMA gibi) yöntemlerinden farklı olarak, NOMA aynı zaman-frekans kaynağını birden fazla kullanıcıya güç alanında çoklayarak paylaştırır.

**Temel Prensipler:**
- **Verici**: Superposition Coding — farklı kullanıcıların sinyalleri, farklı güç seviyeleriyle toplanır
- **Alıcı**: SIC (Successive Interference Cancellation) — en güçlü sinyal önce çözülerek kalan sinyalden çıkarılır

### 5.2 Matematiksel Formülasyon

#### Verici (Superposition Coding)

K kullanıcı için iletilen sinyal:

```
x = √α₁ × s₁ + √α₂ × s₂ + ... + √αₖ × sₖ
```

Burada:
- `sᵢ`: i. kullanıcının modüle edilmiş sembölü (birim enerji: E[|sᵢ|²] = 1)
- `αᵢ`: i. kullanıcıya atanan güç katsayısı
- `Σαᵢ = 1` (toplam güç kısıtlaması)
- `α₁ > α₂ > ... > αₖ` (zayıf kanallı kullanıcıya daha fazla güç)

Projede kullanılan güç katsayıları:

| Kullanıcı Sayısı | α₁ | α₂ | α₃ | α₄ |
|:-:|:-:|:-:|:-:|:-:|
| 2 | 0.75 | 0.25 | — | — |
| 3 | 0.60 | 0.25 | 0.15 | — |
| 4 | 0.50 | 0.25 | 0.15 | 0.10 |

#### Alıcı (SIC Algoritması)

Alınan sinyal (AWGN kanalda): `y = x + n` (n ~ CN(0, σ²))

**SIC aşamaları (2 kullanıcı örneği):**

```
Aşama 1: En güçlü kullanıcıyı çöz (α₁ = 0.75)
  → r = y
  → SINR₁ = α₁·SNR / (α₂·SNR + 1)
  → ŝ₁ = demodulate(r / √α₁)
  → Yeniden oluştur: x̂₁ = modulate(ŝ₁) × √α₁
  → Çıkar: r₂ = y - x̂₁

Aşama 2: Zayıf kullanıcıyı çöz (α₂ = 0.25)
  → SINR₂ = α₂·SNR  (interferans çıkarılmış)
  → ŝ₂ = demodulate(r₂ / √α₂)
```

#### Shannon Kapasite Karşılaştırması

**NOMA kullanıcı kapasitesi:**
```
C₁ = log₂(1 + α₁·SNR / (α₂·SNR + 1))     (güçlü kullanıcı, interferans altında)
C₂ = log₂(1 + α₂·SNR)                       (zayıf kullanıcı, SIC sonrası)
C_NOMA_toplam = C₁ + C₂
```

**OMA kullanıcı kapasitesi (eşit kaynak paylaşımı):**
```
C_OMA_kullanıcı = (1/K) × log₂(1 + SNR)
C_OMA_toplam = log₂(1 + SNR)
```

NOMA, özellikle kanal durumları farklı kullanıcılar arasında toplam kapasiteyi artırır.

### 5.3 Modülasyon Şemaları

Proje üç modülasyon şemasını destekler:

| Modülasyon | Bit/Sembol | Konstelasyon Noktası | Kullanım |
|------------|:----------:|:--------------------:|----------|
| QPSK | 2 | 4 | Düşük SNR, güvenilir |
| 16-QAM | 4 | 16 | Orta SNR, dengeli |
| 64-QAM | 6 | 64 | Yüksek SNR, yüksek veri hızı |

Tüm konstelasyonlar Gray kodlu ve birim enerji normalize edilmiştir.

### 5.4 Yazılım Uygulaması

#### NOMATransmitter Sınıfı (`usrp_noma/noma/transmitter.py`)

```python
from usrp_noma.noma import NOMATransmitter

tx = NOMATransmitter(num_users=2, modulation="QPSK")
combined, orig_bits, orig_symbols = tx.transmit_frame(num_bits=1024)
```

İşlem akışı:
1. `generate_random_bits()` → rastgele bitler
2. `modulate()` → QPSK/QAM sembolleri (Gray kodlu)
3. `allocate_power()` → `signal × √α`
4. `superposition_code()` → sinyalleri topla

#### NOMAReceiver Sınıfı (`usrp_noma/noma/receiver.py`)

```python
from usrp_noma.noma import NOMAReceiver

rx = NOMAReceiver(num_users=2, modulation="QPSK")
noisy = rx.add_awgn(combined, snr_dB=20)
decoded_bits = rx.sic_decode(noisy)
ber = rx.calculate_ber(orig_bits[0], decoded_bits[0])
```

SIC algoritması gücü büyükten küçüğe sıralar, her adımda:
1. Normalize → `r / √αᵢ`
2. Demodulate → ML (minimum uzaklık) karar verici
3. Reconstruct → `modulate(decoded) × √αᵢ`
4. Cancel → `r = r - reconstructed`

#### NOMAnalyzer Sınıfı (`usrp_noma/noma/analyzer.py`)

```python
from usrp_noma.noma import NOMAnalyzer

analyzer = NOMAnalyzer(tx, rx)
analyzer.generate_full_report(save_dir="results")
```

Üretilen çıktılar:

| Dosya | İçerik |
|-------|--------|
| `noma_ber_vs_snr.png` | Her kullanıcının BER eğrisi + teorik QPSK referansı |
| `noma_vs_oma_ber.png` | NOMA/OMA kullanıcı bazlı + ortalama BER karşılaştırma |
| `capacity_comparison.png` | Toplam ve kullanıcı bazlı Shannon kapasitesi |
| `throughput_comparison.png` | Efektif throughput (Mbit/s) karşılaştırma |
| `power_allocation.png` | Güç tahsis dağılımı (bar + pasta grafik) |
| `constellation_tx.png` | Verici superposition coded konstelasyon |
| `constellation_rx.png` | Alıcı tarafı gürültülü konstelasyon |
| `sic_stages.png` | SIC her aşamasındaki sinyal konstelasyonu |
| `noma_ber_results.csv` | BER sayısal sonuçları |
| `capacity_results.csv` | Kapasite sayısal sonuçları |

---

## 6. Frekans Tarama ve Spektrum Analizi

### 6.1 Desteklenen Bantlar

Antenin desteklediği iki frekans bandı:

**Alt Bant (698–960 MHz):**
- LoRaWAN EU 868 MHz, 868.3 MHz, 868.5 MHz
- LoRaWAN US 915 MHz
- GSM 900 UL/DL (890/935 MHz)
- LTE Band 20 DL (796 MHz)

**Üst Bant (1710–2700 MHz):**
- GSM 1800 UL/DL (1710/1805 MHz)
- UMTS Band 1 DL (2140 MHz)
- LTE Band 3 DL (1842.5 MHz)
- LTE Band 7 DL (2655 MHz)
- WiFi 2.4 GHz (Ch1: 2412, Ch6: 2437, Ch11: 2462 MHz)

### 6.2 Tarama Yöntemi

Tarama, merkez frekansını adım adım değiştirip her noktada kısa süreli (varsayılan 50 ms) IQ verisi alarak güç ölçümü yapar.

- Alt bant adımı: 200 kHz
- Üst bant adımı: 1 MHz
- Her adımda FFT tabanlı güç ölçümü
- Eşik üzerindeki sinyaller "aktif" olarak raporlanır

### 6.3 Spektrum Analizi

Welch yöntemi ile Güç Yoğunluk Spektrumu (PSD) hesaplanır:
- Hanning penceresi
- %50 örtüşme (overlap)
- Çift taraflı (two-sided) spektrum
- `scipy.signal.welch` kullanılır

---

## 7. ZMQ Veri Akışı

### 7.1 Mimari

E310'dan host bilgisayara gerçek zamanlı IQ veri aktarımı ZeroMQ PUB/SUB paterni ile sağlanır.

```
USRP E310 (PUB)                    Host PC (SUB)
┌─────────────┐    TCP/5555    ┌─────────────────┐
│ receive_     │──────────────→│ ZMQ SUB Socket  │
│ samples()   │   complex64    │ → callback()    │
│ → zmq.send()│               │ → GNU Radio     │
└─────────────┘               └─────────────────┘
```

### 7.2 GNU Radio Entegrasyonu

ZMQ akışı, GNU Radio'nun `ZMQ SUB Source` bloğu ile doğrudan uyumludur. Host bilgisayarda GNU Radio Companion (GRC) ile görsel akış diyagramları oluşturulabilir.

---

## 8. CLI Arayüzü

`main.py` dosyası `usrp_noma` paketini kullanarak `argparse` tabanlı 12 alt komut sunar:

| Komut | Donanım | Açıklama |
|-------|:-------:|----------|
| `info` | Opsiyonel | Cihaz ve anten bilgisi |
| `capture` | Gerekli | IQ veri yakalama |
| `spectrum` | Gerekli* | FFT spektrum analizi |
| `waterfall` | Gerekli* | Waterfall diyagramı |
| `lora` | Gerekli* | LoRa demodülasyon |
| `generate` | Gerekli | Test sinyali üretme/gönderme |
| `scan` | Gerekli | Frekans band tarama |
| `stream` | Gerekli | ZMQ veri akışı |
| `noma-sim` | Gereksiz | NOMA BER simülasyonu |
| `noma-compare` | Gereksiz | NOMA vs OMA karşılaştırma raporu |
| `noma-constellation` | Gereksiz | Konstelasyon diyagramları |
| `noma-live` | Gerekli | USRP ile gerçek zamanlı NOMA |

*`--input` parametresi ile dosyadan da çalışabilir.

---

## 9. Beklenen Sonuçlar

### 9.1 NOMA BER Performansı

- **Güçlü kullanıcı** (α₁ = 0.75): Düşük SNR'lerde bile düşük BER (interferans altında bile yüksek SINR).
- **Zayıf kullanıcı** (α₂ = 0.25): SIC sonrası interferanssız ortamda çözüldüğü için makul BER (SIC hatalarına duyarlı).
- SNR > 20 dB'de her iki kullanıcı için BER < 10⁻³ beklenir (QPSK).

### 9.2 NOMA vs OMA Karşılaştırma

- NOMA toplam kapasitesi, OMA'dan yüksektir (özellikle kanal farklılıkları büyükken).
- OMA'da her kullanıcı bant genişliğinin 1/K'sini aldığı için efektif SNR düşer.
- NOMA'nın dezavantajı: SIC hata yayılımı ve karmaşıklık.

### 9.3 SIC Hata Yayılımı

İlk aşamada yapılan demodülasyon hatası, yeniden oluşturmada bozulmuş sinyal çıkarılmasına neden olur. Bu hata sonraki aşamalara yayılarak zayıf kullanıcının BER'ini artırır. Bu etki, düşük SNR değerlerinde belirgin olarak gözlemlenir.

---

## 10. Geliştirme Önerileri

1. **Kanal Tahmini**: Gerçek kablosuz ortamda pilot semboller ile kanal katsayısı (h) tahmini eklenmesi.
2. **Frekans Senkronizasyonu**: CFO (Carrier Frequency Offset) düzeltme algoritması.
3. **Adaptif Güç Tahsisi**: Kanal durumuna göre güç katsayılarının dinamik optimize edilmesi.
4. **LDPC/Turbo Kodlama**: İleri hata düzeltme kodları ile BER iyileştirmesi.
5. **MIMO Entegrasyonu**: USRP E310'un çoklu anten desteği ile uzamsal çoklama.
6. **Çok Hücreli NOMA**: Hücreler arası interferans yönetimi.

---

## 11. Sonuç

Bu projede USRP E310 SDR platformu kullanılarak LoRaWAN sinyallerinin yakalanması, analiz edilmesi ve NOMA çoklu erişim tekniğinin uygulanması başarıyla gerçekleştirilmiştir. Python tabanlı modüler yazılım mimarisi sayesinde tüm bileşenler bağımsız çalışabileceği gibi CLI üzerinden birleşik kullanım da mümkündür. NOMA simülasyonları ile BER, kapasite ve throughput analizleri gerçekleştirilmiş, OMA ile karşılaştırmalı sonuçlar grafikler ve CSV dosyaları olarak üretilmiştir. Proje, SDR tabanlı kablosuz iletişim araştırmaları için genişletilebilir bir altyapı sunmaktadır.

---

## 12. Referanslar

1. Ettus Research, "USRP E310 Product Specification," ettus.com.
2. Semtech, "LoRa Modulation Basics," AN1200.22 Application Note.
3. Y. Saito, Y. Kishiyama, A. Benjebbour, T. Nakamura, A. Li, K. Higuchi, "Non-Orthogonal Multiple Access (NOMA) for Cellular Future Radio Access," IEEE VTC, 2013.
4. Z. Ding, Z. Yang, P. Fan, H.V. Poor, "On the Performance of Non-Orthogonal Multiple Access in 5G Systems with Randomly Deployed Users," IEEE Signal Processing Letters, vol. 21, no. 12, 2014.
5. 3GPP, "Study on Non-Orthogonal Multiple Access (NOMA) for NR," TR 38.812.
6. Ebyte, "E220-900T22D Datasheet," ebyte.com.
7. MRTK, "Q7027I28 LTE/4G Antenna Datasheet."
