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
        self.synced = False
        self.diag_counter = 0
        # Son kestirilen User 1 genliği (dinamik normalizasyon için başlangıç değeri)
        self.last_est_amp = near_user_amplitude
        self.consecutive_skips = 0
        
        # Frame sabitleri
        self.PREAMBLE_HEADER_OFFSET = 2048  # preamble(2000) + header(48)
        self.FRAME_SIZE = 3408  # preamble(2000) + header(48) + LDPC payload(1296) + postamble(64)

    def forecast(self, noutput_items, ninputs):
        return [gr.max_int, 0] if hasattr(gr, 'max_int') else [max(1, noutput_items), 0]

    def general_work(self, input_items, output_items):
        in_rx = input_items[0]
        in_tx1 = input_items[1]
        out_rx2 = output_items[0]

        # Tanısal Loglama
        self.diag_counter += 1
        if self.diag_counter % 2000 == 1:
            rx_mean_amp = np.mean(np.abs(in_rx)) if len(in_rx) > 0 else 0.0
            with open("debug_sic.txt", "a") as f:
                f.write(f"[DIAG] Call #{self.diag_counter}: in_rx_len={len(in_rx)}, mean_amp={rx_mean_amp:.6f}, synced={self.synced}, pkt={self.pkt_counter}\n")

        # 1. Gelen RX Verilerini Tampona Ekleme
        if len(in_rx) > 0:
            self.buffer_rx = np.concatenate((self.buffer_rx, in_rx))
            self.consume(0, len(in_rx))

        # 2. Gelen TX1 Verilerini Tampona Ekleme
        if len(in_tx1) > 0:
            self.buffer_tx1 = np.concatenate((self.buffer_tx1, in_tx1))
            self.consume(1, len(in_tx1))

        # 3. Tampon Aşım Koruması
        MAX_RX_BUFFER = 300000
        if len(self.buffer_rx) > MAX_RX_BUFFER:
            trim = len(self.buffer_rx) - MAX_RX_BUFFER
            self.buffer_rx = self.buffer_rx[trim:]
            self.rx_processed_abs += trim
            self.synced = False

        MAX_TX1_BUFFER = 5 * self.payload_size
        if len(self.buffer_tx1) > MAX_TX1_BUFFER:
            self.buffer_tx1 = self.buffer_tx1[-3 * self.payload_size:]

        # 4. SIC Çıkarma ve Hizalama İşlemleri
        while len(self.buffer_tx1) >= self.payload_size:
            tx1_chunk = self.buffer_tx1[:self.payload_size]
            
            # BPSK'dan DBPSK Dönüşümü
            tx1_chunk_norm = np.sign(tx1_chunk.real)
            tx1_chunk_diff = np.cumprod(-tx1_chunk_norm)
            tx1_energy = np.sum(np.abs(tx1_chunk_diff)**2)
            
            if tx1_energy < 1e-6:
                self.buffer_tx1 = self.buffer_tx1[self.payload_size:]
                continue
            
            if not self.synced:
                # === ENERJİ BAZLI GENLİK/AKTİVİTE ALGILAMA ===
                rx_abs = np.abs(self.buffer_rx)
                
                # Gürültü eşiğini (0.15) aşan ilk indeksleri bul
                active_indices = np.where(rx_abs > 0.15)[0]
                
                if len(active_indices) == 0:
                    # Henüz sinyal gelmemiş, gürültüyü kırpıp bekle
                    if len(self.buffer_rx) > 5000:
                        trim = len(self.buffer_rx) - 5000
                        self.buffer_rx = self.buffer_rx[trim:]
                        self.rx_processed_abs += trim
                    break
                
                signal_start_rel = active_indices[0]
                
                # Sinyal öncesi gürültüyü temizle
                if signal_start_rel > 0:
                    self.buffer_rx = self.buffer_rx[signal_start_rel:]
                    self.rx_processed_abs += signal_start_rel
                    signal_start_rel = 0
                
                # Paket boyutu kadar verinin birikmesini bekle
                if len(self.buffer_rx) < 5000:
                    break
                
                # Arama aralığı: Preamble sonu ~2016'da olacağı için 1500-2500 aralığı idealdir
                SEARCH_START = 1500
                SEARCH_END = 2500
                
                rx_search = self.buffer_rx[SEARCH_START : SEARCH_END + self.payload_size]
                
                if len(rx_search) < len(tx1_chunk_diff):
                    break
                
                corr = scipy.signal.correlate(rx_search, tx1_chunk_diff, mode='valid')
                
                if len(corr) == 0:
                    break
                
                best_idx = np.argmax(np.abs(corr))
                best_val = corr[best_idx]
                estimated_amp = np.abs(best_val) / tx1_energy
                
                if estimated_amp >= 0.15:
                    phase_offset = np.angle(best_val)
                    amplitude_scale = max(0.05, min(2.0, estimated_amp))
                    self.last_est_amp = amplitude_scale
                    
                    payload_start_rel = SEARCH_START + best_idx
                    payload_start_abs = self.rx_processed_abs + payload_start_rel
                    
                    # Girişimi sembol bazında dinamik faz takibi (DDPT) ile çıkar
                    rx_payload = self.buffer_rx[payload_start_rel : payload_start_rel + self.payload_size]
                    raw_phase = rx_payload * tx1_chunk_diff
                    window_size = 63  # Arttırıldı: User 2 sızıntısını ve faz gürültüsünü azaltır
                    kernel = np.ones(window_size) / window_size
                    smoothed_phase = np.convolve(raw_phase, kernel, mode='same')
                    # Kenar bozulmalarını engelle
                    half = window_size // 2
                    smoothed_phase[:half] = smoothed_phase[half]
                    smoothed_phase[-half:] = smoothed_phase[-half-1]
                    
                    interference = tx1_chunk_diff * smoothed_phase
                    self.buffer_rx[payload_start_rel : payload_start_rel + self.payload_size] -= interference
                    
                    self.next_packet_start_abs = payload_start_abs - self.PREAMBLE_HEADER_OFFSET + self.FRAME_SIZE
                    self.synced = True
                    self.pkt_counter += 1
                    
                    self.subtracted_until_abs = max(self.subtracted_until_abs, 
                        payload_start_abs - self.PREAMBLE_HEADER_OFFSET + self.FRAME_SIZE)
                    
                    self.buffer_tx1 = self.buffer_tx1[self.payload_size:]
                    
                    print(f"[SIC] Energy-Synced Packet #{self.pkt_counter} @ abs={payload_start_abs}, Phase={phase_offset:.3f}, Est={estimated_amp:.3f}")
                    with open("debug_sic.txt", "a") as f:
                        f.write(f"[SIC] Energy-Synced Packet #{self.pkt_counter} @ abs={payload_start_abs}, Phase={phase_offset:.3f}, Est={estimated_amp:.3f}\n")
                    continue
                else:
                    # Hizalama başarısız ise 500 sembol kaydırıp tekrar dene
                    self.buffer_rx = self.buffer_rx[500:]
                    self.rx_processed_abs += 500
                    continue
            
            else:
                # === SENKRONİZE MOD: Dar arama penceresi ===
                expected_abs = self.next_packet_start_abs + self.PREAMBLE_HEADER_OFFSET
                expected_rel = expected_abs - self.rx_processed_abs
                
                if expected_rel < -128:
                    self.synced = False
                    print(f"[SIC] Packet #{self.pkt_counter} is in the past (expected_rel={expected_rel}), skipping")
                    with open("debug_sic.txt", "a") as f:
                        f.write(f"[SIC] Packet #{self.pkt_counter} is in the past (expected_rel={expected_rel}), skipping\n")
                    self.pkt_counter += 1
                    self.next_packet_start_abs += self.FRAME_SIZE
                    self.buffer_tx1 = self.buffer_tx1[self.payload_size:]
                    continue
                
                search_start = max(0, expected_rel - 128)
                search_end = expected_rel + 128
                
                if len(self.buffer_rx) < search_end + self.payload_size:
                    break
                
                rx_search = self.buffer_rx[search_start : search_end + self.payload_size]
                
                if len(rx_search) < len(tx1_chunk_diff) or len(rx_search) == 0:
                    self.synced = False
                    break  # RX verisi yetersiz, zamanlayıcıyı engellememek için döngüden çık
                
                corr = scipy.signal.correlate(rx_search, tx1_chunk_diff, mode='valid')
                
                if len(corr) == 0:
                    self.synced = False
                    break  # RX verisi yetersiz, zamanlayıcıyı engellememek için döngüden çık
                
                best_idx = np.argmax(np.abs(corr))
                best_val = corr[best_idx]
                estimated_amp = np.abs(best_val) / tx1_energy
                
                payload_start_rel = search_start + best_idx
                payload_start_abs = self.rx_processed_abs + payload_start_rel
                phase_offset = np.angle(best_val)
                
                if estimated_amp >= 0.15:
                    self.consecutive_skips = 0
                    amplitude_scale = max(0.05, min(2.0, estimated_amp))
                    self.last_est_amp = amplitude_scale
                    
                    # Girişimi sembol bazında dinamik faz takibi (DDPT) ile çıkar
                    rx_payload = self.buffer_rx[payload_start_rel : payload_start_rel + self.payload_size]
                    raw_phase = rx_payload * tx1_chunk_diff
                    window_size = 63  # Arttırıldı: User 2 sızıntısını ve faz gürültüsünü azaltır
                    kernel = np.ones(window_size) / window_size
                    smoothed_phase = np.convolve(raw_phase, kernel, mode='same')
                    # Kenar bozulmalarını engelle
                    half = window_size // 2
                    smoothed_phase[:half] = smoothed_phase[half]
                    smoothed_phase[-half:] = smoothed_phase[-half-1]
                    
                    interference = tx1_chunk_diff * smoothed_phase
                    self.buffer_rx[payload_start_rel : payload_start_rel + self.payload_size] -= interference
                    
                    self.pkt_counter += 1
                    self.next_packet_start_abs = payload_start_abs - self.PREAMBLE_HEADER_OFFSET + self.FRAME_SIZE
                    self.subtracted_until_abs = max(self.subtracted_until_abs,
                        payload_start_abs - self.PREAMBLE_HEADER_OFFSET + self.FRAME_SIZE)
                    
                    self.buffer_tx1 = self.buffer_tx1[self.payload_size:]
                    
                    shift = payload_start_rel - expected_rel
                    if self.pkt_counter % 20 == 0:
                        print(f"[SIC] Packet #{self.pkt_counter} OK, Shift={shift}, Phase={phase_offset:.3f}, Est={estimated_amp:.3f}")
                    continue
                else:
                    # Gelişmiş Zamanlama Kurtarma: User 1 alıcısının paket kaçırıp kaçırmadığını kontrol et.
                    # Eğer mevcut referans bloğu, buffer_rx içindeki bir sonraki paketle eşleşiyorsa,
                    # alıcı paket kaçırmıştır. Bu durumda RX tamponunu 1 paket kaydırarak hizalamayı düzeltiriz.
                    lookahead_start = expected_rel + self.FRAME_SIZE - 128
                    lookahead_end = expected_rel + self.FRAME_SIZE + 128
                    la_success = False
                    if len(self.buffer_rx) >= lookahead_end + self.payload_size:
                        rx_lookahead = self.buffer_rx[lookahead_start : lookahead_end + self.payload_size]
                        corr_lookahead = scipy.signal.correlate(rx_lookahead, tx1_chunk_diff, mode='valid')
                        if len(corr_lookahead) > 0:
                            best_idx_la = np.argmax(np.abs(corr_lookahead))
                            best_val_la = corr_lookahead[best_idx_la]
                            est_amp_la = np.abs(best_val_la) / tx1_energy
                            if est_amp_la >= 0.15:
                                # Bir sonraki slotta eşleşme bulundu! Mevcut RX paketini atla.
                                print(f"[SIC] User 1 referans paket kaybı algılandı (#{self.pkt_counter})! RX tamponu kaydırılıyor.")
                                self.next_packet_start_abs += self.FRAME_SIZE
                                self.subtracted_until_abs = max(self.subtracted_until_abs, self.next_packet_start_abs)
                                la_success = True
                                
                    if la_success:
                        # Referans paketini tüketmeden döngüyü tekrar çalıştırarak hizalamayı sına
                        continue
                    
                    # Gerçek senkronizasyon kaybı veya sönümleme (lookahead da başarısız)
                    self.pkt_counter += 1
                    self.next_packet_start_abs += self.FRAME_SIZE
                    self.subtracted_until_abs = max(self.subtracted_until_abs, self.next_packet_start_abs)
                    self.buffer_tx1 = self.buffer_tx1[self.payload_size:]
                    self.consecutive_skips += 1
                    
                    if self.pkt_counter % 100 == 0:
                        print(f"[SIC] Low corr packet #{self.pkt_counter} (Est={estimated_amp:.3f}), skipping")
                    
                    if self.consecutive_skips >= 3:
                        self.synced = False
                        self.consecutive_skips = 0
                        print(f"[SIC] Senkronizasyon Kayboldu (Ardışık 3 başarısız paket, #{self.pkt_counter}). Enerji-senk moduna geçiliyor.")
                    continue

        # 5. Çıkışa Güvenli Örnekleri Yazma
        safe_to_output = self.subtracted_until_abs - self.rx_processed_abs
        safe_to_output = min(safe_to_output, len(self.buffer_rx))
        safe_to_output = max(0, safe_to_output)

        n_out = len(out_rx2)
        limit = min(safe_to_output, n_out)

        if limit > 0:
            # Dinamik normalizasyon: Statik 2.0 yerine, kestirilen User 1 genliğine oranla ölçekle.
            # Bu işlem USRP'deki kanal sönümlemesini (kanal kaybını) kompanse eder ve Soft Diff
            # Decoder'a gönderilen LLR değerlerinin karesel çökmesini önler.
            norm_factor = 2.0 / max(0.05, self.last_est_amp)
            out_rx2[:limit] = self.buffer_rx[:limit] * norm_factor
            self.buffer_rx = self.buffer_rx[limit:]
            self.rx_processed_abs += limit
            return limit
        else:
            return 0
