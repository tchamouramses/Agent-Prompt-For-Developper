---
name: db-query-optimization
description: Rendre des requêtes SQL et ORM rapides avec preuves - compter les requêtes par scénario, détecter et supprimer les N+1 (chargement anticipé, agrégats), lire un plan EXPLAIN / EXPLAIN ANALYZE, choisir l'index qui sert réellement la requête, réécrire les filtres qui empêchent l'index, paginer sans OFFSET profond, traiter les gros volumes par lots, puis verrouiller le gain par un test du nombre de requêtes. À utiliser pour une page, une API ou un traitement lent côté base, pour vérifier les requêtes d'une nouvelle fonctionnalité, et en revue de requêtes.
---

# Optimisation des requêtes

`performance-optimizer` mesure avant et après et préfère supprimer le travail inutile puis corriger index et requêtes ; `data-modeler` vérifie N+1, index et pagination. Ce skill donne la méthode côté base. La mesure globale d'une page relève du skill `profiling`, le cache du skill `caching`.

## Quand l'utiliser
- `performance-optimizer` : goulot identifié dans la base.
- `data-modeler` : vérification des requêtes d'une zone (procédure, point 7).
- `code-reviewer` : boucle qui touche une relation, requête construite à la main, liste sans pagination.

## Ce que l'agent rate sans ce skill
- Il ajoute un index « au feeling » sans regarder le plan, et l'index n'est pas utilisé (mauvais ordre des colonnes, fonction sur la colonne).
- Il lit un `EXPLAIN` sur une base de test de dix lignes : le moteur choisit un parcours complet qui est normal à cette taille, et l'agent en tire une conclusion fausse.
- Il lance `EXPLAIN ANALYZE` sur un `UPDATE` ou un `DELETE` sans transaction annulée : la requête est réellement exécutée.
- Il corrige un N+1 sur la page testée et laisse ceux du sérialiseur (relation chargée dans la ressource API ou le template).
- Il remplace un N+1 par un chargement anticipé de tout le graphe, et charge dix mille lignes pour en afficher vingt.
- Il écrit `WHERE DATE(created_at) = ?`, `LIKE '%mot%'` ou compare une colonne texte à un entier, ce qui empêche l'index.
- Il ne verrouille pas le gain : le N+1 revient au prochain changement de template.

## Entrées
- Le scénario lent (route, commande, job), le moteur et sa version, le volume réel estimé des tables, les requêtes réellement exécutées :
  - Laravel : Debugbar ou Telescope s'ils sont présents, sinon `DB::listen` ou `DB::enableQueryLog()` en test ;
  - Symfony : panneau Doctrine du profiler (`/_profiler`) ;
  - Spring Boot : `spring.jpa.properties.hibernate.generate_statistics=true` et journal `org.hibernate.SQL` en profil de développement ;
  - Prisma (Next.js) : `new PrismaClient({ log: ['query'] })` ;
  - base : `pg_stat_statements` (PostgreSQL), journal des requêtes lentes (MySQL), si disponibles en local.

## Procédure
1. **Compter les requêtes du scénario** et noter leur durée totale : c'est la mesure de départ. Plus de requêtes que d'entités distinctes affichées signale un N+1.
2. **Supprimer les N+1** au niveau où la relation est lue (contrôleur, sérialiseur, template, composant serveur) :
   - Laravel : `with()`, `load()`, `withCount()` ; en développement et test, `Model::preventLazyLoading(! app()->isProduction())` fait échouer tout chargement paresseux ;
   - Doctrine : `JOIN` plus `addSelect` dans le QueryBuilder, ou `fetch: 'EAGER'` seulement si la relation est toujours lue ;
   - JPA : `JOIN FETCH` ou `@EntityGraph` ; `@BatchSize` ou `hibernate.default_batch_fetch_size` pour les collections ; jamais deux `JOIN FETCH` de collections dans la même requête (produit cartésien) ;
   - Prisma : `include` ou `select` imbriqué.
   Pour un total ou un compteur, un agrégat en base (`COUNT`, `SUM`, `withSum`) plutôt que charger les lignes.
3. **Ne charger que l'utile** : colonnes nécessaires (`select`), pagination (skill `api-design`, point 4), traitement par lots pour les tâches de fond (`chunkById`, `lazyById`, `toIterable()` Doctrine avec `clear()` régulier, `Stream` JPA ou pagination par clé).
4. **Lire le plan** de chaque requête restante qui pèse, sur un volume réaliste (factories ou seeds de quelques centaines de milliers de lignes en local) :
   - PostgreSQL : `EXPLAIN (ANALYZE, BUFFERS) <requête>` ; repère `Seq Scan` sur une grosse table, écart fort entre lignes estimées et réelles, `Sort` ou `Hash` sur disque ;
   - MySQL 8 : `EXPLAIN ANALYZE <requête>` (8.0.18 et plus) ou `EXPLAIN FORMAT=TREE` ; repère `type: ALL`, `Using filesort`, `Using temporary` ;
   - Laravel : `->explain()` sur le builder pour un premier aperçu.
   Requête d'écriture : `BEGIN; EXPLAIN ANALYZE …; ROLLBACK;`.
5. **Choisir l'index qui sert la requête** : égalités d'abord, puis intervalle ou tri, colonnes du `SELECT` en index couvrant si la requête est très fréquente (`INCLUDE` en PostgreSQL). Vérifie qu'un index existant ne la couvre pas déjà (préfixe d'un composite). Le créer suit le skill `migrations` (création sans verrou sur grosse table).
6. **Rendre la requête indexable** :
   - `created_at >= ? AND created_at < ?` au lieu de `DATE(created_at) = ?` ;
   - recherche plein texte (index `GIN` avec `tsvector` ou trigrammes en PostgreSQL, `FULLTEXT` en MySQL) au lieu de `LIKE '%…%'` ;
   - mêmes types des deux côtés de la comparaison ;
   - `OR` sur des colonnes différentes réécrit en `UNION ALL` si le plan le montre utile ;
   - `WHERE (created_at, id) < (?, ?)` (pagination par clé) au lieu d'un `OFFSET` profond.
7. **Re-mesurer** le même scénario : nombre de requêtes, durée, plan après. Gain non significatif : annule le changement et l'index.
8. **Verrouiller** par un test du nombre de requêtes du scénario, qui échoue si un N+1 revient : compteur `DB::getQueryLog()` (Laravel), `Statistics#getPrepareStatementCount()` d'Hibernate (Spring Boot), compteur branché sur `prisma.$on('query', …)` (log en mode `emit: 'event'`), ou collecteur du profiler dans un test fonctionnel Symfony.

## Livrable
```markdown
| Scénario | Requêtes avant → après | Durée SQL avant → après | Volume de test |
|----------|------------------------|-------------------------|----------------|
| GET /api/v1/orders (20 éléments) | 43 → 3 | 180 ms → 12 ms | 200 000 commandes |
Plan après : `Index Scan using orders_user_id_created_at_idx` (extrait cité).
Index ajouté : (user_id, created_at), migration <fichier>. Test de verrou : <test>.
```

## Vérifications
- Chaque affirmation de gain cite la commande, le volume de test et le plan avant et après.
- Le test du nombre de requêtes est vu rouge en réintroduisant le chargement paresseux, puis vert.
- Les résultats renvoyés sont identiques avant et après (même test fonctionnel vert, même ordre).

## Limites
- Les plans dépendent des statistiques et du volume : un gain mesuré en local reste **non vérifié** en production tant qu'il n'y est pas mesuré.
- Lire ou analyser la base de production est une action réservée (règle 5 des principes communs) : prépare la requête `EXPLAIN` et laisse l'humain la lancer.

## En cas de blocage
- La requête reste lente avec le bon index : le problème est le volume ou le besoin (agrégat sur toute l'histoire) ; propose une table de synthèse ou un calcul asynchrone à `architect`, ou un cache (skill `caching`).
- ORM incapable d'exprimer la requête efficace : requête native paramétrée dans un repository dédié, couverte par un test d'intégration sur le vrai moteur.
