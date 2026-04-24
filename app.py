from flask import Flask, request, jsonify, redirect, make_response
import os, uuid, json, secrets

app = Flask(__name__)

DATA_FILE = "data.json"
PASTE_DIR = "pastes"

os.makedirs(PASTE_DIR, exist_ok=True)

# ---------------- LOAD ----------------

def load():
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "tokens": {}, "pastes": {}}
    with open(DATA_FILE) as f:
        return json.load(f)

def save(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

DATA = load()

# ---------------- HOME ----------------

@app.route("/")
def home():
    return """
    <style>
    body { background:#000; color:#00ff88; font-family:monospace; text-align:center; }
    input { background:#111; color:#00ff88; border:1px solid #00ff88; padding:10px; margin:5px; }
    button { background:#000; color:#00ff88; border:1px solid #00ff88; padding:10px; }
    </style>

    <h2>[ CREATE ACCOUNT ]</h2>

    <form action="/signup" method="POST">
        <input name="user" placeholder="username"><br>
        <input name="pass" type="password" placeholder="password"><br>
        <button>ENTER</button>
    </form>
    """

# ---------------- SIGNUP ----------------

@app.route("/signup", methods=["POST"])
def signup():
    user = request.form.get("user")
    password = request.form.get("pass")

    if user in DATA["users"]:
        return "USER EXISTS"

    token = secrets.token_hex(32)

    DATA["users"][user] = password
    DATA["tokens"][token] = user
    DATA["pastes"][user] = []
    save(DATA)

    resp = make_response(redirect("/panel"))
    resp.set_cookie("token", token)

    return resp

# ---------------- PANEL ----------------

@app.route("/panel", methods=["GET", "POST"])
def panel():
    token = request.cookies.get("token")

    if token not in DATA["tokens"]:
        return redirect("/")

    user = DATA["tokens"][token]

    if request.method == "POST":
        content = request.form.get("content")

        if content:
            paste_id = str(uuid.uuid4())[:8]

            with open(f"{PASTE_DIR}/{paste_id}.txt", "w") as f:
                f.write(content)

            DATA["pastes"][user].append(paste_id)
            save(DATA)

    paste_list = ""
    for p in DATA["pastes"][user]:
        paste_list += f"[ {p} ] → <a href='/view/{p}'>VIEW</a> | <a href='/raw/{p}'>RAW</a><br>"

    return f"""
    <style>
    body {{ background:#000; color:#00ff88; font-family:monospace; }}
    textarea {{
        width:100%; height:150px;
        background:#000;
        color:#00ff88;
        border:1px solid #00ff88;
        padding:10px;
    }}
    button {{
        background:#000;
        color:#00ff88;
        border:1px solid #00ff88;
        padding:10px;
    }}
    a {{ color:#00ffaa; }}
    </style>

    <h2>[ USER: {user} ]</h2>

    <button onclick="copyToken()">COPY TOKEN</button>

    <script>
    function copyToken(){{
        navigator.clipboard.writeText("{token}")
        alert("TOKEN COPIED")
    }}
    </script>

    <h3>[ NEW PASTE ]</h3>

    <form method="POST">
        <textarea name="content" placeholder="type your code..."></textarea><br>
        <button>UPLOAD</button>
    </form>

    <h3>[ YOUR PASTES ]</h3>
    {paste_list}
    """

# ---------------- API ----------------

@app.route("/api/auth", methods=["POST"])
def auth():
    token = secrets.token_hex(32)
    DATA["tokens"][token] = "api"
    save(DATA)
    return jsonify({"token": token})

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

# ---------------- VIEW ----------------

@app.route("/view/<id>")
def view(id):
    try:
        with open(f"{PASTE_DIR}/{id}.txt") as f:
            content = f.read()
    except:
        return "NOT FOUND"

    return f"""
    <style>
    body {{ background:#000; color:#00ff88; font-family:monospace; }}
    pre {{ border:1px solid #00ff88; padding:10px; }}
    </style>

    <h2>[ VIEW ]</h2>
    <pre>{content}</pre>

    <a href="/raw/{id}">RAW</a>
    """

# ---------------- RAW ----------------

@app.route("/raw/<id>")
def raw(id):
    try:
        with open(f"{PASTE_DIR}/{id}.txt") as f:
            content = f.read()
    except:
        return "NOT FOUND"

    return f"""
    <style>
    body {{ background:#000; color:#00ff88; font-family:monospace; }}
    </style>
    {content}
    """

# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run()
