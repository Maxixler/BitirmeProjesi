import re
import sys

def replace_longtable(text):
    # Replace \begin{longtable}...{ with \begin{tabular{
    # This matches \begin{longtable} (with optional whitespace) then any characters up to and including the first {
    pattern = r'\\begin\s*\(\s*longtable\s*\)[^{]*\{'
    replacement = r'\\begin{tabular{'
    text = re.sub(pattern, replacement, text)

    # Replace \end{longtable} with \end{tabular
    pattern = r'\\end\s*\(\s*longtable\s*\)'
    replacement = r'\\end{tabular'
    text = re.sub(pattern, replacement, text)

    return text

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python fix_longtable4.py input.tex output.tex")
        sys.exit(1)
    input_file = sys.argv[1]
    output_file = sys.argv[2]

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = replace_longtable(content)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"Fixed longtable environments written to {output_file}")