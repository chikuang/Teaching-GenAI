"""Output contracts shared by Chapter 10 and the live RAG experiments.

These checks establish structure and provenance membership, not semantic truth.
"""
import json


def parse_object(raw):
    def invalid_constant(value):
        raise ValueError('Nonfinite JSON constant: ' + value)
    result = json.loads(raw, parse_constant=invalid_constant)
    if not isinstance(result, dict):
        raise ValueError('Expected a JSON object')
    return result


def parse_transport(raw):
    """Permit bare JSON or exactly one enclosing code fence; change no fields."""
    lines = raw.strip().splitlines()
    if len(lines) >= 3 and lines[0] in ('```json', '```') and lines[-1] == '```':
        raw = '\n'.join(lines[1:-1])
    return parse_object(raw)


def validate_response(response, selected):
    if isinstance(response, str):
        response = parse_object(response)
    required = {'answer', 'citations', 'abstain'}
    if not isinstance(response, dict) or set(response) != required:
        raise ValueError('Response must have exactly answer, citations, abstain')
    if not isinstance(response['answer'], str) or not response['answer'].strip():
        raise ValueError('Answer must be a nonempty string')
    if type(response['abstain']) is not bool:
        raise ValueError('abstain must be boolean')
    citations = response['citations']
    if not isinstance(citations, list) or not all(isinstance(x, str) for x in citations):
        raise ValueError('Citations must be a list of strings')
    allowed = {h['id'] for h in selected}
    if len(citations) != len(set(citations)) or not set(citations) <= allowed:
        raise ValueError('Citations must be unique IDs from the supplied context')
    if response['abstain'] and citations:
        raise ValueError('An abstention must not claim supporting citations')
    if not response['abstain'] and not citations:
        raise ValueError('An answered response requires a citation')
    return response


def assess_response(raw, selected, allow_fence=False):
    """Keep parsing and contract validity separate; semantic scoring is external."""
    result = {'json_parseable': False, 'contract_valid': False,
              'semantic_support': None, 'parsed': None, 'error': None}
    try:
        parsed = (parse_transport if allow_fence else parse_object)(raw)
        result.update(json_parseable=True, parsed=parsed)
        validate_response(parsed, selected)
        result['contract_valid'] = True
    except (ValueError, TypeError) as error:
        result['error'] = str(error)
    return result
