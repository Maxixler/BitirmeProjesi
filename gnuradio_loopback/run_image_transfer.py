# -*- coding: utf-8 -*-
"""
BPSK NOMA Image & Arbitrary File Transfer Manager
-------------------------------------------------
Bu script, farkli boyutlardaki iki dosyayi (orn: farkli PNG fotograflarini) BPSK NOMA
akisi uzerinden hatasiz gondermek icin kullanilir. 

GNU Radio'da kisa olan dosya bitince Adder (Toplama) blogunun durmasini ve uzun dosyanin
yarida kalmasini engellemek icin kisa dosyayi binary duzeyde doldurur (padding) ve alici
tarafta bu dolguyu temizleyerek (strip) orijinal dosyalari birebir kurtarir.
"""

import subprocess
import time
import os
import re
import hashlib

# Giris ve cikis resim yollari
IMAGE_1_TX = "transmit_1.png"
IMAGE_2_TX = "transmit_2.png"
IMAGE_1_RX = "bpsk_receive.png"
IMAGE_2_RX = "bpsk_receive_2.png"

# NOMA simulasyon dosyalari
TRANSMIT_1_PATH = "bpsk_transmit.txt"
TRANSMIT_2_PATH = "bpsk_transmit_2.txt"
RECEIVE_1_PATH = "bpsk_receive.txt"
RECEIVE_2_PATH = "bpsk_receive_2.txt"
NOMA_PY_PATH = "NOMA.py"
PYTHON_EXE = r"C:\Users\Armagan\radioconda\python.exe"

def kill_dangling_noma():
    """NOMA.py calistiran askidaki python sureclerini temizler ve dosya kilitlerini acar."""
    import os
    import json
    import subprocess
    import csv
    
    current_pid = os.getpid()
    
    # Metot 1: Modern PowerShell CIM Sorgusu (wmic yerine gecer, Windows 10/11'de 100% standarttir)
    try:
        # NOMA.py argumanini iceren python sureclerini PowerShell ile sorgula ve JSON formatina donustur
        cmd = 'powershell -NoProfile -Command "Get-CimInstance -ClassName Win32_Process -Filter \\"Name = \'python.exe\'\\" | Select-Object ProcessId, CommandLine | ConvertTo-Json -Compress"'
        out = subprocess.check_output(cmd, shell=True).decode('utf-8', errors='ignore').strip()
        
        if out:
            data = json.loads(out)
            # Tek bir surec gelirse sozluk olur, listeye saralim
            processes = data if isinstance(data, list) else [data]
            for proc in processes:
                pid = proc.get('ProcessId')
                cmdline = proc.get('CommandLine') or ""
                if pid and pid != current_pid and "NOMA.py" in cmdline:
                    print(f"-> Askidaki NOMA.py sureci sonlandiriliyor (PID: {pid})...")
                    subprocess.run(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    # Metot 2: tasklist ile pencere basligi veya status kontrolu (Fallback)
    try:
        cmd = 'tasklist /FI "IMAGENAME eq python.exe" /FO CSV /V'
        out = subprocess.check_output(cmd, shell=True).decode('utf-8', errors='ignore')
        reader = csv.reader(out.strip().splitlines())
        for row in reader:
            if len(row) >= 9:
                pid_str = row[1]
                window_title = row[8]
                if "NOMA" in window_title or "NOMA" in row[6]:
                    pid = int(pid_str)
                    if pid != current_pid:
                        print(f"-> Askidaki NOMA.py sureci sonlandiriliyor (PID: {pid})...")
                        subprocess.run(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def get_md5(data):
    """Verinin MD5 hash degerini hesaplar."""
    return hashlib.md5(data).hexdigest()

def modify_noma_throttle(rate=500000):
    """NOMA.py icerisindeki throttle hizini regex ile dinamik olarak gunceller."""
    print(f"-> NOMA.py throttle hizi {rate} sembol/sn olarak ayarlaniyor...")
    if not os.path.exists(NOMA_PY_PATH):
        print(f"[HATA] {NOMA_PY_PATH} bulunamadi!")
        return

    with open(NOMA_PY_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Throttle hizlarini guncelle
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
    print("-> Throttle hizi NOMA.py icerisinde guncellendi.")

def run_simulation(len1, len2, padded_len, duration=150):
    """Simulasyonu baslatir ve alinan dosya boyutlarini anlik olarak takip eder."""
    import shutil
    
    # Askidaki eski NOMA sureclerini sonlandir ve kilitleri ac
    kill_dangling_noma()
    
    # Python modül önbelleğini (pycache) temizle ki eski kodlar yuklenmesin
    pycache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "__pycache__")
    if os.path.exists(pycache_path):
        try:
            shutil.rmtree(pycache_path)
            print("-> Python cache klasoru temizlendi.")
        except Exception:
            pass

    print("-> NOMA Simulasyonu baslatiliyor...")
    
    # Eski cikti dosyalarini temizle ve kilit varsa uyar
    for p in [RECEIVE_1_PATH, RECEIVE_2_PATH]:
        if os.path.exists(p):
            try:
                os.remove(p)
                print(f"-> Eski cikti dosyasi temizlendi: {p}")
            except Exception as e:
                print(f"[UYARI] {p} temizlenemedi! Dosya baska bir surec tarafindan kilitli olabilir. Hata: {e}")
                print("Lutfen acik olan GNU Radio Companion (GRC) uygulamasini veya arka plandaki Python sureclerini kapatin!")

    # PYTHONDONTWRITEBYTECODE=1 ile NOMA.py'nin eski cache yuklemesini 100% engelliyoruz
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.Popen([PYTHON_EXE, NOMA_PY_PATH], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    start_time = time.time()
    completed = False
    
    try:
        while time.time() - start_time < duration:
            # Alinan dosya boyutlarini kontrol et
            sz1 = os.path.getsize(RECEIVE_1_PATH) if os.path.exists(RECEIVE_1_PATH) else 0
            sz2 = os.path.getsize(RECEIVE_2_PATH) if os.path.exists(RECEIVE_2_PATH) else 0
            
            elapsed = int(time.time() - start_time)
            pct1 = min(100.0, (sz1 / padded_len) * 100)
            pct2 = min(100.0, (sz2 / padded_len) * 100)
            
            # Konsolda anlik premium durum bilgisi (carriage return ile ayni satira yazma)
            print(f"   [Sure: {elapsed}s/{duration}s] User 1: {sz1}/{padded_len} B ({pct1:.1f}%) | User 2: {sz2}/{padded_len} B ({pct2:.1f}%)", end="\r", flush=True)
            
            # Eger her iki dosya da en az orijinal dosya boyutlarina ulastiysa erken cik
            if sz1 >= len1 and sz2 >= len2:
                print(f"\n[OK] Her iki dosya da tamamen alindi! (User 1: {sz1}/{len1} B, User 2: {sz2}/{len2} B)")
                print("-> Verilerin diske tam yazilmasi ve senkronizasyon icin 2 saniye bekleniyor...")
                time.sleep(2.0)
                completed = True
                break
                
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\n-> Kullanici tarafindan simulasyon kesildi.")
    
    if not completed:
        print(f"\n[UYARI] Sure siniri ({duration} saniye) doldu veya veri akisi tamamlanamadi.")
    
    # Simulasyonu guvenli sekilde sonlandir
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()
def compile_grc():
    """NOMA.grc dosyasini grcc kullanarak NOMA.py'ye derler."""
    grcc_path = r"C:\Users\Armagan\radioconda\Scripts\grcc.exe"
    grc_path = r"NOMA.grc"
    print("-> NOMA.grc dosya yapisi derleniyor...")
    if not os.path.exists(grcc_path):
        grcc_path = "grcc"
    try:
        res = subprocess.run([grcc_path, grc_path], capture_output=True, text=True)
        if res.returncode == 0:
            print("-> Derleme basarili ve guncel NOMA.py olusturuldu.")
            return True
        else:
            print(f"[UYARI] Derleme hatasi! STDOUT: {res.stdout} | STDERR: {res.stderr}")
    except Exception as e:
        print(f"[UYARI] grcc calistirilamadi: {e}")
    return False

def main():
    # 0. GRC dosyasini otomatik derle (GUI kilitlenmelerini ve dosya uyumsuzluklarini 100% onler)
    compile_grc()
    print("======================================================================")
    print("             BPSK NOMA FARKLI BOYUTTA DOSYA GONDERIM ARACI            ")
    print("======================================================================")

    # 1. Giris dosyalarinin kontrolu
    if not os.path.exists(IMAGE_1_TX) or not os.path.exists(IMAGE_2_TX):
        print(f"[HATA] {IMAGE_1_TX} veya {IMAGE_2_TX} bulunamadi!")
        return

    # Orijinal verileri oku
    with open(IMAGE_1_TX, "rb") as f:
        data1 = f.read()
    with open(IMAGE_2_TX, "rb") as f:
        data2 = f.read()

    len1 = len(data1)
    len2 = len(data2)
    max_len = max(len1, len2)

    # MD5 hashlerini hesapla (dogrulama icin)
    md5_tx1 = get_md5(data1)
    md5_tx2 = get_md5(data2)

    print("-> Orijinal Dosya Boyutlari ve MD5 Hashleri:")
    print(f"   [User 1] {IMAGE_1_TX}: {len1} bayt (MD5: {md5_tx1})")
    print(f"   [User 2] {IMAGE_2_TX}: {len2} bayt (MD5: {md5_tx2})")

    # 2. Kısa dosyayı sıfırlarla doldur (Padding)
    # GNU Radio stream_to_tagged_stream blogu 77 byte paket boyutlarinda calisir.
    # Son paketin yarida kalmasini veya kesilmesini onlemek icin, dolgu boyutunu 77'nin tam katina tamamliyoruz.
    payload_size = 77
    padded_len = ((max_len + payload_size - 1) // payload_size) * payload_size

    print(f"-> Dolgu boyutu hesaplandi: {padded_len} bayt (77'nin kati, orijinal maks: {max_len})")

    padded_data1 = data1 + b'\x00' * (padded_len - len1)
    padded_data2 = data2 + b'\x00' * (padded_len - len2)

    # NOMA aktarim dosyalarini kaydet
    with open(TRANSMIT_1_PATH, "wb") as f:
        f.write(padded_data1)
    with open(TRANSMIT_2_PATH, "wb") as f:
        f.write(padded_data2)

    print(f"-> Aktarim dosyalari hazirlandi: {len(padded_data1)} bayt.")

    # Eski cikti resimlerini sil
    for rx_img in [IMAGE_1_RX, IMAGE_2_RX]:
        if os.path.exists(rx_img):
            try:
                os.remove(rx_img)
            except Exception:
                pass

    # 3. Throttle hizini 500k (500000) olarak ayarla (Dinamik, kararli ve veri dostu)
    modify_noma_throttle(rate=500000)

    # Dinamik olarak maksimum sureyi belirle
    # 500k hizda saniyede yaklasik 2.5 KB veri gonderilir.
    # Emniyet payi ve baslangic senkronizasyon suresi ekleyerek hesapliyoruz.
    expected_throughput = (500000 / 15480) * 77  # ~2487 bayt/sn
    duration = max(180, int((padded_len / expected_throughput) * 2.5))
    print(f"-> Dinamik calisma suresi belirlendi: {duration} saniye.")

    try:
        # 4. Simulasyonu calistir
        run_simulation(len1, len2, padded_len, duration=duration)
    finally:
        # 5. Her durumda throttle hizini varsayilan 8000 degerine geri al
        modify_noma_throttle(rate=8000)

    # 6. Alinan dosyalari oku ve dolguyu temizle (Strip Padding)
    print("\n-> Alici tarafta dosyalar kurtariliyor...")
    
    rx1_data = b""
    if os.path.exists(RECEIVE_1_PATH):
        with open(RECEIVE_1_PATH, "rb") as f:
            rx1_data = f.read()

    rx2_data = b""
    if os.path.exists(RECEIVE_2_PATH):
        with open(RECEIVE_2_PATH, "rb") as f:
            rx2_data = f.read()

    print(f"-> Alinan Ham Akis Boyutlari:")
    print(f"   [User 1] {RECEIVE_1_PATH}: {len(rx1_data)} bayt")
    print(f"   [User 2] {RECEIVE_2_PATH}: {len(rx2_data)} bayt")

    # Dolguyu temizleyerek orijinal resmi kurtar ve MD5 kontrol et
    success_1 = False
    success_2 = False

    if len(rx1_data) >= len1:
        clean_rx1 = rx1_data[:len1]
        md5_rx1 = get_md5(clean_rx1)
        
        with open(IMAGE_1_RX, "wb") as f:
            f.write(clean_rx1)
            
        if md5_rx1 == md5_tx1:
            print(f"[OK] [User 1] Resim BASARIYLA kurtarildi! {IMAGE_1_RX} ({len(clean_rx1)} B) - MD5 ESLESTI")
            success_1 = True
        else:
            print(f"[HATA] [User 1] Resim kurtarildi ama veri bozulmus! MD5 uyusmadi. (TX: {md5_tx1} | RX: {md5_rx1})")
    else:
        print(f"[HATA] [User 1] Yetersiz veri alindi ({len(rx1_data)}/{len1} bayt).")

    if len(rx2_data) >= len2:
        clean_rx2 = rx2_data[:len2]
        md5_rx2 = get_md5(clean_rx2)
        
        with open(IMAGE_2_RX, "wb") as f:
            f.write(clean_rx2)
            
        if md5_rx2 == md5_tx2:
            print(f"[OK] [User 2] Resim BASARIYLA kurtarildi! {IMAGE_2_RX} ({len(clean_rx2)} B) - MD5 ESLESTI")
            success_2 = True
        else:
            print(f"[HATA] [User 2] Resim kurtarildi ama veri bozulmus! MD5 uyusmadi. (TX: {md5_tx2} | RX: {md5_rx2})")
    else:
        print(f"[HATA] [User 2] Yetersiz veri alindi ({len(rx2_data)}/{len2} bayt).")

    print("======================================================================")
    if success_1 and success_2:
        print("          TEBRIKLER! BPSK NOMA ILE RESIM TRANSFERI TAMAMEN BASARILI   ")
    else:
        print("          TRANSFER BASARISIZ! LUTFEN LOGLARI KONTROL EDIN.            ")
    print("======================================================================")

if __name__ == "__main__":
    main()
