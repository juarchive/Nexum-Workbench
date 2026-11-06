import json
import unittest
from nexum.core.portable import catalog, calculate, dispatch
from nexum.core.registry import TOOLS
from nexum.core.calculators import CALCS

class PortableTests(unittest.TestCase):
    def test_every_tool_crosses_json_boundary_without_changing_results(self):
        self.assertEqual({t['id'] for t in catalog()}, set(CALCS))
        for tid, _, _, _, fields in TOOLS:
            with self.subTest(tool=tid):
                inputs={f['key']:f['default'] for f in fields}
                response=json.loads(dispatch(json.dumps({'operation':'calculate','tool':tid,'inputs':inputs})))
                self.assertTrue(response['ok'], response)
                record=response['payload']
                expected=CALCS[tid](inputs)
                self.assertEqual(record['result']['value'],expected.value)
                self.assertEqual(record['result']['details'],expected.details)
                self.assertEqual(record['inputs'],inputs)
                self.assertEqual(record['schema'],1)
    def test_unknown_or_malformed_requests(self):
        for request in ['{','[]','null', 'x'*100001, '{"operation":"delete"}']:
            self.assertFalse(json.loads(dispatch(request))['ok'])
    def test_reject_missing_extra_and_select_values(self):
        for inputs in [{}, {'formula':'H2O','extra':'x'}, {'formula':42}]:
            with self.assertRaises(ValueError): calculate('molar',inputs)
        t=next(t for t in TOOLS if t[0]=='ph'); inputs={f['key']:f['default'] for f in t[4]}
        inputs['kind']='nonsense'
        with self.assertRaises(ValueError): calculate('ph',inputs)
    def test_reference_result_and_traceability(self):
        record=calculate('dilution',{'c1':'1','v1_ml':'10','c2':'0.1'})
        self.assertTrue(record['result']['value'].startswith('100 '))
        self.assertIn('mol/L', record['input_labels']['c1'])
        self.assertTrue(record['created_utc'].endswith('+00:00'))
    def test_guidance_covers_every_tool(self):
        for tool in catalog():
            for key in ['purpose','instructions','interpretation','limits','example_notice']:
                self.assertTrue(tool['guide'][key],tool['id'])
