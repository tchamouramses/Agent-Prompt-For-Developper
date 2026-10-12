---
name: security-typescript
description: Sécuriser du code TypeScript côté navigateur, serveur Node et mobile - XSS et HTML injecté, secrets embarqués dans le code client, stockage des jetons, validation et autorisation côté serveur (Server Actions, route handlers, API Node), redirections, SSRF, pollution de prototype, en-têtes et audit npm. À utiliser pour écrire, relire ou auditer du code Angular, Next.js, React, Expo ou Node exposé à des entrées externes.
---

# Sécurité TypeScript

La liste générale des risques est dans le skill `owasp-checklist`. Ce skill dit où ils se cachent dans un projet JavaScript ou TypeScript, et comment les fermer.

## Quand l'utiliser
- Écrire ou modifier un affichage de contenu externe, un formulaire, une Server Action, un route handler, une API Node, un stockage de jeton ou un appel sortant.
- Revue de sécurité ou audit d'un projet TypeScript (`security-auditor`, `code-reviewer`).

## Ce que l'agent rate sans ce skill
- Il croit qu'une variable d'environnement « cachée » dans le front est secrète : tout ce qui est embarqué dans le code client est public.
- Il insère du HTML reçu avec `dangerouslySetInnerHTML`, `innerHTML` ou `bypassSecurityTrustHtml` sans l'assainir.
- Il ne valide et n'autorise que côté client ; l'API ou la Server Action accepte tout.
- Il stocke un jeton d'accès dans `localStorage` sur le web, ou dans AsyncStorage sur mobile.
- Il redirige vers une URL reçue en paramètre (redirection ouverte).
- Il fusionne un objet JSON reçu dans un objet de configuration (pollution de prototype).

## Entrées
- Code touché (composants, actions, routes, services), configuration des en-têtes, variables d'environnement, `package.json` et fichier de verrouillage.

## Procédure
1. **Ce qui part au client est public** : variables `NEXT_PUBLIC_`, `EXPO_PUBLIC_`, `VITE_`, fichiers `environment.ts` d'Angular, code et assets de l'application mobile. Aucun secret, clé privée ni jeton de service ; les appels qui en demandent passent par le serveur.
2. **Affichage de contenu externe** :
   - laisser l'échappement du framework (JSX, interpolation Angular) ;
   - HTML riche nécessaire : assaini par une librairie dédiée (DOMPurify) côté serveur ou juste avant l'insertion, avec une liste blanche de balises ;
   - URL affichées en lien : protocole `https:` ou `http:` vérifié (pas de `javascript:`) ; `rel="noopener noreferrer"` sur les liens externes ouverts dans un nouvel onglet.
3. **Serveur (Server Actions, route handlers, API Node, NestJS, Express)** :
   - chaque entrée validée par un schéma (corps, paramètres, en-têtes utilisés) ;
   - authentification et autorisation sur la ressource précise dans chaque point d'entrée ou dans la couche d'accès aux données, jamais seulement dans le middleware, le proxy ou l'interface ;
   - réponses limitées aux champs nécessaires (pas l'objet de base entier) ;
   - erreurs génériques vers le client, détail dans les journaux.
4. **Jetons et sessions** :
   - web : cookie `HttpOnly`, `Secure`, `SameSite=Lax` ou `Strict` plutôt que `localStorage` ; protection contre la falsification de requête (CSRF) pour les routes à cookie qui modifient des données (vérification d'origine ou jeton) ;
   - mobile : `expo-secure-store` (ou le trousseau natif), jamais AsyncStorage ;
   - expiration courte, révocation possible, rafraîchissement côté serveur.
5. **Redirections et appels sortants** : redirection vers un chemin relatif ou une liste blanche de domaines ; `fetch` serveur vers une URL fournie par l'utilisateur seulement en `https`, hôte résolu et refusé s'il est privé, local ou de métadonnées, délai d'attente court.
6. **Code dynamique et objets** : jamais `eval`, `new Function`, `setTimeout` avec une chaîne ; fusion d'objets reçus seulement après validation par schéma (qui retire les clés inconnues) ; refus des clés `__proto__`, `constructor`, `prototype` si un parcours générique est inévitable.
7. **Node** : chemins de fichiers construits depuis une entrée normalisés et vérifiés sous le dossier prévu ; `child_process.execFile` ou `spawn` avec un tableau d'arguments, jamais `exec` d'une chaîne construite ; limites de taille des corps de requête.
8. **En-têtes** : Content-Security-Policy adaptée (nonces si scripts en ligne), `X-Content-Type-Options: nosniff`, `Referrer-Policy`, `frame-ancestors` ; CORS limité aux origines connues, jamais `*` avec des cookies.
9. **Dépendances** : `npm audit --omit=dev` (ou `pnpm audit --prod`, `yarn npm audit`) ; fichier de verrouillage versionné et installation par `npm ci` ; une vulnérabilité haute ou critique dans une dépendance utilisée est bloquante ; nouvelle dépendance choisie selon la règle 4 des principes communs (paquet maintenu, nom vérifié contre les imitations).

## Livrable
Pour une implémentation : les protections appliquées et leurs tests, citées dans le compte rendu. Pour une revue ou un audit : chaque constat avec fichier et ligne, scénario d'attaque concret, gravité et correction proposée.

## Vérifications
- Chaque point d'entrée serveur touché a un test de refus d'accès et un test d'entrée invalide.
- Audit des dépendances lancé, résultat cité.
- Recherche lancée et citée sur le diff : `dangerouslySetInnerHTML|innerHTML|bypassSecurityTrust|eval\(|new Function|localStorage\.(set|get)Item\(.*(token|jeton)|NEXT_PUBLIC_.*(SECRET|KEY|TOKEN)|EXPO_PUBLIC_.*(SECRET|KEY|TOKEN)|redirect\(.*(searchParams|query)|exec\(`.

## Limites
- Ce skill ne remplace pas un test d'intrusion. Les choix à portée légale (données personnelles, conservation, cookies de suivi) restent des décisions humaines (règle 5 des principes communs).

## En cas de blocage
- Jeton qui doit être lu par le JavaScript (API tierce sans cookie) : durée de vie courte, portée minimale, stockage en mémoire plutôt que persistant, et risque consigné.
- Vulnérabilité de dépendance sans version corrigée : documente le contournement et le risque résiduel.
