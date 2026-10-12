---
name: angular
description: Savoir Angular pour coder juste du premier coup - repérer la version et les choix du projet (standalone ou NgModules, signaux, zone.js ou sans zone, SSR), utiliser les API de la version installée, éviter les pièges RxJS, de détection des changements, de rendu serveur et de tests. À utiliser pour toute tâche de code, de revue ou de débogage dans une application Angular.
---

# Angular

Les standards de base (composants standalone, `OnPush`, contrôle de flux moderne) sont dans l'agent `angular-implementer`. Ce skill donne ce que le modèle rate le plus souvent : ce qui dépend de la version, et les pièges qui ne se voient qu'à l'exécution.

## Quand l'utiliser
- Toute tâche qui écrit, relit ou débogue du code dans un projet qui dépend de `@angular/core`.
- Avant d'utiliser une API Angular dont tu n'es pas sûr qu'elle existe ou soit stable dans la version installée.

## Ce que l'agent rate sans ce skill
- Il crée un `NgModule` dans un projet standalone, ou un composant standalone mal importé dans un projet à modules.
- Il utilise une API expérimentale ou en aperçu (`resource()`, formulaires à signaux) comme si elle était stable, ou une API absente de la version.
- Il s'abonne dans un composant sans désabonnement, ou imbrique des `subscribe`.
- Il mute un objet passé en `input` d'un composant `OnPush` et l'écran ne se met pas à jour.
- Il accède à `window`, `document` ou `localStorage` dans du code exécuté au rendu serveur.
- Il écrit des tests Karma/Jasmine dans un projet qui utilise Vitest ou Jest, ou l'inverse.

## Entrées
- `package.json` (`@angular/core` et sa version, `@angular/ssr`, `zone.js`, librairie de composants, `@ngrx/*` ou autre gestion d'état, outil de test), `angular.json` (builder, test runner), `src/app/app.config.ts` ou `app.module.ts`, composants voisins.

## Procédure

### 1. Situer le projet
1. Version : `ng version` ou `@angular/core` dans `package.json`. Note : standalone (`app.config.ts`, `bootstrapApplication`) ou modules (`AppModule`) ; avec ou sans `zone.js` (`provideZonelessChangeDetection()`) ; SSR (`@angular/ssr`) ; builder (`@angular/build:application` ou ancien `browser`) ; lanceur de tests.
2. Repère ce qui dépend de la version (vérifie le statut stable ou expérimental dans la documentation de la version installée, skill `version-compatibility`) :

| API | Disponible à partir de |
|-----|------------------------|
| Composants standalone, `inject()` | 14–15 ; standalone par défaut à partir de 19 |
| `@if`, `@for`, `@switch`, `@defer` | 17 |
| Signaux, `computed()`, `effect()`, `toSignal()` | 16–17 |
| `input()`, `model()`, `output()`, requêtes à signaux (`viewChild()`) | 17.1 à 17.3 |
| `linkedSignal()`, `resource()` | 19 (vérifier le statut) |
| Détection des changements sans zone | expérimentale en 18, stable ensuite ; par défaut pour les nouveaux projets récents |

3. Suis le style du projet : un projet à modules garde ses modules pour le code existant ; un nouveau composant y est standalone seulement si le projet a commencé cette migration.

### 2. Pièges à éviter
- **RxJS** : un abonnement dans un composant est libéré (`takeUntilDestroyed()`, pipe `async`, `toSignal()`) ; pas de `subscribe` imbriqué : `switchMap` (recherche, navigation), `concatMap` (écritures dans l'ordre), `exhaustMap` (bouton soumis plusieurs fois) ; erreurs gérées dans le flux (`catchError`) pour ne pas tuer l'abonnement.
- **Détection des changements** : avec `OnPush` ou sans zone, l'écran se met à jour par les signaux, les `input` remplacés (immuables) et les événements du template ; pas de mutation d'un objet reçu en `input`. Pas de `ChangeDetectorRef.detectChanges()` pour masquer un problème de flux.
- **`effect()`** : réservé à la synchronisation avec l'extérieur (journal, stockage, librairie non Angular) ; pas pour recopier un signal dans un autre (utiliser `computed()` ou `linkedSignal()`).
- **Templates** : `@for` avec un `track` sur l'identifiant ; pas d'appel de méthode coûteuse dans le template (signal ou `computed()` à la place).
- **HTTP** : `provideHttpClient(withInterceptors([...]))` avec intercepteurs fonctionnels dans un projet standalone ; services qui renvoient des `Observable` typés ; pas d'appel HTTP dans un composant de présentation.
- **Rendu serveur** : code lié au navigateur dans `afterNextRender()` ou derrière `isPlatformBrowser()` ; hydratation (`provideClientHydration()`) : le rendu serveur et client doivent produire le même DOM (pas de date ou de valeur aléatoire calculée différemment).
- **Sécurité** : liaisons `[innerHTML]` assainies par Angular ; `bypassSecurityTrust*` seulement sur un contenu assaini côté serveur et justifié (skill `security-typescript`).
- **Formulaires** : formulaires réactifs typés (`FormGroup<{…}>`, `NonNullableFormBuilder`) ; les formulaires à signaux seulement si la version les rend stables ou si le projet les a adoptés.
- **Tests** : TestBed avec `provideHttpClient()` et `provideHttpClientTesting()`, `HttpTestingController.verify()` en fin de test ; harnais du CDK pour les composants de librairie ; lanceur du projet (`ng test` avec Karma, Jest ou Vitest selon `angular.json`), skill `testing-typescript`.

### 3. Générer et nettoyer
- Génère avec `ng generate` (schémas du projet). Après une suppression, retire aussi la route, le service, les styles, les clés de traduction et les tests devenus inutiles.
- Montée de version : skill `upgrade-angular`. Lint et formatage : skill `lint-format-typescript`.

### 4. Internationalisation (projet multilingue)
Règles communes, contrôles et livrable : skill `i18n`. Spécifique à Angular :
- **`@angular/localize`** (outil natif) : textes marqués dans les templates (`i18n="@@checkout.submit"`, `i18n-placeholder`, `i18n-aria-label`, `i18n-title`) et dans le code (`` $localize`:@@checkout.total:Total` ``) ; identifiants `@@` explicites et stables ; pluriels et choix en ICU dans le template (`{count, plural, =0 {…} one {…} other {…}}`). `ng extract-i18n --format=xlf2 --output-path src/locale` met à jour la source ; chaque fichier `messages.<langue>.xlf` reçoit toutes les cibles. Un build par langue (`localize: true` dans `angular.json`) : changer de langue recharge l'application sur l'URL de la langue.
- **Transloco** (si le projet l'utilise ou si la langue change sans rechargement) : pipe `transloco` ou directive structurelle dans les templates, `TranslocoService.translate()` seulement hors template, portées (`scope`) par fonctionnalité chargées à la demande ; `@jsverse/transloco-keys-manager` (`find` et `extract`) pour les clés manquantes et inutilisées ; `@jsverse/transloco-messageformat` pour les pluriels ICU.
- **Formats** : pipes `date`, `number`, `currency`, `percent` avec la langue active (`LOCALE_ID`, données de locale enregistrées par `registerLocaleData` ou fournies par `@angular/localize`) ; jamais de format écrit à la main dans un template.
- **Lint** : règle `@angular-eslint/template/i18n` (avec `@angular/localize`) sur les templates modifiés, pour repérer textes et attributs non marqués.
- **SSR** : la langue vient de l'URL ou de la requête, pas de `navigator.language` au rendu serveur.

## Livrable
Le code de la tâche conforme à la version installée, et dans le compte rendu : version d'Angular, mode standalone ou modules, zone ou sans zone, pièges vérifiés qui s'appliquaient.

## Vérifications
- `ng lint` (s'il est configuré), `ng test --watch=false` et `ng build` passent sans avertissement nouveau.
- Aucun abonnement non libéré dans les composants touchés.
- Aucune API expérimentale utilisée sans le signaler dans le compte rendu.

## Limites
- Les librairies de composants (Angular Material, PrimeNG…) et de gestion d'état (NgRx) ont leurs propres versions et conventions : lis leur version avant d'utiliser leurs API.

## En cas de blocage
- API absente de la version installée : utilise l'équivalent de cette version et consigne-le.
- Erreur d'hydratation ou de rendu serveur : identifie le code qui dépend du navigateur ou du temps, et déplace-le dans `afterNextRender()`.
