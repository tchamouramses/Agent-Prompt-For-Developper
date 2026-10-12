---
name: evidence-tracking
description: Méthode pour produire des preuves vérifiables - commande exacte, résultat, commit ou diff testé, environnement - et savoir quand une preuve n'est plus valable. Complète la règle « Preuves et contrôle indépendant » des principes communs. À utiliser chaque fois qu'un agent affirme qu'un test, un build, un lint ou un parcours passe.
---

# Suivi des preuves

La règle est dans les principes communs : aucune affirmation sans commande exécutée dans la session, ce qui n'est pas exécuté est « non vérifié ». Ce skill dit ce qu'une preuve doit contenir et quand elle expire.

## Quand l'utiliser
- En fin de tâche, pour la ligne « Vérifié » du compte rendu.
- `quality-gatekeeper`, `e2e-validator`, `code-reviewer` : pour vérifier les preuves des autres et produire les leurs.

## Ce que l'agent rate sans ce skill
- Il cite un résultat obtenu **avant** sa dernière modification : la preuve ne porte plus sur le code livré.
- Il résume (« tests OK ») sans le nombre de tests, les échecs ignorés ni la commande.
- Il lance une commande filtrée (un seul test) et présente le résultat comme celui de la suite.
- Il ne dit pas dans quel environnement la preuve a été obtenue (base SQLite au lieu de MySQL, simulateur au lieu d'un appareil).

## Entrées
- Le code à prouver (état courant de l'arbre de travail ou commit), les commandes du projet.

## Procédure
1. **Fixer l'état prouvé** : `git rev-parse --short HEAD` et `git status --short`. Si l'arbre de travail a des modifications non commitées, la preuve porte sur « HEAD + modifications locales » : dis-le.
2. **Lancer la commande complète du projet** (celle de la CI quand elle existe), pas une variante filtrée, sauf si tu annonces explicitement le filtre.
3. **Relever le résultat chiffré** : nombre de tests réussis, en échec, ignorés ; nombre d'erreurs et d'avertissements du lint ou du typage ; code de sortie. Copie les lignes de résumé de la sortie, pas une paraphrase.
4. **Noter l'environnement** quand il compte : versions (langage, navigateur, appareil), base de données, variables qui changent le comportement.
5. **Joindre les artefacts** quand l'outil en produit : rapport HTML ou JUnit, captures, vidéos, traces ; cite leur chemin.
6. **Invalider après modification** : toute modification de code ou de configuration après une preuve la rend caduque pour la zone touchée. Relance avant d'affirmer.
7. **Marquer le reste** : ce qui n'a pas été lancé est écrit **non vérifié**, avec la raison (outil absent, service externe, appareil indisponible) et la commande qui le vérifierait.

## Livrable
```markdown
**Vérifié** (commit a1b2c3d + modifications locales, PHP 8.3.12, MySQL 8.0 via docker compose) :
- `php artisan test` → Tests: 214 passed, 2 skipped (exit 0) ; les 2 ignorés existaient avant (tests/Feature/ExportTest.php)
- `./vendor/bin/pint --test` → PASS, 0 fichier à corriger
- `./vendor/bin/phpstan analyse` → [OK] No errors
**Non vérifié** : envoi réel de l'e-mail (fournisseur non configuré) ; vérifiable par `php artisan mail:test` avec les identifiants de préproduction.
```

## Vérifications
- Chaque preuve indique la commande, le résultat chiffré et l'état du code prouvé.
- Aucune preuve n'est antérieure à la dernière modification de sa zone.

## Limites
- Une preuve de CI distante n'est utilisable que si elle porte sur le même commit : cite le lien et le commit.

## En cas de blocage
- Commande impossible à lancer (dépendance manquante, service indisponible) : marque **non vérifié**, donne la cause exacte et ne contourne pas en modifiant la commande ou les tests.
