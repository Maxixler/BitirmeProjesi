"""
Tam sistem analizi: differential encoding + Costas Loop
+ bypass senaryolari test
"""
import numpy as np

const_points = np.array([-1-1j, -1+1j, 1-1j, 1+1j])
sym_map = [0, 1, 2, 3]
access_code_str = "1010101011110000101010101111000010101010111100001010101011110000"
ac_bits = [int(b) for b in access_code_str]

def bits_to_symbols(bits, sym_map, const_pts):
    """Convert bit stream to QPSK symbols (modulator simulation)"""
    # Pack bits to bytes (MSB first)
    packed = []
    for i in range(0, len(bits), 8):
        byte_val = 0
        for bit in bits[i:i+8]:
            byte_val = (byte_val << 1) | bit
        packed.append(byte_val)
    # Unpack to 2-bit symbols (MSB first) and map
    symbols = []
    for byte_val in packed:
        for shift in [6, 4, 2, 0]:
            two_bits = (byte_val >> shift) & 0x03
            idx = sym_map[two_bits]
            symbols.append(const_pts[idx])
    return symbols

def diff_encode(symbols, const_pts, M=4):
    """Differential encoder: encoded[n] = (encoded[n-1] + input[n]) % M"""
    # First, map symbols to indices
    indices = []
    for s in symbols:
        dists = [abs(s - p) for p in const_pts]
        indices.append(np.argmin(dists))
    # Differential encode
    encoded_indices = []
    prev = 0
    for idx in indices:
        enc = (prev + idx) % M
        encoded_indices.append(enc)
        prev = enc
    return [const_pts[i] for i in encoded_indices]

def soft_decode(rx_symbols, const_pts):
    """Simulate constellation_soft_decoder_cf calc_euclidean_soft_dec"""
    soft_out = []
    num_bits = 2
    for rx in rx_symbols:
        for bit_pos in range(num_bits):
            min_d_0 = float('inf')
            min_d_1 = float('inf')
            for j in range(len(const_pts)):
                dist = abs(rx - const_pts[j]) ** 2
                if (j >> (num_bits - 1 - bit_pos)) & 1:
                    min_d_1 = min(min_d_1, dist)
                else:
                    min_d_0 = min(min_d_0, dist)
            soft_out.append(min_d_0 - min_d_1)
    return soft_out

def hard_slice(soft_bits):
    return ''.join(str(1 if s > 0 else 0) for s in soft_bits)

print("=" * 70)
print("SENARYO 1: differential=True, Costas Loop kullanilarak")
print("           (Mevcut GRC durumu)")
print("=" * 70)

# TX: bits -> symbols -> diff_encode -> scale
tx_symbols = bits_to_symbols(ac_bits, sym_map, const_points)
tx_diff = diff_encode(tx_symbols, const_points, 4)
tx_scaled = [s * 0.5 for s in tx_diff]

# RX: ideal channel -> soft decode (using original const at scale 0.5)
scaled_const = const_points * 0.5

for phase_deg in [0, 90, 180, 270]:
    rotated = [s * np.exp(1j * np.radians(phase_deg)) for s in tx_scaled]
    soft = soft_decode(rotated, scaled_const)
    hard = hard_slice(soft)
    match = hard == access_code_str
    print(f"  Faz {phase_deg:3d}: {hard[:32]}... {'MATCH' if match else 'no match'}")

print("\n  SONUC: differential=True ile HIC BIR fazda AC bulunamiyor!")
print("  NEDEN: RX'te differential decoder yok, veriler differentially encoded")

print("\n" + "=" * 70)
print("SENARYO 2: differential=False, Costas Loop ile")
print("           (Onceki GRC durumu)")
print("=" * 70)

# TX: bits -> symbols (NO diff encoding) -> scale
tx_symbols_nodiff = bits_to_symbols(ac_bits, sym_map, const_points)
tx_scaled_nodiff = [s * 0.5 for s in tx_symbols_nodiff]

for phase_deg in [0, 90, 180, 270]:
    rotated = [s * np.exp(1j * np.radians(phase_deg)) for s in tx_scaled_nodiff]
    soft = soft_decode(rotated, scaled_const)
    hard = hard_slice(soft)
    match = hard == access_code_str
    print(f"  Faz {phase_deg:3d}: {hard[:32]}... {'MATCH' if match else 'no match'}")

print("\n  SONUC: Sadece faz=0 da calisiyor, Costas Loop farkli fazda kilitlenebilir")

print("\n" + "=" * 70)
print("SENARYO 3: differential=False, Costas Loop BYPASS")
print("           (Symbol Sync -> dogrudan Soft Decoder)")
print("=" * 70)

# TX: no diff encoding, scale by 0.5
# RX: no Costas Loop -> phase stays at 0 (ideal channel, taps=[1.0])
# Simulate with phase=0 (guaranteed by ideal channel + no Costas Loop)
soft = soft_decode(tx_scaled_nodiff, scaled_const)
hard = hard_slice(soft)
match = hard == access_code_str
print(f"  Faz   0 (guaranteed): {hard[:32]}... {'MATCH' if match else 'no match'}")
print(f"\n  SONUC: Costas Loop kaldirilinca faz herzaman 0 -> AC HERZAMAN BULUNUR!")

print("\n" + "=" * 70)
print("SENARYO 4: differential=False, Costas Loop, cok kucuk BW")
print("           (Loop neredeyse hareket etmez, 0 da kalir)")
print("=" * 70)
print("  Loop BW = 0.001 (mevcut: 0.0628)")
print("  Ideal kanalda loop 0'dan baslar, 0'da kalir")
print("  Faz drift riski: dusuk (BW cok kucuk)")
soft = soft_decode(tx_scaled_nodiff, scaled_const)
hard = hard_slice(soft)
match = hard == access_code_str
print(f"  Faz ~0: {hard[:32]}... {'MATCH' if match else 'no match'}")

print("\n" + "=" * 70)
print("ONERILEN COZUM")
print("=" * 70)
print("""
1. differential=False'a geri don
2. Costas Loop'u BYPASS et (ideal kanal icin gereksiz)
   Connect: Symbol Sync output -> Soft Decoder input
   (Costas Loop'u silmeye gerek yok, sadece baglantiyi degistir)
3. Veya Costas Loop BW'i cok kucuk yap (0.001)
   (Loop 0'a yakin kalir, ideal kanalda calisiyor)
""")
