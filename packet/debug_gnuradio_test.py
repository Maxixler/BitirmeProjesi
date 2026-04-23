#!/usr/bin/env python3
"""
Test: Costas Loop faz kaymasini gercek GNU Radio bloklariyla olc.
Modulator kullanmadan elle QPSK sembol olustur, kanal + RX zincirinden gecir.
"""
from gnuradio import gr, digital, blocks, channels, filter as gr_filter
import numpy as np

ACCESS_CODE = "1010101011110000101010101111000010101010111100001010101011110000"

# Constellation
const_points = [-1-1j, -1+1j, 1-1j, 1+1j]
sym_map = [0, 1, 2, 3]
qpsk = digital.constellation_rect(const_points, sym_map, 4, 2, 2, 1, 1)

print("Constellation points (normalized):", [f"{p:.3f}" for p in qpsk.points()])

# === TEST A: Costas Loop Faz Olcumu ===
print("\n" + "="*60)
print("TEST A: Costas Loop Faz Testi")
print("="*60)

# QPSK semboller olustur (elle, modulator olmadan)
# AC + random data
ac_bits = [int(b) for b in ACCESS_CODE]

# Pack to 2-bit symbols
symbols_complex = []
for i in range(0, len(ac_bits), 2):
    two_bits = (ac_bits[i] << 1) | ac_bits[i+1]
    idx = sym_map[two_bits]
    pt = qpsk.points()[idx]
    symbols_complex.append(complex(pt))

# 200 random symbols + AC symbols + 200 random symbols
import random
random.seed(42)
prefix = [qpsk.points()[random.randint(0,3)] for _ in range(500)]
suffix = [qpsk.points()[random.randint(0,3)] for _ in range(500)]
all_symbols = [complex(s) for s in prefix] + symbols_complex + [complex(s) for s in suffix]

print(f"Toplam {len(all_symbols)} QPSK sembol (normalized)")
print(f"AC sembolleri pozisyon {len(prefix)} - {len(prefix)+len(symbols_complex)-1}")

# Scale by 0.5
scaled = [s * 0.5 for s in all_symbols]

# RRC pulse shaping (sps=4)
import math
sps = 4
ntaps = 11 * sps
excess_bw = 0.35

class test_costas_phase(gr.top_block):
    def __init__(self, noise_voltage=0.0, costas_bw=0.005):
        gr.top_block.__init__(self, "test_costas")
        
        # Upsampling + RRC filter (TX)
        taps = self._rrc_taps(sps, ntaps, excess_bw)
        
        # Source (complex symbols, upsampled)
        upsampled = []
        for s in scaled:
            upsampled.append(s)
            upsampled.extend([0+0j] * (sps - 1))
        
        self.src = blocks.vector_source_c(upsampled, False)
        self.tx_filter = gr_filter.interp_fir_filter_ccf(1, taps)
        
        # Channel
        self.channel = channels.channel_model(
            noise_voltage=noise_voltage,
            frequency_offset=0.0,
            epsilon=1.0,
            taps=[1.0],
            noise_seed=0,
            block_tags=False
        )
        
        # RX: Symbol Sync + Costas Loop + Soft Decoder
        self.sync = digital.symbol_sync_cc(
            detector_type=digital.TED_SIGNAL_TIMES_SLOPE_ML,
            sps=sps,
            loop_bw=0.045,
            damping_factor=1.0,
            ted_gain=0.1,
            max_deviation=1.5,
            osps=1,
            slicer=digital.constellation_bpsk().base(),
            interp_type=digital.IR_MMSE_8TAP,
            n_filters=128,
            taps=[]
        )
        
        self.costas = digital.costas_loop_cc(costas_bw, 4, False)
        self.soft_dec = digital.constellation_soft_decoder_cf(qpsk.base(), -1)
        
        # Correlator
        self.correlator = digital.correlate_access_code_ff_ts(
            ACCESS_CODE, 2, "packet_len"
        )
        
        # Sinks
        self.costas_sink = blocks.vector_sink_c()  # Costas cikisi (complex)
        self.soft_sink = blocks.vector_sink_f()     # Soft decoder cikisi
        self.corr_sink = blocks.vector_sink_f()     # Correlator cikisi
        
        # Connect
        self.connect(self.src, self.tx_filter, self.channel,
                    self.sync, self.costas)
        self.connect(self.costas, self.soft_dec)
        self.connect(self.costas, self.costas_sink)
        self.connect(self.soft_dec, self.soft_sink)
        self.connect(self.soft_dec, self.correlator, self.corr_sink)
    
    def _rrc_taps(self, sps, ntaps, beta):
        """Root Raised Cosine taps"""
        taps = []
        for i in range(ntaps):
            t = (i - ntaps/2.0) / sps
            if abs(t) < 1e-8:
                h = 1.0 - beta + 4*beta/math.pi
            elif abs(abs(t) - 1.0/(4*beta)) < 1e-8:
                h = beta/math.sqrt(2) * ((1+2/math.pi)*math.sin(math.pi/(4*beta)) + 
                                          (1-2/math.pi)*math.cos(math.pi/(4*beta)))
            else:
                num = math.sin(math.pi*t*(1-beta)) + 4*beta*t*math.cos(math.pi*t*(1+beta))
                den = math.pi*t*(1-(4*beta*t)**2)
                h = num / den if abs(den) > 1e-10 else 0.0
            taps.append(h)
        # Normalize
        energy = sum(t**2 for t in taps)
        taps = [t / math.sqrt(energy) * math.sqrt(sps) for t in taps]
        return taps

# Test with different Costas BW values
for bw in [0.005, 0.01, 0.0628]:
    for noise in [0.0, 0.1]:
        try:
            tb = test_costas_phase(noise_voltage=noise, costas_bw=bw)
            tb.run()
            
            costas_data = tb.costas_sink.data()
            soft_data = tb.soft_sink.data()
            corr_data = tb.corr_sink.data()
            
            # Costas cikisindaki fazi olc (ilk 100 sembolden sonra, yaklasik convergence sonrasi)
            if len(costas_data) > 200:
                phases = [np.angle(s, deg=True) for s in costas_data[200:250] if abs(s) > 0.01]
                avg_phase = np.mean(phases) if phases else 0
                
                # Soft decoder'da AC'yi ara
                found_ac = False
                best_diff = 64
                for start in range(0, min(len(soft_data)-64, 2000)):
                    chunk = soft_data[start:start+64]
                    hard = ''.join(str(1 if s > 0 else 0) for s in chunk)
                    diff = sum(1 for a, b in zip(hard, ACCESS_CODE) if a != b)
                    if diff < best_diff:
                        best_diff = diff
                    if diff <= 2:
                        found_ac = True
                        break
                
                corr_found = len(corr_data) > 0
                
                print(f"  BW={bw:.4f} noise={noise:.1f}: "
                      f"costas_samples={len(costas_data)}, "
                      f"avg_phase={avg_phase:+.1f} deg, "
                      f"AC_min_diff={best_diff}/64, "
                      f"AC_found={'YES' if found_ac else 'NO'}, "
                      f"corr_output={'YES' if corr_found else 'NO'}")
            else:
                print(f"  BW={bw:.4f} noise={noise:.1f}: yeterli veri yok ({len(costas_data)} samples)")
                
        except Exception as e:
            print(f"  BW={bw:.4f} noise={noise:.1f}: HATA - {e}")

# === TEST B: Costas Loop OLMADAN ===
print("\n" + "="*60)
print("TEST B: Costas Loop BYPASS (dogrudan Soft Decoder)")
print("="*60)

class test_no_costas(gr.top_block):
    def __init__(self, noise_voltage=0.0):
        gr.top_block.__init__(self, "test_no_costas")
        
        taps = test_costas_phase(0,0.005)._rrc_taps(sps, ntaps, excess_bw)
        
        upsampled = []
        for s in scaled:
            upsampled.append(s)
            upsampled.extend([0+0j] * (sps - 1))
        
        self.src = blocks.vector_source_c(upsampled, False)
        self.tx_filter = gr_filter.interp_fir_filter_ccf(1, taps)
        self.channel = channels.channel_model(
            noise_voltage=noise_voltage, frequency_offset=0.0,
            epsilon=1.0, taps=[1.0], noise_seed=0, block_tags=False
        )
        self.sync = digital.symbol_sync_cc(
            detector_type=digital.TED_SIGNAL_TIMES_SLOPE_ML,
            sps=sps, loop_bw=0.045, damping_factor=1.0,
            ted_gain=0.1, max_deviation=1.5, osps=1,
            slicer=digital.constellation_bpsk().base(),
            interp_type=digital.IR_MMSE_8TAP, n_filters=128, taps=[]
        )
        # NO Costas Loop!
        self.soft_dec = digital.constellation_soft_decoder_cf(qpsk.base(), -1)
        self.correlator = digital.correlate_access_code_ff_ts(ACCESS_CODE, 2, "packet_len")
        self.soft_sink = blocks.vector_sink_f()
        self.corr_sink = blocks.vector_sink_f()
        
        self.connect(self.src, self.tx_filter, self.channel,
                    self.sync, self.soft_dec)  # Skip Costas Loop!
        self.connect(self.soft_dec, self.soft_sink)
        self.connect(self.soft_dec, self.correlator, self.corr_sink)

for noise in [0.0, 0.1, 0.3]:
    try:
        tb = test_no_costas(noise_voltage=noise)
        tb.run()
        soft_data = tb.soft_sink.data()
        corr_data = tb.corr_sink.data()
        
        found_ac = False
        best_diff = 64
        for start in range(0, min(len(soft_data)-64, 2000)):
            chunk = soft_data[start:start+64]
            hard = ''.join(str(1 if s > 0 else 0) for s in chunk)
            diff = sum(1 for a, b in zip(hard, ACCESS_CODE) if a != b)
            if diff < best_diff:
                best_diff = diff
            if diff <= 2:
                found_ac = True
                break
        
        corr_found = len(corr_data) > 0
        print(f"  noise={noise:.1f}: AC_min_diff={best_diff}/64, "
              f"AC_found={'YES' if found_ac else 'NO'}, "
              f"corr_output={'YES' if corr_found else 'NO'}")
    except Exception as e:
        print(f"  noise={noise:.1f}: HATA - {e}")

# === TEST C: Hard Decoder + Unpack + Byte Correlator ===
print("\n" + "="*60)
print("TEST C: Hard Decoder + Unpack + Byte Correlator (Costas ile)")
print("="*60)

class test_hard_decoder(gr.top_block):
    def __init__(self, noise_voltage=0.0, costas_bw=0.005):
        gr.top_block.__init__(self, "test_hard")
        
        taps = test_costas_phase(0,0.005)._rrc_taps(sps, ntaps, excess_bw)
        
        upsampled = []
        for s in scaled:
            upsampled.append(s)
            upsampled.extend([0+0j] * (sps - 1))
        
        self.src = blocks.vector_source_c(upsampled, False)
        self.tx_filter = gr_filter.interp_fir_filter_ccf(1, taps)
        self.channel = channels.channel_model(
            noise_voltage=noise_voltage, frequency_offset=0.0,
            epsilon=1.0, taps=[1.0], noise_seed=0, block_tags=False
        )
        self.sync = digital.symbol_sync_cc(
            detector_type=digital.TED_SIGNAL_TIMES_SLOPE_ML,
            sps=sps, loop_bw=0.045, damping_factor=1.0,
            ted_gain=0.1, max_deviation=1.5, osps=1,
            slicer=digital.constellation_bpsk().base(),
            interp_type=digital.IR_MMSE_8TAP, n_filters=128, taps=[]
        )
        self.costas = digital.costas_loop_cc(costas_bw, 4, False)
        
        # Hard decoder + unpack
        self.hard_dec = digital.constellation_decoder_cb(qpsk.base())
        self.unpack = blocks.unpack_k_bits_bb(2)
        
        # Byte correlator
        self.correlator = digital.correlate_access_code_bb_ts(
            ACCESS_CODE, 2, "packet_len"
        )
        
        self.costas_sink = blocks.vector_sink_c()
        self.unpack_sink = blocks.vector_sink_b()
        self.corr_sink = blocks.vector_sink_b()
        
        self.connect(self.src, self.tx_filter, self.channel,
                    self.sync, self.costas)
        self.connect(self.costas, self.costas_sink)
        self.connect(self.costas, self.hard_dec, self.unpack)
        self.connect(self.unpack, self.unpack_sink)
        self.connect(self.unpack, self.correlator, self.corr_sink)

for bw in [0.005, 0.01, 0.0628]:
    for noise in [0.0, 0.1]:
        try:
            tb = test_hard_decoder(noise_voltage=noise, costas_bw=bw)
            tb.run()
            
            costas_data = tb.costas_sink.data()
            unpack_data = tb.unpack_sink.data()
            corr_data = tb.corr_sink.data()
            
            phases = [np.angle(s, deg=True) for s in costas_data[200:250] if abs(s) > 0.01]
            avg_phase = np.mean(phases) if phases else 0
            
            # Check AC in unpacked bits
            found_ac = False
            best_diff = 64
            for start in range(0, min(len(unpack_data)-64, 2000)):
                chunk = unpack_data[start:start+64]
                hard = ''.join(str(b & 1) for b in chunk)
                diff = sum(1 for a, b in zip(hard, ACCESS_CODE) if a != b)
                if diff < best_diff:
                    best_diff = diff
                if diff <= 2:
                    found_ac = True
                    break
            
            corr_found = len(corr_data) > 0
            print(f"  BW={bw:.4f} noise={noise:.1f}: "
                  f"phase={avg_phase:+.1f} deg, "
                  f"AC_min_diff={best_diff}/64, "
                  f"AC_found={'YES' if found_ac else 'NO'}, "
                  f"corr_output={'YES' if corr_found else 'NO'}")
        except Exception as e:
            print(f"  BW={bw:.4f} noise={noise:.1f}: HATA - {e}")
