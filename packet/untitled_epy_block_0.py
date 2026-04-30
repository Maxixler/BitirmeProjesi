import numpy as np
from gnuradio import gr
import pmt


class arq_header_parser(gr.sync_block):
    def __init__(self):
        gr.sync_block.__init__(
            self,
            name='arq_header_parser',
            in_sig=[np.byte],
            out_sig=[]
        )
        self.message_port_register_out(pmt.intern('header_data'))
        self.buf = []
        self.payload_len = 110  # Fixed payload length in bytes

    def work(self, input_items, output_items):
        inp = input_items[0]
        self.buf.extend(inp.tolist())
        # 32 bits = 4 bytes
        while len(self.buf) >= 4:
            bits = self.buf[:4]
            self.buf = self.buf[4:]
            # Parse ARQ header format (32 bits = 4 bytes):
            # Bits 0-15: Sequence Number (16 bits)
            # Bit 16: ACK/NACK Flag (1 bit)
            # Bits 17-19: Retransmit Count (3 bits)
            # Bits 20-31: Reserved (12 bits)

            # Convert 4 bytes to 32 bits
            all_bits = []
            for byte in bits:
                for i in range(7, -1, -1):
                    all_bits.append((byte >> i) & 1)

            seq_num = 0
            for i in range(16):
                seq_num = (seq_num << 1) | all_bits[i]
            ack_nack = all_bits[16] & 1
            retrans_count = 0
            for i in range(17, 20):
                retrans_count = (retrans_count << 1) | all_bits[i]
            # Use fixed payload length for demux
            msg = pmt.make_dict()
            msg = pmt.dict_add(msg, pmt.intern('payload symbols'), pmt.from_long(self.payload_len))
            msg = pmt.dict_add(msg, pmt.intern('seq_num'), pmt.from_long(seq_num))
            msg = pmt.dict_add(msg, pmt.intern('ack_nack'), pmt.from_long(ack_nack))
            msg = pmt.dict_add(msg, pmt.intern('retrans_count'), pmt.from_long(retrans_count))
            self.message_port_pub(pmt.intern('header_data'), msg)
        return len(inp)
