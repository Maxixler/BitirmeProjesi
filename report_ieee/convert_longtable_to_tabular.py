import re
import sys

def convert_longtable_to_tabular(text):
    # Pattern to match longtable environments with \LTcaptype{none} prefix
    # This matches: {\def\LTcaptype{none} % do not increment counter
    #               \begin{longtable}[]{$cols$}
    #               ... content ...
    #               \end{longtable}}
    #
    # We'll use a more flexible approach - find \begin{longtable} and matching \end{longtable}
    # but we need to be careful about nested braces.

    # Instead, let's do a simpler regex-based replacement that handles the common patterns

    # Pattern 1: \begin{longtable}[]{$cols$} -> \begin{tabular}[$cols$]
    # We need to capture the column specification inside {}
    pattern1 = r'\\begin\s*\(\s*longtable\s*\)\s*\[[^\]]*\]\s*(\{[^}]*\})'
    replacement1 = r'\\begin{tabular\1'
    text = re.sub(pattern1, replacement1, text)

    # Pattern 2: \end{longtable} -> \end{tabular
    pattern2 = r'\\end\s*\(\s*longtable\s*\)'
    replacement2 = r'\\end{tabular'
    text = re.sub(pattern2, replacement2, text)

    return text

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python convert_longtable_to_tabular.py input.tex output.tex")
        sys.exit(1)
    input_file = sys.argv[1]
    output_file = sys.argv[2]

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = convert_longtable_to_tabular(content)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"Converted longtable environments to tabular written to {output_file}")