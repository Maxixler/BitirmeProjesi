import numpy as np
from gnuradio import gr
import pmt


class sequence_number_generator(gr.sync_block):
    def __init__(self):
        gr.sync_block.__init__(
            self,
            name='sequence_number_generator',
            in_sig=[np.byte],
            out_sig=[np.byte]
        )
        self.seq_num = 0
        self.pkt_len = 110
        self.pkt_count = 0
        self.message_port_register_out(pmt.intern('seq_num_info'))

    def work(self, input_items, output_items):
        inp = input_items[0]
        out = output_items[0]
        n_items = min(len(inp), len(out))
        for i in range(n_items):
            out[i] = inp[i]
        # Check if we have a complete packet
        self.pkt_count += n_items
        if self.pkt_count >= self.pkt_len:
            self.pkt_count = 0
            # Send sequence number info via message
            msg = pmt.make_dict()
            msg = pmt.dict_add(msg, pmt.intern('seq_num'), pmt.from_long(self.seq_num))
            self.message_port_pub(pmt.intern('seq_num_info'), msg)
            self.seq_num = (self.seq_num + 1) % 65536
        return n_items
