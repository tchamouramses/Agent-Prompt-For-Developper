---
name: ci-github-actions
description: Écrire des workflows GitHub Actions bloquants et sûrs - un workflow par stack (Laravel, Symfony, Spring Boot, Angular, Next.js, Expo), cache des dépendances, matrice seulement quand elle sert, permissions minimales, actions épinglées par SHA, concurrence, délais, services de base de données, et aucun déploiement sans accord humain. À utiliser pour créer la CI d'un projet, ajouter ou corriger un job, accélérer une CI lente ou réparer une CI rouge.
---

# CI GitHub Actions

Les règles que la CI doit faire respecter sont dans le skill `quality-gates` ; affaiblir une étape pour obtenir le vert est interdit (règle 5 des principes communs, « Interdit même pour avancer »). Déployer, créer un secret de dépôt ou régler la protection de branche sont des actions réservées : la CI les prépare, l'humain les active.

## Quand l'utiliser
- `scaffolder` : CI de base d'un nouveau projet. `devops-engineer` : toute création ou modification de `.github/workflows/`.
- Tout agent dont la CI est rouge sur sa branche.

## Ce que l'agent rate sans ce skill
- Il écrit `uses: actions/checkout@v4` (étiquette mobile) ou recopie un SHA de mémoire, faux ou périmé.
- Il omet `permissions:` : le jeton reçoit les droits par défaut du dépôt, souvent en écriture.
- Il utilise `pull_request_target` avec un checkout du code de la PR, ce qui exécute du code non relu avec des secrets.
- Il ajoute `continue-on-error: true`, `|| true` ou `--passWithNoTests` pour passer au vert.
- Il met une matrice de six versions sur une application qui tourne sur une seule version en production.
- Il met en cache `node_modules` ou `vendor` au lieu du cache du gestionnaire, ou oublie la clé basée sur le fichier de verrouillage.
- Il ajoute un job qui déploie en production à chaque push sur `main`.
- Il teste sur SQLite alors que la production tourne sur PostgreSQL ou MySQL.

## Entrées
- Manifestes, fichiers de verrouillage et scripts du projet ; versions cibles (`.nvmrc`, `composer.json` `require.php`, toolchain Java, `docs/architecture.md`).
- Workflows existants, moteur de base de production, `docs/runbook.md`.

## Procédure
1. **Reprendre les commandes locales** du projet (README, scripts) : la CI exécute les mêmes, dans le même ordre que `quality-gates` : installation, lint, analyse statique ou typage, tests, audit (skill `dependency-audit`), build.
2. **Squelette commun** : `on: pull_request` et `push: branches: [main]` ; `permissions: contents: read` au niveau du workflow, élargi job par job seulement si nécessaire ; `concurrency: { group: ${{ github.workflow }}-${{ github.ref }}, cancel-in-progress: true }` ; `timeout-minutes` sur chaque job ; `runs-on: ubuntu-latest` sauf besoin (iOS : `macos-latest`).
3. **Épingler chaque action tierce par SHA complet**, étiquette en commentaire. Récupère la dernière version et son commit sans te fier à ta mémoire :
   ```bash
   gh release view -R actions/checkout --json tagName -q .tagName
   gh api repos/actions/checkout/commits/<tag> -q .sha
   ```
   Ajoute `.github/dependabot.yml` avec `package-ecosystem: github-actions` pour tenir les épinglages à jour.
4. **Cache** : `actions/setup-node` avec `cache: npm` (ou `pnpm`, `yarn`), `actions/setup-java` avec `cache: maven` ou `gradle`, PHP : `shivammathur/setup-php` puis `actions/cache` sur `composer config cache-files-dir`, clé `hashFiles('**/composer.lock')`. Next.js : cache de `.next/cache` en plus.
5. **Étapes par stack** (adapter aux scripts présents) :
   - Laravel : `composer install --no-interaction --prefer-dist`, `cp .env.example .env && php artisan key:generate`, `./vendor/bin/pint --test`, `./vendor/bin/phpstan analyse`, `php artisan test`, `npm ci && npm run build` si Vite.
   - Symfony : `composer install --no-interaction`, `bin/console lint:container`, `vendor/bin/phpstan analyse`, `vendor/bin/phpunit` (ou `bin/phpunit`).
   - Spring Boot : `./mvnw -B verify` ou `./gradlew build`.
   - Angular : `npm ci`, `npx ng lint` si configuré, `npx ng test --watch=false` (avec `--browsers=ChromeHeadless` sous Karma), `npx ng build`.
   - Next.js : `npm ci`, script `lint` du projet, `npx tsc --noEmit`, `npm test`, `npm run build`.
   - Expo : `npm ci`, `npx tsc --noEmit`, `npm test`, `npx expo-doctor`. Pas de `eas build` ni `eas submit` : compte et coût tiers, soumission aux stores (règle 5).
6. **Base de données** : `services:` avec l'image et la version majeure de production (`postgres:16`, `mysql:8.4`), `options: --health-cmd ...`, variables de connexion de test en clair (valeurs factices) ; un vrai secret passe par `${{ secrets.<NOM> }}` (skill `env-secrets`).
7. **Matrice** seulement pour une bibliothèque ou un projet qui supporte officiellement plusieurs versions ; une application teste la version de production. `fail-fast: false` si l'on veut voir toutes les cellules.
8. **Déploiement** : s'il est demandé, un workflow séparé `on: workflow_dispatch` avec `environment: production` ; les relecteurs obligatoires de l'environnement et ses secrets se règlent dans les paramètres du dépôt, action réservée à préparer (skill `deployment-checklist`).
9. **Vérifier** : `actionlint` s'il est disponible, puis pousse la branche et lis le résultat (`gh run list --branch <branche>`, `gh run view <id> --log-failed`).

## Livrable
```yaml
name: CI
on:
  pull_request:
  push:
    branches: [main]
permissions:
  contents: read
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@<sha> # <tag>
      - uses: actions/setup-node@<sha> # <tag>
        with: { node-version-file: .nvmrc, cache: npm }
      - run: npm ci
      - run: npm run lint
      - run: npm test
      - run: npm run build
```

## Vérifications
- La CI est verte sur la branche de travail : identifiant du run et conclusion cités.
- `rg -n "uses: [^@]+@(v[0-9]|main|master)" .github/workflows` ne renvoie rien ; chaque workflow déclare `permissions:`.
- Aucun `continue-on-error`, `|| true`, test sauté ou étape retirée par rapport à l'état de départ sans justification consignée.

## Limites
- Secrets de dépôt, environnements, protection de branche et activation de GitHub Pages ou d'un registre se règlent dans les paramètres du dépôt : réservés, à préparer.
- Les minutes payantes (dépôt privé au-delà du quota, runners macOS) sont un coût : signale-le si la CI les consomme.

## En cas de blocage
- CI rouge pour un défaut préexistant hors de ta tâche : ne le masque pas ; isole-le, consigne-le et ajoute la tâche au plan (skill `quality-gates`).
- Étape impossible sans secret réel (test d'intégration avec un service tiers) : job conditionné à la présence du secret, documenté, et création du secret proposée comme décision humaine.
