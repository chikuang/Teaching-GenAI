"""Check rendered internal links, assets, notebook execution, and portable prose."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit
import json

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT/'_build/html'
class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids, self.links = set(), []
        self.feed(text)
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        for key in ('href', 'src'):
            if key in attrs:
                self.links.append(attrs[key])

# Theme packages ship Jinja macro templates as static assets; they are not rendered pages.
pages = {p.resolve(): Page(p.read_text()) for p in SITE.rglob('*.html')
         if '_static' not in p.relative_to(SITE).parts}
errors = []
for path, page in pages.items():
    for href in page.links:
        url = urlsplit(href)
        if url.scheme or url.netloc or not (url.path or url.fragment):
            continue
        target = (path.parent/unquote(url.path)).resolve() if url.path else path
        if target.is_dir():
            target /= 'index.html'
        if not target.exists():
            errors.append(f'{path.relative_to(SITE)}: missing {href}')
        elif url.fragment and target in pages and unquote(url.fragment) not in pages[target].ids:
            errors.append(f'{path.relative_to(SITE)}: missing anchor {href}')
notebooks = list((SITE/'notebooks').glob('*.ipynb'))
for path in notebooks:
    nb = json.loads(path.read_text())
    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            if cell.get('execution_count') is None or any(o['output_type']=='error' for o in cell.get('outputs', [])):
                errors.append(f'{path.name}: unexecuted or failed cell')
        elif cell['cell_type'] == 'markdown':
            source = ''.join(cell['source'])
            if '{tabularcolumns}' in source or '{dropdown}' in source or '{eq}`' in source:
                errors.append(f'{path.name}: unconverted publishing directive')
assert len(notebooks) == 17, f'Expected 17 executed notebooks, found {len(notebooks)}'
if errors:
    raise SystemExit('\n'.join(errors))
print(f'Checked {len(pages)} HTML pages and {len(notebooks)} executed notebooks: internal links, assets, and exports passed.')
