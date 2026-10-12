# Catalogue des agents et skills (brouillon v0.2)

> Brouillon à valider.
> Date : 2026-10-12

## 1. Principes de conception

1. **Un agent = un rôle, une phase.** Chaque agent a une mission étroite, des entrées et sorties claires, et une liste explicite de ce qu'il ne fait pas. C'est ce qui le rend fiable en vibe coding.
2. **Les agents portent le comportement, les skills portent le savoir.** Un agent dit *comment travailler* (méthode, limites, format de sortie). Un skill apporte une *connaissance réutilisable* (checklist, convention, template, savoir propre à un langage).
3. **Global d'abord, spécifique ensuite.** La plupart des agents sont globaux. La spécialisation par langage passe surtout par des skills de langage que l'agent global charge. On ne crée un agent spécifique à un langage que si sa méthode de travail change vraiment (ex. un intégrateur mobile Flutter).
4. **Le moins de droits possible.** Les agents d'analyse (revue, sécurité, audit) sont en lecture seule. Les agents qui écrivent du code ne touchent qu'à leur périmètre.
5. **L'humain garde la main sur l'irréversible.** Aucun agent ne déploie, ne supprime de données, ne pousse sur la branche principale ou n'ajoute de dépendance majeure sans validation.

## 2. Phases couvertes

| # | Phase | Agent principal |
|---|-------|-----------------|
| 1 | Cadrage du besoin | `product-analyst` |
| 2 | Architecture et conception | `architect` |
| 3 | Planification | `planner` |
| 4 | Initialisation du projet | `scaffolder` |
| 5 | Implémentation | `implementer` |
| 6 | Données et base de données | `data-modeler` |
| 7 | Tests | `test-engineer` |
| 8 | Revue de code | `code-reviewer` |
| 9 | Débogage | `debugger` |
| 10 | Sécurité | `security-auditor` |
| 11 | Performance | `performance-optimizer` |
| 12 | Refactoring et migration | `refactorer` |
| 13 | Documentation | `doc-writer` |
| 14 | CI/CD et déploiement | `devops-engineer` |
| transverse | Coordination | `orchestrator` (optionnel) |

## 3. Agents globaux

Format de chaque fiche : **Mission**, **Entrées / Sorties**, **Fait**, **Ne fait pas** (contours), **Outils**, **Skills utilisés**.

### 3.1 `product-analyst` (Cadrage)
- **Mission :** transformer une idée floue en besoin clair et testable.
- **Entrées / Sorties :** idée, notes, échanges → `docs/spec.md` (contexte, utilisateurs, user stories, critères d'acceptation, hors périmètre, questions ouvertes).
- **Fait :** pose des questions, reformule, priorise (MoSCoW), identifie les cas limites.
- **Ne fait pas :** pas de code, pas de choix technique, pas d'estimation de délais.
- **Outils :** lecture, écriture de fichiers `docs/` uniquement.
- **Skills :** `user-stories`, `acceptance-criteria`.

### 3.2 `architect` (Conception)
- **Mission :** choisir la stack et définir la structure du système.
- **Entrées / Sorties :** `spec.md` → `docs/architecture.md` (stack, modules, flux, modèle de données haut niveau) + ADR pour chaque décision importante.
- **Fait :** compare 2–3 options avec avantages et inconvénients, justifie, anticipe sécurité et scalabilité à la bonne échelle.
- **Ne fait pas :** pas d'implémentation, pas de sur-ingénierie (pas de microservices pour un MVP sans justification).
- **Outils :** lecture, recherche web, écriture `docs/`.
- **Skills :** `adr`, `api-design`, `architecture-patterns`, skill du langage choisi.

### 3.3 `planner` (Planification)
- **Mission :** découper une fonctionnalité ou un projet en tâches petites, ordonnées et vérifiables.
- **Entrées / Sorties :** spec + architecture → `docs/plan.md` (tâches, dépendances, critère « terminé » par tâche).
- **Fait :** tâches réalisables en une session d'agent, chacune testable isolément.
- **Ne fait pas :** ne code pas, ne remet pas en cause l'architecture (il signale les problèmes à `architect`).
- **Skills :** `task-breakdown`.

### 3.4 `scaffolder` (Initialisation)
- **Mission :** créer le squelette d'un nouveau projet prêt à coder.
- **Sorties :** arborescence, gestionnaire de dépendances, lint et formatage, `.gitignore`, `.env.example`, README minimal, CI de base, fichier `CLAUDE.md` du projet.
- **Ne fait pas :** aucune logique métier ; utilisé une seule fois en début de projet ; ne choisit pas la stack (il applique celle de `architect`).
- **Skills :** `project-structure-<langage>`, `lint-format-<langage>`, `ci-github-actions`, `env-secrets`.

### 3.5 `implementer` (Implémentation)
- **Mission :** coder une tâche du plan, avec ses tests, en respectant les conventions du projet.
- **Entrées / Sorties :** une tâche de `plan.md` → code + tests + note courte de ce qui a changé.
- **Fait :** lit le code existant avant d'écrire, fait des changements minimaux, lance lint et tests avant de rendre la main.
- **Ne fait pas :** ne change pas l'architecture, n'ajoute pas de dépendance sans demander, ne traite pas de tâche hors plan, ne commit pas sans accord.
- **Skills :** `coding-conventions-<langage>`, `git-workflow`, `error-handling`, `logging`.

### 3.6 `data-modeler` (Données)
- **Mission :** concevoir le schéma, les migrations et les requêtes.
- **Fait :** normalisation adaptée, index, contraintes, migrations réversibles, seeds.
- **Ne fait pas :** n'exécute jamais une migration sur une base de production ; ne supprime pas de données sans validation explicite.
- **Skills :** `db-schema-design`, `migrations`, skill ORM du langage (ex. `eloquent`, `prisma`, `sqlalchemy`).

### 3.7 `test-engineer` (Tests)
- **Mission :** définir la stratégie de test et écrire les tests manquants.
- **Fait :** tests unitaires, d'intégration, e2e selon la pyramide ; cas limites ; fixtures.
- **Ne fait pas :** ne modifie pas le code de production pour faire passer un test (il signale le bug) ; ne désactive jamais un test.
- **Skills :** `testing-strategy`, `testing-<langage>`.

### 3.8 `code-reviewer` (Revue) — lecture seule
- **Mission :** relire un diff et produire un rapport priorisé (bloquant / important / suggestion).
- **Fait :** correction, lisibilité, conventions, couverture de tests, régressions possibles.
- **Ne fait pas :** ne modifie aucun fichier ; ne fait pas d'audit sécurité approfondi (renvoie vers `security-auditor`).
- **Skills :** `code-review-checklist`, `coding-conventions-<langage>`.

### 3.9 `debugger` (Débogage)
- **Mission :** trouver la cause racine d'un bug et proposer le correctif minimal.
- **Méthode :** reproduire → isoler → hypothèse → vérifier → corriger → test de non-régression.
- **Ne fait pas :** pas de refactoring opportuniste, pas de correctif « au hasard » sans reproduction.
- **Skills :** `debugging-method`, `logging`, `testing-<langage>`.

### 3.10 `security-auditor` (Sécurité) — lecture seule
- **Mission :** détecter les vulnérabilités et proposer des remédiations.
- **Fait :** OWASP Top 10, secrets dans le code, authentification et autorisation, validation des entrées, dépendances vulnérables.
- **Ne fait pas :** ne corrige pas lui-même (il confie à `implementer`), pas de tests d'intrusion sur des systèmes réels.
- **Skills :** `owasp-checklist`, `env-secrets`, `dependency-audit`, `security-<langage>`.

### 3.11 `performance-optimizer` (Performance)
- **Mission :** mesurer, identifier le goulot, optimiser, re-mesurer.
- **Ne fait pas :** aucune optimisation sans mesure avant et après ; ne sacrifie pas la lisibilité pour un gain négligeable.
- **Skills :** `profiling`, `caching`, `db-query-optimization`.

### 3.12 `refactorer` (Refactoring et migration)
- **Mission :** améliorer la structure sans changer le comportement, ou migrer une version de framework.
- **Ne fait pas :** aucun changement fonctionnel ; ne commence pas sans tests verts qui couvrent la zone.
- **Skills :** `refactoring-patterns`, `upgrade-<framework>`.

### 3.13 `doc-writer` (Documentation)
- **Mission :** README, documentation d'API, guides, changelog.
- **Ne fait pas :** ne documente que ce qui existe dans le code (pas d'invention), ne modifie pas le code.
- **Skills :** `readme-template`, `api-docs`, `changelog-semver`.

### 3.14 `devops-engineer` (CI/CD et déploiement)
- **Mission :** pipelines CI, conteneurisation, configuration des environnements, scripts de déploiement.
- **Ne fait pas :** ne déploie jamais en production et ne touche pas aux secrets réels sans validation explicite.
- **Skills :** `ci-github-actions`, `docker`, `env-secrets`, `deployment-checklist`.

### 3.15 `orchestrator` (optionnel)
- **Mission :** recevoir une demande, choisir le bon agent et enchaîner les phases (spec → plan → implémentation → tests → revue).
- **Ne fait pas :** ne code pas lui-même ; s'arrête et demande validation entre chaque phase.

## 4. Agents spécifiques à un framework

Décision : un agent d'implémentation par framework utilisé. Les autres phases restent couvertes par les agents globaux, qui chargent les skills du langage.

| Dossier | Agent | Framework |
|---------|-------|-----------|
| `Agent/PHP/` | `laravel-implementer` | Laravel |
| `Agent/PHP/` | `symfony-implementer` | Symfony |
| `Agent/Java/` | `spring-boot-implementer` | Spring Boot |
| `Agent/TypeScript/` | `angular-implementer` | Angular |
| `Agent/TypeScript/` | `nextjs-implementer` | Next.js |
| `Agent/TypeScript/` | `expo-mobile-implementer` | React Native + Expo |

Les rôles détaillés des 21 agents sont rédigés dans `Agent/` (même arborescence que le futur dépôt).

**Point technique :** un agent Claude Code ne voit que son propre fichier. Les règles communes (« hérite de `implementer` ») devront donc être recopiées dans chaque agent framework lors de la publication dans le dépôt, idéalement par un petit script de génération pour ne les maintenir qu'à un seul endroit.

## 5. Skills

### 5.1 Skills globaux

| Domaine | Skills |
|---------|--------|
| Cadrage | `user-stories`, `acceptance-criteria` |
| Conception | `adr`, `api-design` (REST/GraphQL), `architecture-patterns` |
| Planification | `task-breakdown` |
| Code | `git-workflow` (branches, commits conventionnels, PR), `error-handling`, `logging` |
| Données | `db-schema-design`, `migrations`, `db-query-optimization` |
| Tests | `testing-strategy` |
| Qualité | `code-review-checklist`, `refactoring-patterns`, `debugging-method` |
| Sécurité | `owasp-checklist`, `env-secrets`, `dependency-audit` |
| Performance | `profiling`, `caching` |
| Docs | `project-docs-tracking` (suivi par projet, voir `docs/doc-suivi-projet.md`), `readme-template`, `api-docs`, `changelog-semver` |
| DevOps | `ci-github-actions`, `docker`, `deployment-checklist` |

### 5.2 Skills par langage et framework

| Dossier | Skills de langage | Skills de framework |
|---------|-------------------|---------------------|
| `Skills/PHP/` | `coding-conventions-php`, `testing-php`, `lint-format-php`, `security-php` | `laravel`, `symfony`, `upgrade-laravel`, `upgrade-symfony` |
| `Skills/Java/` | `coding-conventions-java`, `testing-java`, `lint-format-java`, `security-java` | `spring-boot`, `upgrade-spring-boot` |
| `Skills/TypeScript/` | `coding-conventions-typescript`, `testing-typescript`, `lint-format-typescript`, `security-typescript` | `react`, `angular`, `nextjs`, `expo`, `upgrade-angular`, `upgrade-nextjs`, `upgrade-expo` |

## 6. Structure proposée pour le dépôt

```
Agent/
  Global/
    product-analyst.md
    architect.md
    ...
  <Langage>/            ex. PHP/, JavaScript/, Python/
    laravel-implementer.md
Skills/
  Global/
    git-workflow/SKILL.md
    owasp-checklist/SKILL.md
    ...
  <Langage>/
    coding-conventions-php/SKILL.md
    testing-php/SKILL.md
README.md               catalogue + guide d'installation
```

Installation dans un projet : copier les agents voulus dans `.claude/agents/` et les skills dans `.claude/skills/` (un script d'installation pourra venir plus tard).

## 7. Décisions prises (2026-10-12)

1. Frameworks : Laravel, Symfony, Spring Boot, Angular, Next.js, React Native + Expo.
2. Outils cibles : Claude Code et Codex. Les skills utilisent le format `SKILL.md`, commun aux deux. Les agents sont rédigés au format Claude Code (Markdown + en-tête YAML) ; leur déclinaison Codex sera produite à l'installation (format à confirmer à ce moment-là).
3. L'`orchestrator` est conservé.
4. Tous les agents sont conservés, sans fusion.
5. Documentation de suivi par projet : voir `docs/doc-suivi-projet.md`.
