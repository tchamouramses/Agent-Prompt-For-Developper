---
name: api-design
description: Concevoir la forme d'une API HTTP avant de l'écrire - ressources et URL, sémantique des méthodes et des statuts, filtres et tri, pagination par curseur ou par offset, catalogue d'erreurs au format RFC 9457 (problem+json), stratégie de versionnage, idempotence des créations et paiements, concurrence optimiste, opérations longues, choix REST ou GraphQL. À utiliser pour concevoir un nouvel ensemble d'endpoints, fixer les conventions d'API d'un projet ou revoir une API mal structurée ; le format des champs et la compatibilité relèvent du skill api-contracts.
---

# Conception d'API

`architect` fixe le format des erreurs d'API parmi les conventions transverses et consigne les choix en ADR (skill `adr`). Ce skill porte sur la forme de l'API : ressources, URL, méthodes, pagination, erreurs, versions, idempotence. Les formats de champs (dates, montants, nulls), le classement compatible ou cassant et les tests de contrat sont dans le skill `api-contracts`, à ne pas redéfinir ici.

## Quand l'utiliser
- `architect` : conventions d'API d'un nouveau projet, nouvelle brique exposée à un front, un mobile ou un partenaire.
- Agents d'implémentation back : nouvel ensemble d'endpoints, ou endpoint qui ne rentre dans aucune convention existante.
- `code-reviewer` : URL en verbe, `POST` utilisé pour tout, pagination absente.

## Ce que l'agent rate sans ce skill
- Il crée des URL en verbes (`/getOrders`, `/orders/create`) et un `POST` par action, au lieu de ressources et de méthodes.
- Il imbrique les ressources sur trois niveaux (`/users/1/orders/2/items/3`) alors que l'élément a son propre identifiant.
- Il renvoie une liste sans pagination « parce qu'il y a peu de données », ou une pagination par offset sur un flux qui bouge (doublons et trous entre pages).
- Il accepte `per_page=100000` ou un tri sur n'importe quelle colonne passée par le client.
- Il rend une création non idempotente : un double appel réseau du mobile crée deux commandes ou deux paiements.
- Il confond 401 et 403, ou renvoie 403 sur la ressource d'un autre utilisateur et révèle ainsi qu'elle existe.
- Il versionne chaque endpoint indépendamment, ou crée `/v2` pour un ajout de champ compatible.
- Il expose le modèle de base tel quel (colonnes internes, clés techniques) au lieu de ressources pensées pour le client.

## Entrées
- `docs/spec.md` (stories et règles métier), `docs/architecture.md` et ADR existants, les endpoints déjà en place : `php artisan route:list --path=api` (Laravel), `php bin/console debug:router` (Symfony), endpoint Actuator `mappings` ou spécification `springdoc` (Spring Boot), dossiers `app/api/**/route.ts` (Next.js).
- Les consommateurs prévus (front, mobile publié, partenaire) et leurs contraintes (réseau instable, hors ligne).

## Procédure
1. **Choisir le style** une fois par projet, en ADR : REST par défaut ; GraphQL seulement si plusieurs clients ont des besoins de lecture très différents et que l'équipe l'outille déjà ; RPC (`POST /orders/{id}/cancel`) pour une action métier qui n'est pas une mise à jour de champ.
2. **Modéliser les ressources** à partir des stories, pas des tables : noms au pluriel, en minuscules avec tirets (`/order-items`), identifiants opaques dans l'URL. Imbrication à un niveau au plus, pour une ressource qui n'existe que dans son parent (`/orders/{id}/items`) ; sinon ressource de premier niveau avec filtre (`/items?order_id=…`).
3. **Attribuer les méthodes** : `GET` sûr et sans effet ; `POST` crée (201, en-tête `Location`) ; `PUT` remplace en entier et est idempotent ; `PATCH` modifie partiellement ; `DELETE` idempotent (204, puis 404 ou 204 au second appel, choisi une fois). Statuts et forme des erreurs : table du skill `api-contracts`. Ressource d'un autre utilisateur : 404, pas 403, sauf si son existence est déjà connue du client.
4. **Listes** : pagination obligatoire, taille par défaut (20) et maximale (100) bornées côté serveur.
   - Curseur (`?cursor=…&limit=…`, curseur opaque encodant la clé de tri plus l'identifiant) pour les flux, les grosses tables et le défilement infini mobile.
   - Offset (`?page=…`) seulement pour un back-office qui affiche des numéros de page, sur une table de taille raisonnable.
   - Filtres et tris sur une liste blanche de champs (`?sort=-created_at`), jamais un nom de colonne inséré tel quel dans la requête.
5. **Catalogue d'erreurs RFC 9457** (`application/problem+json`) si le projet n'a pas déjà un format :
   - `type` : URI stable par catégorie d'erreur (`https://<domaine>/errors/insufficient-stock` ou `about:blank`), c'est elle que le client teste, jamais `detail` ;
   - `title` stable, `status`, `detail` lisible sans donnée interne, `instance` facultative ;
   - extensions : `errors` (liste `{field, message}` pour la validation), identifiant de corrélation ;
   - mise en œuvre : `ProblemDetail` et `spring.mvc.problemdetails.enabled=true` (Spring Boot 3), sortie native d'API Platform (Symfony), rendu dans le gestionnaire d'exceptions (`bootstrap/app.php`, `withExceptions`, Laravel 11 et plus). Le passage des exceptions métier aux statuts est dans le skill `error-handling`.
6. **Versionnage** : une version majeure pour toute l'API, dans l'URL (`/api/v1`) par défaut parce qu'elle est visible dans les journaux et les caches ; en-tête ou type de média seulement si c'est déjà la convention. Les changements compatibles n'incrémentent rien ; une nouvelle version n'existe que pour un changement cassant impossible à faire en transition (skill `api-contracts`, point 4).
7. **Idempotence** des `POST` à effet coûteux ou non rejouable (commande, paiement, envoi) : en-tête `Idempotency-Key` fourni par le client (convention répandue, brouillon IETF), clé stockée avec l'empreinte de la requête et la réponse pendant une durée fixée (24 h par défaut) ; même clé et même corps → même réponse ; même clé et corps différent → 422 ; requête en cours → 409. Contrainte d'unicité en base sur la clé, pas seulement un contrôle applicatif.
8. **Concurrence** : pour les ressources modifiées par plusieurs personnes, `ETag` en lecture et `If-Match` en écriture, 412 si la version a changé ; sinon le dernier écrit gagne en silence.
9. **Opérations longues** (export, import) : 202 avec `Location` vers une ressource de suivi (`/exports/{id}` : statut, progression, lien du résultat), jamais une requête qui attend une minute.
10. **Consigner** les conventions dans `docs/architecture.md` et l'ADR, puis décrire chaque endpoint dans la source de vérité du contrat (skill `api-contracts`).

## Livrable
Dans `docs/architecture.md`, section « Conventions d'API », puis par endpoint :
```markdown
| Méthode | URL | Effet | Succès | Erreurs (type) | Idempotent | Story |
|---------|-----|-------|--------|----------------|------------|-------|
| POST | /api/v1/orders | crée une commande | 201 + Location | validation (422), insufficient-stock (409) | oui, Idempotency-Key | US-04 |
| GET | /api/v1/orders?cursor=&limit= | liste paginée des commandes de l'utilisateur | 200 | — | oui | US-05 |
```

## Vérifications
- Aucune URL ne contient de verbe hors action métier explicite ; aucune imbrication au-delà d'un niveau.
- Chaque liste a une taille maximale testée (`limit=1000` renvoie au plus le maximum) et un tri sur liste blanche.
- Chaque `POST` coûteux a un test de double envoi avec la même clé : une seule création.
- Un test vérifie le corps `problem+json` d'au moins une erreur métier et d'une erreur de validation.

## Limites
- GraphQL : ce skill ne couvre pas le schéma, la complexité des requêtes ni le chargement par lots.
- Authentification et autorisation : skill `owasp-checklist` et agent `security-auditor`.
- Documentation publique de l'API : skill `api-docs`.

## En cas de blocage
- API existante qui viole ces conventions : applique la convention en place aux nouveaux endpoints, consigne l'écart, et ajoute la mise en conformité au plan avec sa transition.
- Besoin client qui force une ressource bizarre (écran agrégé) : crée une ressource de lecture dédiée (`/dashboard-summary`) plutôt que de déformer les ressources métier.
