import re
import sys

def markdown_to_latex(markdown_text):
    # Convert code blocks
    def replace_code_blocks(match):
        lang = match.group(1) or ''
        code = match.group(2)
        # For simplicity, we'll use verbatim for now
        return f'\\begin{{verbatim}}\n{code}\\end{{verbatim}}'

    # Replace fenced code blocks
    markdown_text = re.sub(r'```(\w*)\n(.*?)\n```', replace_code_blocks, markdown_text, flags=re.DOTALL)

    # Replace inline code: `code` -> \texttt{code}
    markdown_text = re.sub(r'`([^`]+)`', r'\\texttt{\\1}', markdown_text)

    # Convert headers
    # We'll do from h6 to h1 to avoid replacing parts of already replaced headers
    for i in range(6, 0, -1):
        markdown_text = re.sub(r'^' + '#' * i + r'\\s+(.+)$', r'\\' + {'1':'section','2':'subsection','3':'subsubsection','4':'paragraph','5':'subparagraph','6':'subparagraph'}[str(i)] + r'{\\1}', markdown_text, flags=re.MULTILINE)

    # Convert bold: **text** -> \textbf{text}
    markdown_text = re.sub(r'\*\*(.*?)\*\*', r'\\textbf{\\1}', markdown_text)

    # Convert italic: *text* -> \textit{text} (but be careful not to clash with bold)
    # We'll do italic after bold and use a single * not surrounded by *
    markdown_text = re.sub(r'(?<!\\)\*(?!\*)([^*]+?)(?<!\\)\*(?!\*)', r'\\textit{\\1}', markdown_text)

    # Convert links: [text](url) -> \href{url}{text} (requires hyperref package)
    markdown_text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\\href{\\2}{\\1}', markdown_text)

    # Convert unordered lists
    # We'll process line by line for lists
    lines = markdown_text.split('\n')
    in_list = False
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('- '):
            if not in_list:
                new_lines.append('\\begin{itemize}')
                in_list = True
            new_lines.append('  \\item ' + stripped[2:])
        else:
            if in_list:
                new_lines.append('\\end{itemize}')
                in_list = False
            new_lines.append(line)
    if in_list:
        new_lines.append('\\end{itemize}')
    markdown_text = '\n'.join(new_lines)

    # Convert ordered lists (simplistic: lines starting with number. )
    lines = markdown_text.split('\n')
    in_list = False
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if re.match(r'^\d+\.\s+', stripped):
            if not in_list:
                new_lines.append('\\begin{enumerate}')
                in_list = True
            # Remove the number and dot
            item_text = re.sub(r'^\d+\.\s+', '', stripped)
            new_lines.append('  \\item ' + item_text)
        else:
            if in_list:
                new_lines.append('\\end{enumerate}')
                in_list = False
            new_lines.append(line)
    if in_list:
        new_lines.append('\\end{enumerate}')
    markdown_text = '\n'.join(new_lines)

    # Convert blockquotes: > text -> \begin{quote}...\end{quote}
    lines = markdown_text.split('\n')
    in_quote = False
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('> '):
            if not in_quote:
                new_lines.append('\\begin{quote}')
                in_quote = True
            new_lines.append('  ' + stripped[2:])
        else:
            if in_quote:
                new_lines.append('\\end{quote}')
                in_quote = False
            new_lines.append(line)
    if in_quote:
        new_lines.append('\\end{quote}')
    markdown_text = '\n'.join(new_lines)

    # Convert horizontal rule: --- or *** or ___ -> \hrule
    markdown_text = re.sub(r'^\\s*[-*_]{3,}\\s*$', r'\\hrule', markdown_text, flags=re.MULTILINE)

    # Convert tables (simplistic: we'll assume the table is well-formed and convert to tabular)
    # This is a complex task, so we'll leave tables as is for now and hope the user can adjust.
    # We'll at least try to convert the markdown table to a tabular environment.
    # We'll look for lines with | and assume they are part of a table.
    lines = markdown_text.split('\n')
    in_table = False
    table_lines = []
    new_lines = []
    for line in lines:
        if '|' in line and not line.strip().startswith('|--'):
            # This might be a table line
            if not in_table:
                in_table = True
                table_lines = [line]
            else:
                table_lines.append(line)
        else:
            if in_table:
                # Process the table lines
                # We'll assume the second line is the separator (with ---) and skip it
                if len(table_lines) >= 2:
                    # Header
                    header = table_lines[0]
                    # Alignment line (second) we ignore for now, we'll assume center
                    # Data rows
                    rows = table_lines[2:]
                    # Build tabular
                    # Count columns from header
                    cols = header.count('|') - 1  # because leading and trailing |
                    if cols < 0:
                        cols = 0
                    # Start tabular
                    new_lines.append('\\begin{tabular}{|' + 'c|' * cols + '}')
                    new_lines.append('\\hline')
                    # Process header
                    header_cells = [cell.strip() for cell in header.split('|')[1:-1]]
                    new_lines.append(' & '.join(header_cells) + ' \\\\ \\hline')
                    # Process rows
                    for row in rows:
                        cells = [cell.strip() for cell in row.split('|')[1:-1]]
                        new_lines.append(' & '.join(cells) + ' \\\\')
                    new_lines.append('\\hline')
                    new_lines.append('\\end{tabular}')
                else:
                    # Not enough lines, just output as is
                    new_lines.extend(table_lines)
                in_table = False
                table_lines = []
            new_lines.append(line)
    if in_table:
        # Same as above
        if len(table_lines) >= 2:
            header = table_lines[0]
            cols = header.count('|') - 1
            if cols < 0:
                cols = 0
            new_lines.append('\\begin{tabular}{|' + 'c|' * cols + '}')
            new_lines.append('\\hline')
            header_cells = [cell.strip() for cell in header.split('|')[1:-1]]
            new_lines.append(' & '.join(header_cells) + ' \\\\ \\hline')
            for row in table_lines[2:]:
                cells = [cell.strip() for cell in row.split('|')[1:-1]]
                new_lines.append(' & '.join(cells) + ' \\\\')
            new_lines.append('\\hline')
            new_lines.append('\\end{tabular}')
        else:
            new_lines.extend(table_lines)
    markdown_text = '\n'.join(new_lines)

    return markdown_text

def main():
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'PROJECT_REPORT.md'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'report.tex'

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)

    latex_content = markdown_to_latex(markdown_content)

    # Add a basic LaTeX preamble
    preamble = r"""\\documentclass[12pt]{article}
\\usepackage[utf8]{inputenc}
\\usepackage[T1]{fontenc}
\\usepackage{turkish}% For Turkish language support if needed, otherwise use english
\\usepackage{hyperref}
\\usepackage{geometry}
\\geometry{margin=1in}
\\usepackage{booktabs}% For better tables if needed
\\usepackage{longtable}% For tables that span multiple pages
\\usepackage{array}
\\usepackage{verbatim}% For verbatim environment
\\usepackage{amsmath}
\\usepackage{amssymb}
\\usepackage{graphicx}
\\usepackage{float}
\\hypersetup{
    colorlinks=true,
    linkcolor=blue,
    filecolor=magenta,
    urlcolor=cyan,
}
\\urlstyle{same}

\\title{GNU RADIO TABANLI GÜÇ ETKİ ALANLI NOMA SİSTEMİ İLE ARDIŞIK GİRİŞİM İPTALİ (SIC) UYGULAMASI}
\\author{}
\\date{}

\\begin{document}

\\maketitle

"""

    postamble = r"""
\\end{document}
"""

    full_latex = preamble + latex_content + postamble

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(full_latex)
        print(f"LaTeX file written to {output_file}")
    except Exception as e:
        print(f"Error writing to {output_file}: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()