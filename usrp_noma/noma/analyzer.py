"""
NOMA Performans Analizi

Monte Carlo simulasyonu ile BER/kapasite/throughput analizi,
NOMA vs OMA karsilastirma grafikleri ve rapor uretimi.
"""

import os

import numpy as np
from scipy.special import erfc
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from usrp_noma import config
from usrp_noma.utils import setup_logger
from usrp_noma.noma.transmitter import NOMATransmitter
from usrp_noma.noma.receiver import NOMAReceiver

logger = setup_logger("NOMA.Analyzer")


class NOMAnalyzer:
    """NOMA performans analizi ve gorsellestime sinifi."""

    def __init__(self, transmitter=None, receiver=None):
        """NOMAnalyzer baslatir.

        Args:
            transmitter: NOMATransmitter nesnesi. None ise varsayilan olusturulur.
            receiver: NOMAReceiver nesnesi. None ise varsayilan olusturulur.
        """
        self.tx = transmitter or NOMATransmitter()
        self.rx = receiver or NOMAReceiver()

    def simulate_ber_vs_snr(self, snr_range_dB=None, num_symbols=None):
        """Monte Carlo simulasyonu ile BER vs SNR hesaplar.

        Args:
            snr_range_dB: SNR degerleri dizisi (dB). None ise config'den.
            num_symbols: Test sembol sayisi. None ise config'den.

        Returns:
            dict: {
                "snr_dB": [...],
                "ber_users": [[user0_bers], [user1_bers], ...],
                "ber_average": [...]
            }
        """
        if snr_range_dB is None:
            snr_range_dB = np.arange(
                config.NOMA_SNR_MIN_DB,
                config.NOMA_SNR_MAX_DB + config.NOMA_SNR_STEP_DB,
                config.NOMA_SNR_STEP_DB,
            )

        num_symbols = num_symbols or config.NOMA_NUM_SYMBOLS
        num_bits = num_symbols * self.tx.bits_per_symbol

        ber_users = [[] for _ in range(self.tx.num_users)]
        ber_average = []

        logger.info(
            "NOMA BER simulasyonu baslatiliyor: %d SNR noktasi, %d sembol/nokta",
            len(snr_range_dB), num_symbols,
        )

        for snr_dB in snr_range_dB:
            # Veri olustur ve module et
            combined, orig_bits, _ = self.tx.transmit_frame(num_bits=num_bits)

            # AWGN kanal
            received = self.rx.add_awgn(combined, snr_dB)

            # SIC ile coz
            result = self.rx.receive_frame(received, orig_bits)

            for u in range(self.tx.num_users):
                ber_users[u].append(result["ber_per_user"][u])
            ber_average.append(result["ber_average"])

        logger.info("NOMA BER simulasyonu tamamlandi.")
        return {
            "snr_dB": list(snr_range_dB),
            "ber_users": ber_users,
            "ber_average": ber_average,
        }

    def simulate_oma_ber_vs_snr(self, snr_range_dB=None, num_symbols=None):
        """OMA (Orthogonal Multiple Access) BER simulasyonu.

        Her kullaniciya esit kaynak paylasimi (OFDMA/TDMA benzeri).

        Args:
            snr_range_dB: SNR degerleri dizisi (dB).
            num_symbols: Test sembol sayisi.

        Returns:
            dict: NOMA ile ayni formatta sonuclar.
        """
        if snr_range_dB is None:
            snr_range_dB = np.arange(
                config.NOMA_SNR_MIN_DB,
                config.NOMA_SNR_MAX_DB + config.NOMA_SNR_STEP_DB,
                config.NOMA_SNR_STEP_DB,
            )

        num_symbols = num_symbols or config.NOMA_NUM_SYMBOLS
        num_bits = num_symbols * self.tx.bits_per_symbol
        num_users = self.tx.num_users

        ber_users = [[] for _ in range(num_users)]
        ber_average = []

        logger.info("OMA BER simulasyonu baslatiliyor...")

        for snr_dB in snr_range_dB:
            # OMA: her kullaniciya esit guc, esit BW
            # Efektif SNR = SNR_total / num_users (BW paylasimi)
            oma_snr_dB = snr_dB - 10 * np.log10(num_users)

            user_bers = []
            for u in range(num_users):
                bits = self.tx.generate_random_bits(num_bits)
                symbols = self.tx.modulate(bits)

                # AWGN
                noisy = self.rx.add_awgn(symbols, oma_snr_dB)

                # Dogrudan demodulasyon (interferans yok)
                decoded = self.rx.demodulate(noisy)

                ber = self.rx.calculate_ber(bits, decoded)
                user_bers.append(ber)
                ber_users[u].append(ber)

            ber_average.append(float(np.mean(user_bers)))

        logger.info("OMA BER simulasyonu tamamlandi.")
        return {
            "snr_dB": list(snr_range_dB),
            "ber_users": ber_users,
            "ber_average": ber_average,
        }

    def compare_noma_oma(self, snr_range_dB=None, num_symbols=None):
        """NOMA vs OMA karsilastirma simulasyonu.

        Args:
            snr_range_dB: SNR dizisi.
            num_symbols: Sembol sayisi.

        Returns:
            dict: {"noma": noma_results, "oma": oma_results}
        """
        noma_results = self.simulate_ber_vs_snr(snr_range_dB, num_symbols)
        oma_results = self.simulate_oma_ber_vs_snr(snr_range_dB, num_symbols)
        return {"noma": noma_results, "oma": oma_results}

    # ---- Kapasite Hesaplari ----

    def calculate_capacity_noma(self, snr_dB, power_coefficients=None):
        """NOMA Shannon kapasitesini hesaplar (bit/s/Hz).

        Args:
            snr_dB: SNR degeri (dB)
            power_coefficients: Guc katsayilari. None ise mevcut.

        Returns:
            list: Her kullanicinin kapasitesi [C_user0, C_user1, ...]
        """
        pc = power_coefficients or self.tx.power_coefficients
        snr_linear = 10 ** (snr_dB / 10.0)
        num_users = len(pc)

        # SIC sirasina gore kapasite (gucludan zayifa)
        sorted_pc = sorted(enumerate(pc), key=lambda x: x[1], reverse=True)
        capacities = [0.0] * num_users

        for step, (user_idx, alpha) in enumerate(sorted_pc):
            # Interferans: daha zayif kullanicilardan gelen
            interference = sum(
                sorted_pc[j][1] for j in range(step + 1, num_users)
            )
            sinr = (alpha * snr_linear) / (interference * snr_linear + 1)
            capacities[user_idx] = np.log2(1 + sinr)

        return capacities

    def calculate_capacity_oma(self, snr_dB, num_users=None):
        """OMA Shannon kapasitesini hesaplar (bit/s/Hz).

        Args:
            snr_dB: SNR degeri (dB)
            num_users: Kullanici sayisi. None ise mevcut.

        Returns:
            list: Her kullanicinin kapasitesi
        """
        num_users = num_users or self.tx.num_users
        snr_linear = 10 ** (snr_dB / 10.0)

        # OMA: her kullaniciya 1/K kaynak, esit guc
        capacity_per_user = (1.0 / num_users) * np.log2(1 + snr_linear)
        return [float(capacity_per_user)] * num_users

    def calculate_throughput(self, ber, modulation=None, bandwidth=None):
        """Efektif throughput hesaplar (bit/s).

        Args:
            ber: Bit hata orani
            modulation: Modulasyon tipi
            bandwidth: Bant genisligi (Hz)

        Returns:
            float: Throughput (bit/s)
        """
        modulation = modulation or self.tx.modulation
        bandwidth = bandwidth or config.DEFAULT_SAMPLE_RATE
        bps = config.NOMA_BITS_PER_SYMBOL[modulation]
        return bps * bandwidth * (1 - ber)

    # ---- Grafik Metotlari ----

    def _prepare_plot_dir(self, save_path):
        """Grafik kayit dizinini olusturur."""
        if save_path:
            d = os.path.dirname(save_path)
            if d:
                os.makedirs(d, exist_ok=True)

    def plot_ber_vs_snr(self, results, title=None, save_path=None):
        """BER vs SNR grafigi cizer.

        Args:
            results: simulate_ber_vs_snr() ciktisi
            title: Grafik basligi
            save_path: Kayit yolu (None ise ekranda gosterir)
        """
        self._prepare_plot_dir(save_path)

        fig, ax = plt.subplots(figsize=config.PLOT_FIGURE_SIZE)

        snr = results["snr_dB"]
        colors = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd"]

        for u in range(len(results["ber_users"])):
            ber_data = results["ber_users"][u]
            # Sifir BER degerlerini gosterim icin kucuk bir degere cevir
            ber_plot = [max(b, 1e-7) for b in ber_data]
            ax.semilogy(snr, ber_plot, "o-", markersize=3,
                        label=f"Kullanici {u+1} (a={self.tx.power_coefficients[u]:.2f})",
                        color=colors[u % len(colors)])

        # Ortalama BER
        ber_avg = [max(b, 1e-7) for b in results["ber_average"]]
        ax.semilogy(snr, ber_avg, "k--", linewidth=2, label="Ortalama BER")

        # Teorik QPSK BER referansi
        snr_lin = 10 ** (np.array(snr) / 10.0)
        ber_theory = 0.5 * erfc(np.sqrt(snr_lin))
        ax.semilogy(snr, ber_theory, "g:", linewidth=1.5,
                     label="Teorik QPSK (AWGN)")

        ax.set_xlabel("SNR (dB)", fontsize=config.PLOT_DPI // 12)
        ax.set_ylabel("BER (Bit Hata Orani)", fontsize=config.PLOT_DPI // 12)
        ax.set_title(
            title or f"NOMA BER vs SNR ({self.tx.num_users} Kullanici, {self.tx.modulation})",
            fontsize=14,
        )
        ax.set_ylim(1e-6, 1)
        ax.grid(True, which="both", alpha=0.3)
        ax.legend(fontsize=10)
        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=config.PLOT_DPI)
            logger.info("BER grafigi kaydedildi: %s", save_path)
            plt.close(fig)
        else:
            plt.show()

    def plot_noma_vs_oma_ber(self, comparison_results, save_path=None):
        """NOMA vs OMA BER karsilastirma grafigi.

        Args:
            comparison_results: compare_noma_oma() ciktisi
            save_path: Kayit yolu
        """
        self._prepare_plot_dir(save_path)

        noma = comparison_results["noma"]
        oma = comparison_results["oma"]
        snr = noma["snr_dB"]

        fig, axes = plt.subplots(1, 2, figsize=(16, 7))

        # Sol: Her kullanici icin NOMA vs OMA
        ax1 = axes[0]
        colors_noma = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd"]
        colors_oma = ["#aec7e8", "#ff9896", "#98df8a", "#c5b0d5"]

        for u in range(len(noma["ber_users"])):
            noma_ber = [max(b, 1e-7) for b in noma["ber_users"][u]]
            oma_ber = [max(b, 1e-7) for b in oma["ber_users"][u]]
            ax1.semilogy(snr, noma_ber, "o-", markersize=3,
                         color=colors_noma[u % 4],
                         label=f"NOMA Kullanici {u+1}")
            ax1.semilogy(snr, oma_ber, "s--", markersize=3,
                         color=colors_oma[u % 4],
                         label=f"OMA Kullanici {u+1}")

        ax1.set_xlabel("SNR (dB)")
        ax1.set_ylabel("BER")
        ax1.set_title("Kullanici Bazli BER Karsilastirma")
        ax1.set_ylim(1e-6, 1)
        ax1.grid(True, which="both", alpha=0.3)
        ax1.legend(fontsize=9)

        # Sag: Ortalama BER karsilastirma
        ax2 = axes[1]
        noma_avg = [max(b, 1e-7) for b in noma["ber_average"]]
        oma_avg = [max(b, 1e-7) for b in oma["ber_average"]]
        ax2.semilogy(snr, noma_avg, "b-o", markersize=3, linewidth=2,
                     label="NOMA Ortalama")
        ax2.semilogy(snr, oma_avg, "r--s", markersize=3, linewidth=2,
                     label="OMA Ortalama")
        ax2.set_xlabel("SNR (dB)")
        ax2.set_ylabel("BER")
        ax2.set_title("Ortalama BER Karsilastirma")
        ax2.set_ylim(1e-6, 1)
        ax2.grid(True, which="both", alpha=0.3)
        ax2.legend(fontsize=11)

        plt.suptitle(
            f"NOMA vs OMA ({self.tx.num_users} Kullanici, {self.tx.modulation})",
            fontsize=14, y=1.02,
        )
        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=config.PLOT_DPI, bbox_inches="tight")
            logger.info("NOMA vs OMA BER grafigi kaydedildi: %s", save_path)
            plt.close(fig)
        else:
            plt.show()

    def plot_capacity_comparison(self, snr_range_dB=None, save_path=None):
        """NOMA vs OMA kapasite karsilastirma grafigi.

        Args:
            snr_range_dB: SNR dizisi.
            save_path: Kayit yolu.
        """
        self._prepare_plot_dir(save_path)

        if snr_range_dB is None:
            snr_range_dB = np.arange(
                config.NOMA_SNR_MIN_DB,
                config.NOMA_SNR_MAX_DB + config.NOMA_SNR_STEP_DB,
                config.NOMA_SNR_STEP_DB,
            )

        noma_total = []
        oma_total = []
        noma_per_user = [[] for _ in range(self.tx.num_users)]
        oma_per_user = [[] for _ in range(self.tx.num_users)]

        for snr_dB in snr_range_dB:
            cap_noma = self.calculate_capacity_noma(snr_dB)
            cap_oma = self.calculate_capacity_oma(snr_dB)
            noma_total.append(sum(cap_noma))
            oma_total.append(sum(cap_oma))
            for u in range(self.tx.num_users):
                noma_per_user[u].append(cap_noma[u])
                oma_per_user[u].append(cap_oma[u])

        fig, axes = plt.subplots(1, 2, figsize=(16, 7))

        # Sol: Toplam kapasite
        ax1 = axes[0]
        ax1.plot(snr_range_dB, noma_total, "b-o", markersize=3, linewidth=2,
                 label="NOMA Toplam")
        ax1.plot(snr_range_dB, oma_total, "r--s", markersize=3, linewidth=2,
                 label="OMA Toplam")
        ax1.set_xlabel("SNR (dB)")
        ax1.set_ylabel("Kapasite (bit/s/Hz)")
        ax1.set_title("Toplam Sistem Kapasitesi")
        ax1.grid(True, alpha=0.3)
        ax1.legend(fontsize=11)

        # Sag: Kullanici basi kapasite
        ax2 = axes[1]
        colors = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd"]
        for u in range(self.tx.num_users):
            ax2.plot(snr_range_dB, noma_per_user[u], "-", linewidth=1.5,
                     color=colors[u % 4],
                     label=f"NOMA K{u+1} (a={self.tx.power_coefficients[u]:.2f})")
            ax2.plot(snr_range_dB, oma_per_user[u], "--", linewidth=1.5,
                     color=colors[u % 4], alpha=0.5,
                     label=f"OMA K{u+1}")
        ax2.set_xlabel("SNR (dB)")
        ax2.set_ylabel("Kapasite (bit/s/Hz)")
        ax2.set_title("Kullanici Basi Kapasite")
        ax2.grid(True, alpha=0.3)
        ax2.legend(fontsize=9)

        plt.suptitle(
            f"NOMA vs OMA Kapasite ({self.tx.num_users} Kullanici)",
            fontsize=14, y=1.02,
        )
        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=config.PLOT_DPI, bbox_inches="tight")
            logger.info("Kapasite grafigi kaydedildi: %s", save_path)
            plt.close(fig)
        else:
            plt.show()

    def plot_throughput_comparison(self, snr_range_dB=None, save_path=None):
        """NOMA vs OMA throughput karsilastirma grafigi.

        Args:
            snr_range_dB: SNR dizisi.
            save_path: Kayit yolu.
        """
        self._prepare_plot_dir(save_path)

        if snr_range_dB is None:
            snr_range_dB = np.arange(
                config.NOMA_SNR_MIN_DB,
                config.NOMA_SNR_MAX_DB + config.NOMA_SNR_STEP_DB,
                config.NOMA_SNR_STEP_DB,
            )

        # BER simulasyonlari
        comparison = self.compare_noma_oma(snr_range_dB)
        noma_res = comparison["noma"]
        oma_res = comparison["oma"]

        noma_tput = []
        oma_tput = []

        for i, snr_dB in enumerate(snr_range_dB):
            # Toplam throughput = sum(kullanici throughput)
            noma_t = sum(
                self.calculate_throughput(noma_res["ber_users"][u][i])
                for u in range(self.tx.num_users)
            )
            oma_t = sum(
                self.calculate_throughput(oma_res["ber_users"][u][i])
                / self.tx.num_users  # OMA: BW paylasimi
                for u in range(self.tx.num_users)
            )
            noma_tput.append(noma_t / 1e6)  # Mbit/s
            oma_tput.append(oma_t / 1e6)

        fig, ax = plt.subplots(figsize=config.PLOT_FIGURE_SIZE)
        ax.plot(snr_range_dB, noma_tput, "b-o", markersize=3, linewidth=2,
                label="NOMA")
        ax.plot(snr_range_dB, oma_tput, "r--s", markersize=3, linewidth=2,
                label="OMA")
        ax.set_xlabel("SNR (dB)")
        ax.set_ylabel("Throughput (Mbit/s)")
        ax.set_title(
            f"NOMA vs OMA Throughput ({self.tx.num_users} Kullanici, {self.tx.modulation})"
        )
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=11)
        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=config.PLOT_DPI)
            logger.info("Throughput grafigi kaydedildi: %s", save_path)
            plt.close(fig)
        else:
            plt.show()

    def plot_constellation(self, signal, title=None, save_path=None):
        """Konstelasyon diyagrami cizer.

        Args:
            signal: Kompleks sinyal dizisi
            title: Grafik basligi
            save_path: Kayit yolu
        """
        self._prepare_plot_dir(save_path)

        fig, ax = plt.subplots(figsize=(8, 8))

        ax.scatter(signal.real, signal.imag, s=2, alpha=0.3, color="#1f77b4",
                   label="Alinan")

        # Ideal konstelasyon noktalari
        ideal = self.tx.constellation
        ax.scatter(ideal.real, ideal.imag, s=80, marker="x", color="red",
                   linewidths=2, label="Ideal", zorder=5)

        ax.set_xlabel("In-Phase (I)")
        ax.set_ylabel("Quadrature (Q)")
        ax.set_title(title or f"Konstelasyon Diyagrami ({self.tx.modulation})")
        ax.grid(True, alpha=0.3)
        ax.legend()
        ax.set_aspect("equal")
        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=config.PLOT_DPI)
            plt.close(fig)
        else:
            plt.show()

    def plot_power_allocation(self, save_path=None):
        """Guc tahsis diyagrami cizer.

        Args:
            save_path: Kayit yolu
        """
        self._prepare_plot_dir(save_path)

        pc = self.tx.power_coefficients
        labels = [f"Kullanici {i+1}\n(a={pc[i]:.2f})" for i in range(len(pc))]
        colors = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd"][:len(pc)]

        fig, axes = plt.subplots(1, 2, figsize=(14, 6))

        # Bar chart
        ax1 = axes[0]
        bars = ax1.bar(labels, pc, color=colors, edgecolor="black", linewidth=0.5)
        for bar, val in zip(bars, pc):
            ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                     f"{val*100:.0f}%", ha="center", fontsize=12)
        ax1.set_ylabel("Guc Katsayisi")
        ax1.set_title("Guc Tahsisi (Bar)")
        ax1.set_ylim(0, 1)
        ax1.grid(True, axis="y", alpha=0.3)

        # Pasta grafik
        ax2 = axes[1]
        ax2.pie(pc, labels=labels, colors=colors, autopct="%1.0f%%",
                startangle=90, textprops={"fontsize": 11})
        ax2.set_title("Guc Dagalimi (Pasta)")

        plt.suptitle(
            f"NOMA Guc Tahsisi ({len(pc)} Kullanici)", fontsize=14, y=1.02,
        )
        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=config.PLOT_DPI, bbox_inches="tight")
            logger.info("Guc tahsis grafigi kaydedildi: %s", save_path)
            plt.close(fig)
        else:
            plt.show()

    def plot_sic_stages(self, received_signal, save_path=None):
        """SIC'in her asamasindaki sinyal konstelasyonunu gosterir.

        Args:
            received_signal: Alinan sinyal (SIC cozumlemesi uygulanir)
            save_path: Kayit yolu
        """
        self._prepare_plot_dir(save_path)

        # SIC calistir (ara sinyaller kaydedilir)
        self.rx.sic_decode(received_signal)
        stages = getattr(self.rx, "_last_sic_stages", [])

        n_stages = len(stages)
        if n_stages == 0:
            logger.warning("SIC asamasi verisi bulunamadi.")
            return

        fig, axes = plt.subplots(1, n_stages + 1, figsize=(6 * (n_stages + 1), 6))
        if n_stages == 0:
            axes = [axes]

        # Orijinal alinan sinyal
        ax = axes[0]
        ax.scatter(received_signal.real, received_signal.imag, s=2, alpha=0.3)
        ax.set_title("Alinan Sinyal")
        ax.grid(True, alpha=0.3)
        ax.set_aspect("equal")

        # SIC asamalari
        for i, stage_sig in enumerate(stages):
            ax = axes[i + 1]
            ax.scatter(stage_sig.real, stage_sig.imag, s=2, alpha=0.3)
            ax.set_title(f"SIC Asama {i+1}\n(Kullanici {i+1} cozuluyor)")
            ax.grid(True, alpha=0.3)
            ax.set_aspect("equal")

        plt.suptitle("SIC Asamalari Konstelasyonlari", fontsize=14, y=1.02)
        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=config.PLOT_DPI, bbox_inches="tight")
            logger.info("SIC asamalari grafigi kaydedildi: %s", save_path)
            plt.close(fig)
        else:
            plt.show()

    def generate_full_report(self, save_dir=None):
        """Tum analiz grafiklerini ve sonuc dosyalarini uretir.

        Args:
            save_dir: Cikti dizini. None ise config'den.
        """
        save_dir = save_dir or config.PLOT_OUTPUT_DIR
        os.makedirs(save_dir, exist_ok=True)

        logger.info("Tam rapor olusturuluyor: %s", save_dir)

        # 1. NOMA BER vs SNR
        noma_results = self.simulate_ber_vs_snr()
        self.plot_ber_vs_snr(
            noma_results,
            save_path=os.path.join(save_dir, "noma_ber_vs_snr.png"),
        )

        # 2. NOMA vs OMA BER
        comparison = self.compare_noma_oma()
        self.plot_noma_vs_oma_ber(
            comparison,
            save_path=os.path.join(save_dir, "noma_vs_oma_ber.png"),
        )

        # 3. Kapasite karsilastirma
        self.plot_capacity_comparison(
            save_path=os.path.join(save_dir, "capacity_comparison.png"),
        )

        # 4. Throughput karsilastirma
        self.plot_throughput_comparison(
            save_path=os.path.join(save_dir, "throughput_comparison.png"),
        )

        # 5. Guc tahsis
        self.plot_power_allocation(
            save_path=os.path.join(save_dir, "power_allocation.png"),
        )

        # 6. Konstelasyon diyagramlari
        combined, orig_bits, _ = self.tx.transmit_frame(num_bits=4096)
        noisy = self.rx.add_awgn(combined, 20.0)

        self.plot_constellation(
            combined,
            title="TX Superposition Coded Sinyal",
            save_path=os.path.join(save_dir, "constellation_tx.png"),
        )
        self.plot_constellation(
            noisy,
            title="RX Alinan Sinyal (SNR=20 dB)",
            save_path=os.path.join(save_dir, "constellation_rx.png"),
        )

        # 7. SIC asamalari
        self.plot_sic_stages(
            noisy,
            save_path=os.path.join(save_dir, "sic_stages.png"),
        )

        # 8. Sonuclari CSV'ye kaydet
        self._export_results_csv(noma_results, comparison, save_dir)

        logger.info("Tam rapor olusturuldu: %s", save_dir)

    def _export_results_csv(self, noma_results, comparison, save_dir):
        """Simulasyon sonuclarini CSV dosyalarina kaydeder."""
        # NOMA BER sonuclari
        csv_path = os.path.join(save_dir, "noma_ber_results.csv")
        with open(csv_path, "w") as f:
            header = "SNR_dB"
            for u in range(self.tx.num_users):
                header += f",BER_User{u+1}"
            header += ",BER_Average\n"
            f.write(header)

            for i, snr in enumerate(noma_results["snr_dB"]):
                line = f"{snr}"
                for u in range(self.tx.num_users):
                    line += f",{noma_results['ber_users'][u][i]:.8f}"
                line += f",{noma_results['ber_average'][i]:.8f}\n"
                f.write(line)

        # Kapasite sonuclari
        csv_path = os.path.join(save_dir, "capacity_results.csv")
        snr_range = np.arange(
            config.NOMA_SNR_MIN_DB,
            config.NOMA_SNR_MAX_DB + config.NOMA_SNR_STEP_DB,
            config.NOMA_SNR_STEP_DB,
        )
        with open(csv_path, "w") as f:
            f.write("SNR_dB,NOMA_Total,OMA_Total\n")
            for snr_dB in snr_range:
                cap_noma = sum(self.calculate_capacity_noma(snr_dB))
                cap_oma = sum(self.calculate_capacity_oma(snr_dB))
                f.write(f"{snr_dB},{cap_noma:.6f},{cap_oma:.6f}\n")

        logger.info("CSV sonuclari kaydedildi: %s", save_dir)
