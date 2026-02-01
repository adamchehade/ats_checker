import argparse
import json
from ats import extract_text, analyze_cv
from ats.lang import SUPPORTED_LANGS

def main():
    p = argparse.ArgumentParser(description="ATS Checker — analyse un CV PDF/DOCX vs une offre")
    p.add_argument("--cv", required=True, help="Chemin vers le CV (.pdf/.docx)")
    p.add_argument("--job", help="Chemin vers un fichier texte d'offre (.txt)")
    p.add_argument("--job-text", help="Texte brut de l'offre (entre guillemets)")
    p.add_argument("--cv-lang", default="auto", help="Langue du CV: auto/fr/en/es/de/it/pt")
    p.add_argument("--json", action="store_true", help="Sortie JSON")
    args = p.parse_args()

    cv_lang = (args.cv_lang or "auto").lower()
    if cv_lang not in SUPPORTED_LANGS:
        cv_lang = "auto"

    job_text = ""
    if args.job_text:
        job_text = args.job_text
    elif args.job:
        with open(args.job, "r", encoding="utf-8") as f:
            job_text = f.read()

    cv_text, meta = extract_text(args.cv)
    result = analyze_cv(cv_text=cv_text, job_text=job_text, meta=meta, cv_lang=cv_lang)

    if args.json:
        print(json.dumps({"meta": meta, "result": result}, ensure_ascii=False, indent=2))
        return

    print("=== ATS CHECKER ===")
    print(f"Score ATS: {result['score']}/100")
    print(f"Words: {result['word_count']} | Similarity: {result['similarity']} | CV lang used: {result['language']['used']}")
    print("\n-- Weak points --")
    for w in result["weaknesses"]:
        print(f"* {w['title']}: {w['fix']}")
    print("\n-- Missing keywords (top) --")
    print(", ".join(result["keywords"]["missing"]) or "None (or no job text provided).")

if __name__ == "__main__":
    main()
