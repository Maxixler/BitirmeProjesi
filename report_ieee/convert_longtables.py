import re
import sys

def convert_longtables(content):
    lines = content.split('\n')
    output = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()
        # Check for start of longtable
        if stripped.startswith('\begin{longtable}'):
            # Find the matching \end{longtable}
            start = i
            # We need to capture the column specification from the longtable argument
            # The line may look like: \begin{longtable}[]{@{}ll@{}}
            # or \begin{longtable}[c]{@{}ll@{}}
            # Extract the part after \begin{longtable}
            # We'll assume the format is \begin{longtable}[pos]{cols}
            # Use regex to extract the column spec (the {...} at the end)
            match = re.match(r'\\begin\{longtable\}(?:\[[^\]]*\])?\{(.*)\}', line)
            if match:
                col_spec = match.group(1)
                # Replace with \begin{tabular}{col_spec}
                output.append('\\begin{tabular}{' + col_spec + '}')
                i += 1
                # Now process lines until we find \end{longtable}
                # We'll skip certain longtable-specific lines
                while i < n and not lines[i].strip().startswith('\end{longtable}'):
                    cline = lines[i]
                    cstripped = cline.strip()
                    # Skip lines that are longtable specific
                    if cstripped == '\endhead' or cstripped == '\endfirsthead' or cstripped == '\endfoot' or cstripped == '\endlastfoot':
                        i += 1
                        continue
                    if cstripped == '\newcounter{none} % for unnumbered tables':
                        i += 1
                        continue
                    if cstripped == '\def\LTcaptype{none} % for unnumbered tables':
                        i += 1
                        continue
                    # Remove \noalign{} that appears alone or after a rule on the same line?
                    # We'll remove a standalone \noalign{} line, but if it's attached to a rule we keep the rule.
                    # Actually, in our file, we see lines like: \toprule\noalign{}
                    # We want to keep \toprule and remove the \noalign{}.
                    # We can do: if the line contains \noalign{}, we split and keep the part before.
                    # But note: there might be multiple things on the line.
                    # Simpler: remove the string '\noalign{}' from the line.
                    newaline = cline.replace('\noalign{}', '')
                    # If after removal the line becomes empty, we might skip it? But we should keep empty lines? We'll keep it.
                    # However, we must be careful not to remove backslashes that are part of other commands.
                    # Since \noalign{} is a distinct token, it's safe.
                    # Also remove the '%' comment lines? We'll keep them.
                    output.append(newaline)
                    i += 1
                # Now we are at the line with \end{longtable} (or past)
                if i < n and lines[i].strip().startswith('\end{longtable}'):
                    output.append('\\end{tabular}')
                    i += 1
                else:
                    # No ending found, just output what we have (should not happen)
                    pass
            else:
                # If we couldn't parse, just output the line and move on
                output.append(line)
                i += 1
        else:
            output.append(line)
            i += 1
    return '\n'.join(output)

if __name__ == '__main__':
    with open('report_ieee.tex', 'r', encoding='utf-8') as f:
        content = f.read()
    new_content = convert_longtables(content)
    with open('report_ieee.tex', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('Longtables converted to tabular')
