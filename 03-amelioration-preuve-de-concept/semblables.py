"""Annonces semblables : le même poste publié plusieurs fois par le même employeur.

Exemple réel (collecte du 24 novembre 2026) : Recrute Action a publié trois fois
« Bilingual Mortgage Operations Specialist » sur Talent.com, deux fois à Montréal
et une fois à Laval. Ce sont trois annonces différentes pour le Guichet-Emplois
(trois numéros), donc fusion.py les garde séparées. Ce module ne supprime rien :
il dit seulement quelles annonces vont ensemble, pour les montrer sur une seule
carte dans offres.html.

Règle : même titre, même employeur et même site de publication (sans accents ni
majuscules). Un employeur peut avoir plusieurs postes identiques à pourvoir : c'est
pourquoi toutes les annonces restent visibles, avec leur ville, leur date et leur lien.
"""

from __future__ import annotations

import re

from modele import AggregatedOffer
from texte import normalize


def _key(offer: AggregatedOffer) -> tuple[str, str, str] | None:
    title = re.sub(r"\W+", " ", normalize(offer.original_title or offer.title)).strip()
    employer = re.sub(r"\W+", " ", normalize(offer.employer)).strip()
    if not title or not employer:
        return None  # sans titre ou sans employeur, on ne peut rien affirmer
    first = offer.source_records[0] if offer.source_records else None
    site = normalize((first.origin_site or first.source) if first else "")
    return title, employer, site


def similar_groups(offers: list[AggregatedOffer]) -> list[int]:
    """Pour chaque offre, l'indice de la première offre de son groupe (elle-même si elle est seule)."""
    first_index: dict[tuple[str, str, str], int] = {}
    groups = []
    for index, offer in enumerate(offers):
        key = _key(offer)
        if key is None:
            groups.append(index)
        else:
            groups.append(first_index.setdefault(key, index))
    return groups


def republished(offers: list[AggregatedOffer], groups: list[int] | None = None) -> list[bool]:
    """Vrai pour une annonce « nouvelle » dont le même poste était déjà en ligne à la collecte précédente.

    Exemple réel : la Ville de Québec a republié le 23 novembre un poste de technicien
    déjà publié le 11 novembre. Ce n'est pas vraiment une nouvelle offre.
    """
    groups = groups if groups is not None else similar_groups(offers)
    already_online = {groups[i] for i, offer in enumerate(offers) if not offer.new_since_previous}
    return [offer.new_since_previous and groups[i] in already_online for i, offer in enumerate(offers)]
