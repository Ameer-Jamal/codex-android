package __APP_ID__;

import android.app.Activity;
import android.os.Bundle;
import android.graphics.Color;
import android.view.Gravity;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

public class MainActivity extends Activity {
    private int count;
    private TextView counter;
    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        count = saved == null ? 0 : saved.getInt("count", 0);
        getWindow().setStatusBarColor(Color.rgb(11, 18, 32));
        getWindow().setNavigationBarColor(Color.rgb(11, 18, 32));
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setGravity(Gravity.CENTER);
        int padding = (int)(28 * getResources().getDisplayMetrics().density);
        layout.setPadding(padding, padding, padding, padding);
        layout.setBackgroundColor(Color.rgb(11, 18, 32));
        TextView title = new TextView(this);
        title.setText("Hello from Codex\non Android");
        title.setTextSize(32);
        title.setTextColor(Color.WHITE);
        title.setGravity(Gravity.CENTER);
        layout.addView(title);
        TextView subtitle = new TextView(this);
        subtitle.setText("Compiled in Termux on this phone");
        subtitle.setTextSize(16);
        subtitle.setTextColor(Color.rgb(148, 163, 184));
        subtitle.setGravity(Gravity.CENTER);
        subtitle.setPadding(0, padding, 0, padding);
        layout.addView(subtitle);
        counter = new TextView(this);
        counter.setTextSize(24);
        counter.setTextColor(Color.rgb(94, 234, 212));
        counter.setGravity(Gravity.CENTER);
        layout.addView(counter);
        updateCounter();
        Button button = new Button(this);
        button.setText("Tap me");
        button.setAllCaps(false);
        button.setTextSize(20);
        button.setOnClickListener(view -> { count++; updateCounter(); });
        LinearLayout.LayoutParams buttonParams = new LinearLayout.LayoutParams(-1, -2);
        buttonParams.topMargin = padding;
        layout.addView(button, buttonParams);
        setContentView(layout);
        android.util.Log.i("CodexHelloWorld", "activity_ready");
    }
    private void updateCounter() {
        counter.setText("Taps: " + count);
        android.util.Log.i("CodexHelloWorld", "counter=" + count);
    }
    @Override protected void onSaveInstanceState(Bundle state) {
        state.putInt("count", count);
        super.onSaveInstanceState(state);
    }
}
