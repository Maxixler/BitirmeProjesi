"""
Deep Learning Paket Init

IQ sinyal siniflandirma icin CNN ve ResNet modelleri.
"""


def __getattr__(name):
    if name == "SignalClassifierCNN":
        from usrp_noma.deep_learning.models import SignalClassifierCNN
        return SignalClassifierCNN
    elif name == "SignalResNet":
        from usrp_noma.deep_learning.models import SignalResNet
        return SignalResNet
    elif name == "DLTrainer":
        from usrp_noma.deep_learning.trainer import DLTrainer
        return DLTrainer
    elif name == "DLPredictor":
        from usrp_noma.deep_learning.trainer import DLPredictor
        return DLPredictor
    raise AttributeError(f"module 'usrp_noma.deep_learning' has no attribute '{name}'")
