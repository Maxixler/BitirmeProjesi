import sys

def replace_non_ascii(line):
    # Replace any non-ASCII character with a question mark
    return ''.join(c if ord(c) < 128 else '?' for c in line)

def main():
    if len(sys.argv) < 3:
        print("Usage: python replace_non_ascii_in_verbatim.py input.tex output.tex")
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
            line = replace_non_ascii(line)
        new_lines.append(line)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

if __name__ == '__main__':
    main()