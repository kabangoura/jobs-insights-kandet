"""Tests hors ligne des offres sans description (offres des partenaires du Guichet-Emplois).

Collecte du 24 novembre 2026 : 43 offres sur 183 n'ont pas de description, parce que le
Guichet-Emplois n'affiche que le titre, le lieu, le salaire et un lien vers Québec emploi,
Talent.com, Indeed ou ZipRecruiter. Le seul stage confirmé de la collecte en fait partie :
ces offres sont donc signalées, jamais cachées par défaut.
"""

from datetime import date
import re
import unittest

from analyse import build_summary
from interface import TEMPLATE_FILE, build_html
from test_interface import embedded_rows, offer


def partner_offer(number: int, site: str, description: str = ""):
    item = offer(number, description=description, original_url=f"https://exemple.test/{number}")
    item.source_records[0].origin_site = site
    return item


class WithoutDescriptionTests(unittest.TestCase):
    def test_rows_say_if_the_description_is_there(self) -> None:
        offers = [partner_offer(1, "Québec emploi"), partner_offer(2, "Jobillico", "Tâches : développer des applications."),
                  partner_offer(3, "indeed.com", "   ")]
        rows = embedded_rows(build_html(offers, generated_on="2026-11-24"))
        self.assertEqual([row["aDescription"] for row in rows], [False, True, False])

    def test_summary_counts_them_by_site(self) -> None:
        offers = [partner_offer(1, "Québec emploi"), partner_offer(2, "Québec emploi"), partner_offer(3, "Talent.com"),
                  partner_offer(4, "Jobillico", "Une vraie description."), partner_offer(5, "indeed.com", "   ")]
        summary = build_summary(offers, today=date(2026, 11, 24))
        self.assertEqual(summary["without_description_by_site"], {"Québec emploi": 2, "Talent.com": 1, "indeed.com": 1})

    def test_page_has_the_filter_unchecked_and_the_message(self) -> None:
        template = TEMPLATE_FILE.read_text(encoding="utf-8")
        # La case existe, n'est pas cochée par défaut et fait partie des filtres gardés dans l'adresse.
        self.assertRegex(template, r'<input type="checkbox" id="avecDescription">\s*Description complète seulement')
        self.assertIn('"avecDescription", "suivies", "tri"]', template)
        self.assertIn("if (avecDescription && !o.aDescription) return false;", template)
        self.assertIn("Pas de description sur le Guichet-Emplois", template)
        self.assertIn('["description_complete", (o) => (o.aDescription ? "oui" : "non")]', template)
        self.assertIsNone(re.search(r'id="avecDescription"[^>]*checked', template))


if __name__ == "__main__":
    unittest.main()
