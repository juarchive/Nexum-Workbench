from __future__ import annotations

from importlib.resources import files

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gdk, GLib

from nexum.catalog import VERSION


class HomePage(Gtk.Overlay):
    def __init__(self, window):
        super().__init__()
        self.add_css_class('workbench-home')
        artwork = files('nexum').joinpath('assets/skyline-dusk.svg').read_bytes()
        texture = Gdk.Texture.new_from_bytes(GLib.Bytes.new(artwork))
        landscape = Gtk.Picture(paintable=texture, content_fit=Gtk.ContentFit.COVER)
        landscape.set_can_shrink(True)
        landscape.set_can_target(False)
        self.set_child(landscape)

        scroller = Gtk.ScrolledWindow()
        scroller.add_css_class('landscape-veil')
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.add_overlay(scroller)
        self.set_measure_overlay(scroller, True)

        clamp = Adw.Clamp(maximum_size=1000, tightening_threshold=720)
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        root.set_margin_top(32)
        root.set_margin_bottom(32)
        root.set_margin_start(24)
        root.set_margin_end(24)

        version = Gtk.Label(label=f'NEXUM · {VERSION}', xalign=0)
        version.add_css_class('caption-heading')
        root.append(version)
        title = Gtk.Label(label='Bancada científica', xalign=0)
        title.add_css_class('large-title')
        root.append(title)
        subtitle = Gtk.Label(label='Escolha o que você quer fazer na bancada.', xalign=0, wrap=True)
        subtitle.add_css_class('dim-label')
        root.append(subtitle)

        grid = Gtk.Grid(column_spacing=12, row_spacing=12, column_homogeneous=True)
        actions = [
            ('Buscar uma calculadora', 'Encontre ferramentas por nome ou assunto.',
             window.open_calculator_search),
            ('Trabalhar em um projeto', 'Organize dados, métodos e relatórios no laboratório.',
             window.open_laboratory),
            ('Analisar dados', 'Use as ferramentas de análise e visualização.',
             lambda: window.stack.set_visible_child_name('analysis')),
            ('Explorar estruturas 3D', 'Busque ou importe moléculas e macromoléculas.',
             lambda: window.stack.set_visible_child_name('structures')),
            ('Executar um experimento', 'Acompanhe a evolução de um protocolo simulado.',
             lambda: window.stack.set_visible_child_name('experiments')),
            ('Revisar o histórico', 'Consulte as entradas e saídas de cálculos anteriores.',
             lambda: window.stack.set_visible_child_name('history')),
        ]
        for index, (label, description, action) in enumerate(actions):
            button = Gtk.Button()
            button.add_css_class('home-card')
            content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            heading = Gtk.Label(label=label, xalign=0, wrap=True)
            heading.add_css_class('heading')
            caption = Gtk.Label(label=description, xalign=0, wrap=True)
            caption.add_css_class('dim-label')
            content.append(heading)
            content.append(caption)
            button.set_child(content)
            button.connect('clicked', lambda _, activate=action: activate())
            grid.attach(button, index % 2, index // 2, 1, 1)
        root.append(grid)

        interpretation = Gtk.Label(
            label='Ao interpretar um cálculo, confira as unidades, as hipóteses e o domínio do modelo.',
            xalign=0,
            wrap=True,
        )
        interpretation.add_css_class('landscape-caption')
        interpretation.set_halign(Gtk.Align.START)
        root.append(interpretation)
        clamp.set_child(root)
        scroller.set_child(clamp)
