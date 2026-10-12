---
name: db-schema-design
description: Concevoir un schéma relationnel juste avant d'écrire la migration - entités et relations tirées des règles métier, types précis (montants, dates UTC, énumérations, texte), clés primaires, clés étrangères et règle ON DELETE, contraintes d'intégrité portées par la base (non nul, unicité, check), index composites dans le bon ordre, suppression logique, multi-tenant, colonnes JSON et dénormalisation justifiées. À utiliser pour toute nouvelle table ou relation, toute colonne dont le type ou la contrainte est à choisir, et pour revoir un modèle existant ; l'exécution sûre du changement relève du skill migrations.
---

# Conception de schéma

`data-modeler` conçoit types, clés, contraintes et index (procédure, point 2). Ce skill dit comment choisir ; la façon de livrer le changement sans casse (étapes, verrous, retour arrière) est dans le skill `migrations`.

## Quand l'utiliser
- `data-modeler` : toute nouvelle table, relation ou colonne, et toute revue de modèle.
- `architect` : modèle de données haut niveau ; agents d'implémentation : entité ou modèle ORM à créer.

## Ce que l'agent rate sans ce skill
- Il garantit l'unicité ou l'existence d'une relation par la validation applicative seule : deux requêtes simultanées créent le doublon.
- Il stocke un montant en `float`, une date locale sans fuseau, un statut en texte libre sans contrainte.
- Il ajoute `deleted_at` (suppression logique) et garde un index unique simple : on ne peut plus recréer un compte avec l'adresse d'un compte supprimé.
- Il rend l'e-mail unique en respectant la casse : `A@x.io` et `a@x.io` coexistent.
- Il utilise une association polymorphe (`commentable_type`, `commentable_id`) ou une colonne JSON là où une clé étrangère est possible, et perd toute intégrité.
- Il laisse `ON DELETE` par défaut sans y penser, ou met `CASCADE` partout et une suppression efface l'historique de facturation.
- Il crée un index par colonne au lieu d'un index composite dans l'ordre des requêtes réelles, et duplique celui que crée déjà la clé étrangère (MySQL).
- Il oublie la colonne de locataire dans les contraintes d'unicité d'une application multi-tenant.

## Entrées
- Les règles métier (`docs/spec.md`, RG-xx), `docs/architecture.md`, le schéma actuel : `php artisan db:show` et `php artisan model:show <Modèle>` (Laravel), `php bin/console doctrine:schema:validate` (Symfony), entités JPA et `spring.jpa.hibernate.ddl-auto=validate` en test (Spring Boot), `schema.prisma` et `npx prisma validate` (Next.js avec Prisma).
- Le moteur et sa version, les requêtes prévues sur ces tables (écrans, filtres, exports).

## Procédure
1. **Partir des règles métier** : pour chaque entité, écris les invariants (« un utilisateur a au plus un abonnement actif », « une facture émise ne change plus »). Chaque invariant devient une contrainte de base, ou est noté comme impossible à porter par la base et alors protégé dans le code par un verrou ou une transaction.
2. **Choisir les types** :

| Donnée | Type par défaut |
|--------|-----------------|
| Montant | `DECIMAL(19,4)` ou entier en plus petite unité, plus colonne devise ; jamais `FLOAT` |
| Instant | `timestamptz` (PostgreSQL) ; `DATETIME` en UTC (MySQL : `TIMESTAMP` s'arrête en 2038) |
| Date seule | `DATE` (anniversaire, échéance), sans conversion de fuseau |
| Statut, catégorie | chaîne courte avec contrainte `CHECK` ou table de référence ; énumération native seulement si le projet l'utilise déjà (ajout de valeur coûteux) |
| E-mail, identifiant de connexion | unicité insensible à la casse : `citext` ou index unique sur `lower(email)` (PostgreSQL), collation `_ci` (MySQL), ou normalisation en minuscules à l'écriture |
| Texte | longueur bornée par la règle métier ; `TEXT` pour du contenu libre |
| Booléen exclusif | un seul statut plutôt que plusieurs booléens incompatibles (`is_paid`, `is_cancelled`) |

3. **Clés primaires** : convention du projet d'abord. Sinon entier auto-incrémenté en interne ; identifiant non devinable (UUIDv7 ou ULID, triables) si l'identifiant est exposé dans les URL ou généré côté client hors ligne.
4. **Clés étrangères** sur chaque relation, `NOT NULL` si la relation est obligatoire, et `ON DELETE` choisi :
   - `RESTRICT` par défaut pour les données de valeur (factures, commandes, paiements) ;
   - `CASCADE` seulement pour une partie qui n'existe pas sans son parent (lignes d'un brouillon) ;
   - `SET NULL` quand l'enfant survit au parent (auteur supprimé d'un commentaire).
5. **Contraintes** : `NOT NULL` par défaut, unicité sur chaque clé métier (avec `tenant_id` en tête en multi-tenant), `CHECK` sur les bornes (`quantity > 0`, `ends_at > starts_at`). Suppression logique avec unicité : index unique partiel `WHERE deleted_at IS NULL` (PostgreSQL, SQLite) ; en MySQL, colonne générée ou absence de suppression logique sur ces tables.
6. **Index** depuis les requêtes prévues, pas depuis les colonnes : colonnes d'égalité d'abord, puis la colonne de tri ou d'intervalle (`(user_id, created_at)` pour « les commandes d'un utilisateur, plus récentes d'abord »). PostgreSQL n'indexe pas les clés étrangères tout seul : ajoute-les ; MySQL InnoDB le fait : n'en crée pas un deuxième. Vérification par plan d'exécution : skill `db-query-optimization`.
7. **Normaliser, puis dénormaliser avec preuve** : une copie (total de commande, compteur) n'est acceptée que pour une lecture mesurée lente ou pour figer une valeur historique (prix au moment de l'achat), avec la règle qui la tient à jour écrite dans le code et un test.
8. **JSON** seulement pour des données sans contrainte ni filtre fréquent (préférences, payload brut d'un webhook). Dès qu'un champ est filtré, joint ou obligatoire, il devient une colonne.
9. **Écrire le changement** avec le skill `migrations`, puis l'entité ou le modèle ORM, ses relations, sa factory.

## Livrable
Dans `docs/architecture.md` (section « Modèle de données ») ou le compte rendu :
```markdown
### Table `orders`
| Colonne | Type | Null | Contrainte / défaut | Raison |
|---------|------|------|---------------------|--------|
| id | bigint | non | PK | convention du projet |
| user_id | bigint | non | FK users ON DELETE RESTRICT | une commande garde son client (RG-07) |
| status | varchar(20) | non | CHECK in (draft, paid, cancelled) | RG-08 |
| total_cents | bigint | non | CHECK >= 0 | montant figé à la validation |
Index : (user_id, created_at) — liste « mes commandes » triée (US-05).
Invariants non portés par la base : <invariant> — protégé par <verrou / transaction / test>.
```

## Vérifications
- Chaque invariant des règles métier est soit une contrainte (citée), soit listé comme non porté avec sa protection.
- Test d'intégration qui tente le doublon ou la relation orpheline et attend l'erreur de la base.
- Schéma et ORM d'accord : `doctrine:schema:validate`, `ddl-auto=validate`, `prisma validate` ou `model:show` sans écart.

## Limites
- Le choix du SGBD est une décision de `architect` (skill `adr`).
- Les bases documentaires ou clé-valeur suivent d'autres règles, que ce skill ne couvre pas.

## En cas de blocage
- Règle métier ambiguë sur la suppression ou l'unicité : prends l'option qui préserve les données (`RESTRICT`, unicité stricte), consigne l'hypothèse et laisse `product-analyst` trancher.
- Données existantes qui empêchent la contrainte : suis le skill `migrations`, section « En cas de blocage ».
