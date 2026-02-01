import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename

from ats import extract_text, analyze_cv
from ats.lang import SUPPORTED_LANGS, get_ui, lang_label

UPLOAD_DIR = os.environ.get("UPLOAD_DIR", os.path.join(os.path.dirname(__file__), "uploads"))
ALLOWED_EXT = {"pdf", "docx"}

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "dev-secret-change-me")
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB
os.makedirs(UPLOAD_DIR, exist_ok=True)

def allowed(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT

def _get_langs():
    ui_lang = (request.values.get("ui_lang") or "fr").lower()
    if ui_lang not in ("fr", "en"):
        ui_lang = "en"

    cv_lang = (request.values.get("cv_lang") or "auto").lower()
    if cv_lang not in SUPPORTED_LANGS:
        cv_lang = "auto"

    ui = get_ui(ui_lang)
    return ui_lang, cv_lang, ui

@app.route("/", methods=["GET"])
def index():
    ui_lang, cv_lang, ui = _get_langs()
    return render_template(
        "index.html",
        ui=ui,
        ui_lang=ui_lang,
        cv_lang=cv_lang,
        langs=["auto","fr","en","es","de","it","pt"],
        lang_label=lang_label,
    )

@app.route("/analyze", methods=["POST"])
def analyze():
    ui_lang, cv_lang, ui = _get_langs()

    if "cv" not in request.files:
        flash("No CV file uploaded." if ui_lang == "en" else "Aucun fichier CV envoyé.")
        return redirect(url_for("index", ui_lang=ui_lang, cv_lang=cv_lang))

    f = request.files["cv"]
    job_text = (request.form.get("job_text") or "").strip()

    if f.filename == "":
        flash("Empty filename." if ui_lang == "en" else "Nom de fichier vide.")
        return redirect(url_for("index", ui_lang=ui_lang, cv_lang=cv_lang))

    if not allowed(f.filename):
        flash("Unsupported format. Use PDF or DOCX." if ui_lang == "en" else "Format non supporté. Utilise PDF ou DOCX.")
        return redirect(url_for("index", ui_lang=ui_lang, cv_lang=cv_lang))

    filename = secure_filename(f.filename)
    path = os.path.join(UPLOAD_DIR, filename)
    f.save(path)

    try:
        cv_text, meta = extract_text(path)
    except Exception as e:
        flash(("Extraction error: " if ui_lang == "en" else "Erreur extraction : ") + str(e))
        return redirect(url_for("index", ui_lang=ui_lang, cv_lang=cv_lang))

    result = analyze_cv(cv_text=cv_text, job_text=job_text, meta=meta, cv_lang=cv_lang)
    preview = cv_text[:1400]

    return render_template(
        "result.html",
        ui=ui,
        ui_lang=ui_lang,
        cv_lang=cv_lang,
        langs=["auto","fr","en","es","de","it","pt"],
        lang_label=lang_label,
        result=result,
        meta=meta,
        preview=preview,
        has_job=bool(job_text),
        export_payload={"meta": meta, "result": result},
    )

@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    ui_lang, cv_lang, ui = _get_langs()

    if "cv" not in request.files:
        return jsonify({"error": "missing file"}), 400
    f = request.files["cv"]
    job_text = (request.form.get("job_text") or "").strip()
    if not allowed(f.filename):
        return jsonify({"error": "unsupported file type"}), 400

    filename = secure_filename(f.filename)
    path = os.path.join(UPLOAD_DIR, filename)
    f.save(path)

    cv_text, meta = extract_text(path)
    result = analyze_cv(cv_text=cv_text, job_text=job_text, meta=meta, cv_lang=cv_lang)
    return jsonify({"meta": meta, "result": result})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5001"))
    app.run(host="0.0.0.0", port=port, debug=True)

