import sys
from pathlib import Path

try:
    from PyPDF2 import PdfReader
except Exception as e:
    print('MISSING_LIB', e)
    sys.exit(2)

if len(sys.argv) < 3:
    print('Usage: python extract_pdf.py <input.pdf> <output.txt>')
    sys.exit(1)

inp = Path(sys.argv[1])
out = Path(sys.argv[2])

if not inp.exists():
    print('NOFILE')
    sys.exit(3)

reader = PdfReader(str(inp))
text = []
for p in reader.pages:
    try:
        t = p.extract_text()
    except Exception:
        t = ''
    if t:
        text.append(t)

out.write_text('\n\n'.join(text), encoding='utf-8')
print('OK')
