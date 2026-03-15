"""
Kacak Repeater Tespit Sistemi - Spektrum Gozetleme ve Anomali Tespiti

FrequencyScanner ve SpectrumAnalyzer ile bant taramasi yapar,
bulunan sinyalleri bilinen yasal frekanslarla karsilastirir,
eslesmeyen sinyalleri 'supheli' olarak isaretler.

3 mod destekler:
  1. Donanim modu: USRP E310 ile canli tarama
  2. Simulasyon modu: Sentetik veri ile test
  3. Dosya modu: GNU Radio / .npy dosyasindan analiz
"""

import os
import threading
import time
from datetime import datetime

import numpy as np

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

from usrp_noma.utils import setup_logger, freq_to_str, linear_to_dB
from usrp_noma.analysis.spectrum_analyzer import SpectrumAnalyzer
from repeater_detector import config as det_config
from repeater_detector.utils import classify_frequency, generate_report


logger = setup_logger("repeater_detector.surveillance")


class SpectrumSurveillance:
    """
    Spektrum gozetleme ve anomali tespit sinifi.

    FrequencyScanner ile bant taramasi yapar, bulunan sinyalleri
    bilinen yasal frekanslarla karsilastirir, eslesmeyen sinyalleri
    supheli olarak raporlar.
    """

    def __init__(self, controller=None, known_frequencies=None,
                 simulation_mode=False, sample_rate=None):
        """
        Args:
            controller: USRPController nesnesi. None ise simulation_mode olmali.
            known_frequencies: Bilinen frekans sozlugu. None ise config'den.
            simulation_mode: True ise donanim yerine sentetik veri kullanir.
            sample_rate: Ornekleme hizi. None ise config'den.
        """
        self.controller = controller
        self.known_frequencies = known_frequencies or det_config.ALL_KNOWN_FREQUENCIES
        self.simulation_mode = simulation_mode
        self.sample_rate = sample_rate or det_config.DEFAULT_SAMPLE_RATE

        self.analyzer = SpectrumAnalyzer(
            sample_rate=self.sample_rate,
            fft_size=det_config.DEFAULT_FFT_SIZE
        )

        self.detection_history = []
        self._surveillance_running = False
        self._surveillance_thread = None

        self.logger = setup_logger("SpectrumSurveillance")

        # Donanim modu icin FrequencyScanner
        self._scanner = None
        if controller and not simulation_mode:
            from usrp_noma.analysis.frequency_scanner import FrequencyScanner
            self._scanner = FrequencyScanner(controller)

    def scan_and_detect(self, band="full", threshold_dB=None, dwell_time=None):
        """
        Donanim ile tek seferlik bant taramasi + anomali tespiti yapar.

        Args:
            band: "low", "high", "full" veya alt bant adi (orn: "1800-2100 MHz")
            threshold_dB: Sinyal tespit esigi (dB). None ise config'den.
            dwell_time: Her frekansta bekleme suresi (s). None ise config'den.

        Returns:
            dict: Tespit sonuclari
        """
        if self._scanner is None:
            raise RuntimeError(
                "Donanim modu icin controller gerekli. "
                "--sim veya --input kullanin.")

        if threshold_dB is None:
            threshold_dB = det_config.ANOMALY_POWER_THRESHOLD_DB
        if dwell_time is None:
            dwell_time = det_config.SCAN_DWELL_TIME

        scan_time = datetime.now()
        self.logger.info("Bant taramasi baslatiliyor: %s", band)

        # Alt bant veya standart bant taramasi
        if band in det_config.SCAN_SUB_BANDS:
            sub = det_config.SCAN_SUB_BANDS[band]
            raw_results = self._scanner.scan_band(
                sub["start"], sub["stop"],
                step=sub["step"], dwell_time=dwell_time)
        elif band == "low":
            raw_results = self._scanner.scan_low_band(dwell_time=dwell_time)
        elif band == "high":
            raw_results = self._scanner.scan_high_band(dwell_time=dwell_time)
        elif band == "full":
            raw_results = self._scanner.scan_full(dwell_time=dwell_time)
        else:
            raw_results = self._scanner.scan_full(dwell_time=dwell_time)

        # Aktif sinyalleri bul
        active = self._scanner.find_active_signals(
            threshold_dB=threshold_dB, results=raw_results)

        # Yasal / supheli ayristirma
        legal, suspicious = self._classify_signals(active)

        result = {
            "scan_time": scan_time,
            "band": band,
            "threshold_dB": threshold_dB,
            "total_signals": len(active),
            "legal_signals": legal,
            "suspicious_signals": suspicious,
            "scan_results_raw": raw_results,
        }

        self.detection_history.append(result)
        self.logger.info(
            "Tarama tamamlandi: %d aktif sinyal, %d yasal, %d supheli",
            len(active), len(legal), len(suspicious))

        return result

    def scan_and_detect_from_data(self, iq_data, sample_rate=None,
                                  center_freq=0, threshold_dB=None,
                                  ground_truth=None):
        """
        IQ verisinden (dosya veya sentetik) analiz ve anomali tespiti yapar.
        GNU Radio kayitlari veya simulasyon verileri icin kullanilir.

        Args:
            iq_data: Kompleks IQ veri dizisi (complex64)
            sample_rate: Ornekleme hizi (Hz). None ise mevcut analyzer'dan.
            center_freq: Merkez frekans (Hz)
            threshold_dB: Sinyal tespit esigi (dB). None ise config'den.
            ground_truth: Dogrulama bilgileri (simulasyon icin, dict)

        Returns:
            dict: Tespit sonuclari
        """
        if threshold_dB is None:
            threshold_dB = det_config.ANOMALY_POWER_THRESHOLD_DB
        if sample_rate is not None:
            self.analyzer = SpectrumAnalyzer(
                sample_rate=sample_rate,
                fft_size=det_config.DEFAULT_FFT_SIZE)
            self.sample_rate = sample_rate

        scan_time = datetime.now()

        # PSD hesapla
        freqs, psd_dB = self.analyzer.compute_psd(iq_data, method="welch")

        # Frekanslari mutlak degerlerine cevir
        freqs_abs = freqs + center_freq

        # Adaptif esik: PSD medyanindan belirli dB yukari olan tepeler
        # Sentetik veriler ve gercek veriler farkli PSD olceklerinde olabilir
        # Bu yuzden her zaman adaptif esik kullanilir
        median_psd = float(np.median(psd_dB))
        adaptive_threshold = median_psd + 6  # Gurultu tabanindan 6 dB yukari
        effective_threshold = min(threshold_dB, adaptive_threshold)

        # Tepe noktalarini bul
        peaks = self.analyzer.find_peaks(
            freqs, psd_dB,
            threshold_dB=effective_threshold,
            min_distance=10)

        # Aktif sinyalleri mutlak frekanslarla olustur
        active = []
        for peak_freq_rel, peak_power in peaks:
            active.append((center_freq + peak_freq_rel, peak_power))

        # Siniflandirma
        legal, suspicious = self._classify_signals(active)

        result = {
            "scan_time": scan_time,
            "band": f"IQ data @{freq_to_str(center_freq)}",
            "threshold_dB": threshold_dB,
            "total_signals": len(active),
            "legal_signals": legal,
            "suspicious_signals": suspicious,
            "psd_data": {"freqs": freqs_abs, "psd_dB": psd_dB},
            "center_freq": center_freq,
        }

        # Ground truth karsilastirma (simulasyon icin)
        if ground_truth:
            result["ground_truth"] = ground_truth
            result["detection_accuracy"] = self._evaluate_detection(
                suspicious, ground_truth)

        self.detection_history.append(result)
        self.logger.info(
            "Dosya/simulasyon analizi: %d aktif sinyal, %d yasal, %d supheli",
            len(active), len(legal), len(suspicious))

        return result

    def continuous_surveillance(self, callback, interval_sec=None, band="full"):
        """
        Periyodik gozetleme modu (ayri thread'de calisir).

        Args:
            callback: Her tarama sonrasi cagrilir. Imza: callback(detection_result)
            interval_sec: Taramalar arasi bekleme (s). None ise config'den.
            band: Taranacak bant
        """
        if interval_sec is None:
            interval_sec = det_config.SURVEILLANCE_SCAN_INTERVAL_SEC

        self._surveillance_running = True

        def _loop():
            while self._surveillance_running:
                try:
                    result = self.scan_and_detect(band=band)
                    callback(result)
                except Exception as e:
                    self.logger.error("Gozetleme hatasi: %s", e)
                time.sleep(interval_sec)

        self._surveillance_thread = threading.Thread(
            target=_loop, daemon=True)
        self._surveillance_thread.start()
        self.logger.info("Surekli gozetleme baslatildi (aralik: %ds)", interval_sec)

    def stop_surveillance(self):
        """Surekli gozetlemeyi durdurur."""
        self._surveillance_running = False
        if self._surveillance_thread and self._surveillance_thread.is_alive():
            self._surveillance_thread.join(timeout=10)
        self.logger.info("Gozetleme durduruldu.")

    def _classify_signals(self, active_signals):
        """
        Aktif sinyalleri yasal / supheli olarak siniflandirir.

        Args:
            active_signals: [(freq_hz, power_dB), ...] listesi

        Returns:
            tuple: (legal_list, suspicious_list)
        """
        legal = []
        suspicious = []

        for freq, power_dB in active_signals:
            matched, matched_name, deviation_hz = classify_frequency(freq)

            if matched:
                legal.append({
                    "freq": freq,
                    "power_dB": power_dB,
                    "matched_name": matched_name,
                    "deviation_hz": deviation_hz,
                })
            else:
                score = self._compute_anomaly_score(
                    freq, power_dB, matched_name, deviation_hz)
                level = self._score_to_level(score)
                suspicious.append({
                    "freq": freq,
                    "power_dB": power_dB,
                    "anomaly_score": score,
                    "confidence_level": level,
                    "closest_known": matched_name,
                    "deviation_hz": deviation_hz,
                })

        # Supheli sinyalleri skora gore sirala (yuksek -> dusuk)
        suspicious.sort(key=lambda x: x["anomaly_score"], reverse=True)

        return legal, suspicious

    def _compute_anomaly_score(self, freq, power_dB, closest_name, deviation_hz):
        """
        Anomali skoru hesaplar (0.0 = muhtemelen yasal, 1.0 = kesinlikle kacak).

        Faktorler:
        - Bilinen frekanstan sapma miktari
        - Sinyal gucu (cok guclu bilinmeyen = daha supheli)
        - Frekans bandi uyumsuzlugu
        """
        weights = det_config.ANOMALY_SCORE_WEIGHTS

        # Sapma skoru: ne kadar uzaksa o kadar supheli
        max_dev = 5e6  # 5 MHz referans
        deviation_score = min(1.0, deviation_hz / max_dev)

        # Guc skoru: sinyal ne kadar gucluyse o kadar supheli
        power_ref_low = det_config.ANOMALY_POWER_THRESHOLD_DB
        power_ref_high = -20  # -20 dB referans ust sinir
        if power_dB > power_ref_low:
            power_score = min(1.0,
                              (power_dB - power_ref_low) /
                              (power_ref_high - power_ref_low + 1e-6))
        else:
            power_score = 0.0

        # Bant uyumu skoru: bilinen bantlarin disindaysa supheli
        band_score = 0.0
        in_any_band = False
        for sub_band in det_config.SCAN_SUB_BANDS.values():
            if sub_band["start"] <= freq <= sub_band["stop"]:
                in_any_band = True
                break
        if not in_any_band:
            band_score = 0.8  # Bilinen bantlarin disinda = yuksek skor

        # Agirlikli toplam
        score = (weights["deviation"] * deviation_score +
                 weights["power"] * power_score +
                 weights["bandwidth"] * band_score)

        return min(1.0, max(0.0, score))

    def _score_to_level(self, score):
        """Anomali skorunu guven seviyesine cevirir."""
        levels = det_config.ANOMALY_CONFIDENCE_LEVELS
        if score >= levels["yuksek"]:
            return "yuksek"
        elif score >= levels["orta"]:
            return "orta"
        elif score >= levels["dusuk"]:
            return "dusuk"
        return "cok_dusuk"

    def _evaluate_detection(self, suspicious, ground_truth):
        """
        Simulasyon modunda tespit dogrulugun degerlendirir.

        Args:
            suspicious: Tespit edilen supheli sinyaller
            ground_truth: Gercek kacak sinyal bilgileri

        Returns:
            dict: Dogruluk metrikleri
        """
        true_illegals = [s for s in ground_truth.get("all_signals", [])
                         if s.get("label") == "kacak"]
        true_legals = [s for s in ground_truth.get("all_signals", [])
                       if s.get("label") == "yasal"]
        detected_count = len(suspicious)
        true_count = len(true_illegals)

        # Basit eslestirme: tespit edilen frekanslar gercek frekanslara yakin mi?
        tolerance = det_config.ANOMALY_BW_TOLERANCE_HZ * 3  # Genis tolerans

        matched = 0
        for true_sig in true_illegals:
            true_freq = true_sig["freq"]
            for det_sig in suspicious:
                if abs(det_sig["freq"] - true_freq) < tolerance:
                    matched += 1
                    break

        # Yasal sinyal eslesmesi: tespit edilmis ama aslinda yasal olanlar
        legal_matched = 0
        for det_sig in suspicious:
            for legal_sig in true_legals:
                if abs(det_sig["freq"] - legal_sig["freq"]) < tolerance:
                    legal_matched += 1
                    break

        # Gercek false alarm = tespit edilen - dogru kacak eslesmesi - yasal eslesmesi
        real_false_alarms = max(0, detected_count - matched - legal_matched)

        return {
            "true_illegal_count": true_count,
            "detected_count": detected_count,
            "correctly_detected": matched,
            "detection_rate": matched / max(true_count, 1),
            "false_alarm_count": real_false_alarms,
            "legal_as_suspicious": legal_matched,
        }

    def get_detection_history(self):
        """Onceki tum tespit sonuclarini dondurur."""
        return list(self.detection_history)

    def export_detections(self, filename=None, fmt="csv"):
        """
        Tespit sonuclarini disa aktarir.

        Args:
            filename: Dosya adi. None ise otomatik isimlendirilir.
            fmt: Format ("csv" veya "json")

        Returns:
            str: Dosya yolu
        """
        if not self.detection_history:
            self.logger.warning("Disa aktarilacak tespit sonucu yok.")
            return None

        output_dir = det_config.SURVEILLANCE_REPORT_DIR
        os.makedirs(output_dir, exist_ok=True)

        if filename is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(output_dir, f"detections_{ts}.{fmt}")

        if fmt == "json":
            import json
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(self.detection_history, f,
                          ensure_ascii=False, indent=2, default=str)
        elif fmt == "csv":
            import csv
            with open(filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Tarama Zamani", "Frekans (Hz)", "Frekans",
                    "Guc (dB)", "Anomali Skoru", "Seviye",
                    "En Yakin Yasal", "Sapma (Hz)"])
                for result in self.detection_history:
                    for sig in result.get("suspicious_signals", []):
                        writer.writerow([
                            result.get("scan_time", ""),
                            sig.get("freq", 0),
                            freq_to_str(sig.get("freq", 0)),
                            f"{sig.get('power_dB', 0):.1f}",
                            f"{sig.get('anomaly_score', 0):.3f}",
                            sig.get("confidence_level", ""),
                            sig.get("closest_known", ""),
                            f"{sig.get('deviation_hz', 0):.0f}",
                        ])

        self.logger.info("Tespit sonuclari kaydedildi: %s", filename)
        return filename

    def plot_surveillance_results(self, detection_result, save_path=None):
        """
        Tarama sonuclarini gorsellestirir.

        Spektrum grafigi uzerinde yasal sinyaller (yesil) ve
        supheli sinyaller (kirmizi) isaretlenir.

        Args:
            detection_result: scan_and_detect() veya scan_and_detect_from_data() ciktisi
            save_path: Dosyaya kaydetme yolu. None ise ekranda gosterir.
        """
        if plt is None:
            self.logger.warning("matplotlib yuklu degil, grafik uretilemez.")
            return

        fig, axes = plt.subplots(2, 1, figsize=(14, 10))

        # ---- Panel 1: Spektrum + isaretler ----
        ax1 = axes[0]
        psd_data = detection_result.get("psd_data")
        if psd_data:
            freqs_mhz = psd_data["freqs"] / 1e6
            ax1.plot(freqs_mhz, psd_data["psd_dB"],
                     color="steelblue", linewidth=0.8, alpha=0.8)

        # Yasal sinyaller (yesil)
        for sig in detection_result.get("legal_signals", []):
            ax1.axvline(sig["freq"] / 1e6, color="green",
                        linestyle="--", alpha=0.5, linewidth=1)
            ax1.annotate(sig.get("matched_name", ""),
                         xy=(sig["freq"] / 1e6, sig["power_dB"]),
                         fontsize=6, color="green", rotation=45,
                         ha="left", va="bottom")

        # Supheli sinyaller (kirmizi)
        for sig in detection_result.get("suspicious_signals", []):
            ax1.axvline(sig["freq"] / 1e6, color="red",
                        linestyle="-", alpha=0.7, linewidth=2)
            label = (f"SUPHE\n{freq_to_str(sig['freq'])}\n"
                     f"{sig['power_dB']:.1f} dB\n"
                     f"Skor: {sig['anomaly_score']:.2f}")
            ax1.annotate(label,
                         xy=(sig["freq"] / 1e6, sig.get("power_dB", -30)),
                         fontsize=7, color="red", fontweight="bold",
                         ha="center", va="bottom",
                         bbox=dict(boxstyle="round,pad=0.3",
                                   facecolor="lightyellow", alpha=0.8))

        # Esik cizgisi
        threshold = detection_result.get("threshold_dB",
                                         det_config.ANOMALY_POWER_THRESHOLD_DB)
        if psd_data:
            ax1.axhline(threshold, color="orange", linestyle=":",
                        label=f"Esik: {threshold} dB")

        ax1.set_xlabel("Frekans (MHz)")
        ax1.set_ylabel("Guc (dB)")
        ax1.set_title("Spektrum Gozetleme Sonuclari")
        ax1.legend(loc="upper right", fontsize=8)
        ax1.grid(True, alpha=0.3)

        # ---- Panel 2: Anomali skoru bar grafigi ----
        ax2 = axes[1]
        suspicious = detection_result.get("suspicious_signals", [])
        if suspicious:
            freqs_label = [freq_to_str(s["freq"]) for s in suspicious]
            scores = [s["anomaly_score"] for s in suspicious]
            colors = []
            for s in scores:
                if s >= det_config.ANOMALY_CONFIDENCE_LEVELS["yuksek"]:
                    colors.append("red")
                elif s >= det_config.ANOMALY_CONFIDENCE_LEVELS["orta"]:
                    colors.append("orange")
                else:
                    colors.append("gold")

            bars = ax2.barh(freqs_label, scores, color=colors, edgecolor="black")
            ax2.set_xlabel("Anomali Skoru")
            ax2.set_title("Supheli Sinyaller — Anomali Skorlari")
            ax2.set_xlim(0, 1.1)

            # Guven seviyesi referans cizgileri
            for level_name, level_val in det_config.ANOMALY_CONFIDENCE_LEVELS.items():
                ax2.axvline(level_val, color="gray", linestyle=":",
                            alpha=0.5, linewidth=0.8)
                ax2.text(level_val, -0.5, level_name, fontsize=7,
                         color="gray", ha="center")
        else:
            ax2.text(0.5, 0.5, "Supheli sinyal tespit edilmedi",
                     transform=ax2.transAxes, ha="center", va="center",
                     fontsize=14, color="green")
            ax2.set_title("Supheli Sinyal Yok")

        plt.tight_layout()

        if save_path:
            os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path)
                        else ".", exist_ok=True)
            plt.savefig(save_path, dpi=det_config.PLOT_DPI, bbox_inches="tight")
            self.logger.info("Grafik kaydedildi: %s", save_path)
        else:
            plt.show()

        plt.close(fig)
