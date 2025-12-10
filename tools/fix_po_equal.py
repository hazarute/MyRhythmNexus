from pathlib import Path
import re

PO = Path('desktop/locale/tr/LC_MESSAGES/messages.po')
BACKUP = PO.with_suffix('.po.fixbak')
text = PO.read_text(encoding='utf-8')
BACKUP.write_text(text, encoding='utf-8')
lines = text.splitlines()

out = []
i = 0
while i < len(lines):
    line = lines[i]
    # copy header and comments unchanged
    if line.startswith('msgid '):
        mid = re.match(r'msgid\s+"(.*)"', line)
        if not mid:
            out.append(line)
            i += 1
            continue
        msgid = mid.group(1)
        # copy msgid
        out.append(line)
        # advance to next non-comment
        j = i + 1
        while j < len(lines) and lines[j].startswith('#'):
            out.append(lines[j])
            j += 1
        if j < len(lines) and lines[j].startswith('msgstr '):
            m = re.match(r'msgstr\s+"(.*)"', lines[j])
            if m:
                msgstr = m.group(1)
                if msgid != msgstr:
                    # replace msgstr with msgid
                    out.append(f'msgstr "{msgid}"')
                else:
                    out.append(lines[j])
                i = j + 1
                continue
            else:
                out.append(lines[j])
                i = j + 1
                continue
        else:
            i = j
            continue
    else:
        out.append(line)
        i += 1

new_text = '\n'.join(out) + '\n'
PO.write_text(new_text, encoding='utf-8')
print('Rewrote PO: set msgstr = msgid where they differed. Backup at', BACKUP)
