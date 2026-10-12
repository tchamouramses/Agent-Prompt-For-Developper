---
name: nextjs
description: Savoir Next.js pour coder juste du premier coup - repérer la version et le routeur (App Router ou Pages Router), les API de requête asynchrones, le modèle de cache de la version installée, la frontière serveur/client, la sécurité des Server Actions et du middleware ou proxy. À utiliser pour toute tâche de code, de revue ou de débogage dans une application Next.js.
---

# Next.js

Les standards de base (Server Components par défaut, `"use client"` au plus bas, fichiers spéciaux) sont dans l'agent `nextjs-implementer`. Ce skill donne ce que le modèle rate le plus souvent : ce qui a changé d'une version à l'autre (beaucoup), et les pièges de sécurité et de cache.

## Quand l'utiliser
- Toute tâche qui écrit, relit ou débogue du code dans un projet qui dépend de `next`.
- Avant d'utiliser une API Next.js dont tu n'es pas sûr du comportement dans la version installée.

## Ce que l'agent rate sans ce skill
- Il lit `params`, `searchParams`, `cookies()` ou `headers()` de façon synchrone alors qu'ils sont asynchrones depuis Next.js 15.
- Il suppose que `fetch` est mis en cache par défaut (vrai en 14, faux à partir de 15), ou l'inverse, et sert des données périmées ou surcharge le serveur.
- Il traite une Server Action comme une fonction interne : c'est un point d'entrée HTTP public, appelable par n'importe qui.
- Il ne protège une page que dans le middleware : une faille de contournement a déjà existé, et le middleware ne protège pas les Server Actions ni les données.
- Il met un secret dans une variable `NEXT_PUBLIC_` ou importe un module serveur dans un composant client.
- Il appelle `redirect()` ou `notFound()` dans un `try` qui attrape tout : l'exception de contrôle est avalée.

## Entrées
- `package.json` (`next`, `react`), `next.config.*`, présence de `app/` ou `pages/` (ou sous `src/`), `middleware.ts` ou `proxy.ts`, solution d'authentification, d'accès aux données et de validation (Zod, Valibot…), composants voisins.

## Procédure

### 1. Situer le projet
1. Version : `next` dans `package.json` et `node_modules/next/package.json`. Routeur : `app/` (App Router) ou `pages/` (Pages Router), parfois les deux ; suis celui de la zone touchée.
2. Repère ce qui dépend de la version (vérifie dans la documentation de la version installée, skill `version-compatibility`) :

| Élément | Next.js 14 | Next.js 15 | Next.js 16 |
|---------|------------|------------|------------|
| `params`, `searchParams`, `cookies()`, `headers()` | synchrones | asynchrones (`await`), accès synchrone toléré avec avertissement | asynchrones uniquement |
| Cache de `fetch` et des `GET` de route handlers | en cache par défaut | pas en cache par défaut | modèle « Cache Components » (`"use cache"`) si activé |
| Interception des requêtes | `middleware.ts` | `middleware.ts` | `proxy.ts` (middleware déprécié) |
| React | 18 | 19 | 19 |

3. Lis `next.config.*` : options expérimentales activées (`cacheComponents`, `ppr`, `typedRoutes`), `images.remotePatterns`, en-têtes.

### 2. Frontière serveur et client
- Un module qui lit un secret ou la base importe `server-only` ; un composant client n'importe jamais ce module.
- Props passées d'un Server Component à un Client Component : sérialisables (pas de fonction sauf Server Action, pas de classe, dates converties).
- `"use client"` au plus bas : la page reste serveur, seul le bouton interactif est client.
- Variables `NEXT_PUBLIC_` : inscrites dans le code client **au moment du build** ; jamais de secret, et changer leur valeur demande un nouveau build.

### 3. Données et cache
- Données lues dans les Server Components, au plus près de l'usage, requêtes indépendantes lancées en parallèle (`Promise.all`) ; pas d'appel HTTP vers une route de la même application depuis le serveur : appelle directement la fonction d'accès aux données.
- Choisis explicitement le comportement de cache de chaque lecture selon la version (option `cache` et `next.revalidate` de `fetch`, `unstable_cache` ou `"use cache"` avec `cacheTag` et `cacheLife`) ; après une écriture, invalide ce qui l'affiche (`revalidatePath`, `revalidateTag`, `updateTag` selon la version).
- `useSearchParams()` dans un composant client d'une page statique : enveloppe-le dans `<Suspense>`.

### 4. Mutations et sécurité
- **Chaque Server Action et chaque route handler** : valide l'entrée avec le schéma du projet, vérifie l'authentification et l'autorisation sur la ressource, renvoie une erreur maîtrisée. La vérification d'accès vit dans la couche d'accès aux données (ou au début de l'action), pas seulement dans le middleware ou le proxy, ni dans la page.
- Les arguments d'une Server Action viennent du client, y compris les identifiants « cachés » dans un formulaire : ne leur fais jamais confiance pour l'autorisation.
- `redirect()` et `notFound()` lèvent une exception de contrôle : appelle-les hors d'un `try/catch`, ou relance l'erreur.
- Redirection vers une URL reçue (`?next=`) : chemin relatif seulement.
- Route handler qui lit des cookies et modifie des données : vérifie l'origine (les Server Actions le font nativement, pas les route handlers).

### 5. Rendu et hydratation
- Rendu identique côté serveur et client : pas de `Date.now()`, `Math.random()`, `window` ou locale du navigateur au rendu initial ; ces valeurs vont dans un effet ou viennent du serveur.
- `loading.tsx`, `error.tsx` (composant client), `not-found.tsx` par segment qui en a besoin.
- Images par `next/image` avec dimensions ou `fill` et `sizes`, polices par `next/font`.

### 6. Générer et nettoyer
- Après une suppression, retire aussi la route, le composant, la Server Action, la variable d'environnement, le style et les tests devenus inutiles.
- Montée de version : skill `upgrade-nextjs`. Lint et formatage : skill `lint-format-typescript`. Composants : skill `react`.

## Livrable
Le code de la tâche conforme à la version et au routeur installés, et dans le compte rendu : version de Next.js, routeur, stratégie de cache retenue pour les données touchées, contrôles d'accès des actions ajoutées.

## Vérifications
- Lint, `tsc --noEmit`, tests et `next build` passent sans avertissement nouveau.
- Chaque Server Action ou route handler ajouté valide son entrée et vérifie l'accès, prouvé par un test (refus non connecté, refus sur la ressource d'un autre).
- Aucun secret dans une variable `NEXT_PUBLIC_` ni dans un module importé par un composant client (recherche sur le diff).

## Limites
- Le déploiement (Vercel, conteneur, export statique) et ses réglages relèvent de `devops-engineer`. Le référencement : skill `seo-technique`.

## En cas de blocage
- API ou comportement différent de ce que tu attendais : lis la documentation et le guide de mise à jour de la version installée, applique-les, et consigne l'écart.
- Erreur d'hydratation : identifie la valeur qui diffère entre serveur et client et calcule-la d'un seul côté.
