"""
NOMA (Non-Orthogonal Multiple Access) modulu.

Superposition Coding ile coklu kullanici sinyali olusturma,
SIC (Successive Interference Cancellation) ile kullanici ayristirma
ve performans analizi.
"""


def __getattr__(name):
    if name == "CONSTELLATIONS":
        from usrp_noma.noma.modulation import CONSTELLATIONS
        return CONSTELLATIONS
    if name == "NOMATransmitter":
        from usrp_noma.noma.transmitter import NOMATransmitter
        return NOMATransmitter
    if name == "NOMAReceiver":
        from usrp_noma.noma.receiver import NOMAReceiver
        return NOMAReceiver
    if name == "NOMAnalyzer":
        from usrp_noma.noma.analyzer import NOMAnalyzer
        return NOMAnalyzer
    raise AttributeError(f"module 'usrp_noma.noma' has no attribute {name!r}")


__all__ = [
    "CONSTELLATIONS",
    "NOMATransmitter",
    "NOMAReceiver",
    "NOMAnalyzer",
]
