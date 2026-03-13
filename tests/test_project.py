"""
USRP NOMA Projesi Unit Testleri

NOMA, analiz ve deep learning modullerinin temel birim testleri.
"""

import os
import sys
import unittest

import numpy as np

# Proje kokunu path'e ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestNOMAModulation(unittest.TestCase):
    """NOMA modulasyon testleri."""

    def test_constellations_exist(self):
        from usrp_noma.noma.modulation import CONSTELLATIONS
        self.assertIn("QPSK", CONSTELLATIONS)
        self.assertIn("16QAM", CONSTELLATIONS)
        self.assertIn("64QAM", CONSTELLATIONS)

    def test_qpsk_size(self):
        from usrp_noma.noma.modulation import CONSTELLATIONS
        self.assertEqual(len(CONSTELLATIONS["QPSK"]), 4)

    def test_16qam_size(self):
        from usrp_noma.noma.modulation import CONSTELLATIONS
        self.assertEqual(len(CONSTELLATIONS["16QAM"]), 16)

    def test_64qam_size(self):
        from usrp_noma.noma.modulation import CONSTELLATIONS
        self.assertEqual(len(CONSTELLATIONS["64QAM"]), 64)

    def test_unit_energy(self):
        """Konstelasyonlar birim enerji normalize olmali."""
        from usrp_noma.noma.modulation import CONSTELLATIONS
        for name, const in CONSTELLATIONS.items():
            avg_energy = np.mean(np.abs(const) ** 2)
            self.assertAlmostEqual(avg_energy, 1.0, places=5,
                                   msg=f"{name} birim enerji degil: {avg_energy}")


class TestNOMATransmitter(unittest.TestCase):
    """NOMA verici testleri."""

    def setUp(self):
        from usrp_noma.noma.transmitter import NOMATransmitter
        self.tx = NOMATransmitter(num_users=2, modulation="QPSK")

    def test_power_coefficients_sum(self):
        """Guc katsayilari toplamı 1 olmali."""
        total = sum(self.tx.power_coefficients)
        self.assertAlmostEqual(total, 1.0, places=5)

    def test_transmit_frame_output(self):
        combined, bits_list, symbols_list = self.tx.transmit_frame(num_bits=256)
        self.assertEqual(len(bits_list), 2)
        self.assertEqual(len(symbols_list), 2)
        self.assertGreater(len(combined), 0)

    def test_modulate_demodulate(self):
        """Modulasyon/demodulasyon dogrulugu."""
        bits = self.tx.generate_random_bits(100)
        symbols = self.tx.modulate(bits)
        constellation = self.tx.get_constellation_points()
        # Her sembol icin demodulasyon (tek sembol destegi)
        all_decoded = []
        for s in symbols:
            decoded = self.tx.demodulate_to_bits(s, constellation)
            all_decoded.extend(decoded)
        all_decoded = np.array(all_decoded)
        np.testing.assert_array_equal(bits[:len(all_decoded)], all_decoded[:len(bits)])


class TestNOMAReceiver(unittest.TestCase):
    """NOMA alici SIC testleri."""

    def test_awgn_power(self):
        """AWGN ekleme gurutu seviyesi kontrolu."""
        from usrp_noma.noma.receiver import NOMAReceiver
        rx = NOMAReceiver(num_users=2, modulation="QPSK")
        signal = np.ones(10000, dtype=complex)
        noisy = rx.add_awgn(signal, snr_dB=100)
        # Yuksek SNR'da sinyal yakin olmali
        self.assertAlmostEqual(np.mean(np.abs(noisy - signal) ** 2), 0.0, places=3)

    def test_sic_decode_returns_correct_count(self):
        """SIC decode kullanici sayisi kadar sonuc donmeli."""
        from usrp_noma.noma.transmitter import NOMATransmitter
        from usrp_noma.noma.receiver import NOMAReceiver
        tx = NOMATransmitter(num_users=2, modulation="QPSK")
        rx = NOMAReceiver(num_users=2, modulation="QPSK")
        combined, _, _ = tx.transmit_frame(num_bits=256)
        noisy = rx.add_awgn(combined, snr_dB=30)
        decoded = rx.sic_decode(noisy)
        self.assertEqual(len(decoded), 2)

    def test_ber_high_snr(self):
        """Yuksek SNR'da BER dusuk olmali."""
        from usrp_noma.noma.transmitter import NOMATransmitter
        from usrp_noma.noma.receiver import NOMAReceiver
        tx = NOMATransmitter(num_users=2, modulation="QPSK")
        rx = NOMAReceiver(num_users=2, modulation="QPSK")
        combined, orig_bits, _ = tx.transmit_frame(num_bits=1024)
        noisy = rx.add_awgn(combined, snr_dB=30)
        decoded = rx.sic_decode(noisy)
        for u in range(2):
            n = min(len(orig_bits[u]), len(decoded[u]))
            ber = rx.calculate_ber(orig_bits[u][:n], decoded[u][:n])
            self.assertLess(ber, 0.05, f"Kullanici {u} BER cok yuksek: {ber}")


class TestUtils(unittest.TestCase):
    """Yardimci fonksiyon testleri."""

    def test_linear_to_dB(self):
        from usrp_noma.utils import linear_to_dB
        self.assertAlmostEqual(linear_to_dB(10.0), 10.0, places=5)
        self.assertAlmostEqual(linear_to_dB(100.0), 20.0, places=5)

    def test_dB_to_linear(self):
        from usrp_noma.utils import dB_to_linear
        self.assertAlmostEqual(dB_to_linear(10.0), 10.0, places=5)
        self.assertAlmostEqual(dB_to_linear(20.0), 100.0, places=3)

    def test_freq_to_str(self):
        from usrp_noma.utils import freq_to_str
        self.assertEqual(freq_to_str(868e6), "868.000 MHz")
        self.assertEqual(freq_to_str(2.4e9), "2.400 GHz")
        self.assertEqual(freq_to_str(125e3), "125.000 kHz")


class TestDataAnalysis(unittest.TestCase):
    """Veri analizi testleri."""

    def test_compute_statistics(self):
        from usrp_noma.analysis.data_analysis import IQDataAnalyzer
        analyzer = IQDataAnalyzer(sample_rate=1e6)
        iq = (np.random.randn(1000) + 1j * np.random.randn(1000)).astype(np.complex64)
        stats = analyzer.compute_statistics(iq)
        self.assertIn("amplitude_mean", stats)
        self.assertIn("power_mean_dB", stats)
        self.assertIn("kurtosis", stats)
        self.assertEqual(stats["num_samples"], 1000)

    def test_extract_features(self):
        from usrp_noma.analysis.data_analysis import IQDataAnalyzer
        analyzer = IQDataAnalyzer(sample_rate=1e6)
        iq = (np.random.randn(4096) + 1j * np.random.randn(4096)).astype(np.complex64)
        features = analyzer.extract_features(iq)
        self.assertEqual(len(features), 25)  # 10 + 10 + 5


class TestSyntheticData(unittest.TestCase):
    """Sentetik veri uretim testleri."""

    def test_lora_signal(self):
        from usrp_noma.analysis.synthetic_data import SyntheticDataGenerator
        gen = SyntheticDataGenerator()
        signal = gen.generate_lora_signal(4096, sf=7, snr_dB=15)
        self.assertEqual(len(signal), 4096)
        self.assertTrue(np.iscomplexobj(signal))

    def test_noma_signal(self):
        from usrp_noma.analysis.synthetic_data import SyntheticDataGenerator
        gen = SyntheticDataGenerator()
        signal = gen.generate_noma_signal(4096, num_users=2, snr_dB=15)
        self.assertEqual(len(signal), 4096)

    def test_dataset_generation(self):
        from usrp_noma.analysis.synthetic_data import SyntheticDataGenerator
        gen = SyntheticDataGenerator()
        data, labels, snrs, class_names = gen.generate_dataset(
            samples_per_class=12, num_samples_per_signal=256, snr_range_dB=[0, 10]
        )
        self.assertEqual(len(class_names), 5)
        self.assertEqual(data.shape[1], 256)
        self.assertEqual(len(labels), len(data))


class TestDeepLearningModels(unittest.TestCase):
    """Deep Learning model testleri."""

    def test_cnn_forward(self):
        import torch
        from usrp_noma.deep_learning.models import SignalClassifierCNN
        model = SignalClassifierCNN(num_classes=5, input_length=4096)
        x = torch.randn(4, 2, 4096)  # batch=4, channels=2 (I/Q), length=4096
        output = model(x)
        self.assertEqual(output.shape, (4, 5))

    def test_resnet_forward(self):
        import torch
        from usrp_noma.deep_learning.models import SignalResNet
        model = SignalResNet(num_classes=5, input_length=4096)
        x = torch.randn(4, 2, 4096)
        output = model(x)
        self.assertEqual(output.shape, (4, 5))


if __name__ == "__main__":
    unittest.main()
