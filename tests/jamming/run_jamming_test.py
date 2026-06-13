# -*- coding: utf-8 -*-
"""
BPSK NOMA Test 4: Jamming (Karistirma) Guvenlik ve Dayanim Testi
----------------------------------------------------------------
"""

import subprocess
import time
import os
import re
import math
import numpy as np
import shutil

# Paths (relative to tests/jamming/)
TRANSMIT_1_PATH = "../../bpsk_transmit.txt"
TRANSMIT_2_PATH = "../../bpsk_transmit_2.txt"
RECEIVE_1_PATH = "../../bpsk_receive.txt"
RECEIVE_2_PATH = "../../bpsk_receive_2.txt"
NOMA_PY_PATH = "../../NOMA.py"
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

def inject_jammer_in_noma():
    with open(NOMA_PY_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Inject import
    if "from gnuradio import analog" not in content:
        content = content.replace(
            "from gnuradio import digital",
            "from gnuradio import digital\nfrom gnuradio import analog"
        )
    
    # 2. Inject jammer instantiation in __init__
    if "self.analog_sig_source_x_jammer" not in content:
        content = content.replace(
            "self.blocks_add_xx_0 = blocks.add_vcc(1)",
            "self.blocks_add_xx_0 = blocks.add_vcc(1)\n        self.analog_sig_source_x_jammer = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, 10000, 0.0, 0)"
        )
    
    # 3. Inject jammer connection
    if "self.connect((self.analog_sig_source_x_jammer, 0), (self.blocks_add_xx_0, 2))" not in content:
        content = content.replace(
            "self.connect((self.blocks_tag_gate_0_0, 0), (self.blocks_add_xx_0, 0))",
            "self.connect((self.blocks_tag_gate_0_0, 0), (self.blocks_add_xx_0, 0))\n        self.connect((self.analog_sig_source_x_jammer, 0), (self.blocks_add_xx_0, 2))"
        )

    with open(NOMA_PY_PATH, "w", encoding="utf-8") as f:
        f.write(content)

def modify_jammer_amplitude(amplitude):
    with open(NOMA_PY_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    content = re.sub(
        r"self\.analog_sig_source_x_jammer\s*=\s*analog\.sig_source_c\(\s*samp_rate\s*,\s*analog\.GR_COS_WAVE\s*,\s*\d+\s*,\s*[-+]?\d+\.\d+\s*,\s*0\s*\)",
        f"self.analog_sig_source_x_jammer = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, 10000, {amplitude:.6f}, 0)",
        content
    )
    with open(NOMA_PY_PATH, "w", encoding="utf-8") as f:
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
    print("        BPSK NOMA TEST 4: JAMMING (KARISTIRMA) DAYANIM TESTI         ")
    print("======================================================================")

    # Backup
    noma_bak = NOMA_PY_PATH + ".bak"
    shutil.copyfile(NOMA_PY_PATH, noma_bak)

    # Set throttle to 500k, noise to 0.05 (clean channel), and inject jammer structure
    modify_noma_throttle(rate=500000)
    modify_noma_noise(0.05)
    inject_jammer_in_noma()

    amplitudes = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]
    results = []

    try:
        for amp in amplitudes:
            print(f">> Jammer Genligi (Amp): {amp:.2f} (Guc: {amp**2:.4f}) test ediliyor...")
            
            prepare_test_files()
            modify_jammer_amplitude(amp)
            
            # Hedeflenen boyuta ulasana kadar dinamik bekle
            run_simulation(target_size=77000)
            
            ber1, bler1 = calculate_ber_and_bler(TRANSMIT_1_PATH, RECEIVE_1_PATH)
            ber2, bler2 = calculate_ber_and_bler(TRANSMIT_2_PATH, RECEIVE_2_PATH)
            
            results.append((amp, amp**2, ber1, bler1, ber2, bler2))
            print(f"   [Sonuc] User 1 BER: {ber1:.2%} | User 2 BER: {ber2:.2%}")

    finally:
        # Restore backups
        if os.path.exists(noma_bak):
            shutil.copyfile(noma_bak, NOMA_PY_PATH)
            os.remove(noma_bak)

    # CSV olarak kaydet
    csv_path = "jamming_results.csv"
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("Jammer_Amplitude,Jammer_Power,User1_BER,User1_BLER,User2_BER,User2_BLER\n")
        for r in results:
            f.write(f"{r[0]},{r[1]:.6f},{r[2]:.6f},{r[3]:.6f},{r[4]:.6f},{r[5]:.6f}\n")
    print(f"\n-> Sonuclar '{csv_path}' dosyasina kaydedildi.")

    # Grafiklestirme
    try:
        import matplotlib.pyplot as plt
        
        amp_vals = [r[0] for r in results]
        ber1_vals = [r[2]*100 for r in results]
        ber2_vals = [r[4]*100 for r in results]

        plt.figure(figsize=(8, 5))
        plt.plot(amp_vals, ber1_vals, 'g-^', linewidth=2, label='User 1 BER')
        plt.plot(amp_vals, ber2_vals, 'r-o', linewidth=2, label='User 2 BER')
        plt.title('BPSK NOMA Jammer Genligine Gore Hata Oranlari (BER)')
        plt.xlabel('Jammer Sinyal Genligi (Single-Tone Jamming at 10 kHz)')
        plt.ylabel('Bit Hata Orani - BER (%)')
        plt.grid(True, which="both", ls="--")
        plt.legend()
        
        plot_path = "jamming_vs_ber.png"
        plt.savefig(plot_path, dpi=300)
        plt.close()
        print(f"-> Grafik '{plot_path}' basariyla kaydedildi.")

    except Exception as e:
        print(f"[NOT] Grafikleme adimi basarisiz: {e}")

if __name__ == "__main__":
    main()
