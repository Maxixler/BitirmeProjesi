"""
Cekirdek SDR modulleri: USRP E310 cihaz yonetimi, IQ veri yakalama ve sinyal uretimi.
"""


def __getattr__(name):
    if name == "USRPController":
        from usrp_noma.core.usrp_controller import USRPController
        return USRPController
    if name == "SignalCapture":
        from usrp_noma.core.signal_capture import SignalCapture
        return SignalCapture
    if name == "SignalGenerator":
        from usrp_noma.core.signal_generator import SignalGenerator
        return SignalGenerator
    raise AttributeError(f"module 'usrp_noma.core' has no attribute {name!r}")


__all__ = ["USRPController", "SignalCapture", "SignalGenerator"]
