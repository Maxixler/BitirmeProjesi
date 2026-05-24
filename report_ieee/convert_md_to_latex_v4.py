import re
import sys

def convert_markdown_to_latex(text):
    lines = text.split('\n')
    output = []
    i = 0
    in_code_block = False
    code_block_lang = ''
    in_list = None  # None, 'itemize', 'enumerate'
    in_blockquote = False

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Handle code blocks (fenced)
        if stripped.startswith('```'):
            if not in_code_block:
                in_code_block = True
                code_block_lang = stripped[3:].strip()
                output.append('\\begin{verbatim}')
            else:
                in_code_block = False
                output.append('\\end{verbatim}')
            i += 1
            continue

        if in_code_block:
            output.append(line)
            i += 1
            continue

        # Now we are not in a code block, process the line for inline elements and block elements.

        # Convert links: [text](url) -> \href{url}{text}
        # We need to output a literal backslash, so we use \\\\ in the replacement string to get a single backslash after processing.
        line = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\\\\href{\\\\2}{\\\\1}', line)

        # Convert inline code: `code` -> \texttt{code}
        line = re.sub(r'`([^`]+)`', r'\\\\texttt{\\\\1}', line)

        # Convert bold: **text** -> \textbf{text}
        line = re.sub(r'\*\*(.*?)\*\*', r'\\\\textbf{\\\\1}', line)

        # Convert italic: *text* -> \textit{text} (but not interfering with bold)
        line = re.sub(r'(?<!\\\\)\\\*(?!\\\*)([^*]+?)(?<!\\\\)\\\*(?!\\\*)', r'\\\\textit{\\\\1}', line)

        # Now handle block elements based on the stripped line

        # Horizontal rule
        if re.match(r'^\\s*[-*_]{3,}\\s*$', stripped):
            if in_list:
                output.append('\\end{' + list_type + '}')
                in_list = None
            if in_blockquote:
                output.append('\\end{quote}')
                in_blockquote = False
            output.append('\\\\hrule')
            i += 1
            continue

        # Heading
        if stripped.startswith('#'):
            if in_list:
                output.append('\\end{' + list_type + '}')
                in_list = None
            if in_blockquote:
                output.append('\\end{quote}')
                in_blockquote = False
            # Count the number of #
            level = 0
            for ch in stripped:
                if ch == '#':
                    level += 1
                else:
                    break
            heading_text = stripped[level:].strip()
            if level == 1:
                output.append('\\\\section{' + heading_text + '}')
            elif level == 2:
                output.append('\\\\subsection{' + heading_text + '}')
            elif level == 3:
                output.append('\\\\subsubsection{' + heading_text + '}')
            elif level == 4:
                output.append('\\\\paragraph{' + heading_text + '}')
            elif level == 5:
                output.append('\\\\subparagraph{' + heading_text + '}')
            else:
                output.append('\\\\subparagraph{' + heading_text + '}')
            i += 1
            continue

        # Blockquote
        if stripped.startswith('> '):
            if not in_blockquote:
                output.append('\\\\begin{quote}')
                in_blockquote = True
            # Remove the > and space
            quote_line = stripped[2:]
            output.append('  ' + quote_line)
            i += 1
            continue
        else:
            if in_blockquote:
                output.append('\\\\end{quote}')
                in_blockquote = False

        # Lists
        # Unordered list
        if re.match(r'^\\s*[-*]\\s+', stripped):
            if in_list != 'itemize':
                if in_list:
                    output.append('\\end{' + list_type + '}')
                output.append('\\\\begin{itemize}')
                in_list = 'itemize'
            # Remove the bullet and any spaces after it
            item_text = re.sub(r'^\\s*[-*]\\s+', '', stripped)
            output.append('  \\\\item ' + item_text)
            i += 1
            continue
        # Ordered list
        if re.match(r'^\\s*\\d+\\.\\s+', stripped):
            if in_list != 'enumerate':
                if in_list:
                    output.append('\\end{' + list_type + '}')
                output.append('\\\\begin{enumerate}')
                in_list = 'enumerate'
            # Remove the number dot and spaces
            item_text = re.sub(r'^\\s*\\d+\\.\\s+', '', stripped)
            output.append('  \\\\item ' + item_text)
            i += 1
            continue
        else:
            if in_list:
                output.append('\\end{' + list_type + '}')
                in_list = None

        # If we reach here, it's a regular paragraph line
        if stripped == '':
            output.append('')
        else:
            output.append(line)

        i += 1

    # Close any open environments
    if in_list:
        output.append('\\end{' + list_type + '}')
    if in_blockquote:
        output.append('\\end{quote}')
    if in_code_block:
        output.append('\\end{verbatim}')

    return '\n'.join(output)

def main():
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'PROJECT_REPORT.md'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'report.tex'

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)

    latex_body = convert_markdown_to_latex(markdown_content)

    preamble = r'''\documentclass[12pt]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{turkish}
\usepackage{hyperref}
\usepackage{geometry}
\geometry{margin=1in}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{array}
\usepackage{verbatim}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{graphicx}
\usepackage{float}
\hypersetup{
    colorlinks=true,
    linkcolor=blue,
    filecolor=magenta,
    urlcolor=cyan,
}
\urlstyle{same}

\title{GNU RADIO TABANLI GÜÇ ETKİ ALANLI NOMA SİSTEMİ İLE ARDIŞIK GİRİŞİM İPTALİ (SIC) UYGULAMASI}
\author{}
\date{}

\begin{document}

\maketitle

'''

    postamble = r'''
\end{document}
'''

    full_latex = preamble + latex_body + postamble

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(full_latex)
        print(f"LaTeX file written to {output_file}")
    except Exception as e:
        print(f"Error writing to {output_file}: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()