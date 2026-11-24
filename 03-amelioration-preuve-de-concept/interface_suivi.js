// Suivi de mes candidatures dans offres.html : offres gardées, statut, note.
// Tout reste dans ce navigateur (localStorage) : rien n'est envoyé, rien n'est écrit dans le dépôt.
// Vérifié par test_interface_suivi.py (Node.js, avec un faux stockage).

const CLE_SUIVI = "jobs-insights-kandet.suivi.v1"; // Edge partage le stockage entre toutes les pages locales : nom propre au projet
const STATUTS = ["À postuler", "Postulé", "Entrevue", "Offre reçue", "Refusé", "Abandonné"];

// Une offre garde la même clé d'une collecte à l'autre : son lien (numéro du Guichet-Emplois, lien Remotive).
function cleOffre(o) {
  return o.lien || `${o.titre}|${o.employeur}|${o.ville}`;
}

function creerSuivi(stockage) {
  let donnees = {};
  let disponible = true;
  try {
    const texte = stockage.getItem(CLE_SUIVI);
    const lu = texte ? JSON.parse(texte) : {};
    if (lu && typeof lu === "object" && !Array.isArray(lu)) donnees = lu;
  } catch (e) {
    // Stockage refusé par le navigateur, ou texte abîmé : on repart d'un suivi vide sans planter la page.
    disponible = !(e && e.name === "SecurityError");
  }

  function enregistrer() {
    try {
      stockage.setItem(CLE_SUIVI, JSON.stringify(donnees));
      return true;
    } catch (e) {
      disponible = false;
      return false;
    }
  }

  const aujourdhui = () => new Date().toISOString().slice(0, 10);

  return {
    disponible: () => disponible,
    obtenir: (o) => donnees[cleOffre(o)] || null,
    // On garde aussi une copie du titre, de l'employeur et des liens : l'offre reste dans
    // « Mes candidatures » même si elle disparaît d'une prochaine collecte.
    suivre(o, statut = STATUTS[0]) {
      const cle = cleOffre(o);
      const avant = donnees[cle] || {};
      donnees[cle] = {
        statut: STATUTS.includes(statut) ? statut : STATUTS[0],
        note: avant.note || "",
        ajoutee: avant.ajoutee || aujourdhui(),
        maj: aujourdhui(),
        titre: o.titre, employeur: o.employeur || "", ville: o.ville || o.lieu || "",
        lien: o.lien || "", lienOrigine: o.lienOrigine || "", expire: o.expire || "",
      };
      return enregistrer();
    },
    changer(o, champs) {
      const suivi = donnees[cleOffre(o)];
      if (!suivi) return false;
      if (champs.statut !== undefined && STATUTS.includes(champs.statut)) suivi.statut = champs.statut;
      if (champs.note !== undefined) suivi.note = String(champs.note).slice(0, 500);
      suivi.maj = aujourdhui();
      return enregistrer();
    },
    retirer(o) {
      delete donnees[cleOffre(o)];
      return enregistrer();
    },
    // Toutes les offres suivies, les plus récemment modifiées d'abord.
    liste() {
      return Object.entries(donnees)
        .map(([cle, s]) => ({ cle, ...s }))
        .sort((a, b) => (b.maj || "").localeCompare(a.maj || "") || (a.titre || "").localeCompare(b.titre || "", "fr"));
    },
    nombre: () => Object.keys(donnees).length,
  };
}

// CSV pour Excel (séparateur « ; »). Une cellule qui commence par = + - @ est précédée d'une
// apostrophe : Excel ne l'exécute pas comme une formule.
function suiviEnCsv(liste) {
  const cellule = (v) => {
    let t = v === null || v === undefined ? "" : String(v);
    if (/^[=+\-@]/.test(t)) t = "'" + t;
    return /[;"\r\n]/.test(t) ? `"${t.replace(/"/g, '""')}"` : t;
  };
  const colonnes = ["statut", "titre", "employeur", "ville", "note", "ajoutee_le", "modifiee_le", "expire_le", "lien", "lien_origine"];
  const lignes = liste.map((s) => [s.statut, s.titre, s.employeur, s.ville, s.note, s.ajoutee, s.maj, s.expire, s.lien, s.lienOrigine].map(cellule).join(";"));
  return [colonnes.join(";"), ...lignes].join("\r\n");
}

if (typeof module !== "undefined") module.exports = { creerSuivi, suiviEnCsv, cleOffre, CLE_SUIVI, STATUTS };
