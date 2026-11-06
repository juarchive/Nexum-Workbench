"""Acceptance cases with independent references and explicit output tolerances."""

from decimal import Decimal, localcontext
import math
import unittest

from nexum.core.calculators import CALCS


class ScientificReferenceCases(unittest.TestCase):
    def test_strong_base_matches_ideal_charge_balance_across_dilutions(self):
        # Ideal monobasic solution at 25 °C: [OH-] = C + [H+], [H+][OH-] = Kw.
        # Solve for hydroxide in Decimal, then derive pH independently.
        for concentration in ('1e-9', '1e-7', '1e-3', '0.1', '1.0'):
            with self.subTest(concentration=concentration), localcontext() as ctx:
                ctx.prec = 40
                c = Decimal(concentration)
                kw = Decimal('1e-14')
                oh = (c + (c * c + 4 * kw).sqrt()) / 2
                expected = float(14 + oh.log10())
                result = CALCS['ph']({'kind': 'base forte', 'concentration': concentration})
                self.assertAlmostEqual(float(result.value), expected, delta=1e-8)

    def test_ideal_gas_all_unknowns_against_one_si_reference_state(self):
        # CODATA: R = 8.31446261815324 J/(mol K).
        # Construct the reference state in SI before converting to atm and L.
        pressure_pa = 2.5 * 8.31446261815324 * 315 / 0.018
        inputs = {'p_atm': str(pressure_pa / 101325), 'v_l': '18', 'n_mol': '2.5', 't_k': '315'}
        units = {'p_atm': 'atm', 'v_l': 'L', 'n_mol': 'mol', 't_k': 'K'}
        for unknown, expected in inputs.items():
            with self.subTest(unknown=unknown):
                result = CALCS['ideal'](dict(inputs, **{unknown: ''}))
                number, unit = result.value.split()
                self.assertEqual(unit, units[unknown])
                self.assertAlmostEqual(float(number), float(expected), delta=1e-8)

    def test_ideal_gas_rejects_nonfinite_inputs_and_unrepresentable_results(self):
        inputs = {'p_atm': '', 'v_l': '18', 'n_mol': '2.5', 't_k': '315'}
        for field in ('v_l', 'n_mol', 't_k'):
            for invalid in ('nan', 'inf', '-inf'):
                with self.subTest(field=field, invalid=invalid), self.assertRaisesRegex(ValueError, 'finito'):
                    CALCS['ideal'](dict(inputs, **{field: invalid}))
        with self.assertRaisesRegex(ValueError, 'finito'):
            CALCS['ideal'](dict(inputs, n_mol='1e308'))

    def test_strong_titration_before_at_and_after_equivalence(self):
        inputs = {'mode': 'ácido forte', 'acid_m': '0.12', 'acid_ml': '20',
                  'base_m': '0.08', 'base_ml': '', 'pka': '4.76'}
        # The net analytical proton excess changes sign at 30 mL.
        # Compute the positive root with high precision so cancellation cannot
        # mask discrepancies in the alkaline regime.
        for added_ml in ('10', '30', '45'):
            with self.subTest(added_ml=added_ml), localcontext() as ctx:
                ctx.prec = 40
                volume = Decimal(added_ml)
                excess = (Decimal('0.12') * 20 - Decimal('0.08') * volume) / (20 + volume)
                h = (excess + (excess * excess + Decimal('4e-14')).sqrt()) / 2
                expected_ph = float(-h.log10())
                result = CALCS['titration'](dict(inputs, base_ml=added_ml))
                self.assertAlmostEqual(float(result.value), expected_ph, delta=1e-8)
                plot = result.data['plot']
                self.assertAlmostEqual(plot['markers'][0]['x'], 30, delta=1e-10)
                curve_volume, curve_ph = min(
                    plot['series'][0]['points'], key=lambda point: abs(point[0] - float(volume))
                )
                self.assertAlmostEqual(curve_volume, float(volume), delta=1e-10)
                self.assertAlmostEqual(curve_ph, expected_ph, delta=1e-8)

    def test_acetic_acid_titration_against_polynomial_and_openstax(self):
        # OpenStax Chemistry 2e, §14.7, table 14.2 (theoretical, rounded pH).
        textbook = {'0': 2.87, '10': 4.57, '25': 8.72, '25.1': 10.30, '50': 12.52}
        inputs = {'mode': 'ácido fraco', 'acid_m': '0.1', 'acid_ml': '25',
                  'base_m': '0.1', 'base_ml': '', 'pka': str(-math.log10(1.8e-5))}
        for added_ml, textbook_ph in textbook.items():
            with self.subTest(added_ml=added_ml), localcontext() as ctx:
                ctx.prec = 50
                volume = Decimal(added_ml)
                total_acid = Decimal('2.5') / (25 + volume)
                sodium = Decimal('0.1') * volume / (25 + volume)
                ka, kw = Decimal('1.8e-5'), Decimal('1e-14')
                # Multiply the charge balance by h(Ka+h) to obtain a cubic.
                lo, hi = Decimal(0), Decimal(1)
                for _ in range(160):
                    h = (lo + hi) / 2
                    residual = ((h + ka + sodium) * h + ka * (sodium - total_acid) - kw) * h - kw * ka
                    if residual > 0:
                        hi = h
                    else:
                        lo = h
                reference_ph = float(-((lo + hi) / 2).log10())

                result = CALCS['titration'](dict(inputs, base_ml=added_ml))
                self.assertAlmostEqual(float(result.value), reference_ph, delta=1e-8)
                self.assertAlmostEqual(float(result.value), textbook_ph, delta=0.01)
                self.assertAlmostEqual(result.data['equivalence_ml'], 25, delta=1e-10)
                self.assertAlmostEqual(result.data['a_minus_m'] + result.data['ha_m'], float(total_acid), delta=1e-12)
                charge = result.data['h_m'] + float(sodium) - result.data['a_minus_m'] - result.data['oh_m']
                self.assertAlmostEqual(charge, 0, delta=1e-12)
                if added_ml == '25':
                    curve_volume, curve_ph = min(
                        result.data['plot']['series'][0]['points'], key=lambda point: abs(point[0] - 25)
                    )
                    self.assertAlmostEqual(curve_volume, 25, delta=1e-10)
                    self.assertAlmostEqual(curve_ph, reference_ph, delta=1e-8)

    def test_beer_lambert_absorbance_transmittance_and_curve_agree(self):
        # IUPAC Gold Book, B00626: A = εcl and T = 10^(-A).
        result = CALCS['beer']({'epsilon': '12000', 'path_cm': '2', 'concentration': '0.00002'})
        self.assertAlmostEqual(float(result.value), 0.48, delta=1e-10)
        self.assertAlmostEqual(result.data['transmittance'], 10 ** -0.48, delta=1e-12)
        plot = result.data['plot']
        self.assertEqual(plot['markers'][0]['x'], 2e-5)
        for concentration, absorbance in plot['series'][0]['points']:
            self.assertTrue(math.isclose(absorbance, 24000 * concentration, abs_tol=1e-12))
