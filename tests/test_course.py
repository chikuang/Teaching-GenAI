"""Boundary and scientific checks: no pretrained model is needed."""
from pathlib import Path
import ast
import importlib.util
import json
import re
import unittest
import numpy as np
from scipy.stats import t

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('llm_lab', ROOT/'labs/llm_lab.py')
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)


class ToolBoundaries(unittest.TestCase):
    def test_lookup_then_median_and_reject_unobserved_data(self):
        state = {'observed': {}, 'results': []}
        with self.assertRaises(ValueError):
            lab.execute({'tool': 'summarize', 'arguments': {'dataset': 'pilot_b', 'statistic': 'median'}}, state)
        lab.execute({'tool': 'lookup', 'arguments': {'dataset': 'pilot_b'}}, state)
        result = lab.execute({'tool': 'summarize', 'arguments': {'dataset': 'pilot_b', 'statistic': 'median'}}, state)
        self.assertEqual(result['value'], 1.5)
        for bad in [
            {'tool': 'delete', 'arguments': {}},
            {'tool': 'lookup', 'arguments': {'dataset': 'pilot_a', 'extra': 1}},
            {'tool': 'summarize', 'arguments': {'dataset': 'pilot_b', 'statistic': 'variance'}},
        ]:
            with self.assertRaises(ValueError):
                lab.execute(bad, state)

    def test_invalid_finish_consumes_budget_without_success(self):
        # This is a boundary test with scripted proposals, not a claimed LLM run.
        proposals = iter([
            '{"tool":"lookup","arguments":{"dataset":"pilot_a"}}',
            '{"tool":"summarize","arguments":{"dataset":"pilot_a","statistic":"mean"}}',
            '{"tool":"finish","arguments":{"value":999}}',
        ])
        result = lab.run_agent(lambda messages: next(proposals), 'mean of pilot_a', max_steps=3)
        self.assertEqual(result['status'], 'budget_exhausted')
        self.assertIsNone(result['answer'])
        self.assertEqual(result['trace'][-1]['status'], 'error')

    def test_strict_json(self):
        for raw in ['[]', '{"value":NaN}', '```json\n{}\n```']:
            with self.assertRaises(ValueError):
                lab.parse_object(raw)
        self.assertEqual(lab.parse_object('{"n":12}'), {'n': 12})

    def test_zero_vocabulary_query(self):
        self.assertEqual(lab.retrieve('zzzzqqqq'), [])

    def test_coverage_analytic_reference_and_invalid_sample_size(self):
        for n in [12, 60]:
            result = lab.coverage_tool('normal', n, repetitions=20000, seed=501+n)
            exact = 2*t.cdf(1.96, n-1)-1
            self.assertLess(abs(result['estimate']-exact), 5*np.sqrt(exact*(1-exact)/20000))
        for n in [True, 2, 501]:
            with self.assertRaises(ValueError):
                lab.coverage_tool('normal', n)
        with self.assertRaises(ValueError):
            lab.coverage_tool('cauchy', 30)


class CourseContinuity(unittest.TestCase):
    def test_decoder_definitions_identical(self):
        def definitions(chapter):
            source = next((ROOT/'docs/chapters').glob(chapter+'-*.md')).read_text()
            cells = re.findall(r'```\{code-cell\} python\n(.*?)\n```', source, re.S)
            nodes = [node for cell in cells for node in ast.parse(cell).body
                     if isinstance(node, ast.ClassDef) and node.name in ('DecoderBlock', 'TinyDecoder')]
            return [ast.dump(node, include_attributes=False) for node in nodes]
        self.assertEqual(len(definitions('05')), 2)
        self.assertEqual(definitions('05'), definitions('06'))

    def test_notebook_directives_export(self):
        spec = importlib.util.spec_from_file_location('builder', ROOT/'scripts/build.py')
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        sample = '```{tabularcolumns} \\X{1}{2}\n```\n\n:::{dropdown} Solution\n\nUse a held-out sample.\n:::\n'
        exported = builder.notebook_examples(sample)
        self.assertEqual(builder.notebook_examples('```{raw} latex\n\\clearpage\n```\n'), '')
        self.assertNotIn('{tabularcolumns}', exported)
        self.assertNotIn('{dropdown}', exported)
        self.assertIn('<details>', exported)
        self.assertIn('Use a held-out sample.', exported)

    def test_transport_normalization_does_not_repair_content(self):
        import sys
        sys.path.insert(0, str(ROOT/'labs'))
        import capstone_live
        self.assertEqual(capstone_live.parse_transport('```json\n{"n":12}\n```'), {'n': 12})
        for raw in ['prefix ```json\n{}\n```', '```json\n{"n":}\n```', '{"value":Infinity}']:
            with self.assertRaises(ValueError):
                capstone_live.parse_transport(raw)

    def test_record_identity_and_trace_links(self):
        record = json.loads((ROOT/'docs/_static/experiments/llm-run.json').read_text())
        import hashlib
        self.assertEqual(record['model'], lab.MODEL)
        self.assertEqual(record['protocol']['runner_sha256'], hashlib.sha256((ROOT/'labs/archived-v1/llm_lab.py').read_bytes()).hexdigest())
        self.assertEqual(record['protocol']['task_hash'], lab.digest([lab.DOCUMENTS, lab.RAG_TASKS, lab.AGENT_TASKS, lab.CAPSTONE_TASKS]))
        ids = [i for section in ['rag', 'agents', 'capstone'] for row in record[section] for i in row['call_ids']]
        self.assertEqual(sorted(ids), list(range(len(record['calls']))))
        self.assertEqual(len(record['rag']), len(lab.RAG_TASKS)*3)
        self.assertEqual(len(record['agents']), len(lab.AGENT_TASKS)*3)
        demo = json.loads((ROOT/'docs/_static/experiments/capstone-demo.json').read_text())
        self.assertEqual(demo['runner_sha256'], hashlib.sha256((ROOT/'labs/capstone_live.py').read_bytes()).hexdigest())
        self.assertEqual(len(demo['rows']), 3)
        pilot = json.loads((ROOT/'docs/_static/experiments/llm-pilot.json').read_text())
        self.assertEqual(pilot['protocol']['runner_sha256'], hashlib.sha256((ROOT/'labs/archived-pilot/llm_lab.py').read_bytes()).hexdigest())



if __name__ == '__main__':
    unittest.main()
