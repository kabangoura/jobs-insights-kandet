"""Tests hors ligne des annonces semblables (semblables.py) et de leur affichage dans offres.html."""

import unittest

from interface import build_html, count_text
from main import describe_changes
from semblables import republished, similar_groups
from test_interface import embedded_rows, offer


def annonce(number: int, title: str = "Bilingual Mortgage Operations Specialist", employer: str = "Recrute Action",
            city: str = "Montréal", new: bool = False, site: str = "Talent.com"):
    item = offer(number, original_title=title, employer=employer, city=city, new_since_previous=new)
    item.source_records[0].origin_site = site
    return item


class GroupTests(unittest.TestCase):
    def test_same_post_published_three_times(self) -> None:
        # Cas réel du 24 novembre : deux annonces à Montréal, une à Laval.
        offers = [annonce(1), annonce(2), annonce(3, city="Laval"), annonce(4, title="Autre poste")]
        self.assertEqual(similar_groups(offers), [0, 0, 0, 3])

    def test_accents_case_and_punctuation_do_not_matter(self) -> None:
        offers = [annonce(1, title="Analyste TI – Développeur QA", employer="Ville de Québec"),
                  annonce(2, title="analyste ti ? developpeur qa", employer="VILLE DE QUEBEC")]
        self.assertEqual(similar_groups(offers), [0, 0])

    def test_other_employer_or_other_site_stays_apart(self) -> None:
        offers = [annonce(1), annonce(2, employer="Autre agence"), annonce(3, site="Jobillico")]
        self.assertEqual(similar_groups(offers), [0, 1, 2])

    def test_missing_employer_is_never_grouped(self) -> None:
        offers = [annonce(1, employer=""), annonce(2, employer="")]
        self.assertEqual(similar_groups(offers), [0, 1])

    def test_republished_post_is_not_new(self) -> None:
        # La Ville de Québec republie un poste déjà en ligne à la collecte précédente.
        offers = [annonce(1, new=True), annonce(2, new=False), annonce(3, title="Vrai nouveau poste", new=True)]
        self.assertEqual(republished(offers), [True, False, False])

    def test_three_new_announcements_are_not_republished(self) -> None:
        offers = [annonce(1, new=True), annonce(2, new=True), annonce(3, city="Laval", new=True)]
        self.assertEqual(republished(offers), [False, False, False])


class PageTests(unittest.TestCase):
    def test_rows_carry_group_and_republished_flag(self) -> None:
        offers = [annonce(1, new=True), annonce(2), annonce(3, title="Autre poste")]
        rows = embedded_rows(build_html(offers, generated_on="2026-11-24"))
        self.assertEqual([row["groupe"] for row in rows], [1, 1, 3])
        self.assertEqual([row["republiee"] for row in rows], [True, False, False])

    def test_header_counts_posts_and_announcements(self) -> None:
        page = build_html([annonce(1), annonce(2), annonce(3, title="Autre poste")], generated_on="2026-11-24")
        self.assertIn("2 offres (3 annonces) · collecte du 24 novembre 2026", page)
        self.assertEqual(count_text(1, 1), "1 offre")
        self.assertEqual(count_text(5, 5), "5 offres")

    def test_new_offers_text_counts_like_the_page(self) -> None:
        offers = [annonce(1, new=True), annonce(2, new=True), annonce(3, city="Laval", new=True),  # 1 offre nouvelle
                  annonce(4, title="Technicien", new=True), annonce(5, title="Technicien"),     # republiée
                  annonce(6, title="Ancien poste")]
        self.assertEqual(describe_changes(offers, "2026-11-23"),
                         " · 1 nouvelle offre depuis la collecte du 23 novembre 2026 (et 1 annonce republiée)")


if __name__ == "__main__":
    unittest.main()
