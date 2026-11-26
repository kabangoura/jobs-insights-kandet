"""Salaire annuel équivalent (normalisation.annual_equivalent) et heures de la fiche (fiches.py)."""

import unittest

from fiches import parse_job_posting
from fixtures import make_posting
from interface import build_html
from normalisation import annual_equivalent, weekly_hours
from test_interface import embedded_rows, offer

# Balisage réel de la fiche de Revenu Québec (25 novembre 2026) : « 26,58 $ de l'heure / 35 ».
SALAIRE_AVEC_HEURES = (
    '<span property="minValue" content="26,58">26,58</span> <span property="currency" content="CAD" class="hidden">$</span>'
    '<span property="unitText" class="hidden">HOUR</span> de l’heure</span> / <span property=\'workHours\'> 35</span>'
)


class EquivalentTests(unittest.TestCase):
    def test_hourly_with_written_hours(self) -> None:
        self.assertEqual(annual_equivalent(26.58, None, "heure", " 35"), (48376, 48376, "35 h/sem. × 52 sem."))
        self.assertEqual(annual_equivalent(24.0, 35.0, "heure", "37,5"), (46800, 68250, "37,5 h/sem. × 52 sem."))
        self.assertEqual(annual_equivalent(30.0, None, "heure", "35 à 40"), (54600, 62400, "35 à 40 h/sem. × 52 sem."))

    def test_monthly(self) -> None:
        self.assertEqual(annual_equivalent(4337.0, 10000.0, "mois"), (52044, 120000, "12 mois"))

    def test_nothing_is_assumed(self) -> None:
        self.assertIsNone(annual_equivalent(30.0, None, "heure", ""))  # heures non écrites
        self.assertIsNone(annual_equivalent(101.0, None, "jour", "35"))  # nombre de jours inconnu
        self.assertIsNone(annual_equivalent(None, None, "heure", "35"))
        self.assertIsNone(weekly_hours("NA"))

    def test_hours_are_read_from_the_posting(self) -> None:
        details = parse_job_posting(make_posting(salary_html=SALAIRE_AVEC_HEURES))
        self.assertEqual(details.work_hours, "35")

    def test_equivalent_in_the_page(self) -> None:
        item = offer(1, salary_min=26.58, salary_unit="heure")
        item.source_records[0].source_data["posting"] = {"work_hours": "35"}
        rows = embedded_rows(build_html([item, offer(2, salary_min=70000.0, salary_unit="année")], generated_on="2026-11-26"))
        self.assertEqual(rows[0]["equiv"], {"min": 48376, "max": 48376, "calcul": "35 h/sem. × 52 sem."})
        self.assertIsNone(rows[1]["equiv"])  # déjà annuel


if __name__ == "__main__":
    unittest.main()
