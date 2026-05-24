import re
import sys

def process_lines(lines):
    output = []
    in_longtable = False
    for line in lines:
        original_line = line
        # Handle \usepackage line: remove longtable from the list
        if not in_longtable and '\\usepackage' in line and 'longtable' in line:
            # Remove the word 'longtable' and clean up commas and spaces
            line = line.replace('longtable', '')
            # Clean up possible double commas and leading/trailing commas inside braces.
            line = re.sub(r'\\\\package\s*\{\s*,', r'\\\\usepackage{', line)
            line = re.sub(r',\s*,', r',', line)
            line = re.sub(r',\s*\}', r'}', line)
            # If the list is now empty (i.e., \usepackage{}), remove the line
            if re.search(r'\\\\package\s*\{\s*\}', line):
                line = ''  # remove the line
        # Comment out \patchcmd\longtable
        if not in_longtable and '\\\\patchcmd\\\\longtable' in line:
            line = '% ' + line
        # Comment out \makesavenoteenv{longtable}
        if not in_longtable and '\\\\makesavenoteenv{longtable}' in line:
            line = '% ' + line
        # Comment out \def\LTcaptype{none}
        if not in_longtable and '\\\\def\\\\LTcaptype{none}' in line:
            line = '% ' + line

        # Detect start of longtable
        if not in_longtable and '\\\\begin{longtable}' in line:
            in_longtable = True
            # Replace \\\\begin{longtable} with \\\\begin{tabular, keeping the column spec and removing the optional [] if present.
            # Pattern: \\\\begin{longtable} (with spaces) then optional [ ... ] then spaces then {column spec}
            # We want to keep the column spec and change longtable to tabular.
            line = re.sub(r'\\\\begin\s*{longtable}\s*(?:\\[[^\]]*\\])?\s*(\\{[^}]*\\})', r'\\\\begin{tabular\1', line)
            output.append(line)
            continue

        # If we are in a longtable
        if in_longtable:
            # Detect end of longtable
            if '\\\\end{longtable}' in line:
                in_longtable = False
                line = line.replace('\\\\end{longtable}', '\\\\end{tabular')
                output.append(line)
                continue
            # Skip \endhead and \endlastfoot lines
            if line.strip() in ['\\\\endhead', '\\\\endlastfoot']:
                continue
            # Remove \\\\noalign{} that appears after \\\\toprule, \\\\midrule, \\\\bottomrule on the same line
            # We'll remove the \\\\noalign{} part (including the braces) if it appears after the rule.
            line = line.replace('\\\\noalign{}', '')
            # Also, there might be \\\\noalign without braces? In the file it's with braces.
            # We'll also remove any \\\\noalign that is not followed by anything? But we'll just replace the pattern.
            # Actually, we see lines like: \\\\toprule\\\\noalign{}
            # After replacing \\\\noalign{} with empty string, we get \\\\toprule which is fine.
            output.append(line)
        else:
            output.append(line)
    return output

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python fix_longtable_complete.py input.tex output.tex")
        sys.exit(1)
    input_file = sys.argv[1]
    output_file = sys.argv[2]

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = process_lines(lines)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    print(f"Processed LaTeX file written to {output_file}")