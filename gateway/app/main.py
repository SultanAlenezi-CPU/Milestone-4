from flask import Flask, request, jsonify
import json, time, os, uuid
from pathlib import Path

APP = Flask(__name__)

LOG_DIR = Path("gateway/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "experiment_log.jsonl"

def now_ms() -> int:
    return int(time.time() * 1000)

def log_event(event: dict):
    event.setdefault("ts_ms", now_ms())
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

@APP.get("/health")
def health():
    return jsonify({"status": "ok", "ts_ms": now_ms()})

@APP.post("/start_run")
def start_run():
    """
    Starts a new run and returns run_id.
    Body: { "method": "...", "scenario": "normal|mitm_passive|mitm_modify|replay|rogue" }
    """
    body = request.get_json(force=True)
    run_id = body.get("run_id") or str(uuid.uuid4())
    method = body.get("method")
    scenario = body.get("scenario", "normal")

    log_event({
        "type": "run_start",
        "run_id": run_id,
        "method": method,
        "scenario": scenario,
        "t_start_ms": now_ms(),
    })

    return jsonify({"run_id": run_id, "t_start_ms": now_ms()})

@APP.post("/end_run")
def end_run():
    """
    Ends a run.
    Body: { "run_id": "...", "t_end_ms": <optional>, "metrics": {...}, "mitm_success": 0/1, "notes": "" }
    """
    body = request.get_json(force=True)
    run_id = body["run_id"]
    t_end_ms = body.get("t_end_ms", now_ms())
    metrics = body.get("metrics", {})
    mitm_success = int(body.get("mitm_success", 0))
    notes = body.get("notes", "")

    # latency if start exists in logs will be computed later in analysis stage
    log_event({
        "type": "run_end",
        "run_id": run_id,
        "t_end_ms": t_end_ms,
        "metrics": metrics,
        "mitm_success": mitm_success,
        "notes": notes,
    })

    return jsonify({"run_id": run_id, "t_end_ms": t_end_ms, "mitm_success": mitm_success})

if __name__ == "__main__":
    host = os.environ.get("GATEWAY_HOST", "0.0.0.0")
    port = int(os.environ.get("GATEWAY_PORT", "8080"))
    APP.run(host=host, port=port, debug=True)
