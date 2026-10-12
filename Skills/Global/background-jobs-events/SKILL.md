---
name: background-jobs-events
description: Concevoir et coder les traitements asynchrones et les événements - tâches en file d'attente, tâches planifiées, événements de domaine, messages entre services (RabbitMQ, Kafka, SQS…), webhooks reçus - avec idempotence, envoi après commit (outbox), reprises, file des messages en échec, ordre, observabilité et tests. À utiliser dès qu'un traitement ne s'exécute pas dans la requête de l'utilisateur.
---

# Traitements asynchrones et événements

Un traitement asynchrone est exécuté plus tard, ailleurs, parfois plusieurs fois, parfois dans le désordre. Le code qui fonctionne en local en mode synchrone échoue en production sur ces trois points. Ce skill donne les règles qui le rendent sûr.

## Quand l'utiliser
- Ajouter ou modifier une tâche en file d'attente (job), une tâche planifiée, un écouteur d'événement, un consommateur de messages ou un webhook reçu.
- `architect` : choisir entre appel direct, file d'attente, événement de domaine et broker de messages.
- `debugger` : un traitement exécuté deux fois, jamais, ou dans le mauvais ordre.

## Ce que l'agent rate sans ce skill
- Il envoie un message ou lance une tâche dans une transaction : la tâche part avant le commit et lit des données absentes, ou part alors que la transaction a échoué.
- Il écrit un consommateur qui double l'effet quand le message est livré deux fois (deux e-mails, deux débits, deux lignes).
- Il ne fixe ni nombre d'essais, ni délai, ni délai maximal : la tâche boucle à l'infini ou disparaît sans trace.
- Il suppose que les messages arrivent dans l'ordre d'émission.
- Il passe un objet complet dans le message au lieu d'un identifiant, et le consommateur travaille sur une donnée périmée.
- Il ajoute un broker (Kafka, RabbitMQ) là où la file d'attente du framework suffisait.

## Entrées
- `docs/architecture.md` (pilote de file, broker, conventions), la configuration des files du projet, les tâches et écouteurs existants.

## Procédure

### 1. Choisir le mécanisme
| Besoin | Mécanisme par défaut |
|--------|----------------------|
| Effet secondaire lent ou fragile déclenché par une requête (e-mail, export, appel à un tiers) | file d'attente native du framework (Laravel Queue, Symfony Messenger, `@Async` + file ou Spring Batch, BullMQ côté Node) |
| Prévenir d'autres modules d'un fait métier sans les connaître | événement de domaine, traité de façon synchrone ou mis en file selon le coût |
| Communication entre applications ou services séparés | broker de messages, seulement si l'architecture a des services séparés (ADR, skill `architecture-patterns`) |
| Traitement périodique | planificateur du framework, avec protection contre l'exécution simultanée |
| Événement envoyé par un tiers | webhook reçu : vérifier, enregistrer, répondre vite, traiter en file |

Le pilote de file en développement et en test peut être synchrone ; le code doit rester correct avec un pilote asynchrone.

### 2. Émettre après le commit
- Une tâche, un événement ou un message déclenché par une écriture en base part **après** le commit : option native du framework (`afterCommit`, écouteur transactionnel, `@TransactionalEventListener(phase = AFTER_COMMIT)` en Spring) ou motif **outbox**.
- Outbox, obligatoire quand la perte d'un message vers un autre service est inacceptable : le message est écrit dans une table `outbox` dans la même transaction que la donnée, puis un processus le publie et le marque envoyé. La publication peut donc être répétée : le consommateur doit être idempotent.

### 3. Rendre chaque consommateur idempotent
- Le message transporte des identifiants et une clé d'idempotence (identifiant de l'événement, de la commande ou du webhook), pas l'objet complet. Le consommateur recharge l'état à jour.
- Avant l'effet, le consommateur vérifie qu'il n'a pas déjà été produit : table des messages traités avec contrainte d'unicité, état métier (« déjà payé »), opération naturellement idempotente (mise à jour à une valeur fixe, `upsert`).
- Un effet externe non idempotent (paiement, e-mail) transmet la clé d'idempotence au tiers quand il l'accepte.

### 4. Reprises, échecs et délais
- Chaque tâche ou consommateur fixe explicitement : nombre d'essais, délai entre essais (croissant), délai maximal d'exécution.
- Erreur définitive (donnée invalide, ressource supprimée) : pas de nouvel essai, échec enregistré avec la cause. Erreur temporaire (réseau, tiers indisponible) : nouvel essai.
- Après le dernier essai, le message va dans la file des échecs (`failed_jobs`, dead letter queue) avec assez de contexte pour le rejouer ; la commande de rejeu est documentée dans `docs/runbook.md`.
- Une tâche planifiée longue est protégée contre deux exécutions simultanées (verrou du framework, `withoutOverlapping`, `onOneServer`, verrou en base).

### 5. Ordre et concurrence
- Ne suppose pas l'ordre. Si l'ordre compte pour une même entité : clé de partition par entité (Kafka), groupe de messages (SQS FIFO), ou numéro de version comparé par le consommateur qui ignore un message plus ancien que l'état connu.
- Deux consommateurs simultanés sur la même entité : verrou optimiste (version) ou verrou en base sur la ligne, jamais une vérification puis une écriture sans protection.

### 6. Contrat des messages
- Chaque événement ou message a un nom au passé (`CommandeValidée`), une version de format, et un schéma documenté dans `docs/api.md` (ou un schéma partagé dans un monorepo, skill `monorepo`).
- Faire évoluer un message : ajouter des champs optionnels ; un changement incompatible crée une nouvelle version, et l'ancienne reste consommée pendant la transition.
- Aucune donnée personnelle ni secret inutile dans un message ; les messages sont journalisés sans leur contenu sensible.

### 7. Observabilité et tests
- Chaque traitement journalise son début, sa fin, sa durée et l'identifiant de corrélation de la requête d'origine.
- Tests : le déclenchement (la tâche est mise en file avec les bons paramètres, après le commit), le traitement lui-même (exécuté directement), l'idempotence (deux exécutions = un seul effet), l'échec définitif (pas de nouvel essai).

## Livrable
- Le traitement codé avec : mécanisme justifié, émission après commit, idempotence, essais et délais explicites, destination des échecs, tests ci-dessus.
- `architect` : la section « Traitements asynchrones » de `docs/architecture.md` (mécanisme, pilote, files, conventions de messages) et un ADR si un broker est ajouté.

## Vérifications
- Le test d'idempotence passe (même message traité deux fois, un seul effet).
- Aucune émission dans une transaction sans `afterCommit` ou outbox (recherche dans le diff).
- Le nombre d'essais, le délai et le délai maximal sont explicites pour chaque nouveau traitement.
- La commande de rejeu des échecs est documentée dans `docs/runbook.md`.

## Limites
- Les pièges propres à un framework (sérialisation des modèles, configuration du pilote) sont dans le skill du framework (`laravel`, `symfony`, `spring-boot`…).
- Mettre en place un broker ou un service de file payant en production est une action réservée (coût, infrastructure) : préparer l'ADR et la configuration, l'humain décide.

## En cas de blocage
- Pas de pilote asynchrone disponible en local : tester le traitement en l'exécutant directement et le déclenchement avec le faux de file du framework ; marquer le fonctionnement réel de la file **non vérifié**.
- Idempotence impossible à garantir (tiers sans clé d'idempotence) : enregistrer l'appel avant de le faire, le marquer terminé après, et signaler le risque résiduel de doublon dans le compte rendu.
