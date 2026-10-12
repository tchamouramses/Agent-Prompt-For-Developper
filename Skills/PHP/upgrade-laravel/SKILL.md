---
name: upgrade-laravel
description: Monter un projet Laravel d'une version majeure à la suivante sans régression - état de départ prouvé, guide d'upgrade officiel lu en entier, une version majeure à la fois, PHP et paquets compatibles vérifiés, composer.json mis à jour, dépréciations traitées, structure conservée, tests à chaque étape ; Laravel Shift en option payante soumise à l'humain. À utiliser pour passer de Laravel N à N+1 ou plus, ou pour préparer et chiffrer une montée de version.
---

# Montée de version Laravel

L'agent `refactorer` fixe la démarche (guide officiel, changements cassants listés, version par version, tests à chaque étape) ; le skill `version-compatibility` dit comment lire les versions installées et leur documentation ; le skill `laravel` décrit la structure propre à chaque version. Ce skill donne la procédure propre à Laravel.

## Quand l'utiliser
- `refactorer` : montée de version majeure de `laravel/framework`.
- `laravel-implementer` : correction du code de l'application pendant ou après la montée, et toute tâche qui bute sur une API absente de la version installée.

## Ce que l'agent rate sans ce skill
- Il saute plusieurs versions d'un coup (10 → 12) et mélange les changements cassants de deux guides.
- Il réécrit le projet à la structure allégée de Laravel 11 (`bootstrap/app.php`, suppression des Kernel) : le guide officiel déconseille cette migration, qui n'est pas requise.
- Il change `laravel/framework` dans `composer.json` sans les paquets liés (`phpunit/phpunit`, `pestphp/pest`, `nunomaduro/collision`, `larastan/larastan`, Sanctum, Horizon, Livewire), puis force la résolution.
- Il oublie la version de PHP : le serveur de production ne la fournit pas encore.
- Il ne lit que les changements « High impact » et rate un « Low impact » qui touche le projet.
- Il ne relance pas les tests avec l'affichage des dépréciations, et laisse du code qui cassera à la version suivante.

## Entrées
- `composer.json`, `composer.lock`, `php -v`, version de PHP de production (`docs/architecture.md`, `docs/runbook.md`, Dockerfile), `config/`, la suite de tests, le journal.

## Procédure
1. **État de départ** : version exacte (`composer show laravel/framework | head -5`), suite complète verte et durée notée (`php artisan test`), dépréciations déjà présentes (`php artisan test --display-deprecations`). Sans filet suffisant sur les zones sensibles (authentification, files, paiement), complète-le d'abord (agent `refactorer`, étape 1).
2. **Lire le guide** `https://laravel.com/docs/<cible>.x/upgrade` en entier, et le comparatif du squelette `https://github.com/laravel/laravel/compare/<actuelle>.x...<cible>.x`. Pour chaque point du guide, note dans le journal : concerne le projet (avec `rg` qui le prouve) ou non.
3. **Vérifier les prérequis** : PHP minimal de la cible (10 : 8.1 ; 11 et 12 : 8.2 ; au-delà, tableau « Support Policy » de `laravel.com/docs/<cible>.x/releases`) disponible en local, en CI et en production. Changer PHP en production est une action réservée : prépare-la.
4. **Trouver ce qui bloque** : `composer why-not laravel/framework <cible>.0` liste les paquets incompatibles ; pour chacun, version compatible (notes de version du paquet) ou remplaçant (règle 4 des principes communs).
5. **Une version majeure par étape**, sur la branche de travail, un commit par étape :
   1. mettre à jour les contraintes (`laravel/framework: ^<cible>.0` et les paquets liés) dans `composer.json` ;
   2. `composer update -W` puis relire le diff de `composer.lock` (aucune autre majeure inattendue) ;
   3. `php artisan optimize:clear` ;
   4. appliquer les points du guide qui concernent le projet, du plus probable au moins probable ;
   5. comparer les fichiers de `config/` au squelette de la cible (`php artisan config:publish` depuis Laravel 11) et reporter les nouvelles clés utiles, sans écraser les réglages du projet ;
   6. `php artisan test --display-deprecations`, Pint, Larastan ; corriger avant l'étape suivante.
6. **Points souvent oubliés**, à vérifier dans le guide de la cible : migrations de modification de colonne (depuis Laravel 11, `->change()` doit répéter tous les modificateurs), paquets de premier niveau à monter en même temps (Sanctum, Passport, Horizon, Telescope), Carbon 3 exigé par Laravel 12, `HasUuids` qui produit des UUID v7 en 12. Les migrations déjà appliquées ne se modifient pas (skill `migrations`).
7. **Outillage facultatif** :
   - Rector avec `driftingly/rector-laravel` (gratuit) pour les remplacements mécaniques, si la règle 4 le permet : lancer en `--dry-run`, relire, puis appliquer étape par étape ;
   - Laravel Shift : service payant qui ouvre une PR sur le dépôt ; compte, coût et accès au dépôt sont des actions réservées : propose-le avec son prix et l'alternative manuelle, ne l'utilise pas seul.
8. **Garder la structure** du projet ; l'adoption de la structure allégée devient, si elle est utile, une tâche séparée du plan décidée par `architect`.
9. **Consigner** : journal (points du guide traités, paquets changés, versions avant et après), ligne `Changed` du changelog si un prérequis visible change (PHP minimal), décision humaine préparée pour PHP de production et déploiement (skill `deployment-checklist`).

## Livrable
```markdown
**Montée** : Laravel 11.44.2 → 12.21.0, PHP 8.3 (inchangé)
**Guide** : laravel.com/docs/12.x/upgrade — 14 points, 3 concernent le projet : <liste>
**Paquets** : sanctum 4.0 → 4.1, larastan 2.9 → 3.4 ; remplacé : <paquet> → <paquet> (raison)
**Preuves** : `php artisan test` 412/412 avant et après ; dépréciations 6 → 0 ; Pint et Larastan sans erreur
**Décision humaine** : PHP 8.3 en production avant déploiement (vérifier `php -v` sur le serveur)
```

## Vérifications
- `composer show laravel/framework` affiche la version cible ; `composer validate` et `composer audit` passent.
- Suite complète verte avec le même nombre de tests qu'au départ (aucun test supprimé ni sauté) ; aucune nouvelle dépréciation.
- `php artisan route:list` et `php artisan about` s'exécutent sans erreur ; chaque point du guide est classé dans le journal.

## Limites
- Les majeures de Livewire, Filament ou Inertia ont leurs propres guides : montée séparée, sauf si la cible Laravel l'impose.
- Ce skill ne change pas PHP en production ni ne déploie : préparation pour l'humain (règle 5).

## En cas de blocage
- Paquet abandonné sans version compatible : compare les remplaçants (règle 4), ou isole le paquet derrière une interface et ajoute son remplacement au plan ; la montée attend.
- Test rouge sans lien évident avec le guide : applique le skill `debugging-method` avant toute correction, et ne passe pas à la version suivante tant qu'il reste rouge.
