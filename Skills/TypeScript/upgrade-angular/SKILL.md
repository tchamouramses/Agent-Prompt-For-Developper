---
name: upgrade-angular
description: Monter de version une application Angular en sécurité - une version majeure à la fois avec ng update et ses migrations automatiques, guide officiel update.angular.dev, alignement de TypeScript, Node, RxJS et des librairies (Material, NgRx), migrations optionnelles (standalone, contrôle de flux, signaux) séparées. À utiliser pour toute montée de version d'Angular.
---

# Montée de version Angular

La méthode générale (filet de tests, étapes courtes, une version majeure à la fois) est dans l'agent `refactorer`. Ce skill donne l'ordre propre à Angular, dont l'outil `ng update` applique des migrations de code.

## Quand l'utiliser
- Montée de version de `@angular/core` (et des paquets `@angular/*`).
- Une librairie (Angular Material, NgRx, librairie de composants) exige une version plus récente d'Angular.

## Ce que l'agent rate sans ce skill
- Il change les versions dans `package.json` à la main et perd les migrations automatiques de `ng update`.
- Il saute plusieurs versions majeures d'un coup : `ng update` ne le permet pas et les migrations intermédiaires ne s'exécutent pas.
- Il mélange la montée de version et les migrations de style optionnelles (standalone, contrôle de flux, signaux) dans un seul diff impossible à relire.
- Il oublie que chaque version exige une plage de Node et de TypeScript.

## Entrées
- `package.json`, `angular.json`, version de Node locale et de CI, librairies `@angular/*` et de l'écosystème, suite de tests.

## Procédure
1. **Préparer** : `ng test --watch=false` et `ng build` verts, commandes citées ; branche dédiée ; arbre de travail propre (`ng update` l'exige).
2. **Lire** le guide officiel (`angular.dev/update-guide`, version de départ → version cible, niveau de complexité de l'application) et les notes de version ; liste les points qui touchent le projet.
3. **Vérifier l'environnement** : versions de Node et de TypeScript acceptées par la version cible (tableau de compatibilité de la documentation) ; monter Node en local et en CI avant si besoin.
4. **Monter d'une version majeure** : `npx ng update @angular/core@<N+1> @angular/cli@<N+1>`, puis les librairies liées dans le même ordre (`npx ng update @angular/material@<N+1>`, NgRx, librairies de composants selon leur propre guide). Lis la sortie : migrations appliquées et avertissements.
5. **Relire le diff des migrations**, corriger ce qu'elles signalent, relancer tests et build ; commit par version majeure.
6. **Répéter** jusqu'à la version cible.
7. **Migrations optionnelles** (`ng generate @angular/core:standalone`, `:control-flow`, `:signal-input-migration`, `:inject`…) : seulement si la tâche les demande, chacune dans une étape et un commit séparés, après la montée de version.
8. **Vérifier** : `ng build` sans avertissement nouveau, tests, lint, rendu serveur s'il existe ; recherche des API dépréciées citées par le guide.
9. **Consigner** dans le journal et un ADR : versions de départ et d'arrivée, étapes, migrations appliquées, changements de comportement.

## Livrable
L'application sur la version cible, tests et build verts, une entrée de journal et un ADR, la ligne de CHANGELOG si le comportement visible change.

## Vérifications
- `ng version` affiche la version cible pour tous les paquets `@angular/*`.
- Un commit par version majeure, chacun avec tests et build verts.
- Chaque point du guide officiel qui concerne le projet est traité ou noté « ne s'applique pas ».

## Limites
- Le déploiement de la nouvelle version reste une action réservée (règle 5 des principes communs).

## En cas de blocage
- Librairie sans version compatible : rester sur la version actuelle d'Angular, consigner le blocage avec le lien vers le suivi de la librairie, et proposer un remplaçant selon la règle 4 des principes communs.
- `ng update` échoue sur un conflit de dépendances : lis le conflit, monte d'abord la dépendance bloquante dans une version compatible avec les deux ; `--force` seulement en connaissance de cause, consigné.
