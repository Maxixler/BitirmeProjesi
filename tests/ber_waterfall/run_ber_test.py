# -*- coding: utf-8 -*-
"""
NOMA BER Waterfall Eğrisi Karşılaştırma Testi
===============================================
Bu script, NOMA.grc (LDPC kodlamalı) ve NOMA_ldpcsiz.grc (LDPC'siz) sistemlerinin
BER (Bit Error Rate) performansını farklı Eb/N0 seviyelerinde ölçer ve
karşılaştırmalı bir waterfall eğrisi çizer.

Çıktılar:
  - ber_results.json  : Ham BER verileri
  - ber_waterfall.png : Karşılaştırmalı BER waterfall grafiği

Yazarlar: Armağan Bi - Eren Kale
"""

import subprocess
import time
import os
import re
import json
import math
import sys

# Windows konsolunda UTF-8 karakter desteği
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

# ==============================================================================
# YAPILANDIRMA
# ==============================================================================

# Python yolu (radioconda)
PYTHON_EXE = r"C:\Users\Armagan\radioconda\python.exe"

# Proje kök dizini
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# Flow graph Python dosyaları
NOMA_LDPC_PY = os.path.join(PROJECT_DIR, "NOMA.py")
NOMA_NO_LDPC_PY = os.path.join(PROJECT_DIR, "NOMA_ldpcsiz.py")

# TX/RX dosya yolları (her iki flow graph da aynı dosyaları kullanır)
TRANSMIT_1 = os.path.join(PROJECT_DIR, "bpsk_transmit.txt")
TRANSMIT_2 = os.path.join(PROJECT_DIR, "bpsk_transmit_2.txt")
RECEIVE_1 = os.path.join(PROJECT_DIR, "bpsk_receive.txt")
RECEIVE_2 = os.path.join(PROJECT_DIR, "bpsk_receive_2.txt")
DEBUG_SIC = os.path.join(PROJECT_DIR, "debug_sic.txt")

# Test parametreleri
EBN0_RANGE_DB = list(range(0, 15))  # 0 dB -> 14 dB (15 nokta)
SIMULATION_DURATION = 120            # Her SNR noktası için saniye
NUM_PACKETS = 200                    # Her kullanıcı için paket sayısı
PAYLOAD_SIZE = 77                    # Bayt/paket

# Kanal parametreleri (gerçekçi değerler)
FREQ_OFFSET = 0.01
TIME_OFFSET = 1.0001

# Çıktı dosyaları
RESULTS_JSON = os.path.join(PROJECT_DIR, "ber_results.json")
WATERFALL_PNG = os.path.join(PROJECT_DIR, "ber_waterfall.png")


# ==============================================================================
# YARDIMCI FONKSİYONLAR
# ==============================================================================

def ebn0_to_noise_voltage(ebn0_db):
    """
    Eb/N0 (dB) değerini GNU Radio channel_model noise_voltage (σ) değerine çevirir.

    BPSK için:  Eb/N0 = 1 / (2σ²)
    Dolayısıyla: σ = sqrt(1 / (2 * 10^(Eb_N0_dB / 10)))
    """
    ebn0_linear = 10 ** (ebn0_db / 10.0)
    sigma = math.sqrt(1.0 / (2.0 * ebn0_linear))
    return sigma


def create_test_payload(num_packets=50, payload_size=77):
    """
    Deterministik test verisi oluşturur.
    Her paket farklı bir karakter paterni içerir.
    """
    content = ""
    for p in range(num_packets):
        char = str(p % 10)
        content += char * payload_size
    return content


def prepare_tx_files():
    """TX dosyalarını deterministik test verisi ile oluşturur."""
    tx1_data = create_test_payload(NUM_PACKETS, PAYLOAD_SIZE)
    tx2_data = ""
    for p in range(NUM_PACKETS):
        char = str((9 - p) % 10)
        tx2_data += char * PAYLOAD_SIZE

    with open(TRANSMIT_1, "w") as f:
        f.write(tx1_data)
    with open(TRANSMIT_2, "w") as f:
        f.write(tx2_data)


def clean_rx_files():
    """Eski RX çıktılarını temizler."""
    for fpath in [RECEIVE_1, RECEIVE_2, DEBUG_SIC]:
        if os.path.exists(fpath):
            try:
                os.remove(fpath)
            except Exception:
                with open(fpath, "w") as f:
                    f.write("")


def modify_noise_parameter(py_file, noise_voltage):
    """
    Flow graph Python dosyasındaki noise parametresini değiştirir.
    Diğer kanal parametreleri (freq_offset, time_offset) mevcut değerlerde kalır.
    """
    with open(py_file, "r", encoding="utf-8") as f:
        content = f.read()

    # noise parametresini değiştir
    content = re.sub(
        r"self\.noise = noise = [\d.]+",
        f"self.noise = noise = {noise_voltage:.6f}",
        content
    )

    with open(py_file, "w", encoding="utf-8") as f:
        f.write(content)


def restore_default_parameters(py_file):
    """Flow graph parametrelerini varsayılan değerlere geri yükler."""
    modify_noise_parameter(py_file, 0.1)


def run_simulation(py_file, duration=120):
    """
    Flow graph'ı subprocess olarak başlatır, belirtilen süre bekler ve kapatır.
    """
    script_name = os.path.basename(py_file)
    print(f"    -> Simulasyon baslatiliyor: {script_name} ({duration}s)...", end="", flush=True)

    proc = subprocess.Popen(
        [PYTHON_EXE, py_file],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=PROJECT_DIR
    )

    time.sleep(duration)

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=3)

    print(" Tamamlandi.")


def calculate_ber(tx_path, rx_path):
    """
    TX ve RX dosyalarını bit-seviyesinde karşılaştırarak BER hesaplar.

    Returns:
        dict: {
            'ber': float,           # Bit Error Rate
            'error_bits': int,      # Hatalı bit sayısı
            'total_bits': int,      # Karşılaştırılan toplam bit sayısı
            'tx_bytes': int,        # Gönderilen bayt sayısı
            'rx_bytes': int,        # Alınan bayt sayısı
            'packet_loss_ratio': float  # Paket kaybı oranı
        }
    """
    # Dosyaları binary modda oku
    with open(tx_path, "rb") as f:
        tx_data = f.read()
    
    rx_data = b""
    if os.path.exists(rx_path) and os.path.getsize(rx_path) > 0:
        with open(rx_path, "rb") as f:
            rx_data = f.read()

    tx_len = len(tx_data)
    rx_len = len(rx_data)

    if tx_len == 0:
        return {
            'ber': 0.5,
            'error_bits': 0,
            'total_bits': 0,
            'tx_bytes': 0,
            'rx_bytes': 0,
            'packet_loss_ratio': 1.0
        }

    # Alınan kısımdaki bit hatalarını say
    compare_len = min(tx_len, rx_len)
    error_bits = 0
    for i in range(compare_len):
        xor_byte = tx_data[i] ^ rx_data[i]
        error_bits += bin(xor_byte).count('1')

    # Alınmayan kısım: %50 hata (rastgele tahmin) olarak kabul et
    missing_bytes = tx_len - rx_len
    if missing_bytes > 0:
        error_bits += missing_bytes * 4  # 8 bit * 0.5 = 4 hatalı bit/bayt

    total_bits = tx_len * 8
    ber = error_bits / total_bits if total_bits > 0 else 0.5

    # BER'i makul sınırlarda tut
    ber = min(ber, 0.5)

    packet_loss = max(0, (tx_len - rx_len)) / tx_len if tx_len > 0 else 1.0

    return {
        'ber': ber,
        'error_bits': error_bits,
        'total_bits': total_bits,
        'tx_bytes': tx_len,
        'rx_bytes': rx_len,
        'packet_loss_ratio': packet_loss
    }


def theoretical_bpsk_ber(ebn0_db):
    """Teorik BPSK BER hesaplar: BER = 0.5 * erfc(sqrt(Eb/N0))"""
    ebn0_linear = 10 ** (ebn0_db / 10.0)
    return 0.5 * math.erfc(math.sqrt(ebn0_linear))


def plot_waterfall(results):
    """
    BER waterfall eğrisi çizer.
    Akademik yayın kalitesinde matplotlib grafiği oluşturur.
    """
    try:
        import matplotlib
        matplotlib.use('Agg')  # GUI olmadan çalıştır
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("\n[UYARI] matplotlib bulunamadı. Grafik oluşturulamadı.")
        print("Kurulum: pip install matplotlib")
        return

    fig, ax = plt.subplots(figsize=(11, 8))

    ebn0_values = results['ebn0_db']
    min_ber = 1e-6

    # --- Teorik BPSK referans eğrisi ---
    ebn0_fine = np.linspace(0, 14, 100)
    ber_theory = [theoretical_bpsk_ber(x) for x in ebn0_fine]
    ax.semilogy(ebn0_fine, ber_theory, 'k--', linewidth=1.5, alpha=0.6,
                label='Teorik BPSK (Referans)')

    # --- Eski 50-paket test sonuçlarını yükle ve çiz (varsa) ---
    results_50_path = os.path.join(PROJECT_DIR, "ber_results_50.json")
    if os.path.exists(results_50_path):
        try:
            with open(results_50_path, 'r', encoding='utf-8') as f:
                res_50 = json.load(f)
            ebn0_50 = res_50['ebn0_db']
            
            # LDPC 50 pkts (User 1 & 2)
            u1_50 = [max(b, min_ber) if b > 0 else min_ber for b in res_50['ldpc']['user1_ber']]
            u2_50 = [max(b, min_ber) if b > 0 else min_ber for b in res_50['ldpc']['user2_ber']]
            ax.semilogy(ebn0_50, u1_50, 'b--', linewidth=1, alpha=0.4, label='LDPC U1 (Near, 50 pkts)')
            ax.semilogy(ebn0_50, u2_50, 'g--', linewidth=1, alpha=0.4, label='LDPC U2 (Far, 50 pkts)')
            
            # NoLDPC 50 pkts (User 1 & 2)
            no_u1_50 = [max(b, min_ber) if b > 0 else min_ber for b in res_50['no_ldpc']['user1_ber']]
            no_u2_50 = [max(b, min_ber) if b > 0 else min_ber for b in res_50['no_ldpc']['user2_ber']]
            ax.semilogy(ebn0_50, no_u1_50, 'r--', linewidth=1, alpha=0.4, label='NoLDPC U1 (Near, 50 pkts)')
            ax.semilogy(ebn0_50, no_u2_50, '--', color='orange', linewidth=1, alpha=0.4, label='NoLDPC U2 (Far, 50 pkts)')
            print("[INFO] Eski 50-paket test verileri grafige eklendi.")
        except Exception as e:
            print(f"[UYARI] Eski 50-paket verileri yuklenirken hata olustu: {e}")

    # --- NOMA + LDPC eğrileri (200 paket) ---
    ber_ldpc_u1 = results['ldpc']['user1_ber']
    ber_ldpc_u2 = results['ldpc']['user2_ber']

    # Sıfır BER'leri grafik alt sınırına çek (log ölçekte 0 çizilemez)
    ber_ldpc_u1_plot = [max(b, min_ber) if b > 0 else min_ber for b in ber_ldpc_u1]
    ber_ldpc_u2_plot = [max(b, min_ber) if b > 0 else min_ber for b in ber_ldpc_u2]

    ax.semilogy(ebn0_values, ber_ldpc_u1_plot, 'b-o', linewidth=2, markersize=7,
                markerfacecolor='blue', label='NOMA + LDPC - User 1 (Near, 200 pkts)')
    ax.semilogy(ebn0_values, ber_ldpc_u2_plot, 'g-s', linewidth=2, markersize=7,
                markerfacecolor='green', label='NOMA + LDPC - User 2 (Far, SIC, 200 pkts)')

    # --- NOMA LDPC'siz eğrileri (200 paket) ---
    ber_noldpc_u1 = results['no_ldpc']['user1_ber']
    ber_noldpc_u2 = results['no_ldpc']['user2_ber']

    ber_noldpc_u1_plot = [max(b, min_ber) if b > 0 else min_ber for b in ber_noldpc_u1]
    ber_noldpc_u2_plot = [max(b, min_ber) if b > 0 else min_ber for b in ber_noldpc_u2]

    ax.semilogy(ebn0_values, ber_noldpc_u1_plot, 'r-^', linewidth=2, markersize=7,
                markerfacecolor='red', label='NOMA LDPC\'siz - User 1 (Near, 200 pkts)')
    ax.semilogy(ebn0_values, ber_noldpc_u2_plot, '-D', color='orange', linewidth=2,
                markersize=7, markerfacecolor='orange',
                label='NOMA LDPC\'siz - User 2 (Far, SIC, 200 pkts)')

    # --- Grafik formatı ---
    ax.set_xlabel(r'$E_b/N_0$ (dB)', fontsize=14)
    ax.set_ylabel('Bit Error Rate (BER)', fontsize=14)
    ax.set_title('NOMA Sistemi BER Waterfall Karsilastirmasi\n'
                 r'(LDPC IEEE 802.11n 1296/648 rate-1/2 vs Kodlamasiz | 50 vs 200 Paket)',
                 fontsize=13, fontweight='bold')

    ax.set_xlim([-0.5, 14.5])
    ax.set_ylim([min_ber / 2, 1])
    ax.grid(True, which='both', alpha=0.3)
    ax.legend(loc='lower left', fontsize=9, framealpha=0.9, ncol=2)
    ax.tick_params(axis='both', labelsize=11)

    # Güç katsayıları bilgisi
    ax.text(0.98, 0.98,
            r'$\alpha_1^2=0.8$ (Near), $\alpha_2^2=0.2$ (Far)'
            '\nDBPSK, SPS=4, Freq Offset=0.01'
            '\nSIC: Cross-Correlation Alignment',
            transform=ax.transAxes, fontsize=8,
            verticalalignment='top', horizontalalignment='right',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='wheat', alpha=0.7))

    plt.tight_layout()
    plt.savefig(WATERFALL_PNG, dpi=200, bbox_inches='tight')
    print(f"\n[OK] Waterfall grafigi kaydedildi: {WATERFALL_PNG}")
    plt.close()


# ==============================================================================
# ANA TEST DÖNGÜSÜ
# ==============================================================================

def main():
    print("=" * 70)
    print("    NOMA BER WATERFALL EGRISI KARSILASTIRMA TESTI")
    print("    LDPC Kodlamali (NOMA.grc) vs LDPC'siz (NOMA_ldpcsiz.grc)")
    print("=" * 70)
    print(f"\n  Eb/N0 Araligi  : {EBN0_RANGE_DB[0]} - {EBN0_RANGE_DB[-1]} dB ({len(EBN0_RANGE_DB)} nokta)")
    print(f"  Simulasyon Suresi: {SIMULATION_DURATION}s / nokta")
    print(f"  Kanal Parametreleri: freq_offset={FREQ_OFFSET}, time_offset={TIME_OFFSET}")
    total_time_min = len(EBN0_RANGE_DB) * 2 * SIMULATION_DURATION / 60
    print(f"  Tahmini Toplam Sure: ~{total_time_min:.0f} dakika")
    print(f"  Baslangic: {time.strftime('%H:%M:%S')}")
    print("=" * 70)

    # TX dosyalarını hazırla
    prepare_tx_files()

    # Sonuç veri yapısı
    results = {
        'ebn0_db': EBN0_RANGE_DB,
        'noise_voltages': [],
        'ldpc': {
            'user1_ber': [], 'user2_ber': [],
            'user1_details': [], 'user2_details': []
        },
        'no_ldpc': {
            'user1_ber': [], 'user2_ber': [],
            'user1_details': [], 'user2_details': []
        },
        'theoretical_bpsk_ber': [],
        'test_params': {
            'simulation_duration': SIMULATION_DURATION,
            'num_packets': NUM_PACKETS,
            'payload_size': PAYLOAD_SIZE,
            'freq_offset': FREQ_OFFSET,
            'time_offset': TIME_OFFSET
        }
    }

    # Her SNR noktası için test döngüsü
    for idx, ebn0 in enumerate(EBN0_RANGE_DB):
        sigma = ebn0_to_noise_voltage(ebn0)
        results['noise_voltages'].append(sigma)
        results['theoretical_bpsk_ber'].append(theoretical_bpsk_ber(ebn0))

        print(f"\n{'-' * 60}")
        print(f"  [{idx+1}/{len(EBN0_RANGE_DB)}] Eb/N0 = {ebn0} dB  |  noise_voltage = {sigma:.4f}")
        print(f"{'-' * 60}")

        # ========================
        # 1) NOMA + LDPC Testi
        # ========================
        print(f"\n  [LDPC] NOMA + LDPC (NOMA.py):")
        clean_rx_files()
        modify_noise_parameter(NOMA_LDPC_PY, sigma)
        run_simulation(NOMA_LDPC_PY, SIMULATION_DURATION)

        ber_u1 = calculate_ber(TRANSMIT_1, RECEIVE_1)
        ber_u2 = calculate_ber(TRANSMIT_2, RECEIVE_2)

        results['ldpc']['user1_ber'].append(ber_u1['ber'])
        results['ldpc']['user2_ber'].append(ber_u2['ber'])
        results['ldpc']['user1_details'].append(ber_u1)
        results['ldpc']['user2_details'].append(ber_u2)

        print(f"    User 1 BER: {ber_u1['ber']:.2e}  "
              f"(RX: {ber_u1['rx_bytes']}/{ber_u1['tx_bytes']} byte, "
              f"Loss: {ber_u1['packet_loss_ratio']:.1%})")
        print(f"    User 2 BER: {ber_u2['ber']:.2e}  "
              f"(RX: {ber_u2['rx_bytes']}/{ber_u2['tx_bytes']} byte, "
              f"Loss: {ber_u2['packet_loss_ratio']:.1%})")

        # ========================
        # 2) NOMA LDPC'siz Testi
        # ========================
        print(f"\n  [NoLDPC] NOMA LDPC'siz (NOMA_ldpcsiz.py):")
        clean_rx_files()
        modify_noise_parameter(NOMA_NO_LDPC_PY, sigma)
        run_simulation(NOMA_NO_LDPC_PY, SIMULATION_DURATION)

        ber_u1 = calculate_ber(TRANSMIT_1, RECEIVE_1)
        ber_u2 = calculate_ber(TRANSMIT_2, RECEIVE_2)

        results['no_ldpc']['user1_ber'].append(ber_u1['ber'])
        results['no_ldpc']['user2_ber'].append(ber_u2['ber'])
        results['no_ldpc']['user1_details'].append(ber_u1)
        results['no_ldpc']['user2_details'].append(ber_u2)

        print(f"    User 1 BER: {ber_u1['ber']:.2e}  "
              f"(RX: {ber_u1['rx_bytes']}/{ber_u1['tx_bytes']} byte, "
              f"Loss: {ber_u1['packet_loss_ratio']:.1%})")
        print(f"    User 2 BER: {ber_u2['ber']:.2e}  "
              f"(RX: {ber_u2['rx_bytes']}/{ber_u2['tx_bytes']} byte, "
              f"Loss: {ber_u2['packet_loss_ratio']:.1%})")

        # Ara sonuclari JSON'a kaydet (crash durumunda veri kaybini onle)
        with open(RESULTS_JSON, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

    # ========================
    # Parametreleri varsayılana geri yükle
    # ========================
    restore_default_parameters(NOMA_LDPC_PY)
    restore_default_parameters(NOMA_NO_LDPC_PY)

    # ========================
    # Sonuçları kaydet ve çiz
    # ========================
    with open(RESULTS_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n[OK] BER sonuclari kaydedildi: {RESULTS_JSON}")

    # Waterfall grafiği çiz
    plot_waterfall(results)

    # ========================
    # Özet tablosu yazdır
    # ========================
    print(f"\n{'=' * 80}")
    print("  SONUC OZETI")
    print(f"{'=' * 80}")
    print(f"{'Eb/N0':>6s} | {'sigma':>8s} | {'LDPC U1':>10s} | {'LDPC U2':>10s} | "
          f"{'NoLDPC U1':>10s} | {'NoLDPC U2':>10s} | {'Teorik':>10s}")
    print("-" * 80)

    for i, ebn0 in enumerate(EBN0_RANGE_DB):
        print(f"{ebn0:>5d}dB | {results['noise_voltages'][i]:>8.4f} | "
              f"{results['ldpc']['user1_ber'][i]:>10.2e} | "
              f"{results['ldpc']['user2_ber'][i]:>10.2e} | "
              f"{results['no_ldpc']['user1_ber'][i]:>10.2e} | "
              f"{results['no_ldpc']['user2_ber'][i]:>10.2e} | "
              f"{results['theoretical_bpsk_ber'][i]:>10.2e}")

    print(f"\n{'=' * 80}")
    print(f"  Test tamamlandi: {time.strftime('%H:%M:%S')}")
    print(f"{'=' * 80}")


if __name__ == '__main__':
    main()
