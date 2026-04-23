#!/usr/bin/env python3
"""
Parser'in farkli header_len/format kombinasyonlariyla calisip calismadigini test et
"""
from gnuradio import gr, digital, blocks
import pmt
import time

AC = "1010101011110000101010101111000010101010111100001010101011110000"

hdr_format = digital.header_format_default(AC, 1, 1)
hdr_format_rx = digital.header_format_default("", 0, 1)

print(f"hdr_format header_nbits: {hdr_format.header_nbits()}")
print(f"hdr_format_rx header_nbits: {hdr_format_rx.header_nbits()}")

# Gercek formatter cikisi olustur
class tx(gr.top_block):
    def __init__(self):
        gr.top_block.__init__(self)
        payload = [0] * 1500
        tag = gr.tag_t()
        tag.offset = 0
        tag.key = pmt.intern("packet_len")
        tag.value = pmt.from_long(1500)
        self.src = blocks.vector_source_b(payload, False, 1, [tag])
        self.fmt = digital.protocol_formatter_bb(hdr_format, "packet_len")
        self.sink = blocks.vector_sink_b()
        self.connect(self.src, self.fmt, self.sink)

tb = tx()
tb.run()
fmt_out = list(tb.sink.data())
print(f"\nFormatter output: {len(fmt_out)} packed bytes")

# Unpack formatter
unpacked_hdr = []
for b in fmt_out:
    for bit in range(7, -1, -1):
        unpacked_hdr.append((b >> bit) & 1)

fields_32 = unpacked_hdr[64:96]
fields_str = ''.join(str(b) for b in fields_32)
print(f"Header fields (32 bits): {fields_str}")

# header_format_default.parse() metodu dogrudan cagrilabilir
print("\n--- Dogrudan parse() testi ---")

def test_parse_direct(name, bits, fmt):
    """Dogrudan header_format.parse() cagir"""
    import ctypes
    # parse(nbits_in, input, info, nbits_processed)
    # Ama Python wrapper farkli olabilir
    try:
        result = fmt.parse(len(bits), bits)
        print(f"  {name}: result={result}")
    except Exception as e:
        print(f"  {name}: HATA - {e}")

# Test 1: Full 96 bit (AC + fields) with hdr_format
test_parse_direct("hdr_format + 96bit (AC+fields)", unpacked_hdr[:96], hdr_format)

# Test 2: 32 bit (fields only) with hdr_format  
test_parse_direct("hdr_format + 32bit (fields)", fields_32, hdr_format)

# Test 3: 32 bit (fields) with hdr_format_rx
test_parse_direct("hdr_format_rx + 32bit (fields)", fields_32, hdr_format_rx)

# Test 4: 96 bit (fields + garbage) with hdr_format_rx
garbage = fields_32 + [0]*64
test_parse_direct("hdr_format_rx + 96bit (fields+0s)", garbage, hdr_format_rx)

# Test 5: 96 bit (fields + garbage) with hdr_format
test_parse_direct("hdr_format + 96bit (fields+0s)", garbage, hdr_format)

# Alternative: header_format_default.header_payload() ile parse
print("\n--- header_format.header_payload() testi ---")
for fmt_name, fmt in [("hdr_format", hdr_format), ("hdr_format_rx", hdr_format_rx)]:
    try:
        # Bu metot farkli olabilir
        info_vec = []
        n_proc = [0]
        
        # Unpacked bytes to packed bytes for parse
        # pack bits to bytes
        packed = []
        for i in range(0, len(unpacked_hdr), 8):
            byte = 0
            for j in range(8):
                if i+j < len(unpacked_hdr):
                    byte = (byte << 1) | unpacked_hdr[i+j]
                else:
                    byte = byte << 1
            packed.append(byte)
        
        print(f"  {fmt_name}: packed header = {packed}")
        print(f"  {fmt_name}: header_nbits = {fmt.header_nbits()}")
        
    except Exception as e:
        print(f"  {fmt_name}: HATA - {e}")

# ASIL SORU: test.grc'de parser calisiyor mu?
# Ekran goruntusunde demux cikis veriyor (rx_time tagleri var)
# Bu demek ki parser BASARILI bir sekilde payload uzunlugunu donduruyor
# Nasil?

print("\n" + "="*60)
print("KRITIK ANALIZ: test.grc neden calisiyor?")
print("="*60)

# test.grc'de:
# - HPD header_len=96
# - Parser hdr_format (AC dahil, 96 bit bekleniyor)
# - _tag correlator tag'i AC sonuna koyuyor
# - HPD tag'dan 96 item aliyor
# 
# AMA: test.grc'de modulasyon YOK!
# TX: Mux -> Repack(1->8) -> Virtual Sink
# RX: Virtual Source -> Unpack(8) -> Correlator
#
# Virtual Source/Sink dogrudan byte aktariyor
# Unpack(8): her packed byte -> 8 unpacked bit
# 
# Mux cikisi = [96 header unpacked] + [1500 payload unpacked] = 1596 bit
# Repack(1->8): 1596 bit -> 200 packed byte (4 bit padding)
# Virtual Sink/Source: 200 packed byte
# Unpack(8): 200 byte -> 1600 bit (4 ekstra bit!)
#
# Correlator 1600 bit icerisinde AC'yi ariyor
# AC, byte sinirlarina hizali ise, Unpack(8) sonrasi
# ilk 8 bit = ilk packed byte'in unpack'i
# 
# Formatter packed byte cikartiyor: [0xAA, 0xF0, 0xAA, 0xF0, 0xAA, 0xF0, 0xAA, 0xF0, 0x05, 0xDC, 0x05, 0xDC]
# Bu 12 byte Mux port 0'a giriyor
# AMA: Mux'a girmeden once Repack(8->1) ile unpack ediliyor (test.grc line 1075)
# blocks_repack_bits_bb_0_0 (k=8, l=1): formatter(packed) -> unpacked bits
# Sonra Mux port 0'a 96 unpacked bit giriyor
# Mux port 1'e 1500 unpacked bit giriyor
# Mux toplam 1596 unpacked bit cikariyor
# Repack(1->8): 1596 bit -> 200 byte (1596/8=199.5 -> 200 byte, 4 bit padding)
#
# RX: Unpack(8): 200 byte -> 1600 bit
# Ilk 96 bit: AC(64) + header_fields(32) — DOGRU!
# Correlator AC'yi buluyor, tag ekliyor
# HPD header_len=96: tag'dan 96 item aliyor
# 
# SORUN: tag AC'nin SONUNDA
# Tag pozisyonu = AC_end = bit 63'ten sonra
# HPD tag'dan 96 item aliyor = bit 64 ... bit 159
# Bu = [header_fields_32bit] + [payload_ilk_64bit]
# 
# Parser hdr_format (AC dahil) ile bu 96 byte'i parse etmeye calisiyor
# Ilk 64 byte'ta AC bekliyor ama header_fields bulacak
# AC uyusmaz -> #f donmeli
#
# AMA demux CIKIS VERIYOR! Bu nasil oluyor?

print("Parser hdr_format (AC dahil) ile test:")
print("  HPD'den parser'a gelen 96 byte:")
# Simulate: tag is at bit 64 (after AC), HPD extracts 96 items starting from there
hpd_to_parser = unpacked_hdr[64:96] + [0]*64  # 32 fields + 64 payload start (0s)
hpd_str = ''.join(str(b) for b in hpd_to_parser[:64])
ac_str = AC
wrong_bits = sum(1 for a,b in zip(hpd_str, ac_str) if a != b)
print(f"  Parser ilk 64 bit'i AC olarak okur: {hpd_str}")
print(f"  Beklenen AC:                         {ac_str}")
print(f"  Farkli bit sayisi: {wrong_bits}/64")
print(f"  threshold=1 -> {'GECERLI' if wrong_bits <= 1 else 'REDDEDILIR'}")

# Peki: Eger parser 96 byte alip, AC'yi iceride bulamiyorsa 
# nasil calisiyordur?
# CEVAP: Belki de parser THRESHOLD=1 ve hdr_format threshold=1
# Veya: HPD header_len ile parser'in beklentisi ayri
# Parser nb_bits_in=96 aliyor, header_nbits()=96 ile kiyasliyor
# Parser parse() metodu: first 64 bits = AC check, next 32 bits = fields
# HPD 96 byte veriyor ama bunlar [fields][payload] degil mi?

# Hmm, belki de ben yanlis dusunuyorum.
# Belki de HPD header extract ederken TAG POZISYONUNDAN ONCE degil
# TAG pozisyonundan SONRA baslamiyor.
# HPD'nin trigger_tag_key isleyisi:
# 1. Input stream'de trigger_tag_key="packet_len" tag'ini bul
# 2. Bu tag'in oldugu OFFSET'ten itibaren header_len item extract et
# 3. Bu itemleri Port 0'a yolla
# 4. Sonraki itemleri (parser'dan gelen payload length kadar) Port 1'e yolla

# Peki tag NEREDE?
# correlate_access_code_tag: tag'i AC'nin SON bitine koyar
# Yani tag offset = AC_start + 63 (son AC biti)
# HPD bu offset'ten itibaren 96 item aliyor
# Items = [AC_last_bit, header_fields_32, payload_first_63]?
# NO - HPD tag offset'indeki item'den baslar
# Eger tag AC'nin son bitinde ise, HPD [AC_son_bit, ...95 item daha] alir

# Aslinda GNU Radio dokumantasyonunu kontrol etmem lazim
# correlate_access_code_tag_bb::work():
#   if(match) {
#     add_item_tag(0, abs_out_sample_cnt + j, d_key, pmt::from_long(0), d_me);
#   }
# j = current sample index in output
# Tag, match anindaki sample'a eklenir
# Match AC'nin SON bitinde tespit edilir (shift register dolu)
# Yani tag AC'nin SON bitine (= AC_bit_63) konur
# 
# HPD: trigger_tag gorunce, o noktadan itibaren header_len item alir
# Yani: item[tag_offset], item[tag_offset+1], ..., item[tag_offset+header_len-1]
# = [AC_son_bit] + [header_fields_32] + [payload_first_63]
#
# Eger header_len=96:
#   Parser: 96 item alir
#   Ilk item = AC_son_bit (genellikle 0)
#   Sonraki 95 item = header_fields(32) + payload(63)
#   Parser bunlari AC(64) + fields(32) olarak okumaya calisir
#   -> AC match basarisiz (cunku AC degil) -> #f

# AMA DEMUX CIKIS VERIYOR!
# Bu durumda ya:
# 1. Parser #f donuyor ama HPD bunu ignore ediyor (unlikely)
# 2. Tag pozisyonu benim dusundugumden farkli
# 3. HPD header extract mekanizmasi farkli

# En guvenilir yol: correlator tag'inin GERCEK pozisyonunu olcmek
print("\n" + "="*60)
print("Correlator tag pozisyonu testi")
print("="*60)

# TX output (packed bytes from Repack 1->8)
# Simulate full chain
class full_tx(gr.top_block):
    def __init__(self):
        gr.top_block.__init__(self)
        data = list(range(91))
        tag = gr.tag_t()
        tag.offset = 0
        tag.key = pmt.intern("packet_len")
        tag.value = pmt.from_long(91)
        
        self.src = blocks.vector_source_b(data, False, 1, [tag])
        self.crc = digital.crc32_bb(False, "packet_len", True)
        self.repack1 = blocks.repack_bits_bb(8, 1, "packet_len", False, gr.GR_MSB_FIRST)
        self.scrambler = digital.scrambler_bb(0x8A, 0x7F, 7)
        
        # Skip FEC for simplicity, just use raw bits
        # FEC would change length, let's simulate without it
        
        # Formatter
        self.fmt = digital.protocol_formatter_bb(hdr_format, "packet_len")
        self.fmt_repack = blocks.repack_bits_bb(8, 1, "packet_len", False, gr.GR_MSB_FIRST)
        
        # Mux
        self.mux = blocks.tagged_stream_mux(gr.sizeof_char, "packet_len", 0)
        
        # For direct loopback (no modulation): skip Repack(1->8) and Unpack(8)
        # Just connect Mux -> Correlator directly
        
        # Correlator
        self.corr = digital.correlate_access_code_tag_bb(AC, 2, "packet_len")
        
        # Tag debug
        self.tag_debug = blocks.tag_debug(gr.sizeof_char, "corr_tag", "")
        self.tag_debug.set_display(True)
        
        self.sink = blocks.vector_sink_b()
        
        self.connect(self.src, self.crc, self.repack1, self.scrambler)
        self.connect(self.scrambler, self.fmt)
        self.connect(self.fmt, self.fmt_repack, (self.mux, 0))
        self.connect(self.scrambler, (self.mux, 1))
        self.connect(self.mux, self.corr, self.sink)
        self.connect(self.corr, self.tag_debug)

try:
    ftx = full_tx()
    ftx.run()
    output = list(ftx.sink.data())
    print(f"Correlator output: {len(output)} bytes")
    
    # Correlator girisi ne kadar?
    # scrambler output = 760 bit (91+4=95 byte * 8)
    # formatter output (repack): 96 bit
    # mux: 96 + 760 = 856 bit
    print(f"Expected mux output: 96 (header) + 760 (payload) = 856 bits")
    
    # AC pozisyonunu bul
    out_str = ''.join(str(b & 1) for b in output[:200])
    ac_pos = out_str.find(AC)
    print(f"AC found at position: {ac_pos}")
    
except Exception as e:
    print(f"HATA: {e}")
    import traceback
    traceback.print_exc()
