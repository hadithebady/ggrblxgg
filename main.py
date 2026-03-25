from flask import Flask, request, jsonify, render_template, session, redirect
from functools import wraps
import requests
import json
import time

app = Flask(__name__)
app.secret_key = "67dwhdih290ufhepf-fe"

WEBHOOK_URL = "https://discord.com/api/webhooks/1486428401412735106/pK6JYQ_-XZszpRHE9vyT9BTBhzR-GNcrRRpLEb6yt3220CC_CtbfR9aPxsJAnBm2JMeC"


# ----------------------------
# LOAD KEYS
# ----------------------------
def load_keys():
    with open("keys.json", "r") as f:
        return json.load(f)


# ----------------------------
# WEBHOOK LOGGER
# ----------------------------
def hook(msg):
    try:
        requests.post(WEBHOOK_URL, json={"content": msg})
    except:
        pass


# ----------------------------
# SECURITY DECORATOR
# ----------------------------
def require_login(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            hook(f"🚨 BLOCKED ACCESS | IP: {request.remote_addr} | PATH: {request.path}")
            return redirect("/")
        return f(*args, **kwargs)
    return wrapper


# ----------------------------
# LOGIN PAGE
# ----------------------------
@app.route("/")
def login_page():
    return render_template("login.html")


# ----------------------------
# VERIFY KEY LOGIN
# ----------------------------
@app.route("/verify_key", methods=["POST"])
def verify_key():
    key = request.json.get("key", "").strip()
    keys = load_keys()

    ip = request.remote_addr
    now = time.strftime("%Y-%m-%d %H:%M:%S")

    if key in keys:
        session.clear()
        session["user"] = key
        session["time"] = now
        session["ip"] = ip

        hook(f"✅ LOGIN SUCCESS\nKey: {key}\nIP: {ip}\nTime: {now}")

        return jsonify({"ok": True})

    hook(f"❌ LOGIN FAILED\nKey: {key}\nIP: {ip}\nTime: {now}")

    return jsonify({"ok": False}), 401


# ----------------------------
# PROTECTED MAIN PAGE
# ----------------------------
@app.route("/home")
@require_login
def home():
    return render_template("index.html")


# ----------------------------
# ROBLOX API (REAL)
# ----------------------------
def get_user_id(username):
    r = requests.post(
        "https://users.roblox.com/v1/usernames/users",
        json={"usernames": [username], "excludeBannedUsers": True}
    )

    data = r.json()
    if not data.get("data"):
        return None

    return data["data"][0]["id"]


def get_avatar(user_id):
    r = requests.get(
        f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=420x420&format=Png&isCircular=false"
    )

    try:
        return r.json()["data"][0]["imageUrl"]
    except:
        return None


@app.route("/search_user", methods=["POST"])
@require_login
def search_user():
    username = request.json.get("username", "").strip()

    uid = get_user_id(username)
    if not uid:
        return jsonify({"error": "User not found"}), 404

    profile = requests.get(f"https://users.roblox.com/v1/users/{uid}").json()
    avatar = get_avatar(uid)

    return jsonify({
        "username": profile.get("name"),
        "display_name": profile.get("displayName"),
        "avatar": avatar
    })


# ----------------------------
# SIMPLE IN-MEMORY USER DATA (F2 SHOP SAVE)
# ----------------------------
user_data = {}


# ----------------------------
# SAVE SHOP DATA (F2 PANEL)
# ----------------------------
@app.route("/save_data", methods=["POST"])
@require_login
def save_data():
    user = session["user"]
    user_data[user] = request.json

    hook(f"💾 SHOP UPDATED | USER: {user}")

    return jsonify({"ok": True})


# ----------------------------
# LOAD SHOP DATA
# ----------------------------
@app.route("/get_data")
@require_login
def get_data():
    user = session["user"]
    return jsonify(user_data.get(user, {}))


# ----------------------------
# LOGOUT
# ----------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ----------------------------
# RUN SERVER
# ----------------------------
if __name__ == "__main__":
    app.run(debug=True)
