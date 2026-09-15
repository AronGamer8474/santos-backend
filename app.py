import json, os, time, threading
from flask import Flask, request, jsonify, abort

app = Flask(__name__)

# ─────────────────────────────────────────────────────────────
# CHANGE THESE THREE LINES BEFORE DEPLOYING
# ─────────────────────────────────────────────────────────────
USER_KEY  = "user_test_7f4a91c2"
ADMIN_KEY = "admin_test_9b82e6d1"
PORT      = int(os.environ.get("PORT", 8080))
# ─────────────────────────────────────────────────────────────

STORE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state.json")
_lock  = threading.Lock()
_state = {"seq": 0, "items": []}

def load():
    global _state
    if os.path.exists(STORE):
        try:
            with open(STORE, "r", encoding="utf-8") as f:
                _state = json.load(f)
        except Exception as e:
            print("load failed:", e)
    print(f"[boot] loaded {len(_state['items'])} announcements, seq={_state['seq']}")

def save():
    try:
        with open(STORE, "w", encoding="utf-8") as f:
            json.dump(_state, f)
    except Exception as e:
        print("save failed:", e)

load()

@app.get("/")
def root():
    return f"Santos backend OK. seq={_state['seq']} items={len(_state['items'])}"

@app.get("/sync")
def sync():
    # Client's polling endpoint.
    try:
        ann_since = int(request.args.get("ann_since", "-1"))
    except ValueError:
        ann_since = -1

    with _lock:
        seq = _state["seq"]
        if ann_since < 0:
            new_items = []          # first poll: don't spam old ones
        else:
            new_items = [i for i in _state["items"] if int(i["id"]) > ann_since]

    return jsonify(ok=True, ann_seq=seq, ann=new_items, poll=3, online=1)

@app.post("/announce")
def announce():
    if request.headers.get("X-Admin-Key", "") != ADMIN_KEY:
        abort(401)
    body = request.get_json(silent=True) or {}
    title    = str(body.get("title") or "Announcement")
    text     = str(body.get("text") or body.get("content") or "")
    duration = int(body.get("duration") or 15)
    sound    = body.get("sound", "default")

    with _lock:
        _state["seq"] += 1
        item = {
            "id": _state["seq"],
            "title": title,
            "text": text,
            "duration": duration,
            "sound": sound,
            "ts": int(time.time()),
        }
        _state["items"].append(item)
        save()

    print(f"[announce] #{item['id']} {title!r}")
    return jsonify(ok=True, id=item["id"])

@app.post("/discord-relay/<token>")
def discord_relay(token):
    # Wire a Discord webhook here so you can post announcements from Discord.
    if token != "MTU0OTQyNjI2Mzg3NjQzNjAzOQ.GZjjmn.VeRW3Yiu1NjXEnIXRRswGAzjqfoSmEPXhASbfQ":
        abort(404)
    body = request.get_json(silent=True) or {}
    text = str(body.get("content", "")).strip()
    if not text:
        return jsonify(ok=False, error="empty")

    with _lock:
        _state["seq"] += 1
        _state["items"].append({
            "id": _state["seq"],
            "title": "Santos",
            "text": text,
            "duration": 15,
            "sound": "default",
            "ts": int(time.time()),
        })
        save()
    return jsonify(ok=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
