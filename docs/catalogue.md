# Catalogue des agents et skills (v0.8)

> Brouillon à valider.
> Date : 2026-10-12

## 1. Principes de conception

1. **Un agent = un rôle, une phase.** Chaque agent a une mission étroite, des entrées et sorties claires, et une liste explicite de ce qu'il ne fait pas. C'est ce qui le rend fiable en vibe coding.
2. **Les agents portent le comportement, les skills portent le savoir.** Un agent dit *comment travailler* (méthode, limites, format de sortie). Un skill apporte une *connaissance réutilisable* (checklist, convention, template, savoir propre à un langage).
3. **Global d'abord, spécifique ensuite.** L'outil se veut général dans un premier temps, spécifique par langage dans un second temps. Tout savoir nouveau est d'abord écrit dans un skill global (méthode valable pour tous les langages), puis traduit dans les skills de langage et de framework, qui renvoient au skill global au lieu de le répéter. La plupart des agents sont globaux. La spécialisation par langage passe surtout par des skills de langage que l'agent global charge. On ne crée un agent spécifique à un langage que si sa méthode de travail change vraiment (ex. un intégrateur mobile Flutter).
4. **Le moins de droits possible.** Les agents de contrôle (revue, sécurité, gatekeeper) n'ont aucun outil d'écriture : ils rendent leur rapport, que l'orchestrateur enregistre dans `docs/`. Les agents qui écrivent du code ne touchent qu'à leur périmètre.
5. **Autonomie par défaut, l'humain pour l'irréversible.** Les agents décident seuls de ce qui est réversible (librairies selon des critères, choix par défaut, réduction des régressions, arbitrage entre agents) et consignent leurs choix. Seules les actions réservées attendent un humain : fusion dans la branche principale, déploiement, données réelles, secrets, coûts, messages externes, choix légaux. Elles sont préparées pour qu'il n'ait qu'à accepter, et regroupées en un seul message.
6. **Produire et contrôler sont séparés.** L'agent qui produit ne valide jamais son propre travail. Des agents de contrôle indépendants vérifient, et `quality-gatekeeper` autorise ou refuse la livraison sur preuves.
7. **Aucune affirmation sans preuve.** Un test, un build ou un parcours n'est « réussi » que si la commande a été exécutée et son résultat cité.
8. **Générique.** Aucun agent ni skill ne cite un produit particulier : les exemples sont neutres et valent pour tout projet.

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
- **Entrées / Sorties :** idée, notes, échanges → `docs/spec.md` (contexte, utilisateurs, user stories, critères d'acceptation, hors périmètre, hypothèses).
- **Fait :** tranche les zones floues par des hypothèses explicites, reformule, priorise (MoSCoW), identifie les cas limites.
- **Ne fait pas :** pas de code, pas de choix technique, pas d'estimation de délais.
- **Outils :** lecture, écriture de fichiers `docs/` uniquement.
- **Skills :** `user-stories`, `acceptance-criteria`.

### 3.2 `architect` (Conception)
- **Mission :** choisir la stack et définir la structure du système.
- **Entrées / Sorties :** `spec.md` → `docs/architecture.md` (stack, modules, flux, modèle de données haut niveau) + ADR pour chaque décision importante.
- **Fait :** compare 2–3 options avec avantages et inconvénients, tranche et consigne en ADR, anticipe sécurité et scalabilité à la bonne échelle.
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
- **Ne fait pas :** ne change pas l'architecture, n'ajoute pas de dépendance hors des critères de choix, ne traite pas de tâche hors plan, ne fusionne pas dans la branche principale.
- **Skills :** `coding-conventions-<langage>`, `git-workflow`, `error-handling`, `logging`.

### 3.6 `data-modeler` (Données)
- **Mission :** concevoir le schéma, les migrations et les requêtes.
- **Fait :** normalisation adaptée, index, contraintes, migrations réversibles, seeds.
- **Ne fait pas :** n'exécute jamais une migration sur une base de production ; ne supprime ni ne transforme de façon irréversible des données réelles sans accord humain.
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
- **Ne fait pas :** ne déploie jamais en production et ne touche pas aux secrets réels ; il prépare ces actions pour l'humain.
- **Skills :** `ci-github-actions`, `docker`, `env-secrets`, `deployment-checklist`.

### 3.15 `orchestrator` (optionnel)
- **Mission :** recevoir une demande, choisir le bon agent et enchaîner les phases (spec → plan → implémentation → tests → revue).
- **Ne fait pas :** ne code pas lui-même. Choisit un profil : **léger** (implémentation + revue) ou **livraison** (contrôle indépendant complet) ; les deux s'enchaînent sans validation humaine entre les phases.
- **Fait aussi :** tranche les blocages avec les agents arbitres, regroupe les rares décisions humaines en un seul message et enregistre les rapports des agents de contrôle.

### 3.16 `ui-ux-designer` (Expérience utilisateur)
- **Mission :** parcours, architecture de l'information, maquettes, états d'écran, design system, accessibilité.
- **Ne fait pas :** ne code pas l'application ; aucune librairie de composants payante ou sous licence restrictive sans accord humain.
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
- **Ne fait pas :** ne modifie pas le code ; aucune technique contraire aux consignes des moteurs ; aucun outil payant sans accord humain.
- **Skills :** `seo-technique`, `accessibility`.

### 3.20 Responsabilités intégrées aux agents existants
| Responsabilité proposée | Intégrée dans | Comment |
|-------------------------|---------------|---------|
| Acceptation produit | `quality-gatekeeper` + `e2e-validator` | matrice critère → test → parcours → preuve |
| Intégration front / back | `test-engineer` + `e2e-validator` | tests de contrats d'API, vérification des appels réels |
| Gestion des versions | `devops-engineer` | CI bloquante, staging, sauvegarde, liste de déploiement, retour arrière |
| Réponse aux incidents | `debugger` (mode incident) | qualification, limitation de l'impact, analyse après coup |
| Maintenance des dépendances | `security-auditor` + `refactorer` | audit et versions obsolètes, puis mise à jour sur une branche de travail protégée par les tests ; à lancer en routine périodique |

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
- `Agent/_commun/principes-communs.md`, pour tous : posture senior, autonomie et escalade (l'agent décide, consigne et ne remonte que les actions réservées ; un sous-agent les renvoie dans son compte rendu), preuves et contrôle indépendant, choix des librairies selon des critères, actions réservées à l'humain, fichiers et skills absents, compte rendu avec exemple, suivi documentaire.
- `Agent/_commun/principes-code.md`, pour les agents qui modifient du code : qualité du code, SOLID dès que c'est possible, zéro code mort, régressions évaluées et réduites par l'agent lui-même.

**Modèles :** `opus` pour `architect`, `security-auditor` et `quality-gatekeeper` ; `sonnet` pour `planner` et `doc-writer` ; les autres héritent du modèle de la session.

## 5. Skills

### 5.1 Skills globaux

| Domaine | Skills |
|---------|--------|
| Socle | `autonomy-policy`, `repository-discovery`, `version-compatibility`, `change-impact-analysis`, `agent-handoff`, `evidence-tracking`, `skill-validation` |
| Cadrage | `user-stories`, `acceptance-criteria` |
| Socle (couverture) | `coverage-check` (stacks et architectures couvertes, mode dégradé sinon) |
| Conception | `adr`, `api-design` (REST/GraphQL), `architecture-patterns` (couches, monolithe modulaire, hexagonale, Clean, DDD, CQRS, services séparés), `monorepo`, `background-jobs-events`, `multi-tenancy`, `realtime` |
| Planification | `task-breakdown` |
| Code | `git-workflow` (branches, commits conventionnels, PR), `error-handling`, `logging` |
| Données | `db-schema-design`, `migrations`, `db-query-optimization`, `concurrency-control` (règle d'exclusivité sous accès simultanés, moteur réel, test de concurrence réelle) |
| Tests | `testing-strategy`, `api-contracts`, `e2e-testing` |
| Expérience utilisateur | `design-inputs` (lire images, captures, croquis, PDF, HTML, URL, Figma et autres sources, en tirer les spécifications d'écran), `design-fidelity-review` (comparer le rendu à la référence, classer les écarts, vérifier les corrections), `ux-patterns`, `design-system`, `accessibility` |
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
6. Tous les agents se comportent en seniors : code lisible, sans répétition ni code mort ; risque de régression évalué et réduit avant chaque modification. (La version initiale prévoyait une question à l'utilisateur en cas de doute et un choix des librairies par l'utilisateur ; remplacée par la décision 14.)
7. Équipe « version resserrée » : ajout de `ui-ux-designer`, `e2e-validator` et `quality-gatekeeper` ; les autres responsabilités proposées sont intégrées aux agents existants ou reportées (sections 3.20 et 3.21).
8. Ajout de `seo-specialist`, activé pour les sites publics, et du skill `seo-technique` chargé par les agents Next.js et Angular.
9. Corrections issues de la revue des prompts : l'orchestrateur peut lancer les agents (outil `Agent`), les sous-agents renvoient leurs demandes de décision au lieu d'attendre une réponse, les skills sont déclarés dans l'en-tête, les principes sont scindés (communs et code), les agents de contrôle sont sans outil d'écriture, deux profils de parcours (léger et livraison), génération Codex, exemples, modèles et règle sur les fichiers absents.
10. Les agents qui modifient du code appliquent SOLID dès que c'est possible ; `code-reviewer` le vérifie.
11. Sources visuelles : `ui-ux-designer` a un mode « partir de l'existant » ; les agents qui touchent une interface lisent la spécification d'écran et comparent le rendu à la source ; `e2e-validator` rapporte les écarts avec le design. Le savoir est dans le skill `design-inputs`. Ces agents héritent des outils de la session (dont les outils MCP Figma ou navigateur) sauf `Agent`.
12. Skills du socle rédigés (12) avec un contrat commun vérifié par `scripts/validate-skills.py`. Les principes gardent la règle courte et renvoient au skill pour la méthode.
13. Sources visuelles : deux skills plutôt que cinq, `design-inputs` (lecture de toute source) et `design-fidelity-review` (comparaison du rendu). La transformation en code reste dans les principes des agents et les skills de framework.
14. Autonomie et généricité : les agents décident seuls de tout ce qui est réversible, consignent chaque choix (journal, ADR, hypothèses H-xx) et ne sollicitent l'humain que pour les actions réservées, préparées et regroupées en un message. Le skill `autonomy-policy` porte la méthode (niveaux de décision, défaut quand une information manque, arbitrage, critères de choix d'une librairie). Le dépôt ne cite aucun produit particulier.
15. Garde-fous techniques : les actions réservées sont aussi bloquées par l'outil (hook et permissions Claude Code dans `Config/claude/`, règles execpolicy Codex dans `Config/codex/`), les agents de contrôle ne peuvent écrire que dans `/tmp`. CI de vérification sur chaque PR, installateur `scripts/install.py`, skills prévus listés dans `Skills/PREVUS.md`.
16. Essai réel sur Laravel (voir `docs/essais/2026-10-12-laravel.md`) : profil léger pour un changement localisé même en zone sensible (avec `security-auditor`), bug toujours confié à `debugger`, au plus deux passes par agent de contrôle, défauts préexistants et outils absents traités en réserve, demandes humaines filtrées sur la règle 5, commits au fil des tâches. Les autres stacks s'étendent sur le modèle Laravel, avec leur propre essai.
17. Architectures (2026-10-12) : le système reconnaît ce qu'il ne couvre pas. `coverage-check` (appliqué par `orchestrator`, `architect` et `repository-discovery`) consigne la couverture dans `docs/PROJECT.md` et fait passer toute partie non couverte par `implementer` en mode dégradé, avec les contrôles du profil livraison. Monorepo : un seul `docs/` à la racine, carte des applications, une tâche par application, contrats changés dans l'ordre producteur rétrocompatible puis consommateurs. Skills transverses ajoutés : `architecture-patterns`, `background-jobs-events`, `multi-tenancy`, `realtime`.
18. Stacks (2026-10-12) : les six stacks ont leurs skills de framework, de langage (conventions, tests, sécurité, lint et formatage) et de montée de version, sur le modèle Laravel. Un skill de framework cite ses skills de lint et de montée de version pour qu'ils soient installés avec lui. L'essai réel reste à faire pour Symfony, Spring Boot, Angular, Next.js et Expo.
19. Comparaison avec Superpowers (2026-10-12, voir `docs/essais/2026-10-12-comparatif-superpowers.md`) : même fonctionnalité Angular + Laravel, même résultat fonctionnel, plus de garanties mais un coût 9 fois plus élevé. Suites données, d'abord en global puis par langage (principe 3) : skill global `concurrency-control` traduit dans `laravel`, `symfony`, `spring-boot`, `nextjs`, `testing-php` et `testing-java` ; `e2e-validator` obligatoire dès qu'une interface est touchée et règle de concurrence réelle bloquante pour `quality-gatekeeper` ; coût réduit (tâches regroupées par brief, contrôle accepté non relancé hors de sa zone, petite fonctionnalité d'une seule application en profil léger, `quality-gatekeeper` sur Sonnet). L'autorisation automatique des commandes de développement à l'installation attend l'accord explicite du propriétaire.
