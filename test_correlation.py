import sys
import os
import time
import numpy as np
import scipy.signal
from PyQt5 import Qt

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None

print("Importing NOMA...")
import NOMA

class MyNOMA(NOMA.NOMA):
    def __init__(self):
        super().__init__()

print("Initializing QApplication...")
qapp = Qt.QApplication(sys.argv)

print("Creating NOMA flowgraph...")
tb = MyNOMA()

print("Starting flowgraph...")
tb.start()

print("Flowgraph started. Running for 6 seconds...")
for i in range(6):
    time.sleep(1)
    qapp.processEvents()

print("Stopping flowgraph...")
tb.stop()
tb.wait()

# Now let's extract the internal buffers from epy_block_1
block = tb.epy_block_1
rx_buf = block.buffer_rx
tx_buf = block.buffer_tx1
starts = block.pending_payload_starts

print(f"Captured buffer_rx length: {len(rx_buf)}")
print(f"Captured buffer_tx1 length: {len(tx_buf)}")
print(f"Captured pending starts: {starts}")

if len(starts) > 0 and len(tx_buf) >= 1296:
    payload_start_abs = starts[0]
    start_rel = payload_start_abs - block.rx_processed_abs
    search_left = block.search_window
    search_right = block.search_window
    
    if start_rel - search_left < 0:
        search_left = start_rel
        
    if start_rel + 1296 + search_right <= len(rx_buf):
        rx_chunk = rx_buf[start_rel - search_left : start_rel + 1296 + search_right]
        tx_chunk = tx_buf[:1296]
        
        tx_norm = np.sign(tx_chunk.real)
        
        # Test different options:
        options = {
            "cumprod(-tx)": np.cumprod(-tx_norm),
            "cumprod(tx)": np.cumprod(tx_norm),
            "tx_norm (BPSK)": tx_norm,
            "cumprod(-tx)_inverted": -np.cumprod(-tx_norm),
            "cumprod(tx)_inverted": -np.cumprod(tx_norm)
        }
        
        results = []
        for name, tx_diff in options.items():
            corr = scipy.signal.correlate(rx_chunk, tx_diff, mode='valid')
            best_idx = np.argmax(np.abs(corr))
            best_val = corr[best_idx]
            tx_energy = np.sum(np.abs(tx_diff)**2)
            est_amp = np.abs(best_val) / tx_energy
            results.append(f"Option: {name} -> Max Corr Peak: {np.abs(best_val):.3f}, Est Amp: {est_amp:.3f}, Best Index Shift: {best_idx - search_left}")
            
        with open("corr_results.txt", "w") as f:
            f.write("\n".join(results) + "\n")
            
        print("Analysis completed! Results written to corr_results.txt.")
    else:
        print("Error: rx_buf is too short for search window.")
else:
    print("Error: No pending starts or tx_buf is too short.")
