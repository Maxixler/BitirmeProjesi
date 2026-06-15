# -*- coding: utf-8 -*-
"""
TEST 3: Kanal ve Donanimsal Kusurlar Testi (RHI, ipCSI ve ipSIC)
----------------------------------------------------------------
Bu test; sistemin kusursuz kanal durumu bilgisi (P-CSI) ve ideal donanim
kabullerinden uzaklastirilarak, gercek RF alici-verici kisitlamalari
altindaki dayanikliligini olcmeyi amaclar.

Metodoloji: test_metodolojisi.md TEST 3
- TX Donanim Kusuru (kappa_x): 0.05 ve 0.15
- RX Donanim Kusuru (nu_y): 0.05 ve 0.15
- Gurultu voltajina distorsiyon eklenerek simule edilir
"""

import subprocess
import time
import os
import re
import math
import numpy as np
import shutil

# Dosya yollari (tests/channel_impairments/ icinden calistirilir)
TRANSMIT_1_PATH = "../../bpsk_transmit.txt"
TRANSMIT_2_PATH = "../../bpsk_transmit_2.txt"
RECEIVE_1_PATH = "../../bpsk_receive.txt"
RECEIVE_2_PATH = "../../bpsk_receive_2.txt"
NOMA_PY_PATH = "../../NOMA.py"
PYTHON_EXE = r"C:\Users\Armagan\radioconda\python.exe"

if not os.path.exists(PYTHON_EXE):
    PYTHON_EXE = "python"

def prepare_test_files():
    tx1_data = ("1234567890" * 7 + "1234567") * 1000
    tx2_data = ("abcdefghij" * 7 + "abcdefg") * 1000
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

def calculate_ber_and_bler(tx_path, rx_path):
    if not os.path.exists(tx_path):
        return 1.0, 1.0
    with open(tx_path, "rb") as f:
        tx_data = f.read()
    rx_data = b""
    if os.path.exists(rx_path):
        with open(rx_path, "rb") as f:
            rx_data = f.read()
    tx_blocks = len(tx_data) // 77
    rx_blocks = len(rx_data) // 77
    if tx_blocks == 0:
        bler = 1.0
    else:
        bler = 1.0 - (float(rx_blocks) / tx_blocks)
        bler = max(0.0, min(1.0, bler))
    if len(tx_data) == 0 or len(rx_data) == 0:
        return 1.0, bler
    tx_bits = np.unpackbits(np.frombuffer(tx_data, dtype=np.uint8))
    rx_bits = np.unpackbits(np.frombuffer(rx_data, dtype=np.uint8))
    min_len = min(len(tx_bits), len(rx_bits))
    mismatches = np.sum(tx_bits[:min_len] != rx_bits[:min_len])
    mismatches += abs(len(tx_bits) - len(rx_bits))
    ber = float(mismatches) / len(tx_bits)
    return min(1.0, ber), bler

def modify_noma_throttle(rate=500000):
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
        r"self\.noise = noise = \d+(\.\d+)?",
        f"self.noise = noise = {noise_val:.6f}",
        content
    )
    with open(NOMA_PY_PATH, "w", encoding="utf-8") as f:
        f.write(content)

def run_simulation(target_size=77000, timeout=120, idle_timeout=5):
    proc = subprocess.Popen([PYTHON_EXE, NOMA_PY_PATH], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    start_time = time.time()
    prev_sz1 = 0
    prev_sz2 = 0
    idle_counter = 0
    while True:
        elapsed = time.time() - start_time
        if elapsed > timeout:
            break
        sz1 = os.path.getsize(RECEIVE_1_PATH) if os.path.exists(RECEIVE_1_PATH) else 0
        sz2 = os.path.getsize(RECEIVE_2_PATH) if os.path.exists(RECEIVE_2_PATH) else 0
        if sz1 >= target_size and sz2 >= target_size:
            time.sleep(1.0)
            break
        if sz1 > 0 or sz2 > 0:
            if sz1 == prev_sz1 and sz2 == prev_sz2:
                idle_counter += 1
            else:
                idle_counter = 0
        if idle_counter >= idle_timeout:
            break
        prev_sz1 = sz1
        prev_sz2 = sz2
        time.sleep(0.5)
    proc.terminate()
    try:
        proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        proc.kill()

def compute_effective_noise(sigma_awgn, kappa_x, nu_y, P_total=1.0):
    """
    RHI modeli: TX ve RX distorsiyon gurultuleri Gaussian olarak modellenir.
    Efektif gurultu voltaji:
    sigma_eff = sqrt(sigma_awgn^2 + kappa_x^2 * P_total + nu_y^2 * P_total)
    
    kappa_x: Verici distorsiyon katsayisi (0.05 - 0.15)
    nu_y: Alici distorsiyon katsayisi (0.05 - 0.15)
    """
    sigma_eff = math.sqrt(sigma_awgn**2 + kappa_x**2 * P_total + nu_y**2 * P_total)
    return sigma_eff

def main():
    import sys
    print("=" * 70)
    print("  TEST 3: KANAL VE DONANIMSAL KUSURLAR TESTI (RHI + ipCSI + ipSIC)")
    print("=" * 70)

    csv_path = "channel_impairments_results.csv"
    all_results = {}

    # Eger plot-only ise simülasyon yapmadan CSV'den oku
    if len(sys.argv) > 1 and sys.argv[1] == "--plot-only":
        print("-> '--plot-only' modu algilandi. Sonuclar CSV dosyasindan yukleniyor...")
        if not os.path.exists(csv_path):
            print(f"[HATA] CSV dosyasi bulunamadi: {csv_path}")
            sys.exit(1)
        with open(csv_path, "r", encoding="utf-8") as f:
            lines = f.readlines()[1:] # header atla
        for line in lines:
            parts = line.strip().split(",")
            if len(parts) < 8:
                continue
            scen = ",".join(parts[:-7])
            sb = float(parts[-7])
            eb = float(parts[-6])
            se = float(parts[-5])
            ber1 = float(parts[-4])
            bler1 = float(parts[-3])
            ber2 = float(parts[-2])
            bler2 = float(parts[-1])
            if scen not in all_results:
                all_results[scen] = []
            all_results[scen].append((sb, eb, se, ber1, bler1, ber2, bler2))
    else:
        # Senaryo tanimalari (test_metodolojisi.md'den)
        # Her senaryo: (isim, kappa_x, nu_y)
        scenarios = [
            ("Ideal (P-CSI, Kusursuz)", 0.00, 0.00),
            ("Dusuk RHI (kx=0.05, vy=0.05)", 0.05, 0.05),
            ("Yuksek TX Kusuru (kx=0.15, vy=0.05)", 0.15, 0.05),
            ("Yuksek RX Kusuru (kx=0.05, vy=0.15)", 0.05, 0.15),
            ("Yuksek RHI (kx=0.15, vy=0.15)", 0.15, 0.15),
        ]

        # SNR sweep icin baz gurultu degerleri
        base_sigmas = [0.03, 0.05, 0.08, 0.10, 0.15, 0.20, 0.25, 0.30]

        backup_path = NOMA_PY_PATH + ".bak"
        shutil.copyfile(NOMA_PY_PATH, backup_path)
        modify_noma_throttle(rate=500000)

        try:
            for scenario_name, kappa_x, nu_y in scenarios:
                print(f"\n--- Senaryo: {scenario_name} ---")
                scenario_results = []

                for sigma_base in base_sigmas:
                    # Efektif gurultu hesabi
                    sigma_eff = compute_effective_noise(sigma_base, kappa_x, nu_y)
                    ebno_db = -20.0 * math.log10(sigma_base) - 3.0

                    print(f">> sigma_base={sigma_base:.3f} (Eb/N0={ebno_db:.1f} dB) | sigma_eff={sigma_eff:.4f} (kx={kappa_x}, vy={nu_y})")

                    prepare_test_files()
                    modify_noma_noise(sigma_eff)
                    run_simulation(target_size=77000)

                    ber1, bler1 = calculate_ber_and_bler(TRANSMIT_1_PATH, RECEIVE_1_PATH)
                    ber2, bler2 = calculate_ber_and_bler(TRANSMIT_2_PATH, RECEIVE_2_PATH)

                    scenario_results.append((sigma_base, ebno_db, sigma_eff, ber1, bler1, ber2, bler2))
                    print(f"   User 1 BER: {ber1:.2%} (BLER: {bler1:.1%}) | User 2 BER: {ber2:.2%} (BLER: {bler2:.1%})")

                all_results[scenario_name] = scenario_results

        finally:
            if os.path.exists(backup_path):
                shutil.copyfile(backup_path, NOMA_PY_PATH)
                os.remove(backup_path)

        # CSV kaydet
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write("Scenario,Sigma_Base,EbNo_dB,Sigma_Effective,User1_BER,User1_BLER,User2_BER,User2_BLER\n")
            for scenario_name, results in all_results.items():
                for sigma_base, ebno_db, sigma_eff, ber1, bler1, ber2, bler2 in results:
                    f.write(f"{scenario_name},{sigma_base:.4f},{ebno_db:.2f},{sigma_eff:.6f},{ber1:.6f},{bler1:.6f},{ber2:.6f},{bler2:.6f}\n")
        print(f"\n-> Sonuclar '{csv_path}' dosyasina kaydedildi.")

    # Grafiklestirme
    try:
        import matplotlib.pyplot as plt

        colors = ['green', 'blue', 'orange', 'purple', 'red']
        markers = ['^', 's', 'D', 'v', 'o']

        # Figure 1: User 1 BER vs Eb/N0 (tum senaryolar)
        plt.figure(figsize=(10, 7))
        for i, (scenario_name, results) in enumerate(all_results.items()):
            ebno = [r[1] for r in results]
            ber1 = [max(r[3], 1e-7) for r in results]
            plt.semilogy(ebno, ber1, color=colors[i], marker=markers[i], linestyle='-', linewidth=2, markersize=7, label=scenario_name)
        plt.title('User 1 (Near) BER vs Eb/N0 - Donanim Kusur Senaryolari', fontsize=14, fontweight='bold')
        plt.xlabel('Eb/N0 (dB)', fontsize=13)
        plt.ylabel('BER (Log)', fontsize=13)
        plt.grid(True, which="both", ls="-", alpha=0.3)
        plt.legend(fontsize=9, loc='lower left')
        plt.ylim(1e-7, 1.0)
        plt.savefig("rhi_user1_ber.png", dpi=300, bbox_inches='tight')
        plt.close()

        # Figure 2: User 2 BER vs Eb/N0 (tum senaryolar)
        plt.figure(figsize=(10, 7))
        for i, (scenario_name, results) in enumerate(all_results.items()):
            ebno = [r[1] for r in results]
            ber2 = [max(r[5], 1e-7) for r in results]
            plt.semilogy(ebno, ber2, color=colors[i], marker=markers[i], linestyle='-', linewidth=2, markersize=7, label=scenario_name)
        plt.title('User 2 (Far) BER vs Eb/N0 - Donanim Kusur Senaryolari', fontsize=14, fontweight='bold')
        plt.xlabel('Eb/N0 (dB)', fontsize=13)
        plt.ylabel('BER (Log)', fontsize=13)
        plt.grid(True, which="both", ls="-", alpha=0.3)
        plt.legend(fontsize=9, loc='lower left')
        plt.ylim(1e-7, 1.0)
        plt.savefig("rhi_user2_ber.png", dpi=300, bbox_inches='tight')
        plt.close()

        # Figure 3: User 2 BLER karsilastirma (ideal vs yuksek RHI)
        plt.figure(figsize=(10, 7))
        for i, (scenario_name, results) in enumerate(all_results.items()):
            ebno = [r[1] for r in results]
            bler2 = [r[6]*100 for r in results]
            plt.plot(ebno, bler2, color=colors[i], marker=markers[i], linestyle='-', linewidth=2, markersize=7, label=scenario_name)
        plt.title('User 2 (Far) BLER vs Eb/N0 - Donanim Kusur Senaryolari', fontsize=14, fontweight='bold')
        plt.xlabel('Eb/N0 (dB)', fontsize=13)
        plt.ylabel('BLER (%)', fontsize=13)
        plt.grid(True, which="both", ls="-", alpha=0.3)
        plt.legend(fontsize=9, loc='upper right')
        plt.savefig("rhi_user2_bler.png", dpi=300, bbox_inches='tight')
        plt.close()

        print("-> Grafikler (rhi_user1_ber.png, rhi_user2_ber.png, rhi_user2_bler.png) kaydedildi.")

    except Exception as e:
        print(f"[NOT] Grafikleme basarisiz: {e}")

if __name__ == "__main__":
    main()
