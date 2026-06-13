import csv
import matplotlib.pyplot as plt

pn_results = []
iq_results = []

with open("impairments_results.csv", "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    header = next(reader)
    for row in reader:
        if not row:
            continue
        t = row[0]
        val = float(row[1])
        ber1 = float(row[2])
        bler1 = float(row[3])
        ber2 = float(row[4])
        bler2 = float(row[5])
        if t == "PN":
            pn_results.append((val, ber1, bler1, ber2, bler2))
        elif t == "IQ":
            iq_results.append((val, ber1, bler1, ber2, bler2))

# Plot 1: Phase Noise
pn_vals = [r[0] for r in pn_results]
ber2_pn = [r[3]*100 for r in pn_results]

plt.figure(figsize=(8, 5))
plt.plot(pn_vals, ber2_pn, 'r-o', linewidth=2, label='User 2 (Far User) BER')
plt.title('RF Oscillator Phase Noise Effect on NOMA Performance')
plt.xlabel('Phase Noise Standard Deviation (Rad)')
plt.ylabel('User 2 BER (%)')
plt.grid(True, which="both", ls="--")
plt.legend()
plt.savefig("phase_noise_vs_ber.png", dpi=300)
plt.close()

# Plot 2: IQ Imbalance
iq_vals = [r[0] for r in iq_results]
ber2_iq = [r[3]*100 for r in iq_results] # Note: User 2 BER is index 3 in the loaded list

plt.figure(figsize=(8, 5))
plt.plot(iq_vals, ber2_iq, 'r-o', linewidth=2, label='User 2 (Far User) BER')
plt.title('I/Q Phase Imbalance Effect on NOMA Performance\n(Amplitude Imbalance g = 0.05)')
plt.xlabel('I/Q Phase Imbalance (Degrees)')
plt.ylabel('User 2 BER (%)')
plt.grid(True, which="both", ls="--")
plt.legend()
plt.savefig("iq_imbalance_vs_ber.png", dpi=300)
plt.close()

print("Plots generated successfully!")
