package io.github.nexum.workbench;
import android.content.Context;
import android.graphics.*;
import android.view.View;
import org.json.*;
import java.util.Locale;

/** Plot axes use shared-engine values; no scientific calculation is duplicated. */
public class PlotView extends View {
    private final JSONObject plot;
    private final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);
    private final int[] colors={0xff235e94,0xffad3f5d,0xff237966,0xff7e56a3};
    public PlotView(Context context,JSONObject plot) { super(context); this.plot=plot; setContentDescription(plot.optString("title")+". "+plot.optString("xlabel")+"; "+plot.optString("ylabel")); }
    @Override protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        JSONArray series=plot.optJSONArray("series"); if(series==null) return;
        double xmin=Double.POSITIVE_INFINITY,xmax=Double.NEGATIVE_INFINITY,ymin=xmin,ymax=xmax;
        for(int i=0;i<series.length();i++) {
            JSONArray points=series.optJSONObject(i).optJSONArray("points"); if(points==null) continue;
            for(int j=0;j<points.length();j++) {
                JSONArray p=points.optJSONArray(j); if(p==null) continue;
                double x=p.optDouble(0),y=p.optDouble(1); if(!Double.isFinite(x)||!Double.isFinite(y)) continue;
                xmin=Math.min(xmin,x);xmax=Math.max(xmax,x);ymin=Math.min(ymin,y);ymax=Math.max(ymax,y);
            }
        }
        if(!Double.isFinite(xmin)) return;
        if(xmin==xmax) {xmin-=0.5;xmax+=0.5;} if(ymin==ymax) {ymin-=0.5;ymax+=0.5;}
        float d=getResources().getDisplayMetrics().density,left=60*d,right=getWidth()-12*d,top=22*d,bottom=getHeight()-48*d;
        paint.setTextSize(10*d); paint.setStrokeWidth(d); paint.setStyle(Paint.Style.FILL);
        for(int i=0;i<=4;i++) {
            float y=top+(bottom-top)*i/4; paint.setColor(0xffd4dde3);canvas.drawLine(left,y,right,y,paint);
            paint.setColor(0xff35485b); canvas.drawText(String.format(Locale.ROOT,"%.3g",ymax-(ymax-ymin)*i/4),0,y+3*d,paint);
        }
        canvas.drawLine(left,top,left,bottom,paint);canvas.drawLine(left,bottom,right,bottom,paint);
        canvas.drawText(String.format(Locale.ROOT,"%.3g",xmin),left,bottom+16*d,paint);
        String end=String.format(Locale.ROOT,"%.3g",xmax);canvas.drawText(end,right-paint.measureText(end),bottom+16*d,paint);
        for(int i=0;i<series.length();i++) {
            JSONObject s=series.optJSONObject(i);JSONArray points=s.optJSONArray("points");if(points==null) continue;
            paint.setColor(colors[i%colors.length]); paint.setStrokeWidth(2*d); paint.setStyle(Paint.Style.STROKE);
            Path path=new Path();boolean started=false;
            for(int j=0;j<points.length();j++) {
                JSONArray p=points.optJSONArray(j);if(p==null) continue;
                double x=p.optDouble(0),y=p.optDouble(1); if(!Double.isFinite(x)||!Double.isFinite(y)) {started=false;continue;}
                float px=left+(float)((x-xmin)/(xmax-xmin))*(right-left),py=bottom-(float)((y-ymin)/(ymax-ymin))*(bottom-top);
                if(started) path.lineTo(px,py);else {path.moveTo(px,py);started=true;}
            }
            canvas.drawPath(path,paint);paint.setStyle(Paint.Style.FILL);
            canvas.drawText(s.optString("name"),left,bottom+(30+12*i)*d,paint);
        }
        JSONArray markers=plot.optJSONArray("markers");
        if(markers!=null) for(int i=0;i<markers.length();i++) {
            JSONObject marker=markers.optJSONObject(i);double x=marker.optDouble("x");if(x<xmin||x>xmax||!Double.isFinite(x)) continue;
            float px=left+(float)((x-xmin)/(xmax-xmin))*(right-left);paint.setColor(0xff66546f);paint.setStrokeWidth(d);
            canvas.drawLine(px,top,px,bottom,paint);canvas.drawText(marker.optString("label"),Math.min(px,right-60*d),top-6*d,paint);
        }
    }
}
