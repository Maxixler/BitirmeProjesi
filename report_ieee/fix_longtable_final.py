import re
import sys

def process_lines(lines):
    output = []
    in_longtable = False
    for line in lines:
        original_line = line
        if not in_longtable:
            # Remove longtable from \usepackage line
            if '\\usepackage' in line and 'longtable' in line:
                # Remove the word 'longtable' and any surrounding commas and spaces, then clean up.
                # We'll do a simple removal: replace 'longtable' with empty string, then fix double commas and spaces.
                line = line.replace('longtable', '')
                # Clean up possible double commas and leading/trailing commas inside braces.
                line = re.sub(r'\\package\s*\{\s*,', r'\\usepackage{', line)
                line = re.sub(r',\s*,', r',', line)
                line = re.sub(r',\s*\}', r'}', line)
                # If the list is now empty, we might want to remove the whole \usepackage line, but we'll leave it for now.
                # If after removing longtable the braces are empty or only whitespace, remove the line.
                if re.search(r'\\package\s*\{\s*\}', line):
                    line = ''  # remove the line
            # Comment out \patchcmd\longtable
            if '\\patchcmd\\longtable' in line:
                line = '% ' + line
            # Comment out \makesavenoteenv{longtable}
            if '\\makesavenoteenv{longtable}' in line:
                line = '% ' + line
            # Remove the line with \def\LTcaptype{none} (comment it)
            if '\\def\\LTcaptype{none}' in line:
                line = '% ' + line
            # Detect start of longtable
            if '\\begin{longtable}' in line:
                in_longtable = True
                # Replace \begin{longtable} with \begin{tabular, and remove the optional [] if present.
                # We'll use a regex to capture the column spec (the part in braces after the optional [])
                line = re.sub(r'\\\\begin\s*{longtable}\s*(?:\\[[^\]]*\\])?\s*(\\{[^}]*\\})', r'\\\\begin{tabular\1', line)
                output.append(line)
                continue
            else:
                output.append(line)
        else:   # we are in a longtable environment
            if '\\end{longtable}' in line:
                in_longtable = False
                line = line.replace('\\end{longtable}', '\\end{tabular')
                output.append(line)
                continue
            # Remove \endhead and \endlastfoot lines
            if line.strip() in ['\\endhead', '\\endlastfoot']:
                continue   # skip this line
            # Remove \noalign{} that comes after \toprule, \midrule, \bottomrule on the same line
            line = line.replace('\\noalign{}', '')
            output.append(line)
    return output

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python fix_longtable_final.py input.tex output.tex")
        sys.exit(1)
    input_file = sys.argv[1]
    output_file = sys.argv[2]

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = process_lines(lines)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    print(f"Processed LaTeX file written to {output_file}")