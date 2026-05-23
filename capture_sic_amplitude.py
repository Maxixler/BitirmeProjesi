import sys
import os
import time
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

print("Flowgraph started. Running for 10 seconds to collect prints...")
for i in range(10):
    time.sleep(1)
    qapp.processEvents()
    sys.stdout.flush()
    sys.stderr.flush()

print("Stopping flowgraph...")
tb.stop()
tb.wait()
print("Done!")
