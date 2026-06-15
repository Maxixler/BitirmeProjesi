BPSK, Scrambler, LDPC ve Güç Alanı NOMA Tabanlı Fiziksel Katman Tasarımı İçin Test ve Doğrulama Metodolojisi El Kitabı
Bu kılavuz; İkili Faz Kaydırmalı Anahtarlama (BPSK), Karıştırıcı (Scrambler), Düşük Yoğunluklu Eşlik Denetimi (LDPC) kanal kodlaması ve Güç Alanı Dışı Çoklu Erişim (PD-NOMA) entegrasyonuna sahip bir fiziksel katman (PHY) tasarımının performansını akademik ve endüstriyel standartlara uygun olarak doğrulamak üzere tasarlanmış 6 temel test senaryosunun metodolojisini, matematiksel altyapısını ve adım adım koşum planını içermektedir.1
TEST 1: Mesafe Taraması Testi (Distance Sweep Test)
1. Amaç ve Kapsam
Bu testin amacı, PD-NOMA sisteminin temel çalışma prensibi olan "yakın-far etkisi" (near-far effect) sınırlarını dinamik mesafe değişimleri altında incelemektir.4 Yakın (Near User - UE1) ve uzak (Far User - UE2) kullanıcıların vericiye (Base Station - BS) olan mesafeleri taranarak, yol kaybı (path loss) modelleri altında sistemin kesinti olasılığı (Outage Probability) ve BER değişimleri analiz edilir.3
2. Metodoloji ve Kanal Modellemesi
Kullanıcıların mesafelerine bağlı olarak sinyal zayıflamasını modellemek için 3GPP standartlarıyla uyumlu Genelleştirilmiş Yol Kaybı ve sönümleme modelleri entegre edilir .
Yol Kaybı Formülü (Log-Distance Path Loss) :

Burada  verici ile alıcı arasındaki 3 boyutlu mesafeyi (),  referans mesafesini (1 m),  yol kaybı eksponentini ve  standart sapması  olan log-normal gölgelenme (shadowing) bileşenini temsil eder .
3D Mesafe Hesabı (3GPP TS 38.901 standardı) :

Burada  baz istasyonu yüksekliği,  ise kullanıcı terminali yüksekliğidir .
3. Test Parametreleri

Parametre
Değer / Aralık
Açıklama
Taramalı Mesafe (d_near)
1 - 50 m
Yakın kullanıcı (UE1) mesafe aralığı 3
Taramalı Mesafe (d_far)
10 - 300 m
Uzak kullanıcı (UE2) mesafe aralığı 3
Referans Mesafe (d0)
1 m
Yol kaybı referans mesafesi 5
Yol Kaybı Eksponenti (n)
2.0 (Free Space) - 3.5 (Urban NLOS)
Kanal ortamı zayıf değer katsayısı
Gölgelenme Standart Sapması
4 - 8 dB
Log-normal shadowing standart sapması
Fading Sönümleme Modeli
Rayleigh ve Rician (K = 4)
Küçük ölçekli sönümleme profili 6

4. Adım Adım Koşum Planı
Sabit bir toplam iletim gücü () ve gürültü varyansı () belirleyin.3
Yakın kullanıcı mesafesini  konumunda sabitleyin.3
Uzak kullanıcı mesafesini  değerinden  değerine kadar  adımlarla artırın.3
Her adımda Monte Carlo simülasyonu ile her iki kullanıcı için alınan sinyal gücünü, yol kaybı ve seçilen sönümleme (fading) profili üzerinden hesaplayın .
Alıcıda SIC işlemini uygulayarak her iki kullanıcının BER ve Kesinti Olasılığını (Outage Probability) hesaplayıp kaydedin.6
Aynı işlemi  değerini sabit tutup  değerini tarayarak tekrarlayın.3
Beklenen Grafik: X ekseninde "Uzak Kullanıcı Mesafesi (m)", Y ekseninde "Kesinti Olasılığı (Logaritmik)" olacak şekilde UE1 ve UE2 eğrilerini çıkarın .
TEST 2: BER & BLER Waterfall Testi (LDPC'li ve LDPC'siz)
1. Amaç ve Kapsam
Bu test; 3GPP TS 38.212 uyumlu LDPC kanal kodlamasının, BPSK modülasyonlu PD-NOMA sistemindeki hata düzeltme (FEC) kazancını objektif olarak ortaya koymayı amaçlar.1 LDPC'li ve LDPC'siz (kodsuz) sistem varyasyonları AWGN ve Rayleigh sönümlemeli kanallar altında karşılaştırılır .
2. Metodoloji ve Kodlama Altyapısı
LDPC Kodlama: 3GPP standardına uygun Base Graph 2 (BG2) ve  kaldırma (lifting) boyutları seçilir.11 İlk iki sistematik sütun standart uyarınca delinir (puncture) .
BPSK Soft Demapping (LLR Hesabı): Phase-scrambler etkisini de içeren BPSK yumuşak karar LLR (Log-Likelihood Ratio) formülü uygulanır 2:

Burada  ilgili kullanıcının atanmış gücü,  alınan sembol,  kanal kazancı ve  uygulanan faz karıştırma dizisidir.2
Performans Metrikleri:
Bit Hata Oranı (BER) 15: BER = Hatalı Bit Sayısı / Toplam İletilen Bit Sayısı
Blok Hata Oranı (BLER) 16: BLER = Hatalı Kod Sözcüğü Sayısı / Toplam İletilen Kod Sözcüğü Sayısı
3. Test Parametreleri

Parametre
Değer / Ayar
Açıklama
SNR Sweep Aralığı
-10 dB ile +25 dB
0.5 dB adımlarla Eb/N0 taraması 3
Kodsuz Varyasyon
BPSK + Scrambler + PD-NOMA
Karşılaştırma için temel baseline
Kodlu Varyasyon
LDPC + BPSK + Scrambler + PD-NOMA
Önerilen sistem mimarisi 1
LDPC Base Graph
Base Graph 2 (BG2)
Kısa paket ve düşük kod oranları için optimize yapısı 11
LDPC İterasyon Sayısı
10 (Sabit)
Kod çözücü maksimum iterasyon limiti
Kullanıcı Güç Oranları
a_near = 0.2, a_far = 0.8
PD-NOMA güç tahsis katsayıları 3

4. Adım Adım Koşum Planı
Rastgele veri bitleri üretin ve Scrambler işleminden geçirin .
Kodlu senaryo için LDPC matrisini oluşturup kodlama ve hız eşleştirme (rate matching) adımlarını tamamlayın .
BPSK modülasyonu uygulayıp güç katsayılarına göre süperpozisyon kodlaması (SC) ile sinyalleri birleştirin .
AWGN ve Rayleigh fading kanallarından geçirin.7
Alıcıda uzak kullanıcı sinyalini doğrudan çözüp (girişimi gürültü sayarak) ardından yakın kullanıcı için SIC uygulayarak de-superposition yapın .
Demapper çıkışında elde edilen LLR değerlerini LDPC kod çözücüye (SPA algoritması ile) gönderin .
Beklenen Grafik: X ekseninde "Eb/N0 (dB)", Y ekseninde logaritmik olarak "BER" ve "BLER" değerlerini gösteren waterfall (şelale) eğrilerini kodlu ve kodsuz durumlar için ayrı ayrı çizdirin.7
TEST 3: Kanal ve Donanımsal Kusurlar Testi (RHI, ipCSI ve ipSIC)
1. Amaç ve Kapsam
Bu test; sistemin kusursuz kanal durumu bilgisi (P-CSI) ve ideal donanım kabullerinden uzaklaştırılarak, gerçek RF alıcı-verici kısıtlamaları altındaki dayanıklılığını ölçmeyi amaçlar.3 Artık donanım kusurları (RHI), kusurlu kanal kestirimi (ipCSI) ve SIC sırasındaki hataların (ipSIC) kümülatif etkisi analiz edilir.9
2. Metodoloji ve Hata Modellemesi
Artık Donanım Kusurları (RHI) Modeli : Verici ve alıcıdaki faz gürültüsü, IQ dengesizliği ve amplifikatör doğrusal olmama durumları Gaussian distorsiyon gürültüsü olarak modellenir:

Burada  verici distorsiyonu,  ise alıcı distorsiyon gürültüsüdür.18 Donanım kusur seviyeleri  aralığındadır.9
Kusurlu Kanal Durumu Bilgisi (ipCSI) Modeli : MMSE kestiriminden kalan kanal hatası modellenir:

Burada  kanal kestirim hatası varyansıdır .
Kusurlu SIC (ipSIC) Modeli : Uzak kullanıcının sinyali iptal edilirken kalan artık girişim modellenir:

Burada  artık girişim (residual interference) katsayısıdır . ( ise mükemmel SIC 19).
3. Test Parametreleri

Parametre
Değer / Aralık
Açıklama
TX Donanım Kusuru (k_x)
0.05 ve 0.15
Verici distorsiyon katsayısı 9
RX Donanım Kusuru (v_y)
0.05 ve 0.15
Alıcı distorsiyon katsayısı 9
Kestirim Hatası Varyansı (sigma_e^2)
0.01 ile 0.1
ipCSI hata seviyesi
Artık Girişim Katsayısı (epsilon)
0.01, 0.05, 0.1
ipSIC hata seviyesi (residual SIC error)
Küçük Ölçekli Sönümleme
Nakagami-m (m = 3)
Genelleştirilmiş sönümleme kanalı

4. Adım Adım Koşum Planı
Belirlenen RHI katsayılarına göre verici distorsiyon sinyalini () süperpoze edilmiş NOMA sinyaline ekleyin.18
Sinyali Nakagami-m sönümlü kanaldan geçirin ve alıcı distorsiyon gürültüsünü () ekleyin.18
Alıcıda kanal kestirim hatasını simüle etmek üzere gerçek kanal matrisine  hata terimini ekleyerek  matrisini oluşturun.3
 kullanarak SIC işlemini yürütün ve uzak kullanıcıyı deşifre ederken oluşan hataların yakın kullanıcı demapping sürecine sızmasını ( oranında) formüle edin .
Beklenen Grafik: X ekseninde "Ortalama SNR (dB)", Y ekseninde "Kesinti Olasılığı" veya "BER" olacak şekilde; ideal durum (P-CSI, mükemmel SIC) ile donanım kusurlu durumları (RHI + ipCSI + ipSIC) yarıştırın.9 Yüksek SNR bölgelerinde oluşan "hata tabanı" (error floor) davranışını gözlemleyin .
TEST 4: Güç Paylaşım Taraması Testi (Power Allocation Sweep)
1. Amaç ve Kapsam
Güç alanı NOMA'da toplam iletim gütünün yakın ve uzak kullanıcılar arasında nasıl bölüştürüleceği hayati önem taşır . Bu testin amacı, uzak kullanıcının güç katsayısını () tarayarak, her iki kullanıcının BER dengesini optimize etmek ve sistemin adillik performansını (Jain's Fairness Index) ölçmektir.10
2. Metodoloji ve Adillik Analizi
Güç Katsayıları İlişkisi 3:

* Jain's Fairness Index Formülü :

Burada  kullanıcıların elde ettiği anlık veri hızları veya veri başarımlarıdır ( aralığındadır;  mükemmel adilliği gösterir) .
KKT ve Lagrange Sınır Analizi : Belirli bir minimum QoS (kalite) gereksinimini sağlayan optimum  değerleri Lagrange çarpanları metoduyla analiz edilir .
3. Test Parametreleri

Parametre
Değer / Aralık
Açıklama
Uzak Kullanıcı Güç Oranı (a_far)
0.51'den 0.99'a kadar
Taranacak güç bölüşüm adımları 3
Toplam İletim Gücü (PT)
Sabit (örneğin 1W veya 30 dBm)
Normalize edilmiş toplam güç 5
Hedef BER Eşiği
10^-3
Başarılı bağlantı için gereken QoS sınırı
Test Edilecek SNR Seviyeleri
10 dB, 20 dB, 30 dB
Farklı çalışma koşullarında güç optimizasyonu

4. Adım Adım Koşum Planı
 değerini  değerinden başlatarak  adımlarla  değerine kadar artırın (her adımda  hesaplayın).3
Her adımda BPSK-NOMA sembollerini oluşturup kanaldan geçirin ve alıcıda SIC uygulayın .
Her bir güç kombinasyonunda her iki kullanıcının BER değerlerini ve elde edilen veri hızlarını kaydedin .
Her adım için Jain's Fairness Index () değerini hesaplayın .
Ortak BER'i minimum kılan (Max-Min BER kriteri) ve adilliği maksimize eden optimum  noktasını bulun.22
Beklenen Grafik: X ekseninde "Uzak Kullanıcı Güç Atama Katsayısı ()", sol Y ekseninde "BER (Logaritmik)", sağ Y ekseninde ise "Jain's Fairness Index" olacak şekilde çift eksenli optimizasyon grafiğini oluşturun .
TEST 5: LDPC Karmaşıklık ve Zamanlama Ödünleşimi Testi
1. Amaç ve Kapsam
Bu test; donanımsal kısıtları simüle etmek amacıyla LDPC kod çözücünün iterasyon sayısı ve algoritma varyasyonlarının (SPA, MSA, NMSA vb.) işlem zamanı (execution time) ve hata düzeltme başarımı üzerindeki ödünleşimini (trade-off) ortaya koymayı amaçlar .
2. Metodoloji ve Algoritmalar
Karşılaştırılacak Kod Çözme Algoritmaları :
Sum-Product Algorithm (SPA): Near-optimal performans, yüksek karmaşıklık .
Min-Sum Algorithm (MSA): Düşük karmaşıklık, check node seviyesinde minimum yaklaşımı :

Normalized Min-Sum Algorithm (NMSA): MSA çıkışlarının bir  ölçekleme katsayısı ile optimize edilmesi .
Layered MSA (LMSA): Katmanlı mesaj iletimi ile yakınsama hızını 2 kat artırma .
Zamanlama Analizi : Her algoritmanın tek bir çerçeveyi çözmek için harcadığı CPU/GPU süresi mikrosaniye () veya milisaniye (ms) cinsinden ölçülür .
3. Test Parametreleri
Parametre
Değer / Aralık
Açıklama
Maksimum İterasyon Sayısı
2, 4, 8, 15, 20
Taranacak iterasyon limitleri
Normalizasyon Katsayısı (beta)
0.75 - 0.85
NMSA için optimize ölçekleme faktörü
Blok Uzunluğu (N)
1024 ve 4096 bit
Test edilecek LDPC çerçeve boyutları
Test Platformu
MATLAB / C++ / CUDA
CPU/GPU yürütme ortamı

4. Adım Adım Koşum Planı
Sabit bir Eb/N0 değerinde (örneğin 3 dB veya 5 dB) BPSK-NOMA LDPC kodlu veri blokları üretin .
Seçilen kod çözücü algoritmasını (örneğin SPA) aktif edin .
Kod çözücü maksimum iterasyon limitini () sırasıyla 2, 4, 8, 15, 20 olarak ayarlayarak kodu çalıştırın .
Her iterasyon limiti için işlemcinin harcadığı saf zamanı (execution time) yüksek hassasiyetli zamanlayıcılar (örneğin tic-toc veya chrono) ile ölçüp kaydedin .
Her konfigürasyon için elde edilen nihai BLER değerini hesaplayın .
Aynı adımları MSA, NMSA ve LMSA algoritmaları için tekrarlayın .
Beklenen Grafik: X ekseninde "Yürütme Süresi (ms / çerçeve)", Y ekseninde "BLER" olacak şekilde her algoritmanın performans-zaman eğrisini çıkararak donanımsal olarak en verimli çalışma noktasını belirleyin .
TEST 6: Jamming (Karıştırma) Güvenlik ve Dayanım Testi (PLS)
1. Amaç ve Kapsam
Bu test; aktif bir kısmi bant karıştırıcı (partial-band jammer) veya dinleyici (Eve) varlığında, vericide kullanılan bit seviyesindeki Scrambler ile LDPC kodunun sisteme kazandırdığı Fiziksel Katman Güvenliğini (Physical Layer Security - PLS) doğrulamayı amaçlar . Güvenlik düzeyi "Security Gap" () metriği üzerinden hesaplanır .
2. Metodoloji ve Güvenlik Analizi
Sistem Modeli (Gaussian Wiretap Channel) : Meşru alıcı (Bob) veriyi hatasız çözmeye çalışırken, eavesdropper (Eve) veriyi dinler .
Security Gap (S_g) Formülü :
$$S_g = \frac{E_b/N_0\rvert_{\text{Eve,max}}}{E_b/N_0\rvert_{\text{Bob,min}}}$$Desibel (dB) cinsinden ifadesi :

Burada , Bob'un veriyi güvenilir bir şekilde () çözebilmesi için gereken minimum SNR değeridir .  ise Eve'in veriyi deşifre edememesi (, tam karmaşa) için katlanabileceği maksimum SNR değeridir .
Scrambler Rolü : Scrambler devredeyken takımyıldız belirsizliği (ambiguity) artırılarak Eve'in demapper aşamasında LLR kilidini açması engellenir; böylece Security Gap daraltılır .
3. Test Parametreleri

Parametre
Değer / Ayar
Açıklama
Scrambler Durumu
Açık / Kapalı
Güvenlik etkisini ölçmek için temel anahtar
Güvenilirlik Sınırı (P_B_max)
BER <= 10^-5
Bob için hatasız iletişim eşiği
Gizlilik Sınırı (P_E_min)
BER >= 0.40
Eve için tam karmaşa/bilgi alamama eşiği
Karıştırıcı Sinyal Gücü (I_J)
0 dB ile 20 dB arası
Jammer parazit gücü seviyesi 24
Karıştırılan Bant Oranı (rho_J)
0.1 ile 0.5
Kısmi bant engelleme yüzdesi 24

4. Adım Adım Koşum Planı
Bilgi paketini oluşturun.15 İlk senaryoda Scrambler'ı kapatın, ikinci senaryoda ise Scrambler'ı (3GPP TS 38.211/38.212 uyumlu) aktif edin .
LDPC kodlu BPSK-NOMA sinyalini oluşturup Bob ve Eve kanallarına ayrı ayrı gönderin .
Kanallara belirlenen oranda () kısmi bant jammer gürültüsü ve AWGN ekleyin.24
Alıcı taraflarda (Bob ve Eve) çözülen bitlerin BER oranlarını SNR'a karşı hesaplayın .
Bob'un  değerine ulaştığı minimum SNR () ile Eve'in  sınırını koruyabildiği maksimum SNR () değerlerini tespit edin .
Her iki durum (Scrambler açık vs. kapalı) için desibel cinsinden Security Gap () genişliğini hesaplayın .
Beklenen Grafik: X ekseninde "SNR (dB)", Y ekseninde "BER (Logaritmik)" olacak şekilde Bob ve Eve eğrilerini çizin. Scrambler aktif edildiğinde Eve'in eğrisinin yüksek SNR seviyelerinde dahi nasıl  seviyesinde takılıp kalarak (error floor) Security Gap'i dramatik şekilde daralttığını ( seviyesinden  seviyesine indirdiğini) gözlemleyin .
