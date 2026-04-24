from flask import Flask, request, redirect, session, render_template_string
import os, uuid

app = Flask(__name__)
app.secret_key = "secret123"

PASTE_DIR = "pastes"
os.makedirs(PASTE_DIR, exist_ok=True)

# simple login
USERS = {
    "admin": "1234"
}

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""

    if request.method == "POST":
        u = request.form.get("user")
        p = request.form.get("pass")

        if USERS.get(u) == p:
            session["user"] = u
            return redirect("/")
        else:
            error = "❌ Wrong username or password"

    return f"""
    <style>
    body {{ background:#0f0f0f; color:white; font-family:sans-serif; text-align:center; }}
    input {{ padding:10px; margin:5px; background:#1e1e1e; color:white; border:none; width:200px; }}
    button {{ padding:10px; background:#333; color:white; border:none; }}
    </style>

    <h2>🔐 Login</h2>
    <form method="POST">
    <input name="user" placeholder="username"><br>
    <input name="pass" type="password" placeholder="password"><br>
    <button>Login</button>
    </form>
    <p style='color:red'>{error}</p>
    """

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------------- HOME ----------------
@app.route("/", methods=["GET", "POST"])
def home():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        content = request.form.get("content")

        if not content or content.strip() == "":
            return redirect("/")

        paste_id = str(uuid.uuid4())[:8]
        with open(f"{PASTE_DIR}/{paste_id}.txt", "w", encoding="utf-8") as f:
            f.write(content)

        return redirect("/")

    files = os.listdir(PASTE_DIR)
    pastes = [f.replace(".txt", "") for f in files]

    return render_template_string("""
    <style>
    body { background:#0f0f0f; color:white; font-family:sans-serif; }
    textarea { width:100%; height:150px; background:#1e1e1e; color:white; border:none; padding:10px; }
    button { padding:10px; background:#333; color:white; border:none; margin-top:5px; }
    a { color:cyan; text-decoration:none; }
    .box { background:#1a1a1a; padding:10px; margin:10px 0; border-radius:6px; }
    </style>

    <h2>💀 My Paste</h2>

    <form method="POST">
    <textarea name="content" placeholder="paste your code..."></textarea><br>
    <button>Create Paste</button>
    </form>

    <h3>📄 Your Pastes</h3>

    {% for p in pastes %}
    <div class="box">
        <a href="/raw/{{p}}" target="_blank">View</a> |
        <a href="/delete/{{p}}">Delete</a>
        <br>ID: {{p}}
    </div>
    {% endfor %}

    <br>
    <a href="/logout">Logout</a>
    """, pastes=pastes)

# ---------------- RAW ----------------
@app.route("/raw/<id>")
def raw(id):
    try:
        with open(f"{PASTE_DIR}/{id}.txt", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return "❌ Not found"

# ---------------- DELETE ----------------
@app.route("/delete/<id>")
def delete(id):
    try:
        os.remove(f"{PASTE_DIR}/{id}.txt")
    except:
        pass
    return redirect("/")

# ---------------- START ----------------
if __name__ == "__main__":
    app.run()
