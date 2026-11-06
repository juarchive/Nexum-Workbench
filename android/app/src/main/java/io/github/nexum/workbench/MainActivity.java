package io.github.nexum.workbench;

import android.app.Activity;
import android.os.Bundle;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.View;
import android.widget.*;
import com.chaquo.python.Python;
import org.json.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.*;

/** Offline calculator workspace. Scientific models remain in the shared Python core. */
public class MainActivity extends Activity {
    private final ExecutorService worker = Executors.newSingleThreadExecutor();
    private LinearLayout page, results;
    private JSONArray catalog;
    private JSONObject current, lastResult;
    private final Map<String, View> inputs = new LinkedHashMap<>();
    private TextView status;
    private Button save, export;
    private long revision = 0;
    private String pendingExport;
    private static final int EXPORT = 41;
    private String restoredTool;
    private JSONObject restoredInputs;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        if (state != null) {
            restoredTool = state.getString("tool");
            pendingExport = state.getString("pendingExport");
            try { restoredInputs = new JSONObject(state.getString("inputs", "{}")); } catch (JSONException ignored) { }
        }
        layout("Nexum", "Preparando as ferramentas…");
        worker.execute(() -> {
            try {
                JSONObject response = request(new JSONObject().put("operation", "catalog"));
                catalog = response.getJSONArray("payload");
                runOnUiThread(() -> {
                    if (isDestroyed()) return;
                    if (restoredTool != null) {
                        for (int i=0; i<catalog.length(); i++) {
                            JSONObject tool = catalog.optJSONObject(i);
                            if (tool.optString("id").equals(restoredTool)) { showTool(tool); return; }
                        }
                    }
                    home();
                });
            } catch (Exception e) { runOnUiThread(() -> status.setText("Não foi possível iniciar: " + e.getMessage())); }
        });
    }
    private JSONObject request(JSONObject data) throws JSONException {
        return new JSONObject(Python.getInstance().getModule("nexum.core.portable")
                .callAttr("dispatch", data.toString()).toString());
    }
    private int dp(int value) { return Math.round(value * getResources().getDisplayMetrics().density); }
    private TextView text(String value, int size) {
        TextView v = new TextView(this); v.setText(value); v.setTextSize(size); v.setTextColor(Color.rgb(25,42,61));
        v.setPadding(0, dp(6), 0, dp(6)); return v;
    }
    private void layout(String title, String subtitle) {
        revision++; inputs.clear(); lastResult = null;
        ScrollView scroll = new ScrollView(this); scroll.setFillViewport(true);
        scroll.setBackground(new GradientDrawable(GradientDrawable.Orientation.TL_BR,
                new int[]{0xffdcecf4,0xffeee7f2,0xffe2eced}));
        page = new LinearLayout(this); page.setOrientation(LinearLayout.VERTICAL); page.setPadding(dp(20),dp(16),dp(20),dp(32));
        scroll.addView(page); setContentView(scroll);
        scroll.setOnApplyWindowInsetsListener((v, insets) -> {
            v.setPadding(insets.getSystemWindowInsetLeft(), insets.getSystemWindowInsetTop(),
                         insets.getSystemWindowInsetRight(), insets.getSystemWindowInsetBottom());
            return insets;
        });
        page.addView(text(title,28)); status = text(subtitle,15); page.addView(status);
    }
    private Button button(String label, LinearLayout parent, Runnable action) {
        Button b = new Button(this); b.setText(label); b.setAllCaps(false); b.setMinHeight(dp(48));
        parent.addView(b); b.setOnClickListener(v -> action.run()); return b;
    }
    private LinearLayout card(LinearLayout parent) {
        LinearLayout box = new LinearLayout(this); box.setOrientation(LinearLayout.VERTICAL); box.setPadding(dp(16),dp(12),dp(16),dp(12));
        GradientDrawable bg = new GradientDrawable(); bg.setColor(0xdcffffff); bg.setCornerRadius(dp(20)); bg.setStroke(dp(1),Color.WHITE); box.setBackground(bg);
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1,-2); params.setMargins(0,dp(10),0,dp(10)); parent.addView(box,params); return box;
    }
    private void home() {
        current=null; layout("Nexum", "Bancada de química • Davi P. Souza\nPrévia Android: calculadoras offline. Laboratório e estruturas 3D ainda não disponíveis nesta versão.");
        button("Caderno de resultados", page, this::history);
        EditText search = new EditText(this); search.setHint("O que você precisa calcular?"); search.setSingleLine(true); page.addView(search);
        LinearLayout list = new LinearLayout(this); list.setOrientation(LinearLayout.VERTICAL); page.addView(list);
        Runnable render = () -> {
            list.removeAllViews(); String q = search.getText().toString().toLowerCase(Locale.ROOT);
            for (int i=0; i<catalog.length(); i++) {
                JSONObject t=catalog.optJSONObject(i);
                String purpose=t.optJSONObject("guide").optString("purpose");
                if (!(t.optString("title")+purpose+t.optString("group")).toLowerCase(Locale.ROOT).contains(q)) continue;
                LinearLayout box=card(list); box.addView(text(t.optString("group"),12));
                button(t.optString("title"),box,()->showTool(t)); box.addView(text(purpose,15));
            }
            if (list.getChildCount()==0) list.addView(text("Nenhuma ferramenta encontrada. Tente outro termo.",16));
        };
        search.addTextChangedListener(watcher(render)); render.run();
    }
    private TextWatcher watcher(Runnable action) {
        return new TextWatcher() {
            public void beforeTextChanged(CharSequence s,int start,int count,int after) { }
            public void onTextChanged(CharSequence s,int start,int before,int count) { action.run(); }
            public void afterTextChanged(Editable e) { }
        };
    }
    private void invalidate() {
        revision++; lastResult=null;
        if (results!=null) results.removeAllViews();
        if (save!=null) save.setEnabled(false);
        if (export!=null) export.setEnabled(false);
    }
    private void showTool(JSONObject tool) {
        current=tool; results=null; save=null; export=null;
        layout(tool.optString("title"),tool.optJSONObject("guide").optString("purpose"));
        button("Voltar às ferramentas",page,this::home);
        JSONObject guide=tool.optJSONObject("guide"); LinearLayout help=card(page);
        for (String key:new String[]{"instructions","interpretation","limits","example_notice"}) help.addView(text(guide.optString(key),15));
        LinearLayout form=card(page); JSONArray fields=tool.optJSONArray("fields");
        for (int i=0; i<fields.length(); i++) {
            JSONObject f=fields.optJSONObject(i); String key=f.optString("key");
            String initial=restoredInputs!=null ? restoredInputs.optString(key,f.optString("default")) : f.optString("default");
            TextView label=text(f.optString("label"),16); form.addView(label);
            View input;
            if (f.optString("kind").equals("select")) {
                Spinner spinner=new Spinner(this); ArrayList<String> choices=new ArrayList<>(); JSONArray options=f.optJSONArray("options");
                for(int j=0;j<options.length();j++) choices.add(options.optString(j));
                ArrayAdapter<String> adapter=new ArrayAdapter<>(this,android.R.layout.simple_spinner_item,choices);
                adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item); spinner.setAdapter(adapter);
                spinner.setSelection(Math.max(0,choices.indexOf(initial)));
                spinner.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
                    public void onItemSelected(AdapterView<?> p,View v,int position,long id) { invalidate(); }
                    public void onNothingSelected(AdapterView<?> p) { invalidate(); }
                }); input=spinner;
            } else {
                EditText edit=new EditText(this); edit.setSingleLine(true); edit.setText(initial);
                edit.addTextChangedListener(watcher(this::invalidate)); input=edit;
            }
            input.setId(View.generateViewId()); label.setLabelFor(input.getId()); input.setContentDescription(f.optString("label"));
            form.addView(input); inputs.put(key,input);
        }
        restoredInputs=null; restoredTool=null;
        button("Calcular",form,this::calculate);
        results=card(page); save=button("Registrar no caderno",page,this::saveResult); save.setEnabled(false);
        export=button("Exportar registro JSON",page,this::exportResult); export.setEnabled(false);
    }
    private JSONObject collect() throws JSONException {
        JSONObject data=new JSONObject();
        for (Map.Entry<String,View> e:inputs.entrySet()) {
            View v=e.getValue(); String value=v instanceof EditText ? ((EditText)v).getText().toString().trim() : String.valueOf(((Spinner)v).getSelectedItem());
            data.put(e.getKey(),value);
        }
        return data;
    }
    private void calculate() {
        invalidate(); final long token=revision;
        try {
            JSONObject payload=new JSONObject().put("operation","calculate").put("tool",current.getString("id")).put("inputs",collect());
            results.addView(text("Calculando…",16));
            worker.execute(() -> {
                try {
                    JSONObject response=request(payload);
                    runOnUiThread(() -> {
                        if (isDestroyed() || revision!=token) return;
                        results.removeAllViews();
                        if (!response.optBoolean("ok")) { results.addView(text(response.optString("error"),16)); return; }
                        lastResult=response.optJSONObject("payload"); renderResult(lastResult,results); save.setEnabled(true); export.setEnabled(true);
                    });
                } catch(Exception e) { runOnUiThread(() -> { if(!isDestroyed() && revision==token) {results.removeAllViews(); results.addView(text("Falha no cálculo: "+e.getMessage(),16));} }); }
            });
        } catch(JSONException e) { results.addView(text("Entradas inválidas.",16)); }
    }
    private void renderResult(JSONObject record,LinearLayout target) {
        JSONObject result=record.optJSONObject("result");
        TextView value=text(result.optString("value"),26); value.setTextIsSelectable(true); target.addView(value);
        TextView details=text(result.optString("details"),15); details.setTextIsSelectable(true); target.addView(details);
        JSONObject data=result.optJSONObject("data");
        if (data!=null) {
            JSONArray plots=data.optJSONArray("plots");
            if (plots==null) { plots=new JSONArray(); if(data.optJSONObject("plot")!=null) plots.put(data.optJSONObject("plot")); }
            for(int i=0;i<plots.length();i++) {
                JSONObject plot=plots.optJSONObject(i); if(plot==null) continue;
                target.addView(text(plot.optString("title"),18));
                target.addView(new PlotView(this,plot),new LinearLayout.LayoutParams(-1,dp(240)));
                target.addView(text("Eixo horizontal: "+plot.optString("xlabel")+" • Vertical: "+plot.optString("ylabel"),13));
            }
        }
        target.addView(text("Motor "+record.optString("version")+" • "+record.optString("created_utc"),12));
    }
    private File notebook() { return new File(getFilesDir(),"notebook.jsonl"); }
    private void saveResult() {
        if(lastResult==null) return;
        try(FileOutputStream stream=new FileOutputStream(notebook(),true)) {
            stream.write((lastResult.toString()+"\n").getBytes(StandardCharsets.UTF_8));
            Toast.makeText(this,"Resultado registrado no caderno",Toast.LENGTH_SHORT).show(); save.setEnabled(false);
        } catch(IOException e) { Toast.makeText(this,"Não foi possível salvar",Toast.LENGTH_LONG).show(); }
    }
    private void history() {
        current=null; layout("Caderno", "Registros locais com entradas, modelo, versão e resultado."); button("Voltar",page,this::home);
        try(BufferedReader reader=new BufferedReader(new InputStreamReader(new FileInputStream(notebook()),StandardCharsets.UTF_8))) {
            String line;
            while((line=reader.readLine())!=null) {
                JSONObject record=new JSONObject(line); LinearLayout box=card(page); box.addView(text(record.optString("title"),20));
                renderResult(record,box);
                button("Ver entradas e hipóteses",box,()->new android.app.AlertDialog.Builder(this).setTitle("Registro reproduzível").setMessage(record.toString()).setPositiveButton("Fechar",null).show());
                button("Exportar registro JSON",box,()->beginExport(record));
            }
        } catch(FileNotFoundException e) { page.addView(text("Seu caderno está vazio. Calcule e registre um resultado.",16)); }
        catch(Exception e) { page.addView(text("Não foi possível ler todos os registros; os dados foram preservados.",16)); }
    }
    private void exportResult() { if(lastResult!=null) beginExport(lastResult); }
    private void beginExport(JSONObject record) {
        pendingExport=record.toString();
        Intent intent=new Intent(Intent.ACTION_CREATE_DOCUMENT).setType("application/json").addCategory(Intent.CATEGORY_OPENABLE).putExtra(Intent.EXTRA_TITLE,"Nexum-resultado.json");
        startActivityForResult(intent,EXPORT);
    }
    @Override protected void onActivityResult(int request,int result,Intent data) {
        super.onActivityResult(request,result,data);
        if(request==EXPORT && result==RESULT_OK && data!=null && data.getData()!=null && pendingExport!=null) {
            try(OutputStream stream=getContentResolver().openOutputStream(data.getData())) {
                if(stream==null) throw new IOException();
                stream.write(pendingExport.getBytes(StandardCharsets.UTF_8));
                Toast.makeText(this,"Registro exportado",Toast.LENGTH_SHORT).show();
            } catch(IOException e) { Toast.makeText(this,"Falha ao exportar",Toast.LENGTH_LONG).show(); }
        }
        pendingExport=null;
    }
    @Override protected void onSaveInstanceState(Bundle state) {
        super.onSaveInstanceState(state);
        if(current!=null) { state.putString("tool",current.optString("id")); try {state.putString("inputs",collect().toString());} catch(JSONException ignored) { } }
        state.putString("pendingExport",pendingExport);
    }
    @Override public void onBackPressed() { if(current!=null) home(); else super.onBackPressed(); }
    @Override protected void onDestroy() { revision++; worker.shutdownNow(); super.onDestroy(); }
}
