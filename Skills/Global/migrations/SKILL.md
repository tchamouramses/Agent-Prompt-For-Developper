---
name: migrations
description: Écrire des migrations de schéma et de données sûres - réversibles, sans perte, compatibles avec le code déjà déployé, sans verrou long sur les grosses tables, découpées en étapes (ajouter, remplir, basculer, retirer). À utiliser pour toute création ou modification de table, colonne, index, contrainte ou reprise de données, quel que soit l'outil (Laravel, Doctrine, Flyway, Liquibase, Prisma, Drizzle).
---

# Migrations

La règle « découper les changements de données en deux temps » est dans les principes des agents qui modifient du code (gestion des régressions) ; les données réelles restent réservées à l'humain (règle 5 des principes communs). Ce skill donne la méthode.

## Quand l'utiliser
- Création ou modification d'une table, d'une colonne, d'un index, d'une contrainte ou d'une clé étrangère.
- Reprise, transformation ou nettoyage de données existantes.

## Ce que l'agent rate sans ce skill
- Il modifie une migration déjà appliquée ailleurs au lieu d'en écrire une nouvelle.
- Il renomme ou supprime une colonne dans le même déploiement que le code qui cesse de l'utiliser : pendant la mise en production, l'ancien code tourne encore et casse.
- Il ajoute une colonne `NOT NULL` sans valeur par défaut sur une table pleine, ou un index qui verrouille une grosse table en écriture.
- Il mélange reprise de données et changement de schéma dans une migration non rejouable.
- Il écrit un `down()` vide, ou qui détruit des données sans le dire.

## Entrées
- Le schéma actuel (dernières migrations, `php artisan model:show`, entités Doctrine, `schema.prisma`), le moteur et sa version (MySQL, MariaDB, PostgreSQL, SQLite), la taille estimée des tables touchées si elle est connue, le code qui lit et écrit ces colonnes.

## Procédure
1. **Savoir si une migration est déjà appliquée ailleurs** : elle l'est si elle figure sur la branche principale ou dans une version publiée (`git log origin/main -- <fichier>`). Une migration appliquée ne se modifie jamais : écris-en une nouvelle. Une migration créée sur ta branche et jamais fusionnée peut être corrigée.
2. **Classer le changement** :
   - **additif sans risque** : nouvelle table, colonne nullable ou avec défaut, nouvel index sur petite table → une migration ;
   - **destructif ou incompatible** : renommage, suppression, changement de type, passage à `NOT NULL`, contrainte d'unicité sur des données existantes → plusieurs étapes (point 3).
3. **Étendre puis contracter** pour un changement incompatible, chaque étape étant déployable seule et compatible avec le code de l'étape précédente :
   1. ajouter la nouvelle structure (colonne nullable, nouvelle table) ;
   2. écrire dans les deux structures depuis le code ;
   3. reprendre les données existantes (migration de données ou commande séparée, par lots) ;
   4. lire la nouvelle structure ;
   5. retirer l'ancienne dans une tâche ultérieure de `docs/plan.md`, après une mise en production.
   Dans une seule PR, tu peux livrer les étapes 1 à 4 ; l'étape 5 reste une tâche à part.
4. **Éviter les verrous longs** (tables volumineuses ou inconnues) :
   - PostgreSQL : `CREATE INDEX CONCURRENTLY` (hors transaction ; dans Laravel, migration avec `$withinTransaction = false`), contrainte ajoutée `NOT VALID` puis validée ;
   - MySQL 8 et MariaDB : `ALGORITHM=INPLACE, LOCK=NONE` quand c'est possible ;
   - colonne `NOT NULL` : ajouter nullable, remplir par lots, puis poser la contrainte.
5. **Reprise de données** : idempotente (rejouable sans double effet), par lots (`chunkById`, pagination par clé), sans charger toute la table, sans appeler le code métier qui peut changer plus tard (requêtes directes dans la migration), avec un décompte avant et après.
6. **Réversibilité** : `down()` qui restaure le schéma précédent. Si l'annulation perd des données (colonne supprimée), écris-le en commentaire dans `down()` et dans le compte rendu. Une transformation irréversible de données réelles est une décision humaine.
7. **Contraintes et index** : clé étrangère sur chaque relation (avec `ON DELETE` choisi et justifié), index sur chaque colonne de jointure ou de filtre fréquent, unicité garantie par la base et pas seulement par la validation.
8. **Commandes par outil** :

| Outil | Créer | Appliquer en test | Vérifier sans appliquer | Annuler la dernière |
|-------|-------|-------------------|-------------------------|---------------------|
| Laravel | `php artisan make:migration` | `php artisan migrate --env=testing` | `php artisan migrate --pretend` | `php artisan migrate:rollback --step=1` |
| Doctrine | `php bin/console make:migration` ou `doctrine:migrations:diff` (relire le SQL généré) | `doctrine:migrations:migrate --env=test` | `--dry-run` | `doctrine:migrations:migrate prev` |
| Flyway | fichier `V<n>__<description>.sql` | `flyway migrate` sur la base de test | `flyway validate` | migration `U<n>` ou nouvelle version |
| Liquibase | `changeSet` avec `rollback` | `liquibase update` | `liquibase update-sql` | `liquibase rollback-count 1` |
| Prisma | `prisma migrate dev --name <nom>` | idem | `prisma migrate diff` | nouvelle migration (pas de `down`) |

## Livrable
La ou les migrations, le code compatible, et dans le compte rendu : classement du changement, étapes prévues (avec la tâche de retrait ajoutée au plan), verrous évités, preuve de l'aller et du retour.

## Vérifications
- Aller, retour, puis aller à nouveau sur la base de test sans erreur ; commandes et résultats cités.
- Les tests de la zone passent sur le schéma migré.
- Aucune migration déjà appliquée ailleurs n'a été modifiée (`git diff origin/main --stat -- <dossier des migrations>` ne montre que des ajouts).

## Limites
- Tu n'exécutes rien sur une base partagée ou de production (règle 5) : tu prépares la commande et le plan de retour arrière pour l'humain.
- La taille réelle des tables est souvent inconnue : en cas de doute, applique les précautions des grosses tables.

## En cas de blocage
- Données existantes qui violent la future contrainte (doublons, valeurs nulles) : écris la reprise qui les corrige si la règle métier est claire ; sinon, ajoute la contrainte plus tard, consigne l'hypothèse et laisse la décision de nettoyage à `product-analyst`.
- Moteur de test différent du moteur de production : marque le comportement propre au moteur (verrous, types) **non vérifié**.
