# Documentation de suivi par projet (proposition v0.1)

> Réponse à : « je veux pour chaque projet un gros doc de suivi des mises à jour et de documentation ».

## 1. Idée

Plutôt qu'un seul fichier géant qui devient illisible, chaque projet reçoit un dossier `docs/` avec **un point d'entrée unique** (`docs/PROJECT.md`) et des fichiers spécialisés qui y sont liés. Tous les agents écrivent dedans à la fin de chaque tâche, selon une règle commune. On obtient l'effet « gros doc » sans le chaos.

## 2. Arborescence installée dans chaque projet

```
docs/
  PROJECT.md          ← le document maître (vivant)
  CHANGELOG.md        ← toutes les mises à jour, format Keep a Changelog
  journal/
    2026-10-12-auth-login.md   ← une entrée par tâche ou session
  adr/
    0001-choix-stack.md        ← une décision technique par fichier
  spec.md             ← besoin (product-analyst)
  architecture.md     ← conception (architect)
  plan.md             ← tâches et leur état (planner)
  api.md              ← référence API (doc-writer)
  runbook.md          ← installer, lancer, déployer, dépanner (devops-engineer)
  livraisons/         ← un rapport de livraison par fonctionnalité (quality-gatekeeper)
  incidents/          ← une analyse par incident de production (debugger)
  ux/                 ← parcours, écrans, design system (ui-ux-designer)
  seo/                ← stratégie, spécifications par page, audits (seo-specialist, sites publics)
```

## 3. Le document maître `docs/PROJECT.md`

Sections fixes :
1. **Résumé** : ce que fait le projet, pour qui.
2. **État actuel** : version, dernière mise à jour, ce qui marche, ce qui est en cours.
3. **Stack et architecture** : résumé + lien vers `architecture.md`.
4. **Fonctionnalités** : tableau fonctionnalité / statut (prévu, en cours, livré) / lien spec.
5. **Décisions clés** : liste des ADR avec une ligne chacune.
6. **Dernières mises à jour** : les 10 dernières entrées du journal (liens).
7. **Dette technique et risques connus.**
8. **Index** : liens vers tous les autres fichiers de `docs/`.

## 4. Qui écrit quoi

| Fichier | Écrit par | Quand |
|---------|-----------|-------|
| `journal/*.md` | **chaque agent** qui modifie quelque chose | fin de tâche |
| `CHANGELOG.md` (section *Unreleased*) | `implementer`, agents framework, `debugger`, `refactorer`, `data-modeler` | fin de tâche |
| `plan.md` (statut des tâches) | `planner`, puis l'agent qui termine la tâche | fin de tâche |
| `adr/` | `architect` (et tout agent qui prend une décision structurante, via l'architect) | à la décision |
| `PROJECT.md` | `doc-writer` | après chaque fonctionnalité livrée ou à la demande |
| `api.md`, `runbook.md` | `doc-writer`, `devops-engineer` | quand l'API ou le déploiement change |
| Release (versionner le changelog) | `doc-writer` | à chaque version |
| `livraisons/*.md` | `quality-gatekeeper` | à chaque fin de fonctionnalité |
| `incidents/*.md` | `debugger` | après chaque incident |
| `ux/` | `ui-ux-designer` | avant l'implémentation d'une interface |
| `seo/` | `seo-specialist` | avant l'implémentation et avant la livraison d'un site public |

## 5. Gabarit d'une entrée de journal

```markdown
# 2026-10-12 · Connexion par e-mail
- Agent : laravel-implementer
- Tâche : plan.md#T4
- Fait : formulaire de connexion, contrôleur, tests Feature
- Fichiers : app/Http/Controllers/Auth/LoginController.php, tests/Feature/LoginTest.php
- Décisions : limitation à 5 tentatives par minute (rate limiter Laravel)
- Vérifications : 12 tests verts, lint OK
- Reste à faire / risques : réinitialisation du mot de passe (T5)
```

## 6. Comment l'intégrer techniquement

1. **Une règle commune dans chaque agent** : la section « Suivi documentaire » présente dans tous les fichiers d'agents (déjà rédigée).
2. **Un skill global `project-docs-tracking`** : contient les gabarits ci-dessus et la procédure. Chargé par tous les agents. Compatible Claude Code et Codex (même format `SKILL.md`).
3. **Le fichier d'instructions du projet** (`CLAUDE.md` pour Claude Code, `AGENTS.md` pour Codex) contient trois lignes : lire `docs/PROJECT.md` au début de toute session, appliquer `project-docs-tracking` en fin de tâche, ne jamais supprimer d'entrée de journal.
4. **Initialisation** : `scaffolder` crée le dossier `docs/` avec les gabarits vides au démarrage du projet.
5. **Option Claude Code** : un hook de fin de session peut rappeler de mettre le journal à jour si des fichiers ont changé sans entrée de journal. À ajouter plus tard si la règle seule ne suffit pas.

## 7. Le rapport de livraison

C'est le document que l'utilisateur lit à la place du code. `quality-gatekeeper` le produit à chaque fin de fonctionnalité : verdict (accepté, accepté sous réserve, refusé), résumé fonctionnel sans jargon, indicateurs (tests, parcours e2e, critères d'acceptation, revue, sécurité, performance) avec un lien vers chaque preuve, ce qui est non testé ou risqué, ce qui demande une validation humaine. Gabarit complet dans `Agent/Global/quality-gatekeeper.md`.

## 8. Bénéfice pour le vibe coding

Un nouvel agent (ou une nouvelle session) lit `PROJECT.md` et les dernières entrées du journal, et sait immédiatement où en est le projet, sans tout relire.
