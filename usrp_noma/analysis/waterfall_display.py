"""
Waterfall (Selale) Diyagram

Zaman-frekans gorsellestime: spektrogram/waterfall goruntusu olusturma.
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize

from usrp_noma import config
from usrp_noma.utils import setup_logger, freq_to_str

logger = setup_logger("WaterfallDisplay")


class WaterfallDisplay:
    """Waterfall (selale) diyagram sinifi."""

    def __init__(self, sample_rate=None, fft_size=None, history_size=100):
        """WaterfallDisplay baslatir.

        Args:
            sample_rate: Ornekleme hizi (Hz).
            fft_size: FFT boyutu.
            history_size: Gecmis satir sayisi (zaman ekseni derinligi).
        """
        self.sample_rate = sample_rate or config.DEFAULT_SAMPLE_RATE
        self.fft_size = fft_size or config.DEFAULT_FFT_SIZE
        self.history_size = history_size

        # Waterfall veri matrisi (satirlar = zaman, sutunlar = frekans)
        self.waterfall_data = np.full(
            (history_size, self.fft_size), -120.0, dtype=np.float32
        )
        self._row_index = 0
        self._total_updates = 0

    def update(self, iq_data):
        """Yeni IQ verisinden bir satir ekler.

        Args:
            iq_data: Kompleks IQ veri dizisi (en az fft_size uzunlugunda)
        """
        if len(iq_data) < self.fft_size:
            padded = np.zeros(self.fft_size, dtype=np.complex64)
            padded[:len(iq_data)] = iq_data
            iq_data = padded

        # Pencere uygula ve FFT hesapla
        window = np.hanning(self.fft_size)
        segment = iq_data[:self.fft_size] * window
        spectrum = np.fft.fftshift(np.fft.fft(segment))
        psd = np.abs(spectrum) ** 2 / (self.fft_size * self.sample_rate)
        psd_dB = 10.0 * np.log10(np.maximum(psd, 1e-12))

        # Dairesel tampon seklinde veri ekle
        self.waterfall_data[self._row_index % self.history_size, :] = psd_dB
        self._row_index += 1
        self._total_updates += 1

    def get_ordered_data(self):
        """Waterfall verisini zaman sirasina gore dondurur (en eski ustte).

        Returns:
            numpy.ndarray: sirali waterfall matrisi
        """
        if self._total_updates <= self.history_size:
            return self.waterfall_data[:self._total_updates]
        idx = self._row_index % self.history_size
        return np.roll(self.waterfall_data, -idx, axis=0)

    def plot(self, center_freq=0, title=None, save_path=None,
             vmin=-120, vmax=-20, cmap="viridis"):
        """Waterfall diyagramini cizer.

        Args:
            center_freq: Merkez frekans (Hz)
            title: Grafik basligi
            save_path: Kayit yolu (None ise ekranda gosterir)
            vmin: Minimum renk skalasi degeri (dB)
            vmax: Maksimum renk skalasi degeri (dB)
            cmap: Renk haritasi
        """
        data = self.get_ordered_data()
        if len(data) == 0:
            logger.warning("Goruntulecek veri yok.")
            return

        freqs = np.fft.fftshift(
            np.fft.fftfreq(self.fft_size, 1.0 / self.sample_rate)
        )
        display_freqs = (freqs + center_freq) / 1e6  # MHz

        time_axis = np.arange(len(data)) * (self.fft_size / self.sample_rate)

        fig, ax = plt.subplots(figsize=(12, 8))
        im = ax.imshow(
            data,
            aspect="auto",
            origin="lower",
            extent=[
                display_freqs[0], display_freqs[-1],
                time_axis[0], time_axis[-1],
            ],
            cmap=cmap,
            norm=Normalize(vmin=vmin, vmax=vmax),
        )

        ax.set_xlabel("Frekans (MHz)")
        ax.set_ylabel("Zaman (s)")
        ax.set_title(title or f"Waterfall - {freq_to_str(center_freq)}")

        fig.colorbar(im, ax=ax, label="Guc (dB)")
        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=150)
            logger.info("Waterfall grafigi kaydedildi: %s", save_path)
            plt.close(fig)
        else:
            plt.show()

    def plot_live(self, capture_obj, center_freq=0, update_interval=0.1):
        """Canli waterfall gosterimi.

        Args:
            capture_obj: SignalCapture nesnesi
            center_freq: Merkez frekans (Hz)
            update_interval: Guncelleme araligi (saniye)
        """
        matplotlib.use("TkAgg")
        plt.ion()

        freqs = np.fft.fftshift(
            np.fft.fftfreq(self.fft_size, 1.0 / self.sample_rate)
        )
        display_freqs = (freqs + center_freq) / 1e6

        fig, ax = plt.subplots(figsize=(12, 8))
        data = self.get_ordered_data()
        if len(data) == 0:
            data = self.waterfall_data

        im = ax.imshow(
            data,
            aspect="auto",
            origin="lower",
            extent=[
                display_freqs[0], display_freqs[-1],
                0, self.history_size * (self.fft_size / self.sample_rate),
            ],
            cmap="viridis",
            vmin=-120,
            vmax=-20,
        )
        ax.set_xlabel("Frekans (MHz)")
        ax.set_ylabel("Zaman (s)")
        ax.set_title(f"Canli Waterfall - {freq_to_str(center_freq)}")
        fig.colorbar(im, ax=ax, label="Guc (dB)")

        def _update(iq_data):
            self.update(iq_data)
            im.set_data(self.get_ordered_data())
            fig.canvas.draw_idle()
            fig.canvas.flush_events()

        capture_obj.continuous_capture(
            callback=_update,
            chunk_duration=update_interval,
        )

        try:
            plt.show(block=True)
        except KeyboardInterrupt:
            pass
        finally:
            capture_obj.stop()
            plt.close(fig)

    def save_image(self, filename, center_freq=0, **kwargs):
        """Waterfall goruntusunu PNG olarak kaydeder.

        Args:
            filename: Cikti dosya yolu
            center_freq: Merkez frekans (Hz)
            **kwargs: plot() fonksiyonuna iletilen ek parametreler
        """
        self.plot(center_freq=center_freq, save_path=filename, **kwargs)

    def reset(self):
        """Waterfall verisini sifirlar."""
        self.waterfall_data.fill(-120.0)
        self._row_index = 0
        self._total_updates = 0
