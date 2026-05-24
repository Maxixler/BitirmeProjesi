import re
import sys

def process_lines(lines):
    output = []
    in_longtable = False
    in_preamble = True  # Assume we are in preamble until we see \begin{document}

    for line in lines:
        original_line = line

        # Detect end of preamble
        if in_preamble and r'\begin{document}' in line:
            in_preamble = False

        # Handle preamble modifications
        if in_preamble:
            # Remove longtable from \usepackage line
            if r'\usepackage' in line and 'longtable' in line:
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
            if r'\patchcmd\longtable' in line:
                line = '% ' + line
            # Comment out \makesavenoteenv{longtable}
            if r'\makesavenoteenv{longtable}' in line:
                line = '% ' + line

        # Comment out \def\LTcaptype{none} (anywhere)
        if r'\def\LTcaptype{none}' in line:
            line = '% ' + line

        # Detect start of longtable
        if not in_longtable and r'\begin{longtable}' in line:
            in_longtable = True
            # Replace \begin{longtable} with \begin{tabular and remove the [] if present
            # First handle the case with [] directly after
            line = line.replace(r'\begin{longtable}[]', r'\begin{tabular')
            # Then handle the case without [] (or with whitespace, but we assume no whitespace for simplicity)
            line = line.replace(r'\begin{longtable}', r'\begin{tabular')
            output.append(line)
            continue

        # Detect end of longtable
        if in_longtable and r'\end{longtable}' in line:
            in_longtable = False
            line = line.replace(r'\end{longtable}', r'\end{tabular')
            output.append(line)
            continue

        # If we are in a longtable
        if in_longtable:
            # Remove \endhead and \endlastfoot lines
            if line.strip() in [r'\endhead', r'\endlastfoot']:
                continue  # skip this line
            # Remove \noalign{} that comes after \toprule, \midrule, \bottomrule on the same line
            if r'\toprule' in line:
                line = line.replace(r'\noalign{}', '').replace(r'\noalign', '')
            if r'\midrule' in line:
                line = line.replace(r'\noalign{}', '').replace(r'\noalign', '')
            if r'\bottomrule' in line:
                line = line.replace(r'\noalign{}', '').replace(r'\noalign', '')
            output.append(line)
        else:
            output.append(line)

    return output

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python fix_longtable_comprehensive.py input.tex output.tex")
        sys.exit(1)
    input_file = sys.argv[1]
    output_file = sys.argv[2]

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = process_lines(lines)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    print(f"Processed LaTeX file written to {output_file}")