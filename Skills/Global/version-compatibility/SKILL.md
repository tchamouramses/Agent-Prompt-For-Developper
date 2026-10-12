---
name: version-compatibility
description: Identifier les versions réellement installées (langage, framework, librairies), consulter leur documentation officielle pour appliquer les pratiques recommandées de ces versions, et vérifier que chaque API, option ou syntaxe utilisée existe et n'est pas dépréciée. À utiliser avant d'écrire du code qui appelle un framework ou une librairie, avant de proposer une librairie, et pendant une montée de version.
---

# Compatibilité des versions

## Quand l'utiliser
- Avant d'écrire du code qui s'appuie sur un framework ou une librairie : toujours, même pour une API que tu crois connaître.
- Avant de proposer une librairie (compatibilité avec le langage et le framework installés).
- Pendant une montée de version ou après une erreur du type « méthode inconnue », « option non reconnue », « module introuvable ».

## Ce que l'agent rate sans ce skill
- Il écrit pour la dernière version qu'il connaît (ou pour une ancienne) : API supprimées, options renommées, syntaxes non encore disponibles.
- Il lit la contrainte du manifeste (`^10.0`) au lieu de la version réellement installée (10.48.2).
- Il mélange les documentations de deux versions majeures (Angular modules contre standalone, Next.js Pages Router contre App Router, Laravel 10 contre 11, Spring Boot 2 contre 3 et `javax` contre `jakarta`).
- Il applique les pratiques de la version de sa mémoire alors que la version installée en recommande d'autres, et produit du code déprécié (avertissements au build, suppression à la prochaine version majeure).
- Il affirme une compatibilité sans l'avoir vérifiée.

## Entrées
- Le dépôt, la liste des API ou librairies que la tâche va utiliser.

## Procédure
1. **Lire la version installée, pas la contrainte.** Source de vérité dans l'ordre :
   - fichier de verrouillage : `composer.lock`, `package-lock.json` / `pnpm-lock.yaml` / `yarn.lock`, `gradle.lockfile` ;
   - sinon commande de l'outil : `composer show <paquet>`, `npm ls <paquet>` / `pnpm why <paquet>`, `mvn dependency:tree`, `./gradlew dependencies` ;
   - version du langage : `php -v`, `node -v`, `java -version`, et la contrainte du projet (`composer.json` `require.php`, `engines`, `.nvmrc`, `maven.compiler.release`, toolchain Gradle).
2. **Noter les marqueurs de génération** qui changent la façon d'écrire le code : routeur (Next.js `app/` contre `pages/`), composants autonomes (Angular), structure d'application (Laravel 11 sans `Kernel.php`), espace de noms `jakarta.*` (Spring Boot 3), architecture de React Native (nouvelle architecture activée ou non), SDK Expo.
3. **Lire la documentation officielle de la version installée**, pas celle de ta mémoire, pour la fonctionnalité que tu codes :
   - la page du guide qui traite la fonctionnalité (manière recommandée de faire dans cette version) ;
   - le guide de migration (`UPGRADE.md`, notes de version) entre la version que tu connais et la version installée ;
   - la liste des dépréciations de cette version.
   Sources, dans l'ordre : outil de documentation de la session (serveur MCP de documentation, recherche ou lecture web) sur le site officiel avec le sélecteur de version ; à défaut, les fichiers livrés avec le paquet (`vendor/<paquet>/UPGRADE.md`, `CHANGELOG.md`, `node_modules/<paquet>/README.md`, `docs/`). Si aucune n'est accessible, dis-le dans ton compte rendu et appuie-toi sur le code source installé (étape 4).
4. **Vérifier chaque API** avant de l'utiliser, par ordre de fiabilité :
   1. le code source installé (`vendor/<paquet>`, `node_modules/<paquet>`, types `.d.ts`, sources Maven) : la signature y fait foi ;
   2. la documentation officielle **de la version installée** (sélecteur de version, outil de documentation disponible dans la session) ;
   3. le guide de migration officiel entre la version de ta mémoire et la version installée.
   Ne te fie pas à ta mémoire pour une API que tu n'as pas vue dans le projet. Une API marquée dépréciée (`@deprecated`, `#[\Deprecated]`, `@Deprecated`, avertissement de la documentation) est remplacée par son successeur recommandé.
5. **Pour une librairie proposée** : vérifier la plage de versions compatibles avec le langage et le framework installés, la date de la dernière version et l'état de maintenance, avant de la présenter dans le tableau d'options des principes communs.
6. **Contrôler les dépréciations** à la vérification : lis la sortie des tests et du build (`E_USER_DEPRECATED` et `php artisan test` ou PHPUnit avec `--display-deprecations`, `DeprecationWarning` de Node, avertissements `-Xlint:deprecation` de javac, avertissements du compilateur Angular ou de Next.js). Ton code n'en introduit aucun.
7. **Consigner** dans ton compte rendu les versions utilisées, les pages de documentation consultées et toute API vérifiée qui diffère de l'usage courant.

## Livrable
```markdown
Versions : PHP 8.3.12, Laravel 11.31.0 (composer.lock), Pest 3.5
Documentation : laravel.com/docs/11.x/scheduling, UPGRADE.md 10 → 11
API vérifiées : `Schedule::command()` dans routes/console.php (Laravel 11, plus de Console\Kernel), vérifié dans vendor/laravel/framework/src/Illuminate/Support/Facades/Schedule.php
Dépréciations : aucune nouvelle (php artisan test --display-deprecations)
```

## Vérifications
- Chaque version citée vient d'un fichier de verrouillage ou d'une commande, avec sa source.
- La documentation de la version installée a été consultée, ou son absence est signalée.
- Aucune API incertaine n'est utilisée sans vérification, aucune API dépréciée n'est introduite ; le build ou l'analyse statique passe sans nouvel avertissement de dépréciation.

## Limites
- Ne mets pas à jour une dépendance au passage pour obtenir une API : utilise celle de la version installée, ou fais de la montée de version une tâche séparée (`refactorer`).

## En cas de blocage
- Versions incohérentes entre manifeste, verrou et environnement : signale-le avant de coder.
- API indisponible dans la version installée : propose l'alternative compatible, ou la montée de version comme option à valider.
