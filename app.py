from flask import Flask, request, jsonify, render_template_string
import os, uuid, json, secrets

app = Flask(__name__)

DATA_FILE = "data.json"
PASTE_DIR = "pastes"

os.makedirs(PASTE_DIR, exist_ok=True)

# ---------------- LOAD ----------------

def load():
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "tokens": {}}
    with open(DATA_FILE) as f:
        return json.load(f)

def save(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

DATA = load()

# ---------------- WEB SIGNUP ----------------

@app.route("/", methods=["GET"])
def home():
    return """
    <style>
    body { background:#111; color:white; font-family:sans-serif; }
    input { padding:10px; margin:5px; background:#222; color:white; border:none; }
    button { padding:10px; background:#333; color:white; }
    </style>

    <h2>📝 Sign Up</h2>
    <form action="/websignup" method="POST">
        <input name="user"><br>
        <input name="pass" type="password"><br>
        <button>Create</button>
    </form>
    """

@app.route("/websignup", methods=["POST"])
def websignup():
    user = request.form.get("user")
    password = request.form.get("pass")

    if user in DATA["users"]:
        return "User exists"

    token = secrets.token_hex(32)

    DATA["users"][user] = password
    DATA["tokens"][token] = user
    save(DATA)

    return f"""
    ✅ Account created<br>
    Token:<br><b>{token}</b>
    """

# ---------------- API SIGNUP (ROBLOX) ----------------

@app.route("/api/signup", methods=["POST"])
def api_signup():
    data = request.get_json()

    user = data.get("user")
    password = data.get("pass")

    if not user or not password:
        return jsonify({"error": "missing fields"}), 400

    if user in DATA["users"]:
        return jsonify({"error": "user exists"}), 400

    token = secrets.token_hex(32)

    DATA["users"][user] = password
    DATA["tokens"][token] = user
    save(DATA)

    return jsonify({
        "token": token
    })

# ---------------- VERIFY ----------------

@app.route("/api/verify", methods=["POST"])
def verify():
    token = request.json.get("token")
    return jsonify({"valid": token in DATA["tokens"]})

# ---------------- PASTE ----------------

@app.route("/api/paste", methods=["POST"])
def paste():
    data = request.get_json()

    token = data.get("token")
    content = data.get("content")

    if token not in DATA["tokens"]:
        return jsonify({"error": "invalid token"}), 403

    paste_id = str(uuid.uuid4())[:8]

    with open(f"{PASTE_DIR}/{paste_id}.txt", "w") as f:
        f.write(content)

    return jsonify({
        "id": paste_id,
        "raw": f"/raw/{paste_id}",
        "view": f"/view/{paste_id}"
    })

# ---------------- RAW ----------------

@app.route("/raw/<id>")
def raw(id):
    try:
        with open(f"{PASTE_DIR}/{id}.txt") as f:
            content = f.read()
    except:
        return "Not found"

    return f"""
    <style>
    body {{ background:#0f0f0f; color:#00ff88; font-family:monospace; padding:20px; }}
    </style>
    {content}
    """

# ---------------- VIEW ----------------

@app.route("/view/<id>")
def view(id):
    try:
        with open(f"{PASTE_DIR}/{id}.txt") as f:
            content = f.read()
    except:
        return "Not found"

    return render_template_string("""
    <style>
    body { background:#111; color:white; font-family:sans-serif; }
    .box { background:#1e1e1e; padding:15px; border-radius:8px; white-space:pre-wrap; }
    </style>

    <h2>💀 Paste</h2>
    <div class="box">{{content}}</div>
    <br>
    <a href="/raw/{{id}}">Raw</a>
    """, content=content, id=id)

# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run()
