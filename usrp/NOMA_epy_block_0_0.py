"""
Embedded Python Block: Soft Differential Decoder
Giris: float32  (soft semboller, Constellation Soft Decoder'dan)
Cikis: float32  (soft decoded bitler, LDPC Decoder'a)

BPSK (modulus=2): out[n] = in[n] * in[n-1]
QPSK (modulus=4): I/Q ciftlerini complex'e cevirip diff decode

Chase Combining icin soft bilgiyi korur.
"""

import numpy as np
from gnuradio import gr
import pmt


class blk(gr.sync_block):
    """
    Soft Differential Decoder

    Differential Decoder'in soft-decision versiyonudur.
    Float soft sembolleri alip soft decoded bitler uretir.

    Matematiksel temel:
        BPSK:  out[n] = in[n] * in[n-1]
        QPSK:  y[n] = z[n] * conj(z[n-1])
               z[n] = in[2n] + j*in[2n+1]
               out[2n]   = Re(y[n])
               out[2n+1] = Im(y[n])

    Parametreler:
        modulus: 2 (BPSK) veya 4 (QPSK)
    """

    def __init__(self, modulus=2):
        if modulus not in (2, 4):
            raise ValueError(
                "Desteklenmeyen modulus: {}. "
                "2 (BPSK) veya 4 (QPSK) kullanin.".format(modulus)
            )

        self.modulus = int(modulus)

        gr.sync_block.__init__(
            self,
            name='Soft Diff Decoder',
            in_sig=[np.float32],
            out_sig=[np.float32]
        )

        # QPSK: her seferde 2 float (I, Q cifti) islensin
        if self.modulus == 4:
            self.set_output_multiple(2)

        # Onceki sembol referans degeri
        if self.modulus == 2:
            self.prev = np.float32(1.0)
        else:
            self.prev_complex = complex(1.0, 0.0)

    def work(self, input_items, output_items):
        inp = input_items[0]   # float32 dizisi
        out = output_items[0]  # float32 dizisi
        n = len(inp)

        if n == 0:
            return 0

        if self.modulus == 2:
            # --- BPSK: out[n] = in[n] * in[n-1] ---
            extended = np.empty(n + 1, dtype=np.float32)
            extended[0] = self.prev
            extended[1:] = inp
            # Negation: correlate_access_code_ff_ts pozitif=1
            # olarak yorumlar, diff decode ise pozitif=bit0 uretir.
            # Ters cevirme ile uyum saglanir.
            out[:] = -(extended[1:] * extended[:-1])
            self.prev = np.float32(inp[-1])

        else:
            # --- QPSK: I/Q ciftleri uzerinden complex diff decode ---
            num_symbols = n // 2

            # Soft I ve Q degerlerinden complex sembol olustur
            I_vals = inp[0::2]
            Q_vals = inp[1::2]
            curr = (I_vals + 1j * Q_vals).astype(np.complex64)

            # Onceki semboller dizisi
            prev_arr = np.empty(num_symbols, dtype=np.complex64)
            prev_arr[0] = self.prev_complex
            prev_arr[1:] = curr[:-1]

            # y[k] = curr[k] * conj(prev[k])
            y = curr * np.conj(prev_arr)

            # Interleaved cikis (negated for polarity match)
            out[0::2] = -(y.real.astype(np.float32))
            out[1::2] = -(y.imag.astype(np.float32))

            self.prev_complex = complex(curr[-1])

        return n
