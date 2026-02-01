# ATS Checker (CV) — Application complète (Flask + CLI)

Cette application :
- accepte un **CV PDF ou DOCX** + une **offre d'emploi** (texte),
- calcule un **score ATS /100**,
- affiche les **points faibles** (sections manquantes, mots-clés manquants, contact, lisibilité, etc.),
- propose des **recommandations concrètes**.

## 1) Installation
```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows (PowerShell)
# .\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

## 2) Lancer l'app web
```bash
python app.py
```
Puis ouvre : http://127.0.0.1:5001

## 3) Utiliser en ligne de commande (CLI)
```bash
python cli.py --cv "mon_cv.pdf" --job "offre.txt"
# ou :
python cli.py --cv "mon_cv.docx" --job-text "texte de l'offre ici ..."
```

## Notes
- Pour les **PDF scannés (image)** : l'extraction texte peut être faible -> l'app te prévient.
- L'analyse est volontairement **ATS-friendly** (mots-clés, sections, contacts, quantification).
- Tu peux personnaliser les sections attendues et les règles dans `ats/analyzer.py`.
