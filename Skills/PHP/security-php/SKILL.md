---
name: security-php
description: Écrire et relire du code PHP sûr (Laravel ou Symfony) - autorisation sur chaque ressource, validation, injections SQL et de commandes, XSS, CSRF, fichiers envoyés, SSRF, redirections, mots de passe, secrets et dépendances vulnérables. À utiliser pour coder ou auditer une fonctionnalité PHP qui reçoit des données, touche aux droits, aux fichiers ou aux appels externes.
---

# Sécurité PHP

Le cadre d'audit (surface d'attaque, OWASP, rapport) est dans l'agent `security-auditor` et le skill `owasp-checklist`. Ce skill liste les failles propres à PHP, Laravel et Symfony et la bonne façon de les éviter.

## Quand l'utiliser
- Toute tâche qui ajoute ou modifie une route, une action sur une ressource, une requête construite, un envoi de fichier, un appel HTTP sortant, une redirection ou un traitement de mot de passe.
- Revue ou audit de code PHP.

## Ce que l'agent rate sans ce skill
- Il vérifie l'authentification mais pas l'appartenance : un utilisateur connecté lit ou modifie la ressource d'un autre en changeant l'identifiant (IDOR).
- Il passe un nom de colonne ou un sens de tri venu de la requête à `orderBy()` : les bindings ne protègent pas les identifiants.
- Il fait confiance au nom ou au type MIME d'un fichier envoyé, ou le stocke dans `public/`.
- Il appelle une URL fournie par l'utilisateur (aperçu de lien, webhook) sans filtrer les adresses internes.
- Il journalise des mots de passe, jetons ou données personnelles.

## Entrées
- Le diff ou la fonctionnalité, les routes et leurs middlewares, les Policies ou Voters, `config/` (ou `config/packages/`), `composer.lock`.

## Procédure
1. **Contrôle d'accès, pour chaque route touchée** :
   - qui peut l'appeler (middleware `auth`, `access_control`, `#[IsGranted]`) ;
   - sur quelles ressources : Policy Laravel (`authorize`, `can:`) ou Voter Symfony (`denyAccessUnlessGranted`) qui compare le propriétaire ou le tenant ;
   - les listes et recherches filtrées dans la requête par propriétaire ou tenant ;
   - un test par refus attendu (non connecté, autre utilisateur, rôle insuffisant).
2. **Entrées** :
   - Laravel : Form Request, puis `$request->validated()` ; `$fillable` explicite. Symfony : contraintes de validation sur le DTO (`#[MapRequestPayload]`) ou le formulaire, jamais d'hydratation directe de l'entité depuis la requête sans groupes de sérialisation.
   - Ne passe jamais une valeur reçue à `Rule::unique()->ignore()`, à un nom de colonne, de table, de relation ou de méthode sans liste blanche.
3. **Injections** :
   - SQL : Query Builder, Eloquent ou Doctrine avec paramètres ; `whereRaw`, `selectRaw`, `DB::select` et DQL toujours avec bindings ; colonnes et sens de tri validés par `in:` ou liste blanche.
   - Commandes : `Process` (Laravel ou Symfony) avec un tableau d'arguments, jamais une chaîne construite ; pas de `exec`, `shell_exec`, `system`, `passthru` avec une donnée reçue.
   - Code et objets : jamais `eval`, ni `unserialize` sur une donnée externe (utiliser `json_decode`) ; pas d'`include` d'un chemin construit.
4. **Sortie et navigateur** :
   - Blade `{{ }}`, Twig échappé par défaut ; `{!! !!}` et `|raw` seulement sur du contenu de confiance ou nettoyé par une librairie dédiée.
   - CSRF actif sur les formulaires ; toute exclusion (webhooks) compensée par une signature vérifiée.
   - Redirection vers une URL reçue : seulement vers un chemin relatif ou un domaine de la liste blanche (`redirect()->intended()` plutôt qu'une URL libre).
   - En-têtes : CORS limité aux origines connues ; cookies de session `secure`, `http_only`, `same_site` en production.
5. **Fichiers envoyés** : règles `file`, `mimes` ou `mimetypes` et `max` (Laravel), contrainte `File` (Symfony) ; nom généré (`store()`, `hashName()`), jamais `getClientOriginalName()` comme chemin ; stockage hors de `public/` et accès par une route autorisée ou une URL signée temporaire ; images retraitées si elles sont réaffichées.
6. **Appels sortants** : URL fournie par l'utilisateur seulement en `https`, hôte résolu et refusé s'il est privé, local ou de métadonnées (`127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16`, `::1`), sans suivre les redirections vers ces adresses ; délai d'attente court.
7. **Authentification et secrets** :
   - `Hash::make` ou `UserPasswordHasherInterface`, jamais `md5` ou `sha1` ; comparaison de jetons avec `hash_equals`.
   - Limitation de débit sur connexion, réinitialisation de mot de passe, codes à usage unique et routes coûteuses (`RateLimiter`, `throttle`, `symfony/rate-limiter`).
   - Jetons d'API avec capacités minimales (abilities Sanctum, scopes) et expiration.
   - `APP_DEBUG=false` et `APP_ENV=production` en production ; aucun secret dans le code, les tests ou la documentation ; nouvelles clés seulement dans `.env.example`, sans valeur.
   - Journaux sans mot de passe, jeton, numéro de carte ni donnée personnelle inutile.
8. **Dépendances** : `composer audit` (et `npm audit --omit=dev` si un front est présent) ; une vulnérabilité haute ou critique dans une dépendance utilisée est bloquante.

## Livrable
Pour une implémentation : les protections appliquées et leurs tests, citées dans le compte rendu. Pour une revue ou un audit : chaque constat avec fichier et ligne, scénario d'attaque concret, gravité et correction proposée.

## Vérifications
- Chaque route touchée a au moins un test de refus d'accès.
- `composer audit` lancé, résultat cité.
- Recherche lancée et citée sur le diff : `whereRaw|selectRaw|DB::raw|orderBy\(\$|exec\(|shell_exec|unserialize|\{!!|\|raw|getClientOriginalName`.

## Limites
- Ce skill ne remplace pas un test d'intrusion. Les choix à portée légale (données personnelles, conservation) restent des décisions humaines (règle 5 des principes communs).

## En cas de blocage
- Correction qui casse un contrat consommé hors du dépôt : applique la protection la plus forte compatible, signale le risque restant comme **Bloquant** pour `security-auditor` et `quality-gatekeeper`.
- Vulnérabilité de dépendance sans version corrigée : documente la mesure de contournement et le risque résiduel dans le rapport.
