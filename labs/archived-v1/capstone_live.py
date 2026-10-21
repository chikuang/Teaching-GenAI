"""A separately labeled capstone development demo after the strict-schema pilot.

Run: python labs/capstone_live.py --model-dir _models/qwen2.5-1.5b --output .runs/capstone-demo.json
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from llm_lab import LocalLM, MODEL, parse_object, keys, numeric, coverage_tool


def parse_transport(raw):
    """Accept bare JSON or one enclosing json code fence; never repair its contents."""
    text = raw.strip()
    lines = text.splitlines()
    if len(lines) >= 3 and lines[0] in ('```json', '```') and lines[-1] == '```':
        text = '\n'.join(lines[1:-1])
    return parse_object(text)


TASKS = [
    {'question': 'Use iid normal observations, sample size 36, to estimate coverage of the mean plus or minus 1.96 estimated standard errors.', 'family': 'normal', 'n': 36},
    {'question': 'Use iid exponential observations, sample size 24, to estimate coverage of the mean plus or minus 1.96 estimated standard errors.', 'family': 'exponential', 'n': 24},
    {'question': 'Use iid Cauchy observations, sample size 30, to estimate coverage.', 'family': 'unsupported', 'n': 30},
]


def run(model_dir, output):
    lm = LocalLM(model_dir)
    rows = []
    for task in TASKS:
        start = len(lm.calls)
        row = {'question': task['question'], 'success': False}
        try:
            raw = lm([
                {'role': 'system', 'content': 'Extract the sampling distribution and sample size. The interval formula does not determine the sampling distribution. Only normal and exponential are supported. Return exactly two keys: family and n. Follow the JSON examples.'},
                {'role': 'user', 'content': 'Use exponential observations with sample size 10.'},
                {'role': 'assistant', 'content': '{"family":"exponential","n":10}'},
                {'role': 'user', 'content': 'Use uniform observations with sample size 15.'},
                {'role': 'assistant', 'content': '{"family":"unsupported","n":15}'},
                {'role': 'user', 'content': task['question']},
            ])
            request = parse_transport(raw)
            keys(request, ['family', 'n'])
            row['request'] = request
            intent_correct = request == {'family': task['family'], 'n': task['n']}
            row['interpretation_correct'] = intent_correct
            if request['family'] == 'unsupported':
                row.update(status='abstained', success=intent_correct)
            else:
                result = coverage_tool(request['family'], request['n'])
                row['tool_result'] = result
                raw = lm([
                    {'role': 'system', 'content': 'Return JSON with exactly family, n, estimate, explanation. Copy family, n, estimate from the input. Explain that estimated coverage is not a guarantee. Do not add fields.'},
                    {'role': 'user', 'content': '{"family":"normal","n":10,"estimate":0.9}'},
                    {'role': 'assistant', 'content': '{"family":"normal","n":10,"estimate":0.9,"explanation":"This Monte Carlo estimate describes the specified procedure; it is not a coverage guarantee."}'},
                    {'role': 'user', 'content': json.dumps(result)},
                ], max_new_tokens=160)
                report = parse_transport(raw)
                keys(report, ['family', 'n', 'estimate', 'explanation'])
                if (type(report['n']) is not int or not numeric(report['estimate'])
                        or any(report[k] != result[k] for k in ['family', 'n', 'estimate'])
                        or not isinstance(report['explanation'], str)):
                    raise ValueError('Report does not preserve tool fields')
                row.update(status='completed', report=report, success=intent_correct)
        except (ValueError, TypeError) as error:
            row.update(status='invalid', error=str(error))
        row['call_ids'] = list(range(start, len(lm.calls)))
        rows.append(row)
        print(task['family'], row['status'], row['success'], flush=True)
    record = {'schema_version': 1, 'created_utc': datetime.now(timezone.utc).isoformat(),
              'model': MODEL, 'runtime': lm.versions,
              'protocol': 'Development demo after inspecting strict-schema failures. Adds disjoint few-shot formatting examples and explicitly permits one enclosing JSON code fence. New scenario sizes illustrate operation, not an unbiased performance estimate.',
              'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'tasks': TASKS, 'rows': rows, 'calls': lm.calls}
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model-dir', required=True)
    parser.add_argument('--output', default='.runs/capstone-demo.json')
    args = parser.parse_args()
    run(args.model_dir, args.output)
