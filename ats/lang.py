from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Set
import re

# Minimal stopword sets (lightweight, no external deps).
STOPWORDS: Dict[str, Set[str]] = {
    "fr": {
        "le","la","les","un","une","des","de","du","d","et","ou","à","au","aux","en","pour","par","sur","dans","avec",
        "sans","ce","cet","cette","ces","qui","que","quoi","dont","où","ne","pas","plus","moins","très","tres","ainsi",
        "se","sa","son","ses","leur","leurs","mon","ma","mes","ton","ta","tes","vos","votre","nos","notre","je","tu","il",
        "elle","nous","vous","ils","elles","a","ai","as","avons","avez","ont","est","sont","été","etre","être","fait","faire",
        "comme","lors","lorsque","afin","car","si","mais","donc","or","ni","enfin"
    },
    "en": {
        "the","a","an","and","or","to","for","of","in","on","at","with","without","from","by","as","is","are","was","were",
        "be","been","being","this","that","these","those","it","its","you","your","we","our","they","their","i","me","my",
        "not","no","yes","but","so","than","then","also","into","over","under","about"
    },
    "es": {
        "el","la","los","las","un","una","unos","unas","de","del","y","o","a","en","para","por","con","sin","que","quien",
        "como","cuando","donde","no","sí","si","más","menos","muy","también","pero","porque","sobre","entre","su","sus","mi",
        "mis","tu","tus","nuestro","nuestra","vosotros","ellos","ellas"
    },
    "de": {
        "der","die","das","ein","eine","und","oder","zu","für","von","im","in","am","an","auf","mit","ohne","dass","wie",
        "wann","wo","nicht","ja","nein","mehr","weniger","sehr","aber","weil","über","unter","zwischen","sein","sind","war",
        "waren","ich","du","er","sie","wir","ihr","ihnen"
    },
    "it": {
        "il","lo","la","i","gli","le","un","una","uno","di","del","della","e","o","a","in","per","con","senza","che","chi",
        "come","quando","dove","non","sì","si","più","meno","molto","anche","ma","perché","su","tra","fra","mio","mia","tuo","suo"
    },
    "pt": {
        "o","a","os","as","um","uma","uns","umas","de","do","da","dos","das","e","ou","a","em","para","por","com","sem","que",
        "quem","como","quando","onde","não","sim","mais","menos","muito","também","mas","porque","sobre","entre","seu","sua","meu","minha"
    },
}

# Section title variants per language (used to detect structure).
SECTION_VARIANTS: Dict[str, Dict[str, List[str]]] = {
    "fr": {
        "summary": ["profil", "résumé", "resume", "à propos", "objectif"],
        "skills": ["compétences", "competences", "skills", "technologies", "outils", "stack"],
        "experience": ["expérience", "experience", "projets", "projet", "missions"],
        "education": ["formation", "éducation", "education", "diplôme", "diplomes"],
        "certs": ["certification", "certifications", "certifié", "certificat"],
        "languages": ["langues", "languages"],
    },
    "en": {
        "summary": ["summary", "profile", "about", "objective"],
        "skills": ["skills", "technologies", "tools", "stack"],
        "experience": ["experience", "work experience", "professional experience", "projects", "project"],
        "education": ["education", "degree", "studies"],
        "certs": ["certifications", "certification", "certified"],
        "languages": ["languages"],
    },
    "es": {
        "summary": ["perfil", "resumen", "objetivo", "sobre mí", "sobre mi"],
        "skills": ["habilidades", "competencias", "tecnologías", "herramientas", "stack"],
        "experience": ["experiencia", "experiencia profesional", "proyectos"],
        "education": ["educación", "formación", "estudios", "titulación", "titulacion"],
        "certs": ["certificaciones", "certificación", "certificacion"],
        "languages": ["idiomas", "lenguas"],
    },
    "de": {
        "summary": ["profil", "kurzprofil", "zusammenfassung", "ziel"],
        "skills": ["kenntnisse", "fähigkeiten", "faehigkeiten", "technologien", "tools"],
        "experience": ["erfahrung", "berufserfahrung", "projekte"],
        "education": ["ausbildung", "studium", "bildung", "abschluss"],
        "certs": ["zertifikate", "zertifizierung"],
        "languages": ["sprachen"],
    },
    "it": {
        "summary": ["profilo", "riepilogo", "obiettivo", "su di me"],
        "skills": ["competenze", "abilità", "abilita", "tecnologie", "strumenti"],
        "experience": ["esperienza", "esperienza lavorativa", "progetti"],
        "education": ["istruzione", "formazione", "studi", "laurea"],
        "certs": ["certificazioni", "certificazione"],
        "languages": ["lingue"],
    },
    "pt": {
        "summary": ["perfil", "resumo", "objetivo", "sobre mim"],
        "skills": ["competências", "competencias", "habilidades", "tecnologias", "ferramentas"],
        "experience": ["experiência", "experiencia", "experiência profissional", "projetos"],
        "education": ["educação", "educacao", "formação", "formacao", "estudos"],
        "certs": ["certificações", "certificacoes", "certificação", "certificacao"],
        "languages": ["idiomas"],
    },
}

SUPPORTED_LANGS = ["auto", "fr", "en", "es", "de", "it", "pt"]

def detect_language(text: str, candidates: List[str] | None = None) -> str:
    # Very lightweight language detection based on stopword hits.
    # Returns: fr/en/es/de/it/pt. Falls back to 'en' if unclear.
    candidates = [c for c in (candidates or ["fr","en","es","de","it","pt"]) if c in STOPWORDS]
    toks = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ]{2,}", (text or "").lower())
    if not toks:
        return "en"
    tok_set = set(toks)
    scores = {lang: sum(1 for t in tok_set if t in STOPWORDS[lang]) for lang in candidates}
    best = max(scores.items(), key=lambda x: x[1])[0]
    if scores[best] < 3:
        return "en"
    return best

# Simple UI strings (French + English)
UI: Dict[str, Dict[str, str]] = {
    "fr": {
        "title": "ATS Checker (CV)",
        "subtitle": "Analyse ton CV (PDF/DOCX) contre une offre : score /100, points faibles, recommandations.",
        "cv_file": "CV (PDF/DOCX)",
        "job_desc": "Offre d’emploi (recommandé)",
        "job_placeholder": "Colle ici le texte de l'offre (missions, compétences, outils, etc.)",
        "analyze": "Analyser",
        "reset": "Réinitialiser",
        "ui_lang": "Langue de l’interface",
        "cv_lang": "Langue du CV",
        "cv_lang_hint": "Auto détecte la langue. Choisis une langue si ton CV est mixte.",
        "tips": "Astuce : évite colonnes, icônes et tableaux (souvent mal lus par les ATS). Préfère des titres simples.",
        "back": "Nouvelle analyse",
        "score": "Score ATS",
        "details": "Détails",
        "weak_points": "Points faibles & corrections",
        "keywords": "Mots-clés",
        "found": "Détectés",
        "missing": "Manquants (prioritaires)",
        "preview": "Extraction (aperçu)",
        "readability_warnings": "Avertissements lisibilité",
        "stats": "Statistiques",
        "words": "Mots",
        "similarity": "Similarité",
        "match_ratio": "Match mots-clés",
        "language_detected": "Langue détectée",
        "contacts": "Contacts",
        "sections": "Sections",
        "export_json": "Exporter JSON",
    },
    "en": {
        "title": "ATS Checker (Resume/CV)",
        "subtitle": "Analyze your resume (PDF/DOCX) vs a job description: score /100, weak points, recommendations.",
        "cv_file": "Resume/CV (PDF/DOCX)",
        "job_desc": "Job description (recommended)",
        "job_placeholder": "Paste the job description here (responsibilities, skills, tools, etc.)",
        "analyze": "Analyze",
        "reset": "Reset",
        "ui_lang": "UI language",
        "cv_lang": "CV language",
        "cv_lang_hint": "Auto detects language. Select one if your CV is mixed.",
        "tips": "Tip: avoid columns, icons and tables (often poorly read by ATS). Prefer simple headings.",
        "back": "New analysis",
        "score": "ATS Score",
        "details": "Details",
        "weak_points": "Weak points & fixes",
        "keywords": "Keywords",
        "found": "Detected",
        "missing": "Missing (priority)",
        "preview": "Extraction (preview)",
        "readability_warnings": "Readability warnings",
        "stats": "Stats",
        "words": "Words",
        "similarity": "Similarity",
        "match_ratio": "Keyword match",
        "language_detected": "Detected language",
        "contacts": "Contacts",
        "sections": "Sections",
        "export_json": "Export JSON",
    },
}

def get_ui(lang: str) -> Dict[str, str]:
    return UI.get(lang, UI["en"])

def lang_label(code: str, ui_lang: str = "en") -> str:
    labels = {
        "fr": {"fr": "Français", "en": "French"},
        "en": {"fr": "Anglais", "en": "English"},
        "es": {"fr": "Espagnol", "en": "Spanish"},
        "de": {"fr": "Allemand", "en": "German"},
        "it": {"fr": "Italien", "en": "Italian"},
        "pt": {"fr": "Portugais", "en": "Portuguese"},
        "auto": {"fr": "Auto", "en": "Auto"},
    }
    return labels.get(code, {}).get(ui_lang, code)

@dataclass
class LangInfo:
    ui_lang: str
    cv_lang: str
    detected: str
