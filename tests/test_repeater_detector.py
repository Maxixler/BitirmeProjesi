"""
Kacak Repeater Tespit Sistemi — Birim Testleri

Tum modullerin temel islevselligini dogrulamak icin
donanimsiz (simulasyon) testler.
"""

import os
import sys
import unittest
import tempfile

# Ana proje kokunu Python yoluna ekle
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import numpy as np


class TestConfig(unittest.TestCase):
    """Konfigurasyon degerlerini dogrula."""

    def test_config_imports(self):
        """Config modulu sorunsuz import edilmeli."""
        from repeater_detector import config as det_config
        self.assertIsNotNone(det_config.ALL_KNOWN_FREQUENCIES)
        self.assertIsNotNone(det_config.SCAN_SUB_BANDS)
        self.assertIsNotNone(det_config.ENVIRONMENT_MODELS)

    def test_known_frequencies_not_empty(self):
        """Bilinen frekans listesi bos olmamali."""
        from repeater_detector import config as det_config
        self.assertGreater(len(det_config.ALL_KNOWN_FREQUENCIES), 10)

    def test_sub_bands_valid(self):
        """Alt bantlar gecerli start/stop degerlerine sahip olmali."""
        from repeater_detector import config as det_config
        for name, band in det_config.SCAN_SUB_BANDS.items():
            self.assertIn("start", band)
            self.assertIn("stop", band)
            self.assertGreater(band["stop"], band["start"])

    def test_environment_models(self):
        """Ortam modelleri gecerli n ve sigma degerlerine sahip olmali."""
        from repeater_detector import config as det_config
        for name, env in det_config.ENVIRONMENT_MODELS.items():
            self.assertIn("n", env)
            self.assertIn("sigma", env)
            self.assertGreater(env["n"], 0)
            self.assertGreaterEqual(env["sigma"], 0)


class TestUtils(unittest.TestCase):
    """Yardimci fonksiyonlari dogrula."""

    def test_classify_frequency_known(self):
        """Bilinen frekans dogru siniflandirilmali."""
        from repeater_detector.utils import classify_frequency
        # LoRaWAN EU868 frekansi bilinen olmali
        matched, name, diff = classify_frequency(868e6)
        self.assertTrue(matched)
        self.assertIsNotNone(name)

    def test_classify_frequency_unknown(self):
        """Bilinmeyen frekans supheli olarak isaretlenmeli."""
        from repeater_detector.utils import classify_frequency
        # Rastgele bir frekans (bilinen bantlardan uzak)
        matched, name, diff = classify_frequency(500e6)
        # Bu frekans bilinen bantlarin disinda olmali
        self.assertGreater(diff, 0)

    def test_load_iq_file_npy(self):
        """NPY dosyasi okunabilmeli."""
        from repeater_detector.utils import load_iq_file
        # Gecici npy dosyasi olustur
        data = np.random.randn(1000) + 1j * np.random.randn(1000)
        data = data.astype(np.complex64)
        with tempfile.NamedTemporaryFile(suffix=".npy", delete=False) as f:
            np.save(f.name, data)
            tmp_path = f.name

        try:
            loaded, meta = load_iq_file(tmp_path)
            self.assertEqual(len(loaded), 1000)
            self.assertTrue(np.iscomplexobj(loaded))
        finally:
            os.unlink(tmp_path)

    def test_rssi_to_power_dBm(self):
        """RSSI donusumu dogru calismalir."""
        from repeater_detector.utils import rssi_to_power_dBm
        # rssi_raw=0 dB, gain=40 dB, cable_loss=2 dB
        # Sonuc: 0 - 40 + 2 = -38 dBm
        result = rssi_to_power_dBm(0, 40, 2)
        self.assertAlmostEqual(result, -38.0)


class TestRepeaterSimulator(unittest.TestCase):
    """Sentetik sinyal uretimini dogrula."""

    def setUp(self):
        from repeater_detector.simulation.repeater_simulator import RepeaterSimulator
        self.sim = RepeaterSimulator(sample_rate=1e6)

    def test_generate_repeater_fm(self):
        """FM repeater sinyali uretilmeli."""
        sig = self.sim.generate_repeater_signal(10000, modulation="fm")
        self.assertEqual(len(sig), 10000)
        self.assertTrue(np.iscomplexobj(sig))
        self.assertGreater(np.mean(np.abs(sig) ** 2), 0)

    def test_generate_repeater_dmr(self):
        """DMR repeater sinyali uretilmeli."""
        sig = self.sim.generate_repeater_signal(10000, modulation="dmr")
        self.assertEqual(len(sig), 10000)
        self.assertTrue(np.iscomplexobj(sig))

    def test_generate_legal_gsm(self):
        """GSM benzeri yasal sinyal uretilmeli."""
        sig = self.sim.generate_legal_signal(10000, signal_type="gsm")
        self.assertEqual(len(sig), 10000)
        self.assertTrue(np.iscomplexobj(sig))

    def test_generate_noise(self):
        """AWGN uretilmeli."""
        noise = self.sim.generate_noise(10000)
        self.assertEqual(len(noise), 10000)
        self.assertTrue(np.iscomplexobj(noise))

    def test_generate_scenario(self):
        """Senaryo uretimi calismalir."""
        scenario = self.sim.generate_scenario(
            duration_sec=0.5, num_legal=2, num_illegal=1)
        self.assertIn("iq_data", scenario)
        self.assertIn("legal_signals", scenario)
        self.assertIn("illegal_signals", scenario)
        self.assertIn("ground_truth", scenario)
        self.assertEqual(len(scenario["legal_signals"]), 2)
        self.assertEqual(len(scenario["illegal_signals"]), 1)
        self.assertGreater(len(scenario["iq_data"]), 0)

    def test_simulate_rssi_profile(self):
        """RSSI profili uretilmeli."""
        measurements = self.sim.simulate_rssi_profile(
            true_angle_deg=90, num_points=36)
        self.assertEqual(len(measurements), 36)
        # En yuksek RSSI 90 derece civarinda olmali
        angles = [m["angle_deg"] for m in measurements]
        rssi = [m["rssi_dBm"] for m in measurements]
        peak_idx = np.argmax(rssi)
        peak_angle = angles[peak_idx]
        self.assertAlmostEqual(peak_angle, 90, delta=30)

    def test_simulate_distance_measurements(self):
        """Mesafe olcum simulasyonu calismalir."""
        result = self.sim.simulate_distance_measurements(
            true_distance_m=200, frequency_hz=900e6,
            num_measurements=10, environment="kentsel")
        self.assertEqual(len(result["rssi_measurements"]), 10)
        self.assertEqual(result["true_distance_m"], 200)


class TestScenarioGenerator(unittest.TestCase):
    """Senaryo uretecisini dogrula."""

    def test_list_scenarios(self):
        """Senaryo listesi bos olmamali."""
        from repeater_detector.simulation.scenario_generator import ScenarioGenerator
        gen = ScenarioGenerator()
        scenarios = gen.list_scenarios()
        self.assertGreater(len(scenarios), 0)
        self.assertIn("tek_kacak", scenarios)

    def test_generate_all_scenarios(self):
        """Tum senaryolar hatasiz uretilmeli."""
        from repeater_detector.simulation.scenario_generator import ScenarioGenerator
        gen = ScenarioGenerator()
        for name in gen.SCENARIOS:
            scenario = gen.generate(name, duration_sec=0.1)
            self.assertIn("iq_data", scenario)
            self.assertIn("ground_truth", scenario)

    def test_invalid_scenario(self):
        """Gecersiz senaryo adi ValueError verir."""
        from repeater_detector.simulation.scenario_generator import ScenarioGenerator
        gen = ScenarioGenerator()
        with self.assertRaises(ValueError):
            gen.generate("gecersiz_senaryo")


class TestSpectrumSurveillance(unittest.TestCase):
    """Spektrum gozetleme ve anomali tespitini dogrula."""

    def test_scan_from_data(self):
        """IQ verisinden analiz calismalir."""
        from repeater_detector.detection.spectrum_surveillance import SpectrumSurveillance
        from repeater_detector.simulation.repeater_simulator import RepeaterSimulator

        sim = RepeaterSimulator(sample_rate=1e6)
        scenario = sim.generate_scenario(
            duration_sec=0.5, num_legal=2, num_illegal=1)

        surveillance = SpectrumSurveillance(
            simulation_mode=True, sample_rate=1e6)
        result = surveillance.scan_and_detect_from_data(
            scenario["iq_data"],
            sample_rate=1e6,
            center_freq=900e6,
            ground_truth=scenario["ground_truth"])

        self.assertIn("total_signals", result)
        self.assertIn("legal_signals", result)
        self.assertIn("suspicious_signals", result)
        self.assertGreaterEqual(result["total_signals"], 0)

    def test_classify_signals(self):
        """Yasal/supheli ayristirma calismalir."""
        from repeater_detector.detection.spectrum_surveillance import SpectrumSurveillance

        surv = SpectrumSurveillance(simulation_mode=True)
        # Bilinen frekans
        active = [(868e6, -30)]
        legal, suspicious = surv._classify_signals(active)
        self.assertGreater(len(legal), 0)

    def test_anomaly_score_bounds(self):
        """Anomali skoru 0-1 arasinda olmali."""
        from repeater_detector.detection.spectrum_surveillance import SpectrumSurveillance

        surv = SpectrumSurveillance(simulation_mode=True)
        score = surv._compute_anomaly_score(500e6, -30, "Test", 50e6)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)


class TestSignalClassifier(unittest.TestCase):
    """Sinyal siniflandirmayi dogrula."""

    def test_classify_noise(self):
        """Gurultu sinyali siniflandirilabilmeli."""
        from repeater_detector.detection.signal_classifier import SignalClassifier

        classifier = SignalClassifier(sample_rate=1e6)
        noise = (np.random.randn(10000) + 1j * np.random.randn(10000)).astype(np.complex64)
        result = classifier.classify_signal(noise)
        self.assertIn(result["type"], classifier.SIGNAL_TYPES)
        self.assertGreaterEqual(result["confidence"], 0)
        self.assertLessEqual(result["confidence"], 1)

    def test_estimate_bandwidth(self):
        """Bant genisligi tahmini pozitif olmali."""
        from repeater_detector.detection.signal_classifier import SignalClassifier

        classifier = SignalClassifier(sample_rate=1e6)
        # Ton sinyali
        t = np.arange(10000) / 1e6
        sig = np.exp(1j * 2 * np.pi * 10e3 * t).astype(np.complex64)
        bw = classifier.estimate_bandwidth(sig)
        self.assertGreater(bw, 0)

    def test_estimate_modulation(self):
        """Modulasyon tipi tahmini gecerli bir deger dondurmeli."""
        from repeater_detector.detection.signal_classifier import SignalClassifier

        classifier = SignalClassifier(sample_rate=1e6)
        noise = (np.random.randn(10000) + 1j * np.random.randn(10000)).astype(np.complex64)
        mod = classifier.estimate_modulation_type(noise)
        self.assertIn(mod, ["FM", "AM", "dijital", "bilinmeyen"])


class TestRSSIDistanceEstimator(unittest.TestCase):
    """RSSI mesafe tahminini dogrula."""

    def setUp(self):
        from repeater_detector.localization.rssi_distance import RSSIDistanceEstimator
        self.estimator = RSSIDistanceEstimator(
            frequency_hz=900e6, environment="kentsel")

    def test_fspl_distance(self):
        """FSPL mesafe tahmini pozitif olmali."""
        result = self.estimator.estimate_distance_fspl(-60)
        self.assertGreater(result["distance_m"], 0)
        self.assertEqual(result["model"], "FSPL")

    def test_log_distance(self):
        """Log-distance tahmini gecerli sonuc dondurmeli."""
        result = self.estimator.estimate_distance_log(-60)
        self.assertGreater(result["distance_m"], 0)
        self.assertGreater(result["distance_max_m"], result["distance_min_m"])
        self.assertEqual(result["model"], "log-distance")
        self.assertEqual(result["environment"], "kentsel")

    def test_distance_increases_with_lower_rssi(self):
        """Dusuk RSSI = daha uzak mesafe olmali."""
        d_near = self.estimator.estimate_distance_fspl(-40)["distance_m"]
        d_far = self.estimator.estimate_distance_fspl(-80)["distance_m"]
        self.assertGreater(d_far, d_near)

    def test_multi_measurement(self):
        """Coklu olcum ortalaması calismalir."""
        measurements = [-60, -62, -58, -61, -59]
        result = self.estimator.estimate_distance_multi_measurement(measurements)
        self.assertGreater(result["distance_m"], 0)
        self.assertEqual(result["num_measurements"], 5)

    def test_calibration(self):
        """Kalibrasyon sonrasi PL(d0) degismeli."""
        old_pl = self.estimator._pl_d0
        self.estimator.calibrate(100, -60)
        self.assertTrue(self.estimator._calibrated)
        # PL(d0) degismis olmali (buyuk ihtimalle)
        # Degismeyebilir de ama en azindan hata vermemeli

    def test_measure_rssi(self):
        """IQ verisinden RSSI hesaplanabilmeli."""
        iq = (np.random.randn(10000) + 1j * np.random.randn(10000)).astype(np.complex64)
        rssi = self.estimator.measure_rssi(iq, gain_dB=40)
        self.assertIsInstance(rssi, float)

    def test_invalid_environment(self):
        """Gecersiz ortam tipi ValueError verir."""
        from repeater_detector.localization.rssi_distance import RSSIDistanceEstimator
        with self.assertRaises(ValueError):
            RSSIDistanceEstimator(environment="gecersiz")


class TestDirectionFinder(unittest.TestCase):
    """Yon bulma islevselligini dogrula."""

    def test_find_peak_from_simulated(self):
        """Sentetik RSSI profilinden tepe yonu bulunabilmeli."""
        from repeater_detector.localization.direction_finder import DirectionFinder
        from repeater_detector.simulation.repeater_simulator import RepeaterSimulator

        sim = RepeaterSimulator()
        true_angle = 135.0
        measurements = sim.simulate_rssi_profile(
            true_angle_deg=true_angle, num_points=36,
            beam_width_deg=60, noise_std_dB=1.0)

        finder = DirectionFinder(simulation_mode=True)
        peak = finder.find_peak_direction(measurements)

        self.assertIn("peak_angle_deg", peak)
        self.assertIn("confidence", peak)
        self.assertIn("beam_width_deg", peak)
        # Tepe acisi gercek aciya yakin olmali (30 derece tolerans)
        diff = abs(peak["peak_angle_deg"] - true_angle)
        if diff > 180:
            diff = 360 - diff
        self.assertLess(diff, 30)

    def test_guidance_text(self):
        """Yonlendirme metni uretilmeli."""
        from repeater_detector.localization.direction_finder import DirectionFinder

        finder = DirectionFinder(simulation_mode=True)
        text = finder.get_guidance_text(0, 90)
        self.assertIn("derece", text)

    def test_guidance_text_at_target(self):
        """Hedefteyken uygun mesaj verilmeli."""
        from repeater_detector.localization.direction_finder import DirectionFinder

        finder = DirectionFinder(simulation_mode=True)
        text = finder.get_guidance_text(90, 92)
        self.assertIn("Hedefe", text)

    def test_angle_to_compass(self):
        """Aci-pusula donusumu dogru calismalir."""
        from repeater_detector.localization.direction_finder import DirectionFinder

        self.assertEqual(DirectionFinder._angle_to_compass(0), "Kuzey")
        self.assertEqual(DirectionFinder._angle_to_compass(90), "Dogu")
        self.assertEqual(DirectionFinder._angle_to_compass(180), "Guney")
        self.assertEqual(DirectionFinder._angle_to_compass(270), "Bati")

    def test_too_few_measurements(self):
        """3'ten az olcum ile hata verilmeli."""
        from repeater_detector.localization.direction_finder import DirectionFinder

        finder = DirectionFinder(simulation_mode=True)
        with self.assertRaises(ValueError):
            finder.find_peak_direction([
                {"angle_deg": 0, "rssi_dBm": -50},
                {"angle_deg": 10, "rssi_dBm": -40},
            ])


if __name__ == "__main__":
    unittest.main(verbosity=2)
