# ⚡ BPSK NOMA Simülasyonu, SIC Aligner ve Akademik Test Rehberi

Bu doküman, Yazılım Tabanlı Radyo (SDR) projesinin simülasyon katmanı olan **BPSK NOMA + LDPC + SIC Loopback (Modül 2)** yapısının gereksinimlerini, kurulumunu, konfigürasyonunu ve otomatik akademik sweep testlerinin çalıştırılması süreçlerini açıklamaktadır.

---

## 1. Donanım ve Yazılım Gereksinimleri

Simülasyon modülü tamamen yazılımsal ve bilgisayar tabanlı (loopback) çalıştığı için harici bir SDR donanımına ihtiyaç duymaz.

### A. Donanım Gereksinimleri
*   **İşlemci (CPU):** Intel Core i5/i7 veya AMD Ryzen 5/7 ve üzeri (LDPC matris çözme ve SIC arama penceresi işlemleri yoğun CPU gücü gerektirir).
*   **Bellek (RAM):** En az 8 GB (tercihen 16 GB).
*   **Depolama:** Test grafiklerinin ve veri çıktılarının yazılabilmesi için en az 1 GB boş disk alanı.

### B. Yazılım Gereksinimleri
*   **İşletim Sistemi:** Windows 10/11 veya popüler Linux dağıtımları (Ubuntu, Arch Linux).
*   **Yazılım Platformu:** GNU Radio v3.10.x & Radioconda (Python v3.10+ ve uyumlu paketler).
*   **Python Bağımlılıkları:** `numpy`, `scipy` (kanal modelleme ve SIC hizalama işlemleri için), `PyQt5` (GNU Radio QT GUI kütüphaneleri için), `matplotlib` (test grafiklerini çizdirmek için).

### C. Kullanılan Donanım Listesi (Şimdiki Sistem)
Simülasyon testlerinin koşturulduğu ve süre performanslarının ölçüldüğü referans sistem:
*   **İşlemci:** Intel/AMD x86_64 Çok Çekirdekli İşlemci.
*   **Çalışma Ortamı:** Radioconda Python 3.10/3.12 Çekirdeği.
*   **Bellek:** 16 GB RAM.

---

## 2. Kurulum ve Konfigürasyon

Simülasyon akış şemasının derlenmesi ve gerekli matris kütüphanelerinin sisteme tanıtılması adımlarıdır.

### A. GRC Dosyasının Derlenmesi (NOMA.py Oluşturma)
GNU Radio akış şeması `NOMA.grc` üzerinde yapılan değişikliklerin çalıştırılabilir hale getirilmesi için Host PC terminalinde `grcc` (GNU Radio Companion Compiler) çalıştırılır:
```bash
# Windows (Radioconda terminali veya normal terminalde):
C:\Users\Armagan\radioconda\Scripts\grcc.exe NOMA.grc

# Linux ortamında:
grcc NOMA.grc
```
*Bu komut, güncel Python kodu olan `NOMA.py` dosyasını oluşturur.*

### B. Parite Kontrol Matrisi (LDPC ALIST) Tanımlaması
*   Simülasyonda kanal kodlaması için IEEE 802.11n standardına uyumlu **`n_1296_k_0648_ieee.alist`** matrisi kullanılır.
*   Bu dosyanın simülasyon klasöründe (`gnuradio_loopback/`) yer aldığından emin olunmalıdır. LDPC Encoder ve Decoder blokları bu dosyayı referans alarak çalışır.

---

## 3. Kullanım ve Test

Simülasyon bileşenlerinin entegrasyon doğruluğunun test edilmesi adımıdır.

### A. Gömülü Python SIC Aligner Entegrasyonu
*   Girişim çıkarma işleminin sıfır sızıntı ile çalışabilmesi için alıcıda [gnuradio_loopback/NOMA_epy_block_1.py](file:///c:/Users/Armagan/Documents/GitHub/BitirmeProjesi/gnuradio_loopback/NOMA_epy_block_1.py) (Decoupled NOMA SIC Aligner) bloğu gömülüdür.
*   Bu blok, GNU Radio zamanlayıcı kilitlenmesini (scheduler deadlock) önlemek amacıyla `gr.basic_block` olarak tasarlanmış olup, asenkron decoupled dahili tamponlar yönetir.
*   Preamble korelasyon tag'lerinin kaymasını sıfırlamak için koda **`shift = -16`** telafi sabiti entegre edilmiştir.

### B. Akış Grafiğinin GUI ile Manuel Test Edilmesi
Sistemi görsel olarak test etmek için python dosyası doğrudan çalıştırılabilir:
```bash
python NOMA.py
```
*Bu komut, QT GUI zaman alanını, Costas Loop faz kilitlenmesini ve constellation çakışmalarını canlı gösteren simülasyon ekranını açar.*

---

## 4. Simülasyon Testlerini Çalıştırma (Akademik Sweep Testleri)

Simülasyon üzerinde dinamik dolgulamalı dosya transferleri ve tezinizde kullanabileceğiniz akademik performans sweep testleri gerçekleştirilir.

### A. Uçtan Uca Simülasyon Resim Transferi (run_image_transfer.py)
Gönderilecek iki farklı boyutlu PNG resmini (Örn: `transmit_1.png` ve `transmit_2.png`) NOMA loopback kanalı üzerinden gönderip alıcıda hatasız kurtarmak için wrapper betiği çalıştırılır:
```bash
python run_image_transfer.py
```
*   *Çalışma Mantığı:* Kısa olan dosyayı 77 baytın katına sıfır dolgular (padding). `NOMA.py` akış grafiğini arka planda subprocess olarak çalıştırır. İletim tamamlandıktan (5 saniye sessizlik) sonra akışı otomatik kapatır (Idle Timeout). Dolguları kırpar (stripping), PNG CRC bloklarını otomatik onarır ve dosyaların MD5 hash doğrulamalarını gerçekleştirir.

```

---

## 5. Sorun Giderme (Troubleshooting)

| Hata / Sorun | Olası Neden | Çözüm Yolu |
| :--- | :--- | :--- |
| **Simülasyonun Başlatılamaması (Process Lock)** | Arka planda askıda kalan eski `NOMA.py` süreçleri dosya kilitlemesi yapıyor. | `run_image_transfer.py` askıdaki süreçleri otomatik temizler. Manuel olarak terminalden `taskkill /F /IM python.exe` çalıştırın. |
| **User 2 Çıkışında User 1 Verisi Görünmesi (Sızıntı)** | Zaman hizalamasında 1 sembollük uyuşmazlık (Shift hatası). | SIC Aligner koda gömülü `shift = -16` değerini kontrol edin. `test_correlation.py` ile korelasyon peak hizalamasını analiz edin. |
| **Simülasyonun CPU %100 Tüketip Kilitlenmesi** | `gr.sync_block` kullanımı nedeniyle oluşan zamanlayıcı kilitlenmesi (Scheduler Deadlock). | SIC Aligner bloğunun `gr.basic_block` olarak ayarlandığından ve decoupled tamponları kullandığından emin olun. |
| **PNG Resimlerinin Açılmaması (Corrupt Hatası)** | İletimdeki paket düşüşleri nedeniyle PNG chunk CRC bloklarının bozulması. | `run_image_transfer.py` içerisindeki `fix_png_crc` fonksiyonunun çalıştığından emin olun. |
