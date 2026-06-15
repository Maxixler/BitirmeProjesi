# -*- coding: utf-8 -*-
"""
BPSK NOMA Test 1: LLS BER & BLER Waterfall, Outage, Sum Capacity
----------------------------------------------------------------
Bu script, kanal gürültü voltajı (sigma) sweep'i yaparak BER/BLER waterfall eğrileri,
Rayleigh sönümleme kanalı altındaki outage olasılıkları ve ergodik kapasite değerlerini ölçer.
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
    """Test için 1000 paket (77 bayt/paket = 77.000 bayt) veri üretir."""
    # Deterministick test verisi: tekrarlanan patternler
    tx1_data = ("1234567890" * 7 + "1234567") * 1000  # 77 bayt * 1000
    tx2_data = ("abcdefghij" * 7 + "abcdefg") * 1000  # 77 bayt * 1000

    with open(TRANSMIT_1_PATH, "wb") as f:
        f.write(tx1_data.encode('utf-8'))
    with open(TRANSMIT_2_PATH, "wb") as f:
        f.write(tx2_data.encode('utf-8'))

    # Önceki çıktı dosyalarını temizle
    for p in [RECEIVE_1_PATH, RECEIVE_2_PATH]:
        if os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass

def calculate_ber_and_bler(tx_path, rx_path):
    """BER (Bit Error Rate) ve BLER (Block Error Rate) hesaplar."""
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
    # Blok hatalı sayılırsa tamamen eksik (CRC tarafından düşürülmüşse)
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
    # Eksik bitleri de hata olarak say
    mismatches += abs(len(tx_bits) - len(rx_bits))

    ber = float(mismatches) / len(tx_bits)
    return min(1.0, ber), bler

def modify_noma_throttle(rate=500000):
    """NOMA.py içindeki throttle hızını değiştirir."""
    if not os.path.exists(NOMA_PY_PATH):
        return
    with open(NOMA_PY_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Throttle bloklarını bul ve değiştir
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
    """NOMA.py içindeki noise değerini değiştirir."""
    with open(NOMA_PY_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Noise değişimini bul ve değiştir
    content = re.sub(
        r"self\.noise = noise = \d+(\.\d+)?",
        f"self.noise = noise = {noise_val:.6f}",
        content
    )
    with open(NOMA_PY_PATH, "w", encoding="utf-8") as f:
        f.write(content)

def run_simulation(target_size=77000, timeout=120, idle_timeout=5):
    """
    Simülasyonu çalıştırır ve hedef boyuta ulaşıncaya kadar veya timeout olana kadar bekler.
    Dinamik polling kullanır: alinan veri boyutu değişmiyorsa idle counter artar.
    """
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

        # Hedef boyuta ulaşıldı mı?
        if sz1 >= target_size and sz2 >= target_size:
            time.sleep(1.0)  # buffer flush güvenlik beklemesi
            break

        # İddle kontrolü: veri alınıyor ama boyut değişmiyorsa
        if sz1 > 0 or sz2 > 0:
            if sz1 == prev_sz1 and sz2 == prev_sz2:
                idle_counter += 1
            else:
                idle_counter = 0

        # IDLE timeout durumunda durdur
        if idle_counter >= idle_timeout:
            break

        prev_sz1 = sz1
        prev_sz2 = sz2
        time.sleep(0.5)

    # Süreci güvenli şekilde sonlandır
    proc.terminate()
    try:
        proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        proc.kill()

def Q(x):
    """Q fonksiyonu: Q(x) = 0.5 * erfc(x / sqrt(2))"""
    return 0.5 * math.erfc(x / math.sqrt(2.0))

def noma_theoretical_ber_far(sigma, a_f=0.447, a_n=0.894, P=1.0):
    """
    Uzak Kullanici (UE-F) AWGN Teorik Kodsuz BER Formulu:
    P_b,f = 0.5 * [ Q( (sqrt(a_f*P) + sqrt(a_n*P)) / sigma ) + Q( (sqrt(a_f*P) - sqrt(a_n*P)) / sigma ) ]
    Uzak kullanici yakin kullanicinin sinyalini girisim olarak gordugu icin iki Q terimi vardir.
    """
    sqrt_af = math.sqrt(a_f * P)
    sqrt_an = math.sqrt(a_n * P)
    term1 = Q((sqrt_af + sqrt_an) / sigma)
    term2 = Q((sqrt_af - sqrt_an) / sigma)
    return 0.5 * (term1 + term2)

def noma_theoretical_ber_near(sigma, a_n=0.894, P=1.0):
    """
    Yakin Kullanici (UE-N) AWGN Teorik Kodsuz BER Formulu (Mukemmel SIC):
    P_b,n = Q( sqrt(a_n * P) / sigma )
    Mukemmel SIC varsayilirsa, yakin kullanici uzak kullanicinin sinyalini tamamen cikarir.
    """
    sqrt_an = math.sqrt(a_n * P)
    return Q(sqrt_an / sigma)

def bpsk_theoretical_ber(ebno_db):
    """AWGN kanali icin standart teorik BPSK BER."""
    ebno_linear = 10.0 ** (ebno_db / 10.0)
    return 0.5 * math.erfc(math.sqrt(ebno_linear))

def simulate_rayleigh_metrics(sigma, a1=0.894, a2=0.447, gamma_th_db=6.0, num_samples=10000):
    """
    Rayleigh sönümleme kanalı için outage olasılıkları ve ergodik kapasiteleri hesaplar.
    """
    # a1^2 = 0.8, a2^2 = 0.2 (güç paylaşımı)
    gamma_th = 10.0 ** (gamma_th_db / 10.0) # Eşik SINR

    # Rayleigh sönümleme kanalı (exponential channel gain power)
    h2 = np.random.exponential(scale=1.0, size=num_samples)

    # User 2 SINR (Uzak Kullanıcı)
    # SINR2 = a2^2 * h2 / (a1^2 * h2 + sigma^2)
    sinr2 = (a2**2 * h2) / (a1**2 * h2 + sigma**2)

    # User 1 SINR (Yakın Kullanıcı, SIC öncesi ve sonrası)
    # SINR1_to_1 (Kullanıcı 1'in kendisini çözerken Kullanıcı 2'den gördüğü interference-li SINR)
    sinr1_to_1 = (a1**2 * h2) / (a2**2 * h2 + sigma**2)
    # SINR1_to_2 (Kullanıcı 1'in Kullanıcı 2'yi çözerken gördüğü SNR)
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
    """Ana test akışını yönetir."""
    print("======================================================================")
    print("        BPSK NOMA TEST 1: LLS BER & BLER WATERFALL SWEEP              ")
    print("======================================================================")

    # Gürültü voltajları (Eb/N0 sweep aralığı)
    # Eb/N0 (dB) = -20 log10(sigma) - 3 dB
    sigmas = [0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.15, 0.18, 0.21, 0.24, 0.27, 0.30]
    results = []

    # NOMA.py yedeğini al
    backup_path = NOMA_PY_PATH + ".bak"
    if os.path.exists(NOMA_PY_PATH):
        shutil.copyfile(NOMA_PY_PATH, backup_path)

    try:
        # High-speed throttle için ayarla
        modify_noma_throttle(rate=500000)

        for sigma in sigmas:
            # Eb/No hesabı
            ebno_db = -20.0 * math.log10(sigma) - 3.0

            print(f">> Gürültü (sigma): {sigma:.2f} | Eb/N0: {ebno_db:5.1f} dB test ediliyor...")

            # Test dosyalarını hazırla
            prepare_test_files()

            # Noise değerini ayarla
            modify_noma_noise(sigma)

            # Simülasyonu çalıştır (hedef boyuta ulaşana kadar)
            run_simulation(target_size=77000)

            # BER ve BLER hesapla
            ber1, bler1 = calculate_ber_and_bler(TRANSMIT_1_PATH, RECEIVE_1_PATH)
            ber2, bler2 = calculate_ber_and_bler(TRANSMIT_2_PATH, RECEIVE_2_PATH)

            # Rayleigh Fading metriklerini hesapla
            out1, out2, cap1, cap2, sum_cap, oma_sum = simulate_rayleigh_metrics(sigma)

            # Teorik BPSK BER (AWGN, standart)
            theory_ber = bpsk_theoretical_ber(ebno_db)

            # NOMA Teorik Kodsuz BER (AWGN) - Near User ve Far User
            # Guc katsayilari: a_n = 0.894 (near), a_f = 0.447 (far), P = 1.0
            theory_near = noma_theoretical_ber_near(sigma, a_n=0.894, P=1.0)
            theory_far = noma_theoretical_ber_far(sigma, a_f=0.447, a_n=0.894, P=1.0)

            # Sonuclari kaydet
            results.append((sigma, ebno_db, ber1, bler1, ber2, bler2, theory_ber, theory_near, theory_far, out1, out2, cap1, cap2, sum_cap, oma_sum))

            print(f"   [LDPC Kodlu] User 1 BER: {ber1:.2%} (BLER: {bler1:.1%}) | User 2 BER: {ber2:.2%} (BLER: {bler2:.1%})")
            print(f"   [Kodsuz Teorik] Near BER: {theory_near:.4e} | Far BER: {theory_far:.4e}")
            print(f"   [Rayleigh] Outage U1: {out1:.1%} U2: {out2:.1%} | Sum Cap: {sum_cap:.2f} OMA: {oma_sum:.2f} bps/Hz")

    finally:
        # NOMA.py dosyasını orijinal haliyle geri yükle
        if os.path.exists(backup_path):
            shutil.copyfile(backup_path, NOMA_PY_PATH)
            os.remove(backup_path)

    # CSV olarak sonuclari kaydet
    csv_path = "ber_waterfall.csv"
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("Sigma,EbNo_dB,User1_BER_LDPC,User1_BLER,User2_BER_LDPC,User2_BLER,Theory_BPSK_BER,Theory_Near_Uncoded,Theory_Far_Uncoded,Outage_U1,Outage_U2,Cap_U1,Cap_U2,Sum_Cap,OMA_Sum_Cap\n")
        for r in results:
            f.write(",".join([f"{val:.6f}" if isinstance(val, float) else str(val) for val in r]) + "\n")
    print(f"\n-> Sonuclar '{csv_path}' dosyasina kaydedildi.")

    # Grafikleme
    try:
        import matplotlib.pyplot as plt

        # Verileri ayir
        ebno_vals = [r[1] for r in results]
        ber1_vals = [r[2] for r in results]
        bler1_vals = [r[3] for r in results]
        ber2_vals = [r[4] for r in results]
        bler2_vals = [r[5] for r in results]
        theory_bpsk = [r[6] for r in results]
        theory_near = [r[7] for r in results]
        theory_far = [r[8] for r in results]

        out1_vals = [r[9] for r in results]
        out2_vals = [r[10] for r in results]

        cap1_vals = [r[11] for r in results]
        cap2_vals = [r[12] for r in results]
        sum_cap_vals = [r[13] for r in results]
        oma_sum_vals = [r[14] for r in results]

        # Sifir BER degerlerini log olcek icin 1e-7'ye cek
        ber1_plot = [max(v, 1e-7) for v in ber1_vals]
        ber2_plot = [max(v, 1e-7) for v in ber2_vals]
        theory_near_plot = [max(v, 1e-10) for v in theory_near]
        theory_far_plot = [max(v, 1e-10) for v in theory_far]

        # Figure 1: BER Waterfall (LDPC Kodlu Ampirik vs Kodsuz Teorik)
        plt.figure(figsize=(10, 7))
        # LDPC Kodlu Ampirik Egriler (Dolu isaretler)
        plt.semilogy(ebno_vals, ber1_plot, 'g-^', linewidth=2.5, markersize=8, label='User 1 (Near) LDPC Kodlu BER')
        plt.semilogy(ebno_vals, ber2_plot, 'r-o', linewidth=2.5, markersize=8, label='User 2 (Far) LDPC Kodlu BER')
        # NOMA Kodsuz Teorik Egriler (Kesikli cizgiler)
        plt.semilogy(ebno_vals, theory_near_plot, 'g--', linewidth=2, alpha=0.7, label='User 1 (Near) Kodsuz Teorik')
        plt.semilogy(ebno_vals, theory_far_plot, 'r--', linewidth=2, alpha=0.7, label='User 2 (Far) Kodsuz Teorik')
        # Standart BPSK siniri
        plt.semilogy(ebno_vals, theory_bpsk, 'k:', linewidth=1.5, alpha=0.5, label='Standart BPSK Siniri')
        plt.title('BPSK PD-NOMA BER Waterfall: LDPC Kodlu vs Kodsuz Teorik', fontsize=15, fontweight='bold')
        plt.xlabel('Eb/N0 (dB)', fontsize=14)
        plt.ylabel('Bit Hata Orani - BER (Log)', fontsize=14)
        plt.grid(True, which="both", ls="-", alpha=0.3)
        plt.legend(fontsize=10, loc='lower left')
        plt.ylim(1e-7, 1.0)
        plt.tick_params(axis='both', which='major', labelsize=12)
        plt.savefig("ber_waterfall.png", dpi=300, bbox_inches='tight')
        plt.close()

        # Figure 2: BLER (Block Error Rate)
        plt.figure(figsize=(10, 7))
        plt.plot(ebno_vals, [b*100 for b in bler1_vals], 'g-^', linewidth=3, markersize=8, label='User 1 BLER')
        plt.plot(ebno_vals, [b*100 for b in bler2_vals], 'r-o', linewidth=3, markersize=8, label='User 2 BLER')
        plt.title('BPSK NOMA Block Error Rate (BLER/PER) vs. Eb/N0', fontsize=16, fontweight='bold')
        plt.xlabel('Eb/N0 (dB)', fontsize=14)
        plt.ylabel('Block Error Rate - BLER (%)', fontsize=14)
        plt.grid(True, which="both", ls="-", alpha=0.3)
        plt.legend(fontsize=12, loc='upper right')
        plt.tick_params(axis='both', which='major', labelsize=12)
        plt.tick_params(axis='both', which='minor', labelsize=10)
        plt.savefig("bler_waterfall.png", dpi=300, bbox_inches='tight')
        plt.close()

        # Figure 3: Outage Probability
        plt.figure(figsize=(10, 7))
        plt.plot(ebno_vals, [o*100 for o in out1_vals], 'g-^', linewidth=3, markersize=8, label='User 1 Outage')
        plt.plot(ebno_vals, [o*100 for o in out2_vals], 'r-o', linewidth=3, markersize=8, label='User 2 Outage')
        plt.title('Rayleigh Fading Outage Probability\n(QoS Threshold = 6 dB)', fontsize=16, fontweight='bold')
        plt.xlabel('Average Eb/N0 (dB)', fontsize=14)
        plt.ylabel('Outage Probability (%)', fontsize=14)
        plt.grid(True, which="both", ls="-", alpha=0.3)
        plt.legend(fontsize=12, loc='upper right')
        plt.tick_params(axis='both', which='major', labelsize=12)
        plt.tick_params(axis='both', which='minor', labelsize=10)
        plt.savefig("outage_probability.png", dpi=300, bbox_inches='tight')
        plt.close()

        # Figure 4: Ergodic Sum Capacity
        plt.figure(figsize=(10, 7))
        plt.plot(ebno_vals, sum_cap_vals, 'b-d', linewidth=3, markersize=8, label='NOMA Sum Capacity')
        plt.plot(ebno_vals, oma_sum_vals, 'k--', linewidth=2, label='OMA Sum Capacity')
        plt.plot(ebno_vals, cap1_vals, 'g--', linewidth=2, label='User 1 Capacity')
        plt.plot(ebno_vals, cap2_vals, 'r--', linewidth=2, label='User 2 Capacity')
        plt.title('Rayleigh Fading Spectral Efficiency\n(NOMA vs. OMA)', fontsize=16, fontweight='bold')
        plt.xlabel('Average Eb/N0 (dB)', fontsize=14)
        plt.ylabel('Spectral Efficiency (bps/Hz)', fontsize=14)
        plt.grid(True, which="both", ls="-", alpha=0.3)
        plt.legend(fontsize=12, loc='upper right')
        plt.tick_params(axis='both', which='major', labelsize=12)
        plt.tick_params(axis='both', which='minor', labelsize=10)
        plt.savefig("ergodic_capacity.png", dpi=300, bbox_inches='tight')
        plt.close()

        print("-> All plots (ber_waterfall.png, bler_waterfall.png, outage_probability.png, ergodic_capacity.png) successfully saved.")

    except Exception as e:
        print(f"[NOT] Plotting step failed: {e}")

if __name__ == "__main__":
    main()