"""Exercise the calculator workflow with a native GTK display."""
import unittest
from unittest.mock import Mock

try:
    import gi

    gi.require_version('Gtk', '4.0')
    gi.require_version('Adw', '1')
    from gi.repository import Adw, Gdk, Gtk

    AVAILABLE = bool(Gtk.init_check() and Gdk.Display.get_default())
except (ImportError, ValueError):
    AVAILABLE = False


@unittest.skipUnless(AVAILABLE, 'GTK4/libadwaita e display não estão disponíveis')
class GtkCalculatorTests(unittest.TestCase):
    def setUp(self):
        Adw.init()
        from nexum.ui.calculators_page import CalculatorPage

        self.page = CalculatorPage(Mock(), Mock())

    def test_enter_opens_best_search_result(self):
        self.page.search.set_text('titulação')
        self.page.search.emit('activate')
        self.assertEqual(self.page.tool[0], 'titration')

    def test_edit_invalidates_copy_and_failed_recalculation_leaves_no_value(self):
        page = self.page
        page._calculate()
        self.assertTrue(page.copy.get_sensitive())
        page.inputs['formula'][0].set_text('')
        self.assertEqual(page.value.get_text(), '—')
        self.assertFalse(page.copy.get_sensitive())
        self.assertFalse(page.save_to_project.get_sensitive())
        page._calculate()
        self.assertIn('Não foi possível calcular', page.details.get_text())
        page.history.add.assert_called_once()

    def test_weak_titration_survives_session_project_and_html_export(self):
        import math
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from unittest.mock import patch

        from nexum.core.data_analysis import read_session, write_session
        from nexum.lab.project import read_project, write_project
        from nexum.lab.reports import report
        from nexum.ui.main_window import MainWindow
        from nexum.ui.session_actions import restore, snapshot

        app = Adw.Application()
        app.register(None)
        with TemporaryDirectory() as folder:
            directory = Path(folder)
            with patch('nexum.ui.main_window.data_dir', return_value=directory):
                window = MainWindow(app)
            try:
                page = window.calc
                page.search.set_text('titulação')
                page.search.emit('activate')
                page.inputs['mode'][0].set_selected(1)
                page.inputs['pka'][0].set_text(str(-math.log10(1.8e-5)))
                page._calculate()
                self.assertAlmostEqual(float(page.value.get_text()), 8.72, delta=0.01)

                with patch('nexum.ui.laboratory.data_dir', return_value=directory):
                    page.save_to_project.emit('clicked')
                project_path = directory / 'titulacao.nexum7'
                write_project(project_path, window.lab.project.data)
                project = read_project(project_path)
                entry = project['results'][-1]
                self.assertEqual(entry['parameters']['V base adicionado (mL)'], '25')
                self.assertEqual(entry['payload']['value'], page.value.get_text())
                self.assertEqual(entry['payload']['plots'][0]['xlabel'], 'V base / mL')
                report_path = directory / 'titulacao.html'
                report(project, report_path)
                html = report_path.read_text(encoding='utf-8')
                for expected in (page.value.get_text(), '25 °C', 'V base / mL', 'equivalência', 'ácido fraco'):
                    self.assertIn(expected, html)

                path = directory / 'titulacao.nexum'
                write_session(path, snapshot(window))
                saved = read_session(path)
                page.inputs['base_ml'][0].set_text('10')
                self.assertEqual(page.value.get_text(), '—')
                restore(window, saved)

                self.assertEqual(page.inputs['mode'][0].get_selected_item().get_string(), 'ácido fraco')
                self.assertEqual(page.inputs['base_ml'][0].get_text(), '25')
                self.assertEqual(page.value.get_text(), saved['calculator']['value'])
                self.assertIn('25 °C', page.details.get_text())
                self.assertEqual(page.plots[0].data['xlabel'], 'V base / mL')
                self.assertEqual(page.plots[0].data, saved['calculator']['plots'][0])
            finally:
                window.close_laboratory()
                window.destroy()
