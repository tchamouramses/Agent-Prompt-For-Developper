---
name: testing-typescript
description: Écrire et lancer des tests TypeScript fiables avec les outils du projet (Vitest, Jest, Karma/Jasmine, Testing Library, MSW) - requêtes par rôle, interactions avec user-event, réseau simulé à la frontière, temps maîtrisé, et preuve d'exécution. À utiliser pour écrire, corriger ou juger des tests unitaires et de composants en Angular, Next.js, React, Expo ou Node.
---

# Tests TypeScript

Le choix des tests (niveau, cas, fiabilité) est dans le skill `testing-strategy`. Ce skill dit comment le faire avec l'outillage JavaScript et TypeScript. Les tests de navigateur et sur appareil sont dans le skill `e2e-testing`.

## Quand l'utiliser
- Écrire ou corriger des tests unitaires ou de composants dans un projet TypeScript.
- Relire des tests TypeScript (`code-reviewer`, `quality-gatekeeper`).

## Ce que l'agent rate sans ce skill
- Il écrit `jest.fn()` dans un projet Vitest (`vi.fn()`), ou utilise une API de Jasmine dans Jest.
- Il cherche les éléments par classe CSS ou `data-testid` alors qu'un rôle ou un label accessible existe.
- Il utilise `fireEvent` au lieu de `userEvent`, et le test ne reproduit pas une vraie saisie.
- Il simule le module `fetch` ou le service HTTP du projet au lieu d'intercepter le réseau.
- Il attend avec des délais réels (`setTimeout` de 500 ms) et le test devient lent et instable.
- Il remplace les vraies vérifications par des instantanés (snapshots) énormes que personne ne relit.

## Entrées
- `package.json` (scripts `test`, `vitest`, `jest`, `jest-expo`, `@testing-library/*`, `msw`), `vitest.config.*`, `jest.config.*`, `angular.json` (lanceur de tests), fichiers de mise en place (`setupTests.ts`), tests voisins.

## Procédure
1. **Suivre l'outil du projet** : Vitest (`vi`), Jest (`jest`), Karma/Jasmine (`jasmine.createSpy`) ou `node:test` ; copie la forme des tests voisins (emplacement `*.spec.ts` ou `*.test.ts`, `describe`/`it`, utilitaires de rendu).
2. **Composants avec Testing Library** (`@testing-library/react`, `@testing-library/angular`, `@testing-library/react-native`) :
   - requêtes dans l'ordre de préférence : `getByRole` (avec `name`), `getByLabelText`, `getByText`, et `getByTestId` en dernier recours ;
   - interactions avec `userEvent` (`const user = userEvent.setup(); await user.click(...)`) ;
   - attente d'un résultat asynchrone avec `findBy…` ou `waitFor`, jamais un délai fixe ;
   - teste les états visibles : chargement, vide, erreur, données, et le comportement après interaction.
3. **Réseau simulé à la frontière** : MSW (gestionnaires par route, `server.use()` pour un cas précis, `onUnhandledRequest: 'error'`) s'il est présent ; sinon le mécanisme du framework (`HttpTestingController` en Angular). Ne simule pas les fonctions d'accès aux données du projet quand un test peut les exercer avec le réseau simulé.
4. **Modules et temps** :
   - `vi.mock` et `jest.mock` sont remontés en haut du fichier : déclare les valeurs utilisées dans la fabrique avec `vi.hoisted` ou à l'intérieur de la fabrique ;
   - horloge simulée (`vi.useFakeTimers()`, `jest.useFakeTimers()`, `vi.setSystemTime`) pour les délais et les dates ; remise en état après chaque test (`useRealTimers`, `restoreAllMocks`).
5. **Isolation** : chaque test crée ses données et ne dépend pas de l'ordre ; état global (stores, cache de requêtes) recréé par test (nouveau `QueryClient` par test, par exemple).
6. **Instantanés** : seulement pour une sortie stable et petite (sérialisation, message d'erreur) ; jamais à la place d'assertions sur le comportement ; une mise à jour d'instantané est relue ligne à ligne.
7. **Lancer et prouver** :
   - un fichier ou un test : `npx vitest run chemin/fichier.test.ts -t "nom"`, `npx jest chemin -t "nom"`, `ng test --watch=false --include=chemin` ;
   - suite : le script du projet (`npm test -- --run`, `pnpm test`), en mode non interactif ;
   - cite le résumé exact (`Tests  42 passed (42)`, `Tests: 42 passed, 42 total`), pas une interprétation. Le typage (`tsc --noEmit`) est une vérification à part, pas un test.
8. **Couverture** si demandée : `--coverage` avec le fournisseur configuré (`v8` ou `istanbul`) ; sans configuration, **non vérifiée**.

## Livrable
Les tests, la commande lancée et son résumé, et la correspondance critère ou règle → test (skill `testing-strategy`).

## Vérifications
- Chaque nouveau test a été vu en échec puis en succès quand c'est possible.
- Aucun `.skip`, `.only`, `xit`, `fit` ou assertion retirée laissé dans le diff.
- Aucun avertissement nouveau dans la sortie des tests (`act(...)`, clés React, requête réseau non gérée).

## Limites
- N'ajoute pas de librairie de test si le projet en a une pour ce besoin (règle 4 des principes communs).
- Les particularités de chaque framework (TestBed Angular, Server Components Next.js, mocks natifs Expo) sont dans les skills `angular`, `nextjs` et `expo`.

## En cas de blocage
- Composant serveur asynchrone (Next.js) difficile à rendre en test unitaire : teste sa logique dans une fonction séparée et son rendu par un test E2E (skill `e2e-testing`).
- Test existant rouge avant ta modification : note-le comme état de départ ; `debugger` s'il bloque ta tâche.
