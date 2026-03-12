# CLAUDE_PROJECT_CONTEXT.md — USRP E310 LoRaWAN & NOMA Bitirme Projesi

> **Bu dosya, Claude AI'nin bu projeye herhangi bir bilgisayarda, herhangi bir oturumda devam edebilmesi icin hazirlanmistir. Projenin tum teknik detaylarini, dosya yapilarini, siniflarin tum metotlarini, import bagimliliklarini ve gecmis gelistirme kararlarini icerir.**

---

## 1. PROJE OZETI

| Alan | Deger |
|------|-------|
| **Proje Adi** | USRP E310 ile LoRaWAN Sinyal Analizi ve NOMA Coklu Erisim |
| **Tur** | Universite Bitirme Projesi |
| **Yazar** | Eren KALE |
| **Lisans** | MIT |
| **Dil** | Python 3.8+ |
| **Paket Adi** | `usrp_noma` (v1.0.0) |
| **Ana Giris Noktasi** | `main.py` (argparse CLI, 12 alt komut) |

### Proje Amaci
- USRP E310 SDR ile 868 MHz LoRaWAN sinyallerini yakalama ve demodule etme
- 698-960 MHz ve 1710-2700 MHz frekans bantlarinda genis bant tarama
- NOMA (Non-Orthogonal Multiple Access) ile coklu kullanici erisimi simulasyonu ve gercek zamanli testi
- NOMA vs OMA performans karsilastirmasi (BER, kapasite, throughput)

---

## 2. DONANIM

| Bilesen | Model | Detay |
|---------|-------|-------|
| **SDR** | Ettus USRP E310 | Xilinx Zynq SoC, embedded Linux, AD9361 RF, 70 MHz-6 GHz, 56 MHz BW |
| **LoRa Modulu** | Ebyte E220-900T22D | LLCC68 cip, 868-915 MHz, 22 dBm, UART arayuz |
| **Anten** | MRTK-Q7027I28 | 7 dBi, SMA Male, dual-band: 698-960 MHz / 1710-2700 MHz, RG174 3m kablo, 50 ohm, manyetik taban |
| **Host PC** | Linux (Arch) | Ethernet ile baglanir |
| **Baglanti** | Ethernet + USB-Seri | Veri akisi + seri konsol (115200 baud) |

### Ag Topolojisi
```
USRP E310 (eth0: 192.168.10.2) <--- Ethernet ---> Host PC (eno1: 192.168.10.1)
USRP E310 (USB) <--- USB-Seri ---> Host PC (/dev/ttyUSB0, 115200 baud)
Anten (SMA) <--- SMA konnektor ---> USRP E310 (RX2 veya TX/RX portu)
LoRa Modulu (E220-900T22D) --- 868 MHz hava arayuzu ---> Anten ile yakalanir
```

---

## 3. CALISMA MODLARI

| Mod | Aciklama | UHD device_args |
|-----|----------|-----------------|
| `embedded` | Python scripti dogrudan USRP E310 uzerinde calisir | `""` (bos) |
| `network` | Host PC'den Ethernet uzerinden USRP'ye baglanir | `"addr=192.168.10.2"` |

Mod otomatik algilanir: hostname'de "e3" veya "ettus" varsa ya da `/etc/uhd` dizini mevcutsa `embedded`, aksi halde `network`.

---

## 4. DIZIN YAPISI

```
BitirmeProjesi-main/
├── main.py                          # CLI ana giris noktasi (argparse, 12 alt komut)
├── setup.py                         # pip install -e . icin paket kurulum dosyasi
├── requirements.txt                 # numpy>=1.21, scipy>=1.7, matplotlib>=3.4, pyzmq>=22
├── .gitignore                       # Python, IDE, OS, proje ciktilari
├── LICENSE                          # MIT License (Copyright 2025 Eren KALE)
├── README.md                        # Turkce proje dokumantasyonu
├── PROJE_RAPORU.md                  # Akademik proje raporu (12 bolum)
├── CLAUDE_PROJECT_CONTEXT.md        # Bu dosya
│
├── docs/
│   └── antenbilgisi.txt             # MRTK-Q7027I28 anten veri sayfasi
│
├── data/                            # IQ veri dosyalari (.npy + .meta)
├── results/                         # Cikti grafikleri (.png) ve CSV dosyalari
│
└── usrp_noma/                       # Ana Python paketi (v1.0.0)
    ├── __init__.py                  # Paket init: __version__, config/utils import
    ├── config.py                    # Merkezi konfigurasyon (tum parametreler)
    ├── utils.py                     # Yardimci fonksiyonlar (dB, I/O, log, SNR)
    │
    ├── core/                        # Donanim etkilesim katmani
    │   ├── __init__.py              # Lazy import: USRPController, SignalCapture, SignalGenerator
    │   ├── usrp_controller.py       # UHD API ile USRP E310 cihaz yonetimi
    │   ├── signal_capture.py        # IQ veri yakalama (tek + surekli + dosyaya)
    │   └── signal_generator.py      # Test sinyali uretimi (ton, chirp, LoRa, gurultu)
    │
    ├── analysis/                    # Sinyal analiz katmani
    │   ├── __init__.py              # Lazy import: SpectrumAnalyzer, WaterfallDisplay, FrequencyScanner
    │   ├── spectrum_analyzer.py     # Welch/FFT PSD, tepe bulma, canli spektrum
    │   ├── waterfall_display.py     # Waterfall (selale) diyagram, dairesel tampon
    │   └── frequency_scanner.py     # Genis bant frekans tarama, CSV export
    │
    ├── lora/                        # LoRa demodulasyon katmani
    │   ├── __init__.py              # Lazy import: LoRaDecoder
    │   └── decoder.py               # CSS demodulasyon: preamble, dechirp, sembol, payload
    │
    ├── noma/                        # NOMA coklu erisim katmani
    │   ├── __init__.py              # Lazy import: CONSTELLATIONS, NOMATransmitter, NOMAReceiver, NOMAnalyzer
    │   ├── modulation.py            # QPSK/16QAM/64QAM konstelasyon tablolari (Gray, normalize)
    │   ├── transmitter.py           # Verici: modulasyon, guc tahsisi, superposition coding
    │   ├── receiver.py              # Alici: AWGN, SIC (Successive Interference Cancellation), BER
    │   └── analyzer.py              # Monte Carlo sim, NOMA vs OMA, 7 grafik, CSV
    │
    └── streaming/                   # Veri akis katmani
        ├── __init__.py              # Lazy import: ZMQStreamer
        └── zmq_streamer.py          # ZMQ PUB/SUB IQ veri akisi (GNU Radio uyumlu)
```

---

## 5. KATMANLI MIMARI

```
Katman 3 (Uygulama)       main.py (CLI — 12 alt komut, argparse)
                              |
Katman 2 (Isleme)          analysis/ (spektrum, waterfall, tarama)
                            lora/ (CSS demodulasyon)
                            noma/ (verici, alici-SIC, analizci)
                              |
Katman 1 (Veri Erisim)     core/ (yakalama, sinyal uretimi)
                            streaming/ (ZMQ PUB/SUB)
                              |
Katman 0 (Donanim)         core/usrp_controller (UHD Python API)
                              |
Altyapi                    config (tum parametreler)
                           utils (dB, I/O, log, SNR)
```

### Bagimlilik Grafi
```
config ── utils
  │         │
  └────┬────┘
       │
  core/usrp_controller
       │
  ┌────┼────────────────────┐
  │    │                    │
core/ core/           streaming/
signal signal          zmq_streamer
capture generator
  │
  ┌────┼────────┐
  │    │        │
analysis/  analysis/   noma/modulation
spectrum   waterfall  ┌───┴───┐
analyzer   display   noma/    noma/
  │                transmitter receiver
analysis/              │         │
frequency              └────┬────┘
scanner                     │
  │                  noma/analyzer
lora/decoder                │
  │                         │
  └──────────┬──────────────┘
             │
         main.py
```

---

## 6. DOSYA DETAYLARI: HER SINIF VE METOT

### 6.1 `usrp_noma/config.py`
Hicbir sinif yok — sadece sabit degerler. Import: hicbir proje ici import yok.

| Degisken Grubu | Ornekler |
|----------------|----------|
| USRP Ayarlari | `USRP_ADDR="192.168.10.2"`, `HOST_ADDR="192.168.10.1"`, `DEFAULT_MODE="network"`, `DEVICE_ARGS` dict |
| SDR Parametreleri | `DEFAULT_SAMPLE_RATE=1e6`, `DEFAULT_RX_GAIN=40`, `DEFAULT_TX_GAIN=40`, `DEFAULT_CENTER_FREQ=868e6`, `DEFAULT_ANTENNA="TX/RX"`, `DEFAULT_FFT_SIZE=1024`, `DEFAULT_CAPTURE_DURATION=1.0` |
| Anten Bilgileri | `ANTENNA_INFO` dict: model, gain_dBi=7, impedance=50, vswr_max=2.0, power_W=50 |
| Frekans Bantlari | `BAND_LOW` (698-960 MHz), `BAND_HIGH` (1710-2700 MHz), `FREQUENCY_BANDS` listesi |
| Bilinen Frekanslar | `KNOWN_FREQUENCIES` dict: LoRaWAN EU868/915, GSM 900/1800, LTE Band 20/3/7, UMTS, WiFi 2.4G |
| LoRa | `LORA_DEFAULT_SF=7`, `LORA_DEFAULT_BW=125e3`, `LORA_DEFAULT_CR=1`, `LORA_PREAMBLE_LEN=8`, `LORA_SYNC_WORD=0x34` |
| Tarama | `SCAN_STEP_LOW=200e3`, `SCAN_STEP_HIGH=1e6`, `SCAN_DWELL_TIME=0.05`, `SCAN_THRESHOLD_DB=-50` |
| ZMQ | `ZMQ_PORT=5555`, `ZMQ_PROTOCOL="tcp"`, `ZMQ_BIND_ADDR`, `ZMQ_CONNECT_ADDR` |
| NOMA | `NOMA_NUM_USERS=2`, `NOMA_MAX_USERS=4`, `NOMA_POWER_COEFFICIENTS={2:[0.75,0.25], 3:[0.60,0.25,0.15], 4:[0.50,0.25,0.15,0.10]}`, `NOMA_DEFAULT_MODULATION="QPSK"`, `NOMA_BITS_PER_SYMBOL={"QPSK":2,"16QAM":4,"64QAM":6}`, `NOMA_SNR_MIN_DB=-5`, `NOMA_SNR_MAX_DB=30`, `NOMA_SNR_STEP_DB=1`, `NOMA_NUM_SYMBOLS=100000`, `NOMA_BITS_PER_FRAME=1024` |
| Grafik | `PLOT_FIGURE_SIZE=(12,8)`, `PLOT_DPI=150`, `PLOT_OUTPUT_DIR="results"` |

### 6.2 `usrp_noma/utils.py`
Import: `logging`, `os`, `time`, `datetime`, `numpy`. Proje ici import yok.

| Fonksiyon | Imza | Aciklama |
|-----------|------|----------|
| `linear_to_dB(value)` | `float -> float` | 10*log10 (guc icin) |
| `dB_to_linear(value_dB)` | `float -> float` | 10^(x/10) |
| `amplitude_to_dB(value)` | `float -> float` | 20*log10 (genlik icin) |
| `dB_to_amplitude(value_dB)` | `float -> float` | 10^(x/20) |
| `freq_to_str(freq_hz)` | `float -> str` | "868.000 MHz", "2.400 GHz", "125.000 kHz" |
| `save_iq_data(data, filename, sample_rate, center_freq)` | | .npy + .meta dosyasi kayit |
| `load_iq_data(filename)` | `str -> (ndarray, dict)` | .npy + .meta okuma |
| `timestamp_filename(prefix, ext, directory)` | `-> str` | "data/capture_20260313_143025.npy" |
| `setup_logger(name, level)` | `-> Logger` | `[HH:MM:SS] [name] [LEVEL] msg` formati |
| `compute_power_dBm(iq_data, impedance=50)` | `-> float` | dBm cinsinden ortalama guc |
| `estimate_snr(iq_data, signal_bw, sample_rate)` | `-> float` | FFT tabanli SNR tahmini (dB) |

### 6.3 `usrp_noma/core/usrp_controller.py`
Import: `numpy`, `usrp_noma.config`, `usrp_noma.utils.{setup_logger, freq_to_str}`, `uhd` (opsiyonel — import hatasinda None)

**Sinif: `USRPController`** — UHD Python API sarmalayicisi. Context manager destegi (`with` blogu).

| Metot | Aciklama |
|-------|----------|
| `__init__(mode=None, addr=None)` | mode ("embedded"/"network"), addr (IP) |
| `connect()` | uhd.usrp.MultiUSRP olusturur, RX parametreleri ayarlar |
| `device_info() -> dict` | mboard_name, rx_freq, rx_rate, rx_gain, rx_antenna, rx_bandwidth |
| `set_rx_freq(freq) -> float` | TuneRequest ile RX frekans |
| `set_rx_gain(gain) -> float` | RX kazanc (dB) |
| `set_rx_rate(rate) -> float` | RX ornekleme hizi |
| `set_rx_antenna(antenna)` | RX anten portu |
| `set_rx_bandwidth(bw) -> float` | RX analog bant genisligi |
| `set_tx_freq(freq) -> float` | TX frekans |
| `set_tx_gain(gain) -> float` | TX kazanc |
| `set_tx_rate(rate) -> float` | TX ornekleme hizi |
| `set_tx_antenna(antenna)` | TX anten portu |
| `get_rx_stream() -> streamer` | StreamArgs("fc32","sc16"), channels=[0] |
| `get_tx_stream() -> streamer` | Ayni format |
| `receive_samples(num_samples) -> ndarray` | Bloklayici, complex64, overflow/timeout kontrolu |
| `send_samples(samples) -> int` | complex64, end_of_burst sonlandirma |
| `close()` | Tum kaynaklari serbest birakir |
| `__enter__` / `__exit__` | Context manager: connect() / close() |

### 6.4 `usrp_noma/core/signal_capture.py`
Import: `threading`, `time`, `numpy`, `usrp_noma.config`, `usrp_noma.utils.{setup_logger, save_iq_data, timestamp_filename, freq_to_str}`

**Sinif: `SignalCapture(controller)`** — USRPController uzerinden IQ yakalama.

| Metot | Aciklama |
|-------|----------|
| `capture(duration_sec, freq, gain, rate) -> ndarray` | Tek seferlik yakalama |
| `capture_to_file(filename, ...) -> (filepath, data)` | .npy + .meta kayit |
| `continuous_capture(callback, chunk_duration=0.1, freq, gain, rate)` | Thread'de surekli yakalama, `callback(iq_data)` |
| `stop()` | Thread'i durdurur |
| `is_running` (property) | bool |

### 6.5 `usrp_noma/core/signal_generator.py`
Import: `numpy`, `usrp_noma.config`, `usrp_noma.utils.{setup_logger, freq_to_str}`

**Sinif: `SignalGenerator(controller)`**

| Metot | Aciklama |
|-------|----------|
| `generate_tone(freq_offset=10e3, amplitude=0.7, duration=1.0, sample_rate=None) -> ndarray` | CW sinusoidal (complex64) |
| `generate_chirp(bw, duration, is_up=True, sample_rate) -> ndarray` | Lineer chirp |
| `generate_lora_preamble(sf, bw, n_preamble, sample_rate) -> ndarray` | N up-chirp + 2 down-chirp |
| `generate_noise(bandwidth, power_dBm=-30, duration, sample_rate) -> ndarray` | AWGN, 50 ohm |
| `transmit(samples, freq, gain, rate) -> int` | controller.send_samples() |
| `transmit_continuous(generator_func, freq, gain, rate, max_repeats=0)` | Sonsuz/sinirli loop |

### 6.6 `usrp_noma/analysis/spectrum_analyzer.py`
Import: `numpy`, `scipy.signal`, `matplotlib`, `usrp_noma.config`, `usrp_noma.utils.{setup_logger, linear_to_dB, freq_to_str}`

**Sinif: `SpectrumAnalyzer(sample_rate=None, fft_size=None)`**

| Metot | Aciklama |
|-------|----------|
| `compute_psd(iq_data, method="welch") -> (freqs, psd_dB)` | Welch veya temel FFT |
| `find_peaks(freqs, psd_dB, threshold_dB=-50, min_distance=10) -> list` | `scipy.signal.find_peaks` |
| `get_band_power(iq_data, freq_range, center_freq) -> float` | Belirli bantta toplam guc (dB) |
| `plot_spectrum(iq_data, center_freq, title, save_path)` | Statik spektrum grafigi |
| `plot_spectrum_live(capture_obj, center_freq, update_interval=0.5)` | TkAgg canli spektrum |

### 6.7 `usrp_noma/analysis/waterfall_display.py`
Import: `numpy`, `matplotlib`, `matplotlib.colors.Normalize`, `usrp_noma.config`, `usrp_noma.utils.{setup_logger, freq_to_str}`

**Sinif: `WaterfallDisplay(sample_rate=None, fft_size=None, history_size=100)`**
- `waterfall_data`: `(history_size, fft_size)` float32 matris, -120 ile baslatilir
- Dairesel tampon (`_row_index`), `_total_updates` sayaci

| Metot | Aciklama |
|-------|----------|
| `update(iq_data)` | Hanning pencere + FFT + dB, dairesel tampon satiri ekle |
| `get_ordered_data() -> ndarray` | Zaman sirasina gore (eski ustte) |
| `plot(center_freq, title, save_path, vmin=-120, vmax=-20, cmap="viridis")` | imshow waterfall |
| `plot_live(capture_obj, center_freq, update_interval=0.1)` | TkAgg canli waterfall |
| `save_image(filename, center_freq)` | plot() ile PNG kaydi |
| `reset()` | Matrisi sifirla |

### 6.8 `usrp_noma/analysis/frequency_scanner.py`
Import: `csv`, `time`, `datetime`, `numpy`, `usrp_noma.config`, `usrp_noma.utils.{setup_logger, freq_to_str, linear_to_dB, timestamp_filename}`, `usrp_noma.analysis.spectrum_analyzer.SpectrumAnalyzer`

**Sinif: `FrequencyScanner(controller)`**
- `scan_results`: tarama sonuclari listesi `[(freq, power_dB), ...]`
- Dahili `SpectrumAnalyzer` nesnesi

| Metot | Aciklama |
|-------|----------|
| `scan_band(start_freq, stop_freq, step, dwell_time, gain) -> list` | Genel bant tarama |
| `scan_low_band(step, dwell_time) -> list` | 698-960 MHz |
| `scan_high_band(step, dwell_time) -> list` | 1710-2700 MHz |
| `scan_full(dwell_time) -> list` | Iki bant birlestirmis |
| `find_active_signals(threshold_dB, results) -> list` | Esik uzerindekiler, yakin sinyalleri birlestir |
| `plot_scan_results(results, save_path)` | matplotlib grafik + bant/frekans isaretleri |
| `export_results(filename, results) -> str` | CSV export |

### 6.9 `usrp_noma/lora/decoder.py`
Import: `numpy`, `usrp_noma.config`, `usrp_noma.utils.{setup_logger, linear_to_dB}`

**Sinif: `LoRaDecoder(sf=None, bw=None, fs=None)`**
- `n_symbols = 2^sf`, `symbol_duration = n_symbols/bw`, `samples_per_symbol = int(symbol_duration * fs)`

| Metot | Aciklama |
|-------|----------|
| `generate_chirp(is_up=True, sf=None) -> ndarray` | Referans up/down chirp |
| `dechirp(iq_data) -> ndarray` | down_chirp ile carpma, sembol sembol |
| `detect_preamble(iq_data, threshold=0.6) -> list` | Korelasyon, ardisik chirp kontrolu (>=4), 1/4 adim |
| `extract_symbols(iq_data, start_offset) -> list` | dechirp + FFT peak -> sembol degerleri (0..2^SF-1) |
| `decode_header(symbols) -> dict` | payload_length, coding_rate, has_crc, raw_symbols |
| `decode_payload(symbols) -> bytes` | Her 2 sembolden 1 bayt (basitlestirilmis) |
| `estimate_sf(iq_data) -> int` | SF 7-12 icin korelasyon, en iyi uyum |
| `process(iq_data) -> list[dict]` | Tam pipeline: preamble -> sembol -> header -> payload |

### 6.10 `usrp_noma/noma/modulation.py`
Import: `numpy`. Proje ici import yok.

| Deger | Aciklama |
|-------|----------|
| `_qpsk_constellation() -> ndarray` | 4 nokta, Gray kodlu, /sqrt(2) normalize |
| `_qam16_constellation() -> ndarray` | 16 nokta, levels=[-3,-1,1,3], birim enerji normalize |
| `_qam64_constellation() -> ndarray` | 64 nokta, levels=[-7..7], birim enerji normalize |
| `CONSTELLATIONS` dict | `{"QPSK": ..., "16QAM": ..., "64QAM": ...}` |

### 6.11 `usrp_noma/noma/transmitter.py`
Import: `numpy`, `usrp_noma.config`, `usrp_noma.utils.setup_logger`, `usrp_noma.noma.modulation.CONSTELLATIONS`

**Sinif: `NOMATransmitter(num_users=None, power_coefficients=None, modulation=None, sample_rate=None)`**
- `bits_per_symbol`, `constellation`, `power_coefficients` (toplam=1.0, assert kontrollu)

| Metot | Aciklama |
|-------|----------|
| `generate_random_bits(num_bits) -> ndarray` | {0,1} dizisi |
| `modulate(bits) -> ndarray` | Bit grubunu indekse, indeks -> konstelasyon noktasi (complex128) |
| `demodulate_to_bits(symbol, constellation) -> ndarray` | ML: en yakin nokta, indeks -> bit |
| `allocate_power(user_signals) -> list` | Her sinyale `sqrt(alpha_i)` carpani |
| `superposition_code(user_signals) -> ndarray` | Toplama |
| `transmit_frame(user_data_list, num_bits) -> (combined, bits_list, symbols_list)` | Tam pipeline |
| `get_constellation_points() -> ndarray` | Kopya dondurur |

### 6.12 `usrp_noma/noma/receiver.py`
Import: `numpy`, `usrp_noma.config`, `usrp_noma.utils.setup_logger`, `usrp_noma.noma.modulation.CONSTELLATIONS`, `usrp_noma.noma.transmitter.NOMATransmitter`

**Sinif: `NOMAReceiver(num_users=None, power_coefficients=None, modulation=None)`**
- Dahili `_tx = NOMATransmitter(...)` referansi (remodulasyon icin)
- `_last_sic_stages`: SIC ara sinyalleri (analyzer.plot_sic_stages icin)

| Metot | Aciklama |
|-------|----------|
| `add_awgn(signal, snr_dB) -> ndarray` | Kompleks AWGN: sigma = sqrt(P_noise/2) |
| `estimate_snr(signal) -> float` | Konstelasyon mesafesinden SNR tahmini |
| `demodulate(symbols) -> ndarray` | _tx.demodulate_to_bits ile ML cozumleme |
| `sic_decode(received_signal) -> list[ndarray]` | SIC: gucludan zayifa sirayla coz, yeniden olustur, cikar |
| `calculate_ber(original_bits, decoded_bits) -> float` | Bit hata orani |
| `receive_frame(received_signal, original_bits_list) -> dict` | `{"decoded_users", "ber_per_user", "ber_average"}` |

**SIC Algoritmasi Detayi:**
1. Guc katsayilarina gore kullanicilari buyukten kucuge sirala
2. En guclu kullaniciyi normalize et: `residual / sqrt(alpha)`
3. ML demodulasyon
4. Cozulmus sinyali yeniden module et: `modulate(decoded_bits) * sqrt(alpha)`
5. Kalan sinyalden cikar: `residual = residual - reconstructed`
6. Sonraki kullaniciya gec (adim 2'ye don)

### 6.13 `usrp_noma/noma/analyzer.py`
Import: `os`, `numpy`, `scipy.special.erfc`, `matplotlib`, `usrp_noma.config`, `usrp_noma.utils.setup_logger`, `usrp_noma.noma.transmitter.NOMATransmitter`, `usrp_noma.noma.receiver.NOMAReceiver`

**Sinif: `NOMAnalyzer(transmitter=None, receiver=None)`**

| Metot | Aciklama |
|-------|----------|
| `simulate_ber_vs_snr(snr_range_dB, num_symbols) -> dict` | Monte Carlo NOMA BER simulasyonu |
| `simulate_oma_ber_vs_snr(snr_range_dB, num_symbols) -> dict` | OMA BER (efektif SNR = SNR - 10log10(K)) |
| `compare_noma_oma(snr_range_dB, num_symbols) -> dict` | `{"noma": ..., "oma": ...}` |
| `calculate_capacity_noma(snr_dB, power_coefficients) -> list` | Shannon: SINR hesabi, SIC sirasiyla |
| `calculate_capacity_oma(snr_dB, num_users) -> list` | `(1/K) * log2(1 + SNR)` esit paylasim |
| `calculate_throughput(ber, modulation, bandwidth) -> float` | `bps * BW * (1 - BER)` |
| `plot_ber_vs_snr(results, title, save_path)` | Semilogy, her kullanici + ortalama + teorik QPSK referansi |
| `plot_noma_vs_oma_ber(comparison_results, save_path)` | 2 panel: kullanici bazli + ortalama |
| `plot_capacity_comparison(snr_range_dB, save_path)` | 2 panel: toplam + kullanici basi |
| `plot_throughput_comparison(snr_range_dB, save_path)` | Mbit/s cinsinden NOMA vs OMA |
| `plot_constellation(signal, title, save_path)` | scatter + ideal noktalar |
| `plot_power_allocation(save_path)` | Bar + pasta grafik |
| `plot_sic_stages(received_signal, save_path)` | Alinan sinyal + her SIC asamasi konstelasyon |
| `generate_full_report(save_dir)` | Tum 7 grafik + 2 CSV uretir |
| `_export_results_csv(noma_results, comparison, save_dir)` | noma_ber_results.csv + capacity_results.csv |

### 6.14 `usrp_noma/streaming/zmq_streamer.py`
Import: `threading`, `numpy`, `zmq`, `usrp_noma.config`, `usrp_noma.utils.{setup_logger, freq_to_str}`

**Sinif: `ZMQStreamer(port=None, protocol=None, bind_addr=None)`** — Context manager destegi.

| Metot | Aciklama |
|-------|----------|
| `start_publisher(controller, chunk_duration=0.1)` | PUB socket, thread, complex64 tobytes |
| `start_subscriber(host, port, callback)` | SUB socket, thread, `callback(iq_data)` |
| `receive_once(host, port, timeout_ms=5000) -> ndarray/None` | Tek sefer bloklayici alim |
| `stop()` | Thread + socket kapat |
| `close()` | stop() + context.term() |

### 6.15 `main.py`
Import: `argparse`, `os`, `sys`, `numpy`, `usrp_noma.config`, `usrp_noma.utils.{setup_logger, freq_to_str, load_iq_data}`. Diger importlar lazy (fonksiyon icinde).

| Fonksiyon | CLI Komutu | Lazy Import |
|-----------|-----------|-------------|
| `detect_mode()` | — | — |
| `cmd_info(args)` | `info` | `USRPController` |
| `cmd_capture(args)` | `capture` | `USRPController, SignalCapture` |
| `cmd_spectrum(args)` | `spectrum` | `USRPController, SignalCapture, SpectrumAnalyzer` |
| `cmd_waterfall(args)` | `waterfall` | `USRPController, SignalCapture, WaterfallDisplay` |
| `cmd_lora(args)` | `lora` | `USRPController, SignalCapture, LoRaDecoder` |
| `cmd_generate(args)` | `generate` | `USRPController, SignalGenerator` |
| `cmd_scan(args)` | `scan` | `USRPController, FrequencyScanner` |
| `cmd_noma_sim(args)` | `noma-sim` | `NOMATransmitter, NOMAReceiver, NOMAnalyzer` |
| `cmd_noma_compare(args)` | `noma-compare` | `NOMATransmitter, NOMAReceiver, NOMAnalyzer` |
| `cmd_noma_constellation(args)` | `noma-constellation` | `NOMATransmitter, NOMAReceiver, NOMAnalyzer` |
| `cmd_noma_live(args)` | `noma-live` | `USRPController, SignalCapture, NOMATransmitter, NOMAReceiver, NOMAnalyzer` |
| `cmd_stream(args)` | `stream` | `USRPController, ZMQStreamer` |
| `parse_freq(value)` | — | — (K/M/G suffix destegi) |
| `build_parser()` | — | — |
| `main()` | — | — |

---

## 7. IMPORT KALIPLARI

Tum paket ici importlar `usrp_noma.` prefiksi kullanir:
```python
from usrp_noma import config
from usrp_noma.utils import setup_logger, freq_to_str
from usrp_noma.core import USRPController, SignalCapture, SignalGenerator
from usrp_noma.analysis import SpectrumAnalyzer, WaterfallDisplay, FrequencyScanner
from usrp_noma.lora import LoRaDecoder
from usrp_noma.noma import NOMATransmitter, NOMAReceiver, NOMAnalyzer, CONSTELLATIONS
from usrp_noma.streaming import ZMQStreamer
```

**Onemli:** Tum `__init__.py` dosyalari **lazy import** kullanir (`__getattr__` ile). Bu, eksik bagimliliklarda (uhd, scipy, zmq) paketin hata vermeden yuklenebilmesini saglar.

---

## 8. HARICI BAGIMLILIKLAR

| Paket | Kullanim Yeri | Zorunluluk |
|-------|---------------|------------|
| `numpy` | Her yerde — IQ veri, FFT, sinyal isleme | Zorunlu |
| `scipy` | spectrum_analyzer (Welch PSD, find_peaks), noma/analyzer (erfc) | Zorunlu (analiz icin) |
| `matplotlib` | spectrum_analyzer, waterfall_display, noma/analyzer (7 grafik) | Zorunlu (gorsellestime) |
| `pyzmq` | streaming/zmq_streamer (PUB/SUB) | Opsiyonel (streaming kullanilmazsa gerekmez) |
| `uhd` | core/usrp_controller (UHD Python API) | Sistem paketi — sadece USRP bagliyken gerekli |

---

## 9. CLI KULLANIM ORNEKLERI

```bash
# Cihaz bilgisi
python3 main.py info

# IQ yakalama
python3 main.py capture --freq 868e6 --duration 2 --output data/test.npy

# Spektrum
python3 main.py spectrum --freq 868e6 --save results/spectrum.png
python3 main.py spectrum --input data/test.npy --save spectrum.png
python3 main.py spectrum --freq 868e6 --live

# Waterfall
python3 main.py waterfall --freq 868e6 --duration 5 --save results/waterfall.png

# LoRa demodulasyon
python3 main.py lora --freq 868e6 --sf 7 --duration 10
python3 main.py lora --freq 868e6 --auto-sf
python3 main.py lora --input data/lora_capture.npy

# Sinyal uretme
python3 main.py generate --type tone --freq 868e6 --offset 10000
python3 main.py generate --type lora --sf 7
python3 main.py generate --type tone --freq 868e6 --continuous

# Frekans tarama
python3 main.py scan --band low --plot --save results/scan_low.png
python3 main.py scan --band full --export results/scan.csv

# ZMQ akis
python3 main.py stream --role pub --freq 868e6      # USRP uzerinde
python3 main.py stream --role sub --sub-host 192.168.10.2   # Host'ta

# NOMA simulasyon (donanim gerekmez)
python3 main.py noma-sim --users 2 --modulation QPSK
python3 main.py noma-sim --users 3 --modulation 16QAM --snr-min -10 --snr-max 35

# NOMA tam rapor
python3 main.py noma-compare --users 2 --modulation QPSK
# Cikti: results/ altinda 7 PNG + 2 CSV

# NOMA konstelasyon
python3 main.py noma-constellation --snr 20 --users 2

# NOMA gercek zamanli (USRP gerekir)
python3 main.py noma-live --freq 868e6 --users 2 --duration 5
```

---

## 10. TEKNIK KAVRAMLAR SOZLUGU

| Kavram | Aciklama |
|--------|----------|
| **SDR** | Software Defined Radio — yazilimla tanimlanan radyo |
| **UHD** | USRP Hardware Driver — Ettus SDR'lerin C++/Python API'si |
| **IQ** | In-phase/Quadrature — kompleks baseband sinyal temsili |
| **CSS** | Chirp Spread Spectrum — LoRa'nin modulasyon yontemi |
| **SF** | Spreading Factor — LoRa yayilma faktoru (7-12), arttikca menzil artar hiz duser |
| **BW** | Bandwidth — bant genisligi (LoRa icin tipik 125 kHz) |
| **NOMA** | Non-Orthogonal Multiple Access — ortogonal olmayan coklu erisim |
| **OMA** | Orthogonal Multiple Access — OFDMA/TDMA gibi geleneksel yontemler |
| **SIC** | Successive Interference Cancellation — ardisik interferans iptali |
| **Superposition Coding** | Farkli guc seviyelerinde sinyalleri toplama (NOMA verici) |
| **BER** | Bit Error Rate — bit hata orani |
| **SNR** | Signal-to-Noise Ratio — sinyal gurultu orani (dB) |
| **PSD** | Power Spectral Density — guc yogunluk spektrumu |
| **Welch** | Ortalamalanmis periodogram yontemi ile PSD tahmini |
| **FFT** | Fast Fourier Transform — hizli Fourier donusumu |
| **Gray Coding** | Komsu konstelasyon noktalari tek bitten farklidir |
| **ML** | Maximum Likelihood — en buyuk olabilirlik karar verici |
| **AWGN** | Additive White Gaussian Noise — toplamsul beyaz Gauss gurultusu |
| **Shannon Kapasite** | C = log2(1 + SINR) — teorik kanal kapasitesi (bit/s/Hz) |
| **Monte Carlo** | Rastgele ornek ile istatistiksel simulasyon |
| **ZMQ** | ZeroMQ — yuksek performans mesajlasma kutuphanesi |
| **PUB/SUB** | Publisher/Subscriber kalıbı — yayin/abone mesajlasma |

---

## 11. NOMA MATEMATIKSEL MODEL

### Verici (Superposition Coding)
```
x = sqrt(a1)*s1 + sqrt(a2)*s2 + ... + sqrt(aK)*sK
```
- `ai`: Kullanici i'nin guc katsayisi (toplam = 1.0)
- `si`: Kullanici i'nin modüle edilmis sembolu
- Zayıf kanal kullanıcısına daha fazla güç: a1 > a2 > ... > aK

### Kanal (AWGN)
```
y = x + n,   n ~ CN(0, sigma^2)
sigma^2 = P_signal / (10^(SNR_dB/10))
```

### Alıcı (SIC)
```
1. Kullanici 1 (en guclu) cozumlenir: s1_hat = demod(y / sqrt(a1))
2. Yeniden olusturulur: x1_hat = sqrt(a1) * mod(s1_hat)
3. Cikarilir: y' = y - x1_hat
4. Kullanici 2 cozumlenir: s2_hat = demod(y' / sqrt(a2))
... (K kullaniciya kadar)
```

### Varsayılan Güç Katsayıları
- 2 kullanıcı: `[0.75, 0.25]`
- 3 kullanıcı: `[0.60, 0.25, 0.15]`
- 4 kullanıcı: `[0.50, 0.25, 0.15, 0.10]`

### NOMA Kapasite (Shannon)
```
C_user_i = log2(1 + a_i * SNR / (sum(a_j, j>i) * SNR + 1))
```
SIC sırasına göre, güçlüden zayıfa doğru interferans hesaplanır.

### OMA Kapasite (Referans)
```
C_user = (1/K) * log2(1 + SNR)
```
Her kullanıcıya eşit 1/K kaynak paylaşımı.

---

## 12. LORA CSS DEMODULASYON MODELI

### Up-Chirp Üretimi
```
faz(t) = 2*pi * (-BW/2 * t + (BW/T) * t^2 / 2)
chirp(t) = exp(j * faz(t))
```

### Dechirp İşlemi
```
dechirped(t) = received(t) * conj(down_chirp(t))
```
Up-chirp ile down-chirp çarpılınca sabit frekanslı sinüzoidal ortaya çıkar.

### Sembol Çıkarma
1. Dechirp uygula (down-chirp ile çarp)
2. FFT al
3. Tepe frekans indeksi = sembol değeri (0 .. 2^SF-1)

### Preamble Tespiti
- Referans up-chirp ile korelasyon, eşik > 0.6
- Ardışık en az 4 chirp kontrolü
- 1/4 sembol adımla kayar pencere tarama

---

## 13. GELISTIRME GECMISI VE KARARLAR

### Oturum 1: Temel Dosyaların Oluşturulması
- 11 Python dosyası düz (flat) yapıda oluşturuldu
- config.py, utils.py, usrp_controller.py, signal_capture.py, signal_generator.py, spectrum_analyzer.py, waterfall_display.py, frequency_scanner.py, lora_decoder.py, zmq_streamer.py, main.py

### Oturum 2: NOMA Eklenmesi
- noma.py oluşturuldu (1106 satır, 3 sınıf: NOMATransmitter, NOMAReceiver, NOMAnalyzer)
- main.py'ye 4 yeni alt komut eklendi: noma-sim, noma-compare, noma-constellation, noma-live

### Oturum 3: Dokümantasyon
- README.md ve PROJE_RAPORU.md oluşturuldu

### Oturum 4: Paket Yapısına Geçiş
- Kullanıcı isteği: "dosyalar çok ayrık ayrık oldu, bitirme projesine layık bir şekilde klasörle"
- `usrp_noma/` paket yapısı tasarlandı ve uygulandı
- noma.py 4 dosyaya bölündü: modulation.py, transmitter.py, receiver.py, analyzer.py
- Tüm importlar `usrp_noma.` prefiksi ile güncellendi
- `__init__.py` dosyaları lazy import kullanacak şekilde yazıldı (eksik bağımlılıklarda hata vermez)
- Eski düz dosyalar silindi, setup.py oluşturuldu, .gitignore eklendi
- antenbilgisi.txt -> docs/ taşındı
- README.md ve PROJE_RAPORU.md yeni yapıya göre güncellendi
- Tüm dosyalar py_compile ile derleme testi yapıldı — hatasız
- NOMA pipeline (TX->AWGN->SIC->BER) çalışma zamanında test edildi — başarılı

### Tasarım Kararları
1. **Lazy import (`__getattr__`)** kullanıldı çünkü: `uhd`, `scipy`, `zmq` her ortamda yüklü olmayabilir. Import zamanında değil, kullanım zamanında hata verilir.
2. **UHD import try/except** ile sarıldı: `uhd` bulunamazsa None atanır, sadece gerçek donanım erişiminde hata verilir.
3. **matplotlib.use("Agg")** analiz/noma modüllerinde global olarak ayarlandı: headless ortamda (SSH, E310 üzerinde) GUI hatası önlenir. Canlı gösterime geçildiğinde TkAgg'ye geçilir.
4. **Dairesel tampon** waterfall_display'de kullanıldı: sabit bellek kullanımı (history_size * fft_size).
5. **Gray kodlama** QPSK/16QAM/64QAM konstelasyonlarında: komşu noktalar tek bit farklı, BER düşer.
6. **context manager** USRPController ve ZMQStreamer'da: kaynak sızıntısı önlenir.

---

## 14. BILINEN SINIRLAMALAR VE GELECEK GELISTIRME ALANLARI

### Mevcut Sınırlamalar
1. LoRa decoder basitleştirilmiştir — Gray coding, interleaving, FEC uygulanmaz
2. NOMA alıcıda mükemmel SIC varsayılır (gerçek ortamda hata yayılımı olur)
3. Kanal modeli sadece AWGN — Rayleigh/Rician fading desteklenmez
4. Frekans taramada tuner yerleşme süresi sabit 10ms — gerçek değer cihaza göre değişir
5. ZMQ akışında metadata (frekans, gain vb.) iletilmez — sadece raw IQ

### Olası Geliştirmeler
- OFDM-NOMA entegrasyonu
- Rayleigh fading kanal modeli ekleme
- LoRa decoder'a tam FEC ve CRC kontrolü ekleme
- Web tabanlı dashboard (Flask/Streamlit)
- GNU Radio Companion (GRC) flowgraph entegrasyonu
- Gerçek zamanlı BER ölçümü ile adaptif güç tahsisi

---

## 15. HIZLI REFERANS: DOSYA SATIRLARI VE BOYUTLARI

| Dosya | Satir | Sinif/Fonksiyon |
|-------|-------|-----------------|
| `config.py` | 156 | Sabit degerler |
| `utils.py` | 194 | 11 fonksiyon |
| `core/usrp_controller.py` | 258 | USRPController (20 metot) |
| `core/signal_capture.py` | 156 | SignalCapture (5 metot) |
| `core/signal_generator.py` | 222 | SignalGenerator (6 metot) |
| `analysis/spectrum_analyzer.py` | 207 | SpectrumAnalyzer (5 metot) |
| `analysis/waterfall_display.py` | 198 | WaterfallDisplay (7 metot) |
| `analysis/frequency_scanner.py` | 274 | FrequencyScanner (7 metot) |
| `lora/decoder.py` | 297 | LoRaDecoder (8 metot) |
| `noma/modulation.py` | 48 | 3 fonksiyon + CONSTELLATIONS dict |
| `noma/transmitter.py` | 180 | NOMATransmitter (8 metot) |
| `noma/receiver.py` | 199 | NOMAReceiver (6 metot) |
| `noma/analyzer.py` | 704 | NOMAnalyzer (14 metot) |
| `streaming/zmq_streamer.py` | 185 | ZMQStreamer (6 metot) |
| `main.py` | 685 | 14 fonksiyon |

---

*Bu dosya Claude AI tarafindan olusturulmustur. Proje uzerinde calismaya devam etmek icin bu dosyayi Claude'a okutmaniz yeterlidir.*
