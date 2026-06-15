#!/usr/bin/env python3
import subprocess
import time
import os

NOMA_PY_PATH = "NOMA.py"
PYTHON_EXE = r"C:\Users\Armagan\radioconda\python.exe"
RECEIVE_1_PATH = "bpsk_receive.txt"
RECEIVE_2_PATH = "bpsk_receive_2.txt"

print("Testing NOMA.py execution...")
print(f"Using Python: {PYTHON_EXE}")
print(f"NOMA.py exists: {os.path.exists(NOMA_PY_PATH)}")

# Clean up old files
for f in [RECEIVE_1_PATH, RECEIVE_2_PATH]:
    if os.path.exists(f):
        os.remove(f)
        print(f"Removed {f}")

# Run NOMA.py
print("Starting NOMA.py...")
env = os.environ.copy()
env["PYTHONDONTWRITEBYTECODE"] = "1"
proc = subprocess.Popen([PYTHON_EXE, NOMA_PY_PATH], env=env,
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

try:
    # Wait for 10 seconds or until we see output files
    start_time = time.time()
    while time.time() - start_time < 10:
        sz1 = os.path.getsize(RECEIVE_1_PATH) if os.path.exists(RECEIVE_1_PATH) else 0
        sz2 = os.path.getsize(RECEIVE_2_PATH) if os.path.exists(RECEIVE_2_PATH) else 0
        if sz1 > 0 and sz2 > 0:
            print(f"SUCCESS: Output files created! User1: {sz1} bytes, User2: {sz2} bytes")
            break
        time.sleep(1)
        print(f"Waiting... User1: {sz1} bytes, User2: {sz2} bytes")
    else:
        print("TIMEOUT: No output files created after 10 seconds")
except KeyboardInterrupt:
    print("Interrupted")
finally:
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()

    # Final check
    sz1 = os.path.getsize(RECEIVE_1_PATH) if os.path.exists(RECEIVE_1_PATH) else 0
    sz2 = os.path.getsize(RECEIVE_2_PATH) if os.path.exists(RECEIVE_2_PATH) else 0
    print(f"Final: User1: {sz1} bytes, User2: {sz2} bytes")