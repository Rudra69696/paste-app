from flask import Flask, request, jsonify, render_template_string
import os, uuid, json, secrets

app = Flask(__name__)

# ---------------- FILES ----------------

TOKENS_FILE = "tokens.json"
PASTES_FILE = "pastes.json"
PASTE_DIR = "pastes"

os.makedirs(PASTE_DIR, exist_ok=True)

# ---------------- LOAD / SAVE ----------------

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

TOKENS = load_json(TOKENS_FILE)
PASTES = load_json(PASTES_FILE)

# ---------------- AUTH ----------------

@app.route("/api/auth", methods=["POST"])
def auth():
    token = secrets.token_hex(32)
    TOKENS[token] = True
    save_json(TOKENS_FILE, TOKENS)
    return jsonify({"token": token})

# ---------------- VERIFY ----------------

@app.route("/api/verify", methods=["POST"])
def verify():
    token = request.json.get("token")
    return jsonify({"valid": token in TOKENS})

# ---------------- CREATE PASTE ----------------

@app.route("/api/paste", methods=["POST"])
def create_paste():
    data = request.get_json()

    token = data.get("token")
    content = data.get("content")

    if token not in TOKENS:
        return jsonify({"error": "invalid token"}), 403

    if not content:
        return jsonify({"error": "empty content"}), 400

    paste_id = str(uuid.uuid4())[:8]

    with open(f"{PASTE_DIR}/{paste_id}.txt", "w", encoding="utf-8") as f:
        f.write(content)

    PASTES[paste_id] = True
    save_json(PASTES_FILE, PASTES)

    return jsonify({
        "id": paste_id,
        "raw": f"/raw/{paste_id}",
        "view": f"/view/{paste_id}"
    })

# ---------------- RAW (DARK MODE) ----------------

@app.route("/raw/<paste_id>")
def raw(paste_id):
    file_path = f"{PASTE_DIR}/{paste_id}.txt"

    if not os.path.exists(file_path):
        return "❌ Paste not found", 404

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    return f"""
    <style>
    body {{
        background:#0f0f0f;
        color:#00ff88;
        font-family: monospace;
        padding:20px;
        white-space: pre-wrap;
    }}
    </style>
    {content}
    """

# ---------------- VIEW (PRETTY UI) ----------------

@app.route("/view/<paste_id>")
def view(paste_id):
    file_path = f"{PASTE_DIR}/{paste_id}.txt"

    if not os.path.exists(file_path):
        return "❌ Paste not found", 404

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    return render_template_string("""
    <style>
    body {
        background:#111;
        color:white;
        font-family:sans-serif;
        padding:20px;
    }
    .box {
        background:#1e1e1e;
        padding:15px;
        border-radius:8px;
        white-space:pre-wrap;
        font-family:monospace;
    }
    a {
        color:#00ffcc;
    }
    </style>

    <h2>💀 Paste Viewer</h2>

    <div class="box">{{content}}</div>

    <br>
    <a href="/raw/{{id}}">View Raw</a>
    """, content=content, id=paste_id)

# ---------------- HOME ----------------

@app.route("/")
def home():
    return "💀 Paste API Running"

# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run()
