"""
USRP E310 & LoRaWAN Sinyal Analiz Projesi - Merkezi Konfigurasyon
"""

# ---------------------------------------------------------------------------
# USRP E310 Ayarlari
# ---------------------------------------------------------------------------
USRP_ADDR = "192.168.10.2"
HOST_ADDR = "192.168.10.1"

# Calisma modu: "embedded" (dogrudan E310 uzerinde) veya "network" (host uzerinden)
DEFAULT_MODE = "network"

# UHD cihaz argumanlari
DEVICE_ARGS = {
    "embedded": "",                        # E310 uzerinde calisirken
    "network": f"addr={USRP_ADDR}",        # Host uzerinden erisirken
}

# ---------------------------------------------------------------------------
# Varsayilan SDR Parametreleri
# ---------------------------------------------------------------------------
DEFAULT_SAMPLE_RATE = 1e6       # 1 MHz
DEFAULT_RX_GAIN = 40            # dB
DEFAULT_TX_GAIN = 40            # dB
DEFAULT_CENTER_FREQ = 868e6     # 868 MHz (LoRaWAN)
DEFAULT_ANTENNA = "TX/RX"
DEFAULT_FFT_SIZE = 1024
DEFAULT_CAPTURE_DURATION = 1.0  # saniye

# ---------------------------------------------------------------------------
# Anten Bilgileri (MRTK-Q7027I28 veri sayfasindan)
# ---------------------------------------------------------------------------
ANTENNA_INFO = {
    "model": "MRTK-Q7027I28",
    "type": "LTE/4G Omni-Directional",
    "connector": "SMA Male",
    "gain_dBi": 7,
    "impedance_ohm": 50,
    "vswr_max": 2.0,
    "max_power_W": 50,
    "polarization": "Vertical",
    "radiation": "Omni-Direction",
    "cable_type": "RG174",
    "cable_length_m": 3,
    "operating_temp_min_C": -40,
    "operating_temp_max_C": 70,
}

# ---------------------------------------------------------------------------
# Frekans Bantlari (Anten destekli)
# ---------------------------------------------------------------------------
BAND_LOW = {
    "name": "Alt Bant (698-960 MHz)",
    "start_freq": 698e6,
    "stop_freq": 960e6,
    "description": "LoRa, GSM 900, LTE Band 8/20",
}

BAND_HIGH = {
    "name": "Ust Bant (1710-2700 MHz)",
    "start_freq": 1710e6,
    "stop_freq": 2700e6,
    "description": "LTE Band 1/3/7, GSM 1800, UMTS, WiFi 2.4 GHz",
}

FREQUENCY_BANDS = [BAND_LOW, BAND_HIGH]

# ---------------------------------------------------------------------------
# Bilinen Frekanslar (Tarama icin referans)
# ---------------------------------------------------------------------------
KNOWN_FREQUENCIES = {
    "LoRaWAN EU868": {"freq": 868e6, "bw": 125e3, "band": "low"},
    "LoRaWAN EU868.3": {"freq": 868.3e6, "bw": 125e3, "band": "low"},
    "LoRaWAN EU868.5": {"freq": 868.5e6, "bw": 125e3, "band": "low"},
    "LoRaWAN US915": {"freq": 915e6, "bw": 125e3, "band": "low"},
    "GSM 900 UL": {"freq": 890e6, "bw": 200e3, "band": "low"},
    "GSM 900 DL": {"freq": 935e6, "bw": 200e3, "band": "low"},
    "LTE Band 20 DL": {"freq": 796e6, "bw": 10e6, "band": "low"},
    "GSM 1800 UL": {"freq": 1710e6, "bw": 200e3, "band": "high"},
    "GSM 1800 DL": {"freq": 1805e6, "bw": 200e3, "band": "high"},
    "UMTS Band 1 DL": {"freq": 2140e6, "bw": 5e6, "band": "high"},
    "LTE Band 3 DL": {"freq": 1842.5e6, "bw": 20e6, "band": "high"},
    "LTE Band 7 DL": {"freq": 2655e6, "bw": 20e6, "band": "high"},
    "WiFi Ch1 2.4G": {"freq": 2412e6, "bw": 20e6, "band": "high"},
    "WiFi Ch6 2.4G": {"freq": 2437e6, "bw": 20e6, "band": "high"},
    "WiFi Ch11 2.4G": {"freq": 2462e6, "bw": 20e6, "band": "high"},
}

# ---------------------------------------------------------------------------
# LoRa Parametreleri
# ---------------------------------------------------------------------------
LORA_DEFAULT_SF = 7             # Spreading Factor (7-12)
LORA_DEFAULT_BW = 125e3         # Bant genisligi (Hz)
LORA_DEFAULT_CR = 1             # Coding Rate (1=4/5, 2=4/6, 3=4/7, 4=4/8)
LORA_DEFAULT_FREQ = 868e6       # Merkez frekans
LORA_PREAMBLE_LEN = 8          # Preamble sembol sayisi
LORA_SYNC_WORD = 0x34           # LoRaWAN public sync word

# ---------------------------------------------------------------------------
# Frekans Tarama Ayarlari
# ---------------------------------------------------------------------------
SCAN_STEP_LOW = 200e3           # Alt bant tarama adimi (200 kHz)
SCAN_STEP_HIGH = 1e6            # Ust bant tarama adimi (1 MHz)
SCAN_DWELL_TIME = 0.05          # Her adimda bekleme suresi (saniye)
SCAN_THRESHOLD_DB = -50         # Sinyal tespit esigi (dBm)

# ---------------------------------------------------------------------------
# ZMQ Ayarlari
# ---------------------------------------------------------------------------
ZMQ_PORT = 5555
ZMQ_PROTOCOL = "tcp"
ZMQ_BIND_ADDR = f"{ZMQ_PROTOCOL}://*:{ZMQ_PORT}"
ZMQ_CONNECT_ADDR = f"{ZMQ_PROTOCOL}://{USRP_ADDR}:{ZMQ_PORT}"

# ---------------------------------------------------------------------------
# Dosya Kayit Ayarlari
# ---------------------------------------------------------------------------
DATA_DIR = "data"
DEFAULT_FILE_FORMAT = "npy"     # "npy" veya "raw"

# ---------------------------------------------------------------------------
# NOMA (Non-Orthogonal Multiple Access) Parametreleri
# ---------------------------------------------------------------------------
NOMA_NUM_USERS = 2              # Varsayilan kullanici sayisi
NOMA_MAX_USERS = 4              # Maksimum desteklenen kullanici

# Guc katsayilari (toplam = 1.0, zayif kanalli kullaniciya daha fazla guc)
NOMA_POWER_COEFFICIENTS = {
    2: [0.75, 0.25],
    3: [0.60, 0.25, 0.15],
    4: [0.50, 0.25, 0.15, 0.10],
}

NOMA_DEFAULT_MODULATION = "QPSK"       # "QPSK", "16QAM", "64QAM"
NOMA_BITS_PER_SYMBOL = {
    "QPSK": 2,
    "16QAM": 4,
    "64QAM": 6,
}

# Simulasyon parametreleri
NOMA_SNR_MIN_DB = -5
NOMA_SNR_MAX_DB = 30
NOMA_SNR_STEP_DB = 1
NOMA_NUM_SYMBOLS = 100000       # BER hesaplamasinda kullanilacak sembol sayisi
NOMA_BITS_PER_FRAME = 1024      # Cerceve basina bit sayisi

# ---------------------------------------------------------------------------
# Grafik Ayarlari
# ---------------------------------------------------------------------------
PLOT_FIGURE_SIZE = (12, 8)
PLOT_DPI = 150
PLOT_SAVE_FORMAT = "png"
PLOT_OUTPUT_DIR = "results"
