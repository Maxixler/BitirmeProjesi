import re
import sys

def replace_longtable(text):
    # Replace \begin{longtable} ... { with \begin{tabular{
    text = re.sub(r'\\begin\s*\(\s*longtable\s*\)\s*(?:\[[^\]]*\])?\s*\{', r'\\begin{tabular{', text)
    # Replace \end{longtable} with \end{tabular
    text = re.sub(r'\\end\s*\(\s*longtable\s*\)', r'\\end{tabular', text)
    return text

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python fix_longtable6.py input.tex output.tex")
        sys.exit(1)
    input_file = sys.argv[1]
    output_file = sys.argv[2]

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = replace_longtable(content)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"Fixed longtable environments written to {output_file}")