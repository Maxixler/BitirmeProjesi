#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: TX_host
# Author: Armağan Bi - Eren Kale
# GNU Radio version: 3.10.12.0

from PyQt5 import Qt
from gnuradio import qtgui
from gnuradio import blocks
import pmt
from gnuradio import digital
from gnuradio import fec
from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import uhd
import time
import sip
import threading



class TX_host(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "TX_host", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("TX_host")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except BaseException as exc:
            print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "TX_host")

        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)
        self.flowgraph_started = threading.Event()

        ##################################################
        # Variables
        ##################################################
        self.sps = sps = 4
        self.samp_rate = samp_rate = 200e3
        self.preamble_size = preamble_size = 250
        self.postamble_size = postamble_size = 8
        self.payload_size = payload_size = 77
        self.ldpc_enc = ldpc_enc = fec.ldpc_encoder_make('C:\\Users\\DELL\\Downloads\\BitirmeProjesi2\\n_1296_k_0648_ieee.alist')
        self.ldpc_dec_2 = ldpc_dec_2 = fec.ldpc_decoder.make('C:\\Users\\DELL\\Downloads\\BitirmeProjesi2\\n_1296_k_0648_ieee.alist', 10)
        self.ldpc_dec = ldpc_dec = fec.ldpc_decoder.make('C:\\Users\\DELL\\Downloads\\BitirmeProjesi2\\n_1296_k_0648_ieee.alist', 10)
        self.hdr = hdr = digital.header_format_default(digital.packet_utils.default_access_code, 0)
        self.constel = constel = digital.constellation_bpsk().base()
        self.constel.set_npwr(1.0)

        ##################################################
        # Blocks
        ##################################################

        self.uhd_usrp_sink_0 = uhd.usrp_sink(
            ",".join(("", "mgmt_addr=192.168.10.2,num_send_frames=512,send_frame_size=1472,num_recv_frames=512,recv_frame_size=1472")),
            uhd.stream_args(
                cpu_format="fc32",
                args='',
                channels=list(range(0,1)),
            ),
            "",
        )
        self.uhd_usrp_sink_0.set_samp_rate(samp_rate)
        self.uhd_usrp_sink_0.set_time_unknown_pps(uhd.time_spec(0))

        self.uhd_usrp_sink_0.set_center_freq(868e6, 0)
        self.uhd_usrp_sink_0.set_antenna("TX/RX", 0)
        self.uhd_usrp_sink_0.set_gain(80, 0)
        self.qtgui_freq_sink_x_0 = qtgui.freq_sink_c(
            1024, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            0, #fc
            samp_rate, #bw
            "", #name
            1,
            None # parent
        )
        self.qtgui_freq_sink_x_0.set_update_time(0.10)
        self.qtgui_freq_sink_x_0.set_y_axis((-140), 10)
        self.qtgui_freq_sink_x_0.set_y_label('Relative Gain', 'dB')
        self.qtgui_freq_sink_x_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.qtgui_freq_sink_x_0.enable_autoscale(False)
        self.qtgui_freq_sink_x_0.enable_grid(False)
        self.qtgui_freq_sink_x_0.set_fft_average(1.0)
        self.qtgui_freq_sink_x_0.enable_axis_labels(True)
        self.qtgui_freq_sink_x_0.enable_control_panel(False)
        self.qtgui_freq_sink_x_0.set_fft_window_normalized(False)



        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_freq_sink_x_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_freq_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_freq_sink_x_0.set_line_width(i, widths[i])
            self.qtgui_freq_sink_x_0.set_line_color(i, colors[i])
            self.qtgui_freq_sink_x_0.set_line_alpha(i, alphas[i])

        self._qtgui_freq_sink_x_0_win = sip.wrapinstance(self.qtgui_freq_sink_x_0.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_freq_sink_x_0_win)
        self.fec_extended_encoder_0_0 = fec.extended_encoder(encoder_obj_list=ldpc_enc, threading='capillary', puncpat='11')
        self.fec_extended_encoder_0 = fec.extended_encoder(encoder_obj_list=ldpc_enc, threading='capillary', puncpat='11')
        self.digital_protocol_formatter_bb_0_0 = digital.protocol_formatter_bb(hdr, 'packet_len')
        self.digital_protocol_formatter_bb_0 = digital.protocol_formatter_bb(hdr, 'packet_len')
        self.digital_crc32_bb_0_0 = digital.crc32_bb(False, "packet_len", True)
        self.digital_crc32_bb_0 = digital.crc32_bb(False, "packet_len", True)
        self.digital_constellation_modulator_0_0 = digital.generic_mod(
            constellation=constel,
            differential=True,
            samples_per_symbol=sps,
            pre_diff_code=True,
            excess_bw=0.35,
            verbose=False,
            log=False,
            truncate=False)
        self.digital_constellation_modulator_0 = digital.generic_mod(
            constellation=constel,
            differential=True,
            samples_per_symbol=sps,
            pre_diff_code=True,
            excess_bw=0.35,
            verbose=False,
            log=False,
            truncate=False)
        self.digital_additive_scrambler_xx_0_1 = digital.additive_scrambler_bb(0xAB, 0x55, 7, count=0, bits_per_byte=1, reset_tag_key="packet_len")
        self.digital_additive_scrambler_xx_0 = digital.additive_scrambler_bb(0x8A, 0x7F, 7, count=0, bits_per_byte=1, reset_tag_key="packet_len")
        self.blocks_vector_source_x_0_1 = blocks.vector_source_b([0xc0, 0xaf], True, 1, [])
        self.blocks_vector_source_x_0_0_0 = blocks.vector_source_b([0xc0, 0xaf], True, 1, [])
        self.blocks_vector_source_x_0_0 = blocks.vector_source_b([0xc0, 0xaf], True, 1, [])
        self.blocks_vector_source_x_0 = blocks.vector_source_b([0xc0, 0xaf], True, 1, [])
        self.blocks_tagged_stream_mux_0_0 = blocks.tagged_stream_mux(gr.sizeof_char*1, 'packet_len', 0)
        self.blocks_tagged_stream_mux_0 = blocks.tagged_stream_mux(gr.sizeof_char*1, 'packet_len', 0)
        self.blocks_tagged_stream_multiply_length_0_0 = blocks.tagged_stream_multiply_length(gr.sizeof_char*1, "packet_len", 2.0)
        self.blocks_tagged_stream_multiply_length_0 = blocks.tagged_stream_multiply_length(gr.sizeof_char*1, "packet_len", 2.0)
        self.blocks_tag_gate_0_0 = blocks.tag_gate(gr.sizeof_gr_complex * 1, False)
        self.blocks_tag_gate_0_0.set_single_key("")
        self.blocks_tag_gate_0 = blocks.tag_gate(gr.sizeof_gr_complex * 1, False)
        self.blocks_tag_gate_0.set_single_key("")
        self.blocks_stream_to_tagged_stream_0_0_0_1 = blocks.stream_to_tagged_stream(gr.sizeof_char, 1, payload_size, "packet_len")
        self.blocks_stream_to_tagged_stream_0_0_0_0_1 = blocks.stream_to_tagged_stream(gr.sizeof_char, 1, preamble_size, "packet_len")
        self.blocks_stream_to_tagged_stream_0_0_0_0_0_0 = blocks.stream_to_tagged_stream(gr.sizeof_char, 1, postamble_size, "packet_len")
        self.blocks_stream_to_tagged_stream_0_0_0_0_0 = blocks.stream_to_tagged_stream(gr.sizeof_char, 1, postamble_size, "packet_len")
        self.blocks_stream_to_tagged_stream_0_0_0_0 = blocks.stream_to_tagged_stream(gr.sizeof_char, 1, preamble_size, "packet_len")
        self.blocks_stream_to_tagged_stream_0_0_0 = blocks.stream_to_tagged_stream(gr.sizeof_char, 1, payload_size, "packet_len")
        self.blocks_repack_bits_bb_1_0_0 = blocks.repack_bits_bb(1, 8, "packet_len", True, gr.GR_MSB_FIRST)
        self.blocks_repack_bits_bb_1_0 = blocks.repack_bits_bb(1, 8, "packet_len", True, gr.GR_MSB_FIRST)
        self.blocks_repack_bits_bb_0_1 = blocks.repack_bits_bb(8, 1, "packet_len", True, gr.GR_MSB_FIRST)
        self.blocks_repack_bits_bb_0_0_0 = blocks.repack_bits_bb(1, 8, "packet_len", True, gr.GR_MSB_FIRST)
        self.blocks_repack_bits_bb_0_0 = blocks.repack_bits_bb(1, 8, "packet_len", True, gr.GR_MSB_FIRST)
        self.blocks_repack_bits_bb_0 = blocks.repack_bits_bb(8, 1, "packet_len", True, gr.GR_MSB_FIRST)
        self.blocks_multiply_const_vxx_0_0 = blocks.multiply_const_cc(0.894)
        self.blocks_multiply_const_vxx_0 = blocks.multiply_const_cc(0.447)
        self.blocks_file_source_0_0 = blocks.file_source(gr.sizeof_char*1, 'C:\\Users\\DELL\\Downloads\\BitirmeProjesi2\\bpsk_transmit_2.txt', False, 0, 0)
        self.blocks_file_source_0_0.set_begin_tag(pmt.PMT_NIL)
        self.blocks_file_source_0 = blocks.file_source(gr.sizeof_char*1, 'C:\\Users\\DELL\\Downloads\\BitirmeProjesi2\\bpsk_transmit.txt', False, 0, 0)
        self.blocks_file_source_0.set_begin_tag(pmt.PMT_NIL)
        self.blocks_add_xx_0 = blocks.add_vcc(1)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_add_xx_0, 0), (self.qtgui_freq_sink_x_0, 0))
        self.connect((self.blocks_add_xx_0, 0), (self.uhd_usrp_sink_0, 0))
        self.connect((self.blocks_file_source_0, 0), (self.blocks_stream_to_tagged_stream_0_0_0, 0))
        self.connect((self.blocks_file_source_0_0, 0), (self.blocks_stream_to_tagged_stream_0_0_0_1, 0))
        self.connect((self.blocks_multiply_const_vxx_0, 0), (self.blocks_tag_gate_0, 0))
        self.connect((self.blocks_multiply_const_vxx_0_0, 0), (self.blocks_tag_gate_0_0, 0))
        self.connect((self.blocks_repack_bits_bb_0, 0), (self.digital_additive_scrambler_xx_0, 0))
        self.connect((self.blocks_repack_bits_bb_0_0, 0), (self.blocks_tagged_stream_mux_0, 2))
        self.connect((self.blocks_repack_bits_bb_0_0_0, 0), (self.blocks_tagged_stream_mux_0_0, 2))
        self.connect((self.blocks_repack_bits_bb_0_1, 0), (self.digital_additive_scrambler_xx_0_1, 0))
        self.connect((self.blocks_repack_bits_bb_1_0, 0), (self.digital_protocol_formatter_bb_0, 0))
        self.connect((self.blocks_repack_bits_bb_1_0_0, 0), (self.digital_protocol_formatter_bb_0_0, 0))
        self.connect((self.blocks_stream_to_tagged_stream_0_0_0, 0), (self.digital_crc32_bb_0, 0))
        self.connect((self.blocks_stream_to_tagged_stream_0_0_0_0, 0), (self.blocks_tagged_stream_mux_0, 0))
        self.connect((self.blocks_stream_to_tagged_stream_0_0_0_0_0, 0), (self.blocks_tagged_stream_mux_0, 3))
        self.connect((self.blocks_stream_to_tagged_stream_0_0_0_0_0_0, 0), (self.blocks_tagged_stream_mux_0_0, 3))
        self.connect((self.blocks_stream_to_tagged_stream_0_0_0_0_1, 0), (self.blocks_tagged_stream_mux_0_0, 0))
        self.connect((self.blocks_stream_to_tagged_stream_0_0_0_1, 0), (self.digital_crc32_bb_0_0, 0))
        self.connect((self.blocks_tag_gate_0, 0), (self.blocks_add_xx_0, 1))
        self.connect((self.blocks_tag_gate_0_0, 0), (self.blocks_add_xx_0, 0))
        self.connect((self.blocks_tagged_stream_multiply_length_0, 0), (self.blocks_repack_bits_bb_0_0, 0))
        self.connect((self.blocks_tagged_stream_multiply_length_0, 0), (self.blocks_repack_bits_bb_1_0, 0))
        self.connect((self.blocks_tagged_stream_multiply_length_0_0, 0), (self.blocks_repack_bits_bb_0_0_0, 0))
        self.connect((self.blocks_tagged_stream_multiply_length_0_0, 0), (self.blocks_repack_bits_bb_1_0_0, 0))
        self.connect((self.blocks_tagged_stream_mux_0, 0), (self.digital_constellation_modulator_0_0, 0))
        self.connect((self.blocks_tagged_stream_mux_0_0, 0), (self.digital_constellation_modulator_0, 0))
        self.connect((self.blocks_vector_source_x_0, 0), (self.blocks_stream_to_tagged_stream_0_0_0_0, 0))
        self.connect((self.blocks_vector_source_x_0_0, 0), (self.blocks_stream_to_tagged_stream_0_0_0_0_0, 0))
        self.connect((self.blocks_vector_source_x_0_0_0, 0), (self.blocks_stream_to_tagged_stream_0_0_0_0_0_0, 0))
        self.connect((self.blocks_vector_source_x_0_1, 0), (self.blocks_stream_to_tagged_stream_0_0_0_0_1, 0))
        self.connect((self.digital_additive_scrambler_xx_0, 0), (self.fec_extended_encoder_0, 0))
        self.connect((self.digital_additive_scrambler_xx_0_1, 0), (self.fec_extended_encoder_0_0, 0))
        self.connect((self.digital_constellation_modulator_0, 0), (self.blocks_multiply_const_vxx_0, 0))
        self.connect((self.digital_constellation_modulator_0_0, 0), (self.blocks_multiply_const_vxx_0_0, 0))
        self.connect((self.digital_crc32_bb_0, 0), (self.blocks_repack_bits_bb_0, 0))
        self.connect((self.digital_crc32_bb_0_0, 0), (self.blocks_repack_bits_bb_0_1, 0))
        self.connect((self.digital_protocol_formatter_bb_0, 0), (self.blocks_tagged_stream_mux_0, 1))
        self.connect((self.digital_protocol_formatter_bb_0_0, 0), (self.blocks_tagged_stream_mux_0_0, 1))
        self.connect((self.fec_extended_encoder_0, 0), (self.blocks_tagged_stream_multiply_length_0, 0))
        self.connect((self.fec_extended_encoder_0_0, 0), (self.blocks_tagged_stream_multiply_length_0_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "TX_host")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_sps(self):
        return self.sps

    def set_sps(self, sps):
        self.sps = sps

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.qtgui_freq_sink_x_0.set_frequency_range(0, self.samp_rate)
        self.uhd_usrp_sink_0.set_samp_rate(self.samp_rate)

    def get_preamble_size(self):
        return self.preamble_size

    def set_preamble_size(self, preamble_size):
        self.preamble_size = preamble_size
        self.blocks_stream_to_tagged_stream_0_0_0_0.set_packet_len(self.preamble_size)
        self.blocks_stream_to_tagged_stream_0_0_0_0.set_packet_len_pmt(self.preamble_size)
        self.blocks_stream_to_tagged_stream_0_0_0_0_1.set_packet_len(self.preamble_size)
        self.blocks_stream_to_tagged_stream_0_0_0_0_1.set_packet_len_pmt(self.preamble_size)

    def get_postamble_size(self):
        return self.postamble_size

    def set_postamble_size(self, postamble_size):
        self.postamble_size = postamble_size
        self.blocks_stream_to_tagged_stream_0_0_0_0_0.set_packet_len(self.postamble_size)
        self.blocks_stream_to_tagged_stream_0_0_0_0_0.set_packet_len_pmt(self.postamble_size)
        self.blocks_stream_to_tagged_stream_0_0_0_0_0_0.set_packet_len(self.postamble_size)
        self.blocks_stream_to_tagged_stream_0_0_0_0_0_0.set_packet_len_pmt(self.postamble_size)

    def get_payload_size(self):
        return self.payload_size

    def set_payload_size(self, payload_size):
        self.payload_size = payload_size
        self.blocks_stream_to_tagged_stream_0_0_0.set_packet_len(self.payload_size)
        self.blocks_stream_to_tagged_stream_0_0_0.set_packet_len_pmt(self.payload_size)
        self.blocks_stream_to_tagged_stream_0_0_0_1.set_packet_len(self.payload_size)
        self.blocks_stream_to_tagged_stream_0_0_0_1.set_packet_len_pmt(self.payload_size)

    def get_ldpc_enc(self):
        return self.ldpc_enc

    def set_ldpc_enc(self, ldpc_enc):
        self.ldpc_enc = ldpc_enc

    def get_ldpc_dec_2(self):
        return self.ldpc_dec_2

    def set_ldpc_dec_2(self, ldpc_dec_2):
        self.ldpc_dec_2 = ldpc_dec_2

    def get_ldpc_dec(self):
        return self.ldpc_dec

    def set_ldpc_dec(self, ldpc_dec):
        self.ldpc_dec = ldpc_dec

    def get_hdr(self):
        return self.hdr

    def set_hdr(self, hdr):
        self.hdr = hdr
        self.digital_protocol_formatter_bb_0.set_header_format(self.hdr)
        self.digital_protocol_formatter_bb_0_0.set_header_format(self.hdr)

    def get_constel(self):
        return self.constel

    def set_constel(self, constel):
        self.constel = constel




def main(top_block_cls=TX_host, options=None):

    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

    tb.start()
    tb.flowgraph_started.set()

    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
