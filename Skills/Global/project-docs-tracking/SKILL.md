---
name: project-docs-tracking
description: Tenue de la documentation de suivi du projet dans docs/ (journal, CHANGELOG, plan, PROJECT.md). À appliquer en fin de chaque tâche qui modifie le projet, et au début d'une session pour savoir où en est le projet.
---

# Suivi documentaire du projet

Le dossier `docs/` est la mémoire du projet. Une nouvelle session ou un nouvel agent doit pouvoir lire `docs/PROJECT.md` et les dernières entrées de `docs/journal/` et savoir immédiatement où en est le projet, sans relire le code. La règle est dans les principes communs (« Suivi documentaire ») ; ce skill donne la procédure et les gabarits.

## Quand l'utiliser
- Au début d'une tâche, pour savoir où en est le projet.
- En fin de chaque tâche qui modifie le projet.
- `scaffolder`, `doc-writer`, `orchestrator` : initialiser `docs/` sur un projet qui n'en a pas.

## Ce que l'agent rate sans ce skill
- Il oublie le journal, ou écrit une entrée vague (« corrections diverses ») inutile à la session suivante.
- Il réécrit ou supprime des entrées passées.
- Il met dans le CHANGELOG des détails internes (refactoring, tests) au lieu des changements visibles.
- Il marque une tâche « terminée » sans preuve de son critère.

## Entrées
- `docs/` du projet, la tâche réalisée et son compte rendu.

## Procédure

### Au début d'une tâche
1. Lis `docs/PROJECT.md` (état actuel, décisions clés, dette et risques).
2. Lis les 5 dernières entrées de `docs/journal/` (tri par nom de fichier, qui commence par la date).
3. Si ta tâche vient de `docs/plan.md`, lis sa ligne : identifiant, critère « terminé », dépendances, risque.

Si `docs/` n'existe pas, ne crée pas l'arborescence de ta propre initiative : signale-le dans ton compte rendu. Seuls `scaffolder` (nouveau projet), `doc-writer` et `orchestrator` la créent, à partir des gabarits ci-dessous.

### En fin de tâche

#### 1. Entrée de journal (toujours, si tu as modifié quelque chose)
Fichier `docs/journal/AAAA-MM-JJ-<sujet-court>.md`. Si le fichier existe déjà pour ce sujet et cette date, ajoute une section ; ne réécris ni ne supprime jamais une entrée existante.

```markdown
# AAAA-MM-JJ · <Titre lisible>
- Agent : <nom de l'agent>
- Application : <chemin, si le dépôt en contient plusieurs>
- Tâche : plan.md#<Tx> (ou « hors plan : <demande> »)
- Fait : <ce qui a changé, en une à trois lignes>
- Fichiers : <chemins principaux>
- Décisions : <choix et hypothèses, par qui, raison et façon d'annuler ; « aucune » sinon>
- Vérifications : <commandes et résultats exacts ; ce qui n'a pas été vérifié>
- Reste à faire / risques : <…>
```

Si tu n'as pas d'outil d'écriture (agent de contrôle), mets cette entrée à la fin de ton compte rendu ; l'agent qui t'a lancé l'enregistre.

#### 2. CHANGELOG (si le comportement visible change)
Ajoute une ligne dans `docs/CHANGELOG.md`, section `## [Unreleased]`, sous la bonne rubrique (format Keep a Changelog) :
- `Added` : nouvelle fonctionnalité ;
- `Changed` : comportement modifié ;
- `Fixed` : bug corrigé ;
- `Removed` : fonctionnalité retirée ;
- `Security` : correction de sécurité ;
- `Deprecated` : fonctionnalité appelée à disparaître.

Une ligne = une phrase compréhensible par un utilisateur du produit, suivie de la référence (`(T4)`, `(US-03)`). Dans un dépôt à plusieurs applications visibles, la ligne commence par l'application (« Web : … »). Pas de ligne pour un refactoring sans effet visible, des tests seuls ou de la documentation interne.

#### 3. Plan (si la tâche vient du plan)
Dans `docs/plan.md`, mets à jour le statut de la tâche : `à faire` → `en cours` → `terminée` (ou `bloquée : <raison>`). Une tâche n'est `terminée` que si son critère « terminé » est prouvé.

#### 4. PROJECT.md (seulement `doc-writer`, ou l'agent que l'utilisateur désigne)
Les autres agents ne modifient pas `docs/PROJECT.md` : ils signalent dans leur compte rendu ce qui devrait y changer (nouvelle décision, nouveau risque, fonctionnalité livrée).

### Gabarits pour initialiser `docs/`

Un seul `docs/` à la racine du dépôt, même s'il contient plusieurs applications (skill `monorepo`).

```
docs/
  PROJECT.md      document maître
  CHANGELOG.md    format Keep a Changelog
  journal/        une entrée par tâche
  adr/            une décision technique par fichier (NNNN-titre.md)
  spec.md         besoin (product-analyst)
  architecture.md conception (architect)
  plan.md         tâches et état (planner)
  api.md          référence API (doc-writer)
  runbook.md      installer, lancer, déployer, dépanner (devops-engineer)
  revues/         rapports de code-reviewer
  securite/       rapports de security-auditor
  livraisons/     rapports de quality-gatekeeper
  incidents/      analyses d'incident (debugger)
  ux/             parcours, écrans, design system (ui-ux-designer)
  seo/            stratégie et audits (seo-specialist, sites publics)
```

`docs/PROJECT.md` :

```markdown
# <Nom du projet>

## Résumé
Ce que fait le projet, pour qui.

## État actuel
Version, date de dernière mise à jour, ce qui marche, ce qui est en cours.

## Stack et architecture
Résumé ; détail dans [architecture.md](architecture.md).

## Applications
Dépôt à plusieurs applications seulement : carte du skill `monorepo` (chemin, rôle, stack, commandes, dépendances).

## Couverture par les agents
Table du skill `coverage-check` : ce qui est couvert, ce qui passe en mode dégradé, skills manquants.

## Fonctionnalités
| Fonctionnalité | Statut (prévu, en cours, livré) | Spec |

## Décisions clés
- [ADR-0001](adr/0001-…md) : une ligne.

## Dernières mises à jour
Les 10 dernières entrées du journal, en liens.

## Dette technique et risques connus

## Index
Liens vers les autres fichiers de `docs/`.
```

`docs/CHANGELOG.md` :

```markdown
# Changelog
Format : [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/), versions : [SemVer](https://semver.org/lang/fr/).

## [Unreleased]
```

## Livrable
- Une entrée de journal par tâche, une ligne de CHANGELOG si le comportement visible change, le statut de la tâche à jour dans `docs/plan.md`.

## Vérifications
- L'entrée de journal cite l'agent, la tâche, les fichiers et les vérifications exactes.
- Aucune entrée existante n'a été modifiée ni supprimée (`git diff docs/journal/` ne montre que des ajouts).

## Limites
- Pas de secret, de donnée personnelle ni de sortie complète de commande dans `docs/`.

## En cas de blocage
- `docs/` absent et rôle qui ne prévoit pas de le créer : mettre l'entrée de journal dans le compte rendu et signaler l'absence.
