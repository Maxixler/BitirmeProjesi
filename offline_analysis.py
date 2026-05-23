import numpy as np
import scipy.signal
import os

print("Loading saved chunks...")
if not os.path.exists("rx_chunk.npy") or not os.path.exists("tx1_chunk.npy"):
    print("Error: Chunks not found. Please wait until they are saved.")
    sys.exit(1)

rx_chunk = np.load("rx_chunk.npy")
tx_chunk = np.load("tx1_chunk.npy")

print(f"rx_chunk shape: {rx_chunk.shape}, dtype: {rx_chunk.dtype}")
print(f"tx_chunk shape: {tx_chunk.shape}, dtype: {tx_chunk.dtype}")

tx_norm = np.sign(tx_chunk.real)

search_left = 32 # search window in epy_block_1

options = {
    "cumprod(-tx)": np.cumprod(-tx_norm),
    "cumprod(tx)": np.cumprod(tx_norm),
    "tx_norm (BPSK)": tx_norm,
    "cumprod(-tx)_inverted": -np.cumprod(-tx_norm),
    "cumprod(tx)_inverted": -np.cumprod(tx_norm),
    "tx_chunk itself (BPSK, complex)": tx_norm,
}

for name, tx_diff in options.items():
    corr = scipy.signal.correlate(rx_chunk, tx_diff, mode='valid')
    best_idx = np.argmax(np.abs(corr))
    best_val = corr[best_idx]
    tx_energy = np.sum(np.abs(tx_diff)**2)
    est_amp = np.abs(best_val) / tx_energy
    print(f"Option: {name} -> Max Corr Peak: {np.abs(best_val):.3f}, Est Amp: {est_amp:.3f}, Shift: {best_idx - search_left}")
