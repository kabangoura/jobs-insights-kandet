// Statistiques de l'onglet « Statistiques » de offres.html, calculées sur les offres affichées.
// Mêmes règles que analyse.py (vérifié par test_interface_stats.py) :
// - un salaire horaire et un salaire annuel ne sont jamais mélangés ;
// - la médiane porte sur la valeur basse de la fourchette (salMin) ;
// - une information absente n'est pas devinée : elle est comptée à part (« Non précisé »).

function mediane(valeurs) {
  if (!valeurs.length) return null;
  const v = [...valeurs].sort((a, b) => a - b);
  const m = Math.floor(v.length / 2);
  const resultat = v.length % 2 ? v[m] : (v[m - 1] + v[m]) / 2;
  return Math.round(resultat * 100) / 100;
}

// [[nom, nombre], ...] du plus fréquent au moins fréquent (à égalité : ordre alphabétique).
function compterValeurs(valeurs) {
  const compte = new Map();
  for (const v of valeurs) compte.set(v, (compte.get(v) || 0) + 1);
  return [...compte].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0], "fr"));
}

function salaires(offres, unite) {
  const v = offres.filter((o) => o.salMin !== null && o.unite === unite && o.devise === "CAD").map((o) => o.salMin);
  return { offres: v.length, mediane: mediane(v) };
}

function calculerStatistiques(offres) {
  const NIVEAUX = ["débutant", "intermédiaire", "avancé"];
  const parNiveau = {};
  for (const n of NIVEAUX) parNiveau[n] = salaires(offres.filter((o) => o.niveau === n), "année");
  return {
    total: offres.length,
    stages: offres.filter((o) => o.stage === "Stage").length,
    stagesPossibles: offres.filter((o) => o.stage === "Stage possible").length,
    salaireAnnuel: salaires(offres, "année"),
    salaireHoraire: salaires(offres, "heure"),
    regions: compterValeurs(offres.map((o) => o.region || "Non précisé")),
    technologies: compterValeurs(offres.flatMap((o) => o.technos)),
    avecTechnologie: offres.filter((o) => o.technos.length).length,
    // Ordre fixe : du débutant à l'avancé, puis les offres sans indice de niveau.
    niveaux: [...NIVEAUX, "Non précisé"].map((n) => [n, offres.filter((o) => (o.niveau || "Non précisé") === n).length]),
    salaireParNiveau: parNiveau,
    // Ordre fixe ; « Non précisé » à la fin (le mode n'est jamais deviné).
    modes: [...["Télétravail", "Hybride", "Sur place", "Sur la route"].map((m) => [m, offres.filter((o) => o.mode === m).length]),
      ["Non précisé", offres.filter((o) => !o.mode).length]].filter(([, n]) => n),
    professions: compterValeurs(offres.map((o) => o.titreTri).filter((t) => t)),
  };
}

if (typeof module !== "undefined") module.exports = { calculerStatistiques, mediane, compterValeurs };
