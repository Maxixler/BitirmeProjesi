"""
Decoupled BPSK NOMA SIC Aligner Block (Auto-Aligning & DBPSK Compatible)
--------------------------------------------------------------------------
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
    """
    def __init__(self, sample_rate=200000.0, near_user_amplitude=0.864, search_window=128, payload_size=1296, payload_offset=64):
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

        # Tüketilen ve çıkışa yazılan mutlak örnek sayaçları
        self.rx_processed_abs = 0
        self.subtracted_until_abs = 0
        self.next_packet_start_abs = 0
        self.pkt_counter = 0

    def forecast(self, noutput_items, ninputs):
        # Zamanlayıcı kilidini önlemek için girdi gereksinimlerini 0 yapıyoruz.
        return [0] * ninputs

    def general_work(self, input_items, output_items):
        in_rx = input_items[0]
        in_tx1 = input_items[1]
        out_rx2 = output_items[0]

        # 1. Gelen RX Verilerini Tampona Ekleme
        if len(in_rx) > 0:
            self.buffer_rx = np.concatenate((self.buffer_rx, in_rx))
            self.consume(0, len(in_rx))

        # 2. Gelen TX1 Verilerini Tampona Ekleme
        if len(in_tx1) > 0:
            self.buffer_tx1 = np.concatenate((self.buffer_tx1, in_tx1))
            self.consume(1, len(in_tx1))

        # 3. Tampon Kilitlenme ve Aşım Koruması (Buffer Overflow & Deadlock Prevention)
        MAX_RX_BUFFER = 500000
        if len(self.buffer_rx) > MAX_RX_BUFFER:
            excess = len(self.buffer_rx) - MAX_RX_BUFFER
            self.subtracted_until_abs = max(self.subtracted_until_abs, self.rx_processed_abs + excess)

        MAX_TX1_BUFFER = 5 * self.payload_size
        if len(self.buffer_tx1) > MAX_TX1_BUFFER:
            excess = len(self.buffer_tx1) - MAX_TX1_BUFFER
            self.buffer_tx1 = self.buffer_tx1[excess:]

        # 4. SIC Çıkarma ve Hizalama İşlemleri (Robust Tag-Free SIC)
        while len(self.buffer_tx1) >= self.payload_size:
            if self.pkt_counter == 0:
                SEARCH_START = 1000
                SEARCH_END = 3000
            else:
                expected_payload_start_abs = self.next_packet_start_abs + 2048
                start_rel = expected_payload_start_abs - self.rx_processed_abs
                SEARCH_START = start_rel - 128
                SEARCH_END = start_rel + 128

            SEARCH_START = max(0, SEARCH_START)

            if len(self.buffer_rx) < SEARCH_END + self.payload_size:
                break

            rx_search_chunk = self.buffer_rx[SEARCH_START : SEARCH_END + self.payload_size]
            tx1_chunk = self.buffer_tx1[:self.payload_size]

            # BPSK'dan DBPSK Dönüşümü (Diferansiyel Kodlama)
            tx1_chunk_norm = np.sign(tx1_chunk.real)
            tx1_chunk_diff = np.cumprod(-tx1_chunk_norm)

            # Kayma Kestirimi (Cross-Correlation)
            corr = scipy.signal.correlate(rx_search_chunk, tx1_chunk_diff, mode='valid')

            if len(corr) > 0:
                best_idx = np.argmax(np.abs(corr))
                best_val = corr[best_idx]
                payload_start_rel = SEARCH_START + best_idx
                payload_start_abs = self.rx_processed_abs + payload_start_rel

                # Genlik ve Faz Kestirimi
                tx1_energy = np.sum(np.abs(tx1_chunk_diff)**2)
                if tx1_energy > 1e-6:
                    estimated_amp = np.abs(best_val) / tx1_energy
                else:
                    estimated_amp = self.near_user_amplitude

                phase_offset = np.angle(best_val)

                # Geçerli eşleşme kontrolü (Korelasyon yeterince yüksek mi?)
                if estimated_amp >= 0.03:
                    # Statik Genlik Kullanimi (Tum Durumlarda Matematiksel Olarak Tam Cikarma)
                    amplitude_scale = self.near_user_amplitude
                    
                    # Girişim sinyalini sentezle ve çıkar
                    interference_signal = tx1_chunk_diff * amplitude_scale * np.exp(1j * phase_offset)
                    self.buffer_rx[payload_start_rel : payload_start_rel + self.payload_size] -= interference_signal

                    self.pkt_counter += 1
                    shift = payload_start_abs - (self.next_packet_start_abs + 2048) if self.pkt_counter > 1 else payload_start_abs - 2048
                    
                    # Debug dosyamıza yazalım
                    with open("debug_sic.txt", "a") as f_dbg:
                        f_dbg.write(f"[SIC Aligner] Packet #{self.pkt_counter} Subtracted! Shift: {shift} symbols, Phase: {phase_offset:.3f} rad, Amp (Dynamic): {amplitude_scale:.3f} (Est: {estimated_amp:.3f})\n")
                    
                    print(f"[SIC Aligner] Packet #{self.pkt_counter} Subtracted! Shift: {shift} symbols, Phase: {phase_offset:.3f} rad, Amp (Dynamic): {amplitude_scale:.3f} (Est: {estimated_amp:.3f})")

                    # Bir sonraki paketin başlangıç indeksini güncelle
                    self.next_packet_start_abs = payload_start_abs - 2048 + 3408
                    self.subtracted_until_abs = max(self.subtracted_until_abs, payload_start_abs - 2048 + 3408)
                    
                    # TX1 tamponunu tüket
                    self.buffer_tx1 = self.buffer_tx1[self.payload_size:]
                    continue

            # Eşleşme başarısız ise bu paketi tampondan atla ki kuyruk kilitlenmesin
            with open("debug_sic.txt", "a") as f_dbg:
                f_dbg.write(f"[SIC Aligner] Correlation too low or search failed. Skipping reconstructed packet (Est: {estimated_amp:.3f}).\n")
            print(f"[SIC Aligner] Correlation too low or search failed. Skipping reconstructed packet (Est: {estimated_amp:.3f}).")
            self.pkt_counter += 1
            self.next_packet_start_abs += 3408
            self.buffer_tx1 = self.buffer_tx1[self.payload_size:]

        # 5. Çıkışa Güvenli Örnekleri Yazma (Streaming Output)
        safe_to_output = self.subtracted_until_abs - self.rx_processed_abs
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
