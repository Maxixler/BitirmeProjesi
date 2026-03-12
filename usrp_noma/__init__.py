"""
USRP E310 ile LoRaWAN Sinyal Analizi ve NOMA Coklu Erisim Paketi

Bu paket, USRP E310 SDR platformu kullanarak:
- LoRaWAN 868 MHz sinyallerinin yakalanmasi ve demodulasyonu
- Genis bant frekans taramasi (698-960 MHz, 1710-2700 MHz)
- NOMA (Non-Orthogonal Multiple Access) coklu erisim simulasyonu ve
  gercek zamanli uygulamasi
islemlerini gerceklestirir.
"""

__version__ = "1.0.0"
__author__ = "Bitirme Projesi"

from usrp_noma.config import *  # noqa: F401,F403
from usrp_noma import utils  # noqa: F401
