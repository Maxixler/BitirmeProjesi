import re

# Test string from the file
test_string = r'\begin{longtable}[]@{}}'
print("Test string:", repr(test_string))

pattern = r'\\begin\s*\(\s*longtable\s*\)\s*(?:\[[^\]]*\])?\s*\{'
print("Pattern:", repr(pattern))

match = re.search(pattern, test_string)
if match:
    print("Match found:", match.group())
else:
    print("No match")

# Let's try a simpler approach: just replace \begin{longtable} with \begin{tabular
# and \end{longtable} with \end{tabular, but we need to keep the column spec.
# We can do two-step: first remove the [] after begin, then replace begin and end.

# Actually, we want to keep the column specification inside the braces.
# So we need to capture what's inside the braces after the optional [].

# Let's try a pattern that captures the column spec.
pattern2 = r'\\begin\s*\(\s*longtable\s*\)\s*(?:\[[^\]]*\])?\s*(\{[^}]*\})'
print("Pattern2:", repr(pattern2))
match2 = re.search(pattern2, test_string)
if match2:
    print("Match2 group:", match2.group(1))
else:
    print("No match2")

# Now replace with \begin{tabular plus the captured group.
replacement = r'\\begin{tabular\1'
result = re.sub(pattern2, replacement, test_string)
print("Result:", result)