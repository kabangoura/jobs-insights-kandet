"""Onglet Statistiques de offres.html : mêmes chiffres que Python, et historique par jour.

Les calculs de la page (interface_stats.js) sont exécutés avec Node.js et comparés avec
analyse.py. Si Node.js n'est pas installé, cette comparaison est sautée.
"""

from collections import Counter
from datetime import date
import json
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
import unittest

from analyse import build_summary
from export import load_offers
from historique import read_history
from interface import STATS_SCRIPT_FILE, TEMPLATE_FILE, build_html, offer_to_row
from test_interface import offer

SAMPLE = Path(__file__).with_name("echantillon.json")


def sample_offers():
    """L'échantillon versionné (10 offres réelles), plus des cas limites."""
    offers = load_offers(SAMPLE)
    offers.append(offer(901, salary_min=55000.0, salary_unit="année", salary_currency="CAD", level="débutant"))
    offers.append(offer(902, salary_min=3500.0, salary_unit="mois", salary_currency="", technologies=["SQL"]))  # devise absente
    offers.append(offer(903, region="", level=""))
    return offers


@unittest.skipUnless(shutil.which("node"), "Node.js n'est pas installé : comparaison JavaScript sautée")
class SameNumbersAsPythonTests(unittest.TestCase):
    def run_javascript(self, rows: list[dict[str, object]]) -> dict[str, object]:
        script = """
const { calculerStatistiques } = require(process.argv[2]);
const offres = JSON.parse(require("fs").readFileSync(process.argv[3], "utf8"));
console.log(JSON.stringify(calculerStatistiques(offres)));
"""
        with TemporaryDirectory() as folder:
            data = Path(folder) / "offres.json"
            data.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
            runner = Path(folder) / "essai.js"
            runner.write_text(script, encoding="utf-8")
            result = subprocess.run(["node", str(runner), str(STATS_SCRIPT_FILE), str(data)],
                                    capture_output=True, text=True, encoding="utf-8", timeout=60, check=True)
        return json.loads(result.stdout)

    def test_same_numbers_as_analyse_py(self) -> None:
        offers = sample_offers()
        stats = self.run_javascript([offer_to_row(item, number) for number, item in enumerate(offers, start=1)])
        summary = build_summary(offers, today=date(2026, 11, 24))

        self.assertEqual(stats["total"], len(offers))
        for unit, key in (("année", "salaireAnnuel"), ("heure", "salaireHoraire")):
            with self.subTest(salaire=unit):
                expected = summary["salaries"].get(f"CAD / {unit}")
                self.assertEqual(stats[key]["offres"], expected["offers"] if expected else 0)
                self.assertEqual(stats[key]["mediane"], expected["median_low"] if expected else None)
        self.assertEqual(dict(stats["technologies"]), dict(Counter(t for item in offers for t in item.technologies)))
        regions = dict(stats["regions"])
        self.assertEqual(regions.pop("Non précisé", 0), sum(1 for item in offers if not item.region))
        self.assertEqual(regions, summary["regions"])
        self.assertEqual({name: n for name, n in stats["niveaux"] if n}, summary["levels"])
        self.assertEqual(stats["stages"], summary["stage_classification"].get("confirmed_stage", 0))
        self.assertEqual(dict(stats["professions"]), dict(Counter(item.title for item in offers if item.title)))

    def test_salary_by_level_and_median_of_even_count(self) -> None:
        offers = [offer(n, salary_min=value, salary_unit="année", salary_currency="CAD", level="débutant")
                  for n, value in ((1, 50000.0), (2, 60000.0), (3, 70000.0), (4, 90000.0))]
        offers.append(offer(5, salary_min=30.0, salary_unit="heure", salary_currency="CAD", level="débutant"))
        stats = self.run_javascript([offer_to_row(item, number) for number, item in enumerate(offers, start=1)])
        # Le taux horaire n'entre jamais dans le salaire annuel.
        self.assertEqual(stats["salaireParNiveau"]["débutant"], {"offres": 4, "mediane": 65000})
        self.assertEqual(stats["salaireHoraire"], {"offres": 1, "mediane": 30})

    def test_empty_list(self) -> None:
        stats = self.run_javascript([])
        self.assertEqual((stats["total"], stats["salaireAnnuel"]["mediane"], stats["technologies"]), (0, None, []))


class HistoryTests(unittest.TestCase):
    def test_last_collection_of_each_day(self) -> None:
        with TemporaryDirectory() as folder:
            path = Path(folder) / "historique-collectes.csv"
            path.write_text(
                "﻿date;offres;nouvelles;disparues;retirees_avant_expiration;fiches_lues;erreurs\n"
                "2026-11-20 17:30;195;24;24;13;190;0\n"
                "2026-11-23 09:49;186;6;15;5;181;0\n"
                "2026-11-23 10:45;188;1;0;0;183;0\n"
                "ligne abîmée;;;\n"
                "2026-11-24 17:24;183;19;24;20;178;2\n",
                encoding="utf-8",
            )
            history = read_history(path)
        self.assertEqual(history, [
            {"date": "2026-11-20", "offres": 195, "erreurs": 0},
            {"date": "2026-11-23", "offres": 188, "erreurs": 0},
            {"date": "2026-11-24", "offres": 183, "erreurs": 2},
        ])

    def test_missing_file(self) -> None:
        self.assertEqual(read_history(Path("pas-de-fichier.csv")), [])

    def test_history_is_embedded_in_the_page(self) -> None:
        page = build_html([offer(1)], generated_on="2026-11-24", history=[{"date": "2026-11-24", "offres": 1, "erreurs": 0}])
        self.assertIn('<script type="application/json" id="historique">[{"date": "2026-11-24", "offres": 1, "erreurs": 0}]</script>', page)
        self.assertIn("function calculerStatistiques", page)
        self.assertNotIn("{{", page)

    def test_tab_is_in_the_page_and_off_by_default(self) -> None:
        template = TEMPLATE_FILE.read_text(encoding="utf-8")
        self.assertIn('<button type="button" id="vue-stats" aria-pressed="false">Statistiques</button>', template)
        self.assertIn('<section id="stats" hidden', template)
        self.assertIn('vue = params.get("vue") === "stats" ? "stats" : "liste";', template)


if __name__ == "__main__":
    unittest.main()
