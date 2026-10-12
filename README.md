# Agent Prompt For Developper

Bibliothèque d'agents et de skills réutilisables pour le développement assisté par IA (vibe coding), compatibles Claude Code et Codex.

## Structure

```
Agent/
  Global/        agents par phase de développement, valables pour tous les langages
  PHP/           Laravel, Symfony
  Java/          Spring Boot
  TypeScript/    Angular, Next.js, React Native + Expo
Skills/
  Global/        savoirs transverses (checklists, conventions, gabarits)
  PHP/ Java/ TypeScript/   savoirs propres à chaque langage et framework
docs/
  catalogue.md          catalogue des agents et skills, principes et décisions
  doc-suivi-projet.md   documentation de suivi installée dans chaque projet
```

## État

- Agents : rôles rédigés (brouillon, en relecture).
- Skills : à rédiger.
- Installation dans un projet : à venir (copie dans `.claude/agents/` et `.claude/skills/` pour Claude Code ; déclinaison Codex à définir).
