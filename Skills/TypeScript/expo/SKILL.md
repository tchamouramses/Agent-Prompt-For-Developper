---
name: expo
description: Savoir Expo et React Native pour coder juste du premier coup - repérer le SDK et la New Architecture, Expo Go ou development build, Expo Router, configuration native par app.config et config plugins (CNG), versions compatibles avec expo install, permissions, notifications, EAS Build et Update. À utiliser pour toute tâche de code, de revue ou de débogage dans une application Expo.
---

# Expo

Les standards de base (Expo Router, `expo-secure-store`, listes performantes) sont dans l'agent `expo-mobile-implementer`. Ce skill donne ce que le modèle rate le plus souvent : les contraintes du SDK installé et la frontière entre JavaScript et code natif.

## Quand l'utiliser
- Toute tâche qui écrit, relit ou débogue du code dans un projet qui dépend de `expo`.
- Avant d'ajouter une librairie, une permission, une notification ou une configuration native.

## Ce que l'agent rate sans ce skill
- Il installe une librairie avec `npm install` et obtient une version incompatible avec le SDK ; `npx expo install` choisit la bonne.
- Il ajoute une librairie à code natif et la teste dans Expo Go, où elle n'existe pas ; il faut un development build.
- Il modifie `android/` ou `ios/` à la main alors que le projet les régénère (`expo prebuild`) : la modification disparaît au prochain build.
- Il oublie le texte de justification d'une permission iOS, et l'application est refusée ou plante à la demande.
- Il publie par EAS Update un changement qui touche le code natif : les applications installées ne peuvent pas l'exécuter.
- Il met un secret dans une variable `EXPO_PUBLIC_`, embarquée en clair dans l'application.

## Entrées
- `package.json` (`expo` et sa version, `expo-router`, `react-native`, `expo-dev-client`), `app.json` ou `app.config.ts`, `eas.json`, présence et suivi git de `android/` et `ios/`, `.gitignore`.

## Procédure

### 1. Situer le projet
1. SDK : version de `expo` ; `npx expo-doctor` signale les dépendances incompatibles et les problèmes de configuration.
2. Architecture : la New Architecture de React Native est activée par défaut à partir du SDK 53, puis devient la seule prise en charge ; vérifie qu'une librairie la prend en charge avant de l'ajouter (`npx expo-doctor`, React Native Directory).
3. Flux natif : si `android/` et `ios/` sont ignorés par git, le projet suit le Continuous Native Generation (CNG) : toute configuration native passe par `app.config` et des config plugins. S'ils sont versionnés, le projet est « bare » : la modification native se fait dans ces dossiers, et `prebuild` ne doit pas être relancé sans accord du projet.
4. Exécution : Expo Go seulement si toutes les librairies natives sont incluses dans Expo Go ; sinon development build (`expo-dev-client`, `npx expo run:android|ios` ou build EAS de développement).

### 2. Pièges à éviter
- **Dépendances** : `npx expo install <paquet>` ; `npx expo install --check` pour aligner. Pas de version forcée à la main hors de la plage du SDK.
- **Expo Router** : routes par fichiers dans `app/`, `_layout.tsx` pour piles et onglets, groupes `(nom)` sans segment d'URL, paramètres lus par `useLocalSearchParams()` et validés (ils viennent aussi des liens profonds) ; routes protégées par la redirection du layout ou `Stack.Protected` selon la version, jamais seulement en cachant un bouton.
- **Configuration native** : `app.config.ts` (valeurs par environnement), config plugins des librairies ; permissions iOS avec leur texte (`ios.infoPlist` ou option du plugin), permissions Android déclarées ; schéma de liens profonds déclaré.
- **Permissions à l'exécution** : demandées au moment de l'usage, refus géré (explication et lien vers les réglages), statut relu au retour dans l'application.
- **Notifications** : `expo-notifications` ; les notifications distantes demandent un development build (pas Expo Go) et des identifiants configurés dans EAS (action réservée si un compte est à créer).
- **Variables d'environnement** : `EXPO_PUBLIC_` embarquées en clair et figées au build ; secrets côté serveur uniquement. Les secrets de build passent par les variables d'environnement EAS, pas par le dépôt.
- **Stockage** : jetons dans `expo-secure-store` ; AsyncStorage ou MMKV pour des données non sensibles.
- **EAS Update** : seulement pour du JavaScript et des assets compatibles avec la `runtimeVersion` des builds installés ; un changement natif (nouvelle librairie native, permission, config plugin) demande un nouveau build. Une mise à jour vers un canal de production est une action réservée.
- **Plateformes** : zones sûres (`react-native-safe-area-context`), clavier (`KeyboardAvoidingView` ou la librairie du projet), affichage bord à bord sur Android selon le SDK, mode sombre ; tester iOS et Android, ou dire lequel n'a pas été vérifié.

### 3. Tests
- `jest-expo` comme préréglage Jest, React Native Testing Library (`render`, `screen.getByRole`, `userEvent`) ; modules natifs simulés par les mocks fournis par Expo ou le projet (skill `testing-typescript`).
- Parcours sur appareil ou simulateur avec l'outil E2E du projet (Maestro, Detox) : skill `e2e-testing`.

### 4. Générer et nettoyer
- Après une suppression, retire aussi l'écran, l'asset, la permission devenue inutile, le config plugin et la dépendance.
- Montée de SDK : skill `upgrade-expo`. Lint et formatage : skill `lint-format-typescript`. Composants : skill `react`.

### 5. Internationalisation (projet multilingue)
Règles communes, contrôles et livrable : skill `i18n`. Spécifique à Expo :
- Langue de l'appareil par `getLocales()` d'`expo-localization` (le premier élément est la langue préférée) et calendrier ou fuseau par `getCalendars()` ; choix de l'utilisateur persisté (AsyncStorage) et prioritaire ; écoute du changement de langue système au retour au premier plan.
- Traductions avec `i18next` et `react-i18next` (règles du skill `react`) ; pluriels et `Intl` : vérifie leur disponibilité sur le moteur JavaScript du SDK (Hermes) et sur les deux plateformes, et ajoute les polyfills FormatJS seulement s'ils manquent.
- Textes natifs hors JavaScript (nom de l'application, textes des demandes de permission) : traduits par le champ `locales` d'`app.config.ts` (un fichier JSON par langue) ; support RTL déclaré par `supportsRTL` (dans `extra` ou dans les options du config plugin `expo-localization` selon le SDK, vérifié dans sa documentation) ; ces changements natifs demandent un nouveau build.
- RTL : `I18nManager.forceRTL()` puis redémarrage (`Updates.reloadAsync()`), styles en `start`/`end` et `marginStart`, icônes directionnelles inversées par `I18nManager.isRTL`.

## Livrable
Le code de la tâche compatible avec le SDK installé, et dans le compte rendu : version du SDK, Expo Go ou development build, CNG ou bare, plateformes vérifiées.

## Vérifications
- `npx expo-doctor` sans nouvelle erreur, lint, `tsc --noEmit` et tests verts.
- Toute librairie ajoutée l'a été par `npx expo install` et prend en charge la New Architecture si elle est active.
- Toute nouvelle permission a son texte de justification et la gestion du refus.

## Limites
- La soumission aux stores, les mises à jour publiées vers les utilisateurs et la création de comptes ou d'identifiants (Apple, Google, EAS) sont des actions réservées (règle 5 des principes communs).

## En cas de blocage
- Librairie incompatible avec le SDK ou la New Architecture : cherche l'équivalent du SDK Expo ou une librairie compatible selon la règle 4 des principes communs, et consigne le choix.
- Pas de simulateur ni d'appareil disponible : tests unitaires et de composants seulement, rendu natif marqué **non vérifié**.
