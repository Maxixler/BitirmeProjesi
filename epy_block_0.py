"""
Embedded Python Block: TX Controller
Stop-and-Wait ARQ protokolu ile dosyadan paket gonderimi
"""

import numpy as np
from gnuradio import gr
import pmt
import threading


class blk(gr.basic_block):
    """Stop-and-Wait ARQ TX Controller"""

    def __init__(self, filename="bpsk_transmit.txt", payload_size=77,
                 timeout_ms=2000.0, max_retries=5):
        gr.basic_block.__init__(
            self,
            name='TX Controller',
            in_sig=[],
            out_sig=[]
        )

        # Message portlari
        self.message_port_register_out(pmt.intern("tx_pdu"))
        self.message_port_register_in(pmt.intern("feedback"))
        self.set_msg_handler(pmt.intern("feedback"), self.handle_feedback)

        # Parametreler
        self.filename = filename
        self.payload_size = int(payload_size)
        self.timeout_sec = timeout_ms / 1000.0
        self.max_retries = int(max_retries)

        # Durum
        self.packets = []
        self.current_idx = 0
        self.retry_count = 0
        self.timer = None
        self.lock = threading.Lock()
        self.done = False

    def start(self):
        # Dosyayi oku ve paketlere bol
        with open(self.filename, "rb") as f:
            raw = f.read()
        self.packets = []
        for i in range(0, len(raw), self.payload_size):
            chunk = raw[i:i + self.payload_size]
            if len(chunk) == self.payload_size:
                self.packets.append(chunk)

        print(f"[TX] {len(self.packets)} paket hazir "
              f"({self.payload_size} byte/paket)")

        self.current_idx = 0
        self.retry_count = 0
        self.done = False
        self.send_current_packet()
        return True

    def send_current_packet(self):
        if self.current_idx >= len(self.packets):
            self.done = True
            print("[TX] === Tum paketler basariyla gonderildi ===")
            return

        data = self.packets[self.current_idx]
        pdu = pmt.cons(
            pmt.PMT_NIL,
            pmt.init_u8vector(len(data), list(data))
        )
        self.message_port_pub(pmt.intern("tx_pdu"), pdu)
        self.start_timer()

        if self.retry_count == 0:
            print(f"[TX] Paket {self.current_idx + 1}/"
                  f"{len(self.packets)} gonderildi")
        else:
            print(f"[TX] Paket {self.current_idx + 1}/"
                  f"{len(self.packets)} retry #{self.retry_count}")

    def start_timer(self):
        if self.timer is not None:
            self.timer.cancel()
        self.timer = threading.Timer(self.timeout_sec, self.on_timeout)
        self.timer.daemon = True
        self.timer.start()

    def on_timeout(self):
        with self.lock:
            if self.done:
                return
            self.retry_count += 1
            if self.retry_count > self.max_retries:
                print(f"[TX] Paket {self.current_idx + 1} "
                      f"max retry ({self.max_retries}) asildi, atlaniyor!")
                self.current_idx += 1
                self.retry_count = 0
            else:
                print(f"[TX] Timeout! Paket {self.current_idx + 1}")
            self.send_current_packet()

    def handle_feedback(self, msg):
        with self.lock:
            if self.done:
                return
            if self.timer is not None:
                self.timer.cancel()
            print(f"[TX] ACK alindi! Paket {self.current_idx + 1}/"
                  f"{len(self.packets)}")
            self.current_idx += 1
            self.retry_count = 0
            self.send_current_packet()

    def stop(self):
        if self.timer is not None:
            self.timer.cancel()
        print(f"[TX] Sonuc: {self.current_idx}/{len(self.packets)} "
              f"paket tamamlandi")
        return True
