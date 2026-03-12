"""
NOMA Alici (Receiver)

SIC (Successive Interference Cancellation) ile kullanici sinyallerini ayristirir.
"""

import numpy as np

from usrp_noma import config
from usrp_noma.utils import setup_logger
from usrp_noma.noma.modulation import CONSTELLATIONS
from usrp_noma.noma.transmitter import NOMATransmitter

logger = setup_logger("NOMA.RX")


class NOMAReceiver:
    """NOMA Alici: SIC ile kullanici sinyallerini ayristirir."""

    def __init__(self, num_users=None, power_coefficients=None,
                 modulation=None):
        """NOMAReceiver baslatir.

        Args:
            num_users: Kullanici sayisi.
            power_coefficients: Guc katsayilari (verici ile ayni olmali).
            modulation: Modulasyon tipi.
        """
        self.num_users = num_users or config.NOMA_NUM_USERS
        self.modulation = modulation or config.NOMA_DEFAULT_MODULATION
        self.bits_per_symbol = config.NOMA_BITS_PER_SYMBOL[self.modulation]
        self.constellation = CONSTELLATIONS[self.modulation]

        if power_coefficients is not None:
            self.power_coefficients = list(power_coefficients)
        else:
            self.power_coefficients = list(
                config.NOMA_POWER_COEFFICIENTS[self.num_users]
            )

        # Verici referansi (remodulasyon icin)
        self._tx = NOMATransmitter(
            num_users=self.num_users,
            power_coefficients=self.power_coefficients,
            modulation=self.modulation,
        )

        logger.info(
            "NOMAReceiver: %d kullanici, mod=%s, guc=%s",
            self.num_users, self.modulation, self.power_coefficients,
        )

    def add_awgn(self, signal, snr_dB):
        """Sinyale AWGN (Additive White Gaussian Noise) ekler.

        Args:
            signal: Kompleks sinyal dizisi
            snr_dB: Sinyal-gurultu orani (dB)

        Returns:
            np.ndarray: Gurultulu sinyal
        """
        signal_power = np.mean(np.abs(signal) ** 2)
        noise_power = signal_power / (10 ** (snr_dB / 10.0))
        noise = np.sqrt(noise_power / 2) * (
            np.random.randn(len(signal)) + 1j * np.random.randn(len(signal))
        )
        return signal + noise

    def estimate_snr(self, signal):
        """Alinan sinyalin SNR'ini tahmin eder.

        Args:
            signal: Kompleks sinyal dizisi

        Returns:
            float: Tahmin edilen SNR (dB)
        """
        # Beklenen konstelasyon noktalarindan sapma ile tahmin
        min_distances = np.zeros(len(signal))
        for i, s in enumerate(signal):
            distances = np.abs(s - self.constellation)
            min_distances[i] = np.min(distances) ** 2

        noise_var = np.mean(min_distances)
        signal_power = np.mean(np.abs(signal) ** 2)

        if noise_var > 0:
            snr = signal_power / noise_var
            return 10 * np.log10(max(snr, 1e-12))
        return 100.0

    def demodulate(self, symbols):
        """Sembolleri bitlere cozumler (Maximum Likelihood).

        Args:
            symbols: Kompleks sembol dizisi

        Returns:
            np.ndarray: Cozulen bit dizisi
        """
        bits = np.zeros(len(symbols) * self.bits_per_symbol, dtype=int)
        for i, sym in enumerate(symbols):
            sym_bits = self._tx.demodulate_to_bits(sym, self.constellation)
            bits[i * self.bits_per_symbol:(i + 1) * self.bits_per_symbol] = sym_bits
        return bits

    def sic_decode(self, received_signal):
        """SIC (Successive Interference Cancellation) algoritmasi.

        En guclu kullanicidan baslayarak sirayla cozumler:
        1. r sinyalinden en guclu kullaniciyi coz
        2. Cozulen sinyali yeniden olustur
        3. r'den cikar: r = r - reconstructed
        4. Sonraki kullaniciya gec

        Args:
            received_signal: Alinan kompleks sinyal (superpositioned + noise)

        Returns:
            list: Her kullanicinin cozulmus bit dizisi [ndarray, ...]
                  Dizilim guc katsayisi sirasina goredir (gucludan zayifa).
        """
        decoded_bits_list = []
        residual = received_signal.copy()

        # Guc katsayilari buyukten kucuge siralanmis olmali
        sorted_indices = np.argsort(self.power_coefficients)[::-1]

        sic_stages = []  # Ara sinyal durumlarini kaydet

        for step, user_idx in enumerate(sorted_indices):
            alpha = self.power_coefficients[user_idx]

            # 1. Normalize et
            normalized = residual / np.sqrt(alpha)

            # 2. Demodulate (ML karar verici)
            decoded_bits = self.demodulate(normalized)

            sic_stages.append(residual.copy())

            # 3. Son kullanici degilse interferansi cikar
            if step < self.num_users - 1:
                # Yeniden module et
                reconstructed_symbols = self._tx.modulate(decoded_bits)
                # Guc katsayisi ile carp
                reconstructed_signal = reconstructed_symbols * np.sqrt(alpha)
                # Kalan sinyalden cikar
                residual = residual - reconstructed_signal

            decoded_bits_list.append((user_idx, decoded_bits))

        # Orijinal kullanici sirasina gore sirala
        decoded_bits_list.sort(key=lambda x: x[0])
        decoded_bits = [bits for _, bits in decoded_bits_list]

        self._last_sic_stages = sic_stages
        return decoded_bits

    def calculate_ber(self, original_bits, decoded_bits):
        """Bit Hata Orani (BER) hesaplar.

        Args:
            original_bits: Orijinal bit dizisi
            decoded_bits: Cozulen bit dizisi

        Returns:
            float: BER degeri (0.0 - 0.5)
        """
        min_len = min(len(original_bits), len(decoded_bits))
        if min_len == 0:
            return 0.5
        errors = np.sum(original_bits[:min_len] != decoded_bits[:min_len])
        return float(errors) / min_len

    def receive_frame(self, received_signal, original_bits_list):
        """Tam bir alim cercevesini isler.

        Args:
            received_signal: Alinan kompleks sinyal
            original_bits_list: Orijinal kullanici bit dizileri listesi

        Returns:
            dict: Sonuc bilgileri
        """
        decoded_users = self.sic_decode(received_signal)

        ber_per_user = []
        for i in range(self.num_users):
            ber = self.calculate_ber(original_bits_list[i], decoded_users[i])
            ber_per_user.append(ber)

        return {
            "decoded_users": decoded_users,
            "ber_per_user": ber_per_user,
            "ber_average": float(np.mean(ber_per_user)),
        }
