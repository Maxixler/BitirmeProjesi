# BPSK NOMA Sistemi Detaylı Sistem Analizi ve Durum Raporu

Bu rapor, BPSK NOMA (Non-Orthogonal Multiple Access) sisteminin alıcı tarafındaki ardışık girişim giderimi (Successive Interference Cancellation - SIC) mekanizmasının mevcut durumunu, son yapılan değişikliklerin etkilerini, alıcı zincirindeki kilitlenme ve sızma (bleeding) sorunlarının matematiksel/fiziksel nedenlerini ve gelecekteki oturumlarda projeyi sıfır hata ile tamamlamak için uygulanması gereken net çözüm adımlarını içermektedir.

Bu belge, **konuşma bağlamı değiştiğinde veya yeni bir çalışma oturumuna geçildiğinde** sonraki aşamalara rehberlik edecek şekilde, kafada hiçbir soru işareti bırakmayacak açıklıkta hazırlanmıştır.

---

## 1. Sistem Parametreleri ve Temel Matematiksel Altyapı

Sistem, iki kullanıcılı bir güç bölgesi çoklamalı (Power-Domain NOMA) BPSK/DBPSK iletim hattıdır:

| Parametre | Değer / Açıklama | Matematiksel Karşılığı |
| :--- | :--- | :--- |
| **Kanal Çoklaması** | Power-Domain NOMA | $r(t) = s_{noma}(t) + n(t)$ |
| **User 1 (Strong/Near User)** | Güçlü kullanıcı sinyali | Genlik $a_1 = 0.894 \approx \frac{2}{\sqrt{5}}$ |
| **User 2 (Weak/Far User)** | Zayıf kullanıcı sinyali | Genlik $a_2 = 0.447 \approx \frac{1}{\sqrt{5}}$ |
| **Süperpoze Sinyal** | Toplam iletilen sinyal | $s_{noma}(t) = a_1 x_1(t) + a_2 x_2(t)$ |
| **Paket Yapısı (Sembol)** | Preamble + Header + Payload | $256 + 64 + 1296 = 1616$ sembol |
| **Preamble Deseni** | 32 Baytlık DBPSK Akümülasyonu | `[0xc0, 0xaf] * 15` dizisinin türevsel entegrali |

### Karar Sınırları ve SIC İlkesi
Alıcıda User 1 doğrudan demodüle edilir ve $\hat{x}_1(t)$ elde edilir. SIC bloğu, bu güçlü bileşeni toplam sinyalden çıkararak User 2'nin zayıf sinyalini yalnız bırakmayı amaçlar:
$$r_{clean}(t) = r(t) - a_1 \hat{x}_1(t) = a_2 x_2(t) + n(t) + a_1 (x_1(t) - \hat{x}_1(t))$$

Eğer $x_1(t) = \hat{x}_1(t)$ (hatasız kod çözme) ve zamanlama/faz mükemmel şekilde hizalanmışsa, User 1 girişimi sıfırlanır ve geriye sadece zayıf User 2 sinyali $a_2 x_2(t)$ kalır.

---

## 2. Son Yapılan Değişikliklerin Analizi ve Karşılaşılan Sorunlar

Son geliştirme aşamasında, blok kodunda `sic_aligner` (`gr.basic_block`) yerine **`dynamic_sic_sync_aligner` (`gr.sync_block`)** yapısına geçilmiştir. Bu yeni blok, canlı çapraz korelasyon (cross-correlation) ve anlık faz kalibrasyonu ile sinyalleri dinamik olarak eşleştirmeyi hedeflemektedir.

Yapılan detaylı kod ve akış analizine göre, bu yapı iki kritik mimari ve fiziksel sorun doğurmaktadır:

### ⚠️ Kritik Sorun 1: GNU Radio Zamanlayıcı Kilitlenmesi (Scheduler Deadlock)
* **Neden:** `dynamic_sic_sync_aligner` bloğu bir `gr.sync_block` olarak tanımlanmıştır. GNU Radio scheduler mimarisinde bir `sync_block`, her iki giriş portundan da (`in_rx` ve `in_tx1`) **tam olarak eşit sayıda sembol hazır bulunmadan** `work` fonksiyonunu tetiklemez.
* **Kilitlenme Döngüsü (Circular Dependency):** 
  1. `in_rx` portu, Costas Loop çıkışındaki doğrudan alınan ham sinyaldir (gecikmesizdir).
  2. `in_tx1` portu ise, User 1'in demodüle edilip LDPC çözücüsünden geçirilmesi, ardından CRC kontrolü yapılıp tekrar kodlanması ve modüle edilmesiyle oluşturulan **yeniden üretilmiş (reconstructed)** sinyaldir.
  3. Bu demodülasyon ve kod çözme işlemleri, doğası gereği en az **1 paketlik (1616 sembol) bir çerçeve gecikmesi** ve LDPC algoritmasının capillary iterasyon gecikmelerini barındırır.
  4. `sync_block` yapısı, `in_tx1` hattından veri gelmesini beklerken `in_rx` girişindeki verileri tüketmez (consume etmez). Ancak `in_tx1` hattı, `in_rx` verileri işlenip çözülmeden asla yeni veri üretemez.
  5. Bu durum **GNU Radio zamanlayıcısının tamamen kilitlenmesine (deadlock)** yol açar. Sonuç olarak akış durur ve `bpsk_receive_2.txt` (User 2 çıkışı) **0 bayt (tamamen boş)** kalır.
* **Orijinal Yapının Farkı:** Eski `sic_aligner` bloğu bir `gr.basic_block` idi. Girişleri birbirinden bağımsız olarak anında tüketir (`consume(0, n_rx)` ve `consume(1, n_tx1)`), bunları kendi iç tamponlarında (decoupled internal queues) saklar ve eşleştirmeyi bu bağımsız tamponlar üzerinde yapardı. Bu sayede geri besleme döngüsünün kilitlenmesini engelliyordu.

### ⚠️ Kritik Sorun 2: Korelasyon Penceresi ve Negatif Gecikmeler
* **Neden:** Yeni blokta canlı çapraz korelasyon şu şekilde hesaplanmaktadır:
  `corr = np.correlate(rx_chunk, tx1_chunk[:self.window], mode='valid')`
* **Sınırlılık:** `mode='valid'` kullanımı ve `search_window=64` arama sınırı, sadece `in_rx` sinyalinin `in_tx1` sinyaline göre *ileride* (pozitif gecikmeyle) olduğu durumları yakalayabilir. Eğer gecikme negatif yönlüyse (yani `in_tx1` sinyali demodülasyon zincirindeki kaymalardan ötürü `in_rx` tamponunun gerisinde kalmışsa) veya gecikme penceresi 64 sembolden büyükse, bu korelasyon en iyi hizalama ofsetini bulamaz ve hatalı kaydırma uygular.

---

## 3. Bilinen Sorunlar (Known Issues)

### 🔴 User 2 Çıkışına (`bpsk_receive_2.txt`) User 1 Verilerinin Sızması
* **Hatanın Tanımı:** Kilitlenme aşılsa veya eski tamponlu blok kullanılsa dahi, User 2 alıcı çıktısında kendi verisi olan azalan sayı dizisi (`9999...8888...`) yerine, güçlü olan User 1'in artan sayı dizisi (`0000...1111...`) veya bunun türevsel kalıntıları görünmektedir.
* **Fiziksel Neden (1-Sembol Hizalama Hatası):**
  Detaylı sinyal incelemelerinde, aradaki çıkarma işleminin tam **1 sembol kayık** yapıldığı saptanmıştır. Bu 1 sembollük uyuşmazlık nedeniyle çıkarma işlemi şu şekli alır:
  $$r_{clean}[t] = r[t] - a_1 x_1[t-1] = a_1 (x_1[t] - x_1[t-1]) + a_2 x_2[t] + n[t]$$
* **Girişim Baskınlığı:**
  User 1 genliği ($0.894$), User 2 genliğinin ($0.447$) tam **iki katıdır**. 1 sembol kayık yapılan çıkarmadan arta kalan User 1 girişim terimi ($a_1 \cdot \text{diff}(x_1)$), zayıf User 2 sinyalini ($a_2 x_2$) tamamen bastırır.
* **Karar Aşaması:**
  BPSK demodülatörü sıfır (0) eşiğine göre karar verdiğinden, User 2'nin soft-decision kod çözücüsü bu dominant User 1 kalıntısını kendi verisiymiş gibi algılar ve LDPC kod çözücü bu veriyi başarıyla çözerek User 2 dosyasına yazar. Sonuç olarak sinyal sızıntısı (signal bleeding) gerçekleşir.

---

## 4. Sorunsuz Geçiş İçin Net Çözüm Yol Haritası

Bir sonraki çalışma oturumunda veya farklı bir konuşma bağlamında, sistemi sıfır hata ile çalıştırmak için izlenmesi gereken adımlar şunlardır:

### Adım 1: Decoupled `basic_block` Yapısına Geri Dönüş
Zamanlayıcı kilitlenmesini (deadlock) çözmek için, `NOMA_epy_block_1.py` dosyası yedekteki `NOMA_epy_block_1.py.bak` içeriği kullanılarak yeniden decoupled `gr.basic_block` yapısına dönüştürülmelidir. Bu yapı:
* Gelen verileri anında `consume` ederek bloke olmayı önler.
* Bağımsız `buffer_rx` ve `buffer_tx1` kuyrukları yönetir.
* `pending_tags` ile korelasyon peak'lerini robust şekilde takip eder.

### Adım 2: Preamble ve Peak Hizalama Kaymasının (`shift`) Düzeltilmesi
Preamble korelasyon detektöründen gelen `time_est` tag'lerinin fiziksel ofseti ile payload'un gerçek başlangıcı arasındaki kayma tam olarak **`-16`** semboldür.
* `corr_est` bloğunun `mark_delay=16` parametresi nedeniyle, tetiklenen etiket gerçek preamble sonunun 16 sembol *ilerisindedir*:
  $$\text{T\_offset} = \text{Preamble\_end} + 16 \implies \text{Preamble\_end} = \text{T\_offset} - 16$$
* Header uzunluğu 64 sembol olduğundan, gerçek payload başlangıcı:
  $$\text{Payload\_start} = \text{Preamble\_end} + 64 = \text{T\_offset} - 16 + 64 = \text{T\_offset} + 48$$
* Blok kodunda payload başlangıcı şu şekilde hesaplanmaktadır:
  $$\text{Hesaplanan} = \text{T\_offset} + \text{header\_symbols} + \text{shift} = \text{T\_offset} + 64 + \text{shift}$$
* Bu iki değerin birbirine eşit olması için gereken matematiksel kayma:
  $$\text{T\_offset} + 64 + \text{shift} = \text{T\_offset} + 48 \implies \text{shift} = -16$$
* `NOMA_epy_block_1.py` dosyasındaki ilgili satır kalıcı olarak şu şekilde güncellenmelidir:
  ```python
  self.packet_starts.append(t_offset + self.header_symbols + (-16))
  ```

### Adım 3: Derleme ve Doğrulama
1. GRC üzerinden `NOMA.grc` derlenerek güncel python scripti `NOMA.py` oluşturulur:
   ```powershell
   C:\Users\Armagan\radioconda\Scripts\grcc.exe NOMA.grc
   ```
2. Sistem çalıştırılır ve çıkışlar kontrol edilir:
   * `bpsk_receive.txt` dosyasının **User 1 artan sayı dizisini (`0000...9999`)** içerdiği doğrulanır.
   * `bpsk_receive_2.txt` dosyasının **User 2 azalan sayı dizisini (`9999...0000`)** hatasız içerdiği ve hiçbir User 1 sızıntısı barındırmadığı doğrulanır.

---

Bu detaylı analiz ve çözüm yönergeleri, NOMA SIC sisteminin tüm kilit noktalarını ve arka planını aydınlatmaktadır. Sonraki oturumda bu adımlar uygulanarak süreç başarıyla tamamlanabilir.
