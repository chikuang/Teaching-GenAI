"""Scientific and contract regressions prompted by the beginner review."""
from pathlib import Path
import ast
import hashlib
import json
import re
import unittest
import numpy as np
import nbformat
from labs import contracts, rag_core
from labs.guided_systems import run_decisions, rule_policy, simulation_workflow

ROOT = Path(__file__).resolve().parents[1]


def chapter_nodes(number):
    source = next((ROOT/'docs/chapters').glob(number+'-*.md')).read_text()
    cells = re.findall(r'```\{code-cell\} python\n(.*?)\n```', source, re.S)
    return [node for cell in cells for node in ast.parse(cell).body]


class Contracts(unittest.TestCase):
    def test_rag_rejects_empty_uncited_duplicate_and_foreign_ids(self):
        context = [{'id': 'allowed'}]
        for answer, citations in [('', ['allowed']), ('ok', []),
                                  ('ok', ['allowed', 'allowed']), ('ok', ['other'])]:
            assessment = contracts.assess_response(json.dumps({
                'answer': answer, 'citations': citations, 'abstain': False}), context)
            self.assertTrue(assessment['json_parseable'])
            self.assertFalse(assessment['contract_valid'])
        accepted = contracts.assess_response(
            '{"answer":"Insufficient evidence","citations":[],"abstain":true}', context)
        self.assertTrue(accepted['contract_valid'])
        self.assertIsNone(accepted['semantic_support'])

    def test_transport_never_repairs_content(self):
        self.assertEqual(contracts.parse_transport('```json\n{"n":12}\n```'), {'n': 12})
        for raw in ['prefix ```json\n{}\n```', '{"n":NaN}', '[1,2]', '```json\n{"n":}\n```']:
            with self.assertRaises(ValueError):
                contracts.parse_transport(raw)

    def test_paired_bootstrap_accepts_boolean_scores_without_losing_sign(self):
        node = next(n for n in chapter_nodes('11') if isinstance(n, ast.FunctionDef) and n.name == 'paired_bootstrap')
        namespace = {'np': np}
        exec(compile(ast.Module(body=[node], type_ignores=[]), '<exercise>', 'exec'), namespace)
        bootstrap = namespace['paired_bootstrap']
        self.assertTrue(np.all(bootstrap([False], [True]) == 1))
        self.assertTrue(np.all(bootstrap([True], [False]) == -1))
        self.assertTrue(np.all(bootstrap([True, False], [True, False]) == 0))
        for a, b in [([], []), ([1], [1, 0]), ([[1]], [[1]]), ([np.nan], [0])]:
            with self.assertRaises(ValueError):
                bootstrap(a, b)

    def test_observed_recovery_and_decision_budget(self):
        policy = rule_policy('spring_pilot', 'median', recover=True)
        result = run_decisions(policy, 'Median of spring_pilot')
        self.assertEqual(result['answer'], 1.5)
        self.assertEqual([s['action']['tool'] for s in result['trace']],
                         ['lookup', 'resolve', 'lookup', 'summarize', 'finish'])
        self.assertEqual((result['decisions'], result['tool_calls']), (5, 4))
        limited = run_decisions(policy, 'Same task', max_decisions=4)
        self.assertEqual(limited['status'], 'budget_exhausted')
        unknown = run_decisions(rule_policy('missing', 'median', recover=True), 'Unknown')
        self.assertEqual(unknown['status'], 'abstained')

    def test_simulation_rejects_invalid_intent_without_computing(self):
        for raw in ['{"family":"cauchy","n":22}', '{"family":"normal","n":true}',
                    '{"family":"normal","n":5000}', '{"family":"normal","n":12,"extra":0}']:
            result = simulation_workflow(lambda messages, **kwargs: raw, 'fixture')
            self.assertEqual(result['status'], 'invalid')
            self.assertNotIn('tool_result', result)
        from labs.live_tasks import BASE_SPEC
        card = dict(BASE_SPEC, family='cauchy', n=22)
        result = simulation_workflow(lambda messages, **kwargs: json.dumps(card), 'Cauchy', card)
        self.assertEqual(result['status'], 'abstained')
        self.assertNotIn('tool_result', result)



class Continuity(unittest.TestCase):
    def test_same_rag_pipeline_in_chapter_and_live_lab(self):
        names = {'chunk_document', 'words', 'counts', 'retrieve', 'pack_context',
                 'build_messages', 'extractive_backend', 'run_rag'}
        def functions(nodes):
            return {n.name: ast.dump(n, include_attributes=False) for n in nodes
                    if isinstance(n, ast.FunctionDef) and n.name in names}
        chapter = chapter_nodes('10')
        core = ast.parse((ROOT/'labs/rag_core.py').read_text()).body
        self.assertEqual(set(functions(core)), names)
        self.assertEqual(functions(chapter), functions(core))
        for name in ['notes', 'SYSTEM_INSTRUCTION', 'stopwords']:
            def assignment(nodes):
                return next(ast.dump(n, include_attributes=False) for n in nodes
                            if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in n.targets))
            self.assertEqual(assignment(chapter), assignment(core))
        self.assertIs(rag_core.validate_response, contracts.validate_response)

    def test_factorial_includes_one_attempt_with_cache(self):
        assignment = next(n for n in chapter_nodes('13') if isinstance(n, ast.Assign)
                          and any(isinstance(t, ast.Name) and t.id == 'configurations' for t in n.targets))
        config = ast.literal_eval(assignment.value)
        self.assertEqual(config['Cache only'], (0, True))
        self.assertEqual(config['One pass plus cache'], (1, True))
        self.assertTrue({(1, False), (1, True), (3, False), (3, True)} <= set(config.values()))

    def test_live_notebooks_executed_from_current_source(self):
        sources = sorted((ROOT/'labs/notebooks').glob('*.ipynb'))
        self.assertEqual(len(sources), 4)
        for source in sources:
            plain = nbformat.read(source, as_version=4)
            executed = nbformat.read(ROOT/'docs/_static/live-notebooks'/source.name, as_version=4)
            self.assertEqual([(c.cell_type, c.source) for c in plain.cells],
                             [(c.cell_type, c.source) for c in executed.cells])
            for cell in executed.cells:
                if cell.cell_type == 'code':
                    self.assertIsNotNone(cell.execution_count)
                    self.assertFalse(any(o.output_type == 'error' for o in cell.outputs))

    def test_guided_trace_provenance_is_preserved(self):
        for name in ['first-llm', 'rag-bridge', 'rag-bridge-initial', 'agent-bridge', 'capstone-bridge', 'first-llm-v2', 'rag-bridge-v2', 'agent-bridge-v2', 'capstone-bridge-v2']:
            record = json.loads((ROOT/'docs/_static/experiments'/f'{name}.json').read_text())
            self.assertGreater(len(record['calls']), 0)
            for source, digest in record['source_sha256'].items():
                candidates = [ROOT/'labs'/source, ROOT/'labs/archived-guided-initial'/source, ROOT/'labs/archived-guided-v2'/source]
                self.assertTrue(any(p.exists() and hashlib.sha256(p.read_bytes()).hexdigest() == digest for p in candidates), source)
            self.assertTrue(all(c['messages'] and isinstance(c['raw'], str) for c in record['calls']))


if __name__ == '__main__':
    unittest.main()
