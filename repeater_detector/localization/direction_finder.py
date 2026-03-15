"""
Kacak Repeater Tespit Sistemi - Yon Bulma (Direction Finding)

Yonelimsel anten ile sinyal kaynaginin yonunu belirler.
Kullanici anteni yavas yavas dondururken her pozisyonda RSSI
olcumu yapilir, RSSI profili analiz edilerek tepe yonu bulunur.

Hem donanim hem de simulasyon modunu destekler.
"""

import os
import time

import numpy as np

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

from usrp_noma.utils import setup_logger, freq_to_str, compute_power_dBm
from repeater_detector import config as det_config


logger = setup_logger("repeater_detector.direction_finder")


class DirectionFinder:
    """
    Yonelimsel anten ile yon bulma sinifi.

    Kullanici yonelimsel anteni dondurebilecek bir duzenekte
    her pozisyonda RSSI olcumu yapar. RSSI profili uzerinden
    sinyal kaynaginin yonu belirlenir.
    """

    def __init__(self, controller=None, sample_rate=None,
                 num_measurements=None, measurement_duration=None,
                 simulation_mode=False):
        """
        Args:
            controller: USRPController nesnesi. None ise simulation_mode.
            sample_rate: Ornekleme hizi (Hz). None ise config'den.
            num_measurements: Toplam olcum sayisi. None ise config'den (36).
            measurement_duration: Her olcum suresi (s). None ise config'den.
            simulation_mode: True ise sentetik RSSI profili kullanir.
        """
        self.controller = controller
        self.sample_rate = sample_rate or det_config.DEFAULT_SAMPLE_RATE
        self.num_measurements = num_measurements or det_config.DF_NUM_MEASUREMENTS
        self.measurement_duration = (measurement_duration or
                                     det_config.DF_MEASUREMENT_DURATION_SEC)
        self.simulation_mode = simulation_mode

        self._last_measurements = None
        self._last_peak = None

        self.logger = setup_logger("DirectionFinder")

    def take_single_measurement(self, freq=None, duration_sec=None, gain=None):
        """
        Mevcut anten yonunde tek bir RSSI olcumu yapar.

        Args:
            freq: Frekans (Hz). None ise config'den.
            duration_sec: Olcum suresi (s). None ise instance'dan.
            gain: Alici kazanc (dB). None ise config'den.

        Returns:
            dict: {"rssi_dBm": float, "power_dB": float}
        """
        if self.controller is None:
            raise RuntimeError("Olcum icin controller gerekli.")

        if freq is not None:
            self.controller.set_rx_freq(freq)
        if gain is not None:
            self.controller.set_rx_gain(gain)

        dur = duration_sec or self.measurement_duration
        num_samples = int(dur * self.sample_rate)

        iq_data = self.controller.receive_samples(num_samples)
        power_dBm = compute_power_dBm(iq_data)

        return {
            "rssi_dBm": float(power_dBm),
            "power_dB": float(power_dBm),
        }

    def start_measurement_session(self, freq, gain=None, callback=None):
        """
        Yon bulma olcum oturumu baslatir.

        Her adimda kullanicidan anteni belirli aciya cekmesini ister (interaktif).
        Simulasyon modunda otomatik olarak sentetik olcumler kullanir.

        Args:
            freq: Hedef sinyal frekansi (Hz)
            gain: Alici kazanc (dB)
            callback: Her olcum sonrasi cagrilir.
                      Imza: callback(step_index, angle_deg, rssi_dBm)

        Returns:
            list[dict]: Her adim: {"angle_deg", "rssi_dBm"}
        """
        angular_step = 360.0 / self.num_measurements

        if self.simulation_mode:
            # Simulasyon: sentetik RSSI profili (varsayilan yon: 135 derece)
            true_angle = getattr(self, '_sim_true_angle', 135.0)
            from repeater_detector.simulation.repeater_simulator import \
                RepeaterSimulator
            simulator = RepeaterSimulator(sample_rate=self.sample_rate)
            measurements = simulator.simulate_rssi_profile(
                true_angle_deg=true_angle,
                num_points=self.num_measurements)
            if callback:
                for i, m in enumerate(measurements):
                    callback(i, m["angle_deg"], m["rssi_dBm"])
            self._last_measurements = measurements
            return measurements

        # Donanim modu: interaktif olcum
        if self.controller is None:
            raise RuntimeError(
                "Donanim modu icin controller gerekli. --sim kullanin.")

        self.controller.set_rx_freq(freq)
        if gain is not None:
            self.controller.set_rx_gain(gain)

        measurements = []
        for step in range(self.num_measurements):
            angle = step * angular_step

            # Kullanici bekle (interaktif)
            input(f"\n  [{step+1}/{self.num_measurements}] "
                  f"Anteni {angle:.0f} dereceye cevirin ve ENTER basin...")

            # Olcum yap
            result = self.take_single_measurement(duration_sec=self.measurement_duration)
            result["angle_deg"] = angle

            measurements.append({
                "angle_deg": float(angle),
                "rssi_dBm": result["rssi_dBm"],
            })

            self.logger.info("  Aci: %6.1f° | RSSI: %7.1f dBm",
                             angle, result["rssi_dBm"])

            if callback:
                callback(step, angle, result["rssi_dBm"])

        self._last_measurements = measurements
        return measurements

    def find_peak_direction(self, measurements=None):
        """
        RSSI profilinden en guclu sinyal yonunu bulur.

        Algoritma:
        1. Olcumleri aci sirasina gore sirala
        2. Hareketli ortalama ile yumusat
        3. Tepe noktalarini bul (prominensle)
        4. Parabolik interpolasyon ile hassas aci
        5. 3 dB huzme genisligi hesabi

        Args:
            measurements: Olcum listesi. None ise son oturumdan.

        Returns:
            dict: {
                "peak_angle_deg": float,
                "peak_rssi_dBm": float,
                "confidence": float,
                "beam_width_deg": float,
                "secondary_peaks": list,
            }
        """
        measurements = measurements or self._last_measurements
        if not measurements or len(measurements) < 3:
            raise ValueError("En az 3 olcum gerekli.")

        # Aci sirasina gore sirala
        measurements = sorted(measurements, key=lambda m: m["angle_deg"])

        angles = np.array([m["angle_deg"] for m in measurements])
        rssi = np.array([m["rssi_dBm"] for m in measurements])
        n = len(rssi)

        # Hareketli ortalama (dairesel)
        window = det_config.DF_SMOOTHING_WINDOW
        if window > 1 and n >= window:
            # Dairesel konvolusyon: sinyali 3 kez tekrarla
            rssi_ext = np.concatenate([rssi, rssi, rssi])
            kernel = np.ones(window) / window
            rssi_smooth = np.convolve(rssi_ext, kernel, mode="same")
            rssi_smooth = rssi_smooth[n:2 * n]
        else:
            rssi_smooth = rssi.copy()

        # Tepe bulma
        try:
            from scipy.signal import find_peaks as scipy_find_peaks
            peak_indices, properties = scipy_find_peaks(
                rssi_smooth,
                prominence=det_config.DF_PEAK_MIN_PROMINENCE_DB,
                distance=max(1, n // 12))
        except ImportError:
            # scipy yoksa basit argmax
            peak_indices = np.array([np.argmax(rssi_smooth)])
            properties = {}

        if len(peak_indices) == 0:
            best_idx = int(np.argmax(rssi_smooth))
            peak_indices = np.array([best_idx])
        else:
            best_idx = int(peak_indices[np.argmax(rssi_smooth[peak_indices])])

        # Parabolik interpolasyon ile hassas aci
        if 0 < best_idx < n - 1:
            y_prev = rssi_smooth[best_idx - 1]
            y_peak = rssi_smooth[best_idx]
            y_next = rssi_smooth[best_idx + 1]
            denom = y_prev - 2 * y_peak + y_next
            if abs(denom) > 1e-12:
                delta = 0.5 * (y_prev - y_next) / denom
            else:
                delta = 0
            step_deg = angles[1] - angles[0] if n > 1 else 10
            refined_angle = angles[best_idx] + delta * step_deg
        else:
            refined_angle = angles[best_idx]

        refined_angle = float(refined_angle % 360)

        # 3 dB huzme genisligi
        half_power = rssi_smooth[best_idx] - 3.0
        above_half = rssi_smooth >= half_power
        beam_width = float(np.sum(above_half) * (360.0 / n))

        # Guven skoru
        dynamic_range = float(np.max(rssi_smooth) - np.min(rssi_smooth))
        if "prominences" in properties and len(properties["prominences"]) > 0:
            # best_idx'in peak_indices icindeki pozisyonunu bul
            idx_in_peaks = np.where(peak_indices == best_idx)[0]
            if len(idx_in_peaks) > 0:
                prominence = float(properties["prominences"][idx_in_peaks[0]])
            else:
                prominence = dynamic_range
        else:
            prominence = dynamic_range
        confidence = min(1.0, prominence / max(dynamic_range, 1e-6))

        # Ikincil tepeler
        secondary = []
        for pi in peak_indices:
            if pi != best_idx:
                secondary.append({
                    "angle_deg": float(angles[pi]),
                    "rssi_dBm": float(rssi_smooth[pi]),
                })

        result = {
            "peak_angle_deg": refined_angle,
            "peak_rssi_dBm": float(rssi_smooth[best_idx]),
            "confidence": float(confidence),
            "beam_width_deg": beam_width,
            "dynamic_range_dB": dynamic_range,
            "secondary_peaks": secondary,
            "num_measurements": n,
        }

        self._last_peak = result
        return result

    def get_guidance_text(self, current_angle_deg, target_angle_deg):
        """
        Kullaniciya yonlendirme metni uretir.

        Args:
            current_angle_deg: Mevcut yon (derece)
            target_angle_deg: Hedef yon (derece)

        Returns:
            str: Turkce yonlendirme metni
        """
        diff = (target_angle_deg - current_angle_deg) % 360
        if diff > 180:
            diff -= 360

        abs_diff = abs(diff)

        if abs_diff < 5:
            return "Hedefe ulasildi! Anten dogru yonde."

        direction = "saat yonunde" if diff > 0 else "saat yonunun tersine"

        # Pusula yonu
        compass = self._angle_to_compass(target_angle_deg)

        return (f"{direction} {abs_diff:.0f} derece donun "
                f"(hedef: {target_angle_deg:.0f}° — {compass})")

    def interactive_direction_finding(self, freq, gain=None):
        """
        Interaktif yon bulma oturumu (konsol tabanli).

        Adim adim kullaniciya talimat verir, olcum yapar,
        sonuclari analiz eder ve sinyal yonunu raporlar.

        Args:
            freq: Hedef frekans (Hz)
            gain: Alici kazanc (dB)

        Returns:
            dict: find_peak_direction() sonucu
        """
        print("\n" + "=" * 55)
        print("   YON BULMA OTURUMU")
        print("=" * 55)
        print(f"  Hedef frekans : {freq_to_str(freq)}")
        print(f"  Olcum sayisi  : {self.num_measurements}")
        print(f"  Aci adimi     : {360.0 / self.num_measurements:.0f}°")
        print(f"  Olcum suresi  : {self.measurement_duration:.1f} s")
        print("-" * 55)

        if self.simulation_mode:
            print("  [SIMULASYON MODU — otomatik olcum]")

        print("\n  Anteni dondurmeye hazir oldugunuzda ENTER basin...")
        if not self.simulation_mode:
            input()

        # Olcumleri yap
        def _callback(step, angle, rssi):
            bar_len = max(0, int((rssi + 100) / 2))
            bar = "#" * bar_len
            print(f"  [{step+1:2d}/{self.num_measurements}] "
                  f"Aci: {angle:6.1f}° | RSSI: {rssi:7.1f} dBm | {bar}")

        measurements = self.start_measurement_session(
            freq=freq, gain=gain, callback=_callback)

        # Analiz
        peak = self.find_peak_direction(measurements)

        # Sonuc raporu
        print("\n" + "=" * 55)
        print("   SONUCLAR")
        print("=" * 55)
        compass = self._angle_to_compass(peak["peak_angle_deg"])
        print(f"  Sinyal Yonu    : {peak['peak_angle_deg']:.1f}° ({compass})")
        print(f"  Tepe RSSI      : {peak['peak_rssi_dBm']:.1f} dBm")
        print(f"  Guven Skoru    : {peak['confidence']:.2f}")
        print(f"  Huzme Genisligi: {peak['beam_width_deg']:.0f}°")
        print(f"  Dinamik Aralik : {peak['dynamic_range_dB']:.1f} dB")

        if peak["secondary_peaks"]:
            print(f"\n  Ikincil tepeler (muhtemel yansima):")
            for sp in peak["secondary_peaks"]:
                sp_compass = self._angle_to_compass(sp["angle_deg"])
                print(f"    {sp['angle_deg']:.1f}° ({sp_compass}) — "
                      f"{sp['rssi_dBm']:.1f} dBm")

        print("=" * 55)
        return peak

    def plot_polar_rssi(self, measurements=None, peak_info=None, save_path=None):
        """
        RSSI profilini kutupsal (polar) grafikte gosterir.

        Args:
            measurements: Olcum listesi. None ise son oturumdan.
            peak_info: find_peak_direction() sonucu. None ise hesaplanir.
            save_path: Kayit yolu. None ise ekranda gosterir.
        """
        if plt is None:
            self.logger.warning("matplotlib yuklu degil.")
            return

        measurements = measurements or self._last_measurements
        if not measurements:
            self.logger.warning("Gosterilecek olcum yok.")
            return

        if peak_info is None:
            peak_info = self.find_peak_direction(measurements)

        angles = np.array([m["angle_deg"] for m in measurements])
        rssi = np.array([m["rssi_dBm"] for m in measurements])

        # Kutupsal grafik icin radyana cevir
        angles_rad = np.radians(angles)
        # Daireyi kapat
        angles_rad = np.append(angles_rad, angles_rad[0])
        rssi_plot = np.append(rssi, rssi[0])

        fig, ax = plt.subplots(1, 1, figsize=(10, 10),
                               subplot_kw={"projection": "polar"})

        # RSSI profili
        ax.plot(angles_rad, rssi_plot, "b-", linewidth=2, label="RSSI Profili")
        ax.fill(angles_rad, rssi_plot, alpha=0.15, color="blue")

        # Tepe yonu (kirmizi cizgi)
        peak_rad = np.radians(peak_info["peak_angle_deg"])
        ax.plot([peak_rad, peak_rad],
                [np.min(rssi) - 5, peak_info["peak_rssi_dBm"]],
                color="red", linewidth=3, linestyle="-")

        # Tepe isaretcisi
        peak_label = (f"Sinyal Yonu\n"
                      f"{peak_info['peak_angle_deg']:.1f}°\n"
                      f"{peak_info['peak_rssi_dBm']:.1f} dBm")
        ax.annotate(peak_label,
                    xy=(peak_rad, peak_info["peak_rssi_dBm"]),
                    fontsize=10, color="red", fontweight="bold",
                    ha="center", va="bottom")

        # Ikincil tepeler
        for sp in peak_info.get("secondary_peaks", []):
            sp_rad = np.radians(sp["angle_deg"])
            ax.plot(sp_rad, sp["rssi_dBm"], "o", color="orange",
                    markersize=8, label="Yansima?")

        # Grafik ayarlari
        ax.set_theta_zero_location("N")  # Kuzey 0 derece
        ax.set_theta_direction(-1)  # Saat yonu
        compass_labels = ["K", "KD", "D", "GD", "G", "GB", "B", "KB"]
        ax.set_thetagrids(np.arange(0, 360, 45), labels=compass_labels)
        ax.set_title(
            f"Yon Bulma — RSSI Kutupsal Profil\n"
            f"Guven: {peak_info['confidence']:.2f} | "
            f"Huzme: {peak_info['beam_width_deg']:.0f}°",
            fontsize=13, pad=20)

        plt.tight_layout()

        if save_path:
            os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path)
                        else ".", exist_ok=True)
            plt.savefig(save_path, dpi=det_config.PLOT_DPI, bbox_inches="tight")
            self.logger.info("Grafik kaydedildi: %s", save_path)
        else:
            plt.show()

        plt.close(fig)

    def plot_rssi_vs_angle(self, measurements=None, save_path=None):
        """
        RSSI vs Aci grafigi (kartezyen koordinat).

        Args:
            measurements: Olcum listesi. None ise son oturumdan.
            save_path: Kayit yolu.
        """
        if plt is None:
            self.logger.warning("matplotlib yuklu degil.")
            return

        measurements = measurements or self._last_measurements
        if not measurements:
            self.logger.warning("Gosterilecek olcum yok.")
            return

        peak_info = self.find_peak_direction(measurements)

        angles = [m["angle_deg"] for m in measurements]
        rssi = [m["rssi_dBm"] for m in measurements]

        fig, ax = plt.subplots(1, 1, figsize=(12, 6))

        ax.plot(angles, rssi, "bo-", linewidth=1.5, markersize=5,
                label="RSSI Olcumleri")

        # Tepe noktasi
        ax.axvline(peak_info["peak_angle_deg"], color="red",
                   linestyle="--", linewidth=2,
                   label=f"Tepe: {peak_info['peak_angle_deg']:.1f}°")

        # 3 dB huzme genisligi
        half_power = peak_info["peak_rssi_dBm"] - 3
        ax.axhline(half_power, color="orange", linestyle=":",
                   label=f"-3 dB: {half_power:.1f} dBm")

        ax.set_xlabel("Aci (derece)", fontsize=12)
        ax.set_ylabel("RSSI (dBm)", fontsize=12)
        ax.set_title("RSSI vs Aci — Yon Bulma", fontsize=14)
        ax.set_xlim(0, 360)
        ax.set_xticks(np.arange(0, 361, 30))
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path)
                        else ".", exist_ok=True)
            plt.savefig(save_path, dpi=det_config.PLOT_DPI, bbox_inches="tight")
            self.logger.info("Grafik kaydedildi: %s", save_path)
        else:
            plt.show()

        plt.close(fig)

    @staticmethod
    def _angle_to_compass(angle_deg):
        """Aciyi pusula yonune cevirir."""
        directions = [
            "Kuzey", "Kuzey-Kuzeydogu", "Kuzeydogu", "Dogu-Kuzeydogu",
            "Dogu", "Dogu-Guneydogu", "Guneydogu", "Guney-Guneydogu",
            "Guney", "Guney-Guneybati", "Guneybati", "Bati-Guneybati",
            "Bati", "Bati-Kuzeybati", "Kuzeybati", "Kuzey-Kuzeybati",
        ]
        idx = int(((angle_deg % 360) + 11.25) / 22.5) % 16
        return directions[idx]
