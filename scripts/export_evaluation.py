"""Join declared editorial annotations to immutable recorded responses.

A changed answer requires a new review; this script never invents semantic labels.
"""
from pathlib import Path
import csv
import hashlib
import json
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from labs.evaluation import guided_rows, validate_rows


def response_digest(row):
    evidence = {key:row.get(key) for key in ['raw_response','packed_ids','tool_trace','request','confirmed_request','executor_status']}
    return hashlib.sha256(json.dumps(evidence,sort_keys=True).encode()).hexdigest()


def main():
    folder=ROOT/'docs/_static/evaluation'
    annotations=json.loads((folder/'editorial-annotations.json').read_text())['annotations']
    rows=guided_rows(ROOT)
    for row in rows:
        key=f"{row['task_id']}|{row['condition']}"
        annotation=annotations[key]
        if annotation['response_digest'] != response_digest(row):
            raise ValueError('Changed response/evidence requires review: '+key)
        row.update({k:annotation[k] for k in ['semantic_support','complete','task_success','review_note']})
    validate_rows(rows)
    output={'schema_version':1,'protocol':'Authored development observations; one trajectory per condition. No population accuracy claim. Latency is the sum of recorded model-call elapsed seconds, excluding model loading and tool runtime. Baseline latency is unmeasured (null), not zero.',
            'review_method':'Worked editorial annotations by the course revision assistant after inspecting the saved responses and evidence. Not an independent human annotation study.', 'rows':rows}
    (folder/'common-evaluation.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
    with (folder/'common-evaluation.csv').open('w',newline='') as handle:
        columns=list(rows[0])+sorted(set().union(*(r.keys() for r in rows))-rows[0].keys())
        writer=csv.DictWriter(handle,fieldnames=columns,extrasaction='ignore');writer.writeheader()
        for row in rows:
            writer.writerow({k:json.dumps(row.get(k),ensure_ascii=False) if isinstance(row.get(k),(dict,list)) else row.get(k) for k in columns})
    print('Exported',len(rows),'reviewed rows with unchanged source evidence.')


if __name__=='__main__':main()
