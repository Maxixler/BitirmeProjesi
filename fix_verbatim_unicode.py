import sys

def replace_unicode_in_verbatim(line):
    # Dictionary of unicode to ascii/latex replacements for verbatim block
    replacements = {
        # Box-drawing (already handled in previous step, but just in case)
        '┌': '+', '┐': '+', '└': '+', '┘': '+',
        '├': '+', '┤': '+', '┬': '+', '┴': '+', '┼': '+',
        '│': '|', '─': '-', '▼': 'v', '▲': '^',
        # Greek letters
        'α': 'a', 'β': 'b',
        # Subscripts
        '₁': '1', '₂': '2',
        # Arrow
        '→': '->',
        # Any other we see?
    }
    for uni, ascii in replacements.items():
        line = line.replace(uni, ascii)
    return line

def main():
    if len(sys.argv) < 3:
        print("Usage: python fix_verbatim_unicode.py input.tex output.tex")
        sys.exit(1)
    input_file = sys.argv[1]
    output_file = sys.argv[2]

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    in_verbatim = False
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(r'\begin{verbatim}'):
            in_verbatim = True
            new_lines.append(line)
            continue
        if stripped.startswith(r'\end{verbatim}'):
            in_verbatim = False
            new_lines.append(line)
            continue

        if in_verbatim:
            line = replace_unicode_in_verbatim(line)
        new_lines.append(line)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

if __name__ == '__main__':
    main()