# 🛰️ USRP E310 & Host SDR Donanımsal NOMA OTA İletişim Rehberi

Bu doküman, Yazılım Tabanlı Radyo (SDR) donanımı olan **USRP E310** (veya Gigabit Ethernet tabanlı USRP'ler) ve iki adet Linux host bilgisayar kullanarak havadan (Over-the-Air - OTA) BPSK NOMA dosya ve resim aktarım projesinin gereksinimlerini, kurulumunu, konfigürasyonunu ve adım adım çalıştırma süreçlerini açıklamaktadır.

---

## 1. Donanım ve Yazılım Gereksinimleri

Projenin fiziksel RF donanımı üzerinde sağlıklı çalışabilmesi için aşağıdaki bileşenlerin hazır bulunması gerekmektedir:

### A. Donanım Gereksinimleri
*   **SDR Cihazları:** 2 adet USRP E310 (Embedded Serisi, AD9361 RF ön yüzlü) veya Gigabit Ethernet tabanlı USRP'ler (örn. USRP 2922).
*   **Antenler:** 868 MHz ISM bandına uyumlu 2 adet MRTK-Q7027I28 LTE/4G (SMA/Erkek, 7dBi) omni-directional RF anten. (Alıcı ve verici cihazların **TX/RX** portuna bağlanır).
*   **Host Bilgisayarlar:** Gigabit Ethernet portuna sahip, yüksek işlem gücüne sahip 2 adet PC.
*   **Kablolar:** SDR ve Host PC arası doğrudan bağlantı için Gigabit Ethernet kabloları ve seri konsol erişimi için micro-USB kablosu.


### B. Yazılım Gereksinimleri
*   **İşletim Sistemleri:** 
    *   Host Bilgisayarlar: Linux (tercihen Arch Linux veya Ubuntu).
    *   USRP E310: Cihaz üzerinde yerleşik koşan gömülü Linux.
*   **SDR Sürücü Kütüphaneleri:** UHD (USRP Hardware Driver) v4.10.x ve üzeri.
*   **Sinyal İşleme:** GNU Radio v3.10.x ve üzeri.
*   **Python Ortamı:** Radioconda veya Python 3.10+ kurulu ortam.
*   **Python Bağımlılıkları:** `numpy`, `scipy` (sinyal hizalama hesaplamaları için), `PyQt5` (grafiksel arayüz desteği için).

### C. Kullanılan Donanım Listesi
Laboratuvar testlerinde aktif olarak kullanılan ve sistemi doğruladığımız fiziksel donanım bileşenleri:
*   **SDR Cihazları:** 2 adet USRP E310 SG3 (Embedded Series, XC7Z020 FPGA & AD9361 RFIC).
*   **Antenler:** 2 adet MRTK-Q7027I28 (698-960/1710-2700 MHz, SMA/Erkek, 7dBi kazançlı omni-directional RF anten).
*   **Bağlantı Kabloları:** Cat6 S/FTP shielded RJ-45 Gigabit Ethernet kablosu ve CP2102 tabanlı Micro-USB konsol kablosu.
*   **Host Bilgisayarlar:** Gigabit Ethernet arayüzüne (eno1/enp3s0) sahip 2 adet Linux işletim sistemli PC.

---

## 2. Kurulum ve Konfigürasyon

Fiziksel bağlantıların yapılması, IP adreslerinin tanımlanması ve gecikme/paket kaybını (underflow/overflow) önleyici ağ ayarlarının yapılması adımlarıdır.

### A. Fiziksel Bağlantıların Yapılması
1.  Verici ve alıcı USRP cihazlarının antenlerini **TX/RX** RF konnektörüne vidalayın.
2.  Her bir USRP cihazını Gigabit Ethernet kablosuyla ilgili Host bilgisayarın ethernet portuna doğrudan bağlayın.
3.  E310 üzerinde seri terminal erişimi için micro-USB kablosunu Host bilgisayara bağlayın.

### B. Ağ Yapılandırması ve Statik IP Atama (eno1 / eth0)
Paket kayıplarını engellemek için host bilgisayarlar ile USRP'ler arasında statik IP tanımlamaları yapılmalıdır.

#### 1. Ana Bilgisayar (Host PC - Örn: eno1 arayüzü) IP Ataması:
```bash
# Ethernet kartının adını kontrol edin (eno1, enp3s0 vb.)
ip link show

# Host PC'ye statik IP tanımlama
sudo ip addr add 192.168.10.1/24 dev eno1

# Arayüzü aktif etme
sudo ip link set eno1 up
```

#### 2. USRP Cihazı (Örn: eth0 arayüzü) IP Ataması:
*   USRP E310 cihazlarının varsayılan gömülü IP adresi genellikle **`192.168.10.2`**'dir.
*   Eğer cihaza el ile IP tanımlanması gerekiyorsa, öncelikle Host bilgisayardan USB-seri konsol bağlantısı başlatılır, ardından açılan USRP terminalinde IP tanımlama komutları çalıştırılır:
    ```bash
    # 1. Host bilgisayardan seri konsol ile USRP'ye bağlanın
    sudo screen /dev/ttyUSB0 115200

    # 2. Açılan USRP terminali içerisinde ethernet arayüzünü yapılandırın
    ip addr add 192.168.10.2/24 dev eth0
    ip link set eth0 up
    ```

> [!IMPORTANT]
> Host IP adreslerinin çakışmasını önlemek için TX (Verici) grubu ile RX (Alıcı) grubu tamamen izole edilmeli, bilgisayarlar doğrudan kendi USRP'lerine bağlanmalıdır.

#### 3. Bağlantı Doğrulama (Ping Testi):
Host bilgisayar terminalinden USRP'ye ping atılarak fiziksel hat test edilir:
```bash
ping 192.168.10.2 -c 4
# Paket kaybı %0 ve gecikme <1ms olmalıdır.
```

### C. Underflow ('U') ve Overflow ('O') Hataları İçin Optimizasyonlar
USRP donanım tamponlarındaki paket kaçırma ve veri yetiştirememe hatalarını çözmek için Host bilgisayarda şu ayarlar yapılmalıdır:

#### 1. İşletim Sistemi Ağ Soket Limitlerini Artırma (sysctl):
Underflow hatalarını engellemek amacıyla ağ soketi yazma ve okuma maksimum tampon sınırları **25 MB** değerine yükseltilmelidir:
```bash
# Soket limitlerini 25 MB'a çıkarma
sudo sysctl -w net.core.wmem_max=25000000
sudo sysctl -w net.core.rmem_max=25000000
```
*Bu ayarı kalıcı yapmak için `/etc/sysctl.conf` dosyasının en altına şu iki satır eklenmelidir:*
```ini
net.core.wmem_max=25000000
net.core.rmem_max=25000000
```

#### 2. Ağ Kartı Donanımsal Halka Arabellek (Ring Buffer) Artırımı:
Ağ kartı seviyesinde taşma (overflow) olmaması için ethernet kartını Full Duplex Gigabit hızına sabitleyin ve ring buffer boyutlarını en üst düzeye (4096) çekin:
```bash
# Arayüzü 1000 Mbps Full Duplex yapmaya zorlama
sudo ethtool -s eno1 autoneg on speed 1000 duplex full

# Donanım arabellek (Rx/Tx) değerlerini 4096'ya yükseltme
sudo ethtool -G eno1 rx 4096 tx 4096
```

---

## 3. Kullanım ve Test

Dosya aktarımına geçmeden önce cihaz erişilebilirliğinin ve RF codec katmanının test edilmesi adımıdır.

### A. Seri Konsol ve SSH ile Bağlantı Kurulumu
1.  **Seri Konsol Bağlantısı:**
    USB üzerinden konsol bağlantısını başlatın:
    ```bash
    sudo screen /dev/ttyUSB0 115200
    ```
2.  **SSH Bağlantısı:**
    Doğrudan ethernet üzerinden USRP'ye SSH atın:
    ```bash
    ssh root@192.168.10.2
    ```
3.  **Terminal Uyumluluğu ve UHD Sorgulama:**
    USRP terminalinde nano editörü gibi araçlarda sorun yaşamamak için `TERM` değişkenini tanımlayın ve UHD'nin cihazı gördüğünü doğrulayın:
    ```bash
    export TERM=xterm
    uhd_find_devices
    ```
    *Beklenen Çıktı:* `product: e310_sg3`

### B. Sinyal Testi (Gömülü Mod)
USRP E310'un kendi RF donanımını (codec) test etmek için yerleşik python testi koşturulabilir:
```bash
python3 main.py
```
*Başarı Göstergesi:* `[INFO] ... Performing CODEC loopback test ... passed`

---

## 4. Linux Host Bilgisayarlar ve 2 USRP ile Donanım Testlerini Çalıştırma

Fiziksel USRP cihazları ve Host bilgisayarlar üzerinde BPSK NOMA dosya/resim transferini otomatikleştiren [run_host_transfer.py](file:///c:/Users/Armagan/Documents/GitHub/BitirmeProjesi/usrp/run_host_transfer.py) betiğinin çalışma mekanizmaları ve çalıştırılma adımları aşağıdadır.

### A. Parametre ve Kazanç Kalibrasyonu
*   **Güç Katsayıları:** NOMA süperpozisyonu için Near User (User 1) sinyali $a_1 = 0.894$ (gücün $\%80$'i), Far User (User 2) sinyali ise $a_2 = 0.447$ (gücün $\%20$'si) katsayısıyla toplanır.
*   **Kazanç-Genlik İlişkisi:** Alıcı RF kazancı arttıkça sinyalin genliği artar. Sistemimizde **52 dB** alıcı kazancına karşılık gelen referans `near_user_amplitude` değeri **0.27**'dir. Farklı kazanç değerleri için genlik şu formülle otomatik ölçeklenir:
    $$\text{Amplitude} = 0.27 \times 10^{\frac{\text{Gain} - 52}{20}}$$

### B. Paket Çerçeve Yapısı
1.  **Eğitim Ön Eki (60 Paket):** RRC filtre, Symbol Sync ve Costas Loop'un kilitlenebilmesi için gönderilen 60 adet `TRAIN:xxxxx...` eğitim paketi.
2.  **Metadata Başlığı (Seq = 0, 5 Paket):** Dosya boyutu, uzantısı ve MD5 hash değerini içeren (`boyut:uzantı:md5`), alıcının otomatik algılamasını sağlayan 5 adet yedekli paket.
3.  **Veri Paketleri (Seq >= 1):** 2 bayt Sequence Number + 75 bayt payload = 77 baytlık paket dizileri.
4.  **Kuyruk Dolgusu (60 Paket):** USRP donanım tamponundaki paketlerin yarıda kesilmesini engellemek için eklenen `Seq = 65535` (`\xff\xff`) boş kuyruk paketleri.

### C. Çalıştırma Adımları

#### 1. Adım: Alıcı Bilgisayarın (Host RX) Dinlemeye Alınması
Alıcı tarafta hiçbir dosya boyutu veya uzantı bilgisi girmenize gerek yoktur. Sadece kazanç değerini girerek alıcıyı başlatın:
```bash
python3 run_host_transfer.py --mode rx --gain 55
```
*   *Çalışma Mantığı:* Script `RX_host.grc` dosyasını derler, `RX_host.py` akış grafiğini çalıştırır, ilk 16 baytlık başlığı aldığı an ilerleme çubuğunu ekranda çizer. Veri akışı kesildikten (5 saniye sessizlik - Idle Timeout) sonra otomatik olarak kapanır.

#### 2. Adım: Verici Bilgisayardan (Host TX) Yayının Başlatılması
Verici bilgisayarda iletilmek istenen herhangi iki dosyayı belirterek yayını başlatın:
```bash
python3 run_host_transfer.py --mode tx --file1 transmit_1.png --file2 transmit_2.txt
```
*   *Çalışma Mantığı:* Script `TX_host.grc` şemasını derler, dosyalara otomatik sıra numarası, metadata başlığı, eğitim ön eki ve kuyruk dolgularını ekleyip yayını başlatır.

#### 3. Adım: Dosya Kurtarma ve PNG CRC Onarımı
*   **Dolgu Kırpma (Stripping):** Alınan ham verilerden dolgu sıfırları başlıkta okunan orijinal boyutlara göre temizlenir.
*   **PNG CRC Düzeltme (PNG Auto-Fix):** Eğer aktarılan dosya bir PNG resmi ise ve havadan iletim sırasında düşen paketler varsa, resmin açılabilmesi için PNG chunk'larının CRC32 değerleri script tarafından otomatik olarak yeniden hesaplanıp düzeltilir.
*   **Doğrulama:** `recovered_user_1.png` ve `recovered_user_2.txt` dosyaları MD5 hash eşleşmesi kontrol edilerek diske yazılır.

---

## 5. Sorun Giderme (Troubleshooting)

| Hata / Sorun | Olası Neden | Çözüm Yolu |
| :--- | :--- | :--- |
| **SSH Terminal Hataları** | SSH bağlantısında terminal uyumsuzluğu. | SSH terminalinde `export TERM=xterm` komutunu çalıştırın. |
| **Veri Kaybı / Terminalde 'O' (Overflow)** | CPU veya ethernet kartı gelen örnek hızına yetişemiyor. | Ethernet kartı ayarlarını `ethtool` ile optimize edin veya örnekleme hızını (`rate`) düşürün. |
| **Terminalde 'U' (Underflow) Basılması** | Soket arabellek limiti yetersiz. | `sysctl` soket arabellek boyutlarını 25 MB'a yükseltme adımlarını uygulayın. |
| **User 2 Çıkışının 0 Bayt (Boş) Kalması** | Güçlü olan User 1 sinyali çözülemiyor ve SIC adımı kilitleniyor. | Alıcı kazancını (`--gain`) adım adım değiştirerek optimize edin. Antenlerin yönünü ve mesafesini kontrol edin. |
