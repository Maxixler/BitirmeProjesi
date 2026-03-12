"""
NOMA Verici (Transmitter)

Superposition Coding ile coklu kullanici sinyali olusturur.
QPSK, 16-QAM ve 64-QAM modulasyon destegi.
"""

import numpy as np

from usrp_noma import config
from usrp_noma.utils import setup_logger
from usrp_noma.noma.modulation import CONSTELLATIONS

logger = setup_logger("NOMA.TX")


class NOMATransmitter:
    """NOMA Verici: Superposition Coding ile coklu kullanici sinyali olusturur."""

    def __init__(self, num_users=None, power_coefficients=None,
                 modulation=None, sample_rate=None):
        """NOMATransmitter baslatir.

        Args:
            num_users: Kullanici sayisi (2-4).
            power_coefficients: Guc katsayilari listesi (toplam=1.0).
            modulation: Modulasyon tipi ("QPSK", "16QAM", "64QAM").
            sample_rate: Ornekleme hizi (Hz).
        """
        self.num_users = num_users or config.NOMA_NUM_USERS
        self.modulation = modulation or config.NOMA_DEFAULT_MODULATION
        self.sample_rate = sample_rate or config.DEFAULT_SAMPLE_RATE
        self.bits_per_symbol = config.NOMA_BITS_PER_SYMBOL[self.modulation]
        self.constellation = CONSTELLATIONS[self.modulation]

        if power_coefficients is not None:
            self.power_coefficients = list(power_coefficients)
        else:
            self.power_coefficients = list(
                config.NOMA_POWER_COEFFICIENTS[self.num_users]
            )

        # Dogrulama
        assert len(self.power_coefficients) == self.num_users, \
            f"Guc katsayisi sayisi ({len(self.power_coefficients)}) != kullanici sayisi ({self.num_users})"
        assert abs(sum(self.power_coefficients) - 1.0) < 1e-6, \
            f"Guc katsayilari toplami 1.0 olmali, simdi: {sum(self.power_coefficients)}"

        logger.info(
            "NOMATransmitter: %d kullanici, mod=%s, guc=%s",
            self.num_users, self.modulation, self.power_coefficients,
        )

    def generate_random_bits(self, num_bits):
        """Rastgele bit dizisi uretir.

        Args:
            num_bits: Bit sayisi

        Returns:
            np.ndarray: {0, 1} dizisi
        """
        return np.random.randint(0, 2, size=num_bits)

    def modulate(self, bits):
        """Bitleri kompleks sembollere donusturur.

        Args:
            bits: Bit dizisi (uzunluk bits_per_symbol'un kati olmali)

        Returns:
            np.ndarray: Kompleks sembol dizisi
        """
        bps = self.bits_per_symbol
        n_symbols = len(bits) // bps
        bits = bits[:n_symbols * bps]

        symbols = np.zeros(n_symbols, dtype=np.complex128)
        for i in range(n_symbols):
            bit_group = bits[i * bps:(i + 1) * bps]
            # Bit grubunu indekse cevir
            idx = 0
            for b in bit_group:
                idx = (idx << 1) | int(b)
            idx = idx % len(self.constellation)
            symbols[i] = self.constellation[idx]

        return symbols

    def demodulate_to_bits(self, symbol, constellation=None):
        """Tek bir sembolu bitlere donusturur (hard decision).

        Args:
            symbol: Kompleks sembol
            constellation: Konstelasyon noktalari (None ise mevcut)

        Returns:
            np.ndarray: Bit dizisi
        """
        if constellation is None:
            constellation = self.constellation
        bps = self.bits_per_symbol
        # En yakin konstelasyon noktasi (ML)
        distances = np.abs(symbol - constellation)
        idx = np.argmin(distances)
        # Indeksi bitlere cevir
        bits = np.zeros(bps, dtype=int)
        for k in range(bps - 1, -1, -1):
            bits[k] = idx & 1
            idx >>= 1
        return bits

    def allocate_power(self, user_signals):
        """Her kullanici sinyaline guc katsayisi uygular.

        Args:
            user_signals: Kullanici sinyalleri listesi [ndarray, ...]

        Returns:
            list: Guc ayarlanmis sinyal listesi
        """
        powered = []
        for i, sig in enumerate(user_signals):
            powered.append(sig * np.sqrt(self.power_coefficients[i]))
        return powered

    def superposition_code(self, user_signals):
        """Guc ayarlanmis sinyalleri toplar (superposition coding).

        Args:
            user_signals: Guc ayarlanmis sinyal listesi

        Returns:
            np.ndarray: Birlestirilmis sinyal
        """
        combined = np.zeros_like(user_signals[0])
        for sig in user_signals:
            combined += sig
        return combined

    def transmit_frame(self, user_data_list=None, num_bits=None):
        """Tam bir NOMA iletim cercevesi olusturur.

        Args:
            user_data_list: Her kullanici icin bit dizileri listesi.
                            None ise rastgele uretilir.
            num_bits: Kullanici basina bit sayisi (user_data_list None ise).

        Returns:
            tuple: (combined_signal, original_bits_list, original_symbols_list)
        """
        num_bits = num_bits or config.NOMA_BITS_PER_FRAME
        # bits_per_symbol'un katina yuvarlama
        num_bits = (num_bits // self.bits_per_symbol) * self.bits_per_symbol

        if user_data_list is None:
            user_data_list = [
                self.generate_random_bits(num_bits)
                for _ in range(self.num_users)
            ]

        # Modulasyon
        user_symbols = [self.modulate(bits) for bits in user_data_list]

        # Guc tahsisi
        powered_signals = self.allocate_power(user_symbols)

        # Superposition coding
        combined = self.superposition_code(powered_signals)

        return combined, user_data_list, user_symbols

    def get_constellation_points(self):
        """Mevcut modulasyonun konstelasyon noktalarini dondurur.

        Returns:
            np.ndarray: Konstelasyon noktalari
        """
        return self.constellation.copy()
