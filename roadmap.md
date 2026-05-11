Sistem Mimarisi ve Geliştirme Yol Haritası
Bu doküman, mevcut çalışan Fiziksel Katman (PHY) altyapısının üzerine eklenecek olan NOMA, AMC ve HARQ modüllerinin entegrasyon sırasını, bu modüllerin çalışma prensiplerini ve mimari kararların gerekçelerini açıklamaktadır.

Sistem, tek yönlü ve sabit modülasyonlu bir yapıdan (BPSK + LDPC), kanal durumuna göre kendini adapte edebilen ve aynı spektrumu birden fazla kullanıcıya paylaştırabilen akıllı bir MAC/PHY hibrid yapısına dönüştürülecektir. Kapalı çevrim (closed-loop) sistemlerin gerektirdiği durum makinesi (state machine) zorluklarını aşmak adına aşağıdaki kronolojik sıra izlenecektir.

Aşama 1: Açık Çevrim NOMA (Open-Loop NOMA)
Öncelik: 1
Bağımlılıklar: Çalışan, senkronize edilmiş baz PHY katmanı (Preamble + Payload + LDPC + Scrambler).

Nedir? Aynı zaman ve frekans kaynağının, farklı güç seviyeleri (Power Domain) kullanılarak birden fazla kullanıcıya tahsis edilmesidir.

Verici (Tx) Tarafı: İki farklı veri akışı (Güçlü ve Zayıf kullanıcı için) farklı güç katsayılarıyla çarpılarak toplanır (Superposition Coding).

Alıcı (Rx) Tarafı: Alıcı, önce yüksek güçlü sinyali çözer, yeniden modüle eder ve ana sinyalden çıkarır (SIC - Successive Interference Cancellation). Ardından geriye kalan düşük güçlü sinyali çözer.

Neden İlk Sırada?
Bu modül alıcıdan vericiye herhangi bir geri bildirim (feedback) gerektirmez. Mevcut tek yönlü (simplex) GNU Radio akış yapısına doğrudan entegre edilebilir ve projenin ana akademik hedefini en erken aşamada doğrular.

Aşama 2: Geri Besleme Hattı (Feedback Bridge)
Öncelik: 2
Bağımlılıklar: Aşama 1 (NOMA).

Nedir?
Sistemin tek yönlü (Simplex) iletişimden yarı-çift yönlü (Half-Duplex / TDD) iletişime geçirilmesidir. Alıcının sinyal gürültü oranını (SNR), kanal kalite göstergesini (CQI) veya paketin CRC sonucunu (ACK/NACK) vericiye bildirdiği kontrol hattıdır.

Neden İkinci Sırada?
GNU Radio'nun standart akış (streaming) mimarisi geriye dönük veri iletimini desteklemez. Sistemdeki zekayı (AMC ve HARQ) çalıştırabilmek için PDU (Protocol Data Unit) mesajlaşma bloklarının ve USRP'nin Tx/Rx geçiş (turnaround) mekanizmalarının bu aşamada oturtulması şarttır.

Aşama 3: AMC (Adaptif Modülasyon ve Kodlama)
Öncelik: 3
Bağımlılıklar: Aşama 2 (Geri Besleme Hattı).

Nedir?
Kablosuz kanalın anlık durumuna (alıcıdan gelen SNR / CQI mesajlarına) göre iletim parametrelerinin dinamik olarak değiştirilmesidir.

İyi Kanal Durumu: Sistem yüksek dereceli modülasyonlara (örn. 16-QAM) ve yüksek LDPC kod oranlarına geçer. Veri hızı (throughput) maksimize edilir.

Kötü Kanal Durumu: Sistem dayanıklı modülasyonlara (BPSK/QPSK) ve düşük kod oranlarına (örn. Rate 1/3) düşerek bağlantının kopmasını engeller.

Neden Üçüncü Sırada?
Geri besleme hattı kurulduktan sonra uygulanması en mantıklı ilk dinamik kontrolcüdür. Hafıza (buffer) yönetimi gerektirmediği için donanıma entegrasyonu nispeten kolaydır ve NOMA ile birleştiğinde kullanıcılara dinamik kapasite tahsisi sağlar.

Aşama 4: HARQ (Hibrit Otomatik Tekrar İsteği - Soft Combining)
Öncelik: 4 (Final Fazı)
Bağımlılıklar: Aşama 2 (Geri Besleme Hattı) ve hatasız çalışan LDPC yapısı.

Nedir?
Klasik ARQ sistemlerindeki "hatalı paketi tamamen çöpe atma" israfını önleyen, FEC (LDPC) ve ARQ'nun birleşimidir. Hatalı gelen paketin Yumuşak Karar (LLR - Log-Likelihood Ratio) değerleri alıcıda bir RAM tamponunda (Soft Buffer) saklanır. Verici aynı paketi (Chase Combining) veya ek parite bitlerini (Incremental Redundancy) tekrar gönderdiğinde, alıcı yeni gelen LLR'lar ile hafızadaki LLR'ları toplayarak LDPC dekoderine besler.

Neden Son Sırada?
Sistemin mühendislik açısından en zorlayıcı kısmıdır. GNU Radio'nun akan veri (streaming) doğasına aykırı olan "veriyi hafızada bekletme ve durum makinesi (state machine) ile tekrar işleme" mimarisini gerektirir. Özel C++ (OOT) blokları veya optimize edilmiş Python bellek yönetimi gerektirdiği için sistemin en son ve en olgun fazında eklenmelidir.