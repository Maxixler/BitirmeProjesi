#!/usr/bin/env python3
"""
Parser'in dondurdugu mesaj formatini ve HPD'nin bekledigini kontrol et
"""
from gnuradio import gr, digital, blocks
import pmt
import time

AC = "1010101011110000101010101111000010101010111100001010101011110000"

# Different bps values
for bps in [1, 2]:
    hdr = digital.header_format_default(AC, 0, bps)
    print(f"\nbps={bps}: header_nbits={hdr.header_nbits()}")
    
    # Generate header for payload_len=1500
    payload = [0] * 1500
    tag = gr.tag_t()
    tag.offset = 0
    tag.key = pmt.intern("packet_len")
    tag.value = pmt.from_long(1500)
    
    class tx(gr.top_block):
        def __init__(self, fmt, payload, tag):
            gr.top_block.__init__(self)
            self.src = blocks.vector_source_b(payload, False, 1, [tag])
            self.fmt = digital.protocol_formatter_bb(fmt, "packet_len")
            self.sink = blocks.vector_sink_b()
            self.connect(self.src, self.fmt, self.sink)
    
    tb = tx(hdr, payload, tag)
    tb.run()
    fmt_out = list(tb.sink.data())
    print(f"  Formatter output: {len(fmt_out)} packed bytes")
    
    # Unpack
    unpacked = []
    for b in fmt_out:
        for bit in range(7, -1, -1):
            unpacked.append((b >> bit) & 1)
    
    # Parse with protocol_parser_b
    class parse(gr.top_block):
        def __init__(self, data, fmt):
            gr.top_block.__init__(self)
            tag = gr.tag_t()
            tag.offset = 0
            tag.key = pmt.intern("packet_len")
            tag.value = pmt.from_long(len(data))
            self.src = blocks.vector_source_b(data, False, 1, [tag])
            self.parser = digital.protocol_parser_b(fmt)
            self.msg = blocks.message_debug()
            self.msg_connect(self.parser, "info", self.msg, "store")
            self.connect(self.src, self.parser)
    
    # Parse full header (unpacked)
    ptb = parse(unpacked, hdr)
    ptb.start()
    time.sleep(0.5)
    ptb.stop()
    ptb.wait()
    
    n = ptb.msg.num_messages()
    # Find first non-trivial message
    for i in range(min(n, 3)):
        m = ptb.msg.get_message(i)
        if pmt.is_false(m):
            continue
        if pmt.is_dict(m):
            # Extract all keys and values
            keys = pmt.dict_keys(m)
            vals = pmt.dict_values(m)
            print(f"  Parser output dict:")
            items = pmt.dict_items(m)
            length = pmt.length(items)
            for j in range(length):
                item = pmt.nth(j, items)
                key = pmt.car(item)
                val = pmt.cdr(item)
                print(f"    {pmt.symbol_to_string(key)} = {pmt.to_long(val)}")
            break

# Check what HPD expects
print("\n" + "="*60)
print("HPD mesaj beklentisi")
print("="*60)
print("HPD 'header_data' portundan gelen mesajda su key'leri arar:")
print("  - 'payload symbols': kac SEMBOL payload var")
print("  - Bu deger HPD'nin length_tag_key olarak kullandigi")
print("  - 'output_symbols=False' ise, items = payload_symbols * items_per_symbol")
print("  - 'output_symbols=True' ise, items = payload_symbols")
print()
print("test.grc'de:")
print("  items_per_symbol = 1")
print("  output_symbols = False")
print("  Yani payload items = payload_symbols * 1 = payload_symbols")
print()
print("Parser 'payload symbols: 12000' donduruyor (bps=1)")
print("  Ama gercek payload 1500 bit!")
print("  12000 / 8 = 1500 -> parser payload_len * 8 donduruyor???")
print("  HAYIR, bakalim hesap nasil yapiliyor...")

# Direct calculation: header stores payload_len=1500
# header_format_default::parse() reads 16-bit len twice, checks match
# Then returns: payload_symbols = len * ???
# bps=1: each symbol = 1 bit -> payload_symbols = 1500 / 1 = 1500? no it says 12000
# Maybe: payload_symbols = len (from header) = 1500
# Then: 1500 * 8 = 12000 because bps=1 and something else?

# Actually let me check what header value is stored
# Formatter writes to header: the value from packet_len tag
# packet_len tag BEFORE formatter = 1500 (from multiply_length)
# Header stores: 1500 as 16-bit unsigned int
# Parser reads: 1500
# Parser returns: payload symbols = 1500 * ??? 

# Check with smaller value
for plen in [10, 100, 1500]:
    payload2 = [0] * plen
    tag2 = gr.tag_t()
    tag2.offset = 0
    tag2.key = pmt.intern("packet_len")
    tag2.value = pmt.from_long(plen)
    
    tb2 = tx(hdr, payload2, tag2)
    tb2.run()
    fmt2 = list(tb2.sink.data())
    
    unpacked2 = []
    for b in fmt2:
        for bit in range(7, -1, -1):
            unpacked2.append((b >> bit) & 1)
    
    ptb2 = parse(unpacked2, hdr)
    ptb2.start()
    time.sleep(0.3)
    ptb2.stop()
    ptb2.wait()
    
    for i in range(ptb2.msg.num_messages()):
        m = ptb2.msg.get_message(i)
        if pmt.is_dict(m):
            items = pmt.dict_items(m)
            for j in range(pmt.length(items)):
                item = pmt.nth(j, items)
                key = pmt.car(item)
                val = pmt.cdr(item)
                sym_val = pmt.to_long(val)
                print(f"  plen={plen}: {pmt.symbol_to_string(key)} = {sym_val} (ratio: {sym_val/plen if plen > 0 else 'N/A'})")
            break
