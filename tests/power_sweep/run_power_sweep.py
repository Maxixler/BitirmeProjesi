# -*- coding: utf-8 -*-
"""
BPSK NOMA Power Allocation Sweep Test
--------------------------------------
Bu script, BPSK NOMA sisteminde Güç Bölüşüm Oranını (Power Allocation Ratio)
farklı değerler için sweep ederek, Near User (User 1) ve Far User (User 2)
doğruluk oranlarını ölçer. Bu test, NOMA sınırlarını ve SIC başarısını analiz eder.
"""

import subprocess
import time
import os
import re
import math

# Dosya yollari
TRANSMIT_1_PATH = "../../bpsk_transmit.txt"
TRANSMIT_2_PATH = "../../bpsk_transmit_2.txt"
RECEIVE_1_PATH = "../../bpsk_receive.txt"
RECEIVE_2_PATH = "../../bpsk_receive_2.txt"
NOMA_PY_PATH = "../../NOMA.py"
PYTHON_EXE = r"C:\Users\Armagan\radioconda\python.exe"

def prepare_files():
    """Standart test verilerini hazirlar."""
    tx1_data = ("1234567890" * 7 + "1234567") * 1000
    tx2_data = ("abcdefghij" * 7 + "abcdefg") * 1000
    
    with open(TRANSMIT_1_PATH, "w") as f:
        f.write(tx1_data)
    with open(TRANSMIT_2_PATH, "w") as f:
        f.write(tx2_data)

    # Eski ciktilari sil
    for p in [RECEIVE_1_PATH, RECEIVE_2_PATH]:
        if os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass

def modify_noma_amplitudes(a1, a2):
    """NOMA.py icerisindeki güç katsayilarini regex ile dinamik olarak gunceller."""
    with open(NOMA_PY_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # User 2 genligi (blocks_multiply_const_vxx_0)
    content = re.sub(
        r"self\.blocks_multiply_const_vxx_0 = blocks\.multiply_const_cc\(\d+\.\d+\)",
        f"self.blocks_multiply_const_vxx_0 = blocks.multiply_const_cc({a2:.4f})",
        content
    )
    # User 1 genligi (blocks_multiply_const_vxx_0_0)
    content = re.sub(
        r"self\.blocks_multiply_const_vxx_0_0 = blocks\.multiply_const_cc\(\d+\.\d+\)",
        f"self.blocks_multiply_const_vxx_0_0 = blocks.multiply_const_cc({a1:.4f})",
        content
    )
    # Reconstructed User 1 genligi (blocks_multiply_const_vxx_0_0_0)
    content = re.sub(
        r"self\.blocks_multiply_const_vxx_0_0_0 = blocks\.multiply_const_cc\(\d+\.\d+\)",
        f"self.blocks_multiply_const_vxx_0_0_0 = blocks.multiply_const_cc({a1:.4f})",
        content
    )

    # SIC Aligner block near_user_amplitude parametresi
    # Korelasyonda gercek genlik yaklasik a1 * 0.966 civarindadir (kanal ve rrc kaybi nedeniyle)
    sic_amp = a1 * 0.966
    content = re.sub(
        r"near_user_amplitude=\d+\.\d+",
        f"near_user_amplitude={sic_amp:.4f}",
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

def calculate_accuracy():
    with open(TRANSMIT_1_PATH, "r") as f:
        tx1 = f.read()
    with open(TRANSMIT_2_PATH, "r") as f:
        tx2 = f.read()

    rx1 = ""
    if os.path.exists(RECEIVE_1_PATH):
        with open(RECEIVE_1_PATH, "r") as f:
            rx1 = f.read()

    rx2 = ""
    if os.path.exists(RECEIVE_2_PATH):
        with open(RECEIVE_2_PATH, "r") as f:
            rx2 = f.read()

    len_tx1, len_rx1 = len(tx1), len(rx1)
    len_tx2, len_rx2 = len(tx2), len(rx2)

    match_1 = sum(1 for i in range(min(len_tx1, len_rx1)) if tx1[i] == rx1[i])
    acc_1 = (match_1 / len_tx1) * 100 if len_tx1 > 0 else 0.0

    match_2 = sum(1 for i in range(min(len_tx2, len_rx2)) if tx2[i] == rx2[i])
    acc_2 = (match_2 / len_tx2) * 100 if len_tx2 > 0 else 0.0

    return acc_1, acc_2

def main():
    print("======================================================================")
    print("             BPSK NOMA GUC BOLUSUM ORANI (POWER SWEEP) TESTI          ")
    print("======================================================================")
    print(" Toplam Guc = 1.0 (a1^2 + a2^2 = 1.0) olacak sekilde oranlar taranir.")
    print("======================================================================")

    # Oranlar: (User 1 Power %, User 2 Power %)
    power_scenarios = [
        (0.95, 0.05),
        (0.90, 0.10),
        (0.85, 0.15),
        (0.80, 0.20),  # Varsayilan (80% / 20%)
        (0.70, 0.30),
        (0.60, 0.40),
        (0.50, 0.50),  # Limit (Girisim cok yuksek)
    ]

    results = []

    for p1, p2 in power_scenarios:
        # a = sqrt(P)
        a1 = math.sqrt(p1)
        a2 = math.sqrt(p2)
        
        print(f"\n>> Guc Orani: User 1: %{p1*100:.0f} (a={a1:.3f}) | User 2: %{p2*100:.0f} (a={a2:.3f}) test ediliyor...")
        
        prepare_files()
        modify_noma_amplitudes(a1, a2)
        
        # Hedeflenen boyuta ulasana kadar dinamik bekle
        run_simulation(target_size=77000)
        
        acc_1, acc_2 = calculate_accuracy()
        results.append((p1, p2, acc_1, acc_2))
        
        print(f"   [Sonuc] User 1 Dogruluk: {acc_1:.2f}% | User 2 Dogruluk: {acc_2:.2f}%")

    # Degerleri varsayilana geri dondur (a1=0.894, a2=0.447, near_amp=0.864)
    modify_noma_amplitudes(0.894, 0.447)

    # Sonuclari listele
    print("\n========================= SWEEP SWEEP TABLOSU =========================")
    print("| User 1 Gucu (%) | User 2 Gucu (%) | User 1 Dogruluk (%) | User 2 Dogruluk (%) |")
    print("| :---: | :---: | :---: | :---: |")
    for p1, p2, acc1, acc2 in results:
        print(f"|  %{p1*100:02.0f}  |  %{p2*100:02.0f}  |  {acc1:6.2f}%  |  {acc2:6.2f}%  |")
    print("=======================================================================")

if __name__ == "__main__":
    main()
