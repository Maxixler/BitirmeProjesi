#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BPSK NOMA USRP Host Computer Deployment Script (TX & RX Mode - Smart Auto-Detect)
---------------------------------------------------------------------------------
Bu script, iki adet Linux host bilgisayar ve iki adet USRP (TX/RX) kullanarak
gerçek ortamda NOMA dosya transferini tam otomatik hale getirir.

Yenilikçi Özellikler:
  1. Boyut Bilgisiz Çalışma: Alıcıda dosya boyutu girmek ZORUNDA DEĞİLSİNİZ.
  2. Başlık Metotlu İletim: Dosya boyutları ve uzantısı verinin başına 16 baytlık 
     bir üstbilgi (metadata) olarak eklenir. GRC flowgraph'lerinde değişiklik gerekmez.
  3. Sessizlik Süresi (Idle Timeout): İletim bittiğinde alıcı 5 saniye boyunca veri 
     akışının kesildiğini algılar ve kendiliğinden durup dosyaları kurtarır.
  4. Gerçek Zamanlı İlerleme: Alıcı ilk 16 baytı aldığı anda beklenen boyutu 
     çözümler ve yüzde (%) ilerleme çubuğunu anlık günceller.

Kullanım:
  Verici Bilgisayarda (TX Host):
    python3 run_host_transfer.py --mode tx --file1 transmit_1.png --file2 transmit_2.txt

  Alıcı Bilgisayarda (RX Host):
    python3 run_host_transfer.py --mode rx
"""

import os
import sys
import time
import hashlib
import subprocess
import argparse
import shutil

# Dosya yolları
TRANSMIT_1_PATH = "bpsk_transmit.txt"
TRANSMIT_2_PATH = "bpsk_transmit_2.txt"
RECEIVE_1_PATH = "bpsk_receive.txt"
RECEIVE_2_PATH = "bpsk_receive_2.txt"

METADATA_SIZE = 16  # 16 baytlık üstbilgi alanı

def get_md5(data):
    """Verinin MD5 hash değerini hesaplar."""
    return hashlib.md5(data).hexdigest()

def compile_grc(grc_file, py_file):
    """GRC dosyasını grcc kullanarak Python dosyasına derler."""
    print(f"-> {grc_file} derleniyor...")
    grcc_path = "grcc"
    if sys.platform.startswith("win"):
        radioconda_grcc = r"C:\Users\Armagan\radioconda\Scripts\grcc.exe"
        if os.path.exists(radioconda_grcc):
            grcc_path = radioconda_grcc

    try:
        res = subprocess.run([grcc_path, grc_file], capture_output=True, text=True)
        if res.returncode == 0:
            print(f"-> Derleme başarılı ve güncel {py_file} oluşturuldu.")
            return True
        else:
            print(f"[UYARI] Derleme hatası! STDOUT: {res.stdout} | STDERR: {res.stderr}")
    except Exception as e:
        print(f"[UYARI] grcc çalıştırılamadı. Python dosyası ({py_file}) varsa kullanılacaktır. Hata: {e}")
    
    return os.path.exists(py_file)

def run_tx_mode(args):
    """Verici (TX) Modu İşlemleri"""
    print("\n======================================================================")
    print("        BPSK NOMA HOST VERICI (TX) MODU - SMART METADATA HEADER       ")
    print("======================================================================")

    # 1. GRC Derleme
    grc_file = "TX_host.grc"
    py_file = "TX_host.py"
    if not compile_grc(grc_file, py_file):
        print(f"[HATA] {py_file} oluşturulamadı ve bulunamadı!")
        return

    # 2. Giriş dosyalarını oku
    file1_path = args.file1
    file2_path = args.file2

    if not os.path.exists(file1_path) or not os.path.exists(file2_path):
        print(f"[HATA] İletilecek dosyalar bulunamadı! Yol: {file1_path} ve {file2_path}")
        return

    with open(file1_path, "rb") as f:
        data1 = f.read()
    with open(file2_path, "rb") as f:
        data2 = f.read()

    len1 = len(data1)
    len2 = len(data2)

    # MD5 hashlerini hesapla
    md5_1 = get_md5(data1)
    md5_2 = get_md5(data2)

    # Uzantıları tespit et
    ext1 = os.path.splitext(file1_path)[1].replace(".", "") or "dat"
    ext2 = os.path.splitext(file2_path)[1].replace(".", "") or "dat"

    print("-> Orijinal Dosya Bilgileri:")
    print(f"   [User 1] {file1_path}: {len1} B | MD5: {md5_1} | Uzantı: {ext1}")
    print(f"   [User 2] {file2_path}: {len2} B | MD5: {md5_2} | Uzantı: {ext2}")

    # 3. Üstbilgi (Metadata Header) Oluşturma
    # Format: "boyut:uzanti:md5" şeklinde 16 baytlık bloklara sığdıracağız.
    # User 1 üstbilgi: "len1:ext1"
    header1_str = f"{len1}:{ext1}:{md5_1}"
    header1 = header1_str.encode('utf-8')
    if len(header1) > METADATA_SIZE:
        # Eger sığmazsa MD5'sız sadece boyut ve uzantı koy
        header1 = f"{len1}:{ext1}".encode('utf-8')
    header1 = header1.ljust(METADATA_SIZE, b'\x00')

    # User 2 üstbilgi: "len2:ext2"
    header2_str = f"{len2}:{ext2}:{md5_2}"
    header2 = header2_str.encode('utf-8')
    if len(header2) > METADATA_SIZE:
        header2 = f"{len2}:{ext2}".encode('utf-8')
    header2 = header2.ljust(METADATA_SIZE, b'\x00')

    # Verileri başlıkla birleştir
    tx1_data = header1 + data1
    tx2_data = header2 + data2

    max_len = max(len(tx1_data), len(tx2_data))

    # 77'nin katına tamamla
    payload_size = 77
    padded_len = ((max_len + payload_size - 1) // payload_size) * payload_size
    print(f"-> Toplam Padded Boyut (Başlıklar dahil): {padded_len} bayt (77'nin katı)")

    padded_tx1 = tx1_data + b'\x00' * (padded_len - len(tx1_data))
    padded_tx2 = tx2_data + b'\x00' * (padded_len - len(tx2_data))

    # İletim dosyalarını diske yaz
    with open(TRANSMIT_1_PATH, "wb") as f:
        f.write(padded_tx1)
    with open(TRANSMIT_2_PATH, "wb") as f:
        f.write(padded_tx2)
    print("-> İletim dosyaları hazırlandı.")

    # 4. Modül önbelleğini temizleme
    pycache = "__pycache__"
    if os.path.exists(pycache):
        try:
            shutil.rmtree(pycache)
        except Exception:
            pass

    # 5. TX Akışını Başlat
    print("-> Verici akış diyagramı başlatılıyor...")
    python_exe = sys.executable
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    
    try:
        proc = subprocess.Popen([python_exe, py_file], env=env)
        print("\n[TX AKTIF] USRP verici yayında. Kapatmak için Ctrl+C tuşlarına basın.")
        proc.wait()
    except KeyboardInterrupt:
        print("\n-> Kullanıcı talebiyle verici durduruldu.")
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()

def parse_header(file_path):
    """Dosyanın ilk 16 baytından dosya boyutunu ve uzantısını çözümler."""
    if not os.path.exists(file_path) or os.path.getsize(file_path) < METADATA_SIZE:
        return None
    
    try:
        with open(file_path, "rb") as f:
            header_bytes = f.read(METADATA_SIZE)
        
        # Null byte'ları temizle ve string'e çevir
        header_str = header_bytes.split(b'\x00')[0].decode('utf-8')
        parts = header_str.split(':')
        
        orig_len = int(parts[0])
        orig_ext = parts[1]
        orig_md5 = parts[2] if len(parts) > 2 else ""
        return orig_len, orig_ext, orig_md5
    except Exception:
        return None

def run_rx_mode(args):
    """Alıcı (RX) Modu İşlemleri - Auto-Detection & Idle Timeout"""
    print("\n======================================================================")
    print("      BPSK NOMA HOST ALICI (RX) MODU - SMART AUTO-DETECTION AKTIF     ")
    print("======================================================================")

    # 1. GRC Derleme
    grc_file = "RX_host.grc"
    py_file = "RX_host.py"
    if not compile_grc(grc_file, py_file):
        print(f"[HATA] {py_file} oluşturulamadı ve bulunamadı!")
        return

    # 2. Eski dosyaları temizle
    for p in [RECEIVE_1_PATH, RECEIVE_2_PATH]:
        if os.path.exists(p):
            try:
                os.remove(p)
            except Exception as e:
                pass

    # 3. RX Akışını Başlat
    python_exe = sys.executable
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    print("-> Alıcı akış diyagramı başlatılıyor...")
    proc = subprocess.Popen([python_exe, py_file], env=env)

    print("\n======================================================================")
    print(" [RX AKTIF] Havadan veri bekleniyor... İletim bittiğinde otomatik duracaktır.")
    print("======================================================================\n")

    start_time = time.time()
    
    # Boyut bilgileri (Başlıktan okunacak)
    len1, ext1, md5_1 = 0, "dat", ""
    len2, ext2, md5_2 = 0, "dat", ""
    padded_len = 0
    header_parsed_1 = False
    header_parsed_2 = False

    # İletim sonu algılama değişkenleri
    prev_sz1 = 0
    prev_sz2 = 0
    idle_counter = 0
    timeout_threshold = 5  # 5 saniye boyunca veri gelmezse durdur
    completed = False

    try:
        while True:
            sz1 = os.path.getsize(RECEIVE_1_PATH) if os.path.exists(RECEIVE_1_PATH) else 0
            sz2 = os.path.getsize(RECEIVE_2_PATH) if os.path.exists(RECEIVE_2_PATH) else 0

            # 1. Başlıkları Çözümleme (Real-time Parsing)
            if not header_parsed_1 and sz1 >= METADATA_SIZE:
                meta = parse_header(RECEIVE_1_PATH)
                if meta:
                    len1, ext1, md5_1 = meta
                    header_parsed_1 = True
            
            if not header_parsed_2 and sz2 >= METADATA_SIZE:
                meta = parse_header(RECEIVE_2_PATH)
                if meta:
                    len2, ext2, md5_2 = meta
                    header_parsed_2 = True

            # Eğer her iki başlık da çözümlendiyse, hedeflenen padded boyutu hesapla
            if header_parsed_1 and header_parsed_2 and padded_len == 0:
                max_len = max(len1 + METADATA_SIZE, len2 + METADATA_SIZE)
                payload_size = 77
                padded_len = ((max_len + payload_size - 1) // payload_size) * payload_size
                print(f"\n[INFO] Başlıklar Algılandı! Hedef İletim Boyutu: {padded_len} bayt")
                print(f"       User 1: {len1} B ({ext1}) | User 2: {len2} B ({ext2})")

            # Yüzde hesaplama
            pct1 = min(100.0, (sz1 / padded_len) * 100) if padded_len > 0 else 0
            pct2 = min(100.0, (sz2 / padded_len) * 100) if padded_len > 0 else 0

            elapsed = int(time.time() - start_time)
            print(f"   [Sure: {elapsed}s] User 1: {sz1} B ({pct1:.1f}%) | User 2: {sz2} B ({pct2:.1f}%) | Idle: {idle_counter}s", end="\r", flush=True)

            # 2. İletimin Bittiğini / Durduğunu Algılama (Idle Timeout)
            if sz1 > 0 or sz2 > 0:
                if sz1 == prev_sz1 and sz2 == prev_sz2:
                    idle_counter += 1
                else:
                    idle_counter = 0  # Yeni veri geldiyse sayacı sıfırla
            
            prev_sz1 = sz1
            prev_sz2 = sz2

            # Veriler tamamlandıysa veya iletim kesildikten sonra timeout dolduysa
            if padded_len > 0 and sz1 >= padded_len and sz2 >= padded_len:
                print(f"\n\n[OK] Hedef veri boyutuna ulaşıldı!")
                completed = True
                break

            if idle_counter >= timeout_threshold:
                if sz1 >= METADATA_SIZE and sz2 >= METADATA_SIZE:
                    print(f"\n\n[INFO] Bit iletimi kesildi (5 saniye sessizlik). Dosya kaydetme başlatılıyor...")
                    completed = True
                else:
                    print(f"\n\n[HATA] Veri akışı başlamadan veya başlıklar alınamadan kesildi.")
                break

            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\n-> Kullanıcı talebiyle alıcı durduruluyor...")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
        print("-> Alıcı akış diyagramı kapatıldı.")

    # 6. Padding temizleme ve kurtarma (Strip)
    if completed:
        print("\n-> Alınan dosyalardan dolgular ve başlıklar temizleniyor...")
        
        with open(RECEIVE_1_PATH, "rb") as f:
            rx1_data = f.read()
        with open(RECEIVE_2_PATH, "rb") as f:
            rx2_data = f.read()

        # Eğer başlıklar çalışma esnasında çözümlenemediyse son kez dosyadan dene
        if not header_parsed_1:
            meta = parse_header(RECEIVE_1_PATH)
            if meta:
                len1, ext1, md5_1 = meta
                header_parsed_1 = True
        if not header_parsed_2:
            meta = parse_header(RECEIVE_2_PATH)
            if meta:
                len2, ext2, md5_2 = meta
                header_parsed_2 = True

        if header_parsed_1 and len(rx1_data) >= len1 + METADATA_SIZE:
            clean_1 = rx1_data[METADATA_SIZE : METADATA_SIZE + len1]
            out1_name = f"recovered_user_1.{ext1}"
            with open(out1_name, "wb") as f:
                f.write(clean_1)
            print(f"   [User 1] Kurtarıldı -> {out1_name} ({len(clean_1)} bayt)")
            
            if md5_1:
                rx_md5_1 = get_md5(clean_1)
                if rx_md5_1 == md5_1:
                    print(f"   [User 1] MD5 EŞLEŞTİ! (MD5: {rx_md5_1})")
                else:
                    print(f"   [User 1] HATA: MD5 Uyuşmadı! Beklenen: {md5_1} | Alınan: {rx_md5_1}")
        else:
            print(f"   [User 1] HATA: Veri boyutu kurtarma için yetersiz! Alınan: {len(rx1_data)}")

        if header_parsed_2 and len(rx2_data) >= len2 + METADATA_SIZE:
            clean_2 = rx2_data[METADATA_SIZE : METADATA_SIZE + len2]
            out2_name = f"recovered_user_2.{ext2}"
            with open(out2_name, "wb") as f:
                f.write(clean_2)
            print(f"   [User 2] Kurtarıldı -> {out2_name} ({len(clean_2)} bayt)")

            if md5_2:
                rx_md5_2 = get_md5(clean_2)
                if rx_md5_2 == md5_2:
                    print(f"   [User 2] MD5 EŞLEŞTİ! (MD5: {rx_md5_2})")
                else:
                    print(f"   [User 2] HATA: MD5 Uyuşmadı! Beklenen: {md5_2} | Alınan: {rx_md5_2}")
        else:
            print(f"   [User 2] HATA: Veri boyutu kurtarma için yetersiz! Alınan: {len(rx2_data)}")

        print("\n======================================================================")
        print("          BPSK NOMA USRP DONANIMSAL TRANSFER TAMAMLANDI               ")
        print("======================================================================")
    else:
        print("\n[HATA] Veri akışı tamamlanamadan kesildi.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BPSK NOMA Host USRP Run Manager (Smart Auto-Detect)")
    parser.add_argument("--mode", type=str, required=True, choices=["tx", "rx"], help="tx veya rx modu")
    
    # TX Modu Argümanları
    parser.add_argument("--file1", type=str, default="transmit_1.png", help="TX: User 1 gönderim dosyası")
    parser.add_argument("--file2", type=str, default="transmit_2.png", help="TX: User 2 gönderim dosyası")

    args = parser.parse_args()

    if args.mode == "tx":
        run_tx_mode(args)
    elif args.mode == "rx":
        run_rx_mode(args)
