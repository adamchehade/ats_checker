import re
from typing import List, Tuple, Set

from .lang import STOPWORDS

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"(?:(?:\+|00)\s?\d{1,3}[\s.-]?)?(?:\(?\d{1,4}\)?[\s.-]?){2,6}\d{1,4}")
URL_RE = re.compile(r"\bhttps?://[^\s)]+|\bwww\.[^\s)]+", re.IGNORECASE)

def normalize_spaces(text: str) -> str:
    text = text.replace("\u00A0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def find_contacts(text: str) -> dict:
    emails = sorted(set(EMAIL_RE.findall(text)))
    phones = sorted(set([p.strip() for p in PHONE_RE.findall(text) if len(re.sub(r"\D","",p)) >= 8]))
    urls = sorted(set(URL_RE.findall(text)))
    linkedin = [u for u in urls if "linkedin.com" in u.lower()]
    github = [u for u in urls if "github.com" in u.lower()]
    return {
        "emails": emails,
        "phones": phones,
        "urls": urls,
        "linkedin": linkedin,
        "github": github,
    }

def has_numbers_impact(text: str) -> Tuple[int, List[str]]:
    patterns = [
        r"\b\d{1,3}\s?%\b",
        r"\b\d+(?:[.,]\d+)?\s?(?:k|K|M|m)?\b",
        r"\b\d+\s?(?:ans|mois|semaines|jours|years|months|weeks|days)\b",
    ]
    hits = []
    for pat in patterns:
        hits += re.findall(pat, text, flags=re.IGNORECASE)
    hits = list(dict.fromkeys([h.strip() for h in hits]))
    return len(hits), hits[:15]

def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text, flags=re.UNICODE))

def tokenize_simple(text: str) -> List[str]:
    words = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9+#.\-]{2,}", text, flags=re.UNICODE)
    return [w.lower() for w in words]

def remove_stopwords(tokens: List[str], lang: str = "en") -> List[str]:
    sw = STOPWORDS.get(lang, STOPWORDS.get("en", set()))
    out: List[str] = []
    for t in tokens:
        if t in sw:
            continue
        if re.fullmatch(r"\d+", t):
            continue
        out.append(t)
    return out

def unique_preserve(seq: List[str]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out

def soft_contains(text: str, term: str) -> bool:
    t = re.sub(r"\s+", " ", text.lower())
    s = re.sub(r"\s+", " ", term.lower()).strip()
    return s in t
