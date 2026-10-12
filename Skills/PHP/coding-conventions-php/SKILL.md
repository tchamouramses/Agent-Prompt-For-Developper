---
name: coding-conventions-php
description: Écrire du PHP moderne cohérent avec le projet - fonctionnalités autorisées par la version de PHP installée, typage strict, objets de valeur et énumérations, gestion des erreurs, style appliqué par Pint ou PHP-CS-Fixer et analyse statique PHPStan ou Larastan. À utiliser pour écrire ou relire du code PHP.
---

# Conventions PHP

Les règles générales (lisibilité, SOLID, zéro code mort, changement minimal) sont dans les principes des agents qui modifient du code. Ce skill les traduit en PHP.

## Quand l'utiliser
- Écrire, refactorer ou relire du code PHP.

## Ce que l'agent rate sans ce skill
- Il utilise une syntaxe absente de la version de PHP du projet (classes `readonly` en 8.1, constantes typées en 8.2, hooks de propriétés en 8.3).
- Il fait circuler des tableaux associatifs entre couches au lieu d'objets typés, et chaque lecture devient une supposition.
- Il ajoute `declare(strict_types=1);` dans un seul fichier d'un projet qui ne l'utilise pas, ou reformate tout un fichier.
- Il fait taire l'analyse statique (`@phpstan-ignore`, baseline régénérée) au lieu de corriger le type.
- Il attrape `\Exception` ou `\Throwable` pour continuer en silence.

## Entrées
- Contrainte `php` de `composer.json` et `php -v`, configuration de style (`pint.json`, `.php-cs-fixer.dist.php`, `phpcs.xml`), configuration d'analyse (`phpstan.neon`, `phpstan-baseline.neon`), fichiers voisins.

## Procédure
1. **Version de PHP** : retiens la plus basse entre la contrainte de `composer.json` et la version d'exécution. Fonctionnalités par version :

| Version | Disponible |
|---------|------------|
| 8.0 | promotion des propriétés du constructeur, `match`, opérateur nullsafe `?->`, arguments nommés, types union |
| 8.1 | énumérations, propriétés `readonly`, `never`, `new` dans les initialiseurs, callables de première classe `f(...)` |
| 8.2 | classes `readonly`, types DNF, `true`, `false` et `null` comme types autonomes |
| 8.3 | constantes de classe typées, attribut `#[\Override]`, `json_validate()` |
| 8.4 | hooks et visibilité asymétrique des propriétés, `new` sans parenthèses en chaîne, `array_find()` |

2. **Typage** : types de paramètres, de retour et de propriétés partout où le langage le permet. PHPDoc seulement pour ce que les types ne disent pas : génériques (`@return Collection<int, Note>`, `@param array<string, int>`), formes de tableau, exceptions métier levées. Suis la présence ou l'absence de `declare(strict_types=1);` dans les fichiers voisins.
3. **Modélisation** :
   - énumération (`enum Statut: string`) pour un ensemble fermé de valeurs, avec ses méthodes (`libelle()`, `peutPasserA()`) ;
   - objet de valeur ou DTO `final readonly` pour une donnée qui traverse des couches (requête vers service, service vers job) ;
   - classes `final` par défaut quand le projet le pratique ; héritage seulement pour un vrai « est un ».
4. **Dépendances** : injection par le constructeur (promotion des propriétés). Dans Laravel, façades et helpers acceptés dans les contrôleurs, commandes et vues si le projet les utilise ; dans un service métier, préfère l'injection pour pouvoir le tester. Pas de `new` d'un service d'infrastructure au milieu de la logique métier.
5. **Erreurs** : exceptions métier nommées (`NoteDejaArchiveeException`) ; capture seulement là où tu sais quoi faire (réessayer, traduire en réponse HTTP, compenser) ; jamais d'opérateur `@` ; jamais de bloc `catch` vide.
6. **Nommage** : selon le framework et le projet. Laravel : modèles au singulier (`Note`), tables au pluriel en `snake_case` (`notes`), colonnes en `snake_case`, méthodes en `camelCase`, contrôleurs `NoteController`, Form Requests `StoreNoteRequest`. Symfony : services et classes selon PSR-4, entités au singulier, repositories `NoteRepository`.
7. **Style et analyse** :
   - Laravel : `./vendor/bin/pint` sur tes fichiers seulement (`./vendor/bin/pint app/Models/Note.php`), `--test` pour vérifier.
   - Symfony ou PHP pur : `./vendor/bin/php-cs-fixer fix <fichiers>` ; `--dry-run --diff` pour vérifier.
   - PHPStan ou Larastan : `./vendor/bin/phpstan analyse` au niveau configuré ; corrige les erreurs de tes fichiers ; n'ajoute à la baseline que des erreurs préexistantes, jamais les tiennes ; ne monte pas le niveau dans une tâche sans rapport.

## Livrable
Du code conforme, et dans le compte rendu les commandes de style et d'analyse lancées avec leur résultat.

## Vérifications
- Aucune syntaxe au-dessus de la version de PHP retenue.
- Style et analyse statique sans nouvelle erreur sur les fichiers touchés.
- Aucun `@phpstan-ignore`, `@psalm-suppress` ou ajout à la baseline sans justification écrite dans le compte rendu.

## Limites
- Les conventions déjà en place dans le projet l'emportent sur ce skill (principes communs, règle 1). Ce skill sert quand le projet ne tranche pas.

## En cas de blocage
- Outil de style ou d'analyse absent : n'en installe pas un dans une tâche sans rapport ; suis le style des fichiers voisins, marque le contrôle **non vérifié** et propose l'outil dans le compte rendu.
- Erreur d'analyse causée par une dépendance mal typée : ajoute un PHPDoc local précis plutôt qu'une suppression globale.
