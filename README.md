# Kandet — offres d'emploi et de stage en informatique au Québec

Ce dépôt est ma version personnelle du projet de classe `jobs-insights` (cours 420-SV2-OQ, Collège O'Sullivan de Québec). Il reprend tout mon dossier du dépôt commun, arrêté au 20 novembre 2026, et c'est ici que je continue à le développer. Les liens vers le travail des autres étudiants pointent vers le dépôt commun, qui est privé et réservé à la classe.

Mon travail :
- collecter les offres TI du Québec ;
- les enrichir et les rechercher dans une page Web ;
- comparer un CV et une lettre de motivation avec les offres.

Python 3.12 ou plus récent suffit : **rien à installer**.

## Essayer en 3 commandes

Dans PowerShell, depuis le dossier du dépôt (`jobs-insights-kandet`) :

```powershell
cd .\03-amelioration-preuve-de-concept
python main.py                                             # collecte + page offres.html (environ 17 min la 1re fois, quelques minutes ensuite)
python main.py --depuis offres.json --cv cv-exemple.txt    # classement des offres pour un CV fictif
```

**Le plus simple : double-cliquez sur `Demarrer.cmd`.** La page s'ouvre dans le navigateur avec un bouton **« Mettre à jour les offres »** (pour arrêter, fermez la fenêtre « Offres TI - serveur »). Dans le terminal, c'est `python serveur.py`, puis `http://127.0.0.1:8000`.

Ouvrez ensuite **`offres.html`** d'un double-clic. Elle est recréée à chaque lancement de `main.py` : après une nouvelle collecte, rafraîchissez-la (F5). Dans la page, vous pouvez :
- filtrer par région, ville, technologie, niveau, mode de travail (télétravail, hybride, sur place), langue de l'annonce, salaire ou stage ;
- comparer les offres avec votre CV ;
- vérifier votre lettre pour une offre ;
- voir des statistiques (salaires, régions, technologies…) dans l'onglet « Statistiques » ;
- suivre vos candidatures (statut, note) dans l'onglet « Mes candidatures » ;
- trier les offres selon un score « étudiant du DEC » (stage, niveau débutant, technologies vues au DEC).

Après chaque collecte, `python main.py --depuis offres.json --nouveautes` résume les nouvelles offres (stages en premier) dans `rapport-nouveautes.md`. Ajoutez `--cv mon-cv.docx` pour voir celles qui sont proches de votre CV.

Le CV et la lettre restent dans le navigateur : rien n'est envoyé.

Pour vérifier que tout fonctionne (environ 1 seconde, sans Internet) :

```powershell
python -m unittest discover -p "test_*.py" -v
```

**Le guide complet** est au début de la [note du livrable 3](03-amelioration-preuve-de-concept/note-livrable-3.md#tester-le-projet-guide-rapide). Il couvre toutes les options, la collecte régulière et quoi faire si ça ne marche pas.

## Contenu du dossier

| Dossier | Contenu |
|---|---|
| [`01-inventaire-des-sites/`](01-inventaire-des-sites/sites.md) | Livrable 1 : sites d'offres d'emploi et de stage |
| [`02-preuve-de-concept-scraping/`](02-preuve-de-concept-scraping/compte-rendu-livrable-2.md) | Livrable 2 : premier prototype (Guichet-Emplois et Remotive) et son compte rendu |
| [`03-amelioration-preuve-de-concept/`](03-amelioration-preuve-de-concept/note-livrable-3.md) | Livrable 3 et suite : le projet actuel, sa [note](03-amelioration-preuve-de-concept/note-livrable-3.md) et son [plan de travail](03-amelioration-preuve-de-concept/plan.md) |
| [`format-commun/`](format-commun/README.md) | Mes offres converties au format commun de la classe (modèle `JobOffer` de Gregory). Dossier à part |

## Sources et règles

- **Sources :** le [Guichet-Emplois](https://www.guichetemplois.gc.ca/) (et les offres de ses partenaires) l'API publique de [Remotive](https://remotive.com/), l'API de [Jobicy](https://jobicy.com/) et les pages carrières publiques de 12 employeurs (Greenhouse, Lever, voir `pages_carrieres.json`). Pour la tendance sur 12 mois : les [données ouvertes du Guichet-Emplois](https://open.canada.ca/data/fr/dataset/ea639e28-c0fc-48bf-b5dd-b8899bd43072). Contient des informations visées par la Licence du gouvernement ouvert – Canada.
- **Respect des sites :** 5 s entre deux requêtes au Guichet-Emplois (`robots.txt`), et Remotive au plus une fois par jour.
- **Sites écartés :** Québec emploi, Jobboom, Jobillico et Talent.com ne sont pas collectés directement, parce que leurs conditions d'utilisation l'interdisent (leurs offres arrivent quand même par le Guichet-Emplois). Indeed, Monster, Workopolis et CareerBeacon refusent les robots. Détails dans la note du livrable 3.
- **Rien n'est deviné :** une information absente d'une offre reste vide.
- **Données personnelles :** aucun vrai CV dans le dépôt. `cv-exemple.txt` et `lettre-exemple.txt` sont fictifs.
