"""
IQ Sinyal Veri Analizi Modulu

USRP E310 ile yakalanan veya sentetik uretilen IQ verilerinin
istatistiksel analizi, ozellik cikarimi ve gorsellestirilmesi.
"""

import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import signal as sp_signal

from usrp_noma import config
from usrp_noma.utils import setup_logger, linear_to_dB, freq_to_str

logger = setup_logger("DataAnalysis")


class IQDataAnalyzer:
    """IQ verisi uzerinde kapsamli veri analizi yapar.

    Ozellik cikarimi, istatistiksel analiz ve gorsellestime islemleri.
    """

    def __init__(self, sample_rate=None):
        self.sample_rate = sample_rate or config.DEFAULT_SAMPLE_RATE
        self.logger = logger

    def compute_statistics(self, iq_data):
        """IQ verisinin temel istatistiklerini hesaplar.

        Args:
            iq_data: Kompleks IQ veri dizisi

        Returns:
            dict: Istatistiksel ozellikler
        """
        amplitude = np.abs(iq_data)
        phase = np.angle(iq_data)
        power = amplitude ** 2

        stats = {
            "num_samples": len(iq_data),
            "duration_sec": len(iq_data) / self.sample_rate,
            # Genlik istatistikleri
            "amplitude_mean": float(np.mean(amplitude)),
            "amplitude_std": float(np.std(amplitude)),
            "amplitude_max": float(np.max(amplitude)),
            "amplitude_min": float(np.min(amplitude)),
            "amplitude_median": float(np.median(amplitude)),
            # Guc istatistikleri
            "power_mean_dB": float(linear_to_dB(np.mean(power))),
            "power_peak_dB": float(linear_to_dB(np.max(power))),
            "power_var_dB": float(linear_to_dB(np.var(power))) if np.var(power) > 0 else -120.0,
            # I/Q istatistikleri
            "i_mean": float(np.mean(iq_data.real)),
            "q_mean": float(np.mean(iq_data.imag)),
            "i_std": float(np.std(iq_data.real)),
            "q_std": float(np.std(iq_data.imag)),
            "iq_correlation": float(np.corrcoef(iq_data.real, iq_data.imag)[0, 1]),
            # Faz istatistikleri
            "phase_mean_rad": float(np.mean(phase)),
            "phase_std_rad": float(np.std(phase)),
            # Crest factor (tepe-ortalama orani)
            "crest_factor_dB": float(20 * np.log10(np.max(amplitude) / np.sqrt(np.mean(power)))) if np.mean(power) > 0 else 0.0,
            # Kurtosis (dagılım sivriligi)
            "kurtosis": float(np.mean((amplitude - np.mean(amplitude)) ** 4) / (np.std(amplitude) ** 4)) if np.std(amplitude) > 0 else 0.0,
        }
        return stats

    def extract_features(self, iq_data, n_fft=1024):
        """Makine ogrenimi icin ozellik vektoru cikarir.

        Args:
            iq_data: Kompleks IQ veri dizisi
            n_fft: FFT boyutu

        Returns:
            ndarray: Ozellik vektoru
        """
        amplitude = np.abs(iq_data)
        phase = np.angle(iq_data)
        power = amplitude ** 2

        # Zaman alanı ozellikleri (10)
        time_features = np.array([
            np.mean(amplitude),
            np.std(amplitude),
            np.max(amplitude),
            np.median(amplitude),
            np.mean(power),
            np.std(power),
            np.mean(iq_data.real),
            np.std(iq_data.real),
            np.mean(iq_data.imag),
            np.std(iq_data.imag),
        ])

        # Frekans alani ozellikleri (10)
        spectrum = np.abs(np.fft.fftshift(np.fft.fft(iq_data, n=n_fft))) ** 2
        spectrum_norm = spectrum / (np.sum(spectrum) + 1e-12)

        # Spektral moment ve ozellikler
        freq_bins = np.arange(n_fft)
        spectral_centroid = np.sum(freq_bins * spectrum_norm)
        spectral_spread = np.sqrt(np.sum(((freq_bins - spectral_centroid) ** 2) * spectrum_norm))
        spectral_flatness = np.exp(np.mean(np.log(spectrum + 1e-12))) / (np.mean(spectrum) + 1e-12)
        spectral_peak = np.max(spectrum)
        spectral_entropy = -np.sum(spectrum_norm * np.log2(spectrum_norm + 1e-12))

        # Bant genisligi tahmini (%90 enerji)
        cumulative = np.cumsum(np.sort(spectrum_norm)[::-1])
        bw_90 = np.searchsorted(cumulative, 0.9) / n_fft

        freq_features = np.array([
            spectral_centroid / n_fft,
            spectral_spread / n_fft,
            spectral_flatness,
            linear_to_dB(spectral_peak),
            spectral_entropy,
            bw_90,
            np.mean(spectrum_norm[:n_fft // 4]),   # dusuk frekans enerjisi
            np.mean(spectrum_norm[n_fft // 4:n_fft // 2]),  # orta-alt
            np.mean(spectrum_norm[n_fft // 2:3 * n_fft // 4]),  # orta-ust
            np.mean(spectrum_norm[3 * n_fft // 4:]),  # yuksek frekans enerjisi
        ])

        # Istatistiksel ozellikler (5)
        kurtosis = np.mean((amplitude - np.mean(amplitude)) ** 4) / (np.std(amplitude) ** 4 + 1e-12)
        skewness = np.mean((amplitude - np.mean(amplitude)) ** 3) / (np.std(amplitude) ** 3 + 1e-12)
        crest = np.max(amplitude) / (np.sqrt(np.mean(power)) + 1e-12)
        iq_corr = np.corrcoef(iq_data.real, iq_data.imag)[0, 1]
        phase_std = np.std(phase)

        stat_features = np.array([kurtosis, skewness, crest, iq_corr, phase_std])

        return np.concatenate([time_features, freq_features, stat_features])

    def extract_features_windowed(self, iq_data, window_size=1024, hop_size=512, n_fft=1024):
        """IQ verisini pencereleyerek her pencereden ozellik cikarir.

        Args:
            iq_data: Kompleks IQ veri dizisi
            window_size: Pencere boyutu (ornek)
            hop_size: Pencere kayma miktari
            n_fft: FFT boyutu

        Returns:
            ndarray: (num_windows, num_features) matris
        """
        features_list = []
        num_windows = (len(iq_data) - window_size) // hop_size + 1

        for i in range(num_windows):
            start = i * hop_size
            end = start + window_size
            window = iq_data[start:end]
            features = self.extract_features(window, n_fft=n_fft)
            features_list.append(features)

        return np.array(features_list)

    def compute_spectrogram(self, iq_data, nperseg=256, noverlap=None):
        """IQ verisinin spektrogramini hesaplar.

        Args:
            iq_data: Kompleks IQ veri dizisi
            nperseg: Segment uzunlugu
            noverlap: Segment ortusme miktari

        Returns:
            tuple: (freqs, times, Sxx_dB)
        """
        if noverlap is None:
            noverlap = nperseg // 2

        freqs, times, Sxx = sp_signal.spectrogram(
            iq_data, fs=self.sample_rate,
            nperseg=nperseg, noverlap=noverlap,
            return_onesided=False,
        )

        # Shift: negatif-pozitif frekans sirala
        freqs = np.fft.fftshift(freqs)
        Sxx = np.fft.fftshift(Sxx, axes=0)

        Sxx_dB = 10 * np.log10(np.maximum(Sxx, 1e-12))
        return freqs, times, Sxx_dB

    def plot_comprehensive_analysis(self, iq_data, center_freq=None, title="IQ Veri Analizi", save_dir=None):
        """IQ verisinin kapsamli analiz grafiklerini olusturur.

        6 panelli analiz: I/Q zaman, genlik, faz, PSD, spektrogram, I-Q scatter

        Args:
            iq_data: Kompleks IQ veri dizisi
            center_freq: Merkez frekans (Hz)
            title: Grafik basligi
            save_dir: Kayit dizini
        """
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)

        t = np.arange(len(iq_data)) / self.sample_rate * 1000  # ms

        fig, axes = plt.subplots(3, 2, figsize=(16, 14))
        fig.suptitle(title, fontsize=14, fontweight="bold")

        # 1. I/Q zaman sinyali
        ax = axes[0, 0]
        ax.plot(t[:min(2000, len(t))], iq_data.real[:min(2000, len(iq_data))], "b-", alpha=0.7, label="I", linewidth=0.5)
        ax.plot(t[:min(2000, len(t))], iq_data.imag[:min(2000, len(iq_data))], "r-", alpha=0.7, label="Q", linewidth=0.5)
        ax.set_xlabel("Zaman (ms)")
        ax.set_ylabel("Genlik")
        ax.set_title("I/Q Zaman Sinyali")
        ax.legend(loc="upper right")
        ax.grid(True, alpha=0.3)

        # 2. Genlik zarfi
        ax = axes[0, 1]
        amplitude = np.abs(iq_data)
        ax.plot(t[:min(2000, len(t))], amplitude[:min(2000, len(amplitude))], "g-", linewidth=0.5)
        ax.axhline(y=np.mean(amplitude), color="r", linestyle="--", alpha=0.7, label=f"Ort: {np.mean(amplitude):.4f}")
        ax.set_xlabel("Zaman (ms)")
        ax.set_ylabel("Genlik")
        ax.set_title("Genlik Zarfi")
        ax.legend(loc="upper right")
        ax.grid(True, alpha=0.3)

        # 3. Faz grafigi
        ax = axes[1, 0]
        phase = np.angle(iq_data)
        ax.plot(t[:min(2000, len(t))], np.degrees(phase[:min(2000, len(phase))]), "m-", linewidth=0.5)
        ax.set_xlabel("Zaman (ms)")
        ax.set_ylabel("Faz (derece)")
        ax.set_title("Ani Faz")
        ax.grid(True, alpha=0.3)

        # 4. Guc Yogunluk Spektrumu (PSD)
        ax = axes[1, 1]
        freqs, psd = sp_signal.welch(iq_data, fs=self.sample_rate, nperseg=1024, return_onesided=False)
        freqs = np.fft.fftshift(freqs)
        psd = np.fft.fftshift(psd)
        psd_dB = 10 * np.log10(np.maximum(psd, 1e-12))
        if center_freq:
            freqs_plot = (freqs + center_freq) / 1e6
            ax.set_xlabel("Frekans (MHz)")
        else:
            freqs_plot = freqs / 1e3
            ax.set_xlabel("Frekans (kHz)")
        ax.plot(freqs_plot, psd_dB, "b-", linewidth=0.8)
        ax.set_ylabel("PSD (dB/Hz)")
        ax.set_title("Guc Yogunluk Spektrumu (Welch)")
        ax.grid(True, alpha=0.3)

        # 5. Spektrogram
        ax = axes[2, 0]
        f_spec, t_spec, Sxx_dB = self.compute_spectrogram(iq_data)
        if center_freq:
            f_spec_plot = (f_spec + center_freq) / 1e6
            ax.set_ylabel("Frekans (MHz)")
        else:
            f_spec_plot = f_spec / 1e3
            ax.set_ylabel("Frekans (kHz)")
        im = ax.pcolormesh(t_spec * 1000, f_spec_plot, Sxx_dB, shading="gouraud", cmap="viridis")
        ax.set_xlabel("Zaman (ms)")
        ax.set_title("Spektrogram")
        plt.colorbar(im, ax=ax, label="dB")

        # 6. I-Q Scatter (konstelasyon)
        ax = axes[2, 1]
        max_points = min(5000, len(iq_data))
        indices = np.random.choice(len(iq_data), max_points, replace=False)
        ax.scatter(iq_data.real[indices], iq_data.imag[indices], s=1, alpha=0.3, c="blue")
        ax.set_xlabel("In-Phase (I)")
        ax.set_ylabel("Quadrature (Q)")
        ax.set_title("I-Q Scatter Diyagrami")
        ax.set_aspect("equal")
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_dir:
            path = os.path.join(save_dir, "iq_analysis.png")
            fig.savefig(path, dpi=config.PLOT_DPI, bbox_inches="tight")
            self.logger.info(f"Analiz grafigi kaydedildi: {path}")
        plt.close(fig)

    def plot_feature_distribution(self, features, labels, class_names=None, save_dir=None):
        """Ozellik dagilimlarini sinif bazinda gorsellestirir.

        Args:
            features: (N, n_features) ozellik matrisi
            labels: (N,) sinif etiketleri
            class_names: Sinif isimleri listesi
            save_dir: Kayit dizini
        """
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)

        unique_labels = np.unique(labels)
        n_classes = len(unique_labels)
        if class_names is None:
            class_names = [f"Sinif {i}" for i in unique_labels]

        feature_names = [
            "Genlik Ort", "Genlik Std", "Genlik Max", "Genlik Medyan",
            "Guc Ort", "Guc Std", "I Ort", "I Std", "Q Ort", "Q Std",
            "Spek. Centroid", "Spek. Spread", "Spek. Flatness", "Spek. Peak",
            "Spek. Entropy", "BW %90", "Dusuk F", "Orta-Alt F", "Orta-Ust F", "Yuksek F",
            "Kurtosis", "Skewness", "Crest", "IQ Corr", "Faz Std",
        ]

        # En ayirt edici 8 ozellik (en yuksek varyans orani)
        n_show = min(8, features.shape[1])
        variance_ratios = []
        for j in range(features.shape[1]):
            between_var = 0
            for c in unique_labels:
                mask = labels == c
                between_var += np.sum(mask) * (np.mean(features[mask, j]) - np.mean(features[:, j])) ** 2
            total_var = np.var(features[:, j]) * len(labels) + 1e-12
            variance_ratios.append(between_var / total_var)
        top_indices = np.argsort(variance_ratios)[-n_show:][::-1]

        fig, axes = plt.subplots(2, 4, figsize=(18, 10))
        fig.suptitle("En Ayirt Edici Ozellik Dagilimlari", fontsize=14, fontweight="bold")

        for idx, (ax, feat_idx) in enumerate(zip(axes.flat, top_indices)):
            for c in unique_labels:
                mask = labels == c
                name = class_names[c] if c < len(class_names) else f"Sinif {c}"
                ax.hist(features[mask, feat_idx], bins=30, alpha=0.5, label=name, density=True)
            fname = feature_names[feat_idx] if feat_idx < len(feature_names) else f"Ozellik {feat_idx}"
            ax.set_title(fname, fontsize=10)
            ax.legend(fontsize=7)
            ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_dir:
            path = os.path.join(save_dir, "feature_distributions.png")
            fig.savefig(path, dpi=config.PLOT_DPI, bbox_inches="tight")
            self.logger.info(f"Ozellik dagilim grafigi kaydedildi: {path}")
        plt.close(fig)

    def plot_confusion_matrix(self, y_true, y_pred, class_names, title="Karisiklik Matrisi", save_path=None):
        """Karisiklik matrisini gorsellestirir.

        Args:
            y_true: Gercek etiketler
            y_pred: Tahmin edilen etiketler
            class_names: Sinif isimleri
            title: Grafik basligi
            save_path: Kayit yolu
        """
        from sklearn.metrics import confusion_matrix

        cm = confusion_matrix(y_true, y_pred)
        cm_norm = cm.astype(float) / (cm.sum(axis=1, keepdims=True) + 1e-12)

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        fig.suptitle(title, fontsize=14, fontweight="bold")

        # Mutlak degerli
        im1 = ax1.imshow(cm, interpolation="nearest", cmap="Blues")
        ax1.set_title("Mutlak Degerler")
        for i in range(len(class_names)):
            for j in range(len(class_names)):
                ax1.text(j, i, str(cm[i, j]), ha="center", va="center",
                         color="white" if cm[i, j] > cm.max() / 2 else "black")
        ax1.set_xticks(range(len(class_names)))
        ax1.set_yticks(range(len(class_names)))
        ax1.set_xticklabels(class_names, rotation=45, ha="right")
        ax1.set_yticklabels(class_names)
        ax1.set_xlabel("Tahmin")
        ax1.set_ylabel("Gercek")
        plt.colorbar(im1, ax=ax1)

        # Normalize
        im2 = ax2.imshow(cm_norm, interpolation="nearest", cmap="Blues", vmin=0, vmax=1)
        ax2.set_title("Normalize (%)")
        for i in range(len(class_names)):
            for j in range(len(class_names)):
                ax2.text(j, i, f"{cm_norm[i, j]:.2f}", ha="center", va="center",
                         color="white" if cm_norm[i, j] > 0.5 else "black")
        ax2.set_xticks(range(len(class_names)))
        ax2.set_yticks(range(len(class_names)))
        ax2.set_xticklabels(class_names, rotation=45, ha="right")
        ax2.set_yticklabels(class_names)
        ax2.set_xlabel("Tahmin")
        ax2.set_ylabel("Gercek")
        plt.colorbar(im2, ax=ax2)

        plt.tight_layout()

        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            fig.savefig(save_path, dpi=config.PLOT_DPI, bbox_inches="tight")
            self.logger.info(f"Karisiklik matrisi kaydedildi: {save_path}")
        plt.close(fig)
