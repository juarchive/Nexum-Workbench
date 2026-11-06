import unittest
from nexum.core.chemistry import parse_formula
from nexum.core.calculators import CALCS
from nexum.core.registry import TOOLS

class InputIntegrityTests(unittest.TestCase):
    def test_formula_does_not_silently_discard_characters_or_charge(self):
        for formula in ['H2O!', 'Na+', 'SO4-2', 'H0O', '(OH]', 'Mg()2', '0H2O', '.H2O', 'H2O.', 'CuSO4..5H2O']:
            with self.subTest(formula=formula), self.assertRaises(ValueError): parse_formula(formula)
    def test_nested_groups_and_hydrates_preserve_atom_counts(self):
        self.assertEqual(parse_formula('K4[Fe(CN)6]'), {'K':4,'Fe':1,'C':6,'N':6})
        self.assertEqual(parse_formula('CuSO4·5H2O'),{'Cu':1,'S':1,'O':9,'H':10})
    def test_nonfinite_values_in_previous_gaps_are_rejected(self):
        for tool,key in [('constants','delta_n'),('speciation','pka'),('speciation','ph'),('cell','e_cathode'),('cell','e_anode')]:
            fields=next(t[4] for t in TOOLS if t[0]==tool)
            for value in ['nan','inf','-inf']:
                data={f['key']:f['default'] for f in fields};data[key]=value
                with self.subTest(tool=tool,key=key,value=value),self.assertRaises(ValueError): CALCS[tool](data)
