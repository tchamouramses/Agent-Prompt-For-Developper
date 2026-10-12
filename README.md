# Agent Prompt For Developper

Bibliothèque d'agents et de skills réutilisables pour le développement assisté par IA (vibe coding), compatibles Claude Code et Codex.

## Structure

```
Agent/
  Global/        agents par phase de développement, valables pour tous les langages
  PHP/           Laravel, Symfony
  Java/          Spring Boot
  TypeScript/    Angular, Next.js, React Native + Expo
  _commun/       principes partagés (source unique) : communs à tous, et code pour les agents qui modifient du code
Codex/           version Codex générée : AGENTS.md et agents/*.toml (ne pas modifier à la main)
Config/
  claude/        settings.json et hook qui bloquent techniquement les actions réservées
  codex/         config.toml et règles execpolicy équivalentes
Skills/
  Global/        savoirs transverses (checklists, conventions, gabarits)
  PHP/ Java/ TypeScript/   savoirs propres à chaque langage et framework
  PREVUS.md      skills cités mais pas encore rédigés
install.sh       installation en une commande sans clone, et commande agents-dev
scripts/
  install.py                     installe agents, skills et garde-fous dans un projet ou pour tous (--global)
  test-install.py                cas d'essai de l'installation
  sync-agents.py                 recopie les principes dans chaque agent et génère Codex/
  validate-skills.py             vérifie la forme des skills et les skills cités (--strict : tous rédigés)
  test-hook-actions-reservees.py cas d'essai du hook Claude Code
docs/
  catalogue.md          catalogue des agents et skills, principes et décisions
  doc-suivi-projet.md   documentation de suivi installée dans chaque projet
  essais/               comptes rendus des essais réels sur des projets jetables
```

## État

- Agents : 25 rôles détaillés rédigés (en relecture), dont 3 agents de contrôle indépendants.
- Skills : socle (`autonomy-policy`, `repository-discovery`, `version-compatibility`, `change-impact-analysis`, `acceptance-criteria`, `task-breakdown`, `agent-handoff`, `testing-strategy`, `code-review-checklist`, `evidence-tracking`, `quality-gates`, `project-docs-tracking`, `skill-validation`), skills transverses (produit et design, architecture et données, journalisation, erreurs, performance, sécurité des dépendances et des secrets, documentation, CI, Docker, déploiement), skills d'architecture (`coverage-check`, `monorepo`, `architecture-patterns`, `background-jobs-events`, `multi-tenancy`, `realtime`), et les skills des six stacks : PHP (`laravel`, `symfony`, `coding-conventions-php`, `testing-php`, `security-php`, `lint-format-php`, `upgrade-laravel`, `upgrade-symfony`), Java (`spring-boot`, `coding-conventions-java`, `testing-java`, `security-java`, `lint-format-java`, `upgrade-spring-boot`), TypeScript (`react`, `angular`, `nextjs`, `expo`, `coding-conventions-typescript`, `testing-typescript`, `security-typescript`, `lint-format-typescript`, `upgrade-angular`, `upgrade-nextjs`, `upgrade-expo`). `Skills/PREVUS.md` liste les skills cités mais pas encore rédigés (aucun aujourd'hui).
- Essai réel : Laravel, trois scénarios (fonctionnalité, bug, montée de version), voir `docs/essais/2026-10-12-laravel.md`. Les autres stacks sont à étendre sur le même modèle.

## Fonctionnement autonome

Les agents décident seuls de tout ce qui est réversible (choix par défaut, librairies selon des critères de licence, maintenance et compatibilité, réduction des régressions, arbitrage entre agents) et consignent chaque choix dans `docs/` (journal, ADR, hypothèses). Ils travaillent sur une branche, committent, poussent et ouvrent la PR sans demander. L'humain n'intervient que pour les actions réservées : fusion dans la branche principale, déploiement, données réelles, secrets, coûts, messages vers l'extérieur et choix légaux. Ces actions sont préparées et regroupées en un seul message « Décisions humaines requises ». Détails : règles 2 et 5 de `Agent/_commun/principes-communs.md` et skill `autonomy-policy`.

## Ce que la bibliothèque couvre

- Stacks avec agent dédié : Laravel, Symfony, Spring Boot, Angular, Next.js, React Native + Expo. Toute autre stack est traitée par `implementer` en mode dégradé (documentation officielle de la version installée, contrôles du profil livraison), et le manque est consigné dans `docs/PROJECT.md` (skill `coverage-check`).
- Architectures : application unique ou monorepo (`monorepo`), couches du framework, monolithe modulaire, hexagonale, Clean Architecture, DDD tactique, CQRS (`architecture-patterns`), traitements asynchrones et événements (`background-jobs-events`), multi-tenant (`multi-tenancy`), temps réel (`realtime`).
- Hors périmètre pour l'instant : services séparés à grande échelle (au-delà des critères de `architecture-patterns`), serverless et infrastructure décrite en code, pipelines de données et applications d'IA, librairies publiées, outils en ligne de commande, applications de bureau et extensions de navigateur. Ils sont traités en mode dégradé.

## Installation

**Une seule fois sur la machine** (sans cloner ; Python 3.9+ et curl requis) :

```
curl -fsSL https://raw.githubusercontent.com/tchamouramses/Agent-Prompt-For-Developper/main/install.sh | sh
```

La bibliothèque est téléchargée dans `~/.local/share/agents-dev` et la commande `agents-dev` dans `~/.local/bin`.

**Dans un projet**, depuis sa racine :

```
agents-dev                          # stacks et outils détectés
agents-dev --stack laravel,nextjs   # stacks imposées (laravel, symfony, spring-boot, angular, nextjs, expo, toutes, aucune)
agents-dev --langage typescript     # stacks d'un langage : php (Laravel, Symfony), java (Spring Boot), typescript (Angular, Next.js, Expo)
agents-dev --outil codex            # claude, codex ou les-deux ; par défaut, les outils trouvés dans le PATH
agents-dev --desinstaller           # retire ce que la commande a installé
```

**Pour tous les projets** : `agents-dev --global` installe toutes les stacks dans `~/.claude/` (agents, skills, hook, réglages fusionnés) et pour Codex dans `~/.codex/` (bloc `AGENTS.md`, agents, règles) et `~/.agents/skills/`. Le `~/.codex/config.toml` de l'utilisateur n'est pas modifié. Une installation dans un projet reste prioritaire sur l'installation globale.

**Mise à jour** : `agents-dev maj` télécharge la dernière version et met à jour l'installation globale ; relancer `agents-dev` sans option dans un projet le met à jour avec les mêmes stacks et outils.

Détection : `composer.json` (Laravel, Symfony), `pom.xml` ou `build.gradle` (Spring Boot), `package.json` (Angular, Next.js, Expo), à la racine et jusqu'à deux niveaux de sous-dossiers (`apps/web`). Un langage hors liste (Go, Python, .NET…) est signalé et reçoit les agents génériques. Les fichiers installés sont listés dans `.bibliotheque-agents.json` : la relance remplace ces fichiers et retire ceux devenus inutiles, mais ne remplace jamais un fichier du projet sans `--force`. `.claude/settings.json` est fusionné, les instructions Codex vont dans `AGENTS.md` entre marqueurs, et la commande liste les skills cités qui ne sont pas encore rédigés.

Depuis un clone, la même commande est `python3 scripts/install.py [dossier] [options]`.

Installation manuelle :

**Claude Code**
- Copier les fichiers de `Agent/*/` voulus dans `.claude/agents/` et les dossiers de skills (`Skills/*/<skill>/`) dans `.claude/skills/`.
- Fusionner `Config/claude/settings.json` dans `.claude/settings.json` et copier `Config/claude/hooks/actions-reservees.py` dans `.claude/hooks/` (Python 3 requis). Le hook bloque push vers la branche principale ou forcé, fusion, déploiement, base destructrice hors test, lecture des secrets, et toute écriture hors de `/tmp` par les agents de contrôle.
- Chaque agent précharge ses skills (champ `skills`) ; un skill absent est ignoré avec un avertissement dans le journal de débogage.
- Pour une demande sur plusieurs phases, lancer la session avec `claude --agent orchestrator` : c'est lui qui lance les autres agents et présente le bilan et les décisions humaines requises.

**Codex**
- Copier `Codex/AGENTS.md` à la racine du projet, `Codex/agents/*.toml` dans `.codex/agents/` et les dossiers de skills dans `.agents/skills/`.
- Copier `Config/codex/config.toml` dans `.codex/config.toml` et `Config/codex/rules/` dans `.codex/rules/` ; Codex les charge quand le projet est approuvé. Vérifier une règle : `codex execpolicy check --rules .codex/rules/actions-reservees.rules -- git push origin main`.
- La session principale applique la procédure de l'orchestrateur ; les agents de contrôle n'ont pas d'outil d'écriture dans Claude Code, mais dans Codex cette restriction repose sur leurs consignes.

## Modifier les agents ou les principes

- Principes : éditer `Agent/_commun/principes-communs.md` (tous les agents) ou `Agent/_commun/principes-code.md` (agents qui modifient du code, liste `CODE_AGENTS` du script).
- Puis lancer `python3 scripts/sync-agents.py`, qui met à jour les agents et régénère `Codex/`. L'option `--check` échoue si un fichier n'est pas synchronisé. La CI (`.github/workflows/verifier.yml`) lance `sync-agents.py --check`, `validate-skills.py` et les cas d'essai du hook sur chaque PR.

## Écrire un skill

Chaque skill suit le même contrat : Quand l'utiliser, Ce que l'agent rate sans ce skill, Entrées, Procédure, Livrable, Vérifications, Limites, En cas de blocage. Une règle reste dans les principes des agents ; le skill porte la méthode détaillée et cite la règle sans la réécrire. Avant de publier, appliquer le skill `skill-validation`, lancer `python3 scripts/validate-skills.py` et retirer le skill de `Skills/PREVUS.md`.
