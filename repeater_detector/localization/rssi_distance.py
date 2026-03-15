"""
Kacak Repeater Tespit Sistemi - RSSI Tabanli Mesafe Tahmini

RSSI (Received Signal Strength Indicator) degerlerinden
sinyal kaynagina olan mesafeyi tahmin eder.

Desteklenen modeller:
- Serbest Uzay Yol Kaybi (FSPL)
- Log-Distance Yol Kaybi Modeli
- Coklu olcum ile iyilestirilmis tahmin
"""

import os
import numpy as np

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

from usrp_noma.utils import setup_logger, linear_to_dB, dB_to_linear, compute_power_dBm
from repeater_detector import config as det_config


logger = setup_logger("repeater_detector.rssi_distance")


class RSSIDistanceEstimator:
    """
    RSSI tabanli mesafe tahmini sinifi.

    Farkli yol kaybi modelleri kullanarak sinyal gucunden
    vericiye olan mesafeyi tahmin eder.
    """

    def __init__(self, frequency_hz=None, tx_power_dBm=None,
                 tx_gain_dBi=None, rx_gain_dBi=None,
                 cable_loss_dB=None, environment="kentsel"):
        """
        Args:
            frequency_hz: Calisma frekansi (Hz). None ise 900 MHz.
            tx_power_dBm: Verici cikis gucu (dBm). None ise config'den.
            tx_gain_dBi: Verici anten kazanci (dBi). None ise config'den.
            rx_gain_dBi: Alici anten kazanci (dBi). None ise config'den.
            cable_loss_dB: Kablo kaybi (dB). None ise config'den.
            environment: Ortam tipi (ENVIRONMENT_MODELS anahtari)
        """
        self.frequency_hz = frequency_hz or 900e6
        self.tx_power_dBm = tx_power_dBm or det_config.TX_POWER_DBM
        self.tx_gain_dBi = tx_gain_dBi or det_config.TX_ANTENNA_GAIN_DBI
        self.rx_gain_dBi = rx_gain_dBi or det_config.RX_ANTENNA_GAIN_DBI
        self.cable_loss_dB = cable_loss_dB or det_config.CABLE_LOSS_DB
        self.d0 = det_config.PATH_LOSS_D0  # Referans mesafe (m)

        if environment not in det_config.ENVIRONMENT_MODELS:
            raise ValueError(
                f"Bilinmeyen ortam: '{environment}'. "
                f"Gecerli: {list(det_config.ENVIRONMENT_MODELS.keys())}")
        self.environment = environment

        # Kalibrasyon: PL(d0) ilk hesaplama
        self._pl_d0 = self._compute_fspl_at_distance(self.d0)
        self._calibrated = False

        self.logger = setup_logger("RSSIDistanceEstimator")

    def _compute_fspl_at_distance(self, distance_m):
        """
        Belirli mesafedeki serbest uzay yol kaybini (FSPL) hesaplar.

        FSPL(dB) = 20*log10(d) + 20*log10(f) + 20*log10(4*pi/c)
        """
        wavelength = det_config.SPEED_OF_LIGHT / self.frequency_hz
        if distance_m < 1e-6:
            distance_m = 1e-6
        fspl = 20 * np.log10(4 * np.pi * distance_m / wavelength)
        return fspl

    def _compute_path_loss(self, rssi_dBm):
        """
        RSSI'dan yol kaybini hesaplar.

        PL = P_tx + G_tx + G_rx - L_cable - P_rx
        """
        path_loss = (self.tx_power_dBm + self.tx_gain_dBi +
                     self.rx_gain_dBi - self.cable_loss_dB - rssi_dBm)
        return path_loss

    def estimate_distance_fspl(self, rssi_dBm):
        """
        Serbest Uzay Yol Kaybi (FSPL) modeli ile mesafe tahmini.

        FSPL = 20*log10(d) + 20*log10(f) + 20*log10(4*pi/c)
        => d = (c / (4*pi*f)) * 10^(FSPL/20)

        Args:
            rssi_dBm: Alinan sinyal gucu (dBm)

        Returns:
            dict: {
                "distance_m": float,
                "path_loss_dB": float,
                "model": "FSPL",
            }
        """
        path_loss_dB = self._compute_path_loss(rssi_dBm)
        wavelength = det_config.SPEED_OF_LIGHT / self.frequency_hz

        # d = wavelength / (4*pi) * 10^(PL/20)
        distance_m = (wavelength / (4 * np.pi)) * (10 ** (path_loss_dB / 20.0))
        distance_m = max(distance_m, 0.1)

        return {
            "distance_m": float(distance_m),
            "path_loss_dB": float(path_loss_dB),
            "model": "FSPL",
            "frequency_hz": self.frequency_hz,
        }

    def estimate_distance_log(self, rssi_dBm, n=None, sigma=None):
        """
        Log-Distance Yol Kaybi Modeli ile mesafe tahmini.

        PL(d) = PL(d0) + 10*n*log10(d/d0) + X_sigma
        => d = d0 * 10^((PL - PL(d0)) / (10*n))

        Args:
            rssi_dBm: Alinan sinyal gucu (dBm)
            n: Yol kaybi ussu. None ise ortam tipinden.
            sigma: Golgeleme standart sapma (dB). None ise ortam tipinden.

        Returns:
            dict: {
                "distance_m": float,
                "distance_min_m": float,
                "distance_max_m": float,
                "path_loss_dB": float,
                "model": "log-distance",
                "environment": str,
                "n": float,
                "sigma": float,
            }
        """
        env = det_config.ENVIRONMENT_MODELS[self.environment]
        n = n or env["n"]
        sigma = sigma or env["sigma"]

        path_loss_dB = self._compute_path_loss(rssi_dBm)

        # d = d0 * 10^((PL - PL(d0)) / (10*n))
        exponent = (path_loss_dB - self._pl_d0) / (10 * n)
        distance_m = self.d0 * (10 ** exponent)
        distance_m = max(distance_m, 0.1)

        # Golgeleme ile guven araligi (+-sigma)
        if sigma > 0:
            exp_min = (path_loss_dB - sigma - self._pl_d0) / (10 * n)
            exp_max = (path_loss_dB + sigma - self._pl_d0) / (10 * n)
            d_min = max(self.d0 * (10 ** exp_min), 0.1)
            d_max = max(self.d0 * (10 ** exp_max), 0.1)
        else:
            d_min = distance_m
            d_max = distance_m

        return {
            "distance_m": float(distance_m),
            "distance_min_m": float(d_min),
            "distance_max_m": float(d_max),
            "path_loss_dB": float(path_loss_dB),
            "model": "log-distance",
            "environment": self.environment,
            "environment_desc": env["aciklama"],
            "n": float(n),
            "sigma": float(sigma),
        }

    def estimate_distance_multi_measurement(self, rssi_measurements_dBm,
                                            method="mean"):
        """
        Birden fazla RSSI olcumunden iyilestirilmis mesafe tahmini.

        Args:
            rssi_measurements_dBm: RSSI degerleri listesi (dBm)
            method: Birlestirme yontemi ("mean", "median")

        Returns:
            dict: Mesafe tahmini + istatistikler
        """
        measurements = np.array(rssi_measurements_dBm)

        if method == "median":
            combined_rssi = float(np.median(measurements))
        else:  # mean
            combined_rssi = float(np.mean(measurements))

        rssi_std = float(np.std(measurements))

        # Log-distance modeli ile tahmin
        result = self.estimate_distance_log(combined_rssi)

        # Istatistik bilgileri ekle
        result["num_measurements"] = len(measurements)
        result["rssi_mean_dBm"] = float(np.mean(measurements))
        result["rssi_median_dBm"] = float(np.median(measurements))
        result["rssi_std_dB"] = rssi_std
        result["rssi_min_dBm"] = float(np.min(measurements))
        result["rssi_max_dBm"] = float(np.max(measurements))
        result["method"] = method

        return result

    def measure_rssi(self, iq_data, gain_dB=None):
        """
        IQ verisinden RSSI (dBm) hesaplar.
        compute_power_dBm() kullanir + kazanc/kablo duzeltmesi uygular.

        Args:
            iq_data: Kompleks IQ veri dizisi
            gain_dB: Alici kazanc (dB). None ise config'den.

        Returns:
            float: Kalibre edilmis RSSI (dBm)
        """
        if gain_dB is None:
            gain_dB = det_config.DEFAULT_RX_GAIN

        raw_power_dBm = compute_power_dBm(iq_data)
        # Kazanc duzeltmesi: olculen = gercek + kazanc - kablo_kaybi
        calibrated = raw_power_dBm - gain_dB + self.cable_loss_dB
        return float(calibrated)

    def calibrate(self, known_distance_m, measured_rssi_dBm):
        """
        Bilinen mesafe ve olculen RSSI ile modeli kalibre eder.

        PL(d0) degerini gercek olcumle gunceller.

        Args:
            known_distance_m: Bilinen mesafe (metre)
            measured_rssi_dBm: Olculen RSSI (dBm)
        """
        env = det_config.ENVIRONMENT_MODELS[self.environment]
        n = env["n"]

        measured_pl = self._compute_path_loss(measured_rssi_dBm)
        # PL(d0) = PL(d) - 10*n*log10(d/d0)
        self._pl_d0 = measured_pl - 10 * n * np.log10(
            max(known_distance_m, 0.1) / self.d0)
        self._calibrated = True

        self.logger.info(
            "Model kalibre edildi: d=%sm, RSSI=%.1f dBm -> PL(d0)=%.1f dB",
            known_distance_m, measured_rssi_dBm, self._pl_d0)

    def plot_distance_estimate(self, rssi_dBm, save_path=None):
        """
        Mesafe tahminini gorsellestirir.

        Grafik icerir:
        - Yol kaybi vs mesafe egrileri (FSPL + log-distance)
        - Mevcut RSSI'nin grafik uzerindeki konumu
        - Guven araligi golgeli alan

        Args:
            rssi_dBm: Alinan sinyal gucu (dBm)
            save_path: Kayit yolu. None ise ekranda gosterir.
        """
        if plt is None:
            self.logger.warning("matplotlib yuklu degil.")
            return

        fspl_result = self.estimate_distance_fspl(rssi_dBm)
        log_result = self.estimate_distance_log(rssi_dBm)

        fig, axes = plt.subplots(1, 2, figsize=(16, 7))

        # ---- Panel 1: Yol kaybi vs mesafe ----
        ax1 = axes[0]
        distances = np.logspace(0, 4, 200)  # 1m - 10km

        # FSPL
        fspl_values = [self._compute_fspl_at_distance(d) for d in distances]
        ax1.semilogx(distances, fspl_values, "b-", linewidth=2,
                     label="FSPL (Serbest Uzay)")

        # Log-distance (mevcut ortam)
        env = det_config.ENVIRONMENT_MODELS[self.environment]
        log_values = [self._pl_d0 + 10 * env["n"] * np.log10(d / self.d0)
                      for d in distances]
        ax1.semilogx(distances, log_values, "r-", linewidth=2,
                     label=f"Log-Distance ({self.environment}, n={env['n']})")

        # Golgeleme araligi
        if env["sigma"] > 0:
            log_upper = [v + env["sigma"] for v in log_values]
            log_lower = [v - env["sigma"] for v in log_values]
            ax1.fill_between(distances, log_lower, log_upper,
                             color="red", alpha=0.1,
                             label=f"±{env['sigma']} dB golgeleme")

        # Mevcut olcum
        current_pl = self._compute_path_loss(rssi_dBm)
        ax1.axhline(current_pl, color="green", linestyle="--", linewidth=1.5,
                    label=f"Olculen PL: {current_pl:.1f} dB")

        # Tahmin edilen mesafeler
        ax1.axvline(fspl_result["distance_m"], color="blue",
                    linestyle=":", alpha=0.7)
        ax1.axvline(log_result["distance_m"], color="red",
                    linestyle=":", alpha=0.7)

        ax1.set_xlabel("Mesafe (m)")
        ax1.set_ylabel("Yol Kaybi (dB)")
        ax1.set_title(f"Yol Kaybi Modelleri — {self.frequency_hz/1e6:.0f} MHz")
        ax1.legend(fontsize=8, loc="upper left")
        ax1.grid(True, alpha=0.3)

        # ---- Panel 2: Mesafe tahmin ozeti ----
        ax2 = axes[1]
        ax2.axis("off")

        info_text = [
            "MESAFE TAHMINI OZETI",
            "=" * 40,
            "",
            f"Frekans       : {self.frequency_hz/1e6:.1f} MHz",
            f"RSSI          : {rssi_dBm:.1f} dBm",
            f"Yol Kaybi     : {current_pl:.1f} dB",
            "",
            "--- FSPL Modeli ---",
            f"  Mesafe      : {fspl_result['distance_m']:.1f} m",
            "",
            f"--- Log-Distance ({self.environment}) ---",
            f"  n           : {env['n']}",
            f"  sigma       : {env['sigma']} dB",
            f"  Mesafe      : {log_result['distance_m']:.1f} m",
            f"  Aralik      : {log_result['distance_min_m']:.1f} - "
            f"{log_result['distance_max_m']:.1f} m",
            "",
            "--- Verici Parametreleri ---",
            f"  TX Guc      : {self.tx_power_dBm:.1f} dBm",
            f"  TX Kazanc   : {self.tx_gain_dBi:.1f} dBi",
            f"  RX Kazanc   : {self.rx_gain_dBi:.1f} dBi",
            f"  Kablo Kaybi : {self.cable_loss_dB:.1f} dB",
        ]

        if self._calibrated:
            info_text.append("")
            info_text.append("  [KALIBRE EDILMIS MODEL]")

        ax2.text(0.05, 0.95, "\n".join(info_text),
                 transform=ax2.transAxes,
                 fontfamily="monospace", fontsize=10,
                 verticalalignment="top",
                 bbox=dict(boxstyle="round", facecolor="lightyellow", alpha=0.8))

        plt.tight_layout()

        if save_path:
            os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path)
                        else ".", exist_ok=True)
            plt.savefig(save_path, dpi=det_config.PLOT_DPI, bbox_inches="tight")
            self.logger.info("Grafik kaydedildi: %s", save_path)
        else:
            plt.show()

        plt.close(fig)

    def plot_path_loss_comparison(self, distance_range_m=None, save_path=None):
        """
        Tum ortam modelleri icin yol kaybi karsilastirma grafigi.

        Args:
            distance_range_m: (min, max) mesafe araligi. None ise (1, 5000).
            save_path: Kayit yolu. None ise ekranda gosterir.
        """
        if plt is None:
            self.logger.warning("matplotlib yuklu degil.")
            return

        if distance_range_m is None:
            distance_range_m = (1, 5000)

        distances = np.logspace(
            np.log10(distance_range_m[0]),
            np.log10(distance_range_m[1]),
            300)

        fig, ax = plt.subplots(1, 1, figsize=(12, 8))

        colors = ["blue", "green", "orange", "red", "darkred", "purple"]
        for i, (env_name, env_params) in enumerate(
                det_config.ENVIRONMENT_MODELS.items()):
            n = env_params["n"]
            sigma = env_params["sigma"]
            desc = env_params["aciklama"]

            pl_values = [self._pl_d0 + 10 * n * np.log10(d / self.d0)
                         for d in distances]
            color = colors[i % len(colors)]
            ax.semilogx(distances, pl_values, color=color, linewidth=2,
                        label=f"{env_name} (n={n}, σ={sigma})")

            if sigma > 0:
                pl_upper = [v + sigma for v in pl_values]
                pl_lower = [v - sigma for v in pl_values]
                ax.fill_between(distances, pl_lower, pl_upper,
                                color=color, alpha=0.08)

        ax.set_xlabel("Mesafe (m)", fontsize=12)
        ax.set_ylabel("Yol Kaybi (dB)", fontsize=12)
        ax.set_title(
            f"Yol Kaybi Modeli Karsilastirmasi — {self.frequency_hz/1e6:.0f} MHz",
            fontsize=14)
        ax.legend(fontsize=9, loc="upper left")
        ax.grid(True, alpha=0.3, which="both")

        plt.tight_layout()

        if save_path:
            os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path)
                        else ".", exist_ok=True)
            plt.savefig(save_path, dpi=det_config.PLOT_DPI, bbox_inches="tight")
            self.logger.info("Grafik kaydedildi: %s", save_path)
        else:
            plt.show()

        plt.close(fig)
