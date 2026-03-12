"""
NOMA Modulasyon Tablolari

QPSK, 16-QAM ve 64-QAM konstelasyon noktalari (Gray kodlu, normalize).
Verici ve alici tarafindan ortak kullanilir.
"""

import numpy as np


def _qpsk_constellation():
    """QPSK konstelasyon noktalari (Gray kodlu, normalize)."""
    return np.array([
        1 + 1j,   # 00
        1 - 1j,   # 01
        -1 + 1j,  # 10
        -1 - 1j,  # 11
    ]) / np.sqrt(2)


def _qam16_constellation():
    """16-QAM konstelasyon noktalari (Gray kodlu, normalize)."""
    levels = [-3, -1, 1, 3]
    points = []
    for q in levels:
        for i in levels:
            points.append(i + 1j * q)
    points = np.array(points)
    return points / np.sqrt(np.mean(np.abs(points) ** 2))


def _qam64_constellation():
    """64-QAM konstelasyon noktalari (normalize)."""
    levels = [-7, -5, -3, -1, 1, 3, 5, 7]
    points = []
    for q in levels:
        for i in levels:
            points.append(i + 1j * q)
    points = np.array(points)
    return points / np.sqrt(np.mean(np.abs(points) ** 2))


CONSTELLATIONS = {
    "QPSK": _qpsk_constellation(),
    "16QAM": _qam16_constellation(),
    "64QAM": _qam64_constellation(),
}
