"""Tests hors ligne de autres_sources.py (Jobicy, Greenhouse, Lever) : faux contenus au format réel."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from autres_sources import (GREENHOUSE_URL, JOBICY_URL, LEVER_URL, collect_other_sources, parse_greenhouse,
                            parse_jobicy, parse_lever, place)

JOBICY = {"jobs": [
    {"id": 1, "url": "https://jobicy.com/jobs/1-dev", "jobTitle": "Backend Developer", "companyName": "Acme",
     "jobIndustry": ["Software Engineering"], "jobType": ["full-time"], "jobGeo": "Canada", "pubDate": "2026-11-20 10:00:00",
     "jobDescription": "<p>Build APIs in <b>Python</b>.</p>"},
    {"id": 2, "url": "https://jobicy.com/jobs/2-sales", "jobTitle": "Account Executive", "companyName": "Acme",
     "jobIndustry": ["Sales"], "jobGeo": "Canada", "pubDate": "2026-11-20", "jobDescription": "Sell."},
]}
GREENHOUSE = {"jobs": [
    {"id": 10, "title": "Développeur.euse Java", "location": {"name": "Montréal, Quebec, Canada"},
     "absolute_url": "https://boards.greenhouse.io/levio/jobs/10", "first_published": "2026-11-18T09:00:00-05:00",
     "content": "&lt;p&gt;Java et &lt;strong&gt;SQL&lt;/strong&gt;&lt;/p&gt;"},
    {"id": 11, "title": "Account Manager", "location": {"name": "Montréal"}, "absolute_url": "https://x/11", "content": ""},
    {"id": 12, "title": "Software Engineer", "location": {"name": "London, UK"}, "absolute_url": "https://x/12", "content": ""},
]}
LEVER = [
    {"id": "a1", "text": "Développeur.euse fullstack", "categories": {"location": "Montréal (FR)", "commitment": "Full-time"},
     "hostedUrl": "https://jobs.lever.co/osedea/a1", "createdAt": 1795000000000, "descriptionPlain": "React et Node.",
     "lists": [{"text": "Exigences", "content": "<li>3 ans</li>"}]},
    {"id": "a2", "text": "Juriste", "categories": {"location": "Montréal"}, "hostedUrl": "https://x/a2"},
]


class ParseTests(unittest.TestCase):
    def test_jobicy_keeps_it_industries_and_links_to_jobicy(self) -> None:
        records = parse_jobicy(JOBICY)
        self.assertEqual([r.title for r in records], ["Backend Developer"])
        self.assertEqual((records[0].source, records[0].url), ("Jobicy", "https://jobicy.com/jobs/1-dev"))
        self.assertEqual(records[0].description, "Build APIs in Python .")
        self.assertEqual((records[0].work_mode, records[0].published_at), ("Télétravail", "2026-11-20"))

    def test_greenhouse_keeps_it_jobs_in_canada(self) -> None:
        records = parse_greenhouse(GREENHOUSE, "Levio")
        self.assertEqual([r.title for r in records], ["Développeur.euse Java"])  # ventes et Londres écartés
        self.assertEqual(records[0].description, "Java et SQL")  # HTML échappé deux fois
        self.assertEqual((records[0].employer, records[0].city, records[0].province), ("Levio", "Montréal", "QC"))
        self.assertEqual(records[0].published_at, "2026-11-18")

    def test_lever(self) -> None:
        records = parse_lever(LEVER, "Osedea")
        self.assertEqual([r.title for r in records], ["Développeur.euse fullstack"])
        self.assertIn("Exigences : 3 ans", records[0].description)
        self.assertEqual((records[0].job_type, records[0].city), ("Full-time", "Montréal"))

    def test_place_never_guesses(self) -> None:
        self.assertEqual(place("Montreal, QC"), ("Montreal", "QC"))
        self.assertEqual(place("Quebec City, Quebec, Canada"), ("Québec", "QC"))
        self.assertEqual(place("Québec, Canada"), ("", "QC"))  # la province seule : pas de ville
        self.assertEqual(place("Remote - Montréal"), ("Montréal", "QC"))
        self.assertEqual(place("Toronto, Canada"), ("", ""))  # hors Québec : rien
        self.assertEqual(place("Canada, USA"), ("", ""))


class CollectTests(unittest.TestCase):
    def setUp(self) -> None:
        self.folder = TemporaryDirectory()
        self.employers = Path(self.folder.name) / "pages.json"
        self.employers.write_text(json.dumps({"employeurs": [
            {"plateforme": "greenhouse", "jeton": "levio", "employeur": "Levio"},
            {"plateforme": "lever", "jeton": "osedea", "employeur": "Osedea"},
            {"plateforme": "lever", "jeton": "panne", "employeur": "Panne"},
        ]}), encoding="utf-8")
        self.answers = {JOBICY_URL: JOBICY, GREENHOUSE_URL.format(jeton="levio"): GREENHOUSE,
                        LEVER_URL.format(jeton="osedea"): LEVER}
        self.calls, self.pauses = [], []

    def tearDown(self) -> None:
        self.folder.cleanup()

    def fetch(self, url: str, accept: str) -> bytes:
        self.calls.append(url)
        if url not in self.answers:
            raise OSError("HTTP 404")
        return json.dumps(self.answers[url]).encode("utf-8")

    def collect(self):
        return collect_other_sources(Path(self.folder.name) / "cache", fetch=self.fetch, sleep=self.pauses.append,
                                     employers_file=self.employers, log=lambda text: None)

    def test_all_sources_and_one_error_does_not_stop_the_others(self) -> None:
        records, errors, counts = self.collect()
        self.assertEqual(counts, {"Jobicy": 1, "Levio": 1, "Osedea": 1})
        self.assertEqual(len(records), 3)
        self.assertEqual(errors, ["Panne (lever) : HTTP 404"])
        self.assertEqual(len(self.pauses), 3)  # une pause entre deux appels (4 appels)
        self.assertTrue(all(seconds >= 1 for seconds in self.pauses))  # Jobicy : au plus 1 requête par seconde

    def test_answers_are_reused_for_one_hour(self) -> None:
        self.collect()
        first = len(self.calls)
        self.collect()
        self.assertEqual(len(self.calls) - first, 1)  # seule la source en erreur est redemandée


if __name__ == "__main__":
    unittest.main()
