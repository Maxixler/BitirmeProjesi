"""Tespit modulleri: Spektrum gozetleme ve sinyal siniflandirma."""


def __getattr__(name):
    if name == "SpectrumSurveillance":
        from repeater_detector.detection.spectrum_surveillance import SpectrumSurveillance
        return SpectrumSurveillance
    if name == "SignalClassifier":
        from repeater_detector.detection.signal_classifier import SignalClassifier
        return SignalClassifier
    raise AttributeError(f"module 'repeater_detector.detection' has no attribute {name!r}")


__all__ = ["SpectrumSurveillance", "SignalClassifier"]
