"""
USRP E310 & LoRaWAN Sinyal Analiz Projesi - Yardimci Fonksiyonlar
"""

import logging
import os
from datetime import datetime

import numpy as np


def linear_to_dB(value):
    """Lineer degeri dB'ye cevirir (guc icin)."""
    return 10.0 * np.log10(np.maximum(value, 1e-12))


def dB_to_linear(value_dB):
    """dB degerini lineer'e cevirir (guc icin)."""
    return 10.0 ** (value_dB / 10.0)


def amplitude_to_dB(value):
    """Lineer genlik degerini dB'ye cevirir."""
    return 20.0 * np.log10(np.maximum(np.abs(value), 1e-12))


def dB_to_amplitude(value_dB):
    """dB degerini lineer genlige cevirir."""
    return 10.0 ** (value_dB / 20.0)


def freq_to_str(freq_hz):
    """Frekans degerini okunabilir formata cevirir.

    Ornekler:
        868000000 -> "868.000 MHz"
        2400000000 -> "2.400 GHz"
        125000 -> "125.000 kHz"
    """
    if freq_hz >= 1e9:
        return f"{freq_hz / 1e9:.3f} GHz"
    elif freq_hz >= 1e6:
        return f"{freq_hz / 1e6:.3f} MHz"
    elif freq_hz >= 1e3:
        return f"{freq_hz / 1e3:.3f} kHz"
    else:
        return f"{freq_hz:.1f} Hz"


def save_iq_data(data, filename, sample_rate=None, center_freq=None):
    """IQ verisini dosyaya kaydeder.

    Args:
        data: numpy complex64/complex128 dizisi
        filename: Kayit dosya yolu
        sample_rate: Ornekleme hizi (metadata olarak)
        center_freq: Merkez frekans (metadata olarak)
    """
    directory = os.path.dirname(filename)
    if directory:
        os.makedirs(directory, exist_ok=True)

    if filename.endswith(".npy"):
        np.save(filename, data.astype(np.complex64))
    elif filename.endswith(".raw"):
        data.astype(np.complex64).tofile(filename)
    else:
        np.save(filename, data.astype(np.complex64))

    # Metadata dosyasi kaydet
    if sample_rate is not None or center_freq is not None:
        meta_file = filename + ".meta"
        with open(meta_file, "w") as f:
            if sample_rate is not None:
                f.write(f"sample_rate={sample_rate}\n")
            if center_freq is not None:
                f.write(f"center_freq={center_freq}\n")
            f.write(f"timestamp={datetime.now().isoformat()}\n")
            f.write(f"num_samples={len(data)}\n")


def load_iq_data(filename):
    """IQ verisini dosyadan yukler.

    Args:
        filename: Kayit dosya yolu

    Returns:
        tuple: (data, metadata_dict)
    """
    if filename.endswith(".npy"):
        data = np.load(filename)
    elif filename.endswith(".raw"):
        data = np.fromfile(filename, dtype=np.complex64)
    else:
        data = np.load(filename)

    metadata = {}
    meta_file = filename + ".meta"
    if os.path.exists(meta_file):
        with open(meta_file, "r") as f:
            for line in f:
                line = line.strip()
                if "=" in line:
                    key, val = line.split("=", 1)
                    metadata[key] = val

    return data, metadata


def timestamp_filename(prefix="capture", ext="npy", directory="data"):
    """Zaman damgali dosya adi olusturur.

    Args:
        prefix: Dosya on eki
        ext: Dosya uzantisi
        directory: Hedef klasor

    Returns:
        str: Dosya yolu (ornek: data/capture_20260313_143025.npy)
    """
    os.makedirs(directory, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(directory, f"{prefix}_{ts}.{ext}")


def setup_logger(name, level=logging.INFO):
    """Logger yapilandirmasi olusturur.

    Args:
        name: Logger adi
        level: Log seviyesi

    Returns:
        logging.Logger: Yapilandirilmis logger nesnesi
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
            datefmt="%H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


def compute_power_dBm(iq_data, impedance=50):
    """IQ verisinden ortalama gucu dBm cinsinden hesaplar.

    Args:
        iq_data: Kompleks IQ veri dizisi
        impedance: Empedans (ohm)

    Returns:
        float: Ortalama guc (dBm)
    """
    mean_power = np.mean(np.abs(iq_data) ** 2) / impedance
    if mean_power > 0:
        return 10.0 * np.log10(mean_power) + 30  # W -> dBm
    return -120.0


def estimate_snr(iq_data, signal_bw, sample_rate):
    """Basit SNR tahmini yapar (sinyal/gurultu orani).

    Args:
        iq_data: Kompleks IQ veri dizisi
        signal_bw: Sinyal bant genisligi (Hz)
        sample_rate: Ornekleme hizi (Hz)

    Returns:
        float: SNR tahmini (dB)
    """
    spectrum = np.fft.fftshift(np.abs(np.fft.fft(iq_data)) ** 2)
    n = len(spectrum)
    freqs = np.fft.fftshift(np.fft.fftfreq(n, 1.0 / sample_rate))

    signal_mask = np.abs(freqs) <= signal_bw / 2
    noise_mask = ~signal_mask

    if np.sum(noise_mask) == 0 or np.sum(signal_mask) == 0:
        return 0.0

    signal_power = np.mean(spectrum[signal_mask])
    noise_power = np.mean(spectrum[noise_mask])

    if noise_power > 0:
        return linear_to_dB(signal_power / noise_power)
    return 0.0
