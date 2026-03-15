"""
Kacak Repeater Tespit Sistemi - Sinyal Siniflandirici

Tespit edilen sinyallerin tipini (repeater, baz istasyonu, WiFi,
telsiz, bilinmeyen) ozellik tabanli olarak siniflandirir.

IQDataAnalyzer ve SpectrumAnalyzer'i kullanir.
"""

import numpy as np

from usrp_noma.utils import setup_logger, linear_to_dB
from usrp_noma.analysis.spectrum_analyzer import SpectrumAnalyzer
from repeater_detector import config as det_config


logger = setup_logger("repeater_detector.classifier")


class SignalClassifier:
    """
    Tespit edilen sinyallerin tipini ozellik tabanli siniflandirma.

    Bant genisligi, modulasyon karakteristigi ve spektral ozelliklere
    gore sinyal tipini tahmin eder.
    """

    # Sinyal tipleri
    SIGNAL_TYPES = [
        "repeater",        # Analog/dijital repeater (dar bant FM/DMR)
        "baz_istasyonu",   # GSM/LTE baz istasyonu (genis bant)
        "wifi",            # WiFi erisim noktasi
        "telsiz",          # Basit telsiz / PMR
        "bilinmeyen",      # Siniflandirilamayan sinyal
    ]

    def __init__(self, sample_rate=None):
        """
        Args:
            sample_rate: Ornekleme hizi (Hz). None ise config'den.
        """
        self.sample_rate = sample_rate or det_config.DEFAULT_SAMPLE_RATE
        self.analyzer = SpectrumAnalyzer(
            sample_rate=self.sample_rate,
            fft_size=det_config.DEFAULT_FFT_SIZE)
        self.logger = setup_logger("SignalClassifier")

    def classify_signal(self, iq_data, center_freq=None):
        """
        IQ verisinden sinyal tipini tahmin eder.

        Args:
            iq_data: Kompleks IQ veri dizisi
            center_freq: Merkez frekans (Hz)

        Returns:
            dict: {
                "type": str,
                "confidence": float,
                "bandwidth_hz": float,
                "modulation_est": str,
                "features": dict,
            }
        """
        if len(iq_data) < 64:
            return {
                "type": "bilinmeyen",
                "confidence": 0.0,
                "bandwidth_hz": 0,
                "modulation_est": "bilinmeyen",
                "features": {},
            }

        # Ozellik cikarimi
        bw = self.estimate_bandwidth(iq_data)
        mod_type = self.estimate_modulation_type(iq_data)
        features = self._compute_features(iq_data)

        # Siniflandirma karar agaci
        sig_type, confidence = self._classify(
            bw, mod_type, features, center_freq)

        return {
            "type": sig_type,
            "confidence": confidence,
            "bandwidth_hz": bw,
            "modulation_est": mod_type,
            "features": features,
        }

    def estimate_bandwidth(self, iq_data):
        """
        Sinyalin bant genisligini 90% enerji yontemiyle tahmin eder.

        Args:
            iq_data: Kompleks IQ veri dizisi

        Returns:
            float: Tahmini bant genisligi (Hz)
        """
        freqs, psd_dB = self.analyzer.compute_psd(iq_data, method="welch")
        psd_linear = 10 ** (psd_dB / 10.0)
        total_power = np.sum(psd_linear)

        if total_power < 1e-20:
            return 0.0

        # %90 enerji bariyeri
        cumsum = np.cumsum(psd_linear)
        threshold_low = 0.05 * total_power
        threshold_high = 0.95 * total_power

        idx_low = np.searchsorted(cumsum, threshold_low)
        idx_high = np.searchsorted(cumsum, threshold_high)

        if idx_low >= len(freqs) or idx_high >= len(freqs):
            return self.sample_rate

        bw = abs(freqs[min(idx_high, len(freqs) - 1)] -
                 freqs[min(idx_low, len(freqs) - 1)])
        return float(bw)

    def estimate_modulation_type(self, iq_data):
        """
        Basit modulasyon tipi tahmini.

        Yontem:
        - Anlik frekans sapma analizi (FM tespiti)
        - Genlik varyans analizi (AM tespiti)
        - Konstelasyon scatter dagilimsalligi (dijital tespiti)

        Args:
            iq_data: Kompleks IQ veri dizisi

        Returns:
            str: "FM", "AM", "dijital", "bilinmeyen"
        """
        if len(iq_data) < 32:
            return "bilinmeyen"

        # Genlik analizi
        amplitude = np.abs(iq_data)
        amp_mean = np.mean(amplitude)
        amp_std = np.std(amplitude)
        amp_cv = amp_std / (amp_mean + 1e-12)  # Varyasyon katsayisi

        # Anlik frekans hesaplama
        phase = np.angle(iq_data)
        inst_freq = np.diff(np.unwrap(phase)) * self.sample_rate / (2 * np.pi)
        freq_std = np.std(inst_freq)
        freq_range = np.ptp(inst_freq)  # Tepe-tepe frekans degisimi

        # Karar mantigi
        if amp_cv < 0.15 and freq_std > 500:
            # Sabit genlik + degisken frekans -> FM
            return "FM"
        elif amp_cv > 0.4 and freq_std < 200:
            # Degisken genlik + sabit frekans -> AM
            return "AM"
        elif amp_cv > 0.2 and freq_std > 200:
            # Her ikisi de degisken -> dijital (QAM, OFDM benzeri)
            return "dijital"
        else:
            return "bilinmeyen"

    def _compute_features(self, iq_data):
        """
        Siniflandirma icin temel ozellikleri hesaplar.

        Returns:
            dict: Ozellik sozlugu
        """
        amplitude = np.abs(iq_data)
        power = np.mean(amplitude ** 2)

        # Spektral duzluk (flatness) — beyaz gurultuye yakinlik
        freqs, psd_dB = self.analyzer.compute_psd(iq_data, method="welch")
        psd_linear = 10 ** (psd_dB / 10.0)
        psd_linear = np.maximum(psd_linear, 1e-20)
        geo_mean = np.exp(np.mean(np.log(psd_linear)))
        arith_mean = np.mean(psd_linear)
        spectral_flatness = geo_mean / (arith_mean + 1e-20)

        # Crest factor
        peak = np.max(amplitude)
        rms = np.sqrt(np.mean(amplitude ** 2))
        crest_factor = peak / (rms + 1e-12)

        # Kurtosis
        if np.std(amplitude) > 1e-12:
            kurtosis = float(np.mean(
                ((amplitude - np.mean(amplitude)) / np.std(amplitude)) ** 4))
        else:
            kurtosis = 0.0

        return {
            "power_dB": float(linear_to_dB(power)) if power > 0 else -120,
            "spectral_flatness": float(spectral_flatness),
            "crest_factor": float(crest_factor),
            "crest_factor_dB": float(20 * np.log10(crest_factor + 1e-12)),
            "kurtosis": kurtosis,
            "amplitude_cv": float(np.std(amplitude) / (np.mean(amplitude) + 1e-12)),
        }

    def _classify(self, bandwidth_hz, modulation, features, center_freq=None):
        """
        Karar agaci ile sinyal tipini belirler.

        Returns:
            tuple: (tip_str, guven_skoru)
        """
        confidence = 0.5  # Baslangic

        # WiFi tespiti: genis bant + 2.4 GHz civarinda
        if center_freq and 2400e6 <= center_freq <= 2500e6:
            if bandwidth_hz > 1e6:
                return "wifi", 0.85

        # Repeater tespiti: dar bant FM
        if bandwidth_hz < 25e3 and modulation == "FM":
            confidence = 0.80
            # Repeater bantlarinda ise guven artar
            if center_freq:
                if (430e6 <= center_freq <= 470e6 or
                        145e6 <= center_freq <= 148e6):
                    confidence = 0.90
            return "repeater", confidence

        # Telsiz: dar bant ama FM degil
        if bandwidth_hz < 25e3:
            return "telsiz", 0.60

        # Baz istasyonu: genis bant dijital
        if bandwidth_hz > 200e3 and modulation == "dijital":
            confidence = 0.70
            if center_freq:
                # GSM/LTE bantlarinda ise guven artar
                if (890e6 <= center_freq <= 960e6 or
                        1710e6 <= center_freq <= 1880e6 or
                        2110e6 <= center_freq <= 2170e6):
                    confidence = 0.85
            return "baz_istasyonu", confidence

        # Genis bant ama siniflandirilamayan
        if bandwidth_hz > 500e3:
            return "baz_istasyonu", 0.45

        return "bilinmeyen", 0.30
