import re
from pathlib import Path

PO_PATH = Path('desktop/locale/tr/LC_MESSAGES/messages.po')
BACKUP = PO_PATH.with_suffix('.po.bak')

# Detect common pictographs by explicit characters (avoid complex unicode ranges
# that may cause encoding issues in source). This list covers emojis used in the UI.
PICTOS = set(list('📦📭✅⚠️💳📅🗑️🔍🔎🛈💰👥👤📞📧💵✏️❌'))

def clean_po(path: Path):
    text = path.read_text(encoding='utf-8')
    # backup
    path.write_text(text, encoding='utf-8')
    BACKUP.write_text(text, encoding='utf-8')

    lines = text.splitlines()
    out_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # remove fuzzy flags
        if line.strip().startswith('#,') and 'fuzzy' in line:
            # skip this line
            i += 1
            continue
        # handle msgid/msgstr blocks
        if line.startswith('msgid '):
            msgid_line = line
            # capture msgid possibly multi-line
            msgid = ''
            if msgid_line.strip() == 'msgid ""':
                # header; copy as-is
                out_lines.append(line)
                i += 1
                continue
            else:
                msgid = re.match(r'msgid\s+"(.*)"', msgid_line).group(1)
            # peek ahead for msgstr
            j = i + 1
            # skip comments between
            while j < len(lines) and lines[j].strip().startswith('#'):
                out_lines.append(lines[j])
                j += 1
            if j < len(lines) and lines[j].startswith('msgstr '):
                msgstr_line = lines[j]
                m = re.match(r'msgstr\s+"(.*)"', msgstr_line)
                if m:
                    msgstr = m.group(1)
                    # if msgstr contains pictograph/emoji while msgid is plain text, replace
                    if any(p in msgstr for p in PICTOS) and not any(p in msgid for p in PICTOS):
                        # replace msgstr with msgid
                        out_lines.append(msgid_line)
                        out_lines.append(f'msgstr "{msgid}"')
                        i = j + 1
                        continue
                    # also if msgstr seems unrelated (very different) -- simple heuristic: contains 'Paket' emoji or '📦' etc.
                    if any(p in msgstr for p in PICTOS) and not any(p in msgid for p in PICTOS):
                        out_lines.append(msgid_line)
                        out_lines.append(f'msgstr "{msgid}"')
                        i = j + 1
                        continue
                    # otherwise copy both lines
                    out_lines.append(msgid_line)
                    out_lines.append(msgstr_line)
                    i = j + 1
                    continue
                else:
                    out_lines.append(msgid_line)
                    i += 1
                    continue
            else:
                out_lines.append(msgid_line)
                i += 1
                continue
        else:
            out_lines.append(line)
            i += 1
    new_text = '\n'.join(out_lines) + '\n'
    path.write_text(new_text, encoding='utf-8')
    print('Cleaned PO written to', path)

if __name__ == '__main__':
    clean_po(PO_PATH)
