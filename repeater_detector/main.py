#!/usr/bin/env python3
"""
SDR Tabanli Kacak Repeater Tespit Sistemi — CLI Giris Noktasi

Kullanim:
    python repeater_detector/main.py info
    python repeater_detector/main.py scan --sim --scenario tek_kacak --plot
    python repeater_detector/main.py scan --input data/capture.npy --freq 900e6
    python repeater_detector/main.py monitor --sim --interval 5
    python repeater_detector/main.py distance --freq 900e6 --rssi -65 --env kentsel --plot
    python repeater_detector/main.py direction --freq 900e6 --sim --true-angle 135 --plot
    python repeater_detector/main.py simulate --scenario coklu_kacak --plot
    python repeater_detector/main.py report --input results/repeater_reports/scan.json
    python repeater_detector/main.py path-loss --freq 900e6 --save pathloss.png
"""

import argparse
import os
import sys

# Ana proje kokunu Python yoluna ekle
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from usrp_noma.utils import setup_logger, freq_to_str
from repeater_detector import config as det_config


logger = setup_logger("repeater_detector.main")


# ---------------------------------------------------------------------------
# Yardimci
# ---------------------------------------------------------------------------

def detect_mode():
    """Calisma modunu otomatik algila (embedded/network)."""
    import platform
    hostname = platform.node().lower()
    if "e3" in hostname or "ettus" in hostname:
        return "embedded"
    if os.path.exists("/etc/uhd"):
        return "embedded"
    return "network"


def parse_freq(value):
    """Frekans dizesini float'a cevirir (K/M/G destegi)."""
    value = str(value).strip().upper()
    multipliers = {"K": 1e3, "M": 1e6, "G": 1e9}
    for suffix, mult in multipliers.items():
        if value.endswith(suffix):
            return float(value[:-1]) * mult
    return float(value)


# ---------------------------------------------------------------------------
# Komut isleyicileri
# ---------------------------------------------------------------------------

def cmd_info(args):
    """Sistem ve konfigurasyon bilgilerini gosterir."""
    print("=" * 55)
    print("  KACAK REPEATER TESPIT SISTEMI — Bilgi")
    print("=" * 55)
    print(f"  Versiyon        : {__import__('repeater_detector').__version__}")
    print(f"  Simulasyon modu : {'Evet' if args.sim else 'Hayir'}")
    print()

    print("  Alt Bantlar:")
    for name, band in det_config.SCAN_SUB_BANDS.items():
        print(f"    {name:20s} : {band['start']/1e6:.0f} - "
              f"{band['stop']/1e6:.0f} MHz (adim: {band['step']/1e3:.0f} kHz)")

    print(f"\n  Bilinen Frekans Sayisi: {len(det_config.ALL_KNOWN_FREQUENCIES)}")
    print(f"  Anomali Esigi     : {det_config.ANOMALY_POWER_THRESHOLD_DB} dB")
    print(f"  Tolerans          : {det_config.ANOMALY_BW_TOLERANCE_HZ/1e3:.0f} kHz")

    print(f"\n  Ortam Modelleri:")
    for name, env in det_config.ENVIRONMENT_MODELS.items():
        print(f"    {name:16s} : n={env['n']}, sigma={env['sigma']} dB "
              f"— {env['aciklama']}")

    if not args.sim:
        try:
            from usrp_noma.core import USRPController
            mode = args.mode or detect_mode()
            with USRPController(mode=mode, addr=args.addr) as ctrl:
                info = ctrl.device_info()
                print("\n  USRP Bilgileri:")
                for k, v in info.items():
                    print(f"    {k:20s} : {v}")
        except Exception as e:
            print(f"\n  USRP baglantisi yok: {e}")

    print("=" * 55)


def cmd_scan(args):
    """Tek seferlik bant taramasi + kacak repeater tespiti."""
    from repeater_detector.detection.spectrum_surveillance import SpectrumSurveillance

    if args.input:
        # Dosyadan analiz (GNU Radio / .npy)
        from repeater_detector.utils import load_iq_file
        print(f"Dosyadan analiz: {args.input}")
        iq_data, meta = load_iq_file(args.input)
        sr = meta.get("sample_rate", det_config.DEFAULT_SAMPLE_RATE)
        cf = args.freq or meta.get("center_freq", 0)

        surveillance = SpectrumSurveillance(sample_rate=sr)
        result = surveillance.scan_and_detect_from_data(
            iq_data, sample_rate=sr, center_freq=cf,
            threshold_dB=args.threshold)

    elif args.sim:
        # Simulasyon modu
        from repeater_detector.simulation.repeater_simulator import RepeaterSimulator
        from repeater_detector.simulation.scenario_generator import ScenarioGenerator

        simulator = RepeaterSimulator()
        scenario_name = args.scenario or "tek_kacak"
        scenario = ScenarioGenerator(simulator).generate(
            scenario_name, duration_sec=args.duration)

        surveillance = SpectrumSurveillance(
            simulation_mode=True,
            sample_rate=scenario["sample_rate"])
        result = surveillance.scan_and_detect_from_data(
            scenario["iq_data"],
            sample_rate=scenario["sample_rate"],
            center_freq=scenario["center_freq"],
            threshold_dB=args.threshold,
            ground_truth=scenario["ground_truth"])

        print(f"\nSenaryo: {scenario_name}")
        print(f"  Yasal sinyal: {scenario['ground_truth']['total_legal']}")
        print(f"  Kacak sinyal: {scenario['ground_truth']['total_illegal']}")

    else:
        # Donanim modu
        from usrp_noma.core import USRPController
        mode = args.mode or detect_mode()
        with USRPController(mode=mode, addr=args.addr) as ctrl:
            surveillance = SpectrumSurveillance(controller=ctrl)
            result = surveillance.scan_and_detect(
                band=args.band, threshold_dB=args.threshold,
                dwell_time=args.dwell)

    # Sonuclari goster
    _print_scan_result(result)

    # Grafik
    if args.plot or args.save:
        save_path = args.save or os.path.join(
            det_config.SURVEILLANCE_REPORT_DIR, "scan_result.png")
        surveillance.plot_surveillance_results(result, save_path=save_path)
        print(f"\nGrafik: {save_path}")

    # Disari aktar
    if args.export:
        from repeater_detector.utils import generate_report
        rp = generate_report(result)
        print(f"Rapor: {rp}")


def cmd_monitor(args):
    """Surekli gozetleme modu."""
    from repeater_detector.detection.spectrum_surveillance import SpectrumSurveillance

    print("=" * 55)
    print("  SUREKLI GOZETLEME MODU")
    print(f"  Aralik: {args.interval}s | Bant: {args.band}")
    print("  Durdurmak icin Ctrl+C basin")
    print("=" * 55)

    scan_count = [0]

    def on_result(result):
        scan_count[0] += 1
        suspicious = result.get("suspicious_signals", [])
        print(f"\n[Tarama #{scan_count[0]}] {result['scan_time']} | "
              f"Aktif: {result['total_signals']} | "
              f"Supheli: {len(suspicious)}")
        if suspicious:
            for sig in suspicious:
                print(f"  ! {freq_to_str(sig['freq'])} | "
                      f"{sig['power_dB']:.1f} dB | "
                      f"Skor: {sig['anomaly_score']:.2f} "
                      f"({sig['confidence_level']})")

    if args.sim:
        print("\n  [SIMULASYON MODU — sentetik taramalar]")
        from repeater_detector.simulation.repeater_simulator import RepeaterSimulator
        from repeater_detector.simulation.scenario_generator import ScenarioGenerator

        simulator = RepeaterSimulator()
        gen = ScenarioGenerator(simulator)
        surveillance = SpectrumSurveillance(simulation_mode=True)

        try:
            import time
            scenarios = list(gen.SCENARIOS.keys())
            while True:
                for sc_name in scenarios:
                    scenario = gen.generate(sc_name)
                    result = surveillance.scan_and_detect_from_data(
                        scenario["iq_data"],
                        sample_rate=scenario["sample_rate"],
                        center_freq=scenario["center_freq"],
                        ground_truth=scenario["ground_truth"])
                    on_result(result)
                    time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nGozetleme durduruldu.")
    else:
        from usrp_noma.core import USRPController
        mode = args.mode or detect_mode()
        with USRPController(mode=mode, addr=args.addr) as ctrl:
            surveillance = SpectrumSurveillance(controller=ctrl)
            try:
                surveillance.continuous_surveillance(
                    callback=on_result,
                    interval_sec=args.interval,
                    band=args.band)
                # Ana thread'i canli tut
                import time
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                surveillance.stop_surveillance()
                print("\nGozetleme durduruldu.")


def cmd_distance(args):
    """RSSI'dan mesafe tahmini."""
    from repeater_detector.localization.rssi_distance import RSSIDistanceEstimator

    estimator = RSSIDistanceEstimator(
        frequency_hz=args.freq,
        tx_power_dBm=args.tx_power,
        environment=args.env)

    if args.rssi is not None:
        # Manuel RSSI degeri
        rssi = args.rssi
        print(f"\nManuel RSSI: {rssi:.1f} dBm")

    elif args.input:
        # Dosyadan RSSI hesapla
        from repeater_detector.utils import load_iq_file
        iq_data, meta = load_iq_file(args.input)
        rssi = estimator.measure_rssi(iq_data, gain_dB=args.gain)
        print(f"\nDosyadan RSSI: {rssi:.1f} dBm ({args.input})")

    elif not args.sim:
        # Donanim ile olcum
        from usrp_noma.core import USRPController, SignalCapture
        mode = args.mode or detect_mode()
        with USRPController(mode=mode, addr=args.addr) as ctrl:
            capture = SignalCapture(ctrl)
            measurements = []
            for i in range(args.measurements):
                iq_data = capture.capture(
                    duration_sec=args.duration, freq=args.freq, gain=args.gain)
                r = estimator.measure_rssi(iq_data, gain_dB=args.gain)
                measurements.append(r)
                print(f"  Olcum {i+1}/{args.measurements}: {r:.1f} dBm")

            rssi = float(sum(measurements) / len(measurements))
            print(f"\nOrtalama RSSI: {rssi:.1f} dBm")
    else:
        # Simulasyon
        from repeater_detector.simulation.repeater_simulator import RepeaterSimulator
        sim = RepeaterSimulator()
        sim_data = sim.simulate_distance_measurements(
            true_distance_m=args.sim_distance or 500,
            frequency_hz=args.freq,
            environment=args.env)
        rssi = float(sum(sim_data["rssi_measurements"]) /
                     len(sim_data["rssi_measurements"]))
        print(f"\nSimulasyon RSSI: {rssi:.1f} dBm "
              f"(gercek mesafe: {sim_data['true_distance_m']}m)")

    # Mesafe tahmini
    print(f"\n{'='*50}")
    print("  MESAFE TAHMINI")
    print(f"{'='*50}")

    fspl = estimator.estimate_distance_fspl(rssi)
    log_d = estimator.estimate_distance_log(rssi)

    print(f"  Frekans     : {args.freq/1e6:.1f} MHz")
    print(f"  RSSI        : {rssi:.1f} dBm")
    print(f"  Yol Kaybi   : {fspl['path_loss_dB']:.1f} dB")
    print()
    print(f"  FSPL Modeli : {fspl['distance_m']:.1f} m")
    print(f"  Log-Dist    : {log_d['distance_m']:.1f} m "
          f"({log_d['distance_min_m']:.0f} - {log_d['distance_max_m']:.0f} m)")
    print(f"  Ortam       : {log_d['environment']} — {log_d['environment_desc']}")
    print(f"{'='*50}")

    if args.plot or args.save:
        save_path = args.save or os.path.join(
            det_config.SURVEILLANCE_REPORT_DIR, "distance_estimate.png")
        estimator.plot_distance_estimate(rssi, save_path=save_path)
        print(f"Grafik: {save_path}")


def cmd_direction(args):
    """Interaktif yon bulma oturumu."""
    from repeater_detector.localization.direction_finder import DirectionFinder

    sim_mode = args.sim
    controller = None

    if not sim_mode:
        from usrp_noma.core import USRPController
        mode = args.mode or detect_mode()
        controller = USRPController(mode=mode, addr=args.addr)
        controller.connect()

    try:
        finder = DirectionFinder(
            controller=controller,
            num_measurements=args.steps,
            measurement_duration=args.duration,
            simulation_mode=sim_mode)

        if sim_mode and args.true_angle is not None:
            finder._sim_true_angle = args.true_angle

        peak = finder.interactive_direction_finding(
            freq=args.freq, gain=args.gain)

        if args.plot or args.save:
            save_path = args.save or os.path.join(
                det_config.SURVEILLANCE_REPORT_DIR, "direction_polar.png")
            finder.plot_polar_rssi(save_path=save_path)
            print(f"Kutupsal grafik: {save_path}")

            # Kartezyen grafik de uret
            cart_path = save_path.replace(".png", "_cartesian.png")
            finder.plot_rssi_vs_angle(save_path=cart_path)
            print(f"Kartezyen grafik: {cart_path}")

    finally:
        if controller is not None:
            controller.close()


def cmd_simulate(args):
    """Senaryo simulasyonu (donanimsiz demo)."""
    from repeater_detector.simulation.repeater_simulator import RepeaterSimulator
    from repeater_detector.simulation.scenario_generator import ScenarioGenerator
    from repeater_detector.detection.spectrum_surveillance import SpectrumSurveillance

    simulator = RepeaterSimulator()
    gen = ScenarioGenerator(simulator)

    if args.list:
        print("\nMevcut Senaryolar:")
        print("-" * 50)
        for name, desc in gen.list_scenarios().items():
            print(f"  {name:20s} : {desc}")
        return

    scenario = gen.generate(args.scenario, duration_sec=args.duration)

    print(f"\n{'='*55}")
    print(f"  SENARYO: {args.scenario}")
    print(f"{'='*55}")
    print(f"  Sure         : {scenario['duration_sec']:.1f} s")
    print(f"  Merkez Frek  : {freq_to_str(scenario['center_freq'])}")
    print(f"  Yasal Sinyal : {scenario['ground_truth']['total_legal']}")
    print(f"  Kacak Sinyal : {scenario['ground_truth']['total_illegal']}")

    # Tespit
    surveillance = SpectrumSurveillance(
        simulation_mode=True,
        sample_rate=scenario["sample_rate"])
    result = surveillance.scan_and_detect_from_data(
        scenario["iq_data"],
        sample_rate=scenario["sample_rate"],
        center_freq=scenario["center_freq"],
        ground_truth=scenario["ground_truth"])

    _print_scan_result(result)

    # Dogruluk
    acc = result.get("detection_accuracy")
    if acc:
        print(f"\n  Tespit Dogrulugu:")
        print(f"    Gercek kacak     : {acc['true_illegal_count']}")
        print(f"    Tespit edilen    : {acc['detected_count']}")
        print(f"    Dogru tespit     : {acc['correctly_detected']}")
        print(f"    Tespit orani     : {acc['detection_rate']*100:.0f}%")
        print(f"    Yanlis alarm     : {acc['false_alarm_count']}")

    if args.plot or args.save:
        save_path = args.save or os.path.join(
            det_config.SURVEILLANCE_REPORT_DIR, f"sim_{args.scenario}.png")
        surveillance.plot_surveillance_results(result, save_path=save_path)
        print(f"\nGrafik: {save_path}")


def cmd_report(args):
    """Onceki tarama sonuclarindan rapor uretir."""
    import json

    if not os.path.exists(args.input):
        print(f"Hata: Dosya bulunamadi: {args.input}")
        sys.exit(1)

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    if args.format == "text":
        print(f"\n{'='*55}")
        print("  TARAMA RAPORU")
        print(f"{'='*55}")
        if isinstance(data, dict):
            _print_report_dict(data)
        elif isinstance(data, list):
            for i, entry in enumerate(data):
                print(f"\n--- Tarama #{i+1} ---")
                _print_report_dict(entry)
    else:
        # JSON ciktisi (zaten JSON dosyasi okuduk)
        output = args.output or sys.stdout
        if isinstance(output, str):
            with open(output, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            print(f"Rapor kaydedildi: {output}")
        else:
            json.dump(data, output, ensure_ascii=False, indent=2, default=str)


def cmd_path_loss(args):
    """Yol kaybi model karsilastirma grafigi."""
    from repeater_detector.localization.rssi_distance import RSSIDistanceEstimator

    estimator = RSSIDistanceEstimator(frequency_hz=args.freq)
    save_path = args.save or os.path.join(
        det_config.SURVEILLANCE_REPORT_DIR, "path_loss_comparison.png")

    estimator.plot_path_loss_comparison(
        distance_range_m=(1, args.max_distance),
        save_path=save_path)

    print(f"Yol kaybi karsilastirma grafigi: {save_path}")


# ---------------------------------------------------------------------------
# Yardimci gosterim fonksiyonlari
# ---------------------------------------------------------------------------

def _print_scan_result(result):
    """Tarama sonucunu konsola yazdirir."""
    print(f"\n  Tarama Zamani  : {result.get('scan_time', '-')}")
    print(f"  Toplam Sinyal  : {result.get('total_signals', 0)}")
    print(f"  Yasal Sinyal   : {len(result.get('legal_signals', []))}")
    print(f"  Supheli Sinyal : {len(result.get('suspicious_signals', []))}")

    suspicious = result.get("suspicious_signals", [])
    if suspicious:
        print(f"\n  {'SUPHELI SINYALLER':^50}")
        print(f"  {'-'*50}")
        for i, sig in enumerate(suspicious, 1):
            print(f"  [{i}] {freq_to_str(sig['freq']):>14s} | "
                  f"{sig['power_dB']:>7.1f} dB | "
                  f"Skor: {sig['anomaly_score']:.2f} "
                  f"({sig['confidence_level']})")
            if sig.get("closest_known"):
                print(f"      Yakin: {sig['closest_known']} "
                      f"(fark: {sig['deviation_hz']/1e3:.1f} kHz)")

    legal = result.get("legal_signals", [])
    if legal:
        print(f"\n  Yasal sinyaller:")
        for sig in legal[:10]:  # Ilk 10
            print(f"    {freq_to_str(sig['freq']):>14s} | "
                  f"{sig['power_dB']:>7.1f} dB | "
                  f"{sig.get('matched_name', '')}")
        if len(legal) > 10:
            print(f"    ... ve {len(legal)-10} daha")


def _print_report_dict(data):
    """Rapor sozlugunu konsola yazdirir."""
    print(f"  Zaman    : {data.get('scan_time', '-')}")
    print(f"  Toplam   : {data.get('total_signals', 0)}")
    print(f"  Yasal    : {data.get('legal_count', 0)}")
    print(f"  Supheli  : {data.get('suspicious_count', 0)}")
    for sig in data.get("suspicious_signals", []):
        print(f"    ! {freq_to_str(sig.get('freq', 0))} | "
              f"{sig.get('power_dB', 0):.1f} dB | "
              f"Skor: {sig.get('anomaly_score', 0):.2f}")


# ---------------------------------------------------------------------------
# CLI Parser
# ---------------------------------------------------------------------------

def build_parser():
    """Argparse parser olusturur."""
    parser = argparse.ArgumentParser(
        description="SDR Tabanli Kacak Repeater Tespit Sistemi",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ornekler:
  %(prog)s info
  %(prog)s scan --sim --scenario tek_kacak --plot
  %(prog)s scan --input data/capture.npy --freq 900E6 --plot
  %(prog)s monitor --sim --interval 5
  %(prog)s distance --freq 900e6 --rssi -65 --env kentsel --plot
  %(prog)s direction --freq 900e6 --sim --true-angle 135 --plot
  %(prog)s simulate --scenario coklu_kacak --plot
  %(prog)s simulate --list
  %(prog)s path-loss --freq 900e6 --save results/pathloss.png
        """,
    )

    # Global argümanlar
    parser.add_argument("--mode", choices=["embedded", "network"],
                        help="USRP calisma modu")
    parser.add_argument("--addr", default=det_config.USRP_ADDR,
                        help="USRP IP adresi")
    parser.add_argument("--sim", action="store_true",
                        help="Simulasyon modu (donanim gerektirmez)")

    subparsers = parser.add_subparsers(dest="command")

    # --- info ---
    sub = subparsers.add_parser("info", help="Sistem bilgilerini goster")
    sub.set_defaults(func=cmd_info)

    # --- scan ---
    sub = subparsers.add_parser("scan", help="Bant taramasi ve kacak tespiti")
    sub.add_argument("--band", default="full",
                     help="Bant: low, high, full veya alt bant adi")
    sub.add_argument("--freq", type=parse_freq, help="Merkez frekans (dosyadan analiz icin)")
    sub.add_argument("--threshold", type=float,
                     default=det_config.ANOMALY_POWER_THRESHOLD_DB,
                     help="Tespit esigi (dB)")
    sub.add_argument("--gain", type=float, default=det_config.DEFAULT_RX_GAIN)
    sub.add_argument("--dwell", type=float, default=det_config.SCAN_DWELL_TIME,
                     help="Her frekansta bekleme suresi (s)")
    sub.add_argument("--duration", type=float, default=1.0,
                     help="Simulasyon suresi (s)")
    sub.add_argument("--scenario", help="Simulasyon senaryosu (--sim ile)")
    sub.add_argument("--input", "-i", help="IQ dosyasi (.npy, .raw, .complex64)")
    sub.add_argument("--plot", action="store_true", help="Grafik goster/uret")
    sub.add_argument("--save", "-s", help="Grafik kayit yolu")
    sub.add_argument("--export", "-e", help="Rapor disa aktar")
    sub.set_defaults(func=cmd_scan)

    # --- monitor ---
    sub = subparsers.add_parser("monitor", help="Surekli gozetleme modu")
    sub.add_argument("--band", default="full", help="Taranacak bant")
    sub.add_argument("--interval", type=float,
                     default=det_config.SURVEILLANCE_SCAN_INTERVAL_SEC,
                     help="Tarama araligi (s)")
    sub.add_argument("--threshold", type=float,
                     default=det_config.ANOMALY_POWER_THRESHOLD_DB)
    sub.add_argument("--gain", type=float, default=det_config.DEFAULT_RX_GAIN)
    sub.set_defaults(func=cmd_monitor)

    # --- distance ---
    sub = subparsers.add_parser("distance", help="RSSI'dan mesafe tahmini")
    sub.add_argument("--freq", type=parse_freq, required=True,
                     help="Calisma frekansi (Hz)")
    sub.add_argument("--rssi", type=float, help="Manuel RSSI degeri (dBm)")
    sub.add_argument("--gain", type=float, default=det_config.DEFAULT_RX_GAIN)
    sub.add_argument("--duration", type=float, default=1.0)
    sub.add_argument("--tx-power", type=float, default=det_config.TX_POWER_DBM,
                     help="Verici guc (dBm)")
    sub.add_argument("--env",
                     choices=list(det_config.ENVIRONMENT_MODELS.keys()),
                     default="kentsel", help="Ortam tipi")
    sub.add_argument("--measurements", type=int, default=5,
                     help="Olcum tekrar sayisi")
    sub.add_argument("--input", "-i", help="IQ dosyasi")
    sub.add_argument("--sim-distance", type=float,
                     help="Simulasyon: gercek mesafe (m)")
    sub.add_argument("--plot", action="store_true")
    sub.add_argument("--save", "-s")
    sub.set_defaults(func=cmd_distance)

    # --- direction ---
    sub = subparsers.add_parser("direction", help="Yon bulma oturumu")
    sub.add_argument("--freq", type=parse_freq, required=True,
                     help="Hedef frekans (Hz)")
    sub.add_argument("--gain", type=float, default=det_config.DEFAULT_RX_GAIN)
    sub.add_argument("--steps", type=int,
                     default=det_config.DF_NUM_MEASUREMENTS,
                     help="Olcum adim sayisi")
    sub.add_argument("--duration", type=float,
                     default=det_config.DF_MEASUREMENT_DURATION_SEC,
                     help="Her olcum suresi (s)")
    sub.add_argument("--true-angle", type=float,
                     help="Simulasyon: gercek sinyal acisi (derece)")
    sub.add_argument("--plot", action="store_true")
    sub.add_argument("--save", "-s")
    sub.set_defaults(func=cmd_direction)

    # --- simulate ---
    sub = subparsers.add_parser("simulate",
                                help="Senaryo simulasyonu (donanimsiz)")
    sub.add_argument("--scenario", default="tek_kacak",
                     help="Senaryo adi")
    sub.add_argument("--duration", type=float, default=1.0)
    sub.add_argument("--list", action="store_true",
                     help="Mevcut senaryolari listele")
    sub.add_argument("--plot", action="store_true")
    sub.add_argument("--save", "-s")
    sub.set_defaults(func=cmd_simulate)

    # --- report ---
    sub = subparsers.add_parser("report",
                                help="Onceki taramalardan rapor uret")
    sub.add_argument("--input", "-i", required=True,
                     help="JSON tarama sonuc dosyasi")
    sub.add_argument("--format", choices=["text", "json"], default="text")
    sub.add_argument("--output", "-o", help="Cikti dosyasi")
    sub.set_defaults(func=cmd_report)

    # --- path-loss ---
    sub = subparsers.add_parser("path-loss",
                                help="Yol kaybi model karsilastirmasi")
    sub.add_argument("--freq", type=parse_freq, default=900e6,
                     help="Calisma frekansi")
    sub.add_argument("--max-distance", type=float, default=5000,
                     help="Maks mesafe (m)")
    sub.add_argument("--save", "-s")
    sub.set_defaults(func=cmd_path_loss)

    return parser


# ---------------------------------------------------------------------------
# Giris noktasi
# ---------------------------------------------------------------------------

def main():
    """Ana giris noktasi."""
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    print()
    print("=" * 55)
    print("  SDR TABANLI KACAK REPEATER TESPIT SISTEMI")
    print("=" * 55)

    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\nIslem iptal edildi.")
    except Exception as e:
        logger.error("Hata: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
