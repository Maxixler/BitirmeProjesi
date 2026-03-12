"""
ZMQ Veri Akisi

ZMQ (ZeroMQ) uzerinden IQ veri yayin/alma. USRP E310'dan host bilgisayara
veri aktarimi veya GNU Radio entegrasyonu icin.
"""

import threading

import numpy as np
import zmq

from usrp_noma import config
from usrp_noma.utils import setup_logger, freq_to_str

logger = setup_logger("ZMQStreamer")


class ZMQStreamer:
    """ZMQ tabanli IQ veri akis sinifi."""

    def __init__(self, port=None, protocol=None, bind_addr=None):
        """ZMQStreamer baslatir.

        Args:
            port: ZMQ port numarasi. None ise config'den.
            protocol: Protokol ("tcp", "ipc" vb.). None ise config'den.
            bind_addr: Baglanti adresi. None ise otomatik olusturulur.
        """
        self.port = port or config.ZMQ_PORT
        self.protocol = protocol or config.ZMQ_PROTOCOL
        self.bind_addr = bind_addr or f"{self.protocol}://*:{self.port}"

        self.context = zmq.Context()
        self.socket = None
        self._running = False
        self._thread = None

    def start_publisher(self, controller, chunk_duration=0.1):
        """PUB socket ile IQ veri yayini baslatir.

        USRP'den alinan verileri ZMQ uzerinden yayinlar.
        GNU Radio ZMQ SUB Source blogu ile uyumludur.

        Args:
            controller: USRPController nesnesi (bagli olmali)
            chunk_duration: Her yayindaki veri suresi (saniye)
        """
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind(self.bind_addr)
        self._running = True

        logger.info("ZMQ yayinlayici baslatildi: %s", self.bind_addr)

        def _publish_loop():
            sample_rate = controller.usrp.get_rx_rate()
            chunk_samples = int(chunk_duration * sample_rate)

            while self._running:
                try:
                    data = controller.receive_samples(chunk_samples)
                    if len(data) > 0:
                        # GNU Radio uyumlu format: raw complex64 baytlari
                        raw_bytes = data.astype(np.complex64).tobytes()
                        self.socket.send(raw_bytes, zmq.NOBLOCK)
                except zmq.ZMQError as e:
                    if e.errno == zmq.EAGAIN:
                        continue
                    logger.error("ZMQ gonderme hatasi: %s", e)
                    break
                except Exception as e:
                    logger.error("Veri alma hatasi: %s", e)
                    if not self._running:
                        break

            logger.info("ZMQ yayinlayici durduruldu.")

        self._thread = threading.Thread(target=_publish_loop, daemon=True)
        self._thread.start()

    def start_subscriber(self, host=None, port=None, callback=None):
        """SUB socket ile IQ veri almaya baslar.

        Host bilgisayar tarafinda kullanilir. ZMQ PUB kaynagindan veri alir.

        Args:
            host: Yayincinin IP adresi. None ise config'den.
            port: Yayincinin portu. None ise config'den.
            callback: Alinan veriler icin cagrilacak fonksiyon.
                     Imza: callback(iq_data: np.ndarray)
        """
        host = host or config.USRP_ADDR
        port = port or self.port
        connect_addr = f"{self.protocol}://{host}:{port}"

        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect(connect_addr)
        self.socket.setsockopt(zmq.SUBSCRIBE, b"")  # Tum mesajlara abone ol
        self.socket.setsockopt(zmq.RCVTIMEO, 5000)  # 5 saniye zaman asimi

        self._running = True

        logger.info("ZMQ alici baslatildi: %s", connect_addr)

        def _subscribe_loop():
            while self._running:
                try:
                    raw_bytes = self.socket.recv()
                    iq_data = np.frombuffer(raw_bytes, dtype=np.complex64)

                    if callback is not None:
                        callback(iq_data)

                except zmq.Again:
                    continue
                except zmq.ZMQError as e:
                    logger.error("ZMQ alma hatasi: %s", e)
                    break
                except Exception as e:
                    logger.error("Islem hatasi: %s", e)
                    if not self._running:
                        break

            logger.info("ZMQ alici durduruldu.")

        self._thread = threading.Thread(target=_subscribe_loop, daemon=True)
        self._thread.start()

    def receive_once(self, host=None, port=None, timeout_ms=5000):
        """Tek bir IQ veri parcasi alir (bloklayici).

        Args:
            host: Yayincinin IP adresi.
            port: Port numarasi.
            timeout_ms: Zaman asimi (milisaniye).

        Returns:
            numpy.ndarray: Alinan IQ veri dizisi veya None
        """
        host = host or config.USRP_ADDR
        port = port or self.port
        connect_addr = f"{self.protocol}://{host}:{port}"

        sock = self.context.socket(zmq.SUB)
        sock.connect(connect_addr)
        sock.setsockopt(zmq.SUBSCRIBE, b"")
        sock.setsockopt(zmq.RCVTIMEO, timeout_ms)

        try:
            raw_bytes = sock.recv()
            return np.frombuffer(raw_bytes, dtype=np.complex64)
        except zmq.Again:
            logger.warning("ZMQ zaman asimi: veri alinamadi")
            return None
        finally:
            sock.close()

    def stop(self):
        """Akisi durdurur ve kaynaklari serbest birakir."""
        self._running = False

        if self._thread is not None:
            self._thread.join(timeout=5.0)
            self._thread = None

        if self.socket is not None:
            self.socket.close()
            self.socket = None

        logger.info("ZMQ akisi durduruldu.")

    def close(self):
        """Tum kaynaklari temizler."""
        self.stop()
        if self.context is not None:
            self.context.term()
            self.context = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
