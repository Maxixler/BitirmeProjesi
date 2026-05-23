import numpy as np
import scipy.signal
import os

print("Loading saved chunks...")
if not os.path.exists("rx_chunk.npy") or not os.path.exists("tx1_chunk.npy"):
    print("Error: Chunks not found.")
    sys.exit(1)

rx_chunk = np.load("rx_chunk.npy")
tx_chunk = np.load("tx1_chunk.npy")

print(f"rx_chunk shape: {rx_chunk.shape}")
print(f"tx_chunk shape: {tx_chunk.shape}")

tx_norm = np.sign(tx_chunk.real)

# We want to search over a very large window.
# Let's pad rx_chunk or use mode='full' correlation
options = {
    "cumprod(-tx)": np.cumprod(-tx_norm),
    "cumprod(tx)": np.cumprod(tx_norm),
    "tx_norm (BPSK)": tx_norm,
}

for name, tx_diff in options.items():
    # Use mode='full' to search all possible alignments
    corr = scipy.signal.correlate(rx_chunk, tx_diff, mode='full')
    best_idx = np.argmax(np.abs(corr))
    best_val = corr[best_idx]
    
    # In mode='full', the zero-lag index is len(tx_diff) - 1.
    # So the shift relative to the start of rx_chunk is:
    shift = best_idx - (len(tx_diff) - 1)
    
    tx_energy = np.sum(np.abs(tx_diff)**2)
    est_amp = np.abs(best_val) / tx_energy
    
    print(f"Option: {name} -> Max Corr Peak: {np.abs(best_val):.3f}, Est Amp: {est_amp:.3f}, Shift: {shift}")
