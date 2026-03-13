"""
LoRa Sinyal Demodulasyon

LoRa (Chirp Spread Spectrum) sinyallerinin tespiti ve demodulasyonu.
Preamble algilama, dechirp islemi, sembol cozumleme.
"""

import numpy as np

from usrp_noma import config
from usrp_noma.utils import setup_logger

logger = setup_logger("LoRaDecoder")


class LoRaDecoder:
    """LoRa sinyal demodulasyon sinifi.

    CSS (Chirp Spread Spectrum) tabanli LoRa sinyallerini isler.
    """

    def __init__(self, sf=None, bw=None, fs=None):
        """LoRaDecoder baslatir.

        Args:
            sf: Spreading Factor (7-12). None ise config'den alinir.
            bw: Bant genisligi (Hz). None ise config'den alinir.
            fs: Ornekleme hizi (Hz). None ise config'den alinir.
        """
        self.sf = sf or config.LORA_DEFAULT_SF
        self.bw = bw or config.LORA_DEFAULT_BW
        self.fs = fs or config.DEFAULT_SAMPLE_RATE

        # Turetilmis parametreler
        self.n_symbols = 2 ** self.sf           # Sembol basina ornek (bant genisliginde)
        self.symbol_duration = self.n_symbols / self.bw  # Sembol suresi (s)
        self.samples_per_symbol = int(self.symbol_duration * self.fs)

        logger.info(
            "LoRa Decoder: SF=%d, BW=%.0f Hz, Fs=%.0f Hz, "
            "Sembol basina %d ornek, Sembol suresi=%.4f s",
            self.sf, self.bw, self.fs,
            self.samples_per_symbol, self.symbol_duration,
        )

    def generate_chirp(self, is_up=True, sf=None):
        """Referans chirp sinyali uretir.

        Args:
            is_up: True ise up-chirp, False ise down-chirp
            sf: Spreading Factor (None ise mevcut deger)

        Returns:
            numpy.ndarray: Kompleks chirp sinyali
        """
        sf = sf or self.sf
        n = self.samples_per_symbol
        t = np.arange(n) / self.fs

        # Chirp frekans degisimi: -BW/2 -> +BW/2 (up) veya tersi (down)
        if is_up:
            f0 = -self.bw / 2
            f1 = self.bw / 2
        else:
            f0 = self.bw / 2
            f1 = -self.bw / 2

        # Lineer chirp: faz = 2*pi * (f0*t + (f1-f0)/(2*T) * t^2)
        chirp_rate = (f1 - f0) / self.symbol_duration
        phase = 2 * np.pi * (f0 * t + 0.5 * chirp_rate * t ** 2)

        return np.exp(1j * phase).astype(np.complex64)

    def dechirp(self, iq_data):
        """IQ verisine dechirp islemi uygular.

        Down-chirp referansini carparak up-chirp'leri tek frekanslara donusturur.

        Args:
            iq_data: Kompleks IQ veri dizisi

        Returns:
            numpy.ndarray: Dechirp edilmis sinyal
        """
        down_chirp = self.generate_chirp(is_up=False)
        n = self.samples_per_symbol

        # Sembol sembol dechirp
        num_symbols = len(iq_data) // n
        dechirped = np.zeros_like(iq_data[:num_symbols * n])

        for i in range(num_symbols):
            segment = iq_data[i * n : (i + 1) * n]
            dechirped[i * n : (i + 1) * n] = segment * down_chirp

        return dechirped

    def detect_preamble(self, iq_data, threshold=0.6):
        """LoRa preamble (ardisik up-chirp'ler) tespiti.

        Args:
            iq_data: Kompleks IQ veri dizisi
            threshold: Korelasyon esigi (0-1)

        Returns:
            list: Tespit edilen preamble baslangic indeksleri
        """
        up_chirp = self.generate_chirp(is_up=True)
        n = self.samples_per_symbol
        detections = []

        # Kayar pencere ile korelasyon
        step = n // 4  # 1/4 sembol adimla tara
        max_corr_value = np.sum(np.abs(up_chirp) ** 2)

        for offset in range(0, len(iq_data) - n * config.LORA_PREAMBLE_LEN, step):
            # Ilk chirp ile korelasyon
            segment = iq_data[offset : offset + n]
            if len(segment) < n:
                break

            corr = np.abs(np.sum(segment * np.conj(up_chirp))) / max_corr_value

            if corr > threshold:
                # Ardisik chirp'leri kontrol et (en az 4 tane)
                consecutive = 0
                for k in range(config.LORA_PREAMBLE_LEN):
                    seg = iq_data[offset + k * n : offset + (k + 1) * n]
                    if len(seg) < n:
                        break
                    c = np.abs(np.sum(seg * np.conj(up_chirp))) / max_corr_value
                    if c > threshold:
                        consecutive += 1
                    else:
                        break

                if consecutive >= 4:
                    detections.append(offset)
                    logger.info(
                        "Preamble tespit edildi: ornek=%d, ardisik=%d, korelasyon=%.3f",
                        offset, consecutive, corr,
                    )

        return detections

    def extract_symbols(self, iq_data, start_offset=0):
        """Dechirp edilmis veriyi sembollere cevirir.

        Args:
            iq_data: Kompleks IQ veri dizisi
            start_offset: Baslangic ornek indeksi

        Returns:
            list: Sembol degerleri (0 ile 2^SF-1 arasi)
        """
        down_chirp = self.generate_chirp(is_up=False)
        n = self.samples_per_symbol
        symbols = []

        data = iq_data[start_offset:]
        num_symbols = len(data) // n

        for i in range(num_symbols):
            segment = data[i * n : (i + 1) * n]
            # Dechirp
            dechirped = segment * down_chirp
            # FFT ile tepe frekansini bul
            fft_result = np.abs(np.fft.fft(dechirped))
            # Sembol degeri = tepe indeksi (mod 2^SF)
            peak_bin = np.argmax(fft_result[:self.n_symbols])
            symbols.append(peak_bin)

        return symbols

    def decode_header(self, symbols):
        """LoRa baslik bilgilerini cozumler.

        Args:
            symbols: Sembol listesi (en az 5 sembol)

        Returns:
            dict: Baslik bilgileri veya None
        """
        if len(symbols) < 5:
            return None

        # LoRa header: ilk semboller (basitlesirilmis)
        # Gercek implementasyonda Gray-coding ve interleaving uygulanir
        header = {
            "payload_length": symbols[0] if len(symbols) > 0 else 0,
            "coding_rate": (symbols[1] >> (self.sf - 3)) & 0x07 if len(symbols) > 1 else 0,
            "has_crc": bool(symbols[2] & 1) if len(symbols) > 2 else False,
            "raw_symbols": symbols[:5],
        }
        logger.info("Header cozumlendi: %s", header)
        return header

    def decode_payload(self, symbols):
        """Payload verilerini cozumler.

        Args:
            symbols: Sembol listesi (header sonrasi)

        Returns:
            bytes: Cozumlenmis veri baytlari
        """
        # Basitlesirilmis: her 2 sembolden 1 bayt
        payload = bytearray()
        for i in range(0, len(symbols) - 1, 2):
            byte_val = ((symbols[i] & 0x0F) << 4) | (symbols[i + 1] & 0x0F)
            payload.append(byte_val & 0xFF)
        return bytes(payload)

    def estimate_sf(self, iq_data):
        """Sinyaldeki Spreading Factor'u tahmin eder.

        Farkli SF'ler icin chirp korelasyonu yaparak en iyi uyumu bulur.

        Args:
            iq_data: Kompleks IQ veri dizisi

        Returns:
            int: Tahmin edilen SF degeri (7-12)
        """
        best_sf = self.sf
        best_corr = 0

        for test_sf in range(7, 13):
            test_decoder = LoRaDecoder(sf=test_sf, bw=self.bw, fs=self.fs)
            ref_chirp = test_decoder.generate_chirp(is_up=True)
            n = test_decoder.samples_per_symbol

            if len(iq_data) < n:
                continue

            segment = iq_data[:n]
            corr = np.abs(np.sum(segment * np.conj(ref_chirp)))
            corr /= np.sqrt(np.sum(np.abs(segment) ** 2) * np.sum(np.abs(ref_chirp) ** 2))

            if corr > best_corr:
                best_corr = corr
                best_sf = test_sf

        logger.info("Tahmin edilen SF: %d (korelasyon: %.3f)", best_sf, best_corr)
        return best_sf

    def process(self, iq_data):
        """Tam LoRa demodulasyon pipeline'i.

        Preamble tespiti -> sembol cikartma -> header cozme -> payload cozme

        Args:
            iq_data: Kompleks IQ veri dizisi

        Returns:
            list: Her tespit edilen paket icin sonuc dict'i
        """
        results = []
        preamble_offsets = self.detect_preamble(iq_data)

        for offset in preamble_offsets:
            # Preamble atlama (8 up-chirp + 2 down-chirp = ~10 sembol)
            data_start = offset + (config.LORA_PREAMBLE_LEN + 2) * self.samples_per_symbol

            if data_start >= len(iq_data):
                continue

            # Sembol cikartma
            symbols = self.extract_symbols(iq_data, start_offset=data_start)

            if len(symbols) < 5:
                continue

            # Header ve payload cozumleme
            header = self.decode_header(symbols[:5])
            payload = self.decode_payload(symbols[5:])

            result = {
                "preamble_offset": offset,
                "header": header,
                "payload_raw": payload,
                "payload_hex": payload.hex(),
                "symbols": symbols,
                "num_symbols": len(symbols),
            }
            results.append(result)

            logger.info(
                "Paket cozumlendi: offset=%d, sembol=%d, payload=%s",
                offset, len(symbols), payload.hex(),
            )

        if not results:
            logger.info("Hicbir LoRa paketi tespit edilemedi.")

        return results
