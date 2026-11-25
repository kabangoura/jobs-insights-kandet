"""Tests hors ligne du résumé des nouvelles offres (nouveautes.py et main.py --nouveautes)."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from candidature import build_profile
from nouveautes import build_summary, new_offers
from score_dec import load_program
from test_historique import RegularCollectionTests
from test_interface import offer

PROGRAM = load_program()["technologies"]


def news(number: int, **changes):
    changes.setdefault("original_title", f"Poste {number}")
    return offer(number, new_since_previous=True, **changes)


class NewOffersTests(unittest.TestCase):
    def test_republished_and_similar_announcements(self) -> None:
        offers = [news(1), offer(2, original_title="Poste 1"),  # poste 1 republié : pas nouveau
                  news(3), news(4, original_title="Poste 3"),   # même poste publié deux fois : une seule offre
                  offer(5)]                                        # ancienne offre
        self.assertEqual([o.original_title for o in new_offers(offers)], ["Poste 3"])


class SummaryTests(unittest.TestCase):
    def test_internship_comes_first_even_without_technology(self) -> None:
        # Cas réel du 24 novembre : le stage de Revenu Québec ne cite aucune technologie.
        offers = [news(1, technologies=["Python", "SQL"], level="débutant"),
                  news(2, stage_status="confirmed_stage", level="débutant"), offer(3)]
        text = build_summary(offers, "2026-11-23T09:49:00+00:00", PROGRAM)
        self.assertIn("# Nouvelles offres depuis la collecte du 23 novembre 2026", text)
        self.assertIn("2 nouvelles offres, dont 1 stage.", text)
        self.assertLess(text.index("Poste 2"), text.index("Poste 1"))
        self.assertIn("stage confirmé · score DEC 70/100", text)
        self.assertIn("https://www.guichetemplois.gc.ca/rechercheemplois/offredemploi/2", text)

    def test_offers_close_to_the_cv(self) -> None:
        profile = build_profile("Étudiant au DEC. Python, SQL, Git, Java.")
        offers = [news(1, technologies=["Python", "SQL", "Java"], level="débutant"),
                  news(2, technologies=["Go", "Kubernetes"], level="avancé")]
        text = build_summary(offers, "2026-11-23", PROGRAM, profile, "mon-cv.txt")
        cv_part = text[text.index("## Les plus proches du CV mon-cv.txt"):text.index("## Les autres")]
        self.assertIn("Poste 1", cv_part)
        self.assertIn("en commun : Python, SQL, Java", cv_part)
        self.assertNotIn("Poste 2", cv_part)  # trop loin du CV : dans « les autres »

    def test_no_previous_collection_and_no_news(self) -> None:
        self.assertIn("pas de collecte précédente", build_summary([offer(1)], None, PROGRAM))
        self.assertIn("Aucune nouvelle offre.", build_summary([offer(1)], "2026-11-23", PROGRAM))

    def test_long_list_is_cut(self) -> None:
        offers = [news(n) for n in range(1, 9)]
        text = build_summary(offers, "2026-11-23", PROGRAM, top=5)
        self.assertIn("Et 3 autres : case « Nouvelles offres seulement » dans offres.html.", text)


class MainTests(unittest.TestCase):
    def test_after_a_second_collection(self) -> None:
        collector = RegularCollectionTests("test_second_collection_shows_what_changed")
        with TemporaryDirectory() as folder:
            collector.collect(folder, [101, 102, 103])
            output = collector.collect(folder, [101, 102, 104], "--nouveautes")
            report = (Path(folder) / "rapport-nouveautes.md").read_text(encoding="utf-8")
        self.assertIn("1 nouvelle offre, dont 0 stage.", report)
        self.assertIn("Poste 104", report)
        self.assertNotIn("Poste 101", report)
        self.assertIn("Résumé enregistré dans", output)

    def test_report_file_is_never_committed(self) -> None:
        ignore = (Path(__file__).resolve().parents[1] / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("rapport-*.md", ignore)


if __name__ == "__main__":
    unittest.main()
