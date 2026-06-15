# -*- coding: utf-8 -*-
"""
TEST 5: LDPC Karmasiklik ve Zamanlama Odunlesimi Testi
------------------------------------------------------
LDPC kod cozucunun iterasyon sayisinin (max_iter) islem yukune
ve hata oranina etkisini analiz eder.

Metodoloji: test_metodolojisi.md TEST 5
- max_iter: 2, 4, 8, 15, 20
- Sabit Eb/N0'da BLER ve CPU suresi olcumu
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

def modify_ldpc_max_iter(max_iter):
    """
    NOMA.py'deki LDPC decoder bloklarinin max_iter degerini degistirir.
    Ornek satir:
    self.ldpc_dec = fec.ldpc_decoder.make('...alist', 10)
    -> max_iter parametresi 2. arguman
    """
    with open(NOMA_PY_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # ldpc_dec ve ldpc_dec_2 bloklarini guncelle
    content = re.sub(
        r"fec\.ldpc_decoder\.make\('([^']+)',\s*\d+\)",
        f"fec.ldpc_decoder.make('\\1', {max_iter})",
        content
    )

    with open(NOMA_PY_PATH, "w", encoding="utf-8") as f:
        f.write(content)

def run_simulation_timed(target_size=77000, timeout=120, idle_timeout=5):
    """Simulasyonu calistir ve CPU suresini olc."""
    cpu_start = time.perf_counter()
    wall_start = time.time()

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

    wall_elapsed = time.time() - wall_start
    cpu_elapsed = time.perf_counter() - cpu_start

    return wall_elapsed, cpu_elapsed

def main():
    print("=" * 70)
    print("  TEST 5: LDPC KARMASIKLIK VE ZAMANLAMA ODUNLESIMI")
    print("=" * 70)

    # Test parametreleri
    max_iter_values = [2, 4, 8, 15, 20]

    # Iki farkli SNR noktasinda test et
    test_sigmas = [
        (0.10, "Dusuk Gurultu (sigma=0.10)"),
        (0.25, "Yuksek Gurultu (sigma=0.25)")
    ]

    all_results = {}

    backup_path = NOMA_PY_PATH + ".bak"
    shutil.copyfile(NOMA_PY_PATH, backup_path)

    try:
        for sigma, sigma_label in test_sigmas:
            ebno_db = -20.0 * math.log10(sigma) - 3.0
            print(f"\n--- {sigma_label} | Eb/N0 = {ebno_db:.1f} dB ---")
            scenario_results = []

            for max_iter in max_iter_values:
                print(f">> LDPC max_iter = {max_iter} test ediliyor...")

                # Her adimda orijinalden baslayip degistir
                shutil.copyfile(backup_path, NOMA_PY_PATH)
                modify_noma_throttle(rate=500000)
                modify_noma_noise(sigma)
                modify_ldpc_max_iter(max_iter)

                prepare_test_files()
                wall_time, cpu_time = run_simulation_timed(target_size=77000)

                ber1, bler1 = calculate_ber_and_bler(TRANSMIT_1_PATH, RECEIVE_1_PATH)
                ber2, bler2 = calculate_ber_and_bler(TRANSMIT_2_PATH, RECEIVE_2_PATH)

                # Paket basina ortalama islem suresi (ms)
                rx1_sz = os.path.getsize(RECEIVE_1_PATH) if os.path.exists(RECEIVE_1_PATH) else 0
                rx2_sz = os.path.getsize(RECEIVE_2_PATH) if os.path.exists(RECEIVE_2_PATH) else 0
                total_packets = (rx1_sz + rx2_sz) // 77
                time_per_packet_ms = (wall_time * 1000.0 / total_packets) if total_packets > 0 else 0

                scenario_results.append((max_iter, ber1, bler1, ber2, bler2, wall_time, time_per_packet_ms))
                print(f"   User 1 BER: {ber1:.2%} (BLER: {bler1:.1%}) | User 2 BER: {ber2:.2%} (BLER: {bler2:.1%})")
                print(f"   Wall Time: {wall_time:.1f}s | Paket/ms: {time_per_packet_ms:.2f} ms/paket")

            all_results[sigma_label] = (sigma, ebno_db, scenario_results)

    finally:
        if os.path.exists(backup_path):
            shutil.copyfile(backup_path, NOMA_PY_PATH)
            os.remove(backup_path)

    # CSV kaydet
    csv_path = "complexity_latency_results.csv"
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("Scenario,Sigma,EbNo_dB,Max_Iter,User1_BER,User1_BLER,User2_BER,User2_BLER,Wall_Time_s,Time_Per_Packet_ms\n")
        for scenario_name, (sigma, ebno_db, results) in all_results.items():
            for max_iter, ber1, bler1, ber2, bler2, wall_time, tpp in results:
                f.write(f"{scenario_name},{sigma:.4f},{ebno_db:.2f},{max_iter},{ber1:.6f},{bler1:.6f},{ber2:.6f},{bler2:.6f},{wall_time:.2f},{tpp:.4f}\n")
    print(f"\n-> Sonuclar '{csv_path}' dosyasina kaydedildi.")

    # Grafik
    try:
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(1, 2, figsize=(14, 6))

        for idx, (scenario_name, (sigma, ebno_db, results)) in enumerate(all_results.items()):
            ax = axes[idx]
            iters = [r[0] for r in results]
            bler2_vals = [r[4]*100 for r in results]
            tpp_vals = [r[6] for r in results]

            ax_bler = ax
            ax_time = ax.twinx()

            p1, = ax_bler.plot(iters, bler2_vals, 'r-o', linewidth=2.5, markersize=8, label='User 2 BLER (%)')
            p2, = ax_time.plot(iters, tpp_vals, 'b--D', linewidth=2, markersize=7, label='Islem Suresi (ms/pkt)')

            ax_bler.set_xlabel('LDPC Max Iterasyon Sayisi', fontsize=13)
            ax_bler.set_ylabel('User 2 BLER (%)', color='red', fontsize=13)
            ax_bler.tick_params(axis='y', labelcolor='red', labelsize=11)
            ax_time.set_ylabel('Islem Suresi (ms/paket)', color='blue', fontsize=13)
            ax_time.tick_params(axis='y', labelcolor='blue', labelsize=11)
            ax_bler.set_title(f'{scenario_name}\n(Eb/N0 = {ebno_db:.1f} dB)', fontsize=12, fontweight='bold')
            ax_bler.grid(True, alpha=0.3)
            ax_bler.set_xticks(iters)

            lines = [p1, p2]
            labels = [l.get_label() for l in lines]
            ax_bler.legend(lines, labels, fontsize=9, loc='center right')

        plt.suptitle('LDPC Iterasyon Sayisi vs Performans-Zamanlama Odunlesimi', fontsize=15, fontweight='bold')
        plt.tight_layout()
        plt.savefig("complexity_latency_tradeoff.png", dpi=300, bbox_inches='tight')
        plt.close()

        print("-> Grafik 'complexity_latency_tradeoff.png' kaydedildi.")

    except Exception as e:
        print(f"[NOT] Grafikleme basarisiz: {e}")

if __name__ == "__main__":
    main()
