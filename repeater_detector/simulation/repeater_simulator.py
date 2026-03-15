"""
Kacak Repeater Tespit Sistemi - Sentetik Sinyal Uretici

Donanimsiz test ve demo icin sentetik repeater sinyalleri,
yasal sinyaller ve karisik senaryolar uretir.
GNU Radio kayitlariyla ayni formatta (complex64) cikti verir.
"""

import numpy as np

from usrp_noma.utils import setup_logger, linear_to_dB
from repeater_detector import config as det_config


logger = setup_logger("repeater_detector.simulation")


class RepeaterSimulator:
    """
    Sentetik repeater sinyali uretici.

    Gercekci bir spektrum ortami simule eder:
    - Bilinen yasal sinyaller (GSM, LTE, WiFi benzeri)
    - Kacak repeater sinyalleri (dar bant FM, DMR benzeri)
    - Arka plan gurultusu (AWGN)
    """

    def __init__(self, sample_rate=None, noise_floor_dBm=None):
        """
        Args:
            sample_rate: Ornekleme hizi (Hz). None ise config'den.
            noise_floor_dBm: Gurultu tabani (dBm). None ise config'den.
        """
        self.sample_rate = sample_rate or det_config.SIM_DEFAULT_SAMPLE_RATE
        self.noise_floor_dBm = noise_floor_dBm or det_config.SIM_NOISE_FLOOR_DBM
        self.logger = setup_logger("RepeaterSimulator")

    def generate_repeater_signal(self, num_samples, freq_offset=0,
                                 power_dBm=-30, modulation="fm",
                                 deviation_hz=5e3):
        """
        Tipik bir repeater sinyali uretir.

        Args:
            num_samples: Ornek sayisi
            freq_offset: Merkez frekanstan ofset (Hz)
            power_dBm: Sinyal gucu (dBm)
            modulation: Modulasyon tipi ("fm", "dmr")
            deviation_hz: FM frekans sapma (Hz)

        Returns:
            np.ndarray: Kompleks IQ sinyal (complex64)
        """
        t = np.arange(num_samples) / self.sample_rate

        if modulation == "fm":
            # Basit ses sinyali (coklu tonlu, gercekci)
            audio_freq1 = np.random.uniform(300, 1000)
            audio_freq2 = np.random.uniform(1000, 3000)
            audio = (0.6 * np.sin(2 * np.pi * audio_freq1 * t) +
                     0.4 * np.sin(2 * np.pi * audio_freq2 * t))

            # FM modulasyon: faz = 2*pi * integral(f_offset + deviation * audio)
            inst_freq = freq_offset + deviation_hz * audio
            phase = 2 * np.pi * np.cumsum(inst_freq) / self.sample_rate
            signal = np.exp(1j * phase)

        elif modulation == "dmr":
            # 4FSK (DMR benzeri): 4 sembol seviyesi
            symbol_rate = 4800  # DMR sembol hizi
            samples_per_symbol = max(1, int(self.sample_rate / symbol_rate))
            num_symbols = num_samples // samples_per_symbol + 1
            symbols = np.random.choice([-3, -1, 1, 3], size=num_symbols)
            symbols_up = np.repeat(symbols, samples_per_symbol)[:num_samples]

            deviation = 1944  # DMR tipik sapma (Hz)
            inst_freq = freq_offset + deviation * symbols_up / 3.0
            phase = 2 * np.pi * np.cumsum(inst_freq) / self.sample_rate
            signal = np.exp(1j * phase)

        else:
            # Basit CW (ton sinyali)
            phase = 2 * np.pi * freq_offset * t
            signal = np.exp(1j * phase)

        # Guc normalizasyonu
        signal = self._set_signal_power(signal, power_dBm)

        return signal.astype(np.complex64)

    def generate_legal_signal(self, num_samples, signal_type="gsm",
                              power_dBm=-50, freq_offset=0):
        """
        Bilinen yasal sinyal tipini taklit eden sentetik sinyal uretir.

        Args:
            num_samples: Ornek sayisi
            signal_type: "gsm", "lte", "wifi", "lora", "cw"
            power_dBm: Sinyal gucu (dBm)
            freq_offset: Merkez frekanstan ofset (Hz)

        Returns:
            np.ndarray: Kompleks IQ sinyal (complex64)
        """
        t = np.arange(num_samples) / self.sample_rate

        if signal_type == "gsm":
            # GMSK benzeri: dar bant dijital sinyal (~200 kHz BW)
            symbol_rate = 270833  # GSM sembol hizi
            sps = max(1, int(self.sample_rate / symbol_rate))
            num_syms = num_samples // sps + 1
            bits = np.random.choice([-1, 1], size=num_syms)
            bits_up = np.repeat(bits, sps)[:num_samples]
            # Gaussian filtreleme (basitlestirilmis)
            from scipy.ndimage import gaussian_filter1d
            filtered = gaussian_filter1d(bits_up.astype(float), sigma=sps * 0.3)
            phase = 2 * np.pi * np.cumsum(
                freq_offset + filtered * 67708
            ) / self.sample_rate
            signal = np.exp(1j * phase)

        elif signal_type == "lte":
            # OFDM benzeri: genis bant, duz spektrum
            num_subcarriers = 64
            symbols_per_carrier = num_samples // num_subcarriers + 1
            # Rastgele QPSK semboller her alt tasiyicida
            qpsk = np.exp(1j * np.pi / 4 * np.random.choice([1, 3, 5, 7],
                          size=(symbols_per_carrier, num_subcarriers)))
            ofdm_time = np.fft.ifft(qpsk, axis=1)
            signal = ofdm_time.flatten()[:num_samples]
            # Frekans kaydirmasi
            signal = signal * np.exp(1j * 2 * np.pi * freq_offset * t)

        elif signal_type == "wifi":
            # WiFi benzeri: genis bant burst
            # OFDM + burst kalıbı
            num_subcarriers = 64
            burst_len = int(0.005 * self.sample_rate)  # 5ms burst
            silence_len = int(0.002 * self.sample_rate)  # 2ms suskunluk
            signal = np.zeros(num_samples, dtype=np.complex128)
            pos = 0
            while pos < num_samples:
                # Burst
                blen = min(burst_len, num_samples - pos)
                syms = blen // num_subcarriers + 1
                qpsk = np.exp(1j * np.pi / 4 * np.random.choice([1, 3, 5, 7],
                              size=(syms, num_subcarriers)))
                burst = np.fft.ifft(qpsk, axis=1).flatten()[:blen]
                signal[pos:pos + blen] = burst
                pos += blen
                # Suskunluk
                slen = min(silence_len, num_samples - pos)
                pos += slen
            signal = signal * np.exp(1j * 2 * np.pi * freq_offset * t)

        elif signal_type == "lora":
            # LoRa CSS benzeri: chirp spread spectrum
            sf = 7
            bw = 125e3
            chirp_len = int((2 ** sf / bw) * self.sample_rate)
            if chirp_len < 1:
                chirp_len = 1
            signal = np.zeros(num_samples, dtype=np.complex128)
            pos = 0
            while pos + chirp_len <= num_samples:
                chirp_t = np.arange(chirp_len) / self.sample_rate
                f0 = -bw / 2 + freq_offset
                f1 = bw / 2 + freq_offset
                chirp_rate = (f1 - f0) / (chirp_len / self.sample_rate)
                phase = 2 * np.pi * (f0 * chirp_t + chirp_rate / 2 * chirp_t ** 2)
                signal[pos:pos + chirp_len] = np.exp(1j * phase)
                pos += chirp_len

        else:  # cw
            phase = 2 * np.pi * freq_offset * t
            signal = np.exp(1j * phase)

        signal = self._set_signal_power(signal, power_dBm)
        return signal.astype(np.complex64)

    def generate_noise(self, num_samples, power_dBm=None):
        """
        AWGN (Additive White Gaussian Noise) uretir.

        Args:
            num_samples: Ornek sayisi
            power_dBm: Gurultu gucu (dBm). None ise noise_floor.

        Returns:
            np.ndarray: Kompleks gurultu (complex64)
        """
        if power_dBm is None:
            power_dBm = self.noise_floor_dBm

        # Guc: P = sigma^2
        power_linear = 10 ** ((power_dBm - 30) / 10.0)
        sigma = np.sqrt(power_linear / 2.0)
        noise = sigma * (np.random.randn(num_samples) +
                         1j * np.random.randn(num_samples))
        return noise.astype(np.complex64)

    def generate_scenario(self, duration_sec=1.0, num_legal=None,
                          num_illegal=None, center_freq=900e6,
                          illegal_freq_offsets=None,
                          illegal_powers_dBm=None):
        """
        Yasal + kacak sinyallerin bir arada oldugu tam senaryo uretir.

        Args:
            duration_sec: Senaryo suresi (saniye)
            num_legal: Yasal sinyal sayisi. None ise config'den.
            num_illegal: Kacak sinyal sayisi. None ise config'den.
            center_freq: Merkez frekans (Hz)
            illegal_freq_offsets: Kacak sinyal frekans ofsetleri (Hz listesi)
            illegal_powers_dBm: Kacak sinyal guc seviyeleri (dBm listesi)

        Returns:
            dict: {
                "iq_data": np.ndarray,
                "sample_rate": float,
                "center_freq": float,
                "duration_sec": float,
                "legal_signals": list[dict],
                "illegal_signals": list[dict],
                "noise_floor_dBm": float,
                "ground_truth": dict,
            }
        """
        if num_legal is None:
            num_legal = det_config.SIM_NUM_LEGAL_SIGNALS
        if num_illegal is None:
            num_illegal = det_config.SIM_NUM_ILLEGAL_SIGNALS

        num_samples = int(duration_sec * self.sample_rate)

        # Arka plan gurultusu
        combined = self.generate_noise(num_samples)

        # ---- Yasal sinyaller ----
        legal_signals = []
        legal_types = ["gsm", "lte", "wifi", "lora", "cw"]
        for i in range(num_legal):
            sig_type = legal_types[i % len(legal_types)]
            # Yasal sinyaller farkli frekanslarda
            freq_offset = np.random.uniform(-self.sample_rate / 3,
                                            self.sample_rate / 3)
            power = np.random.uniform(-60, -40)
            sig = self.generate_legal_signal(
                num_samples, signal_type=sig_type,
                power_dBm=power, freq_offset=freq_offset)
            combined = combined + sig
            legal_signals.append({
                "freq": center_freq + freq_offset,
                "freq_offset": freq_offset,
                "power_dBm": power,
                "type": sig_type,
                "label": "yasal",
            })

        # ---- Kacak sinyaller ----
        illegal_signals = []
        for i in range(num_illegal):
            if illegal_freq_offsets and i < len(illegal_freq_offsets):
                freq_offset = illegal_freq_offsets[i]
            else:
                # Bilinen frekanslardan uzak rastgele ofset
                freq_offset = np.random.uniform(-self.sample_rate / 4,
                                                self.sample_rate / 4)

            if illegal_powers_dBm and i < len(illegal_powers_dBm):
                power = illegal_powers_dBm[i]
            else:
                power = np.random.uniform(-45, -25)

            modulation = np.random.choice(["fm", "dmr"])
            sig = self.generate_repeater_signal(
                num_samples, freq_offset=freq_offset,
                power_dBm=power, modulation=modulation)
            combined = combined + sig
            illegal_signals.append({
                "freq": center_freq + freq_offset,
                "freq_offset": freq_offset,
                "power_dBm": power,
                "modulation": modulation,
                "type": "repeater",
                "label": "kacak",
            })

        self.logger.info(
            "Senaryo uretildi: %d yasal + %d kacak sinyal, %.1f saniye",
            num_legal, num_illegal, duration_sec)

        return {
            "iq_data": combined.astype(np.complex64),
            "sample_rate": self.sample_rate,
            "center_freq": center_freq,
            "duration_sec": duration_sec,
            "legal_signals": legal_signals,
            "illegal_signals": illegal_signals,
            "noise_floor_dBm": self.noise_floor_dBm,
            "ground_truth": {
                "total_legal": num_legal,
                "total_illegal": num_illegal,
                "all_signals": legal_signals + illegal_signals,
            },
        }

    def simulate_rssi_profile(self, true_angle_deg, num_points=None,
                              beam_width_deg=60, peak_rssi_dBm=-40,
                              noise_std_dB=2.0):
        """
        Yon bulma testi icin sentetik RSSI profili uretir.
        Gaussian huzme deseni + olcum gurultusu modeli.

        Args:
            true_angle_deg: Gercek sinyal yonu (derece, 0-360)
            num_points: Olcum noktasi sayisi. None ise config'den.
            beam_width_deg: Anten huzme genisligi (derece)
            peak_rssi_dBm: Tepe RSSI degeri (dBm)
            noise_std_dB: RSSI olcum gurultusu standart sapma (dB)

        Returns:
            list[dict]: [{"angle_deg": float, "rssi_dBm": float}, ...]
        """
        if num_points is None:
            num_points = det_config.DF_NUM_MEASUREMENTS

        angles = np.linspace(0, 360, num_points, endpoint=False)
        measurements = []

        for angle in angles:
            # Dairesel Gaussian fark hesabi
            diff = angle - true_angle_deg
            # -180 ile 180 arasina normalize et
            diff = (diff + 180) % 360 - 180

            # Gaussian huzme deseni: RSSI = peak - (diff / sigma)^2
            sigma = beam_width_deg / (2 * np.sqrt(2 * np.log(2)))  # 3dB -> sigma
            beam_attenuation = (diff / sigma) ** 2
            rssi = peak_rssi_dBm - beam_attenuation

            # Olcum gurultusu ekle
            rssi += np.random.normal(0, noise_std_dB)

            # Gurultu tabaninin altina dusmesini onle
            rssi = max(rssi, self.noise_floor_dBm + 5)

            measurements.append({
                "angle_deg": float(angle),
                "rssi_dBm": float(rssi),
            })

        return measurements

    def simulate_distance_measurements(self, true_distance_m, frequency_hz,
                                       num_measurements=10,
                                       environment="kentsel"):
        """
        Mesafe tahmini testi icin sentetik RSSI olcumleri uretir.
        Log-distance yol kaybi modeli + log-normal golgeleme.

        Args:
            true_distance_m: Gercek mesafe (metre)
            frequency_hz: Calisma frekansi (Hz)
            num_measurements: Olcum sayisi
            environment: Ortam tipi

        Returns:
            dict: {
                "rssi_measurements": list[float],
                "true_distance_m": float,
                "true_path_loss_dB": float,
                "environment": str,
                "frequency_hz": float,
            }
        """
        env = det_config.ENVIRONMENT_MODELS[environment]
        n = env["n"]
        sigma = env["sigma"]

        # Referans mesafedeki yol kaybi (FSPL, d0=1m)
        wavelength = det_config.SPEED_OF_LIGHT / frequency_hz
        pl_d0 = 20 * np.log10(4 * np.pi * det_config.PATH_LOSS_D0 / wavelength)

        # Gercek yol kaybi
        true_pl = pl_d0 + 10 * n * np.log10(
            max(true_distance_m, 0.1) / det_config.PATH_LOSS_D0)

        # Alinan guc (dBm)
        true_rssi = (det_config.TX_POWER_DBM + det_config.TX_ANTENNA_GAIN_DBI +
                     det_config.RX_ANTENNA_GAIN_DBI - det_config.CABLE_LOSS_DB -
                     true_pl)

        # Log-normal golgeleme ile coklu olcum
        rssi_measurements = []
        for _ in range(num_measurements):
            shadowing = np.random.normal(0, sigma)
            rssi = true_rssi + shadowing
            rssi_measurements.append(float(rssi))

        return {
            "rssi_measurements": rssi_measurements,
            "true_distance_m": true_distance_m,
            "true_path_loss_dB": true_pl,
            "true_rssi_dBm": true_rssi,
            "environment": environment,
            "frequency_hz": frequency_hz,
        }

    def _set_signal_power(self, signal, target_power_dBm):
        """
        Sinyalin gucunu hedef seviyeye ayarlar.

        Args:
            signal: Kompleks sinyal dizisi
            target_power_dBm: Hedef guc (dBm)

        Returns:
            np.ndarray: Guc ayarlanmis sinyal
        """
        current_power = np.mean(np.abs(signal) ** 2)
        if current_power < 1e-20:
            return signal

        target_power_linear = 10 ** ((target_power_dBm - 30) / 10.0)
        scale = np.sqrt(target_power_linear / current_power)
        return signal * scale
