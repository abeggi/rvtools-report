"""
RVTools Analyzer — Flask App
Porta: 6000
"""

import os
import uuid
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from flask import (
    Flask, request, redirect, url_for,
    send_file, render_template, abort, jsonify
)
from apscheduler.schedulers.background import BackgroundScheduler
from parser import parse_rvtools
from report_builder import build_report

# ── Config ──────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_DIR = Path(os.environ.get("DATA_DIR", str(BASE_DIR / "data")))
UPLOADS_DIR = DATA_DIR / "uploads"
REPORTS_DIR = DATA_DIR / "reports"
STATIC_DIR = BASE_DIR / "static"
SETTINGS_FILE = DATA_DIR / "settings.json"
RETENTION_DAYS = 180
PORT = 8080

DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB


# ── Settings (logo + colori personalizzabili) ────────────────────────────────
DEFAULT_SETTINGS = {
    "primary_color": "#0055b8",
    "accent_color": "#1268FB",
    "company_name": "Var Group",
    "logo_url": "",
}


def get_settings() -> dict:
    if SETTINGS_FILE.exists():
        with open(SETTINGS_FILE) as f:
            s = json.load(f)
        return {**DEFAULT_SETTINGS, **s}
    return DEFAULT_SETTINGS.copy()


def save_settings(data: dict):
    current = get_settings()
    current.update(data)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(current, f)


# ── Pulizia automatica (5 giorni) ────────────────────────────────────────────
def cleanup_old_files():
    cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)
    for folder in [UPLOADS_DIR, REPORTS_DIR]:
        for entry in folder.iterdir():
            if entry.is_dir():
                ts_file = entry / "timestamp.txt"
                if ts_file.exists():
                    ts = datetime.fromisoformat(ts_file.read_text().strip())
                    if ts < cutoff:
                        shutil.rmtree(entry)


scheduler = BackgroundScheduler()
scheduler.add_job(cleanup_old_files, "interval", hours=12)
scheduler.start()


# ── Helper per metadati report ───────────────────────────────────────────────
def get_report_meta(report_id: str) -> dict | None:
    meta_file = REPORTS_DIR / report_id / "meta.json"
    if meta_file.exists():
        with open(meta_file) as f:
            return json.load(f)
    return None


def list_reports() -> list:
    reports = []
    for d in sorted(REPORTS_DIR.iterdir(), reverse=True):
        if d.is_dir():
            meta = get_report_meta(d.name)
            if meta:
                reports.append(meta)
    reports.sort(key=lambda x: x.get("created", ""), reverse=True)
    return reports


# ── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    settings = get_settings()
    return render_template("index.html", settings=settings)


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return redirect(url_for("index"))
    f = request.files["file"]
    if not f.filename or not f.filename.lower().endswith(".xlsx"):
        return render_template("error.html",
                               message="Carica un file .xlsx valido.",
                               settings=get_settings()), 400

    report_id = uuid.uuid4().hex
    upload_folder = UPLOADS_DIR / report_id
    report_folder = REPORTS_DIR / report_id
    upload_folder.mkdir()
    report_folder.mkdir()

    # Salva timestamp
    ts = datetime.now().isoformat()
    (upload_folder / "timestamp.txt").write_text(ts)
    (report_folder / "timestamp.txt").write_text(ts)

    # Salva il file xlsx
    xlsx_path = upload_folder / f.filename
    f.save(str(xlsx_path))

    # Analizza
    try:
        data = parse_rvtools(str(xlsx_path))
    except Exception as e:
        shutil.rmtree(upload_folder, ignore_errors=True)
        shutil.rmtree(report_folder, ignore_errors=True)
        return render_template("error.html",
                               message=f"Errore nella lettura del file: {e}",
                               settings=get_settings()), 400

    # Custom Metadata
    custom_title = request.form.get("report_title", "").strip()
    custom_date_raw = request.form.get("report_date", "").strip()
    custom_date = None
    if custom_date_raw:
        try:
            custom_date = datetime.strptime(custom_date_raw, "%Y-%m-%dT%H:%M").strftime("%d/%m/%Y %H:%M")
        except:
            pass

    # Genera HTML
    settings = get_settings()
    html_content = build_report(
        data, report_id, f.filename, 
        custom=settings, 
        custom_title=custom_title,
        custom_date=custom_date
    )
    html_path = report_folder / "report.html"
    html_path.write_text(html_content, encoding="utf-8")

    # Salva metadati
    meta = {
        "id": report_id,
        "filename": f.filename,
        "created": ts,
        "custom_title": custom_title,
        "custom_date": custom_date,
        "vms_on": data["summary_on"]["count"],
        "vms_off": data["summary_off"]["count"],
        "total": data["summary_total"]["count"],
    }
    with open(report_folder / "meta.json", "w") as mf:
        json.dump(meta, mf)

    return redirect(url_for("view_report", report_id=report_id))


@app.route("/report/<report_id>")
def view_report(report_id: str):
    html_path = REPORTS_DIR / report_id / "report.html"
    if not html_path.exists():
        abort(404)
    return html_path.read_text(encoding="utf-8")




@app.route("/history")
def history():
    reports = list_reports()
    settings = get_settings()
    return render_template("history.html", reports=reports, settings=settings)


@app.route("/history/<report_id>/download")
def download_report_excel(report_id: str):
    """Scarica il file xlsx originale."""
    upload_folder = UPLOADS_DIR / report_id
    if not upload_folder.exists():
        abort(404)
    for f in upload_folder.iterdir():
        if f.suffix == ".xlsx":
            return send_file(str(f), as_attachment=True, download_name=f.name)
    abort(404)


@app.route("/history/<report_id>/delete", methods=["POST"])
def delete_report(report_id: str):
    """Elimina definitivamente un report e i suoi file."""
    upload_folder = UPLOADS_DIR / report_id
    report_folder = REPORTS_DIR / report_id

    if upload_folder.exists():
        shutil.rmtree(upload_folder)
    if report_folder.exists():
        shutil.rmtree(report_folder)

    return redirect(url_for("history"))


@app.route("/settings", methods=["GET", "POST"])
def settings_page():
    settings = get_settings()
    if request.method == "POST":
        # Prefer the hex text field if it looks valid (user may have typed a hex code)
        def pick_color(field_color, field_hex, fallback):
            hex_val = request.form.get(field_hex, "").strip()
            if hex_val and len(hex_val) == 7 and hex_val.startswith("#"):
                return hex_val
            return request.form.get(field_color, fallback)

        new = {
            "primary_color": pick_color("primary_color", "primary_color_hex", settings["primary_color"]),
            "accent_color":  pick_color("accent_color",  "accent_color_hex",  settings["accent_color"]),
            "company_name":  request.form.get("company_name", settings["company_name"]),
        }
        
        # Gestione eliminazione logo
        if request.form.get("delete_logo") == "1":
            new["logo_url"] = ""
            logo_path = STATIC_DIR / "img" / "custom_logo.png"
            if logo_path.exists():
                logo_path.unlink()
        else:
            new["logo_url"] = settings.get("logo_url", "")

        # Gestione upload logo
        if "logo" in request.files:
            logo_file = request.files["logo"]
            if logo_file.filename:
                logo_path = STATIC_DIR / "img" / "custom_logo.png"
                logo_file.save(str(logo_path))
                new["logo_url"] = "/static/img/custom_logo.png"
        
        save_settings(new)
        return redirect(url_for("settings_page"))
    return render_template("settings.html", settings=settings)


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"🚀 RVTools Analyzer avviato su http://0.0.0.0:{PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=False)
