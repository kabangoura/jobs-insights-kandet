"""Tests hors ligne de la langue de l'annonce (texte.announcement_language) et de son filtre."""

import unittest

from interface import TEMPLATE_FILE, build_html
from test_interface import embedded_rows, offer
from texte import announcement_language

FRANCAIS = ("Nous cherchons une personne pour développer des applications avec notre équipe. "
            "Vous serez responsable de la qualité du code et des tests dans un environnement agile, "
            "pour nos clients du Québec. Les tâches sont variées et le poste est permanent.")
ANGLAIS = ("We are looking for a developer to build and maintain our platform. You will work with "
           "the team on the design of new features and you are responsible for the quality of the code "
           "that we ship to our customers in Canada.")


class LanguageTests(unittest.TestCase):
    def test_french_english_and_both(self) -> None:
        self.assertEqual(announcement_language(FRANCAIS), "Français")
        self.assertEqual(announcement_language(ANGLAIS), "Anglais")
        self.assertEqual(announcement_language(FRANCAIS + " " + ANGLAIS), "Français et anglais")

    def test_too_little_text_is_not_decided(self) -> None:
        # Cas réel : annonce du Guichet-Emplois sans description, avec seulement un titre.
        self.assertEqual(announcement_language("Senior Fullstack Java Developer"), "")
        self.assertEqual(announcement_language(""), "")

    def test_a_few_english_words_in_a_french_text(self) -> None:
        self.assertEqual(announcement_language(FRANCAIS + " Stack : React, Node, the cloud."), "Français")


class PageTests(unittest.TestCase):
    def test_language_in_rows_and_filter_in_page(self) -> None:
        offers = [offer(1, description=FRANCAIS), offer(2, description=ANGLAIS), offer(3)]
        rows = embedded_rows(build_html(offers, generated_on="2026-11-26"))
        self.assertEqual([row["langue"] for row in rows], ["Français", "Anglais", ""])
        template = TEMPLATE_FILE.read_text(encoding="utf-8")
        self.assertIn('<select id="langue">', template)
        self.assertIn('if (langueChoisie && (o.langue || "Non précisé") !== langueChoisie) return false;', template)
        self.assertIn('"Annonce en anglais"', template)


if __name__ == "__main__":
    unittest.main()
