#!/usr/bin/env python3
"""
Test: Formatter packed/unpacked cikisi ve RX parser uyumu
"""
from gnuradio import gr, digital, blocks
import pmt
import time

AC = "1010101011110000101010101111000010101010111100001010101011110000"

# TX format (AC dahil)
hdr_format_tx = digital.header_format_default(AC, 0, 1)
# RX format (AC'siz)
hdr_format_rx = digital.header_format_default("", 0, 1)

print(f"TX format: header_nbits={hdr_format_tx.header_nbits()} ({hdr_format_tx.header_nbits()//8} bytes)")
print(f"RX format: header_nbits={hdr_format_rx.header_nbits()} ({hdr_format_rx.header_nbits()//8} bytes)")

# TX formatter - payload_len etkisini incele
print("\n" + "="*60)
print("TX Formatter Cikisi Analizi")
print("="*60)

class test_fmt(gr.top_block):
    def __init__(self, payload_len):
        gr.top_block.__init__(self)
        payload = [0] * payload_len
        tag = gr.tag_t()
        tag.offset = 0
        tag.key = pmt.intern("packet_len")
        tag.value = pmt.from_long(payload_len)
        self.src = blocks.vector_source_b(payload, False, 1, [tag])
        self.fmt = digital.protocol_formatter_bb(hdr_format_tx, "packet_len")
        self.sink = blocks.vector_sink_b()
        self.connect(self.src, self.fmt, self.sink)

# Formatter bps=1 ama packed cikiyor olabilir
for plen in [1500, 100, 200]:
    tb = test_fmt(plen)
    tb.run()
    hdr = list(tb.sink.data())
    print(f"\n  payload_len={plen}: formatter output = {len(hdr)} bytes")
    print(f"    Bytes (hex): {' '.join(f'{b:02x}' for b in hdr)}")
    print(f"    Bytes (dec): {hdr}")
    
    # Eger packed ise, unpack edelim
    unpacked = []
    for b in hdr:
        for bit in range(7, -1, -1):
            unpacked.append((b >> bit) & 1)
    print(f"    Unpacked ({len(unpacked)} bits): {''.join(str(b) for b in unpacked)}")
    print(f"    AC check:   {AC}")
    print(f"    AC match:   {''.join(str(b) for b in unpacked[:64]) == AC}")
    
    # Fields (after AC)
    fields = unpacked[64:96]
    print(f"    Fields (32 bits): {''.join(str(b) for b in fields)}")
    
    # Parse fields
    len1 = int(''.join(str(b) for b in fields[:16]), 2)
    len2 = int(''.join(str(b) for b in fields[16:32]), 2)
    print(f"    Parsed len1={len1}, len2={len2}, match={len1==len2}")

# Simdi GERCEK senaryo: TX formatter packed byte cikariyor
# GRC'deki Mux'a packed byte giriyor
# Mux: [packed_header_12byte] + [payload_unpacked]
# HAYIR! Mux'un her iki girisinin de AYNI formatta olmasi lazim
# tagged_stream_mux girisleri:
#   port 0: formatter output (packed? unpacked?)
#   port 1: payload (unpacked bits from FEC)

print("\n" + "="*60)
print("KRITIK: Formatter bps parametresi")
print("="*60)

# bps=1 demek her sembol 1 bit. Bu formatter'in cikisini UNPACKED yapar mi?
# Hayir! Formatter her zaman packed byte cikarir.
# bps sadece header_nbits hesabini etkiler:
#   header_nbits = (access_code_len + 32) * bps
# bps=1: 96 bits -> 12 packed bytes
# bps=2: 192 bits -> 24 packed bytes

# GRC'de formatter -> Mux baglantisi:
# Formatter(packed) -> Mux port 0
# FEC encoder(unpacked) -> Mux port 1
# Bu YANLIS! Her ikisi de ayni formatta olmali.

# GRC'deki Repack ONCE Mux'a girmeden yapiliyor mu?
# Bakalim: 
# blocks_tagged_stream_multiply_length_0 -> blocks_tagged_stream_mux_0 port 1
# digital_protocol_formatter_bb_0 -> blocks_tagged_stream_mux_0 port 0

# Formatter packed byte cikariyorsa ve payload unpacked bit ise,
# Mux cikisi karisik formatta olur = SORUN!

# EGER formatter zaten packed byte ciktiyor ise,
# payload da packed byte olmali. FEC cikisi unpacked, sonra Repack(1->8) yapiliyor.
# Formatter cikisi DA packed. Mux ikisini birlestiriyor: packed header + packed payload
# Sonra Repack(1->8) gereksiz olur... 

# Hmmm, GRC baglantilarina bakalim:
# formatter -> Mux port 0
# tagged_stream_multiply_length -> Mux port 1  (bu FEC cikisi)
# Mux -> repack(1->8)   !!!

# Yani Mux cikisi repack(1->8)'e giriyor. Bu demek ki Mux'un cikisi 
# UNPACKED bitler olmali. Ama formatter packed byte ciktiyor!
# Bu FORMATTER/MUX formati UYUMSUZ!

print("SORUN TESPIT EDILDI!")
print("  Formatter PACKED byte cikartiyor (12 byte = 96 bit)")
print("  FEC encoder UNPACKED bit cikartiyor (1500 bit)")
print("  Mux ikisini birlestiriyor -> KARISIK FORMAT!")
print("  Mux cikisi Repack(1->8)'e gidiyor")
print("  Repack unpacked bit bekliyorsa, packed header bozulur!")
print()

# Cozum: Formatter cikisini unpack et (8->1) VEYA bps degerini kontrol et
# Asil soru: formatterbb bps=1 ile unpacked mi packed mi cikiyor?

# Test: 0 ve 1 disinda deger var mi?
tb = test_fmt(100)
tb.run()
hdr = list(tb.sink.data())
max_val = max(hdr)
min_val = min(hdr)
print(f"Formatter cikis deger araligi: min={min_val}, max={max_val}")
if max_val > 1:
    print("  -> PACKED (byte degerleri > 1)")
    print("  -> Mux'a girmeden ONCE Repack(8->1) gerekli!")
else:
    print("  -> UNPACKED (sadece 0 ve 1)")
    print("  -> Mux ile uyumlu")
