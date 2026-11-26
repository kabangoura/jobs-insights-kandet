"""Autres sources autorisées : Jobicy et les pages carrières d'employeurs (Greenhouse, Lever).

Vérifié le 25 novembre 2026 (robots.txt et conditions d'utilisation) :
- Jobicy (API publique d'emplois à distance) : « You may use Jobicy listings in your own
  products [...] without requesting individual permission ». Il faut citer Jobicy avec un
  lien vers l'offre sur Jobicy, faire au plus 1 requête par seconde et un passage par heure.
- Lever : « all job postings in the published state are publicly viewable. These jobs may
  be scraped by third parties. »
- Greenhouse : API publique sans clé pour lire les offres, aucune interdiction trouvée, et le
  robots.txt la permet. La source (l'employeur) est citée avec le lien vers son offre.

Écartés : Jobboom, Jobillico, Talent.com, Himalayas en masse (conditions), Indeed, Monster,
Workopolis, CareerBeacon (403), SmartRecruiters (robots.txt). Voir la note du livrable 3.

Chaque réponse est gardée une heure dans le cache : relancer la collecte (ou cliquer sur
« Mettre à jour ») plusieurs fois de suite ne refait pas les appels.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
import time
from typing import Callable

from analyse import classify_stage
from collecte import fetch_url
from modele import SourceRecord
from texte import normalize, plain_text

JOBICY_URL = "https://jobicy.com/api/v2/remote-jobs?count=100&geo=canada"
GREENHOUSE_URL = "https://boards-api.greenhouse.io/v1/boards/{jeton}/jobs?content=true"
LEVER_URL = "https://api.lever.co/v0/postings/{jeton}?mode=json"
EMPLOYERS_FILE = Path(__file__).with_name("pages_carrieres.json")
CACHE_SECONDS = 3600  # Jobicy : « no more than once per hour »
DELAY_SECONDS = 1.5  # Jobicy : au plus 1 requête par seconde

# Secteurs Jobicy liés à l'informatique (essai du 25 novembre 2026).
JOBICY_IT_INDUSTRIES = {"software engineering", "data science & analytics", "devops & infrastructure",
                        "technical support", "cybersecurity", "qa & testing"}
# Pages carrières : les employeurs ont aussi des postes hors TI (ventes, RH...). On garde un
# titre qui parle d'informatique.
IT_TITLE = re.compile(
    # Débuts de mots (« developpeur.euse », « architecture », « infonuagique »)...
    r"\b(?:develop|programm|engineer|ingenieur|software|logiciel|donnee|devops|devsecops|cloud|infonuagi|cyber|"
    r"analyse d.affaires|business analyst|"
    r"securit|qualit|test|analyst|architect|technicien|technician|informati|full[- ]?stack|front[- ]?end|"
    r"back[- ]?end|machine learning|infrastructure|reseau|network|system|administrat|servicenow|salesforce|"
    r"etl|bureautique|intelligence artificielle|scrum|product owner)"
    # ... et mots courts entiers (« IT », « TI », « QA », « IA »...).
    r"|\b(?:it|ti|qa|sre|ux|ui|ai|ia|ml|web|mobile|data|support|soutien)\b"
)
QUEBEC_WORDS = ("quebec", "montreal", "laval", "sherbrooke", "gatineau", "levis", "trois-rivieres",
                "saguenay", "longueuil", "brossard", ", qc", "(qc)", " qc,")
CANADA_WORDS = QUEBEC_WORDS + ("canada", "toronto", "ottawa", "vancouver", "calgary", "remote - ca")


def _cached_json(url: str, cache_dir: Path, fetch: Callable[[str, str], bytes], now: float) -> object:
    """Réponse JSON, réutilisée pendant une heure."""
    name = re.sub(r"[^a-z0-9]+", "-", url.lower()).strip("-")[:120] + ".json"
    path = cache_dir / name
    if path.exists():
        cached = json.loads(path.read_text(encoding="utf-8"))
        if 0 <= now - cached.get("fetched", 0) < CACHE_SECONDS:
            return cached["payload"]
    payload = json.loads(fetch(url, "application/json"))
    cache_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"fetched": now, "url": url, "payload": payload}, ensure_ascii=False), encoding="utf-8")
    return payload


def place(location: str) -> tuple[str, str]:
    """(ville, province) à partir de « Montréal, Québec, Canada », « Quebec City, QC »... Rien n'est deviné."""
    text = normalize(location)
    if not any(word in text for word in QUEBEC_WORDS):
        return "", ""
    first = re.split(r"[,;/|(]", location)[0].strip()
    first = re.sub(r"(?i)^(?:remote|hybrid|hybride|télétravail)\s*[-–:]\s*", "", first).strip()
    key = normalize(first)
    if key in ("quebec city", "ville de quebec"):
        return "Québec", "QC"
    if key in ("quebec", "qc", "canada", "remote", "hybrid", "hybride", ""):
        return "", "QC"  # « Québec » seul peut être la province : la ville reste vide
    return first, "QC"


# Fourchette de salaire écrite dans la description (essai du 26 novembre 2026 : 20 offres sur 181,
# toujours après « Estimated salary range », « Base salary », « Salaire de base », « Échelle salariale »...).
_AMOUNT = r"(?:(?:CA|US|C)?\$\s?\d{2,3}(?:[  ,.]\d{3})+|\d{2,3}(?:[  ,.]\d{3})+\s?\$)"
SALARY_RANGE = re.compile(_AMOUNT + r"\s*(?:CAD|USD)?\s*(?:-|–|—|to|à|and|et)\s*" + _AMOUNT + r"\s*(?:CAD|USD)?", re.IGNORECASE)
SALARY_WORDS = re.compile(r"salary|salaire|salariale|remuneration|compensation|pay range|base pay|traitement", re.IGNORECASE)
MIN_ANNUAL = 20_000  # deux montants d'au moins 20 000 $ : un salaire annuel (pas un taux horaire)


def salary_from_text(description: str) -> tuple[str, str]:
    """(texte du salaire avec son unité, devise) ou (« », « »). La devise n'est gardée que si elle est écrite."""
    from normalisation import parse_salary_text

    for match in SALARY_RANGE.finditer(description):
        before = normalize(description[max(0, match.start() - 150):match.start()])
        if not SALARY_WORDS.search(before):
            continue  # un montant sans mot « salaire » juste avant : peut-être autre chose
        text = " ".join(match.group(0).split())
        low, high, _ = parse_salary_text(text)
        if low is None or high is None or min(low, high) < MIN_ANNUAL:
            continue
        currency = "USD" if "usd" in text.lower() or "us$" in text.lower() else "CAD" if "cad" in text.lower() or "ca$" in text.lower() else ""
        return f"{text} par année", currency
    return "", ""


def _record(source: str, origin: str, source_id: str, url: str, title: str, employer: str, location: str,
            published: str, description: str, job_type: str = "", category: str = "", remote: bool = False,
            raw: dict | None = None, mode: str = "") -> SourceRecord:
    stage_status, stage_signals = classify_stage(title, job_type, description)
    city, province = place(location)
    salary, currency = salary_from_text(description)
    return SourceRecord(
        salary=salary, salary_currency=currency,
        source=source, source_id=source_id, url=url, title=title, origin_site=origin, employer=employer,
        location=location, published_at=published, work_mode=mode or ("Télétravail" if remote else ""),
        job_type=job_type, category=category, description=description, city=city, province=province,
        stage_status=stage_status, stage_signals=stage_signals, source_data=raw or {},
    )


def parse_jobicy(payload: dict) -> list[SourceRecord]:
    records = []
    for job in payload.get("jobs") or []:
        industries = [str(name) for name in job.get("jobIndustry") or []]
        if not {normalize(name) for name in industries} & JOBICY_IT_INDUSTRIES:
            continue
        job_type = ", ".join(str(t) for t in job.get("jobType") or [])
        records.append(_record(
            "Jobicy", "Jobicy", str(job.get("id") or job.get("url")), str(job.get("url") or ""),
            str(job.get("jobTitle") or ""), str(job.get("companyName") or ""), str(job.get("jobGeo") or ""),
            str(job.get("pubDate") or "")[:10], plain_text(str(job.get("jobDescription") or "")), job_type,
            ", ".join(industries), remote=True,
            raw={key: job.get(key) for key in ("jobLevel", "jobGeo", "jobIndustry", "annualSalaryMin",
                                               "annualSalaryMax", "salaryCurrency")},
        ))
    return records


def _keep(title: str, location: str) -> bool:
    return bool(IT_TITLE.search(normalize(title))) and any(word in normalize(location) for word in CANADA_WORDS)


def parse_greenhouse(payload: dict, employer: str) -> list[SourceRecord]:
    records = []
    for job in payload.get("jobs") or []:
        title, location = str(job.get("title") or ""), str((job.get("location") or {}).get("name") or "")
        if not _keep(title, location):
            continue
        # « content » est du HTML échappé (&lt;p&gt;...) : plain_text le décode deux fois.
        description = plain_text(plain_text(str(job.get("content") or "")))
        records.append(_record(
            "Greenhouse", employer, str(job.get("id")), str(job.get("absolute_url") or ""), title, employer,
            location, str(job.get("first_published") or job.get("updated_at") or "")[:10], description,
            remote="remote" in normalize(location) or "teletravail" in normalize(location),
        ))
    return records


def parse_lever(payload: list, employer: str) -> list[SourceRecord]:
    records = []
    for job in payload or []:
        categories = job.get("categories") or {}
        title, location = str(job.get("text") or ""), str(categories.get("location") or "")
        if not _keep(title, location):
            continue
        created = job.get("createdAt")
        published = datetime.fromtimestamp(created / 1000, timezone.utc).date().isoformat() if isinstance(created, (int, float)) else ""
        parts = [str(job.get("descriptionPlain") or "")]
        parts += [f"{item.get('text', '')} : {plain_text(str(item.get('content', '')))}" for item in job.get("lists") or []]
        records.append(_record(
            "Lever", employer, str(job.get("id")), str(job.get("hostedUrl") or ""), title, employer, location,
            published, " ".join(part for part in parts if part).strip(), str(categories.get("commitment") or ""),
            str(categories.get("team") or ""),
            remote="remote" in normalize(location),
            mode={"remote": "Télétravail", "hybrid": "Hybride", "onsite": "Sur place"}.get(str(job.get("workplaceType") or ""), ""),
        ))
    return records


def collect_other_sources(cache_dir: Path, fetch: Callable[[str, str], bytes] = fetch_url,
                          sleep: Callable[[float], None] = time.sleep, employers_file: Path = EMPLOYERS_FILE,
                          log: Callable[[str], None] = print) -> tuple[list[SourceRecord], list[str], dict[str, int]]:
    """Toutes les autres sources. Une source en erreur n'arrête pas les autres."""
    records: list[SourceRecord] = []
    errors: list[str] = []
    counts: dict[str, int] = {}
    now = time.time()
    calls = 0

    def get(url: str) -> object:
        nonlocal calls
        if calls:
            sleep(DELAY_SECONDS)
        calls += 1
        return _cached_json(url, cache_dir, fetch, now)

    try:
        found = parse_jobicy(get(JOBICY_URL))  # type: ignore[arg-type]
        records += found
        counts["Jobicy"] = len(found)
    except (OSError, ValueError) as error:
        errors.append(f"Jobicy : {error}")

    employers = json.loads(employers_file.read_text(encoding="utf-8"))["employeurs"]
    for employer in employers:
        name, platform, token = employer["employeur"], employer["plateforme"], employer["jeton"]
        try:
            if platform == "greenhouse":
                found = parse_greenhouse(get(GREENHOUSE_URL.format(jeton=token)), name)  # type: ignore[arg-type]
            elif platform == "lever":
                found = parse_lever(get(LEVER_URL.format(jeton=token)), name)  # type: ignore[arg-type]
            else:
                raise ValueError(f"plateforme inconnue « {platform} »")
            records += found
            counts[name] = len(found)
        except (OSError, ValueError, KeyError, TypeError) as error:
            errors.append(f"{name} ({platform}) : {error}")
    log(f"Autres sources : {len(records)} offres TI ({', '.join(f'{k} {v}' for k, v in counts.items() if v)})")
    return records, errors, counts
