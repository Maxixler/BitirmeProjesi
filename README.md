# USRP E310 & LoRaWAN Sinyal Analiz Projesi

Bu proje, **USRP E310** Yazılım Tabanlı Radyo (SDR) kullanarak gerçek dünya kablosuz sinyallerini, özellikle **868 MHz LoRaWAN frekans bandını** örneklemeyi ve analiz etmeyi amaçlamaktadır.

## Proje Hedefi
Temel amaç, bir LoRa modülü tarafından üretilen 868 MHz kablosuz sinyallerin USRP E310 kullanılarak yakalanması, örneklenmesi ve işlenmesidir.

*   **Hedef Sinyal:** 868 MHz (LoRaWAN)
*   **Sinyal Kaynağı:** LLCC68 Ebyte E220-900T22D (868MHz-915MHz, 22dBm)
*   **Alıcı:** USRP E310 (Embedded Serisi)

## Donanım ve Yazılım Gereksinimleri

### Donanım
*   **SDR:** USRP E310 (Embedded Serisi)
*   **Ana Bilgisayar (Host):** Arch Linux yüklü PC
*   **LoRa Modülü:** Ebyte E220-900T22D
*   **Bağlantı:** Ethernet (Doğrudan bağlantı), USB-Seri (Konsol erişimi)

### Yazılım
*   **İşletim Sistemi (Host):** Arch Linux
*   **SDR Sürücüleri:** UHD (USRP Hardware Driver)
*   **Sinyal İşleme:** GNU Radio / Python (`sineWaveGRC.py`)

## Kurulum ve Konfigürasyon

### 1. Fiziksel Bağlantılar
*   USRP E310'u **Ethernet** üzerinden Ana Bilgisayara bağlayın.
*   Konsol erişimi için USRP E310'u **USB-Seri** üzerinden Ana Bilgisayara bağlayın.

### 2. Ağ Konfigürasyonu
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

## Kullanım ve Test

### 1. Bağlantı Kontrolü
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

### 2. Sinyal Testi (Gömülü Mod)
RF ön yüzünü test etmek için Python betiğini doğrudan USRP E310 üzerinde çalıştırın.

```bash
python3 sineWaveGRC.py
```
*   **Başarı Göstergesi:** `[INFO] ... Performing CODEC loopback test ... passed`

### 3. Akış (Streaming) Testi
*   Akışı almak için Ana Bilgisayarda GNU Radio kullanın (ZMQ SUB Source üzerinden).
*   Spektrum Analizöründe (QT GUI Frequency Sink) gürültü tabanını veya sinyali gözlemleyin.

## Sorun Giderme

| Sorun | Çözüm |
| :--- | :--- |
| **SSH Terminal Hataları** | SSH oturumunda `export TERM=xterm` komutunu çalıştırın. |
| **Veri Kaybı / Taşma (Overflow)** | Ethernet'in `ethtool` kullanılarak 1000Mb/s Full Duplex ayarlandığından emin olun. |

## Yol Haritası (Roadmap)
*   [ ] Ebyte E220-900T22D LoRa modülünü bir mikrodenetleyiciye (Arduino/STM32) bağla.
*   [ ] 868 MHz'de bir "Beacon" (işaretçi) sinyali üret.
*   [ ] USRP E310 merkez frekansını 868 MHz'e ayarla ve beacon sinyalini yakala.
