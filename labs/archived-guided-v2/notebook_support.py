"""Save provenance from actual notebook calls; never synthesize model outputs."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
from .llm_lab import MODEL


def save_run(root, name, lm, results):
    root = Path(root)
    sources = ['contracts.py', 'llm_lab.py', 'rag_core.py', 'guided_systems.py', 'notebook_support.py']
    record = {'created_utc': datetime.now(timezone.utc).isoformat(), 'model': MODEL,
              'runtime': lm.versions, 'calls': lm.calls, 'results': results,
              'protocol': 'Guided development demonstration. Actual local model calls; no hidden answer replacement. Authored tasks, not a sampled population benchmark.',
              'source_sha256': {s: hashlib.sha256((root/'labs'/s).read_bytes()).hexdigest() for s in sources}}
    path = root/'.runs'/f'{name}.json'
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n')
    print('Saved actual calls and results to', path.name)
    return path
