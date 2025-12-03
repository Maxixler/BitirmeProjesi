Bitirme Projesi Günlük İlerleme Raporu
Tarih: 03.12.2025 Konu: USRP E310 Bağlantı Kurulumu, Ağ Konfigürasyonu ve 868 MHz Sinyal Test Hazırlığı

1. Proje Hedefi ve Kapsam Değişikliği
  Projenin bu aşamasında, gerçek dünya sinyallerini örneklemek amacıyla harici bir sinyal kaynağı kullanılmasına karar verilmiştir.
  
  Hedef Sinyal: 868 MHz frekans bandı (LoRaWAN).
  
  Kullanılacak Modül: LLCC68 Ebyte E220-900T22D (868MHz-915MHz, 22dBm).
  
  Amaç: LoRa modülü ile üretilen 868 MHz'lik kablosuz sinyalin, USRP E310 SDR cihazı kullanılarak yakalanması, örneklenmesi ve işlenmesi.

2. Donanım ve Yazılım Kurulumu
  A. Fiziksel Bağlantı
  SDR: USRP E310 (Embedded Series).
  
  Ana Bilgisayar (Host): Arch Linux yüklü PC.
  
  Bağlantı Tipi: Ethernet (Doğrudan bağlantı) ve USB-Seri (Konsol erişimi için).
  
  B. Ağ Konfigürasyonu (Network Configuration)
  USRP ve Ana Bilgisayar arasında yüksek hızlı veri aktarımı (streaming) sağlamak için statik IP atamaları yapıldı ve Ethernet arayüzü Gigabit hızına sabitlendi.
  
  1. Seri Port (Console) Bağlantısı: USRP E310'a IP adresi atamak için öncelikle USB üzerinden seri bağlantı kuruldu:
     sudo screen /dev/ttyUSB0 115200
  2. IP atamaları
     USRP E310 Tarafı (eth0):
       ip addr add 192.168.10.2/24 dev eth0
     Ana Bilgisayar Tarafı (eno1):
       ip addr add 192.168.10.1/24 dev eno1
  3. Ethernet Performans Ayarı (Host): Veri kaybını önlemek (overflow/underrun) için Ethernet kartı Full Duplex ve 1000Mb/s (Gigabit) moduna zorlandı:
     sudo ethtool -s eno1 autoneg on speed 1000 duplex full
3. Test ve Doğrulama Süreci
   A. Bağlantı Kontrolü
    Seri bağlantıdan çıkılarak SSH üzerinden ağ bağlantısı test edildi. xterm hatasını gidermek için terminal ortam değişkeni ayarlandı.
            # Ana bilgisayardan USRP'ye SSH bağlantısı
      ssh root@192.168.10.2
      
      # Terminal uyumluluk hatası çözümü (USRP içinde)
      export TERM=xterm
  B. Cihaz Doğrulama
    UHD sürücüsünün cihazı ağ üzerinde gördüğü doğrulandı:
     uhd_find_devices
   Sonuç: Cihaz başarıyla listelendi ve Product: e310_sg3 olarak tanımlandı.
  C. Gömülü Mod (Embedded Mode) Sinyal Testi
    Hazırlanan sineWaveGRC.py Python betiği doğrudan USRP E310 üzerinde çalıştırıldı.
    
    Komut: python3 sineWaveGRC.py
    
    Gözlem (Ekran Görüntüsü 1): Terminal çıktısında [INFO] [0/Radio#0] Performing CODEC loopback test on channel 1 ... passed mesajı görüldü. Bu, USRP'nin RF ön yüzünün (frontend) başarıyla başlatıldığını gösterir.
    
    Gözlem (Ekran Görüntüsü 2): Ana bilgisayardaki GNU Radio arayüzünde (ZMQ SUB Source üzerinden) veri akışı sağlandı ve spektrum analizöründe (QT GUI Frequency Sink) gürültü tabanı (noise floor) görüntülendi.
   
   4. Karşılaşılan Hatalar ve Çözümleri
    Sorun: SSH bağlantısında terminalin (nano vb.) düzgün açılmaması.
    
    Çözüm: export TERM=xterm komutu ile terminal tipi tanıtıldı.
    
    Sorun: Ethernet bağlantısında olası hız uyuşmazlığı.
    
    Çözüm: ethtool ile autoneg on ve speed 1000 yapılarak bağlantı kararlı hale getirildi.
   5. Bir Sonraki Adım Planı
    Ebyte E220-900T22D LoRa modülünün bir mikrodenetleyiciye (Arduino/STM32) bağlanarak 868 MHz'de "Beacon" (işaretçi) sinyali üretmesi sağlanacak.

    USRP E310 üzerindeki Center Frequency 868 MHz'e ayarlanarak bu sinyalin spektrumda yakalanması test edilecek.
