"""Score « étudiant du DEC » : à quel point une offre convient à un étudiant en fin de DEC.

Le score est sur 100 et chaque point est expliqué :
- stage confirmé dans l'offre : 40 (stage possible : 20) ;
- niveau débutant : 30 (non précisé : 15, intermédiaire : 10, avancé : 0) ;
- technologies vues au DEC : jusqu'à 30, selon la part des technologies de l'offre
  qui sont dans le programme. On compte au moins 3 technologies : une offre qui ne
  cite que « Windows » reçoit 10 points, pas 30.

La liste des technologies du programme est dans programme_dec.json, avec le lien vers
la liste officielle des cours. Rien n'est deviné : une offre sans technologie écrite
reçoit 0 point pour ce critère, et le programme le dit.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path

from modele import AggregatedOffer

PROGRAM_FILE = Path(__file__).with_name("programme_dec.json")
STAGE_POINTS = {"confirmed_stage": 40, "possible_stage": 20}
LEVEL_POINTS = {"débutant": 30, "intermédiaire": 10, "avancé": 0}
UNKNOWN_LEVEL_POINTS = 15
TECHNOLOGY_POINTS = 30
MIN_TECHNOLOGIES_COUNTED = 3


@dataclass
class DecScore:
    total: int
    parts: list[str] = field(default_factory=list)  # explications, dans l'ordre des critères
    seen: list[str] = field(default_factory=list)  # technologies de l'offre vues au DEC


def load_program(path: Path = PROGRAM_FILE) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def dec_score(offer: AggregatedOffer, program_technologies: list[str] | set[str]) -> DecScore:
    known = set(program_technologies)
    parts = []

    stage = STAGE_POINTS.get(offer.stage_status, 0)
    if stage:
        parts.append(f"{'stage confirmé' if stage == 40 else 'stage possible'} (+{stage})")

    level = LEVEL_POINTS.get(offer.level, UNKNOWN_LEVEL_POINTS)
    parts.append(f"niveau {offer.level or 'non précisé'} (+{level})")

    seen = [name for name in offer.technologies if name in known]
    if offer.technologies:
        technology = round(TECHNOLOGY_POINTS * len(seen) / max(MIN_TECHNOLOGIES_COUNTED, len(offer.technologies)))
        listed = f" : {', '.join(seen)}" if seen else ""
        parts.append(f"{len(seen)} technologie{'s' if len(seen) > 1 else ''} sur {len(offer.technologies)} vue{'s' if len(seen) > 1 else ''} au DEC{listed} (+{technology})")
    else:
        technology = 0
        parts.append("pas de technologie indiquée dans l'offre (+0)")

    return DecScore(stage + level + technology, parts, seen)
