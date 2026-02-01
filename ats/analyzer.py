from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .utils import (
    find_contacts, has_numbers_impact, word_count,
    remove_stopwords, unique_preserve, soft_contains
)
from .lang import SECTION_VARIANTS, detect_language

TECH_HINTS = [
    "python","java","c","c++","c#","javascript","typescript","sql","linux","windows","bash","git","github",
    "docker","kubernetes","aws","azure","gcp",
    "network","réseau","reseau","routing","switching","vlan","vpn","firewall","pfsense","cisco",
    "active directory","ad","dns","dhcp","mqtt","iot","raspberry","esp8266","flask","fastapi",
    "wireshark","tcp/ip","http","rest","api","ssh",
]

CORE_SECTIONS = ["skills","experience","education"]

@dataclass
class ScoreBreakdown:
    keyword_match: int
    similarity: int
    sections: int
    contacts: int
    impact: int
    length: int
    readability: int

def _detect_sections(cv_text: str, lang: str) -> Tuple[Dict[str, bool], List[str]]:
    t = cv_text.lower()
    variants = SECTION_VARIANTS.get(lang, SECTION_VARIANTS.get("en"))
    found: Dict[str, bool] = {}
    for key, words in variants.items():
        found[key] = any(w in t for w in words)
    missing_titles = [k for k in CORE_SECTIONS if not found.get(k, False)]
    return found, missing_titles

def _job_keywords(job_text: str, lang: str, top_k: int = 35) -> List[str]:
    job_text = job_text.strip()
    if not job_text:
        return []
    vectorizer = TfidfVectorizer(
        ngram_range=(1,2),
        min_df=1,
        max_df=0.9,
        token_pattern=r"(?u)\b[A-Za-zÀ-ÖØ-öø-ÿ0-9+#.\-]{2,}\b"
    )
    X = vectorizer.fit_transform([job_text])
    terms = vectorizer.get_feature_names_out()
    scores = X.toarray()[0]
    ranked = sorted(zip(terms, scores), key=lambda x: x[1], reverse=True)
    out = [t for t,s in ranked if len(t) >= 2][:top_k]
    toks = remove_stopwords([x for x in out], lang=lang)
    return unique_preserve(toks)

def _similarity(cv_text: str, job_text: str) -> float:
    if not job_text.strip() or not cv_text.strip():
        return 0.0
    vectorizer = TfidfVectorizer(
        ngram_range=(1,2),
        min_df=1,
        max_df=0.9,
        token_pattern=r"(?u)\b[A-Za-zÀ-ÖØ-öø-ÿ0-9+#.\-]{2,}\b"
    )
    X = vectorizer.fit_transform([cv_text, job_text])
    sim = cosine_similarity(X[0:1], X[1:2])[0][0]
    return float(sim)

def _keyword_match(cv_text: str, keywords: List[str]) -> Tuple[List[str], List[str], float]:
    if not keywords:
        return [], [], 0.0
    t = cv_text.lower()
    matched, missing = [], []
    for kw in keywords:
        if soft_contains(t, kw):
            matched.append(kw)
        else:
            missing.append(kw)
    ratio = len(matched) / max(1, len(keywords))
    return matched, missing, ratio

def _readability_flags(cv_text: str, meta: Dict[str, Any]) -> List[str]:
    flags = []
    if len(cv_text) < 500:
        flags.append("Low text extraction: the PDF might be scanned (image) or heavily formatted. Many ATS will struggle.")
    if meta.get("file_type") == "docx" and meta.get("has_tables"):
        flags.append("Tables detected in DOCX: some ATS read tables poorly. Prefer simple sections and bullet lists.")
    if re.search(r"[■◆●•]{10,}", cv_text):
        flags.append("Too many decorative bullets/icons: keep formatting simple for ATS parsing.")
    return flags

def analyze_cv(cv_text: str, job_text: str = "", meta: Dict[str, Any] | None = None, cv_lang: str = "auto") -> Dict[str, Any]:
    meta = meta or {}

    detected = detect_language(cv_text)
    lang = detected if cv_lang == "auto" else cv_lang

    wc = word_count(cv_text)
    contacts = find_contacts(cv_text)
    impact_count, impact_samples = has_numbers_impact(cv_text)
    sections, missing_core_sections = _detect_sections(cv_text, lang=lang)

    job_lang = detect_language(job_text) if job_text.strip() else lang
    keywords = _job_keywords(job_text, lang=job_lang) if job_text.strip() else []
    if not keywords:
        keywords = unique_preserve([k for k in TECH_HINTS if len(k) >= 2])[:30]

    matched_kw, missing_kw, kw_ratio = _keyword_match(cv_text, keywords)
    sim = _similarity(cv_text, job_text) if job_text.strip() else (kw_ratio * 0.6)

    keyword_score = int(round(kw_ratio * 100))
    similarity_score = int(round(min(1.0, sim) * 100))

    sec_hits = sum(1 for k in CORE_SECTIONS if sections.get(k))
    sections_score = int(round((sec_hits / len(CORE_SECTIONS)) * 100))

    contact_points = 0
    if contacts["emails"]:
        contact_points += 40
    if contacts["phones"]:
        contact_points += 30
    if contacts["linkedin"]:
        contact_points += 20
    elif contacts["github"]:
        contact_points += 15
    contacts_score = min(100, contact_points)

    if impact_count >= 8:
        impact_score = 100
    elif impact_count >= 4:
        impact_score = 70
    elif impact_count >= 2:
        impact_score = 45
    else:
        impact_score = 15

    if wc < 250:
        length_score = 25
    elif wc < 350:
        length_score = 55
    elif wc <= 1100:
        length_score = 100
    elif wc <= 1400:
        length_score = 70
    else:
        length_score = 40

    flags = _readability_flags(cv_text, meta)
    readability_score = 100 - min(60, 20 * len(flags))

    breakdown = ScoreBreakdown(
        keyword_match=keyword_score,
        similarity=similarity_score,
        sections=sections_score,
        contacts=contacts_score,
        impact=impact_score,
        length=length_score,
        readability=readability_score,
    )

    total = (
        0.30 * breakdown.keyword_match +
        0.20 * breakdown.similarity +
        0.15 * breakdown.sections +
        0.10 * breakdown.contacts +
        0.10 * breakdown.impact +
        0.10 * breakdown.length +
        0.05 * breakdown.readability
    )
    total_score = int(round(total))

    weaknesses: List[Dict[str, str]] = []

    if not contacts["emails"]:
        weaknesses.append({"title": "Missing email", "fix": "Add a visible email at the top of the CV (simple format)."})
    if not contacts["phones"]:
        weaknesses.append({"title": "Missing phone number", "fix": "Add a reachable phone number (international format recommended)."})
    if not (contacts["linkedin"] or contacts["github"]):
        weaknesses.append({"title": "Missing professional link", "fix": "Add LinkedIn and/or GitHub (if relevant)."})
    if missing_core_sections:
        weaknesses.append({"title": "Missing core sections", "fix": f"Add clear headings for: {', '.join(missing_core_sections)}."})

    if job_text.strip():
        if similarity_score < 35:
            weaknesses.append({"title": "Low match vs job description", "fix": "Rewrite summary and skills using the exact wording of the job post (without lying)."})
        if keyword_score < 45:
            weaknesses.append({"title": "Missing keywords", "fix": "Add missing skills/tools in a Skills section and within experience bullets (only if true)."})
    else:
        if keyword_score < 45:
            weaknesses.append({"title": "Few technical keywords", "fix": "Add a Skills section (tech, tools, protocols) using common ATS keywords for your target role."})

    if impact_score < 45:
        weaknesses.append({"title": "Not enough quantified impact", "fix": "Add numbers: % improvement, time saved, volumes handled, number of devices, etc."})

    if length_score < 55:
        if wc < 300:
            weaknesses.append({"title": "CV is too short", "fix": "Add projects, missions, technologies used, and concrete responsibilities."})
        else:
            weaknesses.append({"title": "CV is too long", "fix": "Aim for 1–2 pages, remove less relevant items, keep what matches the role."})

    for f in flags:
        weaknesses.append({"title": "ATS readability", "fix": f})

    missing_preview = missing_kw[:18]
    matched_preview = matched_kw[:18]

    return {
        "score": total_score,
        "breakdown": breakdown.__dict__,
        "word_count": wc,
        "contacts": contacts,
        "sections": sections,
        "language": {
            "selected": cv_lang,
            "detected": detected,
            "used": lang,
            "job_detected": job_lang if job_text.strip() else None,
        },
        "keywords": {
            "used": keywords[:40],
            "matched": matched_preview,
            "missing": missing_preview,
            "match_ratio": round(kw_ratio, 3),
        },
        "similarity": round(sim, 3),
        "impact": {
            "count": impact_count,
            "samples": impact_samples,
        },
        "readability_flags": flags,
        "weaknesses": weaknesses,
    }
