import re
import sys

def replace_longtable(text):
    # Pattern for \begin{longtable}[] {cols} -> capture {cols}
    pattern_begin = r'\\begin\s*\(\s*longtable\s*\)\s*\[[^\]]*\]\s*(\{[^}]*\})'
    replacement_begin = r'\\begin{tabular\1'
    text = re.sub(pattern_begin, replacement_begin, text)

    # Pattern for \end{longtable}
    pattern_end = r'\\end\s*\(\s*longtable\s*\)'
    replacement_end = r'\\end{tabular'
    text = re.sub(pattern_end, replacement_end, text)

    return text

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python fix_longtable_capture.py input.tex output.tex")
        sys.exit(1)
    input_file = sys.argv[1]
    output_file = sys.argv[2]

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = replace_longtable(content)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"Fixed longtable environments written to {output_file}")