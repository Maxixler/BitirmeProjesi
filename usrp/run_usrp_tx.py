#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BPSK NOMA USRP Transmitter Executable and Padding Script
-------------------------------------------------------
Bu script, gönderilecek iki adet resmi (veya dosyayı) okur,
GNU Radio'yu kilitlemeyecek şekilde 77 baytın katlarına dolgular (padding),
ardından NOMA_TX flowgraph'ını doğrudan başlatarak fiziksel anten üzerinden iletir.
"""

import os
import sys
import time
import hashlib
import argparse

# run_usrp_tx.py'nin bulunduğu dizini sisteme ekle
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)

from NOMA_TX import NOMA_TX

def get_md5(data):
    """Verinin MD5 hash degerini hesaplar."""
    return hashlib.md5(data).hexdigest()

def main():
    parser = argparse.ArgumentParser(description="BPSK NOMA USRP Transmitter & Padding Wrapper")
    parser.add_argument("--img1", type=str, default="transmit_1.png", help="User 1 gonderilecek resim/dosya")
    parser.add_argument("--img2", type=str, default="transmit_2.png", help="User 2 gonderilecek resim/dosya")
    parser.add_argument("--freq", type=float, default=868e6, help="Merkez frekansi (Hz) [varsayilan: 868e6]")
    parser.add_argument("--rate", type=float, default=200e3, help="Ornekleme hizi (samples/sn) [varsayilan: 200e3]")
    parser.add_argument("--gain", type=float, default=20.0, help="USRP TX Kazanci (dB) [varsayilan: 20.0]")
    args = parser.parse_args()

    project_dir = os.path.dirname(script_dir)
    img1_path = os.path.join(project_dir, args.img1)
    img2_path = os.path.join(project_dir, args.img2)

    print("======================================================================")
    print("             BPSK NOMA USRP FISIKSEL VERICIwrapper ARACI             ")
    print("======================================================================")

    # 1. Giris dosyalarinin kontrolu
    if not os.path.exists(img1_path) or not os.path.exists(img2_path):
        # Proje ana klasöründe yoksa yerel usrp klasöründe ara
        img1_path = os.path.join(script_dir, args.img1)
        img2_path = os.path.join(script_dir, args.img2)
        if not os.path.exists(img1_path) or not os.path.exists(img2_path):
            print(f"[HATA] Gönderilecek dosyalar bulunamadı! Lütfen yolları kontrol edin.")
            print(f"       Aranan: {args.img1} ve {args.img2}")
            return

    # Orijinal verileri oku
    with open(img1_path, "rb") as f:
        data1 = f.read()
    with open(img2_path, "rb") as f:
        data2 = f.read()

    len1 = len(data1)
    len2 = len(data2)
    max_len = max(len1, len2)

    # MD5 hashlerini hesapla (doğrulama için)
    md5_tx1 = get_md5(data1)
    md5_tx2 = get_md5(data2)

    print("-> Orijinal Dosya Boyutlari ve MD5 Hashleri:")
    print(f"   [User 1] {os.path.basename(img1_path)}: {len1} bayt (MD5: {md5_tx1})")
    print(f"   [User 2] {os.path.basename(img2_path)}: {len2} bayt (MD5: {md5_tx2})")

    # 2. Kısa dosyayı sıfırlarla doldur (Padding)
    # GNU Radio LDPC ve Tagged Stream sınırları için 77'nin tam katına tamamlıyoruz.
    payload_size = 77
    padded_len = ((max_len + payload_size - 1) // payload_size) * payload_size

    print(f"-> Dolgu boyutu hesaplandi: {padded_len} bayt (77'nin kati, orijinal maks: {max_len})")

    padded_data1 = data1 + b'\x00' * (padded_len - len1)
    padded_data2 = data2 + b'\x00' * (padded_len - len2)

    # NOMA aktarım dosyalarını local usrp klasörüne kaydet
    tx1_out = os.path.join(script_dir, 'bpsk_transmit.txt')
    tx2_out = os.path.join(script_dir, 'bpsk_transmit_2.txt')

    with open(tx1_out, "wb") as f:
        f.write(padded_data1)
    with open(tx2_out, "wb") as f:
        f.write(padded_data2)

    print(f"-> Aktarim dosyalari hazirlandi.")

    # 3. USRP Verici akış diyagramını başlat
    print(f"-> NOMA USRP Vericisi baslatiliyor...")
    print(f"   Frekans  : {args.freq/1e6:.3f} MHz")
    print(f"   Ornekleme: {args.rate/1e3:.1f} kSps")
    print(f"   TX Kazanc: {args.gain} dB")

    tb = NOMA_TX(samp_rate=int(args.rate), center_freq=args.freq, tx_gain=args.gain)
    tb.start()

    print("\n======================================================================")
    print(" [TX RUNNING] NOMA superpoze sinyali havadan surekli iletiliyor...")
    print(" Kapatmak ve durdurmak icin Ctrl+C tuslarina basin.")
    print("======================================================================")
    
    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\n-> Kullanici talebiyle iletim durduruluyor...")
    finally:
        tb.stop()
        tb.wait()
        print("-> Verici basariyla kapatildi ve temizlendi.")

if __name__ == "__main__":
    main()
