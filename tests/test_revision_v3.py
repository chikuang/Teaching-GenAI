"""Regressions for snapshot evidence, intent fidelity, independent checks and paths."""
from pathlib import Path
from copy import deepcopy
from types import SimpleNamespace
from contextlib import nullcontext, redirect_stdout
import ast
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
import numpy as np
import nbformat
from labs.llm_lab import LocalLM
from labs.guided_systems import execute_confirmed, simulation_workflow
from labs.live_tasks import BASE_SPEC, CAPSTONE_CASES
from labs.evaluation import load_evaluation, make_row, paired_scores, validate_rows
from labs.exercise_checks import check
from labs.assignment_solutions import SOLUTIONS

ROOT=Path(__file__).resolve().parents[1]


class EvidenceAndIntent(unittest.TestCase):
    def test_snapshot_precedes_generation_and_survives_nested_mutation(self):
        messages=[{'role':'user','content':'original'}]
        class Batch(dict):
            @property
            def input_ids(self):return self['input_ids']
        class Tokenizer:
            eos_token_id=9
            def apply_chat_template(self, value, **kwargs):return json.dumps(value)
            def __call__(self, text, **kwargs):return Batch(input_ids=np.array([[1,2]]))
            def decode(self, ids, **kwargs):return 'real fake-model output'
        class Model:
            generation_config=SimpleNamespace(eos_token_id=[9])
            def generate(self, **kwargs):
                # Simulates a caller changing its shared state during generation.
                messages[0]['content']='changed during generation'
                return np.array([[1,2,9]])
        lm=LocalLM.__new__(LocalLM)
        lm.calls=[];lm.tokenizer=Tokenizer();lm.model=Model()
        lm.torch=SimpleNamespace(inference_mode=nullcontext)
        lm(messages)
        messages.append({'role':'assistant','content':'later answer'})
        self.assertEqual(lm.calls[0]['messages'],[{'role':'user','content':'original'}])
        self.assertEqual(json.loads(lm.calls[0]['serialized_prompt']),lm.calls[0]['messages'])
        self.assertEqual(lm.calls[0]['stop_reason'],'eos')

    def test_current_agent_inputs_form_prefixes_without_future_turns(self):
        record=json.loads((ROOT/'docs/_static/experiments/agent-bridge.json').read_text())
        calls=record['calls']
        self.assertEqual([len(c['messages']) for c in calls],[2,4,6,8,10])
        for previous,current in zip(calls,calls[1:]):
            self.assertEqual(current['messages'][:-2],previous['messages'])
            self.assertEqual(current['messages'][-2],{'role':'assistant','content':previous['raw']})
        old=json.loads((ROOT/'docs/_static/experiments/agent-bridge-v2.json').read_text())
        self.assertEqual([len(c['messages']) for c in old['calls']],[11]*5)

    def test_confirmation_and_all_settings_gate_computation(self):
        self.assertEqual(execute_confirmed(BASE_SPEC,None)['status'],'needs_confirmation')
        self.assertEqual(execute_confirmed(dict(BASE_SPEC,n=25),BASE_SPEC)['status'],'intent_mismatch')
        for _,question,card in CAPSTONE_CASES[2:]:
            # Even a model returning the supported default cannot override this card.
            row=simulation_workflow(lambda messages,**kwargs:json.dumps(BASE_SPEC),question,card)
            self.assertEqual(row['status'],'abstained')
            self.assertNotIn('tool_result',row)
        unsupported_question=CAPSTONE_CASES[3][1]
        row=simulation_workflow(lambda messages,**kwargs:json.dumps(BASE_SPEC),unsupported_question)
        self.assertEqual(row['status'],'needs_confirmation')
        self.assertNotIn('tool_result',row)
        row=execute_confirmed(BASE_SPEC,BASE_SPEC)
        self.assertEqual(row['status'],'completed')
        self.assertEqual(row['tool_result']['repetitions'],500)
        self.assertEqual(row['tool_result']['confidence'],.95)

    def test_invalid_settings_are_never_computed(self):
        for invalid in [dict(BASE_SPEC,n=True),dict(BASE_SPEC,confidence=float('nan')),
                        dict(BASE_SPEC,repetitions=True),dict(BASE_SPEC,extra='x'),
                        {'family':'normal','n':18}]:
            row=simulation_workflow(lambda messages,**kwargs:json.dumps(invalid),'fixture',BASE_SPEC)
            self.assertEqual(row['status'],'invalid')
            self.assertNotIn('tool_result',row)


class IndependentAcceptance(unittest.TestCase):
    def test_correct_solutions_and_fourteen_wrong_controls(self):
        for chapter,function in enumerate(SOLUTIONS,1):check(chapter,function)
        def uniform(scores,values):
            w=np.tril(np.ones_like(scores));w/=w.sum(1,keepdims=True)
            return w,w@values
        wrong=[lambda *a:0.,lambda X,y,b:(0.,np.zeros_like(b)),lambda *a:1.,uniform,
               lambda *a:True,lambda g,a:g['stop_reason']=='end_token',lambda *a:1.,
               lambda x,*a:np.zeros_like(x),lambda di,do,r:di*do,lambda *a:True,
               lambda a,b:np.logical_xor(a,b),lambda *a:True,
               lambda m:m[(3,True)]-m[(1,False)],
               lambda p,c:c is not None and p.get('family')==c.get('family') and p.get('n')==c.get('n')]
        for chapter,function in enumerate(wrong,1):
            with self.subTest(chapter=chapter),self.assertRaises(AssertionError):check(chapter,function)

    def test_original_review_mutants_fail_actual_chapter_cells(self):
        mutations={
            '01':('frequency_error','return 0.0'),
            '02':('logistic_loss_gradient','return 0.0, np.zeros_like(beta)'),
            '04':('causal_average','weights = np.tril(np.ones_like(scores))\nweights /= weights.sum(1, keepdims=True)\nreturn weights, weights @ values'),
            '08':('mixture_score','return np.zeros((len(x), 1))')}
        for chapter,(name,body) in mutations.items():
            source=next((ROOT/'docs/chapters').glob(chapter+'-*.md')).read_text()
            cell=next(c for c in re.findall(r'```\{code-cell\} python\n(.*?)\n```',source,re.S) if 'def '+name+'(' in c)
            tree=ast.parse(cell)
            fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
            fn.body=ast.parse(body).body
            namespace={'np':np,'alpha_bar':np.linspace(.99,.4,80)}
            with self.subTest(chapter=chapter),redirect_stdout(io.StringIO()),self.assertRaises(AssertionError):
                exec(compile(ast.fix_missing_locations(tree),'<mutated worked example>','exec'),namespace)

    def test_student_notebooks_run_with_completed_functions_in_fresh_processes(self):
        solution_nodes={n.name:n for n in ast.parse((ROOT/'labs/assignment_solutions.py').read_text()).body if isinstance(n,ast.FunctionDef)}
        env=dict(os.environ);env.pop('GENAI_COURSE_ROOT',None)
        for number,path in enumerate(sorted((ROOT/'labs/assignments').glob('*.ipynb')),1):
            book=nbformat.read(path,4)
            code=[]
            for cell in book.cells:
                if cell.cell_type!='code':continue
                source=cell.source
                if 'raise NotImplementedError' in source:
                    name=ast.parse(source).body[0].name
                    source=ast.unparse(solution_nodes[name])
                code.append(source)
            result=subprocess.run([sys.executable,'-I','-c','\n'.join(code)],cwd=ROOT/'labs/assignments',env=env,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,path.name+'\n'+result.stderr)
            self.assertIn(f'Chapter {number}:',result.stdout)
            public=nbformat.read(ROOT/'docs/_static/assignments'/path.name,4)
            self.assertEqual(book,public)

    def test_bootstrap_from_root_subfolder_and_external_folder(self):
        source=(ROOT/'labs/bootstrap.txt').read_text()+"\nfrom labs.contracts import parse_object\nassert parse_object('{}') == {}\n"
        env=dict(os.environ);env.pop('GENAI_COURSE_ROOT',None)
        for cwd in [ROOT,ROOT/'labs/notebooks',ROOT/'docs/chapters']:
            result=subprocess.run([sys.executable,'-I','-c',source],cwd=cwd,env=env,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
        with tempfile.TemporaryDirectory(prefix='genai-outside-course-') as external:
            result=subprocess.run([sys.executable,'-I','-c',source],cwd=external,env=env,capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
            env['GENAI_COURSE_ROOT']=str(ROOT)
            result=subprocess.run([sys.executable,'-I','-c',source],cwd=external,env=env,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)


class CommonEvaluation(unittest.TestCase):
    def test_semantic_fixtures_separate_valid_json_from_supported_answers(self):
        from labs.contracts import assess_response
        from labs.evaluation import action_contract
        rows=json.loads((ROOT/'docs/_static/evaluation/semantic-fixtures.json').read_text())['rows']
        validate_rows(rows)
        for row in rows:
            assessment=assess_response(row['raw_response'], [{'id':'source-1'}])
            self.assertTrue(assessment['contract_valid'])
        self.assertEqual([r['task_success'] for r in rows],[True,False,False,False,None])
        self.assertFalse(action_contract([{'raw':'malformed'}]))
        self.assertFalse(action_contract([{'action':{'tool':'finish','arguments':{'value':True}}}]))
        self.assertTrue(action_contract([{'action':{'tool':'lookup','arguments':{'dataset':'unknown'}}}]))

    def test_provenance_and_pairing(self):
        rows=load_evaluation(ROOT)
        self.assertEqual(len(rows),14)
        self.assertEqual(paired_scores([row for row in reversed(rows) if row['task_family']=='rag'],'extractive','llm')[0]['difference'],0.)
        for row in rows:
            path=ROOT/'docs/_static/experiments'/row['source_record']
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),row['source_sha256'])
            record=json.loads(path.read_text())
            self.assertEqual(len(row['call_ids']),row['llm_calls'])
            if row['call_ids']:
                self.assertEqual(row['raw_response'],[record['calls'][i]['raw'] for i in row['call_ids']])
        self.assertFalse(rows[0]['complete'])
        self.assertFalse(rows[0]['task_success'])

    def test_no_silent_drop_duplicate_or_null_pass(self):
        a=make_row('task','rag','a',task_success=False)
        b=make_row('task','rag','b',task_success=False)
        for rows in [[a],[a,a,b],[a,dict(b,task_success=None)]]:
            with self.assertRaises(ValueError):paired_scores(rows,'a','b')
        with self.assertRaises(ValueError):validate_rows([dict(a,task_success=True)])
        with self.assertRaises(ValueError):paired_scores([a,dict(b,data_kind='synthetic')],'a','b')


if __name__=='__main__':unittest.main()
