---
name: lint-format-php
description: Mettre en place et utiliser le formatage et l'analyse statique PHP (Pint, PHP-CS-Fixer, PHPStan ou Larastan, Rector) - choisir les outils d'un nouveau projet Laravel ou Symfony, les brancher sur la CI, gérer une baseline, corriger sans faire taire les règles. À utiliser à l'initialisation d'un projet PHP ou quand un contrôle de style ou d'analyse échoue.
---

# Formatage et analyse statique PHP

## Quand l'utiliser
- `scaffolder` : initialiser un projet Laravel, Symfony ou PHP.
- Tout agent : un contrôle de style ou d'analyse échoue, ou il faut savoir quelle commande lancer.

## Ce que l'agent rate sans ce skill
- Il lance Pint ou PHP-CS-Fixer sur tout le projet dans une tâche sans rapport.
- Il installe PHP-CS-Fixer dans un projet Laravel qui a déjà Pint, ou l'inverse.
- Il régénère la baseline PHPStan pour y cacher ses propres erreurs.
- Il applique Rector sur tout le code sans relire, et le diff mélange modernisation et tâche.

## Entrées
- `composer.json` (`laravel/pint`, `friendsofphp/php-cs-fixer`, `phpstan/phpstan`, `larastan/larastan`, `rector/rector`), `pint.json`, `.php-cs-fixer.dist.php`, `phpstan.neon(.dist)`, `phpstan-baseline.neon`, `rector.php`, workflows de CI.

## Procédure

### 1. Projet existant : utiliser ce qui est là
| Outil | Vérifier | Corriger |
|-------|----------|----------|
| Pint | `./vendor/bin/pint --test` | `./vendor/bin/pint <fichiers>` ou `./vendor/bin/pint --dirty` (fichiers modifiés selon git) |
| PHP-CS-Fixer | `./vendor/bin/php-cs-fixer fix --dry-run --diff` | `./vendor/bin/php-cs-fixer fix <fichiers>` |
| PHPStan / Larastan | `./vendor/bin/phpstan analyse` (avec `--memory-limit=1G` si besoin) | à la main |
| Rector | `./vendor/bin/rector process --dry-run` | `./vendor/bin/rector process <fichiers>` |

- Lance les commandes et options de la CI (skill `repository-discovery`), ou les scripts de `composer.json` s'ils existent (`composer lint`, `composer analyse`).
- Applique le formateur à tes fichiers seulement, et vérifie que `git diff --stat` ne touche rien d'autre.

### 2. Nouveau projet : socle par défaut
Choisis selon le skill `autonomy-policy` et consigne le choix ; par défaut :
- **Laravel** : Pint (fourni par le squelette) avec le préréglage `laravel` ; Larastan au niveau le plus haut que le squelette passe sans erreur (souvent 5 à 6), monté par paliers dans des tâches dédiées.
- **Symfony ou PHP** : PHP-CS-Fixer avec les règles `@Symfony` (ou `@PER-CS`) ; PHPStan avec `phpstan/extension-installer` et les extensions Symfony et Doctrine si ces paquets sont présents.
- **Rector** : seulement si le projet prévoit des montées de version régulières ; configuré sur la version de PHP et du framework du projet, jamais lancé en CI pour réécrire.
- **Scripts** : `composer lint`, `composer analyse` (et `composer fix`) dans `composer.json`, appelés par la CI.

### 3. Baseline
- La baseline (`phpstan-baseline.neon`) ne contient que des erreurs existantes avant l'introduction de l'outil ou d'un nouveau niveau.
- Une erreur dans un fichier que tu modifies se corrige plutôt que de rester en baseline ; une erreur que tu corriges disparaît de la baseline (`--generate-baseline` seulement après correction, puis relecture du diff : il ne doit que retirer des lignes).

### 4. Corriger un échec
1. Lis le message et la ligne ; corrige le type ou le code.
2. Faux positif avéré : `@phpstan-ignore <identifiant>` sur la ligne, avec la raison en commentaire ; jamais `ignoreErrors` global ; cite-le dans le compte rendu.

## Livrable
Pour un nouveau projet : la configuration des outils, les scripts Composer et la CI, et leur justification dans le journal. Pour une tâche : les commandes lancées et leur résultat.

## Vérifications
- Les commandes de vérification de la CI passent en local.
- La baseline n'a reçu aucune ligne nouvelle.
- Aucun fichier reformaté hors de la tâche.

## Limites
- Les conventions d'écriture (typage, modélisation, nommage) sont dans le skill `coding-conventions-php` ; ce skill porte les outils.

## En cas de blocage
- Analyse qui échoue faute de mémoire ou d'extension : corrige la commande (`--memory-limit`, extension manquante déclarée dans `composer.json`) plutôt que d'abandonner le contrôle ; sinon marque-le **non vérifié**.
- Outil absent : n'en ajoute pas dans une tâche sans rapport ; propose le socle de l'étape 2 comme tâche du plan.
