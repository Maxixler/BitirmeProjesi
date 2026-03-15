"""Simulasyon modulleri: Sentetik sinyal uretimi ve test senaryolari."""


def __getattr__(name):
    if name == "RepeaterSimulator":
        from repeater_detector.simulation.repeater_simulator import RepeaterSimulator
        return RepeaterSimulator
    if name == "ScenarioGenerator":
        from repeater_detector.simulation.scenario_generator import ScenarioGenerator
        return ScenarioGenerator
    raise AttributeError(f"module 'repeater_detector.simulation' has no attribute {name!r}")


__all__ = ["RepeaterSimulator", "ScenarioGenerator"]
