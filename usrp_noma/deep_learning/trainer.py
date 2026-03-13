"""
Deep Learning Egitim ve Tahmin Pipeline

IQ sinyal siniflandirma modellerinin egitimi, validasyonu ve tahmini.
"""

import os
import json

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from usrp_noma import config
from usrp_noma.utils import setup_logger

logger = setup_logger("DLTrainer")


class IQDataset(Dataset):
    """PyTorch Dataset: IQ verisini I/Q kanallarına ayirarak tensor olusturur."""

    def __init__(self, iq_data, labels):
        """
        Args:
            iq_data: (N, num_samples) kompleks numpy dizisi
            labels: (N,) sinif etiketleri
        """
        # I ve Q kanallarini ayir: (N, 2, num_samples)
        self.data = torch.tensor(
            np.stack([iq_data.real, iq_data.imag], axis=1),
            dtype=torch.float32,
        )
        self.labels = torch.tensor(labels, dtype=torch.long)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return self.data[idx], self.labels[idx]


class DLTrainer:
    """Deep Learning model egitim ve degerlendirme sinifi.

    Egitim, validasyon, loss/accuracy grafikleri ve model kayit/yukleme.
    """

    def __init__(self, model, class_names, device=None):
        """
        Args:
            model: PyTorch nn.Module
            class_names: Sinif isimleri listesi
            device: "cpu" / "cuda" / None (otomatik)
        """
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = torch.device(device)
        self.model = model.to(self.device)
        self.class_names = class_names
        self.logger = logger

        self.train_losses = []
        self.val_losses = []
        self.train_accs = []
        self.val_accs = []

    def train(self, train_data, train_labels, val_data=None, val_labels=None,
              epochs=50, batch_size=32, lr=1e-3, weight_decay=1e-4,
              save_dir=None):
        """Modeli egitir.

        Args:
            train_data: (N, num_samples) kompleks egitim verisi
            train_labels: (N,) egitim etiketleri
            val_data: Validasyon verisi (opsiyonel)
            val_labels: Validasyon etiketleri (opsiyonel)
            epochs: Epoch sayisi
            batch_size: Batch boyutu
            lr: Ogrenme hizi
            weight_decay: L2 regularizasyon
            save_dir: Model kayit dizini

        Returns:
            dict: Egitim sonuclari
        """
        train_dataset = IQDataset(train_data, train_labels)
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)

        val_loader = None
        if val_data is not None and val_labels is not None:
            val_dataset = IQDataset(val_data, val_labels)
            val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(self.model.parameters(), lr=lr, weight_decay=weight_decay)
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=5)

        best_val_acc = 0.0
        self.train_losses = []
        self.val_losses = []
        self.train_accs = []
        self.val_accs = []

        self.logger.info(f"Egitim basliyor: {epochs} epoch, batch={batch_size}, lr={lr}")
        self.logger.info(f"Cihaz: {self.device}")
        self.logger.info(f"Model parametreleri: {sum(p.numel() for p in self.model.parameters()):,}")

        for epoch in range(epochs):
            # --- Egitim ---
            self.model.train()
            running_loss = 0.0
            correct = 0
            total = 0

            for inputs, targets in train_loader:
                inputs = inputs.to(self.device)
                targets = targets.to(self.device)

                optimizer.zero_grad()
                outputs = self.model(inputs)
                loss = criterion(outputs, targets)
                loss.backward()
                optimizer.step()

                running_loss += loss.item() * inputs.size(0)
                _, predicted = outputs.max(1)
                total += targets.size(0)
                correct += predicted.eq(targets).sum().item()

            train_loss = running_loss / total
            train_acc = 100.0 * correct / total
            self.train_losses.append(train_loss)
            self.train_accs.append(train_acc)

            # --- Validasyon ---
            val_loss = 0.0
            val_acc = 0.0
            if val_loader:
                val_loss, val_acc = self._evaluate(val_loader, criterion)
                self.val_losses.append(val_loss)
                self.val_accs.append(val_acc)
                scheduler.step(val_loss)

                if val_acc > best_val_acc:
                    best_val_acc = val_acc
                    if save_dir:
                        self._save_model(os.path.join(save_dir, "best_model.pth"))

            if (epoch + 1) % 5 == 0 or epoch == 0:
                msg = f"Epoch {epoch+1}/{epochs} — Train Loss: {train_loss:.4f}, Acc: {train_acc:.1f}%"
                if val_loader:
                    msg += f" | Val Loss: {val_loss:.4f}, Acc: {val_acc:.1f}%"
                self.logger.info(msg)

        # Son model kaydet
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
            self._save_model(os.path.join(save_dir, "final_model.pth"))
            self.plot_training_curves(save_dir=save_dir)

        results = {
            "final_train_loss": self.train_losses[-1],
            "final_train_acc": self.train_accs[-1],
            "best_val_acc": best_val_acc,
            "epochs": epochs,
        }

        if val_loader:
            results["final_val_loss"] = self.val_losses[-1]
            results["final_val_acc"] = self.val_accs[-1]

        self.logger.info(f"Egitim tamamlandi. En iyi val acc: {best_val_acc:.1f}%")
        return results

    def _evaluate(self, data_loader, criterion):
        """Model performansini degerlendirir."""
        self.model.eval()
        running_loss = 0.0
        correct = 0
        total = 0

        with torch.no_grad():
            for inputs, targets in data_loader:
                inputs = inputs.to(self.device)
                targets = targets.to(self.device)

                outputs = self.model(inputs)
                loss = criterion(outputs, targets)

                running_loss += loss.item() * inputs.size(0)
                _, predicted = outputs.max(1)
                total += targets.size(0)
                correct += predicted.eq(targets).sum().item()

        return running_loss / total, 100.0 * correct / total

    def evaluate_detailed(self, test_data, test_labels):
        """Detayli test degerlendirmesi: sinif bazli metrikler.

        Args:
            test_data: (N, num_samples) kompleks test verisi
            test_labels: (N,) test etiketleri

        Returns:
            dict: Detayli sonuclar
        """
        from sklearn.metrics import classification_report, accuracy_score

        test_dataset = IQDataset(test_data, test_labels)
        test_loader = DataLoader(test_dataset, batch_size=64, shuffle=False)

        self.model.eval()
        all_preds = []
        all_targets = []

        with torch.no_grad():
            for inputs, targets in test_loader:
                inputs = inputs.to(self.device)
                outputs = self.model(inputs)
                _, predicted = outputs.max(1)
                all_preds.extend(predicted.cpu().numpy())
                all_targets.extend(targets.numpy())

        all_preds = np.array(all_preds)
        all_targets = np.array(all_targets)

        overall_acc = accuracy_score(all_targets, all_preds) * 100

        report = classification_report(
            all_targets, all_preds,
            target_names=self.class_names,
            output_dict=True,
        )

        self.logger.info(f"Test Accuracy: {overall_acc:.2f}%")
        self.logger.info(classification_report(all_targets, all_preds, target_names=self.class_names))

        return {
            "accuracy": overall_acc,
            "predictions": all_preds,
            "targets": all_targets,
            "classification_report": report,
        }

    def evaluate_by_snr(self, test_data, test_labels, test_snrs):
        """SNR degerine gore siniflandirma performansini hesaplar.

        Args:
            test_data: (N, num_samples) kompleks test verisi
            test_labels: (N,) test etiketleri
            test_snrs: (N,) SNR degerleri

        Returns:
            dict: SNR bazli accuracy degerleri
        """
        test_dataset = IQDataset(test_data, test_labels)
        test_loader = DataLoader(test_dataset, batch_size=64, shuffle=False)

        self.model.eval()
        all_preds = []

        with torch.no_grad():
            for inputs, _ in test_loader:
                inputs = inputs.to(self.device)
                outputs = self.model(inputs)
                _, predicted = outputs.max(1)
                all_preds.extend(predicted.cpu().numpy())

        all_preds = np.array(all_preds)

        unique_snrs = np.unique(test_snrs)
        snr_accuracy = {}

        for snr in unique_snrs:
            mask = test_snrs == snr
            if np.sum(mask) > 0:
                acc = np.mean(all_preds[mask] == test_labels[mask]) * 100
                snr_accuracy[float(snr)] = acc

        return snr_accuracy

    def plot_training_curves(self, save_dir=None):
        """Egitim loss ve accuracy grafiklerini cizer."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        fig.suptitle("Model Egitim Grafikleri", fontsize=14, fontweight="bold")

        epochs = range(1, len(self.train_losses) + 1)

        # Loss
        ax1.plot(epochs, self.train_losses, "b-", label="Egitim", linewidth=1.5)
        if self.val_losses:
            ax1.plot(epochs, self.val_losses, "r-", label="Validasyon", linewidth=1.5)
        ax1.set_xlabel("Epoch")
        ax1.set_ylabel("Loss")
        ax1.set_title("Loss Egrisi")
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Accuracy
        ax2.plot(epochs, self.train_accs, "b-", label="Egitim", linewidth=1.5)
        if self.val_accs:
            ax2.plot(epochs, self.val_accs, "r-", label="Validasyon", linewidth=1.5)
        ax2.set_xlabel("Epoch")
        ax2.set_ylabel("Accuracy (%)")
        ax2.set_title("Accuracy Egrisi")
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
            path = os.path.join(save_dir, "training_curves.png")
            fig.savefig(path, dpi=config.PLOT_DPI, bbox_inches="tight")
            self.logger.info(f"Egitim grafikleri kaydedildi: {path}")
        plt.close(fig)

    def plot_accuracy_vs_snr(self, snr_accuracy, save_path=None):
        """SNR-Accuracy grafiğini cizer.

        Args:
            snr_accuracy: {snr: accuracy} sozlugu
            save_path: Kayit yolu
        """
        snrs = sorted(snr_accuracy.keys())
        accs = [snr_accuracy[s] for s in snrs]

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(snrs, accs, "bo-", linewidth=2, markersize=8)
        ax.set_xlabel("SNR (dB)", fontsize=12)
        ax.set_ylabel("Siniflandirma Dogrulugu (%)", fontsize=12)
        ax.set_title("SNR vs Siniflandirma Performansi", fontsize=14, fontweight="bold")
        ax.set_ylim([0, 105])
        ax.grid(True, alpha=0.3)
        ax.axhline(y=100 / len(self.class_names), color="r", linestyle="--", alpha=0.5,
                    label=f"Rastgele ({100 / len(self.class_names):.0f}%)")
        ax.legend(fontsize=10)

        plt.tight_layout()

        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            fig.savefig(save_path, dpi=config.PLOT_DPI, bbox_inches="tight")
            self.logger.info(f"SNR-Accuracy grafigi kaydedildi: {save_path}")
        plt.close(fig)

    def _save_model(self, path):
        """Model agirliklarini kaydeder."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        torch.save({
            "model_state_dict": self.model.state_dict(),
            "class_names": self.class_names,
        }, path)
        self.logger.info(f"Model kaydedildi: {path}")

    def load_model(self, path):
        """Kaydedilmis modeli yukler."""
        checkpoint = torch.load(path, map_location=self.device, weights_only=False)
        self.model.load_state_dict(checkpoint["model_state_dict"])
        if "class_names" in checkpoint:
            self.class_names = checkpoint["class_names"]
        self.logger.info(f"Model yuklendi: {path}")


class DLPredictor:
    """Egitilmis model ile IQ sinyali siniflandirma."""

    def __init__(self, model_path, model_class, num_classes=5, device=None):
        """
        Args:
            model_path: Kaydedilmis model dosya yolu
            model_class: Model sinifi (SignalClassifierCNN veya SignalResNet)
            num_classes: Sinif sayisi
            device: Cihaz
        """
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = torch.device(device)

        self.model = model_class(num_classes=num_classes)
        checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.model.to(self.device)
        self.model.eval()

        self.class_names = checkpoint.get("class_names", [f"Sinif {i}" for i in range(num_classes)])

    def predict(self, iq_data):
        """Tek bir IQ sinyalini siniflandirir.

        Args:
            iq_data: (num_samples,) kompleks IQ dizisi

        Returns:
            tuple: (sinif_adi, olasilik, tum_olasiliklar)
        """
        x = np.stack([iq_data.real, iq_data.imag], axis=0)  # (2, num_samples)
        x = torch.tensor(x, dtype=torch.float32).unsqueeze(0).to(self.device)

        with torch.no_grad():
            output = self.model(x)
            probs = torch.softmax(output, dim=1).cpu().numpy()[0]

        pred_idx = int(np.argmax(probs))
        return self.class_names[pred_idx], float(probs[pred_idx]), probs

    def predict_batch(self, iq_batch):
        """Birden fazla IQ sinyalini siniflandirir.

        Args:
            iq_batch: (N, num_samples) kompleks IQ matris

        Returns:
            list[tuple]: Her ornek icin (sinif_adi, olasilik)
        """
        x = np.stack([iq_batch.real, iq_batch.imag], axis=1)  # (N, 2, num_samples)
        x = torch.tensor(x, dtype=torch.float32).to(self.device)

        with torch.no_grad():
            output = self.model(x)
            probs = torch.softmax(output, dim=1).cpu().numpy()

        results = []
        for i in range(len(iq_batch)):
            pred_idx = int(np.argmax(probs[i]))
            results.append((self.class_names[pred_idx], float(probs[i, pred_idx])))
        return results
