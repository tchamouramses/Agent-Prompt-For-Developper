---
name: repository-discovery
description: Comprendre rapidement un dépôt inconnu ou peu connu (architecture, commandes réelles, conventions, dépendances, état des tests) avant d'y travailler. À utiliser au début d'une première tâche sur un projet, ou quand docs/PROJECT.md manque ou paraît dépassé.
---

# Découverte d'un dépôt

## Quand l'utiliser
- Première tâche sur un projet, ou retour après une longue période.
- `docs/PROJECT.md` absent, incomplet ou contredit par le code.
- Avant de briefer des agents sur un projet existant (orchestrateur).

Pas pour une tâche dans une zone déjà connue de la session : relis seulement la zone.

## Ce que l'agent rate sans ce skill
- Il invente les commandes (`npm test` alors que le projet utilise `pnpm vitest`, `phpunit` alors que c'est Pest).
- Il suit les conventions de son entraînement au lieu de celles du projet (services contre actions, structure des dossiers, style de tests).
- Il ignore qu'une partie des tests échoue déjà, puis s'attribue ou se voit reprocher ces échecs.
- Il lit tout le dépôt et sature son contexte au lieu de lire les bons fichiers.

## Entrées
- La racine du dépôt. `docs/PROJECT.md` et `docs/journal/` s'ils existent.

## Procédure
Lis dans cet ordre et arrête-toi dès que tu as la réponse ; ne lis pas tout le code.

1. **Documentation du projet** : `README*`, `docs/PROJECT.md`, `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING*`, dernières entrées de `docs/journal/`.
2. **Manifestes et versions** : `composer.json`, `package.json` (et le gestionnaire réel d'après le fichier de verrouillage : `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `bun.lockb`), `pom.xml` ou `build.gradle*`, `.nvmrc`, `.tool-versions`, `Dockerfile`, `docker-compose*`. Note les versions du langage et du framework (voir le skill `version-compatibility`).
3. **Commandes réelles** : scripts de `package.json`, `composer.json` (`scripts`), `Makefile`, `justfile`, tâches Gradle ou Maven, et surtout les workflows de CI (`.github/workflows/`, `.gitlab-ci.yml`) : la CI montre les commandes qui font foi pour installer, linter, typer, tester et construire.
4. **Structure** : arborescence sur deux ou trois niveaux (hors `vendor/`, `node_modules/`, `build/`, `dist/`, `.git/`). Repère les couches (contrôleurs, services, domaine, composants, routes), les points d'entrée et le modèle d'organisation du code (skill `architecture-patterns`). Si le dépôt contient plusieurs applications ou un fichier de workspace, dresse la carte des applications (skill `monorepo`) et relève les commandes de chacune.
5. **Couverture** : confronte les stacks et traits d'architecture trouvés aux agents et skills installés (skill `coverage-check`).
6. **Conventions** : ouvre deux ou trois fichiers représentatifs par couche et un ou deux tests. Note le nommage, l'organisation, la gestion des erreurs, le style de tests, la configuration du lint et du formatage.
7. **Historique** : `git log --oneline -20` et les branches actives, pour savoir ce qui bouge en ce moment.
8. **État de départ** : lance le lint et les tests (zone concernée, ou suite complète si elle est rapide) avec les commandes trouvées à l'étape 3. Note le résultat exact, y compris les échecs déjà présents.

## Livrable
Une fiche courte, dans ton compte rendu (ou dans `docs/PROJECT.md` si tu es `doc-writer` ou si l'utilisateur le demande) :

```markdown
## Fiche du dépôt (AAAA-MM-JJ, commit <sha court>)
- Stack : PHP 8.3, Laravel 11.x, MySQL 8 ; front Vite + Livewire 3
- Gestionnaires : composer, npm (package-lock.json)
- Commandes : installer `composer install && npm ci` ; tests `php artisan test` ; lint `./vendor/bin/pint --test` ; analyse `./vendor/bin/phpstan analyse` ; build `npm run build`
- Applications : une seule (sinon la carte du skill `monorepo`)
- Structure : app/Actions (logique métier), app/Http (contrôleurs fins), tests/Feature et tests/Unit (Pest) ; modèle : couches du framework
- Couverture : Laravel couvert (laravel-implementer, skill laravel) ; front Livewire sans skill dédié
- Conventions : actions invocables, Form Requests, Resources pour l'API, enums PHP pour les statuts
- État de départ : 212 tests, 210 réussis, 2 en échec (tests/Feature/ExportTest.php, déjà en échec sur main) ; lint propre
- À savoir : pas de CI configurée ; .env.example incomplet (MAIL_*)
```

## Vérifications
- Chaque commande de la fiche a été trouvée dans un fichier du dépôt (cite lequel en cas de doute) et celles de l'étape 8 ont été lancées.
- Les échecs de départ sont listés avec leurs fichiers.

## Limites
- Installer les dépendances déclarées par le projet (`composer install`, `npm ci`…) est permis ; démarrer un service payant ou se connecter à une base réelle ne l'est pas (principes communs, règle 5). Si les tests ne peuvent pas tourner, note-le comme **non vérifié** avec la cause.
- Pas de lecture de secrets : ouvre `.env.example`, jamais `.env`.

## En cas de blocage
- Commandes introuvables ou contradictoires (README contre CI) : la CI fait foi ; signale l'écart.
- Projet qui ne s'installe pas : cherche la cause (version de l'environnement, service manquant, étape absente du README) et corrige ce qui relève de l'environnement local ; sinon livre la fiche avec les erreurs exactes et la cause supposée.
