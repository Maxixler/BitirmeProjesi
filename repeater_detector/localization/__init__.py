"""Lokalizasyon modulleri: RSSI mesafe tahmini ve yon bulma."""


def __getattr__(name):
    if name == "RSSIDistanceEstimator":
        from repeater_detector.localization.rssi_distance import RSSIDistanceEstimator
        return RSSIDistanceEstimator
    if name == "DirectionFinder":
        from repeater_detector.localization.direction_finder import DirectionFinder
        return DirectionFinder
    raise AttributeError(f"module 'repeater_detector.localization' has no attribute {name!r}")


__all__ = ["RSSIDistanceEstimator", "DirectionFinder"]
