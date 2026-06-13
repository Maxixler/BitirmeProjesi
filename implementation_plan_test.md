# Akademik Performans Testleri İmplementasyon Planı

Bu plan, BPSK NOMA + LDPC + SIC projesi kapsamında uygunluğu onaylanan akademik performans testlerinin (LLS, SLS, Stres ve Donanımsal/Kanal Kusurları) otomatik test scriptleri aracılığıyla simülasyon ortamında (`NOMA.py`) koşturulması ve sonuçların grafikleştirilmesi/verileştirilmesi sürecini kapsar.

## User Review Required

> [!IMPORTANT]
> - Simülasyon hızı varsayılan olarak `8000` sembol/sn'dir. Sweep testlerinin hızlı çalışabilmesi ve veri bütünlüğünü bozmaması için throttle hızı dinamik olarak `500,000` sembol/sn değerine yükseltilecektir.
> - Tüm test scriptleri, `NOMA.py` dosyasını değiştirmeden önce bir yedeğini alacak (`NOMA.py.bak`) ve test sonlandığında veya kesintiye uğradığında orijinal dosyayı tamamen geri yükleyecektir.
> - Jammer ve RHI gibi kanala yeni bozucu elemanlar ekleyen testler, `NOMA.py` içerisindeki mevcut blok parametrelerini (örneğin noise veya frekans/zamanlama kayması parametrelerini) modifiye ederek veya ek matematiksel terimler enjekte ederek çalıştırılacaktır.

## Open Questions

> [!NOTE]
> Herhangi bir açık soru bulunmamaktadır. Tüm testler doğrudan Python sweep scriptleri vasıtasıyla `NOMA.py` çıktılarının BER analiziyle gerçekleştirilecektir.

## Proposed Changes

Fiziksel katman simülatörümüzün (`NOMA.py`) davranışlarını sweep etmek için 5 adet yeni otomatik test scripti tasarlanacaktır:

---

### [NOMA Test Automation Suite]

#### [NEW] [run_ber_sweep.py](file:///c:/Users/Armagan/Documents/GitHub/BitirmeProjesi/run_ber_sweep.py)
*   **Açıklama:** Kanal gürültü voltajını ($\sigma$) `0.02` ile `0.30` arasında adımlarla tarayarak User 1, User 2 ve BPSK Teorik sınırının BER ($E_b/N_0$) waterfall eğrilerini çıkartır.
*   **Ek Metrikler:**
    - **BLER (CWER) Analizi:** CRC32 hata oranına dayalı blok hata oranını hesaplar.
    - **Outage Probability (OP):** Eşik SNR ($6\text{ dB}$) sınırına göre kesinti olasılığı değerlerini çıkarır.
    - **Ergodic Sum Capacity:** Her iki kullanıcının toplam kapasitesini ($R_1 + R_2$ bps/Hz) hesaplar.
*   **Çıktılar:** `ber_waterfall.csv`, `ber_waterfall.png`

#### [NEW] [run_sic_mismatch_test.py](file:///c:/Users/Armagan/Documents/GitHub/BitirmeProjesi/run_sic_mismatch_test.py)
*   **Açıklama:** SIC aşamasındaki mükemmel olmayan genlik kestirim hatasını ($\epsilon = \%-20$ ile $\%+20$) ve Costas loop faz hatasını ($\Delta \theta = 0^\circ$ ile $30^\circ$) sweep ederek User 2'nin duyarlılığını test eder.
*   **Ek Metrikler:**
    - **Jain's Fairness Index:** Güç ve genlik sapmalarının hız hakkaniyeti üzerindeki etkisini hesaplar.
*   **Çıktılar:** `sic_mismatch_results.csv`, `sic_mismatch_curves.png`

#### [NEW] [run_complexity_test.py](file:///c:/Users/Armagan/Documents/GitHub/BitirmeProjesi/run_complexity_test.py)
*   **Açıklama:** LDPC kod çözücünün maksimum iterasyon limitini (`max_iter = 2` ile `20` arası) tarar ve `time.perf_counter()` ile mikrosaniye bazında CPU çalışma sürelerini ölçer.
*   **Çıktılar:** `complexity_results.csv`, `latency_vs_ber.png`

#### [NEW] [run_jamming_test.py](file:///c:/Users/Armagan/Documents/GitHub/BitirmeProjesi/run_jamming_test.py)
*   **Açıklama:** Kanalda yapay bir jamming (aktif parazit) sinyali simüle etmek için `NOMA.py` üzerindeki gürültü tabanına ek darbeli veya sürekli parazit voltajı ekler ve BPSK karıştırıcının (scrambler) ile LDPC'nin direnç sınırlarını ölçer.
*   **Çıktılar:** `jamming_results.csv`, `jamming_vs_ber.png`

#### [NEW] [run_channel_impairments_test.py](file:///c:/Users/Armagan/Documents/GitHub/BitirmeProjesi/run_channel_impairments_test.py)
*   **Açıklama:** Alıcıda mükemmel olmayan kanal bilgisi (imperfect CSI: $\hat{h} = h + e$) durumunu ve donanımsal kusurları (IQ Imbalance ve Phase Noise) simüle etmek için `NOMA.py` içindeki parametreleri dinamik değiştirerek test eder.
*   **Çıktılar:** `impairments_results.csv`, `impairments_vs_ber.png`

---

## Verification Plan

### Automated Tests
Her bir script, yazıldıktan sonra yerel simülasyon ortamında (`NOMA.py` aracılığıyla) koşturulacak ve çıktılarının (CSV ve PNG grafikleri) doğru üretilip üretilmediği doğrulanacaktır.
- `python run_ber_sweep.py`
- `python run_sic_mismatch_test.py`
- `python run_complexity_test.py`
- `python run_jamming_test.py`
- `python run_channel_impairments_test.py`

### Manual Verification
- Üretilen grafiklerde teorik limit çizgilerinin (Shannon, BPSK sınırı, default çalışma noktaları) doğru konumlandırılıp konumlandırılmadığı manuel incelenecektir.
