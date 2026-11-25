"""Tests hors ligne du score « étudiant du DEC » (score_dec.py et programme_dec.json)."""

import unittest

from competences import TECHNOLOGY_PATTERNS, find_technologies
from interface import build_html
from score_dec import dec_score, load_program
from test_interface import embedded_rows, offer

PROGRAM = load_program()


class ScoreTests(unittest.TestCase):
    def test_internship_for_a_beginner_without_technology(self) -> None:
        # Cas réel du 24 novembre : le stage de Revenu Québec ne cite aucune technologie.
        score = dec_score(offer(1, stage_status="confirmed_stage", level="débutant"), PROGRAM["technologies"])
        self.assertEqual(score.total, 70)
        self.assertEqual(score.parts, ["stage confirmé (+40)", "niveau débutant (+30)",
                                       "pas de technologie indiquée dans l'offre (+0)"])

    def test_beginner_job_with_technologies_seen_at_the_dec(self) -> None:
        score = dec_score(offer(1, level="débutant", technologies=["Java", "HTML/CSS", "Angular"]), PROGRAM["technologies"])
        self.assertEqual(score.total, 60)
        self.assertEqual(score.parts[-1], "3 technologies sur 3 vues au DEC : Java, HTML/CSS, Angular (+30)")

    def test_one_technology_alone_does_not_give_all_points(self) -> None:
        # On compte au moins 3 technologies : « Windows » seul vaut 10 points, pas 30.
        score = dec_score(offer(1, level="intermédiaire", technologies=["Windows"]), PROGRAM["technologies"])
        self.assertEqual(score.total, 20)
        self.assertEqual(score.parts[-1], "1 technologie sur 1 vue au DEC : Windows (+10)")

    def test_technologies_not_seen_and_senior_level(self) -> None:
        score = dec_score(offer(1, level="avancé", technologies=["Go", "Kubernetes", "Terraform", "Java"]), PROGRAM["technologies"])
        self.assertEqual(score.total, 8)  # 0 (avancé) + 30 × 1/4 arrondi
        self.assertEqual(score.seen, ["Java"])

    def test_unknown_level_and_possible_internship(self) -> None:
        score = dec_score(offer(1, stage_status="possible_stage", level=""), PROGRAM["technologies"])
        self.assertEqual(score.total, 35)
        self.assertEqual(score.parts[:2], ["stage possible (+20)", "niveau non précisé (+15)"])


class ProgramTests(unittest.TestCase):
    def test_program_file_has_its_source(self) -> None:
        self.assertIn("O'Sullivan de Québec", PROGRAM["nom"])
        self.assertTrue(PROGRAM["source"].startswith("https://osullivan-quebec.qc.ca/"))

    def test_every_program_technology_can_be_found_in_offers(self) -> None:
        # Sinon le score ne pourrait jamais la compter.
        known = {name for name, _ in TECHNOLOGY_PATTERNS}
        self.assertEqual([name for name in PROGRAM["technologies"] if name not in known], [])

    def test_new_technologies_from_the_program(self) -> None:
        text = "Maîtrise de jQuery, échanges XML et services SOAP. Savon (soap) non requis."
        self.assertEqual([t for t in find_technologies(text) if t in {"jQuery", "XML", "SOAP"}], ["jQuery", "XML", "SOAP"])
        self.assertNotIn("XML", find_technologies("Fichiers XMLHttpRequest"))


class PageTests(unittest.TestCase):
    def test_score_is_in_the_page_with_its_explanation(self) -> None:
        offers = [offer(1, stage_status="confirmed_stage", level="débutant"), offer(2, level="avancé", original_title="Autre")]
        rows = embedded_rows(build_html(offers, generated_on="2026-11-24"))
        self.assertEqual([row["scoreDec"] for row in rows], [70, 0])
        self.assertEqual(rows[0]["scoreDecDetail"][0], "stage confirmé (+40)")


if __name__ == "__main__":
    unittest.main()
