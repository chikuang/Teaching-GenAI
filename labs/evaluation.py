"""One record format across RAG, agents, inference and controlled simulations."""
from pathlib import Path
import hashlib
import json
from .contracts import parse_transport
from .llm_lab import numeric

REQUIRED = {'task_id','task_family','condition','replicate','data_kind','model_id','prompt_version',
            'source_record','source_sha256','call_ids','raw_response','packed_ids','tool_trace',
            'intent_correct','json_parseable','contract_valid','semantic_support','complete','task_success',
            'llm_calls','tool_calls','latency_seconds','review_note'}


def make_row(task_id, task_family, condition, **values):
    row = dict(task_id=task_id, task_family=task_family, condition=condition, replicate=0,
               data_kind='fixture', model_id=None, prompt_version=None, source_record=None,
               source_sha256=None, call_ids=[], raw_response=None, packed_ids=[], tool_trace=[],
               intent_correct=None, json_parseable=None, contract_valid=None, semantic_support=None, complete=None,
               task_success=None, llm_calls=0, tool_calls=0, latency_seconds=None, review_note=None)
    row.update(values)
    return row


def validate_rows(rows):
    if not rows:
        raise ValueError('An evaluation must contain rows')
    seen = set()
    for row in rows:
        if not REQUIRED <= row.keys():
            raise ValueError('Missing evaluation fields')
        for field in ['task_id', 'task_family', 'condition']:
            if not isinstance(row[field], str) or not row[field].strip():
                raise ValueError(field + ' must be nonempty text')
        key = (row['task_id'], row['condition'], row['replicate'])
        if key in seen:
            raise ValueError('Duplicate task/condition/replicate')
        seen.add(key)
        if row['data_kind'] not in {'actual_llm','deterministic_baseline','synthetic','fixture'}:
            raise ValueError('Unknown data origin')
        if row['semantic_support'] not in (None,'supported','contradicted','insufficient_evidence'):
            raise ValueError('Unknown support label')
        for field in ['intent_correct','json_parseable','contract_valid','complete','task_success']:
            if row[field] is not None and type(row[field]) is not bool:
                raise ValueError(field + ' must be Boolean or null')
        for field in ['replicate','llm_calls','tool_calls']:
            if type(row[field]) is not int or row[field] < 0:
                raise ValueError(field + ' must be a nonnegative integer')
        if row['task_success'] is True and not (row['intent_correct'] is True
                and row['contract_valid'] is True and row['semantic_support'] == 'supported'
                and row['complete'] is True and row['review_note']):
            raise ValueError('Success requires all checks and a review note')
    return rows


def paired_scores(rows, condition_a, condition_b, metric='task_success'):
    """Join by task and replicate; never silently drop a missing or unreviewed case."""
    validate_rows(rows)
    groups = {}
    for row in rows:
        if row['condition'] in (condition_a, condition_b):
            groups.setdefault((row['task_id'],row['replicate']), {})[row['condition']] = row
    if not groups:
        raise ValueError('No tasks in the requested comparison')
    pairs = []
    for key, group in sorted(groups.items()):
        if set(group) != {condition_a,condition_b}:
            raise ValueError('Missing condition for ' + str(key))
        a,b=group[condition_a],group[condition_b]
        if a['task_family'] != b['task_family']:
            raise ValueError('Task family mismatch')
        if (a['data_kind'] == 'synthetic') != (b['data_kind'] == 'synthetic'):
            raise ValueError('Do not pool synthetic and nonsynthetic outcomes')
        if a[metric] is None or b[metric] is None:
            raise ValueError('Unreviewed outcome is not a zero or a pass')
        pairs.append({'task_id':key[0],'replicate':key[1], 'a':float(a[metric]),
                      'b':float(b[metric]),'difference':float(b[metric])-float(a[metric])})
    return pairs


def load_evaluation(root):
    path = Path(root)/'docs/_static/evaluation/common-evaluation.json'
    return validate_rows(json.loads(path.read_text())['rows'])


def parses_as_object(raw):
    try:
        parse_transport(raw)
        return True
    except (ValueError, TypeError):
        return False


def action_contract(trace):
    """Check proposed action shapes; an unknown dataset may still be well formed."""
    fields = {'lookup': {'dataset'}, 'resolve': {'name'},
              'summarize': {'dataset', 'statistic'}, 'finish': {'value'}, 'abstain': set()}
    for step in trace:
        action = step.get('action')
        if not isinstance(action, dict) or set(action) != {'tool', 'arguments'}:
            return False
        tool, arguments = action['tool'], action['arguments']
        if not isinstance(tool, str) or tool not in fields or not isinstance(arguments, dict):
            return False
        if set(arguments) != fields[tool]:
            return False
        if tool == 'finish' and not numeric(arguments['value']):
            return False
        if any(not isinstance(arguments[k], str) for k in ('dataset', 'name') if k in arguments):
            return False
        if tool == 'summarize' and arguments['statistic'] not in ('mean', 'median'):
            return False
    return bool(trace)


def guided_rows(root):
    """Mechanical fields only. Editorial support/completeness are joined separately."""
    root = Path(root)
    rows = []
    def base(name, task_id, family, condition, call_ids, **extra):
        path = root/'docs/_static/experiments'/f'{name}.json'
        record = json.loads(path.read_text())
        calls = [record['calls'][i] for i in call_ids]
        return make_row(task_id,family,condition,data_kind='actual_llm' if calls else 'deterministic_baseline',
                        model_id=record['model']['model_id'] if calls else None,
                        prompt_version=record['source_sha256']['guided_systems.py'] if family=='capstone' or family=='agent' else record['source_sha256']['rag_core.py'] if family=='rag' else 'first-llm-notebook-v3',
                        source_record=name+'.json',source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                        call_ids=call_ids,raw_response=[c['raw'] for c in calls],llm_calls=len(calls),
                        latency_seconds=round(sum(c['elapsed_seconds'] for c in calls),3) if calls else None,**extra)
    records={name:json.loads((root/'docs/_static/experiments'/f'{name}.json').read_text()) for name in ['first-llm','rag-bridge','agent-bridge','capstone-bridge']}
    rows.append(base('first-llm','mc-error','concept','llm',[0],intent_correct=True,contract_valid=True))
    rag=records['rag-bridge']['results']
    context=rag['result']['trace']['context_ids']
    for condition,ids,valid in [('extractive',[],True),('llm_inspection',[0],rag['assessment']['contract_valid']),('llm',[1],rag['result']['status']!='rejected')]:
        row=base('rag-bridge','dependent-bootstrap','rag',condition,ids,packed_ids=context,
                 intent_correct=True,contract_valid=valid,
                 json_parseable=all(parses_as_object(records['rag-bridge']['calls'][i]['raw']) for i in ids) if ids else None)
        if not ids:row['raw_response']=rag['baseline']['answer']
        rows.append(row)
    agent=records['agent-bridge']['results']
    for condition in ['fixed','programmed','actual']:
        result=agent[condition]
        ids=list(range(len(records['agent-bridge']['calls']))) if condition=='actual' else []
        intent = True  # Rule baselines are explicitly given structured intent.
        if condition == 'actual':
            intent = None
            if result['status'] == 'finished':
                intent = (result.get('result', {}).get('dataset') == 'pilot_b'
                          and result.get('result', {}).get('statistic') == 'median')
        rows.append(base('agent-bridge','alias-median','agent',condition,ids,intent_correct=intent,
                         contract_valid=action_contract(result['trace']),
                         json_parseable=all(parses_as_object(records['agent-bridge']['calls'][i]['raw']) for i in ids) if ids else None,
                         tool_trace=result['trace'],tool_calls=result['tool_calls'],
                         executor_status=result['status']))
    for result in records['capstone-bridge']['results']:
        ids=result['call_ids']
        rows.append(base('capstone-bridge',result['task_id'],'capstone','reviewed_interpreter',ids,
                         intent_correct=result['intent_correct'],contract_valid='request' in result,
                         json_parseable=all(parses_as_object(records['capstone-bridge']['calls'][i]['raw']) for i in ids),
                         tool_calls=int('tool_result' in result),tool_trace=[result['tool_result']] if 'tool_result' in result else [],
                         executor_status=result['status'],request=result.get('request'),confirmed_request=result.get('confirmed_request')))
    return rows
