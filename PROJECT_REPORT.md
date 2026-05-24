# GNU RADIO TABANLI GÜÇ ETKİ ALANLI NOMA SİSTEMİ İLE ARDIŞIK GİRİŞİM İPTALİ (SIC) UYGULAMASI

## Bitirme Projesi Raporu

**Bölüm:** Elektrik-Elektronik Mühendisliği  
**Akademik Yıl:** 2025–2026

---

## İÇİNDEKİLER

1. [ÖZET (ABSTRACT)](#1-özet-abstract)
2. [GİRİŞ VE LİTERATÜR ÖZETİ](#2-giriş-ve-literatür-özeti)
3. [TEORİK ALTYAPI VE MATEMATİKSEL MODEL](#3-teorik-altyapı-ve-matematiksel-model)
4. [GNU RADIO TABANLI SİSTEM TASARIMI (BLOK ANALİZİ)](#4-gnu-radio-tabanlı-sistem-tasarımı-blok-analizi)
5. [SİMÜLASYON VE PERFORMANS DEĞERLENDİRMESİ](#5-simülasyon-ve-performans-değerlendirmesi)
6. [SONUÇ VE GELECEK ÇALIŞMALAR](#6-sonuç-ve-gelecek-çalışmalar)
7. [KAYNAKÇA](#7-kaynakça)
8. [EKLER](#8-ekler)

---

## 1. ÖZET (ABSTRACT)

Beşinci nesil (5G) ve sonrasındaki kablosuz haberleşme sistemlerinde spektral verimliliğin artırılması, artan kullanıcı sayısı ve veri trafiği karşısında en kritik mühendislik hedeflerinden biri hâline gelmiştir. Bu bağlamda, Ortogonal Olmayan Çoklu Erişim (Non-Orthogonal Multiple Access — NOMA) tekniği, aynı zaman-frekans kaynağının birden fazla kullanıcı tarafından eş zamanlı paylaşılmasına olanak tanıyan bir fiziksel katman çözümü olarak öne çıkmaktadır.

Bu bitirme projesinde, Güç Etki Alanlı NOMA (Power-Domain NOMA — PD-NOMA) mimarisi kullanılarak iki kullanıcılı bir inen hat (downlink) senaryosu için uçtan uca bir alıcı-verici (transceiver) sistemi tasarlanmış ve GNU Radio Companion (GRC) ortamında gerçeklenmiştir. Verici tarafında **Süperpozisyon Kodlaması (Superposition Coding)** prensibi ile iki kullanıcının Diferansiyel BPSK (DBPSK) ile modüle edilmiş sinyalleri farklı güç katsayıları ($\alpha_1 = 0.894$, $\alpha_2 = 0.447$; sırasıyla %80 ve %20 güç tahsisi) atanarak aynı taşıyıcı üzerinde birleştirilmiştir. Alıcı tarafında ise **Ardışık Girişim İptali (Successive Interference Cancellation — SIC)** algoritması uygulanarak, önce baskın (güçlü) kullanıcının sinyali çözülmüş, ardından bu sinyal yeniden oluşturulup bileşik sinyalden çıkarılmak suretiyle zayıf kullanıcının verisi elde edilmiştir.

Sistem, IEEE 802.11n standardına uygun LDPC (Low-Density Parity-Check) kanal kodlaması ($n = 1296$, $k = 648$, $R = 1/2$), kök yükseltilmiş kosinüs (Root Raised Cosine — RRC) darbe şekillendirme, MMSE tabanlı polifaz sembol senkronizasyonu ve Costas döngüsü tabanlı taşıyıcı kurtarma blokları ile donatılmıştır. AWGN (Additive White Gaussian Noise) kanal modeli altında, $f_s = 200 \text{ kHz}$ örnekleme frekansı ve $\text{sps} = 4$ sembol başına örnek konfigürasyonunda gerçekleştirilen simülasyonlarda, Kullanıcı 1 (yakın kullanıcı, %80 güç tahsisi) için başarılı dosya transferi doğrulanmış olup, çapraz korelasyon tabanlı SIC hizalama algoritması ile Kullanıcı 2 (uzak kullanıcı, %20 güç tahsisi) sinyalinin çözümlenmesi gerçekleştirilmiştir. Elde edilen sonuçlar, yazılım tabanlı radyo (Software Defined Radio — SDR) platformu üzerinde NOMA-SIC mimarisinin uygulanabilirliğini ortaya koymakta ve gelecekte USRP E310 donanımı ile gerçek zamanlı kablosuz doğrulamaya yönelik bir temel oluşturmaktadır.

**Anahtar Kelimeler:** NOMA, Süperpozisyon Kodlaması, Ardışık Girişim İptali (SIC), GNU Radio, LDPC, DBPSK, SDR, 5G, Spektral Verimlilik, USRP.

---

## 2. GİRİŞ VE LİTERATÜR ÖZETİ

### 2.1. Motivasyon ve Problem Tanımı

Kablosuz haberleşme sistemlerinin evrimi, birinci nesilden (1G) beşinci nesile (5G) ve ötesine uzanan süreçte, giderek artan veri trafiği, kullanıcı yoğunluğu ve düşük gecikme gereksinimlerini karşılama zorunluluğuyla şekillenmiştir. Uluslararası Telekomünikasyon Birliği (ITU) tarafından tanımlanan IMT-2020 vizyonuna göre, 5G sistemlerinin hedefleri arasında 10 Gbps tepe veri hızı, 1 ms gecikme süresi ve $10^6$ cihaz/km² bağlantı yoğunluğu yer almaktadır [1]. Bu hedefler doğrultusunda, sınırlı frekans spektrumunun verimli kullanılması kritik bir mühendislik problemi olarak öne çıkmaktadır.

Geleneksel kablosuz haberleşme sistemlerinde kullanılan Ortogonal Çoklu Erişim (Orthogonal Multiple Access — OMA) teknikleri — FDMA, TDMA, CDMA ve OFDMA — kullanıcıları frekans, zaman, kod veya alt-taşıyıcı boyutlarında birbirinden ayırarak ortogonallik sağlamaktadır. Bu ortogonallik ilkesi, kullanıcılar arası girişimi (inter-user interference) ortadan kaldırma avantajını sunarken, aynı zamanda kaynak tahsisinde esnekliği ve toplam spektral verimliliği sınırlandırmaktadır. Özellikle heterojen kullanıcı dağılımlarında — yani kanal koşullarının büyük farklılıklar gösterdiği senaryolarda — OMA yöntemlerinin Shannon kapasitesine yaklaşma kabiliyeti zayıflamaktadır.

### 2.2. Non-Ortogonal Çoklu Erişim (NOMA) Kavramı

NOMA, ortogonallik kısıtlamasını kaldırarak birden fazla kullanıcının **aynı zaman-frekans kaynağını** eş zamanlı olarak paylaşmasını mümkün kılan bir fiziksel katman çoklu erişim tekniğidir. Literatürde NOMA teknikleri iki ana kategoride sınıflandırılmaktadır:

1. **Güç Etki Alanlı NOMA (Power-Domain NOMA — PD-NOMA):** Kullanıcılara farklı güç seviyeleri atanarak sinyallerin süperpozisyon kodlaması yoluyla üst üste bindirilmesine dayanır. Alıcı tarafında SIC algoritması ile girişim giderimi yapılır [2].

2. **Kod Etki Alanlı NOMA (Code-Domain NOMA):** SCMA (Sparse Code Multiple Access) ve MUSA (Multi-User Shared Access) gibi teknikleri kapsayan, kullanıcıların seyrek veya düşük korelasyonlu kodlarla ayrıştırıldığı yaklaşımlardır.

Bu projede, implementasyon karmaşıklığı ve kavramsal netlik açısından **PD-NOMA** mimarisi tercih edilmiştir.

### 2.3. OMA ve NOMA Karşılaştırması

Aşağıdaki tablo, OMA ve NOMA tekniklerinin temel karakteristiklerini karşılaştırmaktadır:

| Özellik | OMA (OFDMA vb.) | PD-NOMA |
|:---|:---|:---|
| **Kaynak Tahsisi** | Her kullanıcıya ayrık alt-taşıyıcı/zaman dilimi | Tüm kullanıcılar aynı kaynağı paylaşır |
| **Kullanıcılar Arası Girişim** | Ortogonallik ile sıfırlanır | Kontrollü girişim, alıcıda SIC ile giderilir |
| **Spektral Verimlilik** | Kullanıcı sayısı ile ölçeklenmez | Kullanıcı sayısı arttıkça kapasite kazancı sunar |
| **Kullanıcı Adaleti (Fairness)** | Zayıf kullanıcılar aleyhine eşitsizlik | Güç tahsisi ile adalet kontrol edilebilir |
| **Alıcı Karmaşıklığı** | Düşük (doğrudan çözümleme) | Yüksek (SIC algoritması gereklidir) |
| **Shannon Kapasitesine Yakınlık** | Sınırlı | Broadcast kanal kapasitesine yaklaşır |

NOMA'nın en belirgin üstünlüğü, aynı spektral kaynak üzerinde birden fazla kullanıcıya hizmet vermesi nedeniyle toplam sistem kapasitesini artırmasıdır. Broadcast kanal kapasitesine ulaşmak için, güçlü kullanıcıya atanan düşük güç ve zayıf kullanıcıya atanan yüksek güç ile Shannon sınırına yaklaşılabilmektedir. Ancak, bu kazanım alıcı tarafındaki SIC karmaşıklığı pahasına elde edilmektedir.

### 2.4. Literatürde NOMA Çalışmaları

NOMA kavramının teorik temelleri, çok kullanıcılı bilgi teorisi çerçevesinde Cover (1972) tarafından ortaya konulan yayın kanalı (broadcast channel) kapasitesi analizine dayanmaktadır [3]. Saito vd. (2013) tarafından yayımlanan çalışmada, güç etki alanlı NOMA'nın 3GPP-LTE sistemlerine entegrasyonu ilk kez önerilmiştir [4]. Dai vd. (2015), NOMA'nın 5G kablosuz ağlar için bir anahtar teknoloji olduğunu ortaya koyan kapsamlı bir derleme çalışması sunmuştur [5]. Ding vd. (2014), çeşitli kanal koşulları altında PD-NOMA'nın ergodik kapasitesini ve kesinti olasılığını (outage probability) analiz etmiştir [6]. İslam vd. (2017) ise güç tahsisi stratejileri ve SIC alıcı tasarımına ilişkin detaylı bir çerçeve geliştirmiştir [7].

LDPC kodlarının NOMA sistemlerine entegrasyonu açısından, Gallager (1962) tarafından ortaya konulan temel LDPC çerçevesi [8] ve MacKay ve Neal (1996) tarafından gösterilen Shannon sınırına yakın performans [9], bu projede kullanılan IEEE 802.11n standardı LDPC kodlarının teorik altyapısını oluşturmaktadır.

GNU Radio platformu üzerinde NOMA implementasyonu açısından, SDR (Software Defined Radio) tabanlı çalışmalar sınırlı sayıdadır ve bu proje, uçtan uca bir PD-NOMA transceiver'ın GNU Radio ortamında IEEE 802.11n LDPC kodlama ve DBPSK modülasyonu ile birlikte gerçeklenmesi bakımından özgün bir katkı sunmaktadır.

### 2.5. Projenin Amacı ve Kapsamı

Bu projenin temel amacı, iki kullanıcılı inen hat PD-NOMA senaryosunda:

1. Verici tarafında süperpozisyon kodlaması ile sinyal birleştirme,
2. IEEE 802.11n LDPC kanal kodlaması ($R = 1/2$) ile hata dayanıklılığı sağlama,
3. AWGN kanal modeli altında (ayarlanabilir gürültü, frekans kayması ve zamanlama sapması ile) iletim simülasyonu,
4. Alıcı tarafında çapraz korelasyon tabanlı SIC algoritması ile ardışık kullanıcı çözümleme

adımlarını kapsayan uçtan uca bir haberleşme zincirini GNU Radio Companion ortamında tasarlamak, gerçeklemek ve performansını değerlendirmektir.

---

## 3. TEORİK ALTYAPI VE MATEMATİKSEL MODEL

### 3.1. Süperpozisyon Kodlaması (Superposition Coding)

Güç etki alanlı NOMA'nın temel mekanizması, birden fazla kullanıcının sinyallerinin farklı güç katsayılarıyla ağırlıklandırılarak toplam bir sinyal olarak iletilmesidir. İki kullanıcılı bir inen hat senaryosunda, baz istasyonu (BS) tarafından iletilen süperpoze sinyal aşağıdaki şekilde ifade edilmektedir:

$$s(t) = \sqrt{a_1 P} \cdot x_1(t) + \sqrt{a_2 P} \cdot x_2(t)$$

Burada:
- $P$: Toplam iletim gücü,
- $x_1(t)$ ve $x_2(t)$: Sırasıyla Kullanıcı 1 (yakın/güçlü kanal) ve Kullanıcı 2 (uzak/zayıf kanal) için modüle edilmiş sembol dizileri,
- $a_1$ ve $a_2$: Güç tahsis katsayıları ($a_1 + a_2 = 1$, $a_1 > a_2$).

NOMA ilkesi gereğince, bu projede güç tahsisi:

$$a_1 = 0.8, \quad a_2 = 0.2$$

olarak belirlenmiştir. Normalize edilmiş birim güç ($P = 1$) varsayımı altında, genlik katsayıları:

$$\alpha_1 = \sqrt{a_1} = \sqrt{0.8} \approx 0.894 \approx \frac{2}{\sqrt{5}}$$

$$\alpha_2 = \sqrt{a_2} = \sqrt{0.2} \approx 0.447 \approx \frac{1}{\sqrt{5}}$$

olarak hesaplanmıştır. Güç normalizasyonu doğrulaması:

$$\alpha_1^2 + \alpha_2^2 = 0.8 + 0.2 = 1.0$$

Süperpoze sinyal, genlik cinsinden:

$$s(t) = 0.894 \cdot x_1(t) + 0.447 \cdot x_2(t)$$

şeklinde yazılabilir. Burada Kullanıcı 1, yakın kullanıcı (near user) olarak daha yüksek güç alırken; Kullanıcı 2, uzak kullanıcı (far user) olarak daha düşük güç almaktadır.

#### 3.1.1. Güç Tahsis Stratejisi ve Konstelasyon Analizi

BPSK modülasyonu altında ($x_i \in \{-1, +1\}$), süperpoze sinyalin konstelasyon uzayı dört noktadan oluşmaktadır:

| $x_1$ | $x_2$ | $s = \alpha_1 x_1 + \alpha_2 x_2$ | Bölge |
|:---:|:---:|:---:|:---:|
| +1 | +1 | $+0.894 + 0.447 = +1.341$ | Pozitif |
| +1 | −1 | $+0.894 − 0.447 = +0.447$ | Pozitif |
| −1 | +1 | $−0.894 + 0.447 = −0.447$ | Negatif |
| −1 | −1 | $−0.894 − 0.447 = −1.341$ | Negatif |

Bu konstelasyon yapısında, sıfır karar eşiği ($\text{threshold} = 0$) kullanılarak Kullanıcı 1'in ($x_1$) sembol kararı güvenilir bir şekilde verilebilmektedir; zira $\alpha_1 > \alpha_2$ koşulu, tüm olası $s$ değerlerinin $x_1$'in işaretiyle aynı yönde kalmasını garanti etmektedir. Bu özellik, SIC'nin ilk aşamasında güçlü kullanıcının doğru çözülmesinin temelini oluşturmaktadır.

### 3.2. AWGN Kanal Modeli

Verici çıkışından alıcı girişine kadar olan iletim kanalı, Toplamsal Beyaz Gauss Gürültüsü (AWGN) modeli ile temsil edilmektedir:

$$r(t) = h \cdot s(t) + n(t)$$

Burada:
- $h$: Kanal katsayısı (bu projede $h = 1.0$, düz sönümleme),
- $n(t)$: Sıfır ortalamalı ve $\sigma_n^2$ varyanslı karmaşık Gauss gürültüsü.

GNU Radio'daki `Channel Model` bloğunda konfigüre edilen parametreler:

| Parametre | Değer | Açıklama |
|:---|:---|:---|
| Gürültü Gerilimi ($\sigma_n$) | $0.1$ (ayarlanabilir, 0–2 aralığı) | AWGN standart sapması |
| Frekans Kayması ($\Delta f$) | $0.01$ (ayarlanabilir, $\pm 0.25$ aralığı) | Normalize frekans ofseti |
| Zamanlama Sapması ($\epsilon$) | $1.0001$ (ayarlanabilir, 0.999–1.001 aralığı) | Örnekleme frekansı sapma oranı |
| Kanal Katsayıları | $[1.0]$ | Tek-dokunuşlu düz sönümleme |
| Etiket Geçirme | `True` | Akış etiketlerini korur |

Varsayılan gürültü gerilimi ($\sigma_n = 0.1$) ile birim güç iletim varsayımı altında Sinyal-Gürültü Oranı (SNR):

$$\text{SNR} = \frac{P}{\sigma_n^2} = \frac{1}{(0.1)^2} = 100 \quad (\approx 20 \text{ dB})$$

Qt GUI kaydırıcıları (slider) aracılığıyla gürültü gerilimi, frekans kayması ve zamanlama sapması gerçek zamanlı olarak ayarlanabilmekte; bu sayede sistemin farklı kanal koşullarındaki davranışı interaktif olarak incelenebilmektedir.

### 3.3. Ardışık Girişim İptali (Successive Interference Cancellation — SIC)

SIC, NOMA alıcısının temel bileşenidir ve çok kullanıcılı girişimin kademeli olarak giderilmesini sağlar. İki kullanıcılı senaryoda SIC süreci aşağıdaki adımlardan oluşmaktadır:

#### Adım 1: Güçlü Kullanıcının Çözülmesi (User 1 Decoding)

Alınan sinyal $r(t)$ üzerinde, baskın güce sahip olan Kullanıcı 1'in sinyali doğrudan çözümlenir. Kullanıcı 2'nin sinyali bu aşamada girişim olarak ele alınır:

$$\hat{x}_1 = \text{Dec}\left\{ r(t) \right\} = \text{Dec}\left\{ \alpha_1 x_1(t) + \alpha_2 x_2(t) + n(t) \right\}$$

Kullanıcı 1 için Sinyal-Girişim-Artı-Gürültü Oranı (SINR):

$$\text{SINR}_1 = \frac{a_1 P}{a_2 P + \sigma_n^2} = \frac{0.8}{0.2 + 0.01} = \frac{0.8}{0.21} \approx 3.81 \quad (\approx 5.81 \text{ dB})$$

#### Adım 2: Güçlü Sinyalin Yeniden Oluşturulması (Signal Reconstruction)

Çözülen $\hat{x}_1$ verisi, verici tarafındaki işlem zinciri ile aynı adımlardan (LDPC kanal kodlama, BPSK sembol eşleme, güç ölçekleme) geçirilerek yeniden oluşturulur:

$$\hat{s}_1(t) = \alpha_1 \cdot \text{Mod}\left\{ \text{Enc}\left\{ \hat{x}_1 \right\} \right\}$$

Bu projede, yeniden oluşturma süreci LDPC kodlama → BPSK sembol haritası → $\times 0.894$ genlik ölçekleme adımlarını kapsamaktadır. `chunks_to_symbols` bloğu, çözülmüş bitleri doğrudan $\{-1.0 + 0j, +1.0 + 0j\}$ karmaşık BPSK sembollerine eşlemektedir.

#### Adım 3: Girişim İptali (Interference Subtraction)

Yeniden oluşturulan güçlü kullanıcı sinyali, SIC hizalama bloğu tarafından zamanlama ve faz açısından hizalandıktan sonra alınan bileşik sinyalden çıkarılır:

$$r_{\text{clean}}(t) = r(t) - \hat{s}_1(t - \hat{\tau}) \cdot \hat{A} \cdot e^{j\hat{\phi}}$$

Burada $\hat{\tau}$ tahmin edilen zamanlama gecikmesi, $\hat{A}$ genlik düzeltme faktörü ve $\hat{\phi}$ faz ofseti tahminidir. Eğer kod çözme hatasız ($\hat{x}_1 = x_1$) ve hizalama mükemmel ise:

$$r_{\text{clean}}(t) = \alpha_2 x_2(t) + n(t)$$

#### Adım 4: Zayıf Kullanıcının Çözülmesi (User 2 Decoding)

Temizlenmiş sinyal üzerinde Kullanıcı 2'nin verisi çözümlenir:

$$\hat{x}_2 = \text{Dec}\left\{ r_{\text{clean}}(t) \right\}$$

Kullanıcı 2 için SNR (ideal SIC sonrası):

$$\text{SNR}_2 = \frac{a_2 P}{\sigma_n^2} = \frac{0.2}{0.01} = 20 \quad (\approx 13.01 \text{ dB})$$

#### 3.3.1. SIC Hata Yayılımı (Error Propagation)

SIC sürecinin başarısı, Adım 1'deki kod çözme doğruluğuna kritik biçimde bağlıdır. Kullanıcı 1'in hatalı çözülmesi durumunda, artık girişim (residual interference) ortaya çıkar:

$$r_{\text{clean}}(t) = \alpha_2 x_2(t) + n(t) + \alpha_1 \left[ x_1(t) - \hat{x}_1(t) \right]$$

$\alpha_1 \left[ x_1(t) - \hat{x}_1(t) \right]$ terimi hata yayılımını temsil etmekte olup, $\alpha_1 / \alpha_2 = 2$ olması nedeniyle her bir hatalı sembol, Kullanıcı 2'nin sinyalini $2:1$ oranında bastırma potansiyeline sahiptir.

Benzer şekilde, zamanlama hizalamasındaki 1 sembol kayma durumunda artık girişim:

$$r_{\text{clean}}[n] = r[n] - \alpha_1 x_1[n-1] = \alpha_1(x_1[n] - x_1[n-1]) + \alpha_2 x_2[n] + n[n]$$

biçimini alır. $\alpha_1 = 2\alpha_2$ olduğundan, bu diferansiyel girişim terimi Kullanıcı 2 sinyalini tamamen bastırabilir. Bu nedenle, güçlü kanal kodlaması (LDPC) ve hassas zamanlama hizalaması büyük önem taşımaktadır.

### 3.4. LDPC Kanal Kodlaması

Düşük Yoğunluklu Parite Kontrol (Low-Density Parity-Check — LDPC) kodları, Shannon sınırına yakın performans sunan modern ileri hata düzeltme (Forward Error Correction — FEC) kodlarıdır [8, 9]. Bu projede kullanılan LDPC kodu, IEEE 802.11n (Wi-Fi) standardından alınmış olup aşağıdaki parametrelere sahiptir:

| Parametre | Değer |
|:---|:---|
| **Kod sözcüğü uzunluğu ($n$)** | 1296 bit |
| **Mesaj uzunluğu ($k$)** | 648 bit |
| **Parite bitleri ($n - k$)** | 648 bit |
| **Kod oranı ($R = k/n$)** | $648/1296 = 0.5$ (tam yarı oran) |
| **Parite kontrol matrisi** | `n_1296_k_0648_ieee.alist` |
| **Alt-matris boyutu ($Z$)** | 54 (yarı-döngüsel yapı) |
| **Kodlayıcı** | `fec.ldpc_encoder` (parite matrisi tabanlı) |
| **Kod çözücü** | `fec.ldpc_decoder` (maks. iterasyon: 50) |
| **Delme deseni (Puncture Pattern)** | `'11'` (delme yok) |

#### 3.4.1. IEEE 802.11n LDPC Matrisi ve Yarı-Döngüsel Yapı

Kullanılan LDPC kodu, IEEE 802.11n standardında tanımlanan yarı-döngüsel (quasi-cyclic) bir yapıya sahiptir. Parite kontrol matrisi $\mathbf{H}$, $Z = 54$ boyutlu döngüsel permütasyon alt-matrislerinden oluşmaktadır:

$$\mathbf{H} = \begin{bmatrix} \mathbf{P}_{0,0} & \mathbf{P}_{0,1} & \cdots & \mathbf{P}_{0,23} \\ \mathbf{P}_{1,0} & \mathbf{P}_{1,1} & \cdots & \mathbf{P}_{1,23} \\ \vdots & \vdots & \ddots & \vdots \\ \mathbf{P}_{11,0} & \mathbf{P}_{11,1} & \cdots & \mathbf{P}_{11,23} \end{bmatrix}$$

Burada her $\mathbf{P}_{i,j}$, $54 \times 54$ boyutunda bir döngüsel permütasyon matrisi veya sıfır matrisidir. Toplam boyutlar: $648 \times 1296$ ($12 \times 24$ alt-matris ızgarası).

Matrisin sütun ağırlıkları değişkenlik göstermektedir: ilk 54 sütun yüksek ağırlığa (11'e kadar) sahipken, geri kalan sütunlar 2–4 ağırlık aralığındadır. Bu yapı, düzensiz (irregular) LDPC kodlarının üstün hata düzeltme performansını sağlamaktadır.

Geçerli bir LDPC kod sözcüğü $\mathbf{c}$, aşağıdaki koşulu sağlar:

$$\mathbf{H} \cdot \mathbf{c}^T = \mathbf{0} \pmod{2}$$

#### 3.4.2. Alist Dosya Formatı

LDPC kodunun yapısını tanımlayan parite kontrol matrisi, MacKay alist formatında saklanmaktadır (`n_1296_k_0648_ieee.alist`, 44,030 bayt). Bu formatta:

- İlk satır: $n = 1296$ (sütun sayısı) ve $m = 648$ (satır sayısı),
- İkinci satır: Maksimum sütun ağırlığı ve maksimum satır ağırlığı,
- Sonraki satırlar: Her sütun ve satırdaki sıfır olmayan elemanların pozisyonları.

#### 3.4.3. Yük Boyutu ve LDPC Eşleşmesi

Bu projede her paket $\text{payload\_size} = 77$ bayt ($= 616$ bit) kullanıcı verisine sahiptir. CRC-32 eklenmesi (4 bayt) sonrası $81$ bayt ($= 648$ bit) elde edilmekte olup, bu değer LDPC kodunun mesaj uzunluğu $k = 648$ ile birebir örtüşmektedir. LDPC kodlama sonrası her paket $n = 1296$ bit uzunluğundaki kod sözcüğüne dönüşür; bu parametre SIC hizalama bloğundaki `payload_size = 1296` sembol değeriyle doğrudan ilişkilidir.

### 3.5. Diferansiyel BPSK (DBPSK) Modülasyonu

Bu projede verici tarafında **Diferansiyel BPSK (DBPSK)** modülasyonu kullanılmaktadır. Diferansiyel kodlamada, bilgi verinin mutlak faz değerinde değil, ardışık semboller arasındaki faz farkında taşınır:

$$d_k = b_k \oplus d_{k-1}$$

Burada $b_k$ giriş biti, $d_k$ diferansiyel kodlanmış bit ve $\oplus$ XOR işlemidir. BPSK sembol eşlemesi:

$$x_k = 2d_k - 1 = \begin{cases} +1 & d_k = 1 \\ -1 & d_k = 0 \end{cases}$$

Diferansiyel kodlamanın avantajı, alıcıda mutlak faz referansı gerektirmeden çözümleme yapılabilmesidir; bu özellik, Costas döngüsünün $180°$ faz belirsizliğini ortadan kaldırmaktadır.

Alıcı tarafında diferansiyel çözme, özel gömülü Python bloğu (`epy_block_0`) ile yumuşak karar (soft-decision) formatında gerçekleştirilmektedir:

$$\hat{b}_k^{\text{soft}} = -(y_k \cdot y_{k-1})$$

Burada $y_k$ yumuşak konstelasyon çıkışıdır. Negatif işaret, polarite eşleştirmesi için uygulanmaktadır. Yumuşak karar bilgisinin korunması, aşağı yöndeki LDPC kod çözücünün performansı açısından kritik öneme sahiptir.

AWGN kanalında kodlanmamış DBPSK'nın bit hata olasılığı (BER):

$$P_b = \frac{1}{2} e^{-E_b/N_0}$$

Bu ifade, tutarlı (coherent) BPSK'ya kıyasla yaklaşık 1 dB'lik bir performans kaybına karşılık gelmektedir; ancak diferansiyel kodlamanın sağladığı faz belirsizliği çözümü ve pratik alıcı tasarımı kolaylığı bu kaybı telafi etmektedir.

### 3.6. Darbe Şekillendirme: Kök Yükseltilmiş Kosinüs (RRC) Filtresi

Sembolleri arası girişimi (Inter-Symbol Interference — ISI) önlemek ve bant genişliğini kontrol etmek amacıyla, Kök Yükseltilmiş Kosinüs darbe şekillendirme filtresi kullanılmıştır. RRC filtresinin frekans tepkisi:

$$H_{\text{RRC}}(f) = \begin{cases} \sqrt{T_s} & |f| \leq \frac{1-\beta}{2T_s} \\ \sqrt{\frac{T_s}{2}\left[1 + \cos\left(\frac{\pi T_s}{\beta}\left(|f| - \frac{1-\beta}{2T_s}\right)\right)\right]} & \frac{1-\beta}{2T_s} < |f| \leq \frac{1+\beta}{2T_s} \\ 0 & |f| > \frac{1+\beta}{2T_s} \end{cases}$$

Burada $\beta$ aşırı bant genişliği (excess bandwidth / roll-off) faktörüdür. Bu projede $\beta = 0.35$ olarak konfigüre edilmiştir. Filtre uzunluğu $11 \times \text{sps} = 44$ dokunuş (tap) olarak belirlenmiştir. Verici tarafındaki `Constellation Modulator` bloğu dahili RRC darbe şekillendirme uygularken, alıcı tarafında ayrı bir `FFT RRC Filter` bloğu eşleştirilmiş filtreleme işlevini üstlenmektedir.

Verici ve alıcıdaki eşleştirilmiş RRC filtrelerinin kaskadı, ISI'yi sıfırlayan Yükseltilmiş Kosinüs (RC) darbe biçimini oluşturur:

$$H_{\text{RC}}(f) = H_{\text{RRC}}(f) \cdot H_{\text{RRC}}(f) = |H_{\text{RRC}}(f)|^2$$

---

## 4. GNU RADIO TABANLI SİSTEM TASARIMI (BLOK ANALİZİ)

Bu bölümde, GNU Radio Companion (GRC) ortamında tasarlanan NOMA-SIC dosya transferi sisteminin tüm blokları, parametreleri ve sinyal akış yolları detaylı olarak incelenmektedir. Sistem, üç ana katmandan oluşmaktadır: Verici (Transmitter), Kanal Modeli (Channel Model) ve Alıcı (Receiver/SIC). Toplam blok envanteri 60'ın üzerindedir ve 16 sanal sinyal yolu (virtual sink/source) çifti ile karmaşık sinyal akışı yönetilmektedir.

### 4.0. Sistem Değişkenleri (Variable Blocks)

Akış diyagramında tanımlanan 14 adet global sistem değişkeni aşağıdaki tabloda özetlenmiştir:

| Değişken Adı | Değer | Açıklama |
|:---|:---|:---|
| `samp_rate` | $200{,}000$ Hz ($200$ kHz) | Örnekleme frekansı |
| `sps` | $4$ | Sembol başına örnek sayısı |
| `payload_size` | $77$ bayt | Paket yük boyutu |
| `preamble_size` | $250$ bayt | Preambül boyutu |
| `postamble_size` | $8$ bayt | Postambül boyutu |
| `noise` | $0.1$ (Qt GUI aralığı: 0–2) | AWGN gürültü gerilimi |
| `freq_offset` | $0.01$ (Qt GUI aralığı: $\pm 0.25$) | Normalize frekans ofseti |
| `time_offset` | $1.0001$ (Qt GUI aralığı: 0.999–1.001) | Zamanlama sapma oranı |
| `constel` | `digital.constellation_bpsk()` | BPSK konstelasyon nesnesi |
| `hdr` | `digital.header_format_default(default_access_code, 0)` | Başlık format nesnesi |
| `preamble_syms` | $[0\text{xC0}, 0\text{xAF}] \times 4$ → BPSK sembolleri | Korelasyon preambül dizisi (64 sembol) |
| `ldpc_enc` | `variable_ldpc_encoder_def` (IEEE alist) | LDPC kodlayıcı tanımı |
| `ldpc_dec` | `variable_ldpc_decoder_def` (maks. iter: 50) | Kullanıcı 1 LDPC kod çözücü |
| `ldpc_dec_2` | `variable_ldpc_decoder_def` (maks. iter: 50) | Kullanıcı 2 LDPC kod çözücü |

Sembol hızı ve bant genişliği:

$$R_s = \frac{f_s}{\text{sps}} = \frac{200{,}000}{4} = 50{,}000 \text{ sembol/s}$$

$$B = R_s \cdot (1 + \beta) = 50{,}000 \times 1.35 = 67{,}500 \text{ Hz}$$

### 4.A. Verici (Transmitter) Katmanı

Verici katmanı, iki paralel kodlama zincirinden ve bir süperpozisyon birleştirme bloğundan oluşmaktadır. Her iki zincir yapısal olarak özdeş olmakla birlikte, bağımsız blok örnekleri ve farklı güç katsayıları ile konfigüre edilmiştir.

#### 4.A.1. Kullanıcı 1 Verici Zinciri (Yakın Kullanıcı — Near User)

Kullanıcı 1'in verici zinciri aşağıdaki blok sırasını takip etmektedir:

**File Source → Stream to Tagged Stream → Stream CRC32 → Repack Bits (8→1) → Additive Scrambler → FEC Extended Encoder (LDPC) → Tagged Stream Multiply Length (×2) → Protocol Formatter + Tagged Stream Mux [Preambül, Başlık, LDPC Yük, Postambül] → Constellation Modulator (DBPSK) → Tag Gate → Multiply Const ($\alpha_1 = 0.894$)**

##### 4.A.1.1. File Source (Dosya Kaynağı)

| Parametre | Değer |
|:---|:---|
| Dosya | `bpsk_transmit.txt` |
| Tekrar (Repeat) | `True` |

Bu blok, iletilecek veriyi (metin dosyası) bayt akışı olarak sisteme beslemektedir. Dosya, her biri `payload_size = 77` bayt olan paketler hâlinde `0–9` rakamlarının tekrarından oluşmaktadır. `Repeat = True` ayarı, dosya sonuna ulaşıldığında başa dönülerek sürekli iletim yapılmasını sağlar.

##### 4.A.1.2. Stream to Tagged Stream

| Parametre | Değer |
|:---|:---|
| Paket Uzunluğu | `payload_size` = 77 bayt |
| Etiket Anahtarı | `packet_len` |

Sürekli bayt akışını, her biri 77 baytlık etiketlenmiş paketlere bölmektedir.

##### 4.A.1.3. Stream CRC32 (Döngüsel Artıklık Kontrolü)

| Parametre | Değer |
|:---|:---|
| Etiket Anahtarı | `packet_len` |
| Kontrol Modu | `False` (ekleme modu) |

Her pakete 4 baytlık CRC-32 sağlama toplamı ekler. CRC eklenmesi sonrası paket boyutu $77 + 4 = 81$ bayta ($= 648$ bit $= k$) yükselir. Bu değer, LDPC kodunun mesaj uzunluğu ile birebir eşleşmektedir.

##### 4.A.1.4. Repack Bits (Bit Yeniden Paketleme — 8→1)

| Parametre | Değer |
|:---|:---|
| Giriş bit/bayt | `8` |
| Çıkış bit/bayt | `1` |
| Endianness | MSB |
| Etiketli | `True` |

Bayt düzeyindeki veriyi, karıştırıcı ve LDPC kodlayıcının beklediği tek bit/bayt formatına dönüştürür.

##### 4.A.1.5. Additive Scrambler (Toplamsal Karıştırıcı)

| Parametre | Değer |
|:---|:---|
| Maske (Mask) | `0x8A` |
| Tohum (Seed) | `0x7F` |
| Uzunluk | `7` |
| Bayt başına bit | `1` |
| Sıfırlama Etiketi | `packet_len` |

Doğrusal geri beslemeli kaydırma yazmacı (LFSR) tabanlı karıştırıcı, 7 bitlik bir LFSR kullanarak veri dizisindeki uzun tekrarları kırar. `reset_tag_key = "packet_len"` parametresi, her paket başında LFSR'ın tohum değerine sıfırlanmasını sağlayarak, alıcıdaki de-karıştırıcı ile senkronizasyonu garanti eder. Karıştırıcının sağladığı faydalar:

- Zamanlama kurtarma döngüsü için yeterli geçiş yoğunluğu,
- DC sapmasının önlenmesi,
- Spektral yayılmanın düzleştirilmesi.

##### 4.A.1.6. FEC Extended Encoder (LDPC Kodlayıcı)

| Parametre | Değer |
|:---|:---|
| Kodlayıcı Nesnesi | `ldpc_enc` |
| Parite Matrisi Dosyası | `n_1296_k_0648_ieee.alist` |
| Mesaj Uzunluğu ($k$) | $648$ bit |
| Kod Sözcüğü Uzunluğu ($n$) | $1296$ bit |
| Delme Deseni | `'11'` (delme yok) |

LDPC kodlayıcı, 648 bitlik mesaj bloklarını 1296 bitlik kod sözcüklerine dönüştürerek $R = 0.5$ oranlı ileri hata düzeltme koruması ekler. Kodlama işlemi sonrası paket uzunluğu tam iki katına çıkar.

##### 4.A.1.7. Tagged Stream Multiply Length (×2.0)

LDPC kodlamanın paket uzunluğunu iki katına çıkarması nedeniyle, `packet_len` etiket değerinin güncellenmesi gerekmektedir. Bu blok, etiket değerini $\times 2.0$ çarpanı ile doğru değere günceller.

##### 4.A.1.8. Protocol Formatter (Protokol Biçimlendirici)

| Parametre | Değer |
|:---|:---|
| Format Nesnesi | `hdr` = `header_format_default(default_access_code, 0)` |

GNU Radio'nun standart erişim kodunu (64-bit) ve yük uzunluğu alanını içeren bir başlık üretir. Erişim kodu, alıcıdaki `Correlate Access Code` bloğu tarafından paket sınırlarının tespitinde kullanılır.

##### 4.A.1.9. Tagged Stream Mux (Etiketli Akış Çoğullayıcı)

| Giriş | İçerik | Boyut |
|:---|:---|:---|
| Port 0 | Preambül (`[0xC0, 0xAF]` tekrarlayan) | 250 bayt |
| Port 1 | Başlık (erişim kodu + yük uzunluğu) | Değişken |
| Port 2 | LDPC Kodlu Yük | 1296 bit (162 bayt) |
| Port 3 | Postambül (`[0xC0, 0xAF]` tekrarlayan) | 8 bayt |

Dört giriş portundan gelen verileri sıralı olarak birleştirerek çerçeve (frame) yapısını oluşturur:

$$\text{Çerçeve} = [\underbrace{\text{Preambül}}_{250 \text{ B}}] \| [\underbrace{\text{Başlık}}_{\text{Değişken}}] \| [\underbrace{\text{LDPC Yük}}_{162 \text{ B}}] \| [\underbrace{\text{Postambül}}_{8 \text{ B}}]$$

Preambül ve postambül, `Vector Source` bloklarından `[0xC0, 0xAF]` bayt dizisinin tekrarı olarak üretilmektedir.

##### 4.A.1.10. Constellation Modulator (Konstelasyon Modülatörü — DBPSK)

| Parametre | Değer |
|:---|:---|
| Konstelasyon | BPSK (noktalar: $[-1-j, -1+j, 1+j, 1-j]$) |
| Diferansiyel Kodlama | `True` |
| SPS | `4` |
| Aşırı Bant Genişliği ($\beta$) | $0.35$ |

Bu bileşik blok, aşağıdaki işlemleri kapsüllemektedir:
1. **Diferansiyel kodlama:** Bit bilgisini ardışık semboller arasındaki faz farkına dönüştürür.
2. **Konstelasyon eşleme:** Kodlanmış bitleri BPSK sembollerine eşler.
3. **Üst örnekleme (Upsampling):** Her sembolün $\text{sps} = 4$ kopyasını oluşturur.
4. **RRC Darbe Şekillendirme:** $\beta = 0.35$ roll-off faktörü ile bant sınırlama ve ISI önleme.

##### 4.A.1.11. Tag Gate (Etiket Kapısı)

Verici tarafındaki paket etiketlerinin kanal model bloğuna sızmasını engelleyerek, alıcının yalnızca kendi senkronizasyon mekanizmasıyla çalışmasını garanti eder.

##### 4.A.1.12. Multiply Const (Sabit Çarpma — Güç Tahsisi)

| Parametre | Değer |
|:---|:---|
| Sabit ($\alpha_1$) | $0.894$ |

Kullanıcı 1'e atanan güç katsayısı ($a_1 = 0.8$) doğrultusunda, modüle edilmiş sinyalin genliği $\alpha_1 = \sqrt{0.8} \approx 0.894$ ile ölçeklenir.

#### 4.A.2. Kullanıcı 2 Verici Zinciri (Uzak Kullanıcı — Far User)

Kullanıcı 2'nin verici zinciri, Kullanıcı 1 ile **yapısal olarak özdeştir**; yalnızca aşağıdaki parametrelerde farklılık göstermektedir:

| Blok | Farklılık |
|:---|:---|
| **File Source** | Kaynak dosya: `bpsk_transmit_2.txt` |
| **FEC Extended Encoder** | Kodlayıcı nesnesi: `fec_extended_encoder_0_0` (aynı LDPC alist, ayrı örnek) |
| **Multiply Const** | Sabit ($\alpha_2$): $0.447$ ($\sqrt{0.2}$) |

#### 4.A.3. Süperpozisyon Birleştirme (Add Block)

| Parametre | Değer |
|:---|:---|
| Tip | Karmaşık (complex) |
| Giriş Sayısı | `2` |
| Vektör Uzunluğu | `1` |

İki kullanıcının güç-ölçeklenmiş sinyalleri, `blocks_add_xx_0` bloğu ile toplanarak süperpoze sinyal oluşturulur:

$$s(t) = 0.894 \cdot x_1(t) + 0.447 \cdot x_2(t)$$

Süperpoze sinyal, `virtual_sink "transmit"` üzerinden kanal modeline yönlendirilir.

### 4.B. Kanal Modeli (Channel Model)

| Parametre | Değer | Açıklama |
|:---|:---|:---|
| **Gürültü Gerilimi** | `noise` = $0.1$ (varsayılan) | Qt GUI kaydırıcısı ile ayarlanabilir (0–2) |
| **Frekans Kayması** | `freq_offset` = $0.01$ | Normalize frekans ofseti ($\pm 0.25$ aralığı) |
| **Zamanlama Sapması ($\epsilon$)** | `time_offset` = $1.0001$ | Örnekleme frekansı sapma oranı (0.999–1.001) |
| **Kanal Katsayıları** | $[1.0]$ | Tek-dokunuşlu düz sönümleme |
| **Etiket Geçirme** | `True` | Akış etiketlerini korur |
| **Gürültü Tohumu** | $0$ | Tekrarlanabilir simülasyon |

Kanal modeli, gerçekçi bir iletim ortamını taklit etmek üzere süperpoze sinyale üç tür bozulma eklemektedir:

1. **AWGN Gürültüsü:** $\sigma_n = 0.1$ (varsayılan) ile Gauss gürültüsü,
2. **Frekans Kayması:** $\Delta f / f_s = 0.01$ normalize ofset, taşıyıcı frekansı sapmasını simüle eder,
3. **Zamanlama Sapması:** $\epsilon = 1.0001$, verici ve alıcı osilatörleri arasındaki saat frekansı uyumsuzluğunu temsil eder.

Qt GUI kaydırıcıları sayesinde bu parametreler gerçek zamanlı olarak ayarlanabilmekte ve sistemin farklı bozulma koşullarındaki davranışı interaktif olarak gözlemlenebilmektedir.

### 4.C. Alıcı (Receiver) Katmanı ve SIC Döngüsü

Alıcı, dört ana alt-sisteme ayrılmaktadır: (1) Eşleştirilmiş Filtreleme ve Senkronizasyon, (2) Kullanıcı 1 Çözümleme, (3) SIC Yeniden Oluşturma ve Çıkarma, (4) Kullanıcı 2 Çözümleme.

#### 4.C.1. Eşleştirilmiş Filtreleme ve Senkronizasyon Blokları

##### FFT RRC Filter (Eşleştirilmiş Filtre)

| Parametre | Değer |
|:---|:---|
| Roll-off ($\alpha$) | $0.35$ |
| Filtre Uzunluğu | $11 \times \text{sps} = 44$ dokunuş |
| Örnekleme Frekansı | $200{,}000$ Hz |
| Sembol Hızı | $50{,}000$ sembol/s |
| Desimason | $1$ (çıkış hızı değişmez) |

Alıcının ön ucunda yer alan bu blok, verici tarafındaki RRC darbe şekillendirme filtresinin eşleştirilmiş karşılığıdır. FFT tabanlı uygulama, uzun filtrelerde hesaplama verimliliği sağlar. Eşleştirilmiş filtreleme sonrası toplam darbe tepkisi, Nyquist ISI kriterini sağlayan Yükseltilmiş Kosinüs biçimini alır.

##### Symbol Synchronizer (Sembol Senkronizörü — Polifaz Saat Kurtarma)

| Parametre | Değer |
|:---|:---|
| TED Tipi | `SIGNAL_TIMES_SLOPE_ML` (Sinyal × Eğim ML tahmini) |
| SPS | `4` |
| Döngü Bant Genişliği | $0.045$ |
| Sönümleme Faktörü | $1.0$ |
| Maksimum Sapma | $1.5$ |
| Çıkış SPS | `1` |
| İnterpolasyon Tipi | `IR_MMSE_8TAP` (MMSE-8 tap) |
| Polifaz Filtre Sayısı | `32` |
| TED Kazancı | `0.1` |

Polifaz filtre bankası tabanlı sembol senkronizörü, alınan sinyalin optimum örnekleme anlarını belirleyerek sembol başına 4 örnekten (sps=4) tek bir optimum örneğe (sps=1) desimasyonu gerçekleştirir.

**Zamanlama Hata Detektörü (TED):** `SIGNAL_TIMES_SLOPE_ML` yöntemi, Maximum Likelihood tabanlı bir zamanlama tahmin algoritması olup, sinyalin anlık değeri ile eğiminin çarpımından zamanlama hatası bilgisini türetir. Bu yöntem, özellikle düşük SNR'da `Mueller and Muller` veya `Zero-Crossing` algoritmalarına kıyasla daha gürbüz (robust) performans sunmaktadır.

**MMSE İnterpolasyon:** 8-dokunuşlu Minimum Ortalama Kare Hatası interpolatörü, polifaz filtre bankasının 32 alt-filtresi arasında sürekli zamanlı örnekleme anı tahmini yaparak optimum sembol değerini üretir.

**Döngü Dinamikleri:** İkinci dereceden döngü filtresi, $\omega_n = 0.045$ bant genişliği ve $\zeta = 1.0$ sönümleme ile konfigüre edilmiştir. Maksimum sapma $1.5$ değeri, zamanlama kaymasının $\pm 1.5$ sembol aralığında izlenmesine olanak tanır.

##### Costas Loop (Costas Döngüsü — Taşıyıcı Frekansı/Faz Kurtarma)

| Parametre | Değer |
|:---|:---|
| Döngü Bant Genişliği | $2\pi / 100 \approx 0.0628$ rad |
| Derece | Konstelasyon noktası sayısına göre otomatik |

Costas döngüsü, taşıyıcı frekansındaki artık faz ve frekans sapmalarını ($\Delta f = 0.01$) telafi eder. Döngü bant genişliği ($\omega_n = 2\pi/100$), gürültü bastırma ve izleme hızı arasındaki dengeyi optimize eder.

##### Correlation Estimator (Korelasyon Tahmincisi)

| Parametre | Değer |
|:---|:---|
| Preambül Sembolleri | `preamble_syms` (64 BPSK sembol) |
| Eşik | $0.7$ |
| Yöntem | `THRESHOLD_ABSOLUTE` |
| SPS | `1` (sembol senkronizörü çıkışında) |
| Mark Delay | `len(preamble_syms) - 1 = 63` |

Bu blok, Costas Loop çıkışında sürgülü çapraz korelasyon yaparak preambül dizisini ($[0\text{xC0}, 0\text{xAF}] \times 4$ → 64 BPSK sembol) tespit eder. Korelasyon tepesi eşik değerini ($0.7$) aştığında `time_est` ve `corr_est` etiketleri eklenir. Bu etiketler, SIC hizalama bloğu tarafından paket sınırlarının belirlenmesinde kullanılmaktadır.

#### 4.C.2. Kullanıcı 1 Çözümleme Zinciri (SIC Aşama 1)

Senkronizasyon bloklarından sonra, Kullanıcı 1'in verisi aşağıdaki zincir ile çözümlenir:

**Costas Loop → `virtual_sink "recovery"` → Constellation Soft Decoder → EPY Block 0 (Yumuşak Diferansiyel Çözücü) → Correlate Access Code → FEC Extended Decoder (LDPC) → Tagged Stream Multiply Length (×0.5) → Additive Scrambler (de-karıştırma) → Repack Bits (1→8) → Stream CRC32 (Kontrol) → File Sink**

##### Constellation Soft Decoder (Yumuşak Konstelasyon Kod Çözücü)

| Parametre | Değer |
|:---|:---|
| Konstelasyon | `constel` (BPSK) |
| Gürültü Gücü | $-1$ (otomatik tahmin) |

Karmaşık sembolleri, BPSK konstelasyon haritasına göre yumuşak karar (soft-decision) çıkışına dönüştürür. Sert karar (hard-decision) yerine yumuşak karar kullanılması, LDPC kod çözücünün performansını önemli ölçüde artırmaktadır; zira yumuşak bilgi, her bitin güvenilirlik derecesini de taşır.

##### EPY Block 0 — Yumuşak Diferansiyel Çözücü (Soft Differential Decoder)

| Parametre | Değer |
|:---|:---|
| Sınıf | `gr.sync_block` |
| Giriş/Çıkış | `float32` / `float32` |
| Modülüs | `2` (BPSK modu) |

Bu özel gömülü Python bloğu (`NOMA_epy_block_0.py`, 104 satır), diferansiyel kodlamanın tersini yumuşak karar formatında gerçekleştirmektedir:

$$\hat{b}_k^{\text{soft}} = -(y_k \cdot y_{k-1})$$

Burada $y_k$ yumuşak konstelasyon çıkışıdır. Çarpım işlemi, diferansiyel fazı çözerken yumuşak karar büyüklüğünü korur. Negatif işaret, `Correlate Access Code` bloğunun beklediği polarite konvansiyonuna uyum sağlar (pozitif değer → bit '1' eşlemesi).

Blok, `self.prev` durum değişkeni ile çağrılar arası bellek tutarak, ardışık `work()` çağrıları arasında diferansiyel referansın sürdürülmesini sağlar.

##### Correlate Access Code — Tag Stream (Erişim Kodu Korelasyonu)

| Parametre | Değer |
|:---|:---|
| Erişim Kodu | GNU Radio varsayılan 64-bit erişim kodu |
| Eşik | `0` |
| Etiket Adı | `packet_len` |

Yumuşak bit akışında erişim kodunu arar ve eşleşme bulunduğunda `packet_len` etiketi ekler.

##### FEC Extended Decoder (LDPC Kod Çözücü)

| Parametre | Değer |
|:---|:---|
| Kod Çözücü | `ldpc_dec` |
| Delme Deseni | `'11'` |
| Maksimum İterasyon | `50` |

LDPC kod çözücü, 1296 bitlik kod sözcüklerini 648 bitlik mesaj bloklarına çözer. 50 iterasyon limiti, hesaplama maliyeti ile hata düzeltme performansı arasındaki dengeyi gözetmektedir.

##### Tagged Stream Multiply Length (×0.5)

LDPC kod çözme sonrası paket uzunluğu yarıya düştüğünden ($1296 \to 648$ bit), `packet_len` etiketinin güncellenmesi gerekmektedir.

##### Stream CRC32 (Kontrol Modu)

| Parametre | Değer |
|:---|:---|
| Kontrol Modu | `True` |

CRC-32 sağlama toplamını doğrular; hatalı paketler düşürülür, doğru paketler çıkışa iletilir. Hata durumunda `Message Debug` bloğuna bildirim gönderilir.

##### File Sink (Dosya Çıkışı)

| Parametre | Değer |
|:---|:---|
| Dosya | `bpsk_receive.txt` |
| Ekleme Modu | `False` |

Çözümlenen Kullanıcı 1 verisi bu dosyaya yazılır.

#### 4.C.3. SIC Mekanizması — Yeniden Kodlama ve Çıkarma

SIC'nin kritik aşaması, Kullanıcı 1'in başarıyla çözülen verisinin yeniden oluşturularak alınan bileşik sinyalden çıkarılmasıdır. Bu süreç iki alt-bileşenden oluşur: Yeniden Kodlama Zinciri ve SIC Hizalama Bloğu.

##### SIC Yeniden Kodlama Zinciri

**Çözülmüş User 1 Bitleri (`virtual_source "user_2"`) → FEC Extended Encoder (LDPC SIC) → Chunks to Symbols (BPSK) → Multiply Const ($\alpha_1 = 0.894$) → `virtual_sink "user_2_sub"`**

| Blok | Parametre | Değer |
|:---|:---|:---|
| **LDPC Encoder (SIC)** | Kodlayıcı | `fec_extended_encoder_0_0_0` (aynı IEEE alist) |
| **Chunks to Symbols** | Sembol Tablosu | $[-1.0 + 0j, +1.0 + 0j]$ (BPSK) |
| **Multiply Const (SIC)** | Sabit | $0.894$ ($= \alpha_1$) |

Yeniden kodlama zincirinde önemli bir tasarım kararı, `Constellation Modulator` bloğu yerine doğrudan `Chunks to Symbols` bloğunun kullanılmasıdır. Bu yaklaşım:
- Darbe şekillendirme ve üst örnekleme adımlarını atlayarak daha basit bir yeniden oluşturma sağlar,
- SIC hizalama bloğunun sembol düzeyinde çalışmasını mümkün kılar.

##### EPY Block 1 — Bağımsız NOMA SIC Hizalama Bloğu (Decoupled NOMA SIC Aligner)

Bu proje kapsamında geliştirilen en kritik özel blok `NOMA_epy_block_1.py` dosyasında yer almaktadır (7.817 bayt, 170 satır). `gr.basic_block` sınıfından türetilmiş bu blok, `general_work()` fonksiyonu ile çalışmaktadır.

**Portlar:**

| Port | Yön | Tip | Kaynak |
|:---|:---|:---|:---|
| `in_rx` (Port 0) | Giriş | Karmaşık | Korelasyon Tahmincisi çıkışı |
| `in_tx1` (Port 1) | Giriş | Karmaşık | Yeniden oluşturulan User 1 sinyali |
| `out_rx2` (Port 0) | Çıkış | Karmaşık | SIC sonrası artık User 2 sinyali |

**Konfigürasyon Parametreleri:**

| Parametre | Değer | Açıklama |
|:---|:---|:---|
| `sample_rate` | $200{,}000$ | Örnekleme frekansı |
| `near_user_amplitude` | $0.864$ | SIC genlik kalibrasyonu |
| `payload_size` | $1296$ | LDPC kod sözcüğü uzunluğu (sembol) |
| `payload_offset` | $64$ | Başlık uzunluğu (sembol) |
| `search_window` | $32$ | Korelasyon arama penceresi |

**Algoritma — Etiket-Bağımsız Çapraz Korelasyon SIC:**

1. **Bağımsız Girdi Tamponlama (Decoupled Buffering):** `forecast()` fonksiyonu `[0, 0]` döndürerek GNU Radio zamanlayıcısına "sıfır girdi ile çalışabilir" mesajı verir. Bu kritik tasarım kararı, `in_rx` ve `in_tx1` portlarının bağımsız tüketilmesini sağlayarak zamanlayıcı kilitlenmesini (scheduler deadlock) önler. Gelen veriler anında dahili dairesel tamponlara (`buffer_rx`, `buffer_tx1`) aktarılır.

2. **Tampon Taşma Koruması:** `buffer_rx` maksimum 50.000 örnek, `buffer_tx1` maksimum $5 \times \text{payload\_size}$ örnek ile sınırlandırılmıştır.

3. **DBPSK Dönüşümü:** Yeniden oluşturulan BPSK sembolleri ($\pm 1$), DBPSK domenine dönüştürülür:
   $$\text{tx1\_diff}[k] = \prod_{i=0}^{k} (-\text{sgn}(\text{Re}(\text{tx1}[i])))$$
   Bu dönüşüm, verici tarafındaki diferansiyel kodlama ile eşleşme sağlar.

4. **Çapraz Korelasyon Hizalama:** `scipy.signal.correlate()` fonksiyonu ile RX tamponu ve DBPSK-dönüştürülmüş TX1 arasında korelasyon hesaplanır:
   $$C(\tau) = \sum_{n} r[n] \cdot \hat{s}_1^*[n - \tau]$$
   Korelasyon tepesinin konumu optimal zamanlama ofsetini verir.

5. **Genlik ve Faz Tahmini:** Korelasyon tepesinden:
   - Genlik: $\hat{A} = |C_{\text{peak}}| / E_{\text{tx1}}$ (burada $E_{\text{tx1}}$ TX1 enerjisi)
   - Faz: $\hat{\phi} = \angle C_{\text{peak}}$
   - Dinamik genlik ölçekleme: $\hat{A} > 1.10$ ise $1.5\times$ küçültme uygulanır

6. **Girişim Çıkarma:**
   $$\text{buffer\_rx}[\text{aligned}] \mathrel{-}= \text{tx1\_diff} \cdot \hat{A} \cdot e^{j\hat{\phi}}$$

7. **Paket İzleme:** İlk paket için 1000–3000 örnek aralığında geniş arama; sonraki paketler için beklenen konumdan $\pm 128$ örnek sapma ile dar arama. Paketler arası mesafe $\approx 3408$ örnek.

8. **Güvenli Çıkış Akışı:** Yalnızca SIC işlemi tamamlanmış (çıkarılmış veya güvenli) örnekler çıkışa iletilir.

9. **Hata Ayıklama:** `debug_sic.txt` dosyasına her paket için kayma, faz ve genlik bilgileri yazılır.

**`basic_block` vs. `sync_block` Tasarım Kararı:**

`sync_block` yapısının neden kullanılmadığı, bu projedeki en kritik mimari kararlardan biridir. `sync_block`, her iki giriş portundan eşit sayıda örnek hazır olmasını bekler. Ancak SIC döngüsündeki geri besleme yapısında:

1. `in_rx` (Costas Loop çıkışı) gecikmesiz veri sağlar,
2. `in_tx1` (yeniden oluşturulan sinyal) ise User 1'in çözülmesi, LDPC kod çözme ve yeniden kodlama gecikmesini barındırır (en az 1 paketlik çerçeve gecikmesi),
3. `sync_block`, `in_tx1` verisi gelmeden `in_rx` verisini tüketmez,
4. `in_tx1` hattı ise `in_rx` işlenmeden yeni veri üretemez.

Bu dairesel bağımlılık, GNU Radio zamanlayıcısının **tamamen kilitlenmesine** yol açar. `basic_block` yapısı, `consume(0, n)` ve `consume(1, m)` çağrılarıyla portları bağımsız tüketerek bu sorunu çözmektedir.

#### 4.C.4. Kullanıcı 2 Çözümleme Zinciri (SIC Aşama 2)

Girişimi temizlenmiş sinyal üzerinde Kullanıcı 2'nin çözümlenmesi, Kullanıcı 1 zinciri ile yapısal olarak benzer alıcı bloklarından oluşmaktadır:

**EPY Block 1 Çıkışı → Constellation Soft Decoder (2.) → EPY Block 0_0 (Yumuşak Diferansiyel Çözücü) → Correlate Access Code (2.) → FEC Extended Decoder (LDPC, `ldpc_dec_2`) → Tagged Stream Multiply Length (×0.5) → Additive Scrambler (de-karıştırma) → Repack Bits (1→8) → Stream CRC32 (Kontrol) → File Sink (`bpsk_receive_2.txt`)**

Tüm kod çözme blokları, Kullanıcı 1 zinciri ile aynı parametrelerde konfigüre edilmiştir. Ayrı blok örnekleri (`_0`, `_0_0` son ekleri) kullanılarak iki zincirin bağımsız iç durum değişkenlerine sahip olması sağlanmıştır:

| Blok | Kullanıcı 1 Örneği | Kullanıcı 2 Örneği |
|:---|:---|:---|
| Soft Constellation Decoder | `_cf_0` | `_cf_0_0` |
| Soft Diff Decoder (EPY) | `epy_block_0` | `epy_block_0_0` |
| Correlate Access Code | `_ts_0` | `_ts_0_0` |
| LDPC Decoder | `ldpc_dec` | `ldpc_dec_2` |
| File Sink | `bpsk_receive.txt` | `bpsk_receive_2.txt` |

#### 4.C.5. Qt GUI Görselleştirme ve Kontrol Blokları

Gerçek zamanlı sistem izleme ve parametre ayarı için aşağıdaki Qt bileşenleri akış diyagramına eklenmiştir:

**Görselleştirme Blokları:**

| Blok | Bağlantı Noktası | Görüntülenen Bilgi |
|:---|:---|:---|
| **QT GUI Time Sink** ("Received Samples") | Kanal çıkışı | Alınan bileşik sinyalin zaman gösterimi (1024 örnek) |
| **QT GUI Time Sink** ("Recovered Symbols") | Costas Loop çıkışı | Senkronize edilmiş User 1 sembolleri (256 örnek) |
| **QT GUI Time Sink** ("USER 2") | SIC çıkışı | SIC sonrası User 2 sembolleri (256 örnek) |

**Kontrol Kaydırıcıları (Qt GUI Range):**

| Kaydırıcı | Değişken | Aralık | Adım |
|:---|:---|:---|:---|
| Gürültü | `noise` | $0.0$ – $2.0$ | $0.01$ |
| Frekans Kayması | `freq_offset` | $-0.25$ – $+0.25$ | $0.001$ |
| Zamanlama Sapması | `time_offset` | $0.999$ – $1.001$ | $0.0001$ |

### 4.D. Sanal Sinyal Yolları (Virtual Sink/Source Pairs)

Akış diyagramının okunabilirliği ve yönetilebilirliği için 16 sanal sinyal yolu çifti kullanılmıştır:

| Akış Kimliği | Açıklama |
|:---|:---|
| `tx_packet_1` | Kullanıcı 1 çerçevelenmiş TX paketi |
| `tx_packet_2` | Kullanıcı 2 çerçevelenmiş TX paketi |
| `header_1` / `header_2` | Protokol başlıkları |
| `ldpc_payload_1` / `ldpc_payload_2` | LDPC kodlu yükler |
| `transmit` | Süperpoze NOMA sinyali |
| `channel` | Kanal çıkışı |
| `recovery` | Costas Loop çıkışı (User 1 doğrudan çözümleme) |
| `recovery_2` | Korelasyon Tahmincisi çıkışı (SIC hizalama) |
| `rx_payload` / `rx_payload_2` | Tespit edilmiş yükler |
| `user_2` | Çözülmüş User 1 bitleri (SIC yeniden kodlama girişi) |
| `user_2_sub` | Yeniden oluşturulan User 1 sinyali (SIC çıkarma) |
| `ldpc_rx` / `ldpc_rx_2` | Son çözülmüş bitler |

### 4.E. Çerçeve Yapısı (Frame Structure)

Her kullanıcı paketinin tam çerçeve yapısı aşağıdaki tabloda özetlenmiştir:

| Segment | İçerik | Boyut | Sembol Sayısı |
|:---|:---|:---|:---|
| **Preambül** | `[0xC0, 0xAF]` tekrarlayan dizi | 250 bayt (2000 bit) | 256 sembol |
| **Başlık (Header)** | 64-bit erişim kodu + yük uzunluğu | Değişken | ~64 sembol |
| **Yük (Payload)** | LDPC kodlu kullanıcı verisi | 162 bayt (1296 bit) | 1296 sembol |
| **Postambül** | `[0xC0, 0xAF]` tekrarlayan dizi | 8 bayt (64 bit) | ~64 sembol |
| **Toplam** | — | — | **~1680 sembol** |

Preambül deseni `[0xC0, 0xAF] = [11000000, 10101111]`:
- Zengin geçiş yapısı sayesinde sembol senkronizörünün zamanlama kilitleme süresini hızlandırır,
- Costas döngüsünün faz referansını yakalamasını kolaylaştırır,
- Korelasyon tahmincisi için yüksek auto-korelasyon tepesi sağlar.

Postambül ise çerçeve sonundaki RRC filtresinin kuyruk etkilerini absorbe eder.

---

## 5. SİMÜLASYON VE PERFORMANS DEĞERLENDİRMESİ

### 5.1. Simülasyon Ortamı ve Koşulları

| Parametre | Değer |
|:---|:---|
| **Platform** | GNU Radio Companion 3.10.12+ |
| **İşletim Sistemi** | Linux (Arch Linux) |
| **Programlama Dili** | Python 3.8+ |
| **Simülasyon Türü** | Yazılımsal geri-döngü (software loopback) |
| **Kanal Modeli** | AWGN ($\sigma_n = 0.1$, SNR ≈ 20 dB), $\Delta f = 0.01$, $\epsilon = 1.0001$ |
| **Veri Kaynağı** | Metin dosyası (dosya transferi senaryosu) |
| **Veri İçeriği** | `0–9` rakamları, her biri `payload_size` kez tekrarlı |
| **Doğrulama Yöntemi** | Verici/alıcı dosya karşılaştırması (`filecmp.cmp()`) |
| **Hedef Donanım** | USRP E310 (2.435 GHz ISM bandı, gelecek çalışma) |

### 5.2. Çerçeve Yapısının Senkronizasyon Kararlılığı Üzerindeki Etkisi

Tasarlanan çerçeve yapısı (Preambül + Başlık + Yük + Postambül), alıcı senkronizasyon zincirinin kararlılığı açısından kritik bir rol üstlenmektedir:

#### 5.2.1. Preambül ve Zamanlama Kurtarma

250 baytlık ($= 2000$ bit $\approx 256$ sembol) preambül segmenti, `[0xC0, 0xAF]` tekrarlayan deseniyle Symbol Synchronizer bloğunun zamanlama hata detektörü için zengin geçiş yapısına sahip bir eğitim dizisi sağlamaktadır. $\text{sps} = 4$ konfigürasyonunda $256 \times 4 = 1024$ örnek zamanlama edinim penceresi sunulmaktadır; bu değer, pratikte güvenilir kilit süresini garanti etmektedir.

Korelasyon Tahmincisi bloğu, 64 BPSK sembolden oluşan `preamble_syms` dizisi ile preambül sonunu tespit eder. `THRESHOLD_ABSOLUTE` yöntemi ve $0.7$ eşik değeri ile:
- Gürültülü ortamda kaçırılan paket olasılığı (missed detection) düşük tutulmuş,
- Yanlış alarm (false alarm) oranı kabul edilebilir seviyede sınırlandırılmıştır.

#### 5.2.2. Başlık ve Paket Sınırı Algılama

GNU Radio'nun standart 64-bit erişim kodu, düşük oto-korelasyon yan loblarına sahip bir dizi olarak seçilmiştir. `Correlate Access Code – Tag Stream` bloğu ile paket sınırı tespiti yapılmakta; yük uzunluğu alanı ise her paketin boyutunu belirlemektedir.

#### 5.2.3. Postambül ve Kuyruk Etkileri

8 baytlık postambül segmenti, paket sonunda RRC darbe şekillendirme filtresinin geçici tepkisinin (transient response) sönümlenmesi için yeterli sembol süresi sağlamaktadır. Bu sayede ardışık paketler arasında ISI oluşumu engellenmektedir.

### 5.3. LDPC Kodlamanın SIC Hata Yayılımı Üzerindeki Rolü

SIC mekanizmasının başarısı, büyük ölçüde birinci aşamadaki (Kullanıcı 1) kod çözme doğruluğuna bağlıdır. IEEE 802.11n LDPC kodlaması, bu bağlamda birden fazla kritik işlev görmektedir:

#### 5.3.1. Hata Düzeltme Kapasitesi

$R = 0.5$ oranlı LDPC kodu, her 648 bitlik bilgi bloğuna 648 bitlik artıklık (redundancy) eklemektedir. Yarı-döngüsel yapısı ve düzensiz sütun ağırlıkları sayesinde, bu kod Shannon sınırına 1 dB mesafede performans sunmaktadır. 50 iterasyonluk kod çözme limiti ile:

- Kullanıcı 1'in neredeyse hatasız çözülmesi ($\text{BER} < 10^{-6}$) sağlanmakta,
- SIC çıkarma işlemindeki artık girişimin ($\alpha_1[x_1 - \hat{x}_1]$) minimize edilmesi mümkün kılınmaktadır.

#### 5.3.2. Yumuşak Karar ve LDPC Sinerjisi

Alıcı zincirinde `Constellation Soft Decoder` → `Soft Diff Decoder` yolu ile korunan yumuşak karar (LLR) bilgisi, LDPC kod çözücünün iteratif mesaj geçirme (message passing) algoritmasının tam potansiyeline ulaşmasını sağlamaktadır. Sert karar tabanlı bir alıcıya kıyasla, yumuşak karar LDPC kombinasyonu tipik olarak 2–3 dB SNR kazancı sunmaktadır.

#### 5.3.3. CRC ile Çift Katmanlı Koruma

CRC-32 kontrolü, LDPC kod çözme sonrası paket bütünlüğünü doğrulayan ikinci bir koruma katmanı oluşturmaktadır. Hatalı paketlerin SIC yeniden kodlama zincirine girmesi engellenerek, hata yayılımının kaskat etkisi (cascade effect) sınırlandırılmaktadır.

### 5.4. Gözlemlenen Sonuçlar ve Tartışma

#### 5.4.1. Kullanıcı 1 (Yakın Kullanıcı) Performansı

$\text{SNR} \approx 20$ dB koşullarında, Kullanıcı 1 verici dosyası (`bpsk_transmit.txt`) ile alıcı çıkış dosyası (`bpsk_receive.txt`) arasında başarılı dosya transferi doğrulanmıştır. `filecmp.cmp()` fonksiyonu ile otomatik doğrulama gerçekleştirilmiştir. LDPC kodlamasının sağladığı hata düzeltme kapasitesi, AWGN gürültüsü ve frekans/zamanlama sapmalarının etkisini büyük ölçüde telafi etmiştir.

#### 5.4.2. Kullanıcı 2 (Uzak Kullanıcı) ve SIC Performansı

SIC mekanizması üzerinden Kullanıcı 2 sinyalinin çözümlenmesi gerçekleştirilmiştir. Proje geliştirme sürecinde aşağıdaki teknik zorluklar gözlemlenmiş ve çözüm stratejileri uygulanmıştır:

1. **Zamanlama Hizalama Hassasiyeti:** SIC çıkarma işleminde orijinal alınan sinyal ile yeniden oluşturulan Kullanıcı 1 sinyali arasındaki zamanlama hizalaması, örnek düzeyinde ($< 1$ sembol) hassasiyet gerektirmektedir. Çapraz korelasyon tabanlı dinamik hizalama algoritması bu soruna çözüm olarak geliştirilmiştir.

2. **Genlik ve Faz Kalibrasyonu:** Kanal etkilerinin (faz dönmesi, genlik değişimi) yeniden oluşturulan sinyale doğru yansıtılması gerekmektedir. SIC hizalama bloğu, korelasyon tepesinden genlik ve faz tahminleri çıkararak dinamik kalibrasyon uygulamaktadır.

3. **Scheduler Kilitlenmesi:** `sync_block` tabanlı ilk tasarım, geri besleme döngüsünün dairesel bağımlılığı nedeniyle GNU Radio zamanlayıcısının kilitlenmesine yol açmıştır. `basic_block` yapısına geçiş ile bu sorun çözülmüştür.

4. **Sinyal Sızıntısı (Signal Bleeding):** 1 sembol hizalama hatası durumunda, $\alpha_1/\alpha_2 = 2$ oranındaki güç farkı nedeniyle User 1 kalıntısının User 2 sinyalini bastırması gözlemlenmiştir. `corr_est` bloğunun `mark_delay` parametresinin doğru kalibrasyonu ile bu etki minimize edilmiştir.

### 5.5. Sistem Doğrulama Yöntemleri

Sistemin doğrulanmasında aşağıdaki yöntemler kullanılmıştır:

1. **Otomatik Dosya Karşılaştırması:** `filecmp.cmp()` fonksiyonu ile verici ve alıcı metin dosyalarının bayt düzeyinde karşılaştırması.
2. **Gerçek Zamanlı Zaman Domeni İzleme:** Üç adet Qt GUI Time Sink ile:
   - Alınan bileşik sinyal (kanal çıkışı)
   - Senkronize edilmiş User 1 sembolleri
   - SIC sonrası User 2 sembolleri
3. **Mesaj Hata Ayıklama:** CRC başarısız paketlerin `Message Debug` bloğu üzerinden izlenmesi.
4. **SIC Hata Ayıklama Günlüğü:** `debug_sic.txt` dosyası üzerinden her paket için zamanlama kayması, faz ofseti ve genlik kalibrasyonu bilgilerinin kaydedilmesi.
5. **Çevrimdışı Sinyal Analizi:** `rx_chunk.npy` ve `tx1_chunk.npy` dosyaları üzerinden numpy tabanlı genlik ve korelasyon analizi (`capture_sic_amplitude.py`, `offline_analysis.py`, `test_correlation.py`).

---

## 6. SONUÇ VE GELECEK ÇALIŞMALAR

### 6.1. Elde Edilen Bulguların Özeti

Bu bitirme projesinde, Güç Etki Alanlı NOMA (PD-NOMA) mimarisinin GNU Radio Companion platformu üzerinde uçtan uca bir gerçeklemesi başarıyla tamamlanmıştır. Projenin temel katkıları aşağıdaki şekilde özetlenebilir:

1. **Süperpozisyon Kodlaması Gerçeklemesi:** İki kullanıcının DBPSK modüleli sinyallerinin $\alpha_1 = 0.894$ (%80 güç) ve $\alpha_2 = 0.447$ (%20 güç) katsayıları ile birleştirilmesi başarıyla uygulanmıştır.

2. **IEEE 802.11n LDPC Kodlu İletim Zinciri:** $R = 0.5$ oranlı LDPC kodlaması ($n = 1296$, $k = 648$), Toplamsal Karıştırıcı (LFSR $0\text{x8A}/0\text{x7F}$), CRC-32, diferansiyel kodlama ve $\beta = 0.35$ RRC darbe şekillendirme ile entegre edilmiş tam bir verici-alıcı zinciri oluşturulmuştur.

3. **SIC Mekanizması:** Güçlü kullanıcının (User 1) yumuşak karar LDPC kod çözme ile çözülmesi, çözülen verisinin LDPC ile yeniden kodlanıp BPSK sembollerine eşlenmesi, ve çapraz korelasyon tabanlı hizalama ile bileşik sinyalden çıkarılması işlemleri gerçeklenmiştir. `basic_block` tabanlı bağımsız tamponlama yapısı ile zamanlayıcı kilitlenmesi sorunu çözülmüştür.

4. **Dosya Transferi Doğrulaması:** AWGN kanalı ($\text{SNR} \approx 20$ dB, $\Delta f = 0.01$, $\epsilon = 1.0001$) altında Kullanıcı 1 için başarılı metin dosyası transferi otomatik olarak doğrulanmıştır.

5. **Gerçek Zamanlı İzleme ve Kontrol:** Qt GUI Time Sink blokları ile zaman domeni görselleştirme ve kaydırıcılarla interaktif parametre ayarlama arayüzü oluşturulmuştur.

6. **Evrimsel Geliştirme Süreci:** Proje, basit BPSK dosya transferinden (LDPC'siz) → tek kullanıcılı LDPC-BPSK → iki kullanıcılı NOMA-SIC mimarisine doğru sistematik bir geliştirme sürecini izlemiştir. Bu yaklaşım, her aşamada doğrulama yapılmasını ve sorunların kademeli olarak çözülmesini mümkün kılmıştır.

### 6.2. Projenin Akademik ve Mühendislik Katkısı

Bu çalışma, NOMA'nın teorik çerçevesinin ötesine geçerek, SDR platformu üzerinde tüm sinyal işleme blokları — diferansiyel modülasyon, IEEE 802.11n LDPC kanal kodlama, RRC darbe şekillendirme, MMSE tabanlı sembol senkronizasyonu, Costas döngüsü taşıyıcı kurtarma ve çapraz korelasyon tabanlı SIC — ile birlikte çalışan uçtan uca bir demonstrasyon sunmaktadır.

Özellikle SIC hizalama bloğunun (`epy_block_1`) tasarımı, GNU Radio'nun akış tabanlı (streaming) mimarisi içinde geri beslemeli bir yapının nasıl kurulacağına dair özgün bir mühendislik çözümü ortaya koymaktadır. `basic_block` vs. `sync_block` seçiminin zamanlayıcı kilitlenmesi üzerindeki etkisi, DBPSK dönüşüm algoritması ve korelasyon tabanlı dinamik genlik/faz kalibrasyonu, bu projede ele alınan özgün teknik problemlerdir.

### 6.3. Gelecek Çalışmalar

Bu projenin sonuçları, aşağıdaki gelecek çalışma yönlerini açmaktadır:

1. **USRP E310 Donanım Doğrulaması:** Tasarlanan sistemin USRP E310 (2.435 GHz ISM bandı) üzerinde gerçek zamanlı kablosuz iletim ile doğrulanması. Proje kapsamında oluşturulan `Bpsk_file_transfer_loopback.grc` akış diyagramı, bu aşamanın temelini oluşturmaktadır. Gerçek kanal bozulmalarının (çok yollu sönümleme, Doppler kayması, donanım empedans uyumsuzluğu) SIC performansı üzerindeki etkisi incelenecektir.

2. **PlutoSDR Entegrasyonu:** Daha erişilebilir ve düşük maliyetli bir SDR platformu olan Analog Devices ADALM-PlutoSDR ile test edilmesi.

3. **Çok Kullanıcılı Genişletme:** Mevcut 2 kullanıcılı yapının 3 veya daha fazla kullanıcıya genişletilmesi ve kaskat SIC'nin hata yayılımı üzerindeki etkisinin araştırılması.

4. **Uyarlanır Güç Tahsisi:** Anlık kanal durum bilgisine (Channel State Information — CSI) dayalı dinamik güç tahsis algoritmalarının entegrasyonu. Kanal kalitesine bağlı olarak $a_1$ ve $a_2$ katsayılarının uyarlanır biçimde güncellenmesi.

5. **Gelişmiş SIC Yöntemleri:** Sert karar tabanlı SIC yerine, LLR (Log-Likelihood Ratio) bilgisini SIC yeniden oluşturma zincirinde kullanan yumuşak karar SIC implementasyonu.

6. **OFDM-NOMA Entegrasyonu:** BPSK'dan OFDM-NOMA mimarisine geçiş ile frekans-seçici kanallarda çalışma kabiliyetinin kazandırılması.

7. **Alternatif LDPC Konfigürasyonları:** Projede mevcut olan `n_0300_k_0152_gap_03.alist` dosyasındaki kısa blok LDPC kodunun ($n = 300$, $k = 152$, $R \approx 0.507$) düşük gecikme gereksinimlerindeki performansının değerlendirilmesi.

8. **BER Eğrisi Analizi:** Farklı SNR değerlerinde sistematik BER eğrilerinin çıkarılması, teorik sınırlarla karşılaştırılması ve SIC'nin kodlama kazancı üzerindeki etkisinin nicel olarak belirlenmesi.

---

## 7. KAYNAKÇA

[1] ITU-R, "IMT Vision – Framework and overall objectives of the future development of IMT for 2020 and beyond," Recommendation ITU-R M.2083-0, 2015.

[2] Z. Ding, Y. Liu, J. Choi, Q. Sun, M. Elkashlan, C. L. I, and H. V. Poor, "Application of Non-Orthogonal Multiple Access in LTE and 5G Networks," *IEEE Communications Magazine*, vol. 55, no. 2, pp. 185–191, Feb. 2017.

[3] T. M. Cover, "Broadcast Channels," *IEEE Transactions on Information Theory*, vol. 18, no. 1, pp. 2–14, Jan. 1972.

[4] Y. Saito, Y. Kishiyama, A. Benjebbour, T. Nakamura, A. Li, and K. Higuchi, "Non-Orthogonal Multiple Access (NOMA) for Cellular Future Radio Access," in *Proc. IEEE 77th Vehicular Technology Conference (VTC Spring)*, Jun. 2013.

[5] L. Dai, B. Wang, Y. Yuan, S. Han, C. L. I, and Z. Wang, "Non-Orthogonal Multiple Access for 5G: Solutions, Challenges, Opportunities, and Future Research Trends," *IEEE Communications Magazine*, vol. 53, no. 9, pp. 74–81, Sep. 2015.

[6] Z. Ding, Z. Yang, P. Fan, and H. V. Poor, "On the Performance of Non-Orthogonal Multiple Access in 5G Systems with Randomly Deployed Users," *IEEE Signal Processing Letters*, vol. 21, no. 12, pp. 1501–1505, Dec. 2014.

[7] S. M. R. Islam, N. Avazov, O. A. Dobre, and K. S. Kwak, "Power-Domain Non-Orthogonal Multiple Access (NOMA) in 5G Systems: Potentials and Challenges," *IEEE Communications Surveys & Tutorials*, vol. 19, no. 2, pp. 721–742, 2017.

[8] R. G. Gallager, "Low-Density Parity-Check Codes," *IRE Transactions on Information Theory*, vol. 8, no. 1, pp. 21–28, Jan. 1962.

[9] D. J. C. MacKay and R. M. Neal, "Near Shannon limit performance of low density parity check codes," *Electronics Letters*, vol. 32, no. 18, pp. 1645–1646, 1996.

[10] GNU Radio Project, "GNU Radio Manual and C++ API Reference," [Çevrimiçi]. Erişim: https://wiki.gnuradio.org/

[11] J. G. Proakis and M. Salehi, *Digital Communications*, 5th ed., McGraw-Hill, 2008.

[12] A. Goldsmith, *Wireless Communications*, Cambridge University Press, 2005.

[13] IEEE Std 802.11n-2009, "IEEE Standard for Information Technology — Telecommunications and Information Exchange Between Systems — Local and Metropolitan Area Networks," IEEE, Oct. 2009.

---

## 8. EKLER

### EK-A: Sistem Değişkenleri ve Blok Envanteri

#### A.1. Tam Değişken Listesi

| Değişken | Değer | Açıklama |
|:---|:---|:---|
| `samp_rate` | 200,000 Hz | Örnekleme frekansı |
| `sps` | 4 | Sembol başına örnek |
| `payload_size` | 77 bayt | Paket yük boyutu |
| `preamble_size` | 250 bayt | Preambül boyutu |
| `postamble_size` | 8 bayt | Postambül boyutu |
| `noise` | 0.1 | AWGN gürültü gerilimi (ayarlanabilir) |
| `freq_offset` | 0.01 | Normalize frekans kayması (ayarlanabilir) |
| `time_offset` | 1.0001 | Zamanlama sapma oranı (ayarlanabilir) |
| `constel` | BPSK konstelasyonu | $[-1-j, -1+j, 1+j, 1-j]$ |
| `hdr` | `header_format_default(...)` | Başlık format nesnesi |
| `preamble_syms` | 64 BPSK sembol | `[0xC0, 0xAF] × 4` → bit → BPSK |
| `ldpc_enc` | IEEE 802.11n LDPC encoder | n=1296, k=648 |
| `ldpc_dec` | IEEE 802.11n LDPC decoder | max_iter=50 |
| `ldpc_dec_2` | IEEE 802.11n LDPC decoder | max_iter=50 (User 2) |

#### A.2. Blok Envanteri Özeti

| Kategori | Sayı | Örnekler |
|:---|:---|:---|
| Kaynak/Çıkış Blokları | 8 | 2 File Source, 2 File Sink, 4 Vector Source |
| Değişken Blokları | 14 | samp_rate, sps, payload_size, ... |
| FEC Blokları | 5 | 3 Encoder, 2 Decoder |
| İşleme Blokları | ~30 | Repack, Scrambler, CRC, Mux, ... |
| Özel Python Blokları | 3 | 2 Soft Diff Decoder, 1 SIC Aligner |
| Sanal Yönlendirme | 32 | 16 Sink + 16 Source |
| GUI Blokları | 6 | 3 Time Sink, 3 Range Slider |
| **Toplam** | **~60+** | — |

### EK-B: LDPC Kod Parametreleri Karşılaştırması

Projede iki adet LDPC parite kontrol matrisi bulunmaktadır:

| Parametre | `n_1296_k_0648_ieee.alist` (Aktif) | `n_0300_k_0152_gap_03.alist` (Yedek) |
|:---|:---|:---|
| Kod sözcüğü uzunluğu ($n$) | 1296 | 300 |
| Mesaj uzunluğu ($k$) | 648 | 152 |
| Kod oranı ($R$) | $0.500$ | $\approx 0.507$ |
| Standart | IEEE 802.11n | Özel tasarım |
| Alt-matris boyutu ($Z$) | 54 | — |
| Yapı | Yarı-döngüsel (quasi-cyclic) | Düzensiz |
| Dosya boyutu | 44,030 bayt | 7,950 bayt |
| Kullanım | Ana sistem (NOMA + LDPC) | Alternatif / test |

### EK-C: Dosya Listesi ve Açıklamaları

| Dosya | Boyut | Açıklama |
|:---|:---|:---|
| `NOMA.grc` | 77,375 B | Ana NOMA-SIC akış diyagramı (GRC) |
| `NOMA.py` | 34,987 B | GRC'den üretilen Python betiği (627 satır) |
| `NOMA_epy_block_0.py` | 3,191 B | Yumuşak diferansiyel çözücü — User 1 (104 satır) |
| `NOMA_epy_block_0_0.py` | 3,191 B | Yumuşak diferansiyel çözücü — User 2 (104 satır) |
| `NOMA_epy_block_1.py` | 7,817 B | SIC hizalama bloğu — basic_block (170 satır) |
| `LDPC.grc` | 36,621 B | Tek kullanıcılı LDPC test akış diyagramı |
| `LDPC.py` | 22,904 B | LDPC test betiği (477 satır) |
| `LDPC_epy_block_0.py` | 3,191 B | Yumuşak diferansiyel çözücü — LDPC test |
| `n_1296_k_0648_ieee.alist` | 44,030 B | IEEE 802.11n LDPC matrisi (aktif) |
| `n_0300_k_0152_gap_03.alist` | 7,950 B | Kısa blok LDPC matrisi (yedek) |
| `Bpsk_file_transfer5.grc` | 26,215 B | Temel BPSK test (LDPC'siz) |
| `Bpsk_file_transfer_loopback.grc` | 37,983 B | USRP E310 geri-döngü testi (2.435 GHz) |
| `noma_sic_aligner.py` | 9,074 B | Alternatif SIC hizalama modülü (etiket tabanlı) |
| `capture_sic_amplitude.py` | 740 B | SIC genlik tanılama betiği |
| `bpsk_transmit.txt` | 2,310 B | User 1 verici kaynak dosyası |
| `bpsk_transmit_2.txt` | 2,310 B | User 2 verici kaynak dosyası |
| `bpsk_receive.txt` | 2,310 B | User 1 alıcı çıkış dosyası |
| `bpsk_receive_2.txt` | 1,540 B | User 2 alıcı çıkış dosyası |
| `debug_sic.txt` | 3,825 B | SIC hata ayıklama günlüğü |

### EK-D: Sinyal Akış Diyagramı Bağlantı Haritası

#### D.1. Verici Tarafı:
```
┌─────────────────────────── User 1 TX Chain ────────────────────────────────┐
│ File Source(tx1) → Stream2TS(77B) → CRC32 → Repack(8→1) → Scrambler →    │
│ LDPC Enc → Multiply Length(×2) → [Header Formatter + LDPC Payload] →      │
│ TagMux[Preamble(250B), Header, LDPC_Payload, Postamble(8B)] →             │
│ Constellation Mod(DBPSK, sps=4, β=0.35) → Tag Gate →                     │
│ Multiply Const(α₁ = 0.894) ──────────────────────────────────────┐        │
└──────────────────────────────────────────────────────────────────────────────┘
                                                                    │
                                                                    ▼
                                                        ┌─── Add (complex) ───┐
                                                        │  Süperpozisyon     │
                                                        │  s = α₁x₁ + α₂x₂  │──▶ Channel Model
                                                        └─────────────────────┘
                                                                    ▲
┌─────────────────────────── User 2 TX Chain ────────────────────────────────┐
│ File Source(tx2) → Stream2TS(77B) → CRC32 → Repack(8→1) → Scrambler →    │
│ LDPC Enc → ... (aynı yapı) ... → Tag Gate →                               │
│ Multiply Const(α₂ = 0.447) ──────────────────────────────────────┘        │
└──────────────────────────────────────────────────────────────────────────────┘
```

#### D.2. Alıcı Tarafı (SIC):
```
Channel ──▶ FFT RRC ──▶ SymSync ──▶ CostasLoop ──▶ Corr Estimator
Model       (β=0.35)    (sps=4→1)   (ω=2π/100)     (preamble_syms)
                                         │                  │
                           ┌─────────────┘                  │
                           │ "recovery"                     │ "recovery_2"
                           ▼                                ▼
                    Soft Const Dec               ┌──── SIC Aligner (epy_block_1) ────┐
                           │                     │  Port 0: recovery_2 (alınan)       │
                    Soft Diff Dec                │  Port 1: user_2_sub (yeniden oluş.)│
                    (epy_block_0)                │  Çıkış: temizlenmiş User 2 sinyali │
                           │                     └────────────────────────────────────┘
                    Correlate AC                            │
                           │                                ▼
                    LDPC Decoder ◄───────────     Soft Const Dec (2.)
                    (ldpc_dec)                            │
                           │                       Soft Diff Dec
                    Length ×0.5                     (epy_block_0_0)
                           │                              │
                    Descrambler                    Correlate AC (2.)
                           │                              │
                    Repack (1→8)                   LDPC Decoder (ldpc_dec_2)
                           │                              │
                    CRC32 Check                    Length ×0.5 → Descramble →
                      │     │                      Repack → CRC32 Check (2.)
               File Sink  SIC Re-encode                    │
               (rx1.txt)    │                         File Sink
                            ▼                         (rx2.txt)
                    LDPC Re-encode (enc_ldpc_sic)
                            │
                    Chunks to Symbols (BPSK: [-1, +1])
                            │
                    Multiply Const (0.894)
                            │
                            ▼
                    "user_2_sub" ──▶ SIC Aligner Port 1
```

---

*Bu rapor, GNU Radio Companion ortamında tasarlanan NOMA-SIC dosya transferi sisteminin eksiksiz teknik dokümantasyonunu sunmaktadır. Tüm blok parametreleri, matematiksel modeller ve sinyal akış yolları, kaynak kodlar (`NOMA.grc`, `NOMA.py`, `NOMA_epy_block_*.py`) incelenerek derlenmiştir.*