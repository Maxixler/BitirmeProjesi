import re
import sys

def replace_longtable_in_line(line):
    # Replace \begin{longtable} ... { with \begin{tabular {
    line = re.sub(r'\\begin\s*\(\s*longtable\s*\)\s*(?:\[[^\]]*\])?\s*\{', r'\\begin{tabular{', line)
    # Replace \end{longtable} with \end{tabular
    line = re.sub(r'\\end\s*\(\s*longtable\s*\)', r'\\end{tabular', line)
    return line

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python fix_longtable_linebyline.py input.tex output.tex")
        sys.exit(1)
    input_file = sys.argv[1]
    output_file = sys.argv[2]

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = [replace_longtable_in_line(line) for line in lines]

    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    print(f"Fixed longtable environments written to {output_file}")