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
    else:
        # Linux: radioconda ortamındaki grcc
        linux_grcc = os.path.expanduser("~/radioconda/envs/bitirme/bin/grcc")
        if os.path.exists(linux_grcc):
            grcc_path = linux_grcc

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

    # 3. Sıra numarası (Sequence Number) tabanlı paketleme
    # Her veri paketi: 2 bayt seq_num + 75 bayt payload = 77 bayt
    # Başlık paketi: seq_num = 0, payload = metadata string'i
    
    # User 1 Paketleri
    chunks1 = [data1[i : i + 75] for i in range(0, len(data1), 75)]
    packets1 = []
    # 5 adet yedekli başlık paketi (seq = 0)
    for _ in range(5):
        h1 = f"{len1}:{ext1}:{md5_1}".encode('utf-8')
        h1 = h1.ljust(75, b'\x00')
        packets1.append(b'\x00\x00' + h1)
    # Veri paketleri (seq >= 1)
    for seq, chunk in enumerate(chunks1, start=1):
        seq_bytes = seq.to_bytes(2, byteorder='big')
        packets1.append(seq_bytes + chunk.ljust(75, b'\x00'))
        
    # User 2 Paketleri
    chunks2 = [data2[i : i + 75] for i in range(0, len(data2), 75)]
    packets2 = []
    # 5 adet yedekli başlık paketi (seq = 0)
    for _ in range(5):
        h2 = f"{len2}:{ext2}:{md5_2}".encode('utf-8')
        h2 = h2.ljust(75, b'\x00')
        packets2.append(b'\x00\x00' + h2)
    # Veri paketleri (seq >= 1)
    for seq, chunk in enumerate(chunks2, start=1):
        seq_bytes = seq.to_bytes(2, byteorder='big')
        packets2.append(seq_bytes + chunk.ljust(75, b'\x00'))

    # Eğitim ön eki
    training_packet = b"TRAIN:" + b"x" * 70 + b"\x00"  # 77 bytes
    training_prefix = training_packet * 60  # 60 training packets (4620 bytes)

    tx1_data = training_prefix + b"".join(packets1)
    tx2_data = training_prefix + b"".join(packets2)

    max_len = max(len(tx1_data), len(tx2_data))

    # 77'nin katına tamamla
    payload_size = 77
    padded_len = ((max_len + payload_size - 1) // payload_size) * payload_size
    print(f"-> Toplam Padded Boyut (Eğitim + Başlıklar + Veriler): {padded_len} bayt ({padded_len//77} paket)")

    # Özel dolgu paketi (seq = 65535, payload = zeros)
    pad_packet = b'\xff\xff' + b'\x00' * 75
    num_pad_1 = (padded_len - len(tx1_data)) // 77
    num_pad_2 = (padded_len - len(tx2_data)) // 77

    padded_tx1 = tx1_data + pad_packet * num_pad_1
    padded_tx2 = tx2_data + pad_packet * num_pad_2

    # USRP/GRC kapanışındaki donanımsal kuyruk kesintisini (Buffer Cut-off) önlemek için 60 paket kuyruk dolgusu ekle.
    tail_padding = pad_packet * 60
    padded_tx1 += tail_padding
    padded_tx2 += tail_padding

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
        log_file = open("tx_output.log", "w")
        proc = subprocess.Popen([python_exe, py_file], env=env, stdout=log_file, stderr=log_file)
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
    """Dosyanın ilk kısımlarını tarayarak dosya boyutu ve uzantısını çözümler.
    Eğer ilk paketler kaybolduysa veya eğitim paketleri varsa, 77'şer baytlık paket sınırlarında arama yapar.
    """
    if not os.path.exists(file_path) or os.path.getsize(file_path) < 77:
        return None
    
    try:
        with open(file_path, "rb") as f:
            # İlk 200 paketi oku (yaklaşık 15400 bayt)
            data = f.read(15400)
        
        # 77 baytlık paket sınırlarını kontrol et
        for offset in range(0, len(data) - 76, 77):
            pkt = data[offset : offset + 77]
            seq = int.from_bytes(pkt[:2], byteorder='big')
            payload = pkt[2:]
            if seq == 0:
                try:
                    # Null byte'ları temizle ve string'e çevir
                    header_str = payload.split(b'\x00')[0].decode('utf-8', errors='ignore')
                    parts = header_str.split(':')
                    if len(parts) >= 2:
                        length = int(parts[0])
                        ext = parts[1]
                        md5_val = parts[2] if len(parts) > 2 else ""
                        if length > 0 and len(ext) <= 5:
                            return length, ext, md5_val, offset
                except Exception:
                    continue
        return None
    except Exception:
        return None

def recover_file_from_packets(file_path):
    """
    77 baytlık paketlerden oluşan dosyayı okur, her paketteki 2-baytlık sıra numarasına (seq_num)
    göre veriyi yeniden birleştirir.
    Düşen paketlerin yerine sıfır (0x00) doldurarak kaymaları %100 engeller.
    """
    if not os.path.exists(file_path) or os.path.getsize(file_path) < 77:
        return None
        
    try:
        with open(file_path, "rb") as f:
            rx_data = f.read()
            
        packets = [rx_data[i : i + 77] for i in range(0, len(rx_data) - 76, 77)]
        
        # 1. Başlık paketini bul
        header_parsed = False
        length = 0
        ext = "dat"
        md5_val = ""
        
        for pkt in packets:
            seq = int.from_bytes(pkt[:2], byteorder='big')
            payload = pkt[2:]
            if seq == 0:
                try:
                    header_str = payload.split(b'\x00')[0].decode('utf-8', errors='ignore')
                    parts = header_str.split(':')
                    if len(parts) >= 2:
                        length = int(parts[0])
                        ext = parts[1]
                        md5_val = parts[2] if len(parts) > 2 else ""
                        if length > 0 and len(ext) <= 5:
                            header_parsed = True
                            break
                except Exception:
                    continue
                    
        if not header_parsed:
            return None
            
        # 2. Veri paketlerini yerleştir
        recovered_data = bytearray(length)
        max_packets = (length + 74) // 75
        
        received_packets_count = 0
        unique_seqs = set()
        
        for pkt in packets:
            seq = int.from_bytes(pkt[:2], byteorder='big')
            payload = pkt[2:]
            if 0 < seq <= max_packets:
                if seq not in unique_seqs:
                    unique_seqs.add(seq)
                    received_packets_count += 1
                
                start_idx = (seq - 1) * 75
                end_idx = min(seq * 75, length)
                recovered_data[start_idx:end_idx] = payload[:end_idx - start_idx]
                
        return bytes(recovered_data), ext, md5_val, received_packets_count, max_packets
    except Exception as e:
        print(f"[RECOVERY ERROR] {e}")
        return None

def fix_png_crc(file_path):
    """PNG dosyasının içindeki chunk CRC'lerini yeniden hesaplar.
    Bu sayede eksik paketler (sıfır dolgular) nedeniyle PNG görüntüleyicilerin
    dosyayı açmayı reddetmesini engeller."""
    import struct
    import zlib
    
    try:
        with open(file_path, "rb") as f:
            data = f.read()
            
        if len(data) < 8 or data[:8] != b'\x89PNG\r\n\x1a\n':
            return
            
        out_data = bytearray(data[:8])
        idx = 8
        while idx < len(data):
            if idx + 8 > len(data):
                break
            length = struct.unpack('>I', data[idx:idx+4])[0]
            chunk_type = data[idx+4:idx+8]
            data_start = idx + 8
            data_end = data_start + length
            if data_end > len(data):
                break
            chunk_data = data[data_start:data_end]
            
            # CRC yeniden hesapla (Type + Data)
            new_crc = zlib.crc32(chunk_type + chunk_data) & 0xffffffff
            
            out_data.extend(data[idx:idx+8])
            out_data.extend(chunk_data)
            out_data.extend(struct.pack('>I', new_crc))
            
            idx = data_end + 4
            
        with open(file_path, "wb") as f:
            f.write(out_data)
        print("   [PNG OTO-DÜZELTME] PNG dosyasının CRC blokları başarıyla güncellendi (Açılabilir durumda).")
    except Exception as e:
        print(f"   [PNG OTO-DÜZELTME HATA] CRC düzeltme başarısız: {e}")

def run_rx_mode(args):
    """Alıcı (RX) Modu İşlemleri - Auto-Detection & Idle Timeout"""
    print("\n======================================================================")
    print("      BPSK NOMA HOST ALICI (RX) MODU - SMART AUTO-DETECTION AKTIF     ")
    print("======================================================================")

    # RX Gain ve near_user_amplitude değerlerini GRC dosyasında dinamik güncelle (eğer gain belirtildiyse)
    if args.gain is not None:
        try:
            with open("RX_host.grc", "r", encoding="utf-8") as f:
                content = f.read()
                
            # 1. gain0 parametresini güncelle
            import re
            content = re.sub(r"gain0:\s*'\d+'", f"gain0: '{args.gain}'", content)
            
            # 2. near_user_amplitude parametresini ölçekle ve güncelle
            # Referans: 52 dB kazançta genlik 0.27'dir.
            new_amp = round(0.27 * (10 ** ((args.gain - 52) / 20.0)), 3)
            content = re.sub(r"near_user_amplitude:\s*'\d+\.?\d*'", f"near_user_amplitude: '{new_amp}'", content)
            
            with open("RX_host.grc", "w", encoding="utf-8") as f:
                f.write(content)
                
            print(f"-> GRC Kazanç Ayarı Güncellendi: Gain = {args.gain} dB | Beklenen Genlik = {new_amp}")
        except Exception as e:
            print(f"[HATA] GRC kazanç ayarı güncellenemedi: {e}")
    else:
        try:
            with open("RX_host.grc", "r", encoding="utf-8") as f:
                content = f.read()
            import re
            gain_match = re.search(r"gain0:\s*'(\d+)'", content)
            current_gain = int(gain_match.group(1)) if gain_match else 52
            print(f"-> GRC mevcut kazanç ayarı baz alınıyor: Gain = {current_gain} dB")
        except Exception:
            pass

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
    log_file = open("rx_output.log", "w")
    proc = subprocess.Popen([python_exe, py_file], env=env, stdout=log_file, stderr=log_file)

    print("\n======================================================================")
    print(" [RX AKTIF] Havadan veri bekleniyor... İletim bittiğinde otomatik duracaktır.")
    print("======================================================================\n")

    start_time = time.time()
    
    # Boyut ve offset bilgileri (Başlıktan okunacak)
    len1, ext1, md5_1, offset1 = 0, "dat", "", 0
    len2, ext2, md5_2, offset2 = 0, "dat", "", 0
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
            if not header_parsed_1 and sz1 >= 77:
                meta = parse_header(RECEIVE_1_PATH)
                if meta:
                    len1, ext1, md5_1, offset1 = meta
                    header_parsed_1 = True
            
            if not header_parsed_2 and sz2 >= 77:
                meta = parse_header(RECEIVE_2_PATH)
                if meta:
                    len2, ext2, md5_2, offset2 = meta
                    header_parsed_2 = True

            # Eğer her iki başlık da çözümlendiyse, hedeflenen padded boyutu hesapla
            if header_parsed_1 and header_parsed_2 and padded_len == 0:
                n1 = (len1 + 74) // 75
                n2 = (len2 + 74) // 75
                padded_len = max(60 + 5 + n1, 60 + 5 + n2) * 77
                print(f"\n[INFO] Başlıklar Algılandı! Hedef İletim Boyutu: {padded_len} bayt")
                print(f"       User 1: {len1} B ({ext1}) offset={offset1} | User 2: {len2} B ({ext2}) offset={offset2}")

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

    # 6. Padding temizleme ve kurtarma (Strip & Reconstruct)
    if completed:
        print("\n-> Alınan dosyalardan dolgular ve başlıklar temizleniyor...")
        
        # User 1 Kurtarma
        res1 = recover_file_from_packets(RECEIVE_1_PATH)
        if res1:
            clean_1, ext1, md5_1, rx_pkts1, total_pkts1 = res1
            out1_name = f"recovered_user_1.{ext1}"
            with open(out1_name, "wb") as f:
                f.write(clean_1)
            
            if ext1.lower() == "png":
                fix_png_crc(out1_name)

            print(f"   [User 1] Kurtarıldı -> {out1_name} ({len(clean_1)} bayt) | Alınan Paket: {rx_pkts1}/{total_pkts1} (%{rx_pkts1/total_pkts1*100:.1f})")
            
            if md5_1:
                rx_md5_1 = get_md5(clean_1)
                if rx_md5_1 == md5_1:
                    print(f"   [User 1] MD5 EŞLEŞTİ! (MD5: {rx_md5_1})")
                else:
                    print(f"   [User 1] HATA: MD5 Uyuşmadı! Beklenen: {md5_1} | Alınan: {rx_md5_1}")
        else:
            print(f"   [User 1] HATA: Dosya kurtarılamadı (Başlık bulunamadı veya paket yok)!")

        # User 2 Kurtarma
        res2 = recover_file_from_packets(RECEIVE_2_PATH)
        if res2:
            clean_2, ext2, md5_2, rx_pkts2, total_pkts2 = res2
            out2_name = f"recovered_user_2.{ext2}"
            with open(out2_name, "wb") as f:
                f.write(clean_2)
            
            if ext2.lower() == "png":
                fix_png_crc(out2_name)

            print(f"   [User 2] Kurtarıldı -> {out2_name} ({len(clean_2)} bayt) | Alınan Paket: {rx_pkts2}/{total_pkts2} (%{rx_pkts2/total_pkts2*100:.1f})")

            if md5_2:
                rx_md5_2 = get_md5(clean_2)
                if rx_md5_2 == md5_2:
                    print(f"   [User 2] MD5 EŞLEŞTİ! (MD5: {rx_md5_2})")
                else:
                    print(f"   [User 2] HATA: MD5 Uyuşmadı! Beklenen: {md5_2} | Alınan: {rx_md5_2}")
        else:
            print(f"   [User 2] HATA: Dosya kurtarılamadı (Başlık bulunamadı veya paket yok)!")

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

    # RX Modu Argümanları
    parser.add_argument("--gain", type=int, default=None, help="Alıcı USRP kazancı (dB) [Mesafe benzetimi için]")

    args = parser.parse_args()

    if args.mode == "tx":
        run_tx_mode(args)
    elif args.mode == "rx":
        run_rx_mode(args)
