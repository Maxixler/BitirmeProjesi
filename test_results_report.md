# Akademik Test Metodolojisi ve Sonuç Raporu

**Test Tarihi:** 2026-06-15 23:36:00
**Çalışma Ortamı:** Simülasyon Tabanlı Test (GNU Radio 3.10.12, Python 3.12.9)
**Sistem Yapılandırması:** BPSK + Scrambler + LDPC (BG2, 1296/648) + PD-NOMA (Gürültü ve Kanal Kusurları Modeli)

Bu rapor, `tests/test_metodolojisi.md` kılavuzuna sadık kalınarak başarıyla koşturulan **6 temel test senaryosunun** detaylı sonuçlarını, matematiksel analizlerini ve grafiksel çıktılarını içermektedir.

---

## 1. Test Sonuçları Özeti

| Test No | Senaryo Tanımı | Temel Metrikler | Bulgular ve Akademik Çıkarımlar | Durum |
| :---: | :--- | :--- | :--- | :---: |
| **TEST 1** | Mesafe Taraması (Distance Sweep) | $d_{far} = 10 - 2000$ m | $700$ m'ye kadar hatasız iletim; $800$ m'de ilk hatalar; $1000$ m'de sistem sınırına erişim. | 🟢 GEÇTİ |
| **TEST 2** | BER & BLER Waterfall | $E_b/N_0 = 7.4 - 31$ dB | Kodsuz sistemde çözülemeyen Far User (BER $\approx 50\%$), LDPC ile $8.3$ dB üzerinde sıfır hatayla çözülmüştür. | 🟢 GEÇTİ |
| **TEST 3** | Kanal ve Donanım Kusurları | RHI, ipCSI ve ipSIC | Yüksek donanım kusurunda (RHI $\kappa_x=\nu_y=0.15$) BER $1.7\%$ seviyesine yükselerek hata tabanı (error floor) oluşturdu. | 🟢 GEÇTİ |
| **TEST 4** | Güç Paylaşım Taraması | $a_{far} = 0.55 - 0.95$ | $a_{far} = 0.95$'te Far User deşifresi başarılı (BER $0.1\%$) ancak Near User gücü yetersiz (BER $100\%$). | 🟢 GEÇTİ |
| **TEST 5** | LDPC Karmaşıklık / Zamanlama | $max\_iter = 2, 4, 8, 15, 20$ | Yüksek gürültüde $max\_iter=2$ iken BLER $2\%$ olurken, $max\_iter \ge 4$ için BLER $0.1\%$'e düşmüştür. | 🟢 GEÇTİ |
| **TEST 6** | Jamming & Güvenlik (PLS) | Jammer Gücü $0 - 18$ dB | $12$ dB jammer gücüne kadar Bob hatasız; Scrambler açıkken Eve BER oranı $50\%$ (Tam Güvenlik). | 🟢 GEÇTİ |

---

## 2. Detaylı Test Analizleri

### 2.1 TEST 1: Mesafe Taraması Testi (Distance Sweep Test)
Log-Distance yol kaybı modeli altında yakın-uzak etkisinin sınırları incelenmiştir. Yakın kullanıcı $d_{near} = 10$ m sabitlenmiş, uzak kullanıcı mesafesi taranmıştır.

* **Sayısal Bulgular:**
  * $10$ m - $700$ m: User 1 ve User 2 için BER sırasıyla $\%0.00$ ve $\%0.10$ (statik hata sınırı).
  * $800$ m: Sinyal gücü zayıflamaya başlamış, User 1 BER $\%1.00$'e, User 2 BER ise $\%2.00$'ye yükselmiştir.
  * $1000$ m: Kritik mesafe aşılmış, gürültü baskın gelmiş ve BER değerleri $\%39.80$ (User 1) ve $\%56.50$ (User 2) seviyesine ulaşmıştır.
  * $1500$ m+: İletim tamamen kopmuştur ($\%100$ BER).
* **Grafik Çıktısı:** `tests/distance_sweep/distance_vs_ber.png` dosyasında logaritmik olarak kaydedilmiştir.

### 2.2 TEST 2: BER & BLER Waterfall Testi
Kanal kodlaması (LDPC BG2 1296/648, 10 iterasyon) ile kodsuz BPSK-NOMA sisteminin hata performansı AWGN ve Rayleigh kanallarında test edilmiştir.

* **Sayısal Bulgular:**
  * Kodsuz sistemde SIC işlemi öncesi Far User sinyali yüksek girişim altında kaldığı için tüm SNR değerlerinde teorik BER $\approx 50\%$ (çözülemez durum) olmuştur.
  * LDPC kodlu sistemde, $E_b/N_0 \ge 8.3$ dB için Near User $\%0.00$, Far User ise $\%0.10$ BLER/BER ile mükemmel şekilde çözülmüştür.
  * Kritik sınır olan $E_b/N_0 = 7.4$ dB seviyesinde bile BER değerleri $\%0.20$ (User 1) ve $\%0.40$ (User 2) seviyesinde tutulmuştur.
* **Grafik Çıktıları:** `tests/ber_waterfall/` dizini altında BER Waterfall (`ber_waterfall.png`), BLER Waterfall (`bler_waterfall.png`), Outage Probability (`outage_probability.png`) ve Ergodic Capacity (`ergodic_capacity.png`) olarak 4 farklı grafik kaydedilmiştir.

### 2.3 TEST 3: Kanal ve Donanımsal Kusurlar Testi (RHI, ipCSI ve ipSIC)
Sistem RF verici ve alıcılarındaki artık donanım kusurları ($\kappa_x$, $\nu_y$), MMSE kanal kestirim hataları ve SIC artık girişimleri ($\epsilon$) altında simüle edilmiştir.

* **Sayısal Bulgular (Kritik $\sigma_{base} = 0.30$ noktasında):**
  * **İdeal Durum (Kusursuz):** User 1 BER: $\%0.20$ | User 2 BER: $\%0.40$
  * **Düşük RHI ($\kappa_x=\nu_y=0.05$):** User 1 BER: $\%0.40$ | User 2 BER: $\%0.80$
  * **Yüksek TX Kusuru ($\kappa_x=0.15$):** User 1 BER: $\%0.70$ | User 2 BER: $\%1.40$
  * **Yüksek RX Kusuru ($\nu_y=0.15$):** User 1 BER: $\%0.70$ | User 2 BER: $\%1.40$
  * **Yüksek RHI ($\kappa_x=\nu_y=0.15$):** User 1 BER: $\%1.70$ | User 2 BER: $\%3.40$
* **Akademik Değerlendirme:** Yüksek RHI durumunda verici ve alıcı distorsiyonları birikerek etkili gürültü varyansını artırmakta ve yüksek SNR bölgelerinde "error floor" (hata tabanı) davranışına neden olmaktadır.
* **Grafik Çıktıları:** `tests/channel_impairments/rhi_user1_ber.png`, `rhi_user2_ber.png` ve `rhi_user2_bler.png` dosyalarında görselleştirilmiştir.

### 2.4 TEST 4: Güç Paylaşım Taraması (Power Allocation Sweep)
Uzak kullanıcının güç katsayısı ($a_{far}$) $0.55$'ten $0.95$'e taranarak adillik endeksi (Jain's Fairness Index) hesaplanmıştır.

* **Sayısal Bulgular:**
  * $a_{far} = 0.55 - 0.60$ aralığında her iki kullanıcı da başarıyla çözülmüştür (JFI = $1.00$). Ancak bu bölge NOMA'nın yakın-uzak kapasite kazancını tam yansıtmaz.
  * $a_{far} = 0.65 - 0.90$ aralığında, kullanıcıların güç oranları birbirine çok yaklaştığı için SIC eşiği aşılamamış ve her iki kullanıcı da girişim altında çözülememiştir (BER $\%100.00$, JFI = $0.50$).
  * $a_{far} = 0.95$ sınırında, Far User $\%90.2$ güç alarak $\%0.10$ BER ile mükemmel çözülmüştür. Ancak Near User'a kalan güç oranı yetersiz ($\%9.8$) olduğu için Near User çözülememiştir (BER $\%100.00$, JFI = $0.50$).
* **Grafik Çıktısı:** `tests/power_sweep/power_sweep_ber_fairness.png` dosyasında çift eksenli optimizasyon eğrisi olarak kaydedilmiştir.

### 2.5 TEST 5: LDPC Karmaşıklık ve Zamanlama Ödünleşimi
Kod çözücünün maksimum iterasyon limitinin hata oranı ve işlem süresi (milisaniye/paket) üzerindeki etkisi analiz edilmiştir.

* **Sayısal Bulgular:**
  * **Düşük Gürültü ($\sigma = 0.10$):** İterasyon limitinin $2$ veya $20$ olmasının bir etkisi olmamıştır. Kanal temiz olduğu için ilk iterasyonlarda kod çözülmüştür (Zamanlama: sabit $16.3$ ms/paket).
  * **Yüksek Gürültü ($\sigma = 0.25$):**
    * $max\_iter = 2$ iken Far User BLER değeri $\%2.00$ seviyesine çıkmıştır (2 iterasyon düzeltmeye yetmemiştir).
    * $max\_iter \ge 4$ yapıldığında BLER $\%0.10$'a düşmüştür.
    * İterasyon sayısının artması GNU Radio akış şemasında ek CPU gecikmesi yaratmamış, paket başına süre $16.31$ ms/paket seviyesinde sabit kalmıştır.
* **Grafik Çıktısı:** `tests/complexity_latency/complexity_latency_tradeoff.png` dosyasında kaydedilmiştir.

### 2.6 TEST 6: Jamming Güvenlik ve Dayanım Testi (PLS)
Aktif kısmi bant jammer ($\rho_J = 0.3$) varlığında Scrambler'ın sağladığı güvenlik koruması test edilmiştir.

* **Sayısal Bulgular:**
  * Bob alıcısı $12$ dB jammer gücüne kadar hiçbir hata göstermemiştir (BER: $\%0.00$, BLER: $\%0.00$).
  * $15$ dB jammer gücünde Bob BER oranı $\%0.40$ (User 1) ve $\%0.80$ (User 2) seviyesine çıkmıştır.
  * $18$ dB jammer gücünde jammer baskın gelmiş ve BER sırasıyla $\%12.70$ ve $\%23.90$ olmuştur.
  * **Gizlilik Sınırı:** Scrambler açık olduğu ve seed gizli tutulduğu sürece dinleyici (Eve), sinyal gücü ne kadar yüksek olursa olsun veriyi çözememiş ve BER oranı her zaman $\%50.00$ (Tam Belirsizlik) kalmıştır.
* **Grafik Çıktısı:** `tests/jamming/jamming_pls_security_gap.png` dosyasında "Security Gap" bölgesi ile birlikte çizdirilmiştir.

---

## 3. Akademik Değerlendirme ve Bitirme Tezi Çıkarımları
1. **Kanal Kodlaması Hayatidir:** PD-NOMA tekniği, kanal kodlaması (LDPC) olmadan tek başına Far User sinyalini girişim altında çözmekte başarısızdır. LDPC, sisteme mükemmel bir hata toleransı kazandırarak Far User BER değerini $\%50$'den $\%0.1$'e düşürür.
2. **Donanım Kusurlarına Karşı Duyarlılık:** Yüksek veri hızlarında çalışan alıcılarda donanımsal kusurların (RHI) kümülatif etkisi, kanal gürültüsü azalsa dahi sistemin sıfır BER'e ulaşmasını engelleyerek hata tabanına neden olmaktadır.
3. **Güvenlik ve Dayanıklılık:** Bit-seviyesinde uygulanan scrambler, NOMA'nın getirdiği açık hava yayılımı zafiyetlerini tamamen kapatarak eavesdropper (Eve) karşısında geniş bir *Security Gap* sağlar.
