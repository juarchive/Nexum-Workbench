package io.github.nexum.workbench;
import android.test.InstrumentationTestCase;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;
import org.json.*;

public class EngineTest extends InstrumentationTestCase {
    public void testPackagedEngineRunsEveryCatalogExample() throws Exception {
        if (!Python.isStarted()) Python.start(new AndroidPlatform(getInstrumentation().getTargetContext()));
        com.chaquo.python.PyObject engine=Python.getInstance().getModule("nexum.core.portable");
        JSONObject listing=new JSONObject(engine.callAttr("dispatch","{\"operation\":\"catalog\"}").toString());
        assertTrue(listing.getBoolean("ok"));
        JSONArray tools=listing.getJSONArray("payload"); assertEquals(43,tools.length());
        for(int i=0;i<tools.length();i++) {
            JSONObject tool=tools.getJSONObject(i),inputs=new JSONObject(); JSONArray fields=tool.getJSONArray("fields");
            for(int j=0;j<fields.length();j++) { JSONObject f=fields.getJSONObject(j); inputs.put(f.getString("key"),f.getString("default")); }
            JSONObject request=new JSONObject().put("operation","calculate").put("tool",tool.getString("id")).put("inputs",inputs);
            JSONObject result=new JSONObject(engine.callAttr("dispatch",request.toString()).toString());
            assertTrue(tool.getString("id")+": "+result,result.getBoolean("ok"));
        }
    }
    public void testKnownDilutionReference() throws Exception {
        if (!Python.isStarted()) Python.start(new AndroidPlatform(getInstrumentation().getTargetContext()));
        String request="{\"operation\":\"calculate\",\"tool\":\"dilution\",\"inputs\":{\"c1\":\"1\",\"v1_ml\":\"10\",\"c2\":\"0.1\"}}";
        JSONObject response=new JSONObject(Python.getInstance().getModule("nexum.core.portable").callAttr("dispatch",request).toString());
        assertTrue(response.getBoolean("ok"));
        assertEquals("100 mL",response.getJSONObject("payload").getJSONObject("result").getString("value"));
    }
}
