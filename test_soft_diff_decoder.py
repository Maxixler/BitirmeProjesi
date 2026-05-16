"""
Soft Differential Decoder - Birim Testi (float giris/cikis)
GNU Radio olmadan numpy ile dogrudan test eder.
"""

import numpy as np


def soft_diff_decode_bpsk(inp, prev=1.0):
    """BPSK: out[n] = in[n] * in[n-1]"""
    extended = np.concatenate(([prev], inp)).astype(np.float32)
    return (extended[1:] * extended[:-1])


def soft_diff_decode_qpsk(inp, prev_complex=complex(1.0, 0.0)):
    """QPSK: I/Q pairs -> complex diff decode -> I/Q pairs"""
    n = len(inp)
    num_symbols = n // 2
    I_vals = inp[0::2]
    Q_vals = inp[1::2]
    curr = I_vals + 1j * Q_vals

    prev_arr = np.empty(num_symbols, dtype=np.complex64)
    prev_arr[0] = prev_complex
    prev_arr[1:] = curr[:-1]

    y = curr * np.conj(prev_arr)
    out = np.empty(n, dtype=np.float32)
    out[0::2] = y.real
    out[1::2] = y.imag
    return out


def hard_diff_decode(symbols, modulus):
    """Standart hard differential decoder"""
    out = np.zeros(len(symbols), dtype=int)
    prev = 0
    for i, s in enumerate(symbols):
        out[i] = (s - prev) % modulus
        prev = s
    return out


# ============================================================
print("=" * 60)
print("TEST 1: BPSK - Hard karar karsilastirma")
print("=" * 60)

original_bits = np.array([1, 0, 1, 1, 0, 0, 1, 0])

# Differential encode
diff_encoded = np.zeros(len(original_bits), dtype=int)
prev_sym = 0
for i, b in enumerate(original_bits):
    diff_encoded[i] = (b + prev_sym) % 2
    prev_sym = diff_encoded[i]

# BPSK mapping: 0 -> +1.0, 1 -> -1.0
soft_symbols = np.where(diff_encoded == 0, 1.0, -1.0).astype(np.float32)

# Soft diff decode
soft_out = soft_diff_decode_bpsk(soft_symbols)
hard_from_soft = (soft_out < 0).astype(int)
hard_ref = hard_diff_decode(diff_encoded, modulus=2)

print("Orjinal bitler:  {}".format(original_bits))
print("Diff encoded:    {}".format(diff_encoded))
print("Soft semboller:  {}".format(soft_symbols))
print("Soft cikis:      {}".format(np.round(soft_out, 3)))
print("Hard (soft):     {}".format(hard_from_soft))
print("Hard (ref):      {}".format(hard_ref))
match1 = np.array_equal(hard_from_soft, hard_ref)
print("Eslesme:         {}".format("BASARILI" if match1 else "BASARISIZ"))

# ============================================================
print("\n" + "=" * 60)
print("TEST 2: BPSK - Gurultulu ortam (soft bilgi korunumu)")
print("=" * 60)

np.random.seed(42)
noise = 0.3 * np.random.randn(len(soft_symbols)).astype(np.float32)
noisy_symbols = soft_symbols + noise

soft_noisy = soft_diff_decode_bpsk(noisy_symbols)
hard_noisy = (soft_noisy < 0).astype(int)

print("Gurultulu soft cikis: {}".format(np.round(soft_noisy, 3)))
print("Hard karar:           {}".format(hard_noisy))
print("Orjinal bitler:       {}".format(original_bits))
is_soft = not np.all(np.abs(np.abs(soft_noisy) - 1.0) < 0.01)
print("Soft bilgi korunuyor: {}".format("EVET" if is_soft else "HAYIR"))

# ============================================================
print("\n" + "=" * 60)
print("TEST 3: QPSK - Cikis boyutu ve format")
print("=" * 60)

# 4 QPSK sembol = 8 float (I0,Q0, I1,Q1, I2,Q2, I3,Q3)
qpsk_input = np.array([
     0.707,  0.707,   # sembol 0: (I, Q)
    -0.707,  0.707,   # sembol 1
    -0.707, -0.707,   # sembol 2
     0.707, -0.707,   # sembol 3
], dtype=np.float32)

soft_qpsk = soft_diff_decode_qpsk(qpsk_input)

print("Giris:  {} float".format(len(qpsk_input)))
print("Cikis:  {} float".format(len(soft_qpsk)))
print("Oran:   {}x (beklenen: 1x, sync_block)".format(len(soft_qpsk) / len(qpsk_input)))
match3 = len(soft_qpsk) == len(qpsk_input)
print("Boyut:  {}".format("BASARILI" if match3 else "BASARISIZ"))
print("Soft I: {}".format(np.round(soft_qpsk[0::2], 3)))
print("Soft Q: {}".format(np.round(soft_qpsk[1::2], 3)))

# ============================================================
print("\n" + "=" * 60)
print("TEST 4: BPSK - State korunumu (parcali islem)")
print("=" * 60)

full_out = soft_diff_decode_bpsk(soft_symbols)

part1 = soft_diff_decode_bpsk(soft_symbols[:4])
prev2 = float(soft_symbols[3])
part2 = soft_diff_decode_bpsk(soft_symbols[4:], prev=prev2)
split_out = np.concatenate([part1, part2])

print("Tek seferde: {}".format(np.round(full_out, 3)))
print("2 parcada:   {}".format(np.round(split_out, 3)))
match4 = np.allclose(full_out, split_out)
print("Eslesme:     {}".format("BASARILI" if match4 else "BASARISIZ"))

# ============================================================
print("\n" + "=" * 60)
all_pass = match1 and is_soft and match3 and match4
print("SONUC: {}".format("TUM TESTLER BASARILI" if all_pass else "BAZI TESTLER BASARISIZ"))
print("=" * 60)
