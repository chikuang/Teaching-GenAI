"""Download the exact public model revision used by the live lab (about 3 GB)."""
from pathlib import Path
import json
from huggingface_hub import snapshot_download

identity = json.loads(Path(__file__).with_name('model.json').read_text())
target = Path(__file__).resolve().parents[1] / '_models' / 'qwen2.5-1.5b'
snapshot_download(repo_id=identity['model_id'], revision=identity['revision'],
                  local_dir=target, token=False,
                  allow_patterns=['*.json', '*.safetensors', '*.txt', '*.model', 'LICENSE', 'README.md'])
(target / 'course-model.json').write_text(json.dumps(identity, indent=2)+'\n')
print('Pinned model ready:', target)
