---
name: upgrade-nextjs
description: Monter de version une application Next.js en sécurité - guide officiel de mise à jour, codemods @next/codemod, alignement de React et de Node, changements de comportement du cache et des API de requête asynchrones, une version majeure à la fois. À utiliser pour toute montée de version de Next.js.
---

# Montée de version Next.js

La méthode générale (filet de tests, étapes courtes, une version majeure à la fois) est dans l'agent `refactorer`. Ce skill donne l'ordre propre à Next.js, dont les versions majeures changent souvent le comportement par défaut sans erreur de compilation.

## Quand l'utiliser
- Montée de version de `next` (et de `react`, `react-dom` liés).
- Une dépendance (librairie d'authentification, de styles, de données) exige une version plus récente.

## Ce que l'agent rate sans ce skill
- Il monte la version sans lire le guide : le cache change de comportement par défaut, et l'application sert des données périmées ou interroge la base à chaque requête, sans aucune erreur.
- Il corrige à la main ce qu'un codemod officiel fait de façon sûre (API de requête asynchrones, renommages).
- Il oublie d'aligner React, les types React et `eslint-config-next`.
- Il ne vérifie pas la version de Node exigée par la cible, en local, en CI et sur l'hébergement.

## Entrées
- `package.json`, `next.config.*`, `middleware.ts` ou `proxy.ts`, routeur utilisé, version de Node locale, de CI et d'hébergement, suite de tests.

## Procédure
1. **Préparer** : lint, typage, tests et `next build` verts, commandes citées ; branche dédiée.
2. **Lire** le guide officiel de mise à jour de la version cible (`nextjs.org/docs/app/guides/upgrading`, version par version) et les notes de version ; liste les points qui touchent le projet, en particulier les changements de comportement par défaut (cache, rendu, API de requête, routage).
3. **Vérifier l'environnement** : version minimale de Node de la cible, en local, en CI et sur l'hébergement (changement d'hébergement : action réservée).
4. **Monter** avec l'outil officiel quand il existe (`npx @next/codemod@latest upgrade <version>`, qui met à jour les paquets et propose les codemods), ou à la main : `next`, `react`, `react-dom`, `@types/react`, `@types/react-dom`, `eslint-config-next` dans les versions indiquées par le guide.
5. **Appliquer les codemods** cités par le guide (`npx @next/codemod <transformation> <chemin>`), relire leur diff, puis traiter à la main ce qu'ils signalent (commentaires `@next-codemod-error` ou équivalents).
6. **Décider explicitement du cache** : pour chaque lecture de données importante, vérifier le comportement après la montée et fixer explicitement l'option voulue (mise en cache, revalidation, dynamique), plutôt que de dépendre du nouveau défaut.
7. **Vérifier** : `next build` (lis la sortie : routes statiques ou dynamiques, avertissements), tests, parcours principaux (skill `e2e-testing`), et comparaison de la liste des routes statiques et dynamiques avant et après.
8. **Consigner** dans le journal et un ADR : versions de départ et d'arrivée, codemods appliqués, décisions de cache, changements de comportement.

## Livrable
L'application sur la version cible, build et tests verts, une entrée de journal et un ADR, la ligne de CHANGELOG si le comportement visible change.

## Vérifications
- `next --version` affiche la version cible ; React et ses types alignés.
- La sortie de `next build` ne montre ni avertissement nouveau ni route passée de statique à dynamique (ou l'inverse) sans décision consignée.
- Suite complète verte, résumé cité.

## Limites
- Le déploiement et tout changement de configuration de l'hébergement restent des actions réservées (règle 5 des principes communs).

## En cas de blocage
- Librairie incompatible avec la nouvelle version de React ou de Next.js : rester sur la version actuelle, consigner le blocage, proposer un remplaçant selon la règle 4 des principes communs.
- Codemod qui échoue sur un fichier : faire la transformation à la main pour ce fichier en suivant la documentation du codemod, et le signaler.
