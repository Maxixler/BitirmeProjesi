"""
Kacak Repeater Tespit Sistemi - Merkezi Konfigurasyon

Ana proje (usrp_noma) konfigurasyonunu dahil eder ve
alt projeye ozgu parametreleri tanimlar.
"""

import os
import sys

# Ana proje kokunu Python yoluna ekle (standalone calisma icin)
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# ---------------------------------------------------------------------------
# Ana Proje Konfigurasyonundan Import
# ---------------------------------------------------------------------------
from usrp_noma.config import (
    USRP_ADDR, HOST_ADDR, DEFAULT_MODE, DEVICE_ARGS,
    DEFAULT_SAMPLE_RATE, DEFAULT_RX_GAIN, DEFAULT_TX_GAIN,
    DEFAULT_CENTER_FREQ, DEFAULT_ANTENNA, DEFAULT_FFT_SIZE,
    DEFAULT_CAPTURE_DURATION,
    ANTENNA_INFO, BAND_LOW, BAND_HIGH, FREQUENCY_BANDS,
    KNOWN_FREQUENCIES,
    SCAN_STEP_LOW, SCAN_STEP_HIGH, SCAN_DWELL_TIME, SCAN_THRESHOLD_DB,
    PLOT_FIGURE_SIZE, PLOT_DPI, PLOT_OUTPUT_DIR,
)

# ---------------------------------------------------------------------------
# Alt Bant Tanimlari (Anten destegi dahilinde filtreleme)
# ---------------------------------------------------------------------------
SCAN_SUB_BANDS = {
    "698-960 MHz": {
        "start": 698e6,
        "stop": 960e6,
        "step": 200e3,
        "description": "Alt bant: LoRa, GSM 900, LTE Band 8/20",
    },
    "1710-1800 MHz": {
        "start": 1710e6,
        "stop": 1800e6,
        "step": 500e3,
        "description": "GSM 1800 UL, LTE Band 3 UL",
    },
    "1800-2100 MHz": {
        "start": 1800e6,
        "stop": 2100e6,
        "step": 1e6,
        "description": "GSM 1800 DL, LTE Band 3 DL, UMTS Band 1",
    },
    "2100-2700 MHz": {
        "start": 2100e6,
        "stop": 2700e6,
        "step": 1e6,
        "description": "UMTS DL, LTE Band 7, WiFi 2.4 GHz",
    },
}

# ---------------------------------------------------------------------------
# Turkiye Operator Frekanslari
# ---------------------------------------------------------------------------
TURKEY_OPERATOR_FREQUENCIES = {
    # GSM 900 Band
    "GSM 900 UL (Turkcell)": {"freq": 897.5e6, "bw": 5e6, "band": "900"},
    "GSM 900 DL (Turkcell)": {"freq": 942.5e6, "bw": 5e6, "band": "900"},
    "GSM 900 UL (Vodafone)": {"freq": 890e6, "bw": 5e6, "band": "900"},
    "GSM 900 DL (Vodafone)": {"freq": 935e6, "bw": 5e6, "band": "900"},
    "GSM 900 UL (Turk Telekom)": {"freq": 902.5e6, "bw": 5e6, "band": "900"},
    "GSM 900 DL (Turk Telekom)": {"freq": 947.5e6, "bw": 5e6, "band": "900"},
    # GSM 1800 Band
    "GSM 1800 UL (Turkcell)": {"freq": 1732.5e6, "bw": 15e6, "band": "1800"},
    "GSM 1800 DL (Turkcell)": {"freq": 1827.5e6, "bw": 15e6, "band": "1800"},
    "GSM 1800 UL (Vodafone)": {"freq": 1752.5e6, "bw": 10e6, "band": "1800"},
    "GSM 1800 DL (Vodafone)": {"freq": 1847.5e6, "bw": 10e6, "band": "1800"},
    "GSM 1800 UL (Turk Telekom)": {"freq": 1767.5e6, "bw": 10e6, "band": "1800"},
    "GSM 1800 DL (Turk Telekom)": {"freq": 1862.5e6, "bw": 10e6, "band": "1800"},
    # UMTS 2100 Band
    "UMTS 2100 UL": {"freq": 1950e6, "bw": 60e6, "band": "2100"},
    "UMTS 2100 DL": {"freq": 2140e6, "bw": 60e6, "band": "2100"},
    # LTE Band 3 (1800 MHz)
    "LTE B3 DL (Turkcell)": {"freq": 1842.5e6, "bw": 20e6, "band": "1800"},
    "LTE B3 DL (Vodafone)": {"freq": 1855e6, "bw": 10e6, "band": "1800"},
    # LTE Band 7 (2600 MHz)
    "LTE B7 DL (Turkcell)": {"freq": 2630e6, "bw": 20e6, "band": "2600"},
    "LTE B7 DL (Vodafone)": {"freq": 2650e6, "bw": 20e6, "band": "2600"},
    "LTE B7 DL (Turk Telekom)": {"freq": 2670e6, "bw": 20e6, "band": "2600"},
    # LTE Band 20 (800 MHz)
    "LTE B20 UL": {"freq": 842e6, "bw": 10e6, "band": "800"},
    "LTE B20 DL": {"freq": 801e6, "bw": 10e6, "band": "800"},
}

# Tum bilinen yasal frekanslar (ana proje + Turkiye operatorleri)
ALL_KNOWN_FREQUENCIES = {**KNOWN_FREQUENCIES, **TURKEY_OPERATOR_FREQUENCIES}

# ---------------------------------------------------------------------------
# Anomali Tespit Esikleri
# ---------------------------------------------------------------------------
ANOMALY_POWER_THRESHOLD_DB = -40       # Bu seviyenin uzerindeki bilinmeyen sinyal -> suphe
ANOMALY_BW_TOLERANCE_HZ = 50e3        # Bilinen frekanstan tolerans (Hz)
ANOMALY_MIN_DURATION_SEC = 0.5        # Gecici girisimleri filtrele (saniye)
ANOMALY_SCORE_WEIGHTS = {
    "deviation": 0.4,                  # Bilinen frekanstan sapma agirlik
    "power": 0.35,                     # Sinyal gucu agirlik
    "bandwidth": 0.25,                 # Bant genisligi uyumu agirlik
}
ANOMALY_CONFIDENCE_LEVELS = {
    "dusuk": 0.3,
    "orta": 0.6,
    "yuksek": 0.85,
}

# ---------------------------------------------------------------------------
# Yol Kaybi Modeli Parametreleri
# ---------------------------------------------------------------------------
SPEED_OF_LIGHT = 3e8                   # m/s

# Varsayilan verici parametreleri (tipik kacak repeater)
TX_POWER_DBM = 40.0                    # Verici cikis gucu (dBm) ~ 10W
TX_ANTENNA_GAIN_DBI = 6.0             # Verici anten kazanci (dBi)
RX_ANTENNA_GAIN_DBI = 7.0             # Alici anten kazanci (dBi) — MRTK-Q7027I28
CABLE_LOSS_DB = 2.0                    # Kablo kaybi (dB)

# Referans mesafe
PATH_LOSS_D0 = 1.0                     # Referans mesafe (metre)

# Ortam tipleri ve karsilik gelen path-loss exponent degerleri
ENVIRONMENT_MODELS = {
    "serbest_uzay": {
        "n": 2.0,
        "sigma": 0.0,
        "aciklama": "Engelsiz acik alan (FSPL)",
    },
    "kirsal": {
        "n": 2.5,
        "sigma": 3.0,
        "aciklama": "Kirsal / acik alan",
    },
    "banliyo": {
        "n": 2.8,
        "sigma": 4.0,
        "aciklama": "Banliyolerde, az yogunluklu yerlesim",
    },
    "kentsel": {
        "n": 3.2,
        "sigma": 5.0,
        "aciklama": "Sehir ici, orta yogunluk",
    },
    "yogun_kentsel": {
        "n": 3.8,
        "sigma": 7.0,
        "aciklama": "Yogun sehir merkezi, cok katli binalar",
    },
    "bina_ici": {
        "n": 4.5,
        "sigma": 8.0,
        "aciklama": "Bina ici yayilim",
    },
}

# ---------------------------------------------------------------------------
# Yon Bulma Parametreleri
# ---------------------------------------------------------------------------
DF_NUM_MEASUREMENTS = 36               # 360 / 36 = her 10 derecede bir olcum
DF_MEASUREMENT_DURATION_SEC = 0.5      # Her olcum suresi (saniye)
DF_ANGULAR_RESOLUTION_DEG = 10.0       # Aci cozunurlugu (derece)
DF_SMOOTHING_WINDOW = 5               # Hareketli ortalama pencere boyutu
DF_PEAK_MIN_PROMINENCE_DB = 6.0       # Tepe belirginlik esigi (dB)

# ---------------------------------------------------------------------------
# Gozetleme (Surveillance) Parametreleri
# ---------------------------------------------------------------------------
SURVEILLANCE_SCAN_INTERVAL_SEC = 60    # Periyodik tarama araligi (saniye)
SURVEILLANCE_HISTORY_SIZE = 100        # Son N tarama sonucunu sakla
SURVEILLANCE_REPORT_DIR = os.path.join(PLOT_OUTPUT_DIR, "repeater_reports")

# ---------------------------------------------------------------------------
# Simulasyon Varsayilanlari
# ---------------------------------------------------------------------------
SIM_NUM_LEGAL_SIGNALS = 5              # Senaryodaki yasal sinyal sayisi
SIM_NUM_ILLEGAL_SIGNALS = 2            # Senaryodaki kacak sinyal sayisi
SIM_SNR_RANGE_DB = [5, 10, 15, 20, 25, 30]
SIM_DEFAULT_DISTANCE_M = 500.0        # Varsayilan kacak vericiye mesafe (m)
SIM_NOISE_FLOOR_DBM = -100.0          # Gurultu tabani (dBm)
SIM_DEFAULT_SAMPLE_RATE = 1e6         # Simulasyon ornekleme hizi
