#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Headless BPSK NOMA Receiver Flowgraph for USRP E310 Integration
--------------------------------------------------------------
Bu script, projenin son aşaması olan USRP E310 donanım testleri için
BPSK NOMA alıcı (receiver) ve SIC Aligner zincirini headless olarak gerçekler.
Masaüstü/Ekran olmayan terminal ortamlarında kararlı çalışır.
"""

import os
import sys
from gnuradio import gr, blocks, digital, fec, uhd
from gnuradio.filter import firdes
from gnuradio import filter
import pmt
import sip

# Embedded python blocks imports (working directory must contain these files)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import NOMA_epy_block_0 as epy_block_0
import NOMA_epy_block_0_0 as epy_block_0_0
import NOMA_epy_block_1 as epy_block_1

class NOMA_RX(gr.top_block):

    def __init__(self, samp_rate=200000, center_freq=868e6, rx_gain=25.0):
        gr.top_block.__init__(self, "NOMA RX", catch_exceptions=True)

        self.samp_rate = samp_rate
        self.center_freq = center_freq
        self.rx_gain = rx_gain

        # Dinamik Yollar (Windows/Linux Uyumlu)
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_dir = os.path.dirname(self.script_dir)
        self.alist_path = os.path.join(self.project_dir, 'n_1296_k_0648_ieee.alist')

        # Alinan veri dosya yolları
        self.rx1_file = os.path.join(self.script_dir, 'bpsk_receive.txt')
        self.rx2_file = os.path.join(self.script_dir, 'bpsk_receive_2.txt')

        # Variables
        self.sps = 4
        self.payload_size = 77
        self.preamble_size = 250
        self.postamble_size = 8
        self.preamble_syms = [complex(1 - 2 * ((b >> (7 - i)) & 1), 0) for b in [0xc0, 0xaf] * 4 for i in range(8)]

        # FEC LDPC Decoders and Encoder (User 1 reconstruction uses encoder)
        self.ldpc_dec = fec.ldpc_decoder.make(self.alist_path, 10)
        self.ldpc_dec_2 = fec.ldpc_decoder.make(self.alist_path, 10)
        self.ldpc_enc = fec.ldpc_encoder_make(self.alist_path)

        self.hdr = digital.header_format_default(digital.packet_utils.default_access_code, 0)
        self.constel = digital.constellation_bpsk().base()
        self.constel.set_npwr(1.0)

        ##################################################
        # Blocks
        ##################################################

        # UHD USRP Source (Fiziksel Anten Alıcısı)
        self.uhd_usrp_source_0 = uhd.usrp_source(
            ",".join(("", "")),
            uhd.stream_args(
                cpu_format="fc32",
                args='',
                channels=list(range(0, 1)),
            ),
        )
        self.uhd_usrp_source_0.set_samp_rate(self.samp_rate)
        self.uhd_usrp_source_0.set_center_freq(self.center_freq, 0)
        self.uhd_usrp_source_0.set_gain(self.rx_gain, 0)
        self.uhd_usrp_source_0.set_antenna("RX2", 0) # E310 RX2 antenna port

        # RRC Filter
        self.filter_fft_rrc_filter_0 = filter.fft_filter_ccc(
            1, 
            firdes.root_raised_cosine(1, self.samp_rate, (self.samp_rate/self.sps), 0.35, (11*self.sps)), 
            1
        )

        # Symbol Synchronizer
        self.digital_symbol_sync_xx_0 = digital.symbol_sync_cc(
            digital.TED_SIGNAL_TIMES_SLOPE_ML,
            self.sps,
            0.045,
            1.0,
            0.1,
            1.5,
            1,
            self.constel.base(),
            digital.IR_MMSE_8TAP,
            32,
            []
        )

        # Costas Loop
        self.digital_costas_loop_cc_0 = digital.costas_loop_cc((2*3.14/100), len(self.constel.points()), False)

        # Correlation Estimator (Preamble detection)
        self.digital_corr_est_cc_0 = digital.corr_est_cc(self.preamble_syms, 1, (len(self.preamble_syms)-1), 0.7, digital.THRESHOLD_ABSOLUTE)

        # File Sinks
        self.blocks_file_sink_0 = blocks.file_sink(gr.sizeof_char*1, self.rx1_file, False)
        self.blocks_file_sink_0.set_unbuffered(True)
        self.blocks_file_sink_0_0 = blocks.file_sink(gr.sizeof_char*1, self.rx2_file, False)
        self.blocks_file_sink_0_0.set_unbuffered(True)

        # ------------------------------------------------
        # USER 1 DECODER CHAIN
        # ------------------------------------------------
        self.digital_constellation_soft_decoder_cf_0 = digital.constellation_soft_decoder_cf(self.constel, -1)
        self.epy_block_0 = epy_block_0.blk(modulus=2) # Soft Diff Decoder for User 1
        self.digital_correlate_access_code_xx_ts_0 = digital.correlate_access_code_ff_ts(digital.packet_utils.default_access_code, 0, 'packet_len')
        self.fec_extended_decoder_0 = fec.extended_decoder(decoder_obj_list=self.ldpc_dec, threading='capillary', ann=None, puncpat='11', integration_period=10000)
        self.blocks_tagged_stream_multiply_length_0_1 = blocks.tagged_stream_multiply_length(gr.sizeof_char*1, "packet_len", 0.5)
        self.digital_additive_scrambler_xx_0_0 = digital.additive_scrambler_bb(0x8A, 0x7F, 7, count=0, bits_per_byte=1, reset_tag_key="packet_len")
        self.blocks_repack_bits_bb_1 = blocks.repack_bits_bb(1, 8, "packet_len", True, gr.GR_MSB_FIRST)
        self.digital_crc32_bb_1 = digital.crc32_bb(True, 'packet_len', True)

        # ------------------------------------------------
        # USER 1 RE-ENCODING & RE-MODULATION FOR SIC
        # ------------------------------------------------
        self.fec_extended_encoder_0_0_0 = fec.extended_encoder(encoder_obj_list=self.ldpc_enc, threading='capillary', puncpat='11')
        self.digital_chunks_to_symbols_xx_0 = digital.chunks_to_symbols_bc([-1.0+0j, 1.0+0j], 1)
        self.blocks_multiply_const_vxx_0_0_0 = blocks.multiply_const_cc(0.894) # Scale back to original tx1 amp

        # ------------------------------------------------
        # SUCCESSIVE INTERFERENCE CANCELLATION (SIC)
        # ------------------------------------------------
        # Self-aligning cross-correlation based custom aligner
        self.epy_block_1 = epy_block_1.blk(
            sample_rate=self.samp_rate, 
            near_user_amplitude=0.864, 
            search_window=32, 
            payload_size=1296, 
            payload_offset=64
        )

        # ------------------------------------------------
        # USER 2 DECODER CHAIN
        # ------------------------------------------------
        self.digital_constellation_soft_decoder_cf_0_0 = digital.constellation_soft_decoder_cf(self.constel, -1)
        self.epy_block_0_0 = epy_block_0_0.blk(modulus=2) # Soft Diff Decoder for User 2
        self.digital_correlate_access_code_xx_ts_0_0 = digital.correlate_access_code_ff_ts(digital.packet_utils.default_access_code, 0, 'packet_len')
        self.fec_extended_decoder_0_0 = fec.extended_decoder(decoder_obj_list=self.ldpc_dec_2, threading='capillary', ann=None, puncpat='11', integration_period=10000)
        self.blocks_tagged_stream_multiply_length_0_1_0 = blocks.tagged_stream_multiply_length(gr.sizeof_char*1, "packet_len", 0.5)
        self.digital_additive_scrambler_xx_0_0_0 = digital.additive_scrambler_bb(0xAB, 0x55, 7, count=0, bits_per_byte=1, reset_tag_key="packet_len")
        self.blocks_repack_bits_bb_1_1 = blocks.repack_bits_bb(1, 8, "packet_len", True, gr.GR_MSB_FIRST)
        self.digital_crc32_bb_1_0 = digital.crc32_bb(True, 'packet_len', True)

        ##################################################
        # Connections
        ##################################################
        
        # Superposed RF Stream Receiver
        self.connect((self.uhd_usrp_source_0, 0), (self.filter_fft_rrc_filter_0, 0))
        self.connect((self.filter_fft_rrc_filter_0, 0), (self.digital_symbol_sync_xx_0, 0))
        self.connect((self.digital_symbol_sync_xx_0, 0), (self.digital_costas_loop_cc_0, 0))
        self.connect((self.digital_costas_loop_cc_0, 0), (self.digital_corr_est_cc_0, 0))

        # USER 1 decoding path
        self.connect((self.digital_costas_loop_cc_0, 0), (self.digital_constellation_soft_decoder_cf_0, 0))
        self.connect((self.digital_constellation_soft_decoder_cf_0, 0), (self.epy_block_0, 0))
        self.connect((self.epy_block_0, 0), (self.digital_correlate_access_code_xx_ts_0, 0))
        self.connect((self.digital_correlate_access_code_xx_ts_0, 0), (self.fec_extended_decoder_0, 0))
        self.connect((self.fec_extended_decoder_0, 0), (self.blocks_tagged_stream_multiply_length_0_1, 0))
        self.connect((self.blocks_tagged_stream_multiply_length_0_1, 0), (self.digital_additive_scrambler_xx_0_0, 0))
        self.connect((self.digital_additive_scrambler_xx_0_0, 0), (self.blocks_repack_bits_bb_1, 0))
        self.connect((self.blocks_repack_bits_bb_1, 0), (self.digital_crc32_bb_1, 0))
        self.connect((self.digital_crc32_bb_1, 0), (self.blocks_file_sink_0, 0))

        # USER 1 re-encoding path (re-modulation for SIC subtraction)
        self.connect((self.blocks_tagged_stream_multiply_length_0_1, 0), (self.fec_extended_encoder_0_0_0, 0))
        self.connect((self.fec_extended_encoder_0_0_0, 0), (self.digital_chunks_to_symbols_xx_0, 0))
        self.connect((self.digital_chunks_to_symbols_xx_0, 0), (self.blocks_multiply_const_vxx_0_0_0, 0))

        # SIC Aligner Inputs
        self.connect((self.digital_corr_est_cc_0, 0), (self.epy_block_1, 0))             # In 0: Superposed stream
        self.connect((self.blocks_multiply_const_vxx_0_0_0, 0), (self.epy_block_1, 1))   # In 1: Reconstructed User 1

        # USER 2 decoding path (after User 1 is subtracted by SIC)
        self.connect((self.epy_block_1, 0), (self.digital_constellation_soft_decoder_cf_0_0, 0))
        self.connect((self.digital_constellation_soft_decoder_cf_0_0, 0), (self.epy_block_0_0, 0))
        self.connect((self.epy_block_0_0, 0), (self.digital_correlate_access_code_xx_ts_0_0, 0))
        self.connect((self.digital_correlate_access_code_xx_ts_0_0, 0), (self.fec_extended_decoder_0_0, 0))
        self.connect((self.fec_extended_decoder_0_0, 0), (self.blocks_tagged_stream_multiply_length_0_1_0, 0))
        self.connect((self.blocks_tagged_stream_multiply_length_0_1_0, 0), (self.digital_additive_scrambler_xx_0_0_0, 0))
        self.connect((self.digital_additive_scrambler_xx_0_0_0, 0), (self.blocks_repack_bits_bb_1_1, 0))
        self.connect((self.blocks_repack_bits_bb_1_1, 0), (self.digital_crc32_bb_1_0, 0))
        self.connect((self.digital_crc32_bb_1_0, 0), (self.blocks_file_sink_0_0, 0))


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Headless BPSK NOMA USRP Receiver")
    parser.add_argument("--freq", type=float, default=868e6, help="Merkez frekansi (Hz) [varsayilan: 868e6]")
    parser.add_argument("--rate", type=float, default=200e3, help="Ornekleme hizi (samples/sn) [varsayilan: 200e3]")
    parser.add_argument("--gain", type=float, default=25.0, help="USRP RX Kazanci (dB) [varsayilan: 25.0]")
    args = parser.parse_args()

    print(f"-> NOMA USRP Alicisi baslatiliyor...")
    print(f"   Frekans  : {args.freq/1e6:.3f} MHz")
    print(f"   Ornekleme: {args.rate/1e3:.1f} kSps")
    print(f"   RX Kazanc: {args.gain} dB")

    tb = NOMA_RX(samp_rate=int(args.rate), center_freq=args.freq, rx_gain=args.gain)
    tb.start()

    print("[RX RUNNING] Havadan gelen NOMA sinyalleri USRP uzerinden aliniyor ve SIC ile cozuluyor.")
    print("Durdurmak icin Ctrl+C tuslarina basin...")
    try:
        # Keep running
        import time
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\n-> Alici durduruluyor...")
        tb.stop()
        tb.wait()
    print("-> Alici basariyla kapatildi.")

if __name__ == '__main__':
    main()
