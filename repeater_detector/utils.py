"""
Kacak Repeater Tespit Sistemi - Yardimci Fonksiyonlar

Ana proje (usrp_noma.utils) fonksiyonlarini kullanir ve
alt projeye ozgu islevleri saglar.
"""

import os
import json
from datetime import datetime

import numpy as np

from usrp_noma.utils import (
    setup_logger,
    freq_to_str,
    linear_to_dB,
    dB_to_linear,
    amplitude_to_dB,
    compute_power_dBm,
    save_iq_data,
    load_iq_data,
    timestamp_filename,
)
from repeater_detector import config as det_config


logger = setup_logger("repeater_detector.utils")


def classify_frequency(freq_hz, tolerance_hz=None):
    """
    Verilen frekansin bilinen yasal frekanslardan birine uyup uymadigini kontrol eder.

    Args:
        freq_hz: Kontrol edilecek frekans (Hz)
        tolerance_hz: Tolerans (Hz). None ise config'den alinir.

    Returns:
        tuple: (eslesme_var_mi, en_yakin_isim, fark_hz)
            eslesme_var_mi: bool — yasal frekansla eslesiyor mu
            en_yakin_isim: str veya None — eslesen frekans adi
            fark_hz: float — en yakin bilinen frekanstan uzaklik (Hz)
    """
    if tolerance_hz is None:
        tolerance_hz = det_config.ANOMALY_BW_TOLERANCE_HZ

    best_name = None
    best_diff = float("inf")

    for name, info in det_config.ALL_KNOWN_FREQUENCIES.items():
        known_freq = info["freq"]
        diff = abs(freq_hz - known_freq)

        if diff < best_diff:
            best_diff = diff
            best_name = name

    # Eslese kontrolu: sadece dar kanalli frekanslar icin BW kullan
    # Genis bant tahsisleri (operatorler, >1 MHz BW) icin sadece tolerans
    # Cunku bant icinde olmak yasallik kaniti degildir
    if best_name is not None:
        best_info = det_config.ALL_KNOWN_FREQUENCIES[best_name]
        known_bw = best_info.get("bw", 0)
        if known_bw <= 1e6:
            # Dar kanal: kanal BW/2 + tolerans
            effective_range = known_bw / 2.0 + tolerance_hz
        else:
            # Genis bant tahsisi: sadece tolerans
            effective_range = tolerance_hz
        matched = best_diff <= effective_range
    else:
        matched = False

    return matched, best_name, best_diff


def load_iq_file(filepath):
    """
    Cesitli formatlardaki IQ dosyalarini okur.
    GNU Radio .complex64, .npy, .raw dosyalarini destekler.

    Args:
        filepath: Dosya yolu

    Returns:
        tuple: (iq_data, metadata)
            iq_data: np.ndarray (complex64)
            metadata: dict (sample_rate, center_freq vb. varsa)
    """
    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".npy":
        # usrp_noma formatini dene
        try:
            data, meta = load_iq_data(filepath)
            return data.astype(np.complex64), meta
        except Exception:
            # Duz npy dosyasi
            data = np.load(filepath)
            if np.iscomplexobj(data):
                return data.astype(np.complex64), {}
            # Gercek degerli ise I+jQ olarak yorumla (2 kanal)
            if data.ndim == 2 and data.shape[1] == 2:
                return (data[:, 0] + 1j * data[:, 1]).astype(np.complex64), {}
            return data.astype(np.complex64), {}

    elif ext in (".raw", ".bin", ".complex64", ".cf32", ".fc32"):
        # GNU Radio complex64 formatı (interleaved float32 I/Q)
        raw = np.fromfile(filepath, dtype=np.complex64)
        return raw, {}

    elif ext in (".cf64", ".fc64"):
        # complex128 format
        raw = np.fromfile(filepath, dtype=np.complex128)
        return raw.astype(np.complex64), {}

    elif ext in (".s16", ".sc16", ".cs16"):
        # Signed 16-bit integer interleaved I/Q
        raw = np.fromfile(filepath, dtype=np.int16)
        iq = raw[::2] + 1j * raw[1::2]
        # 16 bit normalizasyon
        iq = (iq / 32768.0).astype(np.complex64)
        return iq, {}

    else:
        # Varsayilan: complex64 olarak dene
        try:
            raw = np.fromfile(filepath, dtype=np.complex64)
            return raw, {}
        except Exception as e:
            raise ValueError(f"Desteklenmeyen dosya formati: {ext}") from e


def rssi_to_power_dBm(rssi_raw_dB, gain_dB, cable_loss_dB=None):
    """
    Ham RSSI degerini (IQ verisinden olculen) kalibre edilmis
    alici guc degerine (dBm) donusturur.

    Args:
        rssi_raw_dB: Ham guc degeri (dB), IQ verisinden hesaplanan
        gain_dB: Alici kazanc degeri (dB)
        cable_loss_dB: Kablo kaybi (dB). None ise config'den.

    Returns:
        float: Kalibre edilmis alici guc (dBm)
    """
    if cable_loss_dB is None:
        cable_loss_dB = det_config.CABLE_LOSS_DB

    # Guc = ham guc - kazanc + kablo kaybi
    # (kazanc sinyal seviyesini arttirir, kablo kaybi dusurur)
    calibrated = rssi_raw_dB - gain_dB + cable_loss_dB
    return calibrated


def generate_report(detections, scan_time=None, output_dir=None):
    """
    Tespit sonuclarini JSON ve okunabilir metin raporu olarak kaydeder.

    Args:
        detections: scan_and_detect() sonucu (dict)
        scan_time: Tarama zamani (datetime). None ise simdi.
        output_dir: Cikti klasoru. None ise config'den.

    Returns:
        str: Rapor dosya yolu
    """
    if scan_time is None:
        scan_time = datetime.now()
    if output_dir is None:
        output_dir = det_config.SURVEILLANCE_REPORT_DIR

    os.makedirs(output_dir, exist_ok=True)

    timestamp = scan_time.strftime("%Y%m%d_%H%M%S")
    json_path = os.path.join(output_dir, f"scan_{timestamp}.json")
    text_path = os.path.join(output_dir, f"scan_{timestamp}.txt")

    # JSON raporu
    report_data = {
        "scan_time": scan_time.isoformat(),
        "total_signals": detections.get("total_signals", 0),
        "legal_count": len(detections.get("legal_signals", [])),
        "suspicious_count": len(detections.get("suspicious_signals", [])),
        "legal_signals": detections.get("legal_signals", []),
        "suspicious_signals": detections.get("suspicious_signals", []),
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)

    # Metin raporu
    lines = [
        "=" * 60,
        "KACAK REPEATER TESPIT RAPORU",
        "=" * 60,
        f"Tarama Zamani : {scan_time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Toplam Sinyal : {report_data['total_signals']}",
        f"Yasal Sinyal  : {report_data['legal_count']}",
        f"Suphe Sinyal  : {report_data['suspicious_count']}",
        "",
    ]

    if detections.get("suspicious_signals"):
        lines.append("-" * 60)
        lines.append("SUPHELI SINYALLER:")
        lines.append("-" * 60)
        for i, sig in enumerate(detections["suspicious_signals"], 1):
            lines.append(f"  [{i}] Frekans : {freq_to_str(sig.get('freq', 0))}")
            lines.append(f"      Guc     : {sig.get('power_dB', 0):.1f} dB")
            lines.append(f"      Skor    : {sig.get('anomaly_score', 0):.2f}")
            lines.append(f"      Seviye  : {sig.get('confidence_level', 'bilinmeyen')}")
            if sig.get("closest_known"):
                lines.append(f"      Yakin   : {sig['closest_known']} "
                             f"(fark: {sig.get('deviation_hz', 0)/1e3:.1f} kHz)")
            lines.append("")

    if detections.get("legal_signals"):
        lines.append("-" * 60)
        lines.append("YASAL SINYALLER:")
        lines.append("-" * 60)
        for sig in detections["legal_signals"]:
            lines.append(f"  {freq_to_str(sig.get('freq', 0)):>14s}  "
                         f"{sig.get('power_dB', 0):>7.1f} dB  "
                         f"{sig.get('matched_name', '')}")

    lines.append("")
    lines.append("=" * 60)

    with open(text_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info("Rapor kaydedildi: %s", json_path)
    return json_path


def format_detection_result(detection_dict):
    """
    Tek bir tespit sonucunu okunabilir (Turkce) formata donusturur.

    Args:
        detection_dict: Tespit bilgileri iceren sozluk

    Returns:
        str: Formatlanmis metin
    """
    freq = detection_dict.get("freq", 0)
    power = detection_dict.get("power_dB", 0)
    score = detection_dict.get("anomaly_score", 0)
    level = detection_dict.get("confidence_level", "bilinmeyen")
    closest = detection_dict.get("closest_known", "-")
    deviation = detection_dict.get("deviation_hz", 0)

    lines = [
        f"Frekans    : {freq_to_str(freq)}",
        f"Guc        : {power:.1f} dB",
        f"Anomali    : {score:.2f} ({level})",
        f"En Yakin   : {closest} (fark: {deviation/1e3:.1f} kHz)",
    ]
    return "\n".join(lines)


def polar_to_cartesian(angle_deg, magnitude):
    """
    Kutupsal koordinatlari kartezyen koordinatlara cevirir.

    Args:
        angle_deg: Aci (derece)
        magnitude: Buyukluk

    Returns:
        tuple: (x, y)
    """
    angle_rad = np.radians(angle_deg)
    x = magnitude * np.cos(angle_rad)
    y = magnitude * np.sin(angle_rad)
    return x, y
