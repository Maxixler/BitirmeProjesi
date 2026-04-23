#!/usr/bin/env python3
"""
save.grc modulation/demodulation bit korumasi test - simplified
"""
from gnuradio import gr, digital, blocks, channels, filter as grfilter
from gnuradio.filter import firdes
import numpy as np
import time

qpsk_points = [-1-1j, -1+1j, 1+1j, 1-1j]
sym_map = [0, 1, 3, 2]
qpsk = digital.constellation_rect(
    qpsk_points, sym_map, 4, 2, 2, 1, 1, digital.constellation.NO_NORMALIZATION)

AC = "1010101011110000101010101111000010101010111100001010101011110000"
ac_bits = [int(b) for b in AC]

hdr_bits = [0]*8+[0,1,1,0,0,1,0,0]*2
payload_bits = [1,0]*100
all_bits = ac_bits + hdr_bits + payload_bits
print(f"Input: {len(all_bits)} bits")

packed = []
for i in range(0, len(all_bits), 8):
    byte = 0
    for j in range(8):
        if i+j < len(all_bits): byte = (byte << 1) | all_bits[i+j]
        else: byte <<= 1
    packed.append(byte)

SPS = 4

class test_tb(gr.top_block):
    def __init__(self, data):
        gr.top_block.__init__(self)
        
        self.src = blocks.vector_source_b(data * 10, False)
        
        # TX
        self.unpack_tx = blocks.unpack_k_bits_bb(2)
        self.diff_enc = digital.diff_encoder_bb(4, digital.DIFF_DIFFERENTIAL)
        self.encoder = digital.constellation_encoder_bc(qpsk.base())
        
        ntaps = 11 * SPS + 1
        rrc_taps = firdes.root_raised_cosine(SPS, SPS, 1.0, 0.35, ntaps)
        self.rrc_tx = grfilter.interp_fir_filter_ccf(SPS, rrc_taps)
        self.scale = blocks.multiply_const_cc(0.5)
        
        # Channel
        self.chan = channels.channel_model(0.0, 0.0, 1.0, [1.0], 0, False)
        
        # RX
        self.sym_sync = digital.symbol_sync_cc(
            digital.TED_SIGNAL_TIMES_SLOPE_ML,
            SPS, 0.045, 1.0, 1.5, 0.1,
            1, digital.constellation_qpsk().base(),
            digital.IR_MMSE_8TAP, 128, [])
        self.costas = digital.costas_loop_cc(0.005, 4, False)
        self.decoder = digital.constellation_decoder_cb(qpsk.base())
        self.diff_dec = digital.diff_decoder_bb(4, digital.DIFF_DIFFERENTIAL)
        self.unpack_rx = blocks.unpack_k_bits_bb(2)
        self.sink = blocks.vector_sink_b()
        
        self.connect(self.src, self.unpack_tx, self.diff_enc,
                     self.encoder, self.rrc_tx, self.scale, self.chan,
                     self.sym_sync, self.costas, self.decoder,
                     self.diff_dec, self.unpack_rx, self.sink)

tb = test_tb(packed)
tb.start()
time.sleep(5)
tb.stop()
tb.wait()

out = list(tb.sink.data())
print(f"Output: {len(out)} bits")

# Search for AC at different thresholds
for threshold in [0, 2, 4, 8, 16, 32]:
    matches = []
    search_range = min(len(out) - 64, 8000)
    for i in range(search_range):
        errors = sum(1 for j in range(64) if out[i+j] != ac_bits[j])
        if errors <= threshold:
            matches.append((i, errors))
    print(f"Threshold {threshold}: {len(matches)} AC matches")
    if matches and len(matches) < 20:
        for pos, err in matches[:5]:
            print(f"  Pos {pos}: {err} errors")

# Deep debug
print("\n=== DEEP DEBUG ===")
out_str = ''.join(str(b) for b in out[:100])
inp_str = ''.join(str(b) for b in all_bits[:100])
print(f"Inp: {inp_str}")
print(f"Out: {out_str}")

# Check inverted
inv_ac = [1-b for b in ac_bits]
for i in range(min(len(out)-64, 5000)):
    errors = sum(1 for j in range(64) if out[i+j] != inv_ac[j])
    if errors <= 4:
        print(f"\n→ INVERTED AC at pos {i}, {errors} err")
        print(f"  Out: {''.join(str(out[i+j]) for j in range(64))}")
        break

# Check pair-swap
swapped_ac = []
for i in range(0, 64, 2):
    swapped_ac.append(ac_bits[i+1])
    swapped_ac.append(ac_bits[i])
for i in range(min(len(out)-64, 5000)):
    errors = sum(1 for j in range(64) if out[i+j] != swapped_ac[j])
    if errors <= 4:
        print(f"\n→ PAIR-SWAPPED AC at pos {i}, {errors} err")
        break
