"""
Test Sinyal Uretimi

USRP E310 uzerinden test sinyalleri uretme: CW ton, chirp, LoRa preamble, gurultu.
"""

import numpy as np

from usrp_noma import config
from usrp_noma.utils import setup_logger, freq_to_str

logger = setup_logger("SignalGenerator")


class SignalGenerator:
    """Test sinyal uretim sinifi."""

    def __init__(self, controller):
        """SignalGenerator baslatir.

        Args:
            controller: USRPController nesnesi (bagli olmali)
        """
        self.controller = controller

    def generate_tone(self, freq_offset=10e3, amplitude=0.7, duration=1.0,
                      sample_rate=None):
        """CW (Continuous Wave) sinusoidal sinyal uretir.

        Args:
            freq_offset: Merkez frekanstan ofset (Hz)
            amplitude: Sinyal genligi (0-1)
            duration: Sinyal suresi (saniye)
            sample_rate: Ornekleme hizi (Hz). None ise mevcut deger.

        Returns:
            numpy.ndarray: Kompleks sinyal dizisi
        """
        fs = sample_rate or self.controller.usrp.get_tx_rate()
        n_samples = int(duration * fs)
        t = np.arange(n_samples) / fs

        signal = amplitude * np.exp(1j * 2 * np.pi * freq_offset * t)

        logger.info(
            "CW ton uretildi: offset=%s, genlik=%.2f, sure=%.2f s, ornek=%d",
            freq_to_str(freq_offset), amplitude, duration, n_samples,
        )
        return signal.astype(np.complex64)

    def generate_chirp(self, bw=None, duration=None, is_up=True, sample_rate=None):
        """Lineer chirp sinyal uretir.

        Args:
            bw: Chirp bant genisligi (Hz). None ise LoRa BW.
            duration: Sinyal suresi (saniye). None ise 1 sembol suresi.
            is_up: True ise yukari-chirp, False ise asagi-chirp
            sample_rate: Ornekleme hizi (Hz).

        Returns:
            numpy.ndarray: Kompleks chirp sinyali
        """
        bw = bw or config.LORA_DEFAULT_BW
        fs = sample_rate or self.controller.usrp.get_tx_rate()

        if duration is None:
            duration = (2 ** config.LORA_DEFAULT_SF) / bw

        n_samples = int(duration * fs)
        t = np.arange(n_samples) / fs

        if is_up:
            f0, f1 = -bw / 2, bw / 2
        else:
            f0, f1 = bw / 2, -bw / 2

        chirp_rate = (f1 - f0) / duration
        phase = 2 * np.pi * (f0 * t + 0.5 * chirp_rate * t ** 2)
        signal = 0.7 * np.exp(1j * phase)

        direction = "yukari" if is_up else "asagi"
        logger.info(
            "Chirp uretildi: %s, BW=%s, sure=%.4f s, ornek=%d",
            direction, freq_to_str(bw), duration, n_samples,
        )
        return signal.astype(np.complex64)

    def generate_lora_preamble(self, sf=None, bw=None, n_preamble=None,
                               sample_rate=None):
        """LoRa preamble (ardisik up-chirp) sinyali uretir.

        Args:
            sf: Spreading Factor. None ise config'den alinir.
            bw: Bant genisligi (Hz). None ise config'den alinir.
            n_preamble: Preamble sembol sayisi. None ise config'den alinir.
            sample_rate: Ornekleme hizi (Hz).

        Returns:
            numpy.ndarray: Kompleks preamble sinyali
        """
        sf = sf or config.LORA_DEFAULT_SF
        bw = bw or config.LORA_DEFAULT_BW
        n_preamble = n_preamble or config.LORA_PREAMBLE_LEN
        fs = sample_rate or self.controller.usrp.get_tx_rate()

        symbol_len = 2 ** sf
        symbol_duration = symbol_len / bw
        n_per_symbol = int(symbol_duration * fs)

        # Up-chirp'leri birlestir
        preamble = np.zeros(0, dtype=np.complex64)
        t = np.arange(n_per_symbol) / fs

        f0 = -bw / 2
        f1 = bw / 2
        chirp_rate = (f1 - f0) / symbol_duration
        phase = 2 * np.pi * (f0 * t + 0.5 * chirp_rate * t ** 2)
        up_chirp = 0.7 * np.exp(1j * phase).astype(np.complex64)

        for _ in range(n_preamble):
            preamble = np.concatenate([preamble, up_chirp])

        # 2 adet down-chirp (sync word)
        phase_down = 2 * np.pi * (f1 * t + 0.5 * (-chirp_rate) * t ** 2)
        down_chirp = 0.7 * np.exp(1j * phase_down).astype(np.complex64)
        for _ in range(2):
            preamble = np.concatenate([preamble, down_chirp])

        logger.info(
            "LoRa preamble uretildi: SF=%d, BW=%s, %d up-chirp + 2 down-chirp, "
            "toplam %d ornek",
            sf, freq_to_str(bw), n_preamble, len(preamble),
        )
        return preamble

    def generate_noise(self, bandwidth=None, power_dBm=-30, duration=1.0,
                       sample_rate=None):
        """Beyaz Gauss gurultusu uretir.

        Args:
            bandwidth: Bant genisligi (Hz). None ise ornekleme hizinin yarisi.
            power_dBm: Gurultu gucu (dBm)
            duration: Sure (saniye)
            sample_rate: Ornekleme hizi (Hz)

        Returns:
            numpy.ndarray: Kompleks gurultu sinyali
        """
        fs = sample_rate or self.controller.usrp.get_tx_rate()
        n_samples = int(duration * fs)

        # dBm -> lineer guc
        power_linear = 10 ** ((power_dBm - 30) / 10.0)
        amplitude = np.sqrt(power_linear * 50)  # 50 ohm empedans

        noise_i = amplitude * np.random.randn(n_samples)
        noise_q = amplitude * np.random.randn(n_samples)
        signal = (noise_i + 1j * noise_q).astype(np.complex64)

        logger.info(
            "Gurultu uretildi: guc=%.1f dBm, sure=%.2f s, ornek=%d",
            power_dBm, duration, n_samples,
        )
        return signal

    def transmit(self, samples, freq=None, gain=None, rate=None):
        """Sinyal gonderir.

        Args:
            samples: Gonderilecek IQ veri dizisi
            freq: TX merkez frekansi (Hz). None ise mevcut deger.
            gain: TX kazanci (dB). None ise mevcut deger.
            rate: TX ornekleme hizi (Hz). None ise mevcut deger.

        Returns:
            int: Gonderilen ornek sayisi
        """
        if freq is not None:
            self.controller.set_tx_freq(freq)
        if gain is not None:
            self.controller.set_tx_gain(gain)
        if rate is not None:
            self.controller.set_tx_rate(rate)

        logger.info(
            "Sinyal gonderiliyor: %d ornek, freq=%s",
            len(samples),
            freq_to_str(self.controller.usrp.get_tx_freq()),
        )
        return self.controller.send_samples(samples)

    def transmit_continuous(self, generator_func, freq=None, gain=None,
                            rate=None, max_repeats=0):
        """Surekli sinyal iletimi.

        Args:
            generator_func: Sinyal ureten fonksiyon (parametresiz, ndarray dondurur)
            freq: TX merkez frekansi (Hz)
            gain: TX kazanci (dB)
            rate: TX ornekleme hizi (Hz)
            max_repeats: Maksimum tekrar sayisi (0 = sinirsiz)
        """
        if freq is not None:
            self.controller.set_tx_freq(freq)
        if gain is not None:
            self.controller.set_tx_gain(gain)
        if rate is not None:
            self.controller.set_tx_rate(rate)

        logger.info("Surekli iletim baslatiliyor...")

        count = 0
        try:
            while max_repeats == 0 or count < max_repeats:
                samples = generator_func()
                self.controller.send_samples(samples)
                count += 1
        except KeyboardInterrupt:
            logger.info("Surekli iletim durduruldu (kullanici).")

        logger.info("Toplam %d tekrar gonderildi.", count)
