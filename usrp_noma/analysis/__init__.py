"""
Analiz modulleri: Spektrum analizi, waterfall diyagram, frekans taramasi,
veri analizi ve sentetik veri uretimi.
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
    if name == "IQDataAnalyzer":
        from usrp_noma.analysis.data_analysis import IQDataAnalyzer
        return IQDataAnalyzer
    if name == "SyntheticDataGenerator":
        from usrp_noma.analysis.synthetic_data import SyntheticDataGenerator
        return SyntheticDataGenerator
    raise AttributeError(f"module 'usrp_noma.analysis' has no attribute {name!r}")


__all__ = [
    "SpectrumAnalyzer", "WaterfallDisplay", "FrequencyScanner",
    "IQDataAnalyzer", "SyntheticDataGenerator",
]
