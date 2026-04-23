#!/usr/bin/env python3
"""
TEST: Birden fazla AC ile correlator testi - soyutlanmis problem
"""
from gnuradio import gr, digital, blocks
import numpy as np

ACCESS_CODE = "1010101011110000101010101111000010101010111100001010101011110000"

print("="*60)
print("TEST: Correlator coklu AC ile")
print("="*60)

# Soft bits olarak birden fazla paket olustur
# AC + 100 bit data + AC + 100 bit data + AC + 100 bit data
import random
random.seed(42)

soft_ac = [1.0 if b == '1' else -1.0 for b in ACCESS_CODE]

# 3 paket
packets = []
for pkt in range(5):
    # Random preamble (ilk paket icin)
    if pkt == 0:
        packets.extend([random.choice([-1.0, 1.0]) for _ in range(100)])
    
    # Access code
    packets.extend(soft_ac)
    
    # Data (header + payload)
    packets.extend([random.choice([-1.0, 1.0]) for _ in range(200)])

print(f"Toplam {len(packets)} soft bit, 5 paket")

# Test 1: Float correlator (_ff_ts)
class test_multi_ac(gr.top_block):
    def __init__(self, threshold=1):
        gr.top_block.__init__(self, "test_multi_ac")
        
        self.src = blocks.vector_source_f(packets, False)
        self.correlator = digital.correlate_access_code_ff_ts(
            ACCESS_CODE, threshold, "packet_len"
        )
        self.sink = blocks.vector_sink_f()
        self.tag_debug = blocks.tag_debug(gr.sizeof_float, "multi_ac", "packet_len")
        self.tag_debug.set_display(True)
        
        self.connect(self.src, self.correlator, self.sink)
        self.connect(self.correlator, self.tag_debug)

for thresh in [0, 1, 2, 4]:
    try:
        tb = test_multi_ac(threshold=thresh)
        tb.run()
        data = tb.sink.data()
        print(f"\n  threshold={thresh}: correlator cikis={len(data)} float")
        if len(data) > 0:
            print(f"    BASARILI! Correlator calisiyor!")
        else:
            print(f"    BASARISIZ - cikis yok")
    except Exception as e:
        print(f"  threshold={thresh}: HATA - {e}")

# Test 2: Byte correlator (_bb_ts)
print("\n" + "="*60)
print("TEST: Byte Correlator coklu AC ile")
print("="*60)

byte_ac = [1 if b == '1' else 0 for b in ACCESS_CODE]
byte_packets = []
for pkt in range(5):
    if pkt == 0:
        byte_packets.extend([random.randint(0,1) for _ in range(100)])
    byte_packets.extend(byte_ac)
    byte_packets.extend([random.randint(0,1) for _ in range(200)])

class test_multi_ac_bb(gr.top_block):
    def __init__(self, threshold=1):
        gr.top_block.__init__(self, "test_bb")
        
        self.src = blocks.vector_source_b(byte_packets, False)
        self.correlator = digital.correlate_access_code_bb_ts(
            ACCESS_CODE, threshold, "packet_len"
        )
        self.sink = blocks.vector_sink_b()
        self.tag_debug = blocks.tag_debug(gr.sizeof_char, "bb_test", "packet_len")
        self.tag_debug.set_display(True)
        
        self.connect(self.src, self.correlator, self.sink)
        self.connect(self.correlator, self.tag_debug)

for thresh in [0, 1, 2, 4]:
    try:
        tb = test_multi_ac_bb(threshold=thresh)
        tb.run()
        data = tb.sink.data()
        print(f"\n  threshold={thresh}: correlator cikis={len(data)} byte")
        if len(data) > 0:
            print(f"    BASARILI!")
        else:
            print(f"    BASARISIZ")
    except Exception as e:
        print(f"  threshold={thresh}: HATA - {e}")

# Test 3: Gercek senaryo - HPD header_len ile uyumlu data boyutu
print("\n" + "="*60)
print("TEST: Gercek paket boyutlari (header=32 + payload=1500)")
print("="*60)

real_packets = []
for pkt in range(3):
    if pkt == 0:
        real_packets.extend([random.choice([-1.0, 1.0]) for _ in range(100)])
    real_packets.extend(soft_ac)  # 64 bit AC
    real_packets.extend([random.choice([-1.0, 1.0]) for _ in range(32)])  # header
    real_packets.extend([random.choice([-1.0, 1.0]) for _ in range(1500)])  # payload

class test_real_packets(gr.top_block):
    def __init__(self):
        gr.top_block.__init__(self, "test_real")
        self.src = blocks.vector_source_f(real_packets, False)
        self.correlator = digital.correlate_access_code_ff_ts(
            ACCESS_CODE, 2, "packet_len"
        )
        self.sink = blocks.vector_sink_f()
        self.tag_debug = blocks.tag_debug(gr.sizeof_float, "real_pkt", "packet_len")
        self.tag_debug.set_display(True)
        
        self.connect(self.src, self.correlator, self.sink)
        self.connect(self.correlator, self.tag_debug)

try:
    tb = test_real_packets()
    tb.run()
    data = tb.sink.data()
    print(f"  Correlator cikis: {len(data)} float")
    if len(data) > 0:
        print(f"  BASARILI! Gercek paket boyutlariyla calisiyor!")
    else:
        print(f"  BASARISIZ - cikis yok")
except Exception as e:
    print(f"  HATA: {e}")
