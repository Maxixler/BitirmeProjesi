# -*- coding: utf-8 -*-
"""
BPSK NOMA Test 5: Kanal Kusurlari (Imperfect CSI & RHI: IQ Imbalance, Phase Noise)
---------------------------------------------------------------------------------
"""

import subprocess
import time
import os
import re
import math
import numpy as np
import shutil

# Paths (relative to tests/channel_impairments/)
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

def modify_sic_impairments(g, phi, phase_noise):
    with open(SIC_PY_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    content = re.sub(r"g_val\s*=\s*[-+]?\d+(\.\d+)?", f"g_val = {g:.6f}", content)
    content = re.sub(r"phi_val\s*=\s*[-+]?\d+(\.\d+)?", f"phi_val = {phi:.6f}", content)
    content = re.sub(r"phase_noise_std_val\s*=\s*[-+]?\d+(\.\d+)?", f"phase_noise_std_val = {phase_noise:.6f}", content)

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
    print("        BPSK NOMA TEST 5: KANAL VE RF HARDWARE KUSURLARI TESTI        ")
    print("======================================================================")

    # Backups
    noma_bak = NOMA_PY_PATH + ".bak"
    sic_bak = SIC_PY_PATH + ".bak"
    shutil.copyfile(NOMA_PY_PATH, noma_bak)
    shutil.copyfile(SIC_PY_PATH, sic_bak)

    # Set throttle to 500k and noise to 0.05
    modify_noma_throttle(rate=500000)
    modify_noma_noise(0.05)

    pn_results = []
    iq_results = []

    try:
        # 1. PHASE NOISE SWEEP (IQ Imbalance = 0)
        pn_stds = [0.0, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.15] # radyan
        print("\n--- 1. Evre Gurultusu (Phase Noise) Sweep ---")
        for pn in pn_stds:
            print(f">> Phase Noise Std: {pn:.2f} rad test ediliyor...")
            
            prepare_test_files()
            modify_sic_impairments(g=0.0, phi=0.0, phase_noise=pn)
            
            # Hedeflenen boyuta ulasana kadar dinamik bekle
            run_simulation(target_size=77000)
            
            ber1, bler1 = calculate_ber_and_bler(TRANSMIT_1_PATH, RECEIVE_1_PATH)
            ber2, bler2 = calculate_ber_and_bler(TRANSMIT_2_PATH, RECEIVE_2_PATH)
            
            pn_results.append((pn, ber1, bler1, ber2, bler2))
            print(f"   [Sonuc] User 1 BER: {ber1:.2%} | User 2 BER: {ber2:.2%}")

        # 2. IQ PHASE IMBALANCE SWEEP (Phase Noise = 0, Amp imbalance g = 0.05)
        iq_phases = [0, 2, 4, 6, 8, 10, 12, 15] # dereceler
        print("\n--- 2. IQ Faz Dengesisligi (IQ Phase Imbalance) Sweep ---")
        for deg in iq_phases:
            rad = deg * math.pi / 180.0
            print(f">> IQ Faz Dengesi: {deg:2d} derece ({rad:.4f} rad) test ediliyor...")
            
            prepare_test_files()
            modify_sic_impairments(g=0.05, phi=rad, phase_noise=0.0)
            
            # Hedeflenen boyuta ulasana kadar dinamik bekle
            run_simulation(target_size=77000)
            
            ber1, bler1 = calculate_ber_and_bler(TRANSMIT_1_PATH, RECEIVE_1_PATH)
            ber2, bler2 = calculate_ber_and_bler(TRANSMIT_2_PATH, RECEIVE_2_PATH)
            
            iq_results.append((deg, rad, ber1, bler1, ber2, bler2))
            print(f"   [Sonuc] User 1 BER: {ber1:.2%} | User 2 BER: {ber2:.2%}")

    finally:
        # Restore backups
        if os.path.exists(noma_bak):
            shutil.copyfile(noma_bak, NOMA_PY_PATH)
            os.remove(noma_bak)
        if os.path.exists(sic_bak):
            shutil.copyfile(sic_bak, SIC_PY_PATH)
            os.remove(sic_bak)

    # Save results to CSV
    csv_path = "impairments_results.csv"
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("TYPE,Parameter_Val,User1_BER,User1_BLER,User2_BER,User2_BLER\n")
        for pn, ber1, bler1, ber2, bler2 in pn_results:
            f.write(f"PN,{pn},{ber1:.6f},{bler1:.6f},{ber2:.6f},{bler2:.6f}\n")
        for deg, rad, ber1, bler1, ber2, bler2 in iq_results:
            f.write(f"IQ,{deg},{ber1:.6f},{bler1:.6f},{ber2:.6f},{bler2:.6f}\n")
    print(f"\n-> Sonuclar '{csv_path}' dosyasina kaydedildi.")

    # Plot
    try:
        import matplotlib.pyplot as plt
        
        # Plot 1: Phase Noise
        pn_vals = [r[0] for r in pn_results]
        ber2_pn = [r[3]*100 for r in pn_results]
        
        plt.figure(figsize=(8, 5))
        plt.plot(pn_vals, ber2_pn, 'r-o', linewidth=2, label='User 2 (Far User) BER')
        plt.title('RF Oscillator Phase Noise Effect on NOMA Performance')
        plt.xlabel('Phase Noise Standard Deviation (Rad)')
        plt.ylabel('User 2 BER (%)')
        plt.grid(True, which="both", ls="--")
        plt.legend()
        plt.savefig("phase_noise_vs_ber.png", dpi=300)
        plt.close()

        # Plot 2: IQ Imbalance
        iq_vals = [r[0] for r in iq_results]
        ber2_iq = [r[4]*100 for r in iq_results]
        
        plt.figure(figsize=(8, 5))
        plt.plot(iq_vals, ber2_iq, 'r-o', linewidth=2, label='User 2 (Far User) BER')
        plt.title('I/Q Phase Imbalance Effect on NOMA Performance\n(Amplitude Imbalance g = 0.05)')
        plt.xlabel('I/Q Phase Imbalance (Degrees)')
        plt.ylabel('User 2 BER (%)')
        plt.grid(True, which="both", ls="--")
        plt.legend()
        plt.savefig("iq_imbalance_vs_ber.png", dpi=300)
        plt.close()

        print("-> Tum grafikler (phase_noise_vs_ber.png, iq_imbalance_vs_ber.png) basariyla kaydedildi.")

    except Exception as e:
        print(f"[NOT] Grafikleme adimi basarisiz: {e}")

if __name__ == "__main__":
    main()
