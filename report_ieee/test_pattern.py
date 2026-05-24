import re

test_line = r'{\def\LTcaptype{none} % do not increment counter\n\begin{longtable}[]{@{}ll@{}}\n\toprule\noalign{}\nParametre & Değer \\\n\midrule\noalign{}\n\endhead\n\bottomrule\noalign{}\n\endlastfoot\n\textbf{Kod sözcüğü uzunluğu (\(n\))} & 1296 bit \\\n\end{longtable}\n}'

print("Test line:")
print(repr(test_line))
print()

# Try the pattern from fix_longtable_final3.py
pattern1 = r'\\\\begin\s*\\{longtable\\}\s*(?:\\[[^\]]*\\])?\s*(\\{[^}]*\\})'
print("Pattern1:", repr(pattern1))
match1 = re.search(pattern1, test_line)
if match1:
    print("Match1:", match1.group())
    print("Group1:", match1.group(1))
else:
    print("No match1")

# Try a simpler pattern: just look for \begin{longtable}
pattern2 = r'\\\\begin{longtable}'
print("\nPattern2:", repr(pattern2))
match2 = re.search(pattern2, test_line)
if match2:
    print("Match2:", match2.group())
else:
    print("No match2")

# Try to match \begin{longtable} and then capture the optional [] and the column spec
pattern3 = r'\\\\begin\s*{longtable}\s*(?:\\[[^\]]*\\])?\s*(\\{[^}]*\\})'
print("\nPattern3:", repr(pattern3))
match3 = re.search(pattern3, test_line)
if match3:
    print("Match3:", match3.group())
    print("Group1:", match3.group(1))
else:
    print("No match3")

# Try with raw string and single backslashes for the literal backslash in the regex
# We want to match the literal string: \begin{longtable}
# In the regex, to match a backslash we need \\\\, because the string literal must escape the backslash, and the regex engine also escapes.
# Actually, in a raw string, we can use two backslashes to represent a literal backslash in the regex.
# So the pattern for \begin is: \\\\begin
# But note: the test_line string already has a single backslash. So we are matching against a string that has a single backslash.
# The regex engine sees the string as: backslash, b, e, g, i, n, ...
# So we need to match a backslash in the string, which in the regex pattern is represented by \\\\ (because in a raw string, \\\\ is two backslashes, which the regex engine interprets as a single backslash escape, matching a literal backslash).
# So the pattern should start with \\\\begin.

# Let's break down the test_line: the first two characters are backslash and 'b'.
# So we want to match that.

# Let's try pattern: r'\\\\begin{longtable}'
# This should match the literal string "\begin{longtable}".
# We already tried that as pattern2 and it matched.

# Now we want to skip the optional [] and capture the column spec.
# The column spec is inside curly braces: {@@{}}.
# So after \begin{longtable} we might have [] and then spaces and then {@@{}}.

# Let's try: r'\\\\begin{longtable}\s*(?:\[[^\]]*\])*\s*(\\{[^}]*\\})'
# But note: the [] might be present or not. We want to skip it if present.

pattern4 = r'\\\\begin{longtable}\s*(?:\[[^\]]*\])\s*(\\{[^}]*\\})'
print("\nPattern4:", repr(pattern4))
match4 = re.search(pattern4, test_line)
if match4:
    print("Match4:", match4.group())
    print("Group1:", match4.group(1))
else:
    print("No match4")

# Make the [] optional:
pattern5 = r'\\\\begin{longtable}\s*(?:\[[^\]]*\])\s*(\\{[^}]*\\})'
print("\nPattern5:", repr(pattern5))
match5 = re.search(pattern5, test_line)
if match5:
    print("Match5:", match5.group())
    print("Group1:", match5.group(1))
else:
    print("No match5")

# Actually, we want to skip the [] and any spaces, then capture the column spec.
# Let's do: r'\\\\begin{longtable}\s*(?:\[[^\]]*\]\s*)?(\\{[^}]*\\})'
pattern6 = r'\\\\begin{longtable}\s*(?:\[[^\]]*\]\s*)?(\\{[^}]*\\})'
print("\nPattern6:", repr(pattern6))
match6 = re.search(pattern6, test_line)
if match6:
    print("Match6:", match6.group())
    print("Group1:", match6.group(1))
else:
    print("No match6")

# Now test the replacement:
if match6:
    replacement = r'\\\\begin{tabular\1'
    result = re.sub(pattern6, replacement, test_line)
    print("\nResult:", result)
else:
    print("No match for replacement")