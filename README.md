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
scripts/
  install.py                     installe agents, skills et garde-fous dans un projet
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
- Skills : socle rédigé (`autonomy-policy`, `repository-discovery`, `version-compatibility`, `change-impact-analysis`, `acceptance-criteria`, `task-breakdown`, `agent-handoff`, `testing-strategy`, `code-review-checklist`, `evidence-tracking`, `quality-gates`, `project-docs-tracking`, `skill-validation`), skills de design `design-inputs` et `design-fidelity-review`, `migrations`, `git-workflow`, `debugging-method`, `owasp-checklist`, `e2e-testing`, `api-contracts`, et la stack Laravel complète (`laravel`, `testing-php`, `security-php`, `coding-conventions-php`). Les skills restants sont listés dans `Skills/PREVUS.md`.
- Essai réel : Laravel, trois scénarios (fonctionnalité, bug, montée de version), voir `docs/essais/2026-10-12-laravel.md`. Les autres stacks sont à étendre sur le même modèle.

## Fonctionnement autonome

Les agents décident seuls de tout ce qui est réversible (choix par défaut, librairies selon des critères de licence, maintenance et compatibilité, réduction des régressions, arbitrage entre agents) et consignent chaque choix dans `docs/` (journal, ADR, hypothèses). Ils travaillent sur une branche, committent, poussent et ouvrent la PR sans demander. L'humain n'intervient que pour les actions réservées : fusion dans la branche principale, déploiement, données réelles, secrets, coûts, messages vers l'extérieur et choix légaux. Ces actions sont préparées et regroupées en un seul message « Décisions humaines requises ». Détails : règles 2 et 5 de `Agent/_commun/principes-communs.md` et skill `autonomy-policy`.

## Installation dans un projet

```
python3 scripts/install.py <dossier-du-projet> --stack laravel --outil claude   # ou codex, les-deux
```

Le script installe les agents globaux et ceux des stacks choisies, tous les skills rédigés qu'ils citent, et les garde-fous. Il ne remplace aucun fichier existant sans `--force`, fusionne `.claude/settings.json`, ajoute ses instructions Codex dans `AGENTS.md` entre marqueurs, et liste les skills cités qui ne sont pas encore rédigés. Installation manuelle :

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
