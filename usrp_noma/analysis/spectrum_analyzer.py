"""
FFT Spektrum Analizi

IQ verisi uzerinde guc yogunluk spektrumu (PSD) hesaplama, tepe noktasi bulma
ve matplotlib ile gorsellestime.
"""

import numpy as np
from scipy import signal as scipy_signal
import matplotlib
matplotlib.use("Agg")  # GUI olmayan ortamlar icin
import matplotlib.pyplot as plt

from usrp_noma import config
from usrp_noma.utils import setup_logger, linear_to_dB, freq_to_str

logger = setup_logger("SpectrumAnalyzer")


class SpectrumAnalyzer:
    """FFT tabanli spektrum analiz sinifi."""

    def __init__(self, sample_rate=None, fft_size=None):
        """SpectrumAnalyzer baslatir.

        Args:
            sample_rate: Ornekleme hizi (Hz). None ise config'den alinir.
            fft_size: FFT boyutu. None ise config'den alinir.
        """
        self.sample_rate = sample_rate or config.DEFAULT_SAMPLE_RATE
        self.fft_size = fft_size or config.DEFAULT_FFT_SIZE

    def compute_psd(self, iq_data, method="welch"):
        """Guc Yogunluk Spektrumu (PSD) hesaplar.

        Args:
            iq_data: Kompleks IQ veri dizisi
            method: Hesaplama yontemi ("welch" veya "fft")

        Returns:
            tuple: (frekanslar_Hz, psd_dB) numpy dizileri
        """
        if method == "welch":
            freqs, psd = scipy_signal.welch(
                iq_data,
                fs=self.sample_rate,
                nperseg=self.fft_size,
                noverlap=self.fft_size // 2,
                return_onesided=False,
                window="hann",
            )
            # Welch cift tarafli sonuc: sirala
            freqs = np.fft.fftshift(freqs)
            psd = np.fft.fftshift(psd)
        else:
            # Basit FFT yontemi
            num_segments = max(1, len(iq_data) // self.fft_size)
            psd_accum = np.zeros(self.fft_size)

            window = np.hanning(self.fft_size)
            for i in range(num_segments):
                segment = iq_data[i * self.fft_size : (i + 1) * self.fft_size]
                if len(segment) < self.fft_size:
                    break
                windowed = segment * window
                spectrum = np.fft.fftshift(np.fft.fft(windowed))
                psd_accum += np.abs(spectrum) ** 2

            psd = psd_accum / (num_segments * self.fft_size * self.sample_rate)
            freqs = np.fft.fftshift(
                np.fft.fftfreq(self.fft_size, 1.0 / self.sample_rate)
            )

        psd_dB = linear_to_dB(psd)
        return freqs, psd_dB

    def find_peaks(self, freqs, psd_dB, threshold_dB=-50, min_distance=10):
        """Spektrumdaki tepe noktalarini bulur.

        Args:
            freqs: Frekans dizisi (Hz)
            psd_dB: PSD dizisi (dB)
            threshold_dB: Minimum tepe esigi (dB)
            min_distance: Minimum tepeler arasi mesafe (ornek sayisi)

        Returns:
            list: Her tepe icin (frekans_Hz, guc_dB) tuple'lari
        """
        peak_indices, properties = scipy_signal.find_peaks(
            psd_dB, height=threshold_dB, distance=min_distance
        )

        peaks = []
        for idx in peak_indices:
            peaks.append((freqs[idx], psd_dB[idx]))

        # Guce gore sirala (en guclu once)
        peaks.sort(key=lambda x: x[1], reverse=True)

        logger.info("%d tepe noktasi bulundu (esik: %.1f dB)", len(peaks), threshold_dB)
        return peaks

    def get_band_power(self, iq_data, freq_range=None, center_freq=0):
        """Belirli bir frekans bandindaki toplam gucu hesaplar.

        Args:
            iq_data: Kompleks IQ veri dizisi
            freq_range: (alt_frekans, ust_frekans) tuple'i (Hz, merkeze gore)
            center_freq: Merkez frekans (Hz) - goreli frekans hesabi icin

        Returns:
            float: Bant gucu (dB)
        """
        freqs, psd_dB = self.compute_psd(iq_data)

        if freq_range is not None:
            mask = (freqs >= freq_range[0]) & (freqs <= freq_range[1])
            if np.any(mask):
                band_psd_linear = 10 ** (psd_dB[mask] / 10.0)
                total_power = np.sum(band_psd_linear) * (freqs[1] - freqs[0])
                return linear_to_dB(total_power)

        # Tum bant
        band_psd_linear = 10 ** (psd_dB / 10.0)
        total_power = np.sum(band_psd_linear) * (freqs[1] - freqs[0])
        return linear_to_dB(total_power)

    def plot_spectrum(self, iq_data, center_freq=0, title=None, save_path=None):
        """Spektrumu cizer ve gosterir/kaydeder.

        Args:
            iq_data: Kompleks IQ veri dizisi
            center_freq: Merkez frekans (Hz) - eksen etiketi icin
            title: Grafik basligi
            save_path: Dosyaya kaydetme yolu (None ise ekranda gosterir)
        """
        freqs, psd_dB = self.compute_psd(iq_data)

        # Frekans eksenini merkez frekansa gore kaydir
        display_freqs = (freqs + center_freq) / 1e6  # MHz

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(display_freqs, psd_dB, linewidth=0.8, color="#1f77b4")
        ax.set_xlabel("Frekans (MHz)")
        ax.set_ylabel("Guc Yogunlugu (dB)")
        ax.set_title(title or f"Spektrum Analizi - {freq_to_str(center_freq)}")
        ax.grid(True, alpha=0.3)
        ax.set_xlim(display_freqs[0], display_freqs[-1])

        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=150)
            logger.info("Spektrum grafigi kaydedildi: %s", save_path)
            plt.close(fig)
        else:
            plt.show()

    def plot_spectrum_live(self, capture_obj, center_freq=0, update_interval=0.5):
        """Canli spektrum gosterimi.

        Args:
            capture_obj: SignalCapture nesnesi
            center_freq: Merkez frekans (Hz)
            update_interval: Guncelleme araligi (saniye)
        """
        matplotlib.use("TkAgg")
        plt.ion()
        fig, ax = plt.subplots(figsize=(12, 6))

        line = None
        freqs = np.fft.fftshift(
            np.fft.fftfreq(self.fft_size, 1.0 / self.sample_rate)
        )
        display_freqs = (freqs + center_freq) / 1e6

        ax.set_xlabel("Frekans (MHz)")
        ax.set_ylabel("Guc Yogunlugu (dB)")
        ax.set_title(f"Canli Spektrum - {freq_to_str(center_freq)}")
        ax.grid(True, alpha=0.3)
        ax.set_xlim(display_freqs[0], display_freqs[-1])
        ax.set_ylim(-120, 0)

        def _update(iq_data):
            nonlocal line
            _, psd_dB = self.compute_psd(iq_data)

            if line is None:
                line, = ax.plot(display_freqs, psd_dB, linewidth=0.8)
            else:
                line.set_ydata(psd_dB)
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
