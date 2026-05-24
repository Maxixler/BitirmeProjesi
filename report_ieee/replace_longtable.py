import re
import sys

def replace_longtable_to_tabular(content):
    # Pattern to match a longtable block that starts with \begin{longtable} and has \def\LTcaptype{none} in the next line or within the prelude
    # We'll parse line by line.
    lines = content.split('\n')
    output = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith('\begin{longtable}'):
            # Check if this longtable is one we want to convert (simple ones with LTcaptype)
            # Look ahead for \def\LTcaptype{none} within the next few lines before the actual content
            j = i
            found_ltcaptype = False
            # We'll look until we see either \end{longtable} or we pass a reasonable number of lines
            while j < n and not lines[j].strip().startswith('\end{longtable}'):
                if '\def\LTcaptype{none}' in lines[j]:
                    found_ltcaptype = True
                    break
                j += 1
            # Also need to capture the whole block from i to the matching \end{longtable}
            # Find the end index
            end = i
            while end < n and not lines[end].strip().startswith('\end{longtable}'):
                end += 1
            if end < n:
                end_inclusive = end  # include the \end{longtable} line
                if found_ltcaptype:
                    # Convert this block
                    block_lines = lines[i:end_inclusive+1]
                    block = '\n'.join(block_lines)
                    # Replace \begin{longtable} with \begin{tabular}
                    # Replace \end{longtable} with \end{tabular}
                    # Remove the line with \newcounter{none} (if present) and \def\LTcaptype{none}
                    new_block = block.replace('\begin{longtable}', '\begin{tabular}').replace('\end{longtable}', '\end{tabular}')
                    # Remove the two lines
                    new_block_lines = []
                    for bl in new_block.split('\n'):
                        if bl.strip() == '\newcounter{none} % for unnumbered tables':
                            continue
                        if bl.strip() == '\def\LTcaptype{none} % for unnumbered tables':
                            continue
                        new_block_lines.append(bl)
                    new_block = '\n'.join(new_block_lines)
                    output.append(new_block)
                    i = end_inclusive + 1
                    continue
                else:
                    # Not one of our special longtables, keep as is
                    output.append(line)
                    i += 1
                    continue
            else:
                # No ending found, just keep line
                output.append(line)
                i += 1
                continue
        else:
            output.append(line)
            i += 1
    return '\n'.join(output)

if __name__ == '__main__':
    with open('report_ieee.tex', 'r', encoding='utf-8') as f:
        content = f.read()
    new_content = replace_longtable_to_tabular(content)
    with open('report_ieee.tex', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('Replacement done')
