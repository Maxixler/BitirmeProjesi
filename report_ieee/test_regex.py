import re

# Test strings from the file
test_lines = [
    r'{\def\LTcaptype{none} % do not increment counter',
    r'\begin{longtable}[]@{}}',
    r'\begin{longtable}[]{@{}cccc@{}}',
    r'\begin{longtable}[]@{}}',
    r'\begin{longtable}[]{@{}ll@{}}',
    r'\end{longtable}',
]

pattern_begin = r'\\\\begin\s*{longtable}\s*(?:\\[[^\]]*\\])?\s*(\\{[^}]*\\})'
print("Pattern begin:", repr(pattern_begin))
for line in test_lines:
    if line.startswith('\\begin{longtable}'):
        print("Original:", line)
        new_line = re.sub(pattern_begin, r'\\\\begin{tabular\1', line)
        print("New:", new_line)
    elif line.startswith('\\end{longtable}'):
        print("Original:", line)
        new_line = line.replace('\\end{longtable}', '\\end{tabular')
        print("New:", new_line)

# Let's also test the pattern with a simpler approach: just replace longtable with tabular in the begin line, and remove the [] if present.
def fix_begin(line):
    # If line contains \begin{longtable}
    if '\\begin{longtable}' in line:
        # Remove the word longtable and put tabular
        line = line.replace('\\begin{longtable}', '\\begin{tabular')
        # Remove any [] that appears right after \begin{tabular (optional whitespace?)
        # We'll remove [] if it's directly after \begin{tabular possibly with whitespace.
        line = re.sub(r'\\\\begin\s*\{tabular}\s*\[', r'\\\\begin{tabular{', line)
        return line
    return line

print("\nUsing fix_begin function:")
for line in test_lines:
    if line.startswith('\\begin{longtable}'):
        print("Original:", line)
        print("New:", fix_begin(line))