---
name: react
description: Écrire des composants React justes et sobres (web et React Native) - effets utilisés seulement pour se synchroniser avec l'extérieur, état dérivé calculé au rendu, clés stables, état placé au bon niveau, nouveautés de React 19 (actions, use, ref en prop) et React Compiler selon la version. À utiliser pour écrire, relire ou déboguer des composants React, dans Next.js, Expo ou une application Vite.
---

# React

Ce skill porte ce qui est commun à React sur le web et sur mobile. Ce qui est propre au framework est dans `nextjs` ou `expo`.

## Quand l'utiliser
- Écrire, refactorer, relire ou déboguer un composant ou un hook React.

## Ce que l'agent rate sans ce skill
- Il copie une prop dans un état puis la synchronise avec un `useEffect`, ou calcule une valeur dérivée dans un effet : rendus en double et états incohérents.
- Il charge des données dans un `useEffect` sans gérer l'annulation ni les réponses dans le désordre.
- Il utilise l'index comme `key` d'une liste qui change d'ordre ou d'éléments.
- Il ajoute `useMemo`, `useCallback` et `memo` partout, sans mesure, ou alors que le React Compiler est actif.
- Il désactive la règle `react-hooks/exhaustive-deps` au lieu de corriger la dépendance.
- Il utilise une API de React 19 (`use`, `useActionState`, ref en prop) dans un projet en React 18, ou `forwardRef` inutilement en 19.

## Entrées
- `package.json` (`react` et sa version, `react-dom` ou `react-native`, `babel-plugin-react-compiler`, librairie de requêtes, de formulaires et d'état), composants voisins, configuration ESLint.

## Procédure
1. **Version** : lis la version de `react`. React 19 apporte les actions (`useActionState`, `useFormStatus`, `useOptimistic`), `use()` pour lire une promesse ou un contexte, `ref` comme prop ordinaire (plus besoin de `forwardRef`), les métadonnées de document dans le composant. Le React Compiler, s'il est configuré, mémorise automatiquement : n'ajoute pas de `useMemo` ni de `useCallback` manuels.
2. **Effets** : un `useEffect` sert seulement à se synchroniser avec un système extérieur (abonnement, API du navigateur ou de l'appareil, librairie non React). Pas d'effet pour :
   - calculer une valeur à partir des props ou de l'état : calcule-la pendant le rendu ;
   - réagir à un événement utilisateur : mets la logique dans le gestionnaire d'événement ;
   - réinitialiser un état quand une prop change : donne une `key` au composant.
   Tout effet qui s'abonne a sa fonction de nettoyage ; le double appel en mode strict de développement doit rester sans effet visible.
3. **Données serveur** : avec la librairie du projet (TanStack Query, SWR, chargement serveur du framework), jamais un `fetch` dans un effet maison. À défaut, l'effet ignore la réponse d'une requête périmée (drapeau ou `AbortController`).
4. **État** :
   - au niveau le plus bas qui en a besoin ; remonté au parent commun seulement si deux composants le partagent ;
   - une seule source de vérité : pas de copie d'une prop dans un état ;
   - état global (contexte, librairie d'état) seulement pour ce qui est vraiment global (session, thème) ; un contexte qui change souvent est découpé pour ne pas rendre tout l'arbre ;
   - mises à jour immuables ; forme fonctionnelle (`setX(x => …)`) quand la nouvelle valeur dépend de l'ancienne.
5. **Listes** : `key` stable et unique tirée de la donnée (identifiant), jamais l'index si la liste est réordonnée, filtrée ou modifiée.
6. **Hooks** : appelés au premier niveau du composant ou d'un hook personnalisé, jamais dans une condition ; logique réutilisée par deux composants extraite dans un hook `useXxx`. La règle `exhaustive-deps` est respectée, pas désactivée.
7. **Composants** : petits et nommés ; props typées ; composant de présentation séparé du chargement de données quand il est réutilisé ; pas de composant défini à l'intérieur d'un autre composant (il est recréé à chaque rendu et perd son état).
8. **Performance** : sans React Compiler, mémoïse seulement après avoir constaté un rendu coûteux (React DevTools Profiler) ; listes longues virtualisées.
9. **Accessibilité** (web) : éléments natifs (`button`, `a`, `label`) plutôt que des `div` cliquables ; chaque champ a un label ; focus géré à l'ouverture et à la fermeture des fenêtres.
10. **Internationalisation** (projet multilingue, règles communes dans le skill `i18n`) : `react-i18next` par défaut (`useTranslation()` dans le composant, `<Trans>` pour un texte qui contient un lien ou une mise en forme, jamais de HTML injecté) ; espaces de noms par fonctionnalité chargés à la demande ; pluriels par les suffixes `_one`, `_other` (et `_zero`, `_few`, `_many` selon la langue) ou le format ICU si le projet l'a activé ; ressources typées (déclaration `CustomTypeOptions`) pour qu'une clé inconnue casse la compilation. Formats par `Intl` avec `i18n.language`. Lint : `i18next/no-literal-string` (`eslint-plugin-i18next`) sur les fichiers modifiés ; extraction et clés orphelines avec l'outil du projet (`i18next-parser` ou équivalent). Next.js et Expo ont leurs particularités dans leurs skills.

## Livrable
Les composants et hooks de la tâche, et dans le compte rendu la version de React relevée et les choix d'état ou d'effet non évidents.

## Vérifications
- Le lint React (`eslint-plugin-react-hooks`) passe sans désactivation ajoutée.
- Aucun avertissement React nouveau dans la console des tests (clés, `act`, mises à jour sur un composant démonté).
- Chaque `useEffect` ajouté se synchronise avec un système extérieur et a son nettoyage si nécessaire.

## Limites
- Rendu serveur, Server Components et Server Actions : skill `nextjs`. Navigation et API mobiles : skill `expo`. Tests : skill `testing-typescript`.

## En cas de blocage
- Version de React trop ancienne pour l'API voulue : utilise l'équivalent de la version installée et consigne-le.
- Boucle de rendus ou effet qui se relance sans fin : cherche la dépendance recréée à chaque rendu (objet, tableau, fonction) et stabilise-la ou déplace le calcul.
