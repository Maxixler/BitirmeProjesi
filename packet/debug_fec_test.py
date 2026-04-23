#!/usr/bin/env python3
"""
test.grc icin FEC decoder sorununu tespit et
"""
from gnuradio import gr, digital, blocks, fec
import pmt
import time
import numpy as np

AC = "1010101011110000101010101111000010101010111100001010101011110000"
hdr_format = digital.header_format_default(AC, 1, 1)

print("="*60)
print("1) Formatter cikisinin formati")
print("="*60)
print(f"header_nbits: {hdr_format.header_nbits()}")

# Simulate TX chain exactly as in test.grc
class tx_test(gr.top_block):
    def __init__(self):
        gr.top_block.__init__(self)
        
        # Source: 91 bytes
        data = list(range(91))  # dummy data
        tag = gr.tag_t()
        tag.offset = 0
        tag.key = pmt.intern("packet_len")
        tag.value = pmt.from_long(91)
        
        self.src = blocks.vector_source_b(data, False, 1, [tag])
        
        # CRC32
        self.crc = digital.crc32_bb(False, "packet_len", True)
        
        # Repack 8->1
        self.repack1 = blocks.repack_bits_bb(8, 1, "packet_len", False, gr.GR_MSB_FIRST)
        
        # Scrambler
        self.scrambler = digital.scrambler_bb(0x8A, 0x7F, 7)
        
        # FEC encoder
        ldpc_enc = fec.ldpc_encoder_make(
            "C:\\Users\\Armagan\\Documents\\GitHub\\BitirmeProjesi\\packet\\n_0300_k_0152_gap_03.alist"
        )
        self.fec_enc = fec.extended_encoder(ldpc_enc, puncpat='11', threadtype=fec.TP_CAPILLARY)
        
        # Multiply length
        self.mult_len = blocks.tagged_stream_multiply_length(gr.sizeof_char, "packet_len", 300.0/152.0)
        
        # Protocol formatter
        self.formatter = digital.protocol_formatter_bb(hdr_format, "packet_len")
        
        # Formatter repack 8->1
        self.fmt_repack = blocks.repack_bits_bb(8, 1, "packet_len", False, gr.GR_MSB_FIRST)
        
        # Mux
        self.mux = blocks.tagged_stream_mux(gr.sizeof_char, "packet_len", 0)
        
        # Final repack 1->8
        self.repack_final = blocks.repack_bits_bb(1, 8, "packet_len", False, gr.GR_MSB_FIRST)
        
        # Sinks
        self.fmt_sink = blocks.vector_sink_b()  # formatter output
        self.fmt_repack_sink = blocks.vector_sink_b()  # formatter after repack
        self.fec_sink = blocks.vector_sink_b()  # FEC output
        self.mux_sink = blocks.vector_sink_b()  # mux output
        self.final_sink = blocks.vector_sink_b()  # final output
        
        # Connect TX chain
        self.connect(self.src, self.crc, self.repack1, self.scrambler, self.fec_enc)
        self.connect(self.fec_enc, self.mult_len)
        self.connect(self.mult_len, self.formatter)
        self.connect(self.formatter, self.fmt_sink)
        self.connect(self.formatter, self.fmt_repack, self.fmt_repack_sink)
        self.connect(self.fmt_repack, (self.mux, 0))
        self.connect(self.mult_len, (self.mux, 1))
        self.connect(self.mux, self.mux_sink)
        self.connect(self.mux, self.repack_final, self.final_sink)
        
        # Also capture FEC output
        self.connect(self.fec_enc, self.fec_sink)

try:
    tb = tx_test()
    tb.run()
    
    fmt_out = list(tb.fmt_sink.data())
    fmt_repack_out = list(tb.fmt_repack_sink.data())
    fec_out = list(tb.fec_sink.data())
    mux_out = list(tb.mux_sink.data())
    final_out = list(tb.final_sink.data())
    
    print(f"\nFEC encoder output: {len(fec_out)} bits")
    print(f"Formatter output (packed): {len(fmt_out)} bytes, values: {fmt_out}")
    print(f"Formatter repack (unpacked): {len(fmt_repack_out)} bits, first 64: {''.join(str(b) for b in fmt_repack_out[:64])}")
    print(f"AC check: {''.join(str(b) for b in fmt_repack_out[:64]) == AC}")
    print(f"Mux output: {len(mux_out)} bits")
    print(f"  Header (unpacked): {len(fmt_repack_out)} bits")
    print(f"  Payload (unpacked): {len(fec_out)} bits")
    print(f"  Total expected: {len(fmt_repack_out) + len(fec_out)}")
    print(f"Final output (packed): {len(final_out)} bytes")
    
except Exception as e:
    print(f"TX test HATA: {e}")
    import traceback
    traceback.print_exc()

# Test 2: RX chain - HPD ile parser testi
print("\n" + "="*60)
print("2) RX: Parser ile header parse testi")
print("="*60)

# Simulate what HPD receives: after correlator_tag, HPD extracts header_len=96 items
# The correlator_tag places tag at end of AC (offset after AC)
# HPD extracts 96 items starting from tag position
# First 96 items after tag = first 96 items after AC end

# In test.grc: Virtual Source -> Unpack(8) -> Correlator -> HPD
# The Mux output was Repack(1->8) -> packed bytes
# Virtual Source -> Unpack(8) recovers the original unpacked bits
# So correlator sees the EXACT same unpacked bit stream as Mux output

# After AC (64 bits), the next 32 bits are header fields
# After header fields, the next bits are payload
# HPD with header_len=96: extracts items 0-95 starting from tag position
# Tag is at END of AC, so items 0-31 = header fields, items 32-95 = first 64 payload bits!
# Parser (with hdr_format including AC) expects 96 bits = [AC_64][fields_32]
# But it receives [fields_32][payload_start_64] → AC NOT FOUND → #f!

# WAIT - header_len=96 but tag is AFTER AC...
# The tag is placed right after the last bit of the AC
# HPD header extraction: items from tag position to tag+96
# So HPD gives parser: [32 header field bits] + [64 first payload bits]
# Parser expects: [64 AC bits] + [32 header field bits]
# TOTAL MISMATCH!

print("SORUN: HPD header_len=96, ama tag AC'den SONRA!")
print("  HPD parser'a veriyor: [32 header fields][64 payload start]")
print("  Parser bekliyor:      [64 AC bits][32 header fields]")
print("  → FORMAT UYUMSUZ!")
print()
print("COZUM: HPD header_len=32 + hdr_format_rx (AC'siz)")

# Test 3: FEC decoder input format
print("\n" + "="*60)
print("3) FEC Decoder giris formati testi")
print("="*60)

# test.grc payload path:
# HPD port 1 (byte, 0/1) → char_to_float → add_const(-0.5) → ×2 → FEC decoder
# byte 0 → 0.0 → -0.5 → -1.0
# byte 1 → 1.0 → 0.5  → +1.0

# FEC encoder output: unpacked bits (0 or 1)
# These become bytes after Repack(1->8) -> Unpack(8) -> same values
# So byte 0 means original bit was 0
# byte 1 means original bit was 1

# LDPC decoder expects soft decisions:
# Positive → bit 0 (more likely)
# Negative → bit 1 (more likely)

# With current mapping:
# byte 0 (original bit 0) → -1.0 (decoder thinks bit 1) → WRONG!
# byte 1 (original bit 1) → +1.0 (decoder thinks bit 0) → WRONG!
# This is INVERTED!

print("Mevcut donusum:")
print("  byte 0 → 0.0 → -0.5 → ×2 → -1.0 (LDPC: bit=1) ← YANLIS! (orijinal bit 0)")
print("  byte 1 → 1.0 → +0.5 → ×2 → +1.0 (LDPC: bit=0) ← YANLIS! (orijinal bit 1)")
print()
print("Dogru donusum olmali:")
print("  byte 0 → +1.0 (LDPC: bit=0) ← DOGRU")
print("  byte 1 → -1.0 (LDPC: bit=1) ← DOGRU")
print()
print("COZUM: add_const(-0.5) yerine:")
print("  char_to_float → ×(-1) ile carpilmali, sonra add_const(+0.5)")
print("  VEYA: char_to_float → multiply(-2) → add_const(+1)")
print("  byte 0 → 0.0 → ×(-2) → 0.0 → +1.0 → +1.0 (LDPC: bit=0) ✓")
print("  byte 1 → 1.0 → ×(-2) → -2.0 → +1.0 → -1.0 (LDPC: bit=1) ✓")
print()
print("EN BASIT COZUM: add_const=+0.5, multiply=-2 YERINE")
print("  char_to_float(scale=-1) veya:")
print("  char_to_float → ×(-2) → add(+1)")
print("  byte 0 → 0.0 → 0.0 → +1.0")
print("  byte 1 → 1.0 → -2.0 → -1.0")

# Test 4: HPD'nin parser'a ne verdigini kontrol
print("\n" + "="*60)
print("4) HPD header_len=96 → parser 96 byte aliyor")
print("="*60)

# Eger parser gercekten calisiyor ve #f donmuyor ise,
# demux cikis veriyor demektir (ekran goruntusunden goruluyor)
# Ama FEC decoder cikis vermiyor
# Parser calisiyor ama FEC decoder'a yanlis format gidiyor

# Demux cikisinda rx_time taglari goruluyor -> parser CALISIYOR!
# Yani header_len=96 ile parser bir sekilde AC'yi buluyor olabilir...
# ya da threshold=1 ile parser AC'yi es geciyor

# Ekran goruntusunden:
# correlater giris: packet_len:200 tagi var
# correlater cikis: packet_len tag'lar goruluyor
# h/p demux cikis: rx_time taglari var, veri akiyor
# fec decoder cikis: DUZLUK (0) → veri yok

# Sonuc: Parser CALISIYOR (demux cikis veriyor)
# FEC decoder CALISIMIYOR → giris formati YANLIS

print("SONUC:")
print("  Parser CALISIYOR (HPD cikis veriyor, rx_time taglari goruluyor)")
print("  FEC decoder CALISIMIYOR → soft decision polaritesi TERS!")
print()
print("  DUZELTME: test.grc'de")
print("  add_const: -0.5 → SIL")
print("  multiply_const: 2 → -2")
print("  YENİ add_const: +1 ekle (multiply sonrasi)")
print("  VEYA DAHA BASIT:")  
print("  add_const: -0.5 → -0.5 (kalsin)")
print("  multiply_const: 2 → -2 (isaret degistir)")
print("  byte 0 → -0.5 → ×(-2) → +1.0 (LDPC: bit=0) ✓")
print("  byte 1 → +0.5 → ×(-2) → -1.0 (LDPC: bit=1) ✓")
