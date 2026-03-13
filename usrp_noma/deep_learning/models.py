"""
IQ Sinyal Siniflandirma - Deep Learning Modelleri

USRP E310 ile yakalanan IQ sinyallerini siniflandirmak icin
1D CNN ve ResNet mimarileri.

Sinif tanimlari:
- LoRa (CSS)
- NOMA (Superposition Coded)
- CW (Tek ton)
- OFDM
- Gurultu (AWGN)
"""

import torch
import torch.nn as nn


class SignalClassifierCNN(nn.Module):
    """1D CNN tabanli IQ sinyal siniflandirici.

    Girdi: (batch, 2, num_samples) — I ve Q kanallari ayri kanallar olarak.
    Cikti: (batch, num_classes) — sinif olasiliklari.

    Mimari:
    - 4 konvolusyon blogu (Conv1d + BatchNorm + ReLU + MaxPool)
    - Global Average Pooling
    - 2 FC katman + Dropout
    """

    def __init__(self, num_classes=5, input_length=4096):
        super().__init__()

        self.features = nn.Sequential(
            # Blok 1: 2 -> 64 kanal
            nn.Conv1d(2, 64, kernel_size=7, stride=1, padding=3),
            nn.BatchNorm1d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool1d(kernel_size=4, stride=4),

            # Blok 2: 64 -> 128 kanal
            nn.Conv1d(64, 128, kernel_size=5, stride=1, padding=2),
            nn.BatchNorm1d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool1d(kernel_size=4, stride=4),

            # Blok 3: 128 -> 256 kanal
            nn.Conv1d(128, 256, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm1d(256),
            nn.ReLU(inplace=True),
            nn.MaxPool1d(kernel_size=4, stride=4),

            # Blok 4: 256 -> 256 kanal
            nn.Conv1d(256, 256, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm1d(256),
            nn.ReLU(inplace=True),

            # Global Average Pooling
            nn.AdaptiveAvgPool1d(1),
        )

        self.classifier = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(256, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(128, num_classes),
        )

    def forward(self, x):
        """
        Args:
            x: (batch, 2, num_samples) — I/Q kanallari

        Returns:
            (batch, num_classes) logits
        """
        x = self.features(x)
        x = x.squeeze(-1)  # (batch, 256)
        x = self.classifier(x)
        return x


class ResidualBlock(nn.Module):
    """1D Residual Block (skip connection)."""

    def __init__(self, in_channels, out_channels, stride=1):
        super().__init__()

        self.conv1 = nn.Conv1d(in_channels, out_channels, kernel_size=3, stride=stride, padding=1)
        self.bn1 = nn.BatchNorm1d(out_channels)
        self.conv2 = nn.Conv1d(out_channels, out_channels, kernel_size=3, stride=1, padding=1)
        self.bn2 = nn.BatchNorm1d(out_channels)
        self.relu = nn.ReLU(inplace=True)

        self.shortcut = nn.Sequential()
        if stride != 1 or in_channels != out_channels:
            self.shortcut = nn.Sequential(
                nn.Conv1d(in_channels, out_channels, kernel_size=1, stride=stride),
                nn.BatchNorm1d(out_channels),
            )

    def forward(self, x):
        out = self.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out += self.shortcut(x)
        out = self.relu(out)
        return out


class SignalResNet(nn.Module):
    """1D ResNet tabanli IQ sinyal siniflandirici.

    Derin residual aglar ile daha iyi genelleme.

    Girdi: (batch, 2, num_samples)
    Cikti: (batch, num_classes)
    """

    def __init__(self, num_classes=5, input_length=4096):
        super().__init__()

        self.prep = nn.Sequential(
            nn.Conv1d(2, 64, kernel_size=7, stride=2, padding=3),
            nn.BatchNorm1d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool1d(kernel_size=3, stride=2, padding=1),
        )

        self.layer1 = nn.Sequential(
            ResidualBlock(64, 64),
            ResidualBlock(64, 64),
        )

        self.layer2 = nn.Sequential(
            ResidualBlock(64, 128, stride=2),
            ResidualBlock(128, 128),
        )

        self.layer3 = nn.Sequential(
            ResidualBlock(128, 256, stride=2),
            ResidualBlock(256, 256),
        )

        self.pool = nn.AdaptiveAvgPool1d(1)

        self.classifier = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(256, num_classes),
        )

    def forward(self, x):
        x = self.prep(x)
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.pool(x)
        x = x.squeeze(-1)
        x = self.classifier(x)
        return x
