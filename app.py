import json
import requests
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# ===== KONFIGURASI =====
GROQ_API_KEY = "INSERT_YOUR_API_KEY" 
mode = "AUTO"
target_tanaman = "Umum" 
relay = {"pump":"OFF", "lamp":"OFF", "fan":"OFF"}
last_sensor = {"suhu":0, "hum":0, "soil":0, "lux":0}

def fallback_ai(data):
    res = {"pump":"OFF", "lamp":"OFF", "fan":"OFF"}
    if data.get('suhu', 0) > 31: res["fan"] = "ON"
    if data.get('lux', 0) < 100: res["lamp"] = "ON"
    if data.get('soil', 0) < 25: res["pump"] = "ON"
    return res

def groq_ai(data):
    prompt = (f"Plant:{target_tanaman}. Data:T:{data['suhu']},H:{data['hum']},S:{data['soil']},L:{data['lux']}. "
              f"Output JSON ONLY: {{\"pump\":\"ON/OFF\",\"lamp\":\"ON/OFF\",\"fan\":\"ON/OFF\"}}")
    
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": f"Expert Greenhouse AI for {target_tanaman}. Strict JSON output."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0,
        "max_tokens": 60,
        "response_format": {"type": "json_object"}
    }

    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=5)
        response_data = r.json()
        if 'choices' in response_data:
            content = response_data['choices'][0]['message']['content']
            clean_content = content.replace(" ", "").replace("\n", "").replace("\r", "")
            return json.loads(clean_content)
        return fallback_ai(data)
    except:
        return fallback_ai(data)

@app.route("/")
def home():
    html = """
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <title>AI Greenhouse Pro</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/css/bootstrap.min.css">
        <style>
            body { background: #f0f2f5; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding-top: 20px; }
            .card { border-radius: 20px; border: none; box-shadow: 0 10px 20px rgba(0,0,0,0.05); transition: 0.3s; }
            .sensor-card { border-bottom: 5px solid #198754; }
            .sensor-val { font-size: 2rem; font-weight: 800; color: #198754; }
            .status-badge { font-size: 1.1rem; padding: 10px 20px; border-radius: 50px; font-weight: bold; }
            .btn-action { border-radius: 12px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; }
        </style>
    </head>
    <body>
        <div class="container" style="max-width: 700px;">
            <div class="text-center mb-4">
                <h1 class="display-6 fw-bold text-dark">🌿 AI Greenhouse</h1>
            </div>

            <div class="row g-3 mb-4 text-center">
                <div class="col-md-6">
                    <div class="card p-3 h-100">
                        <small class="text-muted fw-bold">TARGET TANAMAN</small>
                        <h4 class="text-success mb-3">{{ target_tanaman }}</h4>
                        <form action="/set_tanaman" method="POST" class="d-flex gap-2">
                            <input type="text" name="tanaman" class="form-control form-control-sm shadow-none" placeholder="Ganti tanaman...">
                            <button type="submit" class="btn btn-success btn-sm">UPDATE</button>
                        </form>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card p-3 h-100">
                        <small class="text-muted fw-bold">MODE SISTEM</small>
                        <h4 class="{% if mode == 'AUTO' %}text-primary{% else %}text-danger{% endif %} mb-3">{{ mode }}</h4>
                        <div class="btn-group w-100">
                            <a href="/set_mode/AUTO" class="btn btn-outline-primary btn-sm">AUTO</a>
                            <a href="/set_mode/MANUAL" class="btn btn-outline-danger btn-sm">MANUAL</a>
                        </div>
                    </div>
                </div>
            </div>

            <div class="row g-3 mb-4 text-center">
                <div class="col-6 col-md-3">
                    <div class="card p-3 sensor-card h-100">
                        <small>🌡️ SUHU</small>
                        <div class="sensor-val">{{ suhu }}°C</div>
                    </div>
                </div>
                <div class="col-6 col-md-3">
                    <div class="card p-3 sensor-card h-100">
                        <small>💧 HUM</small>
                        <div class="sensor-val">{{ hum }}%</div>
                    </div>
                </div>
                <div class="col-6 col-md-3">
                    <div class="card p-3 sensor-card h-100">
                        <small>🪴 SOIL</small>
                        <div class="sensor-val">{{ soil }}%</div>
                    </div>
                </div>
                <div class="col-6 col-md-3">
                    <div class="card p-3 sensor-card h-100">
                        <small>☀️ LUX</small>
                        <div class="sensor-val">{{ lux }}</div>
                    </div>
                </div>
            </div>

            <div class="card p-4 mb-5">
                <h5 class="fw-bold mb-4 text-center text-secondary">PANEL KONTROL ALAT</h5>
                <div class="row text-center mb-4">
                    <div class="col-4">
                        <div class="small text-muted mb-1">POMPA</div>
                        <span class="badge {% if pump == 'ON' %}bg-success{% else %}bg-secondary{% endif %} status-badge">{{ pump }}</span>
                    </div>
                    <div class="col-4">
                        <div class="small text-muted mb-1">LAMPU</div>
                        <span class="badge {% if lamp == 'ON' %}bg-warning text-dark{% else %}bg-secondary{% endif %} status-badge">{{ lamp }}</span>
                    </div>
                    <div class="col-4">
                        <div class="small text-muted mb-1">KIPAS</div>
                        <span class="badge {% if fan == 'ON' %}bg-info text-dark{% else %}bg-secondary{% endif %} status-badge">{{ fan }}</span>
                    </div>
                </div>

                {% if mode == "MANUAL" %}
                <div class="d-grid gap-3">
                    <div class="d-flex justify-content-between align-items-center bg-light p-2 rounded-3">
                        <span class="fw-bold px-2">POMPA</span>
                        <div>
                            <a href="/control/pump/ON" class="btn btn-success btn-sm btn-action px-3">ON</a>
                            <a href="/control/pump/OFF" class="btn btn-danger btn-sm btn-action px-3">OFF</a>
                        </div>
                    </div>
                    <div class="d-flex justify-content-between align-items-center bg-light p-2 rounded-3">
                        <span class="fw-bold px-2">LAMPU</span>
                        <div>
                            <a href="/control/lamp/ON" class="btn btn-success btn-sm btn-action px-3">ON</a>
                            <a href="/control/lamp/OFF" class="btn btn-danger btn-sm btn-action px-3">OFF</a>
                        </div>
                    </div>
                    <div class="d-flex justify-content-between align-items-center bg-light p-2 rounded-3">
                        <span class="fw-bold px-2">KIPAS</span>
                        <div>
                            <a href="/control/fan/ON" class="btn btn-success btn-sm btn-action px-3">ON</a>
                            <a href="/control/fan/OFF" class="btn btn-danger btn-sm btn-action px-3">OFF</a>
                        </div>
                    </div>
                </div>
                {% else %}
                <div class="alert alert-info py-2 text-center mb-0" style="border-radius: 12px;">
                    <small>Sistem dalam kendali penuh AI <b>{{ target_tanaman }}</b></small>
                </div>
                {% endif %}
            </div>
        </div>

        <script>
            setInterval(function(){ 
                if(document.activeElement.tagName !== 'INPUT') location.reload(); 
            }, 5000);
        </script>
    </body>
    </html>
    """
    return render_template_string(html, mode=mode, target_tanaman=target_tanaman, **relay, **last_sensor)

@app.route("/set_tanaman", methods=["POST"])
def set_tanaman():
    global target_tanaman
    target_tanaman = request.form.get("tanaman", "Umum").strip()
    return f"<script>window.location.href='/';</script>"

@app.route("/set_mode/<new_mode>")
def set_mode(new_mode):
    global mode; mode = new_mode.upper(); return f"<script>window.location.href='/';</script>"

@app.route("/control/<device>/<state>")
def control_device(device, state):
    global relay, mode
    if mode == "MANUAL": relay[device] = state.upper()
    return f"<script>window.location.href='/';</script>"

@app.route("/decision", methods=["POST"])
def decision():
    global last_sensor, relay
    try:
        data = request.json
        if not data: return jsonify(relay)
        last_sensor = data
        if mode == "AUTO":
            decision_json = groq_ai(data)
            for k in relay: relay[k] = decision_json.get(k, "OFF").upper()
            print(f"[AUTO - {target_tanaman}] Sensor:{data} -> AI:{relay}")
        return jsonify(relay)
    except:
        return jsonify(relay)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)