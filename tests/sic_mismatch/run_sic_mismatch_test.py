# -*- coding: utf-8 -*-
"""
BPSK NOMA Test 2: SIC Genlik ve Faz Sapmasi Hassasiyet Analizi
--------------------------------------------------------------
"""

import subprocess
import time
import os
import re
import math
import numpy as np
import shutil

# Paths (relative to tests/sic_mismatch/)
TRANSMIT_1_PATH = "../../bpsk_transmit.txt"
TRANSMIT_2_PATH = "../../bpsk_transmit_2.txt"
RECEIVE_1_PATH = "../../bpsk_receive.txt"
RECEIVE_2_PATH = "../../bpsk_receive_2.txt"
NOMA_PY_PATH = "../../NOMA.py"
SIC_PY_PATH = "../../NOMA_epy_block_1.py"
PYTHON_EXE = r"C:\Users\Armagan\radioconda\python.exe"

if not os.path.exists(PYTHON_EXE):
    PYTHON_EXE = "python"

def prepare_test_files():
    # 1000 packets of 77 bytes
    tx1_data = ("1234567890" * 7 + "1234567") * 1000
    tx2_data = ("abcdefghij" * 7 + "abcdefg") * 1000

    with open(TRANSMIT_1_PATH, "wb") as f:
        f.write(tx1_data.encode('utf-8'))
    with open(TRANSMIT_2_PATH, "wb") as f:
        f.write(tx2_data.encode('utf-8'))

    # Delete previous outputs
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

def calculate_jains_fairness(bler1, bler2):
    # Rate is defined as success rate (1 - BLER)
    r1 = 1.0 - bler1
    r2 = 1.0 - bler2
    if (r1**2 + r2**2) == 0:
        return 0.5
    return ((r1 + r2) ** 2) / (2.0 * (r1**2 + r2**2))

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

def modify_sic_block(amp_error=0.0, phase_error_rad=0.0):
    with open(SIC_PY_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    content = re.sub(
        r"amplitude_scale\s*=\s*self\.near_user_amplitude\s*(\*\s*\(1\.0\s*\+\s*[-+]?\d+\.\d+\))?",
        f"amplitude_scale = self.near_user_amplitude * (1.0 + {amp_error:.6f})",
        content
    )
    # Target interference subtraction line:
    content = re.sub(
        r"interference_signal\s*=\s*tx1_chunk_diff\s*\*\s*amplitude_scale\s*\*\s*np\.exp\(1j\s*\*\s*\(phase_offset\s*\+\s*\([-+]?\d+\.\d+\)\)\)",
        f"interference_signal = tx1_chunk_diff * amplitude_scale * np.exp(1j * (phase_offset + {phase_error_rad:.6f}))",
        content
    )
    content = re.sub(
        r"interference_signal\s*=\s*tx1_chunk_diff\s*\*\s*amplitude_scale\s*\*\s*np\.exp\(1j\s*\*\s*phase_offset\)",
        f"interference_signal = tx1_chunk_diff * amplitude_scale * np.exp(1j * (phase_offset + {phase_error_rad:.6f}))",
        content
    )
    with open(SIC_PY_PATH, "w", encoding="utf-8") as f:
        f.write(content)

def run_simulation(target_size=77000, timeout=60, idle_timeout=5):
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

def main():
    print("======================================================================")
    print("        BPSK NOMA TEST 2: SIC GENLIK VE FAZ SAPMASI ANALIZI          ")
    print("======================================================================")

    # Backups
    noma_bak = NOMA_PY_PATH + ".bak"
    sic_bak = SIC_PY_PATH + ".bak"
    shutil.copyfile(NOMA_PY_PATH, noma_bak)
    shutil.copyfile(SIC_PY_PATH, sic_bak)

    # Set throttle to 500k and noise to 0.05 (clean baseline)
    modify_noma_throttle(rate=500000)
    modify_noma_noise(0.05)

    phase_results = []
    amp_results = []

    try:
        # 1. FAZ SAPMASI SWEEP (Genlik hatasi 0)
        phase_angles = [0, 2, 5, 8, 10, 12, 15, 18, 20, 25, 30] # dereceler
        print("\n--- 1. Faz Sapmasi (Phase Mismatch) Sweep (Amp Error = 0) ---")
        for deg in phase_angles:
            rad = deg * math.pi / 180.0
            print(f">> Faz Sapmasi: {deg:2d} derece ({rad:.4f} rad) test ediliyor...")
            
            prepare_test_files()
            modify_sic_block(amp_error=0.0, phase_error_rad=rad)
            
            # Hedeflenen boyuta ulasana kadar dinamik bekle
            run_simulation(target_size=77000)
            
            ber1, bler1 = calculate_ber_and_bler(TRANSMIT_1_PATH, RECEIVE_1_PATH)
            ber2, bler2 = calculate_ber_and_bler(TRANSMIT_2_PATH, RECEIVE_2_PATH)
            jain = calculate_jains_fairness(bler1, bler2)
            
            phase_results.append((deg, rad, ber1, bler1, ber2, bler2, jain))
            print(f"   [Sonuc] User 1 BER: {ber1:.2%} | User 2 BER: {ber2:.2%} | Jain Fairness: {jain:.2%}")

        # 2. GENLIK SAPMASI SWEEP (Faz hatasi 0)
        amp_errors = [-0.20, -0.15, -0.10, -0.05, -0.02, 0.0, 0.02, 0.05, 0.10, 0.15, 0.20]
        print("\n--- 2. Genlik Sapmasi (Amplitude Mismatch) Sweep (Phase Error = 0) ---")
        for err in amp_errors:
            print(f">> Genlik Sapmasi: %{err*100:+.1f} test ediliyor...")
            
            prepare_test_files()
            modify_sic_block(amp_error=err, phase_error_rad=0.0)
            
            # Hedeflenen boyuta ulasana kadar dinamik bekle
            run_simulation(target_size=77000)
            
            ber1, bler1 = calculate_ber_and_bler(TRANSMIT_1_PATH, RECEIVE_1_PATH)
            ber2, bler2 = calculate_ber_and_bler(TRANSMIT_2_PATH, RECEIVE_2_PATH)
            jain = calculate_jains_fairness(bler1, bler2)
            
            amp_results.append((err, ber1, bler1, ber2, bler2, jain))
            print(f"   [Sonuc] User 1 BER: {ber1:.2%} | User 2 BER: {ber2:.2%} | Jain Fairness: {jain:.2%}")

    finally:
        # Restore backups
        if os.path.exists(noma_bak):
            shutil.copyfile(noma_bak, NOMA_PY_PATH)
            os.remove(noma_bak)
        if os.path.exists(sic_bak):
            shutil.copyfile(sic_bak, SIC_PY_PATH)
            os.remove(sic_bak)

    # CSV olarak kaydet
    csv_path = "sic_mismatch_results.csv"
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("TYPE,Parameter_Val,User1_BER,User1_BLER,User2_BER,User2_BLER,Jains_Fairness\n")
        for deg, rad, ber1, bler1, ber2, bler2, jain in phase_results:
            f.write(f"PHASE,{deg},{ber1:.6f},{bler1:.6f},{ber2:.6f},{bler2:.6f},{jain:.6f}\n")
        for err, ber1, bler1, ber2, bler2, jain in amp_results:
            f.write(f"AMP,{err},{ber1:.6f},{bler1:.6f},{ber2:.6f},{bler2:.6f},{jain:.6f}\n")
    print(f"\n-> Sonuclar '{csv_path}' dosyasina kaydedildi.")

    # Grafiklestirme
    try:
        import matplotlib.pyplot as plt
        
        # Plot 1: Phase Mismatch vs User 2 BER
        deg_vals = [r[0] for r in phase_results]
        ber2_phase = [r[4]*100 for r in phase_results]
        jain_phase = [r[6]*100 for r in phase_results]

        fig, ax1 = plt.subplots(figsize=(8, 5))
        ax1.plot(deg_vals, ber2_phase, 'r-o', linewidth=2, label='User 2 BER')
        ax1.set_xlabel('Faz Sapmasi (Derece)')
        ax1.set_ylabel('User 2 BER (%)', color='r')
        ax1.tick_params(axis='y', labelcolor='r')
        ax1.grid(True, which="both", ls="--")

        ax2 = ax1.twinx()
        ax2.plot(deg_vals, jain_phase, 'b--^', linewidth=2, label='Jain Fairness Index')
        ax2.set_ylabel('Jain Fairness Index (%)', color='b')
        ax2.tick_params(axis='y', labelcolor='b')
        
        plt.title('Costas Loop Faz Sapmasinin SIC Basarisina Etkisi\n(User 2 BER & Hakkaniyet Endeksi)')
        plt.savefig("phase_mismatch_vs_ber.png", dpi=300)
        plt.close()

        # Plot 2: Amplitude Mismatch vs User 2 BER
        amp_vals = [r[0]*100 for r in amp_results]
        ber2_amp = [r[3]*100 for r in amp_results]
        jain_amp = [r[5]*100 for r in amp_results]

        fig, ax1 = plt.subplots(figsize=(8, 5))
        ax1.plot(amp_vals, ber2_amp, 'r-o', linewidth=2, label='User 2 BER')
        ax1.set_xlabel('Genlik Kestirim Hatasi (%)')
        ax1.set_ylabel('User 2 BER (%)', color='r')
        ax1.tick_params(axis='y', labelcolor='r')
        ax1.grid(True, which="both", ls="--")

        ax2 = ax1.twinx()
        ax2.plot(amp_vals, jain_amp, 'b--^', linewidth=2, label='Jain Fairness Index')
        ax2.set_ylabel('Jain Fairness Index (%)', color='b')
        ax2.tick_params(axis='y', labelcolor='b')

        plt.title('Genlik Kestirim Hatasinin (SIC Genlik Sapmasi) SIC Basarisina Etkisi\n(User 2 BER & Hakkaniyet Endeksi)')
        plt.savefig("amplitude_mismatch_vs_ber.png", dpi=300)
        plt.close()

        print("-> Tum grafikler (phase_mismatch_vs_ber.png, amplitude_mismatch_vs_ber.png) basariyla kaydedildi.")

    except Exception as e:
        print(f"[NOT] Grafikleme adimi basarisiz: {e}")

if __name__ == "__main__":
    main()
