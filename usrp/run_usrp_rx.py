#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BPSK NOMA USRP Receiver Executable and Stripping Script
------------------------------------------------------
Bu script, havadan gelen USRP BPSK NOMA sinyallerini alır,
alıcı akış diyagramını çalıştırarak verileri dosyaya kaydeder,
alıcıda dosya boyutlarını anlık takip eder, veri alımı bitince
dolgu (padding) sıfırlarını temizler (strip) ve MD5 hash kontrolü ile
dosyaları birebir kurtarır.
"""

import os
import sys
import time
import hashlib
import argparse

# run_usrp_rx.py'nin bulunduğu dizini sisteme ekle
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)

from NOMA_RX import NOMA_RX

def get_md5(data):
    """Verinin MD5 hash degerini hesaplar."""
    return hashlib.md5(data).hexdigest()

def main():
    parser = argparse.ArgumentParser(description="BPSK NOMA USRP Receiver & Stripper Wrapper")
    parser.add_argument("--len1", type=int, default=302574, help="User 1 orijinal dosya boyutu (bayt) [varsayilan: 302574]")
    parser.add_argument("--len2", type=int, default=163032, help="User 2 orijinal dosya boyutu (bayt) [varsayilan: 163032]")
    parser.add_argument("--freq", type=float, default=868e6, help="Merkez frekansi (Hz) [varsayilan: 868e6]")
    parser.add_argument("--rate", type=float, default=200e3, help="Ornekleme hizi (samples/sn) [varsayilan: 200e3]")
    parser.add_argument("--gain", type=float, default=25.0, help="USRP RX Kazanci (dB) [varsayilan: 25.0]")
    parser.add_argument("--md5_1", type=str, default="ce84fa42daddfb0984df89441ec5f2ec", help="User 1 beklenen MD5 [varsayilan: ce84fa...]")
    parser.add_argument("--md5_2", type=str, default="36e725e648c59ccee69186021bf2cd6a", help="User 2 beklenen MD5 [varsayilan: 36e725...]")
    args = parser.parse_args()

    # Çıkış dosyaları (Dolgulu ham veriler)
    rx1_raw = os.path.join(script_dir, 'bpsk_receive.txt')
    rx2_raw = os.path.join(script_dir, 'bpsk_receive_2.txt')

    # Kurtarılmış nihai dosyalar
    rx1_final = os.path.join(script_dir, 'bpsk_receive.png')
    rx2_final = os.path.join(script_dir, 'bpsk_receive_2.png')

    print("======================================================================")
    print("             BPSK NOMA USRP FISIKSEL ALICI WRAPPER ARACI              ")
    print("======================================================================")
    print("-> Beklenen Orijinal Boyutlar:")
    print(f"   [User 1] User 1: {args.len1} bayt")
    print(f"   [User 2] User 2: {args.len2} bayt")

    # 1. Eski çıktı dosyalarını temizle
    for p in [rx1_raw, rx2_raw, rx1_final, rx2_final]:
        if os.path.exists(p):
            try:
                os.remove(p)
            except Exception as e:
                print(f"[UYARI] {p} silinemedi: {e}")

    # 77'nin katı olacak şekilde dolgulu beklenen boyutu hesapla
    payload_size = 77
    max_len = max(args.len1, args.len2)
    padded_len = ((max_len + payload_size - 1) // payload_size) * payload_size
    print(f"-> Dolgulu iletim boyutu: {padded_len} bayt.")

    # 2. USRP Alıcı akış diyagramını başlat
    print(f"-> NOMA USRP Alicisi baslatiliyor...")
    print(f"   Frekans  : {args.freq/1e6:.3f} MHz")
    print(f"   Ornekleme: {args.rate/1e3:.1f} kSps")
    print(f"   RX Kazanc: {args.gain} dB")

    tb = NOMA_RX(samp_rate=int(args.rate), center_freq=args.freq, rx_gain=args.gain)
    tb.start()

    print("\n======================================================================")
    print(" [RX RUNNING] Havadan sinyal bekleniyor. Lutfen vericiyi calistirin.")
    print(" Durdurmak icin Ctrl+C tuslarina basin.")
    print("======================================================================")

    start_time = time.time()
    completed = False

    try:
        while True:
            # Alınan ham verilerin boyutunu anlık takip et
            sz1 = os.path.getsize(rx1_raw) if os.path.exists(rx1_raw) else 0
            sz2 = os.path.getsize(rx2_raw) if os.path.exists(rx2_raw) else 0

            elapsed = int(time.time() - start_time)
            pct1 = min(100.0, (sz1 / padded_len) * 100) if padded_len > 0 else 0
            pct2 = min(100.0, (sz2 / padded_len) * 100) if padded_len > 0 else 0

            print(f"   [Sure: {elapsed}s] User 1: {sz1}/{padded_len} B ({pct1:.1f}%) | User 2: {sz2}/{padded_len} B ({pct2:.1f}%)", end="\r", flush=True)

            # Her iki dosya da en az beklenen orijinal boyuta ulaştıysa aktarımı başarıyla sonlandır
            if sz1 >= args.len1 and sz2 >= args.len2:
                print(f"\n\n[OK] Her iki dosya da havadan tamamen alindi! (User 1: {sz1}/{args.len1} B, User 2: {sz2}/{args.len2} B)")
                print("-> Verilerin diske tam yazilmasi ve senkronizasyon icin 3 saniye bekleniyor...")
                time.sleep(3.0)
                completed = True
                break

            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\n-> Kullanici talebiyle alici durduruluyor...")
    finally:
        tb.stop()
        tb.wait()
        print("-> Alici basariyla kapatildi.")

    # 3. Dosyaları kurtar ve dolguları temizle (Strip Padding)
    if completed:
        print("\n-> Alici tarafta dolgular temizleniyor ve dosyalar kurtariliyor...")
        
        rx1_data = b""
        if os.path.exists(rx1_raw):
            with open(rx1_raw, "rb") as f:
                rx1_data = f.read()

        rx2_data = b""
        if os.path.exists(rx2_raw):
            with open(rx2_raw, "rb") as f:
                rx2_data = f.read()

        success_1 = False
        success_2 = False

        if len(rx1_data) >= args.len1:
            clean_rx1 = rx1_data[:args.len1]
            md5_rx1 = get_md5(clean_rx1)
            
            with open(rx1_final, "wb") as f:
                f.write(clean_rx1)
                
            if md5_rx1 == args.md5_1:
                print(f"[OK] [User 1] Resim BASARIYLA kurtarildi! {os.path.basename(rx1_final)} ({len(clean_rx1)} B) - MD5 ESLESTI")
                success_1 = True
            else:
                print(f"[HATA] [User 1] Resim kurtarildi ama veri bozulmus! MD5 uyusmadi.")
                print(f"       Beklenen: {args.md5_1} | Alinan: {md5_rx1}")
        else:
            print(f"[HATA] [User 1] Yetersiz veri alindi ({len(rx1_data)}/{args.len1} bayt).")

        if len(rx2_data) >= args.len2:
            clean_rx2 = rx2_data[:args.len2]
            md5_rx2 = get_md5(clean_rx2)
            
            with open(rx2_final, "wb") as f:
                f.write(clean_rx2)
                
            if md5_rx2 == args.md5_2:
                print(f"[OK] [User 2] Resim BASARIYLA kurtarildi! {os.path.basename(rx2_final)} ({len(clean_rx2)} B) - MD5 ESLESTI")
                success_2 = True
            else:
                print(f"[HATA] [User 2] Resim kurtarildi ama veri bozulmus! MD5 uyusmadi.")
                print(f"       Beklenen: {args.md5_2} | Alinan: {md5_rx2}")
        else:
            print(f"[HATA] [User 2] Yetersiz veri alindi ({len(rx2_data)}/{args.len2} bayt).")

        print("======================================================================")
        if success_1 and success_2:
            print("  TEBRIKLER! BPSK NOMA USRP ILE DONANIMSAL RESIM TRANSFERI BASARILI   ")
        else:
            print("  TRANSFER BASARISIZ! LUTFEN LOGLARI/BAGLANTILARI KONTROL EDIN.      ")
        print("======================================================================")
    else:
        print("\n[UYARI] Simülasyon tamamlanmadan kesildi. Kurtarma yapilamadi.")

if __name__ == "__main__":
    main()
