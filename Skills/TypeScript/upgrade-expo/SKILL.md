---
name: upgrade-expo
description: Monter de version le SDK Expo en sécurité - un SDK à la fois, notes de version et guide officiel, npx expo install --fix, expo-doctor, New Architecture, régénération native (CNG) ou adaptation des dossiers natifs, nouveau build obligatoire avant toute mise à jour OTA. À utiliser pour toute montée de version du SDK Expo ou de React Native dans un projet Expo.
---

# Montée de version Expo

La méthode générale (filet de tests, étapes courtes, une version majeure à la fois) est dans l'agent `refactorer`. Ce skill donne l'ordre propre à Expo, où chaque SDK fixe la version de React Native et de tous les modules.

## Quand l'utiliser
- Montée de version du SDK Expo (et donc de React Native et React).
- Une librairie ou une exigence des stores impose un SDK plus récent.

## Ce que l'agent rate sans ce skill
- Il saute plusieurs SDK d'un coup et accumule des changements cassants impossibles à isoler.
- Il met à jour `expo` sans réaligner les autres modules : versions incompatibles et plantage au démarrage.
- Il oublie la New Architecture : une librairie qui ne la prend pas en charge casse à l'exécution.
- Il publie le résultat par EAS Update vers des applications construites avec l'ancien SDK.

## Entrées
- `package.json`, `app.config.*`, `eas.json`, `runtimeVersion`, présence de `android/` et `ios/` versionnés ou non, librairies natives, suite de tests.

## Procédure
1. **Préparer** : lint, typage, tests et `npx expo-doctor` verts, commandes citées ; branche dédiée.
2. **Lire** les notes de version du SDK cible (blog Expo) et la page de mise à jour de la documentation ; liste les changements cassants et les modules dépréciés ou remplacés qui touchent le projet, et le changement de version de React Native (et son guide de mise à jour s'il y a du code natif).
3. **Monter d'un SDK** : `npx expo install expo@^<N+1>.0.0`, puis `npx expo install --fix` pour aligner tous les modules sur ce SDK.
4. **Contrôler** : `npx expo-doctor` ; corrige chaque problème signalé (librairie incompatible, dépendance dupliquée, configuration obsolète).
5. **Code natif** :
   - CNG (dossiers natifs ignorés par git) : rien à modifier à la main ; `npx expo prebuild --clean` en local pour vérifier que la génération fonctionne, sans versionner le résultat ;
   - projet « bare » : appliquer les changements natifs du guide de mise à jour de React Native (outil de différences entre versions) dans `android/` et `ios/`.
6. **New Architecture** : vérifier chaque librairie native sur sa prise en charge ; remplacer celles qui bloquent (règle 4 des principes communs).
7. **Vérifier** : lint, typage, tests, `npx expo-doctor`, development build sur Android et iOS quand c'est possible (sinon **non vérifié** pour la plateforme manquante), parcours principaux (skill `e2e-testing`).
8. **Répéter** SDK par SDK jusqu'à la cible ; un commit par SDK.
9. **Préparer la publication** : la nouvelle version demande de nouveaux builds ; `runtimeVersion` changée ; aucune EAS Update vers les applications de l'ancien SDK. Les builds de production et la soumission sont des actions réservées : prépare les commandes.
10. **Consigner** dans le journal et un ADR : SDK de départ et d'arrivée, librairies remplacées, changements de comportement.

## Livrable
L'application sur le SDK cible, `expo-doctor`, tests et typage verts, une entrée de journal et un ADR, la ligne de CHANGELOG si le comportement visible change.

## Vérifications
- `expo` et tous les modules sont dans les versions attendues par le SDK (`npx expo install --check` sans écart).
- `npx expo-doctor` sans erreur.
- `runtimeVersion` adaptée pour qu'aucune mise à jour OTA n'atteigne un build de l'ancien SDK.

## Limites
- Builds de production, soumission aux stores et publication de mises à jour sont des actions réservées (règle 5 des principes communs).

## En cas de blocage
- Librairie sans version compatible avec le SDK ou la New Architecture : rester sur le SDK actuel, consigner le blocage, proposer un remplaçant selon la règle 4 des principes communs.
- Build natif impossible dans l'environnement (pas d'Xcode, pas de SDK Android) : vérifications JavaScript seulement, build marqué **non vérifié** avec la commande EAS de prévisualisation prête.
