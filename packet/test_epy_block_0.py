import numpy as np
from gnuradio import gr
import pmt


class custom_header_parser(gr.sync_block):
    def __init__(self):
        gr.sync_block.__init__(
            self,
            name='custom_header_parser',
            in_sig=[np.byte],
            out_sig=[]
        )
        self.message_port_register_out(pmt.intern('header_data'))
        self.buf = []

    def work(self, input_items, output_items):
        inp = input_items[0]
        self.buf.extend(inp.tolist())
        while len(self.buf) >= 32:
            bits = self.buf[:32]
            self.buf = self.buf[32:]
            len1 = 0
            for i in range(16):
                len1 = (len1 << 1) | (bits[i] & 1)
            len2 = 0
            for i in range(16, 32):
                len2 = (len2 << 1) | (bits[i] & 1)
            if len1 == len2 and 0 < len1 < 10000:
                msg = pmt.make_dict()
                msg = pmt.dict_add(msg, pmt.intern('payload symbols'), pmt.from_long(len1))
                self.message_port_pub(pmt.intern('header_data'), msg)
            else:
                self.message_port_pub(pmt.intern('header_data'), pmt.PMT_F)
        return len(inp)
