#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Headless BPSK NOMA Transmitter Flowgraph for USRP E310 Integration
------------------------------------------------------------------
Bu script, projenin son aşaması olan USRP E310 donanım testleri için 
BPSK NOMA süperpozisyon vericisini (transmitter) headless olarak gerçekler.
Masaüstü/Ekran olmayan terminal ortamlarında kararlı çalışır.
"""

import os
import sys
from gnuradio import gr, blocks, digital, fec, uhd
import pmt

class NOMA_TX(gr.top_block):

    def __init__(self, samp_rate=200000, center_freq=868e6, tx_gain=20.0):
        gr.top_block.__init__(self, "NOMA TX", catch_exceptions=True)

        self.samp_rate = samp_rate
        self.center_freq = center_freq
        self.tx_gain = tx_gain

        # Dinamik Dosya ve Alist Yolları (Windows/Linux Uyumlu)
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_dir = os.path.dirname(self.script_dir)
        self.alist_path = os.path.join(self.project_dir, 'n_1296_k_0648_ieee.alist')

        # Gönderim metin dosyası yolları (Padding eklenmiş)
        self.tx1_file = os.path.join(self.script_dir, 'bpsk_transmit.txt')
        self.tx2_file = os.path.join(self.script_dir, 'bpsk_transmit_2.txt')

        # Variables
        self.sps = 4
        self.payload_size = 77
        self.preamble_size = 250
        self.postamble_size = 8
        self.preamble_syms = [complex(1 - 2 * ((b >> (7 - i)) & 1), 0) for b in [0xc0, 0xaf] * 4 for i in range(8)]

        self.ldpc_enc = fec.ldpc_encoder_make(self.alist_path)
        self.hdr = digital.header_format_default(digital.packet_utils.default_access_code, 0)
        self.constel = digital.constellation_bpsk().base()
        self.constel.set_npwr(1.0)

        ##################################################
        # Blocks
        ##################################################

        # File Sources
        self.blocks_file_source_0 = blocks.file_source(gr.sizeof_char*1, self.tx1_file, False, 0, 0)
        self.blocks_file_source_0.set_begin_tag(pmt.PMT_NIL)
        self.blocks_file_source_0_0 = blocks.file_source(gr.sizeof_char*1, self.tx2_file, False, 0, 0)
        self.blocks_file_source_0_0.set_begin_tag(pmt.PMT_NIL)

        # Stream to Tagged Stream (Payloads)
        self.blocks_stream_to_tagged_stream_0_0_0 = blocks.stream_to_tagged_stream(gr.sizeof_char, 1, self.payload_size, "packet_len")
        self.blocks_stream_to_tagged_stream_0_0_0_1 = blocks.stream_to_tagged_stream(gr.sizeof_char, 1, self.payload_size, "packet_len")

        # CRC32 Blocks
        self.digital_crc32_bb_0 = digital.crc32_bb(False, "packet_len", True)
        self.digital_crc32_bb_0_0 = digital.crc32_bb(False, "packet_len", True)

        # Repack Bits 8 to 1 (Bits stream for LDPC)
        self.blocks_repack_bits_bb_0 = blocks.repack_bits_bb(8, 1, "packet_len", True, gr.GR_MSB_FIRST)
        self.blocks_repack_bits_bb_0_1 = blocks.repack_bits_bb(8, 1, "packet_len", True, gr.GR_MSB_FIRST)

        # Scramblers
        self.digital_additive_scrambler_xx_0 = digital.additive_scrambler_bb(0x8A, 0x7F, 7, count=0, bits_per_byte=1, reset_tag_key="packet_len")
        self.digital_additive_scrambler_xx_0_1 = digital.additive_scrambler_bb(0xAB, 0x55, 7, count=0, bits_per_byte=1, reset_tag_key="packet_len")

        # LDPC Encoders (1/2 Rate)
        self.fec_extended_encoder_0 = fec.extended_encoder(encoder_obj_list=self.ldpc_enc, threading='capillary', puncpat='11')
        self.fec_extended_encoder_0_0 = fec.extended_encoder(encoder_obj_list=self.ldpc_enc, threading='capillary', puncpat='11')

        # Tagged Stream Multiply Length (Length doubled due to 1/2 LDPC)
        self.blocks_tagged_stream_multiply_length_0 = blocks.tagged_stream_multiply_length(gr.sizeof_char*1, "packet_len", 2.0)
        self.blocks_tagged_stream_multiply_length_0_0 = blocks.tagged_stream_multiply_length(gr.sizeof_char*1, "packet_len", 2.0)

        # Repack Bits 1 to 8 (Back to bytes for multiplexing)
        self.blocks_repack_bits_bb_0_0 = blocks.repack_bits_bb(1, 8, "packet_len", True, gr.GR_MSB_FIRST)
        self.blocks_repack_bits_bb_0_0_0 = blocks.repack_bits_bb(1, 8, "packet_len", True, gr.GR_MSB_FIRST)

        # Header Protcol Formatters
        self.digital_protocol_formatter_bb_0 = digital.protocol_formatter_bb(self.hdr, 'packet_len')
        self.digital_protocol_formatter_bb_0_0 = digital.protocol_formatter_bb(self.hdr, 'packet_len')

        # Tagged Stream Multiply Length (Header prep)
        self.blocks_tagged_stream_multiply_length_0_1 = blocks.tagged_stream_multiply_length(gr.sizeof_char*1, "packet_len", 0.5)
        self.blocks_tagged_stream_multiply_length_0_1_0 = blocks.tagged_stream_multiply_length(gr.sizeof_char*1, "packet_len", 0.5)
        self.blocks_repack_bits_bb_1_0 = blocks.repack_bits_bb(1, 8, "packet_len", True, gr.GR_MSB_FIRST)
        self.blocks_repack_bits_bb_1_0_0 = blocks.repack_bits_bb(1, 8, "packet_len", True, gr.GR_MSB_FIRST)

        # Preambles and Postambles sources
        self.blocks_vector_source_x_0 = blocks.vector_source_b([0xc0, 0xaf], True, 1, [])
        self.blocks_vector_source_x_0_0 = blocks.vector_source_b([0xc0, 0xaf], True, 1, [])
        self.blocks_vector_source_x_0_1 = blocks.vector_source_b([0xc0, 0xaf], True, 1, [])
        self.blocks_vector_source_x_0_0_0 = blocks.vector_source_b([0xc0, 0xaf], True, 1, [])

        self.blocks_stream_to_tagged_stream_0_0_0_0 = blocks.stream_to_tagged_stream(gr.sizeof_char, 1, self.preamble_size, "packet_len")
        self.blocks_stream_to_tagged_stream_0_0_0_0_1 = blocks.stream_to_tagged_stream(gr.sizeof_char, 1, self.preamble_size, "packet_len")
        self.blocks_stream_to_tagged_stream_0_0_0_0_0 = blocks.stream_to_tagged_stream(gr.sizeof_char, 1, self.postamble_size, "packet_len")
        self.blocks_stream_to_tagged_stream_0_0_0_0_0_0 = blocks.stream_to_tagged_stream(gr.sizeof_char, 1, self.postamble_size, "packet_len")

        # Tagged Stream Mux
        self.blocks_tagged_stream_mux_0 = blocks.tagged_stream_mux(gr.sizeof_char*1, 'packet_len', 0)
        self.blocks_tagged_stream_mux_0_0 = blocks.tagged_stream_mux(gr.sizeof_char*1, 'packet_len', 0)

        # Modulators
        self.digital_constellation_modulator_0 = digital.generic_mod(
            constellation=self.constel,
            differential=True,
            samples_per_symbol=self.sps,
            pre_diff_code=True,
            excess_bw=0.35,
            verbose=False,
            log=False,
            truncate=False)
        self.digital_constellation_modulator_0_0 = digital.generic_mod(
            constellation=self.constel,
            differential=True,
            samples_per_symbol=self.sps,
            pre_diff_code=True,
            excess_bw=0.35,
            verbose=False,
            log=False,
            truncate=False)

        # Power Allocation Multipliers (NOMA: User 1 Near User has higher power, User 2 Far User has lower power)
        self.blocks_multiply_const_vxx_0 = blocks.multiply_const_cc(0.894)   # User 1 (Strong/Near)
        self.blocks_multiply_const_vxx_0_0 = blocks.multiply_const_cc(0.447) # User 2 (Weak/Far)

        # Tag Gate to strip packet boundary tags before transmission over air
        self.blocks_tag_gate_0 = blocks.tag_gate(gr.sizeof_gr_complex * 1, False)
        self.blocks_tag_gate_0.set_single_key("")
        self.blocks_tag_gate_0_0 = blocks.tag_gate(gr.sizeof_gr_complex * 1, False)
        self.blocks_tag_gate_0_0.set_single_key("")

        # Adder (Superposition coding)
        self.blocks_add_xx_0 = blocks.add_vcc(1)

        # UHD USRP Sink (Fiziksel Anten Vericisi)
        # Note: USRP DAC acts as throttle, no soft throttle block!
        self.uhd_usrp_sink_0 = uhd.usrp_sink(
            ",".join(("", "")),
            uhd.stream_args(
                cpu_format="fc32",
                args='',
                channels=list(range(0, 1)),
            ),
            '',
        )
        self.uhd_usrp_sink_0.set_samp_rate(self.samp_rate)
        self.uhd_usrp_sink_0.set_center_freq(self.center_freq, 0)
        self.uhd_usrp_sink_0.set_gain(self.tx_gain, 0)
        self.uhd_usrp_sink_0.set_antenna("TX/RX", 0)

        ##################################################
        # Connections
        ##################################################
        
        # User 1 Chain
        self.connect((self.blocks_file_source_0, 0), (self.blocks_stream_to_tagged_stream_0_0_0, 0))
        self.connect((self.blocks_stream_to_tagged_stream_0_0_0, 0), (self.digital_crc32_bb_0, 0))
        self.connect((self.digital_crc32_bb_0, 0), (self.blocks_repack_bits_bb_0, 0))
        self.connect((self.blocks_repack_bits_bb_0, 0), (self.digital_additive_scrambler_xx_0, 0))
        self.connect((self.digital_additive_scrambler_xx_0, 0), (self.fec_extended_encoder_0, 0))
        self.connect((self.fec_extended_encoder_0, 0), (self.blocks_tagged_stream_multiply_length_0, 0))
        self.connect((self.blocks_tagged_stream_multiply_length_0, 0), (self.blocks_repack_bits_bb_0_0, 0))
        self.connect((self.blocks_tagged_stream_multiply_length_0, 0), (self.blocks_repack_bits_bb_1_0, 0))
        self.connect((self.blocks_repack_bits_bb_1_0, 0), (self.digital_protocol_formatter_bb_0, 0))
        
        # User 1 Preamble and Postamble
        self.connect((self.blocks_vector_source_x_0, 0), (self.blocks_stream_to_tagged_stream_0_0_0_0, 0))
        self.connect((self.blocks_vector_source_x_0_0, 0), (self.blocks_stream_to_tagged_stream_0_0_0_0_0, 0))
        
        # User 1 Tagged Stream Mux
        self.connect((self.blocks_stream_to_tagged_stream_0_0_0_0, 0), (self.blocks_tagged_stream_mux_0, 0))
        self.connect((self.digital_protocol_formatter_bb_0, 0), (self.blocks_tagged_stream_mux_0, 1))
        self.connect((self.blocks_repack_bits_bb_0_0, 0), (self.blocks_tagged_stream_mux_0, 2))
        self.connect((self.blocks_stream_to_tagged_stream_0_0_0_0_0, 0), (self.blocks_tagged_stream_mux_0, 3))
        
        # User 1 Modulation and Power Allocation
        self.connect((self.blocks_tagged_stream_mux_0, 0), (self.digital_constellation_modulator_0, 0))
        self.connect((self.digital_constellation_modulator_0, 0), (self.blocks_multiply_const_vxx_0, 0))
        self.connect((self.blocks_multiply_const_vxx_0, 0), (self.blocks_tag_gate_0, 0))
        self.connect((self.blocks_tag_gate_0, 0), (self.blocks_add_xx_0, 0))

        # User 2 Chain
        self.connect((self.blocks_file_source_0_0, 0), (self.blocks_stream_to_tagged_stream_0_0_0_1, 0))
        self.connect((self.blocks_stream_to_tagged_stream_0_0_0_1, 0), (self.digital_crc32_bb_0_0, 0))
        self.connect((self.digital_crc32_bb_0_0, 0), (self.blocks_repack_bits_bb_0_1, 0))
        self.connect((self.blocks_repack_bits_bb_0_1, 0), (self.digital_additive_scrambler_xx_0_1, 0))
        self.connect((self.digital_additive_scrambler_xx_0_1, 0), (self.fec_extended_encoder_0_0, 0))
        self.connect((self.fec_extended_encoder_0_0, 0), (self.blocks_tagged_stream_multiply_length_0_0, 0))
        self.connect((self.blocks_tagged_stream_multiply_length_0_0, 0), (self.blocks_repack_bits_bb_0_0_0, 0))
        self.connect((self.blocks_tagged_stream_multiply_length_0_0, 0), (self.blocks_repack_bits_bb_1_0_0, 0))
        self.connect((self.blocks_repack_bits_bb_1_0_0, 0), (self.digital_protocol_formatter_bb_0_0, 0))
        
        # User 2 Preamble and Postamble
        self.connect((self.blocks_vector_source_x_0_1, 0), (self.blocks_stream_to_tagged_stream_0_0_0_0_1, 0))
        self.connect((self.blocks_vector_source_x_0_0_0, 0), (self.blocks_stream_to_tagged_stream_0_0_0_0_0_0, 0))

        # User 2 Tagged Stream Mux
        self.connect((self.blocks_stream_to_tagged_stream_0_0_0_0_1, 0), (self.blocks_tagged_stream_mux_0_0, 0))
        self.connect((self.digital_protocol_formatter_bb_0_0, 0), (self.blocks_tagged_stream_mux_0_0, 1))
        self.connect((self.blocks_repack_bits_bb_0_0_0, 0), (self.blocks_tagged_stream_mux_0_0, 2))
        self.connect((self.blocks_stream_to_tagged_stream_0_0_0_0_0_0, 0), (self.blocks_tagged_stream_mux_0_0, 3))
        
        # User 2 Modulation and Power Allocation
        self.connect((self.blocks_tagged_stream_mux_0_0, 0), (self.digital_constellation_modulator_0_0, 0))
        self.connect((self.digital_constellation_modulator_0_0, 0), (self.blocks_multiply_const_vxx_0_0, 0))
        self.connect((self.blocks_multiply_const_vxx_0_0, 0), (self.blocks_tag_gate_0_0, 0))
        self.connect((self.blocks_tag_gate_0_0, 0), (self.blocks_add_xx_0, 1))

        # Superposed output to UHD USRP Sink
        self.connect((self.blocks_add_xx_0, 0), (self.uhd_usrp_sink_0, 0))


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Headless BPSK NOMA USRP Transmitter")
    parser.add_argument("--freq", type=float, default=868e6, help="Merkez frekansi (Hz) [varsayilan: 868e6]")
    parser.add_argument("--rate", type=float, default=200e3, help="Ornekleme hizi (samples/sn) [varsayilan: 200e3]")
    parser.add_argument("--gain", type=float, default=20.0, help="USRP TX Kazanci (dB) [varsayilan: 20.0]")
    args = parser.parse_args()

    print(f"-> NOMA USRP Vericisi baslatiliyor...")
    print(f"   Frekans  : {args.freq/1e6:.3f} MHz")
    print(f"   Ornekleme: {args.rate/1e3:.1f} kSps")
    print(f"   TX Kazanc: {args.gain} dB")

    tb = NOMA_TX(samp_rate=int(args.rate), center_freq=args.freq, tx_gain=args.gain)
    tb.start()

    print("[TX RUNNING] NOMA superpoze sinyalleri USRP uzerinden iletiliyor.")
    print("Durdurmak icin Ctrl+C tuslarina basin...")
    try:
        # Keep running
        import time
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\n-> Verici durduruluyor...")
        tb.stop()
        tb.wait()
    print("-> Verici basariyla kapatildi.")

if __name__ == '__main__':
    main()
