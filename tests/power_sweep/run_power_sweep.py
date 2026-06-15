# -*- coding: utf-8 -*-
"""
TEST 4: Guc Paylasim Taramasi Testi (Power Allocation Sweep)
------------------------------------------------------------
Uzak kullanicinin guc katsayisini (a_far) tarayarak her iki kullanicinin
BER dengesini optimize eder ve Jain's Fairness Index olcer.

Metodoloji: test_metodolojisi.md TEST 4
- a_far: 0.55 -> 0.95 (adim: 0.05)
- a_near = sqrt(1 - a_far^2)
- Toplam guc sabit: a_near^2 + a_far^2 = 1.0
"""

import subprocess
import time
import os
import re
import math
import numpy as np
import shutil

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

def modify_power_allocation(a_near, a_far):
    """
    NOMA.py'deki guc katsayilarini degistirir.
    User 1 (near) = multiply_const_cc(0.894) -> a_near
    User 2 (far) = multiply_const_cc(0.447) -> a_far
    SIC blogu near_user_amplitude da guncellenir.
    """
    with open(NOMA_PY_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # User 1 (near user) guc carpanlari: 2 adet multiply_const_cc(0.894)
    # blocks_multiply_const_vxx_0_0 ve blocks_multiply_const_vxx_0_0_0
    content = re.sub(
        r"blocks\.multiply_const_cc\(0\.\d+\)\s*\n(\s*)self\.blocks_multiply_const_vxx_0_0_0",
        f"blocks.multiply_const_cc({a_near:.6f})\n\\1self.blocks_multiply_const_vxx_0_0_0",
        content
    )

    # SIC aligner near_user_amplitude
    content = re.sub(
        r"near_user_amplitude=[\d.]+",
        f"near_user_amplitude={a_near:.6f}",
        content
    )

    # User 1 genlik (2 adet 0.894 -> a_near)
    content = re.sub(
        r"multiply_const_cc\(0\.894\)",
        f"multiply_const_cc({a_near:.6f})",
        content
    )

    # User 2 genlik (0.447 -> a_far)
    content = re.sub(
        r"multiply_const_cc\(0\.447\)",
        f"multiply_const_cc({a_far:.6f})",
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

def jains_fairness(bler1, bler2):
    """Jain's Fairness Index: J = (R1 + R2)^2 / (2 * (R1^2 + R2^2))"""
    r1 = 1.0 - bler1
    r2 = 1.0 - bler2
    denom = r1**2 + r2**2
    if denom == 0:
        return 0.5
    return ((r1 + r2)**2) / (2.0 * denom)

def main():
    print("=" * 70)
    print("  TEST 4: GUC PAYLASIM TARAMASI (POWER ALLOCATION SWEEP)")
    print("=" * 70)

    # a_far^2 = uzak kullanici guc orani (0.55 -> 0.95)
    # a_near = sqrt(1 - a_far^2), toplam guc = 1.0
    a_far_values = [0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]

    # Sabit gurultu seviyesi (orta SNR)
    test_noise = 0.10  # sigma

    results = []

    backup_path = NOMA_PY_PATH + ".bak"
    shutil.copyfile(NOMA_PY_PATH, backup_path)
    modify_noma_throttle(rate=500000)
    modify_noma_noise(test_noise)

    try:
        for a_far in a_far_values:
            a_near = math.sqrt(1.0 - a_far**2)
            power_near_pct = a_near**2 * 100
            power_far_pct = a_far**2 * 100

            print(f"\n>> a_far={a_far:.2f} (P_far={power_far_pct:.1f}%) | a_near={a_near:.4f} (P_near={power_near_pct:.1f}%)")

            # NOMA.py'deki guc katsayilarini guncelle
            # Her adimda orijinal dosyadan baslayalim
            shutil.copyfile(backup_path, NOMA_PY_PATH)
            modify_noma_throttle(rate=500000)
            modify_noma_noise(test_noise)
            modify_power_allocation(a_near, a_far)

            prepare_test_files()
            run_simulation(target_size=77000)

            ber1, bler1 = calculate_ber_and_bler(TRANSMIT_1_PATH, RECEIVE_1_PATH)
            ber2, bler2 = calculate_ber_and_bler(TRANSMIT_2_PATH, RECEIVE_2_PATH)
            jfi = jains_fairness(bler1, bler2)

            results.append((a_far, a_near, power_far_pct, power_near_pct, ber1, bler1, ber2, bler2, jfi))
            print(f"   User 1 BER: {ber1:.2%} | User 2 BER: {ber2:.2%} | Jain's FI: {jfi:.4f}")

    finally:
        if os.path.exists(backup_path):
            shutil.copyfile(backup_path, NOMA_PY_PATH)
            os.remove(backup_path)

    # CSV kaydet
    csv_path = "power_sweep_results.csv"
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("a_far,a_near,Power_Far_Pct,Power_Near_Pct,User1_BER,User1_BLER,User2_BER,User2_BLER,Jains_Fairness\n")
        for r in results:
            f.write(",".join([f"{v:.6f}" if isinstance(v, float) else str(v) for v in r]) + "\n")
    print(f"\n-> Sonuclar '{csv_path}' dosyasina kaydedildi.")

    # Grafik
    try:
        import matplotlib.pyplot as plt

        a_far_vals = [r[0] for r in results]
        ber1_vals = [r[4]*100 for r in results]
        ber2_vals = [r[6]*100 for r in results]
        jfi_vals = [r[8]*100 for r in results]

        # Cift eksenli grafik: BER (sol) + Jain's FI (sag)
        fig, ax1 = plt.subplots(figsize=(10, 7))

        ax1.plot(a_far_vals, ber1_vals, 'g-^', linewidth=2.5, markersize=8, label='User 1 (Near) BER')
        ax1.plot(a_far_vals, ber2_vals, 'r-o', linewidth=2.5, markersize=8, label='User 2 (Far) BER')
        ax1.set_xlabel('Uzak Kullanici Guc Katsayisi (a_far)', fontsize=14)
        ax1.set_ylabel('BER (%)', color='black', fontsize=14)
        ax1.tick_params(axis='y', labelcolor='black', labelsize=12)
        ax1.grid(True, which="both", ls="-", alpha=0.3)
        ax1.legend(loc='upper left', fontsize=11)

        ax2 = ax1.twinx()
        ax2.plot(a_far_vals, jfi_vals, 'b--D', linewidth=2, markersize=7, label="Jain's Fairness Index")
        ax2.set_ylabel("Jain's Fairness Index (%)", color='blue', fontsize=14)
        ax2.tick_params(axis='y', labelcolor='blue', labelsize=12)
        ax2.legend(loc='upper right', fontsize=11)

        plt.title('PD-NOMA Guc Paylasim Optimizasyonu\n(BER ve Hakkaniyet Endeksi)', fontsize=15, fontweight='bold')
        plt.savefig("power_sweep_ber_fairness.png", dpi=300, bbox_inches='tight')
        plt.close()

        print("-> Grafik 'power_sweep_ber_fairness.png' kaydedildi.")

    except Exception as e:
        print(f"[NOT] Grafikleme basarisiz: {e}")

if __name__ == "__main__":
    main()
