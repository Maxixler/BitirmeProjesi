"""
Analiz modulleri: Spektrum analizi, waterfall diyagram ve frekans taramasi.
"""


def __getattr__(name):
    if name == "SpectrumAnalyzer":
        from usrp_noma.analysis.spectrum_analyzer import SpectrumAnalyzer
        return SpectrumAnalyzer
    if name == "WaterfallDisplay":
        from usrp_noma.analysis.waterfall_display import WaterfallDisplay
        return WaterfallDisplay
    if name == "FrequencyScanner":
        from usrp_noma.analysis.frequency_scanner import FrequencyScanner
        return FrequencyScanner
    raise AttributeError(f"module 'usrp_noma.analysis' has no attribute {name!r}")


__all__ = ["SpectrumAnalyzer", "WaterfallDisplay", "FrequencyScanner"]
