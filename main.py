"""
USRP E310 & LoRaWAN & NOMA Sinyal Analiz Araci - Ana Giris Noktasi

CLI arayuzu ile tum modulleri tek bir noktadan yonetir.

Kullanim:
    python3 main.py info
    python3 main.py capture --freq 868e6 --duration 2 --output data/test.npy
    python3 main.py spectrum --freq 868e6 --save spectrum.png
    python3 main.py waterfall --freq 868e6 --duration 5
    python3 main.py lora --freq 868e6 --sf 7
    python3 main.py generate --type tone --freq 868e6
    python3 main.py scan --band low
    python3 main.py stream --role pub
    python3 main.py noma-sim --users 2 --modulation QPSK
    python3 main.py noma-compare --users 2
"""

import argparse
import os
import sys

import numpy as np

from usrp_noma import config
from usrp_noma.utils import setup_logger, freq_to_str, load_iq_data

logger = setup_logger("Main")


def detect_mode():
    """Calisma modunu otomatik algila (embedded / network)."""
    hostname = os.popen("hostname").read().strip()
    if "e3" in hostname.lower() or "ettus" in hostname.lower():
        return "embedded"
    if os.path.exists("/etc/uhd"):
        return "embedded"
    return "network"


def cmd_info(args):
    """Cihaz ve sistem bilgilerini gosterir."""
    from usrp_noma.core import USRPController

    mode = args.mode or detect_mode()
    print(f"Calisma modu: {mode}")
    print()

    print("=== ANTEN BILGILERI ===")
    for key, val in config.ANTENNA_INFO.items():
        print(f"  {key}: {val}")
    print()

    print("=== FREKANS BANTLARI ===")
    for band in config.FREQUENCY_BANDS:
        print(f"  {band['name']}: {freq_to_str(band['start_freq'])} - "
              f"{freq_to_str(band['stop_freq'])}")
        print(f"    Aciklama: {band['description']}")
    print()

    print("=== BILINEN FREKANSLAR ===")
    for name, info in config.KNOWN_FREQUENCIES.items():
        print(f"  {name}: {freq_to_str(info['freq'])} (BW: {freq_to_str(info['bw'])})")
    print()

    print("=== USRP BAGLANTI ===")
    try:
        ctrl = USRPController(mode=mode, addr=args.addr)
        ctrl.connect()
        info = ctrl.device_info()
        for key, val in info.items():
            if isinstance(val, float) and val > 1e3:
                print(f"  {key}: {freq_to_str(val)}")
            else:
                print(f"  {key}: {val}")
        ctrl.close()
    except Exception as e:
        print(f"  USRP baglanti hatasi: {e}")


def cmd_capture(args):
    """IQ veri yakalar."""
    from usrp_noma.core import USRPController, SignalCapture

    mode = args.mode or detect_mode()

    with USRPController(mode=mode, addr=args.addr) as ctrl:
        capture = SignalCapture(ctrl)
        filepath, data = capture.capture_to_file(
            filename=args.output, duration_sec=args.duration,
            freq=args.freq, gain=args.gain, rate=args.rate,
        )

    print(f"Yakalama tamamlandi:")
    print(f"  Dosya: {filepath}")
    print(f"  Ornek sayisi: {len(data)}")
    print(f"  Sure: {args.duration:.2f} s")
    print(f"  Frekans: {freq_to_str(args.freq)}")


def cmd_spectrum(args):
    """Spektrum analizi yapar."""
    from usrp_noma.core import USRPController, SignalCapture
    from usrp_noma.analysis import SpectrumAnalyzer

    analyzer = SpectrumAnalyzer(sample_rate=args.rate, fft_size=args.fft_size)

    if args.input:
        data, metadata = load_iq_data(args.input)
        if "sample_rate" in metadata:
            analyzer.sample_rate = float(metadata["sample_rate"])
        center_freq = float(metadata.get("center_freq", args.freq))
    else:
        mode = args.mode or detect_mode()
        ctrl = USRPController(mode=mode, addr=args.addr)
        ctrl.connect()
        capture = SignalCapture(ctrl)

        if args.live:
            analyzer.plot_spectrum_live(capture, center_freq=args.freq)
            ctrl.close()
            return

        data = capture.capture(
            duration_sec=args.duration, freq=args.freq,
            gain=args.gain, rate=args.rate,
        )
        center_freq = args.freq
        ctrl.close()

    freqs, psd_dB = analyzer.compute_psd(data)
    peaks = analyzer.find_peaks(freqs, psd_dB, threshold_dB=args.threshold)

    print(f"Spektrum analizi ({freq_to_str(center_freq)}):")
    if peaks:
        print(f"  {len(peaks)} tepe noktasi bulundu:")
        for freq, power in peaks[:10]:
            abs_freq = freq + center_freq
            print(f"    {freq_to_str(abs_freq)}: {power:.1f} dB")
    else:
        print("  Esik uzerinde tepe noktasi bulunamadi.")

    analyzer.plot_spectrum(data, center_freq=center_freq, save_path=args.save)


def cmd_waterfall(args):
    """Waterfall diyagram olusturur."""
    from usrp_noma.core import USRPController, SignalCapture
    from usrp_noma.analysis import WaterfallDisplay

    waterfall = WaterfallDisplay(
        sample_rate=args.rate, fft_size=args.fft_size, history_size=args.history,
    )

    if args.input:
        data, metadata = load_iq_data(args.input)
        if "sample_rate" in metadata:
            waterfall.sample_rate = float(metadata["sample_rate"])
        center_freq = float(metadata.get("center_freq", args.freq))
        fft_size = waterfall.fft_size
        for i in range(0, len(data) - fft_size, fft_size):
            waterfall.update(data[i : i + fft_size])
        waterfall.plot(center_freq=center_freq, save_path=args.save)
    else:
        mode = args.mode or detect_mode()
        ctrl = USRPController(mode=mode, addr=args.addr)
        ctrl.connect()
        if args.freq:
            ctrl.set_rx_freq(args.freq)
        if args.gain:
            ctrl.set_rx_gain(args.gain)
        if args.rate:
            ctrl.set_rx_rate(args.rate)
        capture = SignalCapture(ctrl)
        if args.live:
            waterfall.plot_live(capture, center_freq=args.freq or config.DEFAULT_CENTER_FREQ)
        else:
            data = capture.capture(duration_sec=args.duration, freq=args.freq)
            fft_size = waterfall.fft_size
            for i in range(0, len(data) - fft_size, fft_size):
                waterfall.update(data[i : i + fft_size])
            center_freq = ctrl.usrp.get_rx_freq()
            waterfall.plot(center_freq=center_freq, save_path=args.save)
        ctrl.close()

    print("Waterfall diyagram olusturuldu.")


def cmd_lora(args):
    """LoRa sinyal demodulasyonu."""
    from usrp_noma.core import USRPController, SignalCapture
    from usrp_noma.lora import LoRaDecoder

    decoder = LoRaDecoder(sf=args.sf, bw=args.bw, fs=args.rate)

    if args.input:
        data, metadata = load_iq_data(args.input)
        if "sample_rate" in metadata:
            decoder.fs = float(metadata["sample_rate"])
    else:
        mode = args.mode or detect_mode()
        ctrl = USRPController(mode=mode, addr=args.addr)
        ctrl.connect()
        capture = SignalCapture(ctrl)
        data = capture.capture(
            duration_sec=args.duration, freq=args.freq,
            gain=args.gain, rate=args.rate,
        )
        ctrl.close()

    if args.auto_sf:
        estimated_sf = decoder.estimate_sf(data)
        print(f"Tahmin edilen SF: {estimated_sf}")
        decoder = LoRaDecoder(sf=estimated_sf, bw=args.bw, fs=decoder.fs)

    results = decoder.process(data)

    print(f"\nLoRa Demodulasyon Sonuclari (SF={decoder.sf}, BW={freq_to_str(decoder.bw)}):")
    if results:
        for i, pkt in enumerate(results):
            print(f"\n  Paket {i + 1}:")
            print(f"    Offset: {pkt['preamble_offset']}")
            print(f"    Sembol sayisi: {pkt['num_symbols']}")
            print(f"    Payload (hex): {pkt['payload_hex']}")
            if pkt["header"]:
                print(f"    Header: {pkt['header']}")
    else:
        print("  Hicbir LoRa paketi tespit edilemedi.")


def cmd_generate(args):
    """Test sinyali uretir ve gonderir."""
    from usrp_noma.core import USRPController, SignalGenerator

    mode = args.mode or detect_mode()

    with USRPController(mode=mode, addr=args.addr) as ctrl:
        ctrl.set_tx_freq(args.freq)
        ctrl.set_tx_gain(args.tx_gain)
        ctrl.set_tx_rate(args.rate)
        gen = SignalGenerator(ctrl)

        if args.type == "tone":
            samples = gen.generate_tone(
                freq_offset=args.offset, amplitude=args.amplitude, duration=args.duration,
            )
        elif args.type == "chirp":
            samples = gen.generate_chirp(bw=args.bw, duration=args.duration)
        elif args.type == "lora":
            samples = gen.generate_lora_preamble(sf=args.sf, bw=args.bw)
        elif args.type == "noise":
            samples = gen.generate_noise(power_dBm=args.power, duration=args.duration)
        else:
            print(f"Bilinmeyen sinyal tipi: {args.type}")
            return

        if args.continuous:
            print("Surekli iletim baslatildi (Ctrl+C ile durdurun)...")
            if args.type == "tone":
                gen.transmit_continuous(
                    lambda: gen.generate_tone(args.offset, args.amplitude, args.duration)
                )
            else:
                gen.transmit_continuous(lambda: samples)
        else:
            sent = gen.transmit(samples)
            print(f"Sinyal gonderildi: {sent} ornek, tip={args.type}")


def cmd_scan(args):
    """Frekans taramasi yapar."""
    from usrp_noma.core import USRPController
    from usrp_noma.analysis import FrequencyScanner

    mode = args.mode or detect_mode()

    with USRPController(mode=mode, addr=args.addr) as ctrl:
        if args.gain:
            ctrl.set_rx_gain(args.gain)
        scanner = FrequencyScanner(ctrl)

        if args.band == "low":
            results = scanner.scan_low_band(dwell_time=args.dwell)
        elif args.band == "high":
            results = scanner.scan_high_band(dwell_time=args.dwell)
        elif args.band == "full":
            results = scanner.scan_full(dwell_time=args.dwell)
        elif args.start and args.stop:
            results = scanner.scan_band(
                args.start, args.stop, step=args.step, dwell_time=args.dwell,
            )
        else:
            print("Bant secimi gerekli: --band low|high|full veya --start/--stop")
            return

    active = scanner.find_active_signals(threshold_dB=args.threshold)
    print(f"\nTarama tamamlandi: {len(results)} nokta tarandi")
    print(f"Aktif sinyaller ({args.threshold} dB esik):")
    for freq, power in active:
        print(f"  {freq_to_str(freq)}: {power:.1f} dB")

    if args.plot or args.save:
        scanner.plot_scan_results(save_path=args.save)
    if args.export:
        filepath = scanner.export_results(filename=args.export)
        print(f"Sonuclar kaydedildi: {filepath}")


def cmd_noma_sim(args):
    """NOMA BER vs SNR simulasyonu (donanim gerektirmez)."""
    from usrp_noma.noma import NOMATransmitter, NOMAReceiver, NOMAnalyzer

    print(f"NOMA Simulasyonu: {args.users} kullanici, {args.modulation}")
    tx = NOMATransmitter(num_users=args.users, modulation=args.modulation)
    rx = NOMAReceiver(num_users=args.users, modulation=args.modulation)
    analyzer = NOMAnalyzer(tx, rx)

    snr_range = np.arange(args.snr_min, args.snr_max + 1, 1)
    results = analyzer.simulate_ber_vs_snr(snr_range, num_symbols=args.symbols)

    save_dir = args.output_dir
    os.makedirs(save_dir, exist_ok=True)
    analyzer.plot_ber_vs_snr(
        results, save_path=os.path.join(save_dir, "noma_ber_vs_snr.png"),
    )

    print(f"\nSimulasyon sonuclari:")
    print(f"  Guc katsayilari: {tx.power_coefficients}")
    for u in range(args.users):
        final_ber = results["ber_users"][u][-1]
        print(f"  Kullanici {u+1} BER (SNR={args.snr_max}dB): {final_ber:.6f}")
    print(f"\nGrafik: {save_dir}/noma_ber_vs_snr.png")


def cmd_noma_compare(args):
    """NOMA vs OMA karsilastirma raporu."""
    from usrp_noma.noma import NOMATransmitter, NOMAReceiver, NOMAnalyzer

    print(f"NOMA vs OMA Karsilastirmasi: {args.users} kullanici, {args.modulation}")
    tx = NOMATransmitter(num_users=args.users, modulation=args.modulation)
    rx = NOMAReceiver(num_users=args.users, modulation=args.modulation)
    analyzer = NOMAnalyzer(tx, rx)

    save_dir = args.output_dir
    analyzer.generate_full_report(save_dir=save_dir)

    print(f"\nTam rapor olusturuldu: {save_dir}/")
    print("  - noma_ber_vs_snr.png")
    print("  - noma_vs_oma_ber.png")
    print("  - capacity_comparison.png")
    print("  - throughput_comparison.png")
    print("  - power_allocation.png")
    print("  - constellation_tx.png / constellation_rx.png")
    print("  - sic_stages.png")
    print("  - noma_ber_results.csv / capacity_results.csv")


def cmd_noma_constellation(args):
    """NOMA konstelasyon diyagramlari."""
    from usrp_noma.noma import NOMATransmitter, NOMAReceiver, NOMAnalyzer

    tx = NOMATransmitter(num_users=args.users, modulation=args.modulation)
    rx = NOMAReceiver(num_users=args.users, modulation=args.modulation)
    analyzer = NOMAnalyzer(tx, rx)

    save_dir = args.output_dir
    os.makedirs(save_dir, exist_ok=True)
    combined, orig_bits, _ = tx.transmit_frame(num_bits=4096)
    noisy = rx.add_awgn(combined, args.snr)

    analyzer.plot_constellation(
        combined,
        title=f"TX Superposition ({args.users} Kullanici, {args.modulation})",
        save_path=os.path.join(save_dir, "constellation_tx.png"),
    )
    analyzer.plot_constellation(
        noisy,
        title=f"RX Alinan (SNR={args.snr} dB)",
        save_path=os.path.join(save_dir, "constellation_rx.png"),
    )
    analyzer.plot_sic_stages(
        noisy, save_path=os.path.join(save_dir, "sic_stages.png"),
    )
    print(f"Konstelasyon grafikleri: {save_dir}/")


def cmd_noma_live(args):
    """USRP E310 ile gercek zamanli NOMA testi."""
    from usrp_noma.core import USRPController, SignalCapture
    from usrp_noma.noma import NOMATransmitter, NOMAReceiver, NOMAnalyzer

    mode = args.mode or detect_mode()

    with USRPController(mode=mode, addr=args.addr) as ctrl:
        capture = SignalCapture(ctrl)
        tx = NOMATransmitter(num_users=args.users, modulation=args.modulation)
        rx = NOMAReceiver(num_users=args.users, modulation=args.modulation)
        analyzer = NOMAnalyzer(tx, rx)

        combined, orig_bits, _ = tx.transmit_frame()
        ctrl.set_tx_freq(args.freq)
        ctrl.set_tx_gain(args.tx_gain)
        ctrl.set_tx_rate(args.rate)
        ctrl.send_samples(combined.astype(np.complex64))
        print(f"NOMA sinyali gonderildi: {len(combined)} ornek")

        import time
        time.sleep(0.1)
        data = capture.capture(
            duration_sec=args.duration, freq=args.freq,
            gain=args.gain, rate=args.rate,
        )
        print(f"Sinyal yakalandi: {len(data)} ornek")

        n = min(len(data), len(combined))
        result = rx.receive_frame(data[:n], orig_bits)
        print(f"\nSonuclar:")
        for u in range(args.users):
            print(f"  Kullanici {u+1} BER: {result['ber_per_user'][u]:.6f}")
        print(f"  Ortalama BER: {result['ber_average']:.6f}")

        save_dir = args.output_dir
        os.makedirs(save_dir, exist_ok=True)
        analyzer.plot_constellation(
            data[:n], title="Gercek Zamanli NOMA RX",
            save_path=os.path.join(save_dir, "noma_live_constellation.png"),
        )
        print(f"Grafik: {save_dir}/noma_live_constellation.png")


def cmd_stream(args):
    """ZMQ veri akisi baslatir."""
    from usrp_noma.core import USRPController
    from usrp_noma.streaming import ZMQStreamer

    streamer = ZMQStreamer(port=args.port)

    if args.role == "pub":
        mode = args.mode or detect_mode()
        ctrl = USRPController(mode=mode, addr=args.addr)
        ctrl.connect()
        if args.freq:
            ctrl.set_rx_freq(args.freq)
        if args.gain:
            ctrl.set_rx_gain(args.gain)
        if args.rate:
            ctrl.set_rx_rate(args.rate)

        print(f"ZMQ yayinlayici baslatildi: port {args.port}")
        print(f"  Frekans: {freq_to_str(ctrl.usrp.get_rx_freq())}")
        print(f"  Ornekleme: {freq_to_str(ctrl.usrp.get_rx_rate())}")
        print("Durdurmak icin Ctrl+C basin...")
        streamer.start_publisher(ctrl)
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            streamer.stop()
            ctrl.close()

    elif args.role == "sub":
        host = args.sub_host or config.USRP_ADDR
        received_count = [0]

        def _on_receive(iq_data):
            received_count[0] += 1
            if received_count[0] % 100 == 0:
                power = 10 * np.log10(np.maximum(np.mean(np.abs(iq_data) ** 2), 1e-12))
                print(f"  [{received_count[0]}] {len(iq_data)} ornek, guc={power:.1f} dB")

        print(f"ZMQ alici baslatildi: {host}:{args.port}")
        print("Veri bekleniyor... (Ctrl+C ile durdurun)")
        streamer.start_subscriber(host=host, port=args.port, callback=_on_receive)
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            streamer.stop()
    else:
        print(f"Bilinmeyen rol: {args.role}. 'pub' veya 'sub' kullanin.")


def parse_freq(value):
    """Frekans degerini parse eder (ornek: "868e6", "868M", "2.4G")."""
    value = value.strip().upper()
    multipliers = {"K": 1e3, "M": 1e6, "G": 1e9}
    for suffix, mult in multipliers.items():
        if value.endswith(suffix):
            return float(value[:-1]) * mult
    return float(value)


def build_parser():
    """Argparse parser olusturur."""
    parser = argparse.ArgumentParser(
        description="USRP E310 & LoRaWAN & NOMA Sinyal Analiz Araci",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ornekler:
  %(prog)s info
  %(prog)s capture --freq 868e6 --duration 2 --output test.npy
  %(prog)s spectrum --freq 868e6 --save spectrum.png
  %(prog)s waterfall --freq 868e6 --duration 5 --live
  %(prog)s lora --freq 868e6 --sf 7
  %(prog)s generate --type tone --freq 868e6 --offset 10000
  %(prog)s scan --band low
  %(prog)s scan --band full --export scan_results.csv
  %(prog)s stream --role pub --freq 868e6
  %(prog)s noma-sim --users 2 --modulation QPSK
  %(prog)s noma-compare --users 2
  %(prog)s noma-constellation --snr 20
  %(prog)s noma-live --freq 868e6 --users 2
        """,
    )

    parser.add_argument("--mode", choices=["embedded", "network"],
                        help="Calisma modu (otomatik algilanir)")
    parser.add_argument("--addr", default=config.USRP_ADDR,
                        help=f"USRP IP adresi (varsayilan: {config.USRP_ADDR})")

    subparsers = parser.add_subparsers(dest="command", help="Alt komutlar")

    # --- info ---
    sub = subparsers.add_parser("info", help="Cihaz ve sistem bilgilerini goster")
    sub.set_defaults(func=cmd_info)

    # --- capture ---
    sub = subparsers.add_parser("capture", help="IQ veri yakala")
    sub.add_argument("--freq", type=parse_freq, default=config.DEFAULT_CENTER_FREQ)
    sub.add_argument("--gain", type=float, default=config.DEFAULT_RX_GAIN)
    sub.add_argument("--rate", type=parse_freq, default=config.DEFAULT_SAMPLE_RATE)
    sub.add_argument("--duration", type=float, default=config.DEFAULT_CAPTURE_DURATION)
    sub.add_argument("--output", "-o", help="Cikti dosyasi")
    sub.set_defaults(func=cmd_capture)

    # --- spectrum ---
    sub = subparsers.add_parser("spectrum", help="Spektrum analizi")
    sub.add_argument("--freq", type=parse_freq, default=config.DEFAULT_CENTER_FREQ)
    sub.add_argument("--gain", type=float, default=config.DEFAULT_RX_GAIN)
    sub.add_argument("--rate", type=parse_freq, default=config.DEFAULT_SAMPLE_RATE)
    sub.add_argument("--duration", type=float, default=1.0)
    sub.add_argument("--fft-size", type=int, default=config.DEFAULT_FFT_SIZE)
    sub.add_argument("--threshold", type=float, default=-50)
    sub.add_argument("--input", "-i", help="IQ veri dosyasindan oku")
    sub.add_argument("--save", "-s", help="Grafigi dosyaya kaydet")
    sub.add_argument("--live", action="store_true")
    sub.set_defaults(func=cmd_spectrum)

    # --- waterfall ---
    sub = subparsers.add_parser("waterfall", help="Waterfall diyagram")
    sub.add_argument("--freq", type=parse_freq, default=config.DEFAULT_CENTER_FREQ)
    sub.add_argument("--gain", type=float, default=config.DEFAULT_RX_GAIN)
    sub.add_argument("--rate", type=parse_freq, default=config.DEFAULT_SAMPLE_RATE)
    sub.add_argument("--duration", type=float, default=2.0)
    sub.add_argument("--fft-size", type=int, default=config.DEFAULT_FFT_SIZE)
    sub.add_argument("--history", type=int, default=200)
    sub.add_argument("--input", "-i")
    sub.add_argument("--save", "-s")
    sub.add_argument("--live", action="store_true")
    sub.set_defaults(func=cmd_waterfall)

    # --- lora ---
    sub = subparsers.add_parser("lora", help="LoRa sinyal demodulasyonu")
    sub.add_argument("--freq", type=parse_freq, default=config.LORA_DEFAULT_FREQ)
    sub.add_argument("--gain", type=float, default=config.DEFAULT_RX_GAIN)
    sub.add_argument("--rate", type=parse_freq, default=config.DEFAULT_SAMPLE_RATE)
    sub.add_argument("--duration", type=float, default=5.0)
    sub.add_argument("--sf", type=int, default=config.LORA_DEFAULT_SF)
    sub.add_argument("--bw", type=parse_freq, default=config.LORA_DEFAULT_BW)
    sub.add_argument("--auto-sf", action="store_true")
    sub.add_argument("--input", "-i")
    sub.set_defaults(func=cmd_lora)

    # --- generate ---
    sub = subparsers.add_parser("generate", help="Test sinyali uret ve gonder")
    sub.add_argument("--type", choices=["tone", "chirp", "lora", "noise"], default="tone")
    sub.add_argument("--freq", type=parse_freq, default=config.DEFAULT_CENTER_FREQ)
    sub.add_argument("--tx-gain", type=float, default=config.DEFAULT_TX_GAIN)
    sub.add_argument("--rate", type=parse_freq, default=config.DEFAULT_SAMPLE_RATE)
    sub.add_argument("--duration", type=float, default=1.0)
    sub.add_argument("--offset", type=float, default=10e3)
    sub.add_argument("--amplitude", type=float, default=0.7)
    sub.add_argument("--bw", type=parse_freq, default=config.LORA_DEFAULT_BW)
    sub.add_argument("--sf", type=int, default=config.LORA_DEFAULT_SF)
    sub.add_argument("--power", type=float, default=-30)
    sub.add_argument("--continuous", action="store_true")
    sub.set_defaults(func=cmd_generate)

    # --- scan ---
    sub = subparsers.add_parser("scan", help="Frekans taramasi")
    sub.add_argument("--band", choices=["low", "high", "full"])
    sub.add_argument("--start", type=parse_freq)
    sub.add_argument("--stop", type=parse_freq)
    sub.add_argument("--step", type=parse_freq)
    sub.add_argument("--dwell", type=float, default=config.SCAN_DWELL_TIME)
    sub.add_argument("--gain", type=float, default=config.DEFAULT_RX_GAIN)
    sub.add_argument("--threshold", type=float, default=config.SCAN_THRESHOLD_DB)
    sub.add_argument("--plot", action="store_true")
    sub.add_argument("--save", "-s")
    sub.add_argument("--export", "-e")
    sub.set_defaults(func=cmd_scan)

    # --- stream ---
    sub = subparsers.add_parser("stream", help="ZMQ veri akisi")
    sub.add_argument("--role", choices=["pub", "sub"], required=True)
    sub.add_argument("--port", type=int, default=config.ZMQ_PORT)
    sub.add_argument("--freq", type=parse_freq)
    sub.add_argument("--gain", type=float)
    sub.add_argument("--rate", type=parse_freq)
    sub.add_argument("--sub-host")
    sub.set_defaults(func=cmd_stream)

    # --- noma-sim ---
    sub = subparsers.add_parser("noma-sim", help="NOMA BER simulasyonu (donanimsiz)")
    sub.add_argument("--users", type=int, default=config.NOMA_NUM_USERS)
    sub.add_argument("--modulation", choices=["QPSK", "16QAM", "64QAM"],
                     default=config.NOMA_DEFAULT_MODULATION)
    sub.add_argument("--snr-min", type=float, default=config.NOMA_SNR_MIN_DB)
    sub.add_argument("--snr-max", type=float, default=config.NOMA_SNR_MAX_DB)
    sub.add_argument("--symbols", type=int, default=config.NOMA_NUM_SYMBOLS)
    sub.add_argument("--output-dir", default=config.PLOT_OUTPUT_DIR)
    sub.set_defaults(func=cmd_noma_sim)

    # --- noma-compare ---
    sub = subparsers.add_parser("noma-compare", help="NOMA vs OMA karsilastirma raporu")
    sub.add_argument("--users", type=int, default=config.NOMA_NUM_USERS)
    sub.add_argument("--modulation", choices=["QPSK", "16QAM", "64QAM"],
                     default=config.NOMA_DEFAULT_MODULATION)
    sub.add_argument("--output-dir", default=config.PLOT_OUTPUT_DIR)
    sub.set_defaults(func=cmd_noma_compare)

    # --- noma-constellation ---
    sub = subparsers.add_parser("noma-constellation", help="NOMA konstelasyon diyagramlari")
    sub.add_argument("--users", type=int, default=config.NOMA_NUM_USERS)
    sub.add_argument("--modulation", choices=["QPSK", "16QAM", "64QAM"],
                     default=config.NOMA_DEFAULT_MODULATION)
    sub.add_argument("--snr", type=float, default=20.0)
    sub.add_argument("--output-dir", default=config.PLOT_OUTPUT_DIR)
    sub.set_defaults(func=cmd_noma_constellation)

    # --- noma-live ---
    sub = subparsers.add_parser("noma-live", help="USRP ile gercek zamanli NOMA testi")
    sub.add_argument("--freq", type=parse_freq, default=config.DEFAULT_CENTER_FREQ)
    sub.add_argument("--gain", type=float, default=config.DEFAULT_RX_GAIN)
    sub.add_argument("--rate", type=parse_freq, default=config.DEFAULT_SAMPLE_RATE)
    sub.add_argument("--tx-gain", type=float, default=config.DEFAULT_TX_GAIN)
    sub.add_argument("--duration", type=float, default=5.0)
    sub.add_argument("--users", type=int, default=config.NOMA_NUM_USERS)
    sub.add_argument("--modulation", choices=["QPSK", "16QAM", "64QAM"],
                     default=config.NOMA_DEFAULT_MODULATION)
    sub.add_argument("--output-dir", default=config.PLOT_OUTPUT_DIR)
    sub.set_defaults(func=cmd_noma_live)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    print(f"=== USRP E310 & LoRaWAN & NOMA Sinyal Analiz Araci ===")
    print()

    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\nIslem iptal edildi.")
    except Exception as e:
        logger.error("Hata: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
