import re
import sys

def process_line(line):
    # Remove longtable from \usepackage line
    if '\\usepackage' in line and 'longtable' in line:
        # Remove the word 'longtable' and any surrounding commas and spaces, then clean up.
        line = line.replace('longtable', '')
        # Clean up possible double commas and leading/trailing commas inside braces.
        line = re.sub(r'\\package\s*\{\s*,', r'\\usepackage{', line)
        line = re.sub(r',\s*,', r',', line)
        line = re.sub(r',\s*\}', r'}', line)
        # If the list is now empty, we might want to remove the whole \usepackage line, but we'll leave it for now.
        # It's better to leave it as \usepackage{} which might cause an error, but we'll see.
        # Alternatively, we can remove the entire line if after removing longtable the braces are empty or only whitespace.
        # We'll do a simple check: if the line contains \usepackage{} then remove the line.
        if re.search(r'\\package\s*\{\s*\}', line):
            line = ''  # remove the line
    # Comment out \patchcmd\longtable
    if '\\patchcmd\\longtable' in line:
        line = '% ' + line
    # Comment out \makesavenoteenv{longtable}
    if '\\makesavenoteenv{longtable}' in line:
        line = '% ' + line
    # Replace \begin{longtable} with \begin{tabular, keeping the column spec
    # We'll use a regex to capture the column spec (the part inside braces after the optional [])
    # Pattern: \begin{longtable} (with spaces) then optional [ ... ] then spaces then { ... } (column spec)
    # We want to keep the column spec and change longtable to tabular.
    # We'll use:
    line = re.sub(r'\\\\begin\s*{longtable}\s*(?:\\[[^\]]*\\])?\s*(\\{[^}]*\\})', r'\\\\begin{tabular\1', line)
    # Replace \end{longtable} with \end{tabular
    line = re.sub(r'\\\\end\s*{longtable}', r'\\\\end{tabular', line)
    return line

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python fix_latex_longtable.py input.tex output.tex")
        sys.exit(1)
    input_file = sys.argv[1]
    output_file = sys.argv[2]

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        new_lines.append(process_line(line))

    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    print(f"Processed LaTeX file written to {output_file}")