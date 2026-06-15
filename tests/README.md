# NOMA Simülasyon Testleri ve Çalışma Kılavuzu

Bu dizin, BPSK NOMA + LDPC + SIC projesinin akademik performansı ve kararlılığını ölçmek amacıyla geliştirilen otomatik test senaryolarını içermektedir. Tüm testler, `NOMA.py` simülatörünün parametrelerini otomatik olarak sweep ederek sonuçları CSV formatında verileştirmekte ve PNG grafiklerine dönüştürmektedir.

---

## 📂 Test Klasör Yapısı

*   `tests/distance_sweep/`: Uzak kullanıcının (User 2) SNR/Mesafe ilişkisine göre BER oranlarını ölçer.
*   `tests/power_sweep/`: Toplam gücün ($a_1^2 + a_2^2 = 1.0$) yakın ve uzak kullanıcılar arasındaki bölüşüm oranlarını sweep eder.
*   `tests/ber_waterfall/`: Kanal gürültüsüne ($\sigma$) göre BER/BLER waterfall eğrilerini ve Rayleigh sönümlemeli kanal altındaki Outage/Kapasite analizlerini sunar.
*   `tests/sic_mismatch/`: Alıcıdaki SIC çıkarma aşamasında oluşan faz ($\Delta \theta$) ve genlik ($\epsilon$) sapmalarının etkisini ölçer.
*   `tests/complexity_latency/`: LDPC kod çözücünün iterasyon sayısına göre CPU süresini (karmaşıklık) ve BER başarısını (doğruluk) ölçer.
*   `tests/jamming/`: Kanalda tek tonlu (single-tone) aktif karıştırma sinyalinin genliğine göre scrambler/LDPC sistemlerinin karıştırma direncini ölçer.
*   `tests/channel_impairments/`: Alıcıdaki yerel osilatör evre gürültüsü (Phase Noise) ve I/Q faz dengesizliğinin (IQ Imbalance) BER üzerindeki donanımsal etkilerini ölçer.

---

## 📑 Test Detayları ve Çalışma Prensipleri

### 1. Mesafe Taraması Testi (`tests/distance_sweep/`)
*   **Testin Amacı:** Log-Distance Yol Kaybı ($n=3.5$ yarı kentsel ortam) modeli kullanılarak, uzak kullanıcının (User 2) hangi mesafeden sonra hatalı veri almaya başladığını tespit etmek.
*   **Ne Yapıldı?** Mesafe $10\text{m}$ ile $2000\text{m}$ arasında taranmış, gürültü voltajları mesafe denklemlerinden türetilerek simülasyon koşturulmuştur. Eşik SNR sınırı $6\text{ dB}$ ($512\text{ m}$) olarak belirlenmiştir.
*   **Python Kodu Ne Yapıyor?**
    - `calculate_noise_from_distance()` fonksiyonu ile mesafeyi gürültü standart sapmasına ($\sigma$) dönüştürür.
    - `modify_noma_noise()` ile `NOMA.py` içindeki noise değerini regex kullanarak değiştirir.
    - Simülasyonu 15 saniye çalıştırıp orijinal ve alınan dosyaların bitlerini unpack ederek BER hesaplar.
    - Sonuçları `academic_distance_sweep.csv` ve `distance_vs_ber.png` olarak kaydeder. Orijinal dosyayı yedekler ve geri yükler.

### 2. Güç Paylaşım Taraması Testi (`tests/power_sweep/`)
*   **Testin Amacı:** NOMA'nın kalbi olan güç paylaşım katsayılarının ($P_1 = a_1^2$ ve $P_2 = a_2^2$) demapping ve SIC başarısı üzerindeki etkisini optimize etmek.
*   **Ne Yapıldı?** Toplam güç sabit tutularak ($P_1 + P_2 = 1.0$) User 1'in gücü $\%50$'den $\%95$'e kadar sweep edilmiştir.
*   **Python Kodu Ne Yapıyor?**
    - Güç senaryolarına göre genlik katsayılarını ($a_i = \sqrt{P_i}$) hesaplar.
    - `modify_noma_amplitudes()` fonksiyonu ile `NOMA.py` içindeki kullanıcı demapper genliklerini ve `noma_sic_aligner.py` (SIC Aligner) içindeki `near_user_amplitude` katsayısını regex ile günceller.
    - Simülasyon sonrası dosya karakter eşleşmelerini kontrol ederek User 1 ve User 2 doğruluk oranlarını (%) hesaplar.

### 3. BER & BLER Waterfall Testi (`tests/ber_waterfall/`)
*   **Testin Amacı:** Kanal gürültü voltajı ($\sigma$) değişiminin sistemin bit ve blok bazlı hata oranlarına (BER/BLER) etkisini görmek ve teorik Rayleigh sönümleme metrikleri ile karşılaştırmak.
*   **Ne Yapıldı?** Gürültü voltajı `0.02` ile `0.30` (Eb/N0: `31 dB` ila `7.5 dB`) arasında taranmıştır. Aynı zamanda 10,000 örnekli Monte Carlo Rayleigh sönümleme simülasyonu çalıştırılarak teorik Outage Probability ve Ergodik Kapasite değerleri hesaplanmıştır.
*   **Python Kodu Ne Yapıyor?**
    - `modify_noma_noise()` ile gürültüyü günceller.
    - `calculate_ber_and_bler()` ile CRC32 kontrolünü geçemeyen paket oranını (BLER/PER) ve bit hata oranını (BER) hesaplar.
    - `simulate_rayleigh_metrics()` ile Rayleigh sönümleme kanalı oluşturarak NOMA vs. OMA Sum Capacity ve Outage olasılıklarını Monte Carlo yöntemiyle hesaplar.
    - Sonuçları `ber_waterfall.csv` dosyasına yazar ve Matplotlib ile 4 farklı analiz grafiği (BER, BLER, Outage, Ergodic Capacity) üretir.

### 4. SIC Sapması ve Mismatch Testi (`tests/sic_mismatch/`)
*   **Testin Amacı:** Alıcıdaki Costas loop faz kaymalarının ve genlik kestirim hatalarının SIC çıkarma başarısına ve User 2'nin performansına etkisini ölçer.
*   **Ne Yapıldı?** Faz sapması $0^\circ$ ile $30^\circ$ arasında, genlik sapması ise $\%-20$ ile $\%+20$ arasında sweep edilmiştir. Başarı kriteri olarak başarılı paket oranlarına dayalı Jain's Fairness Index hesaplanmıştır.
*   **Python Kodu Ne Yapıyor?**
    - `modify_sic_block()` fonksiyonu ile alıcıdaki gömülü python SIC bloğunun (`NOMA_epy_block_1.py`) çıkarma formülüne ($\Delta \theta$) faz ve ($\epsilon$) genlik hata terimlerini enjekte eder.
    - Simülasyonu koşturarak User 2'nin bit hata oranını (BER) ve Jain Fairness index değerlerini hesaplar.
    - Sonuçları `sic_mismatch_results.csv` dosyasına kaydeder ve faz/genlik sapmalarına göre iki adet 2D duyarlılık grafiği üretir.

### 5. LDPC Karmaşıklık ve Zamanlama Ödünleşimi Testi (`tests/complexity_latency/`)
*   **Testin Amacı:** LDPC kod çözücünün maksimum iterasyon sayısı sınırının işlem karmaşıklığı (CPU süresi) ve hata düzeltme performansı (BER) arasındaki ödünleşim sınırlarını saptamak.
*   **Ne Yapıldı?** `max_iter` parametresi 2 ile 20 arasında taranmış, Eb/N0 = 13.5 dB ($\sigma=0.15$) sınırında 15 saniyelik simülasyonlar koşturulmuştur.
*   **Python Kodu Ne Yapıyor?**
    - `modify_noma_iterations()` fonksiyonu ile `NOMA.py` içindeki LDPC kod çözücü bloklarının `make` fonksiyonundaki maksimum iterasyon parametresini günceller.
    - Windows API (`GetProcessTimes`) çağrılarını `ctypes` kütüphanesi üzerinden çağırarak, GUI arayüzü ile çalışan python sürecinin gerçek kernel/user CPU zamanını ölçer (çevresel gecikmelerden etkilenmemek için).
    - Sonuçları `complexity_results.csv` dosyasına kaydeder ve Matplotlib ile çift eksenli (CPU Zamanı ve BER) performans grafiğini üretir.

### 6. Jamming (Karıştırma) Güvenlik ve Dayanım Testi (`tests/jamming/`)
*   **Testin Amacı:** Sistemde veri iletimi yapılırken kanala kasıtlı tek tonlu (single-tone) bir karıştırıcı sinyal eklendiğinde, BPSK modülasyonu, karıştırıcı (scrambler) ve Rate-1/2 LDPC kodunun dayanım sınırını ölçmek.
*   **Ne Yapıldı?** Temiz kanal ($\sigma = 0.05$) ortamında, 10 kHz frekansında tek tonlu bir jammer sinyali sisteme enjekte edilmiş ve genliği 0.0 ile 0.5 (gücü 0.0 ile 0.25) arasında taranmıştır.
*   **Python Kodu Ne Yapıyor?**
    - `inject_jammer_in_noma()` fonksiyonu ile `NOMA.py` içerisine GNU Radio `analog.sig_source_c` bloğunu enjekte eder ve bunu kanal toplama bloğuna (`blocks.add_vcc`) bağlar.
    - `modify_jammer_amplitude()` ile jammer sinyalinin genliğini dinamik olarak değiştirir.
    - Simülasyon sonrası User 1 ve User 2'nin bit hata oranını (BER) hesaplar, sonuçları `jamming_results.csv` ve `jamming_vs_ber.png` olarak kaydeder.

### 7. Kanal ve Donanımsal Kusurlar Testi (`tests/channel_impairments/`)
*   **Testin Amacı:** Alıcı donanımında yer alan yerel osilatörün (LO) evre gürültüsü (Phase Noise) ve I/Q demodülatörünün faz dengesizliği (IQ Phase Imbalance) kusurlarının NOMA demodülasyon ve SIC başarısına etkisini incelemek.
*   **Ne Yapıldı?** Faz gürültüsü standart sapması 0.0 radyan ile 0.15 radyan arasında; I/Q faz dengesizliği ise $0^\circ$ ile $15^\circ$ (ve sabit $g=0.05$ genlik dengesizliği) arasında taranmıştır.
*   **Python Kodu Ne Yapıyor?**
    - `modify_sic_impairments()` fonksiyonu ile `NOMA_epy_block_1.py` bloğuna RF donanım kusurlarını matematiksel olarak enjekte eder.
    - I/Q faz ve genlik dengesizliği için I ve Q kanallarını faz kayması ve genlik çarpanıyla yeniden karıştırır. Evre gürültüsü için sinyali rastgele Gauss dağılımlı faz terimiyle ($e^{j\theta}$) çarpar.
    - Simülasyonu koşturarak donanımsal kusurların her iki kullanıcı üzerindeki BER/BLER etkisini `impairments_results.csv` dosyasına kaydeder ve grafikleri (`phase_noise_vs_ber.png`, `iq_imbalance_vs_ber.png`) üretir.

---

## 🚀 Testleri Çalıştırma Kılavuzu

Herhangi bir testi çalıştırmak için terminalde ilgili klasörün içine giderek scripti çalıştırmanız yeterlidir.

> [!WARNING]
> Testler çalışırken `NOMA.py` veya `NOMA_epy_block_1.py` dosyalarında geçici regex değişiklikleri yapılmaktadır. Testlerin yarıda kesilmesi durumunda bu dosyalar yedeklerinden (`*.bak`) otomatik olarak geri yüklenir. Eğer kilitlenme yaşanırsa, `git checkout NOMA.py NOMA_epy_block_1.py` komutuyla dosyaları sıfırlayabilirsiniz.

### Örnek Çalıştırma Adımları:

```powershell
# LDPC Karmaşıklık ve Zamanlama Ödünleşimi Testi için:
cd tests/complexity_latency
C:\Users\Armagan\radioconda\python.exe run_complexity_test.py

# Jamming Dayanım Testi için:
cd ../jamming
C:\Users\Armagan\radioconda\python.exe run_jamming_test.py

# Donanımsal Kusurlar Testi için:
cd ../channel_impairments
C:\Users\Armagan\radioconda\python.exe run_channel_impairments_test.py
```

---

## 📝 Bugün Yapılan Güncellemeler ve Geliştirmeler (13.06.2026)

Bugün sistemin akademik doğruluk seviyesini artırmak ve kararlılığını test etmek amacıyla aşağıdaki önemli güncellemeler yapılmıştır:

*   **İstatistiksel Güvenilirlik (1000 Paket Desteği):** Tüm sweep testlerindeki iletilen veri hacmi paket başına 77 bayt olmak üzere 20 paketten **1000 pakete** (toplam 77.000 bayt / 616.000 bit) yükseltilmiştir.
*   **Preamble Tabanlı Lock-Loss Arındırması (Sıfır Hata Tabanı):** Alıcının sembol senkronizasyonu ve Costas Loop kilitlenme evresinde kaybettiği paketlerin (transient lock-time loss) analiz dışı kalması sağlanmıştır. Gönderilen 1050 paketin ilk 50'si öncül (preamble) olarak kabul edilerek kilitlenme aşaması atlanmış ve BER/BLER hesaplaması kararlı durumdaki (steady-state) son **1000 paket** üzerinden yapılmıştır. Böylece yüksek SNR bölgesinde yapay binde 1 (%0.10) hata tabanı sıfıra indirilmiştir.
*   **Dinamik Dosya Boyutu İzleme (Polling Loop):** `run_host_transfer.py` Wrapper scriptinin çalışma prensipleri temel alınarak, simülasyonların durdurulmasında sabit saniyeli beklemeler yerine dinamik dosya izleme mekanizmasına geçilmiştir. Alınan dosyaların ikisi de hedef boyut olan **77.000 bayta** ulaştığı an (veya transfer 5 saniye kesildiğinde) `NOMA.py` süreci otomatik kapatılır. Bu sayede GNU Radio tampon (buffering/flushing) kayıpları sıfırlanmış, yapay paket hataları engellenmiştir.
*   **RF / Kanal Kusurları Grafikleri ve Unicode Düzeltmesi:** Matplotlib çizim fonksiyonlarının Windows işletim sisteminde Türkçe karakterlerden (`ş`, `ı`, `ğ` vb.) dolayı `charmap` hatası fırlatarak çöktüğü tespit edilmiş, grafiklerin başlık ve etiketleri ASCII standardına uyarlanarak sorunsuz üretilmeleri sağlanmıştır.
*   **1000 Paket BER/BLER Waterfall Sweep Başarısı:** 1000 paketlik dinamik izlemeli BER testi başarıyla koşturulmuştur. Gürültü standart sapması ($\sigma$) $0.03$ ile $0.45$ arasında (Eb/N0: $27.5\text{ dB}$ ila $3.9\text{ dB}$) sweep edilmiş ve gerçek şelale (waterfall) eğrileri elde edilmiştir. Düşük SNR bölgesinde ($3.9\text{ dB}$) User 1 BER $\%8.90$ ve User 2 BER $\%20.50$ iken, LDPC'nin devreye girmesiyle birlikte $5.0\text{ dB}$ SNR'da sırasıyla $\%0.30$ ve $\%5.20$ seviyelerine inmiş ve $\ge 5.9\text{ dB}$ SNR değerlerinde tam $\%0.00$ sıfır hata oranına ulaşılmıştır.
*   **Tüm Test Scriptlerinin Güncellenmesi:** Yapılan bu dinamik polling ve 1000 paketlik veritabanı iyileştirmesi, diğer tüm sweep test scriptlerine (`distance_sweep`, `power_sweep`, `sic_mismatch`, `complexity_latency`, `jamming`, `channel_impairments`) başarıyla entegre edilmiş, ancak scriptler çalıştırılmadan kod olarak saklanmıştır.
*   **Grafik Çıktılarındaki Kırpılma Sorununun Çözülmesi (Matplotlib Layout Fix):** Özellikle çift eksenli (twinx) grafikler ve uzun başlık/etiket içeren PNG çıktılarında yaşanan kenar kırpılma/kesilme problemleri, tüm sweep test scriptlerindeki `plt.savefig()` çağrılarına `bbox_inches='tight'` parametresi eklenerek giderilmiştir. `ber_waterfall` sweep testi yeniden koşturulmuş ve kusursuz görünümde grafikler (`ber_waterfall.png`, `bler_waterfall.png`, `outage_probability.png`, `ergodic_capacity.png`) başarıyla yeniden üretilmiştir.



