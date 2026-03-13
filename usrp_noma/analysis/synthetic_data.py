"""
Sentetik IQ Veri Uretici

USRP E310 olmadan test ve egitim verisi olusturmak icin
sentetik IQ sinyal uretimi. Farkli sinyal tiplerini (LoRa, LTE, WiFi,
gurultu, NOMA) cesitli SNR seviyelerinde uretir.
"""

import os

import numpy as np

from usrp_noma import config
from usrp_noma.utils import setup_logger, save_iq_data

logger = setup_logger("SyntheticData")


class SyntheticDataGenerator:
    """Makine ogrenimi egitimi icin sentetik IQ verisi uretir.

    Desteklenen sinyal tipleri:
    - LoRa (CSS — Chirp Spread Spectrum)
    - NOMA (Superposition coded)
    - CW (Continuous Wave — tek ton)
    - OFDM (basitlestirilmis)
    - Gurultu (AWGN)
    """

    SIGNAL_TYPES = ["lora", "noma", "cw", "ofdm", "noise"]

    def __init__(self, sample_rate=None):
        self.sample_rate = sample_rate or config.DEFAULT_SAMPLE_RATE
        self.logger = logger

    def generate_lora_signal(self, num_samples, sf=7, bw=125e3, snr_dB=15):
        """LoRa CSS sinyali uretir.

        Args:
            num_samples: Ornek sayisi
            sf: Spreading Factor (7-12)
            bw: Bant genisligi (Hz)
            snr_dB: Sinyal-Gurultu Orani (dB)

        Returns:
            ndarray: Kompleks IQ sinyal
        """
        n_symbols = 2 ** sf
        symbol_duration = n_symbols / bw
        samples_per_symbol = int(symbol_duration * self.sample_rate)

        signal = np.array([], dtype=np.complex64)

        while len(signal) < num_samples:
            # Rastgele sembol degeri
            symbol_val = np.random.randint(0, n_symbols)

            t = np.arange(samples_per_symbol) / self.sample_rate
            f0 = -bw / 2
            chirp_rate = bw / symbol_duration

            # Sembol kaydirmali chirp
            freq_offset = (symbol_val / n_symbols) * bw
            freq = f0 + freq_offset + chirp_rate * t
            freq = np.mod(freq + bw / 2, bw) - bw / 2  # wrap

            phase = 2 * np.pi * np.cumsum(freq) / self.sample_rate
            chirp = np.exp(1j * phase).astype(np.complex64)
            signal = np.concatenate([signal, chirp])

        signal = signal[:num_samples]
        signal = signal / (np.sqrt(np.mean(np.abs(signal) ** 2)) + 1e-12)

        return self._add_awgn(signal, snr_dB)

    def generate_noma_signal(self, num_samples, num_users=2, modulation="QPSK", snr_dB=15):
        """NOMA Superposition Coded sinyal uretir.

        Args:
            num_samples: Ornek sayisi
            num_users: Kullanici sayisi (2-4)
            modulation: Modulasyon tipi
            snr_dB: SNR (dB)

        Returns:
            ndarray: Kompleks IQ sinyal
        """
        from usrp_noma.noma import NOMATransmitter

        tx = NOMATransmitter(num_users=num_users, modulation=modulation)
        bits_per_sym = config.NOMA_BITS_PER_SYMBOL[modulation]

        signal = np.array([], dtype=np.complex64)

        while len(signal) < num_samples:
            n_bits = max(bits_per_sym * 256, 1024)
            combined, _, _ = tx.transmit_frame(num_bits=n_bits)
            # Upsample
            upsampled = np.repeat(combined, max(1, 4))
            signal = np.concatenate([signal, upsampled.astype(np.complex64)])

        signal = signal[:num_samples]
        signal = signal / (np.sqrt(np.mean(np.abs(signal) ** 2)) + 1e-12)

        return self._add_awgn(signal, snr_dB)

    def generate_cw_signal(self, num_samples, freq_offset=10e3, snr_dB=15):
        """Tek ton (CW) sinyal uretir.

        Args:
            num_samples: Ornek sayisi
            freq_offset: Frekans ofseti (Hz)
            snr_dB: SNR (dB)

        Returns:
            ndarray: Kompleks IQ sinyal
        """
        t = np.arange(num_samples) / self.sample_rate
        signal = np.exp(1j * 2 * np.pi * freq_offset * t).astype(np.complex64)
        return self._add_awgn(signal, snr_dB)

    def generate_ofdm_signal(self, num_samples, n_carriers=64, cp_len=16, snr_dB=15):
        """Basitlestirilmis OFDM sinyali uretir.

        Args:
            num_samples: Ornek sayisi
            n_carriers: Alt tasiyici sayisi
            cp_len: Cyclic prefix uzunlugu
            snr_dB: SNR (dB)

        Returns:
            ndarray: Kompleks IQ sinyal
        """
        symbol_len = n_carriers + cp_len

        signal = np.array([], dtype=np.complex64)

        while len(signal) < num_samples:
            # Rastgele QPSK semboller
            data = (np.random.choice([-1, 1], n_carriers) + 1j * np.random.choice([-1, 1], n_carriers)) / np.sqrt(2)

            # IFFT
            time_domain = np.fft.ifft(data, n=n_carriers)

            # Cyclic prefix ekle
            cp = time_domain[-cp_len:]
            ofdm_symbol = np.concatenate([cp, time_domain]).astype(np.complex64)
            signal = np.concatenate([signal, ofdm_symbol])

        signal = signal[:num_samples]
        signal = signal / (np.sqrt(np.mean(np.abs(signal) ** 2)) + 1e-12)

        return self._add_awgn(signal, snr_dB)

    def generate_noise(self, num_samples):
        """Saf AWGN gurultusu uretir.

        Args:
            num_samples: Ornek sayisi

        Returns:
            ndarray: Kompleks gurultu
        """
        noise = (np.random.randn(num_samples) + 1j * np.random.randn(num_samples)) / np.sqrt(2)
        return noise.astype(np.complex64)

    def _add_awgn(self, signal, snr_dB):
        """Sinyale belirtilen SNR'da AWGN ekler."""
        sig_power = np.mean(np.abs(signal) ** 2)
        noise_power = sig_power / (10 ** (snr_dB / 10))
        noise = np.sqrt(noise_power / 2) * (np.random.randn(len(signal)) + 1j * np.random.randn(len(signal)))
        return (signal + noise).astype(np.complex64)

    def generate_dataset(self, samples_per_class=200, num_samples_per_signal=4096,
                         snr_range_dB=None, save_dir=None):
        """Sinif basina belirtilen sayida IQ verisi uretir.

        Args:
            samples_per_class: Her sinif basina uretilecek ornek
            num_samples_per_signal: Her sinyaldeki IQ ornek sayisi
            snr_range_dB: SNR degerleri listesi. None ise [0, 5, 10, 15, 20, 25]
            save_dir: Veri kayit dizini

        Returns:
            tuple: (data, labels, snrs, class_names)
                data: (N, num_samples_per_signal) kompleks matris
                labels: (N,) sinif indeksleri
                snrs: (N,) her ornekteki SNR degeri
                class_names: sinif isimleri listesi
        """
        if snr_range_dB is None:
            snr_range_dB = [0, 5, 10, 15, 20, 25]

        class_names = self.SIGNAL_TYPES
        n_classes = len(class_names)
        samples_per_snr = max(1, samples_per_class // len(snr_range_dB))
        total = n_classes * len(snr_range_dB) * samples_per_snr

        data = np.zeros((total, num_samples_per_signal), dtype=np.complex64)
        labels = np.zeros(total, dtype=np.int64)
        snrs = np.zeros(total, dtype=np.float32)

        idx = 0
        for class_idx, sig_type in enumerate(class_names):
            for snr in snr_range_dB:
                for _ in range(samples_per_snr):
                    if sig_type == "lora":
                        sf = np.random.choice([7, 8, 9, 10])
                        iq = self.generate_lora_signal(num_samples_per_signal, sf=sf, snr_dB=snr)
                    elif sig_type == "noma":
                        users = np.random.choice([2, 3])
                        iq = self.generate_noma_signal(num_samples_per_signal, num_users=users, snr_dB=snr)
                    elif sig_type == "cw":
                        fo = np.random.uniform(5e3, 50e3)
                        iq = self.generate_cw_signal(num_samples_per_signal, freq_offset=fo, snr_dB=snr)
                    elif sig_type == "ofdm":
                        iq = self.generate_ofdm_signal(num_samples_per_signal, snr_dB=snr)
                    elif sig_type == "noise":
                        iq = self.generate_noise(num_samples_per_signal)
                    else:
                        iq = self.generate_noise(num_samples_per_signal)

                    data[idx] = iq
                    labels[idx] = class_idx
                    snrs[idx] = snr
                    idx += 1

            self.logger.info(f"Sinif '{sig_type}' uretildi: {len(snr_range_dB) * samples_per_snr} ornek")

        self.logger.info(f"Toplam veri seti: {total} ornek, {n_classes} sinif")

        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
            np.save(os.path.join(save_dir, "iq_dataset.npy"), data)
            np.save(os.path.join(save_dir, "labels.npy"), labels)
            np.save(os.path.join(save_dir, "snrs.npy"), snrs)

            # Metadata
            with open(os.path.join(save_dir, "dataset_info.meta"), "w") as f:
                f.write(f"sample_rate={self.sample_rate}\n")
                f.write(f"num_samples_per_signal={num_samples_per_signal}\n")
                f.write(f"total_samples={total}\n")
                f.write(f"classes={','.join(class_names)}\n")
                f.write(f"snr_range={','.join(str(s) for s in snr_range_dB)}\n")
                f.write(f"samples_per_class={samples_per_class}\n")

            self.logger.info(f"Veri seti kaydedildi: {save_dir}")

        return data, labels, snrs, class_names
