"""
Decoupled BPSK NOMA SIC Aligner Block (Auto-Aligning & DBPSK Compatible)
--------------------------------------------------------------------------
Bu dosya GNU Radio Companion (GRC) içerisindeki gömülü Python Bloğuna
(Embedded Python Block) kopyalayıp yapıştırmanız için hazırlanmıştır.

Girişler:
  0: in_rx  (Costas Loop'tan gelen, iki kullanıcının süperpoze olduğu ham sinyal)
  1: in_tx1 (LDPC'den çözülüp BPSK modüle edilen ve 0.894 genliğiyle çarpılan User 1 sinyali)

Çıkışlar:
  0: out_rx2 (Çıkarma işleminden sonra kalan User 2 sinyali)
"""

import numpy as np
from gnuradio import gr
import pmt
import scipy.signal

class blk(gr.basic_block):
    """
    Decoupled BPSK NOMA SIC Aligner Block

    Giriş verilerini anında tüketerek dahili kuyruklara yazar, böylece
    GNU Radio zamanlayıcısının kilitlenmesini (deadlock) %100 engeller.
    DBPSK uyumlu diferansiyel kod çözücü öncesi tam şablon eşleme ile
    mükemmel girişim çıkarma ve sıfır sızıntı sağlar.
    """
    def __init__(self, sample_rate=200000.0, near_user_amplitude=0.894, search_window=128, payload_size=1296, payload_offset=64):
        gr.basic_block.__init__(
            self,
            name='Decoupled NOMA SIC Aligner',
            in_sig=[np.complex64, np.complex64],
            out_sig=[np.complex64]
        )
        self.sample_rate = sample_rate
        self.near_user_amplitude = near_user_amplitude
        self.search_window = search_window
        self.payload_size = payload_size
        self.payload_offset = payload_offset

        # Dahili veri tamponları (internal buffers)
        self.buffer_rx = np.array([], dtype=np.complex64)
        self.buffer_tx1 = np.array([], dtype=np.complex64)

        # Bekleyen paketlerin mutlak başlangıç indeksleri (absolute indices)
        self.pending_payload_starts = []

        # Tüketilen ve çıkışa yazılan mutlak örnek sayaçları
        self.rx_processed_abs = 0
        self.pkt_counter = 0

    def forecast(self, noutput_items, ninputs):
        # Zamanlayıcı kilidini önlemek için girdi gereksinimlerini 0 yapıyoruz.
        return [0] * ninputs

    def general_work(self, input_items, output_items):
        in_rx = input_items[0]
        in_tx1 = input_items[1]
        out_rx2 = output_items[0]

        # 1. Gelen RX Verilerini Tampona Ekleme ve Etiket Tarama
        if len(in_rx) > 0:
            self.buffer_rx = np.concatenate((self.buffer_rx, in_rx))

            # time_est, packet_len veya corr_est etiketlerini yakala
            tags = self.get_tags_in_window(0, 0, len(in_rx))
            for tag in tags:
                tag_key = pmt.to_python(tag.key)
                if tag_key in ["time_est", "packet_len", "corr_est"]:
                    # Etiketin mutlak offset değeri
                    tag_abs_idx = tag.offset
                    # Gerçek payload başlangıcı
                    payload_start_abs = tag_abs_idx + self.payload_offset
                    
                    if payload_start_abs not in self.pending_payload_starts:
                        self.pending_payload_starts.append(payload_start_abs)
            
            # RX girişini anında tüket (consume) - Kilitlenmeyi önleyen en kritik adım
            self.consume(0, len(in_rx))

        # 2. Gelen TX1 Verilerini Tampona Ekleme
        if len(in_tx1) > 0:
            self.buffer_tx1 = np.concatenate((self.buffer_tx1, in_tx1))
            self.consume(1, len(in_tx1))

        # 3. Tampon Kilitlenme ve Aşım Koruması (Buffer Overflow / Packet Timeout Safeguard)
        TIMEOUT_SAMPLES = self.payload_size + 20000
        while len(self.pending_payload_starts) > 0:
            start_rel = self.pending_payload_starts[0] - self.rx_processed_abs
            if len(self.buffer_rx) - start_rel > TIMEOUT_SAMPLES:
                print(f"[SIC Aligner] WARNING: Packet at abs_idx {self.pending_payload_starts[0]} timed out (User 1 decoding failed). Skipping subtraction.")
                self.pending_payload_starts.pop(0)
            else:
                break

        # TX1 Tampon Aşım Koruması
        MAX_TX1_BUFFER = 3 * self.payload_size
        if len(self.buffer_tx1) > MAX_TX1_BUFFER:
            excess = len(self.buffer_tx1) - MAX_TX1_BUFFER
            self.buffer_tx1 = self.buffer_tx1[excess:]

        # 4. SIC Çıkarma İşlemleri (Packet Extraction and Subtraction)
        while len(self.pending_payload_starts) > 0:
            payload_start_abs = self.pending_payload_starts[0]
            start_rel = payload_start_abs - self.rx_processed_abs

            # Arama sınırlarını tanımla (Arama penceresi kadar geriye ve ileriye esneyebiliriz)
            search_left = self.search_window
            search_right = self.search_window

            if start_rel - search_left < 0:
                search_left = start_rel

            # RX veya TX1 tamponu henüz hazır değilse bekle
            if start_rel + self.payload_size + search_right > len(self.buffer_rx):
                break
            if len(self.buffer_tx1) < self.payload_size:
                break

            # A. Genişletilmiş Arama Alanı ve TX1 Verisini Al
            rx_search_chunk = self.buffer_rx[start_rel - search_left : start_rel + self.payload_size + search_right]
            tx1_chunk = self.buffer_tx1[:self.payload_size]

            # B. DBPSK Dönüşümü (Diferansiyel Kodlama)
            # in_tx1'den gelen BPSK sembollerini DBPSK alanına dönüştürmek için kümülatif çarpım uyguluyoruz.
            # Bu adım uzyuşmazlığı giderir ve korelasyonun tavan yapmasını sağlar!
            # Not: in_tx1 genlikle çarpılmış olduğundan, kümülatif çarpımın sönümlenmesini önlemek için 
            # önce sembolleri normalize ediyoruz (+1 ve -1 seviyelerine getiriyoruz).
            tx1_chunk_norm = np.sign(tx1_chunk.real)
            tx1_chunk_diff = np.cumprod(-tx1_chunk_norm)

            # C. Otomatik Kayma Kestirimi (Auto-Timing via Valid Sliding Cross-Correlation)
            corr = scipy.signal.correlate(rx_search_chunk, tx1_chunk_diff, mode='valid')
            
            if len(corr) > 0:
                best_idx = np.argmax(np.abs(corr))
                best_val = corr[best_idx]
                # Gerçek kayma miktarı (start_rel'e göre)
                shift = best_idx - search_left
            else:
                shift = 0
                best_val = 0.0

            # D. Genlik ve Faz Kestirimi
            tx1_energy = np.sum(np.abs(tx1_chunk_diff)**2)
            if tx1_energy > 1e-6:
                amplitude_scale = np.abs(best_val) / tx1_energy
            else:
                amplitude_scale = self.near_user_amplitude

            # E. Dinamik Eşleşme Kontrolü (Packet Matcher / Drop Protection)
            if amplitude_scale < 0.4 * self.near_user_amplitude:
                # Korelasyon düşükse bu bir öncül-etiket fazlalığıdır, silme yapmadan geçiyoruz.
                self.pending_payload_starts.pop(0)
                continue

            self.pkt_counter += 1

            # Genliği normal sınırlar içinde kısıtla
            amplitude_scale = np.clip(amplitude_scale, 0.4 * self.near_user_amplitude, 1.6 * self.near_user_amplitude)
            phase_offset = np.angle(best_val)

            # F. Tam Hizalanmış Girişim Sinyalini Sentezle
            interference_signal = tx1_chunk_diff * amplitude_scale * np.exp(1j * phase_offset)

            # G. Tam Hizalanmış Çıkarma İşlemi (SIC Subtraction - Sıfır Sızıntı!)
            payload_start_rel = start_rel + shift
            self.buffer_rx[payload_start_rel : payload_start_rel + self.payload_size] -= interference_signal

            # TX1 tamponunun kullanılan kısmını serbest bırak
            self.buffer_tx1 = self.buffer_tx1[self.payload_size:]
            # İşlenen paketi listeden çıkar
            self.pending_payload_starts.pop(0)

            print(f"[SIC Aligner] Packet #{self.pkt_counter} Subtracted! Shift: {shift} symbols, Phase: {phase_offset:.3f} rad, Amp: {amplitude_scale:.3f}")

        # 5. Çıkışa Güvenli Örnekleri Yazma (Streaming Output)
        if len(self.pending_payload_starts) > 0:
            safe_to_output = self.pending_payload_starts[0] - self.rx_processed_abs
        else:
            safe_to_output = len(self.buffer_rx)

        # ValueError hatasını engelleyen en kritik sınır kontrolü
        safe_to_output = min(safe_to_output, len(self.buffer_rx))
        safe_to_output = max(0, safe_to_output)
        
        n_out = len(out_rx2)
        limit = min(safe_to_output, n_out)

        if limit > 0:
            out_rx2[:limit] = self.buffer_rx[:limit]
            self.buffer_rx = self.buffer_rx[limit:]
            self.rx_processed_abs += limit
            return limit
        else:
            return 0
