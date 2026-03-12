"""
Genis Bant Frekans Tarama

Antenin destekledigi frekans bantlarinda (698-960 MHz ve 1710-2700 MHz)
adim adim tarama yaparak aktif sinyalleri tespit eder.
"""

import csv
import time
from datetime import datetime

import numpy as np

from usrp_noma import config
from usrp_noma.utils import setup_logger, freq_to_str, linear_to_dB, timestamp_filename
from usrp_noma.analysis.spectrum_analyzer import SpectrumAnalyzer

logger = setup_logger("FrequencyScanner")


class FrequencyScanner:
    """Genis bant frekans tarama sinifi."""

    def __init__(self, controller):
        """FrequencyScanner baslatir.

        Args:
            controller: USRPController nesnesi (bagli olmali)
        """
        self.controller = controller
        self.scan_results = []
        self.analyzer = SpectrumAnalyzer()

    def scan_band(self, start_freq, stop_freq, step=None, dwell_time=None,
                  gain=None):
        """Belirli bir frekans bandini adim adim tarar.

        Args:
            start_freq: Baslangic frekansi (Hz)
            stop_freq: Bitis frekansi (Hz)
            step: Frekans adimi (Hz). None ise ornekleme hizinin yarisi.
            dwell_time: Her frekansta bekleme suresi (s). None ise config'den.
            gain: RX kazanci (dB). None ise mevcut deger.

        Returns:
            list: Her adim icin (frekans, ortalama_guc_dB) tuple listesi
        """
        dwell_time = dwell_time or config.SCAN_DWELL_TIME
        sample_rate = self.controller.usrp.get_rx_rate()

        if step is None:
            step = sample_rate / 2  # Nyquist'e gore

        if gain is not None:
            self.controller.set_rx_gain(gain)

        freqs = np.arange(start_freq, stop_freq, step)
        results = []

        logger.info(
            "Bant taramasi baslatiliyor: %s -> %s, adim=%s, %d nokta",
            freq_to_str(start_freq), freq_to_str(stop_freq),
            freq_to_str(step), len(freqs),
        )

        for i, freq in enumerate(freqs):
            self.controller.set_rx_freq(freq)
            time.sleep(0.01)  # Tuner yerlesme suresi

            num_samples = int(dwell_time * sample_rate)
            samples = self.controller.receive_samples(num_samples)

            if len(samples) > 0:
                avg_power = 10.0 * np.log10(
                    np.maximum(np.mean(np.abs(samples) ** 2), 1e-12)
                )
            else:
                avg_power = -120.0

            results.append((freq, avg_power))

            if (i + 1) % 50 == 0 or (i + 1) == len(freqs):
                logger.info(
                    "Tarama ilerleme: %d/%d (%.1f%%) - %s: %.1f dB",
                    i + 1, len(freqs), 100 * (i + 1) / len(freqs),
                    freq_to_str(freq), avg_power,
                )

        self.scan_results = results
        logger.info("Bant taramasi tamamlandi: %d nokta tarandi.", len(results))
        return results

    def scan_low_band(self, step=None, dwell_time=None):
        """Alt banti (698-960 MHz) tarar.

        Args:
            step: Frekans adimi (Hz). None ise config'den.
            dwell_time: Bekleme suresi (s).

        Returns:
            list: Tarama sonuclari
        """
        step = step or config.SCAN_STEP_LOW
        logger.info("Alt bant taramasi: %s", config.BAND_LOW["name"])
        return self.scan_band(
            config.BAND_LOW["start_freq"],
            config.BAND_LOW["stop_freq"],
            step=step,
            dwell_time=dwell_time,
        )

    def scan_high_band(self, step=None, dwell_time=None):
        """Ust banti (1710-2700 MHz) tarar.

        Args:
            step: Frekans adimi (Hz). None ise config'den.
            dwell_time: Bekleme suresi (s).

        Returns:
            list: Tarama sonuclari
        """
        step = step or config.SCAN_STEP_HIGH
        logger.info("Ust bant taramasi: %s", config.BAND_HIGH["name"])
        return self.scan_band(
            config.BAND_HIGH["start_freq"],
            config.BAND_HIGH["stop_freq"],
            step=step,
            dwell_time=dwell_time,
        )

    def scan_full(self, dwell_time=None):
        """Her iki bandi da tarar.

        Args:
            dwell_time: Her frekansta bekleme suresi (s).

        Returns:
            list: Birlestirilmis tarama sonuclari
        """
        results_low = self.scan_low_band(dwell_time=dwell_time)
        results_high = self.scan_high_band(dwell_time=dwell_time)

        self.scan_results = results_low + results_high
        logger.info(
            "Tam tarama tamamlandi: toplam %d nokta", len(self.scan_results)
        )
        return self.scan_results

    def find_active_signals(self, threshold_dB=None, results=None):
        """Esik uzerindeki aktif sinyalleri bulur.

        Args:
            threshold_dB: Sinyal tespit esigi (dB). None ise config'den.
            results: Tarama sonuclari. None ise son tarama sonuclari.

        Returns:
            list: (frekans, guc_dB) aktif sinyal listesi
        """
        threshold_dB = threshold_dB or config.SCAN_THRESHOLD_DB
        results = results or self.scan_results

        if not results:
            logger.warning("Tarama sonucu yok. Once scan_*() fonksiyonunu calistirin.")
            return []

        active = [(f, p) for f, p in results if p > threshold_dB]

        # Birbirine cok yakin sinyalleri birlestir (en gucluyu sec)
        merged = []
        min_spacing = self.controller.usrp.get_rx_rate() / 4
        for freq, power in sorted(active, key=lambda x: x[1], reverse=True):
            too_close = False
            for mf, _ in merged:
                if abs(freq - mf) < min_spacing:
                    too_close = True
                    break
            if not too_close:
                merged.append((freq, power))

        logger.info(
            "%d aktif sinyal bulundu (esik: %.1f dB)", len(merged), threshold_dB
        )
        for freq, power in merged:
            logger.info("  %s: %.1f dB", freq_to_str(freq), power)

        return merged

    def plot_scan_results(self, results=None, save_path=None):
        """Tarama sonuclarini gorsellestirir.

        Args:
            results: Tarama sonuclari. None ise son tarama sonuclari.
            save_path: Kayit yolu. None ise ekranda gosterir.
        """
        import matplotlib
        if save_path:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        results = results or self.scan_results
        if not results:
            logger.warning("Goruntulecek tarama sonucu yok.")
            return

        freqs = [f / 1e6 for f, _ in results]
        powers = [p for _, p in results]

        fig, ax = plt.subplots(figsize=(14, 6))
        ax.plot(freqs, powers, linewidth=0.8, color="#1f77b4")

        # Esik cizgisi
        ax.axhline(
            y=config.SCAN_THRESHOLD_DB, color="red", linestyle="--",
            alpha=0.5, label=f"Esik ({config.SCAN_THRESHOLD_DB} dB)"
        )

        # Bant sinirlarini isaretle
        for band in config.FREQUENCY_BANDS:
            ax.axvspan(
                band["start_freq"] / 1e6, band["stop_freq"] / 1e6,
                alpha=0.05, color="green",
            )

        # Bilinen frekanslari isaretle
        for name, info in config.KNOWN_FREQUENCIES.items():
            ax.axvline(
                x=info["freq"] / 1e6, color="gray", linestyle=":",
                alpha=0.3, linewidth=0.5,
            )

        ax.set_xlabel("Frekans (MHz)")
        ax.set_ylabel("Guc (dB)")
        ax.set_title("Frekans Tarama Sonuclari")
        ax.grid(True, alpha=0.3)
        ax.legend()

        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=150)
            logger.info("Tarama grafigi kaydedildi: %s", save_path)
            plt.close(fig)
        else:
            plt.show()

    def export_results(self, filename=None, results=None):
        """Tarama sonuclarini CSV dosyasina aktarir.

        Args:
            filename: Cikti dosya yolu. None ise otomatik isim.
            results: Tarama sonuclari. None ise son tarama sonuclari.

        Returns:
            str: Kaydedilen dosya yolu
        """
        results = results or self.scan_results
        if not results:
            logger.warning("Kaydedilecek tarama sonucu yok.")
            return None

        if filename is None:
            filename = timestamp_filename(prefix="scan", ext="csv")

        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Frekans (Hz)", "Frekans (MHz)", "Guc (dB)",
                             "Zaman"])
            ts = datetime.now().isoformat()
            for freq, power in results:
                writer.writerow([freq, freq / 1e6, f"{power:.2f}", ts])

        logger.info("Tarama sonuclari kaydedildi: %s (%d satir)", filename, len(results))
        return filename
