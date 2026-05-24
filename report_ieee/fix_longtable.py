import re
import sys

def replace_longtable(text):
    # Pattern to match \begin{longtable}[]{
    # We'll match \begin{longtable}[*]{
    # and then capture everything until the matching \end{longtable}
    # but we need to handle nested braces? Not needed for our case.
    # Simpler: replace \begin{longtable}[] with \begin{tabular}{
    # and \end{longtable} with \end{tabular}
    # Also remove the [] after begin.
    # We'll do two-step: first replace the begin, then the end.
    # But we must ensure we don't replace inside comments or verbatim.
    # Since the file is not huge, we can do simple string replacement.

    # Replace \begin{longtable}[] with \begin{tabular}{
    # Note: there might be spaces. We'll use regex.
    pattern = r'\\begin\s*\(\s*longtable\s*\)\s*\[\s*\]\s*\{'
    replacement = r'\\begin{tabular{'
    text = re.sub(pattern, replacement, text)

    # Replace \end{longtable} with \end{tabular}
    pattern = r'\\end\s*\(\s*longtable\s*\)'
    replacement = r'\\end{tabular'
    text = re.sub(pattern, replacement, text)

    return text

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python fix_longtable.py input.tex output.tex")
        sys.exit(1)
    input_file = sys.argv[1]
    output_file = sys.argv[2]

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = replace_longtable(content)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"Fixed longtable environments written to {output_file}")