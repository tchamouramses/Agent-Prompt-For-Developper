---
name: lint-format-typescript
description: Mettre en place et utiliser le lint et le formatage TypeScript (ESLint en configuration plate avec typescript-eslint, Prettier ou Biome, angular-eslint, configuration ESLint de Next.js et d'Expo) - choisir les outils d'un nouveau projet, les brancher sur la CI, corriger sans faire taire les règles. À utiliser à l'initialisation d'un projet TypeScript ou quand un contrôle de lint ou de format échoue.
---

# Lint et formatage TypeScript

## Quand l'utiliser
- `scaffolder` : initialiser un projet Angular, Next.js, Expo, React ou Node.
- Tout agent : un contrôle de lint ou de formatage échoue, ou il faut savoir quelle commande lancer.

## Ce que l'agent rate sans ce skill
- Il écrit un `.eslintrc.json` dans un projet en configuration plate (`eslint.config.js`, par défaut depuis ESLint 9, seule prise en charge par les versions récentes), ou l'inverse.
- Il installe Prettier dans un projet qui formate avec Biome, ou deux outils se disputent les mêmes règles.
- Il reformate tout le projet dans une tâche sans rapport.
- Il ajoute `// eslint-disable` au lieu de corriger, ou désactive une règle dans la configuration.
- Il lance `next lint`, retiré des versions récentes de Next.js, au lieu du script du projet.

## Entrées
- `package.json` (scripts `lint`, `format`, `check` ; `eslint`, `typescript-eslint`, `prettier`, `@biomejs/biome`, `angular-eslint`, `eslint-config-next`, `eslint-config-expo`), `eslint.config.*` ou `.eslintrc*`, `.prettierrc*`, `biome.json`, workflows de CI, gestionnaire de paquets (fichier de verrouillage).

## Procédure

### 1. Projet existant : utiliser ce qui est là
- Lance les scripts du projet avec son gestionnaire (`npm run lint`, `pnpm lint`, `ng lint`, `npx expo lint`) et les options de la CI (skill `repository-discovery`).
- Vérification du formatage : `npx prettier --check <fichiers>` ou `npx biome check <fichiers>` ; correction limitée à tes fichiers (`npx prettier --write <fichiers>`, `npx biome check --write <fichiers>`, `npx eslint --fix <fichiers>`), puis relecture du diff.
- `git diff --stat` ne doit pas contenir de fichiers reformatés hors de la tâche.

### 2. Nouveau projet : socle par défaut
Choisis selon le skill `autonomy-policy` et consigne le choix ; par défaut, garde ce que fournit l'outil de création du framework et complète :
- **ESLint en configuration plate** (`eslint.config.mjs`, version installée par le framework) avec `typescript-eslint` (préréglage `recommendedTypeChecked` si le temps de lint reste raisonnable, pour attraper les promesses flottantes), plus la configuration du framework : `angular-eslint` (`ng add angular-eslint`), `eslint-config-next`, `eslint-config-expo`, `eslint-plugin-react-hooks` pour React.
- **Formatage** : Prettier, avec `eslint-config-prettier` pour couper les règles de style d'ESLint ; ou Biome seul (lint et format) si le projet n'a pas besoin des règles propres au framework absentes de Biome. Jamais Prettier et Biome ensemble sur les mêmes fichiers.
- **Typage** : script `typecheck` (`tsc --noEmit`, ou `ng build` pour Angular) séparé du lint.
- **Scripts** : `lint`, `format`, `format:check`, `typecheck` dans `package.json`, appelés par la CI.
- **Éditeur** : `.editorconfig` cohérent avec le formateur.

### 3. Corriger un échec
1. Lis la règle et la ligne ; corrige le code.
2. Faux positif avéré : `// eslint-disable-next-line <règle> -- <raison>` sur la ligne, jamais un `eslint-disable` de fichier ni une règle désactivée dans la configuration ; cité dans le compte rendu.

## Livrable
Pour un nouveau projet : la configuration des outils, les scripts et la CI, et leur justification dans le journal. Pour une tâche : les commandes lancées et leur résultat.

## Vérifications
- Les commandes de lint, de format et de typage de la CI passent en local.
- Aucun `eslint-disable` sans règle nommée et sans raison ajouté (recherche sur le diff).
- Aucun fichier reformaté hors de la tâche.

## Limites
- Les règles d'écriture (typage, unions, asynchrone) sont dans le skill `coding-conventions-typescript` ; ce skill porte les outils.

## En cas de blocage
- Lint typé trop lent sur un gros projet : garder le préréglage typé sur les dossiers source et l'exclure des fichiers de configuration et générés, plutôt que de le retirer.
- Configuration héritée (`.eslintrc`) incompatible avec la version d'ESLint installée : signale-le et propose la migration (`npx @eslint/migrate-config`) comme tâche du plan, sans la faire dans une tâche sans rapport.
