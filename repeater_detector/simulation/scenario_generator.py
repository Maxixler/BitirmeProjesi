"""
Kacak Repeater Tespit Sistemi - Senaryo Uretici

Dogrulama ve demo icin onceden tanimli senaryolar uretir.
Her senaryo farkli bir tespit zorluk seviyesini temsil eder.
"""

from usrp_noma.utils import setup_logger
from repeater_detector.simulation.repeater_simulator import RepeaterSimulator


logger = setup_logger("repeater_detector.scenario")


class ScenarioGenerator:
    """
    Onceden tanimli test senaryolari ureteci.

    Her senaryo, belirli bir tespit durumunu simule eder
    (temiz spektrum, tek kacak, coklu kacak, zayif sinyal vb.)
    """

    # Mevcut senaryolar
    SCENARIOS = {
        "temiz_spektrum": "Sadece yasal sinyaller, kacak repeater yok",
        "tek_kacak": "Bir adet kacak repeater + yasal sinyaller",
        "coklu_kacak": "Birden fazla kacak repeater, farkli guc seviyeleri",
        "zayif_kacak": "Gurultuye yakin zayif kacak sinyal (zorlayici senaryo)",
        "yakindaki_kacak": "Yasal frekansa cok yakin kacak (zor ayirt etme)",
    }

    def __init__(self, simulator=None):
        """
        Args:
            simulator: RepeaterSimulator nesnesi. None ise otomatik olusturulur.
        """
        self.simulator = simulator or RepeaterSimulator()
        self.logger = setup_logger("ScenarioGenerator")

    def generate(self, scenario_name, duration_sec=1.0, **kwargs):
        """
        Belirtilen senaryoyu uretir.

        Args:
            scenario_name: SCENARIOS anahtari
            duration_sec: Senaryo suresi (saniye)
            **kwargs: Senaryo'ya ozel parametreler

        Returns:
            dict: RepeaterSimulator.generate_scenario() formatinda cikti
        """
        if scenario_name not in self.SCENARIOS:
            available = ", ".join(self.SCENARIOS.keys())
            raise ValueError(
                f"Bilinmeyen senaryo: '{scenario_name}'. "
                f"Mevcut senaryolar: {available}")

        method = getattr(self, f"_scenario_{scenario_name}")
        self.logger.info("Senaryo uretiliyor: %s — %s",
                         scenario_name, self.SCENARIOS[scenario_name])
        return method(duration_sec=duration_sec, **kwargs)

    def list_scenarios(self):
        """
        Mevcut senaryolari listeler.

        Returns:
            dict: {isim: aciklama} eslesmesi
        """
        return dict(self.SCENARIOS)

    # ------------------------------------------------------------------
    # Senaryo ureticileri
    # ------------------------------------------------------------------

    def _scenario_temiz_spektrum(self, duration_sec=1.0, **kwargs):
        """Temiz spektrum: sadece yasal sinyaller, kacak yok."""
        return self.simulator.generate_scenario(
            duration_sec=duration_sec,
            num_legal=5,
            num_illegal=0,
            center_freq=kwargs.get("center_freq", 900e6),
        )

    def _scenario_tek_kacak(self, duration_sec=1.0, **kwargs):
        """Tek kacak repeater: 1 kacak + 4 yasal sinyal."""
        return self.simulator.generate_scenario(
            duration_sec=duration_sec,
            num_legal=4,
            num_illegal=1,
            center_freq=kwargs.get("center_freq", 900e6),
            illegal_freq_offsets=[150e3],  # 150 kHz ofset
            illegal_powers_dBm=[-35],       # Guclu sinyal
        )

    def _scenario_coklu_kacak(self, duration_sec=1.0, **kwargs):
        """Coklu kacak: 3 kacak repeater, farkli guc seviyeleri."""
        return self.simulator.generate_scenario(
            duration_sec=duration_sec,
            num_legal=4,
            num_illegal=3,
            center_freq=kwargs.get("center_freq", 900e6),
            illegal_freq_offsets=[100e3, -200e3, 350e3],
            illegal_powers_dBm=[-30, -40, -35],  # Farkli gucler
        )

    def _scenario_zayif_kacak(self, duration_sec=1.0, **kwargs):
        """Zayif kacak: gurultuye yakin, tespit etmesi zor."""
        return self.simulator.generate_scenario(
            duration_sec=duration_sec,
            num_legal=3,
            num_illegal=1,
            center_freq=kwargs.get("center_freq", 900e6),
            illegal_freq_offsets=[200e3],
            illegal_powers_dBm=[-75],  # Cok zayif sinyal
        )

    def _scenario_yakindaki_kacak(self, duration_sec=1.0, **kwargs):
        """Yakindaki kacak: yasal frekansa cok yakin, ayirt etmesi zor."""
        return self.simulator.generate_scenario(
            duration_sec=duration_sec,
            num_legal=3,
            num_illegal=2,
            center_freq=kwargs.get("center_freq", 900e6),
            # Yasal sinyale cok yakin (30 kHz ve 20 kHz ofset)
            illegal_freq_offsets=[30e3, -20e3],
            illegal_powers_dBm=[-38, -42],
        )
