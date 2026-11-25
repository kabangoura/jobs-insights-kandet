"""Résumé des nouvelles offres depuis la collecte précédente (option --nouveautes).

Essai du 24 novembre 2026 : 14 nouvelles offres. Classées seulement avec un CV,
le stage de Revenu Québec n'apparaissait pas (il ne cite aucune technologie). Le
résumé a donc trois parties :
1. les nouveaux stages, toujours montrés en premier ;
2. les offres les plus proches du CV, si un CV est donné (candidature.py) ;
3. les autres nouvelles offres, classées par score « étudiant du DEC » (score_dec.py).

Une annonce republiée n'est pas une nouvelle offre, et les annonces semblables
comptent pour une seule (semblables.py), comme dans la page.
"""

from __future__ import annotations

from modele import AggregatedOffer
from score_dec import dec_score
from semblables import republished, similar_groups
from texte import french_date

MIN_CV_SCORE = 40  # en dessous, l'offre va dans « les autres nouvelles offres »


def new_offers(offers: list[AggregatedOffer]) -> list[AggregatedOffer]:
    """Une offre par poste, seulement les vraies nouveautés (pas les republications)."""
    groups = similar_groups(offers)
    again = republished(offers, groups)
    found, seen = [], set()
    for index, offer in enumerate(offers):
        if offer.new_since_previous and not again[index] and groups[index] not in seen:
            seen.add(groups[index])
            found.append(offer)
    return found


def _line(offer: AggregatedOffer, detail: str) -> list[str]:
    title = offer.original_title or offer.title
    place = offer.city or offer.location or "lieu non précisé"
    link = offer.source_records[0].url if offer.source_records else ""
    lines = [f"- **{title}** ({offer.employer or 'employeur non précisé'}, {place})"]
    lines.append(f"  {detail}")
    if link:
        lines.append(f"  {link}")
    return lines


def build_summary(offers: list[AggregatedOffer], previous_date: str | None, program_technologies: list[str],
                  profile=None, cv_name: str = "", top: int = 5) -> str:
    """Le résumé en Markdown (affiché dans le terminal et enregistré dans rapport-nouveautes.md)."""
    if not previous_date:
        return "Nouveautés : pas de collecte précédente à comparer. Le résumé sera possible après la prochaine collecte.\n"
    news = new_offers(offers)
    lines = [f"# Nouvelles offres depuis la collecte du {french_date(previous_date[:10])}", ""]
    if not news:
        lines.append("Aucune nouvelle offre.")
        return "\n".join(lines) + "\n"
    stages = [offer for offer in news if offer.stage_status in ("confirmed_stage", "possible_stage")]
    lines.append(f"{len(news)} nouvelle{'s' if len(news) > 1 else ''} offre{'s' if len(news) > 1 else ''}"
                 f", dont {len(stages)} stage{'s' if len(stages) > 1 else ''}.")
    shown = set()

    lines += ["", "## Nouveaux stages", ""]
    if stages:
        for offer in stages:
            shown.add(id(offer))
            kind = "stage confirmé" if offer.stage_status == "confirmed_stage" else "stage possible"
            lines += _line(offer, f"{kind} · score DEC {dec_score(offer, program_technologies).total}/100")
    else:
        lines.append("Aucun nouveau stage.")

    if profile is not None:
        from candidature import rank_offers

        matches, _ = rank_offers(profile, news)
        close = [match for match in matches if match.score >= MIN_CV_SCORE and id(match.offer) not in shown]
        lines += ["", f"## Les plus proches du CV {cv_name}".rstrip(), ""]
        if close:
            for match in close[:top]:
                shown.add(id(match.offer))
                shared = ", ".join(match.shared_technologies) or "aucune technologie en commun"
                lines += _line(match.offer, f"note {match.score}/100 avec le CV · en commun : {shared}")
        else:
            lines.append(f"Aucune nouvelle offre avec une note d'au moins {MIN_CV_SCORE}/100.")

    others = sorted((offer for offer in news if id(offer) not in shown),
                    key=lambda offer: (-dec_score(offer, program_technologies).total, offer.title))
    if others:
        lines += ["", "## Les autres nouvelles offres (score « étudiant du DEC »)", ""]
        for offer in others[:top]:
            score = dec_score(offer, program_technologies)
            lines += _line(offer, f"score DEC {score.total}/100 · {' · '.join(score.parts)}")
        if len(others) > top:
            lines.append(f"\nEt {len(others) - top} autre{'s' if len(others) - top > 1 else ''} : "
                         "case « Nouvelles offres seulement » dans offres.html.")
    return "\n".join(lines) + "\n"
