"""Petit serveur local : la page offres.html avec un bouton « Mettre à jour ».

    python serveur.py            # puis ouvrir http://127.0.0.1:8000
    python serveur.py --port 8080

Une page ouverte d'un double-clic (file://) ne peut pas lancer Python : le navigateur
l'interdit. Ce serveur sert la page et, quand on clique sur « Mettre à jour », lance
`python main.py --nouveautes` (nouvelle collecte, page recréée, résumé des nouveautés).
La page affiche l'avancement, puis se recharge à la fin.

Sécurité :
- le serveur écoute seulement sur 127.0.0.1 (cet ordinateur), jamais sur le réseau ;
- l'en-tête Host doit être 127.0.0.1 ou localhost (protection contre le « DNS rebinding ») ;
- le lancement demande l'en-tête X-Jobs-Insights. Un autre site ouvert dans le navigateur
  ne peut pas l'envoyer sans permission (CORS), et le serveur n'en donne pas ;
- une seule collecte à la fois. Les règles de la collecte restent celles de main.py
  (5 s entre les pages du Guichet-Emplois, cache de 24 h pour Remotive).
"""

from __future__ import annotations

import argparse
from collections import deque
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import threading

DOSSIER = Path(__file__).resolve().parent
PAGE = DOSSIER / "offres.html"
COMMANDE = [sys.executable, "main.py", "--nouveautes"]
EN_TETE = "X-Jobs-Insights"
HOTES_PERMIS = {"127.0.0.1", "localhost"}
LIGNES_GARDEES = 40


class Collecte:
    """Une collecte lancée en arrière-plan, avec ses dernières lignes affichées."""

    def __init__(self, commande: list[str], dossier: Path) -> None:
        self.commande, self.dossier = commande, dossier
        self.verrou = threading.Lock()
        self.processus: subprocess.Popen | None = None
        self.lignes: deque[str] = deque(maxlen=LIGNES_GARDEES)
        self.debut = self.fin = ""
        self.code: int | None = None

    def en_cours(self) -> bool:
        return self.processus is not None and self.processus.poll() is None

    def lancer(self) -> bool:
        """Démarre la collecte. Faux si une collecte tourne déjà."""
        with self.verrou:
            if self.en_cours():
                return False
            self.lignes.clear()
            self.debut, self.fin, self.code = datetime.now().isoformat(timespec="seconds"), "", None
            env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
            self.processus = subprocess.Popen(
                self.commande, cwd=self.dossier, env=env, text=True, encoding="utf-8", errors="replace",
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
            )
            threading.Thread(target=self._lire, args=(self.processus,), daemon=True).start()
            return True

    def _lire(self, processus: subprocess.Popen) -> None:
        assert processus.stdout is not None
        for ligne in processus.stdout:
            if ligne.strip():
                self.lignes.append(ligne.rstrip())
        processus.wait()
        self.code = processus.returncode
        self.fin = datetime.now().isoformat(timespec="seconds")

    def etat(self) -> dict[str, object]:
        return {"enCours": self.en_cours(), "debut": self.debut, "fin": self.fin, "code": self.code,
                "lignes": list(self.lignes)}


def creer_gestionnaire(collecte: Collecte, page: Path) -> type[BaseHTTPRequestHandler]:
    class Gestionnaire(BaseHTTPRequestHandler):
        server_version = "jobs-insights-kandet"

        def _hote_permis(self) -> bool:
            hote = (self.headers.get("Host") or "").rsplit(":", 1)[0].strip("[]")
            return hote in HOTES_PERMIS

        def _repondre(self, statut: HTTPStatus, corps: bytes, type_contenu: str) -> None:
            self.send_response(statut)
            self.send_header("Content-Type", type_contenu)
            self.send_header("Content-Length", str(len(corps)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(corps)

        def _json(self, statut: HTTPStatus, donnees: dict[str, object]) -> None:
            self._repondre(statut, json.dumps(donnees, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

        def do_GET(self) -> None:  # noqa: N802 (nom imposé par http.server)
            if not self._hote_permis():
                return self._json(HTTPStatus.FORBIDDEN, {"erreur": "hôte refusé"})
            chemin = self.path.split("?", 1)[0]
            if chemin in ("/", "/offres.html"):
                if not page.exists():
                    message = "offres.html n'existe pas encore : cliquez sur « Mettre à jour » ou lancez python main.py."
                    return self._repondre(HTTPStatus.NOT_FOUND, message.encode("utf-8"), "text/plain; charset=utf-8")
                return self._repondre(HTTPStatus.OK, page.read_bytes(), "text/html; charset=utf-8")
            if chemin == "/api/etat":
                return self._json(HTTPStatus.OK, collecte.etat())
            # Rien d'autre n'est servi : ni cache, ni CV, ni rapports.
            self._json(HTTPStatus.NOT_FOUND, {"erreur": "introuvable"})

        def do_POST(self) -> None:  # noqa: N802
            if not self._hote_permis() or self.headers.get(EN_TETE) != "1":
                return self._json(HTTPStatus.FORBIDDEN, {"erreur": "demande refusée"})
            if self.path != "/api/mise-a-jour":
                return self._json(HTTPStatus.NOT_FOUND, {"erreur": "introuvable"})
            if not collecte.lancer():
                return self._json(HTTPStatus.CONFLICT, {"erreur": "une collecte est déjà en cours"})
            self._json(HTTPStatus.ACCEPTED, collecte.etat())

        def log_message(self, format: str, *args: object) -> None:
            pass  # pas de ligne par requête : la page interroge l'état toutes les 2 s

    return Gestionnaire


def creer_serveur(port: int = 8000, commande: list[str] | None = None, dossier: Path = DOSSIER,
                  page: Path = PAGE) -> tuple[ThreadingHTTPServer, Collecte]:
    collecte = Collecte(commande or COMMANDE, dossier)
    serveur = ThreadingHTTPServer(("127.0.0.1", port), creer_gestionnaire(collecte, page))
    return serveur, collecte


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Sert offres.html avec un bouton « Mettre à jour » (cet ordinateur seulement).")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)
    serveur, _ = creer_serveur(args.port)
    print(f"Page : http://127.0.0.1:{args.port}  (Ctrl+C pour arrêter)")
    try:
        serveur.serve_forever()
    except KeyboardInterrupt:
        print("\nServeur arrêté.")
    finally:
        serveur.server_close()


if __name__ == "__main__":
    main()
