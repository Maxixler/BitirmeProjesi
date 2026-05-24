import sys

# Mapping of unicode characters to ASCII replacements for verbatim blocks
UNICODE_MAP = {
    # Greek letters
    'α': 'a', 'β': 'b', 'γ': 'c', 'δ': 'd', 'ε': 'e', 'ζ': 'z', 'η': 'h', 'θ': 'q', 'ι': 'i', 'κ': 'k',
    'λ': 'l', 'μ': 'm', 'ν': 'n', 'ξ': 'x', 'ο': 'o', 'π': 'p', 'ρ': 'r', 'σ': 's', 'τ': 't', 'υ': 'u',
    'φ': 'f', 'χ': 'x', 'ψ': 'y', 'ω': 'w',
    # Uppercase Greek (just in case)
    'Α': 'A', 'Β': 'B', 'Γ': 'G', 'Δ': 'D', 'Ε': 'E', 'Ζ': 'Z', 'Η': 'H', 'Θ': 'Q', 'Ι': 'I', 'Κ': 'K',
    'Λ': 'L', 'Μ': 'M', 'Ν': 'N', 'Ξ': 'X', 'Ο': 'O', 'Π': 'P', 'Ρ': 'R', 'Σ': 'S', 'Τ': 'T', 'Υ': 'Y',
    'Φ': 'F', 'Χ': 'X', 'Ψ': 'Y', 'Ω': 'W',
    # Subscripts
    '₀': '0', '₁': '1', '₂': '2', '₃': '3', '₄': '4', '₅': '5', '₆': '6', '₇': '7', '₈': '8', '₉': '9',
    # Arrow symbols
    '→': '->',   # RIGHTWARDS ARROW
    '←': '<-',   # LEFTWARDS ARROW
    '↔': '<->',  # LEFT RIGHT ARROW
    '⇒': '=>',   # RIGHTWARDS DOUBLE ARROW
    '⇐': '<=',   # LEFTWARDS DOUBLE ARROW
    '⇔': '<=>',  # LEFT RIGHT DOUBLE ARROW
}

def replace_unicode_in_verbatim(line):
    # Replace known unicode characters
    for uni, ascii in UNICODE_MAP.items():
        line = line.replace(uni, ascii)
    # For any remaining non-ASCII characters, replace with a question mark
    # We'll build a new string character by character
    result = []
    for ch in line:
        if ord(ch) < 128:
            result.append(ch)
        else:
            # Replace with a question mark
            result.append('?')
    return ''.join(result)

def main():
    if len(sys.argv) < 3:
        print("Usage: python fix_verbatim_unicode2.py input.tex output.tex")
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