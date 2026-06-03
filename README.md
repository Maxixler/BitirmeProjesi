# USRP E310 & LoRaWAN Sinyal Analizi ve BPSK NOMA Haberleşme Projesi

Bu proje, iki ana modülden oluşan kapsamlı bir kablosuz haberleşme ve sinyal işleme çalışmasıdır:
1. **Modül 1 (Gerçek Zamanlı Sinyal Analizi):** USRP E310 Yazılım Tabanlı Radyo (SDR) cihazı kullanılarak gerçek dünya kablosuz sinyallerinin, özellikle **868 MHz LoRaWAN frekans bandının** örneklenmesi ve analizi.
2. **Modül 2 (BPSK NOMA Simülasyonu):** Non-Orthogonal Multiple Access (NOMA - Dikgen Olmayan Çoklu Erişim) teknolojisinin BPSK modülasyonu, LDPC Kanal Kodlaması ve Ardışık Girişim Giderme (SIC - Successive Interference Cancellation) algoritmalarıyla farklı dosya boyutlarında uçtan uca simüle edilmesi.

---

## 🛰️ Modül 1: USRP E310 & LoRaWAN Gerçek Zamanlı Sinyal Analizi

### Proje Hedefi
Temel amaç, bir LoRa modülü tarafından üretilen 868 MHz kablosuz sinyallerin USRP E310 kullanılarak yakalanması, örneklenmesi ve işlenmesidir.

*   **Hedef Sinyal:** 868 MHz (LoRaWAN)
*   **Sinyal Kaynağı:** LLCC68 Ebyte E220-900T22D (868MHz-915MHz, 22dBm)
*   **Alıcı:** USRP E310 (Embedded Serisi)

### Donanım ve Yazılım Gereksinimleri

#### Donanım
*   **SDR:** USRP E310 (Embedded Serisi)
*   **Ana Bilgisayar (Host):** Linux yüklü PC
*   **LoRa Modülü:** Ebyte E220-900T22D
*   **Bağlantı:** Ethernet (Doğrudan bağlantı), USB-Seri (Konsol erişimi)

#### Yazılım
*   **İşletim Sistemi (Host):** Arch Linux
*   **SDR Sürücüleri:** UHD (USRP Hardware Driver)
*   **Sinyal İşleme:** GNU Radio / Python (`sineWaveGRC.py`)

### Kurulum ve Konfigürasyon

#### 1. Fiziksel Bağlantılar
*   USRP E310'u **Ethernet** üzerinden Ana Bilgisayara bağlayın.
*   Konsol erişimi için USRP E310'u **USB-Seri** üzerinden Ana Bilgisayara bağlayın.

#### 2. Ağ Konfigürasyonu
Yüksek hızlı veri akışı sağlamak ve paket kaybını önlemek için statik IP yapılandırması ve Gigabit Ethernet ayarları gereklidir.

**Seri Konsol Erişimi:**
```bash
sudo screen /dev/ttyUSB0 115200
```

**IP Konfigürasyonu:**
*   **USRP E310 (eth0):**
    ```bash
    ip addr add 192.168.10.2/24 dev eth0
    ```
*   **Ana Bilgisayar (eno1):**
    ```bash
    ip addr add 192.168.10.1/24 dev eno1
    ```

**Ethernet Performans Ayarı (Host):**
Veri taşmasını/kaybını (overflow/underrun) önlemek için ağ arayüzünü Gigabit Full Duplex moduna zorlayın:
```bash
sudo ethtool -s eno1 autoneg on speed 1000 duplex full
```

### Kullanım ve Test

#### 1. Bağlantı Kontrolü
SSH üzerinden bağlantıyı doğrulayın. Terminal sorunları yaşarsanız (örneğin `nano` ile), `TERM` değişkenini ayarlayın.

```bash
# USRP'ye SSH ile bağlanın
ssh root@192.168.10.2

# Terminal uyumluluk hatası çözümü (gerekirse)
export TERM=xterm
```

UHD sürücüsünün cihazı tanıdığını doğrulayın:
```bash
uhd_find_devices
# Beklenen Çıktı: Product: e310_sg3
```

#### 2. Sinyal Testi (Gömülü Mod)
RF ön yüzünü test etmek için Python betiğini doğrudan USRP E310 üzerinde çalıştırın.

```bash
python3 main.py
```
*   **Başarı Göstergesi:** `[INFO] ... Performing CODEC loopback test ... passed`

#### 3. Akış (Streaming) Testi
*   Akışı almak için Ana Bilgisayarda GNU Radio kullanın (ZMQ SUB Source üzerinden).
*   Spektrum Analizöründe (QT GUI Frequency Sink) gürültü tabanını veya sinyali gözlemleyin.

---

## ⚡ Modül 2: BPSK NOMA Farklı Boyutlu Dosya ve Resim İletim Simülasyonu

Bu modül, güce dayalı bölmeli (Power-Domain) NOMA prensibine dayanır. İki kullanıcının verisi aynı anda ve aynı frekansta, ancak farklı güç seviyelerinde havaya gönderilir. Farklı boyutlardaki iki dosyanın iletimi sırasında yaşanan akış kesintilerini (block starvation/deadlock) önleyen **dinamik dolgulamalı (padding)** paket yapısı ve alıcı tarafta çalışan **otomatik zaman hizalamalı ve faz kestirimli SIC algoritması** simüle edilmektedir.

### 🛰️ Sistem Mimarisi ve Çalışma Prensibi

```mermaid
graph TD
    subgraph Verici (Transmitter)
        F1[User 1 Dosyası] --> P1[Dinamik Dolgu & CRC32]
        F2[User 2 Dosyası] --> P2[Dinamik Dolgu & CRC32]
        P1 --> L1[LDPC Kodlayıcı 1/2]
        P2 --> L2[LDPC Kodlayıcı 1/2]
        L1 --> M1[BPSK Modülatör]
        L2 --> M2[BPSK Modülatör]
        M1 --> G1[Güç Katsayısı: 0.894]
        L2 --> M2
        M2 --> G2[Güç Katsayısı: 0.447]
        G1 & G2 --> Add[Sinyal Toplayıcı - Süperpozisyon]
    end

    subgraph Kanal (AWGN & Fading)
        Add --> Ch[Gürültü & Zaman/Frekans Kayması]
    end

    subgraph Alıcı (Receiver - SIC)
        Ch --> S1[User 1 Çözücü]
        S1 --> D1[User 1 Çözülmüş Veri]
        D1 --> Rec1[Yeniden Kodlama & Modülasyon]
        Ch & Rec1 --> SIC[SIC Aligner - Çapraz Korelasyon]
        SIC --> Sub[User 1 Sinyalini Çıkarma]
        Sub --> S2[User 2 Çözücü]
        S2 --> D2[User 2 Çözülmüş Veri]
    end
```

#### 1. Verici Aşaması (Transmitter)
* **Dinamik Dolgu (Padding):** Farklı boyutlardaki iki dosyadan kısa olanı, GNU Radio'nun bloke olmasını önlemek ve LDPC blok sınırlarına uymak için `77` baytın tam katı olacak şekilde sıfırlarla dolgulanır.
* **Hata Tespit (CRC32):** Her pakete 4 bayt CRC32 eklenerek alıcı tarafta hatasız kurtarma doğrulanır.
* **Kanal Kodlama (LDPC):** `n_1296_k_0648_ieee.alist` kullanılarak 1/2 oranında LDPC hata düzeltme kodlaması uygulanır (81 bayt girdi $\rightarrow$ 162 bayt çıktı).
* **Güç Paylaşımı (Power Allocation):** User 1 (yakın kullanıcı) sinyali $a_1 = 0.894$ genliğiyle, User 2 (uzak kullanıcı) sinyali ise $a_2 = 0.447$ genliğiyle çarpılarak süperpoze edilir.

#### 2. Alıcı Aşaması (Receiver - SIC)
* **User 1 Kurtarma:** Gücü yüksek olan User 1 sinyali, User 2'nin sinyali gürültü kabul edilerek doğrudan BPSK yumuşak karar (soft decision) ve LDPC kod çözücü (LDPC Decoder) yardımıyla çözülür.
* **Çapraz Korelasyon ve Zaman Hizalama (SIC Aligner):** Çözülen User 1 verisi yeniden kodlanıp modüle edilir. Alınan süperpoze sinyal ile çapraz korelasyon yapılarak zaman kayması sembol hassasiyetinde bulunur.
* **Girişim Giderme (SIC):** Hizalanan ve fazı kestirilen User 1 sinyali, süperpoze sinyalden matematiksel olarak çıkarılır.
* **User 2 Kurtarma:** Geriye kalan temizlenmiş sinyal üzerinden User 2'nin verisi çözülerek kurtarılır.
* **Dolgu Temizleme (Stripping):** Alınan ham akışlardan dolgu sıfırları ayıklanarak orijinal dosyalar (örneğin PNG resimleri) MD5 hash eşleşmesiyle birebir kurtarılır.

### 🚀 NOMA Simülasyonunu Çalıştırma

NOMA simülasyonunu dinamik derleme, dolgulama, throttle yönetimi ve otomatik doğrulama özellikleriyle tek bir komutla başlatabilirsiniz:

```bash
python run_image_transfer.py
```

### 🚀 Donanımsal USRP E310 Testlerini Çalıştırma

Projenin son aşaması olan USRP E310 donanım testleri için alıcı ve verici kodları ayrıştırılmıştır. Headless (GUI olmayan) yapısı sayesinde SSH üzerinden terminal ortamlarında kararlı çalışır.

1. **Alıcı Tarafında (Receiver - USRP RX):**
   ```bash
   cd usrp
   python run_usrp_rx.py --freq 868e6 --gain 25 --rate 200e3
   ```
   *Alıcı havadan sinyal beklemeye başlar.*

2. **Verici Tarafında (Transmitter - USRP TX):**
   ```bash
   cd usrp
   python run_usrp_tx.py --freq 868e6 --gain 20 --rate 200e3
   ```
   *Verici, resimleri otomatik dolgulayarak havaya sürekli iletir.*

---

## 📂 Proje Klasör Yapısı

```text
├── usrp/                       # Gerçek ortam USRP E310 donanım test klasörü
│   ├── NOMA_TX.py              # Headless USRP Transmitter Flowgraph
│   ├── NOMA_RX.py              # Headless USRP Receiver Flowgraph
│   ├── NOMA_epy_block_0.py     # Soft Diff Decoder (User 2)
│   ├── NOMA_epy_block_0_0.py   # Soft Diff Decoder (User 1)
│   ├── NOMA_epy_block_1.py     # Custom Decoupled SIC Aligner
│   ├── run_usrp_tx.py          # TX hazırlık (padding) ve iletim betiği
│   └── run_usrp_rx.py          # RX alım, temizleme (stripping) ve doğrulama betiği
├── NOMA.grc                    # GNU Radio Companion tasarım dosyası
├── NOMA.py                     # GRC dosyasından derlenen Python akış grafiği
├── NOMA_epy_block_1.py         # Custom Python SIC Aligner Bloğu (Simülasyon)
├── run_image_transfer.py       # Uçtan uca otomatik simülasyon ve doğrulama betiği
├── transmit_1.png              # User 1 için gönderilecek örnek resim
├── transmit_2.png              # User 2 için gönderilecek örnek resim
├── n_1296_k_0648_ieee.alist    # LDPC Parite Kontrol Matrisi
├── .gitignore                  # Git dışlama dosyası
└── README.md                   # Proje açıklama dokümanı
```

---

## 🛠️ Sorun Giderme (Troubleshooting)

| Sorun | Neden / Çözüm |
| :--- | :--- |
| **SSH Terminal Hataları** | SSH oturumunda `export TERM=xterm` komutunu çalıştırın. |
| **Veri Kaybı / Taşma (Overflow)** | Ethernet'in `ethtool` kullanılarak 1000Mb/s Full Duplex ayarlandığından emin olun. |
| **Simülasyon Dosya Kilitlenmeleri** | Arka planda askıda kalan eski Python süreçlerini temizlemek için `run_image_transfer.py` otomatik olarak askıdaki süreçleri bulup sonlandırır. Alternatif olarak açık olan GRC uygulamasını kapatıp simülasyonu yeniden başlatın. |

---

## 🗺️ Yol Haritası (Roadmap)

*   [x] Ebyte E220-900T22D LoRa modülünün kurulumunu yap ve USRP E310 ile 868 MHz bandını analiz et.
*   [x] BPSK modülasyonu ve 1/2 LDPC kanal kodlama yapısını tasarla.
*   [x] Farklı boyutlardaki dosyaların GNU Radio'yu tıkamadan gönderilmesi için dinamik sıfır dolgulama (padding) algoritmasını geliştir.
*   [x] Custom Python SIC Aligner bloğu yazarak alıcı tarafta zaman/faz kayması kestirimli girişim giderme yapısını tamamla.
*   [x] Uçtan uca dosya transferini MD5 eşleşmesiyle \%100 hatasız doğrula.
