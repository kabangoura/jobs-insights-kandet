"""Tests hors ligne de donnees_ouvertes.py (aucun téléchargement : faux portail, faux fichiers)."""

import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from donnees_ouvertes import ATTRIBUTION, monthly_files, read_csv_stream, summarize, trend_for_page, update
from interface import build_html, open_data_for_page
from test_interface import offer

COLUMNS = ["ID WIC Lieu emploi", "Appellation d'emploi", "Code CNP 2021", "Code CNP21 nom", "Indicateur Source Externe",
           "Nombre de postes vacants", "Provinces/Territoires", "Ville", "Salaire par", "Salaire Minimum", "Salaire Maximum"]


def fake_csv(rows: list[list[str]]) -> bytes:
    """Un fichier comme ceux du Guichet-Emplois : UTF-16 avec BOM, séparé par des tabulations."""
    lines = ["\t".join(COLUMNS)] + ["\t".join(row) for row in rows]
    return ("\r\n".join(lines) + "\r\n").encode("utf-16")


ROWS = [
    ["1", "développeur Web", "21234", "Développeurs Web", "0", "2", "Québec", "Québec", "Année", "60000", "70000"],
    ["2", "programmeur", "21232", "Programmeurs", "1", "1", "Québec", "Montréal", "Année", "80000", "NA"],
    ["3", "technicien réseau", "22220", "Techniciens de réseau", "1", "NA", "Québec", "Lévis", "Heure", "30", "35"],
    ["4", "technicien réseau", "22220", "Techniciens de réseau", "1", "1", "Québec", "Hameau inconnu", "NA", "NA", "NA"],
    ["5", "développeur", "21232", "Programmeurs", "0", "1", "Ontario", "Toronto", "Année", "90000", "NA"],  # pas au Québec
    ["6", "cuisinier", "63200", "Cuisiniers", "0", "1", "Québec", "Québec", "Heure", "17", "NA"],  # pas TI
]


def package(*names: tuple[str, str, str]) -> dict:
    return {"result": {"resources": [
        {"name": name, "language": [language], "format": "CSV", "url": url} for name, language, url in names]}}


class MonthlyFilesTests(unittest.TestCase):
    def test_month_comes_from_the_resource_name(self) -> None:
        # Les noms de fichiers changent (oct2026, octobre2023, june-2024…) : on lit le nom de la ressource.
        found = monthly_files(package(
            ("October 2026 Job Postings Advertised on Canada's National Job Bank Website", "fr", "https://x/fr-oct2026.csv"),
            ("October 2026 Job Postings Advertised on Canada's National Job Bank Website", "en", "https://x/en-oct2026.csv"),
            ("June 2024 Job Postings Advertised on Canada's National Job Bank Website", "fr", "https://x/june-2024-fr.csv"),
            ("Data dictionary", "fr", "https://x/dictionnaire.csv"),
            ("April 2026 Job Postings Advertised on Canada's National Job Bank Website", "fr", ""),  # cas réel : pas d'adresse
        ))
        self.assertEqual(found, [("2026-10", "https://x/fr-oct2026.csv"), ("2024-06", "https://x/june-2024-fr.csv")])


class SummaryTests(unittest.TestCase):
    def test_only_it_jobs_in_quebec_are_counted(self) -> None:
        summary = summarize(read_csv_stream(io.BytesIO(fake_csv(ROWS))))
        self.assertEqual(summary["offres"], 4)
        self.assertEqual(summary["postes"], 5)  # « NA » compte pour 1 poste
        self.assertEqual(summary["sources_externes"], 3)
        self.assertEqual(summary["salaire_annuel"], {"offres": 2, "mediane": 70000.0})
        self.assertEqual(summary["salaire_horaire"], {"offres": 1, "mediane": 30.0})
        # Région administrative retrouvée à partir de la ville (regions.py) ; lieu inconnu : « Non précisé ».
        self.assertEqual(summary["regions"], {"Capitale-Nationale": 1, "Chaudière-Appalaches": 1, "Montréal": 1, "Non précisé": 1})
        self.assertEqual(summary["professions"], {"Programmeurs": 1, "Techniciens de réseau": 2, "Développeurs Web": 1} | {})


class UpdateTests(unittest.TestCase):
    def run_update(self, path: Path, months: int, files: dict[str, bytes], opened: list[str]) -> dict:
        names = [(f"{name} Job Postings", "fr", f"https://x/{name}.csv") for name in files]

        def open_url(url: str):
            opened.append(url)
            content = files[url.rsplit("/", 1)[-1].removesuffix(".csv")]
            if isinstance(content, Exception):
                raise content
            return io.BytesIO(content)

        return update(path, months=months, get_package=lambda: package(*names), open_url=open_url,
                      sleep=lambda seconds: None, log=lambda text: None)

    def test_months_already_read_are_not_downloaded_again(self) -> None:
        files = {"October 2026": fake_csv(ROWS), "September 2026": fake_csv(ROWS[:1]), "August 2026": fake_csv([])}
        with TemporaryDirectory() as folder:
            path = Path(folder) / "donnees-ouvertes.json"
            first, second = [], []
            self.run_update(path, 2, files, first)
            document = self.run_update(path, 3, files, second)
        self.assertEqual(first, ["https://x/October 2026.csv", "https://x/September 2026.csv"])
        self.assertEqual(second, ["https://x/August 2026.csv"])  # seulement le mois qui manquait
        self.assertEqual(list(document["mois"]), ["2026-08", "2026-09", "2026-10"])
        self.assertEqual(document["attribution"], ATTRIBUTION)
        self.assertIn("Licence du gouvernement ouvert", document["licence"])

    def test_a_broken_month_does_not_stop_the_others(self) -> None:
        files = {"October 2026": fake_csv(ROWS), "September 2026": OSError("connexion coupée"), "August 2026": fake_csv(ROWS[:1])}
        with TemporaryDirectory() as folder:
            document = self.run_update(Path(folder) / "donnees-ouvertes.json", 3, files, [])
        self.assertEqual(list(document["mois"]), ["2026-08", "2026-10"])  # septembre, illisible, est réessayé plus tard

    def test_trend_for_the_page(self) -> None:
        document = {"mois": {"2026-08": {"offres": 1}, "2026-09": {"offres": 2}, "2026-10": {"offres": 3}}}
        self.assertEqual([m["mois"] for m in trend_for_page(document, months=2)], ["2026-09", "2026-10"])
        self.assertIsNone(open_data_for_page({}))


class PageTests(unittest.TestCase):
    def test_trend_and_licence_are_in_the_page(self) -> None:
        document = {"page": "https://open.canada.ca/x", "licence": "Licence du gouvernement ouvert – Canada",
                    "licence_url": "https://ouvert.canada.ca/l", "attribution": ATTRIBUTION,
                    "mois": {"2026-10": summarize(read_csv_stream(io.BytesIO(fake_csv(ROWS))))}}
        page = build_html([offer(1)], generated_on="2026-11-24", trend=open_data_for_page(document))
        start = page.index('id="tendance">') + len('id="tendance">')
        embedded = json.loads(page[start:page.index("</script>", start)])
        self.assertEqual(embedded["mois"][0]["offres"], 4)
        self.assertEqual(embedded["attribution"], ATTRIBUTION)
        self.assertIn("Ces chiffres ne suivent pas les filtres de gauche", page)


if __name__ == "__main__":
    unittest.main()
