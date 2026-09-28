"""
AI Information Misuse Prevention System - Flask application.

Wires the three layers from the seminar into one runnable system:
  Layer 1 (input guard)  -> layer1_filter.SemanticFilter
  Layer 2 (output guard) -> layer2_detector.ArtifactDetector
  Layer 3 (governance)   -> layer3_governance.db + severity

Run:  py app.py     then open http://127.0.0.1:5000
"""

import os
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")      # quiet TensorFlow logs
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")     # avoid oneDNN notices
import json
import secrets
import uuid
import warnings
from datetime import datetime

from flask import (Flask, render_template, request, redirect, url_for,
                   send_from_directory, flash, abort)
from flask_wtf.csrf import CSRFProtect
from PIL import Image, UnidentifiedImageError
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename

from layer1_filter.filter import SemanticFilter
from layer2_detector.detector import ArtifactDetector
from layer3_governance import db
from layer3_governance.severity import score_to_severity, needs_human_review

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
SAMPLES_DIR = os.path.join(BASE_DIR, "layer2_detector", "data", "samples")
MODEL_DIR = os.path.join(BASE_DIR, "layer2_detector", "model")
L1_METRICS = os.path.join(BASE_DIR, "layer1_filter", "metrics.json")
L2_METRICS = os.path.join(MODEL_DIR, "metrics.json")
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
MAX_UPLOAD_MB = int(os.environ.get("AIMPS_MAX_UPLOAD_MB", "8"))
MAX_IMAGE_PIXELS = int(os.environ.get("AIMPS_MAX_IMAGE_PIXELS", "20000000"))
os.makedirs(UPLOAD_DIR, exist_ok=True)
Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS


def _load_json(path):
    try:
        with open(path) as fh:
            return json.load(fh)
    except Exception:
        return None

app = Flask(__name__)
app.secret_key = os.environ.get("AIMPS_SECRET_KEY") or secrets.token_hex(32)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024
CSRFProtect(app)

# --- initialise everything once at startup ---
db.init_db()
print("Loading Layer 1 (semantic prompt filter) ...")
prompt_filter = SemanticFilter().load()
print("Loading Layer 2 (CNN artifact detector) ...")
image_detector = ArtifactDetector().load()
print(f"  Layer 1 model trained : {prompt_filter.model_ready}")
print(f"  Layer 2 detector mode : {image_detector.mode}")


def list_samples():
    if not os.path.isdir(SAMPLES_DIR):
        return []
    return sorted(f for f in os.listdir(SAMPLES_DIR)
                  if f.lower().endswith((".png", ".jpg", ".jpeg")))


def _is_allowed_image_name(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def _save_validated_upload(uploaded):
    """Validate an uploaded image, re-encode it, and return (path, filename)."""
    original = secure_filename(uploaded.filename or "")
    if not original or not _is_allowed_image_name(original):
        raise ValueError("Upload a PNG, JPG, JPEG, WEBP, or BMP image.")

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            uploaded.stream.seek(0)
            probe = Image.open(uploaded.stream)
            probe.verify()
            uploaded.stream.seek(0)
            im = Image.open(uploaded.stream).convert("RGB")
            im.load()
    except (
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
        UnidentifiedImageError,
        OSError,
        ValueError,
    ):
        raise ValueError("That file is not a valid image or is too large to process.")

    stem = os.path.splitext(original)[0][:60] or "image"
    image_name = (
        f"{datetime.now().strftime('%Y%m%d%H%M%S')}_"
        f"{uuid.uuid4().hex[:10]}_{stem}.png"
    )
    image_path = os.path.join(UPLOAD_DIR, image_name)
    im.save(image_path, format="PNG", optimize=True)
    return image_path, image_name


def _send_image_from(directory, filename):
    safe = secure_filename(filename)
    if safe != filename or not _is_allowed_image_name(safe):
        abort(404)
    response = send_from_directory(directory, safe, max_age=0)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.errorhandler(RequestEntityTooLarge)
def handle_large_upload(_exc):
    flash(f"Image uploads are limited to {MAX_UPLOAD_MB} MB.")
    return redirect(url_for("index"))


@app.route("/")
def index():
    return render_template("index.html", samples=list_samples(), result=None)


@app.route("/analyze", methods=["POST"])
def analyze():
    prompt = (request.form.get("prompt") or "").strip()
    sample_choice = request.form.get("sample") or ""
    uploaded = request.files.get("image")
    has_image_input = bool((uploaded and uploaded.filename) or sample_choice)

    if not prompt and not has_image_input:
        flash("Enter a prompt or choose/upload an image to analyse.")
        return redirect(url_for("index"))

    result = {"prompt": prompt, "layer1": None, "generation": None,
              "layer2": None, "image_url": None, "image_name": None}

    # ---------- Stage 1: prompt screening (Layer 1) ----------
    if prompt:
        a = prompt_filter.analyze(prompt)
        severity = score_to_severity(a["risk_score"], a["categories"])
        escalated = needs_human_review(severity)
        eid = db.log_event("prompt", prompt, a["verdict"], a["risk_score"],
                           severity, details={**a, "escalated": escalated})
        result["layer1"] = {**a, "severity": severity,
                            "escalated": escalated, "event_id": eid}

    # ---------- Stage 2: simulated generation ----------
    prompt_blocked = (result["layer1"] is not None
                      and result["layer1"]["verdict"] == "blocked")
    if prompt:
        result["generation"] = {
            "status": "prevented" if prompt_blocked else "proceeded"}

    # ---------- locate the image to scan ----------
    image_path, image_name = None, None
    if uploaded and uploaded.filename:
        try:
            image_path, image_name = _save_validated_upload(uploaded)
        except ValueError as exc:
            flash(str(exc))
            return redirect(url_for("index"))
        result["image_url"] = url_for("serve_upload", filename=image_name)
    elif sample_choice:
        safe = secure_filename(sample_choice)
        candidate = os.path.join(SAMPLES_DIR, safe)
        if _is_allowed_image_name(safe) and os.path.exists(candidate):
            image_path, image_name = candidate, safe
            result["image_url"] = url_for("serve_sample", filename=safe)
        else:
            flash("Selected sample image was not found.")
            return redirect(url_for("index"))
    result["image_name"] = image_name

    # ---------- Stage 3: image screening (Layer 2) ----------
    # Only scan if there is an image AND generation was not prevented.
    if image_path and not prompt_blocked:
        d = image_detector.analyze(image_path)
        verdict = "flagged" if d["label"] == "ai_generated" else "clean"
        severity = score_to_severity(d["synthetic_probability"]) if verdict == "flagged" else "low"
        escalated = needs_human_review(severity) and verdict == "flagged"
        eid = db.log_event("image", image_name, verdict,
                           d["synthetic_probability"], severity,
                           details={**d, "escalated": escalated})
        result["layer2"] = {**d, "verdict": verdict, "severity": severity,
                            "escalated": escalated, "event_id": eid}

    return render_template("index.html", samples=list_samples(), result=result)


@app.route("/dashboard")
def dashboard():
    view = request.args.get("view", "all")
    events = db.get_events(limit=200,
                           only_flagged=(view == "flagged"),
                           only_pending=(view == "pending"))
    return render_template("dashboard.html", events=events,
                           stats=db.get_stats(), view=view)


@app.route("/case/<int:event_id>")
def case(event_id):
    ev = db.get_event(event_id)
    if not ev:
        abort(404)
    try:
        parsed = json.loads(ev.get("details") or "{}")
    except Exception:
        parsed = {}
    ev["details_json"] = json.dumps(parsed, indent=2)
    return render_template("case.html", ev=ev)


@app.route("/case/<int:event_id>/review", methods=["POST"])
def review(event_id):
    note = (request.form.get("note") or "").strip()
    try:
        db.update_review(event_id, note, mark_reviewed=True)
    except ValueError:
        abort(404)
    flash(f"Case #{event_id} marked reviewed.")
    return redirect(url_for("case", event_id=event_id))


@app.route("/performance")
def performance():
    return render_template("performance.html",
                           l1=_load_json(L1_METRICS),
                           l2=_load_json(L2_METRICS),
                           detector_mode=image_detector.mode)


@app.route("/model-asset/<path:filename>")
def model_asset(filename):
    if not filename.endswith(".png"):
        abort(404)
    return send_from_directory(MODEL_DIR, filename)


@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    return _send_image_from(UPLOAD_DIR, filename)


@app.route("/samples/<path:filename>")
def serve_sample(filename):
    return _send_image_from(SAMPLES_DIR, filename)


if __name__ == "__main__":
    debug = os.environ.get("AIMPS_DEBUG", "0").lower() in {"1", "true", "yes"}
    port = int(os.environ.get("AIMPS_PORT", "5000"))
    app.run(host="127.0.0.1", port=port, debug=debug, use_reloader=False)
