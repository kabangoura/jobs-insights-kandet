"""Tests hors ligne du mode de travail (normalisation.work_mode_of) et du filtre de la page."""

import unittest

from autres_sources import parse_lever
from interface import TEMPLATE_FILE, build_html
from normalisation import work_mode_of
from test_interface import embedded_rows, offer


class WorkModeTests(unittest.TestCase):
    def test_source_field_first(self) -> None:
        self.assertEqual(work_mode_of("À distance"), "Télétravail")  # mot du Guichet-Emplois
        self.assertEqual(work_mode_of("Sur place", title="Developer - 100% Remote"), "Sur place")
        self.assertEqual(work_mode_of("Hybride"), "Hybride")
        self.assertEqual(work_mode_of("Sur la route"), "Sur la route")

    def test_location_or_title_when_clearly_written(self) -> None:
        self.assertEqual(work_mode_of("", "Remote (Canada)"), "Télétravail")
        self.assertEqual(work_mode_of("", "Montréal", "Bilingual Specialist - 100% Remote (MTL, QC)"), "Télétravail")
        self.assertEqual(work_mode_of("", "Montréal", "Sr. Configuration Management Specialist - SECRET hybrid"), "Hybride")

    def test_never_guessed(self) -> None:
        self.assertEqual(work_mode_of("", "Montréal, QC", "Développeur Java"), "")
        self.assertEqual(work_mode_of("", "Remotely Lake", "Remotivation officer"), "")  # mots entiers seulement

    def test_lever_workplace_type(self) -> None:
        jobs = [{"id": str(n), "text": "Développeur web", "categories": {"location": "Montréal"}, "hostedUrl": f"https://x/{n}",
                 "workplaceType": kind} for n, kind in enumerate(["hybrid", "remote", "onsite", "unspecified"])]
        self.assertEqual([r.work_mode for r in parse_lever(jobs, "Osedea")], ["Hybride", "Télétravail", "Sur place", ""])


class PageTests(unittest.TestCase):
    def test_mode_in_rows_and_filter_in_page(self) -> None:
        offers = [offer(1, work_mode="À distance"), offer(2, original_title="Dev - Remote"), offer(3)]
        rows = embedded_rows(build_html(offers, generated_on="2026-11-26"))
        self.assertEqual([row["mode"] for row in rows], ["Télétravail", "Télétravail", ""])
        template = TEMPLATE_FILE.read_text(encoding="utf-8")
        self.assertIn('<select id="mode">', template)
        self.assertIn('if (modeChoisi && (o.mode || "Non précisé") !== modeChoisi) return false;', template)


if __name__ == "__main__":
    unittest.main()
