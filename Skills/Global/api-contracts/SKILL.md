---
name: api-contracts
description: Tenir et tester le contrat d'échange entre deux parties (back et front, back et mobile, services, webhooks, API tierces) - source de vérité unique (OpenAPI, types partagés, schémas), formats de dates, montants, nulls, énumérations, pagination et erreurs, distinction changement compatible ou cassant, tests de contrat stricts et détection automatique des ruptures. À utiliser pour créer ou modifier un endpoint, un payload ou un webhook, pour consommer une API, et pour vérifier qu'un front et un back sont alignés.
---

# Contrats d'API

Ce skill porte sur le format échangé et sa compatibilité dans le temps. La forme des ressources et des URL relève du skill `api-design`.

## Quand l'utiliser
- Agents d'implémentation back : création ou modification d'un endpoint, d'une ressource sérialisée, d'un webhook émis.
- Agents d'implémentation front et mobile : consommation d'un endpoint ou d'une API tierce.
- `test-engineer` : tests de contrat. `e2e-validator` : vérification d'intégration front et back.
- `code-reviewer` : diff qui change une réponse, une requête ou un payload.

## Ce que l'agent rate sans ce skill
- Il renomme un champ, change son type ou le rend nullable sans voir que c'est un changement cassant pour le mobile déjà publié.
- Ses tests vérifient le statut HTTP et un champ, pas la forme complète : un champ interne qui fuit ou un champ disparu passe inaperçu.
- Il recopie à la main les types du back dans le front, et les deux divergent.
- Il mélange les formats dans une même API : dates avec et sans fuseau, montants en flottant, identifiants tantôt nombre tantôt chaîne, champ absent ou `null` selon les cas.
- Chaque endpoint renvoie les erreurs dans une forme différente, et le front ne sait pas afficher une erreur de validation.
- Il ajoute une valeur d'énumération sans vérifier que les clients tolèrent une valeur inconnue.
- Il laisse la spécification OpenAPI décrire l'ancien comportement.

## Entrées
- La source de vérité existante du contrat :
  - spécification OpenAPI (`openapi.yaml`, annotations `springdoc`, `nelmio` ou API Platform, génération Scribe) ;
  - types partagés ou client généré ;
  - classes de sérialisation (API Resources, groupes de sérialisation, DTO) ;
  - schémas de validation (`zod` ou équivalent).
- La liste des consommateurs connus : front, application mobile publiée, services, partenaires.

## Procédure
1. **Identifier la source de vérité** et s'y tenir. S'il n'y en a pas, la classe de sérialisation du back fait foi. Pour un nouvel ensemble d'endpoints consommés par un front ou un mobile, produis une spécification OpenAPI si l'écosystème la génère sans effort, sinon des types partagés (règle 4 des principes communs pour tout outil ajouté).
2. **Fixer les conventions** une fois pour l'API, en reprenant celles qui existent :

| Sujet | Convention par défaut si le projet n'en a pas |
|-------|-----------------------------------------------|
| Dates | ISO 8601 avec fuseau (`2026-10-12T08:30:00Z`) ; date seule en `YYYY-MM-DD` |
| Montants | entier en plus petite unité (`1250` pour 12,50) avec code devise, ou chaîne décimale ; jamais de flottant |
| Identifiants | un seul type par API ; chaîne si identifiants non séquentiels (UUID, ULID) |
| Absence de valeur | champ toujours présent, `null` si vide ; documenté nullable |
| Énumérations | chaînes stables en minuscules ; les clients tolèrent une valeur inconnue |
| Listes paginées | même enveloppe partout (`data` plus `meta` ou `links`), taille de page bornée côté serveur |
| Erreurs | format du framework s'il est déjà utilisé ; sinon `application/problem+json` (RFC 9457) ; validation : liste des erreurs par champ |
| Codes HTTP | 200, 201 avec la ressource, 204 sans corps, 401 non authentifié, 403 ou 404 refusé, 409 conflit, 422 validation, 429 débit ; jamais 200 avec une erreur dans le corps |

3. **Classer chaque changement** avant de l'écrire :

| Compatible | Cassant |
|------------|---------|
| ajouter un endpoint, un champ de réponse, un paramètre facultatif | supprimer ou renommer un champ, un endpoint, un paramètre |
| ajouter une valeur d'énumération que les clients tolèrent | changer le type, le format ou l'unité d'un champ |
| assouplir une validation | rendre obligatoire un paramètre, durcir une validation |
| | rendre nullable un champ qui ne l'était pas, changer un code HTTP ou la forme des erreurs |

4. **Pour un changement cassant**, garde l'ancien contrat tant qu'un consommateur l'utilise :
   - nouveau champ à côté de l'ancien, marqué déprécié ;
   - ou nouvelle version de l'endpoint.
   Ajoute au plan la tâche de suppression, avec sa condition (version minimale du mobile, date). Si un consommateur externe est cassé quoi qu'il arrive, c'est une décision humaine.
5. **Mettre à jour la source de vérité dans le même changement** que le code, puis régénérer les types ou le client si le projet en génère.
6. **Écrire des tests de contrat stricts** côté producteur, un par endpoint touché, sur le succès et sur chaque forme d'erreur :
   - Laravel : `assertJson(fn (AssertableJson $json) => ...)` avec `whereType` et sans `etc()`, pour qu'un champ en trop échoue ;
   - Symfony avec API Platform : `assertMatchesResourceItemJsonSchema` ;
   - Spring : `MockMvc` avec `jsonPath(...)` sur chaque champ et son type ;
   - si une spécification OpenAPI existe : validation de la réponse contre le schéma avec la librairie déjà présente.
7. **Côté consommateur**, valide la réponse à la frontière (schéma `zod` ou équivalent s'il est en place) et tolère les champs et valeurs d'énumération inconnus. Pour une API tierce ou un webhook reçu, garde un exemple réel de payload, tiré de la documentation du fournisseur, comme donnée de test, et vérifie la signature.
8. **Détecter les ruptures automatiquement** si une spécification OpenAPI est versionnée : `oasdiff breaking <spec-de-main> <spec-de-la-branche>` dans la CI, ou un outil équivalent déjà présent. Toute rupture signalée doit correspondre à l'étape 4.

## Livrable
- Le contrat à jour (spécification, types ou schéma) dans le même commit que le code.
- Les tests de contrat.
- Dans le compte rendu : chaque changement de contrat classé compatible ou cassant, et pour un cassant, la stratégie de transition et la tâche de suppression.

## Vérifications
- Chaque endpoint touché a un test qui échoue si un champ est ajouté, retiré ou change de type.
- La source de vérité et le code décrivent le même comportement : spécification régénérée ou relue, diff cité.
- Aucun changement cassant sans transition ou décision humaine tracée.

## Limites
- Les noms de ressources, la structure des URL et le choix REST ou GraphQL relèvent du skill `api-design`.
- Les tests contractuels pilotés par le consommateur (Pact) ne s'ajoutent que si le projet les utilise déjà, ou si plusieurs équipes publient indépendamment.

## En cas de blocage
- Consommateurs inconnus (API publique sans liste de clients) : traite tout changement cassant comme interdit sans nouvelle version.
- Contrat existant incohérent (trois formats d'erreur) : n'unifie pas tout dans la tâche ; applique la convention majoritaire aux endpoints touchés et ajoute l'unification au plan.
- Désaccord entre la spécification et le code en production : le code fait foi pour les clients existants ; corrige la spécification et signale l'écart.
