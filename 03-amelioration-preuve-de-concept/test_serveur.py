"""Tests du serveur local (serveur.py) avec une fausse collecte : aucun site n'est contacté."""

import http.client
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import threading
import time
import unittest

from serveur import creer_serveur

# Fausse collecte : affiche deux lignes, attend un peu, puis se termine.
FAUSSE_COLLECTE = [sys.executable, "-c",
                   "import time; print('Recherche 1 sur 14', flush=True); time.sleep(0.6); print('Page mise à jour')"]


class ServeurTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dossier = TemporaryDirectory()
        self.page = Path(self.dossier.name) / "offres.html"
        self.page.write_text("<!doctype html><title>Offres</title>", encoding="utf-8")
        self.serveur, self.collecte = creer_serveur(0, FAUSSE_COLLECTE, Path(self.dossier.name), self.page)
        self.port = self.serveur.server_address[1]
        threading.Thread(target=self.serveur.serve_forever, daemon=True).start()

    def tearDown(self) -> None:
        self.serveur.shutdown()
        self.serveur.server_close()
        if self.collecte.processus is not None:
            self.collecte.processus.wait(timeout=10)
        self.dossier.cleanup()

    def demande(self, methode: str, chemin: str, en_tetes: dict[str, str] | None = None) -> tuple[int, bytes]:
        connexion = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        connexion.request(methode, chemin, headers=en_tetes or {})
        reponse = connexion.getresponse()
        resultat = reponse.status, reponse.read()
        connexion.close()
        return resultat

    def attendre_fin(self) -> dict:
        for _ in range(100):
            etat = json.loads(self.demande("GET", "/api/etat")[1])
            if not etat["enCours"] and etat["code"] is not None:
                return etat
            time.sleep(0.1)
        self.fail("la fausse collecte ne s'est pas terminée")

    def test_page_is_served(self) -> None:
        statut, corps = self.demande("GET", "/")
        self.assertEqual((statut, corps), (200, b"<!doctype html><title>Offres</title>"))

    def test_update_runs_once_and_reports_progress(self) -> None:
        statut, _ = self.demande("POST", "/api/mise-a-jour", {"X-Jobs-Insights": "1"})
        self.assertEqual(statut, 202)
        # Une seule collecte à la fois.
        self.assertEqual(self.demande("POST", "/api/mise-a-jour", {"X-Jobs-Insights": "1"})[0], 409)
        etat = self.attendre_fin()
        self.assertEqual(etat["code"], 0)
        self.assertEqual(etat["lignes"], ["Recherche 1 sur 14", "Page mise à jour"])

    def test_update_from_another_site_is_refused(self) -> None:
        # Sans l'en-tête X-Jobs-Insights (qu'un autre site ne peut pas envoyer), rien n'est lancé.
        self.assertEqual(self.demande("POST", "/api/mise-a-jour")[0], 403)
        self.assertIsNone(self.collecte.processus)

    def test_other_host_is_refused(self) -> None:
        # Protection contre le « DNS rebinding » : seul 127.0.0.1 ou localhost est accepté.
        self.assertEqual(self.demande("GET", "/", {"Host": "exemple.com"})[0], 403)
        self.assertEqual(self.demande("POST", "/api/mise-a-jour", {"Host": "exemple.com", "X-Jobs-Insights": "1"})[0], 403)

    def test_only_the_page_is_served(self) -> None:
        (Path(self.dossier.name) / "cv-perso.txt").write_text("secret", encoding="utf-8")
        for chemin in ("/cv-perso.txt", "/../serveur.py", "/offres.json", "/cache/"):
            self.assertEqual(self.demande("GET", chemin)[0], 404, chemin)

    def test_listens_on_this_computer_only(self) -> None:
        self.assertEqual(self.serveur.server_address[0], "127.0.0.1")


class LanceurTests(unittest.TestCase):
    def test_demarrer_cmd(self) -> None:
        # Double-clic sur Demarrer.cmd (racine du dépôt) : lance serveur.py et ouvre la page.
        lanceur = Path(__file__).resolve().parents[1] / "Demarrer.cmd"
        contenu = lanceur.read_bytes()
        lignes = contenu.split(bytes([10]))  # 10 = fin de ligne ; 13 = retour chariot (Windows)
        # Fins de ligne Windows partout : sinon cmd lit mal les étiquettes des « goto ».
        self.assertTrue(all(ligne.endswith(bytes([13])) for ligne in lignes[:-1]))
        texte = contenu.decode("utf-8")
        self.assertIn("03-amelioration-preuve-de-concept", texte)
        self.assertIn("python serveur.py", texte)
        self.assertIn("http://127.0.0.1:8000", texte)


if __name__ == "__main__":
    unittest.main()
