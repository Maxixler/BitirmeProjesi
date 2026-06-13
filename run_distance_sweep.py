# -*- coding: utf-8 -*-
"""
BPSK NOMA Distance Sweep Test Script (ASCII safe with throttle mod)
-------------------------------------------------------------------
"""

import subprocess
import time
import os
import re
import math
import numpy as np
import shutil

# Dosya yollari
TRANSMIT_1_PATH = "bpsk_transmit.txt"
TRANSMIT_2_PATH = "bpsk_transmit_2.txt"
RECEIVE_1_PATH = "bpsk_receive.txt"
RECEIVE_2_PATH = "bpsk_receive_2.txt"
NOMA_PY_PATH = "NOMA.py"
PYTHON_EXE = r"C:\Users\Armagan\radioconda\python.exe"

if not os.path.exists(PYTHON_EXE):
    PYTHON_EXE = "python"

def prepare_test_files():
    tx1_data = ("1234567890" * 7 + "1234567") * 20
    tx2_data = ("abcdefghij" * 7 + "abcdefg") * 20

    with open(TRANSMIT_1_PATH, "wb") as f:
        f.write(tx1_data.encode('utf-8'))
    with open(TRANSMIT_2_PATH, "wb") as f:
        f.write(tx2_data.encode('utf-8'))

    for p in [RECEIVE_1_PATH, RECEIVE_2_PATH]:
        if os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass

def calculate_ber(tx_path, rx_path):
    if not os.path.exists(tx_path) or not os.path.exists(rx_path):
        return 1.0
    
    with open(tx_path, "rb") as f:
        tx_data = f.read()
    with open(rx_path, "rb") as f:
        rx_data = f.read()

    if len(tx_data) == 0 or len(rx_data) == 0:
        return 1.0

    tx_bits = np.unpackbits(np.frombuffer(tx_data, dtype=np.uint8))
    rx_bits = np.unpackbits(np.frombuffer(rx_data, dtype=np.uint8))

    min_len = min(len(tx_bits), len(rx_bits))
    mismatches = np.sum(tx_bits[:min_len] != rx_bits[:min_len])
    mismatches += abs(len(tx_bits) - len(rx_bits))
    
    return float(mismatches) / len(tx_bits)

def modify_noma_throttle(rate=500000):
    """NOMA.py icerisindeki throttle hizini gunceller."""
    if not os.path.exists(NOMA_PY_PATH):
        return
    with open(NOMA_PY_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    content = re.sub(
        r"blocks\.throttle\(\s*gr\.sizeof_gr_complex\*1,\s*\d+,",
        f"blocks.throttle( gr.sizeof_gr_complex*1, {rate},",
        content
    )
    content = re.sub(
        r"\*\s*\d+\)\s*if\s*\"items\"\s*==\s*\"time\"",
        f"* {rate}) if \"items\" == \"time\"",
        content
    )
    with open(NOMA_PY_PATH, "w", encoding="utf-8") as f:
        f.write(content)

def modify_noma_noise(noise_val):
    with open(NOMA_PY_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    content = re.sub(
        r"self\.noise = noise = \d+\.\d+",
        f"self.noise = noise = {noise_val:.6f}",
        content
    )

    with open(NOMA_PY_PATH, "w", encoding="utf-8") as f:
        f.write(content)

def run_simulation(duration=15):
    proc = subprocess.Popen([PYTHON_EXE, NOMA_PY_PATH], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(duration)
    proc.terminate()
    try:
        proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        proc.kill()

def calculate_noise_from_distance(d, n=3.5):
    snr2_db = 100.8 - 10.0 * n * math.log10(d)
    snr_linear = 10.0 ** (snr2_db / 10.0)
    sigma = math.sqrt(0.2 / (2.0 * snr_linear))
    return sigma, snr2_db

def main():
    print("======================================================================")
    print("        BPSK NOMA UZAK KULLANICI (USER 2) MESAFE SWEEP TESTI         ")
    print("======================================================================")
    print("  Ortam: Yari Kentsel / Ofis (n = 3.5 Yol Kaybi Modeli)")
    print("  Esik SNR Siniri: 6.0 dB")
    print("======================================================================")

    distances = [10, 50, 100, 200, 300, 400, 500, 600, 700, 800, 1000, 1500, 2000]
    n_exponent = 3.5
    results = []

    backup_path = NOMA_PY_PATH + ".bak"
    shutil.copyfile(NOMA_PY_PATH, backup_path)

    # 500.000 sembol/sn hizina ayarla (hizli iletim icin)
    modify_noma_throttle(rate=500000)

    try:
        for d in distances:
            sigma, snr2 = calculate_noise_from_distance(d, n=n_exponent)
            sigma_clipped = max(0.001, min(1.0, sigma))

            print(f">> Mesafe: {d:4d} m | SNR: {snr2:5.1f} dB | Gurultu: {sigma_clipped:.5f}")
            
            prepare_test_files()
            modify_noma_noise(sigma_clipped)
            
            # 500k hizda 15 saniye veri akisinin tamamlanmasi icin fazlasiyla yeterlidir
            run_simulation(duration=15)
            
            ber1 = calculate_ber(TRANSMIT_1_PATH, RECEIVE_1_PATH)
            ber2 = calculate_ber(TRANSMIT_2_PATH, RECEIVE_2_PATH)
            
            results.append((d, snr2, sigma_clipped, ber1, ber2))
            
            status2 = "OK (HATASIZ)" if ber2 == 0.0 else f"HATALI (BER: {ber2:.2%})"
            print(f"   [Sonuc] User 1 BER: {ber1:.2%} | User 2: {status2}")

    finally:
        # NOMA.py dosyasini eski haline geri yukle
        if os.path.exists(backup_path):
            shutil.copyfile(backup_path, NOMA_PY_PATH)
            os.remove(backup_path)

    csv_path = "academic_distance_sweep.csv"
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("Distance_m,SNR2_dB,Noise_Voltage,User1_BER,User2_BER\n")
        for d, snr2, sigma, ber1, ber2 in results:
            f.write(f"{d},{snr2:.2f},{sigma:.6f},{ber1:.6f},{ber2:.6f}\n")
    print(f"\n-> Sonuclar '{csv_path}' dosyasina kaydedildi.")

    try:
        import matplotlib.pyplot as plt
        
        d_vals = [r[0] for r in results]
        ber2_vals = [r[4] * 100 for r in results]
        
        plt.figure(figsize=(8, 5))
        plt.plot(d_vals, ber2_vals, 'r-o', linewidth=2, label='User 2 (Far User) BER')
        plt.axvline(x=512, color='blue', linestyle='--', label='Teorik Limit (512m)')
        plt.title('BPSK NOMA Mesafe vs. Bit Hata Orani (BER) Grafigi\n(Yari Kentsel Ortam, n=3.5)')
        plt.xlabel('Mesafe (metre)')
        plt.ylabel('Bit Hata Orani - BER (%)')
        plt.grid(True, which="both", ls="--")
        plt.legend()
        
        plot_path = "distance_vs_ber.png"
        plt.savefig(plot_path, dpi=300)
        print(f"-> Grafik '{plot_path}' olarak kaydedildi.")
    except Exception as e:
        print(f"[NOT] Matplotlib grafigi cizilemedi: {e}")

if __name__ == "__main__":
    main()
