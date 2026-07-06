



!pip install requests numpy pandas scikit-learn matplotlib flask pyngrok
import requests
import numpy as np
import pandas as pd
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import time
import json
from threading import Thread
import warnings
warnings.filterwarnings('ignore')


# 🔧 CONFIGURE YOUR THINGSPEAK CHANNEL HERE

CHANNEL_ID    = "(Channel ID)"       
READ_API_KEY  = "(API Key)"     

# Field mapping — adjust to match your ThingSpeak channel fields
FIELD_HUMIDITY    = "field4"   # Humidity %
FIELD_TEMP_C      = "field2"   # Temperature °C
FIELD_TEMP_F      = "field3"   # Temperature °F
FIELD_AIR_QUALITY = "field1"   # Air Quality index

MAX_RESULTS  = 8640            # Max readings (8640 × 20s = 48 hrs)
INTERVAL_SEC = 20              # Sampling interval in seconds
PREDICT_STEPS = 180            # 180 × 20s = 3600s = 1 hour ahead
POLY_DEGREE  = 3               # Polynomial degree


print("✅ Config loaded.")
print(f"   Channel  : {CHANNEL_ID}")
print(f"   Max reads: {MAX_RESULTS}")
print(f"   Interval : {INTERVAL_SEC}s")
print(f"   Predict  : {PREDICT_STEPS} steps = 1 hour ahead")
def fetch_thingspeak_data(results=8640):
    """Fetch up to `results` entries from ThingSpeak."""
    url = (
        f"https://api.thingspeak.com/channels/{CHANNEL_ID}/feeds.json"
        f"?api_key={READ_API_KEY}&results={results}"
    )
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        data = r.json()
        feeds = data.get("feeds", [])
        if not feeds:
            print("⚠️  No feeds returned. Check your CHANNEL_ID and READ_API_KEY.")
            return pd.DataFrame()

        rows = []
        for f in feeds:
            try:
                rows.append({
                    "timestamp"  : pd.to_datetime(f["created_at"]),
                    "humidity"   : float(f.get(FIELD_HUMIDITY)    or np.nan),
                    "temp_c"     : float(f.get(FIELD_TEMP_C)      or np.nan),
                    "temp_f"     : float(f.get(FIELD_TEMP_F)      or np.nan),
                    "air_quality": float(f.get(FIELD_AIR_QUALITY) or np.nan),
                })
            except (TypeError, ValueError):
                continue

        df = pd.DataFrame(rows).dropna().reset_index(drop=True)
        df.sort_values("timestamp", inplace=True)
        df["time_idx"] = np.arange(len(df))
        print(f"✅ Fetched {len(df)} valid readings from ThingSpeak.")
        return df

    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return pd.DataFrame()

# Quick test fetch
df = fetch_thingspeak_data(MAX_RESULTS)
if not df.empty:
    print(df.tail(3).to_string(index=False))
  def build_poly_model(degree=POLY_DEGREE):
    """Return a sklearn Polynomial Regression pipeline."""
    return make_pipeline(
        PolynomialFeatures(degree=degree, include_bias=False),
        LinearRegression()
    )

def fit_and_predict(df, column, steps_ahead=PREDICT_STEPS, degree=POLY_DEGREE):
    """
    Fit polynomial regression on `column` and predict `steps_ahead` future steps.
    Returns (fitted_values, predicted_values, future_timestamps).
    """
    X = df["time_idx"].values.reshape(-1, 1)
    y = df[column].values

    model = build_poly_model(degree)
    model.fit(X, y)

    fitted = model.predict(X)

    last_idx = df["time_idx"].iloc[-1]
    future_X = np.arange(last_idx + 1, last_idx + 1 + steps_ahead).reshape(-1, 1)
    predicted = model.predict(future_X)

    last_ts = df["timestamp"].iloc[-1]
    future_ts = [last_ts + timedelta(seconds=INTERVAL_SEC * i) for i in range(1, steps_ahead + 1)]

    return fitted, predicted, future_ts

def predict_all(df):
    """Run predictions for all four sensor channels."""
    results = {}
    for col in ["humidity", "temp_c", "temp_f", "air_quality"]:
        fitted, predicted, future_ts = fit_and_predict(df, col)
        results[col] = {
            "fitted"   : fitted.tolist(),
            "predicted": predicted.tolist(),
            "future_ts": [str(t) for t in future_ts],
        }
        print(f"  ✅ {col:12s} | last={df[col].iloc[-1]:.2f}  "
              f"| 1-hr pred={predicted[-1]:.2f}")
    return results

print("Running predictions …")
predictions = predict_all(df)
def plot_predictions(df, predictions):
    cols   = ["humidity", "temp_c", "temp_f", "air_quality"]
    labels = ["Humidity (%)", "Temperature (°C)", "Temperature (°F)", "Air Quality"]
    colors = ["#3498db", "#e74c3c", "#e67e22", "#2ecc71"]

    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle("ThingSpeak Sensor Data — Polynomial Regression Forecast (1 Hour)",
                 fontsize=15, fontweight="bold")

    for ax, col, label, color in zip(axes.flat, cols, labels, colors):
        pred  = predictions[col]
        ft    = [pd.to_datetime(t) for t in pred["future_ts"]]
        hist  = df["timestamp"].tolist()

        ax.plot(hist, df[col], color=color, alpha=0.4, linewidth=0.8, label="Historical")
        ax.plot(hist, pred["fitted"],   color=color, linewidth=1.5, linestyle="--", label="Fitted")
        ax.plot(ft,   pred["predicted"], color="black", linewidth=2,  linestyle="-",  label="1-hr Forecast")
        ax.axvline(df["timestamp"].iloc[-1], color="red", linestyle=":", linewidth=1.2, label="Now")

        ax.set_title(label, fontweight="bold")
        ax.set_xlabel("Time")
        ax.set_ylabel(label)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right")

    plt.tight_layout()
    plt.savefig("forecast.png", dpi=150, bbox_inches="tight")
    plt.show()
    print("📊 Chart saved as forecast.png")

plot_predictions(df, predictions)
from flask import Flask, jsonify, render_template_string
from pyngrok import ngrok
import threading

app = Flask(__name__)

# Shared state 
state = {"df": df, "predictions": predictions, "last_update": datetime.utcnow().isoformat()}

HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Air Quality Monitor</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; }
  header { background: linear-gradient(135deg,#1e3a5f,#0f2744);
           padding: 18px 30px; display:flex; align-items:center; gap:14px; }
  header h1 { font-size:1.5rem; }
  .badge { background:#22d3ee; color:#0f172a; border-radius:20px;
           padding:3px 10px; font-size:.75rem; font-weight:700; }
  .cards { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr));
           gap:16px; padding:24px; }
  .card  { background:#1e293b; border-radius:12px; padding:18px; text-align:center; }
  .card .val  { font-size:2.2rem; font-weight:700; margin:8px 0; }
  .card .pred { font-size:.85rem; color:#94a3b8; }
  .card .lbl  { font-size:.8rem; color:#64748b; text-transform:uppercase; letter-spacing:.05em; }
  .charts { display:grid; grid-template-columns:repeat(auto-fit,minmax(420px,1fr));
            gap:16px; padding:0 24px 24px; }
  .chart-box { background:#1e293b; border-radius:12px; padding:16px; }
  footer { text-align:center; padding:12px; color:#475569; font-size:.8rem; }
  #status { margin:0 24px; color:#64748b; font-size:.8rem; }
</style>
</head>
<body>
<header>
  <div>
    <h1>🌬️ Air Quality &amp; Climate Monitor</h1>
    <div class="badge">Live + 1-Hour AI Forecast</div>
  </div>
</header>

<div class="cards" id="cards">
  <div class="card"><div class="lbl">Air Quality</div><div class="val" id="v-aq">--</div>
    <div class="pred">Forecast: <span id="p-aq">--</span></div></div>
  <div class="card"><div class="lbl">Temperature °C</div><div class="val" id="v-tc">--</div>
    <div class="pred">Forecast: <span id="p-tc">--</span></div></div>
  <div class="card"><div class="lbl">Temperature °F</div><div class="val" id="v-tf">--</div>
    <div class="pred">Forecast: <span id="p-tf">--</span></div></div>
  <div class="card"><div class="lbl">Humidity</div><div class="val" id="v-hum">--</div>
    <div class="pred">Forecast: <span id="p-hum">--</span></div></div>
</div>
<p id="status">Loading…</p>

<div class="charts">
  <div class="chart-box"><canvas id="ch-aq"></canvas></div>
  <div class="chart-box"><canvas id="ch-tc"></canvas></div>
  <div class="chart-box"><canvas id="ch-tf"></canvas></div>
  <div class="chart-box"><canvas id="ch-hum"></canvas></div>
</div>

<footer>Updates every 20 s &nbsp;|&nbsp; Polynomial Regression (degree 3) &nbsp;|&nbsp; ThingSpeak</footer>

<script>
const CHARTS = {};

function makeChart(id, label, color) {
  const ctx = document.getElementById(id).getContext('2d');
  CHARTS[id] = new Chart(ctx, {
    data: {
      datasets: [
        { type:'line', label:'Historical', borderColor: color+'99', borderWidth:1.2,
          pointRadius:0, data:[] },
        { type:'line', label:'Fitted',     borderColor: color,      borderWidth:1.5,
          borderDash:[4,3], pointRadius:0, data:[] },
        { type:'line', label:'Forecast',   borderColor:'#f8fafc',   borderWidth:2.5,
          pointRadius:0, data:[] },
      ]
    },
    options:{
      responsive:true, animation:false,
      plugins:{ legend:{labels:{color:'#94a3b8',boxWidth:12}},
                title:{display:true,text:label,color:'#e2e8f0',font:{size:13}} },
      scales:{
        x:{ type:'category', ticks:{color:'#64748b',maxTicksLimit:8,maxRotation:30},
            grid:{color:'#1e293b'} },
        y:{ ticks:{color:'#64748b'}, grid:{color:'#334155'} }
      }
    }
  });
}

makeChart('ch-aq',  'Air Quality',       '#22c55e');
makeChart('ch-tc',  'Temperature (°C)',  '#ef4444');
makeChart('ch-tf',  'Temperature (°F)',  '#f97316');
makeChart('ch-hum', 'Humidity (%)',      '#3b82f6');

function fmt(ts){ return ts.slice(11,16); }

function updateChart(id, hist_ts, hist_vals, fit_vals, fut_ts, pred_vals){
  const c = CHARTS[id];
  c.data.labels = [...hist_ts.map(fmt), ...fut_ts.map(fmt)];
  const n = hist_ts.length;
  c.data.datasets[0].data = [...hist_vals, ...Array(fut_ts.length).fill(null)];
  c.data.datasets[1].data = [...fit_vals,  ...Array(fut_ts.length).fill(null)];
  c.data.datasets[2].data = [...Array(n).fill(null), ...pred_vals];
  c.update('none');
}

async function refresh(){
  try {
    const r   = await fetch('/api/data');
    const d   = await r.json();
    const now = new Date().toLocaleTimeString();

    // Cards
    document.getElementById('v-aq' ).textContent = d.latest.air_quality.toFixed(0) + ' AQI';
    document.getElementById('v-tc' ).textContent = d.latest.temp_c.toFixed(1)      + ' °C';
    document.getElementById('v-tf' ).textContent = d.latest.temp_f.toFixed(1)      + ' °F';
    document.getElementById('v-hum').textContent = d.latest.humidity.toFixed(1)    + ' %';
    document.getElementById('p-aq' ).textContent = d.forecast_1hr.air_quality.toFixed(0) + ' AQI';
    document.getElementById('p-tc' ).textContent = d.forecast_1hr.temp_c.toFixed(1)      + ' °C';
    document.getElementById('p-tf' ).textContent = d.forecast_1hr.temp_f.toFixed(1)      + ' °F';
    document.getElementById('p-hum').textContent = d.forecast_1hr.humidity.toFixed(1)    + ' %';

    document.getElementById('status').textContent = 'Last updated: ' + now
      + '  |  Readings: ' + d.total_readings;

    const N  = 200;
    const HT = d.history_ts.slice(-N);
    const FT = d.future_ts;

    updateChart('ch-aq',  HT, d.history.air_quality.slice(-N),
                d.fitted.air_quality.slice(-N), FT, d.predicted.air_quality);
    updateChart('ch-tc',  HT, d.history.temp_c.slice(-N),
                d.fitted.temp_c.slice(-N),  FT, d.predicted.temp_c);
    updateChart('ch-tf',  HT, d.history.temp_f.slice(-N),
                d.fitted.temp_f.slice(-N),  FT, d.predicted.temp_f);
    updateChart('ch-hum', HT, d.history.humidity.slice(-N),
                d.fitted.humidity.slice(-N), FT, d.predicted.humidity);

  } catch(e) { console.error(e); }
}

refresh();
setInterval(refresh, 20000);
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_PAGE)

@app.route("/api/data")
def api_data():
    s = state
    d = s["df"]
    p = s["predictions"]
    resp = {
        "last_update"   : s["last_update"],
        "total_readings": len(d),
        "latest": {
            "air_quality"   : float(d["humidity"].iloc[-1]),
            "temp_c"     : float(d["temp_c"].iloc[-1]),
            "temp_f"     : float(d["temp_f"].iloc[-1]),
            "humidity": float(d["air_quality"].iloc[-1]),
        },
        "forecast_1hr": {
            col: p[col]["predicted"][-1] for col in ["humidity","temp_c","temp_f","air_quality"]
        },
        "history_ts": [str(t) for t in d["timestamp"].tolist()],
        "future_ts" : p["humidity"]["future_ts"],
        "history": {col: d[col].tolist() for col in ["humidity","temp_c","temp_f","air_quality"]},
        "fitted" : {col: p[col]["fitted"]    for col in ["humidity","temp_c","temp_f","air_quality"]},
        "predicted":{col: p[col]["predicted"] for col in ["humidity","temp_c","temp_f","air_quality"]},
    }
    return jsonify(resp)

print("Flask routes registered ✅")
def background_refresh(interval=INTERVAL_SEC):
    """Fetch new data and re-run predictions every `interval` seconds."""
    while True:
        time.sleep(interval)
        try:
            new_df = fetch_thingspeak_data(MAX_RESULTS)
            if not new_df.empty:
                new_preds = predict_all(new_df)
                state["df"]          = new_df
                state["predictions"] = new_preds
                state["last_update"] = datetime.utcnow().isoformat()
                print(f"🔄 Refreshed at {state['last_update']}")
        except Exception as e:
            print(f"⚠️  Refresh error: {e}")

t = Thread(target=background_refresh, daemon=True)
t.start()
print("🔄 Background refresh thread started.")
import os, time, threading
os.system("fuser -k 5000/tcp")
time.sleep(1)

os.system("pip install gradio -q")
import gradio as gr
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ── Chart generator ──────────────────────────────────────────
def make_chart(column, label, color_hist, color_fit, ax):
    s = state
    d = s["df"]
    p = s["predictions"]

    N = 200
    hist_ts  = d["timestamp"].tolist()[-N:]
    hist_val = d[column].tolist()[-N:]
    fit_val  = p[column]["fitted"][-N:]
    fut_ts   = [pd.to_datetime(t) for t in p[column]["future_ts"]]
    pred_val = p[column]["predicted"]

    ax.set_facecolor("#1e293b")
    ax.plot(hist_ts,  hist_val, color=color_hist, alpha=0.45, linewidth=0.9, label="Historical")
    ax.plot(hist_ts,  fit_val,  color=color_fit,  linewidth=1.6, linestyle="--", label="Fitted")
    ax.plot(fut_ts,   pred_val, color="#f8fafc",  linewidth=2.2, label="1-hr Forecast")
    ax.axvline(d["timestamp"].iloc[-1], color="#ef4444", linestyle=":", linewidth=1.3, label="Now")

    ax.set_title(label, color="#e2e8f0", fontsize=12, fontweight="bold", pad=8)
    ax.tick_params(colors="#64748b", labelsize=8)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right", color="#64748b")
    ax.yaxis.label.set_color("#64748b")
    ax.grid(True, alpha=0.15, color="#334155")
    for spine in ax.spines.values():
        spine.set_edgecolor("#334155")
    legend = ax.legend(fontsize=8, facecolor="#0f172a",
                       labelcolor="#94a3b8", edgecolor="#334155")

def make_all_charts():
    fig, axes = plt.subplots(2, 2, figsize=(14, 8))
    fig.patch.set_facecolor("#0f172a")
    fig.suptitle("Air Quality & Climate — Polynomial Regression Forecast",
                 color="#e2e8f0", fontsize=14, fontweight="bold", y=1.01)

    make_chart("air_quality", "🌿 Air Quality (AQI)",   "#22c55e99", "#22c55e", axes[0][0])
    make_chart("temp_c",      "🌡️ Temperature (°C)",    "#ef444499", "#ef4444", axes[0][1])
    make_chart("temp_f",      "🔥 Temperature (°F)",    "#f9731699", "#f97316", axes[1][0])
    make_chart("humidity",    "💧 Humidity (%)",         "#3b82f699", "#3b82f6", axes[1][1])

    plt.tight_layout()
    return fig

# Stats cards HTML 
def make_stats_html():
    s = state
    d = s["df"]
    p = s["predictions"]

    def card(icon, label, value, unit, forecast, funit):
        return f"""
        <div style="background:#1e293b;border-radius:14px;padding:20px 24px;
                    flex:1;min-width:180px;text-align:center;
                    border:1px solid #334155;box-shadow:0 4px 20px #0004">
          <div style="font-size:.75rem;color:#64748b;text-transform:uppercase;
                      letter-spacing:.08em;margin-bottom:6px">{icon} {label}</div>
          <div style="font-size:2.4rem;font-weight:800;color:#e2e8f0;
                      margin:4px 0">{value}<span style="font-size:1rem;
                      color:#94a3b8;margin-left:4px">{unit}</span></div>
          <div style="font-size:.82rem;color:#64748b;margin-top:4px">
            Forecast: <span style="color:#22d3ee;font-weight:600">{forecast} {funit}</span>
          </div>
        </div>"""

    aq_now  = d["air_quality"].iloc[-1];  aq_f  = p["air_quality"]["predicted"][-1]
    tc_now  = d["temp_c"].iloc[-1];       tc_f  = p["temp_c"]["predicted"][-1]
    tf_now  = d["temp_f"].iloc[-1];       tf_f  = p["temp_f"]["predicted"][-1]
    hum_now = d["humidity"].iloc[-1];     hum_f = p["humidity"]["predicted"][-1]
    total   = len(d)
    updated = s["last_update"][:19].replace("T", " ")

    cards = (
        card("🌿", "Air Quality",    f"{aq_now:.0f}",  "AQI", f"{aq_f:.0f}",  "AQI") +
        card("🌡️", "Temperature",   f"{tc_now:.1f}",  "°C",  f"{tc_f:.1f}",  "°C")  +
        card("🔥", "Temp (°F)",      f"{tf_now:.1f}",  "°F",  f"{tf_f:.1f}",  "°F")  +
        card("💧", "Humidity",       f"{hum_now:.1f}", "%",   f"{hum_f:.1f}", "%")
    )

    return f"""
    <div style="font-family:'Segoe UI',sans-serif;background:#0f172a;
                padding:10px;border-radius:16px">
      <div style="display:flex;flex-wrap:wrap;gap:14px;margin-bottom:16px">
        {cards}
      </div>
      <div style="color:#475569;font-size:.78rem;text-align:center;
                  padding:6px;border-top:1px solid #1e293b">
        📡 {total} readings &nbsp;|&nbsp; 🕐 Last updated: {updated} UTC
        &nbsp;|&nbsp; Polynomial Regression (degree 3) &nbsp;|&nbsp; ThingSpeak
      </div>
    </div>"""

#  Gradio UI 
custom_css = """
body, .gradio-container {
    background: #0f172a !important;
    font-family: 'Segoe UI', sans-serif !important;
}
.gr-button-primary {
    background: linear-gradient(135deg,#1e3a5f,#0f2744) !important;
    border: 1px solid #22d3ee !important;
    color: #22d3ee !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
}
footer { display: none !important; }
"""

HEADER_HTML = """
<div style="background:linear-gradient(135deg,#1e3a5f,#0f2744);
            padding:20px 30px;border-radius:14px;margin-bottom:4px;
            display:flex;align-items:center;gap:16px">
  <div style="font-size:2rem">🌬️</div>
  <div>
    <div style="font-size:1.4rem;font-weight:800;color:#e2e8f0">
      Air Quality &amp; Climate Monitor</div>
    <div style="margin-top:4px">
      <span style="background:#22d3ee;color:#0f172a;border-radius:20px;
                   padding:3px 12px;font-size:.75rem;font-weight:700">
        Live + 1-Hour AI Forecast</span>
      <span style="margin-left:10px;color:#64748b;font-size:.8rem">
        Polynomial Regression · ThingSpeak</span>
    </div>
  </div>
</div>"""

def refresh():
    return make_stats_html(), make_all_charts()

with gr.Blocks(css=custom_css, title="🌬️ Air Quality Monitor") as demo:
    gr.HTML(HEADER_HTML)

    stats = gr.HTML()
    chart = gr.Plot(show_label=False)

    # Auto-update every 20 seconds (matches your INTERVAL_SEC)
    demo.load(refresh, outputs=[stats, chart])
    gr.Timer(value=5).tick(refresh, outputs=[stats, chart])

demo.launch(share=True, quiet=True)
