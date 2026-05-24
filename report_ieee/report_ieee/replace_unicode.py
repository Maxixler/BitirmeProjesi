import sys

def replace_unicode_chars(line):
    replacements = {
        '┌': '+',
        '┐': '+',
        '└': '+',
        '┘': '+',
        '├': '+',
        '┤': '+',
        '┬': '+',
        '┴': '+',
        '┼': '+',
        '│': '|',
        '─': '-',
        '▼': 'v',
        '▲': '^',
        # Keep → as is? Or replace with ->
        # '→': '->',
    }
    for uni, ascii in replacements.items():
        line = line.replace(uni, ascii)
    return line

def main():
    if len(sys.argv) < 3:
        print("Usage: python replace_unicode.py input.tex output.tex")
        sys.exit(1)
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    new_lines = []
    for line in lines:
        new_lines.append(replace_unicode_chars(line))
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

if __name__ == '__main__':
    main()