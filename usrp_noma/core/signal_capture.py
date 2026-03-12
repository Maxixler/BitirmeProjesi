"""
IQ Veri Yakalama

USRP E310'dan IQ veri yakalama, dosyaya kaydetme ve surekli yakalama islemleri.
"""

import threading
import time

import numpy as np

from usrp_noma import config
from usrp_noma.utils import setup_logger, save_iq_data, timestamp_filename, freq_to_str

logger = setup_logger("SignalCapture")


class SignalCapture:
    """IQ sinyal yakalama sinifi."""

    def __init__(self, controller):
        """SignalCapture baslatir.

        Args:
            controller: USRPController nesnesi (bagli olmali)
        """
        self.controller = controller
        self._running = False
        self._thread = None

    def capture(self, duration_sec=None, freq=None, gain=None, rate=None):
        """Belirli sureli IQ veri yakalar.

        Args:
            duration_sec: Yakalama suresi (saniye). None ise config'den alinir.
            freq: Merkez frekans (Hz). None ise mevcut deger kullanilir.
            gain: Kazanc (dB). None ise mevcut deger kullanilir.
            rate: Ornekleme hizi (Hz). None ise mevcut deger kullanilir.

        Returns:
            numpy.ndarray: Yakalanan IQ veri dizisi (complex64)
        """
        if freq is not None:
            self.controller.set_rx_freq(freq)
        if gain is not None:
            self.controller.set_rx_gain(gain)
        if rate is not None:
            self.controller.set_rx_rate(rate)

        duration_sec = duration_sec or config.DEFAULT_CAPTURE_DURATION
        actual_rate = self.controller.usrp.get_rx_rate()
        num_samples = int(duration_sec * actual_rate)

        logger.info(
            "Yakalama baslatiliyor: freq=%s, sure=%.2f s, ornek=%d",
            freq_to_str(self.controller.usrp.get_rx_freq()),
            duration_sec,
            num_samples,
        )

        start_time = time.time()
        data = self.controller.receive_samples(num_samples)
        elapsed = time.time() - start_time

        logger.info(
            "Yakalama tamamlandi: %d ornek, %.2f saniye", len(data), elapsed
        )
        return data

    def capture_to_file(self, filename=None, duration_sec=None, freq=None,
                        gain=None, rate=None):
        """IQ verisini yakalayip dosyaya kaydeder.

        Args:
            filename: Cikti dosya yolu. None ise otomatik isim uretilir.
            duration_sec: Yakalama suresi (saniye).
            freq: Merkez frekans (Hz).
            gain: Kazanc (dB).
            rate: Ornekleme hizi (Hz).

        Returns:
            tuple: (dosya_yolu, yakalanan_veri)
        """
        if filename is None:
            filename = timestamp_filename(prefix="capture", ext="npy")

        data = self.capture(duration_sec, freq, gain, rate)

        center_freq = self.controller.usrp.get_rx_freq()
        sample_rate = self.controller.usrp.get_rx_rate()
        save_iq_data(data, filename, sample_rate=sample_rate, center_freq=center_freq)

        logger.info("Veri kaydedildi: %s", filename)
        return filename, data

    def continuous_capture(self, callback, chunk_duration=0.1, freq=None,
                           gain=None, rate=None):
        """Surekli IQ veri yakalar ve her parcayi callback'e iletir.

        Ayri bir thread'de calisir. Durdurmak icin stop() cagirilmali.

        Args:
            callback: Her chunk icin cagrilacak fonksiyon. Imza: callback(iq_data)
            chunk_duration: Her parcanin suresi (saniye).
            freq: Merkez frekans (Hz).
            gain: Kazanc (dB).
            rate: Ornekleme hizi (Hz).
        """
        if freq is not None:
            self.controller.set_rx_freq(freq)
        if gain is not None:
            self.controller.set_rx_gain(gain)
        if rate is not None:
            self.controller.set_rx_rate(rate)

        self._running = True

        def _capture_loop():
            actual_rate = self.controller.usrp.get_rx_rate()
            chunk_samples = int(chunk_duration * actual_rate)

            logger.info(
                "Surekli yakalama baslatildi: freq=%s, parca=%d ornek",
                freq_to_str(self.controller.usrp.get_rx_freq()),
                chunk_samples,
            )

            while self._running:
                try:
                    data = self.controller.receive_samples(chunk_samples)
                    if len(data) > 0:
                        callback(data)
                except Exception as e:
                    logger.error("Yakalama hatasi: %s", e)
                    if not self._running:
                        break
                    time.sleep(0.1)

            logger.info("Surekli yakalama durduruldu.")

        self._thread = threading.Thread(target=_capture_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Surekli yakalamayi durdurur."""
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=5.0)
            self._thread = None
        logger.info("Yakalama durduruldu.")

    @property
    def is_running(self):
        """Surekli yakalamanin calisip calismadigini dondurur."""
        return self._running
