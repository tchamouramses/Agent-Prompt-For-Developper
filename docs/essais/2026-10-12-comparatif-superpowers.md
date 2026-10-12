# Bibliothèque face à Superpowers : essai Angular + Laravel

Date : 2026-10-12. Un essai par système, même projet de départ, même consigne, même modèle (Sonnet), sans intervention humaine (`claude -p`).

**Fonctionnalité demandée** : réservation de salles.
- API Laravel : Sanctum, pas de chevauchement même en concurrence, droits propriétaire et admin, e-mail de confirmation mis en file après le commit.
- Front Angular : connexion, liste des salles, planning du jour, formulaire qui montre les conflits, annulation de ses réservations.

- **A** : cette bibliothèque, installés avec `install.py --stack laravel,angular --outil claude` (21 agents, 60 skills), lancés par l'orchestrateur.
- **B** : le plugin Superpowers d'obra (`--plugin-dir`).

## Verdict

Les deux livrent une fonctionnalité qui marche. Les tests en boîte noire donnent exactement le même comportement.

A livre nettement plus de garanties : quatre fois plus de tests, sécurité durcie, documentation de suivi complète. En contrepartie, il coûte environ 9 fois plus cher et prend 6 fois plus de temps.

B est rapide et bon marché. En mode autonome, il n'a pourtant presque pas utilisé sa méthode : un seul skill (brainstorming), pas de plan écrit, pas de TDD, pas de sous-agents.

## Chiffres

| | A (bibliothèque) | B (Superpowers) |
|---|---|---|
| Durée | 34 min | 6 min |
| Coût | 10,62 $ (Sonnet 6,92 $, Opus 3,70 $) | 1,14 $ |
| Mécanisme | 16 appels d'agents | 1 skill, 0 sous-agent |
| Refus de permission | 24 | 1 |
| Commits / fichiers / lignes | 13 / 97 / +4237 | 2 / 43 / +1567 |
| Tests API relancés à part | 86/86 (386 assertions) | 23/23 |
| Tests Angular relancés à part | 58/58 | 10/10 |
| Build Angular | OK | OK |
| Pint (style PHP) | conforme | non conforme |
| Verdict de fin | « Accepté sous réserve » (gatekeeper), réserves R1 à R10 | aucun |

Détail des 16 appels d'agents de A :
- laravel-implementer ×5
- angular-implementer ×4
- code-reviewer ×2
- security-auditor ×2
- quality-gatekeeper ×2
- doc-writer ×1

## Sonde en boîte noire

Chaque API a été lancée sur une base SQLite neuve, servie par `php artisan serve` avec 24 workers.

| Cas | A | B |
|---|---|---|
| 5 rafales de 24 requêtes parallèles sur un même créneau (24 utilisateurs différents) | 5 × 201, 115 × 409 | 5 × 201, 115 × 409 |
| Réservations qui se chevauchent en base | 0 | 0 |
| Chevauchement partiel | 409 | 409 |
| Créneau adjacent | 201 | 201 |
| Fin avant début | 422 | 422 |
| Sans jeton | 401 | 401 |
| Un autre utilisateur modifie ou annule | 403 / 403 | 403 / 403 |
| L'admin annule | 204 | 204 |
| E-mails en file (`jobs`) | 1 par réservation créée | 1 par réservation créée |

Une première sonde a envoyé les 20 requêtes avec le même utilisateur. A a alors répondu 429 après 10 écritures, à cause de sa limite de 10 écritures par minute et par utilisateur. B n'a pas de limite de débit.

## Différences qui comptent

**Concurrence**
- Les deux verrouillent la salle (`lockForUpdate`) dans une transaction.
- B a configuré SQLite pour ce cas : transactions `IMMEDIATE`, WAL, `busy_timeout`. Sur SQLite, c'est la bonne réponse.
- A a laissé SQLite en `DEFERRED`. Il écrit lui-même que le verrou est sans effet sur SQLite, et il l'a noté en réserve.
- Ma sonde ne montre aucun doublon chez A. En revanche, en `DEFERRED`, une vraie collision donne plutôt une erreur 500 (base occupée) qu'un 409 propre.
- Ni l'un ni l'autre n'a testé sur MySQL ou PostgreSQL.

**Sécurité**
- A :
  - jeton en `sessionStorage` ;
  - expiration des jetons ;
  - limites de débit sur la connexion et les écritures ;
  - CORS restreint ;
  - comptes de démo exclus en production.
- B :
  - jeton en `localStorage` ;
  - aucune limite de débit sur les écritures ;
  - comptes de démo avec le mot de passe `password`.

**Tests**
- A a des tests dédiés :
  - verrou ;
  - e-mail après commit ;
  - retour arrière des migrations ;
  - seeder ;
  - garde, intercepteur et service d'authentification côté Angular.
- B couvre le parcours principal et peu de cas limites (2 fichiers de tests côté Angular).

**Suivi et documentation**
- A tient un `docs/` complet :
  - PROJECT, CHANGELOG et journal ;
  - spec avec hypothèses H-01 à H-11 ;
  - plan avec réserves R1 à R10 ;
  - rapports de contrôle.
- B a écrit une spec dans `docs/superpowers/specs/`.

**Lacunes communes**
- Aucun test de navigateur de bout en bout n'a été exécuté.
- Aucune concurrence réelle n'a été testée sur une base de production.

## Limites de l'essai

- Un seul essai par système : la variance entre deux runs peut être forte.
- Superpowers est pensé pour une session interactive. En particulier, brainstorming pose des questions à l'utilisateur. En `-p` sans humain, il se réduit presque à un agent seul, donc l'essai le désavantage sur la méthode. Il le mesure pourtant bien sur l'objectif de la bibliothèque : avancer sans intervention humaine.

## Suites données

Appliquées d'abord en global, puis par langage (principe 3 du catalogue, décision 19) :

1. **Concurrence** : skill global `concurrency-control` (choix du mécanisme, effet réel selon le moteur dont SQLite, collisions traduites en 409, test de concurrence réelle), traduit dans `laravel` (verrou, `transaction_mode IMMEDIATE`, WAL, `busy_timeout`), `symfony`, `spring-boot`, `nextjs`, `testing-php` et `testing-java`. `test-engineer`, `acceptance-criteria` et `code-review-checklist` y renvoient.
2. **Bout en bout** : `e2e-validator` obligatoire dès qu'une interface est touchée ; `quality-gatekeeper` ne statue pas sans son rapport. Si aucun navigateur ne peut tourner dans l'environnement, le verdict est au mieux « Accepté sous réserve ».
3. **Coût** :
   - tâches consécutives d'une même application regroupées dans un brief ;
   - un contrôle qui a accepté n'est relancé que si une correction touche sa zone ;
   - petite fonctionnalité d'une seule application en profil léger ;
   - `quality-gatekeeper` sur Sonnet (Opus reste pour `architect` et `security-auditor`).
4. **Permissions** : l'installateur autorise sans confirmation les commandes de développement générales (`Config/claude/settings.json`) puis celles de chaque stack retenue (`Config/claude/autorisations-stacks.json`), pour supprimer les refus de permission. Les refus et le hook des actions réservées passent toujours avant ; Codex n'en a pas besoin (bac à sable `workspace-write`).

## Reproduire

- Projet de base : monorepo `apps/api` (Laravel 12, SQLite, file `database`) et `apps/web` (Angular 21, `.npmrc` avec `legacy-peer-deps=true`).
- Lancement : `claude -p "<consigne>" --model sonnet --permission-mode acceptEdits --allowedTools "<outils et commandes>" --output-format stream-json --verbose`, avec un `CLAUDE_CONFIG_DIR` isolé. L'orchestrateur se lance avec `--agent orchestrator` ; Superpowers se charge avec `--plugin-dir`.
- Sonde : base SQLite neuve, `PHP_CLI_SERVER_WORKERS=24 php artisan serve`, 24 utilisateurs avec chacun son jeton, 5 rafales parallèles sur un même créneau, puis comptage des statuts et requête de contrôle des chevauchements.
