"""Current six-field, reviewed-request capstone demonstration.

Historical two-field runner and results are preserved under archived-v1/.
Run: python labs/capstone_live.py --model-dir _models/qwen2.5-1.5b
"""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from labs.contracts import parse_transport
from labs.llm_lab import LocalLM
from labs.guided_systems import simulation_workflow, scope_reasons
from labs.live_tasks import CAPSTONE_CASES
from labs.notebook_support import save_run


def run(model_dir, output=None):
    lm = LocalLM(model_dir)
    rows = []
    for task_id, question, card in CAPSTONE_CASES:
        start = len(lm.calls)
        row = simulation_workflow(lm, question, confirmed_request=card)
        row['task_id'] = task_id
        row['call_ids'] = list(range(start, len(lm.calls)))
        row['intent_correct'] = row.get('request') == card
        expected = 'abstained' if scope_reasons(card) else 'completed'
        row['task_success'] = row['intent_correct'] and row['status'] == expected
        rows.append(row)
        print(task_id, row['status'], row['task_success'], flush=True)
    path = save_run(Path(__file__).resolve().parents[1], 'capstone-bridge', lm, rows)
    if output is not None and Path(output).resolve() != path.resolve():
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text(path.read_text())
    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model-dir', required=True)
    parser.add_argument('--output')
    args = parser.parse_args()
    run(args.model_dir, args.output)
