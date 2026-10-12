---
name: version-compatibility
description: Identifier les versions réellement installées (langage, framework, librairies) et vérifier que chaque API, option ou syntaxe utilisée existe dans ces versions. À utiliser avant d'écrire du code qui appelle un framework ou une librairie, avant de proposer une librairie, et pendant une montée de version.
---

# Compatibilité des versions

## Quand l'utiliser
- Avant d'utiliser une API d'un framework ou d'une librairie dont tu n'es pas certain qu'elle existe dans la version du projet.
- Avant de proposer une librairie (compatibilité avec le langage et le framework installés).
- Pendant une montée de version ou après une erreur du type « méthode inconnue », « option non reconnue », « module introuvable ».

## Ce que l'agent rate sans ce skill
- Il écrit pour la dernière version qu'il connaît (ou pour une ancienne) : API supprimées, options renommées, syntaxes non encore disponibles.
- Il lit la contrainte du manifeste (`^10.0`) au lieu de la version réellement installée (10.48.2).
- Il mélange les documentations de deux versions majeures (Angular modules contre standalone, Next.js Pages Router contre App Router, Laravel 10 contre 11, Spring Boot 2 contre 3 et `javax` contre `jakarta`).
- Il affirme une compatibilité sans l'avoir vérifiée.

## Entrées
- Le dépôt, la liste des API ou librairies que la tâche va utiliser.

## Procédure
1. **Lire la version installée, pas la contrainte.** Source de vérité dans l'ordre :
   - fichier de verrouillage : `composer.lock`, `package-lock.json` / `pnpm-lock.yaml` / `yarn.lock`, `gradle.lockfile` ;
   - sinon commande de l'outil : `composer show <paquet>`, `npm ls <paquet>` / `pnpm why <paquet>`, `mvn dependency:tree`, `./gradlew dependencies` ;
   - version du langage : `php -v`, `node -v`, `java -version`, et la contrainte du projet (`composer.json` `require.php`, `engines`, `.nvmrc`, `maven.compiler.release`, toolchain Gradle).
2. **Noter les marqueurs de génération** qui changent la façon d'écrire le code : routeur (Next.js `app/` contre `pages/`), composants autonomes (Angular), structure d'application (Laravel 11 sans `Kernel.php`), espace de noms `jakarta.*` (Spring Boot 3), architecture de React Native (nouvelle architecture activée ou non), SDK Expo.
3. **Vérifier chaque API incertaine** avant de l'utiliser, par ordre de fiabilité :
   1. le code source installé (`vendor/<paquet>`, `node_modules/<paquet>`, types `.d.ts`, sources Maven) : la signature y fait foi ;
   2. la documentation officielle **de la version installée** (sélecteur de version, outil de documentation disponible dans la session) ;
   3. le guide de migration officiel entre la version de ta mémoire et la version installée.
   Ne te fie pas à ta mémoire pour une API que tu n'as pas vue dans le projet.
4. **Pour une librairie proposée** : vérifier la plage de versions compatibles avec le langage et le framework installés, la date de la dernière version et l'état de maintenance, avant de la présenter dans le tableau d'options des principes communs.
5. **Consigner** dans ton compte rendu les versions utilisées et toute API vérifiée qui diffère de l'usage courant.

## Livrable
```markdown
Versions : PHP 8.3.12, Laravel 11.31.0 (composer.lock), Pest 3.5
API vérifiées : `Schedule::command()` dans routes/console.php (Laravel 11, plus de Console\Kernel), vérifié dans vendor/laravel/framework/src/Illuminate/Support/Facades/Schedule.php
```

## Vérifications
- Chaque version citée vient d'un fichier de verrouillage ou d'une commande, avec sa source.
- Aucune API incertaine n'est utilisée sans vérification ; le build ou l'analyse statique passe.

## Limites
- Ne mets pas à jour une dépendance au passage pour obtenir une API : utilise celle de la version installée, ou fais de la montée de version une tâche séparée (`refactorer`).

## En cas de blocage
- Versions incohérentes entre manifeste, verrou et environnement : signale-le avant de coder.
- API indisponible dans la version installée : propose l'alternative compatible, ou la montée de version comme option à valider.
