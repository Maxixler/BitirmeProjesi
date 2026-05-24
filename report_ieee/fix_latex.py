import re
import sys

def process_line(line):
    # Remove longtable from \usepackage line
    if '\\usepackage' in line and 'longtable' in line:
        # Replace \usepackage{longtable, ...} with \usepackage{ ... } without longtable
        # We'll split by commas, remove longtable, and rejoin.
        # But we need to keep the braces.
        # Simple approach: replace 'longtable,' with '' and 'longtable' with '' but careful not to break other packages.
        line = line.replace('longtable,', '').replace('longtable', '')
        # If we have empty braces or double commas, clean up.
        line = re.sub(r'\\usepackage\s*\{\s*,', r'\\usepackage{', line)
        line = re.sub(r',\s*,', r',', line)
        line = re.sub(r',\s*\}', r'}', line)
        # If the list becomes empty, remove the whole \usepackage line? But we have other packages.
        # We'll leave it as is; if it's empty, it will be \usepackage{} which is invalid.
        # Let's check if after removing longtable we have nothing inside braces.
        # We'll do a more precise removal later if needed.
    # Comment out \patchcmd\longtable
    if '\\patchcmd\\longtable' in line:
        line = '% ' + line
    # Comment out \makesavenoteenv{longtable}
    if '\\makesavenoteenv{longtable}' in line:
        line = '% ' + line
    # Replace \begin{longtable} with \begin{tabular
    line = re.sub(r'\\begin\s*\(\s*longtable\s*\)', r'\\begin{tabular', line)
    # Replace \end{longtable} with \end{tabular
    line = re.sub(r'\\end\s*\(\s*longtable\s*\)', r'\\end{tabular', line)
    return line

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python fix_latex.py input.tex output.tex")
        sys.exit(1)
    input_file = sys.argv[1]
    output_file = sys.argv[2]

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = [process_line(line) for line in lines]

    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    print(f"Processed LaTeX file written to {output_file}")