"""
LoRa sinyal isleme modulu: CSS (Chirp Spread Spectrum) demodulasyon.
"""


def __getattr__(name):
    if name == "LoRaDecoder":
        from usrp_noma.lora.decoder import LoRaDecoder
        return LoRaDecoder
    raise AttributeError(f"module 'usrp_noma.lora' has no attribute {name!r}")


__all__ = ["LoRaDecoder"]
