"""
USRP E310 Cihaz Yonetimi

USRP E310 ile baglanti kurma, yapilandirma ve veri alma/gonderme islemlerini yonetir.
Hem embedded (dogrudan E310 uzerinde) hem network (host uzerinden) modu destekler.
"""

import numpy as np

from usrp_noma import config
from usrp_noma.utils import setup_logger, freq_to_str

logger = setup_logger("USRPController")

try:
    import uhd
except ImportError:
    uhd = None
    logger.warning("UHD modulu bulunamadi. Gercek donanim erisimi devre disi.")


class USRPController:
    """USRP E310 cihaz yonetim sinifi."""

    def __init__(self, mode=None, addr=None):
        """USRPController baslatir.

        Args:
            mode: Calisma modu ("embedded" veya "network"). None ise config'den alinir.
            addr: USRP IP adresi. None ise config'den alinir.
        """
        self.mode = mode or config.DEFAULT_MODE
        self.addr = addr or config.USRP_ADDR
        self.usrp = None
        self.rx_streamer = None
        self.tx_streamer = None
        self._connected = False

    def connect(self):
        """USRP cihazina baglanir ve yapilandirir."""
        if uhd is None:
            raise RuntimeError(
                "UHD Python modulu yuklu degil. "
                "'sudo apt install python3-uhd' veya ilgili paket yoneticisini kullanin."
            )

        args = config.DEVICE_ARGS.get(self.mode, f"addr={self.addr}")
        logger.info("USRP'ye baglaniyor... mod=%s, args='%s'", self.mode, args)

        self.usrp = uhd.usrp.MultiUSRP(args)
        self._connected = True

        # Varsayilan parametreleri ayarla
        self.set_rx_rate(config.DEFAULT_SAMPLE_RATE)
        self.set_rx_freq(config.DEFAULT_CENTER_FREQ)
        self.set_rx_gain(config.DEFAULT_RX_GAIN)
        self.set_rx_antenna(config.DEFAULT_ANTENNA)

        logger.info("USRP baglantisi basarili.")
        return True

    def device_info(self):
        """Cihaz bilgilerini dondurur.

        Returns:
            dict: Cihaz bilgileri veya None (bagli degilse)
        """
        if not self._connected or self.usrp is None:
            return {"status": "bagli degil", "mode": self.mode}

        info = {
            "status": "bagli",
            "mode": self.mode,
            "mboard_name": self.usrp.get_mboard_name(),
            "rx_freq": self.usrp.get_rx_freq(),
            "rx_rate": self.usrp.get_rx_rate(),
            "rx_gain": self.usrp.get_rx_gain(),
            "rx_antenna": self.usrp.get_rx_antenna(),
            "rx_bandwidth": self.usrp.get_rx_bandwidth(),
        }
        return info

    # ----- RX (Alici) Ayarlari -----

    def set_rx_freq(self, freq):
        """RX merkez frekansini ayarlar."""
        self._ensure_connected()
        tune_req = uhd.types.TuneRequest(freq)
        self.usrp.set_rx_freq(tune_req)
        actual = self.usrp.get_rx_freq()
        logger.info("RX frekans: %s (istenen: %s)", freq_to_str(actual), freq_to_str(freq))
        return actual

    def set_rx_gain(self, gain):
        """RX kazancini (dB) ayarlar."""
        self._ensure_connected()
        self.usrp.set_rx_gain(gain)
        actual = self.usrp.get_rx_gain()
        logger.info("RX kazanc: %.1f dB", actual)
        return actual

    def set_rx_rate(self, rate):
        """RX ornekleme hizini ayarlar."""
        self._ensure_connected()
        self.usrp.set_rx_rate(rate)
        actual = self.usrp.get_rx_rate()
        logger.info("RX ornekleme hizi: %s", freq_to_str(actual))
        return actual

    def set_rx_antenna(self, antenna):
        """RX anten portunu ayarlar."""
        self._ensure_connected()
        self.usrp.set_rx_antenna(antenna)
        logger.info("RX anten: %s", antenna)

    def set_rx_bandwidth(self, bw):
        """RX analog bant genisligini ayarlar."""
        self._ensure_connected()
        self.usrp.set_rx_bandwidth(bw)
        actual = self.usrp.get_rx_bandwidth()
        logger.info("RX bant genisligi: %s", freq_to_str(actual))
        return actual

    # ----- TX (Verici) Ayarlari -----

    def set_tx_freq(self, freq):
        """TX merkez frekansini ayarlar."""
        self._ensure_connected()
        tune_req = uhd.types.TuneRequest(freq)
        self.usrp.set_tx_freq(tune_req)
        actual = self.usrp.get_tx_freq()
        logger.info("TX frekans: %s (istenen: %s)", freq_to_str(actual), freq_to_str(freq))
        return actual

    def set_tx_gain(self, gain):
        """TX kazancini (dB) ayarlar."""
        self._ensure_connected()
        self.usrp.set_tx_gain(gain)
        actual = self.usrp.get_tx_gain()
        logger.info("TX kazanc: %.1f dB", actual)
        return actual

    def set_tx_rate(self, rate):
        """TX ornekleme hizini ayarlar."""
        self._ensure_connected()
        self.usrp.set_tx_rate(rate)
        actual = self.usrp.get_tx_rate()
        logger.info("TX ornekleme hizi: %s", freq_to_str(actual))
        return actual

    def set_tx_antenna(self, antenna):
        """TX anten portunu ayarlar."""
        self._ensure_connected()
        self.usrp.set_tx_antenna(antenna)
        logger.info("TX anten: %s", antenna)

    # ----- Veri Alma/Gonderme -----

    def get_rx_stream(self):
        """RX streamer nesnesi olusturur/dondurur."""
        self._ensure_connected()
        if self.rx_streamer is None:
            st_args = uhd.usrp.StreamArgs("fc32", "sc16")
            st_args.channels = [0]
            self.rx_streamer = self.usrp.get_rx_stream(st_args)
        return self.rx_streamer

    def get_tx_stream(self):
        """TX streamer nesnesi olusturur/dondurur."""
        self._ensure_connected()
        if self.tx_streamer is None:
            st_args = uhd.usrp.StreamArgs("fc32", "sc16")
            st_args.channels = [0]
            self.tx_streamer = self.usrp.get_tx_stream(st_args)
        return self.tx_streamer

    def receive_samples(self, num_samples):
        """Belirtilen sayida IQ ornegi alir.

        Args:
            num_samples: Alinacak ornek sayisi

        Returns:
            numpy.ndarray: Kompleks float32 IQ verisi
        """
        rx_stream = self.get_rx_stream()
        buffer = np.zeros(num_samples, dtype=np.complex64)
        metadata = uhd.types.RXMetadata()

        # Akisi baslat
        stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.num_done)
        stream_cmd.num_samps = num_samples
        stream_cmd.stream_now = True
        rx_stream.issue_stream_cmd(stream_cmd)

        received = 0
        while received < num_samples:
            samps = rx_stream.recv(buffer[received:], metadata)
            if metadata.error_code == uhd.types.RXMetadataErrorCode.timeout:
                logger.warning("RX zaman asimi")
                break
            if metadata.error_code == uhd.types.RXMetadataErrorCode.overflow:
                logger.warning("RX tasmasi (overflow)")
                continue
            if metadata.error_code != uhd.types.RXMetadataErrorCode.none:
                logger.error("RX hatasi: %s", metadata.error_code)
                break
            received += samps

        logger.info("Alinan ornek sayisi: %d / %d", received, num_samples)
        return buffer[:received]

    def send_samples(self, samples):
        """IQ ornekleri gonderir.

        Args:
            samples: Gonderilecek kompleks IQ veri dizisi

        Returns:
            int: Gonderilen ornek sayisi
        """
        tx_stream = self.get_tx_stream()
        metadata = uhd.types.TXMetadata()
        metadata.has_time_spec = False

        samples = np.asarray(samples, dtype=np.complex64)
        sent = tx_stream.send(samples, metadata)

        # Akisi sonlandir
        metadata.end_of_burst = True
        tx_stream.send(np.zeros(0, dtype=np.complex64), metadata)

        logger.info("Gonderilen ornek sayisi: %d", sent)
        return sent

    # ----- Yardimci -----

    def _ensure_connected(self):
        """Cihazin bagli oldugundan emin olur."""
        if not self._connected or self.usrp is None:
            raise RuntimeError("USRP bagli degil. Once connect() cagirilmali.")

    def close(self):
        """Baglantiyi kapatir ve kaynaklari serbest birakir."""
        self.rx_streamer = None
        self.tx_streamer = None
        self.usrp = None
        self._connected = False
        logger.info("USRP baglantisi kapatildi.")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
