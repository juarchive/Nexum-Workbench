package io.github.nexum.workbench;

import android.test.ActivityInstrumentationTestCase2;
import android.graphics.Bitmap;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import java.io.File;
import java.io.FileOutputStream;

public class WorkspaceTest extends ActivityInstrumentationTestCase2<MainActivity> {
    public WorkspaceTest() { super(MainActivity.class); }
    private View find(View root,String text) {
        if (root instanceof TextView && text.contentEquals(((TextView)root).getText())) return root;
        if(root instanceof ViewGroup) for(int i=0;i<((ViewGroup)root).getChildCount();i++) {
            View found=find(((ViewGroup)root).getChildAt(i),text); if(found!=null) return found;
        }
        return null;
    }
    private View await(String text) throws Exception {
        MainActivity activity=getActivity(); final View[] result={null};
        for(int i=0;i<100;i++) {
            getInstrumentation().runOnMainSync(()->result[0]=find(activity.getWindow().getDecorView(),text));
            if(result[0]!=null) return result[0]; Thread.sleep(100);
        }
        fail("Elemento não apareceu: "+text); return null;
    }
    private void screenshot(String name) throws Exception {
        getInstrumentation().waitForIdleSync();
        Bitmap image=getInstrumentation().getUiAutomation().takeScreenshot(); assertNotNull(image);
        File path=new File(getActivity().getExternalFilesDir(null),name+".png");
        try(FileOutputStream stream=new FileOutputStream(path)) { image.compress(Bitmap.CompressFormat.PNG,100,stream); }
    }
    public void testCalculateInvalidateAndOpenNotebook() throws Exception {
        View tool=await("Massa molar"); screenshot("home");
        getInstrumentation().runOnMainSync(()->tool.performClick());
        View calculate=await("Calcular");
        getInstrumentation().runOnMainSync(()->calculate.performClick());
        Button save=(Button)await("Registrar no caderno");
        for(int i=0;i<100;i++) {
            final boolean[] enabled={false};getInstrumentation().runOnMainSync(()->enabled[0]=save.isEnabled());
            if(enabled[0]) break;Thread.sleep(100);
        }
        getInstrumentation().runOnMainSync(()->assertTrue(save.isEnabled())); screenshot("calculation");
        getInstrumentation().runOnMainSync(()->save.performClick());
        View input=await("CuSO4·5H2O");assertTrue(input instanceof EditText);
        getInstrumentation().runOnMainSync(()->((EditText)input).setText("NaCl"));
        getInstrumentation().runOnMainSync(()->assertFalse(save.isEnabled()));
        View back=await("Voltar às ferramentas");getInstrumentation().runOnMainSync(()->back.performClick());
        View notebook=await("Caderno de resultados");getInstrumentation().runOnMainSync(()->notebook.performClick());
        await("Ver entradas e hipóteses");screenshot("notebook");
    }
}
