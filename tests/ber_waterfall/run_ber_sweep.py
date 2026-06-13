# -*- coding: utf-8 -*-
"""
BPSK NOMA Test 1: LLS BER & BLER Waterfall, Outage, Sum Capacity
----------------------------------------------------------------
"""

import subprocess
import time
import os
import re
import math
import numpy as np
import shutil

# Paths (relative to tests/ber_waterfall/)
TRANSMIT_1_PATH = "../../bpsk_transmit.txt"
TRANSMIT_2_PATH = "../../bpsk_transmit_2.txt"
RECEIVE_1_PATH = "../../bpsk_receive.txt"
RECEIVE_2_PATH = "../../bpsk_receive_2.txt"
NOMA_PY_PATH = "../../NOMA.py"
PYTHON_EXE = r"C:\Users\Armagan\radioconda\python.exe"

if not os.path.exists(PYTHON_EXE):
    PYTHON_EXE = "python"

def prepare_test_files():
    # Write exactly 1000 packets of 77 bytes
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

    # Transmitted and received blocks (77 bytes)
    tx_blocks = len(tx_data) // 77
    rx_blocks = len(rx_data) // 77

    # BLER (Block/Packet Error Rate)
    # A block is in error if it's completely missing (dropped by CRC)
    if tx_blocks == 0:
        bler = 1.0
    else:
        bler = 1.0 - (float(rx_blocks) / tx_blocks)
        bler = max(0.0, min(1.0, bler))

    # BER
    if len(tx_data) == 0 or len(rx_data) == 0:
        return 1.0, bler

    tx_bits = np.unpackbits(np.frombuffer(tx_data, dtype=np.uint8))
    rx_bits = np.unpackbits(np.frombuffer(rx_data, dtype=np.uint8))

    min_len = min(len(tx_bits), len(rx_bits))
    mismatches = np.sum(tx_bits[:min_len] != rx_bits[:min_len])
    # Count missing bits as errors
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
            time.sleep(1.0) # buffer flush safety wait
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

def bpsk_theoretical_ber(ebno_db):
    ebno_linear = 10.0 ** (ebno_db / 10.0)
    # Q(x) = 0.5 * erfc(x / sqrt(2))
    # Q(sqrt(2 * Eb/No)) = 0.5 * erfc(sqrt(Eb/No))
    return 0.5 * math.erfc(math.sqrt(ebno_linear))

def simulate_rayleigh_metrics(sigma, a1=0.894, a2=0.447, gamma_th_db=6.0, num_samples=10000):
    # a1^2 = 0.8, a2^2 = 0.2
    gamma_th = 10.0 ** (gamma_th_db / 10.0) # Eşik SINR
    
    # Rayleigh sönümleme kanalı (exponential channel gain power)
    h2 = np.random.exponential(scale=1.0, size=num_samples)
    
    # User 2 SINR (Far User)
    # SINR2 = a2^2 * h2 / (a1^2 * h2 + sigma^2)
    sinr2 = (a2**2 * h2) / (a1**2 * h2 + sigma**2)
    
    # User 1 SINR (Near User, SIC öncesi ve sonrası)
    # SINR1_to_1 (User 1'in kendisini çözerken User 2'den gördüğü girişimli SINR)
    sinr1_to_1 = (a1**2 * h2) / (a2**2 * h2 + sigma**2)
    # SINR1_to_2 (User 1'in User 2'yi çözerken gördüğü SNR)
    sinr1_to_2 = (a2**2 * h2) / sigma**2
    
    # Outage Probability
    outage2 = np.mean(sinr2 < gamma_th)
    outage1 = np.mean((sinr1_to_1 < gamma_th) | (sinr1_to_2 < gamma_th))
    
    # Ergodic Capacity (bps/Hz)
    cap2 = np.mean(np.log2(1 + sinr2))
    cap1 = np.mean(np.log2(1 + (a1**2 * h2) / sigma**2)) # SIC sonrası
    sum_cap = cap1 + cap2
    
    # OMA karşılaştırması (Zaman Bölmeli - TDMA, her kullanıcı %50 zaman diliminde tam güçle iletir)
    # OMA_Cap1 = 0.5 * E[log2(1 + |h|^2 / sigma^2)]
    oma_cap1 = 0.5 * np.mean(np.log2(1 + h2 / sigma**2))
    oma_cap2 = 0.5 * np.mean(np.log2(1 + h2 / sigma**2))
    oma_sum_cap = oma_cap1 + oma_cap2

    return outage1, outage2, cap1, cap2, sum_cap, oma_sum_cap

def main():
    print("======================================================================")
    print("        BPSK NOMA TEST 1: LLS BER & BLER WATERFALL SWEEP              ")
    print("======================================================================")

    # Gurultu voltajlari (Eb/N0 sweep araligi)
    # Eb/N0 (dB) = -20 log10(sigma) - 3 dB
    sigmas = [0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.15, 0.18, 0.21, 0.24, 0.27, 0.30]
    results = []

    backup_path = NOMA_PY_PATH + ".bak"
    shutil.copyfile(NOMA_PY_PATH, backup_path)

    # 500.000 sembol/sn throttle hizina set et
    modify_noma_throttle(rate=500000)

    try:
        for sigma in sigmas:
            # Eb/No hesabi
            ebno_db = -20.0 * math.log10(sigma) - 3.0
            
            print(f">> Gurultu (sigma): {sigma:.2f} | Eb/N0: {ebno_db:5.1f} dB test ediliyor...")
            
            prepare_test_files()
            modify_noma_noise(sigma)
            
            # Hedeflenen boyuta ulasana kadar dinamik bekle
            run_simulation(target_size=77000)
            
            ber1, bler1 = calculate_ber_and_bler(TRANSMIT_1_PATH, RECEIVE_1_PATH)
            ber2, bler2 = calculate_ber_and_bler(TRANSMIT_2_PATH, RECEIVE_2_PATH)
            
            # Rayleigh Fading metriklerini hesapla
            out1, out2, cap1, cap2, sum_cap, oma_sum = simulate_rayleigh_metrics(sigma)
            
            theory_ber = bpsk_theoretical_ber(ebno_db)
            
            results.append((sigma, ebno_db, ber1, bler1, ber2, bler2, theory_ber, out1, out2, cap1, cap2, sum_cap, oma_sum))
            
            print(f"   [Empirical] User 1 BER: {ber1:.2%} (BLER: {bler1:.1%}) | User 2 BER: {ber2:.2%} (BLER: {bler2:.1%})")
            print(f"   [Rayleigh] Outage U1: {out1:.1%} U2: {out2:.1%} | Sum Cap: {sum_cap:.2f} OMA: {oma_sum:.2f} bps/Hz")

    finally:
        # NOMA.py dosyasini eski haline geri yukle
        if os.path.exists(backup_path):
            shutil.copyfile(backup_path, NOMA_PY_PATH)
            os.remove(backup_path)

    # CSV olarak kaydet
    csv_path = "ber_waterfall.csv"
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("Sigma,EbNo_dB,User1_BER,User1_BLER,User2_BER,User2_BLER,Theory_BPSK_BER,Outage_U1,Outage_U2,Cap_U1,Cap_U2,Sum_Cap,OMA_Sum_Cap\n")
        for r in results:
            f.write(",".join([f"{val:.6f}" if isinstance(val, float) else str(val) for val in r]) + "\n")
    print(f"\n-> Sonuclar '{csv_path}' dosyasina kaydedildi.")

    # Grafiklestirme
    try:
        import matplotlib.pyplot as plt
        
        ebno_vals = [r[1] for r in results]
        ber1_vals = [r[2] for r in results]
        bler1_vals = [r[3] for r in results]
        ber2_vals = [r[4] for r in results]
        bler2_vals = [r[5] for r in results]
        theory_ber = [r[6] for r in results]
        
        out1_vals = [r[7] for r in results]
        out2_vals = [r[8] for r in results]
        
        cap1_vals = [r[9] for r in results]
        cap2_vals = [r[10] for r in results]
        sum_cap_vals = [r[11] for r in results]
        oma_sum_vals = [r[12] for r in results]

        # Figure 1: BER Waterfall
        plt.figure(figsize=(8, 5))
        plt.semilogy(ebno_vals, ber1_vals, 'g-^', linewidth=2, label='User 1 (Near User) BER')
        plt.semilogy(ebno_vals, ber2_vals, 'r-o', linewidth=2, label='User 2 (Far User) BER')
        plt.semilogy(ebno_vals, theory_ber, 'k--', linewidth=1.5, label='BPSK Theoretical Limit')
        plt.title('BPSK NOMA BER vs. Eb/N0 Waterfall Egrileri')
        plt.xlabel('Eb/N0 (dB)')
        plt.ylabel('Bit Hata Orani - BER (Log Scale)')
        plt.grid(True, which="both", ls="--")
        plt.legend()
        plt.ylim(1e-4, 1.0)
        plt.savefig("ber_waterfall.png", dpi=300)
        plt.close()

        # Figure 2: BLER (Block Error Rate)
        plt.figure(figsize=(8, 5))
        plt.plot(ebno_vals, [b*100 for b in bler1_vals], 'g-^', linewidth=2, label='User 1 BLER')
        plt.plot(ebno_vals, [b*100 for b in bler2_vals], 'r-o', linewidth=2, label='User 2 BLER')
        plt.title('BPSK NOMA Blok Hata Orani (BLER/PER) vs. Eb/N0')
        plt.xlabel('Eb/N0 (dB)')
        plt.ylabel('Blok Hata Orani - BLER (%)')
        plt.grid(True, which="both", ls="--")
        plt.legend()
        plt.savefig("bler_waterfall.png", dpi=300)
        plt.close()

        # Figure 3: Outage Probability
        plt.figure(figsize=(8, 5))
        plt.plot(ebno_vals, [o*100 for o in out1_vals], 'g-^', linewidth=2, label='User 1 Outage')
        plt.plot(ebno_vals, [o*100 for o in out2_vals], 'r-o', linewidth=2, label='User 2 Outage')
        plt.title('Rayleigh Sonumleme Altinda Kesinti Olasiligi (Outage Probability)\n(QoS Threshold = 6 dB)')
        plt.xlabel('Ortalama Eb/N0 (dB)')
        plt.ylabel('Kesinti Olasiligi (%)')
        plt.grid(True, which="both", ls="--")
        plt.legend()
        plt.savefig("outage_probability.png", dpi=300)
        plt.close()

        # Figure 4: Ergodic Sum Capacity
        plt.figure(figsize=(8, 5))
        plt.plot(ebno_vals, sum_cap_vals, 'b-d', linewidth=2, label='NOMA Sum Capacity')
        plt.plot(ebno_vals, oma_sum_vals, 'k--', linewidth=1.5, label='OMA Sum Capacity')
        plt.plot(ebno_vals, cap1_vals, 'g--', label='User 1 Capacity')
        plt.plot(ebno_vals, cap2_vals, 'r--', label='User 2 Capacity')
        plt.title('Rayleigh Sonumleme Altinda Spektral Verimlilik\n(NOMA vs. OMA)')
        plt.xlabel('Ortalama Eb/N0 (dB)')
        plt.ylabel('Spektral Verimlilik (bps/Hz)')
        plt.grid(True, which="both", ls="--")
        plt.legend()
        plt.savefig("ergodic_capacity.png", dpi=300)
        plt.close()

        print("-> Tum grafikler (ber_waterfall.png, bler_waterfall.png, outage_probability.png, ergodic_capacity.png) basariyla kaydedildi.")

    except Exception as e:
        print(f"[NOT] Grafikleme adimi basarisiz: {e}")

if __name__ == "__main__":
    main()
