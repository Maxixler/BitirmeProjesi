# Packet Communication Loopback Simülasyonu - Proje Durum Raporu

> **GNU Radio Companion Versiyonu:** 3.10.12.0  
> **Dosya:** `untitled.grc` / `untitled.py`  
> **Son Güncelleme:** 2026-04-23

---

## 1. Genel Bakış

QPSK modülasyonu ile **Scrambler** ve **LDPC** kanal kodlaması kullanan bir **paket haberleşme loopback simülasyonu**. Verici (TX) ve alıcı (RX) arasında fiziksel donanım kullanılmaz; sinyal bir **kanal modeli** bloğu üzerinden geçirilir. Giriş olarak `giris.txt` dosyasından metin okunur, paketlenir, kodlanır, modüle edilir, demodüle edilir, kodu çözülür ve `son.txt` dosyasına yazılır.

---

## 2. Değişkenler (Variables)

| Değişken | Değer | Açıklama |
|---|---|---|
| `samp_rate` | `1,000,000` (1 MHz) | Örnekleme hızı |
| `packet_len` | **`110`** byte | Her paketin boyutu (LDPC k=152 ile uyumlu: (110+4)×8=912=6×152) |
| `qpsk` | `constellation_rect` | QPSK: noktalar `[-1-1j, -1+1j, 1+1j, 1-1j]`, symbol map `[0, 1, 3, 2]` (Gray kodlu) |
| `hdr_format` | `header_format_default` | 64-bit erişim kodu, **`bps=1`**, `threshold=0` |
| `ldpc_enc_def` | `ldpc_encoder` | LDPC kodlayıcı — `n_0300_k_0152_gap_03.alist`, dim1=1 |
| `ldpc_dec_def` | `ldpc_decoder` | LDPC kod çözücü — aynı matris, `max_iter=50`, dim1=4 |

### Erişim Kodu (Access Code)
```
1010101011110000101010101111000010101010111100001010101011110000
```
64-bit, `hdr_format` ve `correlate_access_code` bloklarında aynı.

---

## 3. LDPC Matrisi

**Dosya:** `n_0300_k_0152_gap_03.alist`

| Parametre | Değer |
|---|---|
| Kod uzunluğu (n) | 300 |
| Bilgi uzunluğu (k) | 152 |
| Kod oranı (R) | 0.507 |
| Format | AList (seyrek matris) |

### Paket/LDPC Uyumu
```
packet_len = 110 byte
CRC sonrası = 114 packed byte
Unpack sonrası = 912 bit
912 ÷ 152 = 6 codeword (TAM BÖLÜNÜR ✓)
FEC çıkış = 6 × 300 = 1800 bit
```

---

## 4. Sinyal Akış Şeması (Flowgraph)

### 4.1. Verici (TX) Pipeline

```
File Source (giris.txt)
    │  byte stream, repeat=True
    ▼
Throttle (1 MHz)
    │
    ▼
Stream to Tagged Stream
    │  packet_len=110, tag="packet_len"
    ▼
CRC32 (ekleme, packed=True)
    │  +4 byte CRC → 114 packed byte/paket, tag=114
    ▼
Repack Bits (8→1)                    
    │  114 packed → 912 unpacked byte
    │  len_tag_key="packet_len", tag=912
    ▼
Scrambler
    │  mask=0x8A, seed=0x7F, len=7
    │  912 unpacked byte (bit-level XOR)
    ▼
FEC Extended Encoder (LDPC)
    │  puncpat='11', capillary threading
    │  912 bit → 6 codeword → 1800 bit
    │
    ├──────────────────────────────────────┐
    │                                      │
    ▼                                      ▼
Protocol Formatter                    (payload data)
    │  hdr_format (bps=1)                  │
    │  Access code (64 bit) +              │
    │  Header data (32 bit) =              │
    │  96 unpacked byte                    │
    ▼                                      │
Tagged Stream Mux  ◄───────────────────────┘
    │  lengthtagname="packet_len"
    │  [header(96) | payload(1800)] = 1896 byte
    ▼
Repack Bits (1→8)                    
    │  1896 unpacked → 237 packed byte
    │  len_tag_key="packet_len"
    ▼
Constellation Modulator (QPSK)
    │  differential=False, sps=4, excess_bw=0.35
    ▼
Multiply Const (×0.5)
    │  güç ayarı
    ▼
Channel Model
    │  noise=0.0, freq_offset=0.0
    │  epsilon=1.0, taps=[1.0], block_tags=False
    ▼
Virtual Sink  →→→  Virtual Source
```

### 4.2. Alıcı (RX) Pipeline

```
Virtual Source
    │  complex samples
    ▼
Symbol Sync (Polyphase Clock Recovery)
    │  TED: SIGNAL_TIMES_SLOPE_ML
    │  sps=4, loop_bw=0.045
    │  nfilters=128, IR_MMSE_8TAP
    ▼
Costas Loop (4th order)
    │  loop_bw=0.0628 (2π/100)
    │  QPSK faz kurtarma
    ▼
Constellation Soft Decoder
    │  QPSK → float soft bits
    ▼
Correlate Access Code (Float TS)
    │  64-bit access code, threshold=1
    │  tagname="packet_len"
    ▼
Header/Payload Demux
    │  header_len=32, items_per_symbol=1
    │  type=float, trigger_tag_key="packet_len"
    │
    ├── Port 0 (Header) ──────────────────┐
    │                                      ▼
    │                    Multiply Const (×-1.0)
    │                                      │
    │                                      ▼
    │                           Binary Slicer (float→byte)
    │                                      │
    │                                      ▼
    │                           Protocol Parser
    │                                      │
    │                                  msg "info"
    │                                      │
    │                           ◄──────────┘
    │                     (header_data feedback)
    │
    └── Port 1 (Payload)
         │  float soft bits (1800 items)
         ▼
    FEC Extended Decoder (LDPC)
         │  max_iter=50, capillary
         │  1800 → 912 decoded bits
         ▼
    Descrambler
         │  mask=0x8A, seed=0x7F, len=7
         ▼
    Repack Bits (1→8)
         │  len_tag_key="packet_len"
         │  912 unpacked → 114 packed byte
         ▼
    Keep M in N
         │  m=110, n=114, offset=0
         │  4 byte CRC'yi kırpar
         ▼
    File Sink (son.txt)
```

---

## 5. Blok Detayları

### 5.1. Verici Blokları

| Blok | Tip | Kritik Parametreler |
|---|---|---|
| `blocks_file_source_0` | File Source | `giris.txt`, byte, repeat=True |
| `blocks_throttle2_0` | Throttle | 1 MHz, ignore tag=True |
| `blocks_stream_to_tagged_stream_0` | Stream→Tagged | len=91, key="packet_len" |
| `digital_crc32_bb_0` | CRC32 | check=False (ekleme), **packed=True** |
| `blocks_repack_bits_bb_0_0_0` | **Repack Bits** | **k=8, l=1**, len_tag_key="packet_len" |
| `digital_scrambler_bb_0` | Scrambler | mask=0x8A, seed=0x7F, len=7 |
| `fec_extended_encoder_0` | LDPC Encoder | capillary threading, puncpat='11' |
| `digital_protocol_formatter_bb_0` | **Protocol Formatter** | hdr_format (bps=1), len_tag_key="packet_len" |
| `blocks_tagged_stream_mux_0` | Mux | **lengthtagname="packet_len"**, ninputs=2 |
| `blocks_repack_bits_bb_0_0` | **Repack Bits** | **k=1, l=8**, len_tag_key="packet_len" |
| `digital_constellation_modulator_0` | QPSK Mod | diff=False, sps=4, bw=0.35 |
| `blocks_multiply_const_vxx_0` | Gain | ×0.5 |

### 5.2. Kanal

| Blok | Tip | Kritik Parametreler |
|---|---|---|
| `channels_channel_model_0` | Channel Model | noise=0, freq=0, eps=1.0, taps=[1.0], block_tags=False |

### 5.3. Alıcı Blokları

| Blok | Tip | Kritik Parametreler |
|---|---|---|
| `digital_symbol_sync_xx_0` | Symbol Sync | CC, TED_SIGNAL_TIMES_SLOPE_ML, sps=4 |
| `digital_costas_loop_cc_0` | Costas Loop | order=4 (QPSK), bw=0.0628 |
| `digital_constellation_soft_decoder_cf_0` | Soft Decoder | QPSK, npwr=-1 |
| `digital_correlate_access_code_xx_ts_0` | Correlate AC | float, threshold=1, tagname=packet_len |
| `digital_header_payload_demux_0` | HPD | **header_len=32**, items_per_symbol=1, float |
| `blocks_multiply_const_vxx_1` | Multiply Const | **×(-1.0)** (soft bit polarite düzeltme) |
| `digital_binary_slicer_fb_0` | Binary Slicer | float→byte |
| `digital_protocol_parser_b_0` | Protocol Parser | hdr_format |
| `fec_extended_decoder_0` | LDPC Decoder | max_iter=50, capillary |
| `digital_descrambler_bb_0` | Descrambler | mask=0x8A, seed=0x7F, len=7 |
| `blocks_repack_bits_bb_0` | Repack Bits | k=1, l=8, **len_tag_key="packet_len"** |
| `blocks_keep_m_in_n_0` | Keep M in N | **m=110**, **n=114** (4 byte CRC'yi kaldırır) |
| `blocks_file_sink_0` | File Sink | `son.txt`, byte |

---

## 6. Bağlantılar (Connections)

### TX Zinciri
```
file_source → throttle → stream_to_tagged → crc32
  → repack(8→1) → scrambler → fec_encoder
  → protocol_formatter → tagged_stream_mux (input 0)
  → fec_encoder → tagged_stream_mux (input 1)
  → tagged_stream_mux → repack(1→8) → constellation_modulator
  → multiply_const(×0.5) → channel_model → virtual_sink
```

### RX Zinciri
```
virtual_source → symbol_sync → costas_loop → soft_decoder
  → correlate_access_code → header_payload_demux
  → (port 0) multiply_const(×-1) → binary_slicer → protocol_parser → msg→demux
  → (port 1) fec_decoder → descrambler → repack(1→8) → keep_m_in_n → file_sink
```

---

## 7. Debug Görselleştirme Blokları

| Blok | Bağlantı Noktası | Görselleştirme |
|---|---|---|
| `qtgui_time_sink_x_0_0_0` | Soft decoder çıkışı | "correlate access code giriş" |
| `qtgui_time_sink_x_0_0` | Correlate AC çıkışı | "correlate access code çıkış" |
| `qtgui_time_sink_x_0` | HPD payload çıkışı | "demux çıkış" |
| `qtgui_sink_x_0` | Costas Loop çıkışı | Frekans/Zaman/Constellation |

---

## 8. Yapılan Değişiklikler (Changelog)

### Oturumda yapılan düzeltmeler (2026-04-23):

| # | Değişiklik | Önceki | Yeni | Neden |
|---|---|---|---|---|
| 1 | CRC32 packed | False | **True** | Girdi packed byte, CRC packed olarak işlemeli |
| 2 | Repack (8→1) eklendi | — | **blocks_repack_bits_bb_0_0_0** | CRC32 packed çıkışı → Scrambler unpacked girişi dönüşümü |
| 3 | Repack (1→8) eklendi | — | **blocks_repack_bits_bb_0_0** | Mux unpacked çıkışı → Modulator packed girişi dönüşümü |
| 4 | hdr_format bps | 1→2→**1** | **1** | Header ve payload aynı formatta (1 bit/byte) olmalı |
| 5 | header_payload_demux header_len | 32→16→**32** | **32** | bps=1 ile header 32 bit = 32 float item |
| 6 | Tüm Repack blokları len_tag_key | `""` | **`"packet_len"`** | Tagged stream tag'larının propagasyonu için zorunlu |
| 7 | packet_len | 91 | **110** | Byte-Shift Hatası: (110+4)×8=912 bit (114 byte). FEC çıkışı 1800 bit = Tam 225 byte. |
| 8 | tagged_stream_mux lengthtagname | `""` | **`"packet_len"`** | Mux'un paket sınırlarını tanıması için zorunlu |
| 9 | packet_headergenerator | Silindi | **protocol_formatter_bb** | Yeni header formatter bloğu |
| 10 | Multiply Const (×-1) | — | Header path'e eklendi | Soft bit polarite düzeltme |
| 11 | Keep M in N Bloğu | — | RX çıkışına Eklendi | CRC bitlerini (4 byte) dosyaya yazılmadan önce silmek için. |

---

## 9. Giriş/Çıkış Dosyaları

| Dosya | Boyut | Açıklama |
|---|---|---|
| `giris.txt` | 67,886 byte | Lorem ipsum metin (225 satır) |
| `son.txt` | Henüz test edilmedi | Demodüle/decode edilen çıkış |
| `n_0300_k_0152_gap_03.alist` | 7,498 byte | LDPC parity-check matrisi |

---

## 10. Paket Boyut Hesabı

```
packet_len = 110 byte
  │
  ▼ CRC32 (+4 byte)
114 packed byte (tag=114)
  │
  ▼ Repack (8→1)
912 unpacked byte (tag=912)
  │
  ▼ Scrambler (uzunluk değişmez)
912 unpacked byte
  │
  ▼ LDPC Encoder (k=152, n=300)
6 codeword × 300 = 1800 unpacked byte (tag=1800)
  │
  ├─→ Protocol Formatter: 64 AC + 32 header = 96 byte header
  │
  ▼ Tagged Stream Mux
96 + 1800 = 1896 unpacked byte
  │
  ▼ Repack (1→8)
1896/8 = 237 packed byte
  │
  ▼ QPSK Modulator (2 bit/symbol, sps=4)
237 × 8 / 2 = 948 QPSK symbol × 4 = 3792 complex sample
  │
  ▼ ×0.5 → Channel → RX
```

---

## 11. Mermaid Diagram — Güncel Sinyal Akışı

```mermaid
graph TD
    subgraph TX ["Verici (TX)"]
        A["📄 File Source<br/>giris.txt"] --> B["⏱ Throttle<br/>1 MHz"]
        B --> C["🏷 Stream→Tagged<br/>packet_len=110"]
        C --> D["🔒 CRC32<br/>packed=True, +4 byte"]
        D --> RP1["🔧 Repack 8→1<br/>114→912 byte"]
        RP1 --> E["🔀 Scrambler<br/>0x8A/0x7F/7"]
        E --> F["📡 LDPC Encoder<br/>912→1800 bit"]
        F --> G["📋 Protocol Formatter<br/>bps=1, 96 byte header"]
        F --> H["📦 Tagged Stream Mux<br/>lengthtagname=packet_len"]
        G --> H
        H --> RP2["🔧 Repack 1→8<br/>1896→237 byte"]
        RP2 --> I["📻 QPSK Modulator<br/>diff=False, sps=4"]
        I --> J["✖ ×0.5"]
    end

    subgraph CH ["Kanal"]
        J --> K["📡 Channel Model<br/>noise=0, ideal"]
    end

    subgraph RX ["Alıcı (RX)"]
        K --> L["⏱ Symbol Sync<br/>sps=4"]
        L --> M["🔄 Costas Loop<br/>order=4"]
        M --> N["📊 Soft Decoder<br/>QPSK→float"]
        N --> O["🔍 Correlate AC<br/>threshold=1"]
        O --> P["📦 Header/Payload Demux<br/>header_len=32"]
        P -->|Header| Q0["✖ ×(-1)"]
        Q0 --> Q["✂ Binary Slicer"]
        Q --> R["📋 Protocol Parser"]
        R -.->|msg: info| P
        P -->|Payload| S["📡 LDPC Decoder<br/>max_iter=50"]
        S --> T["🔀 Descrambler<br/>0x8A/0x7F/7"]
        T --> U["🔧 Repack 1→8<br/>912→114 byte"]
        U --> V1["✂ Keep M in N<br/>m=110, n=114"]
        V1 --> V["📄 File Sink<br/>son.txt"]
    end
```

---

## 12. Bilinen Sorunlar / İzlenmesi Gerekenler

### 12.1. Costas Loop Faz Belirsizliği
- `differential=False` → Costas Loop 4 farklı fazda kilitlenebilir (0°, 90°, 180°, 270°)
- İdeal kanalda (noise=0) sorun olmamalı ama gürültü eklenince risk oluşur
- Çözüm: differential encoding veya pilot sembolleri

### 12.2. Channel Model block_tags=False
- TX tarafı tag'ları RX'e sızıyor
- `correlate_access_code` yanlış tag'larla karışabilir
- Potansiyel çözüm: `block_tags=True` yap

### 12.3. Multiplicative Descrambler Senkronizasyon Kaybı (Sync Loss)
- `digital_scrambler_bb` ve `descrambler_bb` blokları Multiplicative (kendini senkronize eden) tiptedir ve senkronizasyon için 7 bit'e ihtiyaç duyarlar.
- RX simülasyonu başlarken Costas Loop oturana kadar ilk paket (Packet 0) kaybolur. Bu nedenle RX Descrambler'ın durumu (state), TX Scrambler'ın durumundan 912 bit geride kalır.
- Bu senkronizasyon eksikliği, başarılı alınan ilk paketin ve **her ardışık paketin ilk byte'ında** kalıcı 1 byte'lık bozulmaya (garbage data) neden olmaktadır.
- Bu hata LDPC kod çözücüden *sonra* gerçekleştiği için FEC bunu düzeltemez. Çözüm olarak ileride "Dummy Byte" eklentisi (Python Block) düşünülebilir.

---

## 13. Yapılacaklar Listesi (Kayıpsız İletim ARQ Protokolü)

Alıcı paketi aldıktan sonra doğruluğunu teyit edip, başarılıysa yeni paketi isteyeceği (Wi-Fi/Bluetooth mantığında) tam kayıpsız bir haberleşme mimarisi kurmak için izlenecek adımlar:

1. **RX Tarafında Paket Doğrulama (CRC Check):** 
   - Şu an sadece kırpılıp atılan 4 byte'lık CRC verisinin, alıcıda `digital_crc32_bb` (veya benzeri bir Python bloğu) ile gerçekten kontrol edilerek paketin sağlam (hatasız) ulaşıp ulaşmadığının tespit edilmesi.

2. **Geri Besleme Kanalı (Reverse Channel / ACK-NACK):** 
   - Alıcıdan (RX) vericiye (TX) doğru çalışan, sadece onay mesajlarını (ACK: Başarılı, NACK: Hatalı) iletecek düşük veri hızlı ikinci bir haberleşme kanalının (veya message passing yapısının) kurulması.

3. **Verici Durum Makinesi (Stop-and-Wait ARQ):**
   - TX tarafındaki dosya okuma mantığının değiştirilmesi. Vericinin bir paketi gönderdikten sonra durup alıcıdan `ACK` beklemesi; `ACK` gelirse bir sonraki pakete geçmesi, hata mesajı veya zaman aşımı (timeout) olursa aynı paketi tekrar göndermesi.

4. **Paket Sıra Numaraları (Sequence Numbering):**
   - Header yapısına (Protocol Formatter) paket sıra numaralarının eklenmesi. Böylece alıcının aynı paketi (retransmission durumunda) yanlışlıkla iki kez dosyaya yazmasının önüne geçilmesi.

5. **Gürültülü Ortamda Kayıpsızlık Testi:**
   - Kanal modeline bilinçli olarak gürültü (`noise_voltage > 0`) eklenip paket düşmeleri yaratılarak, sistemin kendi kendini toparlayıp `son.txt` dosyasını `giris.txt` ile %100 aynı (lossless) şekilde oluşturduğunun kanıtlanması.

---

*Bu döküman, `untitled.grc` flowgraph dosyasının güncel analizi ile oluşturulmuştur.*
