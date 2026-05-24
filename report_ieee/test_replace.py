import re

test_string = r'\begin{longtable}[]@{}}'
pattern = r'\\begin\s*\(\s*longtable\s*\)\s*(?:\[[^\]]*\])?\s*\{'
replacement = r'\\begin{tabular{'
result = re.sub(pattern, replacement, test_string)
print("Original:", test_string)
print("Result:", result)