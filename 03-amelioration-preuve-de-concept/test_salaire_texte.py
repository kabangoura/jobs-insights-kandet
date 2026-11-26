"""Salaire écrit dans la description des offres Jobicy et des pages carrières (autres_sources.salary_from_text)."""

import unittest

from autres_sources import parse_greenhouse, salary_from_text
from normalisation import normalize_record


class SalaryFromTextTests(unittest.TestCase):
    def test_real_formats(self) -> None:
        # Formats vus le 26 novembre 2026 (Levio, Workleap, ShareGate, Spiria, PolicyMe, Quora).
        cases = {
            "Estimated salary range: $90,000 to $130,000": ("$90,000 to $130,000 par année", ""),
            "Base salary: 155 000 $ to 185 000 $": ("155 000 $ to 185 000 $ par année", ""),
            "Échelle salariale : 68 000$ - 86 000$": ("68 000$ - 86 000$ par année", ""),
            "Compensation: The total target cash compensation for this role is $132,000–$154,000 CAD":
                ("$132,000–$154,000 CAD par année", "CAD"),
            "For US based applicants, the salary range is $189,507 - $274,604 USD": ("$189,507 - $274,604 USD par année", "USD"),
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(salary_from_text(text), expected)

    def test_amount_without_salary_word_is_ignored(self) -> None:
        self.assertEqual(salary_from_text("We raised $20,000,000 to $40,000,000 from investors last year."), ("", ""))

    def test_small_amounts_are_not_an_annual_salary(self) -> None:
        self.assertEqual(salary_from_text("Salary: $18,000 - $19,000 bonus pool"), ("", ""))

    def test_salary_reaches_the_offer(self) -> None:
        payload = {"jobs": [{"id": 1, "title": "Software Developer", "location": {"name": "Montréal, Quebec, Canada"},
                             "absolute_url": "https://x/1", "content": "&lt;p&gt;Base salary: $80 000 - $105 000&lt;/p&gt;"}]}
        record = parse_greenhouse(payload, "Workleap")[0]
        normalize_record(record)
        self.assertEqual((record.salary_min, record.salary_max, record.salary_unit, record.salary_currency),
                         (80000.0, 105000.0, "année", ""))  # devise non écrite : pas devinée


if __name__ == "__main__":
    unittest.main()
