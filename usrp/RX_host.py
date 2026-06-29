#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: RX_host
# Author: Armağan Bi - Eren Kale
# GNU Radio version: 3.10.12.0

from PyQt5 import Qt
from gnuradio import qtgui
from gnuradio import blocks
from gnuradio import blocks, gr
from gnuradio import digital
from gnuradio import filter
from gnuradio import fec
from gnuradio.filter import firdes
from gnuradio import gr
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import gr, pdu
from gnuradio import uhd
import time
import RX_host_epy_block_0 as epy_block_0  # embedded python block
import RX_host_epy_block_0_0 as epy_block_0_0  # embedded python block
import RX_host_epy_block_1 as epy_block_1  # embedded python block
import sip
import threading



class RX_host(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "RX_host", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("RX_host")
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

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "RX_host")

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
        self.preamble_syms = preamble_syms = [complex(1 - 2 * ((b >> (7 - i)) & 1), 0) for b in [0xc0, 0xaf] * 4 for i in range(8)]
        self.preamble_size = preamble_size = 250
        self.postamble_size = postamble_size = 8
        self.payload_size = payload_size = 77
        self.ldpc_enc = ldpc_enc = fec.ldpc_encoder_make('/home/qrispy/BitirmeProje/n_1296_k_0648_ieee.alist')
        self.ldpc_dec_2 = ldpc_dec_2 = fec.ldpc_decoder.make('/home/qrispy/BitirmeProje/n_1296_k_0648_ieee.alist', 10)
        self.ldpc_dec = ldpc_dec = fec.ldpc_decoder.make('/home/qrispy/BitirmeProje/n_1296_k_0648_ieee.alist', 10)
        self.hdr = hdr = digital.header_format_default(digital.packet_utils.default_access_code, 0)
        self.constel = constel = digital.constellation_bpsk().base()
        self.constel.set_npwr(1.0)

        ##################################################
        # Blocks
        ##################################################

        self.uhd_usrp_source_0 = uhd.usrp_source(
            ",".join(("", '')),
            uhd.stream_args(
                cpu_format="fc32",
                args='',
                channels=list(range(0,1)),
            ),
        )
        self.uhd_usrp_source_0.set_samp_rate(samp_rate)
        self.uhd_usrp_source_0.set_time_unknown_pps(uhd.time_spec(0))

        self.uhd_usrp_source_0.set_center_freq(868e6, 0)
        self.uhd_usrp_source_0.set_antenna("RX2", 0)
        self.uhd_usrp_source_0.set_gain(42, 0)
        self.qtgui_time_sink_x_1_0_0 = qtgui.time_sink_c(
            256, #size
            samp_rate/sps, #samp_rate
            'USER 2', #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_time_sink_x_1_0_0.set_update_time(0.1)
        self.qtgui_time_sink_x_1_0_0.set_y_axis(-1.0, 1.0)

        self.qtgui_time_sink_x_1_0_0.set_y_label('Amplitude', "")

        self.qtgui_time_sink_x_1_0_0.enable_tags(True)
        self.qtgui_time_sink_x_1_0_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.01, 0.0, 0, "")
        self.qtgui_time_sink_x_1_0_0.enable_autoscale(False)
        self.qtgui_time_sink_x_1_0_0.enable_grid(True)
        self.qtgui_time_sink_x_1_0_0.enable_axis_labels(True)
        self.qtgui_time_sink_x_1_0_0.enable_control_panel(False)
        self.qtgui_time_sink_x_1_0_0.enable_stem_plot(False)


        labels = ['Real', 'Imag', 'Signal 3', 'Signal 4', 'Signal 5',
            'Signal 6', 'Signal 7', 'Signal 8', 'Signal 9', 'Signal 10']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ['blue', 'red', 'green', 'black', 'cyan',
            'magenta', 'yellow', 'dark red', 'dark green', 'dark blue']
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]
        styles = [1, 3, 1, 3, 1,
            1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1]


        for i in range(2):
            if len(labels[i]) == 0:
                if (i % 2 == 0):
                    self.qtgui_time_sink_x_1_0_0.set_line_label(i, "Re{{Data {0}}}".format(i/2))
                else:
                    self.qtgui_time_sink_x_1_0_0.set_line_label(i, "Im{{Data {0}}}".format(i/2))
            else:
                self.qtgui_time_sink_x_1_0_0.set_line_label(i, labels[i])
            self.qtgui_time_sink_x_1_0_0.set_line_width(i, widths[i])
            self.qtgui_time_sink_x_1_0_0.set_line_color(i, colors[i])
            self.qtgui_time_sink_x_1_0_0.set_line_style(i, styles[i])
            self.qtgui_time_sink_x_1_0_0.set_line_marker(i, markers[i])
            self.qtgui_time_sink_x_1_0_0.set_line_alpha(i, alphas[i])

        self._qtgui_time_sink_x_1_0_0_win = sip.wrapinstance(self.qtgui_time_sink_x_1_0_0.qwidget(), Qt.QWidget)
        self.top_grid_layout.addWidget(self._qtgui_time_sink_x_1_0_0_win, 9, 0, 4, 3)
        for r in range(9, 13):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.qtgui_time_sink_x_1_0 = qtgui.time_sink_c(
            256, #size
            samp_rate/sps, #samp_rate
            'Recovered Symbols', #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_time_sink_x_1_0.set_update_time(0.1)
        self.qtgui_time_sink_x_1_0.set_y_axis(-1.0, 1.0)

        self.qtgui_time_sink_x_1_0.set_y_label('Amplitude', "")

        self.qtgui_time_sink_x_1_0.enable_tags(True)
        self.qtgui_time_sink_x_1_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.01, 0.0, 0, "")
        self.qtgui_time_sink_x_1_0.enable_autoscale(False)
        self.qtgui_time_sink_x_1_0.enable_grid(True)
        self.qtgui_time_sink_x_1_0.enable_axis_labels(True)
        self.qtgui_time_sink_x_1_0.enable_control_panel(False)
        self.qtgui_time_sink_x_1_0.enable_stem_plot(False)


        labels = ['Real', 'Imag', 'Signal 3', 'Signal 4', 'Signal 5',
            'Signal 6', 'Signal 7', 'Signal 8', 'Signal 9', 'Signal 10']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ['blue', 'red', 'green', 'black', 'cyan',
            'magenta', 'yellow', 'dark red', 'dark green', 'dark blue']
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]
        styles = [1, 3, 1, 3, 1,
            1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1]


        for i in range(2):
            if len(labels[i]) == 0:
                if (i % 2 == 0):
                    self.qtgui_time_sink_x_1_0.set_line_label(i, "Re{{Data {0}}}".format(i/2))
                else:
                    self.qtgui_time_sink_x_1_0.set_line_label(i, "Im{{Data {0}}}".format(i/2))
            else:
                self.qtgui_time_sink_x_1_0.set_line_label(i, labels[i])
            self.qtgui_time_sink_x_1_0.set_line_width(i, widths[i])
            self.qtgui_time_sink_x_1_0.set_line_color(i, colors[i])
            self.qtgui_time_sink_x_1_0.set_line_style(i, styles[i])
            self.qtgui_time_sink_x_1_0.set_line_marker(i, markers[i])
            self.qtgui_time_sink_x_1_0.set_line_alpha(i, alphas[i])

        self._qtgui_time_sink_x_1_0_win = sip.wrapinstance(self.qtgui_time_sink_x_1_0.qwidget(), Qt.QWidget)
        self.top_grid_layout.addWidget(self._qtgui_time_sink_x_1_0_win, 5, 0, 4, 3)
        for r in range(5, 9):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.qtgui_time_sink_x_0_0 = qtgui.time_sink_c(
            1024, #size
            samp_rate, #samp_rate
            'Received Samples', #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_time_sink_x_0_0.set_update_time(0.10)
        self.qtgui_time_sink_x_0_0.set_y_axis(-1.0, 1.0)

        self.qtgui_time_sink_x_0_0.set_y_label('Amplitude', "")

        self.qtgui_time_sink_x_0_0.enable_tags(True)
        self.qtgui_time_sink_x_0_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0.0, 0, '')
        self.qtgui_time_sink_x_0_0.enable_autoscale(False)
        self.qtgui_time_sink_x_0_0.enable_grid(True)
        self.qtgui_time_sink_x_0_0.enable_axis_labels(True)
        self.qtgui_time_sink_x_0_0.enable_control_panel(False)
        self.qtgui_time_sink_x_0_0.enable_stem_plot(False)


        labels = ['Real', 'Imag', 'Signal 3', 'Signal 4', 'Signal 5',
            'Signal 6', 'Signal 7', 'Signal 8', 'Signal 9', 'Signal 10']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ['blue', 'red', 'green', 'black', 'cyan',
            'magenta', 'yellow', 'dark red', 'dark green', 'dark blue']
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]
        styles = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1]


        for i in range(2):
            if len(labels[i]) == 0:
                if (i % 2 == 0):
                    self.qtgui_time_sink_x_0_0.set_line_label(i, "Re{{Data {0}}}".format(i/2))
                else:
                    self.qtgui_time_sink_x_0_0.set_line_label(i, "Im{{Data {0}}}".format(i/2))
            else:
                self.qtgui_time_sink_x_0_0.set_line_label(i, labels[i])
            self.qtgui_time_sink_x_0_0.set_line_width(i, widths[i])
            self.qtgui_time_sink_x_0_0.set_line_color(i, colors[i])
            self.qtgui_time_sink_x_0_0.set_line_style(i, styles[i])
            self.qtgui_time_sink_x_0_0.set_line_marker(i, markers[i])
            self.qtgui_time_sink_x_0_0.set_line_alpha(i, alphas[i])

        self._qtgui_time_sink_x_0_0_win = sip.wrapinstance(self.qtgui_time_sink_x_0_0.qwidget(), Qt.QWidget)
        self.top_grid_layout.addWidget(self._qtgui_time_sink_x_0_0_win, 1, 0, 4, 3)
        for r in range(1, 5):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
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
        self.pdu_tagged_stream_to_pdu_0_0 = pdu.tagged_stream_to_pdu(gr.types.byte_t, 'packet_len')
        self.pdu_tagged_stream_to_pdu_0 = pdu.tagged_stream_to_pdu(gr.types.byte_t, 'packet_len')
        self.filter_fft_rrc_filter_0 = filter.fft_filter_ccc(1, firdes.root_raised_cosine(1, samp_rate, (samp_rate/sps), 0.35, (11*sps)), 1)
        self.fec_extended_encoder_0_0_0 = fec.extended_encoder(encoder_obj_list=ldpc_enc, threading='capillary', puncpat='11')
        self.fec_extended_decoder_0_0 = fec.extended_decoder(decoder_obj_list=ldpc_dec_2, threading='capillary', ann=None, puncpat='11', integration_period=10000)
        self.fec_extended_decoder_0 = fec.extended_decoder(decoder_obj_list=ldpc_dec, threading='capillary', ann=None, puncpat='11', integration_period=10000)
        self.epy_block_1 = epy_block_1.blk(sample_rate=samp_rate, near_user_amplitude=0.085, search_window=32, payload_size=1296, payload_offset=64)
        self.epy_block_0_0 = epy_block_0_0.blk(modulus=2)
        self.epy_block_0 = epy_block_0.blk(modulus=2)
        self.digital_symbol_sync_xx_0 = digital.symbol_sync_cc(
            digital.TED_SIGNAL_TIMES_SLOPE_ML,
            sps,
            0.045,
            1.0,
            0.1,
            1.5,
            1,
            constel.base(),
            digital.IR_MMSE_8TAP,
            32,
            [])
        self.digital_crc32_bb_1_0 = digital.crc32_bb(True, 'packet_len', True)
        self.digital_crc32_bb_1 = digital.crc32_bb(True, 'packet_len', True)
        self.digital_costas_loop_cc_0 = digital.costas_loop_cc((2*3.14/100), len(constel.points()), False)
        self.digital_correlate_access_code_xx_ts_0_0 = digital.correlate_access_code_ff_ts(digital.packet_utils.default_access_code,
          1, 'packet_len')
        self.digital_correlate_access_code_xx_ts_0 = digital.correlate_access_code_ff_ts(digital.packet_utils.default_access_code,
          1, 'packet_len')
        self.digital_corr_est_cc_0 = digital.corr_est_cc(preamble_syms, 1, (len(preamble_syms)-1), 0.7, digital.THRESHOLD_ABSOLUTE)
        self.digital_constellation_soft_decoder_cf_0_0 = digital.constellation_soft_decoder_cf(constel, -1)
        self.digital_constellation_soft_decoder_cf_0 = digital.constellation_soft_decoder_cf(constel, -1)
        self.digital_chunks_to_symbols_xx_0 = digital.chunks_to_symbols_bc([-1.0+0j, 1.0+0j], 1)
        self.digital_additive_scrambler_xx_0_0_0 = digital.additive_scrambler_bb(0xAB, 0x55, 7, count=0, bits_per_byte=1, reset_tag_key="packet_len")
        self.digital_additive_scrambler_xx_0_0 = digital.additive_scrambler_bb(0x8A, 0x7F, 7, count=0, bits_per_byte=1, reset_tag_key="packet_len")
        self.blocks_throttle2_0 = blocks.throttle( gr.sizeof_gr_complex*1, samp_rate, True, 0 if "auto" == "auto" else max( int(float(0.1) * samp_rate) if "auto" == "time" else int(0.1), 1) )
        self.blocks_tagged_stream_multiply_length_0_1_0 = blocks.tagged_stream_multiply_length(gr.sizeof_char*1, "packet_len", 0.5)
        self.blocks_tagged_stream_multiply_length_0_1 = blocks.tagged_stream_multiply_length(gr.sizeof_char*1, "packet_len", 0.5)
        self.blocks_repack_bits_bb_1_1 = blocks.repack_bits_bb(1, 8, "packet_len", True, gr.GR_MSB_FIRST)
        self.blocks_repack_bits_bb_1 = blocks.repack_bits_bb(1, 8, "packet_len", True, gr.GR_MSB_FIRST)
        self.blocks_multiply_const_vxx_0_0_0 = blocks.multiply_const_cc(0.894)
        self.blocks_message_debug_0_0 = blocks.message_debug(True, gr.log_levels.info)
        self.blocks_message_debug_0 = blocks.message_debug(True, gr.log_levels.info)
        self.blocks_file_sink_0_0 = blocks.file_sink(gr.sizeof_char*1, '/home/qrispy/BitirmeProje/bpsk_receive_2.txt', False)
        self.blocks_file_sink_0_0.set_unbuffered(True)
        self.blocks_file_sink_0 = blocks.file_sink(gr.sizeof_char*1, '/home/qrispy/BitirmeProje/bpsk_receive.txt', False)
        self.blocks_file_sink_0.set_unbuffered(True)


        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.pdu_tagged_stream_to_pdu_0, 'pdus'), (self.blocks_message_debug_0, 'print'))
        self.msg_connect((self.pdu_tagged_stream_to_pdu_0_0, 'pdus'), (self.blocks_message_debug_0_0, 'print'))
        self.connect((self.blocks_multiply_const_vxx_0_0_0, 0), (self.epy_block_1, 1))
        self.connect((self.blocks_repack_bits_bb_1, 0), (self.digital_crc32_bb_1, 0))
        self.connect((self.blocks_repack_bits_bb_1_1, 0), (self.digital_crc32_bb_1_0, 0))
        self.connect((self.blocks_tagged_stream_multiply_length_0_1, 0), (self.digital_additive_scrambler_xx_0_0, 0))
        self.connect((self.blocks_tagged_stream_multiply_length_0_1, 0), (self.fec_extended_encoder_0_0_0, 0))
        self.connect((self.blocks_tagged_stream_multiply_length_0_1_0, 0), (self.digital_additive_scrambler_xx_0_0_0, 0))
        self.connect((self.blocks_throttle2_0, 0), (self.filter_fft_rrc_filter_0, 0))
        self.connect((self.blocks_throttle2_0, 0), (self.qtgui_freq_sink_x_0, 0))
        self.connect((self.blocks_throttle2_0, 0), (self.qtgui_time_sink_x_0_0, 0))
        self.connect((self.digital_additive_scrambler_xx_0_0, 0), (self.blocks_repack_bits_bb_1, 0))
        self.connect((self.digital_additive_scrambler_xx_0_0_0, 0), (self.blocks_repack_bits_bb_1_1, 0))
        self.connect((self.digital_chunks_to_symbols_xx_0, 0), (self.blocks_multiply_const_vxx_0_0_0, 0))
        self.connect((self.digital_constellation_soft_decoder_cf_0, 0), (self.epy_block_0, 0))
        self.connect((self.digital_constellation_soft_decoder_cf_0_0, 0), (self.epy_block_0_0, 0))
        self.connect((self.digital_corr_est_cc_0, 0), (self.epy_block_1, 0))
        self.connect((self.digital_correlate_access_code_xx_ts_0, 0), (self.fec_extended_decoder_0, 0))
        self.connect((self.digital_correlate_access_code_xx_ts_0_0, 0), (self.fec_extended_decoder_0_0, 0))
        self.connect((self.digital_costas_loop_cc_0, 0), (self.digital_constellation_soft_decoder_cf_0, 0))
        self.connect((self.digital_costas_loop_cc_0, 0), (self.digital_corr_est_cc_0, 0))
        self.connect((self.digital_costas_loop_cc_0, 0), (self.qtgui_time_sink_x_1_0, 0))
        self.connect((self.digital_crc32_bb_1, 0), (self.blocks_file_sink_0, 0))
        self.connect((self.digital_crc32_bb_1, 0), (self.pdu_tagged_stream_to_pdu_0, 0))
        self.connect((self.digital_crc32_bb_1_0, 0), (self.blocks_file_sink_0_0, 0))
        self.connect((self.digital_crc32_bb_1_0, 0), (self.pdu_tagged_stream_to_pdu_0_0, 0))
        self.connect((self.digital_symbol_sync_xx_0, 0), (self.digital_costas_loop_cc_0, 0))
        self.connect((self.epy_block_0, 0), (self.digital_correlate_access_code_xx_ts_0, 0))
        self.connect((self.epy_block_0_0, 0), (self.digital_correlate_access_code_xx_ts_0_0, 0))
        self.connect((self.epy_block_1, 0), (self.digital_constellation_soft_decoder_cf_0_0, 0))
        self.connect((self.epy_block_1, 0), (self.qtgui_time_sink_x_1_0_0, 0))
        self.connect((self.fec_extended_decoder_0, 0), (self.blocks_tagged_stream_multiply_length_0_1, 0))
        self.connect((self.fec_extended_decoder_0_0, 0), (self.blocks_tagged_stream_multiply_length_0_1_0, 0))
        self.connect((self.fec_extended_encoder_0_0_0, 0), (self.digital_chunks_to_symbols_xx_0, 0))
        self.connect((self.filter_fft_rrc_filter_0, 0), (self.digital_symbol_sync_xx_0, 0))
        self.connect((self.uhd_usrp_source_0, 0), (self.blocks_throttle2_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "RX_host")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_sps(self):
        return self.sps

    def set_sps(self, sps):
        self.sps = sps
        self.digital_symbol_sync_xx_0.set_sps(self.sps)
        self.filter_fft_rrc_filter_0.set_taps(firdes.root_raised_cosine(1, self.samp_rate, (self.samp_rate/self.sps), 0.35, (11*self.sps)))
        self.qtgui_time_sink_x_1_0.set_samp_rate(self.samp_rate/self.sps)
        self.qtgui_time_sink_x_1_0_0.set_samp_rate(self.samp_rate/self.sps)

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.blocks_throttle2_0.set_sample_rate(self.samp_rate)
        self.epy_block_1.sample_rate = self.samp_rate
        self.filter_fft_rrc_filter_0.set_taps(firdes.root_raised_cosine(1, self.samp_rate, (self.samp_rate/self.sps), 0.35, (11*self.sps)))
        self.qtgui_freq_sink_x_0.set_frequency_range(0, self.samp_rate)
        self.qtgui_time_sink_x_0_0.set_samp_rate(self.samp_rate)
        self.qtgui_time_sink_x_1_0.set_samp_rate(self.samp_rate/self.sps)
        self.qtgui_time_sink_x_1_0_0.set_samp_rate(self.samp_rate/self.sps)
        self.uhd_usrp_source_0.set_samp_rate(self.samp_rate)

    def get_preamble_syms(self):
        return self.preamble_syms

    def set_preamble_syms(self, preamble_syms):
        self.preamble_syms = preamble_syms
        self.digital_corr_est_cc_0.set_mark_delay((len(self.preamble_syms)-1))

    def get_preamble_size(self):
        return self.preamble_size

    def set_preamble_size(self, preamble_size):
        self.preamble_size = preamble_size

    def get_postamble_size(self):
        return self.postamble_size

    def set_postamble_size(self, postamble_size):
        self.postamble_size = postamble_size

    def get_payload_size(self):
        return self.payload_size

    def set_payload_size(self, payload_size):
        self.payload_size = payload_size

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

    def get_constel(self):
        return self.constel

    def set_constel(self, constel):
        self.constel = constel
        self.digital_constellation_soft_decoder_cf_0.set_constellation(self.constel)
        self.digital_constellation_soft_decoder_cf_0_0.set_constellation(self.constel)




def main(top_block_cls=RX_host, options=None):

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
