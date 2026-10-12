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
Skills/
  Global/        savoirs transverses (checklists, conventions, gabarits)
  PHP/ Java/ TypeScript/   savoirs propres à chaque langage et framework
scripts/
  sync-agents.py        recopie les principes dans chaque agent et génère Codex/
  validate-skills.py    vérifie la forme des skills et les skills cités par les agents
docs/
  catalogue.md          catalogue des agents et skills, principes et décisions
  doc-suivi-projet.md   documentation de suivi installée dans chaque projet
```

## État

- Agents : 25 rôles détaillés rédigés (en relecture), dont 3 agents de contrôle indépendants.
- Skills : socle rédigé (`autonomy-policy`, `repository-discovery`, `version-compatibility`, `change-impact-analysis`, `acceptance-criteria`, `task-breakdown`, `agent-handoff`, `testing-strategy`, `code-review-checklist`, `evidence-tracking`, `quality-gates`, `project-docs-tracking`, `skill-validation`) et les skills de design `design-inputs` et `design-fidelity-review` ; les autres à rédiger.

## Fonctionnement autonome

Les agents décident seuls de tout ce qui est réversible (choix par défaut, librairies selon des critères de licence, maintenance et compatibilité, réduction des régressions, arbitrage entre agents) et consignent chaque choix dans `docs/` (journal, ADR, hypothèses). Ils travaillent sur une branche, committent, poussent et ouvrent la PR sans demander. L'humain n'intervient que pour les actions réservées : fusion dans la branche principale, déploiement, données réelles, secrets, coûts, messages vers l'extérieur et choix légaux. Ces actions sont préparées et regroupées en un seul message « Décisions humaines requises ». Détails : règles 2 et 5 de `Agent/_commun/principes-communs.md` et skill `autonomy-policy`.

## Installation dans un projet

**Claude Code**
- Copier les fichiers de `Agent/*/` voulus dans `.claude/agents/` et les dossiers de skills (`Skills/*/<skill>/`) dans `.claude/skills/`.
- Chaque agent précharge ses skills (champ `skills`) ; un skill absent est ignoré avec un avertissement dans le journal de débogage.
- Pour une demande sur plusieurs phases, lancer la session avec `claude --agent orchestrator` : c'est lui qui lance les autres agents et présente le bilan et les décisions humaines requises.

**Codex**
- Copier `Codex/AGENTS.md` à la racine du projet, `Codex/agents/*.toml` dans `.codex/agents/` et les dossiers de skills dans `.agents/skills/`.
- La session principale applique la procédure de l'orchestrateur ; les agents de contrôle n'ont pas d'outil d'écriture dans Claude Code, mais dans Codex cette restriction repose sur leurs consignes.

## Modifier les agents ou les principes

- Principes : éditer `Agent/_commun/principes-communs.md` (tous les agents) ou `Agent/_commun/principes-code.md` (agents qui modifient du code, liste `CODE_AGENTS` du script).
- Puis lancer `python3 scripts/sync-agents.py`, qui met à jour les agents et régénère `Codex/`. L'option `--check` échoue si un fichier n'est pas synchronisé.

## Écrire un skill

Chaque skill suit le même contrat : Quand l'utiliser, Ce que l'agent rate sans ce skill, Entrées, Procédure, Livrable, Vérifications, Limites, En cas de blocage. Une règle reste dans les principes des agents ; le skill porte la méthode détaillée et cite la règle sans la réécrire. Avant de publier, appliquer le skill `skill-validation` et lancer `python3 scripts/validate-skills.py`.
