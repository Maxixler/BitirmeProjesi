import re
import sys

def process_lines(lines):
    output = []
    in_longtable = False
    for line in lines:
        # Remove \def\LTcaptype{none} line (comment it out)
        if r'\def\LTcaptype{none}' in line:
            line = '% ' + line
            output.append(line)
            continue

        # Detect start of longtable
        if r'\begin{longtable}' in line:
            in_longtable = True
            # Replace \begin{longtable} with \begin{tabular and remove the [] if present
            line = re.sub(r'\\\\begin\s*{longtable}\s*(?:\\[[^\]]*\\])?', r'\\\\begin{tabular', line)
            output.append(line)
            continue

        # Detect end of longtable
        if r'\end{longtable}' in line:
            in_longtable = False
            line = line.replace(r'\end{longtable}', r'\end{tabular')
            output.append(line)
            continue

        if in_longtable:
            # Remove \noalign{} after \toprule, \midrule, \bottomrule
            if r'\toprule' in line:
                line = line.replace(r'\noalign{}', '').replace(r'\noalign', '')
            if r'\midrule' in line:
                line = line.replace(r'\noalign{}', '').replace(r'\noalign', '')
            if r'\bottomrule' in line:
                line = line.replace(r'\noalign{}', '').replace(r'\noalign', '')
            # Remove \endhead and \endlastfoot lines
            if line.strip() == r'\endhead' or line.strip() == r'\endlastfoot':
                continue  # skip this line
            # Also, note that the \toprule, \midrule, \bottomrule lines might have extra spaces, but we already handled the noalign part.
        output.append(line)
    return output

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python fix_longtable_proper.py input.tex output.tex")
        sys.exit(1)
    input_file = sys.argv[1]
    output_file = sys.argv[2]

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = process_lines(lines)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    print(f"Processed LaTeX file written to {output_file}")