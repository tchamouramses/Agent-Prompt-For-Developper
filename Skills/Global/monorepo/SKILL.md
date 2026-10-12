---
name: monorepo
description: Travailler dans un dépôt qui contient plusieurs applications ou paquets (front et back ensemble, workspaces npm/pnpm/yarn, Nx, Turborepo, modules Maven ou Gradle, paquets internes) - carte des applications, commandes par application, contrat entre applications, ordre des changements, tests et CI ciblés, documentation unique. À utiliser pour concevoir, initialiser ou modifier un monorepo.
---

# Monorepo

Un monorepo regroupe plusieurs applications (une API, un front web, une application mobile…) et parfois des paquets partagés. Les agents sont conçus pour une application ; ce skill leur donne la carte du dépôt et les règles qui évitent de casser une application en modifiant une autre.

## Quand l'utiliser
- Le dépôt contient un fichier de workspace (`pnpm-workspace.yaml`, champ `workspaces` de `package.json`, `nx.json`, `turbo.json`, `lerna.json`, `settings.gradle*` avec plusieurs `include`, `pom.xml` avec `<modules>`) ou plusieurs manifestes d'applications (`apps/*/composer.json`, `apps/*/package.json`…).
- `architect` envisage de placer plusieurs applications dans un même dépôt.
- Une tâche touche à la fois le producteur et le consommateur d'une API interne.

## Ce que l'agent rate sans ce skill
- Il lance `npm install` ou les tests à la racine alors que chaque application a son gestionnaire et ses commandes, ou l'inverse.
- Il modifie une réponse d'API côté back sans mettre à jour le front qui la consomme, ou sans garder l'ancienne forme le temps de la transition.
- Il duplique un type, une constante ou une validation entre applications au lieu d'utiliser le paquet partagé ou le contrat généré.
- Il ajoute une dépendance à la racine au lieu de l'application qui l'utilise, ou dans une version différente de celle des autres applications.
- Il éparpille la documentation (`apps/api/docs/`, `apps/web/docs/`) et la session suivante ne trouve plus l'état du projet.

## Entrées
- La racine du dépôt, les fichiers de workspace, les manifestes de chaque application, la CI.
- `docs/PROJECT.md` (section « Applications ») et `docs/architecture.md` s'ils existent.

## Procédure

### 1. Établir la carte des applications
Pour chaque application ou paquet, relève : chemin, rôle, stack et version, gestionnaire, commandes (installer, lancer, linter, typer, tester, construire), dépendances internes, ce qu'elle expose (API, paquet, composants) et qui le consomme. Les commandes viennent des manifestes et de la CI (skill `repository-discovery`), jamais de la mémoire.

```markdown
## Applications
| Chemin | Rôle | Stack | Commandes (depuis la racine) | Dépend de | Consommée par |
|--------|------|-------|------------------------------|-----------|---------------|
| apps/api | API REST | Laravel 11, PHP 8.3 | `composer --working-dir=apps/api test` | — | apps/web, apps/mobile |
| apps/web | front web | Next.js 15 | `pnpm --filter web test` | packages/api-client | — |
| packages/api-client | client typé généré depuis l'OpenAPI | TypeScript | `pnpm --filter api-client build` | apps/api (contrat) | apps/web, apps/mobile |
```

Cette carte vit dans `docs/PROJECT.md` (section « Applications », tenue par `doc-writer`) ; `architect` la décrit dans `docs/architecture.md` pour un nouveau projet.

### 2. Une seule mémoire de projet
- Un seul dossier `docs/` à la racine : `PROJECT.md`, `CHANGELOG.md`, `journal/`, `adr/`, `plan.md` sont communs (skill `project-docs-tracking`).
- `docs/architecture.md` a une section par application ; `docs/api.md` documente les contrats entre applications.
- Chaque entrée de journal et chaque tâche de `docs/plan.md` indique l'application concernée (`apps/web`) ; une ligne de CHANGELOG commence par l'application quand le produit en a plusieurs visibles (« Web : … »).
- Chaque application garde un `README.md` court avec ses commandes ; les fichiers d'instructions (`CLAUDE.md`, `AGENTS.md`) restent à la racine, avec la carte des commandes.

### 3. Travailler dans une application
- Lance les commandes depuis la racine avec le filtre du gestionnaire (`pnpm --filter`, `npm -w`, `yarn workspace`, `nx run`, `turbo run --filter`, `mvn -pl`, `gradle :module:`), ou avec `--working-dir` / `cd` explicite pour une application hors workspace. Cite la commande exacte en preuve.
- Une dépendance s'ajoute dans le manifeste de l'application qui l'utilise, dans la même version majeure que les autres applications qui l'ont déjà (vérifie le fichier de verrouillage). Seuls les outils de développement communs (formatage, hooks git, orchestrateur de tâches) vont à la racine.
- Un code utile à deux applications va dans un paquet partagé existant ; n'en crée un que si deux applications l'utilisent réellement aujourd'hui (principes de code, pas d'abstraction pour plus tard).
- Ne modifie pas une autre application que celle de ta tâche, sauf le consommateur direct d'un contrat que tu changes (étape 4).

### 4. Changer un contrat entre applications
Un contrat est tout ce qu'une application expose à une autre : route d'API et forme des données, événement, paquet partagé, schéma de base commun.
1. Repère tous les consommateurs (carte de l'étape 1, recherche dans tout le dépôt).
2. Le contrat est décrit à un seul endroit qui fait foi : spécification OpenAPI ou GraphQL, schéma partagé, types générés. Les consommateurs utilisent les types générés, pas une copie écrite à la main.
3. Ordre des changements : le producteur ajoute la nouvelle forme en gardant l'ancienne ; les consommateurs passent à la nouvelle ; l'ancienne est retirée dans une tâche ultérieure de `docs/plan.md`. Les applications du même dépôt peuvent être déployées à des moments différents (une application mobile publiée reste en circulation des mois).
4. Producteur et consommateurs sont dans la même PR si le changement est rétrocompatible et petit ; sinon une tâche par application, dans l'ordre ci-dessus.
5. Un test vérifie le contrat des deux côtés : côté producteur, la réponse respecte le schéma ; côté consommateur, le client généré compile et ses tests passent.

### 5. Tester et intégrer
- Lance d'abord les tests de l'application modifiée, puis ceux de chaque application qui en dépend (graphe des dépendances internes de l'étape 1, ou commande « affected » de l'outil : `nx affected`, `turbo run --filter=...[origin/main]`).
- La CI exécute les vérifications par application, déclenchées par les chemins modifiés et par les dépendances internes ; un changement d'un paquet partagé relance tous ses consommateurs.

### 6. Initialiser un monorepo (nouveau projet)
- `architect` ne choisit le monorepo que si les applications partagent du code, un contrat versionné ensemble ou une équipe ; sinon des dépôts séparés sont plus simples. La décision fait l'objet d'un ADR.
- Structure par défaut : `apps/<application>/` pour ce qui se déploie, `packages/<paquet>/` pour ce qui se partage, `docs/` unique à la racine.
- Outil par défaut : les workspaces natifs du gestionnaire de paquets (`pnpm` ou `npm`) pour les applications JavaScript ou TypeScript ; un orchestrateur de tâches (Turborepo, Nx) seulement si la durée des builds le justifie ; les applications PHP ou Java gardent leur outil (Composer, Maven, Gradle) dans leur dossier, appelé depuis un script racine (`Makefile`, `justfile` ou scripts du `package.json` racine).
- `scaffolder` crée chaque application avec l'outil officiel de son framework, dans son dossier.

## Livrable
- La carte des applications, à jour.
- Pour une tâche : les commandes lancées par application, les consommateurs vérifiés, et l'ordre de changement du contrat s'il y en a un.

## Vérifications
- Toute commande citée en preuve indique l'application visée (filtre ou dossier).
- Aucune dépendance ajoutée à la racine si elle ne sert qu'à une application ; aucune version majeure divergente d'une même dépendance sans raison consignée.
- Un changement de contrat a un test côté producteur et un côté consommateur, et l'ancienne forme est conservée ou son retrait est planifié.

## Limites
- Les règles détaillées des tests de contrat sont dans le skill `api-contracts` ; la conception d'API dans `api-design`.
- Plusieurs dépôts séparés qui communiquent ne sont pas un monorepo : la carte se limite au dépôt courant, et les consommateurs externes sont traités comme hors du dépôt (principes de code, régressions).

## En cas de blocage
- Le workspace ne s'installe pas à la racine : installe et teste application par application, et consigne l'écart dans le journal.
- Consommateur d'un contrat introuvable ou hors du dépôt : garde l'ancienne forme du contrat et signale le consommateur supposé dans le compte rendu.
