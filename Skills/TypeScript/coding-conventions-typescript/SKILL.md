---
name: coding-conventions-typescript
description: Écrire du TypeScript strict et cohérent avec le projet - réglages du tsconfig, pas de any, unknown et rétrécissement, unions discriminées et contrôle exhaustif, validation des données aux frontières, promesses jamais flottantes, imports et nommage du projet. À utiliser pour écrire ou relire du code TypeScript (Angular, Next.js, Expo, Node).
---

# Conventions TypeScript

Les règles générales (lisibilité, SOLID, zéro code mort, changement minimal) sont dans les principes des agents qui modifient du code. Ce skill les traduit en TypeScript.

## Quand l'utiliser
- Écrire, refactorer ou relire du code TypeScript, côté navigateur, serveur ou mobile.

## Ce que l'agent rate sans ce skill
- Il fait taire le compilateur avec `any`, `as` ou `!` au lieu de prouver le type.
- Il fait confiance au type d'une réponse d'API ou d'un `JSON.parse` sans validation : le type ment à l'exécution.
- Il laisse une promesse flottante (`save()` sans `await` ni gestion d'erreur) : l'erreur disparaît.
- Il écrit un `switch` sur une union sans contrôle d'exhaustivité, et un nouveau cas passe inaperçu.
- Il duplique un type existant au lieu de le dériver (`Pick`, `Omit`, `z.infer`).
- Il utilise `@ts-ignore`, qui reste silencieux quand l'erreur disparaît.

## Entrées
- `tsconfig*.json` (`strict`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `paths`, `moduleResolution`), configuration ESLint, librairie de validation du projet (Zod, Valibot, class-validator…), fichiers voisins.

## Procédure
1. **Respecter le tsconfig** : ne baisse jamais un réglage de rigueur. Avec `noUncheckedIndexedAccess`, un accès `tableau[i]` ou `objet[cle]` est `T | undefined` : traite le cas.
2. **Pas de `any`** : `unknown` pour une valeur dont on ignore le type, puis rétrécissement (`typeof`, `in`, `instanceof`, garde de type `estX(v): v is X`). `as` seulement quand le compilateur ne peut pas savoir ce que tu as prouvé, avec la preuve à côté ; jamais `as unknown as X`. `!` (non-null) seulement juste après un contrôle que le compilateur ne voit pas.
3. **Frontières validées** : réponse d'API, `JSON.parse`, stockage local, paramètres d'URL, variables d'environnement, messages reçus : validés par le schéma de la librairie du projet, et le type est dérivé du schéma (`z.infer<typeof schema>`). Pas de schéma et de type écrits séparément.
4. **Modéliser avec des unions** :
   - union discriminée pour des états (`{ etat: 'chargement' } | { etat: 'erreur'; message: string } | { etat: 'ok'; donnees: T }`) plutôt que des booléens combinés ;
   - unions de littéraux (`'brouillon' | 'publie'`) ou objet `as const` ; `enum` seulement si le projet l'utilise déjà ;
   - contrôle d'exhaustivité : `default: { const impossible: never = valeur; throw new Error(...) }` ;
   - `satisfies` pour vérifier une valeur contre un type sans perdre son type précis.
5. **Types dérivés** : `Pick`, `Omit`, `Partial`, `ReturnType`, `Awaited`, types indexés plutôt que de recopier un type ; un type partagé entre front et back vient du contrat généré ou du paquet partagé (skill `monorepo`).
6. **Asynchrone** : chaque promesse est attendue, renvoyée, ou explicitement lancée sans attente avec gestion d'erreur (`void tache().catch(signaler)`) ; requêtes indépendantes en parallèle (`Promise.all`, `Promise.allSettled` si un échec ne doit pas tout arrêter).
7. **Erreurs** : `catch (e)` reçoit `unknown` : rétrécis avant d'utiliser `e.message` ; erreurs métier nommées (classes ou résultats typés) ; jamais de `catch` vide.
8. **Imports et nommage** : alias de chemins du projet (`@/…`) ; `import type` pour les imports de types si le projet ou `verbatimModuleSyntax` l'exige ; nommage de fichiers selon le framework (`kebab-case` Angular, conventions du routeur Next.js et Expo Router) ; `camelCase` pour variables et fonctions, `PascalCase` pour types et composants ; noms booléens en `estX`, `aX` ou `isX` selon la langue du code.
9. **Suppressions** : `// @ts-expect-error <raison>` plutôt que `@ts-ignore`, et seulement pour un défaut de typage d'une dépendance ; cité dans le compte rendu.
10. **Style et lint** : outils et commandes du skill `lint-format-typescript`.

## Livrable
Du code conforme, et dans le compte rendu les commandes de typage et de lint lancées avec leur résultat.

## Vérifications
- `tsc --noEmit` (ou la commande de typage du projet) sans nouvelle erreur.
- Aucun `any`, `as unknown as`, `@ts-ignore` ou désactivation de règle ESLint ajouté sans justification dans le compte rendu (recherche sur le diff).
- Chaque donnée externe nouvellement lue passe par un schéma de validation.

## Limites
- Les conventions déjà en place dans le projet l'emportent sur ce skill (principes communs, règle 1). Ce skill sert quand le projet ne tranche pas.
- Les règles propres aux frameworks : skills `angular`, `nextjs`, `expo`, `react`.

## En cas de blocage
- Type d'une dépendance faux ou absent : déclaration locale minimale (`declare module`) ou `@ts-expect-error` ciblé, et signalement dans le compte rendu.
- Projet sans `strict` : ne l'active pas dans une tâche sans rapport ; écris ton code comme s'il l'était, et propose l'activation comme tâche du plan.
