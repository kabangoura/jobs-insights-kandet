"""Suivi de mes candidatures dans offres.html (interface_suivi.js).

Le script est exécuté avec Node.js et un faux stockage, qui joue le rôle du
localStorage du navigateur. Si Node.js n'est pas installé, ces tests sont sautés.
"""

import json
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
import unittest

from interface import SUIVI_SCRIPT_FILE, TEMPLATE_FILE, build_html
from test_interface import offer

OFFRE = {"lien": "https://www.guichetemplois.gc.ca/rechercheemplois/offredemploi/50787405",
         "titre": "Stagiaire en développement informatique", "employeur": "Revenu québec", "ville": "Québec",
         "lienOrigine": "https://www.quebecemploi.gouv.qc.ca/offre/1", "expire": "2026-12-14"}

# Faux localStorage : un dictionnaire, gardé dans un fichier entre deux « ouvertures de la page ».
PREAMBULE = """
const fs = require("fs");
const { creerSuivi, suiviEnCsv, cleOffre, CLE_SUIVI, STATUTS } = require(process.argv[2]);
const fichier = process.argv[3];
const OFFRE = JSON.parse(process.argv[4]);
function stockage() {
  const d = fs.existsSync(fichier) ? JSON.parse(fs.readFileSync(fichier, "utf8")) : {};
  return { getItem: (k) => (k in d ? d[k] : null), setItem: (k, v) => { d[k] = String(v); fs.writeFileSync(fichier, JSON.stringify(d)); } };
}
const sortie = {};
"""


@unittest.skipUnless(shutil.which("node"), "Node.js n'est pas installé : test JavaScript sauté")
class TrackingTests(unittest.TestCase):
    def run_javascript(self, code: str, store: dict[str, str] | None = None) -> dict[str, object]:
        with TemporaryDirectory() as folder:
            storage = Path(folder) / "stockage.json"
            if store is not None:
                storage.write_text(json.dumps(store), encoding="utf-8")
            runner = Path(folder) / "essai.js"
            runner.write_text(PREAMBULE + code + "\nconsole.log(JSON.stringify(sortie));", encoding="utf-8")
            result = subprocess.run(["node", str(runner), str(SUIVI_SCRIPT_FILE), str(storage), json.dumps(OFFRE)],
                                    capture_output=True, text=True, encoding="utf-8", timeout=60, check=True)
        return json.loads(result.stdout)

    def test_follow_change_and_find_again_after_reopening(self) -> None:
        result = self.run_javascript("""
let s = creerSuivi(stockage());
s.suivre(OFFRE);
s.changer(OFFRE, { statut: "Postulé", note: "Relancer le 1er décembre" });
// Nouvelle ouverture de la page (après une nouvelle collecte) : le numéro de l'offre n'a pas changé.
s = creerSuivi(stockage());
sortie.suivi = s.obtenir({ lien: OFFRE.lien, titre: "titre modifié" });
sortie.nombre = s.nombre();
sortie.cle = cleOffre(OFFRE);
""")
        self.assertEqual(result["nombre"], 1)
        self.assertEqual(result["cle"], OFFRE["lien"])
        self.assertEqual(result["suivi"]["statut"], "Postulé")
        self.assertEqual(result["suivi"]["note"], "Relancer le 1er décembre")
        # Copie gardée : l'offre reste dans « Mes candidatures » même si elle disparaît de la collecte.
        self.assertEqual((result["suivi"]["titre"], result["suivi"]["employeur"]), (OFFRE["titre"], OFFRE["employeur"]))

    def test_unknown_status_is_refused_and_remove_works(self) -> None:
        result = self.run_javascript("""
const s = creerSuivi(stockage());
s.suivre(OFFRE, "N'importe quoi");
sortie.premier = s.obtenir(OFFRE).statut;
s.changer(OFFRE, { statut: "Pirate" });
sortie.apres = s.obtenir(OFFRE).statut;
s.retirer(OFFRE);
sortie.retire = s.obtenir(OFFRE);
sortie.relu = creerSuivi(stockage()).nombre();
""")
        self.assertEqual((result["premier"], result["apres"], result["retire"], result["relu"]), ("À postuler", "À postuler", None, 0))

    def test_damaged_storage_does_not_break_the_page(self) -> None:
        result = self.run_javascript("""
const s = creerSuivi(stockage());
sortie.nombre = s.nombre();
sortie.disponible = s.disponible();
sortie.ok = s.suivre(OFFRE);
""", store={"jobs-insights-kandet.suivi.v1": "{pas du json"})
        self.assertEqual(result, {"nombre": 0, "disponible": True, "ok": True})

    def test_blocked_storage_is_reported(self) -> None:
        result = self.run_javascript("""
const refus = () => { const e = new Error("bloqué"); e.name = "SecurityError"; throw e; };
const s = creerSuivi({ getItem: refus, setItem: refus });
sortie.disponible = s.disponible();
sortie.ok = s.suivre(OFFRE);
""")
        self.assertEqual(result, {"disponible": False, "ok": False})

    def test_csv_for_excel_and_formula_protection(self) -> None:
        result = self.run_javascript("""
const s = creerSuivi(stockage());
s.suivre(OFFRE);
s.changer(OFFRE, { statut: "Entrevue", note: "=HYPERLINK(1); appeler" });
sortie.csv = suiviEnCsv(s.liste());
sortie.statuts = STATUTS;
sortie.cleStockage = CLE_SUIVI;
""")
        lines = result["csv"].split("\r\n")
        self.assertEqual(lines[0], "statut;titre;employeur;ville;note;ajoutee_le;modifiee_le;expire_le;lien;lien_origine")
        self.assertTrue(lines[1].startswith("Entrevue;Stagiaire en développement informatique;Revenu québec;Québec;\"'=HYPERLINK(1); appeler\";"))
        self.assertEqual(result["statuts"][0], "À postuler")
        self.assertEqual(result["cleStockage"], "jobs-insights-kandet.suivi.v1")


class PageTests(unittest.TestCase):
    def test_tracking_is_in_the_page(self) -> None:
        page = build_html([offer(1)], generated_on="2026-11-24")
        self.assertIn("function creerSuivi", page)
        self.assertIn('<button type="button" id="vue-suivi" aria-pressed="false">Mes candidatures</button>', page)
        self.assertIn('<input type="checkbox" id="suivies"> Mes offres suivies seulement', page)
        self.assertNotIn("{{", page)

    def test_nothing_is_sent(self) -> None:
        # Le suivi n'utilise que le stockage du navigateur : aucune requête réseau dans la page.
        template = TEMPLATE_FILE.read_text(encoding="utf-8") + SUIVI_SCRIPT_FILE.read_text(encoding="utf-8")
        for forbidden in ("fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket"):
            self.assertNotIn(forbidden, template)


if __name__ == "__main__":
    unittest.main()
