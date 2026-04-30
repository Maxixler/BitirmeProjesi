# Sistem Analizi ve Eksiklikler

## Tarih
2026-04-27

## Mevcut Sistem Durumu "claude.grc"

### TX Path (Verici Yolu)
1. **File Source** → `giris.txt` dosyasından veri okuma
2. **Throttle** - Örnekleme hızı kontrolü (50k samples/s)
3. **Stream to Tagged Stream** - 110 byte paketlere bölme
4. **CRC32** - Hata kontrolü (check=False, sadece CRC ekleme)
5. **Scrambler** - 7-bit LFSR (mask: 0x8A, seed: 0x7F)
6. **LDPC Encoder** - n=300, k=152, gap=3
7. **Tagged Stream Multiply Length** - 300/152 oranında genişletme
8. **Tagged Stream Mux** - Header ve payload birleştirme
9. **Repack Bits** - 8→1 bit dönüşümü
10. **Constellation Modulator** - QPSK, differential=True, excess_bw=0.35, sps=4
11. **Channel Model** - Gürültü yok (noise_voltage=0.0)
12. **Virtual Sink** - Loopback için

### RX Path (Alıcı Yolu)
1. **Virtual Source** - Loopback'ten veri alma
2. **Symbol Sync** - QPSK için, TED_SIGNAL_TIMES_SLOPE_ML, loop_bw=0.045
3. **Costas Loop** - 4. derece, w=0.005
4. **Constellation Decoder** - QPSK
5. **Diff Decoder** - Differential decoding
6. **Map** - [0,1,3,2] mapping
7. **Unpack k Bits** - 2 bit unpacking
8. **Correlate Access Code** - 64-bit access code detection, threshold=8
9. **Header Payload Demux** - Header/payload ayrımı
10. **Custom Header Parser** (epy_block_0) - 32-bit header'dan payload uzunluğu çıkarma
11. **Descrambler** - Scrambler ters işlemi
12. **LDPC Decoder** - max_iter=50
13. **Repack Bits** - 1→8 bit dönüşümü
14. **Keep m in n** - 110 byte payload çıkarma (114'ten 110)
15. **File Sink** - `son.txt` dosyasına yazma

## Mevcut Özellikler

| Özellik | Durum | Notlar |
|---------|-------|--------|
| CRC32 | ✅ Var | Sadece ekleme, kontrol yok |
| Scrambler/Descrambler | ✅ Var | 7-bit LFSR |
| LDPC FEC | ✅ Var | n=300, k=152 |
| Header/Payload Yapısı | ✅ Var | 32-bit header |
| Access Code Detection | ✅ Var | 64-bit |
| QPSK Modülasyon | ✅ Var | Differential |
| Symbol Sync | ✅ Var | ML TED |
| Carrier Recovery | ✅ Var | Costas Loop |
| Loopback Test | ✅ Çalışıyor | |

## Tespit Edilen Eksiklikler

### 1. CRC32 Kontrolü
**Durum:** TX'de CRC ekleniyor ama RX'de kontrol yapılmıyor.
- `digital_crc32_bb_0` parametresi `check=False`
- RX tarafında CRC check bloğu yok
- **Öncelik:** Yüksek - Veri bütünlüğü için kritik

### 2. Channel Model Gürültü
**Durum:** `channels_channel_model_0`'da `noise_voltage=0.0`
- Gerçekçi kanal simülasyonu yok
- Sistem sadece ideal koşullarda test ediliyor
- **Öncelik:** Orta - Test kapsamını genişletmek için

### 3. Header Format Tutarlılığı
**Durum:** Header format ve custom parser arasında potansiyel uyumsuzluk
- `variable_header_format_default` kullanılıyor ama RX'de `digital.header_format_default("", 0, 1)` var
- Custom parser (epy_block_0) manuel olarak 32-bit header işliyor
- **Öncelik:** Yüksek - Paket kayıplarına neden olabilir

### 4. Packet Length Hesaplama
**Durum:** `blocks_keep_m_in_n_0` sabit değerler kullanıyor
- m=110, n=114 (CRC32 için 4 byte fark)
- Dinamik paket uzunluğu desteği yok
- **Öncelik:** Orta - Esneklik için

### 5. Access Code Threshold
**Durum:** `digital_correlate_access_code_tag_xx_0` threshold=8
- Gürültülü ortamlarda false positive/false negative riski
- **Öncelik:** Düşük - İdeal koşullarda çalışıyor

### 6. BER (Bit Error Rate) Analizi
**Durum:** BER hesaplama bloğu yok
- Sistem performansını ölçmek için gerekli
- **Öncelik:** Orta - Performans değerlendirmesi için

### 7. Freq Offset ve Phase Noise
**Durum:** Channel model'de freq_offset=0.0
- Gerçek RF sistemlerinde frekans ofseti olur
- **Öncelik:** Düşük - İleri seviye test için

### 8. Paket İstatistikleri
**Durum:** Paket sayısı, başarı/fail oranı gibi metrikler yok
- Sistem performansını izlemek için gerekli
- **Öncelik:** Düşük - Debug için faydalı

### 9. Dinamik Paket Boyutu
**Durum:** Sabit 110 byte paket boyutu
- Değişken boyutlu paket desteği yok
- **Öncelik:** Düşük - Esneklik için

### 10. Interleaving
**Durum:** Interleaver bloğu yok
- Burst hatalarına karşı koruma sağlar
- **Öncelik:** Düşük - İleri seviye özellik

### 11. ARQ (Automatic Repeat reQuest)
**Durum:** ARQ sistemi yok
- Hatalı paketlerin otomatik tekrar gönderilmesi mekanizması yok
- **Öncelik:** Yüksek - Güvenilir iletişim için kritik

## ARQ Sistemi Ekleme Adımları

ARQ sistemi için aşağıdaki bileşenler eklenmelidir:

### Ön Koşullar
ARQ'nun çalışması için önce şu eksiklikler giderilmelidir:
1. **CRC32 Kontrolü** - RX tarafında CRC kontrolü yapılmalı
2. **Header Format Tutarlılığı** - Header yapısı ARQ için genişletilmeli

### Adım 1: Header Yapısını Genişletme ✅ TAMAMLANDI
Mevcut 32-bit header'a ARQ için şu alanlar eklendi:

| Alan | Bit | Açıklama |
|------|-----|---------|
| Sequence Number | 16 bit | Paket sıra numarası (0-65535) |
| ACK/NACK Flag | 1 bit | 0=ACK, 1=NACK |
| Retransmit Count | 3 bit | Yeniden gönderim sayısı (0-7) |
| Reserved | 12 bit | Gelecek kullanım için |

**Yeni Header Format:**
```
[16 bit: Sequence Number] [1 bit: ACK/NACK] [3 bit: Retransmit Count] [12 bit: Reserved]
```

**Yapılan Değişiklikler:**
- `epy_block_0` bloğu `arq_header_parser` olarak güncellendi
- Header parser artık sequence number, ack/nack flag ve retransmit count çıkartıyor
- `header_len` değişkeni eklendi (32 bit)
- Header format değişkenlerine ARQ açıklamaları eklendi

### Adım 2: TX Tarafı Değişiklikleri

#### 2.1 Sequence Number Generator
- **Blok:** Epy Block veya Python bloğu
- **Fonksiyon:** Her paket için artan sequence number ekleme
- **Konum:** CRC32'den önce
- **Parametreler:**
  - Başlangıç değeri: 0
  - Modulo: 65536 (16-bit overflow)

#### 2.2 Retransmission Buffer
- **Blok:** Epy Block
- **Fonksiyon:** Gönderilen paketleri buffer'da saklama
- **Konum:** TX path başında
- **Parametreler:**
  - Buffer boyutu: 64 paket (önerilen)
  - Timeout: 1000ms (önerilen)

#### 2.3 ACK/NACK Processor
- **Blok:** Epy Block
- **Fonksiyon:** RX'den gelen ACK/NACK mesajlarını işleme
- **Konum:** TX path'in sonunda (feedback loop)
- **Davranış:**
  - ACK alınırsa: Buffer'dan paketi sil
  - NACK alınırsa: Paketi tekrar kuyruğa ekle
  - Timeout olursa: Paketi tekrar gönder

### Adım 3: RX Tarafı Değişiklikleri

#### 3.1 CRC32 Check
- **Blok:** `digital_crc32_bb` (check=True)
- **Konum:** Descrambler'dan sonra
- **Davranış:**
  - CRC doğru: ACK gönder
  - CRC hatalı: NACK gönder

#### 3.2 Sequence Number Checker
- **Blok:** Epy Block
- **Fonksiyon:** Sequence number kontrolü
- **Konum:** CRC32 check'ten sonra
- **Davranış:**
  - Beklenen sequence number: ACK
  - Beklenmeyen sequence number: NACK
  - Duplicate paket: Ignore, ACK gönder

#### 3.3 ACK/NACK Generator
- **Blok:** Epy Block
- **Fonksiyon:** ACK/NACK paketi oluşturma
- **Konum:** RX path'in sonunda
- **Çıkış:** TX'e feedback loop üzerinden

### Adım 4: Feedback Loop Oluşturma

TX ve RX arasında feedback loop oluşturulmalı:

```
TX → [Channel] → RX
     ↑              ↓
     ← [Feedback] ←
```

**Feedback Path Bileşenleri:**
1. RX ACK/NACK Generator → TX ACK/NACK Processor
2. Feedback için ayrı bir access code kullanılmalı (örn: 64-bit farklı kod)
3. Feedback paketleri daha kısa olabilir (sadece header + sequence number)

### Adım 5: Timeout Mekanizması

- **Blok:** Epy Block
- **Fonksiyon:** ACK bekleme süresi kontrolü
- **Konum:** TX tarafında
- **Parametreler:**
  - Timeout değeri: 1000ms (önerilen)
  - Maksimum retry: 3 (önerilen)
- **Davranış:**
  - Timeout olursa: Paketi tekrar gönder
  - Maksimum retry'a ulaşırsa: Paketi bırak

### Adım 6: GRC Blok Yapısı

#### TX Path (Güncellenmiş)
```
File Source → Throttle → Stream to Tagged Stream →
[Sequence Number Generator] → CRC32 → Scrambler →
LDPC Encoder → Tagged Stream Multiply Length →
[Retransmission Buffer] → Tagged Stream Mux →
Repack Bits → Constellation Modulator → Channel Model → Virtual Sink
```

#### RX Path (Güncellenmiş)
```
Virtual Source → Symbol Sync → Costas Loop →
Constellation Decoder → Diff Decoder → Map →
Unpack k Bits → Correlate Access Code →
Header Payload Demux → [Custom Header Parser] →
Descrambler → [CRC32 Check] → [Sequence Number Checker] →
[ACK/NACK Generator] → Repack Bits → Keep m in n → File Sink
```

#### Feedback Path (Yeni)
```
RX ACK/NACK Generator → [Feedback Modulator] → [Feedback Channel] →
[Feedback Demodulator] → TX ACK/NACK Processor
```

### Adım 7: Epy Block Kodları

#### 7.1 Sequence Number Generator
```python
class sequence_number_generator(gr.sync_block):
    def __init__(self):
        gr.sync_block.__init__(self, name='seq_num_gen',
                              in_sig=[np.byte], out_sig=[np.byte])
        self.seq_num = 0
        self.pkt_len = 110

    def work(self, input_items, output_items):
        inp = input_items[0]
        out = output_items[0]
        n_items = min(len(inp), len(out))
        for i in range(n_items):
            if i % self.pkt_len == 0:
                # Sequence number'ı header'a ekle
                seq_bytes = self.seq_num.to_bytes(2, 'big')
                out[i] = seq_bytes[0]
                out[i+1] = seq_bytes[1]
                self.seq_num = (self.seq_num + 1) % 65536
            else:
                out[i] = inp[i]
        return n_items
```

#### 7.2 ACK/NACK Generator
```python
class ack_nack_generator(gr.sync_block):
    def __init__(self):
        gr.sync_block.__init__(self, name='ack_nack_gen',
                              in_sig=[np.byte], out_sig=[np.byte])
        self.message_port_register_out(pmt.intern('feedback'))
        self.last_seq_num = -1

    def work(self, input_items, output_items):
        inp = input_items[0]
        # CRC kontrolü sonucuna göre ACK/NACK oluştur
        crc_ok = True  # CRC check bloğundan alınmalı
        seq_num = int.from_bytes(inp[0:2], 'big')
        ack_nack = 0 if crc_ok else 1
        msg = pmt.make_dict()
        msg = pmt.dict_add(msg, pmt.intern('seq_num'), pmt.from_long(seq_num))
        msg = pmt.dict_add(msg, pmt.intern('ack_nack'), pmt.from_long(ack_nack))
        self.message_port_pub(pmt.intern('feedback'), msg)
        return len(inp)
```

#### 7.3 Retransmission Buffer
```python
class retransmission_buffer(gr.sync_block):
    def __init__(self, buffer_size=64, timeout_ms=1000):
        gr.sync_block.__init__(self, name='retrans_buffer',
                              in_sig=[np.byte], out_sig=[np.byte])
        self.buffer = {}
        self.buffer_size = buffer_size
        self.timeout_ms = timeout_ms
        self.message_port_register_in(pmt.intern('ack_nack'))
        self.set_msg_handler(pmt.intern('ack_nack'), self.handle_ack_nack)

    def handle_ack_nack(self, msg):
        seq_num = pmt.to_long(pmt.dict_ref(msg, pmt.intern('seq_num'), pmt.PMT_NIL))
        ack_nack = pmt.to_long(pmt.dict_ref(msg, pmt.intern('ack_nack'), pmt.PMT_NIL))
        if ack_nack == 0:  # ACK
            if seq_num in self.buffer:
                del self.buffer[seq_num]
        else:  # NACK
            # Paketi tekrar gönder
            pass
```

### Adım 8: Test Senaryoları

1. **Normal İşlem:** Paket başarıyla iletilmeli, ACK alınmalı
2. **CRC Hatası:** CRC hatalı paket için NACK gönderilmeli, paket tekrar iletilmeli
3. **Timeout:** ACK gelmezse paket tekrar gönderilmeli
4. **Maksimum Retry:** 3 denemeden sonra paket düşürülmeli
5. **Sequence Number Overflow:** 65535'ten sonra 0'a dönmeli

### Adım 9: Parametre Ayarları

| Parametre | Önerilen Değer | Açıklama |
|-----------|----------------|----------|
| Buffer Size | 64 | Maksimum bekleyen paket sayısı |
| Timeout | 1000ms | ACK bekleme süresi |
| Max Retry | 3 | Maksimum yeniden gönderim |
| Feedback Access Code | Farklı 64-bit | Feedback için ayrı kod |

## Önerilen Ekleme Sırası (Güncellenmiş)

1. **CRC32 Kontrolü** - Veri bütünlüğü için en kritik
2. **Header Format Tutarlılığı** - Paket kayıplarını önlemek için
3. **Sequence Number Generator** - ARQ için gerekli
4. **ACK/NACK Generator** - ARQ için gerekli
5. **Retransmission Buffer** - ARQ için gerekli
6. **Feedback Loop** - ARQ için gerekli
7. **Timeout Mekanizması** - ARQ için gerekli
8. **BER Analizi** - Sistem performansını ölçmek için
9. **Channel Model Gürültü** - Gerçekçi test için
10. **Paket İstatistikleri** - Debug ve izleme için

## Notlar

- Sistem şu anda loopback modunda çalışıyor
- `giris.txt` ve `son.txt` dosyaları test için kullanılıyor
- Custom header parser (epy_block_0) header'dan payload uzunluğunu çıkarıyor
- LDPC kodu: `n_0300_k_0152_gap_03.alist` dosyasından yükleniyor
- ARQ sistemi için feedback loop eklenmesi gerekiyor
- Loopback modunda feedback loop virtual sink/source üzerinden yapılabilir
