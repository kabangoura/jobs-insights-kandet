# Note — Livrable 3 : reprendre et améliorer une preuve de concept

**Kandet** — 17 novembre 2026

## Tester le projet (guide rapide)

Pour quelqu'un qui veut essayer le prototype sans avoir suivi le travail.

### Ce qu'il faut

- **Python 3.12 ou plus récent.** Vérifier avec `python --version`. Sous Windows, si `python` n'est pas reconnu, essayer `py --version` et remplacer `python` par `py` dans les commandes.
- **Aucune bibliothèque à installer** : tout est dans la bibliothèque standard, pas de `pip install`.
- **Une connexion Internet**, seulement pour la collecte. Les tests et l'option `--depuis` fonctionnent sans Internet.

### 1. Se placer dans le dossier du projet

Dans un terminal (PowerShell), à partir du dossier du dépôt (`jobs-insights-kandet`) :

```powershell
cd .\03-amelioration-preuve-de-concept
```

Toutes les commandes suivantes se lancent depuis ce dossier.

### 2. Lancer les tests (1 seconde, sans Internet)

```powershell
python -m unittest discover -p "test_*.py" -v
```

La dernière ligne doit être `OK`, après `Ran 275 tests`. Dix tests exécutent les scripts de la page avec Node.js : le CV, la lettre et les statistiques (comparés avec Python), et le suivi des candidatures. Si Node.js n'est pas installé, ces tests sont simplement sautés (`skipped`).

### 3. Lancer la collecte

```powershell
# Essai rapide (environ 1 minute) : pages de résultats + 5 fiches seulement
python main.py --max-fiches 5

# Collecte complète
python main.py
```

**Combien de temps ça prend :**

- **Environ 17 minutes la première fois.** Le script attend 5 secondes entre chaque page, comme le demande le site (`robots.txt`).
- **Environ 1 minute les fois suivantes**, parce que les fiches déjà lues sont gardées dans `cache/fiches/`.

**Pendant la collecte :**

- Des lignes comme `Fiche 42/188` montrent l'avancement : le script tourne, il ne faut pas l'arrêter.
- Le message `HTTP 429 : nouvel essai dans 30 s` est normal : le site demande d'attendre, et le script réessaie tout seul.

À la fin, le script affiche les statistiques et la liste des offres, puis enregistre tout dans `offres.json`.

### 4. Chercher les offres dans le navigateur (le plus simple)

À chaque lancement, `main.py` recrée **`offres.html`** à côté de `offres.json`, avec toutes les offres de la dernière collecte. On l'ouvre d'un **double-clic** : la page s'affiche dans le navigateur (Edge, Chrome, Firefox), sans Internet et sans rien installer.

La page contient une copie des offres. Après une nouvelle collecte, il faut donc **rafraîchir la page (F5)** si elle est déjà ouverte. En haut, « page créée le … à … » indique de quand elle date.

```powershell
python main.py --depuis offres.json    # recrée seulement la page, sans nouvelle collecte
```

Dans la page :

- **Recherche par mots** (titre, employeur, technologie, ville…) et **filtres** : région, ville, technologie, niveau, salaire minimum, stages seulement, salaire indiqué, offres expirées cachées, description complète seulement, mes offres suivies seulement, **mode de travail** (Télétravail, Hybride, Sur place, Sur la route, Non précisé), **langue de l'annonce** (Français, Anglais, Français et anglais, Non précisé), avec un badge « Annonce en anglais » sur la carte. Les offres en télétravail ouvertes à tout le Canada n'ont pas de région : pour les voir toutes, garder « Toutes les régions ».
- **Tri** : plus récentes, salaire le plus élevé, expire bientôt, titre.
- **Technologies demandées** : un clic sur une technologie filtre les offres.
- **Chaque offre** affiche le titre de l'employeur, le salaire, le niveau, les badges (« Stage », « Expire dans 3 j »…), un résumé, les technologies et « Plus de détails » (études, expérience, langues). Elle donne aussi le lien vers l'offre et vers l'annonce d'origine.
- **Annonces semblables** : quand un employeur publie le même poste plusieurs fois (même titre, même site), la page montre une seule carte avec « 3 annonces ». Les autres annonces sont listées sur la carte, avec leur ville, leur date et leur lien. Un poste republié alors qu'il était déjà en ligne a le badge « Republiée » au lieu de « Nouvelle ».
- **Offres sans description** : pour les offres de Québec emploi, Talent.com, Indeed et ZipRecruiter, le Guichet-Emplois ne donne ni les tâches ni les exigences. La carte le dit dans un encadré orange, et le lien « Lire l'offre complète sur … » est mis en gras. La case « Description complète seulement » les cache, mais elle n'est pas cochée par défaut : le seul stage confirmé de la collecte du 24 novembre est une de ces offres.
- **« Exporter en CSV »** enregistre les offres affichées pour Excel (une ligne par annonce, avec une colonne `description_complete`).
- **« Copier le lien de cette recherche »** garde les filtres dans l'adresse de la page. Par exemple, `offres.html#region=Estrie&techno=SQL` rouvre la page avec ces filtres.
- **Onglet « Statistiques »** (à côté de « Liste des offres ») : des graphiques calculés sur les offres affichées, donc ils suivent les filtres. On y trouve les salaires médians (annuel et horaire, jamais mélangés), les stages, les offres par région, les technologies, le niveau, le salaire selon le niveau, les professions et le nombre d'offres à chaque jour de collecte. Après `python main.py --donnees-ouvertes`, l'onglet montre aussi la **tendance des 12 derniers mois** (offres TI au Québec et salaire annuel médian, mois par mois), avec les données ouvertes du Guichet-Emplois. Un clic sur une région, une technologie ou un niveau applique le filtre. `offres.html#vue=stats` ouvre directement cet onglet.
- **Suivi de mes candidatures** : « ☆ Suivre cette offre » sur une carte, puis un statut (À postuler, Postulé, Entrevue, Offre reçue, Refusé, Abandonné). L'onglet « Mes candidatures » liste les offres suivies avec une note (contact, date d'entrevue…), et le bouton « Exporter mon suivi (CSV) » les enregistre pour Excel. Le suivi reste dans le navigateur de l'ordinateur (`localStorage`) : rien n'est envoyé. Il est gardé quand `main.py` recrée la page. Une offre qui disparaît d'une collecte reste dans le suivi, avec la mention « N'est plus dans la dernière collecte ».
- **Score « étudiant du DEC »** sur chaque carte, sur 100, avec le détail des points : stage confirmé (+40, possible +20), niveau débutant (+30, non précisé +15, intermédiaire +10), technologies vues au DEC (jusqu'à +30). Le tri « Score étudiant du DEC » met en premier les offres les plus adaptées à un étudiant en fin de DEC.
- La page s'adapte au téléphone (filtres repliables) et au mode sombre.
- **« Comparer les offres avec mon CV »** (en haut des résultats) :
  - choisir un CV en `.docx` ou en `.txt`, ou coller son texte ;
  - la page affiche ce qu'elle a compris du CV et trie les offres par correspondance ;
  - chaque offre montre sa note sur 100, ce qui est en commun et ce qui manque ;
  - la note est la même qu'avec `main.py --cv` ;
  - le CV reste dans le navigateur : il n'est ni envoyé ni enregistré. « Retirer le CV » efface tout.
- **« Vérifier ma lettre pour cette offre »** (sous chaque offre) :
  - ouvre une fenêtre où l'on choisit sa lettre (`.docx` ou `.txt`) ou colle son texte ;
  - la page affiche les vérifications (✓ / ✗ : zones à remplir, employeur, poste, technologies, longueur) et les suggestions. Ce sont les mêmes que `main.py --lettre` ;
  - si un CV est chargé dans la page, les suggestions séparent les technologies du CV de celles à apprendre ;
  - la lettre reste dans la fenêtre : on peut la retoucher, revérifier, ou la vérifier pour une autre offre.

### 4 bis. Mettre à jour les offres depuis la page (bouton « Mettre à jour les offres »)

Le plus simple : **double-cliquer sur `Demarrer.cmd`** à la racine du dépôt. Il lance le serveur dans une fenêtre réduite « Offres TI - serveur » (la fermer arrête le serveur), attend qu'il réponde, puis ouvre la page. Si le serveur tourne déjà, il ouvre seulement la page. Sans Python, il explique où le télécharger.

```powershell
python serveur.py          # la même chose dans le terminal, puis ouvrir http://127.0.0.1:8000 (Ctrl+C pour arrêter)
```

La page s'ouvre alors avec un bouton **« Mettre à jour les offres »**. Un clic lance `python main.py --nouveautes` : nouvelle collecte, page recréée et résumé des nouveautés. La progression s'affiche à côté du bouton (« Recherche 3 sur 14… »), puis la page se recharge toute seule. Ouverte d'un double-clic, la page ne peut pas lancer Python (le navigateur l'interdit) : elle indique alors de lancer `python serveur.py`.

Le serveur écoute seulement sur cet ordinateur (`127.0.0.1`), sert seulement la page, et n'accepte le lancement que depuis la page elle-même : un autre site ouvert dans le navigateur ne peut pas lancer de collecte. Une seule collecte à la fois.

### 5. Comparer son CV avec les offres (aide à la candidature)

```powershell
# Essai avec le CV fictif fourni
python main.py --depuis offres.json --cv cv-exemple.txt

# Avec son propre CV (Word ou texte), seulement les offres de la Capitale-Nationale, avec un rapport
python main.py --depuis offres.json --cv C:\Users\moi\Documents\mon-cv.docx --region capitale --rapport-cv
```

Le programme :

1. lit le CV (`.docx` ou `.txt`). Les PDF ne sont pas acceptés : il faut enregistrer le CV en `.docx` depuis Word ;
2. affiche ce qu'il a compris : technologies, compétences, années d'expérience, niveau, langues, recherche de stage ;
3. classe les offres avec une note sur 100. Pour chacune, il montre ce qui est en commun avec le CV et ce qui manque ;
4. signale les stages présents dans le classement ;
5. donne des pistes pour adapter le CV aux 3 premières offres : technologies à mettre en avant, technologies demandées absentes du CV, langues, expérience et études demandées, tâches de l'offre à relier à ses projets, date limite ;
6. avec `--rapport-cv`, enregistre tout dans `rapport-candidature.md` (`--nb-offres 20` pour en voir plus).

**Le CV reste sur l'ordinateur** : rien n'est envoyé à un service extérieur. Les fichiers `.docx`, `.pdf` et `rapport-candidature*.md` de ce dossier sont ignorés par Git. Il ne faut jamais mettre un vrai CV dans le dépôt.

Les filtres de l'étape suivante (`--region`, `--stages`, `--niveau`…) choisissent les offres à comparer.

**Vérifier une lettre de motivation pour une offre précise :**

```powershell
# L'offre se donne par son lien (copié depuis offres.html) ou par son numéro du Guichet-Emplois
python main.py --depuis offres.json --lettre lettre-exemple.txt --cv cv-exemple.txt --offre 50585958 --rapport-lettre
```

Le programme ne note pas la lettre. Il repère ce qui peut être amélioré :
- zones à remplir oubliées (« [nom du poste] », « XXX ») ;
- employeur et poste cités ou non ;
- technologies et compétences de l'offre citées ou absentes. Avec `--cv`, il sépare celles qui sont dans le CV de celles à apprendre ;
- mots importants des tâches de l'offre absents de la lettre ;
- longueur (environ 200 à 450 mots).

Avec `--rapport-lettre`, le résultat est aussi enregistré dans `rapport-lettre.md`.

### 6. Garder les offres à jour (collecte régulière)

Les offres changent vite : entre le 17 et le 20 novembre, 24 offres sur 197 étaient nouvelles et 24 avaient disparu. Il faut donc refaire la collecte souvent, par exemple chaque jour ou 2 à 3 fois par semaine.

```powershell
# À la main : collecte, page à jour, ménage du cache (environ 1 minute)
python main.py --nettoyer-cache --html --resume-seulement

# Ou avec le script, qui note aussi tout dans journal-collectes.log
.\collecte-reguliere.ps1
```

À chaque collecte, le programme :
- **compare avec la collecte précédente** : « 24 nouvelle(s) offre(s), 24 disparue(s) (dont 13 retirée(s) avant leur date limite) ». Le détail est dans `offres.json` (`changes_since_previous`) ;
- **marque les nouvelles offres** : badge « Nouvelle » dans `offres.html`, case « Nouvelles offres seulement » dans les filtres, et phrase en haut de la page (« 24 nouvelles offres depuis la collecte du 17 novembre 2026 ») ;
- **ajoute une ligne à `historique-collectes.csv`** (date, offres, nouvelles, disparues…), qui s'ouvre dans Excel ;
- **avec `--nettoyer-cache`**, retire du cache les fiches des offres disparues. Il le fait seulement après une collecte complète et sans erreur, pour ne rien effacer par erreur ;
- **avec `--nouveautes`**, écrit un résumé des nouvelles offres dans `rapport-nouveautes.md` : d'abord les nouveaux stages, puis les offres proches du CV (avec `--cv mon-cv.docx`), puis les autres, classées par score « étudiant du DEC ». Le script `collecte-reguliere.ps1` le fait à chaque collecte (sans CV).

```powershell
python main.py --depuis offres.json --nouveautes --cv mon-cv.docx   # résumé avec son CV, sans nouvelle collecte
```

**Collecte automatique avec Windows :**

```powershell
.\planifier-collecte.ps1                # chaque jour à 8 h
.\planifier-collecte.ps1 -Heure 12:30   # à une autre heure
.\planifier-collecte.ps1 -Supprimer     # arrêter la collecte automatique
```

La tâche lance `collecte-reguliere.ps1` quand la session est ouverte. Si l'ordinateur est éteint à l'heure prévue, elle se lance dès qu'il est rallumé. Une collecte par jour respecte les règles des sites : 5 s entre les pages du Guichet-Emplois, et Remotive au plus 1 fois par jour grâce au cache de 24 h.

### 7. Chercher des offres précises dans le terminal (sans retélécharger)

Après une collecte, `--depuis offres.json` relit les offres en quelques secondes, sans Internet. On peut combiner plusieurs filtres. Les accents et les majuscules ne comptent pas.

```powershell
python main.py --depuis offres.json --ville Québec
python main.py --depuis offres.json --region monteregie
python main.py --depuis offres.json --techno Python
python main.py --depuis offres.json --niveau debutant
python main.py --depuis offres.json --stages
python main.py --depuis offres.json --salaire-min 60000
python main.py --depuis offres.json --salaire-min 30 --unite-salaire heure
python main.py --depuis offres.json --techno SQL --ville Montréal --csv
```

| Option | Ce qu'elle garde |
|---|---|
| `--ville Montréal` | Les offres de cette ville |
| `--region monteregie` | Les offres de cette région administrative. Le début du nom suffit : `capitale`, `chaudiere`, `laurentides`… |
| `--techno SQL` | Les offres qui mentionnent cette technologie (SQL, Python, C#, Azure…) |
| `--niveau débutant` | `débutant`, `intermédiaire` ou `avancé` |
| `--stages` | Les stages confirmés ou possibles |
| `--salaire-min 60000` | Les offres dont le bas de la fourchette atteint ce montant. L'unité est l'année par défaut ; ajouter `--unite-salaire heure` pour un taux horaire |
| `--employeur desjardins` | Les offres dont le nom de l'employeur contient ce mot |
| `--csv` | Enregistre les offres affichées dans `offres.csv`, qui s'ouvre directement dans Excel |
| `--html` | Met dans `offres.html` seulement les offres affichées par les filtres (sans cette option, la page contient toutes les offres) |
| `--sans-html` | Ne pas recréer `offres.html` |
| `--resume-seulement` | Affiche les statistiques sans la liste |
| `--sans-autres-sources` | Ne pas interroger Jobicy ni les pages carrières d'employeurs (`pages_carrieres.json`) |
| `--donnees-ouvertes` | Lit les données ouvertes du Guichet-Emplois pour la tendance des 12 derniers mois dans l'onglet Statistiques (`--donnees-ouvertes 24` pour 24 mois). La première fois, environ 12 fichiers de 60 Mo sont lus en continu, sans être enregistrés (quelques minutes). Ensuite, seuls les nouveaux mois sont lus |
| `--nouveautes` | Résumé des nouvelles offres depuis la collecte précédente (stages, offres proches du CV avec `--cv`, puis les autres par score DEC), enregistré dans `rapport-nouveautes.md` |
| `--score-dec` | Classe les offres affichées selon le score « étudiant du DEC », avec l'explication de chaque score (`--nb-offres` pour en voir plus que 10) |

Les filtres changent ce qui est affiché, ce qui va dans le CSV et ce qui va dans la page HTML. `offres.json` garde toujours toutes les offres.

La liste complète des options s'obtient avec `python main.py --help`.

### Fichiers produits

| Fichier | Contenu | Dans Git ? |
|---|---|---|
| `offres.json` | Toutes les offres avec tous les champs, et les statistiques | Non |
| `offres.csv` | Les offres affichées, pour Excel | Non |
| `offres.html` | La page de recherche à ouvrir dans le navigateur | Non |
| `echantillon.json` | 10 offres d'exemple | Oui |
| `cv-exemple.txt` | CV fictif pour essayer l'aide à la candidature | Oui |
| `rapport-candidature.md` | Classement des offres selon un CV, avec les suggestions | Non |
| `rapport-nouveautes.md` | Résumé des nouvelles offres (`--nouveautes`) | Non |
| `lettre-exemple.txt` | Lettre fictive pour essayer la vérification de lettre | Oui |
| `rapport-lettre.md` | Vérification d'une lettre pour une offre | Non |
| `historique-collectes.csv` | Une ligne par collecte : offres, nouvelles, disparues | Non |
| `donnees-ouvertes.json` | Résumé mois par mois des données ouvertes (`--donnees-ouvertes`), avec la source et la licence | Non |
| `journal-collectes.log` | Ce qu'a affiché chaque collecte lancée par `collecte-reguliere.ps1` | Non |
| `collecte-reguliere.ps1`, `planifier-collecte.ps1` | Scripts de collecte régulière et automatique | Oui |
| `regions_quebec.csv` | Municipalités et arrondissements du Québec avec leur région (source officielle, voir plus bas) | Oui |
| `cache/fiches/` | Les fiches déjà téléchargées | Non |

### Si ça ne marche pas

- **`python` n'est pas reconnu** : utiliser `py`, ou installer Python depuis python.org en cochant « Add Python to PATH ».
- **`No such file or directory: main.py`** : la commande n'est pas lancée depuis le dossier du projet (voir l'étape 1).
- **`Format .pdf non pris en charge`** : ouvrir le CV dans Word, puis « Enregistrer sous » au format `.docx`.
- **« Technologies trouvées dans le CV : aucune »** : écrire les technologies clairement dans le CV, par exemple « Langages : Python, Java, SQL ».
- **`Impossible de lire offres.json`** : faire d'abord une collecte (étape 3) avant d'utiliser `--depuis`.
- **La page `offres.html` ne montre pas les dernières offres** : rafraîchir la page (F5). La date « page créée le … » en haut doit correspondre au dernier lancement de `main.py`. Si la page a été supprimée, le prochain `python main.py` la recrée.
- **`Offres affichées : 0`** : les filtres sont trop stricts. Par exemple, `--ville` demande le nom exact de la ville, comme `Québec` et non `Qc`.

## 1. Site choisi

**Guichet-Emplois** (`https://www.guichetemplois.gc.ca/jobsearch/rechercheemplois`), offres TI au Québec : 14 codes CNP, `fprov=QC`. Remotive reste une source d'appoint pour le télétravail.

J'ai choisi ce site parce que c'est celui qui a été le plus exploré dans la classe (Hugo, Mamadou, Dan, moi), et parce qu'il affiche aussi les offres de Jobillico, Québec emploi, Talent.com et d'autres partenaires.

## 2. Contributions consultées

| Contribution | Méthode | Données obtenues | Difficultés |
|---|---|---|---|
| [Mon L2](../02-preuve-de-concept-scraping/compte-rendu-livrable-2.md) | Pages de résultats HTML, 14 codes CNP | 191 offres, toutes les pages | Pas de description, titres CNP, 0 stage |
| [Hugo](https://github.com/chergreg/jobs-insights/blob/main/equipe/hugo/02-preuve-de-concept-scraping/COMPTE_RENDU_LIVRABLE_2.md) | Atom + recherche par mots-clés + fiches (RDFa, repli DOM) | 87 offres avec description | Liste fixe de mots-clés, pas toutes les pages |
| [Mamadou (L3)](https://github.com/chergreg/jobs-insights/blob/main/equipe/mamadou/03-amelioration-preuve-de-concept/poc_guichet_cnp_v2.py) | Codes CNP + fiches RDFa (BeautifulSoup), cache 24 h | Échantillon de 22 offres (5 sources) | Nombre de pages à choisir (`--pages N`), dépendances externes |
| [Gregory (démo L3)](https://github.com/chergreg/jobs-insights/blob/main/equipe/gregory/livrable3/scrapers/guichet_emplois.py) | Ma pagination + l'enrichissement de Hugo, cache des fiches | 140 offres unifiées (3 sources) | Démonstration du prof |
| [Dan](https://github.com/chergreg/jobs-insights/blob/main/equipe/dan/02-preuve-de-concept-scraping/compte-rendu.md) | Page de résultats HTML (BeautifulSoup), mes 14 codes CNP | 25 offres (1re page, CSV) | Pas de pagination, pas de description ni de site d'origine |

Je me suis aussi appuyé sur la [synthèse du L2](https://github.com/chergreg/jobs-insights/blob/main/livrables/02-preuve-de-concept-scraping/synthese.md), la [synthèse du L3](https://github.com/chergreg/jobs-insights/blob/main/livrables/03-amelioration-preuve-de-concept/synthese.md) et le [plan de Gregory](https://github.com/chergreg/jobs-insights/blob/main/equipe/gregory/livrable3/plan.md). Tous ces documents relèvent la même limite pour mon L2 : les fiches n'étaient pas lues.

**Ce que j'ai vérifié moi-même :**

- J'ai ouvert 3 fiches (Guichet-Emplois, Jobillico, Québec emploi). Elles contiennent les balises RDFa utilisées par Hugo et Mamadou : `description`, `validThrough`, `minValue`/`maxValue`/`unitText`, `employmentType`, `educationRequirements`, `experienceRequirements`, `postalCode`.
- Les fiches des partenaires affichent aussi le titre écrit par l'employeur (`span.source-title-inner`) et un lien vers l'annonce d'origine (`a#externalJobLink`). Mamadou utilisait aussi ce titre.
- Le plan de Mamadou présente `fsrc=16` comme un « filtre stages ». Je l'ai testé : il donne 71 offres, toutes publiées directement sur le Guichet-Emplois. C'est donc un filtre de **source** (16 est aussi le numéro de l'icône du Guichet-Emplois dans le HTML), pas un filtre de stages.
- Il n'y a pas de latitude/longitude sur les fiches du Guichet-Emplois, seulement le code postal. Mamadou obtient le GPS sur Talent.com, un autre site.

## 3. Amélioration choisie

**Lire la fiche de chaque offre trouvée par ma pagination**, pour compléter les données de la liste. C'est exactement l'exemple de l'énoncé : une approche trouve les liens, une autre lit le détail.

**Ce que j'ai repris :**

- de mon L2 : la pagination sans plafond par codes CNP, le site d'origine des offres, la déduplication et la détection des stages ;
- de Hugo et Mamadou : l'idée de lire les balises RDFa de la fiche et de décoder le HTML encodé deux fois des partenaires ;
- de Hugo : sa liste de technologies `TECH_PATTERNS`, sans faux positifs sur « C » seul ni sur « vue d'ensemble » ;
- de Gregory et Mamadou : un cache des fiches sur disque, pour respecter les 5 s du `robots.txt` sans attendre 16 minutes à chaque essai.

**Ce que j'ai modifié :**

- Tout est réécrit avec la bibliothèque standard (`html.parser`) : pas de BeautifulSoup ni de Pydantic, donc aucune installation.
- Le prototype est découpé en modules : `guichet`, `fiches`, `remotive`, `normalisation`, `competences`, `fusion`, `analyse`, `regions`, `filtres`, `export`, `interface` (avec `interface_cv.js`, `interface_stats.js` et `interface_suivi.js`), `candidature`, `lettre`, `historique`, `main`.
- Nouveaux champs :
  - titre de l'employeur, description, tâches ;
  - date d'expiration et date de début ;
  - type d'emploi, études, expérience, langues ;
  - ville, province, code postal ;
  - salaire en chiffres (minimum, maximum, unité, devise, « à négocier ») ;
  - technologies, compétences, années d'expérience, niveau et description courte.
- Stages : le champ « Stage: Ce poste est un stage… » du Guichet-Emplois est reconnu, et la détection se fait aussi sur le vrai titre et la description.
- Statistiques : top technologies, salaires par unité (jamais mélangés), villes, expirations proches, champs remplis.
- Deux défauts de la source sont corrigés :
  - dans 10 fiches, des séquences d'échappement Unicode écrites telles quelles (barre oblique inverse + `u00E9` au lieu de « é ») ;
  - des `&amp;` encodés deux fois.
- Région administrative de chaque offre (module `regions`) : la ville est cherchée dans le Répertoire des municipalités du Québec (ministère des Affaires municipales et de l'Habitation, données ouvertes sous licence CC-BY 4.0). La liste officielle des arrondissements sert pour Saint-Laurent, Lachine, etc. Le fichier `regions_quebec.csv` garde seulement le nom, le type et la région, sans aucun nom d'élu. Il est recréé par `preparer_regions.py`.
- Page de recherche `offres.html` (module `interface` et modèle `interface_modele.html`) : un seul fichier qui s'ouvre dans le navigateur, avec les offres incluses. Il n'y a ni serveur, ni Internet, ni bibliothèque externe. Le JavaScript affiche les textes des offres avec `textContent`, jamais comme du HTML : un texte d'offre ne peut pas devenir du code.
- Aide à la candidature, piste 4 du projet (module `candidature`) :
  - le CV (`.docx` ou `.txt`) est lu sur l'ordinateur, sans service extérieur ;
  - il est comparé aux offres avec les mêmes listes de technologies et de compétences que pour les offres, et une note sur 100 dont chaque partie est expliquée ;
  - le programme donne des suggestions pour adapter le CV à une offre, sans jamais rien inventer sur le candidat ;
  - options `--cv`, `--nb-offres` et `--rapport-cv`.
- Comparaison avec le CV dans la page `offres.html` (script `interface_cv.js`) :
  - au moment de créer la page, `interface.py` y copie les expressions de `competences.py` et `candidature.py`. La page et `main.py --cv` utilisent donc les mêmes règles ;
  - le `.docx` est lu dans le navigateur, sans bibliothèque (`DecompressionStream`).
- Vérification d'une lettre de motivation (module `lettre`), options `--lettre`, `--offre` et `--rapport-lettre`. Elle se fait aussi dans la page, avec le bouton « Vérifier ma lettre pour cette offre ». La page reçoit les listes de mots de `lettre.py`.
- Collecte régulière (module `historique`) :
  - comparaison avec la collecte précédente : offres nouvelles et disparues ;
  - badge « Nouvelle » et filtre dans la page ;
  - annonces semblables regroupées sur une seule carte, et badge « Republiée » (module `semblables`) ;
  - historique CSV et ménage du cache (`--nettoyer-cache`) ;
  - scripts PowerShell `collecte-reguliere.ps1` et `planifier-collecte.ps1` (Planificateur de tâches de Windows).
- Filtres et export : `--ville`, `--region`, `--techno`, `--niveau`, `--stages`, `--salaire-min`, `--employeur`, export `--csv` pour Excel, et `--depuis` pour filtrer une collecte déjà faite sans Internet (modules `filtres` et `export`).

Le code est dans ce dossier. Le prototype du L2 reste tel quel dans `02-preuve-de-concept-scraping/`.

Commits sur `main` :

| Étape | Commit |
|---|---|
| Plan | [`0dc34f1`](https://github.com/chergreg/jobs-insights/commit/0dc34f1) |
| Modules | [`d298b96`](https://github.com/chergreg/jobs-insights/commit/d298b96) |
| Fiches | [`e1dbea9`](https://github.com/chergreg/jobs-insights/commit/e1dbea9) |
| Salaire et lieu | [`c781672`](https://github.com/chergreg/jobs-insights/commit/c781672) |
| Technologies et niveau | [`7aa7e60`](https://github.com/chergreg/jobs-insights/commit/7aa7e60) |
| Statistiques | [`c1f687e`](https://github.com/chergreg/jobs-insights/commit/c1f687e) |

## 4. Commandes

Le guide au début de cette note explique tout pas à pas, filtres et CSV compris. Les mêmes commandes, lancées depuis la racine du dépôt :

```powershell
# Collecte complète : environ 17 min la première fois (5 s par fiche), environ 1 min ensuite grâce au cache
python .\03-amelioration-preuve-de-concept\main.py --echantillon .\03-amelioration-preuve-de-concept\echantillon.json

# Essai court sur 5 fiches
python .\03-amelioration-preuve-de-concept\main.py --max-fiches 5

# Sans les fiches (comme au L2)
python .\03-amelioration-preuve-de-concept\main.py --sans-fiches

# Filtrer une collecte déjà faite, sans Internet, et exporter pour Excel
python .\03-amelioration-preuve-de-concept\main.py --depuis .\03-amelioration-preuve-de-concept\offres.json --techno Python --csv

# Page de recherche à ouvrir dans le navigateur
python .\03-amelioration-preuve-de-concept\main.py --depuis .\03-amelioration-preuve-de-concept\offres.json

# Comparer un CV avec les offres (aide à la candidature)
python .\03-amelioration-preuve-de-concept\main.py --depuis .\03-amelioration-preuve-de-concept\offres.json --cv .\03-amelioration-preuve-de-concept\cv-exemple.txt --rapport-cv

# Vérifier une lettre de motivation pour une offre
python .\03-amelioration-preuve-de-concept\main.py --depuis .\03-amelioration-preuve-de-concept\offres.json --lettre .\03-amelioration-preuve-de-concept\lettre-exemple.txt --offre 50585958

# Collecte régulière : comparaison avec la collecte précédente, page à jour, ménage du cache
python .\03-amelioration-preuve-de-concept\main.py --nettoyer-cache --html --resume-seulement

# Tests hors ligne (275 tests)
python -m unittest discover -s 03-amelioration-preuve-de-concept -p "test_*.py" -v
```

Sorties :
- `offres.json` : toutes les offres et les statistiques. Ce fichier n'est pas dans Git.
- [`echantillon.json`](echantillon.json) : 10 offres enrichies.
- `cache/fiches/` : fiches déjà lues, pas dans Git.

## 5. Vérification

### Avant / après

| Mesure | L2 (12 nov.) | L3 (17 nov.) |
|---|---|---|
| Offres du Guichet-Emplois récupérées | 191 / 191 | 188 / 189 (1 offre retirée pendant la collecte) |
| Fiches lues | 0 | 188 / 188, 0 erreur |
| Description | 0 | 132 / 186 |
| Titre de l'employeur | 0 | 114 |
| Date d'expiration | 0 | 184 |
| Salaire en chiffres | 0 (texte seulement) | 186 / 186 |
| Ville et province séparées | 0 | 179 / 186 |
| Région administrative | 0 | 178 / 179 offres avec ville (Saint-Antoine-Abbé, un hameau, n'est pas une municipalité) |
| Études, expérience, langues | 0 | 71 |
| Technologies détectées | 0 | 83 offres |
| Niveau (débutant, intermédiaire, avancé) | 0 | 124 offres |
| Stages détectés | 0 | 1 confirmé |
| Tests hors ligne | 33 | 275 |

Les compteurs de la dernière colonne viennent du résumé de `offres.json` (`summary.filled_fields`).

### Contrôle des données

- **Salaire :** pour les 188 offres, le montant lu dans le texte de la liste est identique à celui des balises RDFa de la fiche. 0 différence.
- **5 fiches ouvertes en ligne le 17 novembre**, comparées aux données collectées : 2 du Guichet-Emplois, 1 de Jobillico, 1 de Québec emploi, 1 de Talent.com.
  - Le titre, l'employeur, la date d'expiration et le salaire correspondent pour les 5.
  - La description correspond pour 4. La 5e, celle de Québec emploi, est une offre fusionnée avec sa copie Jobillico : sa description vient de la fiche Jobillico, comme prévu.
  - Les technologies détectées sont bien écrites dans les pages. Par exemple, « Postgres » donne PostgreSQL.
- **Détections risquées :** j'ai relu le texte autour des technologies les plus risquées (Windows, Oracle, SAP, Swift, Rust, Cisco, Git, Java). Toutes correspondent à de vraies mentions.

### Vérification de la page HTML

Les tests Python vérifient le contenu de la page :
- les offres incluses ;
- un titre piégé `</script>` qui ne casse pas la page ;
- aucune ressource externe ;
- aucun `innerHTML`.

J'ai aussi ouvert la vraie page (195 offres) dans Edge en mode sans fenêtre (`--headless --dump-dom`), avec des filtres passés dans l'adresse. La page donne les mêmes nombres que les filtres de `main.py` :

| Filtre | Page HTML | `main.py` |
|---|---|---|
| Région Montérégie | 48 | 48 |
| Capitale-Nationale + SQL | 6 | 6 |
| Python | 18 | 18 |
| Niveau débutant | 27 | 27 |
| Stages | 1 | 1 |
| Salaire ≥ 90 000 $ / an | 29 | 29 |
| Montréal + ≥ 40 $ / h | 9 | 9 |

Une copie de test de la page a aussi cliqué elle-même sur les boutons :
- « Afficher plus » : 30, puis 60, puis 90 offres ;
- choix de l'Estrie : seules Sherbrooke, Coaticook et Valcourt sont proposées comme villes ;
- export CSV : 5 offres, et le fichier commence par les octets `EF BB BF` pour qu'Excel lise les accents ;
- « Effacer les filtres » : retour à 195 ;
- clic sur « SQL » : 32 offres.

Des captures d'écran sur ordinateur, sur téléphone (375 pixels) et en mode sombre ont permis de corriger trois défauts avant l'ajout :
- un bouton « Afficher plus (0 restantes) » visible à tort ;
- un titre de filtres mal espacé ;
- un texte de bouton peu lisible en mode sombre.

### Vérification de l'aide à la candidature (20 novembre)

J'ai fait l'essai avant d'écrire le module, avec deux CV fictifs comparés aux 195 vraies offres :
- une étudiante en développement qui cherche un stage ;
- un technicien en soutien et réseau avec 2 ans d'expérience.

L'essai a montré trois défauts de la première règle de note, corrigés avant l'ajout :

| Défaut observé | Correction |
|---|---|
| Une offre qui ne liste que « Python » avait la note maximale sur les technologies avec 1 seule technologie en commun | La note tient compte aussi du nombre de technologies en commun (jusqu'à 4) |
| L'étudiante recevait des postes « avancés » (chef de projet, administrateur de bases de données senior) | Moins de points quand l'offre est d'un niveau au-dessus du CV, aucun quand elle est deux niveaux au-dessus |
| Pour le technicien, les 5 premières offres ne listaient qu'un seul élément (« Réseaux ») : 100/100 sans vraie information | Une offre avec peu d'éléments garde 70 % à 90 % de sa note |

**Résultat après correction :**

- **Étudiante :** 1re offre « développeur Web full-stack », niveau débutant, 6 technologies sur 7 en commun (95/100). Le seul stage trouvé est signalé à part.
- **Technicien :** 1res offres « administrateur réseaux », avec 4 ou 5 éléments en commun (Windows, Active Directory, VMware…).

**Lecture des CV :**

- un vrai `.docx` créé par Word se lit sans bibliothèque externe, et son texte est identique à la version `.txt` ;
- un PDF est refusé avec un message qui explique quoi faire.

**Tests :** 21 nouveaux tests dans `test_candidature.py`. Ils vérifient notamment :
- un `.docx` construit dans le test (avec un tableau et des sauts de ligne) ;
- un ancien stage, sans recherche de stage, qui ne doit pas être compté comme recherche ;
- « Bilingue » compris comme français et anglais ;
- aucune suggestion inventée.

### Vérification du CV dans la page et de la lettre (20 novembre)

**CV dans la page.** Essai fait avant de modifier la page :
- les 72 expressions de Python fonctionnent telles quelles en JavaScript ;
- pour 3 CV fictifs et les 195 vraies offres, le calcul JavaScript (exécuté avec Node.js) donne le même profil et la même note que Python pour chaque offre (0 différence) ;
- un vrai `.docx` créé par Word est lu dans Edge sans bibliothèque, avec le même texte que la version `.txt`.

Une fois la page faite, une copie de test a rempli le panneau elle-même dans Edge :
- CV collé (2 profils) et vrai fichier Word : les 10 premières offres et leurs notes sont identiques à `main.py --cv` ;
- avec le filtre région Montréal, le tri par correspondance est gardé ;
- « Retirer le CV » efface tout, et le CV n'apparaît jamais dans l'adresse de la page ;
- un PDF est refusé avec un message.

Captures sur ordinateur et sur téléphone (375 pixels) : rien ne dépasse de l'écran.

Le test `test_interface_cv.py` compare automatiquement les notes JavaScript et Python. Pour vérifier qu'il sert à quelque chose, je lui ai donné une copie du script avec une seule règle changée (50 points au lieu de 55) : il a échoué, comme il le devait.

**Lettre.** Essai avec une lettre fictive (`lettre-exemple.txt`) pour l'offre « développeur Web full-stack ». Deux défauts trouvés et corrigés avant l'ajout :
- l'employeur était déclaré « cité » parce que la lettre contenait le mot « les » (« Les technologies Duologiq »). On compare maintenant les mots distinctifs du nom ;
- le titre était déclaré « cité » à cause du seul mot « développer ». Il faut maintenant 2 mots importants sur 3 du titre.

Après correction, la lettre fictive est bien signalée : `[nom du poste]` oublié, employeur et poste absents, 4 technologies de l'offre absentes, lettre courte (114 mots). Une fois la lettre corrigée, ces remarques disparaissent.

**Lettre dans la page.** Essai fait avant de modifier la page : la vérification écrite en JavaScript donne les mêmes vérifications et les mêmes phrases que `lettre.py` dans **780 cas sur 780** (4 lettres × 195 vraies offres, avec et sans CV).

Ensuite, dans Edge, une copie de test de la vraie page a fait elle-même les étapes :
- ouvrir la fenêtre d'une offre et coller la lettre : 7 suggestions, identiques à Python ;
- charger le CV puis choisir la lettre en vrai fichier Word : 8 suggestions, identiques à Python ;
- fermer et rouvrir : la lettre est gardée ;
- un PDF est refusé avec un message.

Les captures sur ordinateur et sur téléphone ont fait corriger un champ « Choisir un fichier » qui dépassait sur téléphone.

Le test automatique de la lettre a d'abord été trop faible : avec un script volontairement modifié (mots comparés sur 4 lettres au lieu de 5), il passait encore. J'ai ajouté un cas où cette différence compte (« partenaires » et « participé »). Maintenant, il échoue avec le script modifié.

### Vérification de la collecte régulière (20 novembre)

Essai d'abord : une nouvelle collecte le 20 novembre, enregistrée à part et comparée à celle du 17 novembre.

| Mesure | Résultat |
|---|---|
| Annonces le 17 / le 20 | 197 / 197 |
| Nouvelles | 24 (12 %) |
| Disparues | 24, dont 14 avant leur date limite (sans doute des postes déjà pourvus) |
| Fiches du cache devenues inutiles | 23 |

Sans nouvelle collecte, la page aurait donc montré 24 offres qui n'existent plus et caché 24 nouvelles.

Une fois le code ajouté, j'ai lancé `collecte-reguliere.ps1` pour de vrai, comme le ferait le Planificateur :
- collecte en 58 s, sans erreur ;
- 24 nouvelles et 24 disparues, mêmes chiffres que l'essai ;
- 23 fiches retirées du cache (de 213 à 190) ;
- historique et journal écrits, avec les accents intacts.

J'ai aussi vérifié dans Edge :
- l'en-tête indique « 24 nouvelles offres depuis la collecte du 17 novembre 2026 » ;
- le filtre « Nouvelles offres seulement » donne exactement 24 offres, et 12 avec la région Montréal.

`planifier-collecte.ps1` a seulement été vérifié (syntaxe PowerShell correcte). Il n'a pas été lancé : la tâche s'ajoute à l'ordinateur seulement quand on l'exécute soi-même.

Les 13 nouveaux tests (`test_historique.py`) vérifient notamment :
- deux collectes simulées de suite (1 nouvelle, 1 disparue) ;
- une offre retrouvée chez un autre partenaire, qui ne doit pas être comptée comme nouvelle ;
- un `offres.json` précédent absent ou abîmé ;
- l'historique, avec une seule ligne d'en-tête ;
- le ménage du cache, qui ne se fait pas après une collecte partielle ;
- le marqueur UTF-8 des scripts PowerShell.

### Vérification des annonces semblables (24 novembre)

Question de départ : dans la page, trois cartes « Bilingual Mortgage Operations Specialist » de Recrute Action se suivaient (deux à Montréal, une à Laval). Étaient-ce des doublons ?

Essai sur la collecte du 24 novembre (183 annonces) :

| Constat | Nombre |
|---|---|
| Groupes d'annonces avec le même titre, le même employeur et le même site | 10 groupes, 21 annonces |
| Postes publiés le même jour dans plusieurs villes (Recrute Action, FOP Experts Conseils) | 5 |
| Postes republiés plus tard alors que l'ancienne annonce était encore en ligne (Ville de Québec, Kativik) | 3 |
| Description identique ou presque (quand elle existe) | 7 groupes sur 8 (le 8e : la même offre, une fois en anglais et une fois en français) |

- Chaque annonce a son propre numéro sur le Guichet-Emplois. Ce ne sont donc pas des erreurs de collecte, et `fusion.py` a raison de ne pas les fusionner : un employeur peut avoir plusieurs postes identiques à pourvoir.
- Les 3 postes republiés étaient comptés comme « nouvelles offres », alors que l'annonce précédente était déjà en ligne.

Ce qui a été ajouté :
- `semblables.py` dit quelles annonces vont ensemble. Rien n'est supprimé : toutes les annonces restent dans `offres.json`, dans le CSV et sur la carte ;
- dans la page, une carte par poste : 172 offres (183 annonces) ;
- en haut de la page : « 14 nouvelles offres depuis la collecte du 23 novembre 2026 (et 3 annonces republiées) ». Le filtre « Nouvelles offres seulement » donne aussi 14 offres.

Vérifié dans Edge avec la vraie collecte : la recherche « mortgage » donne 1 offre (3 annonces), avec Montréal et Laval listées sur la carte. Les 9 nouveaux tests (`test_semblables.py`) couvrent le cas de Recrute Action, les accents et la ponctuation dans les titres, un autre employeur ou un autre site (pas regroupés), un employeur absent (jamais regroupé) et le compte des nouvelles offres.

### Vérification des offres sans description (24 novembre)

Essai sur la collecte du 24 novembre : 43 offres sur 183 (23 %) n'ont pas de description.

| Site d'origine | Sans description |
|---|---|
| Québec emploi | 24 sur 25 |
| Talent.com | 15 sur 21 |
| indeed.com | 3 sur 4 |
| ZipRecruiter | 1 sur 1 |
| Guichet-Emplois, Jobillico, JobsMedia.ca, Remotive | 0 |

- Dans les fiches en cache, ces offres n'ont que le titre, l'employeur, le lieu, le salaire, les dates et le lien « Voir l'offre d'emploi complète sur … ». Il n'y a pas d'autre texte à lire sur le Guichet-Emplois.
- Aller chercher le texte chez le partenaire n'est pas permis : les conditions d'utilisation de Québec emploi l'interdisent (voir les limites), comme les règles des autres sites.
- Elles ont quand même un salaire (43 sur 43), un lien d'origine (43 sur 43) et parfois un niveau (17 sur 43). Le seul stage confirmé (« Stagiaire en développement informatique », Revenu Québec) en fait partie.

Ce qui a été ajouté : l'encadré sur la carte, la case « Description complète seulement », la colonne `description_complete` dans l'export CSV de la page, et la ligne « Sans description (détail seulement sur le site d'origine) : 43 {'Québec emploi': 24, …} » dans le résumé du terminal.

Vérifié dans Edge avec la vraie collecte : 172 offres sans filtre, 132 offres (140 annonces) avec la case cochée. La carte du stage de Revenu Québec affiche l'encadré et le lien vers Québec emploi. Les 3 nouveaux tests (`test_sans_description.py`) vérifient aussi qu'une description faite seulement d'espaces compte comme absente.

### Vérification de l'onglet Statistiques (24 novembre)

Essai d'abord, pour savoir quels chiffres sont assez fiables pour un graphique (collecte du 24 novembre, 183 annonces) :

| Donnée | Remplie | Décision |
|---|---|---|
| Région | 170 sur 183 | graphique, avec « Non précisé » à la fin |
| Salaire | 96 annuels, 72 horaires | deux médianes séparées, jamais mélangées |
| Niveau | 128 sur 183 | graphique, avec « Non précisé » |
| Technologies | 80 offres en citent au moins une | graphique, et ce nombre est écrit |
| Mode de travail | 84 sur 183 | pas de graphique : trop d'offres sans information |
| Type d'emploi | mots différents selon la source (« Permanent, Temps plein », `full_time`…) | pas de graphique |
| Historique | 6 collectes sur 3 jours | une colonne par jour (la dernière collecte du jour) |

Piège trouvé dans l'historique : le 23 novembre, quatre collectes ont été lancées en une heure. La colonne « nouvelles » de la dernière (1 nouvelle) compare avec la collecte précédente de 44 minutes plus tôt, pas avec la veille. Le graphique montre donc seulement le nombre d'offres en ligne chaque jour.

Ce qui a été ajouté :
- `interface_stats.js` fait les calculs avec les mêmes règles que `analyse.py` ;
- `historique.read_history` lit l'historique, avec une ligne par jour ;
- dans la page, l'onglet avec 4 tuiles (offres, salaire annuel médian, salaire horaire médian, stages) et 6 graphiques en barres d'une seule couleur, avec la valeur écrite au bout de chaque barre. La couleur a été vérifiée en mode clair et sombre (contraste avec le fond).

Vérifications :
- sur la vraie collecte, la page et `analyse.py` donnent les mêmes chiffres : 96 salaires annuels (médiane 71 860 $), 72 horaires (médiane 35,50 $), et les mêmes technologies, régions et niveaux. Dans l'onglet, les annonces semblables comptent pour une offre : 87 salaires annuels, médiane 70 720 $ ;
- les 7 nouveaux tests (`test_interface_stats.py`) comparent avec Python à l'aide de Node.js, et vérifient la médiane d'un nombre pair de valeurs, le taux horaire jamais compté dans le salaire annuel et la lecture de l'historique (ligne abîmée ignorée). J'ai vérifié qu'ils échouent si on mélange les unités de salaire ou si on oublie « Non précisé » ;
- dans Edge : mode clair, mode sombre, et largeur de téléphone avec le filtre Capitale-Nationale (25 offres : les graphiques suivent le filtre).

### Vérification du suivi des candidatures (24 novembre)

Essai d'abord, dans Edge, avec une page locale (`file://`) comme `offres.html` :
- le navigateur garde les données d'une page locale après une nouvelle ouverture, après que le fichier a été recréé, et même quand la page est copiée dans un autre dossier ;
- toutes les pages locales partagent le même stockage. Le suivi a donc un nom propre au projet (`jobs-insights-kandet.suivi.v1`) ;
- une offre garde le même lien (numéro du Guichet-Emplois) d'une collecte à l'autre. C'est ce lien qui sert à la reconnaître : entre le 23 et le 24 novembre, 164 offres ont été retrouvées ainsi.

Ce qui a été ajouté : `interface_suivi.js`, le bouton « Suivre » et le statut sur les cartes, la case « Mes offres suivies seulement », l'onglet « Mes candidatures » (statut, note, retrait, export CSV). Une copie du titre, de l'employeur et des liens est gardée, pour qu'une offre disparue reste dans le suivi.

Vérifications :
- dans Edge, avec de vrais clics : suivre le stage de Revenu Québec, passer à « Postulé », rouvrir la page (le statut est toujours là), ajouter une note, filtrer « Mes offres suivies seulement » (1 offre sur 172), puis retirer l'offre ;
- capture de l'onglet avec une offre en entrevue et une offre fictive disparue (badges « N'est plus dans la dernière collecte » et « Expirée ») ;
- les 7 nouveaux tests (`test_interface_suivi.py`) utilisent Node.js avec un faux stockage. Ils vérifient la relecture après une nouvelle ouverture, un statut inconnu refusé, un stockage abîmé (la page repart d'un suivi vide sans planter), un stockage bloqué (le message s'affiche), l'export CSV (une note qui commence par `=` n'est pas lue comme une formule par Excel), et l'absence de toute requête réseau dans la page.

### Vérification du score « étudiant du DEC » (24 novembre)

Les technologies du programme viennent de la [liste officielle des cours](https://osullivan-quebec.qc.ca/dec-informatique/cours-dec-techniques-de-linformatique-420-b0/) du DEC 420.B0 d'O'Sullivan de Québec (profil développement d'applications), lignes « Langages abordés ». Elles sont dans `programme_dec.json`, avec la source et la date. Pour comparer, j'ai aussi lu les grilles du Cégep de Sorel-Tracy (Web et mobile) et du Cégep de Saint-Hyacinthe (développement de logiciels, réseaux et cybersécurité). On y retrouve la même base : SQL, Java ou C#, HTML/CSS/JavaScript, PHP et le mobile. Le Collège O'Sullivan de Montréal est un autre établissement, avec un DEC en réseaux et cybersécurité : il n'est pas utilisé.

Essai d'abord sur la collecte du 24 novembre :
- 16 technologies du programme étaient déjà reconnues. jQuery (8 offres), XML (5) et SOAP (3) ont été ajoutés à `competences.py`. Unity n'a pas été ajouté : les 3 offres trouvées parlaient de « Unity Catalog » (données), pas du moteur de jeu ;
- premier classement : le stage de Revenu Québec en tête (70), puis des postes débutants en Java, C#, SQL, Angular (60), et les postes d'architecte senior en bas (0) ;
- défaut trouvé : une offre qui ne cite que « Windows » recevait les 30 points des technologies, autant qu'une offre avec Java, HTML/CSS et Angular. On compte maintenant au moins 3 technologies : « Windows » seul donne 10 points.

Vérifications : `python main.py --depuis offres.json --score-dec` et la page triée par score donnent le même ordre. Les 9 nouveaux tests (`test_score_dec.py`) vérifient les points de chaque critère, l'explication, la règle des 3 technologies, que chaque technologie du programme peut être trouvée dans une offre, et les nouvelles technologies (« XMLHttpRequest » n'est pas compté comme XML).

### Vérification des données ouvertes (24 novembre)

Recherche d'autres sources autorisées :

| Source | Décision |
|---|---|
| [Données ouvertes du Guichet-Emplois](https://open.canada.ca/data/fr/dataset/ea639e28-c0fc-48bf-b5dd-b8899bd43072) (Emploi et Développement social Canada) | **Retenue.** [Licence du gouvernement ouvert – Canada](https://ouvert.canada.ca/fr/licence-du-gouvernement-ouvert-canada), un fichier CSV par mois depuis janvier 2023, sans compte ni clé |
| [API d'Adzuna](https://developer.adzuna.com/docs/terms_of_service) | Possible pour la recherche personnelle ou académique, mais il faut un compte, une clé et le logo « Adzuna » sur chaque offre affichée. Le Canada n'est pas mentionné. Non ajoutée pour l'instant |
| Jooble | Écartée : les conditions interdisent les robots et la republication |

Essai sur le fichier d'octobre 2026 (59 130 offres au Canada) :
- 197 offres TI au Québec avec nos 14 codes CNP. Salaire annuel médian : 70 000 $ ; horaire : 36 $. Ce sont les mêmes valeurs que notre propre collecte ;
- pas d'employeur, pas de description et pas de lien vers l'offre : ces fichiers servent aux statistiques, pas à postuler ;
- certaines offres sont mal classées par la source (« Work From Home Sales Consultant » avec un code TI). Elles sont comptées telles quelles ;
- le fichier utilise les régions économiques. La région administrative est retrouvée à partir de la ville (`regions.py`), comme pour la collecte.

Ce qui a été ajouté :
- `donnees_ouvertes.py` trouve les fichiers avec l'API du portail. Le mois est lu dans le nom de la ressource, parce que les noms de fichiers changent (`oct2026`, `octobre2023`, `june-2024`…) ;
- chaque fichier (UTF-16, tabulations) est lu en continu et n'est jamais enregistré. On garde seulement un résumé par mois dans `donnees-ouvertes.json` ;
- dans l'onglet Statistiques, deux graphiques : les offres TI au Québec par mois et le salaire annuel médian par mois, avec la source et la mention de la licence.

Ce que le vrai essai a trouvé : la ressource française d'avril 2026 n'a pas d'adresse sur le portail (seul le fichier anglais existe). La première lecture s'est arrêtée à ce mois. Après correction, un fichier sans adresse est ignoré, un mois en erreur n'arrête plus les autres, et la page écrit « Mois absent : avr. 2026 ». Résultat : 12 mois, d'octobre 2025 à octobre 2026, entre 99 offres (décembre 2025) et 333 (octobre 2025). Le salaire annuel médian varie de 60 000 $ à 80 000 $.

Les 6 nouveaux tests (`test_donnees_ouvertes.py`) utilisent un faux portail et de petits faux fichiers UTF-16. Ils vérifient la lecture du mois dans le nom, le cas réel sans adresse, le filtre Québec et TI, les salaires (« NA » ignoré), les régions, les mois déjà lus qui ne sont pas retéléchargés, un mois en erreur qui n'arrête pas les autres, et la mention de la licence dans la page.

### Vérification du résumé des nouveautés (24 novembre)

Essai d'abord sur la collecte du 24 novembre : 14 nouvelles offres depuis le 23 novembre. Classées seulement avec le CV fictif (`cv-exemple.txt`), 7 recevaient une note, mais le stage de Revenu Québec n'apparaissait pas : il ne cite aucune technologie, donc la comparaison avec le CV ne peut pas le noter. Le résumé a donc trois parties : les nouveaux stages toujours en premier, puis les offres proches du CV (note d'au moins 40), puis les autres par score DEC. Chaque offre a son lien.

Résultat avec le CV fictif : le stage de Revenu Québec en premier (score DEC 70), puis « analyste commercial en informatique » chez IMDS Software (note 61, en commun : Python, C#, HTML/CSS, SQL), puis les autres.

`rapport-nouveautes.md` peut contenir des informations tirées du CV : il est ignoré par Git (`rapport-*.md`). Les 9 nouveaux tests (`test_nouveautes.py`) vérifient les republications et les annonces semblables, le stage sans technologie en premier, la partie CV, le cas sans collecte précédente, la liste coupée, et deux collectes simulées de suite avec `--nouveautes`.

### Vérification du bouton « Mettre à jour » (25 novembre)

Idée vue au cours du 25 novembre : lancer la collecte depuis la page plutôt que depuis le terminal. Le dossier du professeur dans le dépôt commun n'avait pas encore cette version : `serveur.py` est fait à partir de l'idée, avec la bibliothèque standard (`http.server`, `subprocess`).

Vérifications :
- dans Edge, avec une fausse collecte : le clic fait passer le bouton à « Mise à jour en cours… » et la progression s'affiche (« Recherche 3 sur 14 : analystes ») ;
- une vraie collecte lancée par le serveur, comme le bouton : 146 s, sans erreur, 184 offres, page recréée avec « page créée le 25 novembre 2026 à 19 h 26 » ;
- ouverte d'un double-clic, la page affiche l'aide au lieu du bouton ;
- les 6 tests de `test_serveur.py` démarrent le vrai serveur avec une fausse collecte : page servie, une seule collecte à la fois, lancement refusé sans l'en-tête de la page, autre nom d'hôte refusé (« DNS rebinding »), aucun autre fichier servi (ni CV, ni `offres.json`, ni cache), écoute sur `127.0.0.1` seulement ;
- le test qui vérifie que la page n'envoie rien a été rendu plus précis : les seules requêtes vont à `/api/etat` et `/api/mise-a-jour`, sans données. Le CV, la lettre et le suivi restent dans le navigateur.

### Revue des autres sources (25 novembre)

Après le cours du 25 novembre, j'ai repris tous les sites utilisés dans les dossiers des autres étudiants du dépôt commun, puis d'autres sites canadiens. Pour chacun : `robots.txt`, conditions d'utilisation, puis un appel pour voir ce qu'il apporte vraiment.

| Site | Constat | Décision |
|---|---|---|
| [Jobicy](https://jobicy.com/jobs-rss-feed) (API d'emplois à distance) | « You may use Jobicy listings in your own products [...] without requesting individual permission ». Citer Jobicy avec un lien, au plus 1 requête par seconde, un passage par heure. 51 offres TI ouvertes au Canada | **Ajouté** |
| Pages carrières [Lever](https://github.com/lever/postings-api) | « These jobs may be scraped by third parties. » | **Ajouté** (Osedea, Spiria, Mirego) |
| Pages carrières [Greenhouse](https://docs.greenhouse.io/job-board.html) | API publique sans clé, aucune interdiction, `robots.txt` permis | **Ajouté** (Levio, AlayaCare, AppDirect, Workleap, Vooban, ShareGate, Poka, Novatize, Tailscale) |
| Jobillico | Conditions : robots interdits, pas de republication sans autorisation | Écarté (ses offres arrivent déjà par le Guichet-Emplois) |
| Talent.com | Conditions : « scraping » interdit ; `robots.txt` bloque la recherche | Écarté (idem) |
| Jobboom | Conditions : pas de copie ni de republication (vérifié le 20 novembre) | Écarté |
| Himalayas | Affichage permis sur son propre site, mais pas de transmission à d'autres sites d'emploi ; offres surtout mondiales | Pas ajouté pour l'instant |
| RemoteOK | Lien obligatoire, rien sur la republication, 5 offres au Canada sur 100 | Pas ajouté |
| [Adzuna](https://developer.adzuna.com/docs/terms_of_service) | Permis pour la recherche d'emploi personnelle, avec le logo « Adzuna ». Rayan a obtenu 40 offres à Montréal par recherche. Il faut une clé (compte gratuit) | Possible plus tard, avec une clé gardée hors du dépôt |
| Welcome to the Jungle | Offres surtout en Europe (essai de Ferdinand) | Pas ajouté |
| Indeed, Monster, Workopolis, CareerBeacon | 403 ou robots refusés | Écartés (aucun contournement) |
| SmartRecruiters | `robots.txt` interdit l'API | Écarté |

Les pages carrières ont été trouvées en essayant environ 80 employeurs québécois du numérique sur Greenhouse et Lever : 12 répondent avec des offres au Québec ou au Canada. La liste est dans `pages_carrieres.json`, facile à compléter.

Essai avant l'ajout : le filtre des titres écartait à tort « Développeur.euse Java » et « Conseiller.ère en architecture infonuagique » (il cherchait des mots entiers). Corrigé : il reconnaît maintenant le début des mots, et il écarte toujours les postes de ventes, de marketing, de juristes et de comptables.

Résultat de la vraie collecte du 25 novembre : **365 offres au lieu de 184** (Guichet-Emplois 178, Remotive 7, Jobicy 51, pages carrières 130). Les liens nomment toujours la source (« Voir l'offre sur Jobicy », « Voir l'offre sur la page carrières de Levio »). Chaque réponse est gardée une heure dans le cache, et une source en erreur n'arrête pas les autres. Les 6 nouveaux tests (`test_autres_sources.py`) utilisent de faux contenus au format réel ; les collectes simulées des autres tests remplacent ces sources par un faux, pour rester hors ligne.

### Vérification du filtre « Mode de travail » (25 novembre)

Essai d'abord sur les 365 offres :
- le mode était écrit pour 158 offres : Guichet-Emplois (Sur place 42, Hybride 30, À distance 3, Sur la route 3), Jobicy et Remotive (toutes en télétravail), quelques pages carrières (« Remote (Canada) ») ;
- « Télétravail » et « À distance » veulent dire la même chose : ils sont regroupés sous « Télétravail » ;
- Lever donne un champ précis pour chaque offre (`workplaceType` : hybrid, remote, onsite). Seul « remote » était utilisé : les 36 autres offres Lever ont maintenant leur mode ;
- les descriptions parlent souvent de « hybride » ou de « télétravail », mais une phrase comme « possibilité de télétravail » ne dit pas si le poste est à distance. Elles ne sont pas utilisées : seuls le champ de la source, le lieu et le titre comptent (« Bilingual Specialist - 100% Remote »).

Résultat : Télétravail 86, Hybride 57, Sur place 42, Sur la route 3, Non précisé 177. Ajouts : `normalisation.work_mode_of`, le filtre dans la page (avec les nombres), le graphique « Mode de travail » dans l'onglet Statistiques (un clic filtre) et la colonne `mode_de_travail` de l'export CSV. Vérifié dans Edge après une vraie collecte lancée par le serveur : 84 offres en télétravail, 57 en hybride une fois les annonces semblables regroupées. Les 5 nouveaux tests (`test_mode_travail.py`) vérifient aussi que « Remotely » ou « Remotivation » ne comptent pas comme télétravail.

### Vérification des doublons entre sources (26 novembre)

Essai sur la collecte du 25 novembre (366 annonces, 365 offres) : aucun employeur des pages carrières ni de Jobicy n'était aussi sur le Guichet-Emplois, et aucune offre commune entre Jobicy, Remotive et les pages carrières. Il n'y avait donc pas de doublon caché.

Mais la règle de `fusion.py` n'aurait pas reconnu une offre de Levio publiée à la fois sur le Guichet-Emplois et sur sa page carrières :
- le Guichet-Emplois met le titre CNP (« analyste en informatique ») dans le titre, et le titre de l'employeur à part ;
- le lieu n'est pas écrit pareil (« Montréal (QC) » et « Montréal, Quebec, Canada »).

Nouvelle règle : le titre de l'employeur si les deux annonces en ont un (sinon le titre CNP, comme avant), et la ville si les deux sont connues (sinon le lieu écrit). Sur les 366 annonces réelles : toujours 365 offres, et la seule fusion existante est gardée (une annonce directe du Guichet-Emplois et sa copie de Québec emploi). Les 4 nouveaux tests (`test_fusion_sources.py`) échouent avec l'ancien code, et l'un d'eux montre un défaut de l'ancienne règle : deux postes différents du même employeur, avec le même titre CNP, publiés par deux partenaires, étaient fusionnés à tort.

### Vérification de la langue de l'annonce (26 novembre)

Avec Jobicy et les pages carrières, beaucoup d'annonces sont en anglais. La langue est mesurée dans le titre et la description, en comptant de petits mots très courants (« le, la, et, pour, avec, vous… » et « the, and, to, with, you… »). Avec moins de 15 de ces mots, on ne décide pas.

Essai sur les 365 offres :
- vérité terrain : Osedea indique (FR) ou (EN) dans le lieu de ses offres. 17 sur 18 correspondent ; la 18e (« Senior Software Developer », étiquetée FR) est entièrement en anglais (0 mot français, 116 anglais) ;
- les intitulés en français des fiches du Guichet-Emplois ne faussent pas le résultat : les annonces en anglais qui ont une description sont bien en anglais ;
- résultat : 172 en français, 129 en anglais, 2 bilingues, 62 non précisées (surtout des annonces sans description).

C'est la langue **de l'annonce**, pas les langues demandées pour le poste (celles-ci restent dans « Plus de détails »). Ajouts : `texte.announcement_language`, le filtre, le badge et la colonne `langue_annonce` de l'export CSV. Vérifié dans Edge : 164 offres en français, 128 en anglais, 59 non précisées une fois les annonces semblables regroupées ; 4 nouveaux tests (`test_langue.py`).

### Ce que les données montrent (17 novembre)

- **Salaire médian** (valeur basse de la fourchette) : 70 000 $ par année (111 offres), 36 $ de l'heure (68 offres).
- **Technologies les plus demandées :** SQL (32), JavaScript (21), Windows (19), HTML/CSS (19), Azure (18), Python (18).
- **Villes :** Montréal (50), Brossard (39, surtout une firme de recrutement), Québec (20), Sherbrooke (13).
- **Expirations :** 71 offres expirent d'ici le 24 novembre. Les offres restent en ligne peu de temps.

## 6. Limites qui restent

- **Québec emploi, Indeed et ZipRecruiter :** le Guichet-Emplois n'affiche presque jamais leur description (Québec emploi : 2 sur 40). On garde le lien vers l'annonce d'origine.
  - J'ai vérifié Québec emploi le 17 novembre. Techniquement, ce serait facile : ses pages d'offres contiennent un bloc JSON-LD `JobPosting` avec la description complète, et le `robots.txt` les autorise.
  - Mais ses [conditions d'utilisation](https://www.quebecemploi.gouv.qc.ca/conditions-d-utilisation) disent : « Il est interdit d'avoir recours à des robots ou à tout autre procédé automatisé pour accéder au site Québec emploi ou pour y collecter, extraire, générer ou exploiter des données ».
  - Je ne l'ai donc pas ajouté. Pour ces offres, il faut lire la description sur Québec emploi en suivant le lien.
- **Jobboom (vérifié le 20 novembre) :**
  - le `robots.txt` autorise les pages d'offres, et les fiches contiennent des données structurées ;
  - mais les [conditions d'utilisation](https://www.jobboom.com/carriere/conditions-utilisation) interdisent de « modifier, copier, distribuer, transmettre, diffuser, représenter, reproduire, publier […] tout information […] obtenu à partir du site ». Or notre projet copie les offres (`offres.json`) et les republie (`offres.html`, échantillons sur GitHub) ;
  - je ne l'ai donc pas ajouté. Ce point est à vérifier pour toute collecte de Jobboom dans le projet commun.
- **Stages :** un seul confirmé sur 194 offres. Il y a très peu de stages TI sur le Guichet-Emplois en ce moment, et `fsrc=16` n'est pas un filtre de stages.
- **Caractères des partenaires :** des `?` remplacent les apostrophes dans leurs textes (« d?ordinateur »). Ils sont laissés tels quels, car un `?` peut être une vraie question.
- **Salaires :**
  - pas de conversion entre heure, jour, mois et année ;
  - pour Remotive, la devise n'est pas écrite. 2 montants sans unité (`$170k - $200k`) sont gardés dans l'offre, mais ne sont pas comptés dans le tableau des salaires.
- **Niveau :** c'est une règle simple. « Architecte » dans un titre CNP donne « avancé ». 70 offres n'ont aucun indice de niveau.
- **Cache :** il ne se périme pas. Pour relire une fiche, il faut supprimer son fichier dans `cache/fiches/`.
- **Dépendance au site :** si le Guichet-Emplois change ses classes CSS ou ses balises RDFa, il faudra adapter `guichet.py` et `fiches.py`. Les tests utilisent une copie du balisage de novembre 2026.

- **Régions :** la région est trouvée à partir du nom de la ville. Un lieu qui n'est pas une municipalité ni un arrondissement (hameau, quartier, « Différentes régions ») reste sans région. Un nom porté par des municipalités de deux régions différentes reste aussi sans région, sans qu'on en choisisse une.

- **Autres sources :** Jobicy et quelques pages carrières (Tailscale, Levio à Toronto) donnent aussi des offres ailleurs au Canada ou en télétravail : elles n'ont pas de région québécoise. « Québec » seul dans un lieu peut être la ville ou la province : la ville reste alors vide. Un lieu comme « Montréal ou Québec » est gardé tel quel, sans région.

- **Données ouvertes :** elles donnent une tendance mois par mois, pas des offres. Elles ne suivent pas les filtres de la page. Le Guichet-Emplois publie chaque mois avec quelques semaines de retard (octobre 2026 était le dernier mois le 24 novembre). Un mois sans fichier français est absent du graphique, et la page le dit.

- **Score « étudiant du DEC » :** les poids (40, 30, 30) sont un choix simple, pas une mesure scientifique. La liste du programme est celle d'O'Sullivan de Québec : pour un autre cégep, il faut changer `programme_dec.json`. Les nouvelles technologies (jQuery, XML, SOAP) ne sont trouvées qu'à la prochaine collecte : `--depuis` relit les technologies déjà enregistrées dans `offres.json`.

- **Suivi des candidatures :** il est gardé dans un seul navigateur, sur un seul ordinateur. Il disparaît si on efface les données du navigateur et il n'existe pas en navigation privée : il faut l'exporter de temps en temps. Il a été vérifié dans Edge seulement. Firefox traite les pages locales autrement et peut ne pas garder le suivi.

- **Statistiques :** les médianes portent sur la valeur basse de la fourchette de salaire. Avec un filtre, certains graphiques ont peu d'offres : le nombre d'offres est toujours écrit à côté de la médiane, et le salaire d'un niveau n'est pas montré s'il y a moins de 3 salaires. L'historique ne commence que le 20 novembre.

- **Annonces semblables :** la règle compare le titre, l'employeur et le site. Deux vrais postes différents avec exactement le même titre chez le même employeur sont donc montrés sur la même carte, mais chacun garde sa ligne et son lien. Un même poste publié par deux employeurs différents (par exemple deux agences) n'est pas regroupé.

- **Page HTML :** c'est une copie des offres au moment de sa création. Elle est recréée à chaque lancement de `main.py`, mais une page déjà ouverte ne change qu'après un rafraîchissement (F5). Le bouton « Copier le lien » demande l'accès au presse-papiers : certains navigateurs le refusent pour un fichier ouvert en local, et la page affiche alors « Copiez l'adresse de la page ».

- **Aide à la candidature :**
  - la note vient de règles simples. Elle ne comprend que les technologies et compétences de nos listes (54 et 14), écrites clairement dans le CV ;
  - 70 offres sur 195 ne listent ni technologie ni compétence : elles ne sont pas classées, et le programme le dit ;
  - pas de PDF : il faut enregistrer le CV en `.docx` ;
  - les suggestions aident à savoir quoi mettre en avant, mais il faut toujours relire l'offre complète.

- **Lettre de motivation :**
  - les règles ne jugent ni le style ni l'orthographe ;
  - les mots-clés sont comparés par leur début (5 lettres) : un synonyme (« tester » au lieu de « mettre à l'essai ») n'est pas reconnu.

- **Collecte régulière :**
  - la comparaison se fait seulement avec le dernier `offres.json`. Si une collecte a des erreurs, des offres peuvent paraître « disparues » à tort ; le programme l'écrit alors en avertissement ;
  - le Planificateur ne lance la collecte que si la session Windows est ouverte.

**Pour la mise en commun :** le dossier [`../format-commun/`](../format-commun/README.md), à part de ce projet, convertit `offres.json` au format `JobOffer` de Gregory. Les 195 offres sont acceptées telles quelles par son modèle.

**À faire ensuite :**
- recueillir l'avis des camarades de classe qui testeront la page et l'aide à la candidature.
