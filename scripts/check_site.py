"""Check rendered internal links, assets, notebook execution, and portable prose."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit
import json
import re

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
def course_target(path, href):
    url = urlsplit(href)
    if url.scheme or url.netloc:
        if url.netloc != 'chikuang.github.io' or not url.path.startswith('/teaching/genai/'):
            return None, url
        target = SITE / unquote(url.path.removeprefix('/teaching/genai/'))
    else:
        target = path.parent / unquote(url.path) if url.path else path
    target = target.resolve()
    if target.is_dir():
        target /= 'index.html'
    return target, url

for path, page in pages.items():
    for href in page.links:
        target, url = course_target(path, href)
        if target is None or not (url.path or url.fragment):
            continue
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
            for href in re.findall(r'\]\(([^\s)]+)\)', source):
                if not href.startswith('https://chikuang.github.io/teaching/genai/'):
                    continue
                target, url = course_target(path, href)
                if not target.exists() or (url.fragment and target in pages and unquote(url.fragment) not in pages[target].ids):
                    errors.append(f'{path.name}: broken published-course link {href}')
assert len(notebooks) == 18, f'Expected 18 executed teaching notebooks, found {len(notebooks)}'
live = list((SITE/'_static/live-notebooks').glob('*.ipynb'))
assert len(live) == 4, f'Expected four executed live notebooks, found {len(live)}'
for path in live:
    book = json.loads(path.read_text())
    cells = [c for c in book['cells'] if c['cell_type'] == 'code']
    if not cells or any(c.get('execution_count') is None or any(o['output_type'] == 'error' for o in c.get('outputs', [])) for c in cells):
        errors.append(f'{path.name}: incomplete live notebook')
students = list((SITE/'_static/assignments').glob('*-student.ipynb'))
assert len(students) == 14, f'Expected 14 unfinished student notebooks, found {len(students)}'
for path in students:
    book = json.loads(path.read_text())
    code = [c for c in book['cells'] if c['cell_type'] == 'code']
    if sum('raise NotImplementedError' in ''.join(c['source']) for c in code) != 1:
        errors.append(f'{path.name}: missing independent implementation stub')
    if any(c.get('execution_count') is not None or c.get('outputs') for c in code):
        errors.append(f'{path.name}: student template unexpectedly contains worked outputs')
if errors:
    raise SystemExit('\n'.join(errors))
print(f'Checked {len(pages)} HTML pages, {len(notebooks)} teaching notebooks, {len(live)} live notebooks and {len(students)} student templates: internal links, assets, and exports passed.')
