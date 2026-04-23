#!/usr/bin/env python3
"""
Custom parser: HPD'den 32 bit header alip payload_symbols dondur
"""
from gnuradio import gr, digital, blocks
import pmt, time
import numpy as np

AC = "1010101011110000101010101111000010101010111100001010101011110000"

class custom_header_parser(gr.sync_block):
    def __init__(self):
        gr.sync_block.__init__(
            self, name="custom_header_parser",
            in_sig=[np.byte], out_sig=[]
        )
        self.message_port_register_out(pmt.intern("header_data"))
        self.buffer = []
    
    def work(self, input_items, output_items):
        inp = input_items[0]
        self.buffer.extend(inp.tolist())
        
        while len(self.buffer) >= 32:
            bits = self.buffer[:32]
            self.buffer = self.buffer[32:]
            
            len1 = 0
            for i in range(16):
                len1 = (len1 << 1) | (bits[i] & 1)
            len2 = 0
            for i in range(16, 32):
                len2 = (len2 << 1) | (bits[i] & 1)
            
            if len1 == len2 and 0 < len1 < 65535:
                msg = pmt.make_dict()
                msg = pmt.dict_add(msg, pmt.intern("payload symbols"), pmt.from_long(len1))
                self.message_port_pub(pmt.intern("header_data"), msg)
            else:
                self.message_port_pub(pmt.intern("header_data"), pmt.PMT_F)
        
        return len(inp)

# TX
hdr_format_tx = digital.header_format_default(AC, 1, 8)

class tx_pkt(gr.top_block):
    def __init__(self, plen):
        gr.top_block.__init__(self)
        payload = [0, 1] * (plen // 2)
        tag = gr.tag_t(); tag.offset = 0
        tag.key = pmt.intern("packet_len"); tag.value = pmt.from_long(plen)
        self.src = blocks.vector_source_b(payload, False, 1, [tag])
        self.fmt = digital.protocol_formatter_bb(hdr_format_tx, "packet_len")
        self.fmt_repack = blocks.repack_bits_bb(8, 1, "packet_len", False, gr.GR_MSB_FIRST)
        self.mux = blocks.tagged_stream_mux(gr.sizeof_char, "packet_len", 0)
        self.sink = blocks.vector_sink_b()
        self.connect(self.src, self.fmt, self.fmt_repack, (self.mux, 0))
        self.connect(self.src, (self.mux, 1))
        self.connect(self.mux, self.sink)

packets = []
for i in range(3):
    tb = tx_pkt(1500); tb.run()
    packets.extend(list(tb.sink.data()))
print(f"TX: {len(packets)} bits, {len(packets)/1596:.0f} packets")

# RX
class rx_test(gr.top_block):
    def __init__(self, data):
        gr.top_block.__init__(self)
        self.src = blocks.vector_source_b(data, False)
        self.corr = digital.correlate_access_code_tag_bb(AC, 2, "packet_len")
        self.hpd = digital.header_payload_demux(
            32, 1, 0, "packet_len", "packet_len",
            False, gr.sizeof_char, "rx_time", 1000000, (), 0)
        self.parser = custom_header_parser()
        self.payload_sink = blocks.vector_sink_b()
        self.connect(self.src, self.corr, (self.hpd, 0))
        self.connect((self.hpd, 0), self.parser)
        self.msg_connect(self.parser, "header_data", self.hpd, "header_data")
        self.connect((self.hpd, 1), self.payload_sink)

try:
    tb = rx_test(packets)
    tb.start(); time.sleep(3); tb.stop(); tb.wait()
    payload = tb.payload_sink.data()
    print(f"HPD payload: {len(payload)} bytes")
    if len(payload) > 0:
        print(f"Packets: {len(payload)/1500:.1f}")
        print("SUCCESS!")
    else:
        print("FAIL")
except Exception as e:
    print(f"HATA: {e}")
    import traceback; traceback.print_exc()
