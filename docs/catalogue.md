# Catalogue des agents et skills (v0.5)

> Brouillon à valider.
> Date : 2026-10-12

## 1. Principes de conception

1. **Un agent = un rôle, une phase.** Chaque agent a une mission étroite, des entrées et sorties claires, et une liste explicite de ce qu'il ne fait pas. C'est ce qui le rend fiable en vibe coding.
2. **Les agents portent le comportement, les skills portent le savoir.** Un agent dit *comment travailler* (méthode, limites, format de sortie). Un skill apporte une *connaissance réutilisable* (checklist, convention, template, savoir propre à un langage).
3. **Global d'abord, spécifique ensuite.** La plupart des agents sont globaux. La spécialisation par langage passe surtout par des skills de langage que l'agent global charge. On ne crée un agent spécifique à un langage que si sa méthode de travail change vraiment (ex. un intégrateur mobile Flutter).
4. **Le moins de droits possible.** Les agents de contrôle (revue, sécurité, gatekeeper) n'ont aucun outil d'écriture : ils rendent leur rapport, que l'orchestrateur enregistre dans `docs/`. Les agents qui écrivent du code ne touchent qu'à leur périmètre.
5. **L'humain garde la main sur l'irréversible.** Aucun agent ne déploie, ne supprime de données, ne pousse sur la branche principale ou n'ajoute de dépendance sans validation.
6. **Produire et contrôler sont séparés.** L'agent qui produit ne valide jamais son propre travail. Des agents de contrôle indépendants vérifient, et `quality-gatekeeper` autorise ou refuse la livraison sur preuves.
7. **Aucune affirmation sans preuve.** Un test, un build ou un parcours n'est « réussi » que si la commande a été exécutée et son résultat cité.

## 2. Phases couvertes

| # | Phase | Agent principal |
|---|-------|-----------------|
| 1 | Cadrage du besoin | `product-analyst` |
| 1b | Expérience utilisateur et design | `ui-ux-designer` |
| 2 | Architecture et conception | `architect` |
| 3 | Planification | `planner` |
| 4 | Initialisation du projet | `scaffolder` |
| 5 | Implémentation | `implementer` |
| 6 | Données et base de données | `data-modeler` |
| 7 | Tests (dont contrats d'API) | `test-engineer` |
| 7b | Validation de bout en bout | `e2e-validator` |
| 8 | Revue de code | `code-reviewer` |
| 9 | Débogage et incidents | `debugger` |
| 10 | Sécurité | `security-auditor` |
| 11 | Performance | `performance-optimizer` |
| 12 | Refactoring et migration | `refactorer` |
| 13 | Documentation | `doc-writer` |
| 14 | CI/CD, versions et déploiement | `devops-engineer` |
| 15 | Autorisation de livraison | `quality-gatekeeper` |
| conditionnelle | Référencement (sites publics) | `seo-specialist` |
| transverse | Coordination | `orchestrator` |

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
- **Ne fait pas :** ne code pas lui-même. Choisit un profil : **léger** (implémentation + revue, validation au début et à la fin) ou **livraison** (contrôle indépendant complet, validation entre chaque phase).
- **Fait aussi :** relaie à l'utilisateur les questions des agents, qui ne peuvent pas lui parler directement, et enregistre les rapports des agents de contrôle.

### 3.16 `ui-ux-designer` (Expérience utilisateur)
- **Mission :** parcours, architecture de l'information, maquettes, états d'écran, design system, accessibilité.
- **Ne fait pas :** ne code pas l'application ; propose les librairies de composants sans les imposer.
- **Skills :** `ux-patterns`, `design-system`, `accessibility`.

### 3.17 `e2e-validator` (Validation de bout en bout) — indépendant
- **Mission :** utiliser l'application comme un vrai utilisateur (Playwright, Maestro ou Detox), vérifier les critères d'acceptation et l'intégration réelle front / back, fournir des preuves.
- **Ne fait pas :** ne modifie pas le code de l'application ; ne valide jamais par simple lecture du code.
- **Skills :** `e2e-testing`, `api-contracts`, `acceptance-criteria`.

### 3.18 `quality-gatekeeper` (Autorisation de livraison) — indépendant
- **Mission :** confronter chaque exigence aux preuves, ré-exécuter les contrôles clés, appliquer les règles bloquantes, rendre un verdict et produire le rapport de livraison lu par l'utilisateur à la place du code.
- **Ne fait pas :** ne code pas, ne corrige pas, n'accepte aucune affirmation sans preuve.
- **Skills :** `quality-gates`, `acceptance-criteria`.

### 3.19 `seo-specialist` (Référencement) — sites publics uniquement
- **Mission :** mots-clés, architecture des pages, exigences SEO par page avant le développement ; audit technique, performance et contenus avant la livraison.
- **Ne fait pas :** ne modifie pas le code ; aucune technique contraire aux consignes des moteurs ; aucun outil payant sans accord.
- **Skills :** `seo-technique`, `accessibility`.

### 3.20 Responsabilités intégrées aux agents existants
| Responsabilité proposée | Intégrée dans | Comment |
|-------------------------|---------------|---------|
| Acceptation produit | `quality-gatekeeper` + `e2e-validator` | matrice critère → test → parcours → preuve |
| Intégration front / back | `test-engineer` + `e2e-validator` | tests de contrats d'API, vérification des appels réels |
| Gestion des versions | `devops-engineer` | CI bloquante, staging, sauvegarde, liste de déploiement, retour arrière |
| Réponse aux incidents | `debugger` (mode incident) | qualification, limitation de l'impact, analyse après coup |
| Maintenance des dépendances | `security-auditor` + `refactorer` | audit et versions obsolètes, puis mise à jour après accord ; à lancer en routine périodique |

### 3.21 Agents reportés (à créer selon le projet)
- `sre-observability` : utile quand un projet est en production avec des outils de supervision accessibles.
- `ai-engineer` : utile pour un projet avec des fonctionnalités IA (LLM, RAG, embeddings).
- `product-analytics` : utile quand des données d'usage réelles sont disponibles.

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

Les rôles détaillés des 25 agents sont dans `Agent/`.

**Principes partagés :** un agent ne voit que son propre fichier. Les règles partagées sont maintenues à un seul endroit et recopiées dans chaque agent par `python3 scripts/sync-agents.py`. Ne jamais modifier une section générée directement dans un agent.
- `Agent/_commun/principes-communs.md`, pour tous : posture senior, façon de poser une question (un sous-agent la renvoie dans son compte rendu), preuves et contrôle indépendant, choix des librairies validés par l'utilisateur, actions interdites, fichiers et skills absents, compte rendu avec exemple, suivi documentaire.
- `Agent/_commun/principes-code.md`, pour les agents qui modifient du code : qualité du code, SOLID dès que c'est possible, zéro code mort, gestion des régressions.

**Modèles :** `opus` pour `architect`, `security-auditor` et `quality-gatekeeper` ; `sonnet` pour `planner` et `doc-writer` ; les autres héritent du modèle de la session.

## 5. Skills

### 5.1 Skills globaux

| Domaine | Skills |
|---------|--------|
| Cadrage | `user-stories`, `acceptance-criteria` |
| Conception | `adr`, `api-design` (REST/GraphQL), `architecture-patterns` |
| Planification | `task-breakdown` |
| Code | `git-workflow` (branches, commits conventionnels, PR), `error-handling`, `logging` |
| Données | `db-schema-design`, `migrations`, `db-query-optimization` |
| Tests | `testing-strategy`, `api-contracts`, `e2e-testing` |
| Expérience utilisateur | `design-inputs` (lire images, captures, croquis, PDF, HTML, URL, Figma et autres sources ; comparer le rendu à la maquette), `ux-patterns`, `design-system`, `accessibility` |
| Référencement | `seo-technique` (rendu serveur, sitemap, robots, canoniques, données structurées, Open Graph, hreflang, Core Web Vitals) |
| Qualité | `code-review-checklist`, `refactoring-patterns`, `debugging-method`, `quality-gates` (règles bloquantes, rapport de livraison) |
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

Installation dans un projet : voir le README (Claude Code : `.claude/agents/` et `.claude/skills/` ; Codex : `AGENTS.md`, `.codex/agents/` et `.agents/skills/`).

## 7. Décisions prises (2026-10-12)

1. Frameworks : Laravel, Symfony, Spring Boot, Angular, Next.js, React Native + Expo.
2. Outils cibles : Claude Code et Codex. Les skills utilisent le format `SKILL.md`, commun aux deux. Les agents sont rédigés au format Claude Code (Markdown + en-tête YAML) ; `scripts/sync-agents.py` en génère la version Codex (`Codex/agents/*.toml` et `Codex/AGENTS.md`).
3. L'`orchestrator` est conservé.
4. Tous les agents sont conservés, sans fusion.
5. Documentation de suivi par projet : voir `docs/doc-suivi-projet.md`.
6. Tous les agents se comportent en seniors : code lisible, sans répétition ni code mort ; risque de régression évalué avant chaque modification, avec question à l'utilisateur en cas de doute ; aucune librairie installée sans que l'utilisateur ait choisi parmi des options proposées.
7. Équipe « version resserrée » : ajout de `ui-ux-designer`, `e2e-validator` et `quality-gatekeeper` ; les autres responsabilités proposées sont intégrées aux agents existants ou reportées (sections 3.20 et 3.21).
8. Ajout de `seo-specialist`, activé pour les sites publics, et du skill `seo-technique` chargé par les agents Next.js et Angular.
9. Corrections issues de la revue des prompts : l'orchestrateur peut lancer les agents (outil `Agent`), les sous-agents renvoient leurs questions au lieu d'attendre une réponse, les skills sont déclarés dans l'en-tête, les principes sont scindés (communs et code), les agents de contrôle sont sans outil d'écriture, deux profils de parcours (léger et livraison), génération Codex, exemples, modèles et règle sur les fichiers absents.
10. Les agents qui modifient du code appliquent SOLID dès que c'est possible ; `code-reviewer` le vérifie.
11. Sources visuelles : `ui-ux-designer` a un mode « partir de l'existant » ; les agents qui touchent une interface lisent la spécification d'écran et comparent le rendu à la source ; `e2e-validator` rapporte les écarts avec le design. Le savoir est dans le skill `design-inputs`. Ces agents héritent des outils de la session (dont les outils MCP Figma ou navigateur) sauf `Agent`.
