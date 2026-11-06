from __future__ import annotations
import gi
gi.require_version('Gtk','4.0');gi.require_version('Adw','1')
from gi.repository import Gtk,Adw,Gdk
from nexum.core.registry import GROUPS,TOOLS,TOOL_SCOPE
from nexum.core.calculators import CALCS
from nexum.core.search import relevance
from nexum.core.guidance import guide
from .plot_widget import ScientificPlot

class CalculatorPage(Gtk.Box):
    """Compact GNOME scientific workspace.

    Navigation shows one category at a time; global search temporarily spans every
    category. This replaces the oversized permanently-expanded v5 sidebar.
    """
    def __init__(self,window,history):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL,spacing=0);self.set_hexpand(True);self.set_vexpand(True)
        self.window=window;self.history=history;self.tool=None;self.inputs={};self.tool_rows=[];self._category_idx=0
        self._build_sidebar();self._build_content();self._rebuild_tool_list();self.select_tool(TOOLS[0])

    def _build_sidebar(self):
        self.revealer=Gtk.Revealer();self.revealer.set_reveal_child(True);self.revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_RIGHT)
        side=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=9);side.set_size_request(184,-1);side.set_vexpand(True);side.add_css_class('sidebar')
        side.set_margin_top(10);side.set_margin_bottom(10);side.set_margin_start(10);side.set_margin_end(8)
        self.search=Gtk.SearchEntry();self.search.set_placeholder_text('Buscar ferramenta…');self.search.connect('search-changed',lambda *_:self._rebuild_tool_list());side.append(self.search)
        self.search.connect('activate', self._activate_search)
        self.category=Gtk.DropDown.new_from_strings([g[1] for g in GROUPS]);self.category.set_selected(0);self.category.connect('notify::selected',self._category_changed);side.append(self.category)
        sw=Gtk.ScrolledWindow();sw.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.AUTOMATIC);sw.set_vexpand(True);sw.set_propagate_natural_height(False)
        self.listbox=Gtk.ListBox();self.listbox.set_selection_mode(Gtk.SelectionMode.NONE);self.listbox.add_css_class('navigation-sidebar');sw.set_child(self.listbox);side.append(sw)
        self.revealer.set_child(side);self.append(self.revealer);self.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))

    def _build_content(self):
        self.content=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=12);self.content.set_hexpand(True);self.content.set_vexpand(True)
        self.content.set_margin_top(16);self.content.set_margin_bottom(16);self.content.set_margin_start(18);self.content.set_margin_end(18);self.append(self.content)
        top=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=8)
        toggle=Gtk.Button(icon_name='sidebar-show-symbolic');toggle.add_css_class('flat');toggle.set_tooltip_text('Mostrar/ocultar navegação');toggle.connect('clicked',lambda *_:self.revealer.set_reveal_child(not self.revealer.get_reveal_child()));top.append(toggle)
        h=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=1);self.eyebrow=Gtk.Label(xalign=0);self.eyebrow.add_css_class('caption');self.title=Gtk.Label(xalign=0);self.title.add_css_class('title-1');self.desc=Gtk.Label(xalign=0);self.desc.add_css_class('dim-label');self.desc.set_wrap(True);h.append(self.eyebrow);h.append(self.title);h.append(self.desc);top.append(h);top.append(Gtk.Box(hexpand=True))
        self.validation=Gtk.Label(label='ESCOPO');self.validation.add_css_class('status-pill');top.append(self.validation);self.content.append(top)
        self.paned=Gtk.Paned.new(Gtk.Orientation.HORIZONTAL);self.paned.set_wide_handle(False);self.paned.set_hexpand(True);self.paned.set_vexpand(True);self.paned.set_resize_start_child(True);self.paned.set_resize_end_child(True);self.paned.set_shrink_start_child(True);self.paned.set_shrink_end_child(True);self.content.append(self.paned)

    def _category_changed(self,w,*_):self._category_idx=w.get_selected();self.search.set_text('');self._rebuild_tool_list()
    def _clear_list(self):
        while (c:=self.listbox.get_first_child()) is not None:self.listbox.remove(c)
        self.tool_rows=[]
    def _rebuild_tool_list(self):
        self._clear_list();q=self.search.get_text().strip();gid=GROUPS[self._category_idx][0]
        items=[]
        if q:
            ranked = []
            groups = dict(GROUPS)
            for tool in TOOLS:
                rank = relevance(q, tool[0], tool[2], tool[3], groups[tool[1]])
                if rank is not None:
                    ranked.append((rank, tool))
            items = [tool for _, tool in sorted(ranked, key=lambda item: item[0])]
        else:
            items = [tool for tool in TOOLS if tool[1] == gid]
        for t in items:
            row=Adw.ActionRow(title=t[2],subtitle=dict(GROUPS).get(t[1],''));row.set_subtitle_lines(1);row.set_activatable(True);row.connect('activated',lambda _,tt=t:self.select_tool(tt));self.listbox.append(row);self.tool_rows.append((row,t))
        if not items:
            row=Adw.ActionRow(title='Nenhuma ferramenta encontrada',subtitle='Tente outro termo ou categoria.');row.set_sensitive(False);self.listbox.append(row)

    def _activate_search(self, entry):
        if entry.get_text().strip():
            self._rebuild_tool_list()
            if self.tool_rows:
                self.tool_rows[0][0].emit('activated')

    def focus_search(self):
        self.revealer.set_reveal_child(True)
        self.search.grab_focus()

    def select_tool(self,tool):
        self.tool=tool;tid,gid,title,desc,fields=tool;self.eyebrow.set_text(dict(GROUPS).get(gid,'').upper());self.title.set_text(title);self.desc.set_text(desc);self.inputs={};scope,scope_note=TOOL_SCOPE.get(tid,('MODELO','Consulte a auditoria científica.'));self.validation.set_text(scope);self.validation.set_tooltip_text(scope_note)
        if not self.search.get_text().strip():
            idx=next((i for i,g in enumerate(GROUPS) if g[0]==gid),0)
            if idx!=self._category_idx:self._category_idx=idx;self.category.set_selected(idx);self._rebuild_tool_list()
        form_sw=Gtk.ScrolledWindow();form_sw.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.AUTOMATIC);form_sw.set_hexpand(True);form_sw.set_vexpand(True);form_sw.set_min_content_width(300);form_sw.set_propagate_natural_height(False)
        form=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=14);form.set_margin_top(4);form.set_margin_end(16);form.set_margin_bottom(16)
        guidance = guide(tid)
        help_box = Adw.PreferencesGroup(title='Como usar esta ferramenta')
        for key in ('purpose', 'instructions', 'interpretation', 'example_notice'):
            label = Gtk.Label(label=guidance[key], xalign=0, wrap=True)
            label.set_max_width_chars(52)
            help_box.add(label)
        form.append(help_box)
        group=Adw.PreferencesGroup(title='Entradas',description='Edite os dados do problema. Unidades e hipóteses aparecem no desenvolvimento.')
        for spec in fields:
            if spec['kind']=='select':
                row=Adw.ComboRow(title=spec['label']);row.set_model(Gtk.StringList.new(spec['options']));row.set_selected(spec['options'].index(spec['default']) if spec['default'] in spec['options'] else 0)
                row.connect('notify::selected', self._invalidate_result)
            else:
                row=Adw.EntryRow(title=spec['label']);row.set_text(spec['default'])
                row.connect('changed', self._invalidate_result)
            group.add(row);self.inputs[spec['key']]=(row,spec)
        form.append(group)
        buttons=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=8);calc=Gtk.Button(label='Calcular',icon_name='media-playback-start-symbolic');calc.add_css_class('suggested-action');calc.connect('clicked',self._calculate);clear=Gtk.Button(label='Limpar');clear.connect('clicked',self._clear);buttons.append(calc);buttons.append(clear);form.append(buttons);form_sw.set_child(form)
        result_sw=Gtk.ScrolledWindow();result_sw.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.AUTOMATIC);result_sw.set_hexpand(True);result_sw.set_vexpand(True);result_sw.set_min_content_width(390);result_sw.set_propagate_natural_height(False)
        result=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=12);result.set_margin_start(16);result.set_margin_top(4);result.set_margin_bottom(16)
        rg=Adw.PreferencesGroup(title='Resultado');self.value=Gtk.Label(label='—',xalign=0);self.value.add_css_class('numeric-result');self.value.set_selectable(True);self.value.set_wrap(True);rg.add(self.value)
        scope_label = Gtk.Label(label=scope_note, xalign=0, wrap=True)
        scope_label.add_css_class('dim-label')
        rg.add(scope_label)
        result.append(rg)
        dg=Adw.PreferencesGroup(title='Desenvolvimento, unidades e hipóteses');self.details=Gtk.Label(label='Calcule para ver o desenvolvimento.',xalign=0);self.details.set_selectable(True);self.details.set_wrap(True);self.details.set_wrap_mode(2);self.details.add_css_class('monospace');dg.add(self.details);result.append(dg)
        self.plots=[ScientificPlot() for _ in range(3)]
        for chart in self.plots:chart.set_visible(False);result.append(chart)
        self.plot=self.plots[0]
        self.copy = Gtk.Button(label='Copiar resultado', icon_name='edit-copy-symbolic')
        self.copy.set_halign(Gtk.Align.START)
        self.copy.set_sensitive(False)
        self.copy.connect('clicked', self._copy)
        result.append(self.copy)
        self.save_to_project = Gtk.Button(label='Registrar no projeto', icon_name='document-save-symbolic')
        self.save_to_project.set_halign(Gtk.Align.START)
        self.save_to_project.set_sensitive(False)
        self.save_to_project.connect('clicked', self._record_result)
        result.append(self.save_to_project)
        result_sw.set_child(result)
        self.paned.set_start_child(form_sw);self.paned.set_end_child(result_sw);self.paned.set_position(470)

    def _getdata(self):
        out={}
        for key,(row,spec) in self.inputs.items():
            if isinstance(row,Adw.ComboRow):
                item=row.get_selected_item();out[key]=item.get_string() if item else ''
            else:out[key]=row.get_text().strip()
        return out
    def _invalidate_result(self, *_):
        if self.copy.get_sensitive():
            self._reset_result('As entradas mudaram. Calcule novamente.')

    def _reset_result(self, message):
        self.value.set_text('—')
        self.details.set_text(message)
        self.copy.set_sensitive(False)
        self.save_to_project.set_sensitive(False)
        self._set_plots({})

    def _calculate(self, *_):
        data = self._getdata()
        try:
            result = CALCS[self.tool[0]](data)
            self._set_plots(result.data or {})
        except Exception as exc:
            self._reset_result(f'Não foi possível calcular. {exc}')
            return

        self.value.set_text(result.value)
        self.details.set_text(result.details)
        self.copy.set_sensitive(True)
        self.save_to_project.set_sensitive(True)
        try:
            self.history.add(self.tool[0], data, {'value': result.value, 'data': result.data or {}})
        except Exception:
            self.window.toast('Resultado calculado. Não foi possível salvar no histórico.')
        else:
            self.window.toast('Cálculo concluído')

    def _record_result(self, *_):
        if not self.save_to_project.get_sensitive():
            return
        from nexum.identity import VERSION

        tool_id, _, title, _, _ = self.tool
        scope, note = TOOL_SCOPE.get(tool_id, ('MODELO', 'Consulte a auditoria científica.'))
        payload = {
            'calculator': tool_id,
            'version': VERSION,
            'value': self.value.get_text(),
            'method': self.details.get_text(),
            'scope': scope,
            'scope_note': note,
            'plots': [chart.data for chart in self.plots if chart.data],
        }
        self.window.open_laboratory()
        laboratory = self.window.lab
        if laboratory.busy:
            self.window.toast('Aguarde a operação do laboratório para registrar o cálculo.')
            return
        parameters = {
            self.inputs[key][1]['label']: value for key, value in self._getdata().items()
        }
        try:
            laboratory.result(title, payload, parameters=parameters)
        except ValueError as exc:
            laboratory.toast(f'Não foi possível registrar o cálculo: {exc}')
            return
        laboratory.toast('Cálculo registrado no projeto atual.')

    def _set_plots(self,data):
        graphs=data.get("plots") or [data.get("plot")]
        for i,chart in enumerate(self.plots):chart.set_plot(graphs[i] if i<len(graphs) else None)

    def _clear(self,*_):
        for row,_ in self.inputs.values():
            if isinstance(row,Adw.EntryRow):row.set_text('')
    def _copy(self,*_):
        Gdk.Display.get_default().get_clipboard().set((self.value.get_text()+'\n\n'+self.details.get_text()).strip());self.window.toast('Resultado copiado')

