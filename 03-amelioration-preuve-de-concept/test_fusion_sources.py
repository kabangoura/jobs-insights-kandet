"""Doublons entre sources (fusion.py) : la même offre sur le Guichet-Emplois et ailleurs."""

import unittest

from fusion import aggregate_records
from modele import SourceRecord


def guichet(number: int, original_title: str = "", site: str = "Jobillico", **changes) -> SourceRecord:
    values = dict(source="Guichet-Emplois", source_id=str(number), url=f"https://ge/{number}",
                  title="analyste en informatique", original_title=original_title, employer="Levio",
                  location="Montréal (QC)", city="Montréal", origin_site=site)
    values.update(changes)
    return SourceRecord(**values)


def career_page(title: str = "Développeur.euse Java", **changes) -> SourceRecord:
    values = dict(source="Greenhouse", source_id="9", url="https://boards.greenhouse.io/levio/jobs/9", title=title,
                  employer="Levio", location="Montréal, Quebec, Canada", city="Montréal", origin_site="Levio")
    values.update(changes)
    return SourceRecord(**values)


class CrossSourceTests(unittest.TestCase):
    def test_same_offer_on_guichet_and_on_the_career_page(self) -> None:
        # Le Guichet met le titre CNP dans `title` ; le titre de l'employeur est dans `original_title`.
        offers = aggregate_records([guichet(1, "Développeur.euse Java"), career_page()])
        self.assertEqual(len(offers), 1)
        self.assertEqual([r.source for r in offers[0].source_records], ["Guichet-Emplois", "Greenhouse"])

    def test_different_jobs_with_the_same_cnp_title_stay_apart(self) -> None:
        offers = aggregate_records([guichet(1, "Développeur.euse Java", site="Jobillico"),
                                    guichet(2, "Analyste d'affaires", site="Talent.com")])
        self.assertEqual(len(offers), 2)

    def test_direct_guichet_offer_and_its_partner_copy(self) -> None:
        # Cas réel du 25 novembre : annonce directe (sans titre d'employeur) et copie de Québec emploi.
        offers = aggregate_records([
            guichet(1, "", site="Guichet-Emplois", title="technicien/technicienne en informatique",
                    employer="Université du Québec", location="Québec (QC)", city="Québec"),
            guichet(2, "Technicien en informatique (profil Bureautique)", site="Québec emploi",
                    title="technicien/technicienne en informatique", employer="Universite du quebec",
                    location="Québec (QC)", city="Québec"),
        ])
        self.assertEqual(len(offers), 1)

    def test_other_city_or_employer_is_another_offer(self) -> None:
        self.assertEqual(len(aggregate_records([guichet(1, "Développeur.euse Java"), career_page(city="Québec")])), 2)
        self.assertEqual(len(aggregate_records([guichet(1, "Développeur.euse Java"), career_page(employer="Osedea")])), 2)


if __name__ == "__main__":
    unittest.main()
