---
name: caching
description: Mettre en cache sans servir de données fausses ni fuiter celles d'un autre utilisateur - choisir la couche (mémoïsation, cache applicatif, cache HTTP), construire des clés complètes, invalider sur chaque écriture, fixer un TTL de sécurité, éviter l'avalanche à l'expiration, et poser les en-têtes Cache-Control, ETag et Vary justes. À utiliser après mesure, quand supprimer le travail inutile ne suffit pas, et pour toute revue d'un cache existant (Laravel, Symfony, Spring Boot, Next.js, Angular, Expo).
---

# Cache

Pour `performance-optimizer`, le cache passe après la suppression du travail inutile, les index et la pagination, et toujours avec sa stratégie d'invalidation. Une nouvelle brique d'infrastructure de production (Redis, CDN) est une décision humaine (règle 4 des principes communs). Ce skill donne la méthode.

## Quand l'utiliser
- Le skill `profiling` montre un calcul ou une lecture coûteux, répété avec les mêmes entrées, et les optimisations plus simples sont faites.
- Réponses HTTP publiques ou rarement modifiées (assets, pages de contenu, référentiels).
- Revue d'un cache existant soupçonné de servir des données périmées.

## Ce que l'agent rate sans ce skill
- Il oublie une entrée dans la clé (utilisateur, locataire, langue, rôle, paramètres de pagination) : un utilisateur reçoit les données d'un autre.
- Il invalide dans un seul chemin d'écriture : les mises à jour en masse (`Model::query()->update()`, requêtes DQL ou JPQL `UPDATE`), les commandes et les jobs ne déclenchent pas les événements du modèle.
- Il invalide avant la validation de la transaction : un lecteur concurrent recharge l'ancienne valeur dans le cache.
- Il met en cache un échec ou un `null` sans le vouloir, et l'erreur dure tout le TTL.
- Il sérialise des objets riches (modèle Eloquent, entité Doctrine, proxy JPA) au lieu de données simples ; le cache casse au déploiement suivant.
- Il pose `Cache-Control: public` sur une réponse authentifiée, ou oublie `Vary` : un proxy la sert à tout le monde.
- Il annote avec `@Cacheable` une méthode appelée depuis la même classe : l'appel ne passe pas par le proxy et le cache n'agit jamais.
- Il suppose les valeurs par défaut de cache de Next.js d'une version précédente.

## Entrées
- La mesure initiale (skill `profiling`), la donnée à mettre en cache, tous ses chemins d'écriture, sa tolérance à la péremption (déduite de la spec, sinon hypothèse consignée), le store de cache déjà configuré (`CACHE_STORE`, `config/packages/cache.yaml`, `spring.cache.type`).

## Procédure
1. **Choisir la couche la plus proche du besoin** :
   - mémoïsation dans la requête ou le composant (variable, `once()` en Laravel 11+, `computed` ou `useMemo`) quand la répétition est locale ;
   - cache applicatif partagé quand plusieurs requêtes lisent la même donnée ;
   - cache HTTP quand la réponse entière est réutilisable par le navigateur ou un proxy.
2. **Construire la clé** : préfixe de domaine et version de format, puis chaque entrée qui change le résultat : `v1:catalog:tenant:{tenantId}:locale:{fr}:page:{2}`. Donnée par utilisateur : l'identifiant de l'utilisateur est dans la clé, ou elle n'est pas en cache partagé. Une entrée libre de l'utilisateur est hachée, jamais concaténée brute.
3. **Lister les chemins d'écriture** (`rg` sur la table, le modèle, l'entité, le dépôt) et invalider dans chacun, après validation de la transaction : `DB::afterCommit()` ou `$afterCommit` sur les observateurs (Laravel), `postFlush` (Doctrine), `@TransactionalEventListener(phase = AFTER_COMMIT)` ou `@CacheEvict` hors transaction (Spring).
4. **TTL de sécurité** même avec invalidation explicite, borné par la tolérance à la péremption. Pas de cache sans expiration.
5. **Implémenter avec l'API du framework** :
   - Laravel : `Cache::remember($key, $ttl, fn () => ...)`, `Cache::forget($key)` ; tags seulement si le store les gère (Redis, Memcached ; pas `file` ni `database`) ; `Cache::lock()` contre l'avalanche ;
   - Symfony : `$cache->get($key, function (ItemInterface $item) { $item->expiresAfter(3600); return ...; })` (protection contre l'avalanche intégrée) ; tags avec un pool `TagAwareCacheInterface` ;
   - Spring Boot : `@EnableCaching`, `@Cacheable(cacheNames = "...", key = "...")`, `@CacheEvict`, TTL configuré par le fournisseur (Caffeine, Redis) car l'abstraction n'en a pas ;
   - Next.js : relève la version installée et lis sa documentation de cache (skill `version-compatibility`) avant d'utiliser `fetch` avec `next.revalidate`, `revalidateTag`, `revalidatePath` ou les directives de cache ;
   - Angular et Expo : cache des requêtes par la librairie déjà présente (TanStack Query, intercepteur HTTP) ; aucune donnée sensible persistée sur l'appareil sans stockage sécurisé.
6. **Ne mettre en cache que des données simples** (tableaux, DTO sérialisables), jamais un échec : l'exception remonte et rien n'est stocké.
7. **Cache HTTP** :

| Réponse | En-têtes |
|---------|----------|
| Asset avec empreinte dans le nom | `Cache-Control: public, max-age=31536000, immutable` |
| Page ou API publique modifiable | `Cache-Control: public, max-age=60` + `ETag` ou `Last-Modified`, réponse `304` sur `If-None-Match` |
| Réponse authentifiée | `Cache-Control: private, no-cache` (ou `no-store` si sensible) |
| Contenu qui varie selon un en-tête | `Vary: Accept-Language` (ou l'en-tête concerné) |

8. **Mesurer à nouveau** (skill `profiling`) : gain cache froid et cache chaud, taux de succès si le store l'expose.

## Livrable
```markdown
**Cache** : <donnée> — couche <mémo / applicatif / HTTP> — store <nom>
**Clé** : `<gabarit>` — entrées couvertes : <liste>
**Invalidation** : <chemin d'écriture → mécanisme> (tous listés) ; TTL <durée> justifié par <tolérance>
**Mesure** : avant <x>, après froid <y>, après chaud <z>
```

## Vérifications
- Tests : la deuxième lecture ne recalcule pas ; après chaque chemin d'écriture, la lecture renvoie la nouvelle valeur ; deux utilisateurs (ou locataires) ne partagent pas une entrée ; un échec n'est pas mis en cache.
- Les tests tournent sur un store isolé (`array` en Laravel, pool vidé entre tests) pour qu'un cache ne masque pas un bug.
- En-têtes HTTP vérifiés sur la réponse réelle (`curl -sI <url>`), pas seulement dans le code.

## Limites
- Introduire Redis, Memcached ou un CDN en production, ou changer la configuration d'un cache partagé : décision humaine préparée avec coût et alternative (règle 5).
- Un cache ne corrige pas une requête lente : il la cache jusqu'à l'expiration suivante.

## En cas de blocage
- Un chemin d'écriture échappe à toute invalidation fiable (base modifiée par un autre système) : TTL court assumé et consigné, ou pas de cache.
- Tolérance à la péremption inconnue et donnée visible par l'utilisateur : TTL court, hypothèse signalée à `product-analyst`.
