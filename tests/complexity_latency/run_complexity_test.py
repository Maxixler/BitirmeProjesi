# -*- coding: utf-8 -*-
"""
BPSK NOMA Test 3: LDPC Karmasiklik ve Zamanlama Odunlesimi
----------------------------------------------------------
"""

import subprocess
import time
import os
import re
import math
import numpy as np
import shutil
import ctypes
from ctypes import wintypes

# Paths (relative to tests/complexity_latency/)
TRANSMIT_1_PATH = "../../bpsk_transmit.txt"
TRANSMIT_2_PATH = "../../bpsk_transmit_2.txt"
RECEIVE_1_PATH = "../../bpsk_receive.txt"
RECEIVE_2_PATH = "../../bpsk_receive_2.txt"
NOMA_PY_PATH = "../../NOMA.py"
PYTHON_EXE = r"C:\Users\Armagan\radioconda\python.exe"

if not os.path.exists(PYTHON_EXE):
    PYTHON_EXE = "python"

# Windows API definitions for native CPU time measurement
kernel32 = ctypes.windll.kernel32

def get_process_cpu_time(pid):
    PROCESS_QUERY_INFORMATION = 0x0400
    h_process = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION, False, pid)
    if not h_process:
        return 0.0
    
    creation_time = wintypes.FILETIME()
    exit_time = wintypes.FILETIME()
    kernel_time = wintypes.FILETIME()
    user_time = wintypes.FILETIME()
    
    success = kernel32.GetProcessTimes(
        h_process,
        ctypes.byref(creation_time),
        ctypes.byref(exit_time),
        ctypes.byref(kernel_time),
        ctypes.byref(user_time)
    )
    
    kernel32.CloseHandle(h_process)
    
    if not success:
        return 0.0
        
    # Convert FILETIME (100-nanosecond intervals) to seconds
    kt = (kernel_time.dwHighDateTime << 32) + kernel_time.dwLowDateTime
    ut = (user_time.dwHighDateTime << 32) + user_time.dwLowDateTime
    return (kt + ut) * 1e-7

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

def modify_noma_iterations(iter_count):
    with open(NOMA_PY_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Replaces fec.ldpc_decoder.make('...', \d+) with make('...', iter_count)
    content = re.sub(
        r"fec\.ldpc_decoder\.make\(\s*'([^']+)'\s*,\s*\d+\s*\)",
        f"fec.ldpc_decoder.make('\\1', {iter_count})",
        content
    )
    with open(NOMA_PY_PATH, "w", encoding="utf-8") as f:
        f.write(content)

def main():
    print("======================================================================")
    print("        BPSK NOMA TEST 3: LDPC KARMASIKLIK VE ZAMANLAMA ODUNLESIMI    ")
    print("======================================================================")

    # Backups
    noma_bak = NOMA_PY_PATH + ".bak"
    shutil.copyfile(NOMA_PY_PATH, noma_bak)

    # Set throttle to 500k and noise to 0.15 (Eb/N0 = 13.5 dB, critical LDPC threshold)
    modify_noma_throttle(rate=500000)
    modify_noma_noise(0.15)

    iterations = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
    results = []

    try:
        for iter_count in iterations:
            print(f">> LDPC Max Iteration: {iter_count:2d} test ediliyor...")
            
            prepare_test_files()
            modify_noma_iterations(iter_count)
            
            # Start simulation process
            proc = subprocess.Popen([PYTHON_EXE, NOMA_PY_PATH], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Polling loops to wait for target size
            start_time = time.time()
            prev_sz1 = 0
            prev_sz2 = 0
            idle_counter = 0
            target_size = 77000
            timeout = 60
            idle_timeout = 5
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
            
            # Get CPU Time using native Windows API before terminating
            cpu_time = get_process_cpu_time(proc.pid)
            
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
            
            ber1, bler1 = calculate_ber_and_bler(TRANSMIT_1_PATH, RECEIVE_1_PATH)
            ber2, bler2 = calculate_ber_and_bler(TRANSMIT_2_PATH, RECEIVE_2_PATH)
            
            results.append((iter_count, cpu_time, ber1, bler1, ber2, bler2))
            print(f"   [Sonuc] CPU Time: {cpu_time:5.3f} sn | User 1 BER: {ber1:.2%} | User 2 BER: {ber2:.2%}")

    finally:
        # Restore backups
        if os.path.exists(noma_bak):
            shutil.copyfile(noma_bak, NOMA_PY_PATH)
            os.remove(noma_bak)

    # Save results to CSV
    csv_path = "complexity_results.csv"
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("Max_Iterations,CPU_Time_sec,User1_BER,User1_BLER,User2_BER,User2_BLER\n")
        for r in results:
            f.write(f"{r[0]},{r[1]:.6f},{r[2]:.6f},{r[3]:.6f},{r[4]:.6f},{r[5]:.6f}\n")
    print(f"\n-> Sonuclar '{csv_path}' dosyasina kaydedildi.")

    # Plot
    try:
        import matplotlib.pyplot as plt
        
        iter_vals = [r[0] for r in results]
        cpu_vals = [r[1] for r in results]
        ber2_vals = [r[4]*100 for r in results]

        fig, ax1 = plt.subplots(figsize=(8, 5))
        
        # Plot CPU Time (Complexity)
        ax1.plot(iter_vals, cpu_vals, 'b-d', linewidth=2, label='CPU Calisma Suresi (sn)')
        ax1.set_xlabel('Maksimum LDPC Iterasyon Sayisi')
        ax1.set_ylabel('CPU Calisma Suresi (saniye)', color='b')
        ax1.tick_params(axis='y', labelcolor='b')
        ax1.grid(True, which="both", ls="--")

        # Plot User 2 BER (Accuracy)
        ax2 = ax1.twinx()
        ax2.plot(iter_vals, ber2_vals, 'r--o', linewidth=2, label='User 2 BER')
        ax2.set_ylabel('User 2 Hata Orani - BER (%)', color='r')
        ax2.tick_params(axis='y', labelcolor='r')
        
        plt.title('LDPC Iterasyon Sayisinin Performans ve Zamanlama Odunlesimi\n(Complexity vs. Accuracy)')
        
        plot_path = "latency_vs_ber.png"
        plt.savefig(plot_path, dpi=300)
        plt.close()
        print(f"-> Grafik '{plot_path}' basariyla kaydedildi.")

    except Exception as e:
        print(f"[NOT] Grafikleme adimi basarisiz: {e}")

if __name__ == "__main__":
    main()
