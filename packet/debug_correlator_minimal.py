#!/usr/bin/env python3
"""
Minimal correlator testi - neden cikis URETMIYOR?
"""
from gnuradio import gr, digital, blocks

AC = "1010101011110000101010101111000010101010111100001010101011110000"
soft_ac = [1.0 if b == '1' else -1.0 for b in AC]

# Test 1: Basit test (onceki calisan test)
print("TEST 1: Calisan basit test (onceden calisti)")
data1 = []
import random
random.seed(42)
data1.extend([random.choice([-1.0, 1.0]) for _ in range(200)])
data1.extend(soft_ac)
data1.extend([1.0] * 32)
data1.extend([random.choice([-1.0, 1.0]) for _ in range(200)])
data1.extend([random.choice([-1.0, 1.0]) for _ in range(200)])

class test1(gr.top_block):
    def __init__(self):
        gr.top_block.__init__(self)
        self.src = blocks.vector_source_f(data1, False)
        self.corr = digital.correlate_access_code_ff_ts(AC, 1, "packet_len")
        self.sink = blocks.vector_sink_f()
        self.connect(self.src, self.corr, self.sink)

tb1 = test1()
tb1.run()
print(f"  Input: {len(data1)}, Output: {len(tb1.sink.data())} -- {'OK' if len(tb1.sink.data()) > 0 else 'FAIL'}")

# Test 2: 2 AC ile
print("\nTEST 2: 2 AC ile")
data2 = []
data2.extend([random.choice([-1.0, 1.0]) for _ in range(100)])
data2.extend(soft_ac)  # AC 1
data2.extend([random.choice([-1.0, 1.0]) for _ in range(200)])
data2.extend(soft_ac)  # AC 2
data2.extend([random.choice([-1.0, 1.0]) for _ in range(200)])

class test2(gr.top_block):
    def __init__(self):
        gr.top_block.__init__(self)
        self.src = blocks.vector_source_f(data2, False)
        self.corr = digital.correlate_access_code_ff_ts(AC, 1, "packet_len")
        self.sink = blocks.vector_sink_f()
        self.connect(self.src, self.corr, self.sink)

tb2 = test2()
tb2.run()
print(f"  Input: {len(data2)}, Output: {len(tb2.sink.data())} -- {'OK' if len(tb2.sink.data()) > 0 else 'FAIL'}")

# Test 3: AC bulunamiyor olabilir mi? Elle kontrol
print("\nTEST 3: AC'nin input'ta var olup olmadigini kontrol et")
data2_str = ''.join(str(1 if s > 0 else 0) for s in data2)
ac_pos = data2_str.find(AC)
print(f"  AC pozisyonu: {ac_pos}")
# 2. AC
ac_pos2 = data2_str.find(AC, ac_pos + 64)
print(f"  2. AC pozisyonu: {ac_pos2}")

# Test 4: AC arasinda kac bit var?
if ac_pos >= 0 and ac_pos2 >= 0:
    gap = ac_pos2 - ac_pos - 64
    print(f"  AC'ler arasi gap: {gap} bit (= header+payload)")

# Test 5: Farkli correlator tipleri
print("\nTEST 5: correlate_access_code_tag_ff (tag version, not ts)")
class test5(gr.top_block):
    def __init__(self):
        gr.top_block.__init__(self)
        self.src = blocks.vector_source_f(data2, False)
        self.corr = digital.correlate_access_code_tag_ff(AC, 1, "corr")
        self.sink = blocks.vector_sink_f()
        self.tag_debug = blocks.tag_debug(gr.sizeof_float, "tag_test", "")
        self.tag_debug.set_display(True)
        self.connect(self.src, self.corr, self.sink)
        self.connect(self.corr, self.tag_debug)

tb5 = test5()
tb5.run()
print(f"  Input: {len(data2)}, Output: {len(tb5.sink.data())} samples")
print(f"  (tag versiyonu tum veriyi gecirir, sadece tag ekler)")

# Test 6: vector_source+head ile sinirli veri
print("\nTEST 6: Head block ile sinirli veri")
class test6(gr.top_block):
    def __init__(self):
        gr.top_block.__init__(self)
        self.src = blocks.vector_source_f(data2, True)  # REPEAT
        self.head = blocks.head(gr.sizeof_float, len(data2) * 3)  # 3 tekrar
        self.corr = digital.correlate_access_code_ff_ts(AC, 1, "packet_len")
        self.sink = blocks.vector_sink_f()
        self.tag_debug = blocks.tag_debug(gr.sizeof_float, "head_test", "packet_len")
        self.tag_debug.set_display(True)
        self.connect(self.src, self.head, self.corr, self.sink)
        self.connect(self.corr, self.tag_debug)

tb6 = test6()
tb6.run()
print(f"  Input: {len(data2)*3}, Output: {len(tb6.sink.data())} -- {'OK' if len(tb6.sink.data()) > 0 else 'FAIL'}")
