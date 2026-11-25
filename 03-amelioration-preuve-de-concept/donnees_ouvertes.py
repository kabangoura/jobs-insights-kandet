"""Tendance des offres TI au Québec, mois par mois, avec les données ouvertes du Guichet-Emplois.

Source : jeu de données « Offres d'emploi publiées sur le site du Guichet-Emplois »
d'Emploi et Développement social Canada, sur open.canada.ca, sous la Licence du
gouvernement ouvert – Canada. Un fichier CSV par mois (environ 60 Mo, UTF-16, tabulations).

Ces fichiers n'ont ni employeur, ni description, ni lien vers l'offre : ils servent
seulement aux statistiques. Chaque fichier est lu en continu, sans être enregistré ;
on ne garde qu'un petit résumé par mois dans donnees-ouvertes.json. Un mois déjà
résumé n'est pas retéléchargé.

On garde les offres du Québec avec les 14 codes CNP 2021 de la collecte (guichet.py).
Une offre mal classée par le Guichet-Emplois (ex. « Work From Home Sales Consultant »
avec un code TI) est comptée telle quelle : on ne corrige pas la source.
"""

from __future__ import annotations

import codecs
import csv
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import time
from typing import Callable, Iterable, Iterator
from urllib.request import Request, urlopen

from collecte import USER_AGENT
from guichet import CNP_CODES_TI
from regions import region_of

PACKAGE_ID = "ea639e28-c0fc-48bf-b5dd-b8899bd43072"
PACKAGE_URL = f"https://open.canada.ca/data/api/action/package_show?id={PACKAGE_ID}"
DATASET_PAGE = f"https://open.canada.ca/data/fr/dataset/{PACKAGE_ID}"
LICENCE = "Licence du gouvernement ouvert – Canada"
LICENCE_URL = "https://ouvert.canada.ca/fr/licence-du-gouvernement-ouvert-canada"
ATTRIBUTION = "Contient des informations visées par la Licence du gouvernement ouvert – Canada."
DELAY_SECONDS = 5  # entre deux fichiers, par politesse
DEFAULT_MONTHS = 12
MONTHS_EN = {name: number for number, name in enumerate(
    ["January", "February", "March", "April", "May", "June", "July", "August",
     "September", "October", "November", "December"], start=1)}


def monthly_files(package: dict) -> list[tuple[str, str]]:
    """[(« 2026-10 », url du CSV français), …], du plus récent au plus ancien.

    Le mois est lu dans le nom de la ressource (« October 2026 Job Postings… ») :
    les noms de fichiers, eux, changent d'un mois à l'autre (oct2026, octobre2023, june-2024…).
    """
    found = {}
    for resource in package["result"]["resources"]:
        if "fr" not in (resource.get("language") or []) or (resource.get("format") or "").upper() != "CSV":
            continue
        if not resource.get("url"):
            continue  # vu le 24 novembre 2026 : avril 2026 n'a pas d'adresse pour le fichier français
        words = (resource.get("name") or "").split()
        if len(words) >= 2 and words[0] in MONTHS_EN and words[1].isdigit():
            found[f"{words[1]}-{MONTHS_EN[words[0]]:02d}"] = resource["url"]
    return sorted(found.items(), reverse=True)


def _number(value: str) -> float | None:
    try:
        return float(value.replace(",", "."))
    except (AttributeError, ValueError):
        return None  # « NA » : information absente, jamais devinée


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    middle = len(ordered) // 2
    value = ordered[middle] if len(ordered) % 2 else (ordered[middle - 1] + ordered[middle]) / 2
    return round(value, 2)


def summarize(rows: Iterable[dict[str, str]]) -> dict[str, object]:
    """Résumé d'un mois : offres TI du Québec, postes, régions, professions, salaires médians."""
    codes = set(CNP_CODES_TI)
    offers = vacancies = external = 0
    regions: dict[str, int] = {}
    professions: dict[str, int] = {}
    salaries: dict[str, list[float]] = {"Année": [], "Heure": []}
    for row in rows:
        if row.get("Provinces/Territoires") != "Québec":
            continue
        if (row.get("Code CNP 2021") or "").split(".")[0].zfill(5) not in codes:
            continue
        offers += 1
        vacancies += int(_number(row.get("Nombre de postes vacants", "")) or 1)
        external += row.get("Indicateur Source Externe") == "1"
        region = region_of(row.get("Ville", "")) or "Non précisé"
        regions[region] = regions.get(region, 0) + 1
        name = row.get("Code CNP21 nom") or "Non précisé"
        professions[name] = professions.get(name, 0) + 1
        unit, low = row.get("Salaire par"), _number(row.get("Salaire Minimum", ""))
        if unit in salaries and low:
            salaries[unit].append(low)
    by_count = lambda counts: dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))
    return {
        "offres": offers,
        "postes": vacancies,
        "sources_externes": external,
        "salaire_annuel": {"offres": len(salaries["Année"]), "mediane": _median(salaries["Année"])},
        "salaire_horaire": {"offres": len(salaries["Heure"]), "mediane": _median(salaries["Heure"])},
        "regions": by_count(regions),
        "professions": by_count(professions),
    }


def read_csv_stream(binary: io.BufferedIOBase) -> Iterator[dict[str, str]]:
    """Lit un CSV du Guichet-Emplois (UTF-16, tabulations) sans le charger en entier."""
    text = codecs.getreader("utf-16")(binary)
    return csv.DictReader(text, delimiter="\t")


def _open_url(url: str):
    return urlopen(Request(url, headers={"User-Agent": USER_AGENT}), timeout=120)


def load_summary(path: Path) -> dict[str, object]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def update(path: Path, months: int = DEFAULT_MONTHS,
           get_package: Callable[[], dict] | None = None,
           open_url: Callable[[str], object] = _open_url,
           sleep: Callable[[float], None] = time.sleep,
           log: Callable[[str], None] = print) -> dict[str, object]:
    """Ajoute à donnees-ouvertes.json les mois qui manquent parmi les `months` plus récents."""
    if get_package is None:
        def get_package() -> dict:
            with open_url(PACKAGE_URL) as response:
                return json.loads(response.read().decode("utf-8"))
    document = load_summary(path)
    summaries: dict[str, object] = dict(document.get("mois", {}))
    wanted = monthly_files(get_package())[:months]
    missing = [(month, url) for month, url in wanted if month not in summaries]
    log(f"Données ouvertes : {len(wanted)} mois voulus, {len(wanted) - len(missing)} déjà résumés, {len(missing)} à lire.")
    for index, (month, url) in enumerate(missing):
        if index:
            sleep(DELAY_SECONDS)
        log(f"  lecture de {month} (environ 60 Mo, lu en continu)…")
        try:
            with open_url(url) as response:
                summaries[month] = summarize(read_csv_stream(response))
        except (OSError, ValueError, csv.Error, UnicodeError) as error:
            # Un mois illisible n'arrête pas les autres ; il sera réessayé au prochain lancement.
            log(f"  {month} : non lu ({error}). Il sera réessayé la prochaine fois.")
            continue
        log(f"  {month} : {summaries[month]['offres']} offres TI au Québec")
        # Enregistré après chaque mois : une coupure ne fait pas tout perdre.
        _write(path, summaries)
    return _write(path, summaries)


def _write(path: Path, summaries: dict[str, object]) -> dict[str, object]:
    document = {
        "source": "Offres d'emploi publiées sur le site du Guichet-Emplois (Emploi et Développement social Canada)",
        "page": DATASET_PAGE,
        "licence": LICENCE,
        "licence_url": LICENCE_URL,
        "attribution": ATTRIBUTION,
        "filtre": "Québec, 14 codes CNP 2021 des TI (comme la collecte)",
        "mis_a_jour": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mois": dict(sorted(summaries.items())),
    }
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
    return document


def trend_for_page(document: dict[str, object], months: int = DEFAULT_MONTHS) -> list[dict[str, object]]:
    """Les `months` derniers mois, du plus ancien au plus récent, pour l'onglet Statistiques."""
    summaries = document.get("mois", {}) if document else {}
    return [{"mois": month, **summaries[month]} for month in sorted(summaries)[-months:]]
