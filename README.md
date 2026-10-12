# Agent Prompt For Developper

Bibliothèque d'agents et de skills réutilisables pour le développement assisté par IA (vibe coding), compatibles Claude Code et Codex.

## Structure

```
Agent/
  Global/        agents par phase de développement, valables pour tous les langages
  PHP/           Laravel, Symfony
  Java/          Spring Boot
  TypeScript/    Angular, Next.js, React Native + Expo
  _commun/       principes partagés par tous les agents (source unique)
Skills/
  Global/        savoirs transverses (checklists, conventions, gabarits)
  PHP/ Java/ TypeScript/   savoirs propres à chaque langage et framework
scripts/
  sync-agents.py        recopie les principes communs dans chaque agent
docs/
  catalogue.md          catalogue des agents et skills, principes et décisions
  doc-suivi-projet.md   documentation de suivi installée dans chaque projet
```

## État

- Agents : 24 rôles détaillés rédigés (en relecture), dont 3 agents de contrôle indépendants.
- Skills : à rédiger.
- Installation dans un projet : à venir (copie dans `.claude/agents/` et `.claude/skills/` pour Claude Code ; déclinaison Codex à définir).

## Modifier les principes communs

Éditer `Agent/_commun/principes-communs.md`, puis lancer `python3 scripts/sync-agents.py`. L'option `--check` échoue si un agent n'est pas synchronisé.
