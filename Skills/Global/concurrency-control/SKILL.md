---
name: concurrency-control
description: Garantir une règle d'exclusivité sous accès simultanés (pas de double réservation, stock ou solde jamais négatif, numéro unique, job traité une seule fois) - choisir entre contrainte de base, verrou pessimiste, version optimiste ou idempotence, tenir compte du moteur réel (SQLite, MySQL, PostgreSQL), et prouver la règle par un test de concurrence réelle. À utiliser dès qu'un critère ou une règle métier doit tenir quand plusieurs requêtes ou workers écrivent en même temps.
---

# Contrôle de la concurrence

Ce skill est général : il fixe la méthode quel que soit le langage. Les skills de framework (`laravel`, `symfony`, `spring-boot`, `nextjs`) et de test par langage (`testing-php`, `testing-java`, `testing-typescript`) en donnent ensuite la traduction dans leur stack.

## Quand l'utiliser
- Une règle doit tenir sous accès simultanés : pas de chevauchement de créneaux, stock ou solde jamais négatif, valeur unique, une seule commande par panier, un job traité une fois.
- Une écriture dépend d'une lecture préalable (« vérifier puis écrire »).
- Une revue ou un critère d'acceptation mentionne la concurrence, la double soumission ou le rejeu.

## Ce que l'agent rate sans ce skill
- Il écrit « vérifier puis insérer » sans verrou ni contrainte : deux requêtes simultanées passent toutes les deux la vérification.
- Il pose un verrou qui n'a aucun effet sur le moteur utilisé (par exemple `SELECT … FOR UPDATE` sur SQLite) et le déclare suffisant.
- Il « prouve » la règle par un test séquentiel, qui passe même sans aucune protection.
- Il laisse une collision produire une erreur 500 (base occupée, interblocage) au lieu d'un refus métier propre (409) ou d'une nouvelle tentative.
- Il envoie l'e-mail ou lance le job avant le commit, donc aussi quand la transaction échoue.

## Entrées
- La règle d'exclusivité, écrite comme un invariant (« pour une salle, deux réservations actives ne se chevauchent jamais »).
- Le moteur de base de données de chaque environnement (développement, test, CI, production) et sa version.
- Le modèle d'exécution : nombre de workers ou de processus, files d'attente, plusieurs instances.

## Procédure
1. **Écrire l'invariant** et la ressource qui le porte (la salle, l'article, le compte). Consigne-le dans la spec ou l'ADR.
2. **Choisir le mécanisme**, du plus sûr au plus fragile :
   - **Contrainte de base** quand le moteur sait l'exprimer : index unique, contrainte d'exclusion sur des intervalles (PostgreSQL `EXCLUDE USING gist`), `CHECK`. La base refuse elle-même le doublon ; le code traduit l'erreur en refus métier.
   - **Verrou pessimiste sur la ressource parente**, dans une transaction : verrouiller la ligne qui porte l'invariant (`SELECT … FOR UPDATE` sur la salle), puis vérifier, puis écrire. Toutes les écritures concernées prennent le même verrou, dans le même ordre, pour éviter les interblocages.
   - **Version optimiste** (colonne `version` ou `ETag`) quand les conflits sont rares et que le client peut recharger : l'écriture échoue si la version a changé.
   - **Idempotence** pour les rejeux (double clic, job relancé, webhook) : clé d'idempotence ou contrainte unique sur l'identifiant de l'opération.
3. **Vérifier l'effet sur chaque moteur utilisé.**
   - **SQLite** : un seul écrivain à la fois pour toute la base ; `FOR UPDATE` n'existe pas. En transaction différée, deux transactions lisent puis l'une échoue en « base occupée » au moment d'écrire. Configure des transactions immédiates (verrou d'écriture dès le début), le journal WAL et un délai d'attente (`busy_timeout` de quelques secondes).
   - **MySQL / MariaDB (InnoDB)** : `SELECT … FOR UPDATE` verrouille les lignes lues et, en `REPEATABLE READ`, les intervalles (gap locks) ; une recherche sans index adapté verrouille beaucoup plus que prévu. Gère l'interblocage (erreur 1213) par une nouvelle tentative limitée.
   - **PostgreSQL** : `FOR UPDATE` verrouille les lignes ; préfère une contrainte d'exclusion pour les intervalles. En `SERIALIZABLE`, prévois la nouvelle tentative sur l'erreur de sérialisation.
   - Si les tests tournent sur un moteur différent de la production, la preuve sur le moteur de test ne vaut pas pour la production : ajoute un test sur le moteur de production (service de CI, conteneur) ou marque la règle **non vérifiée** pour ce moteur.
4. **Traduire les collisions** : le perdant reçoit un refus métier clair (409 avec la ressource en conflit), jamais une erreur 500. Une erreur transitoire (base occupée, interblocage, sérialisation) donne une nouvelle tentative bornée, puis un 409 ou 503 explicite.
5. **Effets après le commit** : e-mails, jobs, événements et appels externes partent après le commit de la transaction (skill `background-jobs-events`).
6. **Prouver par un test de concurrence réelle** :
   - lancer l'application comme en exécution réelle, avec plusieurs workers ou processus ;
   - envoyer N requêtes parallèles (au moins 20) qui visent la même ressource, avec des utilisateurs différents pour ne pas buter sur une limite de débit ;
   - vérifier : exactement le nombre attendu de succès, les autres en refus métier, **aucune** erreur 5xx, et en base aucune ligne qui viole l'invariant (requête de contrôle) ;
   - répéter plusieurs rafales (au moins 3) ; une seule réussite ne prouve rien.
   Le test séquentiel (« une deuxième réservation sur le même créneau est refusée ») reste nécessaire mais ne prouve pas la concurrence.
7. **Consigner** dans le compte rendu : mécanisme choisi, moteur(s) sur lesquels la preuve a été faite, commande du test de concurrence et résultat (nombre de succès, de refus, d'erreurs, lignes en violation).

## Livrable
Le mécanisme en place, la traduction des collisions en refus métier, et un test de concurrence réelle reproductible (script ou test de la suite) avec son résultat cité.

## Vérifications
- L'invariant est écrit et chaque chemin d'écriture qui peut le violer prend le même verrou ou heurte la même contrainte.
- Le test de concurrence réelle passe sur plusieurs rafales : 0 erreur 5xx, 0 ligne en violation.
- Le moteur de la preuve est cité ; un moteur de production différent est couvert par un test ou marqué **non vérifié**.
- Aucun effet externe ne part avant le commit.

## Limites
- Ce skill couvre une base de données partagée. Les invariants répartis entre plusieurs services ou bases (saga, verrou distribué, file ordonnée) relèvent du skill `architecture-patterns` et d'un ADR.
- Le réglage fin de l'isolation et des index pour la performance relève du skill `db-query-optimization`.

## En cas de blocage
- Impossible de lancer plusieurs workers dans l'environnement : test parallèle au niveau des processus de test (plusieurs connexions à la base), règle marquée **non vérifiée en conditions réelles** avec la commande prête.
- Moteur de production indisponible en local ou en CI : test sur le moteur disponible, écart consigné en réserve, tâche au plan pour ajouter le service de base en CI.
